# 多人旅行行程與花費分帳 App

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts\init_excel.py
python scripts\seed_debug_data.py
streamlit run app.py
```

所有永久資料儲存於 data/travel_data.xlsx。
