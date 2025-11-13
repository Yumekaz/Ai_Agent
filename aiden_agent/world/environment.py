"""
Environment simulation with time, weather, and world state
"""

import random
from .terrain import Weather, TimeOfDay, GridWorld


class Environment:
    """
    Enhanced environment with 2D grid world
    Contains time, weather, and spatial navigation
    """
    def __init__(self, grid_size=5):
        # Time simulation
        self.cycle = 0
        self.time_of_day = TimeOfDay.MORNING
        self.weather = Weather.SUNNY
        
        # World conditions
        self.ambient_light = 100
        self.temperature = 20
        self.noise_level = 10
        
        # 2D Grid World
        self.grid_world = GridWorld(grid_size, grid_size)
        
        # Discoverable knowledge
        self.available_knowledge = {
            "math": ["algebra", "geometry", "calculus"],
            "science": ["physics", "chemistry", "biology"],
            "arts": ["painting", "music", "literature"],
            "history": ["ancient", "medieval", "modern"],
            "technology": ["computers", "AI", "robotics"]
        }
        
        # Events
        self.events = []
    
    def advance_time(self):
        """Progress time in the world"""
        self.cycle += 1
        
        # Change time of day every 5 cycles
        if self.cycle % 5 == 0:
            times = list(TimeOfDay)
            current_idx = times.index(self.time_of_day)
            self.time_of_day = times[(current_idx + 1) % len(times)]
            
            # Update ambient conditions
            if self.time_of_day == TimeOfDay.MORNING:
                self.ambient_light = 80
                self.noise_level = 30
            elif self.time_of_day == TimeOfDay.AFTERNOON:
                self.ambient_light = 100
                self.noise_level = 50
            elif self.time_of_day == TimeOfDay.EVENING:
                self.ambient_light = 40
                self.noise_level = 30
            else:  # NIGHT
                self.ambient_light = 10
                self.noise_level = 10
        
        # Weather changes
        if random.random() < 0.15:
            self.weather = random.choice(list(Weather))
            self.events.append(f"Weather shifted to {self.weather.value}")
        
        # Temperature varies
        if self.weather == Weather.SUNNY:
            self.temperature = 20 + random.randint(-2, 5)
        elif self.weather == Weather.CLOUDY:
            self.temperature = 18 + random.randint(-3, 3)
        elif self.weather == Weather.RAINY:
            self.temperature = 15 + random.randint(-5, 2)
        else:  # STORMY
            self.temperature = 12 + random.randint(-5, 0)
            # Stormy weather adds hazard
            self.events.append("⚡ The storm makes movement dangerous!")
    
    def get_state(self):
        """Return current world state"""
        return {
            "cycle": self.cycle,
            "time": self.time_of_day.value,
            "weather": self.weather.value,
            "light": self.ambient_light,
            "temperature": self.temperature,
            "noise": self.noise_level,
            "events": self.events.copy()
        }
    
    def clear_events(self):
        """Clear event queue"""
        self.events.clear()
    
    def get_random_knowledge(self, category=None):
        """Get random knowledge piece"""
        if category and category in self.available_knowledge:
            return random.choice(self.available_knowledge[category])
        else:
            cat = random.choice(list(self.available_knowledge.keys()))
            return cat, random.choice(self.available_knowledge[cat])
    
    def get_hazard_level(self):
        """
        Calculate current environmental hazard level
        Affects movement and actions
        """
        hazard = 0
        
        # Weather hazards
        if self.weather == Weather.STORMY:
            hazard += 3
        elif self.weather == Weather.RAINY:
            hazard += 1
        
        # Time of day hazards
        if self.time_of_day == TimeOfDay.NIGHT:
            hazard += 2  # Harder to navigate at night
        
        return hazard