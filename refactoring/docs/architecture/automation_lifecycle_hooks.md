# Automation Pipeline Lifecycle Hooks

**Document Version:** 1.0.0
**Last Updated:** 2025-10-20
**Audience:** Contributors extending the automation system

## Overview

The automation pipeline follows a well-defined 6-step lifecycle that processes user messages and generates context-rich prompts. This document explains each step and how to inject custom logic at various points without modifying core code.

## Pipeline Architecture

The automation pipeline is implemented in `AutomationService.run()` and orchestrates multiple services to transform a simple user message into a comprehensive prompt for AI generation.

### Core Flow

```
User Message
    ↓
[Step 1] Load Configuration & Session State
    ↓
[Step 2] Increment Counters & Load Tiered Files
    ↓
[Step 3] Prepare Domain/Entity Information
    ↓
[Step 4] Build Prompt
    ↓
[Step 5] Execute Agents
    ↓
[Step 6] Post-Run Bookkeeping
    ↓
Enhanced Prompt + Automation Result
```

## Lifecycle Steps

### Step 1: Load Configuration & Session State

**Purpose:** Hydrate the automation context with configuration and session history.

**Components:**
- `ConfigService` - Loads automation settings from `state/automation_config.json`
- `SessionService` - Enriches context with session history (messages, agent data, entities)

**What Happens:**
```python
hydrated_context = self._load_configuration(context)
hydrated_context = self._session_service.enrich_session(hydrated_context)
```

**Extension Point:** Custom session enrichment
```python
class CustomSessionService:
    """Custom session service with additional enrichment."""

    def enrich_session(self, context: AutomationContext) -> AutomationContext:
        # Load session data
        context = self._load_session_data(context)

        # Custom logic: Add custom metadata
        custom_data = self._extract_custom_metadata(context)

        # Merge into context
        return context.with_update(metadata=custom_data)
```

### Step 2: Increment Counters & Load Tiered Files

**Purpose:** Track response count and load context files based on tier rules.

**Components:**
- `FileAccessService.increment_response_counter()` - Increments counter in `state/response_counter.json`
- `FileAccessService.load_tiered_context()` - Loads files from tier 1, 2, and 3

**Tier Rules:**
- **Tier 1:** Always loaded (ROLEPLAY_OVERVIEW.md, GAME_RULES.md, etc.)
- **Tier 2:** Loaded when counter threshold met (entities marked for frequent access)
- **Tier 3:** Conditionally loaded (triggered entities, entities mentioned in message)

**What Happens:**
```python
counter_value = self._file_access.increment_response_counter()
tiered_context = self._file_access.load_tiered_context(
    response_count=counter_value,
    triggered_files=hydrated_context.tier3_files,
)
enriched_context = self._apply_file_context(
    hydrated_context,
    counter_value=counter_value,
    tiered_context=tiered_context,
)
```

**Extension Point:** Custom tier logic
```python
# Override FileAccessService to customize tier loading
class CustomFileAccessService(FileAccessService):
    def load_tiered_context(self, *, response_count, triggered_files):
        # Custom tier 1 logic
        tier1 = self._load_custom_tier1()

        # Custom tier 2 logic (e.g., time-based loading)
        tier2 = self._load_time_based_tier2(response_count)

        # Standard tier 3
        tier3 = self._load_tier3(triggered_files)

        return TieredContext(tier1=tier1, tier2=tier2, tier3=tier3)
```

### Step 3: Prepare Domain/Entity Information

**Purpose:** Enrich context with entity-specific data and metadata.

**Components:**
- `EntityService.prepare_entities()` - Loads entity cards, preferences, cores

**What Happens:**
```python
domain_context = self._entity_service.prepare_entities(enriched_context)
```

**Extension Point:** Custom entity preparation
```python
class CustomEntityService:
    """Entity service with additional processing."""

    def prepare_entities(self, context: AutomationContext) -> AutomationContext:
        # Standard entity loading
        entities = self._load_entities(context)

        # Custom logic: Generate dynamic entity summaries
        summaries = self._generate_entity_summaries(entities)

        # Custom logic: Extract entity relationships
        relationships = self._extract_relationships(entities)

        # Update context
        return context.with_update(
            loaded_entities=[e.name for e in entities],
            entity_summaries=summaries,
            entity_relationships=relationships,
        )
```

### Step 4: Build Prompt

**Purpose:** Assemble the final prompt from all loaded context.

**Components:**
- `PromptBuilder.build_prompt()` - Assembles prompt sections
- `NarrativeTemplateManager` - Adds genre-specific narrative guidance
- `PromptSections` - Modular section builders (tier files, time, entities, agents, etc.)

**What Happens:**
```python
prompt = self._prompt_builder.build_prompt(domain_context)
```

**Sections Included:**
1. Narrative Template (if enabled)
2. Tier 1 Files (always)
3. Tier 2 Files (conditional)
4. Time Tracking (if activities detected)
5. Entity Information
6. Story Arc (if threshold met)
7. File Updates (if pending)
8. Agent Context (immediate + background)
9. User Message

**Extension Point:** Custom prompt sections
```python
class CustomPromptBuilder(PromptBuilder):
    """Prompt builder with custom sections."""

    def build_prompt(self, context: AutomationContext) -> str:
        # Build standard sections
        sections = build_all_sections(context)

        # Add custom section
        custom_section = self._build_custom_section(context)
        sections.append(custom_section)

        # Add narrative template
        template = self._load_narrative_template(context)

        # Assemble
        return f"{template}\n\n" + "\n\n".join(s.render() for s in sections)

    def _build_custom_section(self, context):
        """Build custom prompt section."""
        return PromptSection(
            title="Custom Analytics",
            body=self._generate_analytics(context),
            priority=5,
        )
```

### Step 5: Execute Agents

**Purpose:** Run background/immediate agents to gather additional context or perform analysis.

**Components:**
- `AgentRunner.run()` - Executes agent strategies in order
- `BackgroundAgentStrategy` - Post-response analysis (memory creation, plot detection)
- `ImmediateAgentStrategy` - Pre-response context gathering (entity analysis, memory extraction)
- `FallbackTriggerStrategy` - Pattern-based context loading

**What Happens:**
```python
result = self._agent_runner.run(domain_context, prompt)
```

**Extension Point:** Custom agent strategies
```python
class CustomAgentStrategy:
    """Custom agent strategy for specialized processing."""

    def execute(self, agent_context, prompt, automation_context):
        # Custom agent logic
        analysis = self._run_custom_analysis(agent_context.message)

        # Format results
        formatted = self._format_analysis(analysis)

        # Inject into prompt
        enhanced_prompt = f"{prompt}\n\n<!-- CUSTOM ANALYSIS -->\n{formatted}"

        return AutomationResult(
            success=True,
            enhanced_prompt=enhanced_prompt,
            metadata={"custom_analysis": analysis},
        )

# Register strategy
agent_registry = AgentRegistry(config, logger)
agent_registry.register_strategy("custom", CustomAgentStrategy())
```

### Step 6: Post-Run Bookkeeping

**Purpose:** Finalize state updates, logging, and cleanup.

**Components:**
- Internal logging
- State persistence (counters, session data)
- Cleanup

**What Happens:**
```python
self._finalise(domain_context, result)
self._logger.info("automation.run.complete", context={"success": result.success})
```

**Extension Point:** Post-run hooks
```python
class CustomAutomationService(AutomationService):
    """Automation service with post-run hooks."""

    def run(self, context):
        # Execute standard pipeline
        result = super().run(context)

        # Post-run hook: Log analytics
        self._log_analytics(context, result)

        # Post-run hook: Update external systems
        self._update_external_systems(context, result)

        # Post-run hook: Generate summary
        self._generate_summary(context, result)

        return result

    def _log_analytics(self, context, result):
        """Log analytics data."""
        analytics = {
            "prompt_length": len(result.enhanced_prompt),
            "entities_loaded": len(context.loaded_entities),
            "response_count": context.response_count,
        }
        self._analytics_service.log(analytics)
```

## Pre-Run Hooks

Pre-run hooks allow you to inject custom logic **before** the automation pipeline starts.

### Approach 1: Wrapper Service

```python
class PreRunHookService:
    """Wrapper service that adds pre-run hooks."""

    def __init__(self, automation_service: AutomationService):
        self._automation_service = automation_service

    def run(self, context: AutomationContext) -> AutomationResult:
        # Pre-run hook: Validate context
        if not self._validate_context(context):
            return AutomationResult(success=False, error="Invalid context")

        # Pre-run hook: Enrich context with external data
        context = self._enrich_with_external_data(context)

        # Pre-run hook: Log request
        self._log_request(context)

        # Execute main pipeline
        return self._automation_service.run(context)
```

### Approach 2: Subclass AutomationService

```python
class HookedAutomationService(AutomationService):
    """Automation service with built-in pre/post hooks."""

    def run(self, context: AutomationContext) -> AutomationResult:
        # Pre-run hooks
        context = self._pre_run_hooks(context)

        # Execute pipeline
        result = super().run(context)

        # Post-run hooks
        result = self._post_run_hooks(context, result)

        return result

    def _pre_run_hooks(self, context):
        """Execute all pre-run hooks."""
        for hook in self._registered_pre_hooks:
            context = hook(context)
        return context
```

## Common Extension Patterns

### 1. Adding Custom Prompt Sections

Create a new section builder:

```python
@dataclass(frozen=True)
class CustomSection:
    """Custom prompt section."""

    @staticmethod
    def build(context: AutomationContext) -> List[PromptSection]:
        if not context.custom_data:
            return []

        body = "## Custom Data\n\n"
        body += "\n".join(f"- {item}" for item in context.custom_data)

        return [PromptSection(
            title="Custom Section",
            body=body,
            priority=3,  # Control ordering
        )]

# Register in build_all_sections()
```

### 2. Custom Trigger Evaluators

Add new trigger types:

```python
class LocationProximityEvaluator:
    """Trigger evaluator based on location proximity."""

    def evaluate(self, patterns, context):
        # Custom logic: Check if message mentions nearby locations
        current_location = self._extract_location(context.message)
        nearby_locations = self._find_nearby(current_location, patterns.file_path)

        if nearby_locations:
            return TriggerResult(
                file_path=patterns.file_path,
                entity_name=patterns.entity_name,
                trigger_type="proximity",
                matched_pattern=f"Near {current_location}",
                confidence=0.8,
            )
        return None

# Register in TriggerRegistry
registry.register_evaluator("proximity", LocationProximityEvaluator())
```

### 3. Custom Agent Strategies

Create specialized agents:

```python
class SentimentAnalysisStrategy:
    """Agent strategy for sentiment analysis."""

    def execute(self, agent_context, prompt, automation_context):
        # Analyze message sentiment
        sentiment = self._analyze_sentiment(agent_context.message)

        # Adjust prompt based on sentiment
        if sentiment == "positive":
            enhancement = "<!-- User is feeling positive -->"
        elif sentiment == "negative":
            enhancement = "<!-- User is feeling negative, be supportive -->"
        else:
            enhancement = ""

        enhanced_prompt = f"{prompt}\n\n{enhancement}"

        return AutomationResult(
            success=True,
            enhanced_prompt=enhanced_prompt,
            metadata={"sentiment": sentiment},
        )
```

## Factory Pattern for Dependency Injection

Use the factory to inject custom services:

```python
# Example: Inject custom entity service
custom_entity_service = CustomEntityService(
    repository=CustomRepository(),
    logger=logger,
)

service = create_automation_service(
    rp_dir=Path("/path/to/rp"),
    entity_service=custom_entity_service,
)

# Example: Inject multiple custom services
service = create_automation_service(
    rp_dir=Path("/path/to/rp"),
    entity_service=CustomEntityService(),
    prompt_builder=CustomPromptBuilder(config, logger),
    agent_runner=CustomAgentRunner(strategies, logger),
)
```

## Testing Custom Extensions

Use the factory for easy testing:

```python
def test_custom_entity_service(tmp_path):
    # Create mock entity service
    mock_entities = Mock(spec=EntityService)
    mock_entities.prepare_entities.return_value = test_context

    # Inject into automation service
    service = create_automation_service(
        tmp_path,
        entity_service=mock_entities,
    )

    # Execute and verify
    result = service.run(context)
    assert mock_entities.prepare_entities.called
```

## Best Practices

1. **Use Protocols:** Define clear interfaces for custom services
2. **Maintain Immutability:** Always return new `AutomationContext` instances (use `.with_update()`)
3. **Log Extensively:** Use structured logging for debugging
4. **Test in Isolation:** Mock dependencies when testing custom components
5. **Document Extensions:** Add docstrings explaining custom logic
6. **Follow Naming Conventions:** snake_case for modules/functions, PascalCase for classes

## References

- **Source:** `refactoring/src/automation/services/automation_service.py`
- **Factory:** `refactoring/src/automation/factory.py`
- **Strategies:** `refactoring/src/automation/agents/`
- **Protocols:** `refactoring/src/automation/services/automation_service.py` (lines 14-55)
- **Smoke Test:** `refactoring/tests/automation/test_automation_smoke.py`

## Related Documentation

- [Workstream D Implementation](workstream_d_implementation.md) - Overall automation pipeline
- [Workstream F Implementation](workstream_f_implementation.md) - Trigger & template systems
- [Architecture README](README.md) - Module boundaries and dependencies

---

**Document Owner:** Workstream D
**Last Review:** 2025-10-20
