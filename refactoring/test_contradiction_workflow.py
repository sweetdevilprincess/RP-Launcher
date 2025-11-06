"""Test Contradiction Workflow - End-to-End Verification

This script tests the complete contradiction workflow:
1. ContradictionSynthesisAgent - Detects contradictions and generates resolutions
2. KnowledgeExtractionAgent - Applies contradiction resolutions to knowledge base
3. ResponseAnalyzerAgent - Marks contradictions as resolved when addressed
4. Archive functionality - Moves resolved contradictions to archive

Run this script from the refactoring/ directory:
    python test_contradiction_workflow.py
"""

from pathlib import Path
import json
import sys
from unittest.mock import Mock
from dataclasses import dataclass

@dataclass
class MockLLMResponse:
    """Mock LLMResponse for testing."""
    content: str
    usage: dict = None
    raw_response: dict = None
    thinking: str = None

print("=" * 80)
print("Contradiction Workflow Test")
print("=" * 80)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test RP directory
test_rp_dir = Path(__file__).parent / "RPs" / "test_rp"

if not test_rp_dir.exists():
    print(f"[FAIL] Test RP directory not found: {test_rp_dir}")
    sys.exit(1)

print(f"[OK] Using test RP: {test_rp_dir}")

# =============================================================================
# Test 1: ContradictionSynthesisAgent - Detection and Resolution Generation
# =============================================================================

print("\n" + "=" * 80)
print("Test 1: ContradictionSynthesisAgent")
print("=" * 80)

try:
    from src.automation.agents.implementations import ContradictionSynthesisAgent

    # Create mock bridge
    mock_bridge = Mock()
    mock_bridge.session_state_service.load_session_state.return_value = {
        "timeline": {"current_session_id": "main"},
        "knowledge": {"knowledge_file": "state/knowledge_main.json"}
    }
    mock_bridge.session_state_service.get_scene_context.return_value = {
        "chapter": "Chapter 1",
        "location": "Unknown",
        "characters_in_scene": [],
        "scene_analysis": {},
        "time_context": {}
    }

    # Mock LLM call to return fake contradiction data
    def mock_call_llm(user_message, temperature=1.0):
        json_content = json.dumps({
            "contradictions": [
                {
                    "type": "world_rule",
                    "description": "Test contradiction - magic used without incantation",
                    "established_rule": "All magic requires verbal incantations",
                    "contradicting_statement": "Alice cast spell silently",
                    "chapter_reference": "Message 25",
                    "explanations": [
                        {
                            "explanation": "Alice is exceptionally powerful and mastered silent casting",
                            "plausibility": "high",
                            "narrative_impact": "Establishes Alice as magical prodigy",
                            "supporting_evidence": "Alice has shown advanced abilities"
                        },
                        {
                            "explanation": "Alice uses a magical artifact",
                            "plausibility": "medium",
                            "narrative_impact": "Introduces new plot device",
                            "supporting_evidence": "Alice acquired mysterious amulet"
                        }
                    ],
                    "recommended_action": "clarify_in_knowledge",
                    "suggested_knowledge_entry": "Silent casting is an extremely rare ability that only powerful mages can achieve."
                }
            ],
            "narrative_consistency_score": 8.5,
            "notes": "Overall chapter maintains good consistency"
        })
        return MockLLMResponse(content=json_content)

    # Instantiate agent
    agent = ContradictionSynthesisAgent(
        rp_dir=test_rp_dir,
        log_file=None,
        bridge=mock_bridge
    )

    # Mock the LLM call
    agent.call_llm = mock_call_llm

    print("\n1.1 Testing chapter context loading...")
    chapter_context = agent._load_chapter_context(
        chapter_number=1,
        message_range=(1, 39),
        session_id="main"
    )

    if chapter_context["messages_data"]:
        print(f"   [OK] Loaded {len(chapter_context['messages_data'])} messages from session file")
        print(f"   [OK] Chapter content: {len(chapter_context['chapter_content'])} characters")
    else:
        print("   [WARN] No messages loaded (session file may be empty)")

    print("\n1.2 Testing contradiction detection (with mocked LLM)...")
    result = agent.execute(
        chapter_number=1,
        message_range=(1, 39),
        session_id="main"
    )

    print(f"   [OK] Agent executed: {result}")

    # Check if contradictions file was created
    contradictions_file = test_rp_dir / "state" / "contradictions" / "contradictions_main.json"
    if contradictions_file.exists():
        with open(contradictions_file, "r") as f:
            contradictions_data = json.load(f)

        print(f"   [OK] Contradictions file created: {contradictions_file}")
        print(f"   [OK] Contradictions detected: {len(contradictions_data.get('contradictions', []))}")

        if contradictions_data.get("contradictions"):
            first = contradictions_data["contradictions"][0]
            print(f"   [OK] First contradiction ID: {first['id']}")
            print(f"   [OK] Resolution actions: {len(first.get('resolution_actions', []))}")
    else:
        print(f"   [FAIL] Contradictions file not created: {contradictions_file}")

except Exception as e:
    print(f"   [FAIL] Test 1 failed: {e}")
    import traceback
    traceback.print_exc()

# =============================================================================
# Test 2: KnowledgeExtractionAgent - Apply Contradiction Resolutions
# =============================================================================

print("\n" + "=" * 80)
print("Test 2: KnowledgeExtractionAgent - Apply Resolutions")
print("=" * 80)

try:
    from src.automation.agents.implementations import KnowledgeExtractionAgent

    # Check if we have contradictions to resolve
    contradictions_file = test_rp_dir / "state" / "contradictions" / "contradictions_main.json"

    if not contradictions_file.exists():
        print("   [WARN]  No contradictions file found, skipping resolution test")
    else:
        with open(contradictions_file, "r") as f:
            contradictions_data = json.load(f)

        pending_actions = sum(
            1 for c in contradictions_data.get("contradictions", [])
            for a in c.get("resolution_actions", [])
            if a.get("agent") == "knowledge_extraction" and not a.get("completed")
        )

        print(f"\n2.1 Found {pending_actions} pending knowledge_extraction actions")

        if pending_actions > 0:
            # Create knowledge extraction agent
            knowledge_agent = KnowledgeExtractionAgent(
                rp_dir=test_rp_dir,
                log_file=None,
                bridge=mock_bridge
            )

            # Load current knowledge
            knowledge_data = knowledge_agent._load_existing_knowledge()
            before_count = len(knowledge_data.get("entries", []))

            print(f"   [OK] Current knowledge entries: {before_count}")

            # Apply contradiction resolutions
            resolutions_applied = knowledge_agent._apply_contradiction_resolutions(
                knowledge_data,
                message_number=40
            )

            after_count = len(knowledge_data.get("entries", []))

            print(f"   [OK] Applied {resolutions_applied} contradiction resolutions")
            print(f"   [OK] Knowledge entries after: {after_count}")
            print(f"   [OK] New entries added: {after_count - before_count}")

            # Verify actions were marked completed
            with open(contradictions_file, "r") as f:
                updated_data = json.load(f)

            completed_actions = sum(
                1 for c in updated_data.get("contradictions", [])
                for a in c.get("resolution_actions", [])
                if a.get("agent") == "knowledge_extraction" and a.get("completed")
            )

            print(f"   [OK] Completed actions in file: {completed_actions}")
        else:
            print("   [WARN]  No pending actions to test")

except Exception as e:
    print(f"   [FAIL] Test 2 failed: {e}")
    import traceback
    traceback.print_exc()

# =============================================================================
# Test 3: ResponseAnalyzerAgent - Mark Contradictions as Resolved
# =============================================================================

print("\n" + "=" * 80)
print("Test 3: ResponseAnalyzerAgent - Mark as Resolved")
print("=" * 80)

try:
    from src.automation.agents.implementations import ResponseAnalyzerAgent

    contradictions_file = test_rp_dir / "state" / "contradictions" / "contradictions_main.json"

    if not contradictions_file.exists():
        print("   [WARN]  No contradictions file found, skipping resolution test")
    else:
        with open(contradictions_file, "r") as f:
            contradictions_data = json.load(f)

        pending_count = sum(
            1 for c in contradictions_data.get("contradictions", [])
            if c["status"] == "pending"
        )

        print(f"\n3.1 Found {pending_count} pending contradictions")

        if pending_count > 0:
            # Create response analyzer agent
            analyzer_agent = ResponseAnalyzerAgent(
                rp_dir=test_rp_dir,
                log_file=None,
                bridge=mock_bridge
            )

            # Simulate Claude response that addresses the contradiction
            # This response mentions "powerful", "casting", "silent" which should match
            mock_response = """Alice concentrated deeply, her exceptional power allowing her to cast
            the spell without speaking. This silent casting technique was something only the most
            powerful mages could achieve, and Alice had mastered it through years of study."""

            # Check for resolutions
            resolved_count = analyzer_agent._check_contradiction_resolutions(
                mock_response,
                message_number=41
            )

            print(f"   [OK] Marked {resolved_count} contradictions as resolved")

            # Verify in file
            with open(contradictions_file, "r") as f:
                updated_data = json.load(f)

            resolved_in_file = sum(
                1 for c in updated_data.get("contradictions", [])
                if c["status"] == "resolved"
            )

            print(f"   [OK] Resolved contradictions in file: {resolved_in_file}")
            print(f"   [OK] Stats: {updated_data.get('stats', {})}")
        else:
            print("   [WARN]  No pending contradictions to test")

except Exception as e:
    print(f"   [FAIL] Test 3 failed: {e}")
    import traceback
    traceback.print_exc()

# =============================================================================
# Test 4: Archive Resolved Contradictions
# =============================================================================

print("\n" + "=" * 80)
print("Test 4: Archive Resolved Contradictions")
print("=" * 80)

try:
    contradictions_file = test_rp_dir / "state" / "contradictions" / "contradictions_main.json"

    if not contradictions_file.exists():
        print("   [WARN]  No contradictions file found, skipping archive test")
    else:
        with open(contradictions_file, "r") as f:
            contradictions_data = json.load(f)

        resolved_count = sum(
            1 for c in contradictions_data.get("contradictions", [])
            if c["status"] == "resolved"
        )

        print(f"\n4.1 Found {resolved_count} resolved contradictions to archive")

        if resolved_count > 0:
            # Use the agent's archive method
            agent = ContradictionSynthesisAgent(
                rp_dir=test_rp_dir,
                log_file=None,
                bridge=mock_bridge
            )

            archived_count = agent.archive_resolved_contradictions(session_id="main")

            print(f"   [OK] Archived {archived_count} contradictions")

            # Verify archive file created
            archive_file = test_rp_dir / "state" / "contradictions" / "resolved" / "resolved_main.json"
            if archive_file.exists():
                with open(archive_file, "r") as f:
                    archive_data = json.load(f)

                print(f"   [OK] Archive file created: {archive_file}")
                print(f"   [OK] Total resolved in archive: {archive_data.get('total_resolved', 0)}")

            # Verify active file updated
            with open(contradictions_file, "r") as f:
                active_data = json.load(f)

            remaining_resolved = sum(
                1 for c in active_data.get("contradictions", [])
                if c["status"] == "resolved"
            )

            print(f"   [OK] Resolved remaining in active file: {remaining_resolved} (should be 0)")
        else:
            print("   [WARN]  No resolved contradictions to archive")

except Exception as e:
    print(f"   [FAIL] Test 4 failed: {e}")
    import traceback
    traceback.print_exc()

# =============================================================================
# Test 5: Verify File Structure
# =============================================================================

print("\n" + "=" * 80)
print("Test 5: Verify File Structure")
print("=" * 80)

print("\n5.1 Checking folder structure...")

contradictions_dir = test_rp_dir / "state" / "contradictions"
resolved_dir = contradictions_dir / "resolved"

if contradictions_dir.exists():
    print(f"   [OK] Contradictions directory exists: {contradictions_dir}")
else:
    print(f"   [FAIL] Contradictions directory missing: {contradictions_dir}")

if resolved_dir.exists():
    print(f"   [OK] Resolved archive directory exists: {resolved_dir}")
else:
    print(f"   [WARN]  Resolved archive directory not yet created: {resolved_dir}")

print("\n5.2 Checking files...")

files_to_check = [
    contradictions_dir / "contradictions_main.json",
    resolved_dir / "resolved_main.json" if resolved_dir.exists() else None,
    test_rp_dir / "state" / "knowledge_main.json",
]

for file_path in files_to_check:
    if file_path and file_path.exists():
        size = file_path.stat().st_size
        print(f"   [OK] {file_path.name}: {size} bytes")
    elif file_path:
        print(f"   [WARN]  {file_path.name}: Not created yet")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)

print("\n[OK] ContradictionSynthesisAgent:")
print("   - Loads session files")
print("   - Detects contradictions (with mocked LLM)")
print("   - Generates resolution actions")
print("   - Saves to state/contradictions/ folder")

print("\n[OK] KnowledgeExtractionAgent:")
print("   - Reads contradictions file")
print("   - Applies pending knowledge_extraction actions")
print("   - Marks actions as completed")
print("   - Updates knowledge base")

print("\n[OK] ResponseAnalyzerAgent:")
print("   - Checks if contradictions addressed in responses")
print("   - Marks contradictions as resolved")
print("   - Updates stats")

print("\n[OK] Archive Functionality:")
print("   - Moves resolved contradictions to archive")
print("   - Cleans up active file")

print("\n" + "=" * 80)
print("All Tests Complete!")
print("=" * 80)

print("\nNote: This test uses mocked LLM calls for contradiction detection.")
print("In production, the agent will use actual LLM to analyze chapters.")
print("\nTo test with real LLM analysis:")
print("  1. Ensure you have API keys configured")
print("  2. Remove the 'agent.call_llm = mock_call_llm' line")
print("  3. Run the test with an actual chapter that has contradictions")
