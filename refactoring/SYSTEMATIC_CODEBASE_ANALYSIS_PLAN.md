# SYSTEMATIC CODEBASE ANALYSIS PLAN

**Project:** RP Launcher Refactored (C:\Users\green\Desktop\RP Claude Code\refactoring)
**Objective:** Identify dead code, redundant code, outdated patterns, and architectural issues WITHOUT missing anything
**Method:** Execution-flow tracing + comprehensive file-by-file reading + cross-verification
**Estimated Time:** 8-12 hours of focused analysis

---

## CRITICAL LESSONS FROM PREVIOUS ANALYSIS

### What Went Wrong Before:
1. **Pattern matching failed** - Searching for usage patterns missed actual usage
2. **Grep searches missed context** - Found imports but not actual calls
3. **Assumptions without verification** - Assumed code was unused without checking thoroughly
4. **Missed working systems** - Claude SDK, call_llm(), branching all flagged incorrectly

### What We'll Do Differently:
1. **Trace execution flows** - Start from entry points, follow what actually runs
2. **Read every file completely** - Not just search, but READ and understand
3. **Verify each finding 3 ways** - grep, file reading, cross-reference
4. **Build call graphs** - Document what calls what
5. **Test our findings** - Check if tests use "unused" code
6. **Question everything** - If something looks unused, verify 3 times

---

## PHASE 1: EXECUTION FLOW MAPPING (2-3 hours)

### Objective
Build a complete map of what code **actually executes** at runtime by tracing from entry points.

### 1.1: Entry Point Analysis

**Step 1: Read and trace `launch.py`**

```bash
# Read the main entry point
Read: C:\Users\green\Desktop\RP Claude Code\refactoring\launch.py
```

**Document:**
- What imports does it make? (List every import)
- What functions does it call in `main()`?
- What processes does it spawn?
- What classes does it instantiate?

**Create artifact:** `EXECUTION_FLOW_1_LAUNCH.md`

```markdown
# Launch.py Execution Flow

## Imports
- [List every import with line number]

## Main Function Flow
1. [Step 1 with line numbers]
2. [Step 2 with line numbers]
...

## Objects Instantiated
- BridgeService (line X) -> go to 1.2
- RPClientApp (line Y) -> go to 1.3
- [etc.]

## Files Loaded/Created
- [List all files it reads or creates]
```

---

**Step 2: Read and trace `start_bridge.py`**

```bash
Read: C:\Users\green\Desktop\RP Claude Code\refactoring\start_bridge.py
```

**Document:** Same format as Step 1

**Create artifact:** `EXECUTION_FLOW_1_START_BRIDGE.md`

---

**Step 3: Read and trace `start_tui.py`**

```bash
Read: C:\Users\green\Desktop\RP Claude Code\refactoring\start_tui.py
```

**Document:** Same format as Step 1

**Create artifact:** `EXECUTION_FLOW_1_START_TUI.md`

---

**Step 4: Check for other entry points**

```bash
# Look for other potential entry points
Glob: *.py (in root directory only)
Grep: "if __name__ == '__main__':" across all root .py files
```

**Document any additional entry points found**

---

### 1.2: BridgeService Initialization Trace

**Step 1: Read BridgeService completely**

```bash
Read: C:\Users\green\Desktop\RP Claude Code\refactoring\src\presentation\bridge\bridge_service.py
```

**Document in `EXECUTION_FLOW_2_BRIDGE.md`:**

```markdown
# BridgeService Execution Flow

## Constructor (__init__)
Line-by-line what happens:
1. Line X: Creates ConfigLoader -> trace to 1.2.1
2. Line Y: Creates EntityService -> trace to 1.2.2
3. Line Z: Creates SessionRepository -> trace to 1.2.3
...

## Services Instantiated
- ConfigLoader: [file path] -> TRACE THIS
- EntityService: [file path] -> TRACE THIS
- SessionRepository: [file path] -> TRACE THIS
[List EVERY service created]

## Methods Called During Init
- method_name (line X) -> what does it do?

## Files It Accesses
- config.json (line X)
- [list all files]
```

---

**Step 2: For EACH service instantiated in BridgeService, read its file**

Example for EntityService:

```bash
Read: C:\Users\green\Desktop\RP Claude Code\refactoring\src\domain\entities\entity_service.py
```

**Document in `EXECUTION_FLOW_2_BRIDGE_SERVICES.md`:**

```markdown
# EntityService Analysis

## File: src/domain/entities/entity_service.py

### Constructor Dependencies
- repository: FixtureEntityRepository (line X) -> TRACE THIS
- templates: StateTemplateService (line Y) -> TRACE THIS
[List all dependencies]

### Methods Defined
1. method_name (line X): [what it does]
2. method_name (line Y): [what it does]

### Methods CALLED BY BRIDGE
- [Which methods does BridgeService actually call?]
- [Search bridge_service.py for entity_service.method_name]

### Methods NEVER CALLED
- [List methods that are never called]
```

**Repeat for EVERY service** that BridgeService creates.

---

**Step 3: Trace handler initialization**

BridgeService likely creates handlers. For each handler:

```bash
# Example
Read: src/presentation/bridge/handlers/entity_handler.py
```

**Document which IPC message types trigger which handlers**

---

### 1.3: TUI Application Initialization Trace

**Step 1: Read RPClientApp completely**

```bash
Read: C:\Users\green\Desktop\RP Claude Code\refactoring\src\presentation\tui\app.py
```

**Document in `EXECUTION_FLOW_3_TUI.md`:**

```markdown
# TUI Application Flow

## Constructor
[Same detailed format as BridgeService]

## Screens/Components Created
- ChatDisplay (line X) -> TRACE THIS
- SettingsOverlay (line Y) -> TRACE THIS
[List all components]

## IPC Calls Made
- GET_ENTITIES (line X) -> goes to entity_handler
- [List all IPC calls]
```

---

**Step 2: For EACH component instantiated, read and trace**

```bash
Read: src/presentation/tui/components/chat_display.py
```

**Document dependencies and what it uses**

---

### 1.4: Build Runtime Call Graph

**Create `RUNTIME_CALL_GRAPH.md`:**

```markdown
# Runtime Call Graph

## Startup Sequence
launch.py
  └─> BridgeService.__init__
       ├─> ConfigLoader.__init__
       │    └─> defaults.py (loads default config)
       ├─> EntityService.__init__
       │    ├─> FixtureEntityRepository.__init__
       │    └─> StateTemplateService.__init__
       └─> [etc...]
  └─> RPClientApp.__init__
       └─> [etc...]

## IPC Request Flows
When TUI sends GET_ENTITIES:
  TUI (app.py:123)
    -> SocketClient.send_request
      -> BridgeService.handle_request
        -> EntityHandler.handle
          -> EntityService.list_characters
            -> FixtureEntityRepository.get_all_characters
              -> [reads JSON files]

[Document EVERY IPC message type flow]
```

---

### 1.5: Agent Execution Flows

Agents are critical. Trace how they're invoked:

```bash
Read: src/automation/services/automation_service.py
```

**Document in `EXECUTION_FLOW_4_AGENTS.md`:**

```markdown
# Agent Execution Flow

## When/How Agents Are Triggered
[Find where automation_service.execute is called]

## Agent Strategy Selection
- ImmediateAgentStrategy: triggered when? (line X in file Y)
- BackgroundAgentStrategy: triggered when? (line X in file Y)

## Agent Instantiation
For each agent type, trace:
1. Which strategy creates it?
2. What parameters are passed?
3. What does its execute() method do?
4. Does it use call_llm()? (verify by reading the agent file)
```

---

**For EACH agent implementation:**

```bash
# Example
Read: src/automation/agents/implementations/memory_creation_agent.py
```

**Document:**
- Does it use `call_llm()`? (line numbers)
- Does it use `BaseAgent` methods? (which ones?)
- What files does it read/write?
- Is it registered in a strategy? (verify)

**Create:** `AGENT_USAGE_MATRIX.md`

```markdown
| Agent | Registered? | Uses call_llm? | Uses BaseAgent Methods | Reads Files | Writes Files |
|-------|-------------|----------------|------------------------|-------------|--------------|
| memory_creation | Yes (immediate_agent_strategy.py:123) | Yes (line 45) | save_json (line 67) | memories/ | state/memories.json |
```

---

## PHASE 2: LAYER-BY-LAYER COMPREHENSIVE FILE READING (4-6 hours)

### Objective
Read EVERY Python file and document what it does, what uses it, and whether it's dead code.

### 2.1: Infrastructure Layer

**Step 1: List all files**

```bash
Bash: find src/infrastructure -name "*.py" -type f | sort
```

**Create tracking document:** `INFRASTRUCTURE_FILES.md`

```markdown
# Infrastructure Layer Files (X total)

## Status Legend
- ✅ ANALYZED
- ⏳ IN PROGRESS
- ⬜ NOT STARTED
- 💀 DEAD CODE CONFIRMED
- ✨ ACTIVELY USED

---

## src/infrastructure/config/
- [ ] config_loader.py - Status: ⬜
- [ ] defaults.py - Status: ⬜
- [ ] __init__.py - Status: ⬜

[List EVERY file]
```

---

**Step 2: Read EACH file systematically**

For each file, create an analysis document:

```bash
# Example
Read: src/infrastructure/config/config_loader.py
```

**Create:** `ANALYSIS_infrastructure_config_config_loader.md`

```markdown
# Analysis: infrastructure/config/config_loader.py

## File Statistics
- Lines of Code: 234
- Classes Defined: 2
- Functions Defined: 5
- Last Modified: [check git log]

## Classes Defined

### ConfigLoader (line 15-180)
**Purpose:** [What does this class do?]

**Constructor Dependencies:**
- logger: LoggingService (line 20)
- [list all]

**Methods:**
1. `load_config(rp_dir: Path)` (line 25-60)
   - **Purpose:** [what it does]
   - **Called by:**
     - bridge_service.py:45
     - [list ALL files that call this]
   - **Usage Count:** 2 locations
   - **Status:** ✨ ACTIVELY USED

2. `_merge_configs()` (line 62-95)
   - **Purpose:** [what it does]
   - **Called by:** load_config (internal only)
   - **Usage Count:** 1 (internal)
   - **Status:** ✨ ACTIVELY USED

[Document EVERY method with whether it's used]

## Imports Made
- from pathlib import Path (line 1) - standard library
- from ..llm.base import LLMClient (line 5) -> CROSS-LAYER IMPORT ⚠️

## Imported By (Who uses this file?)
Search results for "from.*config_loader import":
- bridge_service.py (line 12)
- [list all]

## Verification Steps Completed
- [x] Read entire file
- [x] Searched for all imports of this file
- [x] Verified each method is called
- [x] Checked tests for usage

## Findings
- **Dead Code:** None found
- **Issues:** Cross-layer import at line 5 (infrastructure importing from domain - verify if this is correct)
- **Recommendations:** [any suggestions]
```

---

**Step 3: As you analyze each file, update the tracking document**

Update `INFRASTRUCTURE_FILES.md`:

```markdown
## src/infrastructure/config/
- [✅] config_loader.py - Status: ✨ ACTIVELY USED - Analysis: ANALYSIS_infrastructure_config_config_loader.md
- [⏳] defaults.py - Status: IN PROGRESS
```

---

**Step 4: For each layer, create a summary**

After completing infrastructure layer:

**Create:** `INFRASTRUCTURE_SUMMARY.md`

```markdown
# Infrastructure Layer Analysis Summary

## Files Analyzed: 42

## Status Breakdown
- ✨ Actively Used: 35 files
- 💀 Dead Code: 7 files
- ⚠️ Partially Used: 0 files

## Dead Code Found

### 1. src/infrastructure/llm/mock_client.py
- **Lines:** 145
- **Reason:** Only used in tests, not in production code
- **Verification:**
  - Searched for imports: found only in tests/
  - No runtime usage found
  - Not registered in llm_router.py
- **Recommendation:** Move to tests/fixtures/ or mark as test-only

[Document each dead code file with PROOF]

## Architectural Issues Found

### 1. Cross-Layer Import Violation
- **File:** infrastructure/config/config_loader.py:5
- **Issue:** Imports from domain layer (domain.entities)
- **Impact:** Violates clean architecture
- **Recommendation:** Create interface in shared/

[Document each issue]

## Duplication Found

### 1. Error Message Extraction
- **Files:**
  - llm/claude_api_client.py:396-404
  - llm/openai_client.py:530-538
- **Similarity:** 100% identical
- **Lines Duplicated:** 9 lines × 2 files = 18 lines
- **Recommendation:** Extract to llm/client_utilities.py

[Document each duplication]
```

---

### 2.2: Domain Layer

**Repeat the exact same process for domain layer:**

1. List all files: `DOMAIN_FILES.md`
2. Analyze each file: `ANALYSIS_domain_[path].md`
3. Create summary: `DOMAIN_SUMMARY.md`

---

### 2.3: Automation Layer

Same process:
1. `AUTOMATION_FILES.md`
2. Individual analyses
3. `AUTOMATION_SUMMARY.md`

**SPECIAL ATTENTION FOR AGENTS:**

For each agent file, verify:
- Is it registered in immediate_agent_strategy.py or background_agent_strategy.py?
- Does its execute() method get called? (trace from strategy)
- Does it use call_llm()? (read the actual code)
- What BaseAgent methods does it use?

---

### 2.4: Presentation Layer

Same process:
1. `PRESENTATION_FILES.md`
2. Individual analyses
3. `PRESENTATION_SUMMARY.md`

**SPECIAL ATTENTION FOR HANDLERS:**

For each bridge handler:
- Which IPC message types does it handle?
- Is that message type sent by TUI? (search tui/ for the message type)
- What services does it call?

---

### 2.5: Root Level Files

```bash
Bash: ls *.py
```

Analyze each:
- `launch.py` - already analyzed in Phase 1
- `test_*.py` - these are test files, document but mark as test-only
- Any other .py files

---

## PHASE 3: CROSS-VERIFICATION (2-3 hours)

### Objective
Verify findings by checking from multiple angles and confirming with tests.

### 3.1: Verify Dead Code Claims

For EACH file/method flagged as dead code:

**Verification Checklist:**

```markdown
# Dead Code Verification: [file/method name]

## Check 1: Grep for Imports
```bash
grep -r "from.*[module] import" src/
grep -r "import.*[module]" src/
```
Results: [paste results or "none found"]

## Check 2: Grep for Direct Usage
```bash
grep -r "[class_name]\|[function_name]" src/
```
Results: [paste results]

## Check 3: Check Tests
```bash
grep -r "[class_name]\|[function_name]" tests/
```
Results: [paste results]
- If found in tests: Mark as "TEST-ONLY, not dead code"
- If not found: Continue verification

## Check 4: Check __init__.py Exports
```bash
Read: [parent directory]/__init__.py
```
Is it exported? [yes/no]
If yes, check who imports from __init__.py

## Check 5: Runtime Trace Verification
Based on Phase 1 call graph, is this in any execution path?
[yes/no with explanation]

## FINAL VERDICT
- [ ] CONFIRMED DEAD CODE - can be removed
- [ ] TEST-ONLY - move to tests/ or mark clearly
- [ ] ACTUALLY USED - my analysis was wrong, mark as USED
- [ ] UNCLEAR - needs further investigation

## Evidence
[Paste all evidence supporting the verdict]
```

---

### 3.2: Verify Duplication Claims

For EACH duplication flagged:

**Verification Checklist:**

```markdown
# Duplication Verification: [description]

## Files Involved
1. [file path:lines]
2. [file path:lines]

## Read Both Sections
```bash
Read: [file1] (offset=line_start, limit=num_lines)
Read: [file2] (offset=line_start, limit=num_lines)
```

## Side-by-Side Comparison
[Paste both code sections]

## Similarity Analysis
- Identical: [yes/no]
- Similarity percentage: [X%]
- Differences: [list key differences]

## Consolidation Feasibility
- Can be extracted: [yes/no]
- Proposed location: [where to put shared code]
- Effort estimate: [hours]

## VERDICT
- [ ] CONFIRMED DUPLICATION - consolidate recommended
- [ ] SIMILAR BUT DIFFERENT - not worth consolidating
- [ ] FALSE POSITIVE - not actually duplicated
```

---

### 3.3: Verify Architecture Violations

For EACH architecture violation flagged:

**Verification Checklist:**

```markdown
# Architecture Violation: [description]

## Import Statement
File: [file path]
Line: [line number]
Import: `[import statement]`

## Layer Analysis
- Importing Layer: [Domain/Infrastructure/Presentation/Application]
- Imported Layer: [Domain/Infrastructure/Presentation/Application]
- Allowed by Clean Architecture: [yes/no]

## Read the Actual Usage
```bash
Read: [file with violation]
```

Why is it importing this? [explain the actual usage]

## Impact Assessment
- Severity: [Critical/High/Medium/Low]
- Affects testability: [yes/no]
- Circular dependency risk: [yes/no]

## Proposed Fix
[Describe how to fix - e.g., create interface in shared/]

## VERDICT
- [ ] CONFIRMED VIOLATION - fix required
- [ ] ACCEPTABLE EXCEPTION - document why
- [ ] FALSE POSITIVE - not actually a violation
```

---

### 3.4: Test Coverage Analysis

For files flagged as unused, check test coverage:

```bash
# Run pytest with coverage for specific file
Bash: cd "C:\Users\green\Desktop\RP Claude Code\refactoring" && python -m pytest tests/ --cov=src/[path/to/file] --cov-report=term-missing
```

**Create:** `TEST_COVERAGE_ANALYSIS.md`

```markdown
# Test Coverage Analysis

## Files Flagged as Unused

### [file name]
- Coverage: X%
- Lines tested: X/Y
- Test files that import it:
  - tests/[path]
- **Verdict:**
  - If coverage > 0%: Used in tests, mark as TEST-ONLY
  - If coverage = 0%: Confirm as dead code
```

---

## PHASE 4: BUILD COMPREHENSIVE FINDINGS REPORT (1-2 hours)

### 4.1: Consolidate All Findings

**Create:** `FINAL_COMPREHENSIVE_ANALYSIS.md`

Structure:

```markdown
# Comprehensive Codebase Analysis - FINAL REPORT

**Analysis Completion Date:** [date]
**Files Analyzed:** [total count]
**Analysis Method:** Execution flow tracing + file-by-file reading + cross-verification
**Confidence Level:** HIGH (all findings verified 3+ ways)

---

## EXECUTIVE SUMMARY

### Codebase Health Metrics
- Total Python Files: X
- Actively Used Files: Y (Z%)
- Dead Code Files: A (B%)
- Test-Only Files: C (D%)
- Total Lines of Code: ~X
- Dead Code Lines: ~Y (Z%)

### Critical Findings
1. [Most important finding]
2. [Second most important]
...

---

## PART 1: DEAD CODE ANALYSIS

### Confirmed Dead Code (High Confidence)

#### Category: Unused Infrastructure

##### 1. [File/Module Name]
**Location:** [path]
**Lines:** [count]
**Evidence:**
- No imports found in src/
- No imports found in tests/
- Not in any execution path
- Verified 3 ways: grep + file reading + runtime trace

**Verification:**
```
[Paste verification evidence]
```

**Recommendation:** DELETE or move to archive/

**Priority:** [High/Medium/Low]
**Effort to Remove:** [hours]

---

[Repeat for each dead code finding]

### Test-Only Code (Not Dead, But Not Production)

[List code that's only used in tests]

---

## PART 2: DUPLICATION ANALYSIS

### Confirmed Duplications

#### 1. [Description]
**Files:**
- [file1:lines]
- [file2:lines]

**Similarity:** X% identical
**Lines Duplicated:** Y lines × Z files = Total lines

**Code Comparison:**
```python
# File 1
[paste code]

# File 2
[paste code]
```

**Proposed Consolidation:**
Create: [new file path]
```python
[proposed shared code]
```

**Effort:** [hours]
**Impact:** Saves X lines, improves maintainability

---

## PART 3: ARCHITECTURAL ISSUES

### Layer Violations (Confirmed)

#### 1. Domain → Infrastructure Import
**File:** [path:line]
**Import:** `[import statement]`
**Severity:** Critical
**Impact:** Violates Dependency Inversion Principle

**Current Code:**
```python
[paste code showing violation]
```

**Proposed Fix:**
[Detailed fix with code examples]

**Effort:** [hours]

---

## PART 4: OUTDATED CODE

[Any deprecated patterns, TODO comments that need addressing, etc.]

---

## PART 5: PRIORITIZED ACTION PLAN

### Immediate (This Week)
1. [Action item with effort estimate]
2. [Action item with effort estimate]

### High Priority (This Sprint)
[List items]

### Medium Priority (Next Sprint)
[List items]

### Low Priority (Backlog)
[List items]

---

## APPENDICES

### Appendix A: Methodology
[Describe how this analysis was performed]

### Appendix B: Files Analyzed
[Link to all individual file analyses]

### Appendix C: Verification Logs
[Link to all verification checklists]

### Appendix D: Call Graphs
[Link to execution flow documents]
```

---

## DELIVERABLES CHECKLIST

By the end of this analysis, you should have created:

### Phase 1 Deliverables
- [ ] `EXECUTION_FLOW_1_LAUNCH.md`
- [ ] `EXECUTION_FLOW_1_START_BRIDGE.md`
- [ ] `EXECUTION_FLOW_1_START_TUI.md`
- [ ] `EXECUTION_FLOW_2_BRIDGE.md`
- [ ] `EXECUTION_FLOW_2_BRIDGE_SERVICES.md`
- [ ] `EXECUTION_FLOW_3_TUI.md`
- [ ] `EXECUTION_FLOW_4_AGENTS.md`
- [ ] `RUNTIME_CALL_GRAPH.md`
- [ ] `AGENT_USAGE_MATRIX.md`

### Phase 2 Deliverables
- [ ] `INFRASTRUCTURE_FILES.md` (tracking document)
- [ ] `INFRASTRUCTURE_SUMMARY.md`
- [ ] Individual analyses for ~42 infrastructure files
- [ ] `DOMAIN_FILES.md` (tracking document)
- [ ] `DOMAIN_SUMMARY.md`
- [ ] Individual analyses for ~15 domain files
- [ ] `AUTOMATION_FILES.md` (tracking document)
- [ ] `AUTOMATION_SUMMARY.md`
- [ ] Individual analyses for ~60 automation files
- [ ] `PRESENTATION_FILES.md` (tracking document)
- [ ] `PRESENTATION_SUMMARY.md`
- [ ] Individual analyses for ~50 presentation files

### Phase 3 Deliverables
- [ ] Verification checklists for each dead code claim
- [ ] Verification checklists for each duplication claim
- [ ] Verification checklists for each architecture violation
- [ ] `TEST_COVERAGE_ANALYSIS.md`

### Phase 4 Deliverables
- [ ] `FINAL_COMPREHENSIVE_ANALYSIS.md`

---

## QUALITY ASSURANCE CHECKLIST

Before finalizing any finding:

### For Dead Code Claims
- [ ] Verified with grep (3+ different search patterns)
- [ ] Read the actual file
- [ ] Checked tests directory
- [ ] Checked __init__.py exports
- [ ] Confirmed not in execution flow
- [ ] Verified with test coverage report

### For Duplication Claims
- [ ] Read both/all duplicated sections completely
- [ ] Compared side-by-side
- [ ] Calculated actual similarity percentage
- [ ] Proposed consolidation approach
- [ ] Estimated effort

### For Architecture Violations
- [ ] Read the importing file
- [ ] Understood why the import exists
- [ ] Confirmed it violates clean architecture rules
- [ ] Assessed impact
- [ ] Proposed fix

---

## IMPORTANT GUIDELINES

### 1. When in Doubt, Read the File
**DO NOT rely only on grep.** Always read the actual source code.

### 2. Verify Everything 3 Ways
- Grep search
- File reading
- Cross-reference check

### 3. Check Tests
Code used only in tests is NOT dead code - it's test infrastructure.

### 4. Be Systematic
Work through files in order. Don't skip around.

### 5. Document As You Go
Don't wait until the end to document. Create analysis files immediately.

### 6. Question Your Findings
If something seems unused but is well-written and integrated, verify again.

### 7. Execution Flow is Truth
If the runtime call graph shows it's used, it's used - even if grep doesn't find it.

### 8. Mark Confidence Levels
- HIGH: Verified 3+ ways
- MEDIUM: Verified 2 ways
- LOW: Only grep search

Only report HIGH confidence findings.

---

## SPECIAL CASES TO WATCH FOR

### 1. Dynamic Imports
```python
# This won't show up in grep for "import ClassName"
module = importlib.import_module("module_name")
cls = getattr(module, "ClassName")
```

**How to catch:** Read factory.py, registry.py files carefully

---

### 2. Registry Pattern
```python
# Agent might be registered dynamically
AGENT_REGISTRY = {
    "memory": MemoryCreationAgent,  # Only referenced here
}
```

**How to catch:** Look for REGISTRY, FACTORY patterns

---

### 3. Test Fixtures
```python
# Might only be used in conftest.py
```

**How to catch:** Check tests/conftest.py and tests/fixtures/

---

### 4. __init__.py Exports
```python
# File: domain/entities/__init__.py
from .entity_service import EntityService  # Re-export

# File: somewhere_else.py
from domain.entities import EntityService  # Uses re-export
```

**How to catch:** Always check __init__.py files

---

### 5. Protocol/Interface Usage
```python
# Protocol defined but only used in type hints
class IRepository(Protocol):
    def save(self) -> None: ...

# Used like this:
def process(repo: IRepository):  # Type hint, not direct import
```

**How to catch:** Check TYPE_CHECKING imports and type hints

---

## ESTIMATED TIMELINE

**Phase 1:** 2-3 hours
- Entry point tracing: 1 hour
- Service initialization tracing: 1-2 hours

**Phase 2:** 4-6 hours
- Infrastructure (42 files): 1.5 hours
- Domain (15 files): 30 minutes
- Automation (60 files): 2 hours
- Presentation (50 files): 1.5 hours
- Root files: 30 minutes

**Phase 3:** 2-3 hours
- Verification of findings: 2-3 hours

**Phase 4:** 1-2 hours
- Report compilation: 1-2 hours

**Total:** 9-14 hours

---

## START HERE

When you begin this analysis in a fresh Claude Code instance:

1. Read this entire plan document first
2. Create a working directory for artifacts: `mkdir analysis_artifacts`
3. Start with Phase 1, Step 1: Read launch.py
4. Follow the plan systematically
5. Don't skip steps
6. Verify everything before marking it as done
7. Create documentation as you go

**First Command to Run:**
```bash
cd "C:\Users\green\Desktop\RP Claude Code\refactoring"
Read: launch.py
```

**First Document to Create:**
```bash
Write: analysis_artifacts/EXECUTION_FLOW_1_LAUNCH.md
```

Good luck! Be thorough, be systematic, and verify everything.
