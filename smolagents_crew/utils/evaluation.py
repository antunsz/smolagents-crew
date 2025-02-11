"""Module for tracking and evaluating crew execution performance."""

from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

@dataclass
class TaskExecutionStats:
    task_name: str
    start_time: datetime
    end_time: datetime | None
    dependencies: List[str]
    agent_name: str

    @property
    def execution_time(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

class CrewEvaluator:
    def __init__(self):
        self.task_stats: Dict[str, TaskExecutionStats] = {}
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    def start_evaluation(self):
        self.start_time = datetime.now()

    def end_evaluation(self):
        self.end_time = datetime.now()

    def record_task_start(self, task_name: str, agent_name: str, dependencies: List[str]):
        self.task_stats[task_name] = TaskExecutionStats(
            task_name=task_name,
            start_time=datetime.now(),
            end_time=None,
            dependencies=dependencies,
            agent_name=agent_name
        )

    def record_task_end(self, task_name: str):
        if task_name in self.task_stats:
            self.task_stats[task_name].end_time = datetime.now()

    def get_total_execution_time(self) -> float:
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def get_parallel_execution_stats(self) -> Dict[str, List[str]]:
        parallel_groups = defaultdict(list)
        for task_name, stats in self.task_stats.items():
            # Skip tasks that haven't completed
            if stats.end_time is None:
                continue
            for other_name, other_stats in self.task_stats.items():
                # Skip incomplete tasks and self-comparison
                if task_name == other_name or other_stats.end_time is None:
                    continue
                if (
                    stats.start_time <= other_stats.start_time <= stats.end_time
                    or stats.start_time <= other_stats.end_time <= stats.end_time
                ):
                    parallel_groups[task_name].append(other_name)
        return dict(parallel_groups)

    def generate_execution_report(self) -> str:
        if not self.task_stats:
            return "No execution statistics available."

        report = ["Crew Execution Report"]
        report.append("-" * 20)
        report.append(f"Total Execution Time: {self.get_total_execution_time():.2f} seconds\n")

        report.append("Task Execution Details:")
        for task_name, stats in self.task_stats.items():
            report.append(f"\nTask: {task_name}")
            report.append(f"Agent: {stats.agent_name}")
            report.append(f"Execution Time: {stats.execution_time:.2f} seconds")
            if stats.dependencies:
                report.append(f"Dependencies: {', '.join(stats.dependencies)}")

        parallel_stats = self.get_parallel_execution_stats()
        if parallel_stats:
            report.append("\nParallel Execution Groups:")
            for task, parallel_tasks in parallel_stats.items():
                if parallel_tasks:
                    report.append(f"{task} ran in parallel with: {', '.join(parallel_tasks)}")

        return '\n'.join(report)