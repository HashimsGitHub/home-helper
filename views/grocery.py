import streamlit as st

from database import add_grocery, delete_grocery, get_grocery, toggle_grocery


CATEGORIES = ["General", "Produce", "Dairy", "Meat", "Bakery", "Frozen", "Other"]
USER_ID = st.session_state["user_id"]


def render_item(row):
    rid, item, quantity, category, purchased, _ = row
    with st.container(border=True):
        check_col, detail_col, action_col = st.columns([0.14, 0.66, 0.20])
        check_col.checkbox(
            f"Mark {item} as purchased",
            value=bool(purchased),
            key=f"grocery_status_{rid}",
            label_visibility="collapsed",
            on_change=toggle_grocery,
            args=(USER_ID, rid),
        )

        with detail_col:
            st.markdown(f"~~{item}~~" if purchased else f"**{item}**")
            details = [value for value in (quantity, category if category != "General" else "") if value]
            if details:
                st.caption(" · ".join(details))

        with action_col:
            with st.popover("More", use_container_width=True):
                st.button(
                    "Delete item",
                    key=f"delete_grocery_{rid}",
                    use_container_width=True,
                    on_click=delete_grocery,
                    args=(USER_ID, rid),
                )


st.page_link("views/home.py", label="Home", icon="🏠")
st.title("Grocery list")
st.caption("Keep the household shopping list in one place.")

with st.expander("Add grocery item", icon="➕", expanded=False):
    with st.form("add_grocery", clear_on_submit=True):
        item = st.text_input("Item", placeholder="Milk", autocomplete="off")
        quantity = st.text_input("Quantity", placeholder="1 litre", autocomplete="off")
        category = st.selectbox("Category", CATEGORIES)
        submitted = st.form_submit_button("Add to list", use_container_width=True, type="primary")

        if submitted:
            if item.strip():
                add_grocery(USER_ID, item.strip(), quantity.strip(), category)
                st.toast(f"Added {item.strip()}", icon="✅")
            else:
                st.warning("Enter an item name.")

rows = get_grocery(USER_ID)
active = [row for row in rows if not row[4]]
purchased = [row for row in rows if row[4]]

to_buy_tab, purchased_tab = st.tabs([f"To buy ({len(active)})", f"Purchased ({len(purchased)})"])

with to_buy_tab:
    if not active:
        st.success("Your list is clear.", icon="✅")
    for row in active:
        render_item(row)

with purchased_tab:
    if not purchased:
        st.info("Purchased items will appear here.")
    for row in purchased:
        render_item(row)
