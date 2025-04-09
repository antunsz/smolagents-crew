"""SwarmNode gRPC server implementation for handling remote task execution.

This module provides the SwarmNodeServicer class that implements the gRPC service
defined in the proto file, enabling remote task execution and node management.
"""

import time
import grpc
from concurrent import futures
from typing import Dict, Any
from .proto import swarm_pb2, swarm_pb2_grpc
from .node import SwarmNode
from ..core import Agent
from .debug import log_node_connection, create_debug_server, get_debug_level, DEBUG_NONE

class SwarmNodeServicer(swarm_pb2_grpc.SwarmNodeServiceServicer):
    """gRPC service implementation for SwarmNode.
    
    Handles incoming RPC calls for task execution, status updates, and node management.
    """
    
    def __init__(self, node: SwarmNode, debug: bool = False):
        """Initialize the servicer with a SwarmNode instance.
        
        Args:
            node: The SwarmNode instance to handle task execution
            debug: Whether to enable debugging for this servicer
        """
        self.node = node
        self.debug = debug
        
    def RegisterNode(self, request, context):
        """Handle node registration requests.
        
        Args:
            request: NodeInfo message containing node details
            context: RPC context
            
        Returns:
            NodeStatus message with current node status
        """
        # Log registration request if debugging is enabled
        if self.debug:
            print(f"Received registration request from node {request.node_id}")
            start_time = time.time()
            
        status = self.node.get_status()
        response = swarm_pb2.NodeStatus(
            node_id=status['node_id'],
            status=status['status'],
            current_task=status['current_task'] or ''
        )
        
        # Log registration completion if debugging is enabled
        if self.debug:
            duration = time.time() - start_time
            print(f"Completed registration for node {request.node_id} in {duration:.3f}s")
            log_node_connection(request.node_id, context.peer(), True)
            
        return response
        
    def ExecuteTask(self, request, context):
        """Handle task execution requests.
        
        Args:
            request: TaskMessage containing task details
            context: RPC context
            
        Returns:
            TaskResult message with execution results
        """
        # Log task execution request if debugging is enabled
        if self.debug:
            print(f"Received task execution request for task {request.name} from {context.peer()}")
            start_time = time.time()
            
        # Create Task object from message
        from ..core import Task
        task = Task(
            name=request.name,
            agent=self.node.available_agents[request.agent_name],
            data=request.data
        )
        
        # Execute task
        result = self.node.execute_task(task)
        
        # Convert result to protobuf message
        response = swarm_pb2.TaskResult(
            status=result['status'],
            result=result['result'] if result['status'] == 'success' else b'',
            error=result.get('error', '')
        )
        
        # Log task execution completion if debugging is enabled
        if self.debug:
            duration = time.time() - start_time
            status = "succeeded" if result['status'] == "success" else "failed"
            print(f"Task {request.name} {status} in {duration:.3f}s")
            
        return response
        
    def UpdateStatus(self, request, context):
        """Handle status update requests.
        
        Args:
            request: NodeStatus message with new status
            context: RPC context
            
        Returns:
            NodeStatus message with current status
        """
        # Log status update request if debugging is enabled
        if self.debug:
            print(f"Received status update request from node {request.node_id}")
            start_time = time.time()
            
        status = self.node.get_status()
        response = swarm_pb2.NodeStatus(
            node_id=status['node_id'],
            status=status['status'],
            current_task=status['current_task'] or ''
        )
        
        # Log status update completion if debugging is enabled
        if self.debug:
            duration = time.time() - start_time
            print(f"Completed status update for node {request.node_id} in {duration:.3f}s")
            
        return response
        
    def Heartbeat(self, request, context):
        """Handle heartbeat requests to maintain connection.
        
        Args:
            request: NodeInfo message
            context: RPC context
            
        Returns:
            NodeStatus message with current status
        """
        # Log heartbeat request if debugging is enabled
        if self.debug:
            print(f"Received heartbeat from node {request.node_id}")
            start_time = time.time()
            
        status = self.node.get_status()
        response = swarm_pb2.NodeStatus(
            node_id=status['node_id'],
            status=status['status'],
            current_task=status['current_task'] or ''
        )
        
        # Log heartbeat completion if debugging is enabled
        if self.debug:
            duration = time.time() - start_time
            print(f"Completed heartbeat for node {request.node_id} in {duration:.3f}s")
            
        return response

def serve(node: SwarmNode, port: int = 50051, debug: bool = False) -> None:
    """Start the gRPC server for a SwarmNode.
    
    Args:
        node: The SwarmNode instance to serve
        port: Port number to listen on
        debug: Whether to enable debugging for this server
    """
    # Create server with debug interceptors if debugging is enabled
    if debug and get_debug_level() > DEBUG_NONE:
        server = create_debug_server(max_workers=10)
        print(f"Starting debug gRPC server for node {node.node_id} on port {port}")
    else:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
    # Add servicer to server
    swarm_pb2_grpc.add_SwarmNodeServiceServicer_to_server(
        SwarmNodeServicer(node, debug=debug), server
    )
    
    # Add port and start server
    server_address = f'[::]:{port}'
    server.add_insecure_port(server_address)
    server.start()
    
    if debug:
        print(f"gRPC server for node {node.node_id} started on port {port}")
        log_node_connection(node.node_id, server_address, True)
        
    server.wait_for_termination()


def serve_node(servicer: SwarmNodeServicer, address: str, start: bool = True) -> grpc.Server:
    """Start the gRPC server for a SwarmNode using a servicer and address.
    
    Args:
        servicer: The SwarmNodeServicer instance to serve
        address: The address to listen on (e.g. 'localhost:50051')
        start: Whether to start the server immediately
        
    Returns:
        The gRPC server instance
    """
    # Parse address to get host and port
    if ':' in address:
        host, port_str = address.rsplit(':', 1)
        port = int(port_str)
    else:
        port = int(address)
        host = 'localhost'
    
    # Create server with debug interceptors if debugging is enabled
    if servicer.debug and get_debug_level() > DEBUG_NONE:
        server = create_debug_server(max_workers=10)
        print(f"Starting debug gRPC server for node {servicer.node.node_id} on {address}")
    else:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
    # Add servicer to server
    swarm_pb2_grpc.add_SwarmNodeServiceServicer_to_server(servicer, server)
    
    # Add port and start server
    server_address = f'[::]:{port}'
    server.add_insecure_port(server_address)
    
    if start:
        server.start()
        if servicer.debug:
            print(f"gRPC server for node {servicer.node.node_id} started on {address}")
            # Use server_address instead of address for log_node_connection
            log_node_connection(servicer.node.node_id, server_address, True)
        server.wait_for_termination()
    
    return server