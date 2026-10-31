"""Data models for NFA and DFA automata representations."""

from __future__ import annotations
from typing import Dict, List, Set, Optional, Any


class NFA:
    """Nondeterministic Finite Automaton (without epsilon transitions)."""

    def __init__(
        self,
        states: List[str],
        alphabet: List[str],
        initial_state: str,
        accepting_states: List[str],
        transitions: Optional[Dict[str, Dict[str, Set[str]]]] = None,
    ):
        # Preserve order while deduplicating
        self.states: List[str] = list(dict.fromkeys(states))
        self.alphabet: List[str] = list(dict.fromkeys(alphabet))
        self.initial_state: str = initial_state
        self.accepting_states: List[str] = [s for s in dict.fromkeys(accepting_states) if s in self.states]

        # transitions: state -> {symbol -> set(to_states)}
        self.transitions: Dict[str, Dict[str, Set[str]]] = {
            state: {sym: set() for sym in self.alphabet} for state in self.states
        }

        if transitions:
            for from_state, sym_map in transitions.items():
                if from_state in self.transitions:
                    for sym, to_states in sym_map.items():
                        if sym in self.alphabet:
                            for to_s in to_states:
                                if to_s in self.states:
                                    self.transitions[from_state][sym].add(to_s)

    def add_transition(self, from_state: str, symbol: str, to_state: str) -> bool:
        """Add a transition to the NFA."""
        if from_state in self.states and to_state in self.states and symbol in self.alphabet:
            self.transitions[from_state][symbol].add(to_state)
            return True
        return False

    def remove_transition(self, from_state: str, symbol: str, to_state: str) -> bool:
        """Remove a transition from the NFA."""
        if from_state in self.transitions and symbol in self.transitions[from_state]:
            self.transitions[from_state][symbol].discard(to_state)
            return True
        return False

    def get_transitions(self, from_state: str, symbol: str) -> Set[str]:
        """Return the set of destination states for (from_state, symbol)."""
        if from_state in self.transitions and symbol in self.transitions[from_state]:
            return set(self.transitions[from_state][symbol])
        return set()

    def to_dict(self) -> Dict[str, Any]:
        """Convert NFA to a JSON-serializable dictionary."""
        serialized_trans: Dict[str, Dict[str, List[str]]] = {}
        trans_list: List[Dict[str, str]] = []

        for u in self.states:
            u_dict: Dict[str, List[str]] = {}
            for s in self.alphabet:
                dests = sorted(list(self.get_transitions(u, s)))
                if dests:
                    u_dict[s] = dests
                for v in dests:
                    trans_list.append({"from_state": u, "symbol": s, "to_state": v})
            if u_dict:
                serialized_trans[u] = u_dict

        return {
            "states": list(self.states),
            "alphabet": list(self.alphabet),
            "initial_state": self.initial_state,
            "accepting_states": list(self.accepting_states),
            "transitions": serialized_trans,
            "transition_list": trans_list,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NFA:
        """Construct NFA from dictionary data."""
        states = [str(s).strip() for s in data.get("states", []) if str(s).strip()]
        alphabet = [str(a).strip() for a in data.get("alphabet", []) if str(a).strip()]
        initial_state = str(data.get("initial_state", "")).strip()
        accepting_states = [str(s).strip() for s in data.get("accepting_states", []) if str(s).strip()]

        raw_trans = data.get("transitions", {})
        parsed_trans: Dict[str, Dict[str, Set[str]]] = {
            s: {sym: set() for sym in alphabet} for s in states
        }

        # Handle dict format
        if isinstance(raw_trans, dict):
            for u, sym_map in raw_trans.items():
                u_str = str(u).strip()
                if u_str in parsed_trans and isinstance(sym_map, dict):
                    for sym, dests in sym_map.items():
                        sym_str = str(sym).strip()
                        if sym_str in alphabet:
                            if isinstance(dests, (list, set, tuple)):
                                for v in dests:
                                    v_str = str(v).strip()
                                    if v_str in states:
                                        parsed_trans[u_str][sym_str].add(v_str)
                            elif isinstance(dests, str) and dests.strip() in states:
                                parsed_trans[u_str][sym_str].add(dests.strip())

        # Also support transition_list format if provided
        if "transition_list" in data and isinstance(data["transition_list"], list):
            for t in data["transition_list"]:
                if isinstance(t, dict):
                    u = str(t.get("from_state", "")).strip()
                    sym = str(t.get("symbol", "")).strip()
                    v = str(t.get("to_state", "")).strip()
                    if u in parsed_trans and sym in alphabet and v in states:
                        parsed_trans[u][sym].add(v)

        return cls(
            states=states,
            alphabet=alphabet,
            initial_state=initial_state,
            accepting_states=accepting_states,
            transitions=parsed_trans,
        )

    def to_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """Return Cytoscape.js compatible graph elements with merged edge labels."""
        elements: List[Dict[str, Any]] = []

        # Nodes
        for state in self.states:
            is_init = (state == self.initial_state)
            is_acc = (state in self.accepting_states)

            # Check if this NFA state is a dead state (non-accepting, non-initial with 0 outgoing transitions or absorbing)
            is_dead = False
            if not is_acc and not is_init:
                total_outgoing = sum(len(self.get_transitions(state, sym)) for sym in self.alphabet)
                is_absorbing = (total_outgoing > 0 and all(self.get_transitions(state, sym).issubset({state}) for sym in self.alphabet))
                if total_outgoing == 0 or is_absorbing or state.lower() in ("dead", "trap", "∅"):
                    is_dead = True

            if is_dead:
                display_label = f"{state}\nDead (∅)"
            elif is_init:
                display_label = f"-> {state}"
            else:
                display_label = state

            elements.append({
                "data": {
                    "id": state,
                    "label": display_label,
                    "display_name": state,
                    "is_initial": is_init,
                    "is_accepting": is_acc,
                    "is_dead": is_dead,
                    "type": "state",
                },
                "classes": f"{'initial' if is_init else ''} {'accepting' if is_acc else ''} {'dead-state' if is_dead else ''}".strip(),
            })

        # Group transitions by (source, target)
        grouped_edges: Dict[tuple[str, str], List[str]] = {}
        for u in self.states:
            for sym in self.alphabet:
                for v in sorted(self.get_transitions(u, sym)):
                    pair = (u, v)
                    if pair not in grouped_edges:
                        grouped_edges[pair] = []
                    grouped_edges[pair].append(sym)

        edge_idx = 0
        for (u, v), syms in grouped_edges.items():
            sym_label = ", ".join(sorted(syms))
            elements.append({
                "data": {
                    "id": f"e_{u}_{v}_{edge_idx}",
                    "source": u,
                    "target": v,
                    "label": sym_label,
                    "symbols": sorted(syms),
                },
                "classes": "transition-edge",
            })
            edge_idx += 1

        # Dedicated Start Arrow indicator pointing to initial state
        if self.initial_state and self.initial_state in self.states:
            elements.append({
                "data": {
                    "id": f"__start_marker_{self.initial_state}",
                    "label": "Start",
                    "type": "start_marker",
                },
                "classes": "start-marker-node",
            })
            elements.append({
                "data": {
                    "id": f"__start_edge_{self.initial_state}",
                    "source": f"__start_marker_{self.initial_state}",
                    "target": self.initial_state,
                    "label": "",
                    "type": "start_arrow",
                },
                "classes": "start-arrow-edge",
            })

        return elements

    def get_transition_table(self) -> Dict[str, Any]:
        """Return a structured transition table suitable for rendering and CSV export."""
        headers = ["State"] + self.alphabet
        rows = []
        for state in self.states:
            row_prefix = ""
            if state == self.initial_state:
                row_prefix += "->"
            if state in self.accepting_states:
                row_prefix += "*"

            display_state = f"{row_prefix} {state}".strip()
            row = [display_state]
            for sym in self.alphabet:
                dests = sorted(list(self.get_transitions(state, sym)))
                if dests:
                    row.append("{" + ", ".join(dests) + "}")
                else:
                    row.append("∅")
            rows.append(row)

        return {
            "headers": headers,
            "rows": rows,
            "states": self.states,
            "alphabet": self.alphabet,
        }


class DFA:
    """Deterministic Finite Automaton resulting from subset construction."""

    def __init__(
        self,
        states: List[str],
        alphabet: List[str],
        initial_state: str,
        accepting_states: List[str],
        transitions: Dict[str, Dict[str, str]],
        state_subsets: Dict[str, List[str]],
        dead_state: Optional[str] = None,
    ):
        self.states: List[str] = list(states)
        self.alphabet: List[str] = list(alphabet)
        self.initial_state: str = initial_state
        self.accepting_states: List[str] = list(accepting_states)
        self.transitions: Dict[str, Dict[str, str]] = transitions
        self.state_subsets: Dict[str, List[str]] = state_subsets
        self.dead_state: Optional[str] = dead_state

    def get_transition(self, from_state: str, symbol: str) -> Optional[str]:
        """Return destination state for (from_state, symbol) in DFA."""
        if from_state in self.transitions and symbol in self.transitions[from_state]:
            return self.transitions[from_state][symbol]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize DFA to dictionary."""
        return {
            "states": self.states,
            "alphabet": self.alphabet,
            "initial_state": self.initial_state,
            "accepting_states": self.accepting_states,
            "transitions": self.transitions,
            "state_subsets": self.state_subsets,
            "dead_state": self.dead_state,
            "metrics": {
                "num_states": len(self.states),
                "num_accepting_states": len(self.accepting_states),
                "num_transitions": sum(len(m) for m in self.transitions.values()),
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DFA:
        """Construct DFA from dictionary."""
        return cls(
            states=data.get("states", []),
            alphabet=data.get("alphabet", []),
            initial_state=data.get("initial_state", ""),
            accepting_states=data.get("accepting_states", []),
            transitions=data.get("transitions", {}),
            state_subsets=data.get("state_subsets", {}),
            dead_state=data.get("dead_state"),
        )

    def to_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """Return Cytoscape.js compatible graph elements for DFA."""
        elements: List[Dict[str, Any]] = []

        for state in self.states:
            is_init = (state == self.initial_state)
            is_acc = (state in self.accepting_states)
            is_dead = (state == self.dead_state)
            subset = self.state_subsets.get(state, [])
            subset_str = "{" + ", ".join(subset) + "}" if subset else "∅"

            if is_dead:
                display_label = f"{state}\nDead (∅)"
            elif is_init:
                display_label = f"-> {state}\n{subset_str}"
            else:
                display_label = f"{state}\n{subset_str}"

            elements.append({
                "data": {
                    "id": state,
                    "label": display_label,
                    "display_name": state,
                    "subset": subset,
                    "subset_str": subset_str,
                    "is_initial": is_init,
                    "is_accepting": is_acc,
                    "is_dead": is_dead,
                    "type": "state",
                },
                "classes": f"{'initial' if is_init else ''} {'accepting' if is_acc else ''} {'dead-state' if is_dead else ''}".strip(),
            })

        # Group transitions by (source, target)
        grouped_edges: Dict[tuple[str, str], List[str]] = {}
        for u in self.states:
            for sym in self.alphabet:
                v = self.get_transition(u, sym)
                if v:
                    pair = (u, v)
                    if pair not in grouped_edges:
                        grouped_edges[pair] = []
                    grouped_edges[pair].append(sym)

        edge_idx = 0
        for (u, v), syms in grouped_edges.items():
            sym_label = ", ".join(sorted(syms))
            elements.append({
                "data": {
                    "id": f"dfa_e_{u}_{v}_{edge_idx}",
                    "source": u,
                    "target": v,
                    "label": sym_label,
                    "symbols": sorted(syms),
                },
                "classes": "transition-edge",
            })
            edge_idx += 1

        # Dedicated Start Arrow indicator pointing to DFA initial state
        if self.initial_state and self.initial_state in self.states:
            elements.append({
                "data": {
                    "id": f"__start_marker_{self.initial_state}",
                    "label": "Start",
                    "type": "start_marker",
                },
                "classes": "start-marker-node",
            })
            elements.append({
                "data": {
                    "id": f"__start_edge_{self.initial_state}",
                    "source": f"__start_marker_{self.initial_state}",
                    "target": self.initial_state,
                    "label": "",
                    "type": "start_arrow",
                },
                "classes": "start-arrow-edge",
            })

        return elements

    def get_transition_table(self) -> Dict[str, Any]:
        """Return structured DFA transition table."""
        headers = ["DFA State", "NFA Subset"] + self.alphabet
        rows = []
        for state in self.states:
            row_prefix = ""
            if state == self.initial_state:
                row_prefix += "->"
            if state in self.accepting_states:
                row_prefix += "*"

            display_state = f"{row_prefix} {state}".strip()
            subset = self.state_subsets.get(state, [])
            subset_str = "{" + ", ".join(subset) + "}" if subset else "∅"

            row = [display_state, subset_str]
            for sym in self.alphabet:
                dest = self.get_transition(state, sym)
                row.append(dest if dest is not None else "—")
            rows.append(row)

        return {
            "headers": headers,
            "rows": rows,
            "states": self.states,
            "alphabet": self.alphabet,
        }

