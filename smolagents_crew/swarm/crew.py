"""SwarmCrew module for distributed task execution.

This module provides the SwarmCrew class that extends the base Crew functionality
to support distributed task execution across multiple nodes.
"""

from typing import Dict, List, Any
from ..core import Crew, Task, Agent
from .manager import SwarmManager
from .node import SwarmNode
from logging import getLogger
logger = getLogger(__name__)

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_VISUALIZATION_DEPS = True
except ImportError:
    HAS_VISUALIZATION_DEPS = False
    logger.warning("NetworkX or Matplotlib not found. Graph visualization will not be available.")

class SwarmCrew(Crew):
    """A class for managing distributed task execution across multiple nodes.
    
    Extends the base Crew class to support distributed execution while maintaining
    the same interface and dependency management capabilities.
    """
    
    def __init__(self, agents: Dict[str, Agent], tasks: List[Task], initial_context: Dict[str, Any] = None):
        """Initialize a SwarmCrew.
        
        Args:
            agents: Dictionary of agents available for task execution
            tasks: List of tasks to execute
            initial_context: Initial context data for task execution
        """
        super().__init__(agents=agents, tasks=tasks, initial_context=initial_context)
        self.manager = SwarmManager()
        
        # Create a default local node with all agents
        local_node = SwarmNode("local", agents)
        self.manager.register_node(local_node)
        
    def add_node(self, node_id: str, available_agents: Dict[str, Agent]) -> None:
        """Add a new execution node to the swarm.
        
        Args:
            node_id: Unique identifier for the node
            available_agents: Dictionary of agents available on this node
        """
        node = SwarmNode(node_id, available_agents)
        self.manager.register_node(node)
        
    def remove_node(self, node_id: str) -> None:
        """Remove a node from the swarm.
        
        Args:
            node_id: ID of the node to remove
        """
        self.manager.unregister_node(node_id)
        
    def print_swarm_flow(self) -> str:
        """Generate visual representation of distributed workflow"""
        flow = ["\n🌐 SWARM FLOW VISUALIZATION"]
        
        for node_id, node in self.manager.nodes.items():
            flow.append(f"│\n└── {node_id} [Node]")
            
            # Show agents
            flow.append(f"   ├── Agents: {', '.join(node.available_agents.keys())}")
            
            # Check if node has tasks attribute or method
            node_tasks = getattr(node, 'current_task', None)
            if node_tasks:
                flow.append(f"   ├── Tasks:")
                if isinstance(node_tasks, dict):
                    for task_name in node_tasks:
                        flow.append(f"   │   ├── {task_name}")
                else:
                    # If it's a single task object
                    flow.append(f"   │   ├── {node_tasks.name if hasattr(node_tasks, 'name') else str(node_tasks)}")
            
            # Dependencies are handled at the manager level, so we'll skip this for now
            # Unless we implement a way to track dependencies per node

        return '\n'.join(flow)
        
    def execute(self, evaluate: bool = False) -> Dict[str, Any]:
        """Execute tasks across the distributed system.
        
        Args:
            evaluate: Whether to collect execution metrics
            
        Returns:
            Dictionary containing task results
        """
        # Share the initial context with the manager
        if self.context:
            self.manager.task_results.update(self.context)
            
        # Add all tasks to the manager's queue
        for task in self.tasks:
            self.manager.add_task(task)
            
        # Execute tasks and collect results
        results = self.manager.execute_tasks()
        
        if evaluate:
            status = self.manager.get_system_status()
            print("\nDistributed Execution Status:")
            print(f"Total Nodes: {len(status['nodes'])}")
            print(f"Completed Tasks: {status['completed_tasks']}")
            
        return results

    def visualize_swarm_flow(self, save_path=None, show=True, flow_style='process'):
        """Generate a visual graph representation of the swarm structure and task flow.
        
        Creates an intuitive visualization of the task workflow, focusing on dependencies
        and data flow between tasks. The visualization shows how tasks are connected
        through their dependencies and which agents/nodes are responsible for each task.
        
        Note:
            This requires the optional visualization dependencies. You can install them with:
            `pip install smolagents-crew[viz]` or `pip install networkx matplotlib`
        
        Args:
            save_path (str, optional): Path to save the generated image. Defaults to None.
            show (bool, optional): Whether to display the graph. Defaults to True.
            flow_style (str, optional): Style of flow visualization. Options:
                'process' - Focused on task dependencies and data flow (default)
                'system' - Includes all system components (nodes, agents, tasks)
        
        Returns:
            bool: True if visualization was successful, False otherwise.
        """
        if not HAS_VISUALIZATION_DEPS:
            logger.error("Cannot visualize swarm flow. Please install networkx and matplotlib: pip install networkx matplotlib")
            return False

        # Clear any existing plots and create a figure with adequate size
        plt.clf()
        plt.figure(figsize=(20, 16))
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Define colors
        local_color = '#42a1f5'  # Blue for local nodes
        remote_color = '#f59b42'  # Orange for remote nodes
        task_color = '#f5429e'    # Pink for tasks
        data_color = '#42f563'    # Green for data flow
        
        # Track node positions for better layout control
        node_positions = {}
        
        # Add nodes to graph with improved spacing
        node_count = 0
        agent_count = 0
        task_count = 0
        
        # First pass: Add all nodes to the graph
        for node_id, node in self.manager.nodes.items():
            color = local_color if node_id == "local" else remote_color
            G.add_node(node_id, color=color, label=node_id, type='node', layer=0)
            node_count += 1
            
            # Add agents for this node
            for agent_name in node.available_agents.keys():
                agent_id = f"{node_id}_{agent_name}"
                G.add_node(agent_id, color=color, label=agent_name, type='agent', layer=1)
                agent_count += 1
                
                # Connect node to agent
                G.add_edge(node_id, agent_id, label="has agent", style='solid', color='#333333')
        
        # Add tasks to graph
        for task in self.tasks:
            task_id = f"task_{task.name}"
            G.add_node(task_id, color=task_color, label=task.name, type='task', layer=2)
            task_count += 1
            
            # Connect task to its agent
            if task.agent:
                for node_id, node in self.manager.nodes.items():
                    if task.agent.name in node.available_agents:
                        agent_id = f"{node_id}_{task.agent.name}"
                        G.add_edge(agent_id, task_id, label="executes", style='solid', color='#333333')
            
            # Connect task to its dependencies
            if task.dependencies:
                for dep in task.dependencies:
                    dep_id = f"task_{dep.source_task}"
                    G.add_edge(dep_id, task_id, 
                              label=f"Data: {dep.result_key}",
                              style='dashed', 
                              color=data_color)
        
        # Create a custom layout with better spacing
        # Use multipartite layout as a starting point
        pos = nx.multipartite_layout(G, subset_key='layer', align='vertical')
        
        # Adjust positions to avoid overlap
        # Spread nodes horizontally based on their type
        node_spacing = 1.0 / (node_count + 1) if node_count > 0 else 0.5
        agent_spacing = 1.0 / (agent_count + 1) if agent_count > 0 else 0.5
        task_spacing = 1.0 / (task_count + 1) if task_count > 0 else 0.5
        
        # Vertical layer positioning with improved spacing
        layer_offsets = {'node': 0, 'agent': -3.0, 'task': 3.0}
        
        # Adjust node positions
        node_indices = {n: i for i, n in enumerate(
            [n for n in G.nodes() if G.nodes[n]['type'] == 'node'])}
        agent_indices = {n: i for i, n in enumerate(
            [n for n in G.nodes() if G.nodes[n]['type'] == 'agent'])}
        task_indices = {n: i for i, n in enumerate(
            [n for n in G.nodes() if G.nodes[n]['type'] == 'task'])}
        
        for node in G.nodes():
            node_type = G.nodes[node]['type']
            if node_type == 'node':
                pos[node] = (node_indices[node] * node_spacing * 2.0, layer_offsets[node_type])
            elif node_type == 'agent':
                pos[node] = (agent_indices[node] * agent_spacing * 2.0, layer_offsets[node_type])
            elif node_type == 'task':
                pos[node] = (task_indices[node] * task_spacing * 2.0, layer_offsets[node_type])
        
        # Define node shapes and sizes
        node_shapes = {
            'node': 's',  # square
            'agent': 'o',  # circle
            'task': 'D'   # diamond
        }
        
        node_sizes = {
            'node': 2500,
            'agent': 1800,
            'task': 2000
        }
        
        # Draw nodes with different shapes and colors
        for node_type in ['node', 'agent', 'task']:
            nodelist = [n for n in G.nodes() if G.nodes[n]['type'] == node_type]
            if nodelist:
                nx.draw_networkx_nodes(G, pos, 
                                      nodelist=nodelist,
                                      node_shape=node_shapes[node_type],
                                      node_color=[G.nodes[n]['color'] for n in nodelist],
                                      node_size=node_sizes[node_type],
                                      alpha=0.9)
        
        # Assign different curvature values to different edge types
        edge_styles = {}
        for i, e in enumerate(G.edges()):
            source_type = G.nodes[e[0]]['type']
            target_type = G.nodes[e[1]]['type']
            
            # Determine edge style based on source and target types
            if source_type == 'node' and target_type == 'agent':
                edge_styles[e] = {'style': 'solid', 'width': 1.5, 'rad': 0.2, 'color': '#333333'}
            elif source_type == 'agent' and target_type == 'node':
                edge_styles[e] = {'style': 'dotted', 'width': 1.0, 'rad': -0.2, 'color': '#888888'}
            elif source_type == 'agent' and target_type == 'task':
                edge_styles[e] = {'style': 'solid', 'width': 1.5, 'rad': 0.3, 'color': '#333333'}
            elif source_type == 'task' and target_type == 'task':
                # Vary the curvature for task-to-task edges to prevent overlap
                rad = 0.3 + (i % 3) * 0.1
                edge_styles[e] = {'style': 'dashed', 'width': 1.5, 'rad': rad, 'color': data_color}
            else:
                edge_styles[e] = {'style': 'solid', 'width': 1.0, 'rad': 0.0, 'color': '#888888'}
        
        # Draw edges with varying styles and curvatures
        for edge_type in ['solid', 'dotted', 'dashed']:
            edgelist = [e for e in G.edges() if edge_styles[e]['style'] == edge_type]
            if edgelist:
                nx.draw_networkx_edges(G, pos, 
                                      edgelist=edgelist,
                                      width=[edge_styles[e]['width'] for e in edgelist],
                                      edge_color=[edge_styles[e]['color'] for e in edgelist],
                                      style=edge_type,
                                      arrows=True,
                                      arrowstyle='-|>',
                                      arrowsize=15,
                                      connectionstyle=[f"arc3,rad={edge_styles[e]['rad']}" for e in edgelist],
                                      alpha=0.8)
        
        # Draw node labels with improved formatting and positioning
        nx.draw_networkx_labels(G, pos,
                              labels={n: f"{G.nodes[n]['label']}\n({G.nodes[n]['type'].capitalize()})" 
                                      for n in G.nodes()},
                              font_size=10,
                              font_weight='bold',
                              font_family='sans-serif',
                              bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.9))
        
        # Draw edge labels with improved positioning to avoid overlap
        edge_labels = nx.get_edge_attributes(G, 'label')
        if edge_labels:
            # Use a fixed label position value instead of a dictionary
            # This avoids the TypeError when NetworkX tries to do 1 - label_pos
            label_pos = 0.5  # Default middle position
            
            nx.draw_networkx_edge_labels(G, pos, 
                                        edge_labels=edge_labels,
                                        font_size=8,
                                        font_color='#505050',
                                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8),
                                        label_pos=label_pos,
                                        rotate=False)
        
        # Add legend with improved styling
        plt.legend(handles=[
            plt.Line2D([0], [0], marker='s', color='w', label='Node',
                      markerfacecolor=local_color, markersize=15),
            plt.Line2D([0], [0], marker='o', color='w', label='Agent',
                      markerfacecolor=remote_color, markersize=15),
            plt.Line2D([0], [0], marker='D', color='w', label='Task',
                      markerfacecolor=task_color, markersize=15),
            plt.Line2D([0], [0], linestyle='dashed', color=data_color, label='Data Flow')
        ], loc='upper left', framealpha=0.9, fontsize=10)

        # Add title and adjust layout
        plt.title('Swarm Crew Task Flow Visualization', fontsize=16, pad=20)
        plt.axis('off')  # Hide axes
        plt.tight_layout()
        plt.margins(0.2)
        
        # Save figure if path provided
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=300)
            logger.info(f"Swarm flow visualization saved to {save_path}")

        # Show or close figure
        if show:
            plt.show()
        else:
            plt.close()

        return True