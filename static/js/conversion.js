/**
 * Conversion Studio Controller
 * - Renders the 100% complete DFA graph with Start arrow from the beginning
 * - Full stable graph during playback (no missing edges or states)
 * - Synchronized step highlights across NFA graph, DFA graph, and DFA transition table
 * - Plain-English, student-friendly explanations for non-tech students and viva exams
 */

let nfaGraph = null;
let dfaGraph = null;

let conversionData = null;
let events = [];
let currentStepIndex = 0;
let playbackTimer = null;
let playbackSpeedMs = 2400; // Fixed slow, comfortable pace for clear step-by-step observation

document.addEventListener("DOMContentLoaded", () => {
    initGraphs();
    setupControls();
    loadAndConvert();
});

function initGraphs() {
    nfaGraph = new AutomataGraph("conversion-nfa-graph");
    dfaGraph = new AutomataGraph("conversion-dfa-graph", {
        onNodeClick: (nodeData) => {
            showNodeInspector(nodeData);
        }
    });

    document.getElementById("btn-fit-nfa")?.addEventListener("click", () => nfaGraph.fit());
    document.getElementById("btn-reset-nfa-layout")?.addEventListener("click", () => nfaGraph.resetLayout());
    document.getElementById("btn-fit-dfa")?.addEventListener("click", () => dfaGraph.fit());
    document.getElementById("btn-reset-dfa-layout")?.addEventListener("click", () => dfaGraph.resetLayout());
}

async function loadAndConvert() {
    let savedNfa = localStorage.getItem("current_nfa");
    let nfaPayload = null;

    if (savedNfa) {
        try {
            nfaPayload = JSON.parse(savedNfa);
        } catch (e) {
            console.error("Invalid NFA in localStorage", e);
        }
    }

    if (!nfaPayload) {
        // Fallback default: Ends with '01'
        nfaPayload = {
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

    try {
        const res = await fetch("/api/conversion/convert", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(nfaPayload)
        });
        const data = await res.json();
        if (data.success && data.data) {
            conversionData = data.data;
            events = conversionData.events || [];

            // Store DFA in localStorage for Simulator
            localStorage.setItem("current_dfa", JSON.stringify(conversionData.dfa));
            localStorage.setItem("current_conversion_events", JSON.stringify(events));

            // 1. Render FULL Source NFA Graph (with Start ---> arrow)
            nfaGraph.render(conversionData.nfa_cytoscape);

            // 2. Render FULL Complete DFA Graph immediately (all states, all edges, and Start ---> arrow)
            dfaGraph.render(conversionData.cytoscape_elements);

            // 3. Render Comparison Metrics & Complete DFA Transition Table
            renderComparisonMetrics(conversionData.metrics);
            renderDfaTransitionTable(conversionData.transition_table);

            // 4. Initialize playback slider
            const slider = document.getElementById("step-slider");
            if (slider) {
                slider.max = events.length > 0 ? events.length - 1 : 0;
                slider.value = 0;
            }

            // 5. Jump to Step 0 and apply active highlights
            goToStep(0);

            // 6. Populate initial inspector with State A
            if (conversionData.dfa && conversionData.dfa.initial_state) {
                const initSt = conversionData.dfa.initial_state;
                showNodeInspector({
                    id: initSt,
                    display_name: initSt,
                    subset: conversionData.dfa.state_subsets[initSt],
                    subset_str: "{" + (conversionData.dfa.state_subsets[initSt] || []).join(", ") + "}",
                    is_initial: true,
                    is_accepting: conversionData.dfa.accepting_states.includes(initSt),
                    is_dead: (initSt === conversionData.dfa.dead_state),
                });
            }
        } else {
            showNotification("Conversion failed: " + (data.error || "Unknown error"), "danger");
        }
    } catch (e) {
        showNotification("Failed to connect to conversion API: " + e.message, "danger");
    }
}

function renderComparisonMetrics(metrics) {
    if (!metrics) return;
    document.getElementById("metric-nfa-states").textContent = metrics.num_nfa_states;
    document.getElementById("metric-dfa-states").textContent = metrics.num_dfa_states;
    document.getElementById("metric-nfa-accepting").textContent = metrics.num_nfa_accepting;
    document.getElementById("metric-dfa-accepting").textContent = metrics.num_dfa_accepting;
    document.getElementById("metric-nfa-transitions").textContent = metrics.num_nfa_transitions;
    document.getElementById("metric-dfa-transitions").textContent = metrics.num_dfa_transitions;

    const deadBadge = document.getElementById("metric-dead-state-badge");
    if (deadBadge) {
        if (metrics.has_dead_state) {
            deadBadge.innerHTML = `<span class="badge bg-danger fs-6 px-3 py-1"><i class="bi bi-shield-x me-1"></i> Dead State Present: State ${metrics.dead_state_label} (&empty;)</span>`;
        } else {
            deadBadge.innerHTML = `
                <span class="badge bg-secondary bg-opacity-10 text-secondary border me-1">No Dead State in this NFA</span>
                <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 fw-semibold" onclick="loadGlobalExample('dead_state_generation')" title="Load an NFA that generates an explicit Dead State (∅)">
                    <i class="bi bi-play-fill"></i> Load Dead State Example
                </button>
            `;
        }
    }
}

function renderDfaTransitionTable(table) {
    const tableHead = document.getElementById("dfa-table-head");
    const tableBody = document.getElementById("dfa-table-body");
    if (!tableHead || !tableBody || !table) return;

    let headHtml = "<tr>";
    table.headers.forEach(h => {
        headHtml += `<th>${escapeHtml(h)}</th>`;
    });
    headHtml += "</tr>";
    tableHead.innerHTML = headHtml;

    let bodyHtml = "";
    table.rows.forEach((row, rowIdx) => {
        const stateRaw = table.states[rowIdx];
        const isDeadState = (conversionData && conversionData.dfa && conversionData.dfa.dead_state === stateRaw);
        bodyHtml += `<tr id="dfa-table-row-${stateRaw}" class="${isDeadState ? 'table-danger' : ''}">`;
        row.forEach((cell, colIdx) => {
            const isStateCell = (colIdx === 0);
            const isSubsetCell = (colIdx === 1);
            let cellId = "";
            if (!isStateCell && !isSubsetCell) {
                const sym = table.alphabet[colIdx - 2];
                cellId = `id="dfa-cell-${stateRaw}-${sym}"`;
            }
            let cellContent = escapeHtml(cell);
            if (isStateCell && isDeadState) {
                cellContent += ` <span class="badge bg-danger ms-1" style="font-size:0.7rem;">Dead (∅)</span>`;
            }
            bodyHtml += `<td ${cellId} class="${isStateCell ? 'fw-bold' : ''}">${cellContent}</td>`;
        });
        bodyHtml += "</tr>";
    });
    tableBody.innerHTML = bodyHtml;
}

// ----------------- STEP PLAYBACK (STABLE GRAPH HIGHLIGHTING) -----------------

function goToStep(index) {
    if (!events || events.length === 0) return;
    if (index < 0) index = 0;
    if (index >= events.length) index = events.length - 1;

    currentStepIndex = index;
    const evt = events[currentStepIndex];

    // 1. Update Step Counter, Slider & Progress Bar
    const stepLabel = document.getElementById("step-counter-label");
    const badgeCounter = document.getElementById("step-badge-counter");
    const progressBar = document.getElementById("conversion-progress-bar");
    const slider = document.getElementById("step-slider");

    if (stepLabel) {
        stepLabel.textContent = `Step ${evt.step_number} of ${events.length - 1}`;
    }
    if (badgeCounter) {
        badgeCounter.textContent = `Step ${evt.step_number} of ${events.length - 1}`;
    }
    if (slider) {
        slider.value = currentStepIndex;
    }
    if (progressBar) {
        const pct = Math.round((currentStepIndex / (events.length - 1 || 1)) * 100);
        progressBar.style.width = `${pct}%`;
        progressBar.setAttribute("aria-valuenow", pct);
    }

    // 2. Render Student-Friendly Explanation Card
    renderFriendlyExplanation(evt);

    // 3. Highlight DFA Graph & NFA Graph in Sync without destroying Cytoscape
    updateGraphHighlights(evt);

    // 4. Highlight DFA Table Row and Cell
    updateTableHighlights(evt);

    // 5. Update Prev/Next button states
    const btnPrev = document.getElementById("btn-prev-step");
    const btnNext = document.getElementById("btn-next-step");
    if (btnPrev) btnPrev.disabled = (currentStepIndex === 0);
    if (btnNext) btnNext.disabled = (currentStepIndex === events.length - 1);
}

function updateGraphHighlights(evt) {
    if (dfaGraph) dfaGraph.clearHighlights();
    if (nfaGraph) nfaGraph.clearHighlights();

    if (evt.step_number === 0) {
        // Step 0: Starting point
        if (dfaGraph) {
            dfaGraph.highlightSourceNodes([evt.current_dfa_state]);
        }
        if (nfaGraph && evt.current_nfa_subset) {
            nfaGraph.highlightSourceNodes(evt.current_nfa_subset);
        }
    } else {
        // Step > 0: Evaluating transition
        if (dfaGraph) {
            // Source state in Gold
            dfaGraph.highlightSourceNodes([evt.current_dfa_state]);
            // Destination state in Green
            if (evt.destination_dfa_state) {
                dfaGraph.highlightTargetNode(evt.destination_dfa_state);
            }
            // Active Transition Edge in glowing Orange
            if (evt.current_dfa_state && evt.destination_dfa_state && evt.symbol) {
                dfaGraph.highlightTransitionEdge(evt.current_dfa_state, evt.destination_dfa_state, evt.symbol);
            }
        }

        if (nfaGraph) {
            // Source states in Gold
            nfaGraph.highlightSourceNodes(evt.current_nfa_subset);
            // Destination states in Green
            nfaGraph.highlightTargetNode(evt.resulting_nfa_subset);
            // Highlight NFA branching edges
            (evt.transitions_considered || []).forEach(t => {
                (t.to_states || []).forEach(v => {
                    nfaGraph.highlightTransitionEdge(t.from_state, v, t.symbol);
                });
            });
        }
    }
}

function updateTableHighlights(evt) {
    // Clear all previous highlights
    document.querySelectorAll("#dfa-table-body tr").forEach(tr => tr.classList.remove("table-warning"));
    document.querySelectorAll("#dfa-table-body td").forEach(td => td.classList.remove("table-success", "fw-bold", "border-warning"));

    if (evt.step_number > 0 && evt.current_dfa_state && evt.symbol) {
        const row = document.getElementById(`dfa-table-row-${evt.current_dfa_state}`);
        if (row) row.classList.add("table-warning");

        const cell = document.getElementById(`dfa-cell-${evt.current_dfa_state}-${evt.symbol}`);
        if (cell) {
            cell.classList.add("table-success", "fw-bold");
        }
    }
}

function renderFriendlyExplanation(evt) {
    const container = document.getElementById("step-explanation-content");
    if (!container) return;

    if (evt.step_number === 0) {
        container.innerHTML = `
            <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="badge bg-primary px-2 py-1 fs-6"><i class="bi bi-play-circle-fill me-1"></i> STEP 0: STARTING POINT</span>
                <span class="badge bg-light text-dark border font-monospace">Initial State Setup</span>
            </div>
            <div class="row g-2 align-items-center">
                <div class="col-md-8">
                    <p class="mb-1 text-slate-800 fw-medium">
                        Every DFA begins with a <b>"combo state"</b> containing only the NFA's start state.
                    </p>
                    <p class="mb-0 text-secondary small">
                        The NFA start state is <b>${escapeHtml(evt.current_nfa_subset[0])}</b> (marked with the blue <b>Start &rarr;</b> arrow). Therefore, our first DFA state is 
                        <span class="badge bg-warning text-dark font-monospace">${evt.current_dfa_state} = ${evt.current_nfa_subset_str}</span>.
                        We will now check where State A goes on every alphabet symbol.
                    </p>
                </div>
                <div class="col-md-4 text-center">
                    <div class="p-2 border rounded bg-white shadow-sm font-monospace">
                        <small class="text-muted d-block">Initial DFA State</small>
                        <span class="fs-4 fw-bold text-primary">${evt.current_dfa_state}</span>
                        <div class="small text-secondary">${evt.current_nfa_subset_str}</div>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    // Step > 0 explanation
    const transitionsText = (evt.transitions_considered || []).map(t => {
        const dests = t.to_states && t.to_states.length > 0 ? `{ ${t.to_states.join(", ")} }` : "&empty; (nowhere)";
        return `From <b>${t.from_state}</b> on <b>'${t.symbol}'</b> &rarr; goes to <b>${dests}</b>`;
    }).join("<br>");

    let statusBadge = "";
    let takeawayText = "";

    if (evt.is_new_state) {
        statusBadge = `<span class="badge bg-success"><i class="bi bi-sparkles me-1"></i> New State Discovered!</span>`;
        takeawayText = `✨ We haven't seen the combo <b>${evt.resulting_nfa_subset_str}</b> before! We name it <b>State ${evt.destination_dfa_state}</b> and add it to our checklist to explore later.`;
    } else {
        statusBadge = `<span class="badge bg-secondary">Existing State Reached</span>`;
        takeawayText = `🔄 The combo <b>${evt.resulting_nfa_subset_str}</b> was already discovered as <b>State ${evt.destination_dfa_state}</b>. So we draw the transition arrow without creating any duplicate state.`;
    }

    if (evt.is_dead_state) {
        statusBadge = `<span class="badge bg-danger"><i class="bi bi-shield-x me-1"></i> Dead / Trap State (&empty;)</span>`;
        takeawayText = `🚫 The NFA has nowhere to branch! In a complete DFA, we route this to the absorbing Dead State (<b>&empty;</b>) which loops to itself on all symbols.`;
    }

    let acceptingNotice = "";
    if (evt.is_accepting) {
        acceptingNotice = `
            <div class="mt-2 p-1 px-2 rounded bg-success bg-opacity-10 border border-success-subtle small text-success fw-medium">
                <i class="bi bi-check-circle-fill me-1"></i> <b>Final State Rule:</b> Because combo <b>${evt.resulting_nfa_subset_str}</b> contains an NFA accepting state, DFA State <b>${evt.destination_dfa_state}</b> is an <b>Accepting (Final) State</b> (double circle)!
            </div>
        `;
    }

    container.innerHTML = `
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-2">
            <div class="d-flex align-items-center gap-2">
                <span class="badge bg-primary px-2 py-1 fs-6">STEP ${evt.step_number}</span>
                <span class="fw-bold text-slate-900">Checking State ${evt.current_dfa_state} on input '${evt.symbol}'</span>
            </div>
            <div>${statusBadge}</div>
        </div>

        <!-- 3 Step Cards -->
        <div class="row g-2 mb-3">
            <div class="col-4">
                <div class="p-2 rounded bg-white border text-center shadow-sm">
                    <small class="text-muted d-block font-monospace" style="font-size:0.75rem;">1. CURRENT STATE</small>
                    <span class="fw-bold font-monospace text-primary fs-5">${evt.current_dfa_state}</span>
                    <small class="text-secondary d-block font-monospace">${evt.current_nfa_subset_str}</small>
                </div>
            </div>
            <div class="col-4">
                <div class="p-2 rounded bg-white border text-center shadow-sm">
                    <small class="text-muted d-block font-monospace" style="font-size:0.75rem;">2. INPUT SYMBOL</small>
                    <span class="fw-bold font-monospace text-dark fs-5">'${evt.symbol}'</span>
                    <small class="text-secondary d-block font-monospace">Read symbol</small>
                </div>
            </div>
            <div class="col-4">
                <div class="p-2 rounded ${evt.is_new_state ? 'bg-success bg-opacity-10 border border-success' : 'bg-white border'} text-center shadow-sm">
                    <small class="text-muted d-block font-monospace" style="font-size:0.75rem;">3. TARGET DFA STATE</small>
                    <span class="fw-bold font-monospace ${evt.is_new_state ? 'text-success' : 'text-primary'} fs-5">${evt.destination_dfa_state}</span>
                    <small class="text-secondary d-block font-monospace">${evt.resulting_nfa_subset_str}</small>
                </div>
            </div>
        </div>

        <!-- What the machine did -->
        <div class="p-2 px-3 bg-white rounded border mb-2 small text-secondary">
            <div class="fw-bold text-dark mb-1"><i class="bi bi-diagram-2 me-1 text-primary"></i> What is happening?</div>
            <div class="font-monospace text-dark mb-1">${transitionsText}</div>
            <div>Combined destinations (Union): <b class="text-primary font-monospace">${evt.resulting_nfa_subset_str}</b></div>
            <div class="mt-1">${takeawayText}</div>
        </div>

        <!-- DFA Arrow Summary & Accepting Notice -->
        <div class="d-flex align-items-center justify-content-between p-2 rounded bg-light font-monospace small">
            <span><b>DFA Transition Recorded:</b> <span class="badge bg-primary">${evt.current_dfa_state}</span> &mdash; <b>'${evt.symbol}'</b> &rarr; <span class="badge ${evt.is_new_state ? 'bg-success' : 'bg-primary'}">${evt.destination_dfa_state}</span></span>
        </div>
        ${acceptingNotice}
    `;
}

// ----------------- PLAYBACK BUTTON CONTROLS -----------------

function play() {
    if (playbackTimer) return;
    document.getElementById("btn-play")?.classList.add("d-none");
    document.getElementById("btn-pause")?.classList.remove("d-none");

    // Ensure graphs and step explanation card are smoothly in view for simulation
    const explanationCard = document.getElementById("step-explanation-card");
    if (explanationCard) {
        const rect = explanationCard.getBoundingClientRect();
        if (rect.top > window.innerHeight || rect.bottom < 0) {
            explanationCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
    }

    // If at the end, restart from step 0
    if (currentStepIndex >= events.length - 1) {
        goToStep(0);
    } else {
        // Immediate advance 1 step for instant tactile feedback
        goToStep(currentStepIndex + 1);
    }

    playbackTimer = setInterval(() => {
        if (currentStepIndex < events.length - 1) {
            goToStep(currentStepIndex + 1);
        } else {
            pause();
        }
    }, playbackSpeedMs);
}

function pause() {
    if (playbackTimer) {
        clearInterval(playbackTimer);
        playbackTimer = null;
    }
    document.getElementById("btn-play")?.classList.remove("d-none");
    document.getElementById("btn-pause")?.classList.add("d-none");
}

function resetPlayback() {
    pause();
    goToStep(0);
}

function nextStep() {
    pause();
    goToStep(currentStepIndex + 1);
}

function prevStep() {
    pause();
    goToStep(currentStepIndex - 1);
}

function showNodeInspector(nodeData) {
    const card = document.getElementById("dfa-node-inspector");
    if (!card) return;

    const stateId = nodeData.id || nodeData.display_name;
    const alphabet = (conversionData && conversionData.dfa) ? conversionData.dfa.alphabet : [];
    const transitionsMap = (conversionData && conversionData.dfa && conversionData.dfa.transitions) ? conversionData.dfa.transitions[stateId] || {} : {};

    let transitionsHtml = "";
    alphabet.forEach(sym => {
        const dest = transitionsMap[sym];
        transitionsHtml += `
            <div class="col-sm-6">
                <div class="p-2 rounded bg-light border font-monospace small">
                    <span class="text-muted">on <b>'${escapeHtml(sym)}'</b> &rarr;</span> 
                    <span class="badge bg-primary">${escapeHtml(dest || "—")}</span>
                    <span class="badge bg-success bg-opacity-10 text-success ms-1" style="font-size:0.65rem;">1 branch</span>
                </div>
            </div>
        `;
    });

    card.innerHTML = `
        <div class="p-3 border rounded bg-white shadow-sm">
            <h6 class="fw-bold mb-2 text-primary d-flex align-items-center justify-content-between">
                <span>DFA State: ${escapeHtml(nodeData.display_name || nodeData.id)}</span>
                ${nodeData.is_initial ? '<span class="badge bg-primary">START</span>' : ''}
                ${nodeData.is_accepting ? '<span class="badge bg-success">ACCEPTING</span>' : ''}
                ${nodeData.is_dead ? '<span class="badge bg-danger">DEAD STATE</span>' : ''}
            </h6>
            <div class="row g-2 small font-monospace mb-2">
                <div class="col-12"><span class="text-muted">NFA Subset:</span> <b>${escapeHtml(nodeData.subset_str || "∅")}</b></div>
                <div class="col-12"><span class="text-muted">Constituent States:</span> ${Array.isArray(nodeData.subset) && nodeData.subset.length > 0 ? nodeData.subset.join(", ") : "None (Empty Set)"}</div>
            </div>
            <div class="pt-2 border-top">
                <div class="d-flex align-items-center justify-content-between mb-1">
                    <small class="text-uppercase fw-bold text-secondary" style="font-size:0.75rem;">Deterministic Outgoing Transitions:</small>
                    <small class="text-success fw-bold" style="font-size:0.75rem;"><i class="bi bi-check2-circle"></i> Exactly 1 per symbol</small>
                </div>
                <div class="row g-1">
                    ${transitionsHtml}
                </div>
            </div>
        </div>
    `;
}

async function exportDfaCSV() {
    if (!conversionData || !conversionData.dfa) {
        showNotification("No DFA available to export.", "warning");
        return;
    }
    try {
        const res = await fetch("/api/export/csv", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                type: "dfa",
                automaton: conversionData.dfa
            })
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "dfa_transition_table.csv";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification("Downloaded DFA transition table CSV.", "success");
        }
    } catch (e) {
        showNotification("Failed to export DFA CSV: " + e.message, "danger");
    }
}

function setupControls() {
    document.getElementById("btn-start-step")?.addEventListener("click", () => { pause(); goToStep(0); });
    document.getElementById("btn-prev-step")?.addEventListener("click", prevStep);
    document.getElementById("btn-next-step")?.addEventListener("click", nextStep);
    document.getElementById("btn-play")?.addEventListener("click", play);
    document.getElementById("btn-pause")?.addEventListener("click", pause);
    document.getElementById("btn-reset-playback")?.addEventListener("click", resetPlayback);

    document.getElementById("step-slider")?.addEventListener("input", (e) => {
        pause();
        goToStep(parseInt(e.target.value));
    });

    document.getElementById("btn-export-dfa-csv")?.addEventListener("click", exportDfaCSV);
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
