"""
Terrain, resources, weather, and grid cell definitions
"""

import random
from enum import Enum


# ============================================================
# ENUM DEFINITIONS
# ============================================================

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


# ============================================================
# GRID CELL — Phase-6 Compliant
# ============================================================

class GridCell:
    """
    Represents a single cell in the 2D grid world.
    Each cell has terrain type, resources, and discovery state.
    """

    def __init__(self, x, y, terrain_type):
        self.x = x
        self.y = y
        self.terrain = terrain_type            # Enum TerrainType
        self.resources = []                    # List[ResourceType]
        self.discovered = False
        self.visit_count = 0

    # ----------------------------------------------------------
    # ✔ PHASE-6 REQUIRED: Safe/Danger classification
    # ----------------------------------------------------------
    @property
    def is_dangerous(self):
        """Mountains + Ruins = hazardous tiles."""
        return self.terrain in {TerrainType.MOUNTAINS, TerrainType.RUINS}

    @property
    def terrain_name(self):
        """Lowercase normalized terrain string."""
        return self.terrain.value.lower()

    # ----------------------------------------------------------
    # Resource APIs
    # ----------------------------------------------------------
    def add_resource(self, resource_type):
        self.resources.append(resource_type)

    def collect_resource(self, resource_type):
        if resource_type in self.resources:
            self.resources.remove(resource_type)
            return True
        return False

    # ----------------------------------------------------------
    # Terrain effects (energy/focus modifiers)
    # ----------------------------------------------------------
    def get_terrain_effects(self):
        """
        Returns effects used by RL execute_action and movement fatigue.
        """
        effects = {
            TerrainType.FOREST:    {"energy": -3, "focus": +2,
                                    "description": "Dense trees slow movement but sharpen focus"},
            TerrainType.RUINS:     {"energy": -5, "focus": +5,
                                    "description": "Ancient ruins are exhausting but intellectually stimulating"},
            TerrainType.PLAINS:    {"energy": -1, "focus":  0,
                                    "description": "Open plains are easy to traverse"},
            TerrainType.MOUNTAINS: {"energy": -8, "focus": -3,
                                    "description": "Steep mountains drain energy and concentration"},
            TerrainType.RIVER:     {"energy": -2, "focus": +3,
                                    "description": "Flowing water is refreshing and calming"},
        }
        return effects.get(self.terrain, {"energy": 0, "focus": 0, "description": "Neutral terrain"})

    # ----------------------------------------------------------
    # Serialization helpers
    # ----------------------------------------------------------
    def to_dict(self):
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
        cell = GridCell(
            data["x"],
            data["y"],
            TerrainType(data["terrain"])
        )
        cell.resources = [ResourceType(r) for r in data["resources"]]
        cell.discovered = data["discovered"]
        cell.visit_count = data["visit_count"]
        return cell


# ============================================================
# GRID WORLD — Phase-6 Compatible
# ============================================================

class GridWorld:
    """
    The 5x5 grid that the agent navigates.
    Handles:
        • Terrain layout
        • Resource distribution
        • Spatial discovery
        • Provides iter_cells() for BFS routing & goal creation
    """

    def __init__(self, width=5, height=5):
        self.width = width
        self.height = height
        self.grid = []
        self.generate_world()

    # ----------------------------------------------------------
    # World generation
    # ----------------------------------------------------------
    def generate_world(self):
        """Generate the 2D grid with terrain and resources."""
        self.grid = []
        terrain_options = list(TerrainType)

        for y in range(self.height):
            row = []
            for x in range(self.width):

                # Edge-biased terrain distribution
                if x == 0 or x == self.width - 1:
                    terrain = random.choice([
                        TerrainType.MOUNTAINS,
                        TerrainType.FOREST,
                        TerrainType.PLAINS
                    ])
                elif y == self.height // 2:
                    terrain = TerrainType.RIVER if random.random() < 0.6 else random.choice(terrain_options)
                else:
                    terrain = random.choice(terrain_options)

                cell = GridCell(x, y, terrain)

                # 30% resource chance
                if random.random() < 0.3:
                    cell.add_resource(random.choice(list(ResourceType)))

                row.append(cell)
            self.grid.append(row)

        # Agent start always discovered
        self.grid[0][0].discovered = True

    # ----------------------------------------------------------
    # Spatial Helpers
    # ----------------------------------------------------------
    def get_cell(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def is_valid_position(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def get_neighbors(self, x, y):
        neighbors = {}
        directions = {
            "north": (x, y - 1),
            "south": (x, y + 1),
            "east":  (x + 1, y),
            "west":  (x - 1, y)
        }
        for name, (nx, ny) in directions.items():
            if self.is_valid_position(nx, ny):
                neighbors[name] = self.grid[ny][nx]
        return neighbors

    # ----------------------------------------------------------
    # ✔ REQUIRED BY Phase-6 GoalManager._assign_route_target()
    # ----------------------------------------------------------
    def iter_cells(self):
        """
        Yield all cells as (x, y, cell).
        Used by:
            • GoalManager route target assignment
            • Exploration goals
            • Resource collection goals
        """
        for y in range(self.height):
            for x in range(self.width):
                yield x, y, self.grid[y][x]

    # ----------------------------------------------------------
    # Serialization
    # ----------------------------------------------------------
    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "cells": [[cell.to_dict() for cell in row] for row in self.grid]
        }

    @staticmethod
    def from_dict(data):
        world = GridWorld(data["width"], data["height"])
        world.grid = [
            [GridCell.from_dict(cell_data) for cell_data in row_data]
            for row_data in data["cells"]
        ]
        return world

    # ----------------------------------------------------------
    # ASCII Renderer
    # ----------------------------------------------------------
    def render_ascii(self, agent_x, agent_y):
        print("\n╔" + "═══╦" * (self.width - 1) + "═══╗")

        for y in range(self.height):
            row_str = "║"
            for x in range(self.width):
                cell = self.grid[y][x]

                if (x, y) == (agent_x, agent_y):
                    symbol = " A "
                elif not cell.discovered:
                    symbol = " ? "
                else:
                    t = cell.terrain_name[0].upper()
                    r = str(len(cell.resources)) if cell.resources else " "
                    symbol = f" {t}{r}"

                row_str += symbol + "║"

            print(row_str)
            if y < self.height - 1:
                print("╠" + "═══╬" * (self.width - 1) + "═══╣")

        print("╚" + "═══╩" * (self.width - 1) + "═══╝")
        print("\nLegend: A=Agent, ?=Undiscovered, F=Forest, R=Ruins/River, P=Plains, M=Mountains")
        print("        Number = Resource count in cell\n")
