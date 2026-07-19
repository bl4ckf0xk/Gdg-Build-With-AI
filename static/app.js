// ADK Web Dashboard Client Script - Cyberpunk Glassmorphism UI

document.addEventListener("DOMContentLoaded", () => {
    const wsBadge = document.getElementById("wsBadge");
    const wsStatusText = document.getElementById("wsStatusText");
    
    const kpiModel = document.getElementById("kpiModel");
    const kpiBuild = document.getElementById("kpiBuild");
    const kpiStep = document.getElementById("kpiStep");
    
    const terminalStream = document.getElementById("terminalStream");
    const agentStatusBadge = document.getElementById("agentStatusBadge");
    const diffContainer = document.getElementById("diffContainer");
    const activityTimeline = document.getElementById("activityTimeline");

    const targetDirInput = document.getElementById("targetDir");
    const buildCmdInput = document.getElementById("buildCmd");
    const modelSelect = document.getElementById("modelSelect");

    const btnAutoHeal = document.getElementById("btnAutoHeal");
    const btnTogglePaste = document.getElementById("btnTogglePaste");
    const pasteSection = document.getElementById("pasteSection");
    const pastedErrorText = document.getElementById("pastedError");
    const btnSubmitPaste = document.getElementById("btnSubmitPaste");
    const btnClearLogs = document.getElementById("btnClearLogs");

    // Establish WebSocket Connection
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
    let socket = null;

    function connectWebSocket() {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            wsBadge.className = "connection-badge connected";
            wsStatusText.innerText = "Connected";
        };

        socket.onclose = () => {
            wsBadge.className = "connection-badge disconnected";
            wsStatusText.innerText = "Reconnecting...";
            setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
        };

        socket.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                handleServerMessage(payload);
            } catch (e) {
                console.error("Failed to parse WS message:", e);
            }
        };
    }

    function handleServerMessage(payload) {
        if (payload.type === "STATE_UPDATE") {
            updateDashboardState(payload.data);
        } else if (payload.type === "LOG_ENTRY") {
            appendLogEntry(payload.data);
        }
    }

    function updateDashboardState(state) {
        // Update Status Badge
        const statusStr = (state.status || "IDLE").toUpperCase();
        const statusClass = (state.status || "idle").toLowerCase();
        
        agentStatusBadge.className = `agent-status-tag status-${statusClass}`;
        agentStatusBadge.querySelector(".tag-text").innerText = statusStr.replace("_", " ");

        // Update KPIs
        kpiModel.innerText = modelSelect.options[modelSelect.selectedIndex]?.text.split(" ")[0] + " " + modelSelect.options[modelSelect.selectedIndex]?.text.split(" ")[1] || "Gemini 2.5 Pro";
        
        if (state.build_passed) {
            kpiBuild.innerHTML = '<span class="text-emerald">PASSED ✔</span>';
        } else if (state.status === "FAILED") {
            kpiBuild.innerHTML = '<span class="text-rose">FAILED ✖</span>';
        } else if (state.status !== "IDLE") {
            kpiBuild.innerHTML = '<span class="text-amber">TESTING...</span>';
        } else {
            kpiBuild.innerHTML = '<span class="text-emerald">PASSED ✔</span>';
        }

        const current = state.current_step || 0;
        const total = state.total_steps || 15;
        kpiStep.innerText = `${current} / ${total}`;

        // Update Code Diff if available
        if (state.last_diff) {
            renderDiff(state.last_diff);
        }

        // Update Timeline Steps
        if (state.timeline && state.timeline.length > 0) {
            renderTimeline(state.timeline);
        }
    }

    function appendLogEntry(log) {
        const line = document.createElement("div");
        line.className = `log-line ${log.type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        line.innerHTML = `<span class="log-time">[${timestamp}]</span> ${escapeHtml(log.message)}`;

        if (log.meta && log.meta.output) {
            const outputBox = document.createElement("pre");
            outputBox.style.fontSize = "0.75rem";
            outputBox.style.opacity = "0.85";
            outputBox.style.marginTop = "0.3rem";
            outputBox.style.padding = "0.5rem";
            outputBox.style.background = "rgba(0,0,0,0.5)";
            outputBox.style.borderRadius = "6px";
            outputBox.innerText = log.meta.output;
            line.appendChild(outputBox);
        }

        terminalStream.appendChild(line);
        terminalStream.scrollTop = terminalStream.scrollHeight;
    }

    function renderDiff(diff) {
        diffContainer.className = "diff-card-active";
        diffContainer.innerHTML = `
            <div class="diff-file-title">
                <i data-lucide="file-code" style="width:16px;height:16px;"></i>
                <span>${escapeHtml(diff.file)}</span>
            </div>
            <div class="diff-block-del">- ${escapeHtml(diff.target)}</div>
            <div class="diff-block-add">+ ${escapeHtml(diff.replacement)}</div>
        `;
        if (window.lucide) lucide.createIcons();
    }

    function renderTimeline(timeline) {
        activityTimeline.innerHTML = "";
        timeline.forEach((item, idx) => {
            const li = document.createElement("li");
            li.className = "step-item step-completed";
            li.innerHTML = `
                <div class="step-node"><i data-lucide="check"></i></div>
                <div class="step-content">
                    <span class="step-title">${escapeHtml(item.status)}</span>
                    <span class="step-desc">${escapeHtml(item.info)}</span>
                </div>
            `;
            activityTimeline.appendChild(li);
        });
        if (window.lucide) lucide.createIcons();
    }

    function triggerHealTask(autoDetect, pastedErr = null) {
        const payload = {
            target_dir: targetDirInput.value.trim() || "./demo-app",
            build_cmd: buildCmdInput.value.trim() || "npm run build",
            auto_detect: autoDetect,
            pasted_error: pastedErr,
            model_name: modelSelect.value
        };

        fetch("/api/heal", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "STARTED") {
                appendLogEntry({ type: "SYSTEM", message: "🚀 Autonomous Healer initiated from ADK Web Dashboard." });
            } else {
                alert("Error: " + (data.detail || "Failed to start task"));
            }
        })
        .catch(err => alert("Network Error: " + err.message));
    }

    // Button Listeners
    btnAutoHeal.addEventListener("click", () => triggerHealTask(true));

    btnTogglePaste.addEventListener("click", () => {
        pasteSection.classList.toggle("hidden");
    });

    btnSubmitPaste.addEventListener("click", () => {
        const text = pastedErrorText.value.trim();
        if (!text) {
            alert("Please paste build error logs first!");
            return;
        }
        triggerHealTask(false, text);
    });

    btnClearLogs.addEventListener("click", () => {
        terminalStream.innerHTML = '<div class="log-line log-system"><span class="log-time">[SYSTEM]</span> Terminal logs cleared.</div>';
    });

    function escapeHtml(str) {
        return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    connectWebSocket();
});
