"use strict";
// Phone-first workout UI. Taps update the page instantly; the server is only called to load data
// and save. Every URL is relative so the page works behind Home Assistant ingress.

const $view = document.getElementById("view");
const $date = document.getElementById("date");
const $save = document.getElementById("save-state");
const $toast = document.getElementById("toast");

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
const num = (v) =>(v === "" || v === null || v === undefined || Number.isNaN(Number(v)) ? null : Number(v));
const store = {
  get(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ } },
  remove(key) { try { localStorage.removeItem(key); } catch { /* private mode */ } },
};

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) {
    const err = new Error(await res.text());
    err.status = res.status;
    throw err;
  }
  return res.json();
}

let toastTimer;
function toast(text) {
  $toast.textContent = text;
  $toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $toast.classList.remove("show"), 2600);
}

function setSaveState(text, error = false) {
  $save.textContent = text;
  $save.classList.toggle("error", error);
}

const FINISH_DEFAULTS = { rpe: 5, pf: 1, kidney: 1, notes: "" };
const state = {
  tab: "today",
  status: null,
  plan: null,
  sets: {},        // exercise name -> [{weight, reps, done}]
  extras: [],      // exercises added by hand
  checks: {},      // warm-up item -> done
  finish: { ...FINISH_DEFAULTS },
  open: new Set(), // expanded how-to / history / library panels
  history: null,
  progress: { exercise: "", days: [] },
  coach: store.get("coach", null) || [
    { role: "assistant", content: "Hey Joe, how did the left flank feel during those wall sits today?" },
  ],
  coachBusy: false,
  mind: null, mindFilter: "all", mindQ: "",
  med: null, medFilter: "all", medShown: 10, medMinutes: 5, medFocus: "", medScript: "", medBusy: false, medError: "",
  lib: { q: "", focus: "", muscle: "", equipment: "", pictures: true, filtered: false, data: null, results: [], offset: 0 },
};

// --- Shared pieces --------------------------------------------------------------------------

function pictures(urls, note) {
  if (!urls || !urls.length) return "";
  // Start picture last so it is on top when the flip animation begins
  const imgs = [...urls].reverse().map((u) => `<img src="${esc(u)}" alt="" loading="lazy">`).join("");
  return `<div class="flip${urls.length > 1 ? " two" : ""}">${imgs}</div>` + (note ? `<div class="sub">${esc(note)}</div>` : "");
}

function hasHowTo(ex) {
  return Boolean(ex.images?.length || ex.steps?.length || ex.warning || ex.tips?.length);
}

function howTo(ex) {
  const facts = [ex.muscles?.join(", "), ex.equipment, ex.level, ex.sources?.length && `Sources: ${ex.sources.join(", ")}`]
    .filter(Boolean).map(esc).join(" · ");
  return `<div class="howto">
    ${ex.warning ? `<div class="warning">${esc(ex.warning)}</div>` : ""}
    ${pictures(ex.images, ex.image_note)}
    ${ex.gallery?.length > 2 ? `<div class="gallery">${ex.gallery.slice(2).map((u) => `<img src="${esc(u)}" alt="" loading="lazy">`).join("")}</div>` : ""}
    ${ex.dose ? `<div><strong>${esc(ex.dose)}</strong></div>` : ""}
    ${ex.steps?.length ? `<ol>${ex.steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>` : ""}
    ${ex.tips?.length ? `<p class="small muted">Tips: ${esc(ex.tips.join(" "))}</p>` : ""}
    ${facts ? `<p class="small muted">${facts}</p>` : ""}
  </div>`;
}

function toggleButton(key, label = "How to") {
  return `<button type="button" class="btn link" data-act="toggle" data-key="${esc(key)}" aria-expanded="${state.open.has(key)}">
    ${label} ${state.open.has(key) ? "▴" : "▾"}</button>`;
}

function formatDate(iso) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

// --- Today ------------------------------------------------------------------------------------

const finishKey = () => `finish-${state.plan?.date}`;

function loadPlan(plan) {
  state.plan = plan;
  state.checks = { ...(plan.draft?.checks || {}) };
  state.sets = {};
  for (const r of plan.draft?.tracker || []) {
    const name = r.exercise || "Custom";
    (state.sets[name] ||= []).push({ weight: r.weight || "", reps: r.reps || "", done: Boolean(r.done) });
  }
  for (const ex of plan.strength) {
    if (!state.sets[ex.name]) {
      state.sets[ex.name] = Array.from({ length: ex.sets || 3 }, () => ({ weight: "", reps: "", done: false }));
    }
  }
  state.extras = Object.keys(state.sets).filter((n) => !plan.strength.some((e) => e.name === n));
  state.finish = { ...FINISH_DEFAULTS, ...store.get(finishKey(), {}) };
  $date.textContent = formatDate(plan.date);
}

async function refreshPlan() {
  loadPlan(await api("api/plan"));
  if (state.tab === "today") render();
}

function draftRows() {
  const rows = [];
  for (const [exercise, sets] of Object.entries(state.sets)) {
    sets.forEach((s, i) => rows.push({ exercise, set: i + 1, weight: num(s.weight), reps: num(s.reps), done: s.done }));
  }
  return rows;
}

let saveTimer = null;
function scheduleSave() {
  setSaveState("Saving…");
  clearTimeout(saveTimer);
  saveTimer = setTimeout(saveDraft, 700);
}

async function saveDraft() {
  clearTimeout(saveTimer);
  saveTimer = null;
  if (!state.plan) return;
  try {
    await api("api/draft", {
      method: "PUT",
      body: JSON.stringify({ date: state.plan.date, tracker: draftRows(), checks: state.checks }),
    });
    setSaveState("Saved ✓");
  } catch (err) {
    if (err.status === 409) {
      toast("A new day has started: loading today's plan");
      await refreshPlan();
    } else {
      setSaveState("Not saved yet, retrying…", true);
      saveTimer = setTimeout(saveDraft, 5000);
    }
  }
}

function exerciseFor(name) {
  return state.plan.strength.find((e) => e.name === name)
    || { name, dose: null, sets: 1, why: null, images: [], steps: [], tips: [], warning: null };
}

function strengthCard(ex) {
  const sets = state.sets[ex.name] || [];
  const done = sets.filter((s) => s.done).length;
  const key = `s:${ex.name}`;
  return `<div class="card" data-card="${esc(key)}">
    <h3>${esc(ex.name)}</h3>
    <div class="sub">${esc(ex.dose || "Your own exercise")}${sets.length ? ` · ${done}/${plural(sets.length, "set")} done` : ""}</div>
    ${ex.why ? `<div class="why">${esc(ex.why)}</div>` : ""}
    ${hasHowTo(ex) ? toggleButton(key) + (state.open.has(key) ? howTo(ex) : "") : ""}
    <div class="sets">${sets.map((s, i) => setRow(ex.name, s, i)).join("")}</div>
    <div class="row-actions"><button type="button" class="btn small" data-act="add-set" data-name="${esc(ex.name)}">+ Add set</button></div>
  </div>`;
}

function setRow(name, s, i) {
  const attrs = `data-name="${esc(name)}" data-i="${i}"`;
  return `<div class="set">
    <button type="button" class="done${s.done ? " on" : ""}" data-act="done" ${attrs} aria-pressed="${s.done}" aria-label="Set ${i + 1} done">✓</button>
    <span class="n">${i + 1}</span>
    <label><input type="number" inputmode="decimal" min="0" step="2.5" value="${esc(s.weight)}" data-field="weight" ${attrs} aria-label="Set ${i + 1} weight in pounds"><span class="unit">lbs</span></label>
    <label><input type="number" inputmode="numeric" min="0" step="1" value="${esc(s.reps)}" data-field="reps" ${attrs} aria-label="Set ${i + 1} reps"><span class="unit">reps</span></label>
    <button type="button" class="remove" data-act="remove-set" ${attrs} aria-label="Remove set ${i + 1}">×</button>
  </div>`;
}

function warmupCard(ex) {
  const key = `w:${ex.name}`;
  const on = Boolean(state.checks[ex.name]);
  return `<div class="card" data-card="${esc(key)}">
    <button type="button" class="check${on ? " on" : ""}" data-act="check" data-name="${esc(ex.name)}" aria-pressed="${on}">
      <span class="box">✓</span>
      <span><span class="name">${esc(ex.name)}</span><span class="sub" style="display:block">${esc(ex.dose || "")}</span></span>
    </button>
    ${hasHowTo(ex) ? toggleButton(key) + (state.open.has(key) ? howTo(ex) : "") : ""}
  </div>`;
}

function slider(id, label, help) {
  const v = state.finish[id];
  return `<div class="slider">
    <div class="lbl"><span>${label}</span><span class="val" id="val-${id}">${v}/10</span></div>
    <input type="range" min="1" max="10" step="1" value="${v}" data-finish="${id}" aria-label="${label}">
    ${help ? `<div class="sub">${help}</div>` : ""}
  </div>`;
}

function renderToday() {
  const p = state.plan;
  if (!p) {
    $view.innerHTML = `<div class="spinner">Loading today's plan…</div>`;
    return;
  }
  const cardio = p.cardio;
  const cardioText = (cardio.text || "").replace(/^\d+ min:\s*/, "");
  $view.innerHTML = `
    <h2>1. Daily non-negotiables</h2>
    ${p.warmup.map(warmupCard).join("")}

    <h2>2. Strength &amp; stability</h2>
    ${p.strength.map(strengthCard).join("")}
    ${state.extras.map((n) => strengthCard(exerciseFor(n))).join("")}
    <button type="button" class="btn small" data-act="add-exercise">+ Add another exercise</button>

    <h2>3. Cardio</h2>
    <div class="card">
      <div class="minutes">${esc(cardio.minutes ?? "")} <small>min</small></div>
      <p>${esc(cardioText)}</p>
      ${cardio.note ? `<div class="sub">Why this length: ${esc(cardio.note)}</div>` : ""}
      ${pictures(cardio.images)}
    </div>

    ${p.cooldown?.cards?.length ? `<h2>4. Cool-down <span class="muted">(optional)</span></h2>
    <p class="small muted" style="margin-top:0">${esc(p.cooldown.note)}</p>
    ${p.cooldown.cards.map(mindCard).join("")}` : ""}

    <h2>${p.cooldown?.cards?.length ? "5" : "4"}. Finish</h2>
    <div class="card">
      ${slider("rpe", "Overall effort")}
      ${slider("pf", "Pelvic floor tightness", "Higher numbers reduce impact cardio (running) next time.")}
      ${slider("kidney", "Left kidney / flank tightness", "Above 5 makes the next workout a recovery day.")}
      <label class="sub" for="notes">Notes for the coach</label>
      <textarea id="notes" data-finish="notes" placeholder="How did it feel?">${esc(state.finish.notes)}</textarea>
      <div style="height:12px"></div>
      <button type="button" class="btn primary" data-act="complete">Complete workout</button>
    </div>`;
}

function rerenderCard(key) {
  const el = $view.querySelector(`[data-card="${CSS.escape(key)}"]`);
  if (!el) return render();
  const name = key.slice(2);
  el.outerHTML = key.startsWith("w:")
    ? warmupCard(state.plan.warmup.find((e) => e.name === name))
    : strengthCard(exerciseFor(name));
}

async function completeWorkout(btn) {
  if (!confirm("Save this workout to your History?")) return;
  btn.disabled = true;
  btn.textContent = "Saving…";
  clearTimeout(saveTimer);
  try {
    await api("api/complete", {
      method: "POST",
      body: JSON.stringify({
        rpe: Number(state.finish.rpe), pelvic_floor: Number(state.finish.pf), kidney: Number(state.finish.kidney),
        notes: state.finish.notes, tracker: draftRows(),
      }),
    });
    store.remove(finishKey());
    state.history = null;
    toast("Workout saved to History 💪 Your next plan is ready.");
    await refreshPlan();
    window.scrollTo({ top: 0 });
  } catch {
    toast("Couldn't save. Check your connection and try again.");
    btn.disabled = false;
    btn.textContent = "Complete workout";
  }
}

// --- History ----------------------------------------------------------------------------------

function chart(days) {
  if (!days.length) return `<div class="empty">No sets logged for this exercise yet.</div>`;
  const W = 340, H = 170, P = 26, n = days.length;
  const x = (i) => (n === 1 ? W / 2 : P + (i * (W - 2 * P)) / (n - 1));
  const maxW = Math.max(1, ...days.map((d) => d.top_weight_lbs));
  const maxR = Math.max(1, ...days.map((d) => d.total_reps));
  const y = (v, m) => H - P - (v / m) * (H - 2 * P);
  const path = (k, m) => days.map((d, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(d[k], m).toFixed(1)}`).join(" ");
  const dots = (k, m, color) => days.map((d, i) =>
    `<circle cx="${x(i).toFixed(1)}" cy="${y(d[k], m).toFixed(1)}" r="4" style="fill:${color}"><title>${esc(d.date)}: ${d[k]}</title></circle>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Heaviest weight and total reps by day">
      <line x1="${P}" y1="${H - P}" x2="${W - P}" y2="${H - P}" style="stroke:var(--line)"/>
      <path d="${path("total_reps", maxR)}" style="fill:none;stroke:var(--ok);stroke-width:2;stroke-dasharray:5 4"/>
      <path d="${path("top_weight_lbs", maxW)}" style="fill:none;stroke:var(--accent);stroke-width:2.5"/>
      ${dots("total_reps", maxR, "var(--ok)")}${dots("top_weight_lbs", maxW, "var(--accent)")}
      <text x="${P}" y="14" style="fill:var(--muted);font-size:11px">top: ${maxW} lbs · ${maxR} reps</text>
      <text x="${P}" y="${H - 6}" style="fill:var(--muted);font-size:11px">${esc(days[0].date)}</text>
      ${n > 1 ? `<text x="${W - P}" y="${H - 6}" text-anchor="end" style="fill:var(--muted);font-size:11px">${esc(days[n - 1].date)}</text>` : ""}
    </svg>
    <div class="legend"><span><i style="background:var(--accent)"></i>Heaviest lbs</span><span><i style="background:var(--ok)"></i>Total reps</span></div>`;
}

async function loadProgress(exercise) {
  state.progress = { exercise, days: (await api(`api/progress?exercise=${encodeURIComponent(exercise)}`)).days };
  const el = document.getElementById("chart");
  if (el) el.innerHTML = chart(state.progress.days);
}

function workoutCard(w) {
  const key = `h:${w.id}`;
  const open = state.open.has(key);
  const sets = w.sets.map((s) => `<tr><td>${esc(s.exercise)}</td><td>${s.set_number ?? ""}</td><td>${s.weight_lbs ?? ""}</td><td>${s.reps ?? ""}</td><td>${s.done ? "✓" : ""}</td></tr>`).join("");
  return `<div class="card">
    <button type="button" class="result" data-act="toggle" data-key="${esc(key)}" aria-expanded="${open}">
      <h3>${esc(formatDate(w.date))}</h3>
      <div class="stats">
        <span class="pill">Effort ${w.rpe ?? "?"}/10</span>
        <span class="pill">Flank ${w.kidney_flank_pain ?? "?"}/10</span>
        <span class="pill">Pelvic floor ${w.pelvic_floor_tightness ?? "?"}/10</span>
        ${w.sets.length ? `<span class="pill">${plural(w.sets.filter((s) => s.done).length, "set")}</span>` : ""}
      </div>
    </button>
    ${open ? `<div class="howto">
      ${w.workout?.strength?.length ? `<div class="small"><strong>Exercises:</strong> ${esc(w.workout.strength.join(", "))}</div>` : ""}
      ${w.workout?.cardio ? `<div class="small"><strong>Cardio:</strong> ${esc(w.workout.cardio)}</div>` : ""}
      ${sets ? `<table><thead><tr><th>Exercise</th><th>Set</th><th>lbs</th><th>Reps</th><th>✓</th></tr></thead><tbody>${sets}</tbody></table>` : ""}
      ${w.notes ? `<pre class="notes">${esc(w.notes)}</pre>` : ""}
    </div>` : ""}
  </div>`;
}

async function renderHistory() {
  if (!state.history) {
    $view.innerHTML = `<div class="spinner">Loading history…</div>`;
    state.history = await api("api/history");
    if (state.tab !== "history") return;
  }
  const { workouts, exercises } = state.history;
  if (!workouts.length) {
    $view.innerHTML = `<div class="empty">No completed workouts yet.<br>Press <strong>Complete workout</strong> at the end of Today to save one.</div>`;
    return;
  }
  if (exercises.length && !exercises.includes(state.progress.exercise)) {
    state.progress = { exercise: exercises[0], days: [] };
    loadProgress(exercises[0]);
  }
  $view.innerHTML = `
    ${exercises.length ? `<h2>Progress</h2>
    <div class="card">
      <select data-act-change="progress" aria-label="Exercise" style="width:100%;height:44px;border-radius:10px;border:1px solid var(--line);background:var(--card-2);padding:0 10px">
        ${exercises.map((e) => `<option${e === state.progress.exercise ? " selected" : ""}>${esc(e)}</option>`).join("")}
      </select>
      <div id="chart" class="chart">${chart(state.progress.days)}</div>
    </div>` : ""}
    <h2>Completed workouts (${workouts.length})</h2>
    ${workouts.map(workoutCard).join("")}
    <button type="button" class="btn small" data-act="report">Make an HTML progress report (AI Coach)</button>`;
}

// --- Coach ------------------------------------------------------------------------------------

function connectCard() {
  const c = state.claude;
  if (!c || c.signed_in) return "";
  if (!c.cli) return `<div class="card warning">The Claude command-line tool isn't installed in this add-on, so the coach can't sign in.</div>`;
  const l = c.login;
  const failed = l && l.done && l.result && !c.signed_in;
  if (l && !l.done) {
    return `<div class="card">
      <h3>Connect Claude</h3>
      ${l.url ? `<p class="sub">1. Open the link and approve. 2. Paste the code it shows here.</p>
        <p><a class="btn primary" style="display:grid;place-items:center;text-decoration:none" href="${esc(l.url)}" target="_blank" rel="noopener">Open Claude sign-in</a></p>
        <div class="composer" style="position:static;padding:0"><input id="claude-code" class="code-input" placeholder="Paste code" autocomplete="off" aria-label="Sign-in code">
        <button type="button" class="btn primary" style="width:auto" data-act="claude-code">Connect</button></div>`
        : `<p class="sub">Getting a sign-in link…</p>`}
      <button type="button" class="btn link" data-act="claude-cancel">Cancel</button></div>`;
  }
  return `<div class="card warning">
    <p style="margin:0 0 8px">${failed ? esc(l.result) : "The coach needs to be connected to your Claude account."}</p>
    <button type="button" class="btn primary" data-act="claude-login">Connect Claude</button></div>`;
}

async function loadClaude() {
  try { state.claude = await api("api/claude"); } catch { /* keep the old state */ }
  if ((state.tab === "coach" || state.tab === "settings") && !document.activeElement?.matches?.("#claude-code, #coach-input")) render();
  clearTimeout(claudePoll);
  const l = state.claude && state.claude.login;
  if (l && !l.done) claudePoll = setTimeout(loadClaude, 2000);
}
let claudePoll;

function renderCoach() {
  if (!state.claude) loadClaude();
  const signedOut = state.claude && !state.claude.signed_in;
  $view.innerHTML = `
    ${signedOut ? `<div class="card warning"><p style="margin:0 0 8px">The coach isn't connected to your Claude account yet.</p>
      <button type="button" class="btn primary" data-act="goto-settings">Connect in Settings</button></div>` : ""}
    <div class="chat">
      ${state.coach.map((m) => `<div class="msg ${m.role}${m.error ? " error" : ""}">${esc(m.content)}</div>`).join("")}
      ${state.coachBusy ? `<div class="msg assistant muted">Coach is thinking…</div>` : ""}
    </div>
    <div class="composer">
      <textarea id="coach-input" placeholder="E.g. my kidney is tight today…" aria-label="Message the coach"></textarea>
      <button type="button" class="btn primary" style="width:auto" data-act="send" ${state.coachBusy || signedOut ? "disabled" : ""}>Send</button>
    </div>`;
  if (!signedOut) window.scrollTo({ top: document.body.scrollHeight });
}

async function sendCoach() {
  const input = document.getElementById("coach-input");
  const message = input.value.trim();
  if (!message || state.coachBusy) return;
  const recent = state.coach.slice(-6);
  state.coach.push({ role: "user", content: message });
  state.coachBusy = true;
  renderCoach();
  try {
    const res = await api("api/coach", { method: "POST", body: JSON.stringify({ message, recent }) });
    state.coach.push(res.error
      ? { role: "assistant", content: `Coach hit an error: ${res.error}`, error: true }
      : { role: "assistant", content: res.reply || "(no reply)" });
  } catch {
    state.coach.push({ role: "assistant", content: "Couldn't reach the coach. Check your connection.", error: true });
  }
  state.coachBusy = false;
  if (state.coach[state.coach.length - 1].error) state.claude = null;  // re-check sign-in after a failure
  store.set("coach", state.coach.slice(-50));
  if (state.tab === "coach") renderCoach();
}

// --- Settings ---------------------------------------------------------------------------------
// One tab for everything you can change. New sections (sports, training goals) go in as more cards.

async function renderSettings() {
  if (!state.claude) loadClaude();
  if (!state.settings) state.settings = await api("api/settings");
  const s = state.settings;
  const mine = new Set(s.equipment);
  const c = state.claude;
  $view.innerHTML = `
    <h2>Equipment</h2>
    <div class="card">
      <p class="sub" style="margin:0 0 10px">Daily plans only use what's ticked. Barbell moves stay out of your plans for your kidney either way.</p>
      <div class="chips wrap">${s.equipment_options.map((o) =>
        `<button type="button" class="chip${mine.has(o) ? " on" : ""}" data-act="equip" data-v="${esc(o)}" aria-pressed="${mine.has(o)}">${esc(o)}</button>`).join("")}</div>
    </div>
    <div class="card">
      <label class="sub" for="gear-notes">Gear details (the coach reads this: weights, plates, tensions)</label>
      <textarea id="gear-notes" style="min-height:150px">${esc(s.gear_notes)}</textarea>
      <div class="row-actions"><button type="button" class="btn small" data-act="save-gear">Save gear details</button></div>
    </div>
    <h2>Yoga pictures</h2>
    ${s.media_private ? `<div class="card"><h3>Private bucket connected</h3><p class="sub">Pictures load from your private Backblaze B2 bucket through this add-on.</p></div>`
    : `<div class="card">
      <p class="sub" style="margin:0 0 10px">For a private bucket, fill in the bucket settings (endpoint, name, key) in this add-on's Configuration tab, the same as for the Trading Terminal. Or, for a public folder, paste its address:</p>
      <label class="sub" for="media-url">Address of the folder holding the yoga pictures (starts with https://)</label>
      <input type="url" id="media-url" class="code-input" style="width:100%" value="${esc(s.media_base_url)}" placeholder="https://…/workout/yoga">
      <div class="row-actions"><button type="button" class="btn small" data-act="save-media">Save</button></div>
    </div>`}
    <h2>AI Coach</h2>
    ${c && c.signed_in
      ? `<div class="card"><h3>Claude connected</h3><p class="sub">The coach uses your Claude subscription.</p>
         <button type="button" class="btn small" data-act="claude-logout">Disconnect Claude</button></div>`
      : connectCard() || `<div class="card muted">Checking Claude…</div>`}
    `;
}

// --- Mind & Body: yoga, qigong ----------------------------------------------------------------

function findMind(name) {
  const pools = [state.mind?.yoga, state.mind?.qigong, state.plan?.cooldown?.cards];
  for (const pool of pools) { const hit = (pool || []).find((e) => e.name === name); if (hit) return hit; }
  return null;
}

function mindCard(e) {
  const key = `m:${e.name}`;
  const open = state.open.has(key);
  return `<div class="card" data-card="${esc(key)}">
    <button type="button" class="result" data-act="toggle" data-key="${esc(key)}" aria-expanded="${open}">
      <h3>${esc(e.name)}</h3>
      <div class="stats">
        ${e.category ? `<span class="badge">${esc(e.category)}</span>` : ""}
        ${e.level ? `<span class="badge">${esc(e.level)}</span>` : ""}
        ${e.cooldown ? `<span class="badge">cool-down</span>` : ""}
        ${e.safe ? "" : `<span class="badge bad">not in auto picks</span>`}
      </div>
    </button>
    ${open ? howTo(e) : ""}
  </div>`;
}

// Meditation: guided audio streamed from The Holistic Care, plus a script Claude writes and the phone reads aloud.
const speech = { queue: [], on: false };

function stopSpeaking() {
  speech.on = false;
  speech.queue = [];
  try { window.speechSynthesis.cancel(); } catch { /* not supported */ }
}

function speakScript(text) {
  if (!("speechSynthesis" in window)) { toast("This browser can't read aloud"); return; }
  stopSpeaking();
  speech.on = true;
  speech.queue = text.split(/\n+/).map((p) => p.trim()).filter(Boolean);
  const next = () => {
    if (!speech.on || !speech.queue.length) { speech.on = false; return; }
    const u = new SpeechSynthesisUtterance(speech.queue.shift().replace(/\.{3}/g, ", , ,"));
    u.rate = 0.82;
    u.onend = () => setTimeout(next, 2500);   // a breath between paragraphs
    u.onerror = () => { speech.on = false; };
    window.speechSynthesis.speak(u);
  };
  next();
}

function meditationSection() {
  const md = state.med;
  const f = state.medFilter;
  if (!md) return `<h2>Meditation</h2><div class="spinner">Loading…</div>`;
  const list = md.practices.filter((p) => f === "all" || p.category === f);
  const shown = list.slice(0, state.medShown);
  return `<h2>Meditation</h2>
    <div class="card">
      <h3>A session written for you</h3>
      <p class="sub">Claude writes a calm script (slow breathing, long exhales, no straining) and your phone reads it aloud.</p>
      <div class="two-col">
        <select id="med-minutes" aria-label="Length">${[3, 5, 10].map((m) => `<option value="${m}"${m === state.medMinutes ? " selected" : ""}>${m} minutes</option>`).join("")}</select>
        <input class="code-input" id="med-focus" placeholder="Focus (optional)" value="${esc(state.medFocus)}" aria-label="Focus">
      </div>
      <div class="row-actions">
        <button type="button" class="btn small" data-act="med-script" ${state.medBusy ? "disabled" : ""}>${state.medBusy ? "Writing…" : "Write my session"}</button>
        ${state.medScript ? `<button type="button" class="btn small" data-act="med-read">▶ Read aloud</button>
          <button type="button" class="btn small" data-act="med-stop">■ Stop</button>` : ""}
      </div>
      ${state.medError ? `<div class="warning" style="margin-top:8px">${esc(state.medError)}</div>` : ""}
      ${state.medScript ? `<pre class="notes">${esc(state.medScript)}</pre>` : ""}
    </div>
    ${md.error ? `<div class="card warning">${esc(md.error)}</div>` : `
    <div class="chips" style="margin:8px 0">${[{ id: "all", label: "All" }, ...md.categories].map((c) =>
      `<button type="button" class="chip${f === c.id ? " on" : ""}" data-act="med-filter" data-v="${esc(c.id)}">${esc(c.label)}</button>`).join("")}</div>
    ${shown.map((p) => `<div class="card">
      <h3>${esc(p.title)}</h3>
      <div class="stats"><span class="badge">${esc(p.label)}</span>${p.minutes ? `<span class="badge">~${p.minutes} min</span>` : ""}</div>
      <p class="sub">${esc(p.excerpt || "")}</p>
      <audio controls preload="none" src="${esc(p.audio_url)}" style="width:100%"></audio>
    </div>`).join("")}
    ${list.length > shown.length ? `<button type="button" class="btn small" data-act="med-more">Show more</button>` : ""}
    <p class="small muted">${esc(md.credit)}</p>`}`;
}

async function renderMindBody() {
  if (!state.mind) state.mind = await api("api/mindbody");
  if (!state.med) {
    api("api/meditation").then((r) => { if (!r.error) state.med = r; else state.med = { ...r, practices: [] }; if (state.tab === "mind") render(); })
      .catch(() => { state.med = { practices: [], categories: [], error: "Couldn't reach the meditation library." }; if (state.tab === "mind") render(); });
  }
  const m = state.mind;
  const f = state.mindFilter;
  const yoga = m.yoga.filter((e) => (f === "all" || (f === "cooldown" && e.cooldown) || (f === "pictures" && e.images.length))
    && (!state.mindQ || e.name.toLowerCase().includes(state.mindQ)));
  $view.innerHTML = `
    ${meditationSection()}
    <h2>Qigong</h2>
    <p class="small muted" style="margin-top:0">Baduanjin (eight pieces of brocade), adjusted for your kidney: head-only turns, hips square, folds only as far as is comfortable.</p>
    ${m.qigong.map(mindCard).join("")}
    <h2>Yoga</h2>
    <div class="filters">
      <input type="search" id="mind-q" placeholder="Search poses…" value="${esc(state.mindQ)}" aria-label="Search yoga poses">
      <div class="chips">${[["all", "All"], ["cooldown", "Cool-down"], ["pictures", "With pictures"]].map(([v, l]) =>
        `<button type="button" class="chip${f === v ? " on" : ""}" data-act="mind-filter" data-v="${v}">${l}</button>`).join("")}</div>
    </div>
    ${yoga.length ? yoga.map(mindCard).join("") : `<div class="empty">No poses match.</div>`}
    ${m.media_base ? "" : `<p class="small muted">Pictures are off: set the media address in Settings.</p>`}
    <footer class="credits">Yoga pictures: Yoga Posture Dataset on Kaggle (CC0). General wellness guidance, not medical advice.</footer>`;
}

// --- Library ----------------------------------------------------------------------------------

const FOCUS = [["", "All"], ["legs", "Legs"], ["upper back", "Upper back"], ["core", "Core"], ["mobility", "Mobility"], ["balance", "Balance"]];

async function searchLibrary(append = false) {
  const L = state.lib;
  L.offset = append ? L.offset + 25 : 0;
  const params = new URLSearchParams({
    q: L.q, focus: L.focus, muscle: L.muscle, equipment: L.equipment,
    pictures: L.pictures, filtered: L.filtered, offset: L.offset, limit: 25,
  });
  const data = await api(`api/library?${params}`);
  L.data = data;
  L.results = append ? L.results.concat(data.results) : data.results;
  if (state.tab === "library") renderLibraryResults();
}

function libraryCard(e, i) {
  const key = `l:${e.name}`;
  const open = state.open.has(key);
  return `<div class="card">
    <button type="button" class="result" data-act="toggle" data-key="${esc(key)}" data-lib="${i}" aria-expanded="${open}">
      <h3>${esc(e.name)}</h3>
      <div class="stats">
        <span class="badge">${esc(e.equipment)}</span>
        ${e.level ? `<span class="badge">${esc(e.level)}</span>` : ""}
        ${e.safe ? "" : `<span class="badge bad">filtered out</span>`}
      </div>
    </button>
    ${open ? howTo(e) : ""}
  </div>`;
}

function renderLibraryResults() {
  const L = state.lib;
  const box = document.getElementById("lib-results");
  if (!box || !L.data) return;
  const d = L.data;
  for (const [id, options, value] of [["lib-muscle", d.muscles, L.muscle], ["lib-equipment", d.equipment, L.equipment]]) {
    const sel = document.getElementById(id);
    if (sel && sel.options.length <= 1) {
      sel.insertAdjacentHTML("beforeend", options.map((o) => `<option${o === value ? " selected" : ""}>${esc(o)}</option>`).join(""));
    }
  }
  const ninjas = state.status?.ninjas;
  document.getElementById("lib-counts").innerHTML =
    `${d.all.toLocaleString()} exercises · ${d.safe.toLocaleString()} safe for you · ${(d.all - d.safe).toLocaleString()} filtered out for your kidney, pelvic floor or core`
    + (ninjas ? `<br>API Ninjas: ${ninjas.exercises.toLocaleString()} collected so far (${ninjas.complete ? "all collected" : "still collecting in the background"})` : "");
  box.innerHTML = `<p><strong>${d.total.toLocaleString()} matches</strong></p>`
    + L.results.map(libraryCard).join("")
    + (L.results.length < d.total ? `<button type="button" class="btn small" data-act="more">Show more</button>` : "");
}

function renderLibrary() {
  const L = state.lib;
  $view.innerHTML = `
    <div class="filters">
      <input type="search" id="lib-q" placeholder="Search, e.g. glute bridge" value="${esc(L.q)}" aria-label="Search exercises">
      <div class="chips">${FOCUS.map(([v, label]) => `<button type="button" class="chip${L.focus === v ? " on" : ""}" data-act="focus" data-v="${esc(v)}">${label}</button>`).join("")}</div>
      <div class="two-col">
        <select id="lib-muscle" aria-label="Muscle"><option value="">Any muscle</option></select>
        <select id="lib-equipment" aria-label="Equipment"><option value="">Any equipment</option></select>
      </div>
      <div class="two-col">
        <label class="toggle"><input type="checkbox" id="lib-pictures" ${L.pictures ? "checked" : ""}> With pictures</label>
        <label class="toggle"><input type="checkbox" id="lib-filtered" ${L.filtered ? "checked" : ""}> Show filtered-out</label>
      </div>
      <div id="lib-counts" class="small muted"></div>
    </div>
    <div id="lib-results"><div class="spinner">Loading…</div></div>
    <footer class="credits">${esc(state.status?.credits || "")}</footer>`;
  if (L.data) renderLibraryResults();
  else searchLibrary().catch(() => toast("Couldn't load the library"));
}

// --- Events -----------------------------------------------------------------------------------

const actions = {
  toggle(el) {
    const key = el.dataset.key;
    state.open.has(key) ? state.open.delete(key) : state.open.add(key);
    if (key.startsWith("w:") || key.startsWith("s:")) rerenderCard(key);
    else if (key.startsWith("m:")) {   // redraw just this card so a playing meditation isn't interrupted
      const card = $view.querySelector(`[data-card="${CSS.escape(key)}"]`);
      const e = findMind(key.slice(2));
      if (card && e) card.outerHTML = mindCard(e); else render();
    } else render();
  },
  check(el) {
    const name = el.dataset.name;
    state.checks[name] = !state.checks[name];
    rerenderCard(`w:${name}`);
    scheduleSave();
  },
  done(el) {
    const s = state.sets[el.dataset.name][Number(el.dataset.i)];
    s.done = !s.done;
    rerenderCard(`s:${el.dataset.name}`);
    scheduleSave();
  },
  "add-set"(el) {
    const sets = state.sets[el.dataset.name];
    const last = sets[sets.length - 1] || { weight: "", reps: "" };
    sets.push({ weight: last.weight, reps: last.reps, done: false });
    rerenderCard(`s:${el.dataset.name}`);
    scheduleSave();
  },
  "remove-set"(el) {
    state.sets[el.dataset.name].splice(Number(el.dataset.i), 1);
    rerenderCard(`s:${el.dataset.name}`);
    scheduleSave();
  },
  "add-exercise"() {
    const name = (prompt("Exercise name") || "").trim();
    if (!name) return;
    if (!state.sets[name]) {
      state.sets[name] = [{ weight: "", reps: "", done: false }];
      state.extras.push(name);
    }
    render();
    scheduleSave();
  },
  complete(el) { completeWorkout(el); },
  send() { sendCoach(); },
  "mind-filter"(el) { state.mindFilter = el.dataset.v; render(); },
  "med-filter"(el) { state.medFilter = el.dataset.v; state.medShown = 10; render(); },
  "med-more"() { state.medShown += 10; render(); },
  "med-read"() { speakScript(state.medScript); },
  "med-stop"() { stopSpeaking(); },
  async "med-script"() {
    state.medMinutes = Number(document.getElementById("med-minutes").value);
    state.medFocus = document.getElementById("med-focus").value;
    state.medBusy = true; state.medError = ""; render();
    try {
      const r = await api("api/meditation/script", { method: "POST", body: JSON.stringify({ minutes: state.medMinutes, focus: state.medFocus }) });
      if (r.error) state.medError = `Couldn't write the session: ${r.error}`; else state.medScript = r.script;
    } catch { state.medError = "Couldn't reach the coach."; }
    state.medBusy = false; render();
  },
  "goto-settings"() { history.replaceState(null, "", "#settings"); showTab("settings"); },
  async "save-media"() {
    try {
      state.settings = await api("api/settings", { method: "PUT", body: JSON.stringify({ media_base_url: document.getElementById("media-url").value }) });
      state.mind = null;
      toast("Saved");
    } catch { toast("That address must start with https://"); }
  },
  async "save-gear"() {
    try {
      state.settings = await api("api/settings", { method: "PUT", body: JSON.stringify({ gear_notes: document.getElementById("gear-notes").value }) });
      toast("Saved");
    } catch { toast("Couldn't save"); }
  },
  async equip(el) {
    const s = state.settings;
    const v = el.dataset.v;
    const next = new Set(s.equipment);
    next.has(v) ? next.delete(v) : next.add(v);
    next.add("bodyweight");
    s.equipment = [...next];
    el.classList.toggle("on", next.has(v));
    try {
      state.settings = await api("api/settings", { method: "PUT", body: JSON.stringify({ equipment: s.equipment }) });
      if (saveTimer) await saveDraft();   // keep any sets already typed, then rebuild today's plan
      refreshPlan().catch(() => {});
      toast("Saved");
    } catch { toast("Couldn't save"); }
    renderSettings();
  },
  async "claude-login"() { state.claude = await api("api/claude/login", { method: "POST" }); render(); loadClaude(); },
  async "claude-code"() {
    const code = document.getElementById("claude-code").value.trim();
    if (!code) return;
    state.claude = await api("api/claude/code", { method: "POST", body: JSON.stringify({ code }) });
    render();
    toast(state.claude.signed_in ? "Claude connected" : "Checking the code…");
    loadClaude();
  },
  async "claude-cancel"() { state.claude = await api("api/claude/cancel", { method: "POST" }); render(); },
  async "claude-logout"() { state.claude = await api("api/claude/logout", { method: "POST" }); render(); },
  focus(el) {
    state.lib.focus = el.dataset.v;
    $view.querySelectorAll(".chip").forEach((c) => c.classList.toggle("on", c.dataset.v === state.lib.focus));
    searchLibrary();
  },
  more() { searchLibrary(true); },
  async report(el) {
    el.disabled = true;
    el.textContent = "Making the report (a few minutes)…";
    try {
      const res = await api("api/report", { method: "POST" });
      toast(res.ok ? `Report saved to ${res.path}` : `Report failed: ${res.error}`);
    } catch { toast("Couldn't make the report"); }
    el.disabled = false;
    el.textContent = "Make an HTML progress report (AI Coach)";
  },
};

$view.addEventListener("click", (e) => {
  const el = e.target.closest("[data-act]");
  if (el && actions[el.dataset.act]) actions[el.dataset.act](el, e);
});

let searchTimer;
$view.addEventListener("input", (e) => {
  const t = e.target;
  if (t.dataset.field) {
    state.sets[t.dataset.name][Number(t.dataset.i)][t.dataset.field] = t.value;
    scheduleSave();
  } else if (t.dataset.finish) {
    state.finish[t.dataset.finish] = t.value;
    const label = document.getElementById(`val-${t.dataset.finish}`);
    if (label) label.textContent = `${t.value}/10`;
    store.set(finishKey(), state.finish);
  } else if (t.id === "mind-q") {
    state.mindQ = t.value.trim().toLowerCase();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { render(); const q = document.getElementById("mind-q"); q.focus(); q.setSelectionRange(q.value.length, q.value.length); }, 250);
  } else if (t.id === "lib-q") {
    state.lib.q = t.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => searchLibrary(), 300);
  }
});

$view.addEventListener("change", (e) => {
  const t = e.target;
  if (t.dataset.actChange === "progress") loadProgress(t.value);
  else if (t.id === "lib-muscle") { state.lib.muscle = t.value; searchLibrary(); }
  else if (t.id === "lib-equipment") { state.lib.equipment = t.value; searchLibrary(); }
  else if (t.id === "lib-pictures") { state.lib.pictures = t.checked; searchLibrary(); }
  else if (t.id === "lib-filtered") { state.lib.filtered = t.checked; searchLibrary(); }
});

// Save right away when the phone locks or the app goes to the background
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden" && saveTimer) saveDraft();
  if (document.visibilityState === "visible" && state.plan) {
    api("api/plan").then((p) => { if (p.date !== state.plan.date) { loadPlan(p); render(); } }).catch(() => {});
  }
});

// --- Tabs -------------------------------------------------------------------------------------

function render() {
  const views = { today: renderToday, history: renderHistory, coach: renderCoach, library: renderLibrary, mind: renderMindBody, settings: renderSettings };
  Promise.resolve(views[state.tab]()).catch(() => {
    $view.innerHTML = `<div class="empty">Couldn't load this page. Pull down to refresh or try again.</div>`;
  });
}

function showTab(tab) {
  if (!["today", "history", "coach", "library", "mind", "settings"].includes(tab)) tab = "today";
  state.tab = tab;
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  if (tab === "history") state.history = null;   // always fresh
  render();
  window.scrollTo({ top: 0 });
}

document.querySelector(".tabs").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-tab]");
  if (b) history.replaceState(null, "", `#${b.dataset.tab}`), showTab(b.dataset.tab);
});

api("api/status").then((s) => { state.status = s; if (state.tab === "coach" || state.tab === "library") render(); }).catch(() => {});
showTab(location.hash.slice(1) || "today");
refreshPlan().catch(() => {
  $view.innerHTML = `<div class="empty">Couldn't load today's plan. Check that the add-on is running, then reload.</div>`;
});
