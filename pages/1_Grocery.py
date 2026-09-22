import streamlit as st
from database import add_grocery, get_grocery, toggle_grocery, delete_grocery

st.set_page_config(page_title="Grocery · Home Helper", page_icon="🛒")
st.title("🛒 Grocery List")

with st.form("add_grocery", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 1, 1])
    item = col1.text_input("Item", placeholder="e.g. Milk")
    qty  = col2.text_input("Qty", placeholder="1 L")
    cat  = col3.selectbox("Category", ["General", "Produce", "Dairy", "Meat", "Bakery", "Frozen", "Other"])
    if st.form_submit_button("➕ Add", use_container_width=True):
        if item.strip():
            add_grocery(item.strip(), qty.strip(), cat)
            st.toast(f"Added {item}", icon="✅")
            st.rerun()
        else:
            st.warning("Please enter an item.")

st.divider()

rows = get_grocery()
if not rows:
    st.info("Your grocery list is empty. Add something above!")
else:
    for rid, item, qty, cat, purchased, _ in rows:
        cols = st.columns([0.5, 4, 1.5, 1.5, 0.8])
        checked = cols[0].checkbox("", value=bool(purchased), key=f"chk_{rid}", label_visibility="collapsed")
        if checked != bool(purchased):
            toggle_grocery(rid)
            st.rerun()

        text = f"~~{item}~~" if purchased else item
        cols[1].markdown(f"**{text}**" + (f"  \n_{qty}_" if qty else ""))
        cols[2].markdown(f"`{cat}`")

        if cols[4].button("🗑️", key=f"del_{rid}"):
            delete_grocery(rid)
            st.rerun()