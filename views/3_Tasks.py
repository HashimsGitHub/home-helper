from datetime import date
import streamlit as st
from database import add_task, get_tasks, toggle_task, delete_task

#st.set_page_config(page_title="Tasks · HomeHelper", page_icon="✅")
st.title("✅ Tasks")

PRIORITY_ICON = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

with st.form("add_task", clear_on_submit=True):
    title = st.text_input("Task*", placeholder="e.g. Change light bulb")
    desc = st.text_area("Notes", placeholder="Optional", height=80)
    c1, c2 = st.columns(2)
    priority = c1.selectbox("Priority", ["Low", "Medium", "High"], index=1)
    due = c2.date_input("Due date", value=date.today())

    if st.form_submit_button("➕ Add Task", use_container_width=True, type="primary"):
        if title.strip():
            add_task(title.strip(), desc.strip(), priority, due.isoformat())
            st.toast("Task added!", icon="✅")
            st.rerun()
        else:
            st.warning("Task title is required.")

st.divider()

rows = get_tasks()
if not rows:
    st.info("No tasks yet.")
else:
    for rid, title, desc, priority, due, completed in rows:
        c1, c2 = st.columns([0.15, 0.85])
        checked = c1.checkbox(
            f"Mark {title} as completed",
            value=bool(completed),
            key=f"task_{rid}",
            label_visibility="collapsed",
        )
        if checked != bool(completed):
            toggle_task(rid)
            st.rerun()

        with c2:
            text = f"~~{title}~~" if completed else f"**{title}**"
            st.markdown(text)
            meta = []
            if priority:
                meta.append(f"{PRIORITY_ICON.get(priority,'')} {priority}")
            if due:
                meta.append(f"📅 {due}")
            if meta:
                st.caption(" · ".join(meta))
            if desc:
                st.caption(desc)

        if st.button("🗑️ Delete", key=f"deltask_{rid}", use_container_width=True):
            delete_task(rid)
            st.rerun()

        st.markdown("---")