import streamlit as st
from database import add_grocery, get_grocery, toggle_grocery, delete_grocery

#st.set_page_config(page_title="Grocery · HomeHelper", page_icon="🛒")
st.title("🛒 Grocery")

with st.form("add_grocery", clear_on_submit=True):
    item = st.text_input("Item", placeholder="e.g. Milk")
    c1, c2 = st.columns(2)
    qty = c1.text_input("Qty", placeholder="1 L")
    cat = c2.selectbox(
        "Category",
        ["General", "Produce", "Dairy", "Meat", "Bakery", "Frozen", "Other"],
    )
    if st.form_submit_button("➕ Add Item", use_container_width=True, type="primary"):
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
        # Two-row layout per item for mobile
        c1, c2 = st.columns([0.15, 0.85])
        checked = c1.checkbox(
            f"Mark {item} as purchased",
            value=bool(purchased),
            key=f"chk_{rid}",
            label_visibility="collapsed",
        )
        if checked != bool(purchased):
            toggle_grocery(rid)
            st.rerun()

        with c2:
            text = f"~~{item}~~" if purchased else f"**{item}**"
            meta = []
            if qty:
                meta.append(f"_{qty}_")
            if cat and cat != "General":
                meta.append(f"`{cat}`")
            st.markdown(text + ("  \n" + " · ".join(meta) if meta else ""))

        if st.button("🗑️ Remove", key=f"del_{rid}", use_container_width=True):
            delete_grocery(rid)
            st.rerun()

        st.markdown("---")