"""
Common JSON Utilities

Shared JSON parsing utilities with fallbacks to eliminate duplication across agents.
Every agent's format_output repeats json.loads() with identical error handling.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set
import logging


logger = logging.getLogger(__name__)


def parse_json_safe(
    text: str,
    required_fields: Optional[List[str]] = None,
    default: Optional[Any] = None,
    log_errors: bool = True
) -> Any:
    """Parse JSON with safe fallback and field validation.

    Replaces repeated json.loads() + try/except blocks in every agent's format_output.

    Args:
        text: JSON text to parse
        required_fields: List of required top-level keys (validates after parsing)
        default: Default value if parsing fails (default: empty dict)
        log_errors: Whether to log parsing errors

    Returns:
        Parsed JSON object or default value

    Example:
        # Basic usage
        data = parse_json_safe(response_text, default={})

        # With field validation
        data = parse_json_safe(
            response_text,
            required_fields=["entities", "facts"],
            default={"entities": [], "facts": []}
        )
    """
    if default is None:
        default = {}

    # Try to parse JSON
    try:
        parsed = json.loads(text)

        # Validate required fields
        if required_fields and isinstance(parsed, dict):
            missing = [f for f in required_fields if f not in parsed]
            if missing:
                if log_errors:
                    logger.warning(f"JSON missing required fields: {missing}")
                return default

        return parsed

    except json.JSONDecodeError as e:
        if log_errors:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Failed to parse: {text[:200]}...")

        return default


def extract_json_from_text(
    text: str,
    required_fields: Optional[List[str]] = None,
    default: Optional[Any] = None
) -> Any:
    """Extract JSON object from text (handles markdown code blocks, etc.).

    Useful when LLM wraps JSON in markdown or adds extra text.

    Args:
        text: Text potentially containing JSON
        required_fields: List of required fields
        default: Default value if no JSON found

    Returns:
        Parsed JSON object or default value

    Example:
        # Handles: ```json\\n{"key": "value"}\\n```
        data = extract_json_from_text(response_text)
    """
    if default is None:
        default = {}

    # Try direct parse first
    result = parse_json_safe(text, required_fields=required_fields, default=None, log_errors=False)
    if result is not None:
        return result

    # Try to extract from code blocks
    patterns = [
        r'```json\s*\n(.*?)\n```',  # ```json ... ```
        r'```\s*\n(.*?)\n```',       # ``` ... ```
        r'\{.*\}',                    # Anything that looks like JSON object
        r'\[.*\]'                     # Anything that looks like JSON array
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            result = parse_json_safe(match, required_fields=required_fields, default=None, log_errors=False)
            if result is not None:
                return result

    logger.warning("Could not extract valid JSON from text")
    return default


def build_error_payload(
    error_message: str,
    required_fields: Optional[List[str]] = None,
    error_value: Any = None
) -> Dict[str, Any]:
    """Build standardized error payload for failed agent operations.

    Replaces repeated error dict construction across agents.

    Args:
        error_message: Error message
        required_fields: Fields to populate with error_value
        error_value: Value to use for required fields (default: empty list/dict based on context)

    Returns:
        Error payload dict

    Example:
        # Returns: {"entities": [], "facts": [], "error": "Parse failed"}
        payload = build_error_payload(
            "Parse failed",
            required_fields=["entities", "facts"],
            error_value=[]
        )
    """
    payload = {"error": error_message}

    if required_fields:
        for field in required_fields:
            if error_value is not None:
                payload[field] = error_value
            else:
                # Infer default based on field name
                if field.endswith('s') or 'list' in field.lower():
                    payload[field] = []
                else:
                    payload[field] = {}

    return payload


def merge_json_objects(*objects: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge multiple JSON objects.

    Args:
        *objects: JSON objects to merge (later objects override earlier ones)

    Returns:
        Merged object
    """
    result = {}

    for obj in objects:
        if not isinstance(obj, dict):
            continue

        for key, value in obj.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_json_objects(result[key], value)
            else:
                result[key] = value

    return result


def validate_json_schema(
    data: Any,
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None,
    allow_extra: bool = True
) -> tuple[bool, Optional[str]]:
    """Validate JSON object against simple schema.

    Args:
        data: Data to validate
        required_fields: Required top-level keys
        optional_fields: Optional top-level keys
        allow_extra: Allow extra fields not in required/optional

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Data is not a dictionary"

    # Check required fields
    missing = [f for f in required_fields if f not in data]
    if missing:
        return False, f"Missing required fields: {missing}"

    # Check for unexpected fields
    if not allow_extra:
        expected = set(required_fields)
        if optional_fields:
            expected.update(optional_fields)

        extra = set(data.keys()) - expected
        if extra:
            return False, f"Unexpected fields: {extra}"

    return True, None


def sanitize_json_string(text: str) -> str:
    """Sanitize string for safe JSON inclusion.

    Handles newlines, quotes, and other problematic characters.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    # Escape special characters
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    text = text.replace('\n', '\\n')
    text = text.replace('\r', '\\r')
    text = text.replace('\t', '\\t')

    return text
