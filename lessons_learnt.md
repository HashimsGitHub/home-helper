
# HomeHelper — Deployment Lessons Learned

> Audience: LLMs and developers deploying this Streamlit app to Streamlit Community Cloud with a Turso (libSQL) backend.
> Purpose: Avoid every bug we already hit. Follow this document literally.

## 0. TL;DR Checklist
- requirements.txt has no non-existent versions (libsql==0.5.3 does NOT exist)
- Streamlit Python version is 3.12 (NOT 3.14)
- streamlit-calendar version is compatible with pinned Streamlit
- .env is in .gitignore; secrets are in Streamlit Cloud Secrets
- database.py reads st.secrets first, .env as fallback
- st.Page paths point to files that exist in GitHub
- New folders (views/) are tracked by git
- No custom CSS hides header[data-testid="stHeader"]
- Use st.navigation + st.Page + st.page_link only
- Checkbox labels are never empty strings

## 1. Invented package versions
libsql==0.5.3 does not exist. Real versions: 0.1.1 - 0.1.11.
Fix: libsql==0.1.11

## 2. Conflicting Streamlit + streamlit-calendar
streamlit-calendar 1.3.0 requires streamlit>=1.42.0.
Fix: streamlit>=1.42.0 + streamlit-calendar>=1.3.1

## 3. Edited requirements.txt but didn't push
Streamlit Cloud pulls from GitHub. Local edits do nothing until git push.
Verify: https://github.com/<user>/<repo>/blob/main/requirements.txt

## 4. App stuck "in the oven"
Streamlit Cloud defaults to newest Python (3.14). Native wheels stall.
Fix: Delete app, redeploy with Python 3.12.

## 5. Secrets only from .env
Cloud does not read .env. Use st.secrets first, .env fallback.

## 6. Committed .env with real tokens
Never commit .env. Rotate tokens: turso db tokens create/revoke.

## 7. turso:// scheme with libsql client
libsql expects libsql://. Normalize the URL.

## 8. Homepage with instructions, no navigation
Anti-pattern. Use st.metric + st.page_link dashboard.

## 9. st.navigation + pages/ folder = broken nav
Pick one. Recommended: views/ folder with st.Page + st.navigation.

## 10. st.Page("views/grocery.py") fails on cloud
File existed locally but not pushed. Run git add -A, verify git ls-files views/.

## 11. Hiding header[data-testid="stHeader"] removes hamburger
Hide only #MainMenu, footer, stToolbar, stDecoration. Never the header.

## 12. Empty label="" on widgets
Will become a hard error. Use hidden non-empty labels.

## 13. Deprecated st.components.v1.html
Removed after 2026-06-01. Use only for PWA manifest injection temporarily.

## 14. WSL file-watching warning
Informational only. Install watchdog for speed. No effect on cloud.

## 15. Correct setup
home-helper/
  app.py, database.py, requirements.txt, .gitignore, .env
  .streamlit/config.toml
  views/{home,grocery,appointments,tasks}.py

requirements.txt:
  streamlit>=1.42.0
  libsql==0.1.11
  python-dotenv==1.0.1
  streamlit-calendar>=1.3.1
  pandas>=2.2.0

## 16. Do Not Do
- Do not invent package versions
- Do not use Python 3.14 on Streamlit Cloud
- Do not commit .env
- Do not mix st.navigation with pages/ auto-routing
- Do not hide the Streamlit header
- Do not pass label="" to widgets

## 17. Do Do
- Check PyPI for real versions
- Use Python 3.12 on Streamlit Cloud
- Put secrets in Streamlit Cloud Secrets UI
- Use st.navigation + st.Page + st.page_link
- Show live data on home page, not instructions
- Rotate leaked tokens immediately

## 18. Debugging Cheat Sheet
| Symptom | First check |
|---|---|
| "Could not find a version" | Is version real on PyPI? |
| "Conflicting dependencies" | Compatible pins? |
| Stuck "in the oven" | Python 3.12? Delete+redeploy |
| StreamlitPageNotFoundError | File in GitHub? git ls-files |
| Hamburger missing | Hiding stHeader or mixing nav? |
| Secret is None | In st.secrets, not just .env? |
| Buttons dead on mobile | Using st.page_link? |

## 19. When to Use Custom HTML
Legit: PWA manifest, third-party JS with no Streamlit equivalent.
Never: navigation, layout, clickable cards, app shell styling.
Rule: if Streamlit has a native widget, use it.

## 20. Community Cloud stalls with inotify instance limit reached
Streamlit's development file watcher can exhaust the Linux container's
`inotify` handles and repeatedly log `OSError: [Errno 24] inotify instance
limit reached`. Production Community Cloud does not need hot source reload.

Fix in `.streamlit/config.toml`:

```toml
[server]
headless = true
fileWatcherType = "none"
runOnSave = false
```

The non-theme configuration change takes effect after Streamlit restarts or a
new Community Cloud deployment begins.

## 21. Prefer session-only login for this app
`st.session_state` is tied to a Streamlit connection and is reset when the PWA,
tab, or browser creates a new session. For this small household app, asking for
the short username and PIN again is faster and more reliable than loading a
custom browser-cookie component and querying persistent session tokens.

Never use `st.cache_data` as proof of identity because cached data can be
shared. Use it only for user-keyed database reads. Concurrent logins are safe:
two devices using the same username and PIN receive the same `user_id`, while
each device keeps its own independent Streamlit session and database connection.
