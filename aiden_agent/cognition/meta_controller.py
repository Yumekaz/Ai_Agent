import random


class MetaController:
    """
    Phase-6 Meta-Controller (Final & Stable Version)

    Responsibilities:
        • Enforce survival-safety overrides
        • Integrate with global planner routes
        • Enforce intention priorities
        • Handle fatigue overrides
        • Terrain danger overrides
        • Self-model pattern overrides
        • Loop-breaking
        • Danger-zone oscillation escape
        • Final arbitration of actions
    """

    def __init__(self):
        self.last_actions = []
        self.loop_threshold = 4

        self.directions = {
            "move_north": (0, -1),
            "move_south": (0, 1),
            "move_east":  (1, 0),
            "move_west":  (-1, 0)
        }

        # Terrain names compared in lowercase
        self.DANGEROUS = {"mountains", "mountain", "ruins", "ruin"}

    # =====================================================================
    # MAIN CONTROLLER LOGIC
    # =====================================================================
    def evaluate(self, agent, proposed_action, planner_output, self_model):
        """
        INPUTS:
            proposed_action → RL / Intention Engine action (string)
            planner_output → dict OR string OR None
            self_model → provides fatigue/terrain patterns

        RETURNS:
            (final_action_string, reason)
        """

        # Extract useful information
        current_cell = agent.get_current_cell()
        current_terrain = current_cell.terrain.value.lower()

        # =============================================================
        # 1. LOOP-BREAKING – PREVENT BEHAVIORAL LOCK
        # =============================================================
        self.last_actions.append(proposed_action)
        if len(self.last_actions) > self.loop_threshold:
            self.last_actions.pop(0)

        loop_detected = (
            len(self.last_actions) == self.loop_threshold and
            len(set(self.last_actions)) == 1
        )

        if loop_detected:
            # Prefer safe escape if possible
            safe_step = self._safe_exit_step(agent)
            if safe_step:
                return (safe_step, "Loop-break: safe escape")

            # fallback hierarchy
            if agent.energy > 40:
                return (self._random_move(agent), "Loop-break: random scatter")
            elif agent.inventory.get("food", 0) > 0:
                return ("eat", "Loop-break: eat food")
            else:
                return ("rest", "Loop-break: forced conservation")

        # =============================================================
        # 2. HARD FATIGUE OVERRIDE (SURVIVAL FIRST)
        # =============================================================
        if agent.energy < 15 and proposed_action != "rest":
            return ("rest", "Critical fatigue override (<15 energy)")

        # =============================================================
        # 3. TERRAIN SAFETY OVERRIDES
        # =============================================================
        if current_terrain in self.DANGEROUS:

            # 3A. Do NOT rest on dangerous terrain unless extremely weak
            if proposed_action == "rest" and agent.energy >= 20:
                safe_step = self._safe_exit_step(agent)
                return (safe_step, "Unsafe terrain: cannot rest here")

            # 3B. Do NOT move deeper into danger
            if proposed_action and proposed_action.startswith("move"):
                if self._movement_leads_to_danger(agent, proposed_action):
                    safe_step = self._safe_exit_step(agent)
                    return (safe_step, "Avoiding deeper danger")

            # 3C. Danger-zone oscillation escape
            if loop_detected:
                safe_step = self._safe_exit_step(agent)
                return (safe_step, "Danger oscillation escape")

        # =============================================================
        # 4. SELF-MODEL PATTERN OVERRIDES
        # =============================================================
        if self_model and self_model.detected_patterns:
            pattern = self_model.detected_patterns[-1]

            # Terrain avoidance + low energy
            if pattern.get("type") == "terrain_avoidance":
                if proposed_action.startswith("move") and agent.energy < 60:
                    return ("rest", "Self-model: terrain avoidance override")

            # Chronic fatigue
            if pattern.get("type") == "fatigue_accumulation":
                if proposed_action.startswith("move") and agent.energy < 50:
                    return ("rest", "Self-model: fatigue accumulation override")

        # =============================================================
        # 5. REST MOTIVATION OVERRIDE
        # =============================================================
        if agent.motivation_levels.get("rest", 0) > 0.45:
            if proposed_action != "rest":
                return ("rest", "High rest motivation override (>0.45)")

        # =============================================================
        # 6. PLANNER ROUTE HANDLING (FULL PHASE-6)
        # =============================================================
        # The planner may output either:
        #   • None
        #   • "rest"
        #   • dict { action: "move_to_route", next_step: ... }

        if isinstance(planner_output, str):
            if planner_output == "rest":
                return ("rest", "Planner strategic rest")

        if isinstance(planner_output, dict):
            if planner_output.get("action") == "move_to_route":
                next_step = planner_output["next_step"]

                # Reject dangerous BFS suggestions
                if self._movement_leads_to_danger(agent, next_step):
                    safe_step = self._safe_exit_step(agent)
                    return (safe_step, "Planner correction: BFS suggested danger")

                return (next_step, "Following safe BFS route")

        # =============================================================
        # 7. DEFAULT – APPROVE PROPOSED ACTION
        # =============================================================
        return (proposed_action, "Action approved")

    # =====================================================================
    # INTERNAL UTILITIES
    # =====================================================================
    def _random_move(self, agent):
        moves = list(self.directions.keys())
        random.shuffle(moves)
        return moves[0]

    def _movement_leads_to_danger(self, agent, move):
        dx, dy = self.directions.get(move, (0, 0))
        nx = agent.position_x + dx
        ny = agent.position_y + dy

        gw = agent.environment.grid_world
        if not gw.is_valid_position(nx, ny):
            return True  # invalid = dangerous

        cell = gw.get_cell(nx, ny)
        terrain = cell.terrain.value.lower()

        return terrain in self.DANGEROUS

    def _safe_exit_step(self, agent):
        """
        Return a safe movement direction away from danger.
        If none exists, fallback to rest.
        """
        for move, (dx, dy) in self.directions.items():
            nx = agent.position_x + dx
            ny = agent.position_y + dy

            gw = agent.environment.grid_world
            if not gw.is_valid_position(nx, ny):
                continue

            cell = gw.get_cell(nx, ny)
            terrain = cell.terrain.value.lower()

            if terrain not in self.DANGEROUS:
                return move

        return "rest"
