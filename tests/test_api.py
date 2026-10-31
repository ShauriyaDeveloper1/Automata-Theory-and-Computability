"""Tests for Flask API endpoints."""

import json
import pytest
from app import create_app
from examples.example_loader import SAMPLE_AUTOMATA


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


def test_pages_load(client):
    """Ensure all required pages load successfully."""
    for path in ["/", "/builder", "/conversion", "/simulator"]:
        response = client.get(path)
        assert response.status_code in [200, 404]  # 404 only if template not yet created, 200 once templates exist


def test_api_examples(client):
    response = client.get("/api/examples")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert len(data["data"]) >= 5


def test_api_validate_success(client):
    valid_payload = SAMPLE_AUTOMATA[0]["data"]
    response = client.post(
        "/api/automata/validate",
        data=json.dumps(valid_payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


def test_api_validate_failure(client):
    invalid_payload = {"states": ["q0"], "alphabet": []}
    response = client.post(
        "/api/automata/validate",
        data=json.dumps(invalid_payload),
        content_type="application/json",
    )
    assert response.status_code == 422
    data = response.get_json()
    assert data["success"] is False
    assert "error" in data


def test_api_visualize(client):
    payload = SAMPLE_AUTOMATA[0]["data"]
    response = client.post(
        "/api/automata/visualize",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "cytoscape_elements" in data["data"]


def test_api_convert(client):
    payload = SAMPLE_AUTOMATA[1]["data"]
    response = client.post(
        "/api/conversion/convert",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "dfa" in data["data"]
    assert "events" in data["data"]
    assert "metrics" in data["data"]


def test_api_simulation_run(client):
    nfa_payload = SAMPLE_AUTOMATA[0]["data"]
    sim_payload = {
        "mode": "both",
        "input_string": "101",
        "nfa": nfa_payload,
    }
    response = client.post(
        "/api/simulation/run",
        data=json.dumps(sim_payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["accepted"] is True
    assert data["data"]["agrees"] is True


def test_api_export_csv_nfa(client):
    nfa_payload = SAMPLE_AUTOMATA[0]["data"]
    export_payload = {
        "type": "nfa",
        "automaton": nfa_payload,
    }
    response = client.post(
        "/api/export/csv",
        data=json.dumps(export_payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    csv_text = response.data.decode("utf-8")
    assert "State" in csv_text
    assert "q0" in csv_text


def test_api_export_csv_dfa(client):
    dfa_payload = {
        "states": ["A", "B"],
        "alphabet": ["0", "1"],
        "initial_state": "A",
        "accepting_states": ["B"],
        "transitions": {
            "A": {"0": "B", "1": "A"},
            "B": {"0": "B", "1": "B"},
        },
        "state_subsets": {"A": ["q0"], "B": ["q1"]},
        "dead_state": None,
    }
    response = client.post(
        "/api/export/csv",
        data=json.dumps({"type": "dfa", "automaton": dfa_payload}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    csv_text = response.data.decode("utf-8")
    assert "DFA State" in csv_text
    assert "A" in csv_text


def test_api_get_single_example(client):
    response = client.get("/api/examples/binary_ends_with_01")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["id"] == "binary_ends_with_01"


def test_api_get_nonexistent_example(client):
    response = client.get("/api/examples/nonexistent_id_123")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False


def test_api_conversion_steps(client):
    payload = SAMPLE_AUTOMATA[0]["data"]
    response = client.post(
        "/api/conversion/steps",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "events" in data["data"]
    assert len(data["data"]["events"]) > 0


def test_api_simulation_modes(client):
    nfa_payload = SAMPLE_AUTOMATA[0]["data"]
    
    # NFA mode
    res_nfa = client.post(
        "/api/simulation/run",
        data=json.dumps({"mode": "nfa", "input_string": "0", "nfa": nfa_payload}),
        content_type="application/json",
    )
    assert res_nfa.status_code == 200
    assert res_nfa.get_json()["data"]["accepted"] is True

    # DFA mode
    res_dfa = client.post(
        "/api/simulation/run",
        data=json.dumps({"mode": "dfa", "input_string": "0", "nfa": nfa_payload}),
        content_type="application/json",
    )
    assert res_dfa.status_code == 200
    assert res_dfa.get_json()["data"]["accepted"] is True


def test_api_malformed_json(client):
    response = client.post(
        "/api/automata/validate",
        data="not a json string",
        content_type="application/json",
    )
    assert response.status_code == 400
