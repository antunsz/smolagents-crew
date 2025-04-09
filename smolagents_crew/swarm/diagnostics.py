"""Diagnostics module for SwarmCrew remote execution verification.

This module provides utilities for verifying and debugging distributed task execution
across remote nodes, ensuring proper task distribution and communication.

Classes:
    RemoteVerifier: Main class for verifying remote task execution
    TaskTracker: Helper class for tracking task execution details
    
Examples:
    >>> from smolagents_crew.swarm.diagnostics import RemoteVerifier
    >>> verifier = RemoteVerifier(crew)
    >>> task_log = verifier.setup_verification()
    >>> # Run your crew execution
    >>> verifier.print_summary(task_log)
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from functools import wraps

from .debug import (
    set_debug_level, DEBUG_BASIC, DEBUG_DETAILED, DEBUG_VERBOSE,
    get_grpc_call_history, get_connection_status, clear_history
)
from ..core import Task

# Configure module logger
logger = logging.getLogger(__name__)

class TaskTracker:
    """Helper class for tracking task execution across nodes.
    
    This class maintains the execution state of tasks across different nodes,
    recording timing and node assignment information.
    """
    
    def __init__(self):
        """Initialize a new task tracker."""
        self.tasks: Dict[str, Dict[str, Any]] = {}
        
    def start_task(self, task_name: str, node_id: str, agent_name: Optional[str] = None) -> None:
        """Record the start of a task execution.
        
        Args:
            task_name: Name of the task being executed
            node_id: ID of the node executing the task
            agent_name: Name of the agent executing the task, if available
        """
        self.tasks[task_name] = {
            "node": node_id,
            "agent": agent_name or "unknown",
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "status": "running"
        }
        
    def complete_task(self, task_name: str, success: bool = True) -> None:
        """Record the completion of a task execution.
        
        Args:
            task_name: Name of the task that completed
            success: Whether the task completed successfully
        """
        if task_name not in self.tasks:
            logger.warning(f"Attempted to complete unknown task: {task_name}")
            return
            
        self.tasks[task_name]["end_time"] = time.time()
        self.tasks[task_name]["duration"] = (
            self.tasks[task_name]["end_time"] - 
            self.tasks[task_name]["start_time"]
        )
        self.tasks[task_name]["status"] = "completed" if success else "failed"
        
    def get_task_info(self, task_name: str) -> Dict[str, Any]:
        """Get information about a tracked task.
        
        Args:
            task_name: Name of the task to get information for
            
        Returns:
            Dictionary containing task execution information
        """
        return self.tasks.get(task_name, {})
        
    def get_tasks_by_node(self) -> Dict[str, List[str]]:
        """Group tasks by the node that executed them.
        
        Returns:
            Dictionary mapping node IDs to lists of task names
        """
        result = {}
        for task_name, info in self.tasks.items():
            node_id = info["node"]
            if node_id not in result:
                result[node_id] = []
            result[node_id].append(task_name)
        return result
        
    def get_remote_tasks(self, local_node_id: str = "local") -> List[str]:
        """Get list of tasks that executed on remote nodes.
        
        Args:
            local_node_id: ID of the local node (default: "local")
            
        Returns:
            List of task names that executed on remote nodes
        """
        return [task_name for task_name, info in self.tasks.items() 
                if info["node"] != local_node_id]


class RemoteVerifier:
    """Main class for verifying and debugging remote task execution.
    
    This class provides utilities for monitoring, verifying, and debugging
    distributed task execution across remote nodes.
    """
    
    def __init__(self, crew, debug_level: int = DEBUG_DETAILED):
        """Initialize a remote execution verifier.
        
        Args:
            crew: The SwarmCrew instance to monitor
            debug_level: Debug level to use (from debug module)
        """
        self.crew = crew
        self.debug_level = debug_level
        self.tracker = TaskTracker()
        
    def setup_verification(self) -> TaskTracker:
        """Set up verification for remote task execution.
        
        Enables detailed logging and tracking of task execution across nodes.
        
        Returns:
            TaskTracker instance for tracking task execution
        """
        # Enable detailed debugging
        set_debug_level(self.debug_level)
        
        # Clear previous debug history
        clear_history()
        
        # Log initial state
        initial_calls = get_grpc_call_history()
        logger.info(f"Starting with {len(initial_calls)} recorded gRPC calls")
        
        # Patch node execution methods to track task execution
        self._patch_nodes()
        
        # Patch SwarmManager.execute_tasks to add detailed logging
        self._patch_manager()
        
        return self.tracker
        
    def _patch_nodes(self) -> None:
        """Patch node execute_task methods to track task execution."""
        for node_id, node in self.crew.manager.nodes.items():
            original_execute = node.execute_task
            tracker = self.tracker  # Create a local reference for the closure
            
            @wraps(original_execute)
            def execute_with_tracking(task, context=None, _original=original_execute, 
                                     _node_id=node_id, _tracker=tracker):
                # Record task start
                task_name = task.name if hasattr(task, 'name') else str(task)
                agent_name = task.agent.name if hasattr(task, 'agent') and task.agent else None
                
                logger.info(f"⚡ Node {_node_id} executing task: {task_name}")
                _tracker.start_task(task_name, _node_id, agent_name)
                
                # Execute original method
                try:
                    result = _original(task, context)
                    success = result.get("status") == "success"
                    
                    # Record task completion
                    _tracker.complete_task(task_name, success)
                    
                    duration = _tracker.get_task_info(task_name).get("duration", 0)
                    logger.info(f"✅ Node {_node_id} completed task: {task_name} in {duration:.3f}s")
                    
                    return result
                except Exception as e:
                    # Record task failure
                    _tracker.complete_task(task_name, False)
                    logger.error(f"❌ Node {_node_id} failed task: {task_name} - {str(e)}")
                    raise
                    
            # Apply patched method
            node.execute_task = execute_with_tracking
            
    def _patch_manager(self) -> None:
        """Patch SwarmManager.execute_tasks method to add detailed logging."""
        original_execute = self.crew.manager.execute_tasks
        
        @wraps(original_execute)
        def execute_with_logging():
            logger.info("\n===== STARTING DISTRIBUTED TASK EXECUTION =====\n")
            
            # Log initial state
            logger.info(f"Task queue: {[t.name for t in self.crew.manager.task_queue]}")
            logger.info(f"Available nodes: {list(self.crew.manager.nodes.keys())}")
            
            # Log available agents on each node
            for node_id, node in self.crew.manager.nodes.items():
                logger.info(f"Node {node_id} has agents: {list(node.available_agents.keys())}")
            
            # Execute tasks
            start_time = time.time()
            try:
                results = original_execute()
                execution_time = time.time() - start_time
                logger.info(f"\n===== TASK EXECUTION COMPLETED IN {execution_time:.3f}s =====\n")
                return results
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"\n===== TASK EXECUTION FAILED AFTER {execution_time:.3f}s =====\n")
                logger.error(f"Error: {str(e)}")
                raise
                
        # Apply patched method
        self.crew.manager.execute_tasks = execute_with_logging
    
    def force_remote_execution(self, agent_name: str, local_node_id: str = "local") -> None:
        """Force a specific agent to only be available on remote nodes.
        
        This ensures tasks requiring this agent must execute remotely.
        
        Args:
            agent_name: Name of the agent to remove from local node
            local_node_id: ID of the local node (default: "local")
        """
        if local_node_id in self.crew.manager.nodes:
            local_node = self.crew.manager.nodes[local_node_id]
            
            if agent_name in local_node.available_agents:
                logger.info(f"Removing {agent_name} agent from {local_node_id} node to force remote execution")
                del local_node.available_agents[agent_name]
                
                # Verify agent availability after adjustment
                for node_id, node in self.crew.manager.nodes.items():
                    logger.info(f"Node {node_id} now has agents: {list(node.available_agents.keys())}")
            else:
                logger.warning(f"Agent {agent_name} not found on {local_node_id} node")
        else:
            logger.warning(f"Node {local_node_id} not found in crew manager")
    
    def print_summary(self, tracker: Optional[TaskTracker] = None) -> None:
        """Print a detailed summary of remote task execution.
        
        Args:
            tracker: TaskTracker instance to use, or None to use the internal tracker
        """
        tracker = tracker or self.tracker
        
        logger.info("\n===== REMOTE EXECUTION VERIFICATION SUMMARY =====\n")
        
        # Summarize task execution by node
        node_tasks = tracker.get_tasks_by_node()
        
        for node_id, tasks in node_tasks.items():
            logger.info(f"Node {node_id} executed {len(tasks)} tasks: {', '.join(tasks)}")
        
        # Check if any tasks executed on remote nodes
        remote_tasks = tracker.get_remote_tasks()
        
        if remote_tasks:
            logger.info(f"\n✓ VERIFIED: {len(remote_tasks)} tasks executed on remote nodes")
            for task_name in remote_tasks:
                info = tracker.get_task_info(task_name)
                logger.info(f"  - {task_name} executed on {info['node']} by {info['agent']} in {info['duration']:.3f}s")
        else:
            logger.info("\n❌ No tasks were executed on remote nodes!")
        
        # Analyze gRPC communication
        self._print_grpc_summary()
            
        logger.info("\n=============================================\n")
        
    def _print_grpc_summary(self) -> None:
        """Print summary of gRPC communication between nodes."""
        # Get gRPC call history
        calls = get_grpc_call_history()
        
        if calls:
            logger.info(f"\n✓ VERIFIED: {len(calls)} gRPC calls detected")
            
            # Group calls by method
            method_counts = {}
            for call in calls:
                method = call.get('method', 'unknown')
                if method not in method_counts:
                    method_counts[method] = 0
                method_counts[method] += 1
            
            for method, count in sorted(method_counts.items()):
                logger.info(f"  - {method}: {count} calls")
        else:
            logger.info("\n❌ No gRPC communication detected!")
        
        # Print connection status
        connections = get_connection_status()
        if connections:
            logger.info(f"\nNode Connections: {len(connections)}")
            for node_id, info in connections.items():
                status = "Connected" if info.get("connected", False) else "Disconnected"
                logger.info(f"  - {node_id} -> {info.get('address', 'unknown')}: {status}")
                
    def reset(self) -> None:
        """Reset the verifier state.
        
        Clears the task tracker and debug history.
        """
        self.tracker = TaskTracker()
        clear_history()
        logger.info("Remote verification state reset") 