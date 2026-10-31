"""Flask routes package."""

from .automata_routes import automata_bp
from .conversion_routes import conversion_bp
from .simulation_routes import simulation_bp

__all__ = ["automata_bp", "conversion_bp", "simulation_bp"]

