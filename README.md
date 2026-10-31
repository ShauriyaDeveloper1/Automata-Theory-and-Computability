# Interactive NFA-to-DFA Conversion & Simulation Studio
### Academic Course Project — Theory of Computation (TOC)

> **Course:** Theory of Computation (TOC) / Formal Languages and Automata Theory (FLAT)  
> **Project Type:** Academic Undergraduate Laboratory & Capstone Project  
> **Topic:** Nondeterministic Finite Automata (NFA) to Deterministic Finite Automata (DFA) Conversion via Subset Construction and Dual String Simulation  

---

## 1. Academic Project Overview

This project was developed as an academic coursework project for **Theory of Computation (TOC)**. In theoretical computer science, a core theorem proves the computational equivalence of Nondeterministic Finite Automata (NFAs) and Deterministic Finite Automata (DFAs): both machine models recognize exactly the same class of **Regular Languages** ($L(M_N) = L(M_D) \in \text{REG}$).

While an NFA provides design conciseness through nondeterministic guessing (multiple state transitions on a single input symbol or zero transitions), physical computing devices, hardware controllers, and compiler lexical analyzers require deterministic execution. 

This educational web application provides an interactive, visual platform designed specifically for TOC classroom demonstrations, laboratory assignments, and viva voce examinations:
1. **Dynamic Construction:** Build and edit arbitrary NFAs without epsilon transitions.
2. **Subset (Powerset) Construction:** Step-by-step mathematical conversion with live set unions.
3. **Transition Completeness:** Explicit handling and visualization of the absorbing dead/trap state ($\emptyset$) to ensure DFA mathematical validity.
4. **Synchronized Dual Simulation:** Test any input string simultaneously on both the NFA and DFA to verify language equivalence.

---

## 2. Core TOC Concepts Implemented

### 2.1 The Subset Construction Algorithm
An NFA is formally defined as a 5-tuple:
$$M_N = (Q_N, \Sigma, \delta_N, q_0, F_N)$$
Where:
- $Q_N$: Finite set of states
- $\Sigma$: Finite input alphabet
- $\delta_N: Q_N \times \Sigma \to \mathcal{P}(Q_N)$: Transition function mapping a state and symbol to a set of destination states
- $q_0 \in Q_N$: Initial start state
- $F_N \subseteq Q_N$: Set of accepting/final states

The algorithm constructs an equivalent complete DFA:
$$M_D = (Q_D, \Sigma, \delta_D, q_D^0, F_D)$$
Where:
1. **Initial DFA State:**
   $$q_D^0 = \{q_0\}$$
2. **Transition Function (Set Union):**
   For any reachable subset $S \subseteq Q_N$ and input symbol $a \in \Sigma$:
   $$\delta_D(S, a) = \bigcup_{q \in S} \delta_N(q, a)$$
3. **Accepting DFA States:**
   A DFA state $S$ is accepting if it contains at least one NFA accepting state:
   $$F_D = \{S \in Q_D \mid S \cap F_N \neq \emptyset\}$$

### 2.2 Complete DFA & Dead State ($\emptyset$) Handling
In an NFA, a state is legally permitted to have $0$ transitions on an alphabet symbol (missing transitions imply string rejection). However, by textbook definition, **every state in a DFA must have exactly one outgoing transition for every symbol in $\Sigma$**.

When $\delta_D(S, a) = \emptyset$, this project automatically introduces an explicit, absorbing **Dead State** ($\emptyset$), labeled `Dead (∅)`:
$$\forall a \in \Sigma, \quad \delta_D(\emptyset, a) = \emptyset$$
The dead state is styled with a distinct crimson badge/color in Cytoscape graphs and transition tables to make it immediately identifiable for students and viva examiners.

---

## 3. Key Features for Students & TOC Demonstrations

1. **Dynamic NFA Builder (`/builder`):**
   - Add/remove states with validation and duplicate prevention.
   - Configure custom alphabet symbols (strict rejection of reserved $\varepsilon, \lambda$ symbols).
   - Set start state and toggle multiple final states.
   - Interactive transition matrix supporting multiple destinations per symbol.
   - Live Cytoscape.js directed multigraph with textbook initial state marker arrow (`->`) and double-bordered accepting states.

2. **Step-by-Step Conversion Studio (`/conversion`):**
   - **Direct Layout:** The **Live Step Explanation** card is positioned directly **underneath** the side-by-side automata diagrams (Source NFA & Generated DFA) so you can watch active graph animations and read step reasoning simultaneously without scrolling.
   - **Comfortable Slow Playback:** Removed fast/confusing speed controls; playback runs at a comfortable, readable pace (2.4s per step) so non-technical students can clearly follow every state transition.
   - **Step Controls:** First Step, Previous Step, Play, Pause, Next Step, Reset, and a draggable progress slider.
   - **Synchronized Visual Highlighting:**
     - Gold glow on the active source state.
     - Glowing orange on the active transition edge.
     - Emerald green on the newly reached destination state.
     - Dynamic row and cell highlight in the complete DFA transition table.
   - **State Inspector:** Click any state node in the DFA graph to reveal its constituent NFA subset and transition breakdown.

3. **Dual String Simulator (`/simulator`):**
   - Test arbitrary input strings or the empty string ($\varepsilon$).
   - Synchronized execution traces showing active state sets, symbol consumption, and accepted/rejected verdict banners.
   - Demonstrates that NFA parallel state exploration and DFA single-path traversal yield identical acceptance decisions.
   - Runs at a calm, observable speed (2.0s per step).

4. **Curated Academic Examples Gallery:**
   Pre-loaded textbook problems from standard TOC curricula:
   - **Ends with '01':** Classic nondeterministic branching example.
   - **Contains At Least One '0':** Basic binary automaton.
   - **Branching NFA (Multiple Destinations):** Multiple branches on symbols `a` and `b`.
   - **Self-Loops & Accepting Start State:** Demonstrates empty string acceptance and cycles.
   - **Explicit Dead / Trap State Generator:** Missing transitions demonstrating $\emptyset$ induction.
   - **Second Symbol from End is '1':** Demonstrates exponential powerset expansion ($2^n$).
   - **Contains Substring '010':** Pattern matching without backtracking.
   - **Starts with 'a' and Ends with 'b':** Language constraint with dead state on invalid prefixes.

5. **Data Import & Export:**
   - Save and load NFA configurations as JSON files.
   - Download complete NFA and DFA transition tables as CSV spreadsheets.

---

## 4. Technology Stack

- **Backend:**
  - Python 3.11 / 3.12
  - Flask (REST API, application routing, Jinja2 template rendering)
  - Pure Python Standard Library for Automata Logic (`collections`, `itertools`, `csv`, `typing`) — *No external automata black-box libraries used*
  - Pytest (Automated unit and integration test suite)
- **Frontend:**
  - HTML5 & CSS3 with custom academic dashboard styling
  - Vanilla JavaScript (ES6+, Fetch API, localStorage state persistence)
  - Bootstrap 5.3.3 & Bootstrap Icons
  - Cytoscape.js 3.30.2 (Graph visualization engine)

---

## 5. Project Directory Structure

```
c:\Users\lenovo\Downloads\NFA\
├── app.py                      # Flask application entry point & factory
├── requirements.txt            # Python dependencies (Flask, pytest)
├── README.md                   # Academic project documentation
│
├── automata/                   # Pure Python TOC Automata Engine
│   ├── __init__.py             # Module exports
│   ├── models.py               # NFA & DFA classes and Cytoscape JSON adapters
│   ├── validator.py            # Input validation, bounds checks, epsilon rejection
│   ├── nfa_to_dfa.py           # Subset Construction algorithm & event logger
│   └── simulator.py            # Independent NFA & DFA string simulators
│
├── routes/                     # Flask HTTP Routes & API Blueprints
│   ├── __init__.py             # Blueprint registration
│   ├── automata_routes.py      # Page views, NFA validation, visualization, CSV export
│   ├── conversion_routes.py    # Subset construction & step playback endpoints
│   └── simulation_routes.py    # String simulation execution endpoint
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Base layout with navbar and flash toasts
│   ├── index.html              # Academic landing page & sample gallery
│   ├── builder.html            # Dynamic NFA Builder & live graph
│   ├── conversion.html         # Conversion Studio (Diagrams + Step card below)
│   └── simulator.html          # Dual String Simulator & trace tables
│
├── static/                     # Frontend Assets
│   ├── css/
│   │   ├── style.css           # Global theme, graph styles, dead state chips
│   │   ├── builder.css         # Transition matrix & chip list styling
│   │   └── simulation.css      # Playback controls & trace table styles
│   ├── js/
│   │   ├── graph.js            # Cytoscape graph renderer, start arrows & node styles
│   │   ├── builder.js          # NFA Builder interactive controller
│   │   ├── conversion.js       # Conversion Studio step-by-step playback controller
│   │   └── simulator.js        # String simulation & trace playback controller
│   └── images/                 # Static graphical assets
│
├── examples/                   # Curated TOC Sample Automata
│   └── example_loader.py       # Catalog of 8 pre-configured academic examples
│
└── tests/                      # Automated Test Suite (46 Tests)
    ├── test_validator.py       # Configuration & validation tests
    ├── test_conversion.py      # Subset construction, dead state & completeness tests
    ├── test_simulator.py       # String simulation & bounded equivalence tests
    └── test_api.py             # Flask REST API endpoint tests
```

---

## 6. Installation & Execution Guide

### Prerequisites
- Python 3.11 or higher installed on your machine.
- Web browser (Chrome, Edge, Firefox, or Safari) with an active internet connection to load CDN frontend libraries.

### Step 1: Navigate to the Project Directory
```powershell
cd c:\Users\lenovo\Downloads\NFA
```

### Step 2: Create and Activate a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(On Command Prompt use `venv\Scripts\activate.bat`; on Linux/macOS use `source venv/bin/activate`)*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Flask Web Application
```powershell
python app.py
```

The application will start on your local development server:
```
 * Running on http://127.0.0.1:5000
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 7. How to Use the Application

### 1. Building an NFA (`/builder`)
- **Add States:** Type state names (e.g., `q0`, `q1`, `q2`) and press **Add State** or press Enter.
- **Add Symbols:** Enter input symbols (e.g., `0`, `1` or `a`, `b`). Reserved epsilon symbols ($\varepsilon, \lambda$) are blocked.
- **Start & Accepting States:** Designate the initial state from the dropdown; mark accepting states with checkboxes.
- **Add Transitions:** Select Source State, Symbol, and Destination State, then click **$+$**. Multiple destinations for the same symbol are fully supported.
- **Export/Import:** Export the created automaton to JSON or load pre-saved configurations.
- Click **Convert to DFA &rarr;** to open the Conversion Studio.

### 2. Stepping Through Conversion (`/conversion`)
- Click **Play** to automatically run through the subset construction algorithm at a comfortable slow pace.
- Use **Next Step** and **Prev Step** for manual frame-by-frame review.
- Notice the **Live Step Explanation** box located directly **beneath** the graphs:
  - Explains the current DFA combo state.
  - Lists individual NFA branch transitions: $\delta_N(q, a)$.
  - Shows the union of destinations: $\delta_D(S, a) = \bigcup \delta_N(q, a)$.
  - Explains whether a new DFA state was discovered, an existing state was reached, or a dead state ($\emptyset$) was generated.
- Click any node in the Generated DFA graph to inspect its constituent NFA state set in the **DFA State Inspector**.
- Download the generated transition matrix via **Export DFA CSV**.

### 3. Testing String Acceptance (`/simulator`)
- Enter an input string into the text field (e.g., `0101`) or click **$\varepsilon$ (Empty)** for the empty string.
- Click **Run Both**, **Run NFA Only**, or **Run DFA Only**.
- Observe the **Accepted** or **Rejected** verdict banner and agreement verification.
- Click **Play** or step through with **Next Step** to watch active state highlights traverse both automata simultaneously while following the execution trace table.

---

## 8. REST API Reference

| HTTP Method | Route | Description |
|---|---|---|
| `GET` | `/` | Home page with project overview and example gallery |
| `GET` | `/builder` | Interactive Dynamic NFA Builder |
| `GET` | `/conversion` | Conversion Studio with dual graphs and step playback |
| `GET` | `/simulator` | Dual String Simulator and trace visualizer |
| `POST` | `/api/automata/validate` | Validates NFA configuration against TOC rules |
| `POST` | `/api/automata/visualize` | Generates Cytoscape graph elements and transition matrix |
| `POST` | `/api/conversion/convert` | Runs subset construction; returns DFA, metrics, and step events |
| `POST` | `/api/conversion/steps` | Returns step-by-step conversion events |
| `POST` | `/api/simulation/run` | Simulates an input string on NFA, DFA, or both |
| `GET` | `/api/examples` | Retrieves list of all preloaded academic sample automata |
| `GET` | `/api/examples/<id>` | Retrieves configuration of a specific sample automaton |
| `POST` | `/api/export/csv` | Generates and exports in-memory CSV transition table |

---

## 9. Automated Testing & Verification

The project includes a comprehensive test suite written in `pytest` to guarantee mathematical correctness and compliance with TOC theoretical definitions.

### Run the Test Suite:
```powershell
python -m pytest tests -v
```

### Test Coverage Summary (46 Tests Passing):
- **`tests/test_validator.py` (14 tests):** Validates rejection of duplicate states, empty alphabets, missing initial states, invalid transitions, epsilon symbols, and malformed inputs.
- **`tests/test_conversion.py` (12 tests):** Verifies subset construction correctness, multiple branching sets, accepting initial states, unreachable state removal, explicit dead state generation, start marker arrow Cytoscape nodes, and transition completeness for all sample automata.
- **`tests/test_simulator.py` (6 tests):** Validates acceptance/rejection paths, empty string ($\varepsilon$) handling, invalid symbol detection, dead state absorption, and **bounded exhaustive equivalence testing** across all sample automata up to length-4 strings.
- **`tests/test_api.py` (14 tests):** Verifies all Flask endpoints, HTTP status codes, JSON response formats, and CSV exports.

---

## 10. Academic Project Scope & Boundaries

To preserve strict alignment with the standard Theory of Computation (TOC) syllabus:
1. **No Epsilon Transitions ($\varepsilon$-NFA):** The project focuses strictly on standard NFAs without $\varepsilon$-transitions or $\varepsilon$-closures.
2. **No DFA Minimization:** The DFA produced is the direct mathematical output of subset construction (preserving all reachable subset states and explicit dead states).
3. **Responsive State Limits:** To prevent exponential powerset state explosions ($2^{25}$) from freezing the browser during college viva demonstrations, builder limits are set to 25 states and 10 alphabet symbols.
