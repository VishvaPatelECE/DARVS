




document.addEventListener("DOMContentLoaded", function() {

    const container = document.getElementById('dashboard-container');
    if (!container) return;   // <- Prevents admin page breaking


// ===============================
// DARVS Motion System v1
// ===============================

const API_BASE = '/api';

// Elements
const banner = document.getElementById('banner');
const livenessStatus = document.getElementById('liveness-status');
const recognitionStatus = document.getElementById('recognition-status');
const confidenceValue = document.getElementById('confidence-value');
const confidenceCircle = document.querySelector('#confidence-meter circle.fg');
const statTotal = document.getElementById('stat-total');
const statSuccess = document.getElementById('stat-success');
const statFakes = document.getElementById('stat-fakes');
const activityLog = document.querySelector('#activity-log tbody');
const container = document.getElementById('dashboard-container');

// ===============================
// GLOBAL PARALLAX DEPTH
// ===============================
document.addEventListener("mousemove", function (e) {
    const x = (e.clientX / window.innerWidth) - 0.5;
    const y = (e.clientY / window.innerHeight) - 0.5;

    const rotateX = y * 4;
    const rotateY = x * 4;

    container.style.transform =
        `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
});

// ===============================
// PANEL ENTRANCE CASCADE
// ===============================
window.addEventListener("load", () => {
    const panels = document.querySelectorAll(".glass-panel");
    panels.forEach((panel, i) => {
        setTimeout(() => {
            panel.classList.add("visible");
        }, i * 120);
    });
});

// ===============================
// CONFIDENCE ANIMATION
// ===============================
function animateConfidence(percent) {
    const circumference = 339.292;
    let pct = Math.max(0, Math.min(100, percent));
    let offset = circumference - (pct / 100) * circumference;

    confidenceCircle.style.transition =
        "stroke-dashoffset 0.8s cubic-bezier(.4,0,.2,1)";
    confidenceCircle.style.strokeDashoffset = offset;

    confidenceValue.style.transition = "all 0.4s ease";
    confidenceValue.style.transform = "scale(1.1)";

    setTimeout(() => {
        confidenceValue.style.transform = "scale(1)";
    }, 300);

    confidenceValue.textContent = `${pct.toFixed(0)}%`;
}

// ===============================
// STATUS INDICATOR
// ===============================
function updateStatus(status, el) {
    el.classList.remove("active", "inactive", "pulse");

    if (status === true || status === "active") {
        el.classList.add("active", "pulse");
    } else if (status === false || status === "inactive") {
        el.classList.add("inactive");
    }
}

// ===============================
// BANNER
// ===============================
function renderBanner(state, msg) {
    banner.className = "banner";

    if (state === "success") {
        banner.classList.add("banner-success");
    } else if (state === "error") {
        banner.classList.add("banner-fail");
    } else {
        banner.classList.add("banner-neutral");
    }

    banner.textContent = msg || "Awaiting authentication...";

    banner.classList.add("banner-animate");
    setTimeout(() => {
        banner.classList.remove("banner-animate");
    }, 400);
}

// ===============================
// SYSTEM STATS
// ===============================
function renderSystemStats(stats) {
    statTotal.textContent = stats.total_attempts ?? "--";
    statSuccess.textContent =
        typeof stats.success_rate === "number"
            ? stats.success_rate.toFixed(1) + "%"
            : "--";
    statFakes.textContent = stats.liveness_fail_count ?? "--";
}

// ===============================
// ACTIVITY LOG
// ===============================
function renderActivityLog(logs) {
    activityLog.innerHTML = "";

    for (const entry of logs || []) {
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${entry.timestamp || "--"}</td>
            <td>${entry.user || "--"}</td>
            <td>${entry.liveness === true
                ? '<span class="access">✔</span>'
                : entry.liveness === false
                    ? '<span class="deny">✗</span>'
                    : '--'}</td>
            <td>${typeof entry.confidence === "number"
                ? entry.confidence.toFixed(1) + "%"
                : "--"}</td>
            <td>${entry.result === "success"
                ? '<span class="access">GRANTED</span>'
                : entry.result === "fail"
                    ? '<span class="deny">DENIED</span>'
                    : "--"}</td>
        `;

        activityLog.appendChild(tr);
    }
}

// ===============================
// FETCH DASHBOARD
// ===============================
async function fetchDashboardState() {
    try {
        const resp = await fetch(`${API_BASE}/dashboard-state`);
        if (!resp.ok) throw new Error();

        const data = await resp.json();

        updateStatus(data.system_state === "LIVENESS", livenessStatus);
        updateStatus(data.system_state === "RECOGNITION", recognitionStatus);

        animateConfidence(data.confidence ?? 0);
        renderBanner(data.banner?.state, data.banner?.msg);
        renderSystemStats(data.system_stats || {});
        renderActivityLog(data.activity_log || []);

    } catch {
        renderBanner(null, "System error. Check connection.");
    }
}

fetchDashboardState();
setInterval(fetchDashboardState, 1200);


});