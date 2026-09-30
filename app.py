import streamlit as st
import pandas as pd
from datetime import datetime

from utils.calculations import settlement
from utils.excel_store import backup_workbook, initialize_workbook, read_sheet

# --- 🎨 頁面全域設定 (必須放在所有 st 指令的最上方) ---
st.set_page_config(
    page_title="多人旅遊分帳與行程管理", 
    page_icon="✈️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化資料庫
initialize_workbook()

def reload_data():
    st.session_state.trip_info = read_sheet("TripInfo")
    st.session_state.members = read_sheet("Members")
    st.session_state.itinerary_items = read_sheet("Itinerary")
    st.session_state.expense_items = read_sheet("Expenses")
    st.session_state.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if "trip_info" not in st.session_state:
    reload_data()

t = st.session_state.trip_info
m = st.session_state.members
it = st.session_state.itinerary_items
e = st.session_state.expense_items

trip_name = t.iloc[0].get("trip_name", "未命名旅行") if len(t) else "尚未設定旅行"
destination = t.iloc[0].get("destination", "未設定目的地") if len(t) else ""

# --- 🎨 側邊欄設計 (Sidebar) ---
with st.sidebar:
    st.markdown(f"## ✈️ {trip_name}")
    st.caption(f"📍 目的地: {destination}")
    st.divider()
    
    st.markdown("### 🛠️ 資料庫控制台")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔄 重新載入", use_container_width=True):
            reload_data()
            st.success("已同步！")
            st.rerun()

        if st.button("💾 建立備份", use_container_width=True):
            backup_workbook()
            st.success("備份成功！")
            
    st.caption(f"⏱️ 最後同步: {st.session_state.get('last_updated', '剛剛')}")
    st.divider()
    
    st.info("💡 提示：請透過上方或左側的頁面選單切換至「旅行設定」、「行程規劃」或「旅費分帳」進行詳細編輯。")

# --- 🏠 主頁面內容 ---
st.title(f"🌍 {trip_name} - 總覽儀表板")
st.markdown(f"歡迎使用智慧旅遊分帳與行程規劃系統！目前的目的地為：**{destination}**。")
st.divider()

# 計算基本數據
active = m[m.active.astype(str).str.lower().isin(["true", "1", "yes"])].member_name.tolist() if not m.empty else []
total_expense = e["base_amount"].sum() if not e.empty and "base_amount" in e.columns else 0.0
total_itinerary = len(it) if not it.empty else 0
total_members = len(active)

# --- 📊 頂部大型數據指標 (Metrics) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 總花費金額", f"${total_expense:,.2f} HKD")
col2.metric("👥 啟用旅伴人數", f"{total_members} 人")
col3.metric("📅 已排行程項目", f"{total_itinerary} 項")
col4.metric("⚙️ 資料庫狀態", "🟢 運行正常")

st.markdown("### 📊 快速財務總覽")

if not active or e.empty:
    st.info("👋 目前尚無成員或支出資料。請先至左側頁面新增成員並開始記帳！")
else:
    paid, share, balance, transfers = settlement(e, active)
    
    # 顯示個人收支表格
    summary_data = [
        {
            "成員": x,
            "已付金額 (Paid)": float(paid[x]),
            "應分攤額 (Share)": float(share[x]),
            "淨結算 (Net Balance)": float(balance[x]),
            "財務狀態": "🟢 應收回" if balance[x] > 0 else "🔴 需支付" if balance[x] < 0 else "⚪ 平衡",
        }
        for x in active
    ]
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    # 顯示轉帳建議
    if transfers:
        st.markdown("### 💸 推薦轉帳方案（最少筆數結算）")
        trans_df = pd.DataFrame(transfers)
        trans_df.columns = ["付款人 (Debtor)", "收款人 (Creditor)", "轉帳金額 (HKD)"]
        st.dataframe(trans_df, use_container_width=True, hide_index=True)
    else:
        st.success("🎉 目前所有人的帳目皆已結清，無須額外轉帳！")