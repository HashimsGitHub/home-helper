from datetime import date
import streamlit as st
from database import add_task, get_tasks, toggle_task, delete_task

st.set_page_config(page_title="Tasks · Home Helper", page_icon="✅")
st.title("✅ To-Do Tasks")

with st.form("add_task", clear_on_submit=True):
    title = st.text_input("Task*", placeholder="e.g. Change light bulb")
    desc  = st.text_area("Notes", placeholder="Optional")
    col1, col2 = st.columns(2)
    priority = col1.selectbox("Priority", ["Low", "Medium", "High"])
    due      = col2.date_input("Due date", value=date.today())
    if st.form_submit_button("➕ Add Task", use_container_width=True):
        if title.strip():
            add_task(title.strip(), desc.strip(), priority, due.isoformat())
            st.toast("Task added!", icon="✅")
            st.rerun()
        else:
            st.warning("Task title is required.")

st.divider()

PRIORITY_ICON = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

rows = get_tasks()
if not rows:
    st.info("No tasks yet.")
else:
    for rid, title, desc, priority, due, completed in rows:
        cols = st.columns([0.5, 4, 1.5, 1.5, 0.8])
        checked = cols[0].checkbox("", value=bool(completed), key=f"task_{rid}", label_visibility="collapsed")
        if checked != bool(completed):
            toggle_task(rid)
            st.rerun()

        text = f"~~{title}~~" if completed else title
        cols[1].markdown(f"**{text}**" + (f"  \n_{desc}_" if desc else ""))
        cols[2].markdown(f"{PRIORITY_ICON.get(priority,'')} {priority}")
        cols[3].markdown(f"📅 {due or '—'}")

        if cols[4].button("🗑️", key=f"deltask_{rid}"):
            delete_task(rid)
            st.rerun()