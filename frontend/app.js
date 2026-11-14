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

  setState("idle");
  checkHealth();
}

document.addEventListener("DOMContentLoaded", init);
