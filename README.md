# Interactive NFA-to-DFA Conversion & Simulation Studio (TOC Project) — Group ID: [Group ID]

> **Academic Project:** Theory of Computation (TOC) / Automata Theory and Computability  
> **Repository:** [Automata-Theory-and-Computability](https://github.com/ShauriyaDeveloper1/Automata-Theory-and-Computability)

---

## Overview

This project is an educational web-based simulator built for **Theory of Computation (TOC)** coursework, laboratory demonstrations, and viva examinations. It bridges formal automata definitions and step-by-step execution by allowing users to:

1. **Construct Nondeterministic Finite Automata (NFAs)** interactively (without $\varepsilon$-transitions) through a visual builder and live graph editor.
2. **Convert any valid NFA into an equivalent complete Deterministic Finite Automaton (DFA)** using the **Subset Construction (Powerset Construction) Algorithm**.
3. **Observe step-by-step conversion playback** at a calm, readable pace (2.4s per step), with synchronized graph animations and live mathematical set-union explanations displayed directly below the diagrams.
4. **Simulate arbitrary input strings simultaneously** on both the NFA and its generated DFA (2.0s per step) to verify language equivalence ($L(M_N) = L(M_D)$).

---

## Supported Features

- **Dynamic NFA Builder (`/builder`):**
  - Add and remove states and alphabet symbols with duplicate checking.
  - Strict rejection of reserved epsilon tokens ($\varepsilon$, $\lambda$) per project rules.
  - Designate one initial start state and multiple accepting (final) states.
  - Configure single or multi-destination transitions per `(state, symbol)` pair.
  - Real-time Cytoscape.js graph updates with directed start arrows (`->`) and double-circle accepting states.
  - JSON export/import of NFA definitions and CSV export of transition tables.
- **Backend Validation Engine (`automata/validator.py`):**
  - Validates JSON schemas, state/symbol existence, and transition integrity.
  - Enforces safe limits (maximum 25 states, 10 alphabet symbols, 200 transitions) to prevent exponential $2^n$ browser freezes.
- **Subset Construction Engine (`automata/nfa_to_dfa.py`):**
  - Queue-based Breadth-First Search (BFS) starting from initial subset $\{q_0\}$.
  - Canonical `frozenset` state tracking mapped to readable DFA labels ($A, B, C, \dots$).
  - Automatic introduction of an explicit absorbing **Dead / Trap State (`Dead (∅)`)** with distinct crimson styling whenever $\delta_D(S, a) = \emptyset$, guaranteeing DFA transition completeness.
  - Event-by-event execution history capturing transition unions $\delta_D(S, a) = \bigcup_{q \in S} \delta_N(q, a)$.
- **Step-by-Step Conversion Studio (`/conversion`):**
  - Side-by-side **Source NFA** and **Generated DFA** Cytoscape.js diagrams.
  - **Live Step Explanation** panel located directly below the diagrams for simultaneous visual and mathematical observation.
  - Fixed slow playback (2.4s/step) with Start, Prev, Play, Pause, Next, Reset, and Progress Slider controls.
  - Interactive **DFA State Inspector** on node click and complete DFA transition table with CSV download.
- **Dual String Simulator (`/simulator`):**
  - Run strings on **Both NFA & DFA**, **NFA Only**, or **DFA Only**, including empty string ($\varepsilon$) testing.
  - Side-by-side trace tables and synchronized graph highlighting at a comfortable pace (2.0s/step).
  - Clear **ACCEPTED / REJECTED** verdicts and NFA-DFA equivalence verification.
- **Preloaded Textbook Examples:**
  - Includes 8 classic TOC sample NFAs (e.g., *Ends with '01'*, *2nd Symbol from End is '1'*, *Contains Substring '010'*, *Starts with 'a' and Ends with 'b'*, and *Dead State Generator*).

---

## Technology Stack and Dependencies

| Component | Technology / Package | Version |
|---|---|---|
| **Language** | Python | `3.12` (compatible with `>= 3.11`) |
| **Backend Framework** | Flask | `>= 3.0.0, < 4.0.0` |
| **Testing Framework** | pytest | `>= 8.0.0` (verified on `9.0.3`) |
| **Core Automata Logic** | Python Standard Library (`collections`, `itertools`, `csv`, `io`, `typing`) | Built-in (zero third-party automata libraries) |
| **Frontend UI** | Bootstrap & Bootstrap Icons (CDN) | `5.3.3` & `1.11.3` |
| **Graph Visualization** | Cytoscape.js (CDN) | `3.30.2` |
| **Frontend Logic** | HTML5, CSS3, Vanilla JavaScript (ES6+) | Browser standard |

---

## Installation

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone https://github.com/ShauriyaDeveloper1/Automata-Theory-and-Computability.git
   cd Automata-Theory-and-Computability
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Linux / macOS:**
     ```bash
     source venv/bin/activate
     ```

4. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Run

- **Entry Point:** `app.py` (uses `create_app()` factory and runs Flask on `127.0.0.1:5000`).
- **Exact Command:**
  ```bash
  python app.py
  ```
- **Access the Application:**  
  Open a web browser and go to **[http://127.0.0.1:5000](http://127.0.0.1:5000)** (or navigate directly to `/builder`, `/conversion`, or `/simulator`).

---

## Example

### Sample Automaton Definition (NFA Accepting Binary Strings Ending in `01`)

```json
{
  "states": ["q0", "q1", "q2"],
  "alphabet": ["0", "1"],
  "initial_state": "q0",
  "accepting_states": ["q2"],
  "transitions": {
    "q0": {
      "0": ["q0", "q1"],
      "1": ["q0"]
    },
    "q1": {
      "1": ["q2"]
    },
    "q2": {}
  }
}
```

### Subset Construction Output (Generated Complete DFA)

| DFA State | NFA Subset | Input `0` | Input `1` | Role |
|---|---|---|---|---|
| `-> A` | `{q0}` | `B` (`{q0, q1}`) | `A` (`{q0}`) | Initial State |
| `B` | `{q0, q1}` | `B` (`{q0, q1}`) | `C` (`{q0, q2}`) | Intermediate State |
| `* C` | `{q0, q2}` | `B` (`{q0, q1}`) | `A` (`{q0}`) | Accepting State |

### Sample String Simulation Inputs and Outputs

| Input String | NFA Final Active States | DFA Final State | Expected Verdict |
|---|---|---|---|
| `"1001"` | `{q0, q2}` (contains `q2`) | `C` (`{q0, q2}`) | **ACCEPTED** |
| `"01"` | `{q0, q2}` (contains `q2`) | `C` (`{q0, q2}`) | **ACCEPTED** |
| `"010"` | `{q0, q1}` | `B` (`{q0, q1}`) | **REJECTED** |
| `""` ($\varepsilon$) | `{q0}` | `A` (`{q0}`) | **REJECTED** |

---

## Project Structure

```text
Automata-Theory-and-Computability/
├── app.py                      # Main Flask entry point, app factory, and error handlers
├── requirements.txt            # Dependency specification (Flask, pytest)
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
│
├── automata/                   # Core pure-Python TOC computation modules
│   ├── __init__.py             # Package exports
│   ├── models.py               # NFA & DFA dataclasses and Cytoscape graph formatters
│   ├── validator.py            # Input validation, bounds checks, and epsilon rejection
│   ├── nfa_to_dfa.py           # Subset Construction algorithm, dead state completion, event logger
│   └── simulator.py            # Independent NFA (set-based) & DFA (single-state) simulators
│
├── routes/                     # Flask REST API and page-rendering blueprints
│   ├── __init__.py             # Blueprint exports
│   ├── automata_routes.py      # HTML views, NFA validation, visualization, CSV export
│   ├── conversion_routes.py    # Subset construction & step event API endpoints
│   └── simulation_routes.py    # Dual string simulation API endpoint
│
├── examples/                   # Preloaded academic test automata
│   └── example_loader.py       # 8 curated textbook NFA examples
│
├── templates/                  # Jinja2 HTML views
│   ├── base.html               # Shared layout, navigation bar, Bootstrap/Cytoscape CDNs
│   ├── index.html              # Home dashboard and 1-click sample launcher
│   ├── builder.html            # Dynamic NFA Builder UI
│   ├── conversion.html         # Side-by-side Conversion Studio & step explanation card
│   └── simulator.html          # Dual String Simulator & trace table UI
│
├── static/                     # Frontend static files
│   ├── css/
│   │   ├── style.css           # Global theme, graph container, legend, and dead state styles
│   │   ├── builder.css         # State/symbol chips and transition matrix styling
│   │   └── simulation.css      # Playback controls, trace tables, and step cards
│   └── js/
│       ├── graph.js            # Reusable Cytoscape.js renderer, start arrow, and node highlights
│       ├── builder.js          # NFA Builder DOM controller and JSON/CSV handlers
│       ├── conversion.js       # Conversion playback controller (2.4s fixed pace) & table sync
│       └── simulator.js        # Dual string simulation controller (2.0s fixed pace)
│
└── tests/                      # Automated pytest verification suite
    ├── test_validator.py       # Validation & error-handling tests
    ├── test_conversion.py      # Subset construction, completeness & dead state tests
    ├── test_simulator.py       # String simulation & bounded exhaustive equivalence tests
    └── test_api.py             # Flask route & REST API integration tests
```

---

## Testing

### Test Execution Command
```bash
python -m pytest tests -v
```

### Test Data & Expected Behavior
All **46 automated tests** pass (`46 passed`), verifying mathematical accuracy and API stability:

- **`tests/test_validator.py` (14 tests):** Feeds valid NFAs, missing keys, duplicate states/symbols, invalid transitions, and forbidden $\varepsilon/\lambda$ tokens. *Expected:* Valid inputs pass; invalid configurations return descriptive validation errors.
- **`tests/test_conversion.py` (12 tests):** Tests deterministic-looking NFAs, multi-destination branching, accepting initial states, unreachable state exclusion, self-loops, explicit dead state ($\emptyset$) generation, Cytoscape start markers, and all 8 sample automata. *Expected:* Every generated DFA satisfies $\forall S \in Q_D, \forall a \in \Sigma, |\delta_D(S, a)| = 1$.
- **`tests/test_simulator.py` (6 tests):** Runs accepted/rejected strings, $\varepsilon$ (empty string), unrecognized symbols, dead-state traps, and **bounded exhaustive equivalence testing** across all binary/letter strings up to length 4 for every sample automaton. *Expected:* NFA and DFA always produce identical `accepted` boolean outcomes.
- **`tests/test_api.py` (14 tests):** Calls all page routes and JSON/CSV endpoints using Flask's test client. *Expected:* Correct HTTP `200`/`400`/`404` status codes and well-formed JSON/CSV responses.

---

## Known Limitations and Troubleshooting

### Known Limitations
1. **No $\varepsilon$-Transitions:** The simulator supports standard NFAs ($\delta_N: Q_N \times \Sigma \to \mathcal{P}(Q_N)$) only; $\varepsilon$-NFAs and $\varepsilon$-closures are outside the scope of this project.
2. **Un-minimized DFA Output:** Produces the direct DFA resulting from Subset Construction without Hopcroft/Moore state minimization.
3. **Configuration Size Caps:** Input automata are capped at 25 states, 10 alphabet symbols, and 200 transitions to prevent exponential powerset growth during live classroom demos.

### Troubleshooting
- **Diagrams or UI styles do not load:** Bootstrap `5.3.3`, Bootstrap Icons `1.11.3`, and Cytoscape.js `3.30.2` are loaded via CDN. Verify internet connectivity and refresh the page (`Ctrl + F5`).
- **Port 5000 already in use:** Start the server on an alternate port:
  ```powershell
  $env:PORT=5001; python app.py
  ```
- **Modified NFA not reflected in DFA view:** After editing an NFA in the Builder, click **Convert to DFA &rarr;** again to recompute and overwrite cached `localStorage` conversion data.

---

## Team Contributions and Acknowledgements

- **Author / Group:** `[Group ID]` — **ShauriyaDeveloper1** *(Theory of Computation Academic Project Team)*
- **Module Responsibilities:**
  - **Core Automata & Algorithm Design:** Pure-Python Subset Construction engine, validation module, dead state completion, and dual string simulator (`automata/`, `examples/`).
  - **Backend API & Test Suite:** Flask application factory, REST endpoints, CSV/JSON serialization, and 46 `pytest` unit/integration tests (`app.py`, `routes/`, `tests/`).
  - **Frontend & Graph Visualization:** Dynamic NFA Builder, Cytoscape.js start arrows and dead-state styling, Conversion Studio step-by-step playback, and Simulator UI (`templates/`, `static/`).
- **Acknowledgements:**
  - Guided by standard **Theory of Computation (TOC)** coursework and automata theory concepts from Hopcroft, Motwani, and Ullman (*Introduction to Automata Theory, Languages, and Computation*).
  - Built with open-source tools including Python, Flask, Bootstrap, Cytoscape.js, and pytest.
