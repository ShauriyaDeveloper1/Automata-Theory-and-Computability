"""Simulation module for executing input strings on NFA and DFA."""

from __future__ import annotations
from typing import Dict, List, Set, Optional, Any
from .models import NFA, DFA


def simulate_nfa(nfa: NFA, input_string: str) -> Dict[str, Any]:
    """
    Simulate an input string on an NFA independently.
    
    Returns an execution trace and acceptance result.
    """
    clean_input = input_string.strip()
    symbols = list(clean_input)

    # Validate that all symbols belong to the alphabet
    invalid_symbols = [s for s in symbols if s not in nfa.alphabet]
    if invalid_symbols:
        return {
            "success": False,
            "error": f"Input string contains symbols {invalid_symbols} not present in NFA alphabet {nfa.alphabet}.",
            "input_string": input_string,
            "accepted": False,
            "trace": [],
        }

    trace: List[Dict[str, Any]] = []

    # Step 0: Start at {initial_state}
    active_states: Set[str] = {nfa.initial_state}
    is_init_acc = bool(active_states.intersection(set(nfa.accepting_states)))

    trace.append({
        "step": 0,
        "symbol_read": "— (Start)",
        "active_states": sorted(list(active_states)),
        "active_states_str": "{" + ", ".join(sorted(list(active_states))) + "}",
        "transitions_used": [],
        "explanation": f"Initial state: Active state set is {{{nfa.initial_state}}}.",
        "is_accepting": is_init_acc,
    })

    # Process each symbol
    for idx, sym in enumerate(symbols):
        step_num = idx + 1
        next_active_states: Set[str] = set()
        transitions_used: List[Dict[str, Any]] = []

        for q in sorted(active_states):
            dests = nfa.get_transitions(q, sym)
            for d in sorted(dests):
                transitions_used.append({"from": q, "symbol": sym, "to": d})
            next_active_states.update(dests)

        prev_states_str = "{" + ", ".join(sorted(list(active_states))) + "}" if active_states else "∅"
        new_states_str = "{" + ", ".join(sorted(list(next_active_states))) + "}" if next_active_states else "∅"

        if transitions_used:
            t_str = ", ".join(f"δ({t['from']}, '{sym}') -> {t['to']}" for t in transitions_used)
            explanation = f"Read '{sym}': From active states {prev_states_str}, followed {t_str}. New active states: {new_states_str}."
        else:
            explanation = f"Read '{sym}': From active states {prev_states_str}, no transitions exist for symbol '{sym}'. Active states become ∅."

        active_states = next_active_states
        is_step_acc = bool(active_states.intersection(set(nfa.accepting_states)))

        trace.append({
            "step": step_num,
            "symbol_read": sym,
            "active_states": sorted(list(active_states)),
            "active_states_str": new_states_str,
            "transitions_used": transitions_used,
            "explanation": explanation,
            "is_accepting": is_step_acc,
        })

    # Final acceptance condition: active_states contains at least one accepting state
    is_accepted = bool(active_states.intersection(set(nfa.accepting_states)))
    final_active_str = "{" + ", ".join(sorted(list(active_states))) + "}" if active_states else "∅"

    if is_accepted:
        accepting_matches = sorted(list(active_states.intersection(set(nfa.accepting_states))))
        summary = (
            f"ACCEPTED: Execution ended in active states {final_active_str}, "
            f"which contains accepting state(s) {{{', '.join(accepting_matches)}}}."
        )
    else:
        summary = (
            f"REJECTED: Execution ended in active states {final_active_str}, "
            f"which does not contain any accepting state (Accepting states: {{{', '.join(nfa.accepting_states)}}})."
        )

    return {
        "success": True,
        "automaton_type": "NFA",
        "input_string": clean_input,
        "display_input": clean_input if clean_input else "ε (empty string)",
        "accepted": is_accepted,
        "final_states": sorted(list(active_states)),
        "final_states_str": final_active_str,
        "trace": trace,
        "summary": summary,
    }


def simulate_dfa(dfa: DFA, input_string: str) -> Dict[str, Any]:
    """
    Simulate an input string on a DFA independently.
    
    Returns an execution trace and acceptance result.
    """
    clean_input = input_string.strip()
    symbols = list(clean_input)

    # Validate symbols
    invalid_symbols = [s for s in symbols if s not in dfa.alphabet]
    if invalid_symbols:
        return {
            "success": False,
            "error": f"Input string contains symbols {invalid_symbols} not present in DFA alphabet {dfa.alphabet}.",
            "input_string": input_string,
            "accepted": False,
            "trace": [],
        }

    trace: List[Dict[str, Any]] = []

    # Step 0: Start at DFA initial state
    curr_state = dfa.initial_state
    curr_subset = dfa.state_subsets.get(curr_state, [])
    curr_subset_str = "{" + ", ".join(curr_subset) + "}" if curr_subset else "∅"
    is_init_acc = (curr_state in dfa.accepting_states)

    trace.append({
        "step": 0,
        "symbol_read": "— (Start)",
        "current_state": curr_state,
        "subset": curr_subset,
        "subset_str": curr_subset_str,
        "next_state": None,
        "is_dead_state": (curr_state == dfa.dead_state),
        "explanation": f"Initial state: Start at DFA state {curr_state} = {curr_subset_str}.",
        "is_accepting": is_init_acc,
    })

    # Process each symbol
    for idx, sym in enumerate(symbols):
        step_num = idx + 1
        prev_state = curr_state
        prev_subset = dfa.state_subsets.get(prev_state, [])
        prev_subset_str = "{" + ", ".join(prev_subset) + "}" if prev_subset else "∅"

        dest_state = dfa.get_transition(prev_state, sym)

        if dest_state is None:
            # Complete DFA should always have a transition, but handle defensively
            dest_state = dfa.dead_state or "∅"

        curr_state = dest_state
        curr_subset = dfa.state_subsets.get(curr_state, [])
        curr_subset_str = "{" + ", ".join(curr_subset) + "}" if curr_subset else "∅"
        is_step_acc = (curr_state in dfa.accepting_states)
        is_dead = (curr_state == dfa.dead_state)

        explanation = (
            f"Read '{sym}': From state {prev_state} ({prev_subset_str}), "
            f"follow δ({prev_state}, '{sym}') -> {curr_state} ({curr_subset_str})."
        )
        if is_dead:
            explanation += " (Entered Dead/Trap state)."

        trace.append({
            "step": step_num,
            "symbol_read": sym,
            "current_state": curr_state,
            "subset": curr_subset,
            "subset_str": curr_subset_str,
            "is_dead_state": is_dead,
            "explanation": explanation,
            "is_accepting": is_step_acc,
        })

    # Final acceptance
    is_accepted = (curr_state in dfa.accepting_states)
    final_subset = dfa.state_subsets.get(curr_state, [])
    final_subset_str = "{" + ", ".join(final_subset) + "}" if final_subset else "∅"

    if is_accepted:
        summary = (
            f"ACCEPTED: Execution finished at DFA state {curr_state} = {final_subset_str}, "
            f"which is an accepting state."
        )
    else:
        summary = (
            f"REJECTED: Execution finished at DFA state {curr_state} = {final_subset_str}, "
            f"which is NOT an accepting state."
        )

    return {
        "success": True,
        "automaton_type": "DFA",
        "input_string": clean_input,
        "display_input": clean_input if clean_input else "ε (empty string)",
        "accepted": is_accepted,
        "final_state": curr_state,
        "final_subset": final_subset,
        "final_subset_str": final_subset_str,
        "trace": trace,
        "summary": summary,
    }


def simulate_both(nfa: NFA, dfa: DFA, input_string: str) -> Dict[str, Any]:
    """
    Run independent simulations on both NFA and DFA and compare results.
    """
    nfa_result = simulate_nfa(nfa, input_string)
    dfa_result = simulate_dfa(dfa, input_string)

    if not nfa_result["success"]:
        return nfa_result
    if not dfa_result["success"]:
        return dfa_result

    agrees = (nfa_result["accepted"] == dfa_result["accepted"])

    return {
        "success": True,
        "input_string": input_string,
        "display_input": input_string if input_string.strip() else "ε (empty string)",
        "agrees": agrees,
        "accepted": nfa_result["accepted"],
        "nfa_result": nfa_result,
        "dfa_result": dfa_result,
        "comparison_note": (
            "Both automata agree on the result: "
            + ("Accepted." if nfa_result["accepted"] else "Rejected.")
            if agrees
            else "Discrepancy detected between NFA and DFA simulations."
        ),
    }

