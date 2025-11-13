"""
Convenience runner for the Aiden Agent package.

Run with:
	python run.py

This will execute the package module `aiden_agent.main` so it behaves
the same as `python -m aiden_agent.main`.
"""

import runpy


if __name__ == "__main__":
	# Execute the package's main module as a script
	runpy.run_module("aiden_agent.main", run_name="__main__")
