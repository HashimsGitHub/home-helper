import streamlit as st
import streamlit.components.v1 as components
import logging

# Silence noisy warnings in console
logging.getLogger("streamlit.elements.lib.policies").setLevel(logging.ERROR)

st.set_page_config(
    page_title="HomeHelper",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None,
)

# ---------- PWA manifest + iOS meta tags ----------
components.html("""
<script>
(function() {
  const parent = window.parent.document;

  // --- Manifest ---
  const manifest = {
    "name": "HomeHelper",
    "short_name": "HomeHelper",
    "description": "Grocery, appointments, and tasks in one place.",
    "start_url": ".",
    "scope": ".",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#ffffff",
    "theme_color": "#0ea5e9",
    "icons": [
      {
        "src": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e0.png",
        "sizes": "72x72",
        "type": "image/png"
      },
      {
        "src": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e0.png",
        "sizes": "192x192",
        "type": "image/png",
        "purpose": "any maskable"
      },
      {
        "src": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3e0.png",
        "sizes": "512x512",
        "type": "image/png",
        "purpose": "any maskable"
      }
    ]
  };
  const blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  parent.querySelectorAll('link[rel="manifest"]').forEach(e => e.remove());
  const link = document.createElement('link');
  link.rel = 'manifest';
  link.href = url;
  parent.head.appendChild(link);

  // --- Title (overrides "Streamlit" in tab / PWA name) ---
  parent.title = "HomeHelper";

  // --- Meta tags ---
  const metas = [
    ['apple-mobile-web-app-capable', 'yes'],
    ['mobile-web-app-capable', 'yes'],
    ['apple-mobile-web-app-status-bar-style', 'default'],
    ['apple-mobile-web-app-title', 'HomeHelper'],
    ['application-name', 'HomeHelper'],
    ['theme-color', '#0ea5e9'],
    ['viewport', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover']
  ];
  metas.forEach(([n, c]) => {
    let m = parent.querySelector(`meta[name="${n}"]`);
    if (!m) { m = document.createElement('meta'); m.name = n; parent.head.appendChild(m); }
    m.content = c;
  });
})();
</script>
""", height=0)

# ---------- Global mobile-friendly CSS ----------
st.markdown("""
<style>
/* Tighten Streamlit's default padding on mobile */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 4rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
    max-width: 100% !important;
}

/* Hide the Streamlit header/footer chrome */
header[data-testid="stHeader"] { display: none !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* Bigger touch targets for buttons */
.stButton > button {
    min-height: 44px !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
}

/* Checkbox hit area */
.stCheckbox {
    padding: 0.4rem 0 !important;
}
.stCheckbox input {
    width: 22px !important;
    height: 22px !important;
}

/* Inputs: larger, touch-friendly */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input {
    min-height: 44px !important;
    font-size: 1rem !important;
    border-radius: 10px !important;
}

/* Tabs bigger */
.stTabs [data-baseweb="tab"] {
    font-size: 0.95rem !important;
    padding: 0.6rem 1rem !important;
}

/* Compact metric cards */
[data-testid="stMetric"] {
    background: #f8fafc;
    padding: 0.8rem;
    border-radius: 12px;
}

/* Sidebar nav styling */
section[data-testid="stSidebar"] {
    background-color: #f8fafc;
}
section[data-testid="stSidebar"] .st-emotion-cache-1cypcdb {
    padding-top: 1rem;
}

/* Headings */
h1 { font-size: 1.6rem !important; margin-top: 0.5rem !important; }
h2 { font-size: 1.3rem !important; }
h3 { font-size: 1.1rem !important; }

/* Responsive columns: stack on narrow screens */
@media (max-width: 640px) {
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------- App ----------
# Since we removed the homepage, send users straight to Grocery.
# Streamlit auto-detects pages/ folder, so we only show a small header here.
st.title("🏠 HomeHelper")
st.caption("Grocery · Appointments · Tasks")

# Quick stats (optional, mobile-friendly)
from database import init_db, get_grocery, get_appointments, get_tasks

if "db_ready" not in st.session_state:
    init_db()
    st.session_state.db_ready = True

groceries = get_grocery()
appointments = get_appointments()
tasks = get_tasks()

pending_grocery = sum(1 for g in groceries if not g[4])
pending_tasks = sum(1 for t in tasks if not t[5])

c1, c2, c3 = st.columns(3)
c1.metric("🛒", pending_grocery, help="Pending groceries")
c2.metric("📅", len(appointments), help="Appointments")
c3.metric("✅", pending_tasks, help="Pending tasks")

st.markdown("---")
st.info("👉 **Tap ☰ (top-left) to open the menu and switch between Grocery, Appointments, and Tasks.**", icon="📱")