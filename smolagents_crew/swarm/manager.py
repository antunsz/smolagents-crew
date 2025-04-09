"""SwarmManager module for coordinating distributed task execution.

This module provides the SwarmManager class that handles task distribution,
node coordination, and result synchronization across the distributed system.
"""

import time
from typing import Dict, List, Any, Optional
from ..core import Task
from .node import SwarmNode
from .debug import log_grpc_call, get_debug_level, DEBUG_NONE, DEBUG_BASIC, DEBUG_DETAILED

class SwarmManager:
    """A class for managing distributed task execution across multiple nodes.
    
    Handles task distribution, node coordination, and result synchronization.
    Maintains the dependency graph and ensures proper task execution order.
    """
    
    def __init__(self, debug: bool = False):
        """Initialize a SwarmManager.
        
        Args:
            debug: Whether to enable debugging for this manager
        """
        self.nodes: Dict[str, SwarmNode] = {}
        self.task_queue: List[Task] = []
        self.task_results: Dict[str, Any] = {}
        self.debug = debug
        self.task_timings: Dict[str, Dict[str, float]] = {}
        
        if debug and get_debug_level() >= DEBUG_BASIC:
            print("Initialized SwarmManager with debugging enabled")
        
    def register_node(self, node: SwarmNode) -> None:
        """Register a new node with the manager.
        
        Args:
            node: The SwarmNode to register
        """
        if self.debug:
            print(f"Registering node {node.node_id} with manager")
            start_time = time.time()
            
        self.nodes[node.node_id] = node
        
        if self.debug:
            duration = time.time() - start_time
            print(f"Node {node.node_id} registered in {duration:.3f}s")
            if get_debug_level() >= DEBUG_DETAILED:
                print(f"Available agents on node {node.node_id}: {list(node.available_agents.keys())}")
        
    def unregister_node(self, node_id: str) -> None:
        """Remove a node from the manager.
        
        Args:
            node_id: ID of the node to remove
        """
        if self.debug:
            print(f"Unregistering node {node_id} from manager")
            
        if node_id in self.nodes:
            del self.nodes[node_id]
            
            if self.debug:
                print(f"Node {node_id} unregistered successfully")
        elif self.debug:
            print(f"Node {node_id} not found in manager")
            
    def add_task(self, task: Task) -> None:
        """Add a task to the execution queue.
        
        Args:
            task: The task to add
        """
        if self.debug:
            print(f"Adding task {task.name} to execution queue")
            if get_debug_level() >= DEBUG_DETAILED:
                print(f"Task {task.name} dependencies: {[dep.task_name for dep in task.dependencies]}")
                
        self.task_queue.append(task)
        
        # Initialize timing information for this task
        self.task_timings[task.name] = {
            "queued_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "duration": None
        }
        
    def get_available_node(self, task: Task) -> Optional[SwarmNode]:
        """Find an available node that can execute the given task.
        
        Args:
            task: The task to find a node for
            
        Returns:
            An available node or None if no suitable node is found
        """
        if self.debug and get_debug_level() >= DEBUG_DETAILED:
            print(f"Finding available node for task {task.name} (agent: {task.agent.name})")
            
        for node in self.nodes.values():
            if (node.status == "idle" and 
                task.agent.name in node.available_agents):
                if self.debug:
                    print(f"Found available node {node.node_id} for task {task.name}")
                return node
                
        if self.debug:
            print(f"No available node found for task {task.name}")
        return None
        
    def execute_tasks(self) -> Dict[str, Any]:
        """Execute all queued tasks across available nodes.
        
        Returns:
            Dictionary containing all task results
        """
        if self.debug:
            print(f"Starting execution of {len(self.task_queue)} queued tasks")
            start_time = time.time()
            
        while self.task_queue:
            task = self.task_queue[0]
            
            # Check if task dependencies are met
            dependencies_met = all(
                dep.source_task in self.task_results
                for dep in task.dependencies
            )
            
            if not dependencies_met:
                # Move task to end of queue and continue
                if self.debug and get_debug_level() >= DEBUG_DETAILED:
                    print(f"Task {task.name} dependencies not met, moving to end of queue")
                self.task_queue.append(self.task_queue.pop(0))
                continue
                
            # Find available node for task
            node = self.get_available_node(task)
            if not node:
                if self.debug and get_debug_level() >= DEBUG_DETAILED:
                    print(f"No available node for task {task.name}, waiting...")
                time.sleep(0.1)
                continue
                
            # Record task start time
            if self.debug:
                print(f"Executing task {task.name} on node {node.node_id}")
                self.task_timings[task.name]["started_at"] = time.time()
                
            # Build context with dependency results and all available results
            # This ensures all task results are available to all subsequent tasks
            context = self.task_results.copy()  # Include all previous results
            
            # Add specific dependency results to ensure they're available
            for dep in task.dependencies:
                if dep.source_task in self.task_results:
                    context[dep.result_key] = self.task_results[dep.source_task]
                else:
                    if self.debug:
                        print(f"Warning: Dependency {dep.source_task} not found in task_results")
            
            # Log context keys for debugging
            if self.debug and get_debug_level() >= DEBUG_DETAILED:
                print(f"Context keys for task {task.name}: {list(context.keys())}")
            
            # Execute task with context and store result
            result = node.execute_task(task, context)
            
            # Record task completion time
            if self.debug:
                self.task_timings[task.name]["completed_at"] = time.time()
                self.task_timings[task.name]["duration"] = (
                    self.task_timings[task.name]["completed_at"] - 
                    self.task_timings[task.name]["started_at"]
                )
                
            if result["status"] == "success":
                if self.debug:
                    print(f"Task {task.name} completed successfully in {self.task_timings[task.name]['duration']:.3f}s")
                self.task_results[task.name] = result["result"]
                self.task_queue.pop(0)
            else:
                error_msg = f"Task {task.name} failed: {result['error']}"
                if self.debug:
                    print(f"ERROR: {error_msg}")
                raise RuntimeError(error_msg)
                
        if self.debug:
            total_duration = time.time() - start_time
            print(f"All tasks completed in {total_duration:.3f}s")
            
        return self.task_results
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get the current status of the distributed system.
        
        Returns:
            Dictionary containing system status information
        """
        status = {
            "nodes": {
                node_id: node.get_status()
                for node_id, node in self.nodes.items()
            },
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.task_results)
        }
        
        # Add task timing information if debugging is enabled
        if self.debug:
            status["task_timings"] = self.task_timings
            
            # Calculate additional statistics
            if self.task_timings:
                completed_tasks = [t for t in self.task_timings.values() if t["duration"] is not None]
                if completed_tasks:
                    avg_duration = sum(t["duration"] for t in completed_tasks) / len(completed_tasks)
                    status["average_task_duration"] = avg_duration
                    status["max_task_duration"] = max(t["duration"] for t in completed_tasks)
                    status["min_task_duration"] = min(t["duration"] for t in completed_tasks)
        
        return status