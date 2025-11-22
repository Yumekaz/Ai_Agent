from collections import deque
from enum import Enum, auto
from aiden_agent.cognition_rules.intention_rules import INTENTION_RULES


class IntentionType(Enum):
    EXPLORE = auto()
    GATHER = auto()
    LEARN = auto()
    SOCIALIZE = auto()
    REST = auto()
    SURVIVE = auto()
    MOVE_TO_SAFER_AREA = auto()


class Intention:
    def __init__(self, intent_type, strength=1.0, reason=""):
        self.intent_type = intent_type
        self.strength = strength
        self.reason = reason
        self.completed = False
        self.cycles_alive = 0

    def __repr__(self):
        return f"Intention({self.intent_type.name}, strength={self.strength:.2f})"


class IntentionEngine:
    """
    Phase-6 Intention Engine (Final & Stable)
    Includes:
    - Dedup
    - Stack cleanup
    - LEARN suppression when saturated
    - Stagnation escape
    - MOVE_TO_SAFER_AREA auto-resolve
    - MOVE_TO_SAFER_AREA decay when stuck
    - EXPLORE routes via BFS (planner)
    """

    def __init__(self):
        self.stack = deque(maxlen=5)
        self.last_intention = None
        self.stagnation_counter = 0
        self.history = []

    # =====================================================================
    # PUBLIC ENTRY
    # =====================================================================
    def evaluate(self, agent, world_obj, spatial):
        """
        agent      → AutonomousAgent
        world_obj  → GridWorld object (NOT dict)
        spatial    → Optional dict with planner spatial info
        Returns Intention object.
        """

        # 1. cleanup
        self._clean_stack()

        # 2. auto-complete MOVE_TO_SAFER_AREA
        self._check_auto_complete_safety(agent, world_obj)

        # 3. Symbolic intention rules (priority ordered)
        rule_out = self._apply_rules(agent, world_obj, spatial)

        if rule_out:
            new_type = IntentionType[rule_out["type"]]

            # ---- Fix: LEARN suppression when knowledge saturated ----
            if new_type == IntentionType.LEARN and agent.knowledge > 15:
                return None

            # build new intention
            new_int = Intention(
                new_type,
                rule_out["strength"],
                rule_out["reason"]
            )

            # Dedup existing intention of same type
            if self.last_intention and self.last_intention.intent_type == new_type:
                if new_int.strength > self.last_intention.strength:
                    self.last_intention.strength = new_int.strength
                    self.last_intention.reason = new_int.reason
                    self.last_intention.completed = False
                return self.last_intention

            self._push(new_int)
            return new_int

        # 4. stagnation escape
        forced = self._check_stagnation(agent)
        if forced:
            return forced

        # 5. Decay MOVE_TO_SAFER_AREA if stuck
        self._decay_safety_if_stuck()

        # 6. fallback to top of stack
        if self.stack:
            top = self.stack[-1]
            top.cycles_alive += 1
            return top

        return None

    # =====================================================================
    # ACTION SUGGESTION
    # =====================================================================
    def suggest_action(self, intention, agent, world_obj, spatial):
        if not intention:
            return None

        # LEARN decay logic
        if intention.intent_type == IntentionType.LEARN and agent.knowledge > 25:
            intention.strength -= 0.15
            if intention.strength <= 0:
                intention.completed = True
                self._clean_stack()
                return None

        # ---- FIX: EXPLORE NOW USES BFS ROUTES ----
        mapping = {
            IntentionType.EXPLORE: "move_to_route",       # <--- IMPORTANT
            IntentionType.GATHER: "collect",
            IntentionType.LEARN: "study",
            IntentionType.SOCIALIZE: "socialize",
            IntentionType.REST: "rest",
            IntentionType.SURVIVE: "rest",
        }

        # Safety routing
        if intention.intent_type == IntentionType.MOVE_TO_SAFER_AREA:
            return "move_to_route"

        return mapping.get(intention.intent_type, None)

    # =====================================================================
    # INTERNAL HELPERS
    # =====================================================================
    def _push(self, intention):
        self.stack.append(intention)
        self.last_intention = intention
        self.history.append(intention)

    def _apply_rules(self, agent, world_obj, spatial):
        for rule in INTENTION_RULES:
            out = rule(agent, world_obj, spatial)
            if out:
                return out
        return None

    def _clean_stack(self):
        active = [i for i in self.stack if not i.completed]
        self.stack = deque(active, maxlen=5)
        self.last_intention = self.stack[-1] if self.stack else None

    # =====================================================================
    # AUTO COMPLETE SAFETY INTENTION
    # =====================================================================
    def _check_auto_complete_safety(self, agent, world_obj):
        if not self.last_intention:
            return

        if self.last_intention.intent_type != IntentionType.MOVE_TO_SAFER_AREA:
            return

        cell = world_obj.get_cell(agent.position_x, agent.position_y)
        terrain = cell.terrain.value.lower()

        dangerous = {"mountains", "mountain", "ruins", "ruin"}

        if terrain not in dangerous:
            self.last_intention.completed = True
            self._clean_stack()

    # =====================================================================
    # SAFETY DECAY WHEN STUCK
    # =====================================================================
    def _decay_safety_if_stuck(self):
        """
        If MOVE_TO_SAFER_AREA stays too long without reaching safety,
        decay its strength to prevent forever blocking the stack.
        """
        if not self.last_intention:
            return

        if self.last_intention.intent_type != IntentionType.MOVE_TO_SAFER_AREA:
            return

        self.last_intention.strength -= 0.10
        if self.last_intention.strength <= 0:
            self.last_intention.completed = True
            self._clean_stack()

    # =====================================================================
    # STAGNATION ESCAPE
    # =====================================================================
    def _check_stagnation(self, agent):
        novelty = (
            agent.self_model.novelty_history[-1]
            if agent.self_model.novelty_history else 1.0
        )

        if novelty < 0.05:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0

        if self.stagnation_counter > 4:
            forced = Intention(
                IntentionType.EXPLORE,
                strength=1.5,
                reason="Forced EXPLORE due to stagnation"
            )
            self._push(forced)
            self.stagnation_counter = 0
            return forced

        return None

    # =====================================================================
    # DEBUG
    # =====================================================================
    def debug_dashboard(self):
        print("\n===== INTENTION ENGINE (PHASE-6) =====")
        if self.last_intention:
            print(f" Last: {self.last_intention.intent_type.name}")
            print(f" Strength: {self.last_intention.strength:.2f}")
            print(f" Reason: {self.last_intention.reason}")
        else:
            print(" Last: None")
        print(f" Stack: {[i.intent_type.name for i in self.stack]}")
        print(f" Stagnation Counter: {self.stagnation_counter}")
        print("=======================================\n")
