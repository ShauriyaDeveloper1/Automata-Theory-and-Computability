"""Tests for the Subset Construction conversion algorithm."""

import pytest
from automata.models import NFA, DFA
from automata.nfa_to_dfa import convert_nfa_to_dfa
from examples.example_loader import get_example_by_id


def test_conversion_deterministic_looking_nfa():
    """An already deterministic NFA should convert directly to an equivalent DFA."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={
            "q0": {"0": {"q1"}, "1": {"q0"}},
            "q1": {"0": {"q1"}, "1": {"q0"}},
        },
    )
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    assert len(dfa.states) == 2
    assert dfa.initial_state == "A"
    assert "B" in dfa.accepting_states
    # Check completeness
    for s in dfa.states:
        for a in dfa.alphabet:
            assert dfa.get_transition(s, a) is not None


def test_conversion_multiple_destinations():
    """NFA with multiple destinations on symbol '0' from q0."""
    nfa = NFA(
        states=["q0", "q1", "q2"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q2"],
        transitions={
            "q0": {"0": {"q0", "q1"}, "1": {"q0"}},
            "q1": {"1": {"q2"}},
            "q2": {},
        },
    )
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    # Verify reachable states contain subset with {q0, q1}
    subsets = list(dfa.state_subsets.values())
    assert ["q0", "q1"] in subsets
    # Check completeness
    for s in dfa.states:
        for a in dfa.alphabet:
            assert dfa.get_transition(s, a) is not None


def test_conversion_accepting_initial_state():
    """NFA where initial state is accepting."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["a"],
        initial_state="q0",
        accepting_states=["q0"],
        transitions={
            "q0": {"a": {"q1"}},
            "q1": {"a": {"q0"}},
        },
    )
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    assert dfa.initial_state in dfa.accepting_states


def test_conversion_no_accepting_states():
    """NFA with no accepting states produces DFA with no accepting states."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=[],
        transitions={"q0": {"0": {"q1"}}, "q1": {}},
    )
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    assert len(dfa.accepting_states) == 0


def test_conversion_unreachable_states_omitted():
    """Unreachable NFA states must not create arbitrary unreachable DFA subsets."""
    nfa = NFA(
        states=["q0", "q1", "unreachable_q2"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={
            "q0": {"0": {"q1"}, "1": {"q0"}},
            "q1": {"0": {"q1"}, "1": {"q0"}},
            "unreachable_q2": {"0": {"unreachable_q2"}},
        },
    )
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    for s, subset in dfa.state_subsets.items():
        assert "unreachable_q2" not in subset


def test_conversion_dead_state_generation():
    """NFA with missing transitions generates dead state in DFA."""
    ex = get_example_by_id("dead_state_generation")
    nfa = NFA.from_dict(ex["data"])
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    assert result["metrics"]["has_dead_state"] is True
    dead_label = result["metrics"]["dead_state_label"]
    assert dfa.state_subsets[dead_label] == []
    # Dead state must loop to itself on every alphabet symbol
    for a in dfa.alphabet:
        assert dfa.get_transition(dead_label, a) == dead_label


def test_conversion_self_loops():
    """NFA with self loops converts correctly."""
    ex = get_example_by_id("self_loop_and_cycles")
    nfa = NFA.from_dict(ex["data"])
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    assert len(dfa.states) >= 3
    # Complete DFA verification
    for s in dfa.states:
        for a in dfa.alphabet:
            assert dfa.get_transition(s, a) is not None


def test_conversion_contains_zero_example():
    ex = get_example_by_id("binary_contains_zero")
    nfa = NFA.from_dict(ex["data"])
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    assert len(dfa.accepting_states) > 0


def test_conversion_ends_with_01_example():
    ex = get_example_by_id("binary_ends_with_01")
    nfa = NFA.from_dict(ex["data"])
    result = convert_nfa_to_dfa(nfa)
    dfa = result["dfa"]
    assert len(dfa.accepting_states) > 0


def test_conversion_events_completeness():
    """Conversion events must contain all required pedagogical details."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={"q0": {"0": {"q0", "q1"}}, "q1": {}},
    )
    result = convert_nfa_to_dfa(nfa)
    events = result["events"]
    assert len(events) > 1

    # Check step 0
    assert events[0]["step_number"] == 0
    assert events[0]["current_dfa_state"] == "A"

    # Check subsequent transition events
    for evt in events[1:]:
        assert "step_number" in evt
        assert "current_dfa_state" in evt
        assert "current_nfa_subset" in evt
        assert "symbol" in evt
        assert "transitions_considered" in evt
        assert "resulting_nfa_subset" in evt
        assert "destination_dfa_state" in evt
        assert "is_new_state" in evt
        assert "is_accepting" in evt
        assert "is_dead_state" in evt
        assert "explanation" in evt


def test_start_marker_cytoscape_elements():
    """Both NFA and DFA must generate dedicated start marker node and incoming arrow edge."""
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        accepting_states=["q1"],
        transitions={"q0": {"0": {"q1"}}, "q1": {"0": {"q1"}}},
    )
    nfa_elements = nfa.to_cytoscape_elements()
    
    # Assert NFA start marker exists
    nfa_marker = next((el for el in nfa_elements if el["data"].get("id") == "__start_marker_q0"), None)
    nfa_edge = next((el for el in nfa_elements if el["data"].get("id") == "__start_edge_q0"), None)
    assert nfa_marker is not None
    assert nfa_marker["classes"] == "start-marker-node"
    assert nfa_edge is not None
    assert nfa_edge["data"]["source"] == "__start_marker_q0"
    assert nfa_edge["data"]["target"] == "q0"
    assert nfa_edge["classes"] == "start-arrow-edge"

    # Assert DFA start marker exists
    conv = convert_nfa_to_dfa(nfa)
    dfa = conv["dfa"]
    dfa_elements = dfa.to_cytoscape_elements()
    dfa_marker = next((el for el in dfa_elements if el["data"].get("id") == "__start_marker_A"), None)
    dfa_edge = next((el for el in dfa_elements if el["data"].get("id") == "__start_edge_A"), None)
    assert dfa_marker is not None
    assert dfa_marker["classes"] == "start-marker-node"
    assert dfa_edge is not None
    assert dfa_edge["data"]["source"] == "__start_marker_A"
    assert dfa_edge["data"]["target"] == "A"
    assert dfa_edge["classes"] == "start-arrow-edge"


def test_all_sample_automata_dfa_completeness():
    """Every DFA generated for every sample automaton must have 100% complete transitions (no state with missing symbols)."""
    from examples.example_loader import get_all_examples
    for ex in get_all_examples():
        nfa = NFA.from_dict(ex["data"])
        conv = convert_nfa_to_dfa(nfa)
        dfa = conv["dfa"]
        for s in dfa.states:
            for sym in dfa.alphabet:
                dest = dfa.get_transition(s, sym)
                assert dest is not None, f"DFA state {s} missing transition on '{sym}' in example {ex['id']}"
                assert dest in dfa.states

