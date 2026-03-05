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

    /* ================= CONFIDENCE SETUP ================= */

    const radius = 65;
    const circumference = 2 * Math.PI * radius;

    if (circle) {
        circle.style.strokeDasharray = circumference;
        circle.style.strokeDashoffset = circumference;
    }

    function updateConfidence(value) {

        if (!circle) return;

        const offset = circumference - (value / 100) * circumference;
        circle.style.strokeDashoffset = offset;

        if (confidenceDisplay) {
            confidenceDisplay.textContent = value + "%";
        }
    }

    /* ================= CAMERA CONTROL ================= */

    if (startBtn) {

        startBtn.addEventListener("click", function () {

            if (!cameraActive) {

                cameraFeed.src = "/video_feed?t=" + new Date().getTime();
                cameraActive = true;

            }
        });
    }

    if (stopBtn) {

        stopBtn.addEventListener("click", function () {

            cameraFeed.src = "";
            cameraActive = false;

            updateConfidence(0);
        });
    }

    /* ================= CONNECTION INFO ================= */

    const connEl = document.getElementById("connection-type");

    if (connEl) {

        if (navigator.connection && navigator.connection.effectiveType) {

            connEl.textContent =
                "Connection: " + navigator.connection.effectiveType.toUpperCase();

        } else {

            connEl.textContent = "Connection: LAN";

        }
    }

    /* ================= DASHBOARD STATE ================= */

    async function fetchState() {

        if (!cameraActive) return;

        try {

            const res = await fetch("/api/dashboard-state");

            if (!res.ok) return;

            const data = await res.json();

            /* CONFIDENCE */

            updateConfidence(data.confidence);

            /* SYSTEM STATUS */

            if (systemState) {
                systemState.textContent = data.system_state;
            }

            /* ACTIVITY LOG */

            if (logTable) {

                logTable.innerHTML = "";

                data.activity_log.forEach(function (entry) {

                    const tr = document.createElement("tr");

                    if (entry.result === "success") {
                        tr.classList.add("success");
                    } else {
                        tr.classList.add("fail");
                    }

                    tr.innerHTML =
                        "<td>" + entry.timestamp + "</td>" +
                        "<td>" + entry.user + "</td>" +
                        "<td>" + entry.result.toUpperCase() + "</td>";

                    logTable.appendChild(tr);
                });
            }

            /* LOGO FEEDBACK */

            if (data.system_state === "HARD_FAIL") {

                logo.classList.remove("logo-success");
                logo.classList.add("logo-fail");

            } else if (data.system_state === "RECOGNITION" && data.confidence > 0) {

                logo.classList.remove("logo-fail");
                logo.classList.add("logo-success");

            } else {

                logo.classList.remove("logo-success", "logo-fail");
            }

        }

        catch (error) {

            console.log("Dashboard fetch error:", error);

        }
    }

    setInterval(fetchState, 1500);

    /* ================= LOADER ================= */

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