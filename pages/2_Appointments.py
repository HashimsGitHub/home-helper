from datetime import datetime, date, time
import streamlit as st
from streamlit_calendar import calendar
from database import add_appointment, get_appointments, delete_appointment

st.set_page_config(page_title="Appointments · Home Helper", page_icon="📅", layout="wide")
st.title("📅 Appointments")

# ---------- Add form ----------
with st.expander("➕ Schedule a new appointment", expanded=False):
    with st.form("add_appt", clear_on_submit=True):
        title = st.text_input("Title*", placeholder="Dentist visit")
        desc  = st.text_area("Description", placeholder="Optional notes")
        col1, col2 = st.columns(2)
        d = col1.date_input("Date", value=date.today())
        start_t = col2.time_input("Start time", value=time(9, 0))
        col3, col4 = st.columns(2)
        end_t = col3.time_input("End time", value=time(10, 0))
        loc = col4.text_input("Location", placeholder="Optional")
        if st.form_submit_button("Save", use_container_width=True):
            if title.strip():
                start_dt = datetime.combine(d, start_t).isoformat()
                end_dt   = datetime.combine(d, end_t).isoformat()
                add_appointment(title.strip(), desc.strip(), start_dt, end_dt, loc.strip())
                st.success("Appointment saved!")
                st.rerun()
            else:
                st.warning("Title is required.")

# ---------- Calendar ----------
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
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,listWeek",
    },
    "initialView": "dayGridMonth",
    "selectable": False,
    "editable": False,
    "height": 600,
}

calendar(events=events, options=calendar_options)

# ---------- Manage list ----------
st.subheader("📋 Upcoming Appointments")
if not rows:
    st.info("No appointments scheduled.")
else:
    for rid, title, desc, start, end, loc in rows:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"**{title}**")
                st.caption(f"🕒 {start} → {end or '?'}" + (f"  |  📍 {loc}" if loc else ""))
                if desc:
                    st.write(desc)
            if c2.button("🗑️", key=f"del_appt_{rid}"):
                delete_appointment(rid)
                st.rerun()