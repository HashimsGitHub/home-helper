# 🏠 Home Helper

A Streamlit Progressive Web App (PWA) for managing:
- 🛒 Grocery lists
- 📅 Appointments with calendar UI
- ✅ Household tasks

Backend: **Turso Cloud (libSQL)** — edge-replicated SQLite.

## Local Dev
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo 'TURSO_DATABASE_URL="libsql://..."' > .env
echo 'TURSO_AUTH_TOKEN="..."' >> .env
streamlit run app.py