from typing import Dict, List
from .core import Crew, Agent, Task, TaskDependency

class CrewBuilder:
    """Builder for creating complex crews.

    This class provides a fluent interface for constructing Crew instances
    with multiple agents, tasks, and shared context. It includes advanced features
    such as task chain creation and crew validation.

    Attributes:
        agents (Dict[str, Agent]): Dictionary of registered agents.
        tasks (List[Task]): List of tasks to be executed.
        shared_context (Dict): Shared context data for all tasks.
    """
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: List[Task] = []
        self.shared_context: Dict = {}

    def add_agent(self, name: str, agent: Agent) -> 'CrewBuilder':
        self.agents[name] = agent
        return self

    def add_task(self, task: Task) -> 'CrewBuilder':
        self.tasks.append(task)
        return self

    def add_shared_context(self, key: str, value) -> 'CrewBuilder':
        self.shared_context[key] = value
        return self

    def print_crew(self) -> 'CrewBuilder':
        """Prints a formatted representation of the crew structure.

        This method displays all agents, tasks, and their dependencies in a
        tree-like structure for better visualization.

        Returns:
            CrewBuilder: The builder instance for method chaining.
        """
        print("\n🤖 Crew Structure")
        print("═══════════════\n")

        # Print Agents
        print("📋 Agents:")
        if not self.agents:
            print("   No agents registered")
        for name, agent in self.agents.items():
            print(f"   • {name}")
        print()

        # Print Tasks and Dependencies
        print("📝 Tasks and Dependencies:")
        if not self.tasks:
            print("   No tasks defined")
        for task in self.tasks:
            print(f"   • {task.name}")
            if task.agent.name:
                print(f"     ├─ Agent: {task.agent.name}")
            if task.dependencies:
                print("     ├─ Dependencies:")
                for dep in task.dependencies:
                    print(f"     │  └─ {dep.source_task} (uses {dep.result_key})")
            print("     └─ Result Key: {}".format(task.result_key or 'None'))
        print()

        # Print Shared Context
        print("🔄 Shared Context:")
        if not self.shared_context:
            print("   No shared context defined")
        for key, value in self.shared_context.items():
            print(f"   • {key}: {value}")
        print()

        return self

    def add_task_chain(self, tasks: List[Task]) -> 'CrewBuilder':
        """Adds a sequence of tasks with linear dependencies.

        This method automatically creates dependencies between consecutive tasks,
        where each task depends on the result of the previous task.

        Args:
            tasks (List[Task]): List of tasks to chain together.

        Returns:
            CrewBuilder: The builder instance for method chaining.
        """
        for i in range(1, len(tasks)):
            tasks[i].dependencies.append(
                TaskDependency(tasks[i-1].name, tasks[i-1].result_key)
            )
        for task in tasks:
            self.add_task(task)
        return self
    
    def validate_crew(self) -> 'CrewBuilder':
        """Performs early validation of the crew structure.

        This method checks for potential issues in the crew configuration,
        such as circular dependencies or missing required components.

        Returns:
            CrewBuilder: The builder instance for method chaining.

        Raises:
            ValueError: If validation fails due to circular dependencies,
                       missing agents, or invalid task configurations.
        """
        # Check for circular dependencies
        visited = set()
        path = set()

        def check_circular_deps(task_name: str) -> bool:
            if task_name in path:
                return True
            if task_name in visited:
                return False
            
            path.add(task_name)
            visited.add(task_name)
            
            task = next((t for t in self.tasks if t.name == task_name), None)
            if task:
                for dep in task.dependencies:
                    if check_circular_deps(dep.task_name):
                        return True
            
            path.remove(task_name)
            return False

        # Validate each task
        for task in self.tasks:
            # Check for circular dependencies
            if check_circular_deps(task.name):
                raise ValueError(f"Circular dependency detected involving task: {task.name}")
            
            # Verify task has required agent
            if task.agent_name and task.agent_name not in self.agents:
                raise ValueError(f"Missing agent '{task.agent_name}' for task: {task.name}")
            
            # Verify task dependencies exist
            for dep in task.dependencies:
                dep_task = next((t for t in self.tasks if t.name == dep.task_name), None)
                if not dep_task:
                    raise ValueError(f"Dependency task '{dep.task_name}' not found for task: {task.name}")
                if not dep.result_key:
                    raise ValueError(f"Missing result key in dependency for task: {task.name}")

        return self

    def build(self) -> Crew:
        return Crew(self.agents, self.tasks, self.shared_context)