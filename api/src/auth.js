import { createHmac, timingSafeEqual } from "node:crypto";

const SESSION_COOKIE = "homehelper_session";
const SESSION_SECONDS = 60 * 60 * 24 * 7;

export function isValidUsername(username) {
  return typeof username === "string" && username.trim().length >= 2 && username.trim().length <= 30;
}

export function isValidPin(pin) {
  return typeof pin === "string" && /^\d{4}$/.test(pin);
}

function signature(value, secret) {
  return createHmac("sha256", secret).update(value).digest("base64url");
}

export function createSession(user, secret, now = Date.now()) {
  if (typeof secret !== "string" || Buffer.byteLength(secret) < 32) {
    throw new Error("SESSION_SECRET must contain at least 32 bytes.");
  }

  const payload = Buffer.from(JSON.stringify({
    userId: Number(user.id),
    username: user.username,
    expiresAt: Math.floor(now / 1000) + SESSION_SECONDS,
  })).toString("base64url");

  return `${payload}.${signature(payload, secret)}`;
}

export function verifySession(token, secret, now = Date.now()) {
  if (!token || typeof secret !== "string" || Buffer.byteLength(secret) < 32) return null;

  const [payload, suppliedSignature, extra] = token.split(".");
  if (!payload || !suppliedSignature || extra) return null;

  const expectedSignature = signature(payload, secret);
  const supplied = Buffer.from(suppliedSignature);
  const expected = Buffer.from(expectedSignature);
  if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) return null;

  try {
    const session = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (!Number.isInteger(session.userId) || session.userId < 1) return null;
    if (typeof session.username !== "string" || session.expiresAt <= Math.floor(now / 1000)) return null;
    return { id: session.userId, username: session.username };
  } catch {
    return null;
  }
}

export function sessionCookie(token, { secure = true, clear = false } = {}) {
  const parts = [
    `${SESSION_COOKIE}=${clear ? "" : token}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Lax",
    `Max-Age=${clear ? 0 : SESSION_SECONDS}`,
  ];
  if (secure) parts.push("Secure");
  return parts.join("; ");
}

export function sessionFromCookieHeader(header) {
  if (typeof header !== "string") return null;
  for (const part of header.split(";")) {
    const [name, ...value] = part.trim().split("=");
    if (name === SESSION_COOKIE) return value.join("=") || null;
  }
  return null;
}

export const SESSION_LIFETIME_SECONDS = SESSION_SECONDS;