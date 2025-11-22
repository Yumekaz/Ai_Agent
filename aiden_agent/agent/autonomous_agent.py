"""
Autonomous Agent with Cognitive Drift
"""

import random
import time
import json
import os
from datetime import datetime
from collections import defaultdict, deque

from aiden_agent.world import Environment, ResourceType, TerrainType, Weather
from aiden_agent.cognition import PersonalityProfile, MotivationType, ReflectionSystem
from aiden_agent.learning import QLearningSystem
from aiden_agent.goals import GoalManager
from aiden_agent.agent.actions import Action, ActionResult
from aiden_agent.cognition.self_model import SelfModel
from aiden_agent.cognition.meta_controller import MetaController
from aiden_agent.cognition.global_planner import GlobalPlanner
from aiden_agent.cognition.intent_engine import IntentionEngine

class AutonomousAgent:
    """
    Agent with cognitive drift: personality evolves based on experiences
    Enhanced with metacognition and self-modifying personality traits
    """
    def __init__(self, name="Aiden", memory_file="aiden_world_memory.json"):
        self.name = name
        self.memory_file = memory_file
        self.environment = Environment(grid_size=5)
        
        # ===== COGNITIVE DRIFT - PERSONALITY =====
        self.personality = PersonalityProfile()
        
        # ===== SPATIAL STATE =====
        self.position_x = 0
        self.position_y = 0
        self.cells_discovered = 1
        
        # ===== INVENTORY =====
        self.inventory = {
            ResourceType.FOOD: 0,
            ResourceType.BOOK: 0,
            ResourceType.RELIC: 0
        }
        
        # ===== INTERNAL STATE =====
        self.energy = 100.0
        self.knowledge = 0.0
        self.happiness = 50.0
        self.focus = 50.0
        self.social_need = 20.0
        
        # ===== GOAL SYSTEM =====
        self.goal_manager = GoalManager(max_active_goals=3)
        
        # ===== MEMORY =====
        self.short_term_memory = deque(maxlen=10)
        self.learned_topics = defaultdict(int)
        self.experiences = []
        
        self.long_term_memory = {
            "total_actions": defaultdict(int),
            "successful_strategies": defaultdict(list),
            "world_observations": [],
            "reflections": [],
            "knowledge_gained": [],
            "cells_explored": []
        }
        self.load_memory()
        
        # ===== MOTIVATION =====
        self.motivation_levels = {
            MotivationType.CURIOSITY: 0.5,
            MotivationType.BOREDOM: 0.0,
            MotivationType.MAINTENANCE: 0.1,
            MotivationType.LEARNING: 0.5,
            MotivationType.SOCIAL: 0.2,
            MotivationType.SURVIVAL: 0.0,
            MotivationType.REST: 0.2,
            MotivationType.EXPLORATION: 0.6
        }
        
        # ===== REINFORCEMENT LEARNING =====
        self.rl_system = QLearningSystem(
            learning_rate=0.1,
            epsilon=0.15,
            discount_factor=0.9
        )
        
        self.previous_state = None
        self.previous_context = None
        self.previous_action = None
        
        # ===== TIMING =====
        self.cycles_alive = 0
        self.last_rest = 0
        self.last_study = 0
        self.last_reflection = 0
        self.last_personality_display = 0
    
        # ===== SELF-MODELING LAYER =====
        self.self_model = SelfModel(history_size=50)
        self.last_self_model_display = 0

        # ===== META-COGNITION =====
        self.meta_controller = MetaController()
        self.global_planner = GlobalPlanner()
        
        self.intent_engine = IntentionEngine()
        self.current_intention = None
    
    # ========================================
    # COGNITIVE DRIFT - PERSONALITY INFLUENCE
    # ========================================
    
    def apply_personality_to_motivations(self):
        """
        Apply personality traits to motivation weights dynamically
        Called at the start of every cycle
        """
        # CURIOSITY BIAS → multiplies curiosity and exploration
        curiosity_multiplier = 1 + (self.personality.curiosity_bias - 0.5)
        self.motivation_levels[MotivationType.CURIOSITY] *= curiosity_multiplier
        self.motivation_levels[MotivationType.EXPLORATION] *= curiosity_multiplier
        
        # DISCIPLINE → boosts learning, reduces social
        discipline_effect = (self.personality.discipline - 0.5)
        self.motivation_levels[MotivationType.LEARNING] *= (1 + discipline_effect * 0.8)
        self.motivation_levels[MotivationType.SOCIAL] *= (1 - discipline_effect * 0.5)
        
        # RISK TOLERANCE → reduces survival/rest weight
        risk_effect = self.personality.risk_tolerance
        self.motivation_levels[MotivationType.SURVIVAL] *= (1.2 - risk_effect)
        self.motivation_levels[MotivationType.REST] *= (1.1 - risk_effect * 0.5)
        
        # SOCIAL AFFINITY → amplifies social motivation
        social_multiplier = 1 + (self.personality.social_affinity - 0.5)
        self.motivation_levels[MotivationType.SOCIAL] *= social_multiplier
        
        # OPTIMISM → affects happiness baseline (passive effect handled elsewhere)
        
        # Clamp all motivations 0-1
        for mot_type in self.motivation_levels:
            self.motivation_levels[mot_type] = max(0.0, min(1.0, self.motivation_levels[mot_type]))
        
        # PATCH 6: Normalize Motivations After Personality Multipliers
        total = sum(self.motivation_levels.values())
        if total > 1:
            for k in self.motivation_levels:
                self.motivation_levels[k] /= total
    
    def apply_optimism_to_happiness_recovery(self, base_recovery):
        """
        Optimism affects happiness recovery rate after negative events
        """
        optimism_bonus = (self.personality.optimism - 0.5) * 5
        return base_recovery + optimism_bonus
    
    # ========================================
    # METACOGNITIVE SELF-REFLECTION WITH PERSONALITY MUTATION
    # ========================================
    
    def self_reflect_from_memory(self):
        """
        Analyze long_term_memory and RL data to generate introspective reflections
        NOW ALSO MUTATES PERSONALITY based on insights
        NOW INCLUDES SELF-MODEL INTROSPECTION
        
        Returns: (reflection_string, personality_mutations, introspective_summary)
        """
        reflection_text, reward_trend, failure_count, success_count = ReflectionSystem.self_reflect_from_memory(
            self.long_term_memory, 
            self.rl_system, 
            self.goal_manager, 
            self.learned_topics, 
            self.cycles_alive,
            self.personality
        )
        
        # ===== SELF-MODEL CAUSE-EFFECT ANALYSIS =====
        new_patterns = self.self_model.analyze_cause_effect()
        
        if new_patterns:
            pattern_summary = f" Discovered {len(new_patterns)} new behavioral patterns."
            reflection_text += pattern_summary
        
        # ===== COGNITIVE DRIFT: PERSONALITY MUTATION =====
        # Determine dominant motivation
        dominant_motivation = max(self.motivation_levels.items(), key=lambda x: x[1])[0]
        
        # Mutate personality based on insights
        mutations = self.personality.mutate_from_reflection(
            reward_trend=reward_trend,
            failure_count=failure_count,
            success_count=success_count,
            dominant_motivation=dominant_motivation
        )
        
        # Record snapshot
        self.personality.record_snapshot(self.cycles_alive)
        
        # ===== GENERATE INTROSPECTIVE SUMMARY =====
        introspective_summary = ReflectionSystem.generate_introspective_summary(self, self.self_model)
        
        # Store reflection in memory with introspection
        self.long_term_memory["reflections"].append({
            "cycle": self.cycles_alive,
            "type": "self_analysis",
            "text": reflection_text,
            "personality_mutations": mutations,
            "archetype": self.personality.get_personality_archetype(),
            "self_narrative": self.self_model.generate_self_narrative(),
            "detected_patterns": len(new_patterns)
        })
        
        return reflection_text, mutations, introspective_summary
    
    # ========================================
    # MEMORY MANAGEMENT (Enhanced with Personality)
    # ========================================
    
    def load_memory(self):
        """Load persistent memory including personality profile"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load agent memories
                    self.long_term_memory["total_actions"] = defaultdict(int, data.get("total_actions", {}))
                    self.long_term_memory["successful_strategies"] = defaultdict(list, data.get("successful_strategies", {}))
                    self.long_term_memory["world_observations"] = data.get("world_observations", [])
                    self.long_term_memory["reflections"] = data.get("reflections", [])
                    self.long_term_memory["knowledge_gained"] = data.get("knowledge_gained", [])
                    self.long_term_memory["cells_explored"] = data.get("cells_explored", [])
                    self.learned_topics = defaultdict(int, data.get("learned_topics", {}))
                    
                    # Load personality profile
                    if "personality_profile" in data:
                        self.personality = PersonalityProfile.from_dict(data["personality_profile"])
                        archetype = self.personality.get_personality_archetype()
                        print(f"\n🧠 Personality Profile Loaded: {archetype}")
                        print(f"   Optimism: {self.personality.optimism:.2f} | Discipline: {self.personality.discipline:.2f}")
                        print(f"   Curiosity: {self.personality.curiosity_bias:.2f} | Risk: {self.personality.risk_tolerance:.2f}")
                    
                    # Load self-model state
                    if "self_model" in data:
                        self.self_model = SelfModel.from_dict(data["self_model"])
                        print(f"    🧠 Self-Model: {len(self.self_model.detected_patterns)} patterns detected")
                        print(f"        Fatigue Score: {self.self_model.fatigue_cause_score:.2f} | Environment Sensitivity: {self.self_model.environment_sensitivity:.2f}")
                    
                    # Load spatial state
                    if "position" in data:
                        self.position_x = data["position"]["x"]
                        self.position_y = data["position"]["y"]
                        self.cells_discovered = data["position"].get("cells_discovered", 1)
                    
                    # Load inventory
                    if "inventory" in data:
                        for resource, count in data["inventory"].items():
                            self.inventory[ResourceType(resource)] = count
                    
                    # Load grid world
                    if "grid_world" in data:
                        from aiden_agent.world import GridWorld
                        self.environment.grid_world = GridWorld.from_dict(data["grid_world"])
                    
                    # Load Q-table
                    if "q_table" in data:
                        for context, actions in data["q_table"].items():
                            for action, q_value in actions.items():
                                self.rl_system.q_table[context][action] = q_value
                    
                    # Load goal manager
                    if "goal_system" in data:
                        self.goal_manager = GoalManager.from_dict(data["goal_system"])
                    
                    print(f"[Memory] Loaded world state from previous session")
                    print(f"        Position: ({self.position_x}, {self.position_y})")
                    print(f"        Cells discovered: {self.cells_discovered}")
                    print(f"        Active goals: {len(self.goal_manager.active_goals)}\n")
                    
            except Exception as e:
                print(f"[Memory] Load error: {e}")
                print(f"[Memory] Starting fresh world\n")
    
    def save_memory(self):
        """Persist memory including personality profile"""
        try:
            # Convert Q-table
            q_table_serializable = {}
            for context in self.rl_system.q_table:
                # PATCH 5: Ensure Q-table Action Keys Serialize as Strings
                q_table_serializable[context] = {}
                for action, q_value in self.rl_system.q_table[context].items():
                    q_table_serializable[context][str(action)] = float(q_value)
            
            data = {
                "total_actions": dict(self.long_term_memory["total_actions"]),
                "successful_strategies": dict(self.long_term_memory["successful_strategies"]),
                "world_observations": self.long_term_memory["world_observations"][-50:],
                "reflections": self.long_term_memory["reflections"][-20:],
                "knowledge_gained": self.long_term_memory["knowledge_gained"][-100:],
                "cells_explored": self.long_term_memory["cells_explored"][-50:],
                "learned_topics": dict(self.learned_topics),
                "q_table": q_table_serializable,
                "learning_stats": self.rl_system.get_learning_stats(),
                "position": {
                    "x": self.position_x,
                    "y": self.position_y,
                    "cells_discovered": self.cells_discovered
                },
                "inventory": {r.value: count for r, count in self.inventory.items()},
                "grid_world": self.environment.grid_world.to_dict(),
                "goal_system": self.goal_manager.to_dict(),
                "self_model": self.self_model.to_dict(),
                "personality_profile": self.personality.to_dict(),  # SAVE PERSONALITY
                
                # PATCH 4 (Part 1)
                "intrinsic_rewards": getattr(self, "intrinsic_rewards", []),
                
                "last_saved": datetime.now().isoformat()
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[Memory] Save error: {e}")
    
    # ========================================
    # SPATIAL PERCEPTION
    # ========================================
    
    def perceive_world(self):
        """Observe world including spatial surroundings"""
        world_state = self.environment.get_state()
        current_cell = self.environment.grid_world.get_cell(self.position_x, self.position_y)
        
        # Discover current cell
        if not current_cell.discovered:
            current_cell.discovered = True
            self.cells_discovered += 1
            world_state["events"].append(f"🗺   Discovered new terrain: {current_cell.terrain.value}!")
            
            self.long_term_memory["cells_explored"].append({
                "cycle": self.cycles_alive,
                "x": self.position_x,
                "y": self.position_y,
                "terrain": current_cell.terrain.value
            })
        
        current_cell.visit_count += 1
        
        # Count nearby resources
        neighbors = self.environment.grid_world.get_neighbors(self.position_x, self.position_y)
        nearby_resources = sum(len(cell.resources) for cell in neighbors.values())
        
        # Build spatial context for RL
        spatial_context = {
            "terrain": current_cell.terrain.value,
            "terrain_type": current_cell.terrain,                   # NEW
            "position": (self.position_x, self.position_y),         # NEW

            # Neighbor terrain map
            "neighbors": {
                direction: cell.terrain.value
                for direction, cell in neighbors.items()
            },

            "nearby_resources": nearby_resources,
            "resources_here": len(current_cell.resources),
            "hazard_level": self.environment.get_hazard_level(),
        }
        
        # Record observation
        observation = {
            "cycle": self.cycles_alive,
            "world_state": world_state,
            "spatial_state": {
                "position": (self.position_x, self.position_y),
                "terrain": current_cell.terrain.value,
                "resources": len(current_cell.resources)
            },
            "internal_state": {
                "energy": self.energy,
                "knowledge": self.knowledge,
                "happiness": self.happiness,
                "focus": self.focus
            }
        }
        
        self.short_term_memory.append(observation)
        
        if world_state["events"]:
            for event in world_state["events"]:
                self.long_term_memory["world_observations"].append({
                    "cycle": self.cycles_alive,
                    "event": event
                })
        
        return world_state, spatial_context
    
    def get_current_cell(self):
        """Return the grid cell the agent is currently standing on."""
        return self.environment.grid_world.get_cell(self.position_x, self.position_y)

    def get_internal_state(self):
        """Get internal state for RL"""
        return {
            "energy": self.energy,
            "knowledge": self.knowledge,
            "happiness": self.happiness,
            "focus": self.focus,
            "curiosity": self.motivation_levels[MotivationType.CURIOSITY],
            "boredom": self.motivation_levels[MotivationType.BOREDOM]
        }
    
    def get_spatial_state(self):
        """Get spatial state for goal system"""
        return {
            "cells_discovered": self.cells_discovered,
            "inventory": {r.value: count for r, count in self.inventory.items()}
        }
    
    # ========================================
    # MOTIVATION (Enhanced with Personality Influence)
    # ========================================
    
    def update_motivations(self, world_state, spatial_context):
        """Update motivations including spatial exploration drive"""
        # SURVIVAL
        if self.energy < 20:
            self.motivation_levels[MotivationType.SURVIVAL] = 0.9
            self.motivation_levels[MotivationType.REST] = 0.95
        elif self.energy < 40:
            self.motivation_levels[MotivationType.SURVIVAL] = 0.4
            self.motivation_levels[MotivationType.REST] = 0.6
        else:
            self.motivation_levels[MotivationType.SURVIVAL] = 0.0
            self.motivation_levels[MotivationType.REST] = max(0.0, (100 - self.energy) / 150)
        
        # CURIOSITY
        knowledge_hunger = max(0.0, (50 - self.knowledge) / 50)
        if world_state["weather"] == Weather.SUNNY.value and self.energy > 50:
            self.motivation_levels[MotivationType.CURIOSITY] = min(0.9, knowledge_hunger + 0.3)
        else:
            self.motivation_levels[MotivationType.CURIOSITY] = knowledge_hunger * 0.5
        
        # LEARNING
        if self.focus > 60 and self.energy > 40:
            self.motivation_levels[MotivationType.LEARNING] = 0.7
        else:
            self.motivation_levels[MotivationType.LEARNING] = 0.3
        
        # EXPLORATION
        total_cells = self.environment.grid_world.width * self.environment.grid_world.height
        exploration_ratio = self.cells_discovered / total_cells
        
        if exploration_ratio < 0.3:
            self.motivation_levels[MotivationType.EXPLORATION] = 0.8
        elif exploration_ratio < 0.7:
            self.motivation_levels[MotivationType.EXPLORATION] = 0.5
        else:
            self.motivation_levels[MotivationType.EXPLORATION] = 0.2
        
        # Boost exploration if resources nearby
        if spatial_context.get("nearby_resources", 0) > 0:
            self.motivation_levels[MotivationType.EXPLORATION] = min(0.9, 
                self.motivation_levels[MotivationType.EXPLORATION] + 0.3)
        
        # BOREDOM
        cycles_since_variety = min(10, self.cycles_alive - self.last_study)
        self.motivation_levels[MotivationType.BOREDOM] = min(0.8, cycles_since_variety / 15.0)
        
        # SOCIAL
        if world_state["weather"] == Weather.SUNNY.value:
            self.motivation_levels[MotivationType.SOCIAL] = min(0.7, self.social_need / 100.0)
        else:
            self.motivation_levels[MotivationType.SOCIAL] = min(0.4, self.social_need / 150.0)
        
        # MAINTENANCE
        cycles_since_reflection = self.cycles_alive - self.last_reflection
        if cycles_since_reflection > 10:
            self.motivation_levels[MotivationType.MAINTENANCE] = min(0.8, cycles_since_reflection / 15.0)
        else:
            self.motivation_levels[MotivationType.MAINTENANCE] = 0.1
        
        # APPLY PERSONALITY INFLUENCE TO MOTIVATIONS
        self.apply_personality_to_motivations()
    
    def decide_action(self, world_state, spatial_context):
        """Choose action using RL with spatial context and self-model biases"""
        agent_state = self.get_internal_state()
        context = self.rl_system.get_context(agent_state, world_state, spatial_context)
        
        # All available actions
        available_actions = list(Action)
        
        # Get Q-values or scores for all actions
        action_scores = {}
        for action in available_actions:
            # Get base Q-value from RL system
            score = self.rl_system.q_table[context].get(action.value, 0.0)
            
            # ===== PATCH A: ADD BIASES USING SELF-MODEL INSIGHTS =====
            
            # Avoid studying when energy < 40
            if action == Action.STUDY and self.energy < 40:
                score -= 3.0
            
            # Avoid repeating the same action if repetition index > 0.4
            if self.previous_action is not None and self.self_model.action_repetition_index > 0.4:
                if action.value == self.previous_action.value:
                    score -= 2.5
            
            # Prefer movement when novelty is low
            if action.name.startswith("MOVE"):
                recent = list(self.self_model.novelty_history)[-5:]
                if recent:
                    novelty_avg = sum(recent) / len(recent)
                else:
                    novelty_avg = 0.0
                score += novelty_avg * 2.0
            
            # Prefer favorable terrains from self_model
            current_terrain = self.environment.grid_world.get_cell(self.position_x, self.position_y).terrain.value
            if current_terrain in self.self_model.terrain_preferences:
                if self.self_model.terrain_preferences[current_terrain] == "favorable":
                    score += 1.5
                elif self.self_model.terrain_preferences[current_terrain] == "unfavorable":
                    score -= 2.0
            
            # PATCH 1: Add Fatigue-Avoidance Bias (Missing part of PATCH A)
            # Avoid actions that historically contribute to fatigue
            if action in [Action.EXERCISE, Action.EXPLORE] and self.self_model.fatigue_cause_score > 0.6:
                score -= 2.0

            # PATCH 2: Add Environment Sensitivity Penalty (Missing part of PATCH B)
            # Penalize actions during unfavourable environmental conditions
            if self.self_model.environment_sensitivity > 0.5:
                if world_state.get("weather") != "sunny":
                    score -= 1.5
                if spatial_context.get("hazard_level", 0) > 0:
                    score -= self.self_model.environment_sensitivity * 2
            
            action_scores[action] = score
        
        # Choose action with highest score (with epsilon-greedy exploration)
        if random.random() < self.rl_system.epsilon:
            chosen_action = random.choice(available_actions)
        else:
            chosen_action = max(action_scores.items(), key=lambda x: x[1])[0]
        
        # Store for reward calculation
        self.previous_context = context
        self.previous_action = chosen_action
        self.previous_state = agent_state.copy()
        
        return chosen_action
    
    # ========================================
    # ACTIONS (Complete Implementation)
    # ========================================
    
    def execute_action(self, action, world_state, spatial_context):
        """Execute action with spatial awareness"""
        effects = {}
        success = True
        message = ""
        spatial_bonus = 0.0
        
        current_cell = self.environment.grid_world.get_cell(self.position_x, self.position_y)
        terrain_effects = current_cell.get_terrain_effects()
        
        # ===== MOVEMENT ACTIONS =====
        if action in [Action.MOVE_NORTH, Action.MOVE_SOUTH, Action.MOVE_EAST, Action.MOVE_WEST]:
            if self.energy < 10:
                success = False
                effects = {"energy": 0}
                message = "Too exhausted to move"
            else:
                # Determine new position
                new_x, new_y = self.position_x, self.position_y
                
                if action == Action.MOVE_NORTH:
                    new_y -= 1
                    direction_name = "north"
                elif action == Action.MOVE_SOUTH:
                    new_y += 1
                    direction_name = "south"
                elif action == Action.MOVE_EAST:
                    new_x += 1
                    direction_name = "east"
                else:  # WEST
                    new_x -= 1
                    direction_name = "west"
                
                # Check if valid
                if self.environment.grid_world.is_valid_position(new_x, new_y):
                    target_cell = self.environment.grid_world.get_cell(new_x, new_y)
                    
                    # Move with terrain cost
                    terrain_cost = abs(terrain_effects["energy"])
                    hazard_cost = self.environment.get_hazard_level() * 2
                    total_cost = terrain_cost + hazard_cost
                    
                    self.energy -= total_cost
                    self.focus += terrain_effects["focus"]
                    
                    # Discovery bonus
                    if not target_cell.discovered:
                        spatial_bonus = 5.0
                        self.happiness += 10
                    
                    self.position_x, self.position_y = new_x, new_y
                    
                    effects = {
                        "energy": -total_cost,
                        "focus": terrain_effects["focus"],
                        "happiness": 10 if not target_cell.discovered else 2
                    }
                    
                    message = f"Traveled {direction_name} to ({new_x}, {new_y}). {terrain_effects['description']}"
                    
                else:
                    success = False
                    effects = {"energy": 0}
                    message = f"Cannot move {direction_name} - blocked by world boundary"
        
        # ===== EXPLORE =====
        elif action == Action.EXPLORE:
            if self.energy < 10:
                success = False
                effects = {"energy": 0}
                message = "Too tired to explore thoroughly"
            else:
                self.energy -= 8
                self.happiness += 8
                self.focus += 5
                
                # Check for resources in current cell
                if current_cell.resources:
                    resource = random.choice(current_cell.resources)
                    self.knowledge += 3
                    effects = {"energy": -8, "happiness": 8, "knowledge": 3, "focus": 5}
                    message = f"Explored the {current_cell.terrain.value} and noticed a {resource.value} nearby!"
                    spatial_bonus = 2.0
                else:
                    effects = {"energy": -8, "happiness": 8, "focus": 5}
                    message = f"Explored the {current_cell.terrain.value}. The landscape is fascinating."
        
        # ===== COLLECT RESOURCES =====
        elif action == Action.COLLECT:
            if self.energy < 5:
                success = False
                effects = {"energy": 0}
                message = "Too tired to gather resources"
            elif not current_cell.resources:
                success = False
                effects = {"energy": -2}
                message = "No resources to collect here"
            else:
                # Collect a random resource
                resource = random.choice(current_cell.resources)
                current_cell.collect_resource(resource)
                self.inventory[resource] += 1
                
                # Resource benefits
                if resource == ResourceType.FOOD:
                    self.energy += 15
                    self.happiness += 5
                    effects = {"energy": 10, "happiness": 5}
                    message = f"🍎 Collected {resource.value}! Consumed for energy restoration."
                
                elif resource == ResourceType.BOOK:
                    self.knowledge += 8
                    self.focus += 10
                    effects = {"energy": -5, "knowledge": 8, "focus": 10}
                    message = f"📖 Collected {resource.value}! Gained valuable knowledge."
                    spatial_bonus = 4.0
                
                elif resource == ResourceType.RELIC:
                    self.happiness += 12
                    self.knowledge += 5
                    effects = {"energy": -5, "happiness": 12, "knowledge": 5}
                    message = f"🏺 Collected ancient {resource.value}! A magnificent discovery."
                    spatial_bonus = 6.0
        
        # ===== REST =====
        elif action == Action.REST:
            energy_gain = 15 + random.randint(0, 10)
            focus_gain = 10 + random.randint(0, 5)
            
            # Terrain affects rest quality
            if current_cell.terrain == TerrainType.RIVER:
                energy_gain += 5
                message_suffix = " The sound of water is soothing."
            else:
                message_suffix = ""
            
            self.energy += energy_gain
            self.focus += focus_gain
            self.last_rest = self.cycles_alive
            
            effects = {"energy": energy_gain, "focus": focus_gain}
            message = f"Rested peacefully (+{energy_gain} energy, +{focus_gain} focus).{message_suffix}"
        
        # ===== STUDY =====
        elif action == Action.STUDY:
            if self.energy < 8:
                success = False
                effects = {"energy": 0}
                message = "Too tired to concentrate on studying"
            else:
                # Study effectiveness depends on focus
                effectiveness = min(1.0, self.focus / 100.0)
                knowledge_gain = int(10 * effectiveness) + random.randint(0, 5)
                
                category, topic = self.environment.get_random_knowledge()
                self.learned_topics[category] += 1
                
                self.knowledge += knowledge_gain
                self.energy -= 8
                self.focus -= 5
                self.last_study = self.cycles_alive
                
                effects = {"knowledge": knowledge_gain, "energy": -8, "focus": -5}
                message = f"Studied {category}: {topic}. Gained {knowledge_gain} knowledge."
                
                self.long_term_memory["knowledge_gained"].append({
                    "cycle": self.cycles_alive,
                    "category": category,
                    "topic": topic,
                    "gain": knowledge_gain
                })
        
        # ===== REFLECT =====
        elif action == Action.REFLECT:
            if self.energy < 5:
                success = False
                effects = {"energy": 0}
                message = "Too tired for deep reflection"
            else:
                # Reflection with personality mutation AND self-model introspection
                reflection_text, personality_mutations, introspective_summary = self.self_reflect_from_memory()
                
                focus_gain = 15
                happiness_gain = 10
                
                self.focus += focus_gain
                # Happiness boost influenced by optimism
                happiness_bonus = self.apply_optimism_to_happiness_recovery(happiness_gain)
                self.happiness += happiness_bonus
                self.energy -= 5
                self.last_reflection = self.cycles_alive
                
                effects = {"focus": focus_gain, "happiness": happiness_bonus, "energy": -5}
                message = f"💭 Reflected deeply. {reflection_text[:80]}..."
                
                # Display personality mutations if significant
                if personality_mutations:
                    mut_summary = ", ".join([f"{k}: {v}" for k, v in list(personality_mutations.items())[:2]])
                    message += f"\n   🧩 Personality shift → {mut_summary}"
                
                # Display self-model insights
                if introspective_summary:
                    print("\n" + introspective_summary)
        
        # ===== SOCIALIZE =====
        elif action == Action.SOCIALIZE:
            if self.energy < 6:
                success = False
                effects = {"energy": 0}
                message = "Too tired to socialize"
            else:
                # Social interaction (imaginary for now)
                happiness_gain = 12 + random.randint(0, 8)
                knowledge_gain = random.randint(0, 3)
                
                # Social affinity boosts effectiveness
                social_bonus = int((self.personality.social_affinity - 0.5) * 10)
                happiness_gain += social_bonus
                
                self.happiness += happiness_gain
                self.knowledge += knowledge_gain
                self.social_need = max(0, self.social_need - 30)
                self.energy -= 6
                
                effects = {"happiness": happiness_gain, "knowledge": knowledge_gain, "energy": -6}
                message = f"Socialized with travelers. Gained {happiness_gain} happiness and {knowledge_gain} knowledge."
        
        # ===== OBSERVE =====
        elif action == Action.OBSERVE:
            if self.energy < 3:
                success = False
                effects = {"energy": 0}
                message = "Too tired to observe carefully"
            else:
                focus_gain = 8
                knowledge_gain = 3
                
                self.focus += focus_gain
                self.knowledge += knowledge_gain
                self.energy -= 3
                
                effects = {"focus": focus_gain, "knowledge": knowledge_gain, "energy": -3}
                
                # Observation based on terrain
                if current_cell.terrain == TerrainType.RUINS:
                    message = "🔍 Observed ancient ruins. Noticed intricate architectural patterns."
                elif current_cell.terrain == TerrainType.FOREST:
                    message = "🔍 Observed the forest. Identified various plant species."
                else:
                    message = f"🔍 Observed the {current_cell.terrain.value}. Gained new insights."
        
        # ===== EXERCISE =====
        elif action == Action.EXERCISE:
            if self.energy < 15:
                success = False
                effects = {"energy": 0}
                message = "Too low on energy to exercise"
            else:
                happiness_gain = 8
                focus_gain = 5
                
                self.happiness += happiness_gain
                self.focus += focus_gain
                self.energy -= 12
                
                effects = {"happiness": happiness_gain, "focus": focus_gain, "energy": -12}
                message = "💪 Exercised vigorously. Feeling refreshed and focused."
        
        # Apply effects to state
        for stat, delta in effects.items():
            if stat == "energy":
                self.energy = max(0, min(100, self.energy))
            elif stat == "knowledge":
                self.knowledge = max(0, self.knowledge)
            elif stat == "happiness":
                self.happiness = max(0, min(100, self.happiness))
            elif stat == "focus":
                self.focus = max(0, min(100, self.focus))
        
        # Record action
        self.long_term_memory["total_actions"][action.value] += 1
        
        return ActionResult(action, success, effects, message), spatial_bonus
    
    # ========================================
    # MAIN AGENT LOOP
    # ========================================
    
    def run_cycle(self):
        """Execute one full Phase-6 cognitive–behavioral cycle."""

        # ============================================================
        # 0. TIME & COUNTERS
        # ============================================================
        self.cycles_alive += 1
        self.environment.advance_time()

        # ============================================================
        # 1. PERCEPTION
        # ============================================================
        world_state, spatial_context = self.perceive_world()

        # ============================================================
        # 2. MOTIVATION UPDATE
        # ============================================================
        self.update_motivations(world_state, spatial_context)

        # ============================================================
        # 3. INTENTION ENGINE (symbolic)
        # ============================================================
        self.current_intention = self.intent_engine.evaluate(
            self,
            self.environment.grid_world,     # ✔ correct world
            spatial_context
        )

        intention_action = self.intent_engine.suggest_action(
            self.current_intention,
            self,
            self.environment.grid_world,     # ✔ correct world
            spatial_context
        )

        self.intent_engine.debug_dashboard()

        # ============================================================
        # 4. GLOBAL PLANNER (BFS strategic)
        # ============================================================
        planner_output = self.global_planner.get_strategic_action(
            self,
            world_state
        )
        # planner_output can be:
        #   None
        #   "rest"
        #   { "action": "move_to_route", "next_step": "...", ... }

        # ============================================================
        # 5. GOAL MANAGER
        # ============================================================
        agent_state = self.get_internal_state()
        spatial_state = self.get_spatial_state()

        if self.goal_manager.should_create_goals(self.cycles_alive):
            new_goals = self.goal_manager.create_goals(
                agent_state, world_state, spatial_state,
                self.motivation_levels, self.cycles_alive
            )
            if new_goals:
                for goal in new_goals:
                    print(f"🎯 New Goal: {goal.description}")

        self.goal_manager.update_goal_progress(agent_state, spatial_state)
        completed, failed, goal_bonus = self.goal_manager.evaluate_goals(self.cycles_alive)

        if completed:
            for goal in completed:
                print(f"✅ Goal Completed: {goal.description} (+{goal.reward_bonus:.1f})")

        if failed:
            for goal in failed:
                print(f"❌ Goal Failed: {goal.description}")
                happiness_loss = 5 * (1.0 - self.personality.optimism)
                self.happiness = max(0, self.happiness - happiness_loss)

        # ============================================================
        # 6. RL ACTION CHOICE
        # ============================================================
        rl_action = self.decide_action(world_state, spatial_context)

        # ============================================================
        # 7. ARBITRATION (Phase-6 priority)
        # ===============================================================
        # 7a. Highest: BFS route packet
        if isinstance(planner_output, dict) and planner_output.get("action") == "move_to_route":
            proposed_action_name = planner_output["next_step"]

        # 7b. Direct planner command
        elif isinstance(planner_output, str):
            proposed_action_name = planner_output

        # 7c. Intention engine suggestion
        elif intention_action:
            proposed_action_name = intention_action

        # 7d. Final fallback → RL
        else:
            proposed_action_name = rl_action.value

        # Convert string → Action enum safely
        try:
            proposed_action = Action[proposed_action_name.upper()]
        except KeyError:
            proposed_action = rl_action

        # ============================================================
        # 8. META-CONTROLLER (FINAL SAFETY OVERRIDE)
        # ============================================================
        final_value, reason = self.meta_controller.evaluate(
            agent=self,
            proposed_action=proposed_action.value,  # pass lowercase string
            planner_output=planner_output,
            self_model=self.self_model
        )

        self.last_override_reason = reason

        # Convert final_value → Action enum
        try:
            action = Action[final_value.upper()]
        except KeyError:
            action = proposed_action

        if final_value != proposed_action.value:
            print(f"⚠️ Meta-Controller Override → {final_value} ({reason})")

        # ============================================================
        # 9. EXECUTE ACTION
        # ============================================================
        result, spatial_bonus = self.execute_action(
            action,
            world_state,
            spatial_context
        )

        # ============================================================
        # 10. SELF-MODEL UPDATE
        # ============================================================
        self.self_model.record_state(self)
        self.self_model.analyze_cause_effect()

        # ============================================================
        # 11. REWARD + Q-LEARNING
        # ============================================================
        reward = self.rl_system.calculate_reward(
            result.effects,
            self.previous_state,
            self.get_internal_state(),
            spatial_bonus=spatial_bonus,
            goal_bonus=goal_bonus
        )

        intrinsic_bonus = 0.0
        if self.self_model.novelty_history:
            intrinsic_bonus += self.self_model.novelty_history[-1] * 2.0
        intrinsic_bonus -= self.self_model.action_repetition_index * 0.8
        if self.self_model.action_repetition_index > 0.4:
            intrinsic_bonus += 1.2
        if self.energy < 35:
            intrinsic_bonus -= 0.5
        if self.previous_action:
            intrinsic_bonus += self.self_model.get_positive_pattern_reward(self.previous_action)

        reward += intrinsic_bonus

        if not hasattr(self, "intrinsic_rewards"):
            self.intrinsic_rewards = []
        self.intrinsic_rewards.append({
            "cycle": self.cycles_alive,
            "intrinsic_bonus": intrinsic_bonus
        })

        if self.previous_context and self.previous_action:
            self.rl_system.update_q_value(self.previous_context, self.previous_action, reward)
            self.rl_system.record_experience(self.previous_context, self.previous_action, reward)

        # ============================================================
        # 12. DISPLAY + PERIODIC SAVES
        # ============================================================
        self.display_status(world_state, action, result, reward)

        if self.cycles_alive % 10 == 0:
            self.personality.display_summary()
            print("\n" + self.self_model.get_self_awareness_summary())

        self.personality.cycles_since_activity += 1
        if self.personality.cycles_since_activity > 100:
            self.personality.decay_toward_neutral(decay_rate=0.005)
            self.personality.cycles_since_activity = 0

        if self.cycles_alive % 5 == 0:
            self.save_memory()

        self.environment.clear_events()


    
    def display_status(self, world_state, action, result, reward):
        """Display current cycle status"""
        print(f"\n{'='*70}")
        print(f"⏰ Cycle {self.cycles_alive} | {world_state['time'].title()} | {world_state['weather'].title()}")
        print(f"📍 Position: ({self.position_x}, {self.position_y}) | Explored: {self.cells_discovered}/25")
        print(f"{'='*70}")
        
        # Internal state
        print(f"💚 Energy: {self.energy:.1f}/100 | 🧠 Knowledge: {self.knowledge:.1f} | 😊 Happiness: {self.happiness:.1f}/100 | 🎯 Focus: {self.focus:.1f}/100")
        
        # Inventory
        inv_str = " | ".join([f"{r.value}: {count}" for r, count in self.inventory.items() if count > 0])
        if inv_str:
            print(f"🎒 Inventory: {inv_str}")
        
        # Top motivations
        top_motivations = sorted(self.motivation_levels.items(), key=lambda x: x[1], reverse=True)[:3]
        mot_str = ", ".join([f"{m.value}: {v:.2f}" for m, v in top_motivations])
        print(f"💭 Motivations: {mot_str}")
        
        # Active goals
        active_goals_display = self.goal_manager.get_active_goals_display()
        if active_goals_display:
            print(f"\n🎯 Active Goals:")
            for goal_info in active_goals_display:
                print(f"   • {goal_info['description']} {goal_info['progress']} [{goal_info['priority']}]")
        
        # Action and result
        print(f"\n🎬 Action: {action.value.replace('_', ' ').title()}")
        print(f"{'✅' if result.success else '❌'} {result.message}")
        print(f"🏆 Reward: {reward:.2f}")
        
        # Learning stats
        stats = self.rl_system.get_learning_stats()
        print(f"📊 Avg Reward: {stats['avg_reward']:.2f} | Contexts Learned: {stats['contexts_learned']}")
        
        print(f"{'='*70}\n")
    
    def run_simulation(self, cycles=50):
        """Run the agent for N cycles"""
        print(f"\n🤖 Starting {self.name}'s Journey - Cognitive Drift Enabled")
        print(f"{'='*70}\n")
        
        # Display initial personality
        self.personality.display_summary()
        
        # Show initial world map
        self.environment.grid_world.render_ascii(self.position_x, self.position_y)
        
        try:
            for _ in range(cycles):
                self.run_cycle()
                time.sleep(0.1)  # Brief pause for readability
                
                # Death condition
                if self.energy <= 0:
                    print("\n💀 Energy depleted. Journey ended.")
                    break
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Simulation interrupted by user")
        
        finally:
            # Final summary
            self.display_final_summary()
            self.save_memory()
            print(f"\n💾 Memory saved to {self.memory_file}")
    
    def display_final_summary(self):
        """Display comprehensive summary at end"""
        print(f"\n{'='*70}")
        print(f"📋 FINAL SUMMARY - {self.name}'s Journey")
        print(f"{'='*70}\n")
        
        print(f"⏰ Cycles Survived: {self.cycles_alive}")
        print(f"📍 Final Position: ({self.position_x}, {self.position_y})")
        print(f"🗺️   Cells Explored: {self.cells_discovered}/25")
        print(f"🧠 Total Knowledge: {self.knowledge:.1f}")
        print(f"😊 Final Happiness: {self.happiness:.1f}/100")
        print(f"💚 Final Energy: {self.energy:.1f}/100\n")
        
        # Inventory summary
        print("🎒 Final Inventory:")
        for resource, count in self.inventory.items():
            if count > 0:
                print(f"   • {resource.value}: {count}")
        
        # Goal statistics
        goal_stats = self.goal_manager.get_goal_statistics()
        print(f"\n🎯 Goal Statistics:")
        print(f"   • Total Created: {goal_stats['total_created']}")
        print(f"   • Completed: {goal_stats['completed']}")
        print(f"   • Failed: {goal_stats['failed']}")
        print(f"   • Success Rate: {goal_stats['success_rate']:.1f}%")
        
        # Learning summary
        print(f"\n📊 Learning Summary:")
        top_actions = self.rl_system.get_best_actions(top_n=5)
        print("   Top Learned Actions:")
        for context, action, q_value in top_actions[:3]:
            print(f"   • {action} in {context}: Q={q_value:.2f}")
        
        # Knowledge expertise
        if self.learned_topics:
            print(f"\n📚 Knowledge Expertise:")
            top_topics = sorted(self.learned_topics.items(), key=lambda x: x[1], reverse=True)[:5]
            for topic, count in top_topics:
                print(f"   • {topic}: studied {count} times")
        
        # Self-Model Final Analysis
        print(f"\n🧠 SELF-MODEL FINAL ANALYSIS:")
        print(self.self_model.get_self_awareness_summary())
        
        # Self-narrative
        narrative = self.self_model.generate_self_narrative()
        print(f"\n📖 Final Self-Narrative:")
        print(f'   "{narrative}"')
        print()
        
        # Final personality state
        print(f"\n🧬 FINAL PERSONALITY PROFILE:")
        self.personality.display_summary()
        
        # Personality evolution
        if len(self.personality.trait_history) > 1:
            initial = self.personality.trait_history[0]
            final = self.personality.trait_history[-1]
            
            print("📈 Personality Evolution:")
            for trait in ["optimism", "discipline", "curiosity_bias", "risk_tolerance", "social_affinity"]:
                delta = final[trait] - initial[trait]
                arrow = "↑" if delta > 0.05 else ("↓" if delta < -0.05 else "→")
                print(f"   • {trait}: {initial[trait]:.2f} → {final[trait]:.2f} {arrow} ({delta:+.2f})")
        
        print(f"\n{'='*70}\n")