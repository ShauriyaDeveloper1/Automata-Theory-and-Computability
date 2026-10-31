"""Routes for NFA-to-DFA conversion and step-by-step playback data."""

from __future__ import annotations
from flask import Blueprint, request, jsonify
from automata.models import NFA
from automata.validator import validate_nfa
from automata.nfa_to_dfa import convert_nfa_to_dfa

conversion_bp = Blueprint("conversion", __name__)


@conversion_bp.route("/api/conversion/convert", methods=["POST"])
def api_convert():
    """Convert an NFA configuration into an equivalent complete DFA."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"success": False, "error": "Malformed JSON in request body.", "data": None}), 400

    is_valid, err_msg, err_details = validate_nfa(payload)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg, "details": err_details, "data": None}), 422

    try:
        nfa = NFA.from_dict(payload)
        conv_result = convert_nfa_to_dfa(nfa)

        return jsonify({
            "success": True,
            "error": None,
            "data": {
                "dfa": conv_result["dfa_dict"],
                "metrics": conv_result["metrics"],
                "transition_table": conv_result["transition_table"],
                "cytoscape_elements": conv_result["cytoscape_elements"],
                "total_steps": len(conv_result["events"]),
                "events": conv_result["events"],
                "nfa": nfa.to_dict(),
                "nfa_cytoscape": nfa.to_cytoscape_elements(),
                "nfa_table": nfa.get_transition_table(),
            },
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Conversion error: {str(e)}", "data": None}), 500


@conversion_bp.route("/api/conversion/steps", methods=["POST"])
def api_conversion_steps():
    """Return only the ordered conversion events for step-by-step playback."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"success": False, "error": "Malformed JSON in request body."}), 400

    is_valid, err_msg, err_details = validate_nfa(payload)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg, "details": err_details}), 422

    try:
        nfa = NFA.from_dict(payload)
        conv_result = convert_nfa_to_dfa(nfa)
        return jsonify({
            "success": True,
            "error": None,
            "data": {
                "events": conv_result["events"],
                "total_steps": len(conv_result["events"]),
                "metrics": conv_result["metrics"],
            },
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Step calculation failed: {str(e)}"}), 500

