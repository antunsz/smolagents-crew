# 🤖 SmolagentsCrew

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
    model=OpenAIServerModel('gpt-4'),
    tools=[DuckDuckGoSearchTool()]
)
builder.add_agent("researcher", research_agent)

# Create and add writer agent
writer_agent = Agent(
    "writer",
    agent_instance=CodeAgent,
    model=OpenAIServerModel('gpt-4'),
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

## 🤝 Contributing

Join our crew! We love contributions that make our framework even better. Feel free to submit a Pull Request! 💪

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 📜