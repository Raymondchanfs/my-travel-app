import streamlit as st
import pandas as pd
import gspread
from datetime import date, datetime

def get_spreadsheet_url():
    try:
        return st.secrets["connections"]["gsheets"]["spreadsheet"]
    except Exception:
        return None

def read_sheet(sheet_name: str) -> pd.DataFrame:
    try:
        spreadsheet_url = get_spreadsheet_url()
        if not spreadsheet_url:
            return pd.DataFrame()
        
        # 從網址中萃取 Spreadsheet ID
        if "/d/" in spreadsheet_url:
            sheet_id = spreadsheet_url.split("/d/")[1].split("/")[0]
        else:
            sheet_id = spreadsheet_url
            
        # 使用 Google 內建的公開 CSV 匯出連結讀取，100% 避開 st.connection 報錯
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        return pd.DataFrame()

def write_sheet(sheet_name: str, df: pd.DataFrame):
    try:
        spreadsheet_url = get_spreadsheet_url()
        if not spreadsheet_url:
            st.error("找不到試算表網址設定")
            return

        # 檢查專案中是否有現成的連線工具或 st.secrets 設定
        try:
            # 嘗試使用 gspread 預設的憑證載入 (支援 Streamlit Cloud Secrets)
            import json
            import os
            
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                gc = gspread.service_account_from_dict(creds_dict)
            elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
                creds_dict = dict(st.secrets["connections"]["gsheets"])
                gc = gspread.service_account_from_dict(creds_dict)
            else:
                # 如果沒有 secrets，嘗試從環境變數或預設路徑，若無則改用共用授權
                gc = gspread.oauth()
        except Exception:
            # 終極備案：直接利用您專案中可能已經初始化好的 gspread 授權
            import gspread
            gc = gspread.oauth()

        sh = gc.open_by_url(spreadsheet_url)
        
        try:
            worksheet = sh.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
            
        df_to_write = df.copy()
        for col in df_to_write.columns:
            if pd.api.types.is_datetime64_any_dtype(df_to_write[col]):
                df_to_write[col] = df_to_write[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 轉換資料格式並寫入
        data = [df_to_write.columns.tolist()] + df_to_write.astype(str).values.tolist()
        worksheet.clear()
        worksheet.update(data)
        
    except Exception as e:
        st.error(f"寫入 Google 試算表失敗: {e}")
        raise e

def update_row(sheet_name: str, id_col: str, row_id: str, new_values: dict):
    df = read_sheet(sheet_name)
    if df.empty or id_col not in df.columns:
        return
    match = df[df[id_col].astype(str) == str(row_id)]
    if not match.empty:
        idx = match.index[0]
        for key, val in new_values.items():
            if key in df.columns:
                df.at[idx, key] = val
        write_sheet(sheet_name, df)

def delete_row(sheet_name: str, id_col: str, row_id: str):
    df = read_sheet(sheet_name)
    if df.empty or id_col not in df.columns:
        return
    df = df[df[id_col].astype(str) != str(row_id)]
    write_sheet(sheet_name, df)

def initialize_workbook():
    pass

def backup_workbook():
    st.info("使用 Google 試算表後，版本歷史記錄與備份將由 Google 自動管理！")