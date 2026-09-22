# Home Helper

A mobile-first Streamlit Progressive Web App (PWA) for managing grocery lists,
appointments, and household tasks from one simple dashboard.

Backend: **Turso Cloud (libSQL)** — edge-replicated SQLite.

## User accounts

- New users register with a unique user name and four-digit PIN.
- A successful registration signs the user in immediately.
- Grocery items, appointments, and tasks are filtered by the authenticated
  database user ID.
- Update and delete queries also verify ownership, preventing one user from
  changing another user's records by ID.
- The home page is personalised, for example, `Uzma's home at a glance`.

This prototype stores PINs as plain text by design. It should therefore only
be used for low-risk household data. Run `python homehelper_turso.py` with the
Turso environment variables configured to list registered users and PINs.

### Existing data after upgrade

At startup, the app automatically adds `user_id` to installations created
before user accounts were introduced. Existing rows are deliberately left
unassigned and hidden because the app cannot safely infer their owner. Assign
them manually in Turso after the intended user has registered:

```sql
SELECT id, username FROM homehelper_users;
UPDATE grocery SET user_id = 1 WHERE user_id IS NULL;
UPDATE appointments SET user_id = 1 WHERE user_id IS NULL;
UPDATE tasks SET user_id = 1 WHERE user_id IS NULL;
```

Replace `1` with the correct registered user's ID.

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
