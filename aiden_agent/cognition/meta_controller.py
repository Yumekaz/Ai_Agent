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

        # 1. LOOP-BREAKING
        self.last_actions.append(proposed_action)
        if len(self.last_actions) > self.loop_threshold:
            self.last_actions.pop(0)

        if len(set(self.last_actions)) == 1:
            return ("rest", "Breaking action repetition loop")

        # 2. EXTREME FATIGUE PROTECTION
        if agent.energy < 10 and proposed_action != "rest":
            return ("rest", "Energy critically low — forcing recovery")

        # 3. PATTERN-INFORMED AVOIDANCE
        for pattern in self_model.detected_patterns[-5:]:
            ptype = pattern.get("type", "")

            if ptype == "terrain_avoidance" and "move" in proposed_action:
                return ("rest", "Avoiding terrain known to reduce rewards")

            if ptype == "fatigue_accumulation" and proposed_action == "explore":
                return ("rest", "Fatigue pattern detected — rest recommended")

        # 4. BASIC SAFETY
        if agent.energy < 20 and proposed_action in ["exercise", "explore"]:
            return ("rest", "Unsafe — low energy for high-cost action")

        # 5. MOTIVATION-DRIVEN PRIORITY
        if agent.motivation_levels.get("rest", 0) > 0.35 and proposed_action != "rest":
            return ("rest", "Rest motivation dominant")

        # 6. If no override: allow RL decision
        return (proposed_action, "RL-proposed action accepted")
