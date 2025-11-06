#!/usr/bin/env python3
"""
TUI Bridge Script - Connects TUI to Claude Code

This script monitors for TUI input and sends it to Claude Code,
then captures the response and sends it back to the TUI.

REFACTORED VERSION - Uses modular automation system

Usage:
    python tui_bridge.py "Example RP"

Run this in a separate terminal alongside the TUI.
"""

# ============================================================================
# ⚠️  CRITICAL: DO NOT MOVE THIS CODE BELOW - MUST BE FIRST! ⚠️
# ============================================================================
# This Python path fix MUST be the very first code that runs, before ANY
# other imports. If you move this down or import anything before it, you'll
# get Unicode encoding errors (emojis failing) which indicates the wrong
# Python (conda pkgs cache) is being used.
#
# This code detects if we're using the wrong Python and relaunches with the
# correct one BEFORE any imports that would fail.
# ============================================================================

import sys
from pathlib import Path

# Check if we're using the wrong Python (pkgs cache) and relaunch if needed
current_python = Path(sys.executable)
if "\\pkgs\\" in str(current_python) or "/pkgs/" in str(current_python):
    # We're using pkgs cache Python - find the correct one
    import subprocess
    conda_root = None
    for parent in current_python.parents:
        if parent.name in ["miniconda3", "anaconda3", "miniforge3"]:
            conda_root = parent
            break

    if conda_root:
        correct_python = conda_root / "python.exe"
        if correct_python.exists():
            # Relaunch with correct Python
            result = subprocess.run(
                [str(correct_python), sys.argv[0]] + sys.argv[1:],
                cwd=str(Path.cwd())
            )
            sys.exit(result.returncode)

# Now add project root to Python path
# Bridge is in src/, so go up one level to project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now safe to import everything else
import time
import json

from src.clients.claude_api import ClaudeAPIClient, ConversationManager, load_api_settings
from src.clients.claude_sdk import ClaudeSDKClient
from src.fs_write_queue import flush_all_writes

# Import modular automation system
from src.automation.core import get_response_count
from src.automation.background_tasks import shutdown_task_queue
from src.file_manager import FileManager

# Import requests for proxy testing
import requests


# =============================================================================
# PROXY TEST FUNCTION
# =============================================================================

def test_proxy_connection(proxy_url: str, proxy_token: str) -> dict:
    """Test proxy connection in three stages: connection, auth, and message.

    Returns a dict with test results for each stage.
    """
    results = {
        "stages": {
            "connection": {"passed": False, "error": None},
            "authentication": {"passed": False, "error": None},
            "message_routing": {"passed": False, "error": None}
        },
        "summary": "Not started"
    }

    # Stage 1: Test connection
    try:
        print("  Stage 1: Testing connection to proxy...")
        response = requests.head(proxy_url, timeout=5)
        results["stages"]["connection"]["passed"] = True
        print(f"  ✅ Stage 1 passed: Proxy is reachable (HTTP {response.status_code})")
    except requests.exceptions.ConnectionError as e:
        results["stages"]["connection"]["error"] = f"Connection refused: {str(e)}"
        print(f"  ❌ Stage 1 failed: {results['stages']['connection']['error']}")
        results["summary"] = "Failed at Stage 1: Could not connect to proxy"
        return results
    except requests.exceptions.Timeout:
        results["stages"]["connection"]["error"] = "Connection timed out (proxy not responding)"
        print(f"  ❌ Stage 1 failed: {results['stages']['connection']['error']}")
        results["summary"] = "Failed at Stage 1: Proxy connection timeout"
        return results
    except Exception as e:
        results["stages"]["connection"]["error"] = str(e)
        print(f"  ❌ Stage 1 failed: {results['stages']['connection']['error']}")
        results["summary"] = f"Failed at Stage 1: {str(e)}"
        return results

    # Stage 2: Test authentication
    try:
        print("  Stage 2: Testing authentication...")
        headers = {
            "X-Proxy-Authorization": f"Bearer {proxy_token}",
            "Content-Type": "application/json"
        }
        response = requests.head(proxy_url, headers=headers, timeout=5)
        results["stages"]["authentication"]["passed"] = True
        print(f"  ✅ Stage 2 passed: Authentication accepted (HTTP {response.status_code})")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401 or e.response.status_code == 403:
            results["stages"]["authentication"]["error"] = f"Authentication failed (HTTP {e.response.status_code}): Invalid or expired token"
            print(f"  ❌ Stage 2 failed: {results['stages']['authentication']['error']}")
            results["summary"] = "Failed at Stage 2: Authentication rejected by proxy"
        else:
            results["stages"]["authentication"]["error"] = str(e)
            print(f"  ❌ Stage 2 failed: {results['stages']['authentication']['error']}")
            results["summary"] = f"Failed at Stage 2: {str(e)}"
        return results
    except Exception as e:
        results["stages"]["authentication"]["error"] = str(e)
        print(f"  ❌ Stage 2 failed: {results['stages']['authentication']['error']}")
        results["summary"] = f"Failed at Stage 2: {str(e)}"
        return results

    # Stage 3: Test message routing (simulate minimal API call)
    try:
        print("  Stage 3: Testing message routing...")
        headers = {
            "X-Proxy-Authorization": f"Bearer {proxy_token}",
            "Content-Type": "application/json"
        }
        # Send a minimal test payload
        payload = {
            "test": True,
            "message": "Proxy test"
        }
        response = requests.post(proxy_url, headers=headers, json=payload, timeout=5)
        results["stages"]["message_routing"]["passed"] = True
        print(f"  ✅ Stage 3 passed: Message routing works (HTTP {response.status_code})")
        results["summary"] = "✅ All tests passed! Proxy is working correctly."
    except requests.exceptions.HTTPError as e:
        # Some proxy responses might be 4xx/5xx but still accept the request
        results["stages"]["message_routing"]["passed"] = True
        print(f"  ✅ Stage 3 passed: Message routing accepted (HTTP {e.response.status_code})")
        results["summary"] = "✅ All tests passed! Proxy is working correctly."
    except Exception as e:
        results["stages"]["message_routing"]["error"] = str(e)
        print(f"  ❌ Stage 3 failed: {results['stages']['message_routing']['error']}")
        results["summary"] = f"Failed at Stage 3: Message routing issue - {str(e)}"

    return results


# =============================================================================
# MAIN BRIDGE LOOP
# =============================================================================

def main():
    # Initialize shutdown flag early (used in finally block)
    normal_shutdown = False

    # Initialize variables for cleanup (in case of early error)
    sdk_client = None
    ready_flag = None
    done_flag = None
    tui_active_flag = None

    try:
        if len(sys.argv) < 2:
            print("Usage: python tui_bridge.py <RP_FOLDER_NAME>")
            print("Example: python tui_bridge.py \"Example RP\"")
            sys.exit(1)

        # Get RP directory
        # Bridge is in src/, so go up one level to project root
        base_dir = Path(__file__).parent.parent
        rp_folder = sys.argv[1]
        rp_dir = base_dir / "RPs" / rp_folder

        if not rp_dir.exists():
            print(f"Error: RP folder not found: {rp_dir}")
            sys.exit(1)

        state_dir = rp_dir / "state"
        input_file = state_dir / "rp_client_input.json"
        response_file = state_dir / "rp_client_response.json"
        ready_flag = state_dir / "rp_client_ready.flag"
        done_flag = state_dir / "rp_client_done.flag"
        tui_active_flag = state_dir / "tui_active.flag"

        # Initialize Module Manager
        from src.core.module_manager import ModuleManager
        from src.core.config import ConfigLoader
        from src.modules.session.session_manager_module import SessionManagerModule
        from src.modules.files.file_manager_module import FileManagerModule
        from src.modules.files.fs_write_queue_module import FSWriteQueueModule
        from src.modules.tasks.background_task_queue_module import BackgroundTaskQueueModule
        from src.modules.entities.entity_manager_module import EntityManagerModule
        from src.modules.updates.update_checker_module import UpdateCheckerModule
        from src.modules.agents.agent_coordinator_module import AgentCoordinatorModule
        from src.modules.automation.orchestrator_module import OrchestratorModule

        # Load configuration
        config_loader = ConfigLoader(rp_dir)
        full_config = config_loader.load()

        # Create module manager
        module_manager = ModuleManager(rp_dir, full_config)

        # Register modules (order doesn't matter - manager resolves dependencies)
        module_manager.register(FileManagerModule)  # No dependencies
        module_manager.register(FSWriteQueueModule)  # Depends on FileManager
        module_manager.register(BackgroundTaskQueueModule)  # No dependencies
        module_manager.register(SessionManagerModule)  # No dependencies
        module_manager.register(EntityManagerModule)  # Depends on FileManager
        module_manager.register(UpdateCheckerModule)  # No dependencies (optional)
        module_manager.register(AgentCoordinatorModule)  # Depends on FileManager, FSWriteQueue
        module_manager.register(OrchestratorModule)  # Depends on FileManager, AgentCoordinator

        # Initialize all modules (automatic dependency order)
        if module_manager.initialize_all():
            print("📦 Module system initialized")
        else:
            print("⚠️  Some modules failed to initialize")

        # Start all modules
        if module_manager.start_all():
            print("▶️  All modules started")
        else:
            print("⚠️  Some modules failed to start")

        # Create FileManager for IPC operations (legacy)
        file_manager = FileManager(rp_dir)

        # Get orchestrator from module manager
        orchestrator = module_manager.get('orchestrator')
        if not orchestrator:
            print("⚠️  Orchestrator module not available")
        else:
            print("🎭 Automation orchestrator (V2) initialized")

        # Check for mode configuration (global config first, then per-RP)
        # Modes: SDK (default), API (alternative)
        use_api_mode = False
        use_sdk_mode = True  # SDK is now the default!
        api_client = None
        conversation_manager = None
        sdk_client = None

        try:
            # Check global config.json (created by TUI settings)
            global_config_file = base_dir / "config" / "config.json"
            local_config_file = state_dir / "config.json"

            config = {}

            # Load global config first
            if global_config_file.exists():
                with open(global_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # Override with local config if it exists
            if local_config_file.exists():
                with open(local_config_file, 'r', encoding='utf-8') as f:
                    local_config = json.load(f)
                    config.update(local_config)

            # Check if user wants API mode (alternative to SDK)
            use_api_mode = config.get("use_api_mode", False)

            # Get thinking mode configuration (default to megathink)
            thinking_mode = config.get("thinking_mode", "megathink")
            thinking_budget = config.get("thinking_budget", None)  # Custom budget overrides mode

            if use_api_mode:
                # API mode requested - use direct API calls
                use_sdk_mode = False
                api_settings = load_api_settings(config)
                api_key = api_settings.get("api_key")
                auth_token = api_settings.get("auth_token")
                base_url = api_settings.get("base_url")

                if api_key or auth_token:
                    try:
                        api_client = ClaudeAPIClient(
                            api_key=api_key,
                            base_url=base_url,
                            auth_token=auth_token
                        )
                        conversation_manager = ConversationManager(state_dir)
                        print("🌉 TUI Bridge started (API MODE with Prompt Caching + Extended Thinking)")
                        print("💾 TIER_1 files will be cached for maximum efficiency!")
                        thinking_label = f"{thinking_mode}" + (f" ({thinking_budget} tokens)" if thinking_budget else "")
                        print(f"🧠 Thinking mode: {thinking_label}")
                        if api_settings.get("proxy_url"):
                            print(f"🛡️ Routing via proxy: {api_settings['proxy_url']}")
                        elif base_url and "anthropic.com" not in base_url:
                            print(f"🛡️ Custom Anthropic endpoint: {base_url}")
                    except ValueError as e:
                        print(f"⚠️  {e}. Falling back to SDK mode.")
                        use_api_mode = False
                        use_sdk_mode = True
                else:
                    print("⚠️  API mode enabled but no Anthropic credentials found. Falling back to SDK mode.")
                    print("   Provide ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or configure proxy credentials in settings.")
                    use_api_mode = False
                    use_sdk_mode = True
        except Exception as e:
            print(f"⚠️  Error initializing API mode: {e}. Falling back to SDK mode.")
            use_api_mode = False
            use_sdk_mode = True

        # Initialize SDK mode (default)
        if use_sdk_mode and not use_api_mode:
            try:
                sdk_client = ClaudeSDKClient(cwd=rp_dir)
                print("🚀 TUI Bridge started (SDK MODE - High Performance)")
                print("💾 TIER_1 files will be cached for maximum efficiency!")
                print("⚡ Real-time streaming enabled!")
                thinking_label = f"{thinking_mode}" + (f" ({thinking_budget} tokens)" if thinking_budget else "")
                print(f"🧠 Thinking mode: {thinking_label}")
            except Exception as e:
                print(f"❌ Error initializing SDK: {e}")
                print("   Make sure Node.js is installed and run: npm install")
                print("   Check work_in_progress/QUICKSTART_SDK.md for setup")
                sys.exit(1)

        print(f"📁 Monitoring: {rp_dir}")
        print("⏳ Waiting for TUI to start...")

        # Wait for TUI to create the active flag (with timeout)
        tui_started = False
        parent_pid = None
        for i in range(30):  # Wait up to 15 seconds (30 * 0.5s)
            if tui_active_flag.exists():
                tui_started = True
                # Get parent (launcher) process ID for monitoring
                try:
                    import os
                    import psutil
                    parent_pid = os.getppid()
                    parent_process = psutil.Process(parent_pid)
                    print(f"✓ TUI has started (Launcher PID: {parent_pid})")
                except Exception as e:
                    print(f"✓ TUI has started (Could not get parent PID: {e})")
                    parent_pid = None
                break
            time.sleep(0.5)

        if not tui_started:
            print("❌ ERROR: TUI did not start within 15 seconds")
            print("   The tui_active.flag was not created")
            print("   Please check if the TUI is running correctly")
            sys.exit(1)

        print("💡 Bridge will auto-shutdown when TUI closes")
        print("(Or press Ctrl+C to stop manually)")
        print()
        print("🔄 Entering main monitoring loop...")

        loop_count = 0
        while True:
            loop_count += 1
            if loop_count == 1:
                print(f"✓ Main loop started (iteration {loop_count})")

            # Check if TUI is still active (check both flag and parent process)
            flag_exists = tui_active_flag.exists()
            parent_alive = True

            if parent_pid:
                try:
                    import psutil
                    parent_process = psutil.Process(parent_pid)
                    parent_alive = parent_process.is_running()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    parent_alive = False

            if loop_count <= 3:
                print(f"  Loop {loop_count}: Flag exists = {flag_exists}, Parent alive = {parent_alive}")

            # Shut down if either the flag is gone OR the parent process died
            if not flag_exists or not parent_alive:
                reason = "flag removed" if not flag_exists else "launcher process ended"
                print(f"\n📴 TUI has been closed ({reason}, detected at loop {loop_count}). Shutting down bridge...")
                normal_shutdown = True
                break

            # Check for proxy test request
            proxy_test_request_file = base_dir / "config" / "proxy_test_request.json"
            if proxy_test_request_file.exists():
                try:
                    with open(proxy_test_request_file, 'r', encoding='utf-8') as f:
                        test_request = json.load(f)

                    proxy_url = test_request.get("proxy_url")
                    proxy_token = test_request.get("proxy_token")

                    print(f"🧪 Testing proxy connection to {proxy_url}")
                    test_results = test_proxy_connection(proxy_url, proxy_token)

                    # Write results
                    proxy_test_results_file = base_dir / "config" / "proxy_test_results.json"
                    with open(proxy_test_results_file, 'w', encoding='utf-8') as f:
                        json.dump(test_results, f, indent=2)

                    print(f"✅ Proxy test complete. Results saved.")
                    print(json.dumps(test_results, indent=2))

                    # Clean up request file
                    proxy_test_request_file.unlink(missing_ok=True)
                except Exception as e:
                    print(f"❌ Error testing proxy: {e}")
                    proxy_test_request_file.unlink(missing_ok=True)

                time.sleep(0.5)
                continue

            # Check for ready flag (handle both .json and .txt input files)
            input_file_txt = state_dir / "rp_client_input.txt"
            if ready_flag.exists() and (input_file.exists() or input_file_txt.exists()):
                print("📨 Received input from TUI")

                # Read user message (JSON format with .txt fallback)
                try:
                    message = file_manager.read_ipc_input(state_dir).strip()
                    print(f"📝 Message: {message[:50]}..." if len(message) > 50 else f"📝 Message: {message}")
                except Exception as e:
                    print(f"❌ Error reading input: {e}")
                    ready_flag.unlink(missing_ok=True)
                    continue

                # Check for /new command first
                session_flag = state_dir / "claude_session_active.flag"
                if message.strip().lower() == "/new":
                    # Start fresh conversation
                    if session_flag.exists():
                        session_flag.unlink()
                        print("🔄 Session reset - next message will start fresh conversation")
                    if use_api_mode and conversation_manager:
                        conversation_manager.clear_history()
                        print("🗑️  Conversation history cleared (API)")
                    if use_sdk_mode and sdk_client:
                        sdk_client.clear_session()
                        print("🗑️  Conversation history cleared (SDK)")

                    # Clear agent cache
                    try:
                        from src.automation.agent_coordinator import AgentCoordinator
                        agent_cache_file = state_dir / "agent_analysis.md"
                        coordinator = AgentCoordinator(rp_dir, state_dir / "hook.log")
                        coordinator.clear_cache(agent_cache_file)
                        print("🗑️  Agent cache cleared")
                    except Exception as e:
                        print(f"⚠️  Failed to clear agent cache: {e}")

                    response = "Session reset. Your next message will start a new conversation."
                    # Write response and continue to next message
                    try:
                        file_manager.write_ipc_response(response, state_dir=state_dir)
                        done_flag.touch()
                        print("📤 Response sent to TUI")
                        print()
                        print("⏳ Waiting for next input...")
                    except Exception as e:
                        print(f"❌ Error writing response: {e}")
                    ready_flag.unlink(missing_ok=True)
                    continue

                # ============================================================================
                # SESSION MANAGEMENT COMMANDS
                # ============================================================================

                # Get session manager from module manager
                session_manager_module = module_manager.get('session_manager')

                if not session_manager_module:
                    response = "❌ Error: Session manager module not initialized"
                    file_manager.write_json(response_file, {"response": response})
                    file_manager.write_flag(done_flag)
                    continue

                # Helper function for parsing tags
                def parse_command_with_tags(command: str):
                    """Parse command and extract hashtags."""
                    tags = []
                    parts = command.split()
                    clean_parts = []

                    for part in parts:
                        if part.startswith("#"):
                            tags.append(part[1:])
                        else:
                            clean_parts.append(part)

                    return " ".join(clean_parts), tags

                # Helper function for parsing branch command
                def parse_branch_command(command: str):
                    """Parse branch command to extract response num, name, and tags."""
                    clean_command, tags = parse_command_with_tags(command)
                    args = clean_command.replace("/branch", "").strip()
                    parts = args.split(maxsplit=1)

                    if len(parts) == 2 and parts[0].isdigit():
                        return int(parts[0]), parts[1].strip('"\''), tags
                    else:
                        return None, args.strip('"\''), tags

                # Parse command and tags
                message_clean, tags = parse_command_with_tags(message.strip())
                command_lower = message_clean.lower()

                # --- /retry command ---
                if command_lower == "/retry":
                    try:
                        # Perform retry
                        archive_path = session_manager_module.retry(tags=tags if tags else None)

                        response = f"""✅ Retry successful!

Last response removed and archived to:
{archive_path.name}

{f'Tags: {", ".join(tags)}' if tags else ''}

You can now send your message again to get a new response."""

                        log_to_file(log_file, f"[RETRY] Archived to {archive_path}")

                    except ValueError as e:
                        response = f"❌ Retry failed: {str(e)}"
                        log_to_file(log_file, f"[ERROR] Retry failed: {e}")

                    file_manager.write_ipc_response(response, state_dir=state_dir)
                    done_flag.touch()
                    print("📤 Response sent to TUI")
                    print()
                    ready_flag.unlink(missing_ok=True)
                    continue

                # --- /branch command ---
                if command_lower.startswith("/branch"):
                    try:
                        # Parse branch command
                        response_num, branch_name, branch_tags = parse_branch_command(message)

                        # Create branch
                        branch_path = session_manager_module.branch(
                            branch_name=branch_name,
                            response_num=response_num,
                            tags=branch_tags if branch_tags else None
                        )

                        response = f"""✅ Branch created!

Name: {branch_name}
Branched from: Response {response_num or 'current'}
Location: {branch_path.name}
{f'Tags: {", ".join(branch_tags)}' if branch_tags else ''}

You can /switch "{branch_name}" to work on this branch, or continue here."""

                        log_to_file(log_file, f"[BRANCH] Created {branch_name}")

                    except ValueError as e:
                        response = f"❌ Branch failed: {str(e)}"
                        log_to_file(log_file, f"[ERROR] Branch failed: {e}")

                    file_manager.write_ipc_response(response, state_dir=state_dir)
                    done_flag.touch()
                    print("📤 Response sent to TUI")
                    print()
                    ready_flag.unlink(missing_ok=True)
                    continue

                # --- /checkpoint command ---
                if command_lower.startswith("/checkpoint"):
                    try:
                        # Extract checkpoint name
                        checkpoint_name = message_clean.replace("/checkpoint", "").strip().strip('"\'')

                        if not checkpoint_name:
                            raise ValueError("Checkpoint name required")

                        # Create checkpoint
                        checkpoint_path = session_manager_module.checkpoint(
                            checkpoint_name=checkpoint_name,
                            tags=tags if tags else None
                        )

                        response = f"""✅ Checkpoint saved!

Name: {checkpoint_name}
Location: {checkpoint_path.name}
{f'Tags: {", ".join(tags)}' if tags else ''}"""

                        log_to_file(log_file, f"[CHECKPOINT] Created {checkpoint_name}")

                    except ValueError as e:
                        response = f"❌ Checkpoint failed: {str(e)}"
                        log_to_file(log_file, f"[ERROR] Checkpoint failed: {e}")

                    file_manager.write_ipc_response(response, state_dir=state_dir)
                    done_flag.touch()
                    print("📤 Response sent to TUI")
                    print()
                    ready_flag.unlink(missing_ok=True)
                    continue

                # --- /switch command ---
                if command_lower.startswith("/switch"):
                    try:
                        # Extract session name
                        session_name = message_clean.replace("/switch", "").strip().strip('"\'')

                        if not session_name:
                            raise ValueError("Session name required")

                        # Switch session
                        new_active_path = session_manager_module.switch(session_name)

                        response = f"""✅ Switched to: {session_name}

TUI will need to reload to show this session's history.

Type /sessions to see all available sessions."""

                        log_to_file(log_file, f"[SWITCH] Switched to {session_name}")

                        # TODO: Signal TUI to reload session
                        # (TUI needs to re-read session_main.json)

                    except FileNotFoundError as e:
                        response = f"❌ Switch failed: {str(e)}"
                        log_to_file(log_file, f"[ERROR] Switch failed: {e}")
                    except Exception as e:
                        response = f"❌ Switch failed: {str(e)}"
                        log_to_file(log_file, f"[ERROR] Switch failed: {e}")

                    file_manager.write_ipc_response(response, state_dir=state_dir)
                    done_flag.touch()
                    print("📤 Response sent to TUI")
                    print()
                    ready_flag.unlink(missing_ok=True)
                    continue

                # --- /sessions command ---
                if command_lower.startswith("/sessions"):
                    try:
                        # Parse tag filter
                        tag_filter = None
                        if "tag:" in command_lower:
                            tag_filter = command_lower.split("tag:")[1].strip()

                        # List sessions
                        sessions = session_manager_module.list_sessions(tag_filter=tag_filter)

                        # Format response
                        lines = ["📁 Available Sessions:\n"]

                        # Active session
                        active_sessions = [s for s in sessions if s["type"] == "active"]
                        if active_sessions:
                            s = active_sessions[0]
                            lines.append(f"  ● {s['name']} (Response {s['response_count']}) [ACTIVE]")
                            if s['tags']:
                                lines.append(f"    └─ Tags: {', '.join(s['tags'])}")
                            lines.append("")

                        # Branches
                        branches = [s for s in sessions if s["type"] == "branch"]
                        if branches:
                            lines.append("  Branches:")
                            for s in branches:
                                lines.append(f"    {s['name']} (Response {s['response_count']})")
                                if s['tags']:
                                    lines.append(f"    └─ Tags: {', '.join(s['tags'])}")
                                if s['description']:
                                    lines.append(f"    └─ \"{s['description']}\"")
                            lines.append("")

                        # Archived
                        archived = [s for s in sessions if s["type"] in ["archived", "checkpoint"]]
                        if archived:
                            lines.append("  Archived:")
                            for s in archived[:10]:  # Limit to 10 most recent
                                lines.append(f"    {s['name']} (Response {s['response_count']})")
                                if s['tags']:
                                    lines.append(f"    └─ Tags: {', '.join(s['tags'])}")
                            if len(archived) > 10:
                                lines.append(f"    ... and {len(archived)-10} more")

                        response = "\n".join(lines)

                    except Exception as e:
                        response = f"❌ List failed: {str(e)}"
                        log_to_file(log_file, f"[ERROR] List failed: {e}")

                    file_manager.write_ipc_response(response, state_dir=state_dir)
                    done_flag.touch()
                    print("📤 Response sent to TUI")
                    print()
                    ready_flag.unlink(missing_ok=True)
                    continue

                # ===== API MODE =====
                if use_api_mode and api_client:
                    print("⚙️ Running automation (API Mode with Caching)...")
                    try:
                        # Use orchestrator module (V2)
                        cached_context, dynamic_prompt, loaded_entities, profiler = orchestrator.run_automation_with_caching(message)
                        if loaded_entities:
                            print(f"📚 TIER_3 entities loaded: {', '.join(loaded_entities)}")
                        print(f"✅ Automation complete - TIER_1 will be cached!")

                        # Display profiling information
                        if profiler:
                            print(profiler.report("⚡ Automation Performance"))
                    except Exception as e:
                        print(f"⚠️ Automation error: {e}")
                        import traceback
                        traceback.print_exc()
                        cached_context = ""
                        dynamic_prompt = message

                    print("🤖 Sending to Claude API...")
                    print(f"🧠 Thinking mode: {thinking_mode}" + (f" ({thinking_budget} tokens)" if thinking_budget else ""))
                    try:
                        result = api_client.send_message(
                            user_message=dynamic_prompt,
                            cached_context=cached_context if cached_context else None,
                            conversation_history=conversation_manager.get_history(),
                            max_tokens=8192,
                            thinking_mode=thinking_mode,
                            thinking_budget=thinking_budget
                        )

                        response = result["content"]
                        print("✓ Response received")

                        # Add to conversation history
                        conversation_manager.add_user_message(dynamic_prompt)
                        conversation_manager.add_assistant_message(response)

                        # Print cache stats
                        print(api_client.format_cache_stats(result["usage"]))

                        # Queue background agents (non-blocking, runs while user types next message)
                        try:
                            from src.automation.background_tasks import get_task_queue
                            task_queue = get_task_queue()

                            # Get response counter for response number
                            counter_file = rp_dir / "state" / "response_counter.json"
                            response_number = get_response_count(counter_file)

                            # Queue background analysis (V2 simplified interface)
                            task_queue.queue_task(
                                orchestrator.run_background_agents,
                                response,
                                task_id=f"background_agents_{response_number}"
                            )
                            print("🔄 Background agents queued (V2)")
                        except Exception as e:
                            print(f"⚠️ Failed to queue background agents: {e}")

                        # Create session flag after successful response
                        if not session_flag.exists():
                            session_flag.touch()
                            print("📝 Session flag created")

                    except Exception as e:
                        response = f"Error calling Claude API: {e}"
                        print(f"❌ {response}")
                        import traceback
                        traceback.print_exc()

                # ===== SDK MODE (default) =====
                elif use_sdk_mode and sdk_client:
                    print("⚙️ Running automation (SDK Mode with Caching)...")
                    try:
                        # Use orchestrator module (V2)
                        cached_context, dynamic_prompt, loaded_entities, profiler = orchestrator.run_automation_with_caching(message)
                        if loaded_entities:
                            print(f"📚 TIER_3 entities loaded: {', '.join(loaded_entities)}")
                        print(f"✅ Automation complete - TIER_1 will be cached!")

                        # Display profiling information
                        if profiler:
                            print(profiler.report("⚡ Automation Performance"))
                    except Exception as e:
                        print(f"⚠️ Automation error: {e}")
                        import traceback
                        traceback.print_exc()
                        cached_context = ""
                        dynamic_prompt = message

                    # Call Claude Code SDK
                    print("🚀 Sending to Claude Code SDK...")
                    print(f"🧠 Thinking mode: {thinking_mode}" + (f" ({thinking_budget} tokens)" if thinking_budget else ""))
                    try:
                        response = ""
                        # Stream the response
                        for chunk in sdk_client.query(
                            message=dynamic_prompt,
                            cached_context=cached_context if cached_context else None,
                            thinking_mode=thinking_mode,
                            thinking_budget=thinking_budget
                        ):
                            response += chunk
                            # Could optionally stream to TUI here in the future

                        print("✓ Response received")

                        # Get and display cache stats
                        stats = sdk_client.get_cache_stats()
                        if stats:
                            print(stats)

                        # Get metadata
                        metadata = sdk_client.get_metadata()
                        if metadata and metadata.session_id:
                            print(f"📝 Session: {metadata.session_id[:8]}...")

                        # Queue background agents (non-blocking, runs while user types next message)
                        try:
                            from src.automation.background_tasks import get_task_queue
                            task_queue = get_task_queue()

                            # Get response counter for response number
                            counter_file = rp_dir / "state" / "response_counter.json"
                            response_number = get_response_count(counter_file)

                            # Queue background analysis (V2 simplified interface)
                            task_queue.queue_task(
                                orchestrator.run_background_agents,
                                response,
                                task_id=f"background_agents_{response_number}"
                            )
                            print("🔄 Background agents queued (V2)")
                        except Exception as e:
                            print(f"⚠️ Failed to queue background agents: {e}")

                        # Create session flag after successful response
                        if not session_flag.exists():
                            session_flag.touch()
                            print("📝 Session flag created")

                    except Exception as e:
                        response = f"Error calling Claude Code SDK: {e}"
                        print(f"❌ {response}")
                        import traceback
                        traceback.print_exc()

                # Write response (JSON format with metadata)
                try:
                    # Try to extract model name and cache stats if available
                    model_name = None
                    cache_stats = None

                    # Get model from sdk_client if available
                    if 'sdk_client' in locals() and sdk_client:
                        try:
                            metadata = sdk_client.get_metadata()
                            if metadata:
                                model_name = getattr(metadata, 'model', None)
                        except:
                            pass

                    file_manager.write_ipc_response(response, model=model_name, cache_stats=cache_stats, state_dir=state_dir)
                    done_flag.touch()
                    print("📤 Response sent to TUI")
                    print()
                    print("⏳ Waiting for next input...")
                except Exception as e:
                    print(f"❌ Error writing response: {e}")

                # Clean up ready flag
                ready_flag.unlink(missing_ok=True)

            # Sleep briefly
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n👋 Bridge stopped manually")
        normal_shutdown = True

    except Exception as e:
        print(f"\n\n❌ Bridge crashed with error: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Bridge will now exit due to error")
        # Don't set normal_shutdown - we want to see the error

    finally:
        # Shutdown module manager first
        if 'module_manager' in locals() and module_manager:
            print("📦 Shutting down modules...")
            try:
                module_manager.shutdown_all()
                print("✓ All modules shut down")
            except Exception as e:
                print(f"⚠️  Warning: Error shutting down modules: {e}")

        # Shutdown background task queue (stop accepting new tasks)
        print("🛑 Shutting down background tasks...")
        try:
            shutdown_task_queue()
            print("✓ Background tasks stopped")
        except Exception as e:
            print(f"⚠️  Warning: Error shutting down task queue: {e}")

        # Flush pending writes before shutdown
        print("💾 Flushing pending writes...")
        try:
            flush_all_writes()
            print("✓ All writes complete")
        except Exception as e:
            print(f"⚠️  Warning: Error flushing writes: {e}")

        # Clean up SDK client - be aggressive
        if 'sdk_client' in locals() and sdk_client:
            try:
                print("🔒 Closing SDK client...")
                sdk_client.close()
                print("✓ SDK client closed")
            except Exception as e:
                print(f"⚠️  Warning: Error closing SDK client: {e}")
                # Force kill if close fails
                try:
                    if sdk_client.process:
                        sdk_client.process.kill()
                        print("✓ SDK process forcefully terminated")
                except:
                    pass

        # Clean up flags (only if they were initialized)
        try:
            if ready_flag:
                ready_flag.unlink(missing_ok=True)
            if done_flag:
                done_flag.unlink(missing_ok=True)
            if tui_active_flag:
                tui_active_flag.unlink(missing_ok=True)
            print("✓ Flags cleaned up")
        except Exception as e:
            print(f"⚠️  Warning: Error cleaning flags: {e}")

        print("✓ Bridge shutdown complete")

        # Only force exit on normal shutdown (not errors)
        if normal_shutdown:
            print("👋 Exiting now...")
            sys.exit(0)
        else:
            print("⚠️  Bridge stopped due to error (see above)")
            input("\nPress Enter to close this window...")


if __name__ == "__main__":
    main()
