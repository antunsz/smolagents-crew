"""Debug utilities for SwarmNode and SwarmManager gRPC communication.

This module provides debugging tools and utilities to verify and monitor
gRPC communication between SwarmNodes and SwarmManager. These utilities help
confirm that nodes are properly communicating across machines through gRPC
rather than through local function calls.
"""

import logging
import time
import json
import socket
import datetime
from typing import Dict, Any, Optional, List, Tuple
import grpc
import concurrent.futures

# Configure logging
logger = logging.getLogger("smolagents.swarm")

# Debug levels
DEBUG_NONE = 0      # No debugging
DEBUG_BASIC = 1     # Basic debugging (connection events, task execution)
DEBUG_DETAILED = 2  # Detailed debugging (message contents, timing)
DEBUG_VERBOSE = 3   # Verbose debugging (all information)

# Global debug level setting
_debug_level = DEBUG_NONE

# Communication tracking
_grpc_calls = []
_node_connections = {}
_message_sizes = {}
_network_latency = {}
_communication_graph = {}


def set_debug_level(level: int) -> None:
    """Set the debug level for SwarmNode and SwarmManager.
    
    Args:
        level: Debug level (0-3)
    """
    global _debug_level
    _debug_level = level
    
    # Configure logging based on debug level
    if level >= DEBUG_VERBOSE:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    elif level >= DEBUG_DETAILED:
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)
    elif level >= DEBUG_BASIC:
        logging.basicConfig(level=logging.WARNING)
        logger.setLevel(logging.WARNING)
    else:
        logging.basicConfig(level=logging.ERROR)
        logger.setLevel(logging.ERROR)
    
    logger.info(f"Debug level set to {level}")


def get_debug_level() -> int:
    """Get the current debug level.
    
    Returns:
        Current debug level
    """
    return _debug_level


def log_grpc_call(method: str, request: Any, response: Any, duration: float) -> None:
    """Log a gRPC call for debugging purposes.
    
    Args:
        method: Name of the gRPC method called
        request: Request message
        response: Response message
        duration: Call duration in seconds
    """
    if _debug_level >= DEBUG_BASIC:
        logger.info(f"gRPC call: {method} (took {duration:.3f}s)")
        
    if _debug_level >= DEBUG_DETAILED:
        logger.debug(f"Request: {request}")
        logger.debug(f"Response: {response}")
    
    # Calculate message sizes
    request_size = len(str(request))
    response_size = len(str(response))
    
    # Update message size tracking
    if method not in _message_sizes:
        _message_sizes[method] = {
            "request": {"count": 0, "total_size": 0, "min": float('inf'), "max": 0},
            "response": {"count": 0, "total_size": 0, "min": float('inf'), "max": 0}
        }
    
    _message_sizes[method]["request"]["count"] += 1
    _message_sizes[method]["request"]["total_size"] += request_size
    _message_sizes[method]["request"]["min"] = min(_message_sizes[method]["request"]["min"], request_size)
    _message_sizes[method]["request"]["max"] = max(_message_sizes[method]["request"]["max"], request_size)
    
    _message_sizes[method]["response"]["count"] += 1
    _message_sizes[method]["response"]["total_size"] += response_size
    _message_sizes[method]["response"]["min"] = min(_message_sizes[method]["response"]["min"], response_size)
    _message_sizes[method]["response"]["max"] = max(_message_sizes[method]["response"]["max"], response_size)
    
    # Extract node information from method and request if possible
    source_node = None
    target_node = None
    
    # Try to extract node IDs from the request
    if hasattr(request, "node_id"):
        source_node = request.node_id
    
    # Update communication graph
    if source_node and target_node:
        if source_node not in _communication_graph:
            _communication_graph[source_node] = {}
        if target_node not in _communication_graph[source_node]:
            _communication_graph[source_node][target_node] = []
        
        _communication_graph[source_node][target_node].append({
            "method": method,
            "timestamp": time.time(),
            "duration": duration
        })
        
    # Store call information for later analysis
    _grpc_calls.append({
        "method": method,
        "timestamp": time.time(),
        "duration": duration,
        "request": str(request),
        "response": str(response),
        "request_size": request_size,
        "response_size": response_size,
        "source_node": source_node,
        "target_node": target_node
    })


def log_node_connection(node_id: str, address: str, connected: bool) -> None:
    """Log a node connection event.
    
    Args:
        node_id: ID of the node
        address: Address of the node
        connected: Whether the node connected or disconnected
    """
    if _debug_level >= DEBUG_BASIC:
        status = "connected" if connected else "disconnected"
        logger.info(f"Node {node_id} {status} at {address}")
    
    # Extract host from address if possible
    host = address.split(':')[0] if ':' in address else address
    
    # Measure network latency if this is a connection event
    latency = None
    if connected and host not in ('localhost', '127.0.0.1', '[::]'):
        try:
            # Try to ping the host to measure latency
            latency = measure_network_latency(host)
            if latency is not None:
                _network_latency[host] = latency
                if _debug_level >= DEBUG_DETAILED:
                    logger.info(f"Network latency to {host}: {latency:.3f}ms")
        except Exception as e:
            if _debug_level >= DEBUG_DETAILED:
                logger.warning(f"Failed to measure network latency to {host}: {e}")
    
    # Update node connection status
    _node_connections[node_id] = {
        "address": address,
        "connected": connected,
        "last_updated": time.time(),
        "network_latency": latency
    }


def get_connection_status() -> Dict[str, Any]:
    """Get the current connection status of all nodes.
    
    Returns:
        Dictionary containing node connection information
    """
    return _node_connections


def get_message_size_stats() -> Dict[str, Any]:
    """Get statistics about message sizes for different methods.
    
    Returns:
        Dictionary containing message size statistics
    """
    stats = {}
    
    for method, data in _message_sizes.items():
        stats[method] = {
            "request": {
                "count": data["request"]["count"],
                "total_size": data["request"]["total_size"],
                "avg_size": data["request"]["total_size"] / data["request"]["count"] if data["request"]["count"] > 0 else 0,
                "min_size": data["request"]["min"] if data["request"]["min"] != float('inf') else 0,
                "max_size": data["request"]["max"]
            },
            "response": {
                "count": data["response"]["count"],
                "total_size": data["response"]["total_size"],
                "avg_size": data["response"]["total_size"] / data["response"]["count"] if data["response"]["count"] > 0 else 0,
                "min_size": data["response"]["min"] if data["response"]["min"] != float('inf') else 0,
                "max_size": data["response"]["max"]
            }
        }
    
    return stats


def get_network_latency() -> Dict[str, float]:
    """Get network latency measurements for connected hosts.
    
    Returns:
        Dictionary mapping host addresses to latency in milliseconds
    """
    return _network_latency


def measure_network_latency(host: str, samples: int = 3) -> Optional[float]:
    """Measure network latency to a host using socket connections.
    
    Args:
        host: Host address to measure latency to
        samples: Number of samples to take
        
    Returns:
        Average latency in milliseconds or None if measurement failed
    """
    if host in ('localhost', '127.0.0.1', '[::]'):
        return 0.0  # Local connections have negligible latency
    
    latencies = []
    for _ in range(samples):
        try:
            start_time = time.time()
            # Try to establish a connection to measure latency
            with socket.create_connection((host, 80), timeout=1.0) as sock:
                pass
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            latencies.append(latency)
        except (socket.timeout, socket.error):
            # Try a different approach if connection fails
            try:
                start_time = time.time()
                socket.gethostbyname(host)
                latency = (time.time() - start_time) * 1000
                latencies.append(latency)
            except socket.error:
                continue
    
    if latencies:
        return sum(latencies) / len(latencies)
    return None


def get_grpc_call_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get the history of gRPC calls.
    
    Args:
        limit: Maximum number of calls to return
        
    Returns:
        List of dictionaries containing call information
    """
    return _grpc_calls[-limit:]


def clear_history() -> None:
    """Clear the gRPC call history and related statistics."""
    global _grpc_calls, _message_sizes, _network_latency, _communication_graph
    _grpc_calls = []
    _message_sizes = {}
    _network_latency = {}
    _communication_graph = {}


class DebugInterceptor(grpc.UnaryUnaryClientInterceptor, grpc.ServerInterceptor):
    """gRPC interceptor for debugging purposes.
    
    Intercepts gRPC calls to log timing and message information.
    """
    
    def __init__(self, is_client: bool = True):
        """Initialize the interceptor.
        
        Args:
            is_client: Whether this is a client-side interceptor
        """
        self.is_client = is_client
        
    def intercept_unary_unary(self, continuation, client_call_details, request):
        """Intercept a unary-unary gRPC call (client-side).
        
        Args:
            continuation: Function to continue the call
            client_call_details: Call details
            request: Request message
            
        Returns:
            Response from the continuation
        """
        method = client_call_details.method
        if isinstance(method, bytes):
            method = method.decode('utf-8')
        start_time = time.time()
        
        # Log the request if detailed debugging is enabled
        if _debug_level >= DEBUG_DETAILED:
            side = "Client" if self.is_client else "Server"
            logger.debug(f"{side} {method} request: {request}")
        
        # Continue the call
        response = continuation(client_call_details, request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the call
        log_grpc_call(method, request, response, duration)
        
        return response
        
    def intercept_service(self, continuation, handler_call_details):
        """Intercept a service call (server-side).
        
        Args:
            continuation: Function to continue the call
            handler_call_details: Call details
            
        Returns:
            RpcMethodHandler
        """
        method = handler_call_details.method
        if isinstance(method, bytes):
            method = method.decode('utf-8')
        
        # Get the original handler
        handler = continuation(handler_call_details)
        
        if handler:
            # Create a wrapper for the handler that logs timing and message information
            return self._wrap_rpc_handler(handler, method)
        
        return handler
    
    def _wrap_rpc_handler(self, handler, method):
        """Wrap an RPC handler with timing and logging.
        
        Args:
            handler: Original RPC handler
            method: Method name
            
        Returns:
            Wrapped RPC handler
        """
        if not handler:
            return None
            
        # We only handle unary-unary methods for now
        if handler.request_streaming or handler.response_streaming:
            return handler
            
        # Store the original handler function
        original_handler = handler.unary_unary
        
        # Define a new handler function that adds timing and logging
        def new_handler(request, context):
            start_time = time.time()
            
            # Log the request if detailed debugging is enabled
            if _debug_level >= DEBUG_DETAILED:
                logger.debug(f"Server {method} request: {request}")
            
            # Call the original handler
            try:
                response = original_handler(request, context)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Log the call
                log_grpc_call(method, request, response, duration)
                
                return response
            except Exception as e:
                logger.error(f"Error in handler for {method}: {e}")
                raise
        
        # Create a new handler with the wrapped function
        return grpc.RpcMethodHandler(
            request_streaming=handler.request_streaming,
            response_streaming=handler.response_streaming,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
            unary_unary=new_handler,
            unary_stream=handler.unary_stream,
            stream_unary=handler.stream_unary,
            stream_stream=handler.stream_stream
        )


def create_debug_channel(address: str) -> grpc.Channel:
    """Create a gRPC channel with debugging interceptors.
    
    Args:
        address: Address to connect to
        
    Returns:
        gRPC channel with debugging interceptors
    """
    interceptors = [DebugInterceptor(is_client=True)]
    return grpc.intercept_channel(grpc.insecure_channel(address), *interceptors)


def create_debug_server(max_workers: int = 10) -> grpc.Server:
    """Create a gRPC server with debugging interceptors.
    
    Args:
        max_workers: Maximum number of worker threads
        
    Returns:
        gRPC server with debugging interceptors
    """
    server = grpc.server(
        concurrent.futures.ThreadPoolExecutor(max_workers=max_workers),
        interceptors=[DebugInterceptor(is_client=False)]
    )
    return server


def analyze_communication_patterns() -> Dict[str, Any]:
    """Analyze communication patterns between nodes.
    
    Returns:
        Dictionary containing communication pattern analysis
    """
    if not _grpc_calls:
        return {"error": "No gRPC calls recorded"}
    
    # Analyze call frequency over time
    time_windows = {}
    window_size = 1.0  # 1 second windows
    
    for call in _grpc_calls:
        window = int(call["timestamp"] / window_size)
        if window not in time_windows:
            time_windows[window] = {"count": 0, "methods": {}}
        
        time_windows[window]["count"] += 1
        
        method = call["method"]
        if method not in time_windows[window]["methods"]:
            time_windows[window]["methods"][method] = 0
        time_windows[window]["methods"][method] += 1
    
    # Analyze call durations
    durations = [call["duration"] for call in _grpc_calls]
    avg_duration = sum(durations) / len(durations) if durations else 0
    min_duration = min(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    
    # Analyze message sizes
    request_sizes = [call.get("request_size", 0) for call in _grpc_calls]
    response_sizes = [call.get("response_size", 0) for call in _grpc_calls]
    
    avg_request_size = sum(request_sizes) / len(request_sizes) if request_sizes else 0
    avg_response_size = sum(response_sizes) / len(response_sizes) if response_sizes else 0
    
    # Determine if communication patterns suggest real network communication
    is_network_communication = avg_duration > 0.001  # More than 1ms suggests network calls
    
    return {
        "call_count": len(_grpc_calls),
        "time_windows": time_windows,
        "durations": {
            "avg": avg_duration,
            "min": min_duration,
            "max": max_duration
        },
        "message_sizes": {
            "request": {
                "avg": avg_request_size,
                "total": sum(request_sizes)
            },
            "response": {
                "avg": avg_response_size,
                "total": sum(response_sizes)
            }
        },
        "is_network_communication": is_network_communication,
        "network_latency": get_network_latency()
    }


def verify_distributed_communication() -> Tuple[bool, str]:
    """Verify that communication is happening between distributed nodes.
    
    This function analyzes the recorded gRPC calls and network measurements
    to determine if the communication is happening through the network
    rather than through local function calls.
    
    Returns:
        Tuple of (is_verified, reason)
    """
    if not _grpc_calls:
        return False, "No gRPC calls recorded"
    
    # Check call durations
    durations = [call["duration"] for call in _grpc_calls]
    avg_duration = sum(durations) / len(durations)
    
    # Check network latency
    has_remote_nodes = any(host not in ('localhost', '127.0.0.1', '[::]') 
                          for host in _network_latency.keys())
    
    # Check message sizes
    request_sizes = [call.get("request_size", 0) for call in _grpc_calls]
    response_sizes = [call.get("response_size", 0) for call in _grpc_calls]
    avg_message_size = (sum(request_sizes) + sum(response_sizes)) / (len(request_sizes) + len(response_sizes)) \
                      if (request_sizes and response_sizes) else 0
    
    # Analyze methods called
    methods = set(call["method"] for call in _grpc_calls)
    has_node_registration = any("RegisterNode" in method for method in methods)
    has_task_execution = any("ExecuteTask" in method for method in methods)
    
    # Make verification decision
    is_verified = False
    reason = ""
    
    if avg_duration < 0.0001:  # Less than 0.1ms
        reason = "Call durations too short for network communication"
    elif not has_remote_nodes and avg_duration < 0.001:  # Less than 1ms for localhost
        reason = "Only local connections detected with fast call times"
    elif has_node_registration and has_task_execution and avg_duration > 0.001:
        is_verified = True
        reason = "Verified distributed communication with appropriate call patterns and timing"
    elif has_remote_nodes and avg_duration > 0.005:  # More than 5ms
        is_verified = True
        reason = "Verified distributed communication with remote nodes and network-appropriate timing"
    else:
        reason = "Could not conclusively verify distributed communication"
    
    return is_verified, reason


def format_timestamp(timestamp: float) -> str:
    """Format a timestamp for display.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted timestamp string
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%H:%M:%S.%f")[:-3]  # Format with milliseconds


def generate_communication_report() -> str:
    """Generate a comprehensive report of communication between nodes.
    
    Returns:
        Formatted report string
    """
    report = ["===== GRPC COMMUNICATION REPORT ====="]
    
    # Verify distributed communication
    is_verified, reason = verify_distributed_communication()
    verification_status = "✓ VERIFIED" if is_verified else "✗ NOT VERIFIED"
    report.append(f"\nDistributed Communication: {verification_status}")
    report.append(f"Reason: {reason}")
    
    # Connection status
    connections = get_connection_status()
    report.append(f"\nNode Connections: {len(connections)}")
    for node_id, info in connections.items():
        status = "Connected" if info["connected"] else "Disconnected"
        latency = f", Latency: {info.get('network_latency', 'N/A')}ms" if info.get("network_latency") else ""
        report.append(f"  {node_id} -> {info['address']}: {status}{latency}")
        report.append(f"  Last updated: {format_timestamp(info['last_updated'])}")
    
    # Call statistics
    calls = _grpc_calls
    report.append(f"\ngRPC Calls: {len(calls)}")
    
    # Group calls by method
    method_counts = {}
    method_durations = {}
    
    for call in calls:
        method = call["method"]
        if method not in method_counts:
            method_counts[method] = 0
            method_durations[method] = []
        method_counts[method] += 1
        method_durations[method].append(call["duration"])
    
    # Report method statistics
    report.append("\nCall statistics by method:")
    for method, count in method_counts.items():
        durations = method_durations[method]
        avg_time = sum(durations) / len(durations)
        report.append(f"  {method}: {count} calls, avg time: {avg_time:.3f}s, "  
                     f"total: {sum(durations):.3f}s")
    
    # Message size statistics
    size_stats = get_message_size_stats()
    if size_stats:
        report.append("\nMessage Size Statistics:")
        for method, data in size_stats.items():
            report.append(f"  {method}:")
            report.append(f"    Request: avg {data['request']['avg_size']:.0f} bytes, "  
                         f"total {data['request']['total_size']} bytes")
            report.append(f"    Response: avg {data['response']['avg_size']:.0f} bytes, "  
                         f"total {data['response']['total_size']} bytes")
    
    # Network latency
    latency = get_network_latency()
    if latency:
        report.append("\nNetwork Latency:")
        for host, ms in latency.items():
            report.append(f"  {host}: {ms:.3f}ms")
    
    # Communication pattern analysis
    analysis = analyze_communication_patterns()
    report.append(f"\nCommunication Pattern Analysis:")
    report.append(f"  Average call duration: {analysis['durations']['avg']:.6f}s")
    report.append(f"  Average request size: {analysis['message_sizes']['request']['avg']:.0f} bytes")
    report.append(f"  Average response size: {analysis['message_sizes']['response']['avg']:.0f} bytes")
    
    # Final verification
    if is_verified:
        report.append("\n✓ VERIFICATION SUCCESSFUL: Confirmed gRPC communication between nodes")
        report.append("  This confirms that nodes are communicating through the network")
        report.append("  rather than through local function calls.")
    else:
        report.append("\n⚠ VERIFICATION INCOMPLETE: Could not fully confirm gRPC communication")
    
    return "\n".join(report)