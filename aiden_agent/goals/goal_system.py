"""
Goal system for self-generated objectives
Phase-6 corrected version:
• Adds intention hints for exploration / collection
• Adds planner-compliant routing flags
• Ensures goals interact with BFS planner
• Ensures goals don’t send agent into unsafe zones
"""

from enum import Enum
from collections import defaultdict


class GoalStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class Goal:
    """
    Phase-6 goal object (unchanged)
    """
    def __init__(self, goal_id, description, goal_type, target_value, priority=1.0):
        self.id = goal_id
        self.description = description
        self.goal_type = goal_type
        self.target_value = target_value
        self.current_progress = 0.0
        self.priority = priority
        self.status = GoalStatus.ACTIVE
        self.created_cycle = 0
        self.completed_cycle = None
        self.reward_bonus = 0.0

        # PHASE-6 ADD:
        self.intention_hint = None      # ← maps goal → intention
        self.routing_required = False   # ← tells planner when routing is needed
        self.safe_routing_only = False  # ← avoid mountains/ruins


    # ------------------------------
    # Progress logic unchanged
    # ------------------------------
    def update_progress(self, new_progress):
        self.current_progress = new_progress

    def calculate_completion_percentage(self):
        if self.target_value == 0:
            return 0.0
        return min(1.0, self.current_progress / self.target_value)

    def check_completion(self):
        return self.current_progress >= self.target_value

    def mark_completed(self, cycle):
        self.status = GoalStatus.COMPLETED
        self.completed_cycle = cycle
        time_taken = cycle - self.created_cycle
        time_factor = max(0.5, 1.0 - (time_taken / 50.0))
        self.reward_bonus = 5.0 * self.priority * time_factor

    def mark_failed(self, cycle):
        self.status = GoalStatus.FAILED
        self.completed_cycle = cycle

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "goal_type": self.goal_type,
            "target_value": self.target_value,
            "current_progress": self.current_progress,
            "priority": self.priority,
            "status": self.status.value,
            "created_cycle": self.created_cycle,
            "completed_cycle": self.completed_cycle,
            "reward_bonus": self.reward_bonus,

            # Phase-6 additions
            "intention_hint": self.intention_hint,
            "routing_required": self.routing_required,
            "safe_routing_only": self.safe_routing_only,
        }

    @staticmethod
    def from_dict(data):
        g = Goal(
            goal_id=data["id"],
            description=data["description"],
            goal_type=data["goal_type"],
            target_value=data["target_value"],
            priority=data["priority"]
        )
        g.current_progress = data["current_progress"]
        g.status = GoalStatus(data["status"])
        g.created_cycle = data["created_cycle"]
        g.completed_cycle = data.get("completed_cycle")
        g.reward_bonus = data.get("reward_bonus", 0.0)

        # Phase-6 additions
        g.intention_hint = data.get("intention_hint")
        g.routing_required = data.get("routing_required", False)
        g.safe_routing_only = data.get("safe_routing_only", False)
        return g


class GoalManager:
    """
    PHASE-6 Goal Manager
    Now includes routing flags and intention hints.
    """
    def __init__(self, max_active_goals=3):
        self.max_active_goals = max_active_goals
        self.active_goals = []
        self.completed_goals = []
        self.failed_goals = []
        self.next_goal_id = 1
        self.total_goals_created = 0
        self.total_goals_completed = 0
        self.last_goal_creation_cycle = 0
        self.goal_creation_interval = 8

    # --------------------------------------------------
    # Goal creation logic
    # --------------------------------------------------
    def should_create_goals(self, current_cycle):
        cycles_since = current_cycle - self.last_goal_creation_cycle
        return len(self.active_goals) < self.max_active_goals and cycles_since >= self.goal_creation_interval

    def create_goals(self, agent_state, world_state, spatial_state, motivation_levels, current_cycle):
        from aiden_agent.cognition.motivation import MotivationType

        new_goals = []
        slots = self.max_active_goals - len(self.active_goals)
        if slots <= 0:
            return new_goals

        energy = agent_state.get("energy", 50)
        knowledge = agent_state.get("knowledge", 0)
        happiness = agent_state.get("happiness", 50)
        cells_discovered = spatial_state.get("cells_discovered", 1)
        inventory = spatial_state.get("inventory", {})

        # Candidate list
        candidates = []

        # =====================================================
        # EXPLORATION GOAL
        # =====================================================
        if motivation_levels.get(MotivationType.EXPLORATION, 0) > 0.45:
            unexplored = 25 - cells_discovered
            if unexplored > 0:
                target = min(5, max(2, unexplored // 3))
                candidates.append({
                    "description": f"Explore {target} new tiles",
                    "goal_type": "explore_tiles",
                    "target": target,
                    "priority": motivation_levels[MotivationType.EXPLORATION],

                    # Phase-6:
                    "intention_hint": "EXPLORE",
                    "routing_required": True,
                    "safe_routing_only": False
                })

        # =====================================================
        # RELIC COLLECTION
        # =====================================================
        if inventory.get("relic", 0) < 3 and motivation_levels.get(MotivationType.CURIOSITY, 0) > 0.3:
            candidates.append({
                "description": "Collect 2 relics",
                "goal_type": "collect_relics",
                "target": 2,
                "priority": 0.7,

                # Phase-6:
                "intention_hint": "GATHER",
                "routing_required": True,
                "safe_routing_only": True
            })

        # =====================================================
        # BOOK COLLECTION
        # =====================================================
        if inventory.get("book", 0) < 5 and motivation_levels.get(MotivationType.LEARNING, 0) > 0.4:
            candidates.append({
                "description": "Collect 3 books",
                "goal_type": "collect_books",
                "target": 3,
                "priority": 0.6,

                "intention_hint": "GATHER",
                "routing_required": True,
                "safe_routing_only": False
            })

        # =====================================================
        # KNOWLEDGE GOAL
        # =====================================================
        if motivation_levels.get(MotivationType.LEARNING, 0) > 0.55:
            knowledge_gap = 100 - knowledge
            target = min(30, max(10, int(knowledge_gap * 0.25)))
            candidates.append({
                "description": f"Increase knowledge by ≥{target}",
                "goal_type": "knowledge_gain",
                "target": target,
                "priority": motivation_levels[MotivationType.LEARNING],

                "intention_hint": "LEARN",
                "routing_required": False,
                "safe_routing_only": False
            })

        # =====================================================
        # ENERGY GOAL
        # =====================================================
        if energy < 70:
            priority = 0.9 if energy < 30 else 0.6
            candidates.append({
                "description": "Reach energy ≥80",
                "goal_type": "energy_level",
                "target": 80,
                "priority": priority,

                "intention_hint": "REST",
                "routing_required": False,
                "safe_routing_only": True
            })

        # =====================================================
        # HAPPINESS GOAL
        # =====================================================
        if happiness < 60:
            candidates.append({
                "description": "Reach happiness ≥70",
                "goal_type": "happiness_level",
                "target": 70,
                "priority": 0.5,

                "intention_hint": "SOCIALIZE",
                "routing_required": False,
                "safe_routing_only": True
            })

        # =====================================================
        # SELECT GOALS
        # =====================================================
        candidates.sort(key=lambda x: x["priority"], reverse=True)
        chosen = candidates[:slots]

        for c in chosen:
            g = Goal(
                goal_id=self.next_goal_id,
                description=c["description"],
                goal_type=c["goal_type"],
                target_value=c["target"],
                priority=c["priority"]
            )
            g.created_cycle = current_cycle

            # Phase-6: attach routing requirements
            g.intention_hint = c["intention_hint"]
            g.routing_required = c["routing_required"]
            g.safe_routing_only = c["safe_routing_only"]

            self.active_goals.append(g)
            new_goals.append(g)
            self.next_goal_id += 1
            self.total_goals_created += 1

        if new_goals:
            self.last_goal_creation_cycle = current_cycle

        return new_goals

    # ------------------------------------------------------------------
    # Progress tracking
    # ------------------------------------------------------------------
    def update_goal_progress(self, agent_state, spatial_state):
        """Unchanged except Phase-6 fixes already safe"""
        energy = agent_state.get("energy", 0)
        knowledge = agent_state.get("knowledge", 0)
        happiness = agent_state.get("happiness", 0)
        cells_discovered = spatial_state.get("cells_discovered", 0)
        inventory = spatial_state.get("inventory", {})

        if not hasattr(self, "_baseline_knowledge"):
            self._baseline_knowledge = {}
            self._baseline_cells = {}
            self._baseline_relics = {}
            self._baseline_books = {}

        for g in self.active_goals:
            if g.status != GoalStatus.ACTIVE:
                continue

            if g.goal_type == "explore_tiles":
                if g.id not in self._baseline_cells:
                    self._baseline_cells[g.id] = cells_discovered
                g.update_progress(cells_discovered - self._baseline_cells[g.id])

            elif g.goal_type == "collect_relics":
                if g.id not in self._baseline_relics:
                    self._baseline_relics[g.id] = inventory.get("relic", 0)
                g.update_progress(inventory.get("relic", 0) - self._baseline_relics[g.id])

            elif g.goal_type == "collect_books":
                if g.id not in self._baseline_books:
                    self._baseline_books[g.id] = inventory.get("book", 0)
                g.update_progress(inventory.get("book", 0) - self._baseline_books[g.id])

            elif g.goal_type == "knowledge_gain":
                if g.id not in self._baseline_knowledge:
                    self._baseline_knowledge[g.id] = knowledge
                g.update_progress(knowledge - self._baseline_knowledge[g.id])

            elif g.goal_type == "energy_level":
                g.update_progress(energy)

            elif g.goal_type == "happiness_level":
                g.update_progress(happiness)

    # ------------------------------------------------------------------
    # Completion logic
    # ------------------------------------------------------------------
    def evaluate_goals(self, current_cycle):
        completed = []
        failed = []
        bonus = 0.0

        for g in self.active_goals[:]:
            if g.status != GoalStatus.ACTIVE:
                continue

            if g.check_completion():
                g.mark_completed(current_cycle)
                completed.append(g)
                bonus += g.reward_bonus
                self.active_goals.remove(g)
                self.completed_goals.append(g)
                self.total_goals_completed += 1

            elif current_cycle - g.created_cycle > 25:
                g.mark_failed(current_cycle)
                failed.append(g)
                self.active_goals.remove(g)
                self.failed_goals.append(g)

        return completed, failed, bonus

    def get_active_goal(self):
        """
        Return the most important active goal.
        Planner depends on this.
        """
        if not self.active_goals:
            return None

        # Highest priority goal first
        return max(self.active_goals, key=lambda g: g.priority)

    def get_goal_statistics(self):
        """
        Return simple statistics required by final summary.
        """
        total_goals = self.total_goals_created
        completed = self.total_goals_completed
        failed = len(self.failed_goals)
        active = len(self.active_goals)

        success_rate = (completed / total_goals * 100) if total_goals > 0 else 0.0

        return {
            "total_created": total_goals,
            "completed": completed,
            "failed": failed,
            "active": active,
            "success_rate": success_rate
        }

    def get_active_goals_display(self):
        """
        Return lightweight UI-friendly display format for active goals.
        Required by autonomous_agent.display_status().
        """
        if not self.active_goals:
            return []

        display = []

        for g in self.active_goals:
            pct = g.calculate_completion_percentage() * 100
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))

            display.append({
                "description": g.description,
                "progress": f"[{bar}] {pct:.0f}%",
                "priority": f"P{g.priority:.1f}"
            })

        return display

    def to_dict(self):
        """
        Serialize full goal manager state for saving.
        """
        return {
            "active_goals": [g.to_dict() for g in self.active_goals],
            "completed_goals": [g.to_dict() for g in self.completed_goals[-20:]],
            "failed_goals": [g.to_dict() for g in self.failed_goals[-20:]],
            "next_goal_id": self.next_goal_id,
            "total_goals_created": self.total_goals_created,
            "total_goals_completed": self.total_goals_completed,
            "last_goal_creation_cycle": self.last_goal_creation_cycle
        }

    @staticmethod
    def from_dict(data):
        """
        Load saved GoalManager state.
        """
        gm = GoalManager()
        gm.active_goals = [Goal.from_dict(g) for g in data.get("active_goals", [])]
        gm.completed_goals = [Goal.from_dict(g) for g in data.get("completed_goals", [])]
        gm.failed_goals = [Goal.from_dict(g) for g in data.get("failed_goals", [])]
        gm.next_goal_id = data.get("next_goal_id", 1)
        gm.total_goals_created = data.get("total_goals_created", 0)
        gm.total_goals_completed = data.get("total_goals_completed", 0)
        gm.last_goal_creation_cycle = data.get("last_goal_creation_cycle", 0)
        return gm

    # ---------------------- UI / Saving code unchanged ----------------------