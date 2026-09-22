# Home Helper

A mobile-first Streamlit Progressive Web App (PWA) for managing grocery lists,
appointments, and household tasks from one simple dashboard.

Backend: **Turso Cloud (libSQL)** — edge-replicated SQLite.

## Mobile UX

- Native top navigation keeps every section visible without opening a sidebar.
- Add forms stay collapsed until needed, keeping lists easy to scan.
- Active and completed items are separated into focused tabs.
- Large native controls and full-width actions work well on touch screens.
- Destructive actions live inside an actions menu to reduce accidental deletion.
- The PWA manifest supports adding Home Helper to a phone's Home Screen.

## Local development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo 'TURSO_DATABASE_URL="libsql://..."' > .env
echo 'TURSO_AUTH_TOKEN="..."' >> .env
streamlit run app.py
```

For Streamlit Community Cloud, use Python 3.12 and add
`TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` in the app's Secrets settings.
