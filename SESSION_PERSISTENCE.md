# Remembered user sessions

Home Helper keeps its existing username and four-digit PIN authentication while
allowing a trusted browser or installed PWA to restore the user automatically.

## How it works

1. A successful login or registration creates a cryptographically random,
   opaque token.
2. The browser stores that token in a `Secure`, `SameSite=Lax` cookie for up to
   30 days. The username, user ID, and PIN are not stored in the cookie.
3. Turso stores only the token's SHA-256 hash, user ID, and expiry time in the
   `homehelper_sessions` table.
4. A new Streamlit session reads the cookie and looks up the active token hash.
5. If the token is valid, the user's ordinary Streamlit session state is
   restored before page navigation is created.
6. Sign-out deletes the database session, removes the cookie, closes the
   session-scoped database connection, and returns to the login screen.

## Failure behaviour

- Missing, invalid, expired, or malformed cookies fall back to the normal login
  screen.
- Expired database sessions are cleaned up when the schema is initialised and
  whenever a new remembered session is issued.
- A token revoked on one device does not sign the user out on another device.
- Cookie persistence is a convenience layer; the existing username/PIN flow
  remains the fallback and continues to work independently.

## Security boundary

The cookie is set from the browser and therefore cannot be `HttpOnly` in this
Streamlit architecture. The random token, server-side hash, expiry, HTTPS-only
cookie, and server-side revocation reduce the risk, but this remains appropriate
only for the low-risk household data described by the project.
