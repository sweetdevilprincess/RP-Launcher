"""DeepSeek API client via OpenRouter."""

import os
import json
import requests
from pathlib import Path
from typing import Optional


# Default configuration
DEFAULT_MODEL = "deepseek/deepseek-chat-v3.1"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 60  # seconds


class DeepSeekError(Exception):
    """Base exception for DeepSeek API errors."""
    pass


class MissingAPIKeyError(DeepSeekError):
    """Raised when API key is not found."""
    pass


def _load_api_key(rp_dir: Optional[Path] = None) -> str:
    """Load API key from environment, config, or secrets.json.

    Checks in order:
    1. DEEPSEEK_API_KEY environment variable
    2. OPENROUTER_API_KEY environment variable
    3. Global config.json (created by TUI settings)
    4. {rp_dir}/state/secrets.json
    5. ./state/secrets.json

    Args:
        rp_dir: RP directory to check for secrets.json

    Returns:
        API key string

    Raises:
        MissingAPIKeyError: If no API key found
    """
    # Check environment variables
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        return api_key

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        return api_key

    # Check global config.json (TUI settings)
    base_dir = Path(__file__).parent.parent.parent
    config_file = base_dir / "config.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding='utf-8'))
            api_key = config.get("deepseek_api_key")
            if api_key:
                return api_key
        except Exception:
            pass

    # Check secrets.json in RP directory
    if rp_dir:
        secrets_file = rp_dir / "state" / "secrets.json"
        if secrets_file.exists():
            try:
                secrets = json.loads(secrets_file.read_text(encoding='utf-8'))
                api_key = secrets.get("OPENROUTER_API_KEY") or secrets.get("DEEPSEEK_API_KEY")
                if api_key:
                    return api_key
            except Exception:
                pass

    # Check secrets.json in current directory
    secrets_file = Path("state/secrets.json")
    if secrets_file.exists():
        try:
            secrets = json.loads(secrets_file.read_text(encoding='utf-8'))
            api_key = secrets.get("OPENROUTER_API_KEY") or secrets.get("DEEPSEEK_API_KEY")
            if api_key:
                return api_key
        except Exception:
            pass

    raise MissingAPIKeyError(
        "DeepSeek API key not found. Please:\n"
        "  1. Press F9 in TUI to add DeepSeek key in Settings, OR\n"
        "  2. Set OPENROUTER_API_KEY or DEEPSEEK_API_KEY environment variable, OR\n"
        "  3. Add to state/secrets.json"
    )


def call_deepseek(
    prompt: str,
    rp_dir: Optional[Path] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    endpoint: str = DEFAULT_ENDPOINT,
    timeout: int = DEFAULT_TIMEOUT
) -> str:
    """Call DeepSeek API via OpenRouter.

    Args:
        prompt: The prompt to send
        rp_dir: RP directory (used to find secrets.json)
        model: Model to use (default: deepseek/deepseek-chat-v3.1)
        temperature: Temperature for generation (default: 0.3)
        endpoint: API endpoint (default: OpenRouter)
        timeout: Request timeout in seconds (default: 60)

    Returns:
        Generated text from the API

    Raises:
        MissingAPIKeyError: If API key not found
        DeepSeekError: If API call fails
        requests.exceptions.Timeout: If request times out
        requests.exceptions.RequestException: For other request errors
    """
    # Load API key
    api_key = _load_api_key(rp_dir)

    # Build request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }

    # Make request
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise DeepSeekError(f"API returned error: {e}")

    # Parse response
    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise DeepSeekError(f"Failed to parse API response: {e}")


# CLI interface for command-line usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m work_in_progress.clients.deepseek \"your prompt here\"")
        sys.exit(1)

    prompt = sys.argv[1]

    try:
        result = call_deepseek(prompt)
        print(result)
    except MissingAPIKeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except DeepSeekError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
