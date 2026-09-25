import test from "node:test";
import assert from "node:assert/strict";

import {
  createSession,
  isValidPin,
  isValidUsername,
  sessionCookie,
  sessionFromCookieHeader,
  verifySession,
} from "../src/auth.js";

const secret = "test-session-secret-with-at-least-32-bytes";

test("validates the existing username and PIN rules", () => {
  assert.equal(isValidUsername("Home Helper"), true);
  assert.equal(isValidUsername(" A "), false);
  assert.equal(isValidUsername("x".repeat(31)), false);
  assert.equal(isValidPin("0123"), true);
  assert.equal(isValidPin("123"), false);
  assert.equal(isValidPin("12a4"), false);
});

test("signs a session and rejects tampering or expiry", () => {
  const now = Date.UTC(2026, 8, 26);
  const token = createSession({ id: 7, username: "Sam" }, secret, now);

  assert.deepEqual(verifySession(token, secret, now), { id: 7, username: "Sam" });
  assert.equal(verifySession(`${token}x`, secret, now), null);
  assert.equal(verifySession(token, secret, now + 8 * 24 * 60 * 60 * 1000), null);
  assert.equal(verifySession(token, "short", now), null);
});

test("formats and reads an HTTP-only session cookie", () => {
  const cookie = sessionCookie("signed.token", { secure: false });

  assert.match(cookie, /HttpOnly/);
  assert.match(cookie, /SameSite=Lax/);
  assert.doesNotMatch(cookie, /Secure/);
  assert.equal(sessionFromCookieHeader(`other=value; ${cookie.split(";")[0]}`), "signed.token");
  assert.equal(sessionFromCookieHeader(undefined), null);
  assert.match(sessionCookie("", { clear: true }), /Max-Age=0/);
});