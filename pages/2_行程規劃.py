import pandas as pd
import streamlit as st

from utils.excel_store import read_sheet, write_sheet, update_row, delete_row
from utils.validators import uid

st.title("📅 旅遊行程與時間軸規劃")

t = read_sheet("TripInfo")
it = read_sheet("Itinerary")
m = read_sheet("Members")

active_members = []
if not m.empty and "member_name" in m.columns and "active" in m.columns:
    active_members = m[m.active.astype(str).str.lower().isin(["true", "1", "yes"])].member_name.tolist()

# --- 📑 分頁籤設計 ---
tab_calendar, tab_list, tab_add = st.tabs(["🗓️ 時間軸行事曆檢視", "📝 行程清單與編輯", "➕ 新增行程項目"])

# ==================== 分頁 1：時間軸行事曆檢視 (仿行事曆網格) ====================
with tab_calendar:
    st.subheader("🗓️ 行程時間軸矩陣")
    
    if it.empty:
        st.info("目前尚無行程資料，請至「新增行程項目」分頁添加。")
    else:
        # 確保必要的欄位存在
        if "day_index" in it.columns:
            # 取得所有不重複的天數並排序
            days = sorted(it["day_index"].dropna().unique())
            
            # 建立多欄位佈局，每一天代表一個直式行（類似行事曆的 Day 欄位）
            cols = st.columns(len(days) if len(days) > 0 else 1)
            
            for idx, day in enumerate(days):
                with cols[idx]:
                    st.markdown(f"### 📌 Day {int(day)}")
                    st.divider()
                    
                    # 篩選該天的行程並依時間排序
                    day_items = it[it["day_index"] == day]
                    if "item_time" in day_items.columns:
                        day_items = day_items.sort_values(by="item_time", ascending=True)
                    
                    for _, row in day_items.iterrows():
                        time_str = row.get('item_time', '全天')
                        title_str = row.get('title', '未命名行程')
                        loc_str = row.get('location', '')
                        cost_val = row.get('cost', 0)
                        
                        # 使用卡片式外框呈現每一個時間點的行程區塊（仿日曆 Event 卡片）
                        with st.container(border=True):
                            st.markdown(f"⏰ **{time_str}**")
                            st.markdown(f"**{title_str}**")
                            if loc_str:
                                st.caption(f"📍 {loc_str}")
                            if pd.notna(cost_val) and float(cost_val) > 0:
                                st.markdown(f"💰 `預估: ${float(cost_val):,.1f}`")
        else:
            st.warning("行程資料格式缺少 day_index 欄位。")

# ==================== 分頁 2：行程清單與編輯 ====================
with tab_list:
    st.subheader("📋 行程明細管理 (可編輯與刪除)")
    
    if it.empty:
        st.info("目前沒有行程紀錄。")
    else:
        for idx, row in it.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**Day {row.get('day_index', 1)} | {row.get('item_time', '')} - {row.get('title', '')}**")
                    st.caption(f"地點: {row.get('location', '未指定')} | 預估花費: ${row.get('cost', 0)} | 備註: {row.get('notes', '')}")
                with c2:
                    with st.popover("✏️ 編輯"):
                        with st.form(f"edit_it_{row.get('item_id', idx)}"):
                            edit_day = st.number_input("第幾天 (Day)", min_value=1, value=int(row.get("day_index", 1)))
                            edit_time = st.text_input("時間 (例如 09:30)", value=str(row.get("item_time", "")))
                            edit_title = st.text_input("行程標題", value=str(row.get("title", "")))
                            edit_loc = st.text_input("地點", value=str(row.get("location", "")))
                            edit_cost = st.number_input("預估花費", value=float(row.get("cost", 0)))
                            edit_notes = st.text_area("備註說明", value=str(row.get("notes", "")))
                            
                            if st.form_submit_button("儲存修改"):
                                update_row("Itinerary", "item_id", row["item_id"], {
                                    "day_index": edit_day,
                                    "item_time": edit_time,
                                    "title": edit_title,
                                    "location": edit_loc,
                                    "cost": edit_cost,
                                    "notes": edit_notes
                                })
                                st.success("行程更新成功！")
                                st.rerun()
                with c3:
                    if st.button("🗑️ 刪除", key=f"del_it_{row.get('item_id', idx)}"):
                        delete_row("Itinerary", "item_id", row["item_id"])
                        st.success("已刪除行程")
                        st.rerun()

# ==================== 分頁 3：新增行程項目 ====================
with tab_add:
    st.subheader("➕ 新增旅遊行程")
    
    with st.form("itinerary_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            day_idx = st.number_input("第幾天 (Day)", min_value=1, value=1)
            item_time = st.text_input("時間 (例如 09:30 或 上午9:30)")
            title = st.text_input("行程標題 (例如: 大城動物園)")
        with col_b:
            location = st.text_input("地點 (例如: Sriayuthaya Lion Park)")
            cost = st.number_input("預估花費 (HKD)", min_value=0.0, value=0.0)
            
        notes = st.text_area("備註 / 交通方式說明")
        
        submitted = st.form_submit_button("✨ 確認新增行程", type="primary")
        if submitted:
            if not title.strip():
                st.error("行程標題不可空白！")
            else:
                new_row = pd.DataFrame(
                    [
                        {
                            "item_id": uid("it"),
                            "trip_id": t.iloc[0].trip_id if len(t) and "trip_id" in t.columns else "",
                            "day_index": day_idx,
                            "item_time": item_time,
                            "title": title.strip(),
                            "location": location.strip(),
                            "cost": cost,
                            "notes": notes.strip(),
                            "created_at": pd.Timestamp.now(),
                        }
                    ]
                )
                updated_it = pd.concat([it, new_row], ignore_index=True) if not it.empty else new_row
                write_sheet("Itinerary", updated_it)
                st.success("🎉 行程新增成功！")
                st.rerun()