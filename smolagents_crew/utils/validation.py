"""Validation utilities for SmolagentsCrew.

This module provides functions for validating dependencies and configurations
used throughout the framework.
"""

from typing import Dict, Any, List
import importlib


def validate_dependencies(required_packages: List[str]) -> Dict[str, bool]:
    """Validate that required packages are installed and available.

    Args:
        required_packages: List of package names to validate.

    Returns:
        Dictionary mapping package names to their availability status.
    """
    status = {}
    for package in required_packages:
        try:
            importlib.import_module(package)
            status[package] = True
        except ImportError:
            status[package] = False
    return status


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """Validate that a configuration dictionary contains all required keys.

    Args:
        config: Configuration dictionary to validate.
        required_keys: List of required keys that must be present.

    Returns:
        True if all required keys are present, False otherwise.
    """
    return all(key in config for key in required_keys)