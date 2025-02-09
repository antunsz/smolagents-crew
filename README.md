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

Currently, you can install SmolagentsCrew locally from the repository:

```bash
git clone https://github.com/antunsz/smolagents-crew.git
cd smolagents-crew
pip install -e .
```

> 🔥 Coming Soon: SmolagentsCrew will be available on PyPI! Stay tuned for a simpler installation via `pip install smolagents-crew`

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

### Using the Builder Pattern

SmolagentsCrew provides a builder pattern that simplifies the process of creating and configuring complex agent workflows. The builder pattern allows you to:

- Construct crews step by step with clear, readable code
- Validate agent configurations and dependencies automatically
- Create reusable agent templates and workflows
- Handle complex task chains and dependencies with ease

Here's how to use our builder pattern:

```python
from smolagents_crew import CrewBuilder, AdvancedCrewBuilder
from smolagents import CodeAgent, OpenAIServerModel, DuckDuckGoSearchTool

# Build your crew step by step 🏗️
builder = CrewBuilder()

# Add agents with specific capabilities
research_agent = Agent(
    "researcher",
    agent_instance=CodeAgent,  # Using smolagents' CodeAgent as base
    model=OpenAIServerModel('gpt-4'),
    tools=[DuckDuckGoSearchTool()]
)
builder.add_agent("researcher", research_agent)

# Add tasks with clear dependencies
task = Task(
    name="research_task",
    agent=research_agent,
    prompt_template="Research about {topic}",
    result_key="research_result"
)
builder.add_task(task)

# Add shared context for all tasks
builder.add_shared_context("topic", "AI agents")
crew = builder.build()

# For complex workflows, use AdvancedCrewBuilder
advanced_builder = AdvancedCrewBuilder()

# Create sequential task chains automatically
advanced_builder.add_task_chain([
    research_task,
    analysis_task,
    writing_task
])  # Dependencies are handled automatically
crew = advanced_builder.build()
```

## 🤝 Contributing

Join our crew! We love contributions that make our framework even better. Feel free to submit a Pull Request! 💪

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 📜