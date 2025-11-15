"""
Self-Modeling Layer for metacognitive self-awareness
Tracks internal state history and analyzes cause-effect patterns
"""


from collections import deque, defaultdict



class SelfModel:
    """
    Self-modeling system that tracks agent's internal states and discovers
    cause-effect relationships between states, actions, and outcomes
    """
    def __init__(self, history_size=50):
        self.history_size = history_size
        
        # State tracking
        self.state_history = deque(maxlen=history_size)
        self.action_history = deque(maxlen=history_size)
        self.emotion_history = deque(maxlen=history_size)
        self.terrain_reward_history = defaultdict(list)
        
        # Cause-effect memory: list of pattern dictionaries
        self.cause_effect_memory = []
        
        # Self-awareness metrics
        self.fatigue_cause_score = 0.0
        self.environment_sensitivity = 0.5
        self.habit_strength = {}
        
        # Pattern detection
        self.detected_patterns = []
        self.terrain_preferences = {}
        self.motivation_trends = defaultdict(list)
        
        # Novelty and repetition tracking (PATCH)
        self.tile_visit_count = defaultdict(int)
        self.novelty_history = deque(maxlen=50)
        self.repetition_tracker = deque(maxlen=10)
        self.action_repetition_index = 0.0
        
    def record_state(self, agent):
        """
        Capture comprehensive snapshot of agent's current state
        Called every cycle
        """
        try:
            # Get current cell terrain
            current_cell = agent.environment.grid_world.get_cell(agent.position_x, agent.position_y)
            terrain = current_cell.terrain.value if current_cell else "unknown"
            
            # Build state snapshot
            state_snapshot = {
                "cycle": agent.cycles_alive,
                "energy": agent.energy,
                "happiness": agent.happiness,
                "focus": agent.focus,
                "knowledge": agent.knowledge,
                "social_need": agent.social_need,
                "terrain": terrain,
                "position": (agent.position_x, agent.position_y),
                "weather": agent.environment.weather.value,
                "motivations": {k.value: v for k, v in agent.motivation_levels.items()},
                "personality": {
                    "optimism": agent.personality.optimism,
                    "discipline": agent.personality.discipline,
                    "curiosity_bias": agent.personality.curiosity_bias,
                    "risk_tolerance": agent.personality.risk_tolerance,
                    "social_affinity": agent.personality.social_affinity
                }
            }
            
            # Record last action and reward if available
            if agent.previous_action:
                state_snapshot["last_action"] = agent.previous_action.value
                
            if agent.rl_system.total_rewards:
                state_snapshot["last_reward"] = agent.rl_system.total_rewards[-1]
            
            self.state_history.append(state_snapshot)
            
            # Track emotion state
            emotion_state = self._categorize_emotion(agent.happiness, agent.energy, agent.focus)
            self.emotion_history.append({
                "cycle": agent.cycles_alive,
                "emotion": emotion_state,
                "happiness": agent.happiness,
                "energy": agent.energy
            })
            
            # Track terrain rewards
            if "last_reward" in state_snapshot:
                self.terrain_reward_history[terrain].append(state_snapshot["last_reward"])
            
            # Track motivation trends
            for mot_type, value in agent.motivation_levels.items():
                self.motivation_trends[mot_type.value].append(value)
            
            # PATCH: Track tile visit frequency and novelty
            self.tile_visit_count[(agent.position_x, agent.position_y)] += 1
            
            # Novelty = 1 / visit_count
            novelty_score = 1.0 / self.tile_visit_count[(agent.position_x, agent.position_y)]
            self.novelty_history.append(novelty_score)
            
            # PATCH: Track action repetition
            self.repetition_tracker.append(state_snapshot.get("last_action"))
            if len(self.repetition_tracker) >= 4:
                last4 = list(self.repetition_tracker)[-4:]
                if len(set(last4)) == 1:
                    self.action_repetition_index = min(1.0, self.action_repetition_index + 0.1)
                
        except Exception as e:
            # Silently fail to avoid breaking simulation
            pass
    
    def _categorize_emotion(self, happiness, energy, focus):
        """Categorize emotional state based on metrics"""
        if happiness > 70 and energy > 60:
            return "thriving"
        elif happiness > 50 and energy > 40:
            return "content"
        elif energy < 30:
            return "exhausted"
        elif happiness < 30:
            return "distressed"
        elif focus > 70:
            return "focused"
        else:
            return "neutral"
    
    def analyze_cause_effect(self):
        """
        Analyze state history to detect cause-effect patterns
        Returns list of discovered patterns
        """
        if len(self.state_history) < 10:
            return []
        
        new_patterns = []
        
        # Pattern 1: Low energy → poor study rewards
        self._detect_energy_learning_pattern(new_patterns)
        
        # Pattern 2: Weather/terrain effects on exploration
        self._detect_terrain_patterns(new_patterns)
        
        # Pattern 3: Personality trait influence on actions
        self._detect_personality_action_patterns(new_patterns)
        
        # Pattern 4: Motivation-action correlations
        self._detect_motivation_patterns(new_patterns)
        
        # Pattern 5: Fatigue accumulation
        self._detect_fatigue_patterns(new_patterns)
        
        # Pattern 6: Happiness recovery patterns
        self._detect_emotion_recovery_patterns(new_patterns)
        
        # PATCH: Pattern 7: Action repetition loops
        self._detect_action_loops(new_patterns)
        
        # Update detected patterns
        for pattern in new_patterns:
            if pattern not in self.detected_patterns:
                self.detected_patterns.append(pattern)
                
                # Store in cause-effect memory
                self.cause_effect_memory.append({
                    "cycle": self.state_history[-1]["cycle"],
                    "pattern": pattern
                })
        
        return new_patterns
    
    def _detect_energy_learning_pattern(self, patterns):
        """Detect if low energy correlates with poor learning rewards"""
        try:
            low_energy_rewards = []
            high_energy_rewards = []
            
            for state in list(self.state_history)[-20:]:
                if "last_action" in state and "study" in state["last_action"]:
                    if state["energy"] < 30:
                        if "last_reward" in state:
                            low_energy_rewards.append(state["last_reward"])
                    elif state["energy"] > 60:
                        if "last_reward" in state:
                            high_energy_rewards.append(state["last_reward"])
            
            if len(low_energy_rewards) >= 3 and len(high_energy_rewards) >= 3:
                low_avg = sum(low_energy_rewards) / len(low_energy_rewards)
                high_avg = sum(high_energy_rewards) / len(high_energy_rewards)
                
                if high_avg > low_avg + 1.5:
                    patterns.append({
                        "type": "energy_learning",
                        "description": f"Low energy reduces study effectiveness by {(high_avg - low_avg):.1f} reward points",
                        "condition": "low_energy",
                        "action": "study",
                        "outcome": "reduced_reward"
                    })
                    self.fatigue_cause_score = min(1.0, self.fatigue_cause_score + 0.05)
        except:
            pass
    
    def _detect_terrain_patterns(self, patterns):
        """Detect terrain-specific reward patterns"""
        try:
            for terrain, rewards in self.terrain_reward_history.items():
                if len(rewards) >= 5:
                    avg_reward = sum(rewards) / len(rewards)
                    
                    # Compare to overall average
                    all_rewards = [r for rewards_list in self.terrain_reward_history.values() 
                                   for r in rewards_list]
                    overall_avg = sum(all_rewards) / len(all_rewards) if all_rewards else 0
                    
                    if avg_reward > overall_avg + 1.0:
                        self.terrain_preferences[terrain] = "favorable"
                        patterns.append({
                            "type": "terrain_preference",
                            "description": f"{terrain.title()} terrain yields higher rewards (+{(avg_reward - overall_avg):.1f})",
                            "condition": f"terrain_{terrain}",
                            "outcome": "positive_reward"
                        })
                        self.environment_sensitivity = min(1.0, self.environment_sensitivity + 0.03)
                    
                    elif avg_reward < overall_avg - 1.0:
                        self.terrain_preferences[terrain] = "unfavorable"
                        patterns.append({
                            "type": "terrain_avoidance",
                            "description": f"{terrain.title()} terrain yields lower rewards ({(avg_reward - overall_avg):.1f})",
                            "condition": f"terrain_{terrain}",
                            "outcome": "negative_reward"
                        })
        except:
            pass
    
    def _detect_personality_action_patterns(self, patterns):
        """Detect how personality traits influence action selection"""
        try:
            if len(self.state_history) < 15:
                return
            
            high_discipline_studies = 0
            low_discipline_studies = 0
            high_discipline_total = 0
            low_discipline_total = 0
            
            for state in list(self.state_history)[-15:]:
                discipline = state["personality"]["discipline"]
                
                if discipline > 0.6:
                    high_discipline_total += 1
                    if state.get("last_action") == "study":
                        high_discipline_studies += 1
                elif discipline < 0.4:
                    low_discipline_total += 1
                    if state.get("last_action") == "study":
                        low_discipline_studies += 1
            
            if high_discipline_total >= 3 and low_discipline_total >= 3:
                high_rate = high_discipline_studies / high_discipline_total
                low_rate = low_discipline_studies / low_discipline_total
                
                if high_rate > low_rate + 0.2:
                    patterns.append({
                        "type": "personality_behavior",
                        "description": f"High discipline increases study frequency by {((high_rate - low_rate) * 100):.0f}%",
                        "condition": "high_discipline",
                        "action": "study",
                        "outcome": "increased_frequency"
                    })
        except:
            pass
    
    def _detect_motivation_patterns(self, patterns):
        """Detect motivation trends over time"""
        try:
            for mot_type, values in self.motivation_trends.items():
                if len(values) >= 20:
                    recent_10 = values[-10:]
                    older_10 = values[-20:-10]
                    
                    recent_avg = sum(recent_10) / len(recent_10)
                    older_avg = sum(older_10) / len(older_10)
                    
                    change = recent_avg - older_avg
                    
                    if abs(change) > 0.15:
                        trend = "rising" if change > 0 else "falling"
                        patterns.append({
                            "type": "motivation_trend",
                            "description": f"{mot_type.replace('_', ' ').title()} motivation is {trend} ({change:+.2f})",
                            "condition": f"{mot_type}_trending",
                            "outcome": trend
                        })
        except:
            pass
    
    def _detect_fatigue_patterns(self, patterns):
        """Detect fatigue accumulation patterns"""
        try:
            if len(self.state_history) < 10:
                return
            
            recent_energy = [s["energy"] for s in list(self.state_history)[-10:]]
            
            low_energy_count = sum(1 for e in recent_energy if e < 40)
            
            if low_energy_count >= 7:
                patterns.append({
                    "type": "fatigue_accumulation",
                    "description": f"Sustained low energy for {low_energy_count}/10 cycles - chronic fatigue detected",
                    "condition": "chronic_low_energy",
                    "outcome": "fatigue_pattern"
                })
                self.fatigue_cause_score = min(1.0, self.fatigue_cause_score + 0.1)
            
            if len(recent_energy) >= 5:
                first_half_avg = sum(recent_energy[:5]) / 5
                second_half_avg = sum(recent_energy[5:]) / 5
                
                if first_half_avg - second_half_avg > 15:
                    patterns.append({
                        "type": "energy_depletion",
                        "description": f"Energy declining rapidly (-{(first_half_avg - second_half_avg):.1f} over 5 cycles)",
                        "condition": "energy_declining",
                        "outcome": "depletion_risk"
                    })
        except:
            pass
    
    def _detect_emotion_recovery_patterns(self, patterns):
        """Detect happiness recovery patterns"""
        try:
            if len(self.emotion_history) < 10:
                return
            
            recovery_events = []
            
            emotions = list(self.emotion_history)[-10:]
            for i in range(1, len(emotions)):
                prev_happiness = emotions[i-1]["happiness"]
                curr_happiness = emotions[i]["happiness"]
                
                if prev_happiness < 40 and curr_happiness > prev_happiness + 10:
                    recovery_events.append(curr_happiness - prev_happiness)
            
            if len(recovery_events) >= 2:
                avg_recovery = sum(recovery_events) / len(recovery_events)
                patterns.append({
                    "type": "emotion_recovery",
                    "description": f"Happiness recovers by average of {avg_recovery:.1f} points after low periods",
                    "condition": "low_happiness",
                    "outcome": "recovery_pattern"
                })
        except:
            pass
    
    def _detect_action_loops(self, patterns):
        """Detect repetitive behavior loops (PATCH)"""
        try:
            if self.action_repetition_index > 0.4:
                patterns.append({
                    "type": "repetition_loop",
                    "description": "Agent is repeating the same action several cycles",
                    "condition": "action_repeated",
                    "outcome": "stagnation"
                })
        except:
            pass
    
    def generate_self_narrative(self):
        """
        Generate natural-language self-description based on detected patterns
        Returns human-readable introspective summary
        """
        if not self.state_history:
            return "I am just beginning to understand myself."
        
        narrative_parts = []
        
        try:
            # Recent action patterns
            recent_actions = [s.get("last_action") for s in list(self.state_history)[-10:] 
                              if "last_action" in s]
            
            if recent_actions:
                action_counts = defaultdict(int)
                for action in recent_actions:
                    action_counts[action] += 1
                
                most_common = max(action_counts.items(), key=lambda x: x[1])
                
                if most_common[1] >= 4:
                    action_name = most_common[0].replace("_", " ")
                    narrative_parts.append(f"I've been {action_name} frequently - it's become a habit")
            
            # Energy patterns
            recent_energy = [s["energy"] for s in list(self.state_history)[-5:]]
            avg_energy = sum(recent_energy) / len(recent_energy)
            
            if avg_energy < 35:
                narrative_parts.append("I'm chronically fatigued and need to prioritize rest")
            elif avg_energy > 75:
                narrative_parts.append("I maintain high energy levels effectively")
            
            # Personality influence
            current_state = self.state_history[-1]
            personality = current_state["personality"]
            
            if personality["curiosity_bias"] > 0.65:
                narrative_parts.append("My curiosity drives me to explore constantly")
            
            if personality["discipline"] > 0.65:
                narrative_parts.append("My discipline keeps me focused on learning")
            
            if personality["risk_tolerance"] < 0.35:
                narrative_parts.append("I'm risk-averse and prefer safe, predictable choices")
            
            # Terrain preferences
            if self.terrain_preferences:
                favorable = [t for t, pref in self.terrain_preferences.items() if pref == "favorable"]
                unfavorable = [t for t, pref in self.terrain_preferences.items() if pref == "unfavorable"]
                
                if favorable:
                    narrative_parts.append(f"I thrive in {', '.join(favorable)} environments")
                
                if unfavorable:
                    narrative_parts.append(f"I avoid {', '.join(unfavorable)} areas due to poor outcomes")
            
            # Cause-effect awareness
            if len(self.cause_effect_memory) > 0:
                recent_patterns = [p["pattern"] for p in self.cause_effect_memory[-3:]]
                
                for pattern in recent_patterns:
                    if pattern["type"] == "energy_learning":
                        narrative_parts.append("I've learned that studying when exhausted is ineffective")
                        break
                    elif pattern["type"] == "fatigue_accumulation":
                        narrative_parts.append("I recognize a pattern of overexertion leading to fatigue")
                        break
            
        except:
            pass
        
        if not narrative_parts:
            return "I continue observing myself to understand my patterns better."
        
        return ". ".join(narrative_parts[:5]) + "."
    
    def get_self_awareness_summary(self):
        """Generate formatted summary for console display"""
        if not self.state_history:
            return "Insufficient data for self-modeling"
        
        lines = []
        lines.append("=" * 60)
        lines.append("🧠 SELF-MODELING SUMMARY")
        lines.append("=" * 60)
        
        try:
            # Fatigue patterns
            lines.append(f"• Fatigue Impact Score: {self.fatigue_cause_score:.2f}/1.0")
            if self.fatigue_cause_score > 0.5:
                lines.append("  ⚠️  High fatigue awareness - rest is critical")
            
            # Environment sensitivity
            lines.append(f"• Environment Sensitivity: {self.environment_sensitivity:.2f}/1.0")
            
            # PATCH: Novelty seeking metric
            if self.novelty_history:
                recent = [v for v in list(self.novelty_history)[-10:] if isinstance(v, (int, float))]
                if recent:
                    try:
                        novelty_avg = sum(recent) / len(recent)
                        lines.append(f"• Novelty Seeking: {novelty_avg:.2f}")
                    except:
                        pass
            
            # Terrain preferences
            if self.terrain_preferences:
                lines.append("• Terrain Preferences:")
                for terrain, pref in self.terrain_preferences.items():
                    emoji = "✅" if pref == "favorable" else "❌"
                    lines.append(f"  {emoji} {terrain.title()}: {pref}")
            
            # Recent patterns detected
            if self.detected_patterns:
                lines.append("• Recent Patterns Detected:")
                for pattern in self.detected_patterns[-3:]:
                    desc = pattern.get("description", f"[no description] ({pattern.get('type')})")
                    lines.append(f"  → {desc}")

            
            # Motivation trends (safe version)
            if self.motivation_trends:
                lines.append("• Motivation Trends (recent avg):")
                for mot_type in list(self.motivation_trends.keys())[:5]:
                    values = [v for v in self.motivation_trends[mot_type] if isinstance(v, (int, float))]
        
                    if len(values) >= 5:
                        try:
                            recent_avg = sum(values[-5:]) / 5
                            bar = "█" * int(recent_avg * 10) + "░" * (10 - int(recent_avg * 10))
                            lines.append(f"  {mot_type.replace('_', ' ').title()}: [{bar}] {recent_avg:.2f}")
                        except:
                            continue

            # Personality snapshot
            if self.state_history:
                personality = self.state_history[-1]["personality"]
                lines.append("• Current Personality State:")
                lines.append(f"  Optimism: {personality['optimism']:.2f} | Discipline: {personality['discipline']:.2f}")
                lines.append(f"  Curiosity: {personality['curiosity_bias']:.2f} | Risk: {personality['risk_tolerance']:.2f}")
        
        except:
            lines.append("• Error generating summary")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def to_dict(self):
        """Serialize self-model for JSON storage"""
        return {
            "cause_effect_memory": self.cause_effect_memory[-50:],
            "terrain_reward_map": {k: v[-20:] for k, v in self.terrain_reward_history.items()},
            "terrain_preferences": self.terrain_preferences,
            "detected_patterns": self.detected_patterns[-20:],
            "fatigue_cause_score": self.fatigue_cause_score,
            "environment_sensitivity": self.environment_sensitivity,
            "habit_strength": dict(self.habit_strength)
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize self-model from dictionary"""
        model = SelfModel()
        model.cause_effect_memory = data.get("cause_effect_memory", [])
        
        terrain_map = data.get("terrain_reward_map", {})
        for terrain, rewards in terrain_map.items():
            model.terrain_reward_history[terrain] = rewards
        
        model.terrain_preferences = data.get("terrain_preferences", {})
        model.detected_patterns = data.get("detected_patterns", [])
        model.fatigue_cause_score = data.get("fatigue_cause_score", 0.0)
        model.environment_sensitivity = data.get("environment_sensitivity", 0.5)
        model.habit_strength = data.get("habit_strength", {})
        
        return model

    def get_positive_pattern_reward(self, action):
        """
        Returns small intrinsic reward when the action aligns with
        beneficial patterns detected by the self-model.
        """
        reward = 0.0

        for pattern in self.detected_patterns:
            ptype = pattern.get("type", "")

            # Energy-learning pattern → prefer studying when energy is high
            if ptype == "energy_learning" and action.value == "study":
                reward += 0.4

            # Terrain preference → reward staying in favorable terrain
            if ptype == "terrain_preference":
                reward += 0.3

            # Motivation trend → reward actions aligned with rising motivations
            if ptype == "motivation_trend":
                reward += 0.2

            # Emotion recovery → reward actions that boost happiness
            if ptype == "emotion_recovery" and action.value in ["rest", "socialize"]:
                reward += 0.3

        return reward