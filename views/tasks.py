from datetime import date

import streamlit as st

from database import add_task, delete_task, get_tasks, toggle_task
from ui_helpers import due_label


PRIORITY_ICON = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}
USER_ID = st.session_state["user_id"]


def render_task(row):
    rid, title, description, priority, due, completed = row
    with st.container(border=True):
        check_col, detail_col, action_col = st.columns([0.14, 0.66, 0.20])
        check_col.checkbox(
            f"Mark {title} as completed",
            value=bool(completed),
            key=f"task_status_{rid}",
            label_visibility="collapsed",
            on_change=toggle_task,
            args=(USER_ID, rid),
        )

        with detail_col:
            st.markdown(f"~~{title}~~" if completed else f"**{title}**")
            st.caption(f"{PRIORITY_ICON.get(priority, '')} {priority} · {due_label(due)}")
            if description:
                st.write(description)

    with action_col:
        st.button(
            "Delete",
            key=f"delete_task_{rid}",
            use_container_width=True,
            on_click=delete_task,
            args=(USER_ID, rid),
        )


st.page_link("views/home.py", label="Home", icon="🏠")
st.title("Tasks")
st.caption("Capture household jobs and see what needs attention first.")

with st.expander("Add task", icon="➕", expanded=False):
    with st.form("add_task", clear_on_submit=True):
        title = st.text_input("Task", placeholder="Change the light bulb", autocomplete="off")
        description = st.text_area("Notes", placeholder="Optional details", height=80)
        priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=1)
        due = st.date_input("Due date", value=date.today())
        submitted = st.form_submit_button("Add task", use_container_width=True, type="primary")

        if submitted:
            if title.strip():
                add_task(USER_ID, title.strip(), description.strip(), priority, due.isoformat())
                st.toast("Task added", icon="✅")
            else:
                st.warning("Enter a task name.")

rows = get_tasks(USER_ID)
active = sorted(
    (row for row in rows if not row[5]),
    key=lambda row: (row[4] or "9999-12-31", PRIORITY_ORDER.get(row[3], 3)),
)
completed = [row for row in rows if row[5]]

todo_tab, done_tab = st.tabs([f"To do ({len(active)})", f"Completed ({len(completed)})"])

with todo_tab:
    if not active:
        st.success("All tasks are complete.", icon="✅")
    for row in active:
        render_task(row)

with done_tab:
    if not completed:
        st.info("Completed tasks will appear here.")
    for row in completed:
        render_task(row)
