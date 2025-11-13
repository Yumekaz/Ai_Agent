"""
Main entry point for Aiden Agent simulation
Run this from the parent directory: python -m aiden_agent.main
Or use the run.py script in the parent directory
"""

import sys
import os

# Add parent directory to path to allow absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiden_agent.agent.autonomous_agent import AutonomousAgent


if __name__ == "__main__":
    # Create agent with cognitive drift
    agent = AutonomousAgent(name="Aiden", memory_file="aiden_cognitive_drift_memory.json")
    
    # Run simulation
    agent.run_simulation(cycles=50)
    
    print("\n✨ Simulation complete. Aiden's personality has evolved through experience.\n")