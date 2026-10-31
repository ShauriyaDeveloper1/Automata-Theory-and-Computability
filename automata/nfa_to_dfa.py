"""Subset Construction Algorithm for converting an NFA to an equivalent complete DFA."""

from __future__ import annotations
from typing import Dict, List, Set, FrozenSet, Tuple, Optional, Any
from .models import NFA, DFA


def generate_state_label(index: int) -> str:
    """Generate human-readable DFA state label: A..Z, then S1, S2, etc."""
    if index < 26:
        return chr(ord('A') + index)
    return f"S{index - 25}"


def format_subset(subset: FrozenSet[str] | Set[str] | List[str]) -> str:
    """Format a subset nicely, e.g. {q0, q1} or ∅."""
    sorted_items = sorted(list(subset))
    if not sorted_items:
        return "∅"
    return "{" + ", ".join(sorted_items) + "}"


def convert_nfa_to_dfa(nfa: NFA) -> Dict[str, Any]:
    """
    Convert an NFA to a complete DFA using the Subset Construction (Powerset Construction) algorithm.
    
    Returns a dictionary containing:
        - dfa: The resulting DFA object
        - dfa_dict: Serialized DFA
        - events: Step-by-step conversion events
        - metrics: Comparison metrics between NFA and DFA
    """
    # 1. Initial DFA state corresponds to {nfa.initial_state}
    initial_subset: FrozenSet[str] = frozenset([nfa.initial_state])

    subset_to_label: Dict[FrozenSet[str], str] = {}
    label_to_subset: Dict[str, FrozenSet[str]] = {}
    dead_state_label: Optional[str] = None

    # Assign initial state label 'A'
    initial_label = generate_state_label(0)
    subset_to_label[initial_subset] = initial_label
    label_to_subset[initial_label] = initial_subset

    # Queue of subsets to explore
    queue: List[FrozenSet[str]] = [initial_subset]

    # DFA transitions: dfa_state -> {symbol -> target_dfa_state}
    dfa_transitions: Dict[str, Dict[str, str]] = {}

    # Conversion events for step-by-step playback
    events: List[Dict[str, Any]] = []
    step_counter = 0

    # Initial event: Discovery of initial state
    is_initial_acc = bool(initial_subset.intersection(set(nfa.accepting_states)))
    events.append({
        "step_number": 0,
        "event_type": "initial_state",
        "current_dfa_state": initial_label,
        "current_nfa_subset": sorted(list(initial_subset)),
        "current_nfa_subset_str": format_subset(initial_subset),
        "symbol": None,
        "transitions_considered": [],
        "resulting_nfa_subset": sorted(list(initial_subset)),
        "resulting_nfa_subset_str": format_subset(initial_subset),
        "destination_dfa_state": initial_label,
        "is_new_state": True,
        "is_accepting": is_initial_acc,
        "is_dead_state": False,
        "explanation": (
            f"Step 0: Initialized DFA. The NFA start state is '{nfa.initial_state}', "
            f"so DFA initial state is {initial_label} = {format_subset(initial_subset)}."
            f"{' (Accepting state)' if is_initial_acc else ''}"
        ),
        "discovered_states": [
            {
                "label": initial_label,
                "subset": sorted(list(initial_subset)),
                "subset_str": format_subset(initial_subset),
                "is_accepting": is_initial_acc,
                "is_initial": True,
            }
        ],
        "recorded_transitions": [],
    })

    discovered_order = [initial_label]

    # 2. Process discovered subsets in queue
    while queue:
        curr_subset = queue.pop(0)
        curr_label = subset_to_label[curr_subset]
        curr_subset_str = format_subset(curr_subset)

        if curr_label not in dfa_transitions:
            dfa_transitions[curr_label] = {}

        # Evaluate transitions on each alphabet symbol
        for sym in nfa.alphabet:
            step_counter += 1

            trans_considered: List[Dict[str, Any]] = []
            dest_states: Set[str] = set()

            for q in sorted(curr_subset):
                dests = nfa.get_transitions(q, sym)
                trans_considered.append({
                    "from_state": q,
                    "symbol": sym,
                    "to_states": sorted(list(dests)),
                })
                dest_states.update(dests)

            canonical_dest: FrozenSet[str] = frozenset(dest_states)
            dest_subset_str = format_subset(canonical_dest)
            is_dead = (len(canonical_dest) == 0)

            # Check if this subset was already discovered
            is_new = False
            if canonical_dest in subset_to_label:
                dest_label = subset_to_label[canonical_dest]
            else:
                is_new = True
                dest_label = generate_state_label(len(subset_to_label))
                subset_to_label[canonical_dest] = dest_label
                label_to_subset[dest_label] = canonical_dest
                discovered_order.append(dest_label)
                queue.append(canonical_dest)
                if is_dead and dead_state_label is None:
                    dead_state_label = dest_label

            dfa_transitions[curr_label][sym] = dest_label
            is_acc = bool(canonical_dest.intersection(set(nfa.accepting_states)))

            # Build detailed explanation
            if curr_subset:
                trans_calc_strs = [
                    f"δ({t['from_state']}, '{sym}') = {format_subset(t['to_states'])}"
                    for t in trans_considered
                ]
                trans_calc_summary = ", ".join(trans_calc_strs)
            else:
                trans_calc_summary = f"Empty state has no NFA states to branch from -> ∅"

            explanation_lines = [
                f"Step {step_counter}: Evaluate δ_D({curr_label}, '{sym}') where {curr_label} = {curr_subset_str}.",
                f"• Examined NFA transitions: {trans_calc_summary}",
                f"• Union of reachable states: ⋃ δ = {dest_subset_str}",
                f"• Target DFA State: {dest_label} = {dest_subset_str} "
                f"({'New state added to queue' if is_new else 'Existing state'})",
                f"• Recorded DFA transition: {curr_label} --'{sym}'--> {dest_label}",
            ]

            if is_dead:
                explanation_lines.append("• Notice: Destination is the empty set (Dead / Trap state).")
            if is_acc:
                explanation_lines.append("• Note: Destination is an Accepting state (contains at least one NFA final state).")

            # Collect snapshot of transitions so far
            curr_recorded_trans = [
                {"from": u, "symbol": s, "to": v}
                for u in discovered_order
                if u in dfa_transitions
                for s, v in dfa_transitions[u].items()
            ]

            curr_discovered = [
                {
                    "label": lbl,
                    "subset": sorted(list(label_to_subset[lbl])),
                    "subset_str": format_subset(label_to_subset[lbl]),
                    "is_accepting": bool(label_to_subset[lbl].intersection(set(nfa.accepting_states))),
                    "is_initial": (lbl == initial_label),
                    "is_dead": (lbl == dead_state_label),
                }
                for lbl in discovered_order
            ]

            events.append({
                "step_number": step_counter,
                "event_type": "transition_evaluated",
                "current_dfa_state": curr_label,
                "current_nfa_subset": sorted(list(curr_subset)),
                "current_nfa_subset_str": curr_subset_str,
                "symbol": sym,
                "transitions_considered": trans_considered,
                "resulting_nfa_subset": sorted(list(canonical_dest)),
                "resulting_nfa_subset_str": dest_subset_str,
                "destination_dfa_state": dest_label,
                "is_new_state": is_new,
                "is_accepting": is_acc,
                "is_dead_state": is_dead,
                "explanation": "\n".join(explanation_lines),
                "discovered_states": curr_discovered,
                "recorded_transitions": curr_recorded_trans,
            })

    # 3. Finalize DFA state list and accepting states
    ordered_dfa_states = list(discovered_order)
    dfa_accepting_states = [
        lbl for lbl in ordered_dfa_states
        if bool(label_to_subset[lbl].intersection(set(nfa.accepting_states)))
    ]

    state_subsets_dict: Dict[str, List[str]] = {
        lbl: sorted(list(label_to_subset[lbl])) for lbl in ordered_dfa_states
    }

    dfa = DFA(
        states=ordered_dfa_states,
        alphabet=list(nfa.alphabet),
        initial_state=initial_label,
        accepting_states=dfa_accepting_states,
        transitions=dfa_transitions,
        state_subsets=state_subsets_dict,
        dead_state=dead_state_label,
    )

    # Calculate comparison metrics
    nfa_transition_count = sum(
        len(dests)
        for sym_map in nfa.transitions.values()
        for dests in sym_map.values()
    )
    dfa_transition_count = sum(len(m) for m in dfa.transitions.values())

    metrics = {
        "num_nfa_states": len(nfa.states),
        "num_dfa_states": len(dfa.states),
        "num_nfa_accepting": len(nfa.accepting_states),
        "num_dfa_accepting": len(dfa.accepting_states),
        "num_nfa_transitions": nfa_transition_count,
        "num_dfa_transitions": dfa_transition_count,
        "has_dead_state": dead_state_label is not None,
        "dead_state_label": dead_state_label,
    }

    return {
        "dfa": dfa,
        "dfa_dict": dfa.to_dict(),
        "events": events,
        "metrics": metrics,
        "transition_table": dfa.get_transition_table(),
        "cytoscape_elements": dfa.to_cytoscape_elements(),
    }

