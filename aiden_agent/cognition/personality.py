"""
Personality profile and cognitive drift system
"""


class PersonalityProfile:
    """
    Personality traits that evolve over time based on experiences
    Each trait ranges from 0.0 to 1.0, starting at 0.5 (neutral)
    """
    def __init__(self):
        self.optimism = 0.5          # Affects happiness recovery, outlook on failures
        self.discipline = 0.5         # Boosts learning motivation, reduces social drive
        self.curiosity_bias = 0.5     # Multiplies curiosity and exploration drives
        self.risk_tolerance = 0.5     # Reduces survival weight, encourages exploration
        self.social_affinity = 0.5    # Amplifies social motivation
        
        # Track evolution history
        self.trait_history = []
        self.last_update_cycle = 0
        self.cycles_since_activity = 0
    
    def get_trait_changes(self):
        """Calculate trait deltas from neutral (0.5)"""
        return {
            "optimism": self.optimism - 0.5,
            "discipline": self.discipline - 0.5,
            "curiosity_bias": self.curiosity_bias - 0.5,
            "risk_tolerance": self.risk_tolerance - 0.5,
            "social_affinity": self.social_affinity - 0.5
        }
    
    def get_personality_archetype(self):
        """Determine personality archetype based on dominant traits"""
        traits = {
            "optimism": self.optimism,
            "discipline": self.discipline,
            "curiosity_bias": self.curiosity_bias,
            "risk_tolerance": self.risk_tolerance,
            "social_affinity": self.social_affinity
        }
        
        # Find dominant traits (>0.6)
        dominant = [name for name, value in traits.items() if value > 0.6]
        
        if self.curiosity_bias > 0.65 and self.risk_tolerance > 0.6:
            return "Bold Explorer"
        elif self.discipline > 0.65 and self.optimism > 0.6:
            return "Focused Scholar"
        elif self.social_affinity > 0.65:
            return "Social Butterfly"
        elif self.risk_tolerance < 0.4 and self.discipline > 0.6:
            return "Cautious Planner"
        elif self.optimism > 0.65:
            return "Cheerful Wanderer"
        elif self.curiosity_bias > 0.6:
            return "Curious Seeker"
        elif len(dominant) == 0:
            return "Balanced Neutral"
        else:
            return "Evolving Individual"
    
    def mutate_from_reflection(self, reward_trend, failure_count, success_count, dominant_motivation):
        """
        Adjust personality traits based on reflective insights
        reward_trend: 'improving', 'declining', or 'stable'
        """
        mutations = {}
        
        # REWARD TREND ANALYSIS
        if reward_trend == "improving":
            # Success breeds optimism and discipline
            self.optimism = min(1.0, self.optimism + 0.01)
            self.discipline = min(1.0, self.discipline + 0.01)
            mutations["optimism"] = "+0.01"
            mutations["discipline"] = "+0.01"
        
        elif reward_trend == "declining":
            # Failure/stagnation → explore new strategies
            self.curiosity_bias = min(1.0, self.curiosity_bias + 0.02)
            self.discipline = max(0.0, self.discipline - 0.01)
            mutations["curiosity_bias"] = "+0.02"
            mutations["discipline"] = "-0.01"
            
            # Lower optimism slightly
            self.optimism = max(0.0, self.optimism - 0.01)
            mutations["optimism"] = "-0.01"
        
        # FAILURE/SUCCESS RATIO ANALYSIS
        total_goals = failure_count + success_count
        if total_goals > 5:
            failure_rate = failure_count / total_goals
            
            if failure_rate > 0.5:
                # High failure → increase risk tolerance, reduce discipline
                self.risk_tolerance = min(1.0, self.risk_tolerance + 0.02)
                self.discipline = max(0.0, self.discipline - 0.01)
                mutations["risk_tolerance"] = "+0.02 (adapting to failures)"
            
            elif failure_rate < 0.2:
                # High success → increase discipline, slight optimism
                self.discipline = min(1.0, self.discipline + 0.01)
                self.optimism = min(1.0, self.optimism + 0.01)
                mutations["discipline"] = "+0.01 (reinforcing success)"
        
        # DOMINANT MOTIVATION INFLUENCE
        from aiden_agent.cognition.motivation import MotivationType  # Import here to avoid circular dependency
        
        if dominant_motivation == MotivationType.EXPLORATION:
            self.curiosity_bias = min(1.0, self.curiosity_bias + 0.01)
            mutations["curiosity_bias"] = "+0.01 (exploration drive)"
        
        elif dominant_motivation == MotivationType.LEARNING:
            self.discipline = min(1.0, self.discipline + 0.01)
            mutations["discipline"] = "+0.01 (learning focus)"
        
        elif dominant_motivation == MotivationType.SOCIAL:
            self.social_affinity = min(1.0, self.social_affinity + 0.01)
            mutations["social_affinity"] = "+0.01 (social engagement)"
        
        elif dominant_motivation == MotivationType.SURVIVAL:
            self.risk_tolerance = max(0.0, self.risk_tolerance - 0.01)
            mutations["risk_tolerance"] = "-0.01 (survival caution)"
        
        return mutations
    
    def decay_toward_neutral(self, decay_rate=0.005):
        """
        Slowly drift traits back toward 0.5 if inactive for extended periods
        Simulates personality stabilization
        """
        self.optimism += (0.5 - self.optimism) * decay_rate
        self.discipline += (0.5 - self.discipline) * decay_rate
        self.curiosity_bias += (0.5 - self.curiosity_bias) * decay_rate
        self.risk_tolerance += (0.5 - self.risk_tolerance) * decay_rate
        self.social_affinity += (0.5 - self.social_affinity) * decay_rate
    
    def record_snapshot(self, cycle):
        """Record current personality state"""
        self.trait_history.append({
            "cycle": cycle,
            "optimism": round(self.optimism, 3),
            "discipline": round(self.discipline, 3),
            "curiosity_bias": round(self.curiosity_bias, 3),
            "risk_tolerance": round(self.risk_tolerance, 3),
            "social_affinity": round(self.social_affinity, 3)
        })
        self.last_update_cycle = cycle
    
    def to_dict(self):
        """Serialize personality"""
        return {
            "optimism": self.optimism,
            "discipline": self.discipline,
            "curiosity_bias": self.curiosity_bias,
            "risk_tolerance": self.risk_tolerance,
            "social_affinity": self.social_affinity,
            "trait_history": self.trait_history[-50:],  # Keep last 50
            "last_update_cycle": self.last_update_cycle,
            "cycles_since_activity": self.cycles_since_activity
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize personality"""
        profile = PersonalityProfile()
        profile.optimism = data.get("optimism", 0.5)
        profile.discipline = data.get("discipline", 0.5)
        profile.curiosity_bias = data.get("curiosity_bias", 0.5)
        profile.risk_tolerance = data.get("risk_tolerance", 0.5)
        profile.social_affinity = data.get("social_affinity", 0.5)
        profile.trait_history = data.get("trait_history", [])
        profile.last_update_cycle = data.get("last_update_cycle", 0)
        profile.cycles_since_activity = data.get("cycles_since_activity", 0)
        return profile
    
    def display_summary(self):
        """Format personality summary for console output"""
        archetype = self.get_personality_archetype()
        
        print("\n" + "="*60)
        print(f"🧬 COGNITIVE DRIFT SUMMARY - Personality: {archetype}")
        print("="*60)
        
        def trait_bar(value):
            filled = int(value * 20)
            return "█" * filled + "░" * (20 - filled)
        
        def arrow(value):
            if value > 0.55:
                return "↑"
            elif value < 0.45:
                return "↓"
            else:
                return "→"
        
        print(f"  Optimism:       [{trait_bar(self.optimism)}] {self.optimism:.2f} {arrow(self.optimism)}")
        print(f"  Discipline:     [{trait_bar(self.discipline)}] {self.discipline:.2f} {arrow(self.discipline)}")
        print(f"  Curiosity Bias: [{trait_bar(self.curiosity_bias)}] {self.curiosity_bias:.2f} {arrow(self.curiosity_bias)}")
        print(f"  Risk Tolerance: [{trait_bar(self.risk_tolerance)}] {self.risk_tolerance:.2f} {arrow(self.risk_tolerance)}")
        print(f"  Social Affinity:[{trait_bar(self.social_affinity)}] {self.social_affinity:.2f} {arrow(self.social_affinity)}")
        print("="*60 + "\n")