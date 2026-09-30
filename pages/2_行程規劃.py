import pandas as pd
import streamlit as st

from utils.excel_store import read_sheet, write_sheet, update_row, delete_row
from utils.validators import uid

st.title("📅 旅遊行程與時間軸規劃")

t = read_sheet("TripInfo")
it = read_sheet("Itinerary")
m = read_sheet("Members")

# 🔒 自動對應您的真實試算表欄位名稱
if not it.empty:
    col_mapping = {
        "item_id": "itinerary_id",
        "day_index": "day_num",
        "title": "activity",
        "location": "place",
        "item_time": "start_time"
    }
    it = it.rename(columns=col_mapping)

# 確保必要欄位存在
required_cols = ["itinerary_id", "trip_id", "day_num", "start_time", "end_time", "place", "activity", "note", "created_at"]
for col in required_cols:
    if col not in it.columns:
        it[col] = ""

# --- 📑 分頁籤設計 ---
tab_calendar, tab_batch, tab_list, tab_add = st.tabs([
    "🗓️ 時間軸行事曆檢視", 
    "📊 批次表格編輯 (推薦)", 
    "📝 單筆清單與編輯", 
    "➕ 新增行程項目"
])

# ==================== 分頁 1：時間軸行事曆檢視 ====================
with tab_calendar:
    st.subheader("🗓️ 行程時間軸矩陣")
    
    if it.empty:
        st.info("目前尚無行程資料，請至「新增行程項目」分頁添加。")
    else:
        days = sorted(it["day_num"].dropna().unique()) if "day_num" in it.columns else [1]
        cols = st.columns(len(days) if len(days) > 0 else 1)
        
        for idx, day in enumerate(days):
            with cols[idx]:
                st.markdown(f"### 📌 Day {int(day) if pd.notna(day) and str(day).isdigit() else day}")
                st.divider()
                
                day_items = it[it["day_num"] == day]
                if "start_time" in day_items.columns:
                    day_items = day_items.sort_values(by="start_time", ascending=True)
                
                for _, row in day_items.iterrows():
                    start_str = str(row.get('start_time', ''))
                    end_str = str(row.get('end_time', ''))
                    time_str = f"{start_str} - {end_str}" if end_str and end_str != 'nan' else start_str
                    if not time_str or time_str == 'nan':
                        time_str = '全天'
                        
                    activity_str = str(row.get('activity', '未命名行程'))
                    place_str = str(row.get('place', ''))
                    note_str = str(row.get('note', ''))
                    
                    with st.container(border=True):
                        st.markdown(f"⏰ **{time_str}**")
                        st.markdown(f"**{activity_str}**")
                        if place_str and place_str != 'nan':
                            st.caption(f"📍 地點: {place_str}")
                        if note_str and note_str != 'nan':
                            st.caption(f"📝 {note_str}")

# ==================== 分頁 2：批次表格編輯 (st.data_editor) ====================
with tab_batch:
    st.subheader("📊 批次修改行程資料")
    st.info("💡 您可以直接在此表格內點擊儲存格修改多筆資料（如調整時間、地點或活動內容），修改完成後點擊下方的按鈕即可一鍵儲存！")
    
    if it.empty:
        st.info("目前沒有行程可以編輯。")
    else:
        # 選擇要在表格中顯示與編輯的核心欄位
        display_cols = ["day_num", "start_time", "end_time", "place", "activity", "note", "itinerary_id"]
        editable_df = it[[col for col in display_cols if col in it.columns]].copy()
        
        # 使用 Streamlit 內建的強大互動式編輯器
        edited_df = st.data_editor(
            editable_df,
            num_rows="dynamic",  # 允許直接新增/刪除行
            use_container_width=True,
            key="itinerary_batch_editor"
        )
        
        if st.button("💾 儲存所有批次變更", type="primary"):
            try:
                # 將編輯後的資料與原本的完整欄位（如 trip_id, created_at 等）進行合併
                # 確保不小心被隱藏或沒顯示的系統欄位不會遺失
                for idx, row in edited_df.iterrows():
                    it_id = row.get("itinerary_id")
                    
                    # 如果是新增加的列，自動補上 id 與時間
                    if pd.isna(it_id) or not str(it_id).startswith("it_"):
                        edited_df.at[idx, "itinerary_id"] = uid("it")
                        edited_df.at[idx, "trip_id"] = t.iloc[0].get('trip_id', '') if len(t) and "trip_id" in t.columns else "trip_debug"
                        edited_df.at[idx, "created_at"] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                edited_df["updated_at"] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 寫回 Google 試算表
                write_sheet("Itinerary", edited_df)
                st.success("🎉 所有變更已成功同步至 Google 試算表！")
                st.rerun()
            except Exception as e:
                st.error(f"儲存失敗: {e}")

# ==================== 分頁 3：單筆清單與編輯 ====================
with tab_list:
    st.subheader("📋 行程明細管理 (單筆微調與刪除)")
    
    if it.empty:
        st.info("目前沒有行程紀錄。")
    else:
        for idx, row in it.iterrows():
            it_id = row.get('itinerary_id', f"row_{idx}")
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**Day {row.get('day_num', 1)} | {row.get('start_time', '')} ~ {row.get('end_time', '')} - {row.get('activity', '')}**")
                    st.caption(f"地點: {row.get('place', '未指定')} | 備註: {row.get('note', '')}")
                with c2:
                    with st.popover("✏️ 編輯"):
                        with st.form(f"edit_it_{it_id}"):
                            edit_day = st.number_input("第幾天 (Day)", min_value=1, value=int(row.get("day_num", 1) if pd.notna(row.get("day_num")) and str(row.get("day_num")).isdigit() else 1))
                            edit_start = st.text_input("開始時間", value=str(row.get("start_time", "") if pd.notna(row.get("start_time")) else ""))
                            edit_end = st.text_input("結束時間", value=str(row.get("end_time", "") if pd.notna(row.get("end_time")) else ""))
                            edit_place = st.text_input("地點 (place)", value=str(row.get("place", "") if pd.notna(row.get("place")) else ""))
                            edit_act = st.text_input("活動 (activity)", value=str(row.get("activity", "") if pd.notna(row.get("activity")) else ""))
                            edit_note = st.text_area("備註 (note)", value=str(row.get("note", "") if pd.notna(row.get("note")) else ""))
                            
                            if st.form_submit_button("儲存修改"):
                                update_row("Itinerary", "itinerary_id", it_id, {
                                    "day_num": edit_day,
                                    "start_time": edit_start,
                                    "end_time": edit_end,
                                    "place": edit_place,
                                    "activity": edit_act,
                                    "note": edit_note
                                })
                                st.success("行程更新成功！")
                                st.rerun()
                with c3:
                    if st.button("🗑️ 刪除", key=f"del_it_{it_id}"):
                        delete_row("Itinerary", "itinerary_id", it_id)
                        st.success("已刪除行程")
                        st.rerun()

# ==================== 分頁 4：新增行程項目 ====================
with tab_add:
    st.subheader("➕ 新增旅遊行程")
    
    with st.form("itinerary_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            day_idx = st.number_input("第幾天 (Day)", min_value=1, value=1)
            start_t = st.text_input("開始時間 (例如 09:00)")
            end_t = st.text_input("結束時間 (例如 12:00)")
        with col_b:
            place = st.text_input("地點 (place)")
            activity = st.text_input("活動名稱 (activity)")
            
        note = st.text_area("備註 (note)")
        
        submitted = st.form_submit_button("✨ 確認新增行程", type="primary")
        if submitted:
            if not activity.strip():
                st.error("活動名稱不可空白！")
            else:
                new_row = pd.DataFrame(
                    [
                        {
                            "itinerary_id": uid("it"),
                            "trip_id": t.iloc[0].get('trip_id', '') if len(t) and "trip_id" in t.columns else "trip_debug",
                            "day_num": day_idx,
                            "start_time": start_t,
                            "end_time": end_t,
                            "place": place.strip(),
                            "activity": activity.strip(),
                            "note": note.strip(),
                            "created_at": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "updated_at": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    ]
                )
                updated_it = pd.concat([it, new_row], ignore_index=True) if not it.empty else new_row
                write_sheet("Itinerary", updated_it)
                st.success("🎉 行程新增成功！")
                st.rerun()