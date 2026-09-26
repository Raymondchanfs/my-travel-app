# 多人旅行行程與花費分帳 App

```powershell
python -m venv .venv
.venv\Scripts\activate (deactivate)
pip install -r requirements.txt
python scripts\init_excel.py
python scripts\seed_debug_data.py
streamlit run app.py
```

所有永久資料儲存於 data/travel_data.xlsx。

git init
git add .
git commit -m "Migrate to Git and Google Sheets backend"
git branch -M main
git remote add origin https://github.com/Raymondchanfs/my-travel-app.git
git remote add origin git@github.com:Raymondchanfs/my-travel-app.git
git push -u origin main##