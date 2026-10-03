// DevFlow dashboard. Plain JavaScript: fetches data from the Flask REST API.
const API = "/api";
const TITLES = { dashboard: "Dashboard", services: "Services", deployments: "Deployments", cicd: "CI/CD", docker: "Docker" };
let buildChart = null;
let serviceModal = null;

// ---------- helpers ----------
const $ = (id) => document.getElementById(id);

function esc(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function fmtDate(iso) {
  return iso ? new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "Never";
}

function fmtDuration(seconds) {
  return `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

function badge(status) {
  return `<span class="badge-status s-${esc(status)}">${esc(status)}</span>`;
}

function toast(message) {
  $("toastBody").textContent = message;
  bootstrap.Toast.getOrCreateInstance($("toast"), { delay: 2500 }).show();
}

async function api(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.error || "Request failed");
    error.details = body.details;
    throw error;
  }
  return body;
}

function table(headers, rows, emptyText) {
  if (!rows.length) return `<div class="empty">${emptyText}</div>`;
  const head = headers.map((h) => `<th>${h}</th>`).join("");
  return `<table class="table"><thead><tr>${head}</tr></thead><tbody>${rows.join("")}</tbody></table>`;
}

// ---------- renderers ----------
async function loadDashboard() {
  const [stats, services, deployments, runs] = await Promise.all([
    api("/stats"), api("/services"), api("/deployments"), api("/pipelines"),
  ]);

  const cards = [
    ["bi-hdd-stack", stats.total_services, "Total services"],
    ["bi-activity", stats.active_services, "Active services"],
    ["bi-rocket-takeoff", stats.total_deployments, "Deployments"],
    ["bi-check2-circle", stats.successful_builds, "Successful builds"],
  ];
  $("statCards").innerHTML = cards.map(([icon, num, label]) =>
    `<div class="col-sm-6 col-xl-3"><div class="stat"><div class="icon"><i class="bi ${icon}"></i></div>
     <div><div class="num">${num}</div><div class="lbl">${label}</div></div></div></div>`).join("");

  drawChart(stats.build_chart);

  const last = runs[0];
  $("latestRun").innerHTML = last
    ? `<div class="mb-2">${badge(last.status)}</div>
       <div class="fw-semibold">${esc(last.pipeline_name)} #${last.build_number}</div>
       <div class="text-muted small">${fmtDuration(last.duration_seconds)} &middot; ${esc(last.trigger)}</div>
       <div class="text-muted small">${fmtDate(last.started_at)}</div>`
    : `<div class="empty">No pipeline runs yet.</div>`;

  $("dashServices").innerHTML = table(["Service", "Version", "Environment", "Status"],
    services.map((s) => `<tr><td>${esc(s.name)}</td><td>${esc(s.version)}</td>
      <td class="env-tag">${esc(s.environment)}</td><td>${badge(s.status)}</td></tr>`),
    "No services available.");

  $("dashDeployments").innerHTML = deployments.slice(0, 5).map((d) =>
    `<div class="deploy-item"><div><strong>${esc(d.service_name)}</strong> v${esc(d.version)}
     <small>${fmtDate(d.deployed_at)} &middot; ${esc(d.method)}</small></div>${badge(d.status)}</div>`).join("")
    || `<div class="empty">No deployments yet.</div>`;
}

function drawChart(data) {
  // Empty state: no finished builds yet, so show a message instead of an empty chart.
  const hasBuilds = data.some((d) => d.success + d.failed > 0);
  $("buildChart").classList.toggle("d-none", !hasBuilds);
  $("chartEmpty").classList.toggle("d-none", hasBuilds);
  if (!hasBuilds) {
    if (buildChart) { buildChart.destroy(); buildChart = null; }
    return;
  }
  const labels = data.map((d) => new Date(d.date + "T00:00").toLocaleDateString([], { weekday: "short" }));
  const config = {
    type: "bar",
    data: { labels, datasets: [
      { label: "Success", data: data.map((d) => d.success), backgroundColor: "#0f9d8a" },
      { label: "Failed", data: data.map((d) => d.failed), backgroundColor: "#d9534f" },
    ] },
    options: { maintainAspectRatio: false,
      scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } } },
      plugins: { legend: { position: "bottom" } } },
  };
  if (buildChart) buildChart.destroy();
  buildChart = new Chart($("buildChart"), config);
}

async function loadServices() {
  const services = await api("/services");
  $("servicesTable").innerHTML = table(
    ["Service", "Version", "Environment", "Status", "Last deployment", "Actions"],
    services.map((s) => `<tr>
      <td><strong>${esc(s.name)}</strong><div class="text-muted small">${esc(s.description)}</div></td>
      <td>${esc(s.version)}</td><td class="env-tag">${esc(s.environment)}</td><td>${badge(s.status)}</td>
      <td>${fmtDate(s.last_deployed_at)}</td>
      <td class="text-nowrap">
        <button class="btn-icon" title="Deploy" aria-label="Deploy ${esc(s.name)}" data-act="deploy" data-id="${s.id}"><i class="bi bi-rocket-takeoff"></i></button>
        <button class="btn-icon" title="Edit" aria-label="Edit ${esc(s.name)}" data-act="edit" data-id="${s.id}"><i class="bi bi-pencil"></i></button>
        <button class="btn-icon" title="Delete" aria-label="Delete ${esc(s.name)}" data-act="delete" data-id="${s.id}" data-name="${esc(s.name)}"><i class="bi bi-trash"></i></button>
      </td></tr>`),
    "No services available.");
}

async function loadDeployments() {
  const items = await api("/deployments");
  $("deploymentsTable").innerHTML = table(["ID", "Service", "Version", "Status", "Date/Time", "Method"],
    items.map((d) => `<tr><td>#${d.id}</td><td>${esc(d.service_name)}</td><td>${esc(d.version)}</td>
      <td>${badge(d.status)}</td><td>${fmtDate(d.deployed_at)}</td><td>${esc(d.method)}</td></tr>`),
    "No deployments recorded yet.");
}

async function loadPipelines() {
  const runs = await api("/pipelines");
  $("pipelinesTable").innerHTML = table(["Pipeline", "Build", "Status", "Duration", "Last run", "Trigger"],
    runs.map((r) => `<tr><td>${esc(r.pipeline_name)}</td><td>#${r.build_number}</td><td>${badge(r.status)}</td>
      <td>${fmtDuration(r.duration_seconds)}</td><td>${fmtDate(r.started_at)}</td><td>${esc(r.trigger)}</td></tr>`),
    "No builds recorded yet. Run the Jenkins pipeline to add one.");
}

async function loadDocker() {
  const containers = await api("/docker");
  $("dockerTable").innerHTML = table(["Container", "Image", "Status", "Status source", "Port", "Environment"],
    containers.map((c) => `<tr><td><i class="bi bi-box me-2"></i>${esc(c.name)}</td><td>${esc(c.image)}</td>
      <td>${badge(c.status)}</td><td class="env-tag">${esc(c.source)}</td><td>${esc(c.port)}</td><td class="env-tag">${esc(c.environment)}</td></tr>`),
    "No container information available.");
}

async function checkHealth() {
  try {
    await api("/health");
    $("healthDot").className = "dot up";
  } catch {
    $("healthDot").className = "dot down";
  }
}

// ---------- navigation ----------
const loaders = { dashboard: loadDashboard, services: loadServices, deployments: loadDeployments, cicd: loadPipelines, docker: loadDocker };

async function showPage() {
  const page = loaders[location.hash.slice(1)] ? location.hash.slice(1) : "dashboard";
  document.querySelectorAll(".page").forEach((p) => p.classList.toggle("d-none", p.id !== `page-${page}`));
  document.querySelectorAll(".sidebar .nav-link").forEach((a) => a.classList.toggle("active", a.getAttribute("href") === `#${page}`));
  $("pageTitle").textContent = TITLES[page];
  $("sidebar").classList.remove("open");
  try {
    await loaders[page]();
  } catch (error) {
    toast("Could not load data: " + error.message);
  }
  checkHealth();
}

// ---------- service form ----------
function openForm(service) {
  $("modalTitle").textContent = service ? "Edit service" : "Add service";
  $("svcId").value = service ? service.id : "";
  $("svcName").value = service ? service.name : "";
  $("svcVersion").value = service ? service.version : "";
  $("svcEnv").value = service ? service.environment : "development";
  $("svcStatus").value = service ? service.status : "running";
  $("svcDesc").value = service ? service.description : "";
  $("formError").textContent = "";
  serviceModal.show();
}

async function saveService() {
  const id = $("svcId").value;
  const payload = {
    name: $("svcName").value, version: $("svcVersion").value, environment: $("svcEnv").value,
    status: $("svcStatus").value, description: $("svcDesc").value,
  };
  try {
    await api(id ? `/services/${id}` : "/services", { method: id ? "PUT" : "POST", body: JSON.stringify(payload) });
    serviceModal.hide();
    toast(id ? "Service updated" : "Service created");
    loadServices();
  } catch (error) {
    const details = error.details ? Object.entries(error.details).map(([k, v]) => `${k}: ${v}`).join("; ") : "";
    $("formError").textContent = details || error.message;
  }
}

async function handleTableAction(event) {
  const button = event.target.closest("button[data-act]");
  if (!button) return;
  const { act, id, name } = button.dataset;
  try {
    if (act === "edit") openForm(await api(`/services/${id}`));
    if (act === "deploy") { await api(`/services/${id}/deploy`, { method: "POST" }); toast("Deployment recorded"); loadServices(); }
    if (act === "delete" && confirm(`Delete service "${name}" and its deployment history?`)) {
      await api(`/services/${id}`, { method: "DELETE" }); toast("Service deleted"); loadServices();
    }
  } catch (error) {
    toast(error.message);
  }
}

// ---------- start ----------
document.addEventListener("DOMContentLoaded", () => {
  serviceModal = new bootstrap.Modal($("serviceModal"));
  $("addServiceBtn").addEventListener("click", () => openForm(null));
  $("saveServiceBtn").addEventListener("click", saveService);
  $("servicesTable").addEventListener("click", handleTableAction);
  $("menuBtn").addEventListener("click", () => $("sidebar").classList.toggle("open"));
  window.addEventListener("hashchange", showPage);
  showPage();
});
