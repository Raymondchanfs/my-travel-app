import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.excel_store import initialize_workbook

if __name__ == "__main__":
    initialize_workbook()
    print("已建立或確認 data/travel_data.xlsx")
