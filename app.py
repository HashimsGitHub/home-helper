import logging

import streamlit as st
import streamlit.components.v1 as components

from database import (
    UsernameTakenError,
    authenticate_user,
    close_session_connection,
    create_user,
    init_db,
)

logging.getLogger("streamlit.elements.lib.policies").setLevel(logging.ERROR)

st.set_page_config(
    page_title="Home Helper",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items=None,
)

if not st.session_state.get("_database_ready"):
    init_db()
    st.session_state["_database_ready"] = True

# ---------- Responsive background ----------
# A strong white veil keeps text and controls readable while allowing the
# supplied home image to give the app a warmer visual identity.
st.markdown(
    """
    <style>
        .stApp {
            background-image:
                linear-gradient(
                    rgba(255, 255, 255, 0.80),
                    rgba(255, 255, 255, 0.80)
                ),
                url("https://myresearchdata.blob.core.windows.net/home-helper/HomeImage.jpg");
            background-repeat: no-repeat;
            background-position: center center;
            background-size: cover;
            background-attachment: fixed;
        }

        /* Keep native controls visually distinct from the photograph. */
        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stAlert"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: rgba(255, 255, 255, 0.78);
            backdrop-filter: blur(3px);
            -webkit-backdrop-filter: blur(3px);
            border-radius: 0.75rem;
        }

        /* Clearly separate example/placeholder text from entered user data. */
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            color: #17211f !important;
            -webkit-text-fill-color: #17211f !important;
        }

        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder {
            color: #8a9490 !important;
            -webkit-text-fill-color: #8a9490 !important;
            opacity: 1 !important;
        }

        @media (max-width: 768px) {
            .stApp {
                background-position: 58% center;
                background-attachment: scroll;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
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


def _valid_pin(pin):
    return len(pin) == 4 and pin.isdigit()


def _sign_in(user_row):
    st.session_state["user_id"] = user_row[0]
    st.session_state["username"] = user_row[1]


def authentication_page():
    st.title("Welcome home")
    st.caption("Sign in to see your private household lists.")

    login_tab, register_tab = st.tabs(["Sign in", "Register"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input(
                "User name",
                placeholder="Your name",
                autocomplete="username",
                key="login_username",
            )
            pin = st.text_input(
                "4-digit PIN",
                type="password",
                max_chars=4,
                autocomplete="current-password",
                key="login_pin",
            )
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if not username.strip() or not _valid_pin(pin):
                    st.warning("Enter your user name and four-digit PIN.")
                else:
                    user = authenticate_user(username, pin)
                    if user:
                        _sign_in(user)
                        st.rerun()
                    else:
                        st.error("The user name or PIN is incorrect.")

    with register_tab:
        st.caption("Choose a unique name and a PIN you can remember.")
        with st.form("registration_form"):
            new_username = st.text_input(
                "User name",
                placeholder="e.g. Uzma",
                max_chars=30,
                autocomplete="username",
                key="registration_username",
            )
            new_pin = st.text_input(
                "Choose a 4-digit PIN",
                type="password",
                max_chars=4,
                autocomplete="new-password",
                key="registration_pin",
            )
            registered = st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True,
            )

            if registered:
                clean_name = new_username.strip()
                if len(clean_name) < 2:
                    st.warning("User name must contain at least two characters.")
                elif not _valid_pin(new_pin):
                    st.warning("PIN must contain exactly four numbers.")
                else:
                    try:
                        user_id = create_user(clean_name, new_pin)
                        _sign_in((user_id, clean_name))
                        st.rerun()
                    except UsernameTakenError:
                        st.error("That user name is already registered.")


if "user_id" not in st.session_state:
    auth_page = st.Page(
        authentication_page,
        title="Sign in",
        icon="🔐",
        default=True,
    )
    st.navigation([auth_page], position="hidden").run()
    st.stop()

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

signed_in_col, logout_col = st.columns([0.72, 0.28], vertical_alignment="center")
signed_in_col.caption(f"Signed in as **{st.session_state['username']}**")
if logout_col.button("Sign out", use_container_width=True):
    close_session_connection()
    st.session_state.pop("user_id", None)
    st.session_state.pop("username", None)
    for auth_key in (
        "login_username",
        "login_pin",
        "registration_username",
        "registration_pin",
    ):
        st.session_state.pop(auth_key, None)
    st.rerun()

# ---------- Register native top navigation ----------
pg = st.navigation(
    [home_page, grocery_page, appointments_page, tasks_page],
    position="top",
)

# ---------- Run the selected page ----------
pg.run()
