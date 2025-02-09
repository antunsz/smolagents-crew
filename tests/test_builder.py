"""Unit tests for the CrewBuilder functionality.

This module contains tests for the CrewBuilder and AdvancedCrewBuilder classes
and their methods for constructing customized agent crews."""

import pytest
from unittest.mock import Mock
from smolagents_crew.core import Task, Agent, TaskDependency
from smolagents_crew.builder import CrewBuilder, AdvancedCrewBuilder


def test_builder_creation():
    """Test CrewBuilder initialization."""
    builder = CrewBuilder()
    assert len(builder.agents) == 0
    assert len(builder.tasks) == 0
    assert len(builder.shared_context) == 0


def test_builder_add_agent():
    """Test adding agent to the builder."""
    agent = Mock(spec=Agent)
    builder = CrewBuilder()
    builder.add_agent("test_agent", agent)
    
    assert len(builder.agents) == 1
    assert builder.agents["test_agent"] == agent


def test_builder_add_task():
    """Test adding task to the builder."""
    agent = Mock(spec=Agent)
    task = Task(
        name="test_task",
        agent=agent,
        prompt_template="Test {param}",
        result_key="test_result"
    )
    
    builder = CrewBuilder()
    builder.add_task(task)
    
    assert len(builder.tasks) == 1
    assert builder.tasks[0] == task


def test_builder_add_shared_context():
    """Test adding shared context to the builder."""
    builder = CrewBuilder()
    builder.add_shared_context("key", "value")
    
    assert len(builder.shared_context) == 1
    assert builder.shared_context["key"] == "value"


def test_builder_build():
    """Test building a crew with all components."""
    agent = Mock(spec=Agent)
    task = Task(
        name="test_task",
        agent=agent,
        prompt_template="Test {param}",
        result_key="test_result"
    )
    
    builder = CrewBuilder()
    builder.add_agent("test_agent", agent)
    builder.add_task(task)
    builder.add_shared_context("param", "value")
    
    crew = builder.build()
    
    assert len(crew.agents) == 1
    assert len(crew.tasks) == 1
    assert len(crew.context) == 1


def test_advanced_builder_task_chain():
    """Test AdvancedCrewBuilder task chain creation."""
    agent = Mock(spec=Agent)
    task1 = Task(
        name="task1",
        agent=agent,
        prompt_template="Test1 {param}",
        result_key="result1"
    )
    task2 = Task(
        name="task2",
        agent=agent,
        prompt_template="Test2 {result1}",
        result_key="result2"
    )
    
    builder = AdvancedCrewBuilder()
    builder.add_agent("test_agent", agent)
    builder.add_task_chain([task1, task2])
    
    # Verify task2 depends on task1
    assert len(task2.dependencies) == 1
    assert task2.dependencies[0].task_name == task1.name
    assert task2.dependencies[0].result_key == task1.result_key


def test_validate_crew_circular_dependency():
    """Test crew validation with circular dependencies."""
    agent = Mock(spec=Agent)
    task1 = Task(
        name="task1",
        agent=agent,
        prompt_template="Test1 {result2}",
        result_key="result1"
    )
    task2 = Task(
        name="task2",
        agent=agent,
        prompt_template="Test2 {result1}",
        result_key="result2"
    )
    
    task1.dependencies.append(TaskDependency(task2.name, task2.result_key))
    task2.dependencies.append(TaskDependency(task1.name, task1.result_key))
    
    builder = AdvancedCrewBuilder()
    builder.add_agent("test_agent", agent)
    builder.add_task(task1)
    builder.add_task(task2)
    
    with pytest.raises(ValueError, match="Circular dependency detected"):
        builder.validate_crew()


def test_validate_crew_missing_agent():
    """Test crew validation with missing agent."""
    agent = Mock(spec=Agent)
    task = Task(
        name="task1",
        agent=agent,
        prompt_template="Test {param}",
        result_key="result1"
    )
    
    builder = AdvancedCrewBuilder()
    builder.add_task(task)
    
    with pytest.raises(ValueError, match="Missing agent"):
        builder.validate_crew()


def test_validate_crew_missing_dependency():
    """Test crew validation with missing task dependency."""
    agent = Mock(spec=Agent)
    task = Task(
        name="task1",
        agent=agent,
        prompt_template="Test {missing_result}",
        result_key="result1"
    )
    task.dependencies.append(TaskDependency("missing_task", "missing_result"))
    
    builder = AdvancedCrewBuilder()
    builder.add_agent("test_agent", agent)
    builder.add_task(task)
    
    with pytest.raises(ValueError, match="Dependency task.*not found"):
        builder.validate_crew()


def test_print_crew(capsys):
    """Test crew structure visualization."""
    agent = Mock(spec=Agent)
    task = Task(
        name="test_task",
        agent=agent,
        prompt_template="Test {param}",
        result_key="test_result"
    )
    
    builder = CrewBuilder()
    builder.add_agent("test_agent", agent)
    builder.add_task(task)
    builder.add_shared_context("param", "value")
    builder.print_crew()
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "🤖 Crew Structure" in output
    assert "📋 Agents:" in output
    assert "test_agent" in output
    assert "📝 Tasks and Dependencies:" in output
    assert "test_task" in output
    assert "🔄 Shared Context:" in output
    assert "param: value" in output