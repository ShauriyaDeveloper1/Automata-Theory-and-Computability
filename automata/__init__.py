"""Automata package for NFA and DFA data models, validation, subset construction conversion, and simulation."""

from .models import NFA, DFA
from .validator import validate_nfa, AutomataValidationError
from .nfa_to_dfa import convert_nfa_to_dfa
from .simulator import simulate_nfa, simulate_dfa, simulate_both

__all__ = [
    "NFA",
    "DFA",
    "validate_nfa",
    "AutomataValidationError",
    "convert_nfa_to_dfa",
    "simulate_nfa",
    "simulate_dfa",
    "simulate_both",
]

