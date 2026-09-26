import pandas as pd
import streamlit as st

from utils.excel_store import read_sheet, write_sheet, update_row, delete_row
from utils.validators import uid

st.title("🗓️ 曼谷旅行行程規劃")

t = read_sheet("TripInfo")
if not len(t):
    st.warning("⚠️ 請先至「旅行設定」頁面設定旅行起訖日期！")
    st.stop()

start = pd.to_datetime(t.iloc[0].start_date).date()
end = pd.to_datetime(t.iloc[0].end_date).date()
total_days = (end - start).days + 1

# 讀取現有行程資料
data = read_sheet("Itinerary")

# --- 🎯 頂部快速指標儀表板 ---
col1, col2, col3 = st.columns(3)
col1.metric("📅 旅行起訖", f"{start} ~ {end}")
col2.metric("⏳ 總天數", f"{total_days} 天")
col3.metric("📌 已規劃行程數", f"{len(data)} 項")
st.divider()

# --- 📑 分頁籤設計 (Tabs) ---
tab_view, tab_add = st.tabs(["🗺️ 依天數檢視行程", "➕ 快速新增行程"])

# ==================== 分頁 1：依天數檢視行程 ====================
with tab_view:
    st.subheader("📋 行程總覽與管理")
    
    if data.empty:
        st.info("目前尚無任何行程規劃，請至「快速新增行程」分頁添加。")
    else:
        # 建立天數篩選器 (例如: 全部顯示、Day 1、Day 2...)
        day_options = ["全部顯示"] + [f"Day {d}" for d in range(1, total_days + 1)]
        selected_day = st.selectbox("選擇要檢視的天數", day_options)
        
        # 篩選資料
        filtered_data = data if selected_day == "全部顯示" else data[data["day_number"].astype(str) == selected_day.replace("Day ", "")]
        
        if filtered_data.empty:
            st.info(f"這一天 ({selected_day}) 目前還沒有安排任何活動。")
        else:
            # 依照日期與時間排序
            filtered_data = filtered_data.sort_values(by=["day_number", "itinerary_date"])
            
            for idx, row in filtered_data.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([4, 1, 1])
                    with c1:
                        st.markdown(f"**Day {row['day_number']}** ({row['itinerary_date']}) | 📍 **{row['place']}**")
                        st.write(f"🏃‍♂️ **活動內容**: {row['activity']}")
                        if row["note"]:
                            st.caption(f"📝 備註: {row['note']}")
                    with c2:
                        # 彈出式編輯按鈕
                        with st.popover("✏️ 編輯"):
                            with st.form(f"edit_it_{row['itinerary_id']}"):
                                new_date = st.date_input("日期", pd.to_datetime(row["itinerary_date"]).date() if pd.notnull(row["itinerary_date"]) else start, min_value=start, max_value=end)
                                new_place = st.text_input("地點", value=str(row["place"]))
                                new_activity = st.text_input("活動", value=str(row["activity"]))
                                new_note = st.text_input("備註", value=str(row["note"]))
                                
                                if st.form_submit_button("儲存變更"):
                                    new_day_num = (new_date - start).days + 1
                                    update_row("Itinerary", "itinerary_id", row["itinerary_id"], {
                                        "itinerary_date": new_date,
                                        "day_number": new_day_num,
                                        "place": new_place,
                                        "activity": new_activity,
                                        "note": new_note,
                                        "updated_at": pd.Timestamp.now()
                                    })
                                    st.success("行程修改成功！")
                                    st.rerun()
                    with c3:
                        # 刪除按鈕
                        if st.button("🗑️ 刪除", key=f"del_it_{row['itinerary_id']}"):
                            delete_row("Itinerary", "itinerary_id", row["itinerary_id"])
                            st.success("已刪除該行程")
                            st.rerun()

# ==================== 分頁 2：快速新增行程 ====================
with tab_add:
    st.subheader("➕ 新增一日行程或景點")
    
    with st.form("itinerary_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            d = st.date_input("活動日期", start, min_value=start, max_value=end)
            place = st.text_input("地點 / 景點名稱 (例如: 大皇宮)")
        with col_b:
            activity = st.text_input("活動內容 (例如: 參觀玉佛寺、穿泰服)")
            note = st.text_input("備註 (例如: 穿著須過膝、門票已訂)")
            
        submitted = st.form_submit_button("✨ 確認新增行程", type="primary")
        
        if submitted:
            if not place.strip() or not activity.strip():
                st.error("地點與活動內容不可空白！")
            else:
                day_num = (d - start).days + 1
                r = {
                    "itinerary_id": uid("it"),
                    "trip_id": t.iloc[0].trip_id,
                    "day_number": day_num,
                    "itinerary_date": d,
                    "start_time": "",
                    "end_time": "",
                    "place": place.strip(),
                    "activity": activity.strip(),
                    "note": note.strip(),
                    "created_at": pd.Timestamp.now(),
                    "updated_at": pd.Timestamp.now(),
                }
                write_sheet("Itinerary", pd.concat([data, pd.DataFrame([r])], ignore_index=True))
                st.success("🎉 行程新增成功！")
                st.rerun()