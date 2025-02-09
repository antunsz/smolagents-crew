"""SmolagentsCrew - A framework for building and managing agent-based systems using HF Smolagents as base.

This package provides tools and utilities for creating and managing crews of AI agents
that can work together to accomplish complex tasks.
"""

__version__ = "0.1.0"

from .core import Task, Agent, Crew, TaskDependency
from .builder import CrewBuilder

__all__ = ['Task', 'Agent', 'Crew', 'TaskDependency', 'CrewBuilder']