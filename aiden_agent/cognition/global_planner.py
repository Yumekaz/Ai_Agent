from collections import deque
from aiden_agent.world.terrain import TerrainType


class GlobalPlanner:
    """
    Phase-6 Strategic Planner (Final Corrected Version)
    """

    SAFE_TERRAINS = {TerrainType.PLAINS, TerrainType.FOREST, TerrainType.RIVER}

    def __init__(self):
        self.last_plan = None

    # -------------------------------------------------------------
    # SUBGOAL SELECTION
    # -------------------------------------------------------------
    def propose_subgoal(self, agent):
        cell = agent.get_current_cell()

        exploration = agent.motivation_levels.get("exploration", 0)
        learning = agent.motivation_levels.get("learning", 0)

        # Escape dangerous terrain
        if cell.terrain in {TerrainType.MOUNTAINS, TerrainType.RUINS}:
            return "find_safe_area"

        # Low energy
        if agent.energy < 25:
            return "recover_energy"

        # Learning saturation rule
        if exploration > 0.45:
            return "find_new_cell"

        if learning > 0.55:
            return "study_knowledge"

        return "maintain_status"

    # -------------------------------------------------------------
    # BFS CORE ROUTER (Corrected)
    # -------------------------------------------------------------
    def bfs_route(self, agent, is_valid_target, avoid_danger=False):
        gw = agent.environment.grid_world
        start = (agent.position_x, agent.position_y)

        queue = deque([(start, [], None)])  # (pos, path, first_step)
        visited = {start}

        dangerous = {TerrainType.MOUNTAINS, TerrainType.RUINS}

        while queue:
            (x, y), path, first_step = queue.popleft()
            cell = gw.get_cell(x, y)

            # Found a valid target
            if is_valid_target(x, y, cell) and (x, y) != start:
                if first_step is None:
                    return None
                return {
                    "action": first_step,   # FIXED: actual movement, no fake "move_to_route"
                    "route": path,
                    "distance": len(path),
                }

            # Explore neighbors
            for move, (nx, ny) in {
                "move_north": (x, y - 1),
                "move_south": (x, y + 1),
                "move_west": (x - 1, y),
                "move_east": (x + 1, y)
            }.items():

                if not gw.is_valid_position(nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue

                ncell = gw.get_cell(nx, ny)

                # Avoid dangerous terrain when required
                if avoid_danger and ncell.terrain in dangerous:
                    continue

                visited.add((nx, ny))

                # FIXED first_step logic
                new_first_step = move if first_step is None else first_step

                queue.append(((nx, ny), path + [(nx, ny)], new_first_step))

        return None  # BFS failed

    # -------------------------------------------------------------
    # SAFE AREA ROUTING
    # -------------------------------------------------------------
    def route_to_safe_area(self, agent):
        def safe(x, y, cell):
            return cell.terrain in self.SAFE_TERRAINS

        return self.bfs_route(agent, safe, avoid_danger=True)

    # -------------------------------------------------------------
    # UNEXPLORED CELL ROUTING (Corrected)
    # -------------------------------------------------------------
    def route_to_unexplored(self, agent):
        def unseen(x, y, cell):
            # FIXED: handle discovered/visited differences
            discovered = getattr(cell, "discovered", False)
            visited = getattr(cell, "visit_count", 0) > 0
            return not discovered and not visited

        return self.bfs_route(agent, unseen, avoid_danger=True)

    # -------------------------------------------------------------
    # LEARNING TILE ROUTING
    # -------------------------------------------------------------
    def route_to_learning_tile(self, agent):
        def stable(x, y, cell):
            return cell.terrain in {TerrainType.PLAINS, TerrainType.RIVER}
        return self.bfs_route(agent, stable, avoid_danger=True)

    # -------------------------------------------------------------
    # GOAL ROUTING
    # -------------------------------------------------------------
    def route_to_goal(self, agent):
        goal = agent.goal_manager.get_active_goal()
        if not goal:
            return None

        if not getattr(goal, "routing_required", False):
            return None

        route_target = getattr(goal, "route_target", None)
        if not isinstance(route_target, tuple):
            return None

        tx, ty = route_target

        def hit(x, y, cell):
            return (x, y) == (tx, ty)

        return self.bfs_route(agent, hit, avoid_danger=goal.safe_routing_only)

    # -------------------------------------------------------------
    # MAIN STRATEGIC DECISION
    # -------------------------------------------------------------
    def get_strategic_action(self, agent, world_state):
        cell = agent.get_current_cell()
        subgoal = self.propose_subgoal(agent)

        # 1. Escape dangerous terrain immediately
        if cell.terrain in {TerrainType.MOUNTAINS, TerrainType.RUINS}:
            plan = self.route_to_safe_area(agent)
            self.last_plan = plan
            return plan or {"action": "rest"}

        # 2. Goal routing
        goal_route = self.route_to_goal(agent)
        if goal_route:
            self.last_plan = goal_route
            return goal_route

        # 3. Recover energy
        if subgoal == "recover_energy":
            plan = {"action": "rest"}
            self.last_plan = plan
            return plan

        # 4. Find safe area (fixed check)
        if subgoal == "find_safe_area" and cell.terrain not in self.SAFE_TERRAINS:
            plan = self.route_to_safe_area(agent)
            self.last_plan = plan
            return plan

        # 5. Explore
        if subgoal == "find_new_cell":
            plan = self.route_to_unexplored(agent)
            if plan:
                self.last_plan = plan
                return plan

        # 6. Learn
        if subgoal == "study_knowledge":
            plan = self.route_to_learning_tile(agent)
            if plan:
                self.last_plan = plan
                return plan

        # 7. No strategic suggestion
        self.last_plan = None
        return None
