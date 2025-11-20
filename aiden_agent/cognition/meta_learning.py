class MetaLearner:
    """
    Adaptive Meta-Learning Layer.
    Examines self-model patterns and updates RL hyperparameters:
        - learning rate (alpha)
        - discount factor (gamma)
        - exploration rate (epsilon)
    """

    def __init__(self):
        self.learning_rate_bounds = (0.05, 0.4)
        self.gamma_bounds = (0.80, 0.99)
        self.epsilon_bounds = (0.05, 0.35)

        self.adjustment_history = []

    def adapt(self, agent, self_model):
        """
        Adjusts RL parameters based on behavior patterns.
        Returns (changes_made: dict)
        """

        changes = {}

        # ----------------------------
        # 1. REPETITION LOOP → decrease epsilon
        # ----------------------------
        if self_model.repetition_rate > 0.6:
            agent.rl_system.epsilon *= 0.9
            agent.rl_system.epsilon = max(agent.rl_system.epsilon, self.epsilon_bounds[0])
            changes["epsilon"] = agent.rl_system.epsilon

        # ----------------------------
        # 2. RAPID FATIGUE → increase gamma (value future rest higher)
        # ----------------------------
        if self_model.recent_fatigue_spike > 0.4:
            agent.rl_system.gamma *= 1.05
            agent.rl_system.gamma = min(agent.rl_system.gamma, self.gamma_bounds[1])
            changes["gamma"] = agent.rl_system.gamma

        # ----------------------------
        # 3. LOW REWARD TREND → increase learning rate (adapt faster)
        # ----------------------------
        if self_model.short_term_reward_trend < -0.2:
            agent.rl_system.alpha *= 1.1
            agent.rl_system.alpha = min(agent.rl_system.alpha, self.learning_rate_bounds[1])
            changes["alpha"] = agent.rl_system.alpha

        # ----------------------------
        # 4. HIGH REWARD BUT NO CHANGE → decrease learning rate (stabilize)
        # ----------------------------
        if self_model.reward_plateau_detected:
            agent.rl_system.alpha *= 0.9
            agent.rl_system.alpha = max(agent.rl_system.alpha, self.learning_rate_bounds[0])
            changes["alpha"] = agent.rl_system.alpha

        # ----------------------------
        # 5. EXPLORATION SURGE → reduce epsilon (avoid chaotic behavior)
        # ----------------------------
        if self_model.novelty_seeking > 0.6:
            agent.rl_system.epsilon *= 0.9
            agent.rl_system.epsilon = max(agent.rl_system.epsilon, self.epsilon_bounds[0])
            changes["epsilon"] = agent.rl_system.epsilon

        # ----------------------------
        # 6. BOREDOM SPIKE → increase epsilon (explore more)
        # ----------------------------
        if self_model.boredom_index > 0.5:
            agent.rl_system.epsilon *= 1.1
            agent.rl_system.epsilon = min(agent.rl_system.epsilon, self.epsilon_bounds[1])
            changes["epsilon"] = agent.rl_system.epsilon

        if changes:
            self.adjustment_history.append(changes)

        return changes
