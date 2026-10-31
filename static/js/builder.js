/**
 * Dynamic NFA Builder Controller
 */

let nfaGraph = null;

// Working NFA in-memory state
let currentNFA = {
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

document.addEventListener("DOMContentLoaded", () => {
    initGraph();
    loadSavedOrInitialNFA();
    setupEventListeners();
    renderAll();
});

function initGraph() {
    nfaGraph = new AutomataGraph("nfa-builder-graph", {
        onNodeClick: (data) => {
            selectNodeInUI(data.id);
        }
    });

    document.getElementById("btn-fit-graph")?.addEventListener("click", () => nfaGraph.fit());
    document.getElementById("btn-reset-layout")?.addEventListener("click", () => nfaGraph.resetLayout());
}

function loadSavedOrInitialNFA() {
    const saved = localStorage.getItem("current_nfa");
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            if (parsed && Array.isArray(parsed.states) && parsed.states.length > 0) {
                currentNFA = parsed;
            }
        } catch (e) {
            console.error("Failed to parse saved NFA from localStorage", e);
        }
    }
}

function saveToLocalStorage(isCustom = true) {
    localStorage.setItem("current_nfa", JSON.stringify(currentNFA));
    if (isCustom) {
        localStorage.setItem("current_nfa_title", "Custom Automaton");
        if (typeof updateActiveAutomatonBadge === "function") {
            updateActiveAutomatonBadge();
        }
    }
    // Invalidate stale DFA
    localStorage.removeItem("current_dfa");
    localStorage.removeItem("current_conversion_events");
    notifyStaleDFA();
}

function notifyStaleDFA() {
    const banner = document.getElementById("stale-banner");
    if (banner) banner.style.display = "block";
}

// ----------------- RENDERING -----------------

function renderAll() {
    renderStatesList();
    renderAlphabetList();
    renderInitialStateSelector();
    renderAcceptingStatesSelector();
    renderTransitionDropdowns();
    renderTransitionList();
    renderTransitionTable();
    refreshGraph();
}

function renderStatesList() {
    const container = document.getElementById("states-chip-container");
    if (!container) return;
    container.innerHTML = "";

    currentNFA.states.forEach(state => {
        const isInit = (state === currentNFA.initial_state);
        const isAcc = currentNFA.accepting_states.includes(state);

        // Check if dead state (non-initial, non-accepting with 0 transitions)
        let isDead = false;
        if (!isInit && !isAcc) {
            let totalOutgoing = 0;
            currentNFA.alphabet.forEach(sym => {
                const dests = (currentNFA.transitions[state] && currentNFA.transitions[state][sym]) || [];
                totalOutgoing += dests.length;
            });
            if (totalOutgoing === 0 || state.toLowerCase().includes("dead") || state.includes("∅")) {
                isDead = true;
            }
        }

        const chip = document.createElement("span");
        chip.className = `chip ${isInit ? 'chip-initial' : ''} ${isAcc ? 'chip-accepting' : ''} ${isDead ? 'chip-dead' : ''}`;
        chip.innerHTML = `
            <span>${escapeHtml(state)}</span>
            ${isInit ? '<span class="badge bg-primary rounded-pill" style="font-size:0.65rem;">START</span>' : ''}
            ${isAcc ? '<span class="badge bg-success rounded-pill" style="font-size:0.65rem;">FINAL</span>' : ''}
            ${isDead ? '<span class="badge bg-danger rounded-pill" style="font-size:0.65rem;">DEAD (∅)</span>' : ''}
            <button type="button" class="btn-chip-remove" title="Delete State" onclick="deleteState('${escapeHtml(state)}')">
                <i class="bi bi-x-circle-fill"></i>
            </button>
        `;
        container.appendChild(chip);
    });
}

function renderAlphabetList() {
    const container = document.getElementById("alphabet-chip-container");
    if (!container) return;
    container.innerHTML = "";

    currentNFA.alphabet.forEach(sym => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.innerHTML = `
            <span>${escapeHtml(sym)}</span>
            <button type="button" class="btn-chip-remove" title="Delete Symbol" onclick="deleteSymbol('${escapeHtml(sym)}')">
                <i class="bi bi-x-circle-fill"></i>
            </button>
        `;
        container.appendChild(chip);
    });
}

function renderInitialStateSelector() {
    const select = document.getElementById("select-initial-state");
    if (!select) return;
    select.innerHTML = "";

    currentNFA.states.forEach(state => {
        const opt = document.createElement("option");
        opt.value = state;
        opt.textContent = state;
        if (state === currentNFA.initial_state) {
            opt.selected = true;
        }
        select.appendChild(opt);
    });
}

function renderAcceptingStatesSelector() {
    const container = document.getElementById("accepting-checkboxes-container");
    if (!container) return;
    container.innerHTML = "";

    currentNFA.states.forEach(state => {
        const isAcc = currentNFA.accepting_states.includes(state);
        const wrap = document.createElement("div");
        wrap.className = "form-check form-check-inline";
        wrap.innerHTML = `
            <input class="form-check-input" type="checkbox" id="acc-${escapeHtml(state)}" value="${escapeHtml(state)}" ${isAcc ? 'checked' : ''} onchange="toggleAcceptingState('${escapeHtml(state)}')">
            <label class="form-check-label font-monospace" for="acc-${escapeHtml(state)}">${escapeHtml(state)}</label>
        `;
        container.appendChild(wrap);
    });
}

function renderTransitionDropdowns() {
    const fromSelect = document.getElementById("trans-from");
    const symSelect = document.getElementById("trans-symbol");
    const toSelect = document.getElementById("trans-to");
    if (!fromSelect || !symSelect || !toSelect) return;

    fromSelect.innerHTML = currentNFA.states.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join("");
    symSelect.innerHTML = currentNFA.alphabet.map(a => `<option value="${escapeHtml(a)}">${escapeHtml(a)}</option>`).join("");
    toSelect.innerHTML = currentNFA.states.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join("");
}

function renderTransitionList() {
    const container = document.getElementById("transition-list-container");
    const countBadge = document.getElementById("transition-count-badge");
    if (!container) return;
    container.innerHTML = "";

    let totalCount = 0;

    currentNFA.states.forEach(u => {
        if (!currentNFA.transitions[u]) return;
        currentNFA.alphabet.forEach(sym => {
            const dests = currentNFA.transitions[u][sym] || [];
            dests.forEach(v => {
                totalCount++;
                const item = document.createElement("div");
                item.className = "transition-item";
                item.innerHTML = `
                    <div>
                        <span class="badge bg-light text-dark border me-1">${escapeHtml(u)}</span>
                        <span class="text-secondary">&mdash; <b>${escapeHtml(sym)}</b> &rarr;</span>
                        <span class="badge bg-light text-dark border ms-1">${escapeHtml(v)}</span>
                    </div>
                    <button class="btn btn-sm btn-outline-danger py-0 px-1" title="Delete Transition" onclick="deleteTransition('${escapeHtml(u)}', '${escapeHtml(sym)}', '${escapeHtml(v)}')">
                        <i class="bi bi-trash3"></i>
                    </button>
                `;
                container.appendChild(item);
            });
        });
    });

    if (totalCount === 0) {
        container.innerHTML = `<div class="p-3 text-muted text-center small">No transitions defined yet.</div>`;
    }

    if (countBadge) countBadge.textContent = totalCount;
}

function renderTransitionTable() {
    const tableHead = document.getElementById("nfa-table-head");
    const tableBody = document.getElementById("nfa-table-body");
    if (!tableHead || !tableBody) return;

    // Header
    let headHtml = `<tr><th>State</th>`;
    currentNFA.alphabet.forEach(sym => {
        headHtml += `<th>Symbol '${escapeHtml(sym)}'</th>`;
    });
    headHtml += `</tr>`;
    tableHead.innerHTML = headHtml;

    // Body
    let bodyHtml = "";
    currentNFA.states.forEach(u => {
        let prefix = "";
        if (u === currentNFA.initial_state) prefix += "&rarr; ";
        if (currentNFA.accepting_states.includes(u)) prefix += "* ";

        bodyHtml += `<tr><td class="fw-bold">${prefix}${escapeHtml(u)}</td>`;
        currentNFA.alphabet.forEach(sym => {
            const dests = (currentNFA.transitions[u] && currentNFA.transitions[u][sym]) || [];
            if (dests.length > 0) {
                bodyHtml += `<td>{${dests.map(d => escapeHtml(d)).join(", ")}}</td>`;
            } else {
                bodyHtml += `<td class="text-muted">&empty;</td>`;
            }
        });
        bodyHtml += `</tr>`;
    });
    tableBody.innerHTML = bodyHtml;
}

async function refreshGraph() {
    try {
        const res = await fetch("/api/automata/visualize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentNFA)
        });
        const data = await res.json();
        if (data.success && data.data && nfaGraph) {
            nfaGraph.render(data.data.cytoscape_elements);
        }
    } catch (e) {
        console.error("Failed to visualize NFA", e);
    }
}

// ----------------- ACTIONS -----------------

function addState() {
    const input = document.getElementById("input-new-state");
    if (!input) return;
    const name = input.value.trim();

    if (!name) {
        showNotification("State name cannot be empty.", "warning");
        return;
    }
    if (currentNFA.states.includes(name)) {
        showNotification(`State '${name}' already exists.`, "warning");
        return;
    }

    currentNFA.states.push(name);
    if (!currentNFA.transitions[name]) {
        currentNFA.transitions[name] = {};
        currentNFA.alphabet.forEach(sym => {
            currentNFA.transitions[name][sym] = [];
        });
    }

    if (!currentNFA.initial_state) {
        currentNFA.initial_state = name;
    }

    input.value = "";
    saveToLocalStorage();
    renderAll();
    showNotification(`Added state '${name}'`, "success");
}

function deleteState(stateName) {
    if (currentNFA.states.length <= 1) {
        showNotification("An automaton must have at least one state.", "warning");
        return;
    }

    currentNFA.states = currentNFA.states.filter(s => s !== stateName);
    currentNFA.accepting_states = currentNFA.accepting_states.filter(s => s !== stateName);

    // If initial state was deleted, set to first remaining
    if (currentNFA.initial_state === stateName) {
        currentNFA.initial_state = currentNFA.states[0];
    }

    // Clean up transitions
    delete currentNFA.transitions[stateName];
    Object.keys(currentNFA.transitions).forEach(u => {
        Object.keys(currentNFA.transitions[u]).forEach(sym => {
            currentNFA.transitions[u][sym] = currentNFA.transitions[u][sym].filter(v => v !== stateName);
        });
    });

    saveToLocalStorage();
    renderAll();
    showNotification(`Deleted state '${stateName}' and cleaned up associated transitions.`, "info");
}

function addSymbol() {
    const input = document.getElementById("input-new-symbol");
    if (!input) return;
    const sym = input.value.trim();

    if (!sym) {
        showNotification("Symbol cannot be empty.", "warning");
        return;
    }

    const reserved = ["", "ε", "epsilon", "λ", "lambda"];
    if (reserved.includes(sym.toLowerCase())) {
        showNotification("Epsilon transitions are strictly prohibited for ordinary NFAs.", "danger");
        return;
    }

    if (currentNFA.alphabet.includes(sym)) {
        showNotification(`Symbol '${sym}' already exists in alphabet.`, "warning");
        return;
    }

    currentNFA.alphabet.push(sym);
    currentNFA.states.forEach(u => {
        if (!currentNFA.transitions[u]) currentNFA.transitions[u] = {};
        if (!currentNFA.transitions[u][sym]) currentNFA.transitions[u][sym] = [];
    });

    input.value = "";
    saveToLocalStorage();
    renderAll();
    showNotification(`Added symbol '${sym}' to alphabet.`, "success");
}

function deleteSymbol(sym) {
    if (currentNFA.alphabet.length <= 1) {
        showNotification("The alphabet must have at least one symbol.", "warning");
        return;
    }

    currentNFA.alphabet = currentNFA.alphabet.filter(s => s !== sym);
    currentNFA.states.forEach(u => {
        if (currentNFA.transitions[u]) {
            delete currentNFA.transitions[u][sym];
        }
    });

    saveToLocalStorage();
    renderAll();
    showNotification(`Removed symbol '${sym}' from alphabet.`, "info");
}

function changeInitialState(newInit) {
    if (currentNFA.states.includes(newInit)) {
        currentNFA.initial_state = newInit;
        saveToLocalStorage();
        renderAll();
        showNotification(`Initial state set to '${newInit}'.`, "info");
    }
}

function toggleAcceptingState(state) {
    if (currentNFA.accepting_states.includes(state)) {
        currentNFA.accepting_states = currentNFA.accepting_states.filter(s => s !== state);
    } else {
        currentNFA.accepting_states.push(state);
    }
    saveToLocalStorage();
    renderAll();
}

function addTransition() {
    const fromSelect = document.getElementById("trans-from");
    const symSelect = document.getElementById("trans-symbol");
    const toSelect = document.getElementById("trans-to");

    const u = fromSelect.value;
    const sym = symSelect.value;
    const v = toSelect.value;

    if (!u || !sym || !v) {
        showNotification("Select from-state, symbol, and to-state.", "warning");
        return;
    }

    if (!currentNFA.transitions[u]) currentNFA.transitions[u] = {};
    if (!currentNFA.transitions[u][sym]) currentNFA.transitions[u][sym] = [];

    if (currentNFA.transitions[u][sym].includes(v)) {
        showNotification(`Transition ${u} --${sym}--> ${v} already exists.`, "warning");
        return;
    }

    currentNFA.transitions[u][sym].push(v);
    saveToLocalStorage();
    renderAll();
    showNotification(`Added transition: ${u} --${sym}--> ${v}`, "success");
}

function deleteTransition(u, sym, v) {
    if (currentNFA.transitions[u] && currentNFA.transitions[u][sym]) {
        currentNFA.transitions[u][sym] = currentNFA.transitions[u][sym].filter(dest => dest !== v);
        saveToLocalStorage();
        renderAll();
        showNotification(`Deleted transition: ${u} --${sym}--> ${v}`, "info");
    }
}

async function validateCurrentNFA() {
    try {
        const res = await fetch("/api/automata/validate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(currentNFA)
        });
        const data = await res.json();
        if (data.success) {
            showNotification("Automaton is valid and ready for conversion!", "success");
            return true;
        } else {
            showNotification("Validation Error: " + data.error, "danger");
            return false;
        }
    } catch (e) {
        showNotification("Validation request failed: " + e.message, "danger");
        return false;
    }
}

async function proceedToConversion() {
    const isValid = await validateCurrentNFA();
    if (isValid) {
        window.location.href = "/conversion";
    }
}

function resetBuilder() {
    if (confirm("Reset NFA to default example? Any unsaved edits will be lost.")) {
        loadGlobalExample('binary_ends_with_01');
    }
}

function exportJSON() {
    const jsonStr = JSON.stringify(currentNFA, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "nfa_configuration.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showNotification("Exported NFA configuration to JSON.", "success");
}

function importJSON(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const data = JSON.parse(e.target.result);
            const res = await fetch("/api/automata/validate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });
            const check = await res.json();
            if (check.success) {
                currentNFA = data;
                saveToLocalStorage();
                renderAll();
                showNotification("Successfully imported and validated NFA!", "success");
            } else {
                showNotification("Import failed: " + check.error, "danger");
            }
        } catch (err) {
            showNotification("Malformed JSON file: " + err.message, "danger");
        }
        fileInput.value = "";
    };
    reader.readAsText(file);
}

async function exportCSV() {
    try {
        const res = await fetch("/api/export/csv", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                type: "nfa",
                automaton: currentNFA
            })
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "nfa_transition_table.csv";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification("Downloaded NFA transition table CSV.", "success");
        } else {
            showNotification("Failed to export CSV.", "danger");
        }
    } catch (e) {
        showNotification("Export error: " + e.message, "danger");
    }
}

function setupEventListeners() {
    document.getElementById("btn-add-state")?.addEventListener("click", addState);
    document.getElementById("input-new-state")?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") addState();
    });

    document.getElementById("btn-add-symbol")?.addEventListener("click", addSymbol);
    document.getElementById("input-new-symbol")?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") addSymbol();
    });

    document.getElementById("select-initial-state")?.addEventListener("change", (e) => {
        changeInitialState(e.target.value);
    });

    document.getElementById("btn-add-transition")?.addEventListener("click", addTransition);
    document.getElementById("btn-validate-nfa")?.addEventListener("click", validateCurrentNFA);
    document.getElementById("btn-convert-nfa")?.addEventListener("click", proceedToConversion);
    document.getElementById("btn-reset-nfa")?.addEventListener("click", resetBuilder);
    document.getElementById("btn-export-json")?.addEventListener("click", exportJSON);
    document.getElementById("btn-export-csv")?.addEventListener("click", exportCSV);

    const importInput = document.getElementById("file-import-json");
    importInput?.addEventListener("change", (e) => importJSON(e.target));
}

function selectNodeInUI(stateId) {
    const fromSelect = document.getElementById("trans-from");
    if (fromSelect && currentNFA.states.includes(stateId)) {
        fromSelect.value = stateId;
    }
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

