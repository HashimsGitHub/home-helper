import streamlit as st
from database import init_db

st.set_page_config(
    page_title="Home Helper",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="expanded",
)
import streamlit.components.v1 as components

components.html("""
<script>
(function() {
  const manifest = {
    "name": "Home Helper",
    "short_name": "HomeHelper",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#0ea5e9",
    "icons": [{
      "src": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e0.png",
      "sizes": "72x72",
      "type": "image/png"
    }]
  };
  const blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);

  // Remove any existing manifest
  document.querySelectorAll('link[rel="manifest"]').forEach(e => e.remove());
  const link = document.createElement('link');
  link.rel = 'manifest';
  link.href = url;
  document.head.appendChild(link);

  // iOS meta tags
  const metas = [
    ['apple-mobile-web-app-capable', 'yes'],
    ['apple-mobile-web-app-status-bar-style', 'default'],
    ['apple-mobile-web-app-title', 'HomeHelper'],
    ['theme-color', '#0ea5e9'],
    ['viewport', 'width=device-width, initial-scale=1, maximum-scale=1']
  ];
  metas.forEach(([n, c]) => {
    let m = document.querySelector(`meta[name="${n}"]`);
    if (!m) { m = document.createElement('meta'); m.name = n; document.head.appendChild(m); }
    m.content = c;
  });
})();
</script>
""", height=0)


# Initialize DB once per session
if "db_ready" not in st.session_state:
    init_db()
    st.session_state.db_ready = True

st.title("🏠 Home Helper")
st.caption("Your all-in-one household companion")

st.markdown("""
### What would you like to do?

Use the **sidebar** to navigate:

| Page | Purpose |
|------|---------|
| 🛒 **Grocery** | Manage your shopping list |
| 📅 **Appointments** | Schedule & view appointments on a calendar |
| ✅ **Tasks** | Track your to-do items |
""")

st.info("💡 **Tip:** Install this app on your phone! Open the browser menu and select **'Add to Home Screen'** to use it as a Progressive Web App.")

col1, col2, col3 = st.columns(3)
col1.metric("🛒 Grocery", "→", "Shopping")
col2.metric("📅 Appointments", "→", "Calendar")
col3.metric("✅ Tasks", "→", "To-Do")