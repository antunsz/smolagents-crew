#!/usr/bin/env python
"""
Distributed Research Writer Crew Example

This example demonstrates how to use SwarmCrew to distribute research and writing tasks
across multiple nodes. It shows how to:

1. Set up a SwarmManager and multiple SwarmNodes
2. Register different agents on different nodes
3. Create interdependent research and writing tasks
4. Coordinate task execution across the distributed system
5. Visualize the distributed execution flow

The example simulates a distributed research and writing workflow where:
- Research tasks are executed on one node
- Writing tasks are executed on another node
- Editing tasks are executed on a third node
- The final compilation happens on the manager node

This demonstrates how complex workflows with dependencies can be distributed
across multiple machines while maintaining proper execution order.
"""

import os
import time
import threading
import logging
from typing import Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Import SwarmCrew components
from smolagents_crew.swarm.crew import SwarmCrew
from smolagents_crew.swarm.node import SwarmNode
from smolagents_crew.swarm.server import SwarmNodeServicer, serve_node
from smolagents_crew.swarm.client import SwarmNodeClient
from smolagents_crew.swarm.debug import set_debug_level, DEBUG_DETAILED
from smolagents_crew.core import Task, Agent, TaskDependency

# Import agent tools
from smolagents import CodeAgent, OpenAIServerModel, DuckDuckGoSearchTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("distributed_research_writer")


class DistributedResearchWriterDemo:
    """Demonstrates a distributed research and writing workflow using SwarmCrew."""
    
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
        
        # Store topics for research
        self.topics = [
            "Artificial Intelligence in Healthcare",
            "Climate Change Mitigation Strategies",
            "The Future of Remote Work"
        ]
        
        # Create agents
        self.create_agents()
        
        # Initialize SwarmCrew
        self.crew = None
    
    def create_agents(self):
        """Create the specialized agents for research, writing, and editing."""
        # Research agent with search capabilities
        self.research_agent = Agent(
            "researcher",
            agent_instance=CodeAgent,
            model=OpenAIServerModel('gpt-4o-mini'),
            tools=[DuckDuckGoSearchTool()]
        )
        
        # Writer agent for content creation
        self.writer_agent = Agent(
            "writer",
            agent_instance=CodeAgent,
            model=OpenAIServerModel('gpt-4o-mini'),
            tools=[]
        )
        
        # Editor agent for content refinement
        self.editor_agent = Agent(
            "editor",
            agent_instance=CodeAgent,
            model=OpenAIServerModel('gpt-4o-mini'),
            tools=[]
        )
        
        # Compiler agent for final assembly
        self.compiler_agent = Agent(
            "compiler",
            agent_instance=CodeAgent,
            model=OpenAIServerModel('gpt-4o-mini'),
            tools=[]
        )
        
        logger.info("Created specialized agents for research, writing, editing, and compilation")
    
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
    
    def setup_distributed_system(self):
        """Set up the distributed system with multiple nodes."""
        # Create research node
        research_node = self.create_node(
            "research_node", 
            "localhost", 
            50051, 
            {"researcher": self.research_agent}
        )
        
        # Create writing node
        writing_node = self.create_node(
            "writing_node", 
            "localhost", 
            50052, 
            {"writer": self.writer_agent}
        )
        
        # Create editing node
        editing_node = self.create_node(
            "editing_node", 
            "localhost", 
            50053, 
            {"editor": self.editor_agent}
        )
        
        # Create local node for compilation
        compilation_node = self.create_node(
            "compilation_node", 
            "localhost", 
            50054, 
            {"compiler": self.compiler_agent}
        )
        
        logger.info("Distributed system set up with research, writing, editing, and compilation nodes")
        
        # Create SwarmCrew with all agents
        self.crew = SwarmCrew(
            agents={
                "researcher": self.research_agent,
                "writer": self.writer_agent,
                "editor": self.editor_agent,
                "compiler": self.compiler_agent
            },
            tasks=[],  # We'll add tasks later
            initial_context={}
        )
        
        # Add remote nodes to the crew
        # Note: The local node is already registered by default
        self.crew.add_node("research_node", {"researcher": self.research_agent})
        self.crew.add_node("writing_node", {"writer": self.writer_agent})
        self.crew.add_node("editing_node", {"editor": self.editor_agent})
        self.crew.add_node("compilation_node", {"compiler": self.compiler_agent})
        
        logger.info("SwarmCrew initialized with all nodes registered")
    
    def create_research_writing_workflow(self, topics):
        """Create a research and writing workflow with multiple topics.
        
        Args:
            topics: List of topics to research and write about
        """
        logger.info(f"Creating research and writing workflow for {len(topics)} topics")
        
        all_tasks = []
        
        for i, topic in enumerate(topics):
            topic_id = f"topic_{i+1}"
            
            # Research task
            research_task = Task(
                name=f"research_{topic_id}",
                agent=self.research_agent,
                prompt_template=f"Research the following topic and provide key findings: {topic}\n\n"
                               f"Focus on recent developments, key statistics, and expert opinions.\n"
                               f"Organize your findings into clear sections with Markdown formatting:\n"
                               f"- Use ### for section headings\n"
                               f"- Use bullet points (- ) for lists\n"
                               f"- Use *italics* for emphasis\n"
                               f"- Use **bold** for important points\n"
                               f"- Include [links](url) to sources where relevant",
                result_key=f"research_findings_{topic_id}"
            )
            
            # Writing task that depends on research
            writing_task = Task(
                name=f"write_{topic_id}",
                agent=self.writer_agent,
                prompt_template="Write a comprehensive article using the following research findings:\n\n"
                               "{research_findings_" + topic_id + "}\n\n"
                               "Create a well-structured article with Markdown formatting:\n"
                               "- Use ## for the article title\n"
                               "- Use ### for section headings\n"
                               "- Use #### for subsection headings\n"
                               "- Use proper Markdown for lists, emphasis, and other formatting\n"
                               "- Include a brief introduction, well-organized body sections, and a conclusion\n"
                               "Use engaging language and provide concrete examples.",
                result_key=f"draft_article_{topic_id}",
                dependencies=[TaskDependency(f"research_{topic_id}", f"research_findings_{topic_id}")]
            )
            
            # Editing task that depends on writing
            editing_task = Task(
                name=f"edit_{topic_id}",
                agent=self.editor_agent,
                prompt_template="Edit and improve the following article draft:\n\n"
                               "{draft_article_" + topic_id + "}\n\n"
                               "Focus on clarity, coherence, grammar, and style.\n"
                               "Ensure the article flows logically and maintains reader engagement.\n"
                               "Preserve and enhance the Markdown formatting:\n"
                               "- Maintain all headings (##, ###, ####)\n"
                               "- Ensure proper formatting of lists, emphasis, and other Markdown elements\n"
                               "- Add additional Markdown formatting where it improves readability\n"
                               "- Fix any Markdown syntax errors in the original draft",
                result_key=f"edited_article_{topic_id}",
                dependencies=[TaskDependency(f"write_{topic_id}", f"draft_article_{topic_id}")]
            )
            
            all_tasks.extend([research_task, writing_task, editing_task])
        
        # Final compilation task that depends on all edited articles
        # Fix the task names and result keys to match the actual tasks created in the loop
        topic_ids = [f"topic_{i+1}" for i in range(len(topics))]
        compilation_dependencies = [
            TaskDependency(f"edit_{topic_id}", f"edited_article_{topic_id}")
            for topic_id in topic_ids
        ]
        
        compilation_template = "Compile the following edited articles into a cohesive report in Markdown format:\n\n"
        for topic_id in topic_ids:
            compilation_template += "{edited_article_" + topic_id + "}\n\n"
        
        compilation_template += "\nCreate a unified Markdown document with the following structure:\n"
        compilation_template += "1. Use # for the main title\n"
        compilation_template += "2. Use ## for section headings (one for each topic)\n"
        compilation_template += "3. Use ### for subsections within each topic\n"
        compilation_template += "4. Use proper Markdown formatting for:\n"
        compilation_template += "   - Lists (using - or 1. for numbered lists)\n"
        compilation_template += "   - *Emphasis* and **strong emphasis**\n"
        compilation_template += "   - > for blockquotes\n"
        compilation_template += "   - Code blocks with ```\n"
        compilation_template += "   - [Links](url) where appropriate\n\n"
        compilation_template += "Start with a # Title, followed by a brief introduction, then a ## Table of Contents section with links to each topic section.\n"
        compilation_template += "Ensure the document has a professional and consistent Markdown formatting throughout."
        
        # Log the compilation task details for debugging
        logger.info(f"Creating compilation task with {len(compilation_dependencies)} dependencies")
        for dep in compilation_dependencies:
            logger.info(f"  Dependency: {dep.source_task} -> {dep.result_key}")
        
        compilation_task = Task(
            name="compile_final_report",
            agent=self.compiler_agent,
            prompt_template=compilation_template,
            result_key="final_report",
            dependencies=compilation_dependencies
        )
        
        all_tasks.append(compilation_task)
        
        # Add all tasks to the crew
        for task in all_tasks:
            self.crew.manager.add_task(task)
        
        logger.info(f"Created {len(all_tasks)} tasks in the research-writing workflow")
        
        return all_tasks
    
    def execute_workflow(self):
        """Execute the distributed research and writing workflow."""
        logger.info("Starting execution of the distributed research and writing workflow")
        
        # Execute all tasks and collect results
        start_time = time.time()
        
        # Add debug logging to track context sharing between nodes
        logger.info("Setting debug level for better context tracking")
        set_debug_level(DEBUG_DETAILED)
        
        # Add initial context for all topics to ensure they're available
        initial_context = {}
        for i, topic in enumerate(self.topics):
            topic_id = f"topic_{i+1}"
            logger.info(f"Adding topic {topic_id} to initial context: {topic}")
            initial_context[f"topic_{topic_id}"] = topic
        
        # Update crew's context with initial values
        self.crew.context.update(initial_context)
        
        # Log all tasks before execution
        logger.info("Tasks to be executed:")
        for task in self.crew.manager.task_queue:
            logger.info(f"  Task: {task.name}, Agent: {task.agent.name}, Result Key: {task.result_key}")
            if task.dependencies:
                logger.info(f"    Dependencies: {[(dep.source_task, dep.result_key) for dep in task.dependencies]}")
        
        results = self.crew.execute(evaluate=True)
        
        # Log all results after execution
        logger.info("Task results:")
        for key, value in results.items():
            preview = value[:100] + "..." if isinstance(value, str) and len(value) > 100 else value
            logger.info(f"  {key}: {preview}")
            
        total_time = time.time() - start_time
        
        logger.info(f"Workflow execution completed in {total_time:.2f} seconds")
        
        # Print system status
        status = self.crew.manager.get_system_status()
        logger.info("\nDistributed System Status:")
        logger.info(f"Total Nodes: {len(status['nodes'])}")
        logger.info(f"Completed Tasks: {status['completed_tasks']}")
        
        # Print final report
        if "final_report" in results:
            logger.info("\nFinal Report Preview:")
            preview = results["final_report"][:500] + "..." if len(results["final_report"]) > 500 else results["final_report"]
            logger.info(preview)
        
        return results
    
    def shutdown(self):
        """Shutdown all nodes and servers."""
        logger.info("Shutting down distributed system")
        
        # Close all client connections
        for client_id, client in self.clients.items():
            logger.info(f"Closing client connection: {client_id}")
            client.close()
        
        # Stop all servers
        for node_id, server in self.servers.items():
            logger.info(f"Stopping server: {node_id}")
            server.stop(0)
        
        logger.info("Distributed system shutdown complete")


def main():
    """Run the distributed research writer crew example."""
    # Create the demo instance
    demo = DistributedResearchWriterDemo()
    
    try:
        # Set up the distributed system
        demo.setup_distributed_system()
        
        # Create the research-writing workflow using the predefined topics
        demo.create_research_writing_workflow(demo.topics)
        
        # Execute the workflow
        results = demo.execute_workflow()
        
        # Print final report
        print("\n" + "=" * 50)
        print("FINAL RESEARCH REPORT")
        print("=" * 50)
        print(results.get("final_report", "No final report generated"))
        
        # Save the final report as a Markdown file
        if "final_report" in results:
            output_file = "research_report.md"
            with open(output_file, "w") as f:
                f.write(results["final_report"])
            logger.info(f"Saved final research report as Markdown file: {output_file}")
            print(f"\nMarkdown report saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error in distributed research writer demo: {e}", exc_info=True)
    finally:
        # Ensure proper shutdown
        demo.shutdown()


if __name__ == "__main__":
    main()