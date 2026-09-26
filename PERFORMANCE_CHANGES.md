# Performance improvements

The app keeps Turso connections reusable and reduces avoidable work in its
Streamlit and Azure Static Web Apps execution paths.

## Database

- Reuses one libSQL connection per Streamlit user session instead of opening
  and closing a connection for every query.
- Closes the session connection when the user signs out.
- Loads groceries, appointments, and tasks for the home dashboard with one
  `UNION ALL` query instead of three separate remote queries.
- Reuses the dashboard cache on category pages to avoid another Turso read
  when navigating while that five-second cache is warm.
- Caches user-keyed list and dashboard reads for five seconds.
- Immediately clears the relevant list and dashboard caches after a write, so
  the user still sees their change without waiting for the cache to expire.
- Preserves `user_id` filters on every read, update, and delete operation.
- Avoids persistent-login cookie components and session-token database queries.
- Supports concurrent sessions for the same `user_id`, allowing multiple
  devices to share the same centrally stored records.

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

## Azure Static Web App

- Reuses the dashboard response in browser memory for five seconds across Home
  and category navigation. Expired data falls back to the existing category
  endpoint.
- Clears the browser cache after writes and authentication changes.
- Reuses one module-scoped libSQL client in each Azure Functions worker.

## Production file watcher

The Streamlit source-code file watcher is disabled in production with
`server.fileWatcherType = "none"`. This prevents Linux `inotify` exhaustion
from stalling the app and does not affect GitHub-triggered Community Cloud
deployments.
