"""Validation module for NFA configurations."""

from __future__ import annotations
from typing import Dict, Any, List, Set, Optional, Tuple

# Configurable limits for safe educational usage
MAX_STATES = 25
MAX_ALPHABET_SIZE = 10
MAX_TRANSITIONS = 200
MAX_STATE_NAME_LEN = 20
MAX_SYMBOL_LEN = 5

RESERVED_EPSILON_TOKENS = {"", "ε", "epsilon", "λ", "lambda"}


class AutomataValidationError(Exception):
    """Exception raised when an automaton configuration fails validation."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "field": self.field,
            "details": self.details,
        }


def validate_nfa(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate an NFA configuration.
    
    Returns:
        (is_valid, error_message, structured_error_dict)
    """
    if not isinstance(data, dict):
        err = AutomataValidationError("Configuration must be a JSON object.", field="root")
        return False, err.message, err.to_dict()

    # 1. Check required top-level keys
    required_keys = ["states", "alphabet", "initial_state", "accepting_states"]
    for key in required_keys:
        if key not in data:
            err = AutomataValidationError(f"Missing required field: '{key}'.", field=key)
            return False, err.message, err.to_dict()

    raw_states = data.get("states")
    raw_alphabet = data.get("alphabet")
    raw_initial = data.get("initial_state")
    raw_accepting = data.get("accepting_states")
    raw_transitions = data.get("transitions", {})
    raw_transition_list = data.get("transition_list")

    # 2. Validate states
    if not isinstance(raw_states, list):
        err = AutomataValidationError("Field 'states' must be a list of strings.", field="states")
        return False, err.message, err.to_dict()

    if len(raw_states) == 0:
        err = AutomataValidationError("At least one state must exist in the NFA.", field="states")
        return False, err.message, err.to_dict()

    if len(raw_states) > MAX_STATES:
        err = AutomataValidationError(
            f"State count ({len(raw_states)}) exceeds maximum allowed ({MAX_STATES}).",
            field="states",
            details={"max": MAX_STATES, "current": len(raw_states)},
        )
        return False, err.message, err.to_dict()

    seen_states: Set[str] = set()
    cleaned_states: List[str] = []
    for idx, s in enumerate(raw_states):
        if not isinstance(s, (str, int)):
            err = AutomataValidationError(f"State at index {idx} must be a string.", field="states")
            return False, err.message, err.to_dict()
        s_str = str(s).strip()
        if not s_str:
            err = AutomataValidationError("State names cannot be empty or whitespace only.", field="states")
            return False, err.message, err.to_dict()
        if len(s_str) > MAX_STATE_NAME_LEN:
            err = AutomataValidationError(
                f"State name '{s_str}' exceeds maximum length ({MAX_STATE_NAME_LEN}).",
                field="states",
            )
            return False, err.message, err.to_dict()
        if s_str in seen_states:
            err = AutomataValidationError(
                f"Duplicate state detected: '{s_str}'. State names must be unique.",
                field="states",
                details={"duplicate": s_str},
            )
            return False, err.message, err.to_dict()
        seen_states.add(s_str)
        cleaned_states.append(s_str)

    # 3. Validate alphabet
    if not isinstance(raw_alphabet, list):
        err = AutomataValidationError("Field 'alphabet' must be a list of symbols.", field="alphabet")
        return False, err.message, err.to_dict()

    if len(raw_alphabet) == 0:
        err = AutomataValidationError("Alphabet cannot be empty. At least one symbol is required.", field="alphabet")
        return False, err.message, err.to_dict()

    if len(raw_alphabet) > MAX_ALPHABET_SIZE:
        err = AutomataValidationError(
            f"Alphabet size ({len(raw_alphabet)}) exceeds maximum allowed ({MAX_ALPHABET_SIZE}).",
            field="alphabet",
            details={"max": MAX_ALPHABET_SIZE, "current": len(raw_alphabet)},
        )
        return False, err.message, err.to_dict()

    seen_symbols: Set[str] = set()
    cleaned_alphabet: List[str] = []
    for idx, a in enumerate(raw_alphabet):
        if not isinstance(a, (str, int)):
            err = AutomataValidationError(f"Alphabet symbol at index {idx} must be a string.", field="alphabet")
            return False, err.message, err.to_dict()
        a_str = str(a).strip()
        if not a_str:
            err = AutomataValidationError("Alphabet symbols cannot be empty.", field="alphabet")
            return False, err.message, err.to_dict()

        if a_str.lower() in RESERVED_EPSILON_TOKENS:
            err = AutomataValidationError(
                f"Epsilon transitions and symbols ('{a_str}') are strictly not allowed. Ordinary NFAs only.",
                field="alphabet",
                details={"rejected_symbol": a_str},
            )
            return False, err.message, err.to_dict()

        if len(a_str) > MAX_SYMBOL_LEN:
            err = AutomataValidationError(
                f"Alphabet symbol '{a_str}' exceeds maximum length ({MAX_SYMBOL_LEN}).",
                field="alphabet",
            )
            return False, err.message, err.to_dict()

        if a_str in seen_symbols:
            err = AutomataValidationError(
                f"Duplicate alphabet symbol: '{a_str}'. Symbols must be unique.",
                field="alphabet",
                details={"duplicate": a_str},
            )
            return False, err.message, err.to_dict()
        seen_symbols.add(a_str)
        cleaned_alphabet.append(a_str)

    # 4. Validate initial state
    if raw_initial is None or not str(raw_initial).strip():
        err = AutomataValidationError("Initial state must be specified.", field="initial_state")
        return False, err.message, err.to_dict()

    initial_str = str(raw_initial).strip()
    if initial_str not in seen_states:
        err = AutomataValidationError(
            f"Initial state '{initial_str}' does not exist in the defined states: {list(seen_states)}.",
            field="initial_state",
            details={"initial_state": initial_str, "defined_states": list(seen_states)},
        )
        return False, err.message, err.to_dict()

    # 5. Validate accepting states
    if not isinstance(raw_accepting, list):
        err = AutomataValidationError("Field 'accepting_states' must be a list.", field="accepting_states")
        return False, err.message, err.to_dict()

    seen_accepting: Set[str] = set()
    for acc in raw_accepting:
        acc_str = str(acc).strip()
        if acc_str not in seen_states:
            err = AutomataValidationError(
                f"Accepting state '{acc_str}' does not exist in the defined states.",
                field="accepting_states",
                details={"invalid_state": acc_str},
            )
            return False, err.message, err.to_dict()
        seen_accepting.add(acc_str)

    # 6. Validate transitions
    total_transitions = 0

    # Transitions can be specified via transition_list or transitions dict
    trans_entries: List[Tuple[str, str, str]] = []

    if raw_transition_list is not None:
        if not isinstance(raw_transition_list, list):
            err = AutomataValidationError("Field 'transition_list' must be a list of objects.", field="transitions")
            return False, err.message, err.to_dict()
        for t in raw_transition_list:
            if not isinstance(t, dict):
                err = AutomataValidationError("Each transition item must be an object with from_state, symbol, to_state.", field="transitions")
                return False, err.message, err.to_dict()
            u = str(t.get("from_state", "")).strip()
            sym = str(t.get("symbol", "")).strip()
            v = str(t.get("to_state", "")).strip()
            trans_entries.append((u, sym, v))
    elif isinstance(raw_transitions, dict):
        for u, sym_map in raw_transitions.items():
            u_str = str(u).strip()
            if not isinstance(sym_map, dict):
                err = AutomataValidationError(f"Transitions for state '{u_str}' must be a mapping of symbol to destinations.", field="transitions")
                return False, err.message, err.to_dict()
            for sym, dests in sym_map.items():
                sym_str = str(sym).strip()
                if isinstance(dests, list):
                    for v in dests:
                        trans_entries.append((u_str, sym_str, str(v).strip()))
                elif isinstance(dests, str):
                    trans_entries.append((u_str, sym_str, dests.strip()))
                elif dests is not None:
                    err = AutomataValidationError(f"Invalid transition destination '{dests}' from state '{u_str}'.", field="transitions")
                    return False, err.message, err.to_dict()
    else:
        err = AutomataValidationError("Field 'transitions' must be a dictionary or list.", field="transitions")
        return False, err.message, err.to_dict()

    if len(trans_entries) > MAX_TRANSITIONS:
        err = AutomataValidationError(
            f"Total transitions ({len(trans_entries)}) exceeds maximum allowed ({MAX_TRANSITIONS}).",
            field="transitions",
            details={"max": MAX_TRANSITIONS, "current": len(trans_entries)},
        )
        return False, err.message, err.to_dict()

    for u, sym, v in trans_entries:
        if sym.lower() in RESERVED_EPSILON_TOKENS:
            err = AutomataValidationError(
                f"Epsilon transition detected ({u} --{sym}--> {v}). Epsilon transitions are strictly forbidden.",
                field="transitions",
                details={"transition": {"from": u, "symbol": sym, "to": v}},
            )
            return False, err.message, err.to_dict()

        if u not in seen_states:
            err = AutomataValidationError(
                f"Transition source '{u}' is not a defined state.",
                field="transitions",
                details={"invalid_source": u},
            )
            return False, err.message, err.to_dict()

        if sym not in seen_symbols:
            err = AutomataValidationError(
                f"Transition symbol '{sym}' is not in the defined alphabet {list(seen_symbols)}.",
                field="transitions",
                details={"invalid_symbol": sym, "alphabet": list(seen_symbols)},
            )
            return False, err.message, err.to_dict()

        if v not in seen_states:
            err = AutomataValidationError(
                f"Transition destination '{v}' is not a defined state.",
                field="transitions",
                details={"invalid_target": v},
            )
            return False, err.message, err.to_dict()

    return True, None, None

