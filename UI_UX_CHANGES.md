# Mobile UI/UX redesign

## What changed

- Replaced sidebar-only navigation with native top navigation so all four areas
  remain discoverable on a phone.
- Reworked the home page into a task-focused dashboard with full-width links,
  an urgent "Today" section, and a short grocery preview.
- Moved add forms into collapsed expanders to keep the primary lists visible.
- Separated active and completed grocery items and tasks into tabs.
- Sorted open tasks by due date and then priority.
- Made appointments list-first on mobile, with the calendar as a secondary tab.
- Added plain-language date labels such as "Due today" and "Overdue".
- Moved delete controls into native action popovers to reduce accidental taps.
- Improved empty, success, and validation states.
- Updated the colour theme and PWA metadata for a calmer home-oriented visual
  identity.
- Added the supplied HomeImage photograph as a responsive full-screen
  background with a white readability veil and subtly translucent content
  surfaces.

## Lessons-learned constraints preserved

- Uses `st.navigation`, `st.Page`, and `st.page_link` only.
- Keeps the Streamlit header visible.
- Uses non-empty accessible labels for every widget.
- Does not add a `pages/` directory or mix navigation systems.
- Uses native Streamlit navigation, layout, and interactive controls; the only
  added presentation override is the requested background styling.
- Reads Streamlit Cloud Secrets first, with `.env` as the local fallback.
- Keeps `libsql==0.1.11` and Python 3.12 compatibility.

## Validation completed

- Python compilation and AST parsing for every Python file.
- JSON parsing for the PWA manifest.
- Local libSQL create/read/write smoke test.
- Streamlit widget-tree execution for grocery, task, and appointment pages.
- Streamlit server startup on Python 3.12 with the declared dependencies.
