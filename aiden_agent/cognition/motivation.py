"""
Motivation system for agent behavior
"""

from enum import Enum


class MotivationType(Enum):
    """Intrinsic motivations"""
    CURIOSITY = "curiosity"
    BOREDOM = "boredom"
    MAINTENANCE = "maintenance"
    LEARNING = "learning"
    SOCIAL = "social"
    SURVIVAL = "survival"
    REST = "rest"
    EXPLORATION = "exploration"