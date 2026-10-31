/**
 * String Simulator Controller
 * - Responsive execution & smooth playback
 * - Synchronized live graph animation (states & transition edges)
 * - Trace table auto-scroll & highlighting
 * - Plain-English explanations for students & viva examination
 */

let nfaGraph = null;
let dfaGraph = null;

let currentNfa = null;
let currentDfa = null;

let currentSimulationResult = null;
let activeTrace = [];
let simStepIndex = 0;
let simTimer = null;
let simSpeedMs = 2000; // Fixed slow, comfortable simulation speed

document.addEventListener("DOMContentLoaded", () => {
    initSimulator();
});

async function initSimulator() {
    nfaGraph = new AutomataGraph("sim-nfa-graph");
    dfaGraph = new AutomataGraph("sim-dfa-graph");

    document.getElementById("btn-fit-sim-nfa")?.addEventListener("click", () => nfaGraph.fit());
    document.getElementById("btn-fit-sim-dfa")?.addEventListener("click", () => dfaGraph.fit());

    setupEventListeners();
    await loadAutomata();
}

async function loadAutomata() {
    const savedNfa = localStorage.getItem("current_nfa");
    if (savedNfa) {
        try {
            currentNfa = JSON.parse(savedNfa);
        } catch (e) {
            console.error("Failed to parse stored NFA", e);
        }
    }

    if (!currentNfa) {
        currentNfa = {
            states: ["q0", "q1", "q2"],
            alphabet: ["0", "1"],
            initial_state: "q0",
            accepting_states: ["q2"],
            transitions: {
                "q0": { "0": ["q0", "q1"], "1": ["q0"] },
                "q1": { "1": ["q2"] },
                "q2": {}
            }
        };
    }

    // Render NFA graph
    try {
        const res = await fetch("/api/automata/visualize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentNfa)
        });
        const nfaData = await res.json();
        if (nfaData.success && nfaData.data) {
            nfaGraph.render(nfaData.data.cytoscape_elements);
        }
    } catch (e) {
        console.error("NFA visualization error", e);
    }

    // Convert and render DFA graph
    try {
        const convRes = await fetch("/api/conversion/convert", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentNfa)
        });
        const convData = await convRes.json();
        if (convData.success && convData.data) {
            currentDfa = convData.data.dfa;
            localStorage.setItem("current_dfa", JSON.stringify(currentDfa));
            dfaGraph.render(convData.data.cytoscape_elements);
        }
    } catch (e) {
        console.error("DFA conversion error", e);
    }

    // Populate alphabet hint
    const alphabetBadge = document.getElementById("sim-alphabet-hint");
    if (alphabetBadge) {
        alphabetBadge.textContent = `{ ${currentNfa.alphabet.join(", ")} }`;
    }

    // Populate dynamic test string samples matching this automaton
    renderDynamicSampleButtons();
}

function renderDynamicSampleButtons() {
    const container = document.getElementById("sim-quick-samples-container");
    if (!container || !currentNfa || !currentNfa.alphabet) return;

    const alphabet = currentNfa.alphabet;
    const samples = [];
    if (alphabet.length >= 2) {
        samples.push(alphabet[0]);
        samples.push(alphabet[1]);
        samples.push(alphabet[0] + alphabet[1]);
        samples.push(alphabet[1] + alphabet[0]);
        samples.push(alphabet[0] + alphabet[0] + alphabet[1]);
    } else if (alphabet.length === 1) {
        samples.push(alphabet[0]);
        samples.push(alphabet[0] + alphabet[0]);
    }

    let html = `<small class="text-muted fw-bold font-monospace me-1">Samples:</small>`;
    samples.forEach(s => {
        html += `<button type="button" class="btn btn-sm btn-outline-secondary font-monospace py-0 px-2" onclick="setTestString('${escapeHtml(s)}')">"${escapeHtml(s)}"</button> `;
    });
    html += `<button type="button" class="btn btn-sm btn-outline-secondary font-monospace py-0 px-2" onclick="setTestString('')">&epsilon; (Empty)</button>`;

    container.innerHTML = html;
}

// ----------------- SIMULATION EXECUTION -----------------

async function runSimulation(mode = "both") {
    pauseSim();

    const inputField = document.getElementById("input-sim-string");
    const inputString = inputField ? inputField.value.trim() : "";

    const payload = {
        mode: mode,
        input_string: inputString,
        nfa: currentNfa,
        dfa: currentDfa,
    };

    try {
        const res = await fetch("/api/simulation/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!data.success) {
            showNotification(data.error || "Simulation error occurred.", "danger");
            return;
        }

        currentSimulationResult = data.data;
        displaySimulationResults(mode, currentSimulationResult);
    } catch (e) {
        showNotification("Simulation request failed: " + e.message, "danger");
    }
}

function displaySimulationResults(mode, result) {
    const resultContainer = document.getElementById("simulation-result-container");
    if (resultContainer) resultContainer.classList.remove("d-none");

    const banner = document.getElementById("sim-acceptance-banner");
    const bannerTitle = document.getElementById("sim-banner-title");
    const bannerDesc = document.getElementById("sim-banner-desc");

    let isAccepted = false;
    let desc = "";

    if (mode === "both") {
        isAccepted = result.accepted;
        desc = `${result.comparison_note} (Tested String: "${result.display_input}")`;
        activeTrace = result.nfa_result.trace;
    } else if (mode === "nfa") {
        isAccepted = result.accepted;
        desc = `${result.summary} (Tested String: "${result.display_input}")`;
        activeTrace = result.trace;
    } else {
        isAccepted = result.accepted;
        desc = `${result.summary} (Tested String: "${result.display_input}")`;
        activeTrace = result.trace;
    }

    if (banner && bannerTitle && bannerDesc) {
        banner.className = `result-banner ${isAccepted ? 'accepted' : 'rejected'}`;
        bannerTitle.innerHTML = isAccepted
            ? `<i class="bi bi-check-circle-fill text-success fs-3"></i> <span class="fw-bold fs-4 text-success">ACCEPTED</span>`
            : `<i class="bi bi-x-circle-fill text-danger fs-3"></i> <span class="fw-bold fs-4 text-danger">REJECTED</span>`;
        bannerDesc.innerHTML = `<span class="fw-medium">${escapeHtml(desc)}</span>`;
    }

    // Render Trace Tables
    renderTraceTables(mode, result);

    // Initialize playback slider
    const slider = document.getElementById("sim-step-slider");
    if (slider) {
        slider.max = activeTrace.length > 0 ? activeTrace.length - 1 : 0;
        slider.value = 0;
    }

    goToSimStep(0);
}

function renderTraceTables(mode, result) {
    const nfaTraceCard = document.getElementById("card-nfa-trace");
    const dfaTraceCard = document.getElementById("card-dfa-trace");

    if (mode === "nfa") {
        if (nfaTraceCard) nfaTraceCard.classList.remove("d-none");
        if (dfaTraceCard) dfaTraceCard.classList.add("d-none");
        renderNfaTraceTable(result.trace);
    } else if (mode === "dfa") {
        if (nfaTraceCard) nfaTraceCard.classList.add("d-none");
        if (dfaTraceCard) dfaTraceCard.classList.remove("d-none");
        renderDfaTraceTable(result.trace);
    } else {
        if (nfaTraceCard) nfaTraceCard.classList.remove("d-none");
        if (dfaTraceCard) dfaTraceCard.classList.remove("d-none");
        renderNfaTraceTable(result.nfa_result.trace);
        renderDfaTraceTable(result.dfa_result.trace);
    }
}

function renderNfaTraceTable(trace) {
    const tbody = document.getElementById("nfa-trace-tbody");
    if (!tbody || !trace) return;

    let html = "";
    trace.forEach((row, idx) => {
        html += `
            <tr id="nfa-trace-row-${idx}" onclick="pauseSim(); goToSimStep(${idx});" style="cursor: pointer;">
                <td class="fw-bold font-monospace">${row.step}</td>
                <td><span class="badge bg-secondary font-monospace">${escapeHtml(row.symbol_read)}</span></td>
                <td><span class="badge ${row.is_accepting ? 'bg-success' : 'bg-primary'} font-monospace">${escapeHtml(row.active_states_str)}</span></td>
                <td class="small text-secondary font-monospace">${escapeHtml(row.explanation)}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

function renderDfaTraceTable(trace) {
    const tbody = document.getElementById("dfa-trace-tbody");
    if (!tbody || !trace) return;

    let html = "";
    trace.forEach((row, idx) => {
        html += `
            <tr id="dfa-trace-row-${idx}" onclick="pauseSim(); goToSimStep(${idx});" style="cursor: pointer;">
                <td class="fw-bold font-monospace">${row.step}</td>
                <td><span class="badge bg-secondary font-monospace">${escapeHtml(row.symbol_read)}</span></td>
                <td><span class="badge ${row.is_accepting ? 'bg-success' : (row.is_dead_state ? 'bg-danger' : 'bg-primary')} font-monospace">${escapeHtml(row.current_state)} (${escapeHtml(row.subset_str)})</span></td>
                <td class="small text-secondary font-monospace">${escapeHtml(row.explanation)}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

// ----------------- STEP PLAYBACK -----------------

function goToSimStep(index) {
    if (!activeTrace || activeTrace.length === 0) return;
    if (index < 0) index = 0;
    if (index >= activeTrace.length) index = activeTrace.length - 1;

    simStepIndex = index;

    // Update Slider & Counter
    const slider = document.getElementById("sim-step-slider");
    const label = document.getElementById("sim-step-counter");
    if (slider) slider.value = simStepIndex;
    if (label) label.textContent = `Step ${simStepIndex} of ${activeTrace.length - 1}`;

    // Highlight rows in trace tables
    highlightTraceRows(simStepIndex);

    // Live Step Ticker Info
    const ticker = document.getElementById("sim-live-ticker");

    // Synchronize NFA and DFA graph highlighting
    if (currentSimulationResult) {
        let nfaStep = null;
        let dfaStep = null;

        if (currentSimulationResult.nfa_result) {
            nfaStep = currentSimulationResult.nfa_result.trace[simStepIndex];
        } else if (currentSimulationResult.automaton_type === "NFA") {
            nfaStep = currentSimulationResult.trace[simStepIndex];
        }

        if (currentSimulationResult.dfa_result) {
            dfaStep = currentSimulationResult.dfa_result.trace[simStepIndex];
        } else if (currentSimulationResult.automaton_type === "DFA") {
            dfaStep = currentSimulationResult.trace[simStepIndex];
        }

        // Animate NFA graph
        if (nfaGraph && nfaStep) {
            nfaGraph.clearHighlights();
            nfaGraph.highlightSourceNodes(nfaStep.active_states);

            // Highlight transitions used in this step
            if (nfaStep.transitions_used && nfaStep.transitions_used.length > 0) {
                nfaStep.transitions_used.forEach(t => {
                    nfaGraph.highlightTransitionEdge(t.from, t.to, t.symbol);
                });
            }
        }

        // Animate DFA graph
        if (dfaGraph && dfaStep) {
            dfaGraph.clearHighlights();
            dfaGraph.highlightSourceNodes([dfaStep.current_state]);

            // If not step 0, highlight edge from previous step state
            if (simStepIndex > 0) {
                const prevDfaStep = (currentSimulationResult.dfa_result ? currentSimulationResult.dfa_result.trace : currentSimulationResult.trace)[simStepIndex - 1];
                if (prevDfaStep && dfaStep.symbol_read) {
                    dfaGraph.highlightTransitionEdge(prevDfaStep.current_state, dfaStep.current_state, dfaStep.symbol_read);
                }
            }
        }

        // Update live ticker bar
        if (ticker && nfaStep) {
            ticker.innerHTML = `
                <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 p-2 rounded bg-light border font-monospace small">
                    <div>
                        <span class="badge bg-primary me-2">STEP ${simStepIndex}</span>
                        <span>Read: <b>${escapeHtml(nfaStep.symbol_read)}</b></span>
                        <span class="mx-2 text-muted">|</span>
                        <span>NFA Branch: <span class="badge ${nfaStep.is_accepting ? 'bg-success' : 'bg-primary'}">${escapeHtml(nfaStep.active_states_str)}</span></span>
                        ${dfaStep ? `<span class="mx-2 text-muted">|</span><span>DFA State: <span class="badge ${dfaStep.is_accepting ? 'bg-success' : 'bg-primary'}">${escapeHtml(dfaStep.current_state)} (${escapeHtml(dfaStep.subset_str)})</span></span>` : ''}
                    </div>
                    <div>
                        ${nfaStep.is_accepting ? '<span class="badge bg-success"><i class="bi bi-check-circle-fill me-1"></i>Accepting State Reached</span>' : '<span class="badge bg-secondary">In Progress</span>'}
                    </div>
                </div>
            `;
        }
    }
}

function highlightTraceRows(index) {
    document.querySelectorAll(".table-trace tbody tr").forEach(tr => {
        tr.classList.remove("trace-active");
    });

    const nfaRow = document.getElementById(`nfa-trace-row-${index}`);
    if (nfaRow) {
        nfaRow.classList.add("trace-active");
        nfaRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    const dfaRow = document.getElementById(`dfa-trace-row-${index}`);
    if (dfaRow) {
        dfaRow.classList.add("trace-active");
        dfaRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function playSim() {
    if (simTimer) return;

    // If simulation results not loaded yet, run simulation first!
    if (!currentSimulationResult || activeTrace.length === 0) {
        runSimulation("both").then(() => {
            startSimInterval();
        });
        return;
    }

    startSimInterval();
}

function startSimInterval() {
    document.getElementById("btn-sim-play")?.classList.add("d-none");
    document.getElementById("btn-sim-pause")?.classList.remove("d-none");

    // If at end, wrap around to 0
    if (simStepIndex >= activeTrace.length - 1) {
        goToSimStep(0);
    } else {
        // Immediately advance 1 step for instant tactile feedback
        goToSimStep(simStepIndex + 1);
    }

    simTimer = setInterval(() => {
        if (simStepIndex < activeTrace.length - 1) {
            goToSimStep(simStepIndex + 1);
        } else {
            pauseSim();
        }
    }, simSpeedMs);
}

function pauseSim() {
    if (simTimer) {
        clearInterval(simTimer);
        simTimer = null;
    }
    document.getElementById("btn-sim-play")?.classList.remove("d-none");
    document.getElementById("btn-sim-pause")?.classList.add("d-none");
}

function resetSimPlayback() {
    pauseSim();
    goToSimStep(0);
}

function nextSimStep() {
    pauseSim();
    goToSimStep(simStepIndex + 1);
}

function prevSimStep() {
    pauseSim();
    goToSimStep(simStepIndex - 1);
}

function setTestString(str) {
    const input = document.getElementById("input-sim-string");
    if (input) {
        input.value = str;
        runSimulation("both");
    }
}

function setupEventListeners() {
    document.getElementById("btn-run-both")?.addEventListener("click", () => runSimulation("both"));
    document.getElementById("btn-run-nfa")?.addEventListener("click", () => runSimulation("nfa"));
    document.getElementById("btn-run-dfa")?.addEventListener("click", () => runSimulation("dfa"));

    document.getElementById("input-sim-string")?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") runSimulation("both");
    });

    document.getElementById("btn-sim-start")?.addEventListener("click", () => { pauseSim(); goToSimStep(0); });
    document.getElementById("btn-sim-prev")?.addEventListener("click", prevSimStep);
    document.getElementById("btn-sim-next")?.addEventListener("click", nextSimStep);
    document.getElementById("btn-sim-play")?.addEventListener("click", playSim);
    document.getElementById("btn-sim-pause")?.addEventListener("click", pauseSim);
    document.getElementById("btn-sim-reset")?.addEventListener("click", resetSimPlayback);

    document.getElementById("sim-step-slider")?.addEventListener("input", (e) => {
        pauseSim();
        goToSimStep(parseInt(e.target.value));
    });
}

function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
