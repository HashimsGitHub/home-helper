from datetime import date, datetime

import streamlit as st

from database import get_dashboard
from ui_helpers import due_label, friendly_date, parse_datetime


user_id = st.session_state["user_id"]
username = st.session_state["username"]
today = date.today()
dashboard = get_dashboard(user_id)
groceries = dashboard["groceries"]
appointments = dashboard["appointments"]
tasks = dashboard["tasks"]

pending_grocery = [item for item in groceries if not item[4]]
pending_tasks = [task for task in tasks if not task[5]]
upcoming_appointments = [
    appointment
    for appointment in appointments
    if (parse_datetime(appointment[3]) and parse_datetime(appointment[3]).date() >= today)
]

st.title("Home Helper")
st.caption(datetime.now().strftime("%A, %d %B"))

possessive_name = f"{username}'" if username.lower().endswith("s") else f"{username}'s"
st.subheader(f"{possessive_name} home at a glance")
st.page_link(
    "views/grocery.py",
    label=f"Grocery list · {len(pending_grocery)} to buy",
    icon="🛒",
    use_container_width=True,
)
st.page_link(
    "views/appointments.py",
    label=f"Appointments · {len(upcoming_appointments)} upcoming",
    icon="📅",
    use_container_width=True,
)
st.page_link(
    "views/tasks.py",
    label=f"Tasks · {len(pending_tasks)} to do",
    icon="✅",
    use_container_width=True,
)

st.divider()
st.subheader("Today")

today_appointments = [
    item for item in upcoming_appointments if parse_datetime(item[3]).date() == today
]
today_tasks = [
    item
    for item in pending_tasks
    if parse_datetime(item[4]) and parse_datetime(item[4]).date() <= today
]

if not today_appointments and not today_tasks:
    st.success("Nothing urgent today — you're all caught up.", icon="✨")
else:
    for appointment in today_appointments:
        with st.container(border=True):
            st.caption("APPOINTMENT")
            st.markdown(f"**{appointment[1]}**")
            details = friendly_date(appointment[3], include_time=True)
            if appointment[5]:
                details += f" · {appointment[5]}"
            st.caption(details)

    for task in today_tasks:
        with st.container(border=True):
            st.caption("TASK")
            st.markdown(f"**{task[1]}**")
            st.caption(f"{due_label(task[4])} · {task[3]} priority")

if pending_grocery:
    with st.expander(f"Next grocery items ({min(3, len(pending_grocery))})"):
        for item in pending_grocery[:3]:
            quantity = f" · {item[2]}" if item[2] else ""
            st.write(f"• {item[1]}{quantity}")

