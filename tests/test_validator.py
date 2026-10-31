"""Tests for NFA validation module."""

import pytest
from automata.validator import validate_nfa, AutomataValidationError


def test_valid_nfa():
    data = {
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": ["q1"],
        "transitions": {
            "q0": {"0": ["q1"], "1": ["q0"]},
            "q1": {"0": ["q1"], "1": ["q1"]},
        },
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is True
    assert msg is None
    assert err is None


def test_missing_required_fields():
    data = {"states": ["q0"]}
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "alphabet" in msg.lower() or "missing" in msg.lower()


def test_empty_states():
    data = {
        "states": [],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": [],
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "at least one state" in msg.lower()


def test_duplicate_states():
    data = {
        "states": ["q0", "q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": ["q1"],
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "duplicate state" in msg.lower()


def test_empty_alphabet():
    data = {
        "states": ["q0"],
        "alphabet": [],
        "initial_state": "q0",
        "accepting_states": ["q0"],
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "alphabet cannot be empty" in msg.lower()


def test_duplicate_alphabet():
    data = {
        "states": ["q0"],
        "alphabet": ["0", "0"],
        "initial_state": "q0",
        "accepting_states": ["q0"],
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "duplicate alphabet" in msg.lower()


def test_epsilon_in_alphabet():
    for eps in ["ε", "epsilon", "λ", "lambda"]:
        data = {
            "states": ["q0"],
            "alphabet": ["0", eps],
            "initial_state": "q0",
            "accepting_states": ["q0"],
        }
        is_valid, msg, err = validate_nfa(data)
        assert is_valid is False
        assert "epsilon" in msg.lower()


def test_missing_or_invalid_initial_state():
    data = {
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q99",
        "accepting_states": ["q1"],
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "initial state" in msg.lower()


def test_invalid_accepting_state():
    data = {
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": ["q99"],
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "accepting state" in msg.lower()


def test_invalid_transition_source():
    data = {
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": ["q1"],
        "transitions": {
            "q99": {"0": ["q1"]},
        },
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "not a defined state" in msg.lower()


def test_invalid_transition_destination():
    data = {
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": ["q1"],
        "transitions": {
            "q0": {"0": ["q99"]},
        },
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "not a defined state" in msg.lower()


def test_invalid_transition_symbol():
    data = {
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": ["q1"],
        "transitions": {
            "q0": {"x": ["q1"]},
        },
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "not in the defined alphabet" in msg.lower()


def test_epsilon_transition_rejected():
    data = {
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "initial_state": "q0",
        "accepting_states": ["q1"],
        "transition_list": [
            {"from_state": "q0", "symbol": "ε", "to_state": "q1"}
        ],
    }
    is_valid, msg, err = validate_nfa(data)
    assert is_valid is False
    assert "epsilon" in msg.lower()


def test_malformed_json_types():
    assert validate_nfa("invalid")[0] is False
    assert validate_nfa(123)[0] is False
    assert validate_nfa([])[0] is False

