from collections import deque
from aiden_agent.world.terrain import TerrainType


class GlobalPlanner:
    """
    Phase-6 Strategic Planner:
    • Forecasts future state
    • Determines subgoals using motivations + conditions
    • Computes safe-area routing using BFS
    • Avoids world-boundary traps
    • Terrain-aware high-level action suggestion
    """

    def __init__(self):
        self.plan_memory = []
        self.last_plan = None

    # ---------------------------------------------------------
    # Forecast future agent condition (self-model patterns)
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
    # High-level subgoal selection
    # ---------------------------------------------------------
    def propose_subgoal(self, agent):

        # Survival priority
        if agent.energy < 35:
            return "recover_energy"

        # If stuck in bad terrain → search safe cell
        cell = agent.get_current_cell()
        if cell.terrain in {TerrainType.MOUNTAINS, TerrainType.RUINS}:
            return "find_safe_area"

        # Exploration motivation
        if agent.motivation_levels.get("exploration", 0) > 0.20:
            return "find_new_cell"

        # Learning drive
        if agent.motivation_levels.get("learning", 0) > 0.20:
            return "study_knowledge"

        return "maintain_status"

    # ---------------------------------------------------------
    # Terrain danger scoring (not used directly but future-proof)
    # ---------------------------------------------------------
    def terrain_cost(self, terrain):
        if terrain in [TerrainType.MOUNTAINS, TerrainType.RUINS]:
            return 8  # highly dangerous
        if terrain == TerrainType.PLAINS:
            return 3
        if terrain == TerrainType.FOREST:
            return 4
        if terrain == TerrainType.RIVER:
            return 1  # beneficial terrain
        return 2

    # ---------------------------------------------------------
    # BFS to find nearest non-dangerous terrain cell
    # ---------------------------------------------------------
    def find_nearest_safe_cell(self, agent):
        gw = agent.environment.grid_world
        start = (agent.position_x, agent.position_y)

        dangerous = {TerrainType.MOUNTAINS, TerrainType.RUINS}

        queue = deque([(start, None)])  # (pos, first_direction)
        visited = set([start])

        while queue:
            (x, y), first_step = queue.popleft()
            cell = gw.get_cell(x, y)

            # Found safe terrain
            if cell.terrain not in dangerous:
                return first_step

            neighbors = {
                "move_north": (x, y - 1),
                "move_south": (x, y + 1),
                "move_west": (x - 1, y),
                "move_east": (x + 1, y),
            }

            for move, (nx, ny) in neighbors.items():
                if not gw.is_valid_position(nx, ny):
                    continue

                if (nx, ny) in visited:
                    continue

                visited.add((nx, ny))

                if first_step is None:
                    queue.append(((nx, ny), move))
                else:
                    queue.append(((nx, ny), first_step))

        return None

    # ---------------------------------------------------------
    # Subgoal → strategic action
    # ---------------------------------------------------------
    def choose_action_for_subgoal(self, subgoal, agent):

        # 1. Rest if energy critical
        if subgoal == "recover_energy":
            return "rest"

        # 2. Move toward safe area
        if subgoal == "find_safe_area":
            direction = self.find_nearest_safe_cell(agent)
            if direction:
                return direction
            return "move_random"

        # ---------------------------------------------------------
        # 3. HARD BOUNDARY ESCAPE (critical for exploration)
        # ---------------------------------------------------------
        gw = agent.environment.grid_world
        max_x = gw.width - 1
        max_y = gw.height - 1

        x = agent.position_x
        y = agent.position_y

        if y == 0 and gw.is_valid_position(x, y + 1):
            return "move_south"

        if y == max_y and gw.is_valid_position(x, y - 1):
            return "move_north"

        if x == 0 and gw.is_valid_position(x + 1, y):
            return "move_east"

        if x == max_x and gw.is_valid_position(x - 1, y):
            return "move_west"

        # ---------------------------------------------------------
        # 4. Find undiscovered neighbor cells
        # ---------------------------------------------------------
        if subgoal == "find_new_cell":
            moves = []

            # north
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

            # fallback: let RL handle open exploration
            return "explore"

        # 5. Knowledge gain
        if subgoal == "study_knowledge":
            return "study"

        # Default
        return None

    # ---------------------------------------------------------
    # Master strategic planner entry point
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
