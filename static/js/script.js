document.addEventListener("DOMContentLoaded", function () {

    const logo = document.getElementById("darvs-icon");
    const startBtn = document.getElementById("start-btn");
    const stopBtn = document.getElementById("stop-btn");
    const cameraFeed = document.getElementById("camera-feed");
    const logTable = document.querySelector("#activity-log tbody");
    const confidenceDisplay = document.getElementById("confidence-display");
    const systemState = document.getElementById("system-state");
    const loader = document.getElementById("loader-screen");
    const circle = document.getElementById("confidence-circle");

    let cameraActive = false;

    // ================= CONFIDENCE SETUP =================

    const radius = 65; // MUST match your SVG r value
    const circumference = 2 * Math.PI * radius;

    if (circle) {
        circle.style.strokeDasharray = circumference;
        circle.style.strokeDashoffset = circumference; // start empty
    }

    function updateConfidence(value) {
        if (!circle) return;

        const offset = circumference - (value / 100) * circumference;
        circle.style.strokeDashoffset = offset;
        confidenceDisplay.textContent = value + "%";
    }

    // ================= CAMERA CONTROL =================

    startBtn.addEventListener("click", function () {
        if (!cameraActive) {
            cameraFeed.src = "/video_feed";
            cameraActive = true;
        }
    });

    stopBtn.addEventListener("click", function () {
        cameraFeed.src = "";
        cameraActive = false;
    });

    // ================= CONNECTION INFO =================

    const connEl = document.getElementById("connection-type");

    if (navigator.connection && navigator.connection.effectiveType) {
        connEl.textContent =
            "Connection: " + navigator.connection.effectiveType.toUpperCase();
    } else {
        connEl.textContent = "Connection: LAN";
    }

    // ================= DASHBOARD STATE =================

    async function fetchState() {
        if (!cameraActive) return;

        try {
            const res = await fetch("/api/dashboard-state");
            if (!res.ok) return;

            const data = await res.json();

            updateConfidence(data.confidence);

            systemState.textContent = data.system_state;

            logTable.innerHTML = "";

            data.activity_log.forEach(entry => {
                const tr = document.createElement("tr");
                tr.classList.add(entry.result === "success" ? "success" : "fail");

                tr.innerHTML = `
                    <td>${entry.timestamp}</td>
                    <td>${entry.user}</td>
                    <td>${entry.result.toUpperCase()}</td>
                `;

                logTable.appendChild(tr);
            });

            const logoIcon = document.getElementById("darvs-icon");
            if (data.system_state === "HARD_FAIL") {
            logoIcon.classList.remove("logo-success");
            logoIcon.classList.add("logo-fail");
            }

            else if (data.system_state === "RECOGNITION" && data.confidence > 0) {
            logoIcon.classList.remove("logo-fail");
            logoIcon.classList.add("logo-success");
            }

            else {
            logoIcon.classList.remove("logo-success","logo-fail");
            }

        } catch (error) {
            console.log("Dashboard fetch error:", error);
        }
    }

    setInterval(fetchState, 1500);

    // ================= LOADER =================

    const facts = [
        "DARVS analyzes micro facial movements.",
        "AI-powered deepfake detection.",
        "Defense-grade biometric verification.",
        "Real-time anomaly intelligence."
    ];

    const factEl = document.getElementById("loader-fact");
    let index = 0;

    const factInterval = setInterval(function () {
        if (factEl) {
            factEl.textContent = facts[index];
            index = (index + 1) % facts.length;
        }
    }, 900);

    setTimeout(function () {
        if (loader) {
            loader.style.display = "none";
        }
        document.body.classList.remove("loading");
        clearInterval(factInterval);
    }, 2800);

});