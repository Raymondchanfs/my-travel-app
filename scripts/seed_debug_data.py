import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.excel_store import initialize_workbook, write_sheet
from utils.validators import json_text, uid

initialize_workbook()
now = pd.Timestamp.now()
trip = "trip_debug_bangkok_5d"
write_sheet(
    "TripInfo",
    pd.DataFrame(
        [
            {
                "trip_id": trip,
                "trip_name": "曼谷五日旅行 Debug 測試",
                "destination": "曼谷 Bangkok",
                "start_date": date(2026, 11, 1),
                "end_date": date(2026, 11, 5),
                "base_currency": "HKD",
                "default_exchange_rate": 0.23,
                "created_at": now,
                "updated_at": now,
            }
        ]
    ),
)
write_sheet(
    "Members",
    pd.DataFrame(
        [
            {
                "member_id": f"mem_{x}",
                "member_name": f"成員{x.upper()}",
                "active": True,
                "created_at": now,
            }
            for x in ["a", "b", "c", "d"]
        ]
    ),
)
items = [
    (1, "14:00", "15:45", "香港 -> 曼谷", "香港航空 HX775", "香港出發"),
    (1, "18:00", "21:00", "暹羅商圈", "Siam Paragon、CentralWorld", "市區商圈"),
    (2, "09:00", "12:00", "大皇宮", "大皇宮及玉佛寺", "參觀"),
    (2, "14:00", "17:00", "泰服體驗", "泰服租借及拍照", "預約行程"),
    (3, "07:00", "19:00", "郊區一日遊", "水上市場及美功鐵道市場", "包車行程"),
    (4, "10:00", "13:00", "One Bangkok", "最新地標", "探索商場"),
    (4, "19:00", "23:00", "高空酒吧", "曼谷高空酒吧", "城市夜景"),
    (5, "09:00", "12:00", "曼谷市區", "最後購物及午餐", "整理行李"),
    (5, "15:35", "19:30", "曼谷 -> 香港", "香港航空 HX776", "返回香港"),
]
write_sheet(
    "Itinerary",
    pd.DataFrame(
        [
            {
                "itinerary_id": uid("it"),
                "trip_id": trip,
                "day_number": d,
                "itinerary_date": date(2026, 11, d),
                "start_time": s,
                "end_time": e,
                "place": p,
                "activity": a,
                "note": n,
                "created_at": now,
                "updated_at": now,
            }
            for d, s, e, p, a, n in items
        ]
    ),
)
vals = [
    (1, "交通", "去程機票 HX775", 2800, "成員A"),
    (5, "交通", "回程機票 HX776", 2800, "成員B"),
    (1, "其他", "機場稅及附加費", 900, "成員A"),
    (1, "其他", "旅遊保險", 364, "成員C"),
    (1, "其他", "優惠折扣", -100, "成員D"),
    (2, "餐飲", "泰服體驗訂金", 400, "成員D"),
    (3, "交通", "郊區一日遊訂金", 500, "成員C"),
    (4, "其他", "高空酒吧預約費", 200, "成員B"),
]
people = ["成員A", "成員B", "成員C", "成員D"]
write_sheet(
    "Expenses",
    pd.DataFrame(
        [
            {
                "expense_id": uid("ex"),
                "trip_id": trip,
                "expense_date": date(2026, 11, d),
                "category": c,
                "item_name": i,
                "original_currency": "HKD",
                "original_amount": a,
                "exchange_rate": 1,
                "base_amount": a,
                "payer": p,
                "split_type": "全體均分",
                "split_members": json_text(people),
                "note": "",
                "created_at": now,
                "updated_at": now,
            }
            for d, c, i, a, p in vals
        ]
    ),
)
write_sheet(
    "AuditLog",
    pd.DataFrame(
        columns=[
            "log_id",
            "action",
            "entity_type",
            "entity_id",
            "description",
            "before_data",
            "after_data",
            "operator",
            "created_at",
        ]
    ),
)
print("Debug 資料已建立，預載總額 HK$7,864.00")
