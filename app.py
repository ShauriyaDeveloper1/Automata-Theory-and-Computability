"""Main Flask Application Entry Point for NFA-to-DFA Simulator."""

import os
from flask import Flask, jsonify, render_template
from routes.automata_routes import automata_bp
from routes.conversion_routes import conversion_bp
from routes.simulation_routes import simulation_bp


def create_app(config: dict | None = None) -> Flask:
    """Application factory for the automata web application."""
    app = Flask(__name__)

    # Sensible request limits (1MB max payload)
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-nfa-dfa-sim")
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # Disable static file caching for development

    if config:
        app.config.update(config)

    # Register blueprints
    app.register_blueprint(automata_bp)
    app.register_blueprint(conversion_bp)
    app.register_blueprint(simulation_bp)

    # Global error handlers
    @app.errorhandler(400)
    def handle_bad_request(err):
        return jsonify({
            "success": False,
            "error": "Bad Request: " + str(err.description if hasattr(err, "description") else err),
            "data": None,
        }), 400

    @app.errorhandler(404)
    def handle_not_found(err):
        if hasattr(err, "description") and "The requested URL was not found" in str(err.description):
            return render_template("base.html", page_title="Page Not Found", content="<div class='container py-5 text-center'><h2>404 - Page Not Found</h2><p>The requested page does not exist.</p><a href='/' class='btn btn-primary'>Return Home</a></div>"), 404
        return jsonify({
            "success": False,
            "error": "Resource not found.",
            "data": None,
        }), 404

    @app.errorhandler(413)
    def handle_payload_too_large(err):
        return jsonify({
            "success": False,
            "error": "Payload too large. Maximum configuration size is 1MB.",
            "data": None,
        }), 413

    @app.errorhandler(500)
    def handle_server_error(err):
        return jsonify({
            "success": False,
            "error": "An internal server error occurred. Please check your automaton configuration.",
            "data": None,
        }), 500

    return app


app = create_app()

if __name__ == "__main__":
    # Run development server
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting NFA-to-DFA Simulator on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)

