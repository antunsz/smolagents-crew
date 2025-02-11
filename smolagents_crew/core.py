import threading
from string import Formatter
from typing import Dict, List, Optional, Callable
from smolagents import MultiStepAgent as SmolagentAgent, ChatMessage as SmolagentAgentChatMessage

class TaskDependency:
    """Represents a dependency between tasks.

    This class defines a relationship where one task depends on the result of another task.

    Args:
        source_task (str): The name of the task that produces the required result.
        result_key (str): The key under which the result is stored in the context.
    """
    def __init__(self, source_task: str, result_key: str):
        self.source_task = source_task
        self.result_key = result_key

class Task:
    """Represents an atomic task in the system with automatic variable management.

    This class handles the execution of individual tasks, managing their dependencies
    and required variables automatically. It ensures all necessary conditions are met
    before task execution.

    Args:
        name (str): The unique identifier for the task.
        agent (Agent): The agent responsible for executing the task.
        prompt_template (str): The template string for generating the task's prompt.
        dependencies (List[TaskDependency], optional): List of task dependencies.
        result_key (str, optional): Key under which to store the task's result.
    """
    def __init__(self, 
                 name: str,
                 agent: 'Agent',
                 prompt_template: str,
                 dependencies: List[TaskDependency] = None,
                 result_key: Optional[str] = None):
        self.name = name
        self.agent = agent
        self.prompt_template = prompt_template
        self.dependencies = dependencies or []
        self.result_key = result_key
        self.required_vars = self._extract_template_vars()
        self._result = None
        self._completed = False

    def _extract_template_vars(self) -> List[str]:
        formatter = Formatter()
        return [fn for _, fn, _, _ in formatter.parse(self.prompt_template) if fn is not None]

    def is_ready(self, context: Dict) -> bool:
        dependencies_ready = all(context.get(dep.result_key) is not None for dep in self.dependencies)
        vars_ready = all(var in context for var in self.required_vars)
        return dependencies_ready and vars_ready

    def execute(self, context: Dict):
        if not self.is_ready(context):
            missing_deps = [dep.result_key for dep in self.dependencies if dep.result_key not in context]
            missing_vars = [var for var in self.required_vars if var not in context]
            raise ValueError(
                f"Task {self.name} not ready. Missing dependencies: {missing_deps}, "
                f"Missing variables: {missing_vars}"
            )

        try:
            prompt = self.prompt_template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing variable in template: {e}") from e

        self._result = self.agent.run(prompt)
        
        if self.result_key:
            context[self.result_key] = self._result
        
        self._completed = True

class Agent:
    """Factory for creating specialized agents.

    This class serves as a factory for creating and configuring specialized agents
    that can execute specific tasks within the system.

    Args:
        name (str): The unique identifier for the agent.
        agent_instance (SmolagentAgent): The base agent class to instantiate.
        model (Callable): The model function for processing agent responses.
        tools (list): List of tools available to the agent.
        imports (List[str], optional): Additional Python imports for the agent.
    """
    def __init__(self, name: str, agent_instance: SmolagentAgent, model:Callable[[List[Dict[str, str]]], SmolagentAgentChatMessage], tools: list, imports: List[str] = None):
        self.name = name
        self.instance = agent_instance(
            tools=tools,
            model=model,
            additional_authorized_imports=imports or []
        )

    def run(self, prompt: str) -> str:
        return self.instance.run(prompt)

class Crew:
    """Main class with optimized execution using threading.

    This class orchestrates the execution of multiple tasks in parallel,
    managing their dependencies and shared context.

    Args:
        agents (Dict[str, Agent]): Dictionary of available agents.
        tasks (List[Task]): List of tasks to execute.
        initial_context (Dict): Initial context data for task execution.
    """
    def __init__(self, agents: Dict[str, Agent], tasks: List[Task], initial_context: Dict):
        self.agents = agents
        self.tasks = tasks
        self.context = initial_context.copy()
        self.lock = threading.Lock()
        self.completed_tasks = []
        self.evaluator = None

    def _task_runner(self, task: Task):
        try:
            with self.lock:
                if not task.is_ready(self.context):
                    return

            task.execute(self.context)

            with self.lock:
                self.completed_tasks.append(task.name)
                if self.evaluator:
                    self.evaluator.record_task_end(task.name)
                print(f"✅ Task completed: {task.name}")

        except Exception as e:
            print(f"❌ Error in task {task.name}: {str(e)}")

    def execute(self, evaluate: bool = False):
        from .utils.evaluation import CrewEvaluator
        
        threads = []
        remaining_tasks = self.tasks.copy()

        if evaluate:
            self.evaluator = CrewEvaluator()
            self.evaluator.start_evaluation()

        while remaining_tasks:
            current_batch = []

            with self.lock:
                current_batch = [task for task in remaining_tasks if task.is_ready(self.context)]
                remaining_tasks = [task for task in remaining_tasks if task not in current_batch]

            if not current_batch:
                if remaining_tasks:
                    print("⚠️ Deadlock detected! Check for circular dependencies or missing variables.")
                break

            for task in current_batch:
                if self.evaluator:
                    self.evaluator.record_task_start(
                        task.name,
                        task.agent.name,
                        [dep.source_task for dep in task.dependencies]
                    )
                thread = threading.Thread(target=self._task_runner, args=(task,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

        if self.evaluator:
            self.evaluator.end_evaluation()
            print(self.evaluator.generate_execution_report())

        print("\n🏁 All tasks completed!")
        return self.context