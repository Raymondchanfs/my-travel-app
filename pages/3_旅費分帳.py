import pandas as pd
import streamlit as st

from utils.calculations import settlement
from utils.excel_store import read_sheet, write_sheet, update_row, delete_row
from utils.validators import json_text, uid

st.title("💰 旅費記帳與智慧分帳")

t = read_sheet("TripInfo")
m = read_sheet("Members")
active = m[
    m.active.astype(str).str.lower().isin(["true", "1", "yes"])
].member_name.tolist()
e = read_sheet("Expenses")

if not active:
    st.warning("⚠️ 請先至「旅行設定」頁面新增並啟用同行成員！")
    st.stop()

# --- 🎯 頂部快速指標儀表板 ---
if not e.empty:
    total_hkd = e["base_amount"].sum()
    paid_dict, share_dict, balance_dict, _ = settlement(e, active)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💳 總旅費支出 (HKD)", f"${total_hkd:,.2f}")
    col2.metric("👥 同行啟用人數", f"{len(active)} 人")
    col3.metric("💸 平均每人應付", f"${total_hkd / len(active):,.2f}" if active else "$0.00")
    st.divider()

# --- 📑 分頁籤設計 (Tabs) ---
tab_summary, tab_list, tab_add = st.tabs(["📊 結算與圖表總覽", "📝 支出明細與編輯", "➕ 快速新增支出"])

# ==================== 分頁 1：結算與圖表總覽 ====================
with tab_summary:
    st.subheader("👥 個人收支結算表")
    if e.empty:
        st.info("目前尚無任何支出紀錄，請先至「快速新增支出」分頁添加。")
    else:
        paid, share, balance, trans = settlement(e, active)
        
        # 轉換為美化後的 DataFrame
        settle_df = pd.DataFrame([
            {
                "成員": x,
                "已付金額 (Paid)": float(paid[x]),
                "應分攤額 (Share)": float(share[x]),
                "淨結算 (Net Balance)": float(balance[x]),
                "狀態": "🟢 應收回" if balance[x] > 0 else "🔴 需支付" if balance[x] < 0 else "⚪ 平衡"
            }
            for x in active
        ])
        st.dataframe(settle_df, use_container_width=True, hide_index=True)

        st.subheader("💡 最佳找贖建議 (誰該轉帳給誰)")
        if trans:
            trans_df = pd.DataFrame(trans)
            # 美化欄位名稱
            trans_df.columns = ["付款人 (Debtor)", "收款人 (Creditor)", "轉帳金額 (HKD)"]
            st.dataframe(trans_df, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 目前所有人的帳目皆已平衡，無需額外轉帳！")

        st.divider()
        st.subheader("📈 消費類別統計")
        # 簡單的分類長條圖
        if "category" in e.columns and "base_amount" in e.columns:
            cat_sum = e.groupby("category")["base_amount"].sum()
            st.bar_chart(cat_sum)

        # 匯出按鈕
        st.download_button(
            "📥 匯出完整旅費 CSV 報表", 
            e.to_csv(index=False).encode("utf-8-sig"), 
            "travel_expenses.csv",
            mime="text/csv"
        )

# ==================== 分頁 2：支出明細與編輯 ====================
with tab_list:
    st.subheader("📋 所有支出紀錄 (可編輯與刪除)")
    if e.empty:
        st.info("目前沒有支出紀錄。")
    else:
        for idx, row in e.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{row['item_name']}** (`{row['category']}`)")
                    st.caption(f"金額: **{row['original_amount']} {row['original_currency']}** (折合 HKD: **${row['base_amount']}**) | 支付者: **{row['payer']}** | 日期: {row['expense_date']}")
                with c2:
                    with st.popover("✏️ 編輯"):
                        with st.form(f"edit_ex_{row['expense_id']}"):
                            new_item = st.text_input("項目名稱", value=str(row["item_name"]))
                            new_amt = st.number_input("原始金額", value=float(row["original_amount"]))
                            new_rate = st.number_input("匯率", value=float(row["exchange_rate"]))
                            new_payer = st.selectbox("付款人", active, index=active.index(row["payer"]) if row["payer"] in active else 0)
                            if st.form_submit_button("儲存修改"):
                                update_row("Expenses", "expense_id", row["expense_id"], {
                                    "item_name": new_item,
                                    "original_amount": new_amt,
                                    "exchange_rate": new_rate,
                                    "base_amount": round(new_amt * new_rate, 2),
                                    "payer": new_payer,
                                    "updated_at": pd.Timestamp.now()
                                })
                                st.success("修改成功！")
                                st.rerun()
                with c3:
                    if st.button("🗑️ 刪除", key=f"del_ex_{row['expense_id']}"):
                        delete_row("Expenses", "expense_id", row["expense_id"])
                        st.success("已刪除")
                        st.rerun()

# ==================== 分頁 3：快速新增支出 ====================
with tab_add:
    st.subheader("➕ 記一筆新花費")
    with st.form("expense_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            d = st.date_input("消費日期")
            cat = st.selectbox("類別", ["交通", "住宿", "餐飲", "門票", "購物", "其他"])
            item = st.text_input("項目名稱 (例如: 曼谷計程車)")
            cur = st.selectbox("原始幣別", ["THB", "HKD", "USD"], index=0)
        with col_b:
            amount = st.number_input("原始金額", min_value=0.01, value=100.0)
            default_r = 0.23 if cur == "THB" else 1.0
            rate = st.number_input("匯率 (對 HKD)", min_value=0.0001, value=default_r)
            payer = st.selectbox("付款人 (誰付的錢)", active)
            typ = st.selectbox("分攤方式", ["全體均分", "指定成員"])
            
        targets = st.multiselect("選擇分攤成員", active, default=active) if typ == "指定成員" else active
        
        submitted = st.form_submit_button("✨ 確認新增支出", type="primary")
        if submitted:
            if typ == "指定成員" and not targets:
                st.error("請至少選擇一位分攤成員！")
            else:
                r = {
                    "expense_id": uid("ex"),
                    "trip_id": t.iloc[0].trip_id if len(t) else "",
                    "expense_date": d,
                    "category": cat,
                    "item_name": item,
                    "original_currency": cur,
                    "original_amount": amount,
                    "exchange_rate": rate,
                    "base_amount": round(amount * rate, 2),
                    "payer": payer,
                    "split_type": typ,
                    "split_members": json_text(targets),
                    "note": "",
                    "created_at": pd.Timestamp.now(),
                    "updated_at": pd.Timestamp.now(),
                }
                write_sheet("Expenses", pd.concat([e, pd.DataFrame([r])], ignore_index=True))
                st.success("🎉 支出新增成功！")
                st.rerun()