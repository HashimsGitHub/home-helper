import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import logging

logging.getLogger("streamlit.elements.lib.policies").setLevel(logging.ERROR)

st.set_page_config(
    page_title="HomeHelper",
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
    "name": "HomeHelper",
    "short_name": "HomeHelper",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#0ea5e9",
    "icons": [{
      "src": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e0.png",
      "sizes": "192x192",
      "type": "image/png",
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
  parent.title = "HomeHelper";
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
    position="sidebar",   # native sidebar menu
)

# ---------- Run the selected page ----------
pg.run()