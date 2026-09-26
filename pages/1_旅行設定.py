from datetime import date
import pandas as pd
import streamlit as st

from utils.excel_store import read_sheet, write_sheet, update_row, delete_row
from utils.validators import uid

st.title("⚙️ 旅行與成員設定中心")

t = read_sheet("TripInfo")
m = read_sheet("Members")
old = t.iloc[0].to_dict() if len(t) else {}

# --- 安全計算啟用成員數 ---
active_count = 0
if not m.empty and "active" in m.columns:
    active_count = len(m[m.active.astype(str).str.lower().isin(["true", "1", "yes"])])

# --- 🎯 頂部快速指標儀表板 ---
col1, col2, col3 = st.columns(3)
col1.metric("📌 當前旅行名稱", old.get("trip_name", "未命名旅行"))
col2.metric("📍 目的地", old.get("destination", "未設定"))
col3.metric("👥 啟用成員數", f"{active_count} 人")
st.divider()

# --- 📑 分頁籤設計 (Tabs) ---
tab_trip, tab_members, tab_add_member = st.tabs(["✈️ 基本旅行設定", "👥 同行成員列表與管理", "➕ 新增成員"])

# ==================== 分頁 1：基本旅行設定 ====================
with tab_trip:
    st.subheader("📌 編輯旅行基本資訊")
    
    with st.form("trip_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("旅行名稱", old.get("trip_name", ""))
            dest = st.text_input("目的地", old.get("destination", ""))
            start = st.date_input(
                "出發日期",
                pd.to_datetime(old["start_date"]).date()
                if old.get("start_date")
                else date.today(),
            )
        with col_b:
            end = st.date_input(
                "回程日期",
                pd.to_datetime(old["end_date"]).date() if old.get("end_date") else date.today(),
            )
            cur = st.text_input("本位幣別", old.get("base_currency", "HKD"))
            rate = st.number_input(
                "預設匯率", min_value=0.01, value=float(old.get("default_exchange_rate") or 1)
            )
            
        ok = st.form_submit_button("💾 儲存旅行設定", type="primary")

    if ok:
        if end < start:
            st.error("⚠️ 回程日期不可早於出發日期！")
        else:
            now = pd.Timestamp.now()
            write_sheet(
                "TripInfo",
                pd.DataFrame(
                    [
                        {
                            "trip_id": old.get("trip_id") or uid("trip"),
                            "trip_name": name,
                            "destination": dest,
                            "start_date": start,
                            "end_date": end,
                            "base_currency": cur,
                            "default_exchange_rate": rate,
                            "created_at": old.get("created_at") or now,
                            "updated_at": now,
                        }
                    ]
                ),
            )
            st.success("🎉 旅行設定已成功更新！")
            st.rerun()

# ==================== 分頁 2：同行成員列表與管理 ====================
with tab_members:
    st.subheader("👥 成員名單與狀態管理")
    
    if m.empty or "member_name" not in m.columns:
        st.info("目前尚無成員，請至「新增成員」分頁添加。")
    else:
        for idx, row in m.iterrows():
            is_active = str(row.get('active', True)).lower() in ['true', '1', 'yes']
            status_badge = "🟢 啟用中" if is_active else "🔴 已停用"
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{row.get('member_name', '')}**  |  狀態: `{status_badge}`")
                with c2:
                    with st.popover("✏️ 編輯"):
                        with st.form(f"edit_mem_{row.get('member_id', idx)}"):
                            edit_name = st.text_input("修改名稱", value=str(row.get("member_name", "")))
                            edit_active = st.checkbox("啟用參與分帳", value=is_active)
                            
                            if st.form_submit_button("儲存變更"):
                                if not edit_name.strip():
                                    st.error("名稱不可空白！")
                                else:
                                    update_row("Members", "member_id", row["member_id"], {
                                        "member_name": edit_name.strip(),
                                        "active": edit_active
                                    })
                                    st.success("成員更新成功！")
                                    st.rerun()
                with c3:
                    if st.button("🗑️ 刪除", key=f"del_mem_{row.get('member_id', idx)}"):
                        delete_row("Members", "member_id", row["member_id"])
                        st.success("已刪除成員")
                        st.rerun()

# ==================== 分頁 3：新增成員 ====================
with tab_add_member:
    st.subheader("➕ 新增同行旅伴")
    
    with st.form("add_member_form", clear_on_submit=True):
        new_name = st.text_input("新成員名稱 (例如: 成員A)")
        add_ok = st.form_submit_button("✨ 確認新增成員", type="primary")
        
        if add_ok:
            if not new_name.strip():
                st.error("成員名稱不可空白！")
            elif not m.empty and "member_name" in m.columns and new_name.strip() in m.member_name.values:
                st.error("該成員名稱已經存在！")
            else:
                new_row = pd.DataFrame(
                    [
                        {
                            "member_id": uid("mem"),
                            "member_name": new_name.strip(),
                            "active": True,
                            "created_at": pd.Timestamp.now(),
                        }
                    ]
                )
                # 確保舊資料與新資料串接順暢
                updated_m = pd.concat([m, new_row], ignore_index=True) if not m.empty else new_row
                write_sheet("Members", updated_m)
                st.success(f"🎉 已成功新增成員：{new_name.strip()}")
                st.rerun()