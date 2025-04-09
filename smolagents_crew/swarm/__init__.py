"""Swarm module for distributed task execution in SmolagentsCrew.

This module extends the core functionality of SmolagentsCrew to support distributed
task execution across multiple nodes while maintaining the dependency management
and context sharing capabilities of the base system.
"""

from .crew import SwarmCrew
from .node import SwarmNode
from .manager import SwarmManager
from .server import serve
from .diagnostics import RemoteVerifier, TaskTracker

__all__ = ["SwarmManager", "SwarmNode", "SwarmCrew", "serve", "RemoteVerifier", "TaskTracker"]