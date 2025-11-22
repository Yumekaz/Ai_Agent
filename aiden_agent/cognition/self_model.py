"""
Self-Modeling Layer for metacognitive self-awareness
Tracks internal state history and analyzes cause-effect patterns
"""

from collections import deque, defaultdict


class SelfModel:
    """
    Metacognitive layer:
    - records internal & external factors
    - detects stable patterns
    - influences planning, intentions, RL
    """
    def __init__(self, history_size=50):
        self.history_size = history_size

        # State/time history
        self.state_history = deque(maxlen=history_size)
        self.action_history = deque(maxlen=history_size)
        self.emotion_history = deque(maxlen=history_size)

        # Terrain → rewards (key must be normalized string)
        self.terrain_reward_history = defaultdict(list)

        # Pattern memory
        self.cause_effect_memory = []
        self.detected_patterns = []

        # Learned terrain preferences: { "forest": "favorable", ... }
        self.terrain_preferences = {}

        # Motivation trends recorded over time
        self.motivation_trends = defaultdict(list)

        # Fatigue/env metrics used by RL bias + meta-controller
        self.fatigue_cause_score = 0.0
        self.environment_sensitivity = 0.5

        # Novelty system
        self.tile_visit_count = defaultdict(int)
        self.novelty_history = deque(maxlen=50)

        # Action repetition
        self.repetition_tracker = deque(maxlen=10)
        self.action_repetition_index = 0.0

        # Habit formation (future use)
        self.habit_strength = {}

    # ============================================================
    # STATE RECORDING
    # ============================================================
    def record_state(self, agent):
        """
        Capture snapshot every cycle.
        """
        try:
            cell = agent.environment.grid_world.get_cell(agent.position_x, agent.position_y)
            terrain = cell.terrain.value.lower() if cell else "unknown"

            snapshot = {
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

            if agent.previous_action:
                snapshot["last_action"] = agent.previous_action.value

            if agent.rl_system.total_rewards:
                snapshot["last_reward"] = agent.rl_system.total_rewards[-1]

            self.state_history.append(snapshot)

            # Emotion classification
            emotion = self._categorize_emotion(agent.happiness, agent.energy, agent.focus)
            self.emotion_history.append({
                "cycle": agent.cycles_alive,
                "emotion": emotion,
                "happiness": agent.happiness,
                "energy": agent.energy
            })

            # Terrain reward (normalized key)
            if "last_reward" in snapshot:
                self.terrain_reward_history[terrain].append(snapshot["last_reward"])

            # Motivation trends
            for mot_type, val in agent.motivation_levels.items():
                self.motivation_trends[mot_type.value].append(val)

            # Novelty tracking
            pos = (agent.position_x, agent.position_y)
            self.tile_visit_count[pos] += 1
            novelty = 1.0 / self.tile_visit_count[pos]
            self.novelty_history.append(float(novelty))

            # Repetition loop tracking
            self.repetition_tracker.append(snapshot.get("last_action"))
            if len(self.repetition_tracker) >= 4:
                last4 = list(self.repetition_tracker)[-4:]
                if len(set(last4)) == 1 and last4[0] is not None:
                    self.action_repetition_index = min(1.0, self.action_repetition_index + 0.1)

        except:
            pass

    # ============================================================
    # EMOTION CLASSIFIER
    # ============================================================
    def _categorize_emotion(self, happiness, energy, focus):
        if happiness > 70 and energy > 60:
            return "thriving"
        if happiness > 50 and energy > 40:
            return "content"
        if energy < 30:
            return "exhausted"
        if happiness < 30:
            return "distressed"
        if focus > 70:
            return "focused"
        return "neutral"

    # ============================================================
    # PATTERN DISCOVERY
    # ============================================================
    def analyze_cause_effect(self):
        if len(self.state_history) < 10:
            return []

        new_patterns = []

        self._detect_energy_learning_pattern(new_patterns)
        self._detect_terrain_patterns(new_patterns)
        self._detect_personality_patterns(new_patterns)
        self._detect_motivation_patterns(new_patterns)
        self._detect_fatigue_patterns(new_patterns)
        self._detect_emotion_recovery_patterns(new_patterns)
        self._detect_action_loops(new_patterns)

        # Deduplicate + store
        for p in new_patterns:
            if p not in self.detected_patterns:
                self.detected_patterns.append(p)
                self.cause_effect_memory.append({
                    "cycle": self.state_history[-1]["cycle"],
                    "pattern": p
                })

        return new_patterns

    # ------------------------------------------------------------
    # Pattern Detectors
    # ------------------------------------------------------------
    def _detect_energy_learning_pattern(self, patterns):
        try:
            lows = []
            highs = []

            for s in list(self.state_history)[-20:]:
                if s.get("last_action") == "study" and "last_reward" in s:
                    if s["energy"] < 30:
                        lows.append(s["last_reward"])
                    elif s["energy"] > 60:
                        highs.append(s["last_reward"])

            if len(lows) >= 3 and len(highs) >= 3:
                if sum(highs)/len(highs) > sum(lows)/len(lows) + 1.5:
                    patterns.append({
                        "type": "energy_learning",
                        "description": "Low energy → poor study efficiency",
                        "condition": "low_energy",
                        "action": "study"
                    })
                    self.fatigue_cause_score = min(1.0, self.fatigue_cause_score + 0.05)
        except:
            pass

    def _detect_terrain_patterns(self, patterns):
        try:
            all_rewards = [
                r for lst in self.terrain_reward_history.values() for r in lst
            ]
            if not all_rewards:
                return

            overall = sum(all_rewards) / len(all_rewards)

            for terrain, rewards in self.terrain_reward_history.items():
                if len(rewards) < 5:
                    continue

                avg = sum(rewards) / len(rewards)

                if avg > overall + 1.0:
                    self.terrain_preferences[terrain] = "favorable"
                    patterns.append({
                        "type": "terrain_preference",
                        "description": f"{terrain} improves rewards",
                        "condition": terrain
                    })
                    self.environment_sensitivity = min(1.0, self.environment_sensitivity + 0.03)

                elif avg < overall - 1.0:
                    self.terrain_preferences[terrain] = "unfavorable"
                    patterns.append({
                        "type": "terrain_avoidance",
                        "description": f"{terrain} reduces rewards",
                        "condition": terrain
                    })
        except:
            pass

    def _detect_personality_patterns(self, patterns):
        try:
            if len(self.state_history) < 15:
                return

            s = list(self.state_history)[-15:]

            high = [x for x in s if x["personality"]["discipline"] > 0.6]
            low = [x for x in s if x["personality"]["discipline"] < 0.4]

            if len(high) >= 3 and len(low) >= 3:
                high_rate = sum(1 for x in high if x.get("last_action") == "study") / len(high)
                low_rate = sum(1 for x in low if x.get("last_action") == "study") / len(low)

                if high_rate > low_rate + 0.2:
                    patterns.append({
                        "type": "personality_behavior",
                        "description": "High discipline increases studying frequency",
                        "condition": "high_discipline"
                    })
        except:
            pass

    def _detect_motivation_patterns(self, patterns):
        try:
            for key, values in self.motivation_trends.items():
                if len(values) < 20:
                    continue

                old = sum(values[-20:-10]) / 10
                new = sum(values[-10:]) / 10
                delta = new - old

                if abs(delta) > 0.15:
                    patterns.append({
                        "type": "motivation_trend",
                        "description": f"{key} motivation changed by {delta:+.2f}",
                        "condition": key
                    })
        except:
            pass

    def _detect_fatigue_patterns(self, patterns):
        try:
            hist = list(self.state_history)[-10:]
            energies = [s["energy"] for s in hist]

            if sum(1 for e in energies if e < 40) >= 7:
                patterns.append({
                    "type": "fatigue_accumulation",
                    "description": "Persistent low energy detected"
                })
                self.fatigue_cause_score = min(1.0, self.fatigue_cause_score + 0.1)

            if len(energies) >= 10:
                if sum(energies[:5])/5 - sum(energies[5:])/5 > 15:
                    patterns.append({
                        "type": "energy_depletion",
                        "description": "Energy collapsing in recent cycles"
                    })
        except:
            pass

    def _detect_emotion_recovery_patterns(self, patterns):
        try:
            if len(self.emotion_history) < 10:
                return

            events = []
            for i in range(1, len(self.emotion_history)):
                prev = self.emotion_history[i-1]["happiness"]
                curr = self.emotion_history[i]["happiness"]
                if prev < 40 and curr > prev + 10:
                    events.append(curr - prev)

            if len(events) >= 2:
                patterns.append({
                    "type": "emotion_recovery",
                    "description": "Happiness rebounds after low periods"
                })
        except:
            pass

    def _detect_action_loops(self, patterns):
        try:
            if self.action_repetition_index > 0.4:
                patterns.append({
                    "type": "repetition_loop",
                    "description": "Agent stuck repeating same action"
                })
        except:
            pass

    # ============================================================
    # NARRATIVE GENERATION
    # ============================================================
    def generate_self_narrative(self):
        if not self.state_history:
            return "I am still forming my self-awareness."

        parts = []

        # Action habits
        recent = [s.get("last_action") for s in list(self.state_history)[-10:] if s.get("last_action")]
        if recent:
            freq = defaultdict(int)
            for a in recent:
                freq[a] += 1

            top, n = max(freq.items(), key=lambda x: x[1])
            if n >= 4:
                parts.append(f"I've been doing {top.replace('_', ' ')} very frequently—it feels habitual")

        # Energy
        e_vals = [s["energy"] for s in list(self.state_history)[-5:]]
        if e_vals and sum(e_vals)/len(e_vals) < 35:
            parts.append("I'm running low on energy and should rest more")

        # Personality influence
        p = self.state_history[-1]["personality"]
        if p["curiosity_bias"] > 0.65:
            parts.append("My curiosity keeps pushing me outward to explore")
        if p["discipline"] > 0.65:
            parts.append("My discipline keeps me focused on learning tasks")
        if p["risk_tolerance"] < 0.35:
            parts.append("I prefer safe, low-risk decisions")

        # Terrain preferences
        if self.terrain_preferences:
            fav = [t for t,v in self.terrain_preferences.items() if v=="favorable"]
            unf = [t for t,v in self.terrain_preferences.items() if v=="unfavorable"]

            if fav:
                parts.append(f"I perform well in {', '.join(fav)} terrain")
            if unf:
                parts.append(f"I struggle in {', '.join(unf)} terrain")

        if not parts:
            return "I'm observing myself and learning my patterns."

        return ". ".join(parts[:5]) + "."

    # ============================================================
    # SUMMARY OUTPUT
    # ============================================================
    def get_self_awareness_summary(self):
        if not self.state_history:
            return "Self-model is empty."

        out = []
        out.append("=" * 60)
        out.append("🧠 SELF-MODEL SUMMARY")
        out.append("=" * 60)

        out.append(f"• Fatigue Impact Score: {self.fatigue_cause_score:.2f}")
        out.append(f"• Environment Sensitivity: {self.environment_sensitivity:.2f}")

        # Novelty
        if self.novelty_history:
            vals = [n for n in list(self.novelty_history)[-10:] if isinstance(n, float)]
            if vals:
                out.append(f"• Novelty Seeking: {sum(vals)/len(vals):.2f}")

        # Terrain prefs
        if self.terrain_preferences:
            out.append("• Terrain Preferences:")
            for t,pref in self.terrain_preferences.items():
                out.append(f"   {t}: {pref}")

        # Patterns
        if self.detected_patterns:
            out.append("• Recent Patterns:")
            for p in self.detected_patterns[-3:]:
                out.append(f"   → {p['description']}")

        out.append("=" * 60)
        return "\n".join(out)

    # ============================================================
    # SERIALIZATION
    # ============================================================
    def to_dict(self):
        return {
            "cause_effect_memory": self.cause_effect_memory[-50:],
            "terrain_reward_map": {k: v[-20:] for k,v in self.terrain_reward_history.items()},
            "terrain_preferences": self.terrain_preferences,
            "detected_patterns": self.detected_patterns[-20:],
            "fatigue_cause_score": self.fatigue_cause_score,
            "environment_sensitivity": self.environment_sensitivity,
            "habit_strength": self.habit_strength
        }

    @staticmethod
    def from_dict(data):
        m = SelfModel()

        m.cause_effect_memory = data.get("cause_effect_memory", [])

        tr_map = data.get("terrain_reward_map", {})
        for terrain, rewards in tr_map.items():
            m.terrain_reward_history[terrain] = rewards

        m.terrain_preferences = data.get("terrain_preferences", {})
        m.detected_patterns = data.get("detected_patterns", [])
        m.fatigue_cause_score = data.get("fatigue_cause_score", 0.0)
        m.environment_sensitivity = data.get("environment_sensitivity", 0.5)
        m.habit_strength = data.get("habit_strength", {})

        return m

    # ============================================================
    # RL INTRINSIC BONUS HOOK
    # ============================================================
    def get_positive_pattern_reward(self, action):
        reward = 0.0

        for p in self.detected_patterns:
            t = p.get("type")

            if t == "energy_learning" and action.value == "study":
                reward += 0.4
            if t == "terrain_preference":
                reward += 0.3
            if t == "motivation_trend":
                reward += 0.2
            if t == "emotion_recovery" and action.value in ["rest", "socialize"]:
                reward += 0.3

        return reward
