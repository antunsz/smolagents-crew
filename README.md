# 🤖 SmolagentsCrew

> ⚠️ **Disclaimer**: This is an independent project that uses [smolagents](https://github.com/huggingface/smolagents) from Hugging Face but is not an official part of the Hugging Face ecosystem.

Orchestrate your AI dream team! 🚀 A framework built on top of [smolagents](https://github.com/huggingface/smolagents) from Hugging Face that brings multiple AI agents together to collaborate efficiently through smart threading and dependency management.

SmolagentsCrew serves as an orchestration layer that allows you to coordinate multiple smolagents, enabling them to work together on complex tasks while handling dependencies, parallel execution, and context sharing automatically.

## ✨ Features

- 🔄 **Concurrent Task Execution**: Watch your agents work in parallel with efficient threading
- 🔗 **Smart Dependency Management**: Let your tasks flow naturally with automatic dependency handling
- 🌐 **Context Sharing**: Seamless data sharing between tasks through an intelligent context system
- 🏗️ **Flexible Agent Configuration**: Build your perfect crew using our intuitive builder pattern
- 📝 **Template-based Prompts**: Create dynamic, context-aware prompts with variable substitution

## 📦 Installation

You can install SmolagentsCrew directly from PyPI using your preferred package manager. We recommend using `uv` for its superior performance and dependency resolution:

```bash
# Using uv (Recommended) 🚀
uv pip install smolagents-crew

# Using pip
pip install smolagents-crew

# With visualization support
pip install smolagents-crew[viz]
```

> 💡 Why uv? It's significantly faster than pip and provides better dependency resolution. Learn more at [the uv repo](https://github.com/astral-sh/uv)

## 🚀 Quick Start

```python
import os
from smolagents_crew import Agent, Task, Crew, TaskDependency
from smolagents import CodeAgent, DuckDuckGoSearchTool, OpenAIServerModel 

#you need to set your OPENAI_API_KEY var in you env
os.environ['OPENAI_API_KEY']=<sk-your_key>
# Create your AI dream team! 🤖
agent1 = Agent("research", agent_instance=CodeAgent, model=OpenAIServerModel('gpt-4o-mini'), tools=[DuckDuckGoSearchTool()])
agent2 = Agent("writer", agent_instance=CodeAgent, model=OpenAIServerModel('gpt-4o-mini'), tools=[DuckDuckGoSearchTool()])

# Define their missions with smart dependencies 📋
task1 = Task(
    name="research_topic",
    agent=agent1,
    prompt_template="Research about {topic}",
    result_key="research_result"
)

task2 = Task(
    name="write_article",
    agent=agent2,
    prompt_template="Write an article using this research: {research_result}",
    dependencies=[TaskDependency("research_topic", "research_result")]
)

# Assemble and launch your crew! 🚀
crew = Crew(
    agents={"research": agent1, "writer": agent2},
    tasks=[task1, task2],
    initial_context={"topic": "AI agents"}
)

results = crew.execute()
```

### Complex Task Management Example

Here's an example demonstrating more complex task dependencies and parallel execution patterns:

```python
from smolagents_crew import Agent, Task, Crew, TaskDependency
from smolagents import CodeAgent, OpenAIServerModel

# Create specialized agents
agent_a = Agent("data_collector", agent_instance=CodeAgent, model=OpenAIServerModel('gpt-4o-mini'))
agent_b = Agent("analyzer", agent_instance=CodeAgent, model=OpenAIServerModel('gpt-4o-mini'))
agent_c = Agent("researcher", agent_instance=CodeAgent, model=OpenAIServerModel('gpt-4o-mini'))
agent_d = Agent("summarizer", agent_instance=CodeAgent, model=OpenAIServerModel('gpt-4o-mini'))

# Task A: Collect initial data
task_a = Task(
    name="collect_data",
    agent=agent_a,
    prompt_template="Collect data about {topic}",
    result_key="raw_data"
)

# Task B: Analyze data (depends on A)
task_b = Task(
    name="analyze_data",
    agent=agent_b,
    prompt_template="Analyze this data: {raw_data}",
    result_key="analysis_results",
    dependencies=[TaskDependency("collect_data", "raw_data")]
)

# Task C: Independent research
task_c = Task(
    name="research",
    agent=agent_c,
    prompt_template="Research latest trends about {topic}",
    result_key="research_results"
)

# Task D: Final summary (depends on both B and C)
task_d = Task(
    name="summarize",
    agent=agent_d,
    prompt_template="Create summary using analysis: {analysis_results} and research: {research_results}",
    result_key="final_summary",
    dependencies=[
        TaskDependency("analyze_data", "analysis_results"),
        TaskDependency("research", "research_results")
    ]
)

# Create and execute the crew
crew = Crew(
    agents={
        "data_collector": agent_a,
        "analyzer": agent_b,
        "researcher": agent_c,
        "summarizer": agent_d
    },
    tasks=[task_a, task_b, task_c, task_d],
    initial_context={"topic": "AI agents"}
)

# Execute with evaluation enabled
results = crew.execute(evaluate=True)
```

In this example:
- Task A collects initial data
- Task B depends on A's output
- Task C runs independently
- Task D depends on both B and C

The framework automatically:
- Executes A and C in parallel
- Waits for A to complete before starting B
- Waits for both B and C to complete before starting D
- Manages all data dependencies and context sharing

## 🔧 Advanced Usage

### Task Execution Evaluation

SmolagentsCrew includes a evaluation system that helps you track and analyze task execution performance. You can enable evaluation to:

- Monitor task execution times
- Track parallel execution patterns
- Analyze task dependencies
- Generate detailed execution reports

Here's how to use the evaluation feature:

```python
# Enable evaluation when executing the crew
results = crew.execute(evaluate=True)

# The execution report will be automatically printed, showing:
# - Total execution time
# - Individual task execution times
# - Agent assignments
# - Task dependencies
# - Parallel execution groups
```

Example output:
```
Crew Execution Report
--------------------
Total Execution Time: 15.42 seconds

Task Execution Details:
Task: research_topic
Agent: researcher
Execution Time: 8.31 seconds

Task: write_article
Agent: writer
Execution Time: 7.11 seconds
Dependencies: research_topic

Parallel Execution Groups:
research_topic ran in parallel with: write_article
```

### Using the Builder Pattern

SmolagentsCrew provides a builder pattern that simplifies the process of creating and configuring complex agent workflows. The builder pattern allows you to:

- Construct crews step by step with clear, readable code
- Validate agent configurations and dependencies automatically
- Create reusable agent templates and workflows
- Handle complex task chains and dependencies with ease

Here's how to use our builder pattern:

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."

from smolagents_crew import CrewBuilder, Task, Agent
from smolagents import CodeAgent, OpenAIServerModel, DuckDuckGoSearchTool

# Create a builder instance
builder = CrewBuilder()

# Create and add research agent
research_agent = Agent(
    "researcher",
    agent_instance=CodeAgent,
    model=OpenAIServerModel('gpt-4o-mini'),
    tools=[DuckDuckGoSearchTool()]
)
builder.add_agent("researcher", research_agent)

# Create and add writer agent
writer_agent = Agent(
    "writer",
    agent_instance=CodeAgent,
    model=OpenAIServerModel('gpt-4o-mini'),
    tools=[]
)
builder.add_agent("writer", writer_agent)

# Create research task
research_task = Task(
    name="research_topic",
    agent=research_agent,
    prompt_template="Research about {topic} and provide key findings",
    result_key="research_findings"
)

# Create writing task that depends on research results
writing_task = Task(
    name="write_article",
    agent=writer_agent,
    prompt_template="Write an article using the following research: {research_findings}",
    result_key="final_article",
    dependencies=[TaskDependency("research_topic", "research_findings")]
)

# Add tasks to the builder
builder.add_task(research_task)
builder.add_task(writing_task)

# Add shared context
builder.add_shared_context("topic", "Artificial Intelligence in Healthcare")

# Print the crew structure for visualization
builder.print_crew()

# Build and execute the crew
crew = builder.build()
results = crew.execute()

# Access the final article
print("\nFinal Article:")
print(results["final_article"])
```

### Advanced Crew Building

SmolagentsCrew provides a builder pattern for creating complex agent crews. The `CrewBuilder` class offers advanced features for orchestrating sophisticated multi-agent workflows:

```python
from smolagents_crew import CrewBuilder

# Create a crew using the builder pattern
builder = CrewBuilder()

# Add agents
builder.add_agent("researcher", researcher_agent)
       .add_agent("writer", writer_agent)
       .add_agent("editor", editor_agent)

# Create a chain of dependent tasks
builder.add_task_chain([
    research_task,    # First task
    writing_task,     # Automatically depends on research_task
    editing_task     # Automatically depends on writing_task
])

# Add shared context
builder.add_shared_context("topic", "AI Agents")

# Validate the crew configuration
builder.validate_crew()

# Print the crew structure
builder.print_crew()

# Build and execute
crew = builder.build()
results = crew.execute(evaluate=True)
```

Key features of advanced crew building:

- 🔗 **Task Chaining**: Automatically create linear task dependencies
- ✅ **Crew Validation**: Detect issues like circular dependencies or missing components
- 🎯 **Shared Context**: Easily manage data shared between tasks
- 📊 **Visual Structure**: Print a clear overview of your crew's configuration
- 🔄 **Fluent Interface**: Chain method calls for cleaner code

### Distributed Task Execution with Swarm

SmolagentsCrew supports distributed task execution through its swarm functionality, allowing you to scale your AI operations across multiple nodes! 🌐

```python
from smolagents_crew.core import Agent, Task
from smolagents_crew.swarm import SwarmCrew, SwarmNode, serve

# Create your agents
agent1 = SimpleAgent("agent1")
agent2 = SimpleAgent("agent2")

# Set up the SwarmManager
swarm_crew = SwarmCrew()

# Create and register nodes with different agents
node1 = SwarmNode("node1", {"agent1": agent1})
node2 = SwarmNode("node2", {"agent2": agent2})

# Start node servers
serve(node1, 50051)
serve(node2, 50052)

# Register nodes with manager
manager.register_node("node1", "localhost:50051")
manager.register_node("node2", "localhost:50052")

# Create tasks with dependencies
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

# Submit and execute tasks
manager.submit_task(task1)
manager.submit_task(task2)

# O SwarmCrew garante a execução ordenada das tarefas
# by tracking dependencies and coordinating across nodes.
# In this case, task2 will only start after task1 is complete,
# even if they're running on different nodes.
```

#### Key Features of Swarm Mode 🔑

- 🌍 **Distributed Execution**: Run tasks across multiple machines or nodes
- 🔄 **Automatic Load Balancing**: Tasks are distributed based on node availability
- 🔗 **Dependency Management**: Maintains task dependencies across distributed nodes
- 📊 **Status Monitoring**: Track task execution status across the swarm
- 🛡️ **Fault Tolerance**: Handles node failures and task retries
- 🎨 **Flow Visualization**: Generate interactive workflow diagrams and text-based representations

#### Visualization Features 🌐

```python
# Text-based workflow visualization
print(swarm_crew.print_swarm_flow())

# Graphical visualization (requires optional dependencies)
swarm_crew.visualize_swarm_flow(
    save_path='fluxo_swarm.png',
    mostrar=True,
    estilo_fluxo='processo'  # Opções: 'processo' ou 'sistema'
)
```

##### Installation with Visualization Support
```bash
pip install smolagents-crew[viz]  # Instala networkx e matplotlib automaticamente
```
- 🎨 **Flow Visualization**: Generate interactive workflow diagrams and text-based representations

#### Visualization Features 🌐

```python
# Text-based workflow visualization
print(swarm_crew.print_swarm_flow())

# Graphical visualization (requires optional dependencies)
swarm_crew.visualize_swarm_flow(
    save_path='fluxo_swarm.png',
    mostrar=True,
    estilo_fluxo='processo'  # Opções: 'processo' ou 'sistema'
)
```

##### Installation with Visualization Support
```bash
pip install smolagents-crew[viz]  # Instala networkx e matplotlib automaticamente
```

#### Using SwarmCrew

For easier management of distributed tasks, you can use the `SwarmCrew` class that extends the base `Crew` functionality:

```python
from smolagents_crew.swarm import SwarmCrew

# Initialize SwarmCrew with your agents and tasks
crew = SwarmCrew(
    agents={"agent1": agent1, "agent2": agent2},
    tasks=[task1, task2]
)

# Add remote nodes
crew.add_node("remote1", {"agent1": agent1})
crew.add_node("remote2", {"agent2": agent2})

# Execute tasks across the swarm
results = crew.execute(evaluate=True)
```

> 💡 The swarm functionality is perfect for scenarios requiring high throughput or when you need to distribute computation across multiple machines.

## 🤝 Contributing

Join our crew! We love contributions that make our framework even better. Feel free to submit a Pull Request! 💪

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 📜