"""Gallery of educational sample NFAs for academic demonstration."""

from __future__ import annotations
from typing import Dict, List, Any


SAMPLE_AUTOMATA: List[Dict[str, Any]] = [
    {
        "id": "binary_contains_zero",
        "title": "Contains At Least One '0'",
        "description": "Accepts all binary strings that have at least one '0' symbol anywhere in the string.",
        "test_strings": ["0", "10", "1101", "1", "111", ""],
        "data": {
            "states": ["q0", "q1"],
            "alphabet": ["0", "1"],
            "initial_state": "q0",
            "accepting_states": ["q1"],
            "transitions": {
                "q0": {
                    "0": ["q1"],
                    "1": ["q0"],
                },
                "q1": {
                    "0": ["q1"],
                    "1": ["q1"],
                },
            },
        },
    },
    {
        "id": "binary_ends_with_01",
        "title": "Ends with '01'",
        "description": "Accepts binary strings ending in '01'. Demonstrates non-determinism with multiple destinations on '0' from q0.",
        "test_strings": ["01", "1001", "11101", "0", "010", "10"],
        "data": {
            "states": ["q0", "q1", "q2"],
            "alphabet": ["0", "1"],
            "initial_state": "q0",
            "accepting_states": ["q2"],
            "transitions": {
                "q0": {
                    "0": ["q0", "q1"],
                    "1": ["q0"],
                },
                "q1": {
                    "1": ["q2"],
                },
                "q2": {},
            },
        },
    },
    {
        "id": "multiple_destinations",
        "title": "Branching NFA (Multiple Destinations)",
        "description": "Features multiple branching on symbols 'a' and 'b', showing how subset construction tracks combinations of states.",
        "test_strings": ["ab", "ba", "aab", "bba", "aaa"],
        "data": {
            "states": ["q0", "q1", "q2", "q3"],
            "alphabet": ["a", "b"],
            "initial_state": "q0",
            "accepting_states": ["q3"],
            "transitions": {
                "q0": {
                    "a": ["q0", "q1"],
                    "b": ["q0", "q2"],
                },
                "q1": {
                    "b": ["q3"],
                },
                "q2": {
                    "a": ["q3"],
                },
                "q3": {},
            },
        },
    },
    {
        "id": "self_loop_and_cycles",
        "title": "Self-Loops & Accepting Start State",
        "description": "NFA where the initial state is accepting (accepts empty string) with self-loops and cyclic transitions.",
        "test_strings": ["", "0", "00", "11", "010", "101"],
        "data": {
            "states": ["q0", "q1", "q2"],
            "alphabet": ["0", "1"],
            "initial_state": "q0",
            "accepting_states": ["q0", "q2"],
            "transitions": {
                "q0": {
                    "0": ["q0"],
                    "1": ["q1"],
                },
                "q1": {
                    "0": ["q1"],
                    "1": ["q2"],
                },
                "q2": {
                    "0": ["q0"],
                    "1": ["q2"],
                },
            },
        },
    },
    {
        "id": "dead_state_generation",
        "title": "Explicit Dead / Trap State Generator",
        "description": "Incomplete NFA transitions that force subset construction to generate an explicit empty-set dead state (∅).",
        "test_strings": ["a", "b", "aa", "ab", ""],
        "data": {
            "states": ["q0", "q1"],
            "alphabet": ["a", "b"],
            "initial_state": "q0",
            "accepting_states": ["q1"],
            "transitions": {
                "q0": {
                    "a": ["q1"],
                },
                "q1": {},
            },
        },
    },
    {
        "id": "second_from_end_is_1",
        "title": "Second Symbol from End is '1'",
        "description": "Classic textbook problem. Accepts binary strings where the 2nd symbol from the right is '1'. Demonstrates powerset state doubling.",
        "test_strings": ["10", "11", "010", "111", "100", "01", "0", "1"],
        "data": {
            "states": ["q0", "q1", "q2"],
            "alphabet": ["0", "1"],
            "initial_state": "q0",
            "accepting_states": ["q2"],
            "transitions": {
                "q0": {
                    "0": ["q0"],
                    "1": ["q0", "q1"],
                },
                "q1": {
                    "0": ["q2"],
                    "1": ["q2"],
                },
                "q2": {},
            },
        },
    },
    {
        "id": "contains_substring_010",
        "title": "Contains Substring '010'",
        "description": "Accepts binary strings containing pattern '010'. Shows non-deterministic pattern guessing without backtracking.",
        "test_strings": ["010", "10101", "00100", "0110", "111", "000"],
        "data": {
            "states": ["q0", "q1", "q2", "q3"],
            "alphabet": ["0", "1"],
            "initial_state": "q0",
            "accepting_states": ["q3"],
            "transitions": {
                "q0": {
                    "0": ["q0", "q1"],
                    "1": ["q0"],
                },
                "q1": {
                    "1": ["q2"],
                },
                "q2": {
                    "0": ["q3"],
                },
                "q3": {
                    "0": ["q3"],
                    "1": ["q3"],
                },
            },
        },
    },
    {
        "id": "starts_a_ends_b",
        "title": "Starts with 'a' and Ends with 'b'",
        "description": "Accepts strings over {a, b} that start with 'a' and end with 'b'. Generates an absorbing Dead State (∅) if input begins with 'b'.",
        "test_strings": ["ab", "aab", "abbb", "aba", "b", "ba", ""],
        "data": {
            "states": ["q0", "q1", "q2"],
            "alphabet": ["a", "b"],
            "initial_state": "q0",
            "accepting_states": ["q2"],
            "transitions": {
                "q0": {
                    "a": ["q1"],
                },
                "q1": {
                    "a": ["q1"],
                    "b": ["q1", "q2"],
                },
                "q2": {},
            },
        },
    },
]


def get_all_examples() -> List[Dict[str, Any]]:
    """Return list of sample automata with metadata."""
    return SAMPLE_AUTOMATA


def get_example_by_id(example_id: str) -> Dict[str, Any] | None:
    """Retrieve an example automaton by its ID."""
    for ex in SAMPLE_AUTOMATA:
        if ex["id"] == example_id:
            return ex
    return None

