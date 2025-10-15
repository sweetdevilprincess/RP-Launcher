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

from src.clients.claude_api import ClaudeAPIClient, ConversationManager, load_api_key
from src.clients.claude_sdk import ClaudeSDKClient
from src.fs_write_queue import flush_all_writes

# Import modular automation system
from src.automation import run_automation_with_caching
from src.automation.file_loading import load_proxy_prompt
from src.automation.core import get_response_count
from src.automation.orchestrator import AutomationOrchestrator
from src.file_manager import FileManager


# =============================================================================
# MAIN BRIDGE LOOP
# =============================================================================

def main():
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

    # Create FileManager for IPC operations
    file_manager = FileManager(rp_dir)

    # Initialize orchestrator for background agent tasks
    orchestrator = AutomationOrchestrator(rp_dir)
    print("🎭 Automation orchestrator initialized")

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
            api_key = load_api_key()
            if api_key:
                api_client = ClaudeAPIClient(api_key)
                conversation_manager = ConversationManager(state_dir)
                print("🌉 TUI Bridge started (API MODE with Prompt Caching + Extended Thinking)")
                print("💾 TIER_1 files will be cached for maximum efficiency!")
                thinking_label = f"{thinking_mode}" + (f" ({thinking_budget} tokens)" if thinking_budget else "")
                print(f"🧠 Thinking mode: {thinking_label}")
            else:
                print("⚠️  API mode enabled but no API key found. Falling back to SDK mode.")
                print("   Set ANTHROPIC_API_KEY environment variable or add to config.json")
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
    print("⏳ Waiting for TUI input...")
    print("💡 Bridge will auto-shutdown when TUI closes")
    print("(Or press Ctrl+C to stop manually)")
    print()

    try:
        while True:
            # Check if TUI is still active
            if not tui_active_flag.exists():
                print("\n📴 TUI has been closed. Shutting down bridge...")
                break

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

                # ===== API MODE =====
                if use_api_mode and api_client:
                    print("⚙️ Running automation (API Mode with Caching)...")
                    try:
                        # Use modular automation system
                        cached_context, dynamic_prompt, loaded_entities, profiler = run_automation_with_caching(message, rp_dir)
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

                    # Apply proxy prompt if enabled
                    if config.get("use_proxy", False):
                        proxy_prompt = load_proxy_prompt(base_dir)
                        if proxy_prompt:
                            print("🔀 Proxy mode active - injecting custom prompt")
                            dynamic_prompt = f"{proxy_prompt}\n\n---\n\n{dynamic_prompt}"

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

                            # Queue background analysis
                            task_queue.queue_task(
                                orchestrator.run_background_agents,
                                response,
                                response_number,
                                loaded_entities if 'loaded_entities' in locals() else None,
                                task_id=f"background_agents_{response_number}"
                            )
                            print("🔄 Background agents queued")
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
                        # Use modular automation system
                        cached_context, dynamic_prompt, loaded_entities, profiler = run_automation_with_caching(message, rp_dir)
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

                    # Apply proxy prompt if enabled
                    if config.get("use_proxy", False):
                        proxy_prompt = load_proxy_prompt(base_dir)
                        if proxy_prompt:
                            print("🔀 Proxy mode active - injecting custom prompt")
                            dynamic_prompt = f"{proxy_prompt}\n\n---\n\n{dynamic_prompt}"

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

                            # Queue background analysis
                            task_queue.queue_task(
                                orchestrator.run_background_agents,
                                response,
                                response_number,
                                loaded_entities if 'loaded_entities' in locals() else None,
                                task_id=f"background_agents_{response_number}"
                            )
                            print("🔄 Background agents queued")
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

    finally:
        # Flush pending writes before shutdown
        print("💾 Flushing pending writes...")
        flush_all_writes()
        print("✓ All writes complete")

        # Clean up SDK client
        if 'sdk_client' in locals() and sdk_client:
            try:
                sdk_client.close()
                print("🔒 SDK client closed")
            except:
                pass

        # Clean up flags
        ready_flag.unlink(missing_ok=True)
        done_flag.unlink(missing_ok=True)
        print("✓ Bridge shutdown complete")


if __name__ == "__main__":
    main()
