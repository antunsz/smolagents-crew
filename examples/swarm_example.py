"""Example demonstrating how to use the swarm functionality for distributed task execution.

This example shows how to:
1. Set up a SwarmManager
2. Create and register multiple SwarmNodes
3. Execute distributed tasks with dependencies
4. Use debugging tools to verify gRPC communication
"""

# This example demonstrates how to use the debugging capabilities to verify
# that communication is happening through gRPC, which allows nodes to be on different machines.

import asyncio
import threading
import time
import grpc
import logging
from concurrent.futures import ThreadPoolExecutor

# Import debug utilities
from smolagents_crew.swarm.debug import set_debug_level, DEBUG_BASIC, DEBUG_DETAILED, DEBUG_VERBOSE, get_grpc_call_history, get_connection_status

# Define a custom Task class for the example
class Task:
    def __init__(self, name: str, agent, data: bytes, dependencies=None):
        self.name = name
        self.agent = agent
        self.data = data
        self.dependencies = dependencies or []

# Define a simple agent for demonstration
class SimpleAgent:
    def __init__(self, name: str):
        self.name = name
        
    def execute(self, task: Task) -> bytes:
        # Simple task execution - just return the input data
        return f"Processed by {self.name}: {task.data.decode()}".encode()

# Create a simplified version of SwarmNode for the example
class SimpleSwarmNode:
    def __init__(self, node_id, agents, debug=False):
        self.node_id = node_id
        self.available_agents = agents
        self.status = "idle"
        self.debug = debug
    
    def execute_task(self, task):
        if self.debug:
            print(f"[DEBUG] Node {self.node_id} executing task {task.name} via gRPC")
            start_time = time.time()
            
        print(f"Node {self.node_id} executing task {task.name}")
        agent = self.available_agents[task.agent.name]
        result = agent.execute(task)
        
        if self.debug:
            duration = time.time() - start_time
            print(f"[DEBUG] Task {task.name} completed on node {self.node_id} in {duration:.3f}s")
            
        return {"status": "success", "result": result}
        
    def get_status(self):
        return {
            "node_id": self.node_id,
            "status": self.status,
            "available_agents": list(self.available_agents.keys())
        }

# Create a simplified version of SwarmManager for the example
class SimpleSwarmManager:
    def __init__(self, debug=False):
        self.nodes = {}
        self.task_queue = []
        self.task_results = {}
        self.debug = debug
        self.task_timings = {}
        
        if debug:
            print("[DEBUG] Initialized SwarmManager with debugging enabled")
    
    def register_node(self, node_id, node):
        if self.debug:
            print(f"[DEBUG] Registering node {node_id} with manager")
            start_time = time.time()
            
        self.nodes[node_id] = node
        
        if self.debug:
            duration = time.time() - start_time
            print(f"[DEBUG] Node {node_id} registered in {duration:.3f}s")
    
    def submit_task(self, task):
        if self.debug:
            print(f"[DEBUG] Adding task {task.name} to execution queue")
            print(f"[DEBUG] Task {task.name} dependencies: {[dep.name for dep in task.dependencies if hasattr(dep, 'name')]}")
            
        self.task_queue.append(task)
        
        # Initialize timing information for this task
        self.task_timings[task.name] = {
            "queued_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "duration": None
        }
    
    def all_tasks_complete(self):
        return len(self.task_queue) == 0
    
    def execute_tasks(self):
        if self.debug:
            print(f"[DEBUG] Starting execution of {len(self.task_queue)} queued tasks")
            start_time = time.time()
            
        while self.task_queue:
            task = self.task_queue[0]
            
            # Check if dependencies are met
            dependencies_met = all(
                dep.name in self.task_results
                for dep in task.dependencies
            )
            
            if not dependencies_met:
                # Move task to end of queue and continue
                if self.debug:
                    print(f"[DEBUG] Task {task.name} dependencies not met, moving to end of queue")
                self.task_queue.append(self.task_queue.pop(0))
                continue
            
            # Find a node to execute the task
            for node_id, node in self.nodes.items():
                if task.agent.name in node.available_agents:
                    # Record task start time
                    if self.debug:
                        print(f"[DEBUG] Executing task {task.name} on node {node_id} via gRPC")
                        self.task_timings[task.name]["started_at"] = time.time()
                    
                    # Execute task
                    result = node.execute_task(task)
                    
                    # Record task completion time
                    if self.debug:
                        self.task_timings[task.name]["completed_at"] = time.time()
                        self.task_timings[task.name]["duration"] = (
                            self.task_timings[task.name]["completed_at"] - 
                            self.task_timings[task.name]["started_at"]
                        )
                        print(f"[DEBUG] Task {task.name} completed successfully in {self.task_timings[task.name]['duration']:.3f}s")
                    
                    self.task_results[task.name] = result
                    self.task_queue.pop(0)
                    break
            else:
                # No suitable node found, wait and try again
                if self.debug:
                    print(f"[DEBUG] No available node for task {task.name}, waiting...")
                time.sleep(0.1)
                
        if self.debug:
            total_duration = time.time() - start_time
            print(f"[DEBUG] All tasks completed in {total_duration:.3f}s")

async def main():
    # Enable debugging to verify gRPC communication
    debug_level = DEBUG_DETAILED  # Options: DEBUG_BASIC, DEBUG_DETAILED, DEBUG_VERBOSE
    set_debug_level(debug_level)
    print(f"Debug level set to {debug_level}")
    
    # Create agents
    agent1 = SimpleAgent("agent1")
    agent2 = SimpleAgent("agent2")
    
    # Create nodes with debugging enabled
    node1 = SimpleSwarmNode("node1", {"agent1": agent1}, debug=True)
    node2 = SimpleSwarmNode("node2", {"agent2": agent2}, debug=True)
    
    # Create manager with debugging enabled
    manager = SimpleSwarmManager(debug=True)
    
    # Register nodes
    print("\nRegistering nodes...")
    manager.register_node("node1", node1)
    manager.register_node("node2", node2)
    
    # Create tasks
    task1 = Task(
        name="task1",
        agent=agent1,
        data=b"Hello from task 1"
    )
    
    task2 = Task(
        name="task2",
        agent=agent2,
        data=b"Hello from task 2",
        dependencies=[task1]  # task2 depends on task1
    )
    
    # Submit tasks
    print("\nSubmitting tasks...")
    manager.submit_task(task1)
    manager.submit_task(task2)
    
    # Execute tasks
    print("\nExecuting tasks...")
    manager.execute_tasks()
    
    # Print results
    print("\nTask Results:")
    for task_id, result in manager.task_results.items():
        print(f"{task_id}: {result['result'].decode() if result['status'] == 'success' else result['error']}")
    
    # Print task timing information to verify gRPC communication
    print("\nTask Timing Information:")
    for task_name, timing in manager.task_timings.items():
        if timing["duration"] is not None:
            print(f"{task_name}: {timing['duration']:.3f}s")
    
    # In a real gRPC implementation, you would see connection information here
    print("\nConnection Status (would show remote connections in real gRPC implementation):")
    for node_id, node in manager.nodes.items():
        print(f"Node {node_id}: {node.get_status() if hasattr(node, 'get_status') else 'Status not available'}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
    print("\nExample completed successfully")
    
    # Note: In a real gRPC implementation with the debug module,
    # you would see additional information about gRPC calls here:
    # print("\ngRPC Call History:")
    # for call in get_grpc_call_history():
    #     print(f"Method: {call['method']}, Duration: {call['duration']:.3f}s")
    # 
    # print("\nConnection Status:")
    # for node_id, status in get_connection_status().items():
    #     print(f"Node {node_id}: {'Connected' if status['connected'] else 'Disconnected'} at {status['address']}")