"""Unit tests for core functionality.

This module contains tests for the core classes (Task, Agent, Crew)
of the SmolagentsCrew framework."""

import pytest
from unittest.mock import Mock
from smolagents_crew.core import Task, Agent, Crew, TaskDependency


def test_task_creation():
    """Test task creation with dependencies and variable management."""
    agent = Mock(spec=Agent)
    task = Task(
        name="test",
        agent=agent,
        prompt_template="Test {param}",
        result_key="test_result"
    )
    assert task.name == "test"
    assert task.agent == agent
    assert task.prompt_template == "Test {param}"
    assert task.result_key == "test_result"
    assert task.required_vars == ["param"]
    assert not task._completed


def test_task_dependencies():
    """Test task dependency management."""
    agent = Mock(spec=Agent)
    dep = TaskDependency("task1", "result1")
    task = Task(
        name="test",
        agent=agent,
        prompt_template="Test {param}",
        dependencies=[dep]
    )
    assert len(task.dependencies) == 1
    assert task.dependencies[0].source_task == "task1"
    assert task.dependencies[0].result_key == "result1"


def test_task_readiness():
    """Test task readiness checking."""
    agent = Mock(spec=Agent)
    dep = TaskDependency("task1", "result1")
    task = Task(
        name="test",
        agent=agent,
        prompt_template="Test {param}",
        dependencies=[dep]
    )
    
    # Not ready - missing dependency and variable
    context = {}
    assert not task.is_ready(context)
    
    # Not ready - missing variable
    context = {"result1": "value"}
    assert not task.is_ready(context)
    
    # Ready - all dependencies and variables present
    context = {"result1": "value", "param": "test"}
    assert task.is_ready(context)


def test_task_execution():
    """Test task execution with context management."""
    agent = Mock(spec=Agent)
    agent.run.return_value = "executed"
    
    task = Task(
        name="test",
        agent=agent,
        prompt_template="Test {param}",
        result_key="test_result"
    )
    
    context = {"param": "value"}
    task.execute(context)
    
    assert task._completed
    assert task._result == "executed"
    assert context["test_result"] == "executed"
    agent.run.assert_called_once_with("Test value")


def test_crew_execution():
    """Test crew task execution with threading."""
    agent1 = Mock(spec=Agent)
    agent2 = Mock(spec=Agent)
    agent1.run.return_value = "result1"
    agent2.run.return_value = "result2"
    
    task1 = Task(
        name="task1",
        agent=agent1,
        prompt_template="Test1 {param}",
        result_key="result1"
    )
    task2 = Task(
        name="task2",
        agent=agent2,
        prompt_template="Test2 {result1}",
        dependencies=[TaskDependency("task1", "result1")],
        result_key="result2"
    )
    
    crew = Crew(
        agents={"agent1": agent1, "agent2": agent2},
        tasks=[task1, task2],
        initial_context={"param": "value"}
    )
    
    result_context = crew.execute()
    
    assert "result1" in result_context
    assert "result2" in result_context
    assert result_context["result1"] == "result1"
    assert result_context["result2"] == "result2"
    assert len(crew.completed_tasks) == 2