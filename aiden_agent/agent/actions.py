"""
Agent actions and action results
"""

from enum import Enum


class Action(Enum):
    """Actions the agent can take - includes directional movement"""
    STUDY = "study"
    REST = "rest"
    EXPLORE = "explore"
    REFLECT = "reflect"
    SOCIALIZE = "socialize"
    OBSERVE = "observe"
    EXERCISE = "exercise"
    COLLECT = "collect"
    MOVE_NORTH = "move_north"
    MOVE_SOUTH = "move_south"
    MOVE_EAST = "move_east"
    MOVE_WEST = "move_west"


class ActionResult:
    """Result of an action taken"""
    def __init__(self, action, success, effects, message):
        self.action = action
        self.success = success
        self.effects = effects
        self.message = message