"""Unit tests for AgentFormatter - Result formatting strategies.

Tests the AgentFormatter component with different output formats.
"""

import json
import pytest
from refactoring.src.automation.contracts import AgentExecutionResult
from refactoring.src.automation.services.agent_formatter import (
    AgentFormatter,
    JsonCacheFormatter,
    PromptInjectionFormatter,
)


@pytest.mark.unit
def test_json_cache_formatter_basic_structure():
    """Test that JSON cache formatter creates correct structure."""
    formatter = JsonCacheFormatter()

    result = AgentExecutionResult(
        agent_id="test_agent",
        success=True,
        content='{"data": "test"}',
        duration_ms=100,
    )

    cache_data = formatter.format(
        results=[result],
        response_number=42,
    )

    # Verify structure
    assert "version" in cache_data
    assert cache_data["version"] == "1.0"
    assert "meta" in cache_data
    assert cache_data["meta"]["resp_num"] == 42
    assert cache_data["meta"]["agents_run"] == 1
    assert cache_data["meta"]["agents_ok"] == 1
    assert cache_data["meta"]["agents_fail"] == 0
    assert "background" in cache_data
    assert "immediate" in cache_data
    assert "stats" in cache_data


@pytest.mark.unit
def test_json_cache_formatter_successful_results():
    """Test formatting successful agent results."""
    formatter = JsonCacheFormatter()

    result1 = AgentExecutionResult(
        agent_id="agent1",
        success=True,
        content='{"key1": "value1"}',
        duration_ms=100,
    )

    result2 = AgentExecutionResult(
        agent_id="agent2",
        success=True,
        content='{"key2": "value2"}',
        duration_ms=150,
    )

    cache_data = formatter.format(
        results=[result1, result2],
        response_number=1,
    )

    # Verify background results are parsed
    assert "agent1" in cache_data["background"]
    assert cache_data["background"]["agent1"]["key1"] == "value1"
    assert "agent2" in cache_data["background"]
    assert cache_data["background"]["agent2"]["key2"] == "value2"

    # Verify stats
    assert cache_data["stats"]["total_dur"] == 250


@pytest.mark.unit
def test_json_cache_formatter_failed_results():
    """Test that failed results are counted but not included in data."""
    formatter = JsonCacheFormatter()

    result1 = AgentExecutionResult(
        agent_id="good",
        success=True,
        content='{"data": "ok"}',
        duration_ms=100,
    )

    result2 = AgentExecutionResult(
        agent_id="bad",
        success=False,
        content="Error occurred",
        duration_ms=50,
    )

    cache_data = formatter.format(
        results=[result1, result2],
        response_number=1,
    )

    # Verify counts
    assert cache_data["meta"]["agents_run"] == 2
    assert cache_data["meta"]["agents_ok"] == 1
    assert cache_data["meta"]["agents_fail"] == 1

    # Verify only successful result in background
    assert "good" in cache_data["background"]
    assert "bad" not in cache_data["background"]


@pytest.mark.unit
def test_json_cache_formatter_non_json_content():
    """Test handling of non-JSON content from agents."""
    formatter = JsonCacheFormatter()

    result = AgentExecutionResult(
        agent_id="text_agent",
        success=True,
        content="This is plain text, not JSON",
        duration_ms=100,
    )

    cache_data = formatter.format(
        results=[result],
        response_number=1,
    )

    # Should store as raw text with error marker
    assert "text_agent" in cache_data["background"]
    assert "raw" in cache_data["background"]["text_agent"]
    assert "error" in cache_data["background"]["text_agent"]
    assert cache_data["background"]["text_agent"]["error"] == "non-json"


@pytest.mark.unit
def test_json_cache_formatter_with_immediate_results():
    """Test including immediate results in cache."""
    formatter = JsonCacheFormatter()

    background_result = AgentExecutionResult(
        agent_id="bg_agent",
        success=True,
        content='{"bg": "data"}',
        duration_ms=200,
    )

    immediate_result = AgentExecutionResult(
        agent_id="im_agent",
        success=True,
        content='{"im": "data"}',
        duration_ms=50,
    )

    cache_data = formatter.format(
        results=[background_result],
        response_number=1,
        immediate_results=[immediate_result],
    )

    # Verify both sections populated
    assert "bg_agent" in cache_data["background"]
    assert "im_agent" in cache_data["immediate"]

    # Verify stats separated
    assert cache_data["stats"]["bg_dur"] == 200
    assert cache_data["stats"]["im_dur"] == 50


@pytest.mark.unit
def test_json_cache_formatter_empty_results():
    """Test formatting with no results."""
    formatter = JsonCacheFormatter()

    cache_data = formatter.format(
        results=[],
        response_number=1,
    )

    # Should still have valid structure
    assert cache_data["meta"]["agents_run"] == 0
    assert cache_data["meta"]["agents_ok"] == 0
    assert cache_data["background"] == {}
    assert cache_data["immediate"] == {}


@pytest.mark.unit
def test_prompt_injection_formatter_basic_structure():
    """Test that prompt formatter creates markdown structure."""
    formatter = PromptInjectionFormatter()

    result = AgentExecutionResult(
        agent_id="test_agent",
        success=True,
        content='{}',
        duration_ms=100,
    )

    prompt_text = formatter.format([result])

    # Should have comment delimiters
    assert "<!-- AGENT CONTEXT -->" in prompt_text
    assert "<!-- END AGENT CONTEXT -->" in prompt_text


@pytest.mark.unit
def test_prompt_injection_formatter_entity_analysis():
    """Test formatting quick_entity_analysis results."""
    formatter = PromptInjectionFormatter()

    result = AgentExecutionResult(
        agent_id="quick_entity_analysis",
        success=True,
        content=json.dumps({
            "tier1": ["Alice", "Bob"],
            "tier2": ["Charlie"],
        }),
        duration_ms=100,
    )

    prompt_text = formatter.format([result])

    # Should format entity tiers
    assert "Entities" in prompt_text
    assert "Scene" in prompt_text
    assert "Alice" in prompt_text
    assert "Mentioned" in prompt_text
    assert "Charlie" in prompt_text


@pytest.mark.unit
def test_prompt_injection_formatter_fact_extraction():
    """Test formatting fact_extraction results."""
    formatter = PromptInjectionFormatter()

    result = AgentExecutionResult(
        agent_id="fact_extraction",
        success=True,
        content=json.dumps({
            "facts": {
                "Alice": ["tall", "brave", "from London"],
                "Bob": ["quiet", "mysterious"],
            }
        }),
        duration_ms=100,
    )

    prompt_text = formatter.format([result])

    # Should format facts (max 2 entities, 3 facts each)
    assert "Alice" in prompt_text
    assert "tall" in prompt_text
    assert "brave" in prompt_text


@pytest.mark.unit
def test_prompt_injection_formatter_memory_extraction():
    """Test formatting memory_extraction results."""
    formatter = PromptInjectionFormatter()

    result = AgentExecutionResult(
        agent_id="memory_extraction",
        success=True,
        content=json.dumps({
            "memories": {
                "Alice": [
                    {"id": "MEM_001", "text": "remembers..."},
                    {"id": "MEM_002", "text": "recalls..."},
                ]
            }
        }),
        duration_ms=100,
    )

    prompt_text = formatter.format([result])

    # Should format memory IDs
    assert "Alice" in prompt_text
    assert "Memories" in prompt_text
    assert "MEM_001" in prompt_text


@pytest.mark.unit
def test_prompt_injection_formatter_plot_extraction():
    """Test formatting plot_thread_extraction results."""
    formatter = PromptInjectionFormatter()

    result = AgentExecutionResult(
        agent_id="plot_thread_extraction",
        success=True,
        content=json.dumps({
            "loaded": [
                {"id": "PLOT_001", "title": "Thread 1"},
                {"id": "PLOT_002", "title": "Thread 2"},
            ]
        }),
        duration_ms=100,
    )

    prompt_text = formatter.format([result])

    # Should format thread IDs
    assert "Active Threads" in prompt_text
    assert "PLOT_001" in prompt_text
    assert "PLOT_002" in prompt_text


@pytest.mark.unit
def test_prompt_injection_formatter_failed_results():
    """Test that failed results are excluded from prompt."""
    formatter = PromptInjectionFormatter()

    result1 = AgentExecutionResult(
        agent_id="good",
        success=True,
        content='{"data": "ok"}',
        duration_ms=100,
    )

    result2 = AgentExecutionResult(
        agent_id="bad",
        success=False,
        content="Error",
        duration_ms=50,
    )

    prompt_text = formatter.format([result1, result2])

    # Should only include successful results
    # (Would see agent-specific formatting if processed)
    assert "<!-- AGENT CONTEXT -->" in prompt_text


@pytest.mark.unit
def test_prompt_injection_formatter_malformed_json():
    """Test that malformed JSON is silently skipped."""
    formatter = PromptInjectionFormatter()

    result = AgentExecutionResult(
        agent_id="quick_entity_analysis",
        success=True,
        content="Not valid JSON{",
        duration_ms=100,
    )

    prompt_text = formatter.format([result])

    # Should not crash, just return empty context
    assert "<!-- AGENT CONTEXT -->" in prompt_text
    assert "<!-- END AGENT CONTEXT -->" in prompt_text


@pytest.mark.unit
def test_prompt_injection_formatter_empty_results():
    """Test formatting with no results."""
    formatter = PromptInjectionFormatter()

    prompt_text = formatter.format([])

    # Should return minimal structure
    assert "<!-- AGENT CONTEXT -->" in prompt_text
    assert "<!-- END AGENT CONTEXT -->" in prompt_text


@pytest.mark.unit
def test_agent_formatter_facade_format_for_cache(stub_logger):
    """Test AgentFormatter facade format_for_cache method."""
    formatter = AgentFormatter(logger=stub_logger)

    result = AgentExecutionResult(
        agent_id="test",
        success=True,
        content='{"data": "test"}',
        duration_ms=100,
    )

    cache_data = formatter.format_for_cache(
        results=[result],
        response_number=5,
    )

    # Should delegate to JsonCacheFormatter
    assert cache_data["meta"]["resp_num"] == 5
    assert "test" in cache_data["background"]

    # Should log the operation
    assert any("agent_formatter.cache_formatted" in msg for msg in stub_logger.messages)


@pytest.mark.unit
def test_agent_formatter_facade_format_for_prompt(stub_logger):
    """Test AgentFormatter facade format_for_prompt method."""
    formatter = AgentFormatter(logger=stub_logger)

    result = AgentExecutionResult(
        agent_id="quick_entity_analysis",
        success=True,
        content='{"tier1": ["Alice"]}',
        duration_ms=100,
    )

    prompt_text = formatter.format_for_prompt([result])

    # Should delegate to PromptInjectionFormatter
    assert "<!-- AGENT CONTEXT -->" in prompt_text
    assert "Alice" in prompt_text

    # Should log the operation
    assert any("agent_formatter.prompt_formatted" in msg for msg in stub_logger.messages)


@pytest.mark.unit
def test_agent_formatter_repr():
    """Test formatter string representation."""
    formatter = AgentFormatter()

    repr_str = repr(formatter)

    assert "AgentFormatter" in repr_str
    assert "json" in repr_str
    assert "prompt" in repr_str
