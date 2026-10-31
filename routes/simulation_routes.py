"""Routes for running input string simulations on NFA and DFA."""

from __future__ import annotations
from flask import Blueprint, request, jsonify
from automata.models import NFA, DFA
from automata.validator import validate_nfa
from automata.nfa_to_dfa import convert_nfa_to_dfa
from automata.simulator import simulate_nfa, simulate_dfa, simulate_both

simulation_bp = Blueprint("simulation", __name__)


@simulation_bp.route("/api/simulation/run", methods=["POST"])
def api_run_simulation():
    """
    Run input string simulation on NFA, DFA, or both.
    
    Expected JSON payload:
        {
            "mode": "nfa" | "dfa" | "both",
            "input_string": "0101",
            "nfa": { ... },
            "dfa": { ... } (optional)
        }
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"success": False, "error": "Malformed JSON in request body."}), 400

    mode = payload.get("mode", "both").lower()
    input_string = str(payload.get("input_string", ""))
    nfa_data = payload.get("nfa")
    dfa_data = payload.get("dfa")

    if not nfa_data and not dfa_data:
        return jsonify({"success": False, "error": "No automaton data provided."}), 400

    # Limit string length to 100 for responsive execution and UI rendering
    if len(input_string) > 100:
        return jsonify({"success": False, "error": "Input string length cannot exceed 100 characters."}), 400

    nfa = None
    if nfa_data:
        is_valid, err_msg, err_details = validate_nfa(nfa_data)
        if not is_valid:
            return jsonify({"success": False, "error": err_msg, "details": err_details}), 422
        nfa = NFA.from_dict(nfa_data)

    dfa = None
    if dfa_data:
        dfa = DFA.from_dict(dfa_data)
    elif nfa:
        # Generate DFA on the fly from valid NFA
        dfa = convert_nfa_to_dfa(nfa)["dfa"]

    if mode == "nfa":
        if not nfa:
            return jsonify({"success": False, "error": "NFA configuration is required for NFA simulation."}), 400
        res = simulate_nfa(nfa, input_string)
        if not res["success"]:
            return jsonify(res), 400
        return jsonify({"success": True, "error": None, "data": res}), 200

    elif mode == "dfa":
        if not dfa:
            return jsonify({"success": False, "error": "DFA configuration is required for DFA simulation."}), 400
        res = simulate_dfa(dfa, input_string)
        if not res["success"]:
            return jsonify(res), 400
        return jsonify({"success": True, "error": None, "data": res}), 200

    elif mode == "both":
        if not nfa or not dfa:
            return jsonify({"success": False, "error": "Both NFA and DFA are required for dual simulation."}), 400
        res = simulate_both(nfa, dfa, input_string)
        if not res["success"]:
            return jsonify(res), 400
        return jsonify({"success": True, "error": None, "data": res}), 200

    else:
        return jsonify({"success": False, "error": f"Unknown simulation mode: '{mode}'."}), 400

