"""
Agent Result Dataclass

Standardized result format for all agent operations.
Replaces ad-hoc JSON structures with consistent schema.
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional
from datetime import datetime
import json


@dataclass
class AgentResult:
    """Standardized result from agent execution.

    All agents should return this format for consistency.
    Replaces scattered JSON structures across background/immediate agents.

    Attributes:
        success: Whether agent execution succeeded
        agent_id: Agent identifier (e.g., "fact_extraction", "entity_analysis")
        payload: Agent-specific result data
        model: Model used for generation (optional)
        duration_ms: Execution time in milliseconds (optional)
        error: Error message if failed (optional)
        timestamp: When result was generated
        metadata: Additional metadata (optional)
    """

    success: bool
    agent_id: str
    payload: Dict[str, Any]
    model: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls,
        agent_id: str,
        payload: Dict[str, Any],
        model: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **metadata
    ) -> 'AgentResult':
        """Create successful result.

        Args:
            agent_id: Agent identifier
            payload: Result payload
            model: Model used
            duration_ms: Execution time
            **metadata: Additional metadata

        Returns:
            AgentResult with success=True

        Example:
            return AgentResult.success_result(
                agent_id="fact_extraction",
                payload={"facts": extracted_facts},
                model="claude-3-opus",
                duration_ms=1234.5
            )
        """
        return cls(
            success=True,
            agent_id=agent_id,
            payload=payload,
            model=model,
            duration_ms=duration_ms,
            metadata=metadata
        )

    @classmethod
    def error_result(
        cls,
        agent_id: str,
        error: str,
        payload: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        **metadata
    ) -> 'AgentResult':
        """Create error result.

        Args:
            agent_id: Agent identifier
            error: Error message
            payload: Partial payload (optional)
            duration_ms: Execution time
            **metadata: Additional metadata

        Returns:
            AgentResult with success=False

        Example:
            return AgentResult.error_result(
                agent_id="fact_extraction",
                error="Failed to parse JSON response",
                payload={"facts": []}  # Empty fallback
            )
        """
        return cls(
            success=False,
            agent_id=agent_id,
            payload=payload or {},
            error=error,
            duration_ms=duration_ms,
            metadata=metadata
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return asdict(self)

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string.

        Args:
            indent: JSON indentation

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResult':
        """Create from dictionary.

        Args:
            data: Dictionary with result fields

        Returns:
            AgentResult instance
        """
        # Extract known fields
        known_fields = {
            'success', 'agent_id', 'payload', 'model',
            'duration_ms', 'error', 'timestamp', 'metadata'
        }

        kwargs = {k: v for k, v in data.items() if k in known_fields}
        return cls(**kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> 'AgentResult':
        """Create from JSON string.

        Args:
            json_str: JSON string

        Returns:
            AgentResult instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __repr__(self) -> str:
        """String representation."""
        status = "✓" if self.success else "✗"
        duration_str = f", {self.duration_ms:.0f}ms" if self.duration_ms else ""
        error_str = f", error: {self.error}" if self.error else ""

        return f"<AgentResult {status} {self.agent_id}{duration_str}{error_str}>"


@dataclass
class CachedAgentResult:
    """Cached result with cache metadata.

    Extends AgentResult with cache-specific fields.
    """

    result: AgentResult
    cache_key: str
    cached_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    hit_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result": self.result.to_dict(),
            "cache_key": self.cache_key,
            "cached_at": self.cached_at,
            "expires_at": self.expires_at,
            "hit_count": self.hit_count
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


def combine_agent_results(
    *results: AgentResult,
    combined_agent_id: str = "combined"
) -> AgentResult:
    """Combine multiple agent results into one.

    Args:
        *results: Agent results to combine
        combined_agent_id: ID for combined result

    Returns:
        Combined AgentResult
    """
    # Check if all succeeded
    all_success = all(r.success for r in results)

    # Combine payloads
    combined_payload = {}
    for result in results:
        combined_payload.update(result.payload)

    # Collect errors
    errors = [r.error for r in results if r.error]
    combined_error = "; ".join(errors) if errors else None

    # Sum durations
    total_duration = sum(r.duration_ms for r in results if r.duration_ms)

    # Collect models
    models = list(set(r.model for r in results if r.model))
    combined_model = models[0] if len(models) == 1 else ", ".join(models) if models else None

    return AgentResult(
        success=all_success,
        agent_id=combined_agent_id,
        payload=combined_payload,
        model=combined_model,
        duration_ms=total_duration if total_duration > 0 else None,
        error=combined_error,
        metadata={"component_count": len(results)}
    )
