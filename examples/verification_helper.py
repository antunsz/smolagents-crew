# Set up debugging to verify remote execution
from smolagents_crew.swarm.debug import (
    set_debug_level, DEBUG_BASIC, DEBUG_DETAILED, DEBUG_VERBOSE,
    get_grpc_call_history, get_connection_status, clear_history
)
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("swarm_verification")

# This function sets up debugging for remote execution verification
def setup_remote_verification(crew):
    """Set up debugging to verify remote task execution.
    
    Args:
        crew: The SwarmCrew instance to monitor
        
    Returns:
        task_execution_log: Dictionary to track which node executes each task
    """
    # Enable detailed debugging for gRPC calls
    set_debug_level(DEBUG_DETAILED)
    
    # Clear previous history if any
    clear_history()
    
    # Store initial gRPC call state for comparison later
    initial_calls = get_grpc_call_history()
    logger.info(f"Starting with {len(initial_calls)} recorded gRPC calls")
    
    # Add task execution tracker to monitor which node executes each task
    task_execution_log = {}
    
    # Monkey patch SwarmManager.execute_tasks to add detailed logging
    original_execute_task = crew.manager.execute_tasks
    
    def debug_execute_tasks():
        """Wrapper for execute_tasks with detailed logging"""
        logger.info("\n===== STARTING DISTRIBUTED TASK EXECUTION =====\n")
        logger.info(f"Task queue at start: {[t.name for t in crew.manager.task_queue]}")
        logger.info(f"Available nodes: {list(crew.manager.nodes.keys())}")
        
        # Log available agents on each node
        for node_id, node in crew.manager.nodes.items():
            logger.info(f"Node {node_id} has agents: {list(node.available_agents.keys())}")
        
        # Patch node.execute_task to track which node executes what
        for node_id, node in crew.manager.nodes.items():
            original_node_execute = node.execute_task
            
            def node_execute_with_logging(task, context=None, _node_id=node_id, _original=original_node_execute):
                logger.info(f"⚡ Node {_node_id} executing task: {task.name}")
                task_execution_log[task.name] = {
                    "node": _node_id,
                    "agent": task.agent.name if hasattr(task, 'agent') and task.agent else 'unknown',
                    "start_time": time.time()
                }
                result = _original(task, context)
                task_execution_log[task.name]["end_time"] = time.time()
                task_execution_log[task.name]["duration"] = (
                    task_execution_log[task.name]["end_time"] - 
                    task_execution_log[task.name]["start_time"]
                )
                logger.info(f"✅ Node {_node_id} completed task: {task.name} in {task_execution_log[task.name]['duration']:.3f}s")
                return result
            
            node.execute_task = node_execute_with_logging
        
        # Run the original execution function
        results = original_execute_task()
        
        # Log execution completion
        logger.info("\n===== TASK EXECUTION COMPLETED =====\n")
        return results
    
    # Apply our debug wrapper
    crew.manager.execute_tasks = debug_execute_tasks
    
    return task_execution_log

# Function to force task distribution to remote node
def force_remote_execution(crew, agent_name):
    """Remove an agent from local node to force remote execution.
    
    Args:
        crew: The SwarmCrew instance
        agent_name: Name of the agent to remove from local node
    """
    if agent_name in crew.manager.nodes["local"].available_agents:
        logger.info(f"Removing {agent_name} agent from local node to force remote execution")
        del crew.manager.nodes["local"].available_agents[agent_name]

    # Verify agent availability after adjustment
    for node_id, node in crew.manager.nodes.items():
        logger.info(f"Node {node_id} now has agents: {list(node.available_agents.keys())}")

# Function to print a summary of the remote execution verification
def print_verification_summary(crew, task_log):
    """Print a summary of task execution across nodes.
    
    Args:
        crew: The SwarmCrew instance
        task_log: Dictionary with task execution logs
    """
    logger.info("\n===== REMOTE EXECUTION VERIFICATION SUMMARY =====\n")
    
    # Summarize task execution by node
    node_tasks = {}
    for task_name, info in task_log.items():
        node_id = info["node"]
        if node_id not in node_tasks:
            node_tasks[node_id] = []
        node_tasks[node_id].append(task_name)
    
    for node_id, tasks in node_tasks.items():
        logger.info(f"Node {node_id} executed {len(tasks)} tasks: {', '.join(tasks)}")
    
    # Check if any tasks executed on remote nodes
    remote_tasks = [t for node_id, tasks in node_tasks.items() 
                   for t in tasks if node_id != "local"]
    if remote_tasks:
        logger.info(f"\n✓ VERIFIED: {len(remote_tasks)} tasks executed on remote nodes")
        for task in remote_tasks:
            info = task_log[task]
            logger.info(f"  - {task} executed on {info['node']} by {info['agent']} in {info['duration']:.3f}s")
    else:
        logger.info("\n❌ No tasks were executed on remote nodes!")
    
    # Get gRPC call history
    calls = get_grpc_call_history()
    new_calls = len(calls)
    
    if new_calls > 0:
        logger.info(f"\n✓ VERIFIED: {new_calls} gRPC calls detected")
        
        # Group calls by method
        method_counts = {}
        for call in calls:
            method = call.get('method', 'unknown')
            if method not in method_counts:
                method_counts[method] = 0
            method_counts[method] += 1
        
        for method, count in method_counts.items():
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
    
    logger.info("\n=============================================\n")
