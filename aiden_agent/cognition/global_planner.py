class GlobalPlanner:
    """
    High-level planning engine.
    Produces strategic action suggestions before RL.
    """

    def __init__(self):
        self.plan_memory = []
        self.last_plan = None

    # ---------------------------------------------------------
    # Forecast future agent condition (simple heuristic model)
    # ---------------------------------------------------------
    def forecast(self, agent, world_state, steps=3):
        energy = agent.energy
        reward_est = 0
        risk = 0

        for p in agent.self_model.detected_patterns[-5:]:
            desc = p.get("description", "")

            if "energy" in desc:
                energy -= p.get("avg_drop", 2)

            if "low reward" in desc:
                reward_est -= 0.5

            if "danger" in desc:
                risk += 1

        return {
            "future_energy": max(0, min(100, energy)),
            "reward_est": reward_est,
            "risk": risk
        }

    # ---------------------------------------------------------
    # Strategic sub-goal selection
    # ---------------------------------------------------------
    def propose_subgoal(self, agent):
        if agent.energy < 35:
            return "recover_energy"

        # more realistic threshold (since your personality normalization compresses values)
        if agent.motivation_levels.get("exploration", 0) > 0.20:
            return "find_new_cell"

        if agent.motivation_levels.get("learning", 0) > 0.20:
            return "study_knowledge"

        return "maintain_status"

    # ---------------------------------------------------------
    # Convert subgoal → strategic action
    # ---------------------------------------------------------
    def choose_action_for_subgoal(self, subgoal, agent):
        if subgoal == "recover_energy":
            return "rest"

        # -------------------------------------
        # Find new cells to explore
        # -------------------------------------
        if subgoal == "find_new_cell":
            gw = agent.environment.grid_world
            x = agent.position_x
            y = agent.position_y

            moves = []

            # check north
            if gw.is_valid_position(x, y - 1) and not gw.get_cell(x, y - 1).discovered:
                moves.append("move_north")

            # south
            if gw.is_valid_position(x, y + 1) and not gw.get_cell(x, y + 1).discovered:
                moves.append("move_south")

            # west
            if gw.is_valid_position(x - 1, y) and not gw.get_cell(x - 1, y).discovered:
                moves.append("move_west")

            # east
            if gw.is_valid_position(x + 1, y) and not gw.get_cell(x + 1, y).discovered:
                moves.append("move_east")

            if moves:
                return moves[0]

            # if all known → simple explore
            return "explore"

        if subgoal == "study_knowledge":
            return "study"

        return None

    # ---------------------------------------------------------
    # Main strategic decision function
    # ---------------------------------------------------------
    def get_strategic_action(self, agent, world_state):
        forecast = self.forecast(agent, world_state)
        subgoal = self.propose_subgoal(agent)
        strategic_action = self.choose_action_for_subgoal(subgoal, agent)

        self.last_plan = {
            "forecast": forecast,
            "subgoal": subgoal,
            "suggestion": strategic_action
        }

        return strategic_action
