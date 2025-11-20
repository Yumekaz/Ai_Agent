class MetaController:
    """
    Meta-layer that evaluates RL-selected actions and overrides when:
    1. Action unsafe (fatigue, hunger, risk conditions)
    2. Action repeats irrationally (loop breaker)
    3. Action contradicts known self-model patterns
    4. Action violates strong motivations (e.g., rest when nearly collapsed)
    """

    def __init__(self):
        self.last_actions = []
        self.loop_threshold = 4  # detect repetition loops
        self.override_history = []

    def evaluate(self, agent, proposed_action, self_model):
        """
        Returns (final_action, reason)
        """

        # ============================================================
        # 1. LOOP-BREAKING (unchanged)
        # ============================================================
        self.last_actions.append(proposed_action)
        if len(self.last_actions) > self.loop_threshold:
            self.last_actions.pop(0)

        if len(set(self.last_actions)) == 1:
            return ("rest", "Breaking action repetition loop")

        # ============================================================
        # 2. EXTREME FATIGUE PROTECTION (PATCH 1)
        #    Raised threshold to ensure no more energy-death
        # ============================================================
        if agent.energy < 25 and proposed_action != "rest":
            return ("rest", "Energy low — recovery prioritized")

        # ============================================================
        # 3. SELF-MODEL PATTERN-INFORMED OVERRIDES
        # ============================================================
        for pattern in self_model.detected_patterns[-5:]:
            ptype = pattern.get("type", "")

            # Terrain pattern
            if ptype == "terrain_avoidance" and "move" in proposed_action:
                return ("rest", "Avoiding terrain known to reduce rewards")

            # Old fatigue check (kept)
            if ptype == "fatigue_accumulation" and proposed_action == "explore":
                return ("rest", "Fatigue pattern detected — rest recommended")

        # ============================================================
        # 3B. FATIGUE PATTERN — BLOCK ALL HIGH-ENERGY ACTIONS (PATCH 2)
        # ============================================================
        for pattern in self_model.detected_patterns[-5:]:
            if pattern.get("type") in ["fatigue_accumulation", "energy_depletion"]:
                if proposed_action in [
                    "exercise", "explore",
                    "move_north", "move_south", "move_east", "move_west"
                ]:
                    return ("rest", "Fatigue pattern detected — switching to recovery")

        # ============================================================
        # 4. BASIC SAFETY (modified by PATCH 3)
        #    Exercise forbidden when energy <50%
        # ============================================================
        if proposed_action == "exercise" and agent.energy < 50:
            return ("rest", "Too low energy for exercise")

        # Existing safety rule kept
        if agent.energy < 20 and proposed_action in ["exercise", "explore"]:
            return ("rest", "Unsafe — low energy for high-cost action")

        # ============================================================
        # 5. MOTIVATION-DRIVEN PRIORITY (unchanged)
        # ============================================================
        if agent.motivation_levels.get("rest", 0) > 0.35 and proposed_action != "rest":
            return ("rest", "Rest motivation dominant")

        # ============================================================
        # 6. NO OVERRIDE → Accept RL
        # ============================================================
        return (proposed_action, "RL-proposed action accepted")
