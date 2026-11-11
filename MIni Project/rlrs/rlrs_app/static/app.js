"use strict";
/* RLRS front end: no libraries. All dynamic text goes through textContent (no innerHTML). */
const $ = (s, r = document) => r.querySelector(s);
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) el.append(k.nodeType ? k : document.createTextNode(String(k)));
  return el;
}
const state = { user: null, tab: "calendar", equipment: [], eqId: null, weekStart: null, slots: [], slotMin: 30, sel: null };

async function api(method, path, body) {
  const r = await fetch(path, { method, headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
  let data = null;
  try { data = await r.json(); } catch (_) { /* empty */ }
  if (!r.ok) throw Object.assign(new Error((data && data.message) || "Request failed"), { status: r.status, data });
  return data;
}
function say(text, ok = true, list = null) {
  const m = $("#msg");
  m.className = "msg " + (ok ? "ok" : "err");
  m.replaceChildren(text, list ? h("ul", {}, list.map(x => h("li", {}, x))) : null);
  m.hidden = false;
  if (ok) setTimeout(() => { if (m.textContent.startsWith(text)) m.hidden = true; }, 6000);
}
function fail(e) {
  const d = e.data && e.data.details;
  say(e.message, false, Array.isArray(d) ? d.map(x => x.message || `${x.kind || "conflict"} ${String(x.start).slice(11, 16)}-${String(x.end).slice(11, 16)}`) : null);
}
const guard = fn => async (...a) => { try { await fn(...a); } catch (e) { if (e.status === 401) { state.user = null; render(); } fail(e); } };
const isStaff = () => state.user && state.user.role !== "Student";
const pad = n => String(n).padStart(2, "0");
const ymd = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const mondayOf = d => { const x = new Date(d.getFullYear(), d.getMonth(), d.getDate()); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x; };
const hm = s => String(s).slice(11, 16);
const dtLocal = s => String(s).slice(0, 16).replace("T", " ");

/* ---------- auth ---------- */
function authView() {
  let reg = false;
  const box = h("div", { class: "card narrow" });
  const draw = () => {
    const name = h("input", { id: "name", autocomplete: "name" }), email = h("input", { id: "email", type: "email", autocomplete: "username" }),
      pw = h("input", { id: "pw", type: "password", autocomplete: reg ? "new-password" : "current-password" });
    box.replaceChildren(h("h2", {}, reg ? "Create student account" : "Sign in"),
      h("form", { class: "row", style: "flex-direction:column;align-items:stretch", onsubmit: guard(async ev => {
        ev.preventDefault();
        if (reg) { await api("POST", "/api/register", { name: name.value, email: email.value, password: pw.value }); say("Account created. Please sign in."); reg = false; draw(); return; }
        state.user = await api("POST", "/api/login", { email: email.value, password: pw.value });
        $("#msg").hidden = true; await boot();
      }) },
        reg ? h("label", {}, "Name", name) : null, h("label", {}, "Email", email), h("label", {}, "Password", pw),
        h("button", { class: "pri", type: "submit" }, reg ? "Register" : "Sign in")),
      h("p", { class: "muted" }, reg ? "Have an account? " : "New student? ", h("button", { type: "button", onclick: () => { reg = !reg; draw(); } }, reg ? "Sign in" : "Register")),
      reg ? null : h("p", { class: "muted" }, "Demo: student1@lab.test / student123, incharge@lab.test / incharge123"));
  };
  draw();
  return box;
}

/* ---------- calendar ---------- */
async function loadSlots() {
  if (!state.eqId) { state.slots = []; return; }
  const to = addDays(state.weekStart, 6);
  const r = await api("GET", `/api/equipment/${state.eqId}/availability?from=${ymd(state.weekStart)}&to=${ymd(to)}`);
  state.slots = r.slots; state.slotMin = r.slot_minutes;
}
function calendarView() {
  const eq = state.equipment.find(e => e.id === state.eqId);
  const days = [...Array(7)].map((_, i) => addDays(state.weekStart, i));
  const times = [...new Set(state.slots.map(s => hm(s.start)))].sort();
  const bySlot = new Map(state.slots.map(s => [s.start.slice(0, 16), s]));
  const sel = h("select", { id: "eqsel", "aria-label": "Equipment", onchange: guard(async ev => { state.eqId = +ev.target.value; state.sel = null; await loadSlots(); render(); }) },
    state.equipment.map(e => h("option", { value: e.id, selected: e.id === state.eqId }, `${e.lab}: ${e.name}${e.requires_approval ? " (needs approval)" : ""}`)));
  const nav = (n) => guard(async () => { state.weekStart = n === 0 ? mondayOf(new Date()) : addDays(state.weekStart, n * 7); state.sel = null; await loadSlots(); render(); });
  const grid = h("table", { class: "grid", "aria-label": "Availability" },
    h("thead", {}, h("tr", {}, h("th", {}, ""), days.map(d => h("th", {}, d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" }))))),
    h("tbody", {}, times.map(t => h("tr", {}, h("th", {}, t), days.map(d => {
      const s = bySlot.get(`${ymd(d)}T${t}`);
      if (!s) return h("td", {}, "");
      const sel2 = state.sel && state.sel.start === s.start;
      return h("td", {}, h("button", { class: `slot ${s.state}${sel2 ? " sel" : ""}`, disabled: !(s.state === "free"), title: `${s.label} ${t}`,
        "aria-label": `${d.toDateString()} ${t} ${s.label}`, onclick: () => { state.sel = s; render(); } }, s.label));
    })))));
  return h("div", {},
    h("div", { class: "card" }, h("div", { class: "row" },
      h("label", { class: "grow" }, "Equipment", sel),
      h("button", { onclick: nav(-1) }, "< Prev week"), h("button", { onclick: nav(0) }, "This week"), h("button", { onclick: nav(1) }, "Next week >")),
      eq && eq.description ? h("p", { class: "muted" }, eq.description + (eq.remote_info ? ` | Remote access: ${eq.remote_info}` : "")) : null,
      h("div", { class: "legend" }, h("span", { class: "slot free" }, "Free"), h("span", { class: "slot own" }, "Yours"), h("span", { class: "slot booked" }, "Booked"),
        h("span", { class: "slot maintenance" }, "Maintenance"), h("span", { class: "slot past" }, "Past")),
      h("div", { class: "scroll" }, times.length ? grid : h("p", { class: "muted" }, "No slots to show."))),
    state.sel ? bookingForm() : null);
}
function bookingForm() {
  const s = state.sel, n = 8;
  const dur = h("select", { id: "dur" }, [...Array(n)].map((_, i) => h("option", { value: (i + 1) * state.slotMin }, `${(i + 1) * state.slotMin} min`)));
  const reserve = guard(async () => {
    const end = new Date(s.start); end.setMinutes(end.getMinutes() + +dur.value);
    const r = await api("POST", "/api/reservations", { equipment_id: state.eqId, start: s.start.slice(0, 16), end: `${ymd(end)}T${pad(end.getHours())}:${pad(end.getMinutes())}` });
    say(r.status === "Pending" ? "Request sent: waiting for approval." : "Reservation confirmed. A confirmation email is queued.");
    state.sel = null; state.equipment = await api("GET", "/api/equipment"); await loadSlots(); render();
  });
  return h("div", { class: "card" }, h("h2", {}, "Book this slot"),
    h("div", { class: "row" }, h("div", {}, h("strong", {}, state.equipment.find(e => e.id === state.eqId).name), h("div", { class: "muted" }, dtLocal(s.start))),
      h("label", {}, "Duration", dur), h("button", { class: "pri", id: "bookbtn", onclick: async () => { try { await reserve(); } catch (e) { fail(e); } } }, "Reserve"),
      h("button", { onclick: () => { state.sel = null; render(); } }, "Cancel")));
}

/* ---------- my reservations ---------- */
async function mineView() {
  const rows = await api("GET", "/api/reservations/mine");
  const cancel = id => guard(async () => { if (!confirm("Cancel this reservation?")) return; await api("POST", `/api/reservations/${id}/cancel`); say("Reservation cancelled."); render(); });
  return h("div", { class: "card" }, h("h2", {}, "My reservations"), rows.length ? h("div", { class: "scroll" }, h("table", {},
    h("thead", {}, h("tr", {}, ["Equipment", "Lab", "Start", "End", "Status", ""].map(x => h("th", {}, x)))),
    h("tbody", {}, rows.map(r => h("tr", {}, h("td", {}, r.equipment), h("td", {}, r.lab), h("td", {}, dtLocal(r.start)), h("td", {}, hm(r.end)),
      h("td", {}, h("span", { class: `tag ${r.status}` }, r.status), r.reason ? h("div", { class: "muted" }, r.reason) : null, r.remote_info ? h("div", { class: "muted" }, "Remote access: " + r.remote_info) : null),
      h("td", {}, ["Pending", "Confirmed"].includes(r.status) ? h("button", { class: "danger", onclick: cancel(r.id) }, "Cancel") : null)))))) : h("p", { class: "muted" }, "You have no reservations yet."));
}

/* ---------- staff ---------- */
async function manageView() {
  const [list, labs, eqs] = await Promise.all([api("GET", "/api/reservations/manage"), api("GET", "/api/labs"), api("GET", "/api/equipment")]);
  const act = (fn, okMsg) => guard(async ev => { if (ev && ev.preventDefault) ev.preventDefault(); await fn(); say(okMsg); render(); });
  const pending = list.filter(r => r.status === "Pending");
  const now = new Date();
  const due = list.filter(r => r.status === "Confirmed" && new Date(r.end) <= now);

  const pendingCard = h("div", { class: "card" }, h("h2", {}, `Pending approvals (${pending.length})`), pending.length ? h("table", {}, h("tbody", {}, pending.map(r => h("tr", {},
    h("td", {}, r.user), h("td", {}, r.equipment), h("td", {}, `${dtLocal(r.start)} - ${hm(r.end)}`),
    h("td", {}, h("button", { class: "pri", onclick: act(() => api("POST", `/api/reservations/${r.id}/approve`), "Approved.") }, "Approve"), " ",
      h("button", { class: "danger", onclick: act(async () => { const reason = prompt("Reason for rejection?"); if (reason === null) throw Object.assign(new Error("Rejection cancelled."), {}); await api("POST", `/api/reservations/${r.id}/reject`, { reason }); }, "Rejected.") }, "Reject")))))) : h("p", { class: "muted" }, "Nothing waiting."));

  const attendCard = h("div", { class: "card" }, h("h2", {}, `Attendance to mark (${due.length})`), due.length ? h("table", {}, h("tbody", {}, due.map(r => h("tr", {},
    h("td", {}, r.user), h("td", {}, r.equipment), h("td", {}, `${dtLocal(r.start)} - ${hm(r.end)}`),
    h("td", {}, h("button", { onclick: act(() => api("POST", `/api/reservations/${r.id}/attendance`, { outcome: "Completed" }), "Marked completed.") }, "Completed"), " ",
      h("button", { onclick: act(() => api("POST", `/api/reservations/${r.id}/attendance`, { outcome: "NoShow" }), "Marked no-show.") }, "No-show")))))) : h("p", { class: "muted" }, "No finished reservations are waiting."));

  const f = { lab: h("select", { id: "nlab" }, labs.map(l => h("option", { value: l.id }, l.name))), name: h("input", { id: "nname", placeholder: "Name" }), type: h("input", { id: "ntype", placeholder: "Type" }),
    appr: h("input", { id: "nappr", type: "checkbox" }) };
  const eqCard = h("div", { class: "card" }, h("h2", {}, "Equipment"), h("div", { class: "scroll" }, h("table", {}, h("thead", {}, h("tr", {}, ["Lab", "Name", "Type", "Approval", "Active", ""].map(x => h("th", {}, x)))),
    h("tbody", {}, eqs.map(e => h("tr", {}, h("td", {}, e.lab), h("td", {}, e.name), h("td", {}, e.type), h("td", {}, e.requires_approval ? "Required" : "No"), h("td", {}, e.active ? "Yes" : "No"),
      h("td", {}, h("button", { onclick: act(() => api("PUT", `/api/equipment/${e.id}`, { active: !e.active }), "Updated.") }, e.active ? "Deactivate" : "Activate"), " ",
        h("button", { onclick: act(() => api("PUT", `/api/equipment/${e.id}`, { requires_approval: !e.requires_approval }), "Updated.") }, "Toggle approval"))))))),
    h("form", { class: "row", onsubmit: act(async () => { await api("POST", "/api/equipment", { lab_id: +f.lab.value, name: f.name.value, type: f.type.value, requires_approval: f.appr.checked }); }, "Equipment added.") },
      h("label", {}, "Lab", f.lab), h("label", {}, "Name", f.name), h("label", {}, "Type", f.type), h("label", {}, "Needs approval", f.appr), h("button", { class: "pri", type: "submit" }, "Add equipment")));

  const lsel = h("select", { id: "lab" }, labs.map(l => h("option", { value: l.id }, l.name)));
  const L = { o: h("input", { id: "lo", type: "time" }), c: h("input", { id: "lc", type: "time" }), s: h("input", { id: "ls", type: "number", min: 5, max: 240 }), m: h("input", { id: "lm", type: "number", min: 5 }),
    a: h("input", { id: "la", type: "number", min: 1 }), x: h("input", { id: "lx", type: "number", min: 1 }) };
  const fill = () => { const l = labs.find(z => z.id === +lsel.value); L.o.value = l.open_time; L.c.value = l.close_time; L.s.value = l.slot_minutes; L.m.value = l.max_duration; L.a.value = l.advance_days; L.x.value = l.max_active; };
  lsel.addEventListener("change", fill); fill();
  const labCard = h("div", { class: "card" }, h("h2", {}, "Lab hours and booking limits"), h("form", { class: "row", onsubmit: act(async () => {
    await api("PUT", `/api/labs/${lsel.value}`, { open_time: L.o.value, close_time: L.c.value, slot_minutes: +L.s.value, max_duration: +L.m.value, advance_days: +L.a.value, max_active: +L.x.value }); }, "Lab settings saved.") },
    h("label", {}, "Lab", lsel), h("label", {}, "Opens", L.o), h("label", {}, "Closes", L.c), h("label", {}, "Slot (min)", L.s), h("label", {}, "Max duration (min)", L.m),
    h("label", {}, "Advance (days)", L.a), h("label", {}, "Max active / user", L.x), h("button", { class: "pri", type: "submit" }, "Save")));

  const M = { e: h("select", { id: "meq" }, eqs.map(e => h("option", { value: e.id }, `${e.lab}: ${e.name}`))), s: h("input", { id: "ms", type: "datetime-local" }), t: h("input", { id: "mt", type: "datetime-local" }), r: h("input", { id: "mr", placeholder: "Reason" }) };
  const maintCard = h("div", { class: "card" }, h("h2", {}, "Block equipment for maintenance"), h("p", { class: "muted" }, "Existing reservations in the window are cancelled and their holders emailed."),
    h("form", { class: "row", onsubmit: guard(async ev => { ev.preventDefault(); const r = await api("POST", "/api/maintenance", { equipment_id: +M.e.value, start: M.s.value, end: M.t.value, reason: M.r.value });
      say(`Maintenance block created. ${r.cancelled_reservation_ids.length} reservation(s) cancelled.`); render(); }) },
      h("label", {}, "Equipment", M.e), h("label", {}, "From", M.s), h("label", {}, "To", M.t), h("label", { class: "grow" }, "Reason", M.r), h("button", { class: "pri", type: "submit" }, "Create block")));
  return h("div", {}, pendingCard, attendCard, eqCard, labCard, maintCard);
}
async function reportView() {
  const today = new Date(), from = h("input", { id: "rf", type: "date", value: ymd(addDays(today, -30)) }), to = h("input", { id: "rt", type: "date", value: ymd(addDays(today, 14)) });
  const out = h("div", {});
  const run = guard(async () => {
    const rows = await api("GET", `/api/reports/utilisation?from=${from.value}&to=${to.value}`);
    out.replaceChildren(h("div", { class: "scroll" }, h("table", { id: "report" }, h("thead", {}, h("tr", {}, ["Equipment", "Booked h", "Available h", "Utilisation %", "Bookings", "Cancellations", "No-shows"].map(x => h("th", {}, x)))),
      h("tbody", {}, rows.map(r => h("tr", {}, h("td", {}, r.equipment), h("td", {}, r.booked_hours), h("td", {}, r.available_hours), h("td", {}, r.utilisation_pct), h("td", {}, r.bookings), h("td", {}, r.cancellations), h("td", {}, r.no_shows)))))));
  });
  const audit = h("div", {});
  const loadAudit = guard(async () => { const rows = await api("GET", "/api/audit");
    audit.replaceChildren(h("div", { class: "scroll" }, h("table", {}, h("thead", {}, h("tr", {}, ["When", "Who", "Action", "Details"].map(x => h("th", {}, x)))),
      h("tbody", {}, rows.map(r => h("tr", {}, h("td", {}, dtLocal(r.at)), h("td", {}, r.actor), h("td", {}, r.action), h("td", {}, JSON.stringify(r.details)))))))); });
  return h("div", {}, h("div", { class: "card" }, h("h2", {}, "Utilisation and no-show report"), h("div", { class: "row" }, h("label", {}, "From", from), h("label", {}, "To", to), h("button", { class: "pri", onclick: run }, "Run report")), out),
    h("div", { class: "card" }, h("h2", {}, "Audit log"), h("button", { onclick: loadAudit }, "Load latest 100"), audit));
}

/* ---------- shell ---------- */
async function render() {
  const app = $("#app"), who = $("#who");
  if (!state.user) { who.hidden = true; app.replaceChildren(authView()); return; }
  who.hidden = false;
  who.replaceChildren(`${state.user.name} (${state.user.role})`, h("button", { id: "logout", onclick: async () => { await api("POST", "/api/logout"); state.user = null; render(); } }, "Sign out"));
  const tabs = [["calendar", "Calendar"], ["mine", "My reservations"], ...(isStaff() ? [["manage", "Manage"], ["report", "Reports"]] : [])];
  const bar = h("div", { class: "tabs", role: "tablist" }, tabs.map(([k, label]) => h("button", { role: "tab", class: state.tab === k ? "on" : "", "aria-selected": state.tab === k, onclick: () => { state.tab = k; $("#msg").hidden = true; render(); } }, label)));
  let body;
  try { body = state.tab === "calendar" ? calendarView() : state.tab === "mine" ? await mineView() : state.tab === "manage" ? await manageView() : await reportView(); } catch (e) { fail(e); body = h("div"); }
  app.replaceChildren(bar, body);
}
async function boot() {
  state.equipment = await api("GET", "/api/equipment");
  state.eqId = state.equipment.length ? state.equipment[0].id : null;
  state.weekStart = mondayOf(new Date());
  await loadSlots();
  render();
}
(async () => { try { state.user = await api("GET", "/api/me"); await boot(); } catch (_) { render(); } })();
