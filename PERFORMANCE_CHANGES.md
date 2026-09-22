# Performance improvements

The app keeps Turso and reduces avoidable work in the Streamlit execution path.

## Database

- Reuses one libSQL connection per Streamlit user session instead of opening
  and closing a connection for every query.
- Closes the session connection when the user signs out.
- Loads groceries, appointments, and tasks for the home dashboard with one
  `UNION ALL` query instead of three separate remote queries.
- Caches user-keyed list and dashboard reads for five seconds.
- Immediately clears the relevant list and dashboard caches after a write, so
  the user still sees their change without waiting for the cache to expire.
- Preserves `user_id` filters on every read, update, and delete operation.

## Streamlit reruns

- Removes explicit `st.rerun()` calls after adding groceries, appointments,
  and tasks. The updated list is fetched later in the same form-submission run.
- Uses `on_change` callbacks for completion checkboxes.
- Uses `on_click` callbacks for delete actions.
- Registration, login, and sign-out retain their necessary reruns because they
  change the available navigation and authenticated session.

## Expected effect

- Repeated page renders within five seconds normally avoid a database read.
- Home dashboard database reads are reduced from three requests to one.
- Add, toggle, and delete actions redraw once instead of triggering an extra
  manual rerun.
- A typical signed-in session creates one reusable database connection rather
  than one connection per operation.

Streamlit Community Cloud cold starts after inactivity are controlled by the
hosting platform and cannot be removed by application code.

## Production file watcher

The Streamlit source-code file watcher is disabled in production with
`server.fileWatcherType = "none"`. This prevents Linux `inotify` exhaustion
from stalling the app and does not affect GitHub-triggered Community Cloud
deployments.
