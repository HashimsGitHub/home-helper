from datetime import date, datetime, time

import streamlit as st
from streamlit_calendar import calendar

from database import add_appointment, delete_appointment, get_dashboard
from ui_helpers import friendly_date, parse_datetime


USER_ID = st.session_state["user_id"]


def render_appointment(row):
    rid, title, description, start, end, location = row
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(friendly_date(start, include_time=True))
        if location:
            st.caption(f"📍 {location}")
        if description:
            st.write(description)
        st.button(
            "Delete",
            key=f"delete_appointment_{rid}",
            use_container_width=True,
            on_click=delete_appointment,
            args=(USER_ID, rid),
        )


st.page_link("views/home.py", label="Home", icon="🏠")
st.title("Appointments")
st.caption("See upcoming commitments without hunting through the calendar.")

with st.expander("Add appointment", icon="➕", expanded=False):
    with st.form("add_appointment", clear_on_submit=True):
        title = st.text_input("Title", placeholder="Dentist visit", autocomplete="off")
        appointment_date = st.date_input("Date", value=date.today())
        start_time = st.time_input("Start time", value=time(9, 0))
        end_time = st.time_input("End time", value=time(10, 0))
        location = st.text_input("Location", placeholder="Optional", autocomplete="off")
        description = st.text_area("Notes", placeholder="Optional details", height=80)
        submitted = st.form_submit_button("Save appointment", use_container_width=True, type="primary")

        if submitted:
            start = datetime.combine(appointment_date, start_time)
            end = datetime.combine(appointment_date, end_time)
            if not title.strip():
                st.warning("Enter an appointment title.")
            elif end <= start:
                st.warning("End time must be after the start time.")
            else:
                add_appointment(
                    USER_ID,
                    title.strip(),
                    description.strip(),
                    start.isoformat(),
                    end.isoformat(),
                    location.strip(),
                )
                st.toast("Appointment saved", icon="✅")

rows = get_dashboard(USER_ID)["appointments"]
today = date.today()
# Parse each appointment date once, then retain the original upcoming/past order.
dated_rows = [(row, parse_datetime(row[3])) for row in rows]
upcoming = [row for row, start in dated_rows if start and start.date() >= today]
past = [row for row, start in dated_rows if start and start.date() < today]

upcoming_tab, calendar_tab = st.tabs([f"Upcoming ({len(upcoming)})", "Calendar"])

with upcoming_tab:
    if not upcoming:
        st.info("No upcoming appointments.")
    for row in upcoming:
        render_appointment(row)

    if past:
        with st.expander(f"Past appointments ({len(past)})"):
            for row in reversed(past):
                render_appointment(row)

with calendar_tab:
    events = [
        {
            "id": str(row[0]),
            "title": row[1],
            "start": row[3],
            "end": row[4] or row[3],
            "description": row[2] or "",
            "location": row[5] or "",
        }
        for row in rows
    ]
    calendar(
        events=events,
        options={
            "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"},
            "initialView": "listMonth",
            "height": "auto",
            "contentHeight": "auto",
            "editable": False,
            "selectable": False,
        },
        custom_css="""
            .fc { font-size: 0.9rem; }
            .fc .fc-toolbar { gap: 0.5rem; }
            .fc .fc-toolbar-title { font-size: 1rem !important; }
            .fc .fc-button { min-height: 40px; }
        """,
    )
