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