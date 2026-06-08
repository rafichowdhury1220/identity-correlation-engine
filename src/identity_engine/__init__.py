"""Identity Correlation Engine - Main module"""

__version__ = "1.0.0"
__author__ = "Rafi Chowdhury"
__description__ = "Enterprise identity deduplication and unification platform"

from .core import IdentityCorrelator
from .models import Identity, UnifiedProfile, MatchingDecision
from .config import load_config

__all__ = [
    "IdentityCorrelator",
    "Identity",
    "UnifiedProfile",
    "MatchingDecision",
    "load_config",
]
