"""
Q-Learning reinforcement learning system
"""

import random
from collections import defaultdict, deque


class QLearningSystem:
    """
    Enhanced Q-Learning with spatial context and goal rewards
    Now considers: terrain, resources, hazards, position, goals
    """
    def __init__(self, learning_rate=0.1, epsilon=0.15, discount_factor=0.9):
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.alpha = learning_rate
        self.epsilon = epsilon
        self.gamma = discount_factor
        self.experience_buffer = deque(maxlen=200)
        self.total_rewards = []
        self.action_rewards = defaultdict(list)
    
    def get_context(self, agent_state, world_state, spatial_context):
        """
        Enhanced context with spatial awareness
        spatial_context includes: terrain, nearby_resources, hazard_level
        """
        # Energy state
        if agent_state["energy"] < 20:
            energy_ctx = "critical"
        elif agent_state["energy"] < 40:
            energy_ctx = "low"
        elif agent_state["energy"] < 70:
            energy_ctx = "medium"
        else:
            energy_ctx = "high"
        
        # Focus state
        focus_ctx = "low" if agent_state["focus"] < 40 else "high"
        
        # Terrain context
        terrain_ctx = spatial_context.get("terrain", "unknown")
        
        # Resource proximity
        resource_ctx = "resources_nearby" if spatial_context.get("nearby_resources", 0) > 0 else "no_resources"
        
        # Hazard level
        hazard = spatial_context.get("hazard_level", 0)
        hazard_ctx = "dangerous" if hazard > 2 else ("risky" if hazard > 0 else "safe")
        
        # Composite context
        context = f"{energy_ctx}_{focus_ctx}_{terrain_ctx}_{resource_ctx}_{hazard_ctx}"
        
        return context
    
    def choose_action(self, context, available_actions):
        """Epsilon-greedy action selection"""
        if random.random() < self.epsilon:
            return random.choice(available_actions)
        else:
            best_action = None
            best_q_value = float('-inf')
            
            for action in available_actions:
                q_value = self.q_table[context][action.value]
                if q_value > best_q_value:
                    best_q_value = q_value
                    best_action = action
            
            return best_action if best_action else random.choice(available_actions)
    
    def calculate_reward(self, effects, prev_state, new_state, spatial_bonus=0, goal_bonus=0):
        """
        Enhanced reward calculation with spatial exploration and goal bonuses
        """
        delta_knowledge = effects.get("knowledge", 0.0)
        delta_happiness = effects.get("happiness", 0.0)
        delta_energy = effects.get("energy", 0.0)
        delta_focus = effects.get("focus", 0.0)
        
        reward = (
            delta_knowledge * 0.5 +
            delta_happiness * 0.3 +
            delta_energy * 0.2 +
            delta_focus * 0.15 +
            spatial_bonus +
            goal_bonus
        )
        
        # Survival penalties
        if new_state["energy"] < 15:
            reward -= 10.0
        elif new_state["energy"] < 30:
            reward -= 2.0
        
        # Balance bonus
        if (new_state["energy"] > 40 and 
            new_state["happiness"] > 40 and 
            new_state["focus"] > 40):
            reward += 2.0
        
        return reward
    
    def update_q_value(self, context, action, reward):
        """Q-learning update rule with intrinsic reward support"""
        # Clamp reward for safety
        total_reward = max(min(reward, 10), -10)
        
        current_q = self.q_table[context][action.value]
        new_q = current_q + self.alpha * (total_reward - current_q)
        self.q_table[context][action.value] = new_q
    
    def record_experience(self, context, action, reward):
        """Store experience"""
        self.experience_buffer.append({
            "context": context,
            "action": action.value,
            "reward": reward
        })
        self.total_rewards.append(reward)
        self.action_rewards[action.value].append(reward)
    
    def get_best_actions(self, top_n=5):
        """Get top N action-context pairs"""
        action_values = []
        for context in self.q_table:
            for action, q_value in self.q_table[context].items():
                action_values.append((context, action, q_value))
        action_values.sort(key=lambda x: x[2], reverse=True)
        return action_values[:top_n]
    
    def get_learning_stats(self):
        """Learning statistics"""
        if not self.total_rewards:
            return {
                "avg_reward": 0.0,
                "total_experiences": 0,
                "contexts_learned": 0
            }
        
        return {
            "avg_reward": sum(self.total_rewards) / len(self.total_rewards),
            "recent_avg_reward": sum(list(self.total_rewards)[-10:]) / min(10, len(self.total_rewards)),
            "total_experiences": len(self.experience_buffer),
            "contexts_learned": len(self.q_table),
            "actions_learned": sum(len(actions) for actions in self.q_table.values())
        }
    
    def get_reward_trend(self, window=20):
        """
        Analyze recent reward trend
        Returns: 'improving', 'declining', or 'stable'
        """
        if len(self.total_rewards) < window * 2:
            return "stable"
        
        recent = list(self.total_rewards)[-window:]
        older = list(self.total_rewards)[-(window*2):-window]
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        
        if diff > 1.0:
            return "improving"
        elif diff < -1.0:
            return "declining"
        else:
            return "stable"
    
    def compute_intrinsic_reward(self, agent):
        """Compute intrinsic motivation rewards based on self-model"""
        r = 0.0
        
        # Novelty
        if agent.self_model.novelty_history:
            r += agent.self_model.novelty_history[-1] * 0.5
        
        # Repetition penalty
        r -= agent.self_model.action_repetition_index * 0.7
        
        # Terrain awareness
        terrain = agent.environment.grid_world.get_cell(agent.position_x, agent.position_y).terrain.value
        if terrain in agent.self_model.terrain_preferences:
            if agent.self_model.terrain_preferences[terrain] == "favorable":
                r += 0.3
            else:
                r -= 0.3
        
        return r