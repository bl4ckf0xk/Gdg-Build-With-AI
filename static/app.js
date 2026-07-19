// ADK Web Dashboard Client Script

document.addEventListener("DOMContentLoaded", () => {
    const wsStatus = document.getElementById("wsStatus");
    const wsStatusText = document.getElementById("wsStatusText");
    const terminalStream = document.getElementById("terminalStream");
    const agentStatusBadge = document.getElementById("agentStatusBadge");
    const stepProgressText = document.getElementById("stepProgressText");
    const stepProgressBar = document.getElementById("stepProgressBar");
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
            wsStatus.classList.add("connected");
            wsStatusText.innerText = "Connected";
        };

        socket.onclose = () => {
            wsStatus.classList.remove("connected");
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
        // Update Agent Status Badge
        agentStatusBadge.className = "agent-status-badge status-" + (state.status || "idle").toLowerCase();
        agentStatusBadge.innerText = (state.status || "IDLE").replace("_", " ");

        // Update Step Progress
        const current = state.current_step || 0;
        const total = state.total_steps || 15;
        stepProgressText.innerText = `${current} / ${total}`;
        const pct = Math.min(100, Math.round((current / total) * 100));
        stepProgressBar.style.width = `${pct}%`;

        // Update Code Diff if available
        if (state.last_diff) {
            renderDiff(state.last_diff);
        }

        // Update Timeline
        if (state.timeline && state.timeline.length > 0) {
            renderTimeline(state.timeline);
        }
    }

    function appendLogEntry(log) {
        const entry = document.createElement("div");
        entry.className = `log-entry ${log.type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        entry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${escapeHtml(log.message)}`;

        if (log.meta && log.meta.output) {
            const outputBox = document.createElement("pre");
            outputBox.style.fontSize = "0.775rem";
            outputBox.style.opacity = "0.8";
            outputBox.style.marginTop = "0.2rem";
            outputBox.innerText = log.meta.output;
            entry.appendChild(outputBox);
        }

        terminalStream.appendChild(entry);
        terminalStream.scrollTop = terminalStream.scrollHeight;
    }

    function renderDiff(diff) {
        diffContainer.className = "diff-container";
        diffContainer.innerHTML = `
            <div class="diff-file-name">📄 File: ${escapeHtml(diff.file)}</div>
            <div class="diff-line-del">- ${escapeHtml(diff.target)}</div>
            <div class="diff-line-add">+ ${escapeHtml(diff.replacement)}</div>
        `;
    }

    function renderTimeline(timeline) {
        activityTimeline.innerHTML = "";
        timeline.slice(-6).forEach(item => {
            const li = document.createElement("li");
            li.className = "timeline-item";
            li.innerHTML = `
                <span class="timeline-icon">⚙️</span>
                <div class="timeline-content">
                    <div class="timeline-title">${escapeHtml(item.status)}</div>
                    <div class="timeline-desc">${escapeHtml(item.info)}</div>
                </div>
            `;
            activityTimeline.appendChild(li);
        });
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
                appendLogEntry({ type: "SYSTEM", message: "🚀 Healing task initiated from Web Dashboard." });
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
        terminalStream.innerHTML = '<div class="log-entry system-log"><span class="timestamp">[SYSTEM]</span> Console cleared.</div>';
    });

    function escapeHtml(str) {
        return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    connectWebSocket();
});
