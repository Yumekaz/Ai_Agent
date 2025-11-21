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
        self.cycles_alive = 0
        self.completed = False

    def __repr__(self):
        return f"Intention({self.intent_type.name}, strength={self.strength:.2f})"


class IntentionEngine:
    """
    Phase-5 clean symbolic intention engine.
    No Phase-6 strategic planning.
    """

    def __init__(self):
        self.stack = deque(maxlen=5)
        self.last_intention = None
        self.intention_history = []
        self.stagnation_counter = 0

    # ============================================================
    # MAIN PIPELINE
    # ============================================================
    def evaluate(self, agent, world, spatial):

        # -- 1. Apply symbolic rules --------------------------------------
        rule_output = self._apply_rules(agent, world, spatial)

        if rule_output:
            new_type = IntentionType[rule_output["type"]]
            new_intent = Intention(
                new_type,
                rule_output["strength"],
                rule_output["reason"]
            )

            # ---------------------------
            # RULE: Learn spam kill-switch
            # ---------------------------
            if new_type == IntentionType.LEARN and agent.knowledge > 20:
                new_intent.completed = True

            self._clean_stack()

            # ---------------------------
            # Deduplication
            # ---------------------------
            if self.last_intention and self.last_intention.intent_type == new_type:
                if new_intent.strength > self.last_intention.strength:
                    self.last_intention.strength = new_intent.strength
                    self.last_intention.reason = new_intent.reason
                return self.last_intention

            # Fresh addition
            if not new_intent.completed:
                self.stack.append(new_intent)
                self.last_intention = new_intent
                self.intention_history.append(new_intent)
                return new_intent

        # -- 2. Stagnation fallback ---------------------------------------
        stagnation = self._check_stagnation(agent)
        if stagnation:
            return stagnation

        # -- 3. Default to stack top --------------------------------------
        if self.stack:
            top = self.stack[-1]
            top.cycles_alive += 1
            return top

        return None

    # ============================================================
    # RULE EXECUTION
    # ============================================================
    def _apply_rules(self, agent, world, spatial):
        for rule in INTENTION_RULES:
            out = rule(agent, world, spatial)
            if out:
                return out
        return None

    # ============================================================
    # STACK MAINTENANCE
    # ============================================================
    def _clean_stack(self):
        """Remove completed intentions and keep the stack tight."""
        self.stack = deque([i for i in self.stack if not i.completed], maxlen=5)

    # ============================================================
    # PATCH — STAGNATION HANDLER
    # ============================================================
    def _check_stagnation(self, agent):

        novelty = agent.self_model.novelty_history[-1] if agent.self_model.novelty_history else 1.0

        if novelty < 0.05:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = max(0, self.stagnation_counter - 1)

        # Threshold tuned for Phase-5 stability: 5 → 7
        if self.stagnation_counter > 6:
            self.stagnation_counter = 0

            forced = Intention(
                IntentionType.EXPLORE,
                strength=1.4,
                reason="Forced exploration due to stagnation"
            )

            self._clean_stack()
            self.stack.append(forced)
            self.last_intention = forced
            return forced

        return None

    # ============================================================
    # DEBUG
    # ============================================================
    def debug_dashboard(self):
        print("\n===== INTENTION ENGINE DEBUG =====")

        if self.last_intention:
            print(f" Last: {self.last_intention.intent_type.name} "
                  f"(strength={self.last_intention.strength:.2f})")
            print(f" Reason: {self.last_intention.reason}")
        else:
            print(" Last: None")

        print(f" Stack({len(self.stack)}): {[i.intent_type.name for i in self.stack]}")
        print(f" Stagnation Counter: {self.stagnation_counter}")
        print("=================================\n")

    # ============================================================
    # ACTION SUGGESTION
    # ============================================================
    def suggest_action(self, intention, agent, world, spatial):
        if not intention:
            return None

        # Learn decay softening
        if intention.intent_type == IntentionType.LEARN and agent.knowledge > 28:
            intention.strength -= 0.15
            if intention.strength <= 0:
                intention.completed = True
                self._clean_stack()
                return None

        mapping = {
            IntentionType.EXPLORE: "explore",
            IntentionType.GATHER: "collect",
            IntentionType.LEARN: "study",
            IntentionType.SOCIALIZE: "socialize",
            IntentionType.REST: "rest",
            IntentionType.SURVIVE: "rest",
            IntentionType.MOVE_TO_SAFER_AREA: "move_random"  # Prevent forced loops
        }

        return mapping.get(intention.intent_type, None)
