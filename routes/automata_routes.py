"""Routes for NFA building, page rendering, validation, graph data, examples, and CSV exports."""

from __future__ import annotations
import csv
import io
from flask import Blueprint, render_template, request, jsonify, make_response
from automata.models import NFA, DFA
from automata.validator import validate_nfa
from examples.example_loader import get_all_examples, get_example_by_id

automata_bp = Blueprint("automata", __name__)


# ---------------------- PAGE RENDERING ROUTES ----------------------

@automata_bp.route("/")
def index():
    """Render the Home landing page."""
    return render_template("index.html")


@automata_bp.route("/builder")
def builder():
    """Render the Interactive NFA Builder page."""
    return render_template("builder.html")


@automata_bp.route("/conversion")
def conversion():
    """Render the Step-by-Step Conversion Studio page."""
    return render_template("conversion.html")


@automata_bp.route("/simulator")
def simulator():
    """Render the String Simulator page."""
    return render_template("simulator.html")


# ---------------------- API ROUTES ----------------------

@automata_bp.route("/api/automata/validate", methods=["POST"])
def api_validate():
    """Validate NFA JSON payload."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({
            "success": False,
            "error": "Malformed JSON in request body.",
            "data": None,
        }), 400

    is_valid, err_msg, err_details = validate_nfa(payload)
    if not is_valid:
        return jsonify({
            "success": False,
            "error": err_msg,
            "details": err_details,
            "data": None,
        }), 422

    return jsonify({
        "success": True,
        "error": None,
        "message": "NFA configuration is valid.",
        "data": payload,
    }), 200


@automata_bp.route("/api/automata/visualize", methods=["POST"])
def api_visualize():
    """Return Cytoscape.js elements and transition table for an NFA."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"success": False, "error": "Malformed JSON.", "data": None}), 400

    is_valid, err_msg, err_details = validate_nfa(payload)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg, "details": err_details}), 422

    try:
        nfa = NFA.from_dict(payload)
        return jsonify({
            "success": True,
            "error": None,
            "data": {
                "cytoscape_elements": nfa.to_cytoscape_elements(),
                "transition_table": nfa.get_transition_table(),
                "nfa": nfa.to_dict(),
            },
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to generate visualization: {str(e)}"}), 500


@automata_bp.route("/api/examples", methods=["GET"])
def api_get_examples():
    """Return gallery of sample automata."""
    return jsonify({
        "success": True,
        "error": None,
        "data": get_all_examples(),
    }), 200


@automata_bp.route("/api/examples/<example_id>", methods=["GET"])
def api_get_example(example_id: str):
    """Return single sample automaton by ID."""
    ex = get_example_by_id(example_id)
    if not ex:
        return jsonify({"success": False, "error": f"Example '{example_id}' not found."}), 404
    return jsonify({
        "success": True,
        "error": None,
        "data": ex,
    }), 200


@automata_bp.route("/api/export/csv", methods=["POST"])
def api_export_csv():
    """
    Export NFA or DFA transition table as CSV generated completely in memory.
    Expected JSON payload:
        {
            "type": "nfa" | "dfa",
            "automaton": { ... }
        }
    """
    payload = request.get_json(silent=True)
    if not payload or "type" not in payload or "automaton" not in payload:
        return jsonify({"success": False, "error": "Missing 'type' or 'automaton' in request."}), 400

    auto_type = payload.get("type", "").lower()
    auto_data = payload.get("automaton", {})

    output = io.StringIO()
    writer = csv.writer(output)

    if auto_type == "nfa":
        is_valid, err_msg, err_details = validate_nfa(auto_data)
        if not is_valid:
            return jsonify({"success": False, "error": err_msg, "details": err_details}), 422
        nfa = NFA.from_dict(auto_data)
        table = nfa.get_transition_table()
        filename = "nfa_transition_table.csv"
        writer.writerow(["# NFA Transition Table Export"])
        writer.writerow(["# Initial State:", nfa.initial_state])
        writer.writerow(["# Accepting States:", ", ".join(nfa.accepting_states)])
        writer.writerow([])
        writer.writerow(table["headers"])
        for row in table["rows"]:
            writer.writerow(row)

    elif auto_type == "dfa":
        dfa = DFA.from_dict(auto_data)
        table = dfa.get_transition_table()
        filename = "dfa_transition_table.csv"
        writer.writerow(["# DFA Transition Table Export (Subset Construction)"])
        writer.writerow(["# Initial State:", dfa.initial_state])
        writer.writerow(["# Accepting States:", ", ".join(dfa.accepting_states)])
        if dfa.dead_state:
            writer.writerow(["# Dead State:", dfa.dead_state])
        writer.writerow([])
        writer.writerow(table["headers"])
        for row in table["rows"]:
            writer.writerow(row)
    else:
        return jsonify({"success": False, "error": f"Unsupported export type: '{auto_type}'."}), 400

    csv_content = output.getvalue()
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

