from datetime import datetime, date, time
import streamlit as st
from streamlit_calendar import calendar
from database import add_appointment, get_appointments, delete_appointment

st.set_page_config(page_title="Appointments · HomeHelper", page_icon="📅", layout="centered")
st.title("📅 Appointments")

with st.expander("➕ New Appointment", expanded=False):
    with st.form("add_appt", clear_on_submit=True):
        title = st.text_input("Title*", placeholder="Dentist visit")
        desc = st.text_area("Notes", placeholder="Optional", height=80)

        d = st.date_input("Date", value=date.today())
        c1, c2 = st.columns(2)
        start_t = c1.time_input("Start", value=time(9, 0))
        end_t = c2.time_input("End", value=time(10, 0))
        loc = st.text_input("Location", placeholder="Optional")

        if st.form_submit_button("Save", use_container_width=True, type="primary"):
            if title.strip():
                start_dt = datetime.combine(d, start_t).isoformat()
                end_dt = datetime.combine(d, end_t).isoformat()
                add_appointment(title.strip(), desc.strip(), start_dt, end_dt, loc.strip())
                st.success("Saved!")
                st.rerun()
            else:
                st.warning("Title is required.")

rows = get_appointments()
events = [{
    "id": str(r[0]),
    "title": r[1],
    "start": r[3],
    "end": r[4] or r[3],
    "description": r[2] or "",
    "location": r[5] or "",
} for r in rows]

calendar_options = {
    "headerToolbar": {
        "left": "prev,next",
        "center": "title",
        "right": "today",
    },
    "initialView": "listMonth",     # list view is best on mobile
    "height": "auto",
    "contentHeight": "auto",
    "editable": False,
    "selectable": False,
}

calendar(events=events, options=calendar_options, custom_css="""
    .fc { font-size: 0.9rem; }
    .fc-toolbar-title { font-size: 1.1rem !important; }
""")

st.subheader("📋 All Appointments")
if not rows:
    st.info("No appointments scheduled.")
else:
    for rid, title, desc, start, end, loc in rows:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(f"🕒 {start} → {end or '?'}" + (f"  |  📍 {loc}" if loc else ""))
            if desc:
                st.write(desc)
            if st.button("🗑️ Delete", key=f"del_appt_{rid}", use_container_width=True):
                delete_appointment(rid)
                st.rerun()