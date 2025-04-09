"""SwarmManager gRPC client implementation for communicating with remote nodes.

This module provides the SwarmNodeClient class that handles communication with
remote SwarmNodes through gRPC, enabling distributed task execution.
"""

import time

import grpc
from typing import Dict, Any, Optional
from .proto import swarm_pb2, swarm_pb2_grpc
from ..core import Task
from .debug import log_node_connection, create_debug_channel, get_debug_level, DEBUG_NONE

class SwarmNodeClient:
    """gRPC client for communicating with remote SwarmNodes.
    
    Handles communication with remote nodes for task execution and status updates.
    """
    
    def __init__(self, address: str, node_id: str = None, debug: bool = False):
        """Initialize connection to a remote SwarmNode.
        
        Args:
            address: The address of the remote node (e.g. 'localhost:50051')
            node_id: Optional identifier for the node (for debugging)
            debug: Whether to enable debugging for this connection
        """
        self.address = address
        self.node_id = node_id or f"client-{id(self)}"
        self.debug = debug
        
        # Create channel with debug interceptors if debugging is enabled
        if debug and get_debug_level() > DEBUG_NONE:
            self.channel = create_debug_channel(address)
        else:
            self.channel = grpc.insecure_channel(address)
            
        self.stub = swarm_pb2_grpc.SwarmNodeServiceStub(self.channel)
        
        # Log connection
        if debug:
            log_node_connection(self.node_id, address, True)
        
    def register_node(self, node_id: str, available_agents: list) -> Dict[str, Any]:
        """Register with the remote node.
        
        Args:
            node_id: Unique identifier for this node
            available_agents: List of available agent names
            
        Returns:
            Dictionary containing node status information
        """
        # Update node_id if provided
        if node_id:
            self.node_id = node_id
            
        # Create request
        request = swarm_pb2.NodeInfo(
            node_id=node_id,
            available_agents=available_agents,
            status='idle'
        )
        
        # Measure call time if debugging is enabled
        start_time = time.time()
        response = self.stub.RegisterNode(request)
        duration = time.time() - start_time
        
        # Log successful registration
        if self.debug:
            print(f"Node {node_id} registered with {self.address} in {duration:.3f}s")
            
        return {
            'node_id': response.node_id,
            'status': response.status,
            'current_task': response.current_task or None,
            'duration': duration if self.debug else None
        }
        
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task on the remote node.
        
        Args:
            task: The task to execute
            
        Returns:
            Dictionary containing task execution results
        """
        # Create request
        request = swarm_pb2.TaskMessage(
            name=task.name,
            agent_name=task.agent.name,
            data=task.data,
            dependencies=[dep.task_name for dep in task.dependencies]
        )
        
        # Log task execution if debugging is enabled
        if self.debug:
            print(f"Executing task {task.name} on node {self.node_id} at {self.address}")
            
        # Measure call time if debugging is enabled
        start_time = time.time()
        response = self.stub.ExecuteTask(request)
        duration = time.time() - start_time
        
        # Log execution result
        if self.debug:
            status = "succeeded" if response.status == "success" else "failed"
            print(f"Task {task.name} {status} on node {self.node_id} in {duration:.3f}s")
            
        return {
            'status': response.status,
            'result': response.result if response.status == 'success' else None,
            'error': response.error,
            'duration': duration if self.debug else None
        }
        
    def update_status(self, node_id: str, status: str, current_task: Optional[str] = None) -> Dict[str, Any]:
        """Update status on the remote node.
        
        Args:
            node_id: ID of the node
            status: New status string
            current_task: Name of current task if any
            
        Returns:
            Dictionary containing updated node status
        """
        request = swarm_pb2.NodeStatus(
            node_id=node_id,
            status=status,
            current_task=current_task or ''
        )
        response = self.stub.UpdateStatus(request)
        return {
            'node_id': response.node_id,
            'status': response.status,
            'current_task': response.current_task or None
        }
        
    def heartbeat(self, node_id: str, available_agents: list) -> Dict[str, Any]:
        """Send heartbeat to maintain connection with remote node.
        
        Args:
            node_id: ID of the node
            available_agents: List of available agent names
            
        Returns:
            Dictionary containing current node status
        """
        # Create request
        request = swarm_pb2.NodeInfo(
            node_id=node_id,
            available_agents=available_agents,
            status='idle'
        )
        
        # Log heartbeat if debugging is enabled
        if self.debug:
            print(f"Sending heartbeat for node {node_id} to {self.address}")
            
        # Measure call time if debugging is enabled
        start_time = time.time()
        response = self.stub.Heartbeat(request)
        duration = time.time() - start_time
        
        # Log heartbeat result
        if self.debug:
            print(f"Heartbeat for node {node_id} completed in {duration:.3f}s")
            
        return {
            'node_id': response.node_id,
            'status': response.status,
            'current_task': response.current_task or None,
            'duration': duration if self.debug else None
        }
        
    def close(self) -> None:
        """Close the gRPC channel."""
        # Log disconnection if debugging is enabled
        if self.debug:
            print(f"Closing connection to {self.address} for node {self.node_id}")
            log_node_connection(self.node_id, self.address, False)
            
        self.channel.close()