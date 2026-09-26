import streamlit as st
import pandas as pd
from datetime import date, datetime

def get_connection():
    # 使用 st-gsheets-connection 的標準連線方式
    return st.connection("gsheets", type="gsheets")

def read_sheet(sheet_name: str) -> pd.DataFrame:
    try:
        conn = get_connection()
        # 讀取指定的 worksheet
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception as e:
        return pd.DataFrame()

def write_sheet(sheet_name: str, df: pd.DataFrame):
    try:
        conn = get_connection()
        df_to_write = df.copy()
        for col in df_to_write.columns:
            if pd.api.types.is_datetime64_any_dtype(df_to_write[col]) or isinstance(df_to_write[col].iloc[0] if len(df_to_write)>0 else None, (date, datetime)):
                df_to_write[col] = pd.to_datetime(df_to_write[col]).dt.strftime('%Y-%m-%d')
        
        conn.update(worksheet=sheet_name, data=df_to_write)
    except Exception as e:
        st.error(f"寫入 Google 試算表失敗: {e}")

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