import random

class MetaController:
    """
    Phase-5 Meta-Controller:
    • Breaks loops
    • Handles fatigue
    • Respects basic self-model patterns
    • No terrain safety (that is Phase-6)
    """

    def __init__(self):
        self.last_actions = []
        self.loop_threshold = 4
        self.override_history = []

    def evaluate(self, agent, proposed_action, self_model):

        # ============================================================
        # 1. LOOP-BREAKING (Phase-5 version)
        # ============================================================
        self.last_actions.append(proposed_action)
        if len(self.last_actions) > self.loop_threshold:
            self.last_actions.pop(0)

        if len(set(self.last_actions)) == 1:
            valid_moves = [
                "move_north", "move_south",
                "move_east", "move_west"
            ]

            if agent.energy > 40:
                return (random.choice(valid_moves), "Breaking repetition loop")

            if agent.inventory.get("food", 0) > 0:
                return ("eat", "Breaking loop using food")

            return ("rest", "Breaking loop safely")

        # ============================================================
        # 2. FATIGUE OVERRIDE (soft Phase-5 version)
        # ============================================================
        if agent.energy < 15 and proposed_action != "rest":
            return ("rest", "Energy critical")

        if proposed_action == "exercise" and agent.energy < 40:
            return ("rest", "Too tired for exercise")

        # ============================================================
        # 3. PATTERN-BASED SAFETY (non-terrain)
        # ============================================================
        for pattern in self_model.detected_patterns[-5:]:
            if pattern.get("type") in ["fatigue_accumulation", "energy_depletion"]:
                if proposed_action.startswith("move") and agent.energy < 50:
                    return ("rest", "Fatigue trend detected")

        # ============================================================
        # 4. MOTIVATION PRIORITY
        # ============================================================
        if agent.motivation_levels.get("rest", 0) > 0.45:
            if proposed_action != "rest":
                return ("rest", "Rest motivation dominant")

        # ============================================================
        # 5. ACCEPT RL
        # ============================================================
        return (proposed_action, "RL accepted")
