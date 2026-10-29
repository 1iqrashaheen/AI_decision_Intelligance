/**
 * DecisionAI API Client
 * Author: Muhammad Arham (Module 07 — Backend connections)
 * Connects frontend pages to the FastAPI backend at http://localhost:8001/api
 */
const DIS_API = (() => {
  const API_BASE = window.location.port === "8001" ? window.location.origin + "/api" : "http://localhost:8001/api";
  let _isConnected = false;

  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: "GET", headers: { Accept: "application/json" } });
      if (res.ok) {
        const data = await res.json();
        _isConnected = true;
        updateStatusBadge(true, data);
        return true;
      }
    } catch (e) {
      // Backend not running
    }
    _isConnected = false;
    updateStatusBadge(false);
    return false;
  }

  function updateStatusBadge(online, data = null) {
    let badge = document.getElementById("api-status-badge");
    const topbar = document.querySelector(".topbar-inner");
    if (!badge && topbar) {
      badge = document.createElement("div");
      badge.id = "api-status-badge";
      badge.style.display = "inline-flex";
      badge.style.alignItems = "center";
      badge.style.gap = "6px";
      badge.style.fontSize = "0.75rem";
      badge.style.padding = "4px 8px";
      badge.style.borderRadius = "999px";
      badge.style.fontWeight = "600";
      badge.style.cursor = "pointer";
      topbar.appendChild(badge);
    }
    if (!badge) return;

    if (online) {
      badge.style.backgroundColor = "rgba(16, 185, 129, 0.15)";
      badge.style.color = "#10b981";
      badge.style.border = "1px solid rgba(16, 185, 129, 0.4)";
      badge.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:#10b981"></span> FastAPI Connected`;
      badge.title = `Connected to FastAPI Backend (Author: ${data?.author || "Muhammad Arham"})\nEndpoints ready on port 8001`;
    } else {
      badge.style.backgroundColor = "rgba(100, 116, 139, 0.15)";
      badge.style.color = "#94a3b8";
      badge.style.border = "1px solid rgba(100, 116, 139, 0.3)";
      badge.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:#94a3b8"></span> Offline Mode`;
      badge.title = "Backend is offline.\nRun 'python -m uvicorn main:app --port 8001' from the main project folder.";
    }
  }

  async function uploadFile(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: { message: "Upload failed" } }));
      throw new Error(err.error?.message || "Upload failed");
    }
    return await res.json();
  }

  async function getAnalysis(datasetId) {
    const res = await fetch(`${API_BASE}/analysis/${encodeURIComponent(datasetId)}`);
    if (!res.ok) throw new Error("Could not retrieve analysis from backend");
    return await res.json();
  }

  async function getForecast(datasetId, periods = 3) {
    const res = await fetch(`${API_BASE}/forecast`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: datasetId, periods }),
    });
    if (!res.ok) throw new Error("Could not compute forecast");
    return await res.json();
  }

  async function getBaseline(datasetId) {
    const res = await fetch(`${API_BASE}/simulate/baseline/${encodeURIComponent(datasetId)}`);
    if (!res.ok) throw new Error("Could not extract baseline from dataset");
    return await res.json();
  }

  async function simulate(baseline, changes, assumptions = { elasticity: -1.2, marketing_lift: 0.15 }) {
    const res = await fetch(`${API_BASE}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ baseline, changes, assumptions }),
    });
    if (!res.ok) throw new Error("Simulation request failed");
    return await res.json();
  }

  async function compareCases(baseline, changes) {
    const res = await fetch(`${API_BASE}/simulate/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ baseline, changes }),
    });
    if (!res.ok) throw new Error("Comparison request failed");
    return await res.json();
  }

  async function chat(datasetId, question, scenario = null) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: datasetId, question, scenario, scenario_dataset_id: scenario ? datasetId : null }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error?.message || "Chat request failed");
    }
    return await res.json();
  }

  async function downloadReport(format = "pdf", payload = null) {
    const res = await fetch(`${API_BASE}/export?format=${encodeURIComponent(format)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload ? JSON.stringify(payload) : null,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.error?.message || "Report export failed. Check the selected data and try again.");
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `decision_intelligence_report.${format}`;
    document.body.appendChild(a);
    a.click();
    window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    a.remove();
  }

  // Check the connection when the page opens.
  if (typeof window !== "undefined") {
    window.addEventListener("DOMContentLoaded", () => {
      checkHealth();
    });
  }

  return {
    API_BASE,
    isOnline: () => _isConnected,
    checkHealth,
    uploadFile,
    getAnalysis,
    getForecast,
    getBaseline,
    simulate,
    compareCases,
    chat,
    downloadReport,
  };
})();
