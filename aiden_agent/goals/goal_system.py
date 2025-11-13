"""
Goal system for self-generated objectives
"""

from enum import Enum
from collections import defaultdict


class GoalStatus(Enum):
    """Status of a goal"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class Goal:
    """
    Represents a self-generated objective for the agent
    Each goal has: description, priority, progress tracking, target, status
    """
    def __init__(self, goal_id, description, goal_type, target_value, priority=1.0):
        self.id = goal_id
        self.description = description
        self.goal_type = goal_type  # 'explore', 'collect', 'knowledge', 'energy', 'happiness'
        self.target_value = target_value  # Numeric target
        self.current_progress = 0.0
        self.priority = priority  # 0.0 to 1.0
        self.status = GoalStatus.ACTIVE
        self.created_cycle = 0
        self.completed_cycle = None
        self.reward_bonus = 0.0
        
    def update_progress(self, new_progress):
        """Update progress toward goal"""
        self.current_progress = new_progress
        
    def calculate_completion_percentage(self):
        """Calculate how close to completion (0.0 to 1.0)"""
        if self.target_value == 0:
            return 0.0
        return min(1.0, self.current_progress / self.target_value)
    
    def check_completion(self):
        """Check if goal is completed"""
        return self.current_progress >= self.target_value
    
    def mark_completed(self, cycle):
        """Mark goal as completed"""
        self.status = GoalStatus.COMPLETED
        self.completed_cycle = cycle
        # Calculate reward bonus based on priority and completion time
        time_taken = cycle - self.created_cycle
        time_factor = max(0.5, 1.0 - (time_taken / 50.0))  # Bonus for quick completion
        self.reward_bonus = 5.0 * self.priority * time_factor
    
    def mark_failed(self, cycle):
        """Mark goal as failed"""
        self.status = GoalStatus.FAILED
        self.completed_cycle = cycle
    
    def to_dict(self):
        """Serialize goal for JSON storage"""
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
            "reward_bonus": self.reward_bonus
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize goal from dictionary"""
        goal = Goal(
            goal_id=data["id"],
            description=data["description"],
            goal_type=data["goal_type"],
            target_value=data["target_value"],
            priority=data["priority"]
        )
        goal.current_progress = data["current_progress"]
        goal.status = GoalStatus(data["status"])
        goal.created_cycle = data["created_cycle"]
        goal.completed_cycle = data.get("completed_cycle")
        goal.reward_bonus = data.get("reward_bonus", 0.0)
        return goal


class GoalManager:
    """
    Manages goal creation, evaluation, prioritization, and reflection
    Integrates with agent's motivations and Q-learning system
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
        self.goal_creation_interval = 8  # Create goals every N cycles
        
    def should_create_goals(self, current_cycle):
        """Determine if it's time to create new goals"""
        cycles_since_last = current_cycle - self.last_goal_creation_cycle
        has_space = len(self.active_goals) < self.max_active_goals
        return has_space and cycles_since_last >= self.goal_creation_interval
    
    def create_goals(self, agent_state, world_state, spatial_state, motivation_levels, current_cycle):
        """
        Analyze current state and motivations to generate appropriate goals
        Returns list of newly created goals
        """
        from aiden_agent.cognition.motivation import MotivationType  # Import here to avoid circular dependency
        
        new_goals = []
        available_slots = self.max_active_goals - len(self.active_goals)
        
        if available_slots <= 0:
            return new_goals
        
        # Extract state information
        energy = agent_state.get("energy", 50)
        knowledge = agent_state.get("knowledge", 0)
        happiness = agent_state.get("happiness", 50)
        cells_discovered = spatial_state.get("cells_discovered", 1)
        inventory = spatial_state.get("inventory", {})
        
        # Determine which motivations are highest
        sorted_motivations = sorted(motivation_levels.items(), key=lambda x: x[1], reverse=True)
        top_motivation = sorted_motivations[0][0] if sorted_motivations else None
        
        # Goal candidates based on motivations and state
        candidates = []
        
        # EXPLORATION goals (if exploration motivation is high)
        if cells_discovered < 25 and motivation_levels.get(MotivationType.EXPLORATION, 0) > 0.4:
            unexplored = 25 - cells_discovered
            target = min(5, max(2, unexplored // 3))
            priority = motivation_levels.get(MotivationType.EXPLORATION, 0.5)
            candidates.append({
                "description": f"Explore {target} new tiles",
                "goal_type": "explore_tiles",
                "target": target,
                "priority": priority
            })
        
        # COLLECTION goals (if resources are important)
        total_relics = inventory.get("relic", 0)
        total_books = inventory.get("book", 0)
        
        if total_relics < 3 and motivation_levels.get(MotivationType.CURIOSITY, 0) > 0.3:
            candidates.append({
                "description": "Collect 2 relics",
                "goal_type": "collect_relics",
                "target": 2,
                "priority": 0.7
            })
        
        if total_books < 5 and motivation_levels.get(MotivationType.LEARNING, 0) > 0.4:
            candidates.append({
                "description": "Collect 3 books",
                "goal_type": "collect_books",
                "target": 3,
                "priority": 0.6
            })
        
        # KNOWLEDGE goals (if learning motivation is high)
        if knowledge < 100 and motivation_levels.get(MotivationType.LEARNING, 0) > 0.5:
            knowledge_gap = 100 - knowledge
            target = min(30, max(15, int(knowledge_gap * 0.3)))
            priority = motivation_levels.get(MotivationType.LEARNING, 0.5)
            candidates.append({
                "description": f"Increase knowledge by ≥{target}",
                "goal_type": "knowledge_gain",
                "target": target,
                "priority": priority
            })
        
        # ENERGY goals (if survival/rest motivation is high or energy is low)
        if energy < 70 and motivation_levels.get(MotivationType.SURVIVAL, 0) > 0.3:
            target_energy = 80
            priority = 0.9 if energy < 30 else 0.6
            candidates.append({
                "description": f"Reach energy ≥{target_energy}",
                "goal_type": "energy_level",
                "target": target_energy,
                "priority": priority
            })
        
        # HAPPINESS goals (if happiness is low)
        if happiness < 60:
            target_happiness = 70
            priority = 0.5
            candidates.append({
                "description": f"Reach happiness ≥{target_happiness}",
                "goal_type": "happiness_level",
                "target": target_happiness,
                "priority": priority
            })
        
        # Select top goals based on priority
        candidates.sort(key=lambda x: x["priority"], reverse=True)
        selected = candidates[:available_slots]
        
        # Create Goal objects
        for candidate in selected:
            goal = Goal(
                goal_id=self.next_goal_id,
                description=candidate["description"],
                goal_type=candidate["goal_type"],
                target_value=candidate["target"],
                priority=candidate["priority"]
            )
            goal.created_cycle = current_cycle
            self.active_goals.append(goal)
            new_goals.append(goal)
            self.next_goal_id += 1
            self.total_goals_created += 1
        
        if new_goals:
            self.last_goal_creation_cycle = current_cycle
        
        return new_goals
    
    def update_goal_progress(self, agent_state, spatial_state):
        """
        Update progress for all active goals based on current state
        """
        energy = agent_state.get("energy", 0)
        knowledge = agent_state.get("knowledge", 0)
        happiness = agent_state.get("happiness", 0)
        cells_discovered = spatial_state.get("cells_discovered", 0)
        inventory = spatial_state.get("inventory", {})
        
        # Track baselines for delta calculations
        if not hasattr(self, '_baseline_knowledge'):
            self._baseline_knowledge = {}
            self._baseline_cells = {}
            self._baseline_relics = {}
            self._baseline_books = {}
        
        for goal in self.active_goals:
            if goal.status != GoalStatus.ACTIVE:
                continue
            
            # Update progress based on goal type
            if goal.goal_type == "explore_tiles":
                # Track from baseline
                if goal.id not in self._baseline_cells:
                    self._baseline_cells[goal.id] = cells_discovered
                progress = cells_discovered - self._baseline_cells[goal.id]
                goal.update_progress(progress)
            
            elif goal.goal_type == "collect_relics":
                if goal.id not in self._baseline_relics:
                    self._baseline_relics[goal.id] = inventory.get("relic", 0)
                progress = inventory.get("relic", 0) - self._baseline_relics[goal.id]
                goal.update_progress(progress)
            
            elif goal.goal_type == "collect_books":
                if goal.id not in self._baseline_books:
                    self._baseline_books[goal.id] = inventory.get("book", 0)
                progress = inventory.get("book", 0) - self._baseline_books[goal.id]
                goal.update_progress(progress)
            
            elif goal.goal_type == "knowledge_gain":
                if goal.id not in self._baseline_knowledge:
                    self._baseline_knowledge[goal.id] = knowledge
                progress = knowledge - self._baseline_knowledge[goal.id]
                goal.update_progress(progress)
            
            elif goal.goal_type == "energy_level":
                # Direct level check
                goal.update_progress(energy)
            
            elif goal.goal_type == "happiness_level":
                # Direct level check
                goal.update_progress(happiness)
    
    def evaluate_goals(self, current_cycle):
        """
        Check active goals for completion or failure
        Returns: (newly_completed, newly_failed, total_reward_bonus)
        """
        newly_completed = []
        newly_failed = []
        total_reward_bonus = 0.0
        
        for goal in self.active_goals[:]:  # Copy list to allow removal
            if goal.status != GoalStatus.ACTIVE:
                continue
            
            # Check for completion
            if goal.check_completion():
                goal.mark_completed(current_cycle)
                newly_completed.append(goal)
                total_reward_bonus += goal.reward_bonus
                self.active_goals.remove(goal)
                self.completed_goals.append(goal)
                self.total_goals_completed += 1
            
            # Check for failure (timeout or impossible)
            elif current_cycle - goal.created_cycle > 25:  # 25 cycle timeout
                goal.mark_failed(current_cycle)
                newly_failed.append(goal)
                self.active_goals.remove(goal)
                self.failed_goals.append(goal)
        
        return newly_completed, newly_failed, total_reward_bonus
    
    def get_active_goals_display(self):
        """Format active goals for display"""
        if not self.active_goals:
            return []
        
        display = []
        for goal in self.active_goals:
            progress_pct = goal.calculate_completion_percentage() * 100
            progress_bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))
            display.append({
                "description": goal.description,
                "progress": f"[{progress_bar}] {progress_pct:.0f}%",
                "priority": f"P{goal.priority:.1f}"
            })
        return display
    
    def get_goal_statistics(self):
        """Get statistics about goals"""
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
    
    def reflect_on_goals(self, cycle):
        """
        Generate reflection summary on completed and failed goals
        Returns a reflection string
        """
        recent_completed = [g for g in self.completed_goals if cycle - g.completed_cycle <= 15]
        recent_failed = [g for g in self.failed_goals if cycle - g.completed_cycle <= 15]
        
        if not recent_completed and not recent_failed:
            return "No recent goals to reflect upon."
        
        reflection_parts = []
        
        if recent_completed:
            reflection_parts.append(f"Successfully completed {len(recent_completed)} goal(s):")
            for goal in recent_completed[:3]:  # Top 3
                reflection_parts.append(f"  ✓ {goal.description}")
        
        if recent_failed:
            reflection_parts.append(f"Failed {len(recent_failed)} goal(s):")
            for goal in recent_failed[:2]:  # Top 2
                reflection_parts.append(f"  ✗ {goal.description}")
            reflection_parts.append("  → Need to adjust strategies")
        
        return "\n".join(reflection_parts)
    
    def to_dict(self):
        """Serialize goal manager state"""
        return {
            "active_goals": [g.to_dict() for g in self.active_goals],
            "completed_goals": [g.to_dict() for g in self.completed_goals[-20:]],  # Keep last 20
            "failed_goals": [g.to_dict() for g in self.failed_goals[-10:]],  # Keep last 10
            "next_goal_id": self.next_goal_id,
            "total_goals_created": self.total_goals_created,
            "total_goals_completed": self.total_goals_completed,
            "last_goal_creation_cycle": self.last_goal_creation_cycle
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize goal manager from dictionary"""
        manager = GoalManager()
        manager.active_goals = [Goal.from_dict(g) for g in data.get("active_goals", [])]
        manager.completed_goals = [Goal.from_dict(g) for g in data.get("completed_goals", [])]
        manager.failed_goals = [Goal.from_dict(g) for g in data.get("failed_goals", [])]
        manager.next_goal_id = data.get("next_goal_id", 1)
        manager.total_goals_created = data.get("total_goals_created", 0)
        manager.total_goals_completed = data.get("total_goals_completed", 0)
        manager.last_goal_creation_cycle = data.get("last_goal_creation_cycle", 0)
        return manager