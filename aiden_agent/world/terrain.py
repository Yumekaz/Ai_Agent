"""
Terrain, resources, weather, and grid cell definitions
"""

import random
from enum import Enum


class TerrainType(Enum):
    """Different terrain types with unique properties"""
    FOREST = "forest"
    RUINS = "ruins"
    PLAINS = "plains"
    MOUNTAINS = "mountains"
    RIVER = "river"


class ResourceType(Enum):
    """Collectable resources in the world"""
    FOOD = "food"
    BOOK = "book"
    RELIC = "relic"


class Weather(Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"


class TimeOfDay(Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class GridCell:
    """
    Represents a single cell in the 2D grid world
    Each cell has terrain type, resources, and discovery state
    """
    def __init__(self, x, y, terrain_type):
        self.x = x
        self.y = y
        self.terrain = terrain_type
        self.resources = []  # List of ResourceType
        self.discovered = False
        self.visit_count = 0
        
    def add_resource(self, resource_type):
        """Add a resource to this cell"""
        self.resources.append(resource_type)
    
    def collect_resource(self, resource_type):
        """Remove and return a resource if available"""
        if resource_type in self.resources:
            self.resources.remove(resource_type)
            return True
        return False
    
    def get_terrain_effects(self):
        """
        Return energy and focus modifiers for this terrain
        Different terrains have different costs/benefits
        """
        effects = {
            TerrainType.FOREST: {"energy": -3, "focus": +2, "description": "Dense trees slow movement but sharpen focus"},
            TerrainType.RUINS: {"energy": -5, "focus": +5, "description": "Ancient ruins are exhausting but intellectually stimulating"},
            TerrainType.PLAINS: {"energy": -1, "focus": 0, "description": "Open plains are easy to traverse"},
            TerrainType.MOUNTAINS: {"energy": -8, "focus": -3, "description": "Steep mountains drain energy and concentration"},
            TerrainType.RIVER: {"energy": -2, "focus": +3, "description": "Flowing water is refreshing and calming"}
        }
        return effects.get(self.terrain, {"energy": 0, "focus": 0, "description": "Neutral terrain"})
    
    def to_dict(self):
        """Serialize cell to dictionary for JSON"""
        return {
            "x": self.x,
            "y": self.y,
            "terrain": self.terrain.value,
            "resources": [r.value for r in self.resources],
            "discovered": self.discovered,
            "visit_count": self.visit_count
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize cell from dictionary"""
        cell = GridCell(data["x"], data["y"], TerrainType(data["terrain"]))
        cell.resources = [ResourceType(r) for r in data["resources"]]
        cell.discovered = data["discovered"]
        cell.visit_count = data["visit_count"]
        return cell


class GridWorld:
    """
    5x5 grid map where the agent navigates
    Each cell has terrain, resources, and hazards
    """
    def __init__(self, width=5, height=5):
        self.width = width
        self.height = height
        self.grid = []
        self.generate_world()
    
    def generate_world(self):
        """Generate the 2D grid with varied terrain and resources"""
        self.grid = []
        
        # Create grid cells with random terrain
        terrain_options = list(TerrainType)
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Distribute terrain with some biasing for variety
                if x == 0 or x == self.width - 1:
                    # Edges more likely to be mountains/forests
                    terrain = random.choice([TerrainType.MOUNTAINS, TerrainType.FOREST, TerrainType.PLAINS])
                elif y == self.height // 2:
                    # Middle row could be a river
                    terrain = TerrainType.RIVER if random.random() < 0.6 else random.choice(terrain_options)
                else:
                    terrain = random.choice(terrain_options)
                
                cell = GridCell(x, y, terrain)
                
                # Randomly place resources (30% chance per cell)
                if random.random() < 0.3:
                    resource = random.choice(list(ResourceType))
                    cell.add_resource(resource)
                
                row.append(cell)
            self.grid.append(row)
        
        # Start position is always discovered
        self.grid[0][0].discovered = True
    
    def get_cell(self, x, y):
        """Get cell at coordinates (returns None if out of bounds)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None
    
    def is_valid_position(self, x, y):
        """Check if coordinates are within bounds"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_neighbors(self, x, y):
        """Get valid neighboring cells (N, S, E, W)"""
        neighbors = {}
        directions = {
            "north": (x, y - 1),
            "south": (x, y + 1),
            "east": (x + 1, y),
            "west": (x - 1, y)
        }
        
        for direction, (nx, ny) in directions.items():
            if self.is_valid_position(nx, ny):
                neighbors[direction] = self.grid[ny][nx]
        
        return neighbors
    
    def to_dict(self):
        """Serialize grid to dictionary"""
        return {
            "width": self.width,
            "height": self.height,
            "cells": [[cell.to_dict() for cell in row] for row in self.grid]
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize grid from dictionary"""
        world = GridWorld(data["width"], data["height"])
        world.grid = []
        for row_data in data["cells"]:
            row = [GridCell.from_dict(cell_data) for cell_data in row_data]
            world.grid.append(row)
        return world
    
    def render_ascii(self, agent_x, agent_y):
        """
        Render the grid as ASCII art
        A = Agent, ? = Undiscovered, Terrain first letter = Discovered
        """
        print("\n╔" + "═══╦" * (self.width - 1) + "═══╗")
        
        for y in range(self.height):
            row_str = "║"
            for x in range(self.width):
                cell = self.grid[y][x]
                
                if x == agent_x and y == agent_y:
                    symbol = " A "  # Agent position
                elif not cell.discovered:
                    symbol = " ? "  # Undiscovered
                else:
                    # Show terrain type first letter + resource indicator
                    terrain_char = cell.terrain.value[0].upper()
                    resource_char = str(len(cell.resources)) if cell.resources else " "
                    symbol = f" {terrain_char}{resource_char}"
                
                row_str += symbol + "║"
            
            print(row_str)
            
            if y < self.height - 1:
                print("╠" + "═══╬" * (self.width - 1) + "═══╣")
        
        print("╚" + "═══╩" * (self.width - 1) + "═══╝")
        
        # Legend
        print("\nLegend: A=Agent, ?=Undiscovered, F=Forest, R=Ruins/River, P=Plains, M=Mountains")
        print("        Number = Resource count in cell\n")