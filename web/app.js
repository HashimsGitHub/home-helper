const app = document.querySelector("#app");
const categories = ["General", "Produce", "Dairy", "Meat", "Bakery", "Frozen", "Other"];
const views = [
  { id: "home", label: "Home", letter: "H" },
  { id: "groceries", label: "Groceries", letter: "G" },
  { id: "appointments", label: "Appointments", letter: "A" },
  { id: "tasks", label: "Tasks", letter: "T" },
];
const state = {
  user: null,
  view: "home",
  authMode: "login",
  groceryFilter: "active",
  taskFilter: "active",
  appointmentMode: "upcoming",
  calendarMonth: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  calendarDate: null,
  feedback: "",
  feedbackError: false,
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api/${path}`, {
      credentials: "same-origin",
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error("The service is unavailable. Check your connection and try again.");
  }

  const result = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && state.user) {
      state.user = null;
      state.authMode = "login";
    }
    throw new Error(result.error || "The request could not be completed.");
  }
  return result;
}

function feedbackMarkup() {
  if (!state.feedback) return "";
  return `<p class="feedback${state.feedbackError ? " feedback-error" : ""}" role="status">${escapeHtml(state.feedback)}</p>`;
}

function setFeedback(message = "", isError = false) {
  state.feedback = message;
  state.feedbackError = isError;
}

function navMarkup(mobile = false) {
  const items = views.map(({ id, label, letter }) => `
    <button class="nav-button" type="button" data-view="${id}" aria-current="${state.view === id ? "page" : "false"}">
      <span class="nav-letter" aria-hidden="true">${letter}</span><span>${label}</span>
    </button>`).join("");
  return mobile
    ? `<nav class="mobile-nav" aria-label="Main navigation">${items}</nav>`
    : `<nav class="side-nav" aria-label="Main navigation"><p class="nav-label">Your home</p><div class="nav-list">${items}</div></nav>`;
}

function appFrame() {
  return `
    <div class="app-frame">
      <header class="topbar">
        <div class="brand"><span class="brand-mark" aria-hidden="true">HH</span><span class="brand-name">Home Helper</span></div>
        <div class="user-tools"><span class="user-name">${escapeHtml(state.user.username)}</span><button class="button button-quiet" type="button" data-action="logout">Sign out</button></div>
      </header>
      <div class="app-body">
        ${navMarkup()}
        <section class="workspace" aria-label="Home Helper workspace">
          ${feedbackMarkup()}
          <div id="view-panel"><p class="loading">Loading your home...</p></div>
        </section>
      </div>
      ${navMarkup(true)}
    </div>`;
}

function authScreen() {
  const registering = state.authMode === "register";
  return `
    <section class="auth-screen">
      <div class="auth-intro">
        <div class="brand"><span class="brand-mark" aria-hidden="true">HH</span><span class="brand-name">Home Helper</span></div>
        <span class="eyebrow">A little more in order</span>
        <h1>Make room for home.</h1>
        <p>Keep the shopping list, family plans and small jobs together in one place.</p>
        <div class="auth-accent" aria-hidden="true"></div>
      </div>
      <section class="auth-panel" aria-labelledby="auth-title">
        <h2 id="auth-title">${registering ? "Create your account" : "Welcome back"}</h2>
        <p>${registering ? "Choose a name and a four-digit PIN." : "Sign in to see your household lists."}</p>
        <div class="auth-tabs" role="group" aria-label="Account access">
          <button type="button" data-auth-mode="login" aria-pressed="${!registering}">Sign in</button>
          <button type="button" data-auth-mode="register" aria-pressed="${registering}">Register</button>
        </div>
        ${feedbackMarkup()}
        <form id="auth-form" novalidate>
          <label class="field"><span>User name</span><input name="username" type="text" autocomplete="${registering ? "username" : "username"}" maxlength="30" required autofocus></label>
          <label class="field"><span>4-digit PIN</span><input name="pin" type="password" inputmode="numeric" autocomplete="${registering ? "new-password" : "current-password"}" pattern="[0-9]{4}" maxlength="4" required></label>
          <button class="button button-primary button-full" type="submit">${registering ? "Create account" : "Sign in"}</button>
        </form>
      </section>
    </section>`;
}

function dateKey(value) {
  return typeof value === "string" ? value.slice(0, 10) : "";
}

function localDate(value) {
  if (!value) return null;
  const key = dateKey(value);
  const [year, month, day] = key.split("-").map(Number);
  if (!year || !month || !day) return null;
  const date = new Date(year, month - 1, day);
  return Number.isNaN(date.valueOf()) ? null : date;
}

function formatDate(value, options = { weekday: "short", day: "numeric", month: "short" }) {
  const date = localDate(value);
  return date ? new Intl.DateTimeFormat(undefined, options).format(date) : "Date not set";
}

function formatTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "" : new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(date);
}

function startOfToday() {
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  return date;
}

function dueLabel(value) {
  const due = localDate(value);
  if (!due) return "No due date";
  const days = Math.round((due - startOfToday()) / 86400000);
  if (days < 0) return `Overdue · ${formatDate(value)}`;
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  return `Due ${formatDate(value)}`;
}

function pageHeading(eyebrow, title, description, action = "") {
  return `<header class="page-heading"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${description}</p></div>${action}</header>`;
}

function emptyState(title, detail) {
  return `<div class="empty-state"><strong>${title}</strong>${detail}</div>`;
}

function addPanel(summary, form) {
  return `<details class="add-panel"><summary>${summary}</summary>${form}</details>`;
}

function groceryForm() {
  const options = categories.map((category) => `<option>${category}</option>`).join("");
  return addPanel("Add grocery item", `
    <form class="add-form" data-form="grocery">
      <div class="add-form-grid">
        <label class="field"><span>Item</span><input name="item" placeholder="Milk" maxlength="160" required></label>
        <label class="field"><span>Quantity</span><input name="quantity" placeholder="1 litre" maxlength="80"></label>
        <label class="field field-wide"><span>Category</span><select name="category">${options}</select></label>
      </div>
      <div class="form-actions"><button class="button button-primary" type="submit">Add to list</button></div>
    </form>`);
}

function appointmentForm() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dateValue = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, "0")}-${String(tomorrow.getDate()).padStart(2, "0")}`;
  return addPanel("Add appointment", `
    <form class="add-form" data-form="appointment">
      <div class="add-form-grid">
        <label class="field field-wide"><span>Title</span><input name="title" placeholder="Dentist visit" maxlength="160" required></label>
        <label class="field"><span>Starts</span><input name="start_time" type="datetime-local" value="${dateValue}T09:00" required></label>
        <label class="field"><span>Ends</span><input name="end_time" type="datetime-local" value="${dateValue}T10:00" required></label>
        <label class="field field-wide"><span>Location</span><input name="location" placeholder="Optional" maxlength="160"></label>
        <label class="field field-wide"><span>Notes</span><textarea name="description" placeholder="Optional details" maxlength="2000"></textarea></label>
      </div>
      <div class="form-actions"><button class="button button-primary" type="submit">Save appointment</button></div>
    </form>`);
}

function taskForm() {
  const today = new Date();
  const dateValue = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  return addPanel("Add task", `
    <form class="add-form" data-form="task">
      <div class="add-form-grid">
        <label class="field field-wide"><span>Task</span><input name="title" placeholder="Change the light bulb" maxlength="160" required></label>
        <label class="field"><span>Priority</span><select name="priority"><option>Low</option><option selected>Medium</option><option>High</option></select></label>
        <label class="field"><span>Due date</span><input name="due_date" type="date" value="${dateValue}" required></label>
        <label class="field field-wide"><span>Notes</span><textarea name="description" placeholder="Optional details" maxlength="2000"></textarea></label>
      </div>
      <div class="form-actions"><button class="button button-primary" type="submit">Add task</button></div>
    </form>`);
}

function groceryRow(item) {
  const checked = Number(item.purchased) === 1;
  const meta = [item.quantity, item.category !== "General" ? item.category : ""].filter(Boolean).map(escapeHtml).join(" · ");
  return `<article class="item-row">
    <input type="checkbox" aria-label="Mark ${escapeHtml(item.item)} as purchased" data-toggle-kind="groceries" data-id="${Number(item.id)}" ${checked ? "checked" : ""}>
    <div class="item-main"><p class="item-title${checked ? " is-done" : ""}">${escapeHtml(item.item)}</p>${meta ? `<p class="item-meta">${meta}</p>` : ""}</div>
    <div class="item-actions"><button class="button button-danger" type="button" data-delete-kind="groceries" data-id="${Number(item.id)}">Delete</button></div>
  </article>`;
}

function taskRow(task) {
  const checked = Number(task.completed) === 1;
  const priorityClass = String(task.priority).toLowerCase();
  return `<article class="item-row">
    <input type="checkbox" aria-label="Mark ${escapeHtml(task.title)} as complete" data-toggle-kind="tasks" data-id="${Number(task.id)}" ${checked ? "checked" : ""}>
    <div class="item-main"><p class="item-title${checked ? " is-done" : ""}">${escapeHtml(task.title)}</p>
      <p class="item-meta"><span class="priority priority-${priorityClass}"><span class="priority-dot"></span>${escapeHtml(task.priority)}</span> · ${escapeHtml(dueLabel(task.due_date))}</p>
      ${task.description ? `<p class="item-meta">${escapeHtml(task.description)}</p>` : ""}
    </div>
    <div class="item-actions"><button class="button button-danger" type="button" data-delete-kind="tasks" data-id="${Number(task.id)}">Delete</button></div>
  </article>`;
}

function appointmentRow(item) {
  const meta = [formatDate(item.start_time), formatTime(item.start_time), item.location].filter(Boolean).join(" · ");
  return `<article class="item-row appointment-row">
    <span class="nav-letter" aria-hidden="true">A</span>
    <div class="item-main"><p class="item-title">${escapeHtml(item.title)}</p><p class="item-meta">${escapeHtml(meta)}</p>
      ${item.description ? `<p class="item-meta">${escapeHtml(item.description)}</p>` : ""}
    </div>
    <div class="item-actions"><button class="button button-danger" type="button" data-delete-kind="appointments" data-id="${Number(item.id)}">Delete</button></div>
  </article>`;
}

function pageCount(count) {
  return `<span class="record-count">${count} ${count === 1 ? "item" : "items"}</span>`;
}

async function renderHome() {
  const data = await api("dashboard");
  const todayKey = new Date().toLocaleDateString("en-CA");
  const pendingGroceries = data.groceries.filter((item) => Number(item.completed) !== 1);
  const pendingTasks = data.tasks.filter((task) => Number(task.completed) !== 1);
  const upcoming = data.appointments.filter((item) => dateKey(item.date_value) >= todayKey);
  const todayAppointments = upcoming.filter((item) => dateKey(item.date_value) === todayKey);
  const dueTasks = pendingTasks.filter((task) => !task.date_value || dateKey(task.date_value) <= todayKey);
  const agenda = [
    ...todayAppointments.map((item) => ({ time: formatTime(item.date_value), kind: "Appointment", title: item.title, detail: item.location || item.description })),
    ...dueTasks.map((task) => ({ time: "Task", kind: `${task.label || "Medium"} priority`, title: task.title, detail: dueLabel(task.date_value) })),
  ];

  return `
    <section class="page-content">
      <header class="home-heading"><span class="eyebrow">${new Intl.DateTimeFormat(undefined, { weekday: "long" }).format(new Date())}</span>
        <h1 class="home-title">Home, at a glance.</h1><p class="home-date">${new Intl.DateTimeFormat(undefined, { day: "numeric", month: "long", year: "numeric" }).format(new Date())}</p>
      </header>
      <section class="summary-grid" aria-label="Household summary">
        <button class="summary-tile" type="button" data-view="groceries"><span class="summary-top">Groceries <span>To buy</span></span><span class="summary-count">${pendingGroceries.length}</span></button>
        <button class="summary-tile" type="button" data-view="appointments"><span class="summary-top">Appointments <span>Upcoming</span></span><span class="summary-count">${upcoming.length}</span></button>
        <button class="summary-tile" type="button" data-view="tasks"><span class="summary-top">Tasks <span>To do</span></span><span class="summary-count">${pendingTasks.length}</span></button>
      </section>
      <div class="today-layout">
        <section><div class="section-heading"><h2>Today</h2><button type="button" data-view="appointments">Open schedule</button></div>
          ${agenda.length ? `<div class="agenda">${agenda.map((item) => `<article class="agenda-row"><span class="agenda-time">${escapeHtml(item.time)}</span><div><p class="agenda-kind">${escapeHtml(item.kind)}</p><p class="agenda-title">${escapeHtml(item.title)}</p><p class="agenda-detail">${escapeHtml(item.detail || "")}</p></div></article>`).join("")}</div>` : emptyState("Nothing urgent today", "Your day is clear.")}
        </section>
        <section><div class="section-heading"><h2>Next to pick up</h2><button type="button" data-view="groceries">Full list</button></div>
          ${pendingGroceries.length ? `<div class="side-list">${pendingGroceries.slice(0, 5).map((item) => `<div class="side-list-item"><span>${escapeHtml(item.title)}</span><small>${escapeHtml(item.description || "")}</small></div>`).join("")}</div>` : emptyState("Shopping list is clear", "Add an item when you need it.")}
        </section>
      </div>
    </section>`;
}

async function renderGroceries() {
  const { items } = await api("groceries");
  const active = items.filter((item) => Number(item.purchased) !== 1);
  const purchased = items.filter((item) => Number(item.purchased) === 1);
  const visible = state.groceryFilter === "active" ? active : purchased;
  return `
    <section class="page-content">
      ${pageHeading("The shopping list", "Groceries", "Everything the household needs, in one list.", pageCount(items.length))}
      ${groceryForm()}
      <div class="content-toolbar"><div class="segmented" role="group" aria-label="Filter groceries">
        <button type="button" data-grocery-filter="active" aria-pressed="${state.groceryFilter === "active"}">To buy (${active.length})</button>
        <button type="button" data-grocery-filter="purchased" aria-pressed="${state.groceryFilter === "purchased"}">Purchased (${purchased.length})</button>
      </div></div>
      <div class="list-stack">${visible.length ? visible.map(groceryRow).join("") : emptyState(state.groceryFilter === "active" ? "Your list is clear" : "Nothing purchased yet", state.groceryFilter === "active" ? "Add an item above when you need it." : "Items you check off will appear here.")}</div>
    </section>`;
}

function calendarMarkup(items) {
  const month = state.calendarMonth;
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const start = new Date(first);
  start.setDate(first.getDate() - ((first.getDay() + 6) % 7));
  const today = new Date();
  const todayKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  const selectedKey = state.calendarDate || todayKey;
  const cells = Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    const events = items.filter((item) => dateKey(item.start_time) === key);
    const classes = ["calendar-day", date.getMonth() !== month.getMonth() ? "is-outside" : "", key === todayKey ? "is-today" : "", key === selectedKey ? "is-selected" : ""].filter(Boolean).join(" ");
    return `<button class="${classes}" type="button" data-calendar-date="${key}" aria-label="${escapeHtml(formatDate(key, { weekday: "long", day: "numeric", month: "long" }))}${events.length ? `, ${events.length} appointments` : ""}"><span class="day-number">${date.getDate()}</span>${events.slice(0, 2).map((event) => `<span class="calendar-event">${escapeHtml(event.title)}</span>`).join("")}</button>`;
  }).join("");
  const selectedItems = items.filter((item) => dateKey(item.start_time) === selectedKey);
  return `<div class="calendar-wrap">
    <div class="calendar-head"><button class="calendar-step" type="button" data-month-step="-1" aria-label="Previous month">&lt;</button>
      <h2>${new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" }).format(month)}</h2>
      <button class="calendar-step" type="button" data-month-step="1" aria-label="Next month">&gt;</button></div>
    <div class="calendar-grid"><div class="calendar-weekday">Mon</div><div class="calendar-weekday">Tue</div><div class="calendar-weekday">Wed</div><div class="calendar-weekday">Thu</div><div class="calendar-weekday">Fri</div><div class="calendar-weekday">Sat</div><div class="calendar-weekday">Sun</div>${cells}</div>
    <section class="calendar-agenda"><h3>${escapeHtml(formatDate(selectedKey, { weekday: "long", day: "numeric", month: "long" }))}</h3>
      <div class="list-stack">${selectedItems.length ? selectedItems.map(appointmentRow).join("") : emptyState("No appointments", "Nothing is scheduled for this day.")}</div></section>
  </div>`;
}

async function renderAppointments() {
  const { items } = await api("appointments");
  const todayKey = new Date().toLocaleDateString("en-CA");
  const upcoming = items.filter((item) => dateKey(item.start_time) >= todayKey);
  const past = items.filter((item) => dateKey(item.start_time) < todayKey);
  return `
    <section class="page-content">
      ${pageHeading("Plans and places", "Appointments", "Keep upcoming commitments easy to find.")}
      ${appointmentForm()}
      <div class="content-toolbar"><div class="segmented" role="group" aria-label="Appointment view">
        <button type="button" data-appointment-mode="upcoming" aria-pressed="${state.appointmentMode === "upcoming"}">Upcoming (${upcoming.length})</button>
        <button type="button" data-appointment-mode="calendar" aria-pressed="${state.appointmentMode === "calendar"}">Calendar</button>
      </div></div>
      ${state.appointmentMode === "calendar" ? calendarMarkup(items) : `<div class="list-stack">${upcoming.length ? upcoming.map(appointmentRow).join("") : emptyState("No upcoming appointments", "Add a commitment above when plans are made.")}</div>${past.length ? `<details class="add-panel" style="margin-top:18px"><summary>Past appointments (${past.length})</summary><div class="list-stack" style="padding:12px">${past.slice().reverse().map(appointmentRow).join("")}</div></details>` : ""}`}
    </section>`;
}

async function renderTasks() {
  const { items } = await api("tasks");
  const active = items.filter((task) => Number(task.completed) !== 1).sort((a, b) => String(a.due_date || "9999-12-31").localeCompare(String(b.due_date || "9999-12-31")) || ["High", "Medium", "Low"].indexOf(a.priority) - ["High", "Medium", "Low"].indexOf(b.priority));
  const completed = items.filter((task) => Number(task.completed) === 1);
  const visible = state.taskFilter === "active" ? active : completed;
  return `
    <section class="page-content">
      ${pageHeading("Shared responsibilities", "Tasks", "Keep the small jobs from slipping through.", pageCount(items.length))}
      ${taskForm()}
      <div class="content-toolbar"><div class="segmented" role="group" aria-label="Filter tasks">
        <button type="button" data-task-filter="active" aria-pressed="${state.taskFilter === "active"}">To do (${active.length})</button>
        <button type="button" data-task-filter="completed" aria-pressed="${state.taskFilter === "completed"}">Completed (${completed.length})</button>
      </div></div>
      <div class="list-stack">${visible.length ? visible.map(taskRow).join("") : emptyState(state.taskFilter === "active" ? "All tasks are complete" : "No completed tasks", state.taskFilter === "active" ? "Add a task above when something needs doing." : "Finished tasks will appear here.")}</div>
    </section>`;
}

const renderers = {
  home: renderHome,
  groceries: renderGroceries,
  appointments: renderAppointments,
  tasks: renderTasks,
};

async function render() {
  app.innerHTML = state.user ? appFrame() : authScreen();
  if (!state.user) return;

  const panel = document.querySelector("#view-panel");
  const view = state.view;
  try {
    panel.innerHTML = await renderers[view]();
  } catch (error) {
    if (!state.user) return render();
    panel.innerHTML = `<div class="feedback feedback-error" role="alert">${escapeHtml(error.message)} <button class="text-button" type="button" data-action="retry">Try again</button></div>`;
  }
}

async function refresh(message = "") {
  setFeedback(message);
  await render();
}

async function submitAuth(form) {
  const values = new FormData(form);
  const username = String(values.get("username") || "").trim();
  const pin = String(values.get("pin") || "");
  if (username.length < 2 || username.length > 30 || !/^\d{4}$/.test(pin)) {
    setFeedback("Enter a user name (2-30 characters) and four-digit PIN.", true);
    return render();
  }
  const endpoint = state.authMode === "register" ? "register" : "login";
  try {
    const result = await api(endpoint, { method: "POST", body: JSON.stringify({ username, pin }) });
    state.user = result.user;
    state.view = "home";
    setFeedback("");
    await render();
  } catch (error) {
    setFeedback(error.message, true);
    await render();
  }
}

async function submitData(form) {
  const values = Object.fromEntries(new FormData(form));
  const kind = form.dataset.form;
  try {
    if (kind === "grocery") {
      await api("groceries", { method: "POST", body: JSON.stringify(values) });
      setFeedback("Added to the grocery list.");
    } else if (kind === "appointment") {
      if (new Date(values.end_time) <= new Date(values.start_time)) throw new Error("End time must be after the start time.");
      await api("appointments", { method: "POST", body: JSON.stringify(values) });
      setFeedback("Appointment saved.");
    } else {
      await api("tasks", { method: "POST", body: JSON.stringify(values) });
      setFeedback("Task added.");
    }
    await render();
  } catch (error) {
    setFeedback(error.message, true);
    await render();
  }
}

async function toggleItem(input) {
  const kind = input.dataset.toggleKind;
  const property = kind === "groceries" ? "purchased" : "completed";
  try {
    await api(`${kind}/${input.dataset.id}`, { method: "PATCH", body: JSON.stringify({ [property]: input.checked }) });
    await refresh();
  } catch (error) {
    setFeedback(error.message, true);
    await render();
  }
}

async function deleteItem(button) {
  const kind = button.dataset.deleteKind;
  if (!window.confirm("Delete this item?")) return;
  try {
    await api(`${kind}/${button.dataset.id}`, { method: "DELETE" });
    await refresh("Item deleted.");
  } catch (error) {
    setFeedback(error.message, true);
    await render();
  }
}

app.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  if (button.dataset.view) {
    state.view = button.dataset.view;
    setFeedback("");
    return render();
  }
  if (button.dataset.authMode) {
    state.authMode = button.dataset.authMode;
    setFeedback("");
    return render();
  }
  if (button.dataset.groceryFilter) {
    state.groceryFilter = button.dataset.groceryFilter;
    return render();
  }
  if (button.dataset.taskFilter) {
    state.taskFilter = button.dataset.taskFilter;
    return render();
  }
  if (button.dataset.appointmentMode) {
    state.appointmentMode = button.dataset.appointmentMode;
    return render();
  }
  if (button.dataset.monthStep) {
    state.calendarMonth.setMonth(state.calendarMonth.getMonth() + Number(button.dataset.monthStep));
    return render();
  }
  if (button.dataset.calendarDate) {
    state.calendarDate = button.dataset.calendarDate;
    const [year, month] = state.calendarDate.split("-").map(Number);
    state.calendarMonth = new Date(year, month - 1, 1);
    return render();
  }
  if (button.dataset.deleteKind) return deleteItem(button);
  if (button.dataset.action === "logout") {
    try { await api("logout", { method: "POST" }); } catch { /* The local session still clears if the API is offline. */ }
    state.user = null;
    state.authMode = "login";
    setFeedback("");
    return render();
  }
  if (button.dataset.action === "retry") return render();
});

app.addEventListener("change", (event) => {
  if (event.target.matches("[data-toggle-kind]")) toggleItem(event.target);
});

app.addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.target.id === "auth-form") return submitAuth(event.target);
  if (event.target.matches("[data-form]")) return submitData(event.target);
});

async function start() {
  try {
    const result = await api("me");
    state.user = result.user;
  } catch (error) {
    if (/not configured/i.test(error.message)) setFeedback(error.message, true);
  }
  await render();
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}), { once: true });
  }
}

start();