import streamlit as st
from datetime import datetime
from database import get_grocery, get_appointments, get_tasks

st.markdown("## 🏠 HomeHelper")

groceries = get_grocery()
appointments = get_appointments()
tasks = get_tasks()

pending_grocery = sum(1 for g in groceries if not g[4])
pending_tasks = sum(1 for t in tasks if not t[5])

today = datetime.now().date()
upcoming_appts = [
    a for a in appointments
    if datetime.fromisoformat(a[3]).date() >= today
]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🛒 Grocery", pending_grocery, help="Pending items")
    st.page_link("views/grocery.py", label="Open Grocery", icon="🛒")

with col2:
    st.metric("📅 Appointments", len(upcoming_appts), help="Upcoming")
    st.page_link("views/appointments.py", label="Open Calendar", icon="📅")

with col3:
    st.metric("✅ Tasks", pending_tasks, help="Pending tasks")
    st.page_link("views/tasks.py", label="Open Tasks", icon="✅")

st.divider()

st.markdown("### 🛒 Next up")
pending_items = [g for g in groceries if not g[4]][:3]
if not pending_items:
    st.caption("_Nothing on the list_")
else:
    for rid, item, qty, cat, purchased, _ in pending_items:
        st.markdown(f"• {item}" + (f" — {qty}" if qty else ""))

st.markdown("### 📅 Upcoming")
if not upcoming_appts:
    st.caption("_No upcoming appointments_")
else:
    for a in upcoming_appts[:3]:
        dt = datetime.fromisoformat(a[3])
        st.markdown(f"• **{dt.strftime('%a %d %b, %H:%M')}** — {a[1]}")

st.markdown("### ✅ To do")
pending = [t for t in tasks if not t[5]][:3]
if not pending:
    st.caption("_All caught up_")
else:
    for t in pending:
        icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(t[3], "")
        st.markdown(f"• {icon} {t[1]}")
