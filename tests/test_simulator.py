"""Tests for the simulation module, including bounded exhaustive equivalence checks."""

import pytest
import itertools
from automata.models import NFA
from automata.nfa_to_dfa import convert_nfa_to_dfa
from automata.simulator import simulate_nfa, simulate_dfa, simulate_both
from examples.example_loader import SAMPLE_AUTOMATA


def test_nfa_and_dfa_accepted_and_rejected_string():
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={
            "q0": {"0": {"q1"}, "1": {"q0"}},
            "q1": {"0": {"q1"}, "1": {"q1"}},
        },
    )
    dfa = convert_nfa_to_dfa(nfa)["dfa"]

    # String with 0 should be accepted
    res_nfa = simulate_nfa(nfa, "1101")
    res_dfa = simulate_dfa(dfa, "1101")
    assert res_nfa["accepted"] is True
    assert res_dfa["accepted"] is True

    # String with only 1s should be rejected
    res_nfa = simulate_nfa(nfa, "111")
    res_dfa = simulate_dfa(dfa, "111")
    assert res_nfa["accepted"] is False
    assert res_dfa["accepted"] is False


def test_empty_string_simulation():
    # NFA with non-accepting start state
    nfa1 = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={},
    )
    dfa1 = convert_nfa_to_dfa(nfa1)["dfa"]
    assert simulate_nfa(nfa1, "")["accepted"] is False
    assert simulate_dfa(dfa1, "")["accepted"] is False

    # NFA with accepting start state
    nfa2 = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q0"],
        transitions={},
    )
    dfa2 = convert_nfa_to_dfa(nfa2)["dfa"]
    assert simulate_nfa(nfa2, "")["accepted"] is True
    assert simulate_dfa(dfa2, "")["accepted"] is True


def test_invalid_symbol_rejection():
    nfa = NFA(
        states=["q0"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q0"],
        transitions={},
    )
    dfa = convert_nfa_to_dfa(nfa)["dfa"]

    res_nfa = simulate_nfa(nfa, "012")
    assert res_nfa["success"] is False
    assert "not present in NFA alphabet" in res_nfa["error"]

    res_dfa = simulate_dfa(dfa, "012")
    assert res_dfa["success"] is False
    assert "not present in DFA alphabet" in res_dfa["error"]


def test_empty_active_states_recovery():
    """When an NFA enters empty active states set, it stays empty."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={"q0": {"a": {"q1"}}},
    )
    res = simulate_nfa(nfa, "ba")
    assert res["accepted"] is False
    assert res["final_states"] == []


def test_dead_state_simulation():
    """In a DFA, entering a dead state stays in the dead state."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={"q0": {"a": {"q1"}}},
    )
    conv = convert_nfa_to_dfa(nfa)
    dfa = conv["dfa"]
    dead_label = conv["metrics"]["dead_state_label"]

    res = simulate_dfa(dfa, "bba")
    assert res["accepted"] is False
    assert res["final_state"] == dead_label
    assert any(step["is_dead_state"] for step in res["trace"])


def test_bounded_exhaustive_equivalence():
    """
    For all sample automata, test all strings up to length 4.
    Verify that independently executed NFA and DFA simulations always produce identical acceptance results.
    """
    for sample in SAMPLE_AUTOMATA:
        nfa = NFA.from_dict(sample["data"])
        conv = convert_nfa_to_dfa(nfa)
        dfa = conv["dfa"]

        alphabet = nfa.alphabet
        # Generate strings of length 0 to 4
        test_strings = [""]
        for length in range(1, 4):
            for p in itertools.product(alphabet, repeat=length):
                test_strings.append("".join(p))

        for test_str in test_strings:
            both_res = simulate_both(nfa, dfa, test_str)
            assert both_res["agrees"] is True, (
                f"Discrepancy for automaton '{sample['id']}' on input '{test_str}': "
                f"NFA={both_res['nfa_result']['accepted']}, DFA={both_res['dfa_result']['accepted']}"
            )

