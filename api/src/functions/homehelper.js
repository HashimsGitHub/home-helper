import { app } from "@azure/functions";
import { createClient } from "@libsql/client";
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

import {
  createSession,
  isValidPin,
  isValidUsername,
  sessionCookie,
  sessionFromCookieHeader,
  verifySession,
} from "../auth.js";

config({ path: fileURLToPath(new URL("../../../.env", import.meta.url)) });

const schemaTables = {
  grocery: `CREATE TABLE IF NOT EXISTS grocery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    quantity TEXT,
    category TEXT DEFAULT 'General',
    purchased INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES homehelper_users(id)
  )`,
  appointments: `CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    location TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES homehelper_users(id)
  )`,
  tasks: `CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'Medium',
    due_date TEXT,
    completed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES homehelper_users(id)
  )`,
};

let client;
let schemaReady;

function database() {
  if (client) return client;
  let url = process.env.TURSO_DATABASE_URL || "";
  if (url.startsWith("turso://")) url = `libsql://${url.slice("turso://".length)}`;
  if (!url) throw new Error("TURSO_DATABASE_URL is not configured.");

  client = createClient({
    url,
    authToken: process.env.TURSO_AUTH_TOKEN,
  });
  return client;
}

async function ensureSchema() {
  if (schemaReady) return schemaReady;

  schemaReady = (async () => {
    const db = database();
    await db.execute(`CREATE TABLE IF NOT EXISTS homehelper_users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL COLLATE NOCASE UNIQUE,
      pin TEXT NOT NULL CHECK(length(pin) = 4 AND pin NOT GLOB '*[^0-9]*'),
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )`);

    for (const [table, createSql] of Object.entries(schemaTables)) {
      await db.execute(createSql);
      const columns = await db.execute(`PRAGMA table_info(${table})`);
      if (!columns.rows.some((column) => column.name === "user_id")) {
        await db.execute(`ALTER TABLE ${table} ADD COLUMN user_id INTEGER REFERENCES homehelper_users(id)`);
      }
      await db.execute(`CREATE INDEX IF NOT EXISTS idx_${table}_user ON ${table}(user_id)`);
    }
  })().catch((error) => {
    schemaReady = undefined;
    throw error;
  });

  return schemaReady;
}

function json(body, status = 200, headers = {}) {
  return {
    status,
    jsonBody: body,
    headers: { "Content-Type": "application/json; charset=utf-8", ...headers },
  };
}

function secureRequest(request) {
  return new URL(request.url).protocol === "https:";
}

function readSession(request) {
  const secret = process.env.SESSION_SECRET;
  if (!secret || Buffer.byteLength(secret) < 32) {
    throw new Error("SESSION_SECRET must contain at least 32 bytes.");
  }

  return verifySession(
    sessionFromCookieHeader(request.headers.get("cookie")),
    secret,
  );
}

function requiredUser(request) {
  const user = readSession(request);
  return user ? { user } : { response: json({ error: "Sign in to continue." }, 401) };
}

async function readJson(request) {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

async function dashboard(userId) {
  const result = await database().execute({
    sql: `
      SELECT 'grocery' AS kind, id, item AS title, quantity AS description,
             category AS label, purchased AS completed, created_at AS date_value,
             NULL AS end_time, NULL AS location
      FROM grocery WHERE user_id = ?
      UNION ALL
      SELECT 'appointment', id, title, description, NULL, 0, start_time, end_time, location
      FROM appointments WHERE user_id = ?
      UNION ALL
      SELECT 'task', id, title, description, priority, completed, due_date, NULL, NULL
      FROM tasks WHERE user_id = ?`,
    args: [userId, userId, userId],
  });

  const data = { groceries: [], appointments: [], tasks: [] };
  for (const row of result.rows) {
    if (row.kind === "grocery") data.groceries.push(row);
    else if (row.kind === "appointment") data.appointments.push(row);
    else data.tasks.push(row);
  }
  data.groceries.sort((a, b) => String(a.label).localeCompare(String(b.label)) || b.id - a.id);
  data.appointments.sort((a, b) => String(a.date_value).localeCompare(String(b.date_value)));
  data.tasks.sort((a, b) => String(a.date_value || "").localeCompare(String(b.date_value || "")) || b.id - a.id);
  return data;
}

function positiveId(value) {
  const id = Number(value);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

async function route(request, context) {
  const path = new URL(request.url).pathname.replace(/^\/api\/?/, "").replace(/\/$/, "");
  const method = request.method.toUpperCase();

  if (path === "health" && method === "GET") {
    return json({
      ok: true,
      databaseConfigured: Boolean(process.env.TURSO_DATABASE_URL && process.env.TURSO_AUTH_TOKEN),
      sessionConfigured: Boolean(process.env.SESSION_SECRET && Buffer.byteLength(process.env.SESSION_SECRET) >= 32),
    });
  }

  if (["login", "register"].includes(path) && method === "POST") {
    const input = await readJson(request);
    const username = input?.username?.trim();
    const pin = input?.pin;
    if (!isValidUsername(username) || !isValidPin(pin)) {
      return json({ error: "Enter a user name (2-30 characters) and a four-digit PIN." }, 400);
    }

    await ensureSchema();
    const db = database();
    let user;

    if (path === "register") {
      try {
        const result = await db.execute({
          sql: "INSERT INTO homehelper_users (username, pin) VALUES (?, ?)",
          args: [username, pin],
        });
        user = { id: Number(result.lastInsertRowid), username };
      } catch (error) {
        if (/unique|constraint/i.test(String(error))) {
          return json({ error: "That user name is already registered." }, 409);
        }
        throw error;
      }
    } else {
      const result = await db.execute({
        sql: `SELECT id, username FROM homehelper_users
              WHERE username = ? COLLATE NOCASE AND pin = ?`,
        args: [username, pin],
      });
      user = result.rows[0] ? { id: Number(result.rows[0].id), username: result.rows[0].username } : null;
      if (!user) return json({ error: "The user name or PIN is incorrect." }, 401);
    }

    const token = createSession(user, process.env.SESSION_SECRET);
    return json({ user }, 200, {
      "Set-Cookie": sessionCookie(token, { secure: secureRequest(request) }),
    });
  }

  if (path === "logout" && method === "POST") {
    return json({ ok: true }, 200, {
      "Set-Cookie": sessionCookie("", { secure: secureRequest(request), clear: true }),
    });
  }

  if (path === "me" && method === "GET") {
    const { user, response } = requiredUser(request);
    return response || json({ user });
  }

  const { user, response } = requiredUser(request);
  if (response) return response;

  await ensureSchema();
  const db = database();
  const segments = path.split("/").map((part) => decodeURIComponent(part));
  const resource = segments[0];
  const itemId = segments.length === 2 ? positiveId(segments[1]) : null;

  if (path === "dashboard" && method === "GET") {
    return json(await dashboard(user.id));
  }

  if (resource === "groceries" && segments.length === 1 && method === "GET") {
    const result = await db.execute({
      sql: `SELECT id, item, quantity, category, purchased, created_at
            FROM grocery WHERE user_id = ? ORDER BY purchased, id DESC`,
      args: [user.id],
    });
    return json({ items: result.rows });
  }

  if (resource === "groceries" && segments.length === 1 && method === "POST") {
    const input = await readJson(request);
    const item = typeof input?.item === "string" ? input.item.trim() : "";
    const quantity = typeof input?.quantity === "string" ? input.quantity.trim() : "";
    const category = typeof input?.category === "string" ? input.category : "General";
    const categories = ["General", "Produce", "Dairy", "Meat", "Bakery", "Frozen", "Other"];
    if (!item || item.length > 160 || quantity.length > 80 || !categories.includes(category)) {
      return json({ error: "Enter a valid item, quantity, and category." }, 400);
    }
    await db.execute({
      sql: "INSERT INTO grocery (user_id, item, quantity, category) VALUES (?, ?, ?, ?)",
      args: [user.id, item, quantity, category],
    });
    return json({ ok: true }, 201);
  }

  if (resource === "groceries" && itemId && method === "PATCH") {
    const input = await readJson(request);
    if (typeof input?.purchased !== "boolean") return json({ error: "A purchased status is required." }, 400);
    await db.execute({
      sql: "UPDATE grocery SET purchased = ? WHERE id = ? AND user_id = ?",
      args: [Number(input.purchased), itemId, user.id],
    });
    return json({ ok: true });
  }

  if (resource === "groceries" && itemId && method === "DELETE") {
    await db.execute({ sql: "DELETE FROM grocery WHERE id = ? AND user_id = ?", args: [itemId, user.id] });
    return json({ ok: true });
  }

  if (resource === "appointments" && segments.length === 1 && method === "GET") {
    const result = await db.execute({
      sql: `SELECT id, title, description, start_time, end_time, location
            FROM appointments WHERE user_id = ? ORDER BY start_time`,
      args: [user.id],
    });
    return json({ items: result.rows });
  }

  if (resource === "appointments" && segments.length === 1 && method === "POST") {
    const input = await readJson(request);
    const title = typeof input?.title === "string" ? input.title.trim() : "";
    const start = typeof input?.start_time === "string" ? input.start_time : "";
    const end = typeof input?.end_time === "string" ? input.end_time : "";
    if (!title || title.length > 160 || !Number.isFinite(Date.parse(start)) || !Number.isFinite(Date.parse(end)) || Date.parse(end) <= Date.parse(start)) {
      return json({ error: "Enter a title and a valid appointment time range." }, 400);
    }
    const description = typeof input.description === "string" ? input.description.trim().slice(0, 2000) : "";
    const location = typeof input.location === "string" ? input.location.trim().slice(0, 160) : "";
    await db.execute({
      sql: `INSERT INTO appointments (user_id, title, description, start_time, end_time, location)
            VALUES (?, ?, ?, ?, ?, ?)`,
      args: [user.id, title, description, start, end, location],
    });
    return json({ ok: true }, 201);
  }

  if (resource === "appointments" && itemId && method === "DELETE") {
    await db.execute({ sql: "DELETE FROM appointments WHERE id = ? AND user_id = ?", args: [itemId, user.id] });
    return json({ ok: true });
  }

  if (resource === "tasks" && segments.length === 1 && method === "GET") {
    const result = await db.execute({
      sql: `SELECT id, title, description, priority, due_date, completed
            FROM tasks WHERE user_id = ? ORDER BY completed, id DESC`,
      args: [user.id],
    });
    return json({ items: result.rows });
  }

  if (resource === "tasks" && segments.length === 1 && method === "POST") {
    const input = await readJson(request);
    const title = typeof input?.title === "string" ? input.title.trim() : "";
    const priority = input?.priority;
    const dueDate = input?.due_date;
    if (!title || title.length > 160 || !["Low", "Medium", "High"].includes(priority) || !/^\d{4}-\d{2}-\d{2}$/.test(dueDate || "")) {
      return json({ error: "Enter a task, priority, and due date." }, 400);
    }
    const description = typeof input.description === "string" ? input.description.trim().slice(0, 2000) : "";
    await db.execute({
      sql: "INSERT INTO tasks (user_id, title, description, priority, due_date) VALUES (?, ?, ?, ?, ?)",
      args: [user.id, title, description, priority, dueDate],
    });
    return json({ ok: true }, 201);
  }

  if (resource === "tasks" && itemId && method === "PATCH") {
    const input = await readJson(request);
    if (typeof input?.completed !== "boolean") return json({ error: "A completed status is required." }, 400);
    await db.execute({
      sql: "UPDATE tasks SET completed = ? WHERE id = ? AND user_id = ?",
      args: [Number(input.completed), itemId, user.id],
    });
    return json({ ok: true });
  }

  if (resource === "tasks" && itemId && method === "DELETE") {
    await db.execute({ sql: "DELETE FROM tasks WHERE id = ? AND user_id = ?", args: [itemId, user.id] });
    return json({ ok: true });
  }

  return json({ error: "Not found." }, 404);
}

app.http("homehelper", {
  route: "{*route}",
  methods: ["GET", "POST", "PATCH", "DELETE"],
  authLevel: "anonymous",
  handler: async (request, context) => {
    try {
      return await route(request, context);
    } catch (error) {
      context.error(error);
      if (/not configured|must contain at least 32 bytes/i.test(String(error))) {
        return json({ error: "The Home Helper API is not configured. Check its application settings." }, 503);
      }
      return json({ error: "The request could not be completed." }, 500);
    }
  },
});