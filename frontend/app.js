// Cliente desacoplado de la API REST de neumonía (spec 012).
// Estados: idle → loading → success | error. Toda la inferencia ocurre en el backend.
"use strict";

const API = String(window.NEUMONIA_API || "http://localhost:8000").replace(/\/+$/, "");
const TIMEOUT_MS = Number(window.NEUMONIA_TIMEOUT_MS || 120000);

const CLASS_LABELS = { bacteriana: "Bacteriana", normal: "Sin hallazgos", viral: "Viral" };
const SEX = { F: "Femenino", M: "Masculino", O: "Otro" };
const VIEW = { AP: "AP (anteroposterior)", PA: "PA (posteroanterior)", LL: "Lateral", LATERAL: "Lateral" };
const MODALITY = { DX: "Radiografía digital (DX)", CR: "Radiografía computarizada (CR)" };
const BODY_PART = { CHEST: "Tórax" };

const ZONES = {
  derecho_superior: "Der. superior",
  derecho_medio: "Der. medio",
  derecho_inferior: "Der. inferior",
  izquierdo_superior: "Izq. superior",
  izquierdo_medio: "Izq. medio",
  izquierdo_inferior: "Izq. inferior",
};
const LATERALITY = {
  derecho: "Pulmón derecho",
  izquierdo: "Pulmón izquierdo",
  bilateral: "Bilateral",
  sin_foco: "Difusa (sin foco)",
};
const SEGMENTATION = {
  pspnet: "Silueta pulmonar segmentada (PSPNet)",
  geometrica: "Zonas geométricas aproximadas",
};

const $ = (id) => document.getElementById(id);

function percent(value) {
  return `${(Number(value) * 100).toFixed(2)} %`;
}

function validatePatient(raw) {
  const value = raw.trim();
  if (!value) return null; // opcional: solo se muestra en el panel, no se envía a la API
  return /^\d{5,15}$/.test(value) ? null : "El documento debe tener entre 5 y 15 dígitos.";
}

// Mismas filas que `presenter.patient_rows` del backend: nunca PatientName.
function patientRows(metadata, patientId, filename) {
  const m = metadata || {};
  const rows = [["Documento", patientId.trim() || "No ingresado"]];
  if (m.patient_code) rows.push(["Código del paciente", String(m.patient_code)]);
  if (m.dataset_code) rows.push(["Código en el dataset", String(m.dataset_code)]);
  if (m.age !== undefined) rows.push(["Edad", `${m.age} años`]);
  if (m.sex) rows.push(["Sexo", SEX[m.sex] || String(m.sex)]);
  if (m.view_position) {
    const v = String(m.view_position).toUpperCase();
    rows.push(["Proyección", VIEW[v] || v]);
  }
  if (m.modality) {
    const mod = String(m.modality).toUpperCase();
    rows.push(["Modalidad", MODALITY[mod] || mod]);
  }
  if (m.body_part) {
    const part = String(m.body_part).toUpperCase();
    rows.push(["Región", BODY_PART[part] || part.charAt(0) + part.slice(1).toLowerCase()]);
  }
  if (m.rows && m.columns) rows.push(["Imagen", `${m.columns} × ${m.rows} px`]);
  if (Object.keys(m).length === 0) rows.push(["Metadatos", "No disponibles (imagen JPG o PNG)"]);
  if (filename) rows.push(["Archivo", filename]);
  return rows;
}

// Traduce la respuesta de error de la API (422 de FastAPI o 500 {error}) a un texto legible.
function errorMessage(status, body) {
  if (body && Array.isArray(body.detail) && body.detail.length) {
    return `Entrada inválida (${status}): ${body.detail.map((d) => d.msg).join("; ")}`;
  }
  if (body && typeof body.detail === "string") return `Error ${status}: ${body.detail}`;
  if (body && body.error) return `Error ${status}: ${body.error}`;
  return `La API respondió ${status}.`;
}

function setState(name) {
  document.querySelectorAll(".state").forEach((el) => {
    el.hidden = el.dataset.state !== name;
  });
  document.body.dataset.state = name;
}

function fillList(dl, rows) {
  dl.replaceChildren();
  for (const [label, value] of rows) {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value; // textContent: los metadatos nunca se interpretan como HTML
    dl.append(dt, dd);
  }
}

async function checkHealth() {
  const dot = $("api-dot");
  const text = $("api-text");
  try {
    const res = await fetch(`${API}/health`, { signal: AbortSignal.timeout(5000) });
    const body = await res.json();
    dot.className = body.model_loaded ? "dot ok" : "dot warn";
    text.textContent = `API ${API} · ${body.model_version} · ${
      body.model_loaded ? "modelo cargado" : "modelo sin cargar"
    }`;
  } catch {
    dot.className = "dot down";
    text.textContent = `API no disponible en ${API} (ejecuta make backend)`;
  }
}

let lastSubmit = null;
let timer = null;

async function predict(file, patientId) {
  lastSubmit = { file, patientId };
  $("patient-panel").hidden = true; // no dejar datos de un paciente anterior en pantalla
  setState("loading");
  $("submit").disabled = true;
  const started = performance.now();
  timer = setInterval(() => {
    $("elapsed").textContent = ((performance.now() - started) / 1000).toFixed(1);
  }, 100);

  const form = new FormData();
  form.append("file", file, file.name);
  try {
    const res = await fetch(`${API}/predict`, {
      method: "POST",
      body: form,
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    const body = await res.json().catch(() => null);
    if (!res.ok) throw new Error(errorMessage(res.status, body));
    const roundTrip = performance.now() - started;
    showResult(body, file, patientId, res.headers.get("X-Process-Time-ms"), roundTrip);
  } catch (err) {
    const msg =
      err.name === "TimeoutError"
        ? `La API no respondió en ${TIMEOUT_MS / 1000} s.`
        : err instanceof TypeError
          ? `No hay conexión con la API en ${API}. ¿Está corriendo make backend?`
          : err.message;
    $("error-text").textContent = msg;
    setState("error");
  } finally {
    clearInterval(timer);
    $("submit").disabled = !$("file").files.length;
  }
}

// ---------- Informe detallado (findings de la API) ----------
function renderReport(findings) {
  const has = Boolean(findings && findings.zone_attention);
  $("inf-empty").hidden = has;
  $("inf-body").hidden = !has;
  if (!has) return;
  const summary = $("inf-summary");
  summary.replaceChildren();
  for (const line of findings.summary || []) {
    const li = document.createElement("li");
    li.textContent = line;
    summary.append(li);
  }
  $("inf-warning").hidden = !findings.shortcut_warning;
  const zones = $("inf-zones");
  zones.replaceChildren();
  for (const [zone, value] of Object.entries(findings.zone_attention)) {
    const tr = document.createElement("tr");
    const dominant = zone === findings.dominant_zone;
    for (const text of [ZONES[zone] || zone, percent(value), dominant ? "◀ dominante" : ""]) {
      const td = document.createElement("td");
      td.textContent = text;
      tr.append(td);
    }
    if (dominant) tr.className = "dominant";
    zones.append(tr);
  }
  const ratio = Number(findings.outside_inside_ratio || 0).toFixed(2);
  const rows = [
    ["Lateralidad", LATERALITY[findings.laterality] || findings.laterality],
    ["Extensión de alta atención", `${Number(findings.extent_pct).toFixed(0)} % del área pulmonar`],
    ["Atención fuera del pulmón", `${Number(findings.out_of_lung_pct).toFixed(0)} % (razón ${ratio})`],
    ["Delimitación pulmonar", SEGMENTATION[findings.lung_source] || findings.lung_source],
  ];
  if (findings.lung_note) rows.push(["Nota", findings.lung_note]);
  fillList($("inf-facts"), rows);
}

// ---------- Vista 3D: superficie de la rejilla Grad-CAM en canvas (sin librerías) ----------
function jet(v) {
  const x = Math.max(0, Math.min(1, v));
  const r = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * x - 3)));
  const g = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * x - 2)));
  const b = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * x - 1)));
  return `rgb(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)})`;
}

const view3d = { grid: null, az: -0.6, el: 0.75 };

function drawSurface() {
  const canvas = $("v3d");
  const grid = view3d.grid;
  if (!canvas || !grid || !grid.length) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const n = grid.length;
  const m = grid[0].length;
  const ca = Math.cos(view3d.az);
  const sa = Math.sin(view3d.az);
  const ce = Math.cos(view3d.el);
  const se = Math.sin(view3d.el);
  const scale = Math.min(W, H) * 0.42;
  const project = (i, j, z) => {
    const x = (j / (m - 1)) * 2 - 1; // izquierda→derecha de la imagen
    const y = (i / (n - 1)) * 2 - 1; // arriba→abajo de la imagen
    const zz = z * 0.7;
    const xr = x * ca - y * sa;
    const yr = x * sa + y * ca;
    const depth = yr * ce + zz * se;
    const sy = yr * se - zz * ce;
    return [W / 2 + xr * scale, H / 2 + sy * scale * 0.9, depth];
  };
  const quads = [];
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < m - 1; j++) {
      const v = (grid[i][j] + grid[i + 1][j] + grid[i][j + 1] + grid[i + 1][j + 1]) / 4;
      const p = [
        project(i, j, grid[i][j]),
        project(i, j + 1, grid[i][j + 1]),
        project(i + 1, j + 1, grid[i + 1][j + 1]),
        project(i + 1, j, grid[i + 1][j]),
      ];
      quads.push({ p, v, d: (p[0][2] + p[1][2] + p[2][2] + p[3][2]) / 4 });
    }
  }
  quads.sort((a, b) => b.d - a.d); // algoritmo del pintor: lo lejano primero
  ctx.lineWidth = 0.4;
  ctx.strokeStyle = "rgba(255,255,255,0.12)";
  for (const q of quads) {
    ctx.beginPath();
    ctx.moveTo(q.p[0][0], q.p[0][1]);
    for (let k = 1; k < 4; k++) ctx.lineTo(q.p[k][0], q.p[k][1]);
    ctx.closePath();
    ctx.fillStyle = jet(q.v);
    ctx.fill();
    ctx.stroke();
  }
  ctx.fillStyle = "rgba(255,255,255,0.75)";
  ctx.font = "13px sans-serif";
  const [rx, ry] = project(n / 2, 0, 0);
  const [lx, ly] = project(n / 2, m - 1, 0);
  ctx.fillText("DERECHO", rx - 30, ry + 22);
  ctx.fillText("IZQUIERDO", lx - 35, ly + 22);
}

function render3d(findings) {
  const grid = findings && findings.attention_grid;
  const has = Array.isArray(grid) && grid.length > 1;
  $("v3d-empty").hidden = has;
  $("v3d-body").hidden = !has;
  view3d.grid = has ? grid : null;
  view3d.az = -0.6;
  view3d.el = 0.75;
}


// ---- SPEC-018: tomografía 3D (casos precalculados con MEDPSeg) -------------------------------
const CT_STYLE = {
  pulmon_derecho: ["Pulmón derecho", "#8ecae6", 0.12],
  pulmon_izquierdo: ["Pulmón izquierdo", "#8ecae6", 0.12],
  via_aerea: ["Vía aérea", "#f1f1f1", 0.85],
  vasos: ["Arterias pulmonares", "#d1495b", 0.45],
  vidrio_esmerilado: ["Vidrio esmerilado", "#ffd166", 0.9],
  consolidacion: ["Consolidación", "#f3722c", 0.95],
};
const CT_BG = "#11151c";
const ct = { mode: "ct", started: false, plotted: false };

function ctStatus(text) {
  $("ct-status").textContent = text || "";
  $("ct-status").hidden = !text;
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const tag = document.createElement("script");
    tag.src = src;
    tag.onload = resolve;
    tag.onerror = () => reject(new Error(`No se pudo cargar ${src}`));
    document.head.appendChild(tag);
  });
}

async function ensurePlotly() {
  if (!window.Plotly) await loadScript(`${API}/vendor/plotly.min.js`);
}

function column(rows, c) {
  return rows.map((r) => r[c]);
}

function ctFigure(structures) {
  const traces = [];
  Object.entries(CT_STYLE).forEach(([name, [label, color, opacity]]) => {
    const mesh = structures[name];
    if (!mesh || !mesh.faces.length) return;
    traces.push({
      type: "mesh3d",
      x: column(mesh.vertices, 0),
      y: column(mesh.vertices, 1),
      z: column(mesh.vertices, 2),
      i: column(mesh.faces, 0),
      j: column(mesh.faces, 1),
      k: column(mesh.faces, 2),
      color,
      opacity,
      name: label,
      showlegend: true,
      flatshading: false,
      lighting: { ambient: 0.45, diffuse: 0.8, specular: 0.3, roughness: 0.6 },
      hovertemplate: `${label}<extra></extra>`,
    });
  });
  const annotations = [];
  [["pulmon_derecho", "DERECHO"], ["pulmon_izquierdo", "IZQUIERDO"]].forEach(([name, text]) => {
    const mesh = structures[name];
    if (!mesh || !mesh.vertices.length) return;
    const n = mesh.vertices.length;
    const mean = (c) => mesh.vertices.reduce((acc, v) => acc + v[c], 0) / n;
    const top = mesh.vertices.reduce((acc, v) => Math.max(acc, v[2]), -Infinity);
    annotations.push({
      x: mean(0), y: mean(1), z: top + 15, text, showarrow: false,
      font: { size: 12, color: "#e8e8e8" },
    });
  });
  const hidden = { visible: false };
  const layout = {
    height: 560,
    margin: { l: 0, r: 0, t: 10, b: 0 },
    paper_bgcolor: CT_BG,
    legend: { font: { color: "#e8e8e8" }, bgcolor: "rgba(0,0,0,0)" },
    scene: {
      xaxis: hidden, yaxis: hidden, zaxis: hidden,
      aspectmode: "data",
      bgcolor: CT_BG,
      annotations,
      camera: { eye: { x: 0, y: 1.9, z: 0.25 }, up: { x: 0, y: 0, z: 1 } },
    },
  };
  return { traces, layout };
}

function fmt(value, digits = 1) {
  return Number(value).toLocaleString("es-CO", { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function renderCtReport(report, lobeLabels) {
  const lungs = report.lung_volume_ml || {};
  const lungMl = Object.values(lungs).reduce((a, b) => a + Number(b), 0);
  const metrics = [
    ["Pulmón comprometido", `${fmt(report.percent_total)} %`],
    ["Volumen de lesión", `${fmt(report.lesion_ml, 0)} mL`],
    ["Vidrio esmerilado", `${fmt(report.ggo_ml, 0)} mL`],
    ["Consolidación", `${fmt(report.consolidation_ml, 0)} mL`],
    ["Volumen pulmonar", `${fmt(lungMl, 0)} mL`],
    ["Severidad (lóbulos)", report.severity_score == null ? "—" : `${report.severity_score} / 25`],
  ];
  const dl = $("ct-metrics");
  dl.replaceChildren(
    ...metrics.map(([k, v]) => {
      const box = document.createElement("div");
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = k;
      dd.textContent = v;
      box.append(dt, dd);
      return box;
    }),
  );
  $("ct-summary").replaceChildren(
    ...(report.summary || []).map((line) => {
      const li = document.createElement("li");
      li.textContent = line;
      return li;
    }),
  );
  $("ct-lobes").replaceChildren(
    ...(report.lobes || []).map((lobe) => {
      const tr = document.createElement("tr");
      [lobeLabels[lobe.name] || lobe.name, `${fmt(lobe.volume_ml, 0)} mL`, `${fmt(lobe.percent)} %`, String(lobe.score)]
        .forEach((text) => {
          const td = document.createElement("td");
          td.textContent = text;
          tr.appendChild(td);
        });
      return tr;
    }),
  );
  $("ct-report").hidden = false;
}

async function getJson(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw Object.assign(new Error(`HTTP ${res.status}`), { status: res.status });
  return res.json();
}

async function loadCtCase(caseId) {
  ctStatus("Cargando la reconstrucción 3D…");
  $("ct-report").hidden = true;
  try {
    const data = await getJson(`/ct/cases/${encodeURIComponent(caseId)}`);
    const { traces, layout } = ctFigure(data.structures);
    $("ct-plot").hidden = false;
    await window.Plotly.react("ct-plot", traces, layout, { responsive: true, displaylogo: false });
    ct.plotted = true;
    renderCtReport(data.report, data.lobe_labels || {});
    ctStatus("");
  } catch (err) {
    ctStatus(`No se pudo cargar el caso ${caseId}: ${err.message}`);
  }
}

async function startCt() {
  if (ct.started) return;
  ct.started = true;
  ctStatus("Preparando el visor 3D…");
  try {
    const { cases } = await getJson("/ct/cases");
    if (!cases.length) {
      ct.started = false;
      ctStatus(
        "No hay tomografías procesadas: copie covid_ejemplo.npz en runtime/ct_cache " +
          "(o ejecute make ct-precompute) y vuelva a abrir esta vista.",
      );
      return;
    }
    await ensurePlotly();
    const select = $("ct-case");
    select.replaceChildren(
      ...cases.map((id) => {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = id;
        return option;
      }),
    );
    select.value = cases.includes("covid_ejemplo") ? "covid_ejemplo" : cases[0];
    select.addEventListener("change", () => loadCtCase(select.value));
    await loadCtCase(select.value);
  } catch (err) {
    ct.started = false;
    ctStatus(
      err.status === 404
        ? "El backend en ejecución es anterior a esta vista: detenga make backend (Ctrl+C) y vuelva a iniciarlo."
        : `No se pudo preparar el visor 3D: ${err.message}. Reinicie make backend.`,
    );
  }
}

function selectView3d(mode) {
  ct.mode = mode;
  document.querySelectorAll(".seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.v3d === mode));
  $("ct-view").hidden = mode !== "ct";
  $("att-view").hidden = mode !== "att";
  if (mode === "ct") {
    startCt();
    if (ct.plotted && window.Plotly) window.Plotly.Plots.resize("ct-plot");
  } else {
    drawSurface();
  }
}

function initTabs() {
  document.querySelectorAll(".seg-btn").forEach((b) =>
    b.addEventListener("click", () => selectView3d(b.dataset.v3d)),
  );
  document.querySelectorAll(".tab").forEach((tab) =>
    tab.addEventListener("click", () => selectTab(tab.dataset.tab)),
  );
  const canvas = $("v3d");
  let drag = null;
  canvas.addEventListener("pointerdown", (e) => {
    drag = { x: e.clientX, y: e.clientY, az: view3d.az, el: view3d.el };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag) return;
    view3d.az = drag.az + (e.clientX - drag.x) * 0.01;
    view3d.el = Math.max(0.1, Math.min(1.5, drag.el + (e.clientY - drag.y) * 0.01));
    drawSurface();
  });
  canvas.addEventListener("pointerup", () => (drag = null));
  canvas.addEventListener("dblclick", () => {
    view3d.az = -0.6;
    view3d.el = 0.75;
    drawSurface();
  });
}

function selectTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".panel").forEach((p) => (p.hidden = p.dataset.panel !== name));
  if (name === "3d") selectView3d(ct.mode);
}

function showResult(body, file, patientId, serverMs, roundTripMs) {
  const pneumonia = body.label === "PNEUMONIA";
  const label = $("label");
  label.textContent = pneumonia ? "Hallazgos compatibles con NEUMONÍA" : "Sin hallazgos de neumonía";
  label.className = pneumonia ? "positive" : "negative";
  $("probability").textContent = percent(body.probability);
  $("bar-fill").style.width = `${(body.probability * 100).toFixed(1)}%`;
  $("bar-fill").className = pneumonia ? "positive" : "negative";
  $("subtype").textContent = CLASS_LABELS[body.subtype] || body.subtype;

  const tbody = $("classes");
  tbody.replaceChildren();
  for (const [name, p] of Object.entries(body.class_probabilities || {})) {
    const tr = document.createElement("tr");
    const c1 = document.createElement("td");
    c1.textContent = CLASS_LABELS[name] || name;
    const c2 = document.createElement("td");
    c2.textContent = percent(p);
    tr.append(c1, c2);
    tbody.append(tr);
  }

  const gradcam = $("gradcam");
  gradcam.hidden = !body.gradcam_url;
  if (body.gradcam_url) gradcam.src = `${API}${body.gradcam_url}`;

  const isDicom = /\.dcm$/i.test(file.name) || file.type === "application/dicom";
  $("preview-figure").hidden = isDicom;
  $("preview-note").hidden = !isDicom;
  document.querySelector(".grid").classList.toggle("two", isDicom);
  if (!isDicom) $("preview").src = URL.createObjectURL(file);

  renderReport(body.findings);
  render3d(body.findings);
  selectTab("res");

  fillList($("patient-rows"), patientRows(body.metadata, patientId, file.name));
  $("patient-panel").hidden = false;

  const server = serverMs ? `${Number(serverMs).toFixed(0)} ms en el servidor · ` : "";
  $("trace").textContent =
    `request_id ${body.request_id} · ${body.model_version} · ${server}` +
    `${roundTripMs.toFixed(0)} ms ida y vuelta`;
  setState("success");
}

function init() {
  const fileInput = $("file");
  const drop = $("drop");
  fileInput.addEventListener("change", () => {
    const f = fileInput.files[0];
    $("file-name").textContent = f ? `${f.name} · ${(f.size / 1024).toFixed(1)} KB` : "";
    $("submit").disabled = !f;
  });
  ["dragenter", "dragover"].forEach((ev) =>
    drop.addEventListener(ev, (e) => {
      e.preventDefault();
      drop.classList.add("over");
    }),
  );
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove("over")));
  drop.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      fileInput.dispatchEvent(new Event("change"));
    }
  });

  $("form").addEventListener("submit", (e) => {
    e.preventDefault();
    const problem = validatePatient($("patient").value);
    $("patient-error").textContent = problem || "";
    $("patient-error").hidden = !problem;
    const file = fileInput.files[0];
    if (problem || !file) return;
    predict(file, $("patient").value);
  });
  $("retry").addEventListener("click", () => {
    checkHealth();
    if (lastSubmit) predict(lastSubmit.file, lastSubmit.patientId);
  });

  initTabs();
  setState("idle");
  checkHealth();
}

document.addEventListener("DOMContentLoaded", init);
