"""SwarmNode module for handling individual node operations in the distributed system.

This module provides the SwarmNode class that represents a single node in the distributed
system, handling task execution, resource management, and communication with the SwarmManager.
"""

from typing import Dict, Any, Optional
import time  # Ensure time module is imported
from ..core import Task, Agent

class SwarmNode:
    """A class representing a single node in the distributed system.
    
    Handles task execution, resource management, and communication with the SwarmManager.
    Each node can execute tasks independently while maintaining synchronization with
    the overall system through the SwarmManager.
    """
    
    def __init__(self, node_id: str, available_agents: Dict[str, Agent]):
        """Initialize a SwarmNode.
        
        Args:
            node_id: Unique identifier for this node
            available_agents: Dictionary of agents available on this node
        """
        self.node_id = node_id
        self.available_agents = available_agents
        self.current_task: Optional[Task] = None
        self.status = "idle"
        
    def execute_task(self, task: Task, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task on this node.
        
        Args:
            task: The task to execute
            context: Context dictionary containing dependency results
            
        Returns:
            Dictionary with execution result
        """
        start_time = time.time()
        
        # Get the agent for this task
        agent_name = task.agent.name
        if agent_name not in self.available_agents:
            return {
                'status': 'error',
                'error': f"Agent {agent_name} not found on node {self.node_id}"
            }
        
        agent = self.available_agents[agent_name]
        
        try:
            # Use provided context or create a new one
            context = context or {}
            
            # Check if all required variables are in the context
            required_vars = task._extract_template_vars()
            missing_vars = [var for var in required_vars if var not in context]
            
            if missing_vars:
                return {
                    'status': 'error',
                    'error': f"Task {task.name} is missing required variables: {missing_vars}. Available context keys: {list(context.keys())}"
                }
            
            # Format the prompt template with the context
            try:
                prompt = task.prompt_template.format(**context)
            except KeyError as e:
                return {
                    'status': 'error',
                    'error': f"Missing variable in template: {e}. Available context keys: {list(context.keys())}"
                }
            
            # Execute the task using the agent's run method
            result = agent.run(prompt)
            
            return {
                'status': 'success',
                'result': result,
                'duration': time.time() - start_time
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'duration': time.time() - start_time
            }
            
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of this node.
        
        Returns:
            Dictionary containing node status information
        """
        return {
            "node_id": self.node_id,
            "status": self.status,
            "current_task": self.current_task.name if self.current_task else None,
            "available_agents": list(self.available_agents.keys())
        }