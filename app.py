import streamlit as st
import streamlit.components.v1 as components
import logging

logging.getLogger("streamlit.elements.lib.policies").setLevel(logging.ERROR)

st.set_page_config(
    page_title="Home Helper",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None,
)

# ---------- PWA manifest (keep this — it's the only custom HTML needed) ----------
components.html("""
<script>
(function() {
  const parent = window.parent.document;
  const manifest = {
    "name": "Home Helper",
    "short_name": "HomeHelper",
    "description": "A simple shared home organiser for groceries, appointments and tasks.",
    "start_url": ".",
    "scope": ".",
    "display": "standalone",
    "orientation": "portrait-primary",
    "background_color": "#f7f8f6",
    "theme_color": "#176b5b",
    "icons": [{
      "src": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/1f3e0.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }]
  };
  const blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  parent.querySelectorAll('link[rel="manifest"]').forEach(e => e.remove());
  const link = document.createElement('link');
  link.rel = 'manifest';
  link.href = url;
  parent.head.appendChild(link);
  parent.title = "Home Helper";

  let theme = parent.querySelector('meta[name="theme-color"]');
  if (!theme) {
    theme = parent.createElement('meta');
    theme.name = 'theme-color';
    parent.head.appendChild(theme);
  }
  theme.content = '#176b5b';

  let mobile = parent.querySelector('meta[name="mobile-web-app-capable"]');
  if (!mobile) {
    mobile = parent.createElement('meta');
    mobile.name = 'mobile-web-app-capable';
    mobile.content = 'yes';
    parent.head.appendChild(mobile);
  }
})();
</script>
""", height=0)

# ---------- Define pages (native Streamlit way) ----------
home_page = st.Page(
    "views/home.py",
    title="Home",
    icon="🏠",
    default=True,
)

grocery_page = st.Page(
    "views/grocery.py",
    title="Grocery",
    icon="🛒",
)

appointments_page = st.Page(
    "views/appointments.py",
    title="Appointments",
    icon="📅",
)

tasks_page = st.Page(
    "views/tasks.py",
    title="Tasks",
    icon="✅",
)

# ---------- Register navigation (creates native sidebar menu) ----------
pg = st.navigation(
    [home_page, grocery_page, appointments_page, tasks_page],
    position="top",
)

# ---------- Run the selected page ----------
pg.run()
