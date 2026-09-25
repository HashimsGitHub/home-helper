# Home Helper

Home Helper is a mobile-friendly household organiser for groceries,
appointments, and tasks. The native web app is served as static files by Azure
Static Web Apps; its Azure Functions API connects to the existing Turso
database. The deployed app does not load or call Streamlit.

## Run Locally

Requirements: Node.js 20 or later, Azure Static Web Apps CLI, and Azure
Functions Core Tools v4.

Install the API dependencies:

```sh
npm --prefix api install
```

Create or update the repository-root `.env` with the existing Turso connection
values and a new session-signing secret:

```dotenv
TURSO_DATABASE_URL=libsql://your-database.turso.io
TURSO_AUTH_TOKEN=your-turso-auth-token
SESSION_SECRET=your-random-secret-at-least-32-bytes
```

Generate a session secret locally with:

```sh
node -e "console.log(require('node:crypto').randomBytes(32).toString('base64url'))"
```

For an isolated end-to-end test, start the API against a temporary local
SQLite database in one terminal (the empty token prevents the value in `.env`
from being used):

```sh
TURSO_DATABASE_URL=file:/tmp/homehelper-local.db TURSO_AUTH_TOKEN= SESSION_SECRET="$(node -e "process.stdout.write(require('node:crypto').randomBytes(32).toString('base64url'))")" func start --script-root api --port 7071 --javascript
```

Start the SWA frontend in another terminal:

```sh
swa start web --api-devserver-url http://localhost:7071
```

Open `http://localhost:4280`. To test against Turso instead, add
`SESSION_SECRET` to `.env` and start the Functions host without the temporary
database overrides. **Those local requests read and write the shared Turso
database.** The API creates missing tables and indexes and adds missing
`user_id` columns on first use, matching the existing application's
non-destructive schema setup.

Run the API unit tests and syntax checks:

```sh
npm --prefix api test
node --check api/src/functions/homehelper.js
node --check web/app.js
```

## Azure Static Web Apps

The GitHub Actions workflow on `feature/swa-native-app` deploys `web/` and
`api/`. Add these application settings to the Static Web App before enabling
the branch:

- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`
- `SESSION_SECRET` (at least 32 bytes; use the same value for every deployment
   slot that should share sessions)

Keep the database token and session secret in environment settings, never in
the static `web/` directory. The workflow uses the existing
`AZURE_STATIC_WEB_APPS_API_TOKEN_LIVELY_SAND_094772910` GitHub secret. The API
sets an HTTP-only signed session cookie; the service worker caches only static
files and never caches API responses.

The existing Android TWA points at the Static Web App domain, so it can keep
that domain when the SWA is pointed at this branch. The previous Python and
Streamlit sources remain in the repository for reference during migration, but
the new workflow does not build or deploy them.
