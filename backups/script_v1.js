const API_BASE = '/api';

const banner = document.getElementById('banner');
const livenessStatus = document.getElementById('liveness-status');
const recognitionStatus = document.getElementById('recognition-status');
const confidenceValue = document.getElementById('confidence-value');
const confidenceCircle = document.querySelector('#confidence-meter circle.fg');
const activityLog = document.querySelector('#activity-log tbody');
const successRing = document.getElementById("success-ring");
const successRateText = document.getElementById("success-rate-text");
const miniBars = document.getElementById("mini-bars");
const lockOverlay = document.getElementById("lock-overlay");

/* ================= CONFIDENCE ================= */

function animateConfidence(percent) {
    const circumference = 339.292;
    let pct = Math.max(0, Math.min(100, percent));
    let offset = circumference - (pct / 100) * circumference;

    confidenceCircle.style.strokeDashoffset = offset;
    confidenceValue.textContent = `${pct.toFixed(0)}%`;

    confidenceCircle.style.stroke =
        pct >= 80 ? "var(--neon-green)" :
        (pct >= 45 ? "var(--neon-cyan)" : "var(--danger)");
}

/* ================= STATUS LIGHTS ================= */

function updateStatus(active, el) {
    if (!el) return;
    el.classList.toggle("active", active);
    el.classList.toggle("inactive", !active);
}

/* ================= BANNER ================= */

function renderBannerFromState(state) {

    if (state === "ACCESS_GRANTED") {
        banner.className = "banner banner-success";
        banner.textContent = "ACCESS GRANTED";
    }
    else if (state === "HARD_FAIL") {
        banner.className = "banner banner-fail";
        banner.textContent = "ACCESS DENIED";
    }
    else if (state === "RECOGNITION") {
        banner.className = "banner banner-neutral";
        banner.textContent = "Analyzing biometric signature...";
    }
    else if (state === "LIVENESS") {
        banner.className = "banner banner-neutral";
        banner.textContent = "Liveness verification in progress...";
    }
    else {
        banner.className = "banner banner-neutral";
        banner.textContent = "Awaiting authentication...";
    }
}

/* ================= ADVANCED METRICS ================= */

function renderSystemStats(stats, logs) {

    const rate = typeof stats.success_rate === "number"
        ? stats.success_rate
        : 0;

    // Success Ring
    if (successRing) {
        const circumference = 314;
        const offset = circumference - (rate / 100) * circumference;
        successRing.style.strokeDashoffset = offset;
    }

    if (successRateText) {
        successRateText.textContent = rate.toFixed(0) + "%";
    }

    // Mini History Bars (real logs)
    if (!miniBars) return;

    miniBars.innerHTML = "";

    if (!Array.isArray(logs) || logs.length === 0) {
        return;
    }

    const lastTen = logs.slice(0, 10).reverse();

    for (const entry of lastTen) {

        const bar = document.createElement("div");

        if (entry.result === "success") {
            bar.style.background = "var(--neon-green)";
            bar.style.height = "90%";
        }
        else if (entry.result === "fail") {
            bar.style.background = "var(--danger)";
            bar.style.height = "40%";
        }
        else {
            bar.style.background = "var(--neon-cyan)";
            bar.style.height = "60%";
        }

        miniBars.appendChild(bar);
    }
}

/* ================= ACTIVITY LOG ================= */

function renderActivityLog(logs) {

    if (!activityLog) return;

    activityLog.innerHTML = '';

    if (!Array.isArray(logs) || logs.length === 0) {
        return;
    }

    for (const entry of logs) {

        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td>${entry.timestamp || '--'}</td>
            <td>${entry.user || '--'}</td>
            <td>${entry.liveness === true ? '✔' :
                (entry.liveness === false ? '✗' : '--')}</td>
            <td>${typeof entry.confidence === "number"
                ? entry.confidence.toFixed(1) + "%"
                : '--'}</td>
            <td>${entry.result || '--'}</td>
        `;

        activityLog.appendChild(tr);
    }
}

/* ================= MAIN FETCH ================= */

async function fetchDashboardState() {

    try {
        const resp = await fetch(`${API_BASE}/dashboard-state`);

        if (!resp.ok) {
            console.warn("API not responding");
            return;
        }

        const data = await resp.json();

        console.log("Dashboard Data:", data);

        const state = data.system_state || "UNKNOWN";

        document.body.setAttribute("data-state", state);

        updateStatus(state === "LIVENESS", livenessStatus);
        updateStatus(state === "RECOGNITION", recognitionStatus);

        animateConfidence(data.confidence ?? 0);

        renderBannerFromState(state);

        const logs = Array.isArray(data.activity_log)
            ? data.activity_log
            : [];

        renderSystemStats(data.system_stats || {}, logs);
        renderActivityLog(logs);

        if (lockOverlay) {
            lockOverlay.classList.toggle(
                "active",
                state === "ACCESS_GRANTED"
            );
        }

    } catch (err) {
        console.warn("Fetch failed:", err);
    }
}

/* ================= INIT ================= */

fetchDashboardState();
setInterval(fetchDashboardState, 1200);