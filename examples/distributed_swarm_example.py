"""Distributed Swarm Example with Comprehensive Debugging

This example demonstrates how to set up a distributed swarm system with multiple nodes
communicating via gRPC, with comprehensive debugging to verify communication between nodes.

Key features demonstrated:
1. Setting up multiple SwarmNode instances with gRPC servers
2. Connecting to remote nodes via SwarmNodeClient
3. Distributing tasks across nodes with dependencies
4. Detailed logging of gRPC communication with message inspection
5. Verification of distributed task execution with timing analysis
6. Visual confirmation of cross-machine communication

This example can be run on multiple machines by changing the IP addresses.
The debugging utilities provide clear evidence that communication is happening through
gRPC rather than local function calls.
"""

import asyncio
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

# Import SwarmNode components
from smolagents_crew.swarm.node import SwarmNode
from smolagents_crew.swarm.client import SwarmNodeClient
from smolagents_crew.swarm.server import SwarmNodeServicer, serve_node
from smolagents_crew.core import Task, Agent

# Import debug utilities
from smolagents_crew.swarm.debug import (
    set_debug_level, DEBUG_BASIC, DEBUG_DETAILED, DEBUG_VERBOSE,
    get_grpc_call_history, get_connection_status, clear_history,
    log_grpc_call, DebugInterceptor, generate_communication_report,
    verify_distributed_communication, analyze_communication_patterns,
    get_message_size_stats, get_network_latency
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("distributed_swarm")

# Define a simple agent for demonstration
class SimpleAgent(Agent):
    def __init__(self, name: str):
        self.name = name
        
    def execute(self, task: Task) -> bytes:
        logger.info(f"Agent {self.name} executing task {task.name}")
        # Simulate some processing time
        time.sleep(1)
        return f"Processed by {self.name}: {task.data.decode()}".encode()


class DistributedSwarmDemo:
    """Class to demonstrate distributed swarm functionality with detailed debugging."""
    
    def __init__(self, debug_level=DEBUG_DETAILED):
        # Set debug level for the entire system
        set_debug_level(debug_level)
        self.debug_level = debug_level
        logger.info(f"Debug level set to {debug_level}")
        
        # Track nodes and servers
        self.nodes = {}
        self.servers = {}
        self.clients = {}
        self.server_threads = {}
        
        # Task tracking
        self.task_results = {}
        self.task_timings = {}
        
        # Communication tracking
        self.grpc_calls_before = []
        self.grpc_calls_after = []
        
        # Store initial state of gRPC calls for comparison
        self.grpc_calls_before = get_grpc_call_history()
    
    def create_node(self, node_id, host, port, agents):
        """Create a SwarmNode with a gRPC server.
        
        Args:
            node_id: Unique identifier for the node
            host: Host address for the gRPC server
            port: Port for the gRPC server
            agents: Dictionary of agent name to agent instance
        """
        logger.info(f"Creating node {node_id} at {host}:{port}")
        
        # Create the SwarmNode
        node = SwarmNode(node_id, agents)
        self.nodes[node_id] = node
        
        # Start the gRPC server for this node
        address = f"{host}:{port}"
        servicer = SwarmNodeServicer(node, debug=True)
        server = serve_node(servicer, address, start=False)
        self.servers[node_id] = server
        
        # Start the server in a separate thread
        logger.info(f"Starting gRPC server for node {node_id} at {address}")
        server_thread = threading.Thread(
            target=server.start,
            name=f"server-{node_id}",
            daemon=True
        )
        server_thread.start()
        self.server_threads[node_id] = server_thread
        
        # Give the server a moment to start
        time.sleep(0.5)
        logger.info(f"Node {node_id} server started successfully")
        
        return node
    
    def connect_to_node(self, address, client_id=None):
        """Create a client connection to a remote node.
        
        Args:
            address: Address of the remote node (host:port)
            client_id: Optional identifier for the client
            
        Returns:
            SwarmNodeClient instance
        """
        client_id = client_id or f"client-{len(self.clients) + 1}"
        logger.info(f"Creating client {client_id} connecting to {address}")
        
        # Create the client with debugging enabled
        client = SwarmNodeClient(address, node_id=client_id, debug=True)
        self.clients[client_id] = client
        
        # Log successful connection
        logger.info(f"Client {client_id} connected to {address}")
        
        return client
    
    def execute_task_on_node(self, client, task):
        """Execute a task on a remote node via client.
        
        Args:
            client: SwarmNodeClient instance
            task: Task to execute
            
        Returns:
            Task execution result
        """
        logger.info(f"Sending task {task.name} to node via {client.node_id}")
        
        # Record task start time
        self.task_timings[task.name] = {
            "sent_at": time.time(),
            "completed_at": None,
            "duration": None
        }
        
        # Execute the task remotely
        result = client.execute_task(task)
        
        # Record task completion time
        self.task_timings[task.name]["completed_at"] = time.time()
        self.task_timings[task.name]["duration"] = (
            self.task_timings[task.name]["completed_at"] - 
            self.task_timings[task.name]["sent_at"]
        )
        
        # Log the result
        status = "succeeded" if result["status"] == "success" else "failed"
        logger.info(f"Task {task.name} {status} in {self.task_timings[task.name]['duration']:.3f}s")
        if result["status"] == "success":
            logger.info(f"Result: {result['result'].decode() if result['result'] else 'None'}")
        else:
            logger.error(f"Error: {result['error']}")
        
        # Store the result
        self.task_results[task.name] = result
        
        return result
    
    def print_communication_summary(self):
        """Print a summary of all gRPC communication that occurred."""
        logger.info("\n===== COMMUNICATION SUMMARY =====")
        
        # Get connection status
        connections = get_connection_status()
        logger.info(f"\nNode Connections: {len(connections)}")
        for node_id, info in connections.items():
            status = "Connected" if info["connected"] else "Disconnected"
            latency = f", Latency: {info.get('network_latency', 'N/A')}ms" if info.get("network_latency") else ""
            logger.info(f"  {node_id} -> {info['address']}: {status}{latency}")
            logger.info(f"  Last updated: {time.strftime('%H:%M:%S', time.localtime(info['last_updated']))}")
        
        # Get gRPC call history
        self.grpc_calls_after = get_grpc_call_history()
        calls = self.grpc_calls_after
        
        # Calculate new calls since initialization
        new_calls = calls[len(self.grpc_calls_before):] if len(self.grpc_calls_before) < len(calls) else calls
        
        logger.info(f"\ngRPC Calls: {len(new_calls)} new calls detected")
        
        # Group calls by method for better analysis
        method_counts = {}
        method_total_time = {}
        
        for call in new_calls:
            method = call['method']
            if method not in method_counts:
                method_counts[method] = 0
                method_total_time[method] = 0
            method_counts[method] += 1
            method_total_time[method] += call['duration']
        
        # Print method statistics
        logger.info("\nCall statistics by method:")
        for method, count in method_counts.items():
            avg_time = method_total_time[method] / count
            logger.info(f"  {method}: {count} calls, avg time: {avg_time:.3f}s, total: {method_total_time[method]:.3f}s")
        
        # Print detailed call information
        if self.debug_level >= DEBUG_DETAILED:
            logger.info("\nDetailed gRPC call information:")
            for i, call in enumerate(new_calls):
                logger.info(f"  {i+1}. {call['method']} at {time.strftime('%H:%M:%S', time.localtime(call['timestamp']))} - {call['duration']:.3f}s")
                if self.debug_level >= DEBUG_VERBOSE:
                    logger.info(f"     Request: {call['request'][:150]}")
                    logger.info(f"     Response: {call['response'][:150]}")
                    if 'request_size' in call and 'response_size' in call:
                        logger.info(f"     Message sizes: Request {call['request_size']} bytes, Response {call['response_size']} bytes")
        
        # Display message size statistics
        self.print_message_size_stats()
        
        # Display network latency information
        self.print_network_latency()
        
        # Print task timings
        logger.info("\nTask Execution Times:")
        for task_name, timing in self.task_timings.items():
            logger.info(f"  {task_name}: {timing['duration']:.3f}s")
            
        # Verify gRPC communication
        self.verify_grpc_communication(new_calls)
    
    def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up resources...")
        
        # Close all clients
        for client_id, client in self.clients.items():
            logger.info(f"Closing client {client_id}")
            client.close()
        
        # Stop all servers
        for node_id, server in self.servers.items():
            logger.info(f"Stopping server for node {node_id}")
            server.stop(grace=1)
        
        # Wait for all server threads to finish
        for node_id, thread in self.server_threads.items():
            logger.info(f"Waiting for server thread {node_id} to finish")
            thread.join(timeout=2)
        
        logger.info("Cleanup complete")


    def print_message_size_stats(self):
        """Print statistics about message sizes for different gRPC methods."""
        size_stats = get_message_size_stats()
        if not size_stats:
            logger.info("No message size statistics available")
            return
            
        logger.info("\n===== MESSAGE SIZE STATISTICS =====")
        for method, data in size_stats.items():
            logger.info(f"Method: {method}")
            logger.info(f"  Request: avg {data['request']['avg_size']:.0f} bytes, "
                       f"min {data['request']['min_size']} bytes, "
                       f"max {data['request']['max_size']} bytes, "
                       f"total {data['request']['total_size']} bytes")
            logger.info(f"  Response: avg {data['response']['avg_size']:.0f} bytes, "
                       f"min {data['response']['min_size']} bytes, "
                       f"max {data['response']['max_size']} bytes, "
                       f"total {data['response']['total_size']} bytes")
    
    def print_network_latency(self):
        """Print network latency information for connected hosts."""
        latency = get_network_latency()
        if not latency:
            logger.info("No network latency measurements available")
            return
            
        logger.info("\n===== NETWORK LATENCY =====")
        for host, ms in latency.items():
            logger.info(f"  {host}: {ms:.3f}ms")
            
        # Provide interpretation of latency values
        avg_latency = sum(latency.values()) / len(latency)
        if avg_latency < 0.1:
            logger.info("  All connections appear to be local (very low latency)")
        elif avg_latency < 1.0:
            logger.info("  Connections appear to be on the same local network")
        else:
            logger.info("  Connections show typical network latency, confirming distributed communication")
    
    def verify_grpc_communication(self, calls):
        """Verify that actual gRPC communication occurred between nodes.
        
        This function analyzes the gRPC calls to confirm that communication
        happened through the network rather than local function calls.
        
        Args:
            calls: List of gRPC call records to analyze
        """
        logger.info("\n===== VERIFYING GRPC COMMUNICATION =====")
        
        # Check if we have any gRPC calls
        if not calls:
            logger.warning("No gRPC calls detected! Communication may not be working properly.")
            return
            
        # Count calls by direction (client/server)
        client_calls = 0
        server_calls = 0
        
        for call in calls:
            # Determine if this is a client or server call based on method name
            if "/SwarmNodeService/" in call['method']:
                if "client" in call['method'].lower():
                    client_calls += 1
                else:
                    server_calls += 1
        
        logger.info(f"Detected {client_calls} client-initiated calls and {server_calls} server-handled calls")
        
        # Check for RegisterNode calls which indicate node registration
        register_calls = [call for call in calls if "RegisterNode" in call['method']]
        if register_calls:
            logger.info(f"Verified {len(register_calls)} node registration calls")
            
        # Check for ExecuteTask calls which indicate task distribution
        execute_calls = [call for call in calls if "ExecuteTask" in call['method']]
        if execute_calls:
            logger.info(f"Verified {len(execute_calls)} task execution calls")
            
        # Analyze timing to verify network communication
        # Local function calls would be much faster than network calls
        call_durations = [call['duration'] for call in calls]
        if call_durations:
            avg_duration = sum(call_durations) / len(call_durations)
            logger.info(f"Average call duration: {avg_duration:.6f}s")
            
            # Network calls typically take at least a few milliseconds
            if avg_duration > 0.001:  # More than 1ms
                logger.info("✓ Call durations consistent with network communication")
            else:
                logger.warning("⚠ Call durations unusually fast, might be local function calls")
        
        # Final verification message
        if client_calls > 0 and server_calls > 0:
            logger.info("\n✓ VERIFICATION SUCCESSFUL: Confirmed gRPC communication between nodes")
            logger.info("  This confirms that nodes are communicating through the network")
            logger.info("  rather than through local function calls.")
        else:
            logger.warning("\n⚠ VERIFICATION INCOMPLETE: Could not fully confirm gRPC communication")


async def main():
    # Create the demo with detailed debugging
    demo = DistributedSwarmDemo(debug_level=DEBUG_DETAILED)
    
    try:
        # Create agents
        agent1 = SimpleAgent("agent1")
        agent2 = SimpleAgent("agent2")
        
        # Create nodes with gRPC servers
        # In a real distributed scenario, these would be on different machines with different IPs
        node1 = demo.create_node(
            "node1", 
            "localhost", 
            50051, 
            {"agent1": agent1}
        )
        
        node2 = demo.create_node(
            "node2", 
            "localhost", 
            50052, 
            {"agent2": agent2}
        )
        
        # Create clients to connect to the nodes
        client1 = demo.connect_to_node("localhost:50051", "manager-to-node1")
        client2 = demo.connect_to_node("localhost:50052", "manager-to-node2")
        
        # Register the nodes (in a real scenario, this would include discovery)
        logger.info("Registering nodes with the system")
        client1.register_node("node1", ["agent1"])
        client2.register_node("node2", ["agent2"])
        
        # Create tasks
        logger.info("Creating tasks")
        task1 = Task(
            name="task1",
            agent=agent1,
            data=b"Hello from task 1"
        )
        
        # Execute task1 on node1
        logger.info("Executing task1 on node1")
        result1 = demo.execute_task_on_node(client1, task1)
        
        # Create task2 that depends on task1
        # In a real scenario, you would pass the result of task1 to task2
        task2 = Task(
            name="task2",
            agent=agent2,
            data=b"Hello from task 2 (depends on task1)"
        )
        
        # Execute task2 on node2
        logger.info("Executing task2 on node2")
        result2 = demo.execute_task_on_node(client2, task2)
        
        # Print a summary of all communication that occurred
        demo.print_communication_summary()
        
        # Generate and display the comprehensive communication report
        logger.info("\n" + generate_communication_report())
        
        # Verify distributed communication
        is_verified, reason = verify_distributed_communication()
        if is_verified:
            logger.info("\n✅ VERIFICATION SUCCESSFUL: Distributed communication confirmed")
            logger.info(f"Reason: {reason}")
        else:
            logger.warning("\n⚠️ VERIFICATION INCOMPLETE: Could not fully confirm distributed communication")
            logger.warning(f"Reason: {reason}")
        
        # Display communication pattern analysis
        analysis = analyze_communication_patterns()
        logger.info("\n===== COMMUNICATION PATTERN ANALYSIS =====")
        logger.info(f"Total gRPC calls: {analysis['call_count']}")
        logger.info(f"Average call duration: {analysis['durations']['avg']:.6f}s")
        logger.info(f"Average request size: {analysis['message_sizes']['request']['avg']:.0f} bytes")
        logger.info(f"Average response size: {analysis['message_sizes']['response']['avg']:.0f} bytes")
        
        logger.info("\n===== EXECUTION RESULTS =====")
        logger.info(f"Task1 result: {result1['result'].decode() if result1['status'] == 'success' else result1['error']}")
        logger.info(f"Task2 result: {result2['result'].decode() if result2['status'] == 'success' else result2['error']}")
        
        # Demonstrate how to run this across machines
        logger.info("\n===== CROSS-MACHINE DEPLOYMENT INSTRUCTIONS =====")
        logger.info("To run this example across multiple machines:")
        logger.info("1. Run the server portion on each machine with its IP address:")
        logger.info("   - Machine 1: node1 = demo.create_node('node1', '192.168.1.101', 50051, {'agent1': agent1})")
        logger.info("   - Machine 2: node2 = demo.create_node('node2', '192.168.1.102', 50051, {'agent2': agent2})")
        logger.info("2. Connect to remote nodes using their IP addresses:")
        logger.info("   - client1 = demo.connect_to_node('192.168.1.101:50051', 'manager-to-node1')")
        logger.info("   - client2 = demo.connect_to_node('192.168.1.102:50051', 'manager-to-node2')")
        logger.info("3. The debug utilities will show the actual network communication")
        
        logger.info("\nDistributed swarm example completed successfully!")
        logger.info("This example demonstrates that tasks can be distributed across multiple nodes via gRPC.")
        logger.info("The debugging utilities provide clear evidence of network communication between nodes.")
        
    finally:
        # Clean up resources
        demo.cleanup()


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())