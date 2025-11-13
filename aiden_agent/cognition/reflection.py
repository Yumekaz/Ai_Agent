"""
Metacognitive reflection system
"""

import random
from collections import defaultdict
from aiden_agent.cognition.motivation import MotivationType


class ReflectionSystem:
    """
    Handles metacognitive self-reflection and analysis
    """
    
    @staticmethod
    def self_reflect_from_memory(long_term_memory, rl_system, goal_manager, learned_topics, cycles_alive, personality):
        """
        Analyze long_term_memory and RL data to generate introspective reflections
        NOW ALSO MUTATES PERSONALITY based on insights
        
        Returns: (reflection_string, personality_mutations)
        """
        reflection_parts = []
        
        # ===== 1. ACTION PATTERN ANALYSIS =====
        total_actions = long_term_memory["total_actions"]
        
        if total_actions:
            # Find most and least used actions
            sorted_actions = sorted(total_actions.items(), key=lambda x: x[1], reverse=True)
            most_used = sorted_actions[0] if sorted_actions else None
            least_used = sorted_actions[-1] if len(sorted_actions) > 1 else None
            
            total_count = sum(total_actions.values())
            
            # Check for over-reliance on certain actions
            if most_used and most_used[1] / total_count > 0.3:
                action_name = most_used[0].replace("_", " ")
                if most_used[0] == "rest":
                    reflection_parts.append(f"I notice I've been resting frequently — perhaps I'm avoiding challenges, or simply exhausted from my journey.")
                elif most_used[0] == "study":
                    reflection_parts.append(f"My mind craves knowledge — studying has become my primary pursuit.")
                elif most_used[0] in ["move_north", "move_south", "move_east", "move_west"]:
                    reflection_parts.append(f"I've been wandering constantly, driven by an insatiable urge to explore.")
                else:
                    reflection_parts.append(f"I find myself drawn repeatedly to {action_name}.")
            
            # Check for neglected actions
            if least_used and least_used[1] < total_count * 0.05 and total_count > 20:
                neglected_action = least_used[0].replace("_", " ")
                if least_used[0] == "socialize":
                    reflection_parts.append(f"I've become isolated, rarely connecting with others.")
                elif least_used[0] == "reflect":
                    reflection_parts.append(f"I've been too focused on action — reflection has suffered.")
                else:
                    reflection_parts.append(f"I rarely engage in {neglected_action} anymore.")
        
        # ===== 2. REWARD AND LEARNING ANALYSIS =====
        action_rewards = rl_system.action_rewards
        
        if action_rewards and len(action_rewards) > 1:
            # Find best and worst performing actions
            avg_rewards = {}
            for action_name, rewards in action_rewards.items():
                if rewards and len(rewards) >= 3:
                    avg_rewards[action_name] = sum(rewards) / len(rewards)
            
            if avg_rewards:
                best_action = max(avg_rewards.items(), key=lambda x: x[1])
                worst_action = min(avg_rewards.items(), key=lambda x: x[1])
                
                # Compare best vs worst
                if best_action[1] > worst_action[1] + 2.0:
                    best_name = best_action[0].replace("_", " ")
                    worst_name = worst_action[0].replace("_", " ")
                    
                    if "explore" in best_action[0] or "move" in best_action[0]:
                        reflection_parts.append(f"Exploration brings me far more reward than {worst_name} — the unknown calls to me.")
                    elif "study" in best_action[0]:
                        reflection_parts.append(f"Learning yields higher rewards than {worst_name} — knowledge is its own treasure.")
                    elif "collect" in best_action[0]:
                        reflection_parts.append(f"Gathering resources proves more fruitful than {worst_name}.")
                    else:
                        reflection_parts.append(f"I've learned that {best_name} serves me better than {worst_name}.")
        
        # ===== 3. TEMPORAL LEARNING TREND =====
        reward_trend = "stable"
        if len(rl_system.total_rewards) >= 20:
            recent_10 = list(rl_system.total_rewards)[-10:]
            older_10 = list(rl_system.total_rewards)[-20:-10]
            
            recent_avg = sum(recent_10) / len(recent_10)
            older_avg = sum(older_10) / len(older_10)
            
            improvement = recent_avg - older_avg
            
            if improvement > 1.0:
                reflection_parts.append(f"My strategies have improved — recent rewards average {improvement:.1f} points higher.")
                reward_trend = "improving"
            elif improvement < -1.0:
                reflection_parts.append(f"My performance has declined recently — I need to reconsider my approach.")
                reward_trend = "declining"
        
        # ===== 4. GOAL PERFORMANCE ANALYSIS =====
        goal_stats = goal_manager.get_goal_statistics()
        failure_count = goal_stats["failed"]
        success_count = goal_stats["completed"]
        
        if goal_stats["total_created"] > 0:
            success_rate = goal_stats["success_rate"]
            
            if success_rate > 70:
                reflection_parts.append(f"I complete most goals I set — my planning and execution are effective.")
            elif success_rate < 30:
                reflection_parts.append(f"Too many goals slip through my grasp — I aim too high or lose focus.")
            
            # Analyze goal types
            failed_goals = goal_manager.failed_goals
            completed_goals = goal_manager.completed_goals
            
            if failed_goals:
                failed_types = defaultdict(int)
                for goal in failed_goals[-5:]:  # Last 5 failures
                    failed_types[goal.goal_type] += 1
                
                if failed_types:
                    most_failed_type = max(failed_types.items(), key=lambda x: x[1])
                    
                    if most_failed_type[0] == "collect_relics":
                        reflection_parts.append(f"Relic-hunting eludes me — these ancient treasures are harder to find than I expected.")
                    elif most_failed_type[0] == "explore_tiles":
                        reflection_parts.append(f"My exploration goals often fail — perhaps I'm too cautious or easily distracted.")
                    elif most_failed_type[0] == "knowledge_gain":
                        reflection_parts.append(f"Knowledge accumulation proves difficult — my focus wavers when I try to learn too quickly.")
            
            if completed_goals:
                completed_types = defaultdict(int)
                for goal in completed_goals[-5:]:  # Last 5 completions
                    completed_types[goal.goal_type] += 1
                
                if completed_types:
                    most_completed_type = max(completed_types.items(), key=lambda x: x[1])
                    
                    if most_completed_type[0] == "collect_books":
                        reflection_parts.append(f"Books come naturally to me — I excel at gathering written knowledge.")
                    elif most_completed_type[0] == "energy_level":
                        reflection_parts.append(f"I'm good at maintaining my energy — survival instincts serve me well.")
        
        # ===== 5. KNOWLEDGE AND EXPERTISE =====
        if learned_topics:
            top_topic = max(learned_topics.items(), key=lambda x: x[1])
            total_topics = len(learned_topics)
            
            if top_topic[1] >= 3:
                reflection_parts.append(f"I've developed expertise in {top_topic[0]} — studied it {top_topic[1]} times across my journey.")
            
            if total_topics >= 8:
                reflection_parts.append(f"My knowledge spans {total_topics} different subjects — I'm becoming a polymath.")
        
        # ===== ASSEMBLE FINAL REFLECTION =====
        if not reflection_parts:
            reflection_text = "I continue my journey, learning and adapting with each passing moment."
        else:
            # Select 2-4 most interesting insights
            selected = reflection_parts[:4] if len(reflection_parts) <= 4 else random.sample(reflection_parts, min(4, len(reflection_parts)))
            reflection_text = " ".join(selected)
        
        # ===== COGNITIVE DRIFT: PERSONALITY MUTATION =====
        # This needs to be done by calling the personality's method
        # Return the data needed for mutation
        return reflection_text, reward_trend, failure_count, success_count