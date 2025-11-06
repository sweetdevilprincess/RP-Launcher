# Infrastructure Component Inventory

Legacy modules earmarked for the infrastructure layer and their refactor destinations.

| Legacy Path | Responsibility | Refactor Target | Status |
| --- | --- | --- | --- |
| `src/fs_write_queue.py` | Debounced filesystem writes | `refactoring/src/infrastructure/filesystem/write_queue.py` | Ported |
| `src/file_manager.py` | High-level file operations & migrations | `refactoring/src/infrastructure/filesystem/file_manager.py` + helpers | Ported |
| `src/utils/file_utils.py` | Generic file helpers (read/write/list) | Evaluate merge into `FileManager` & shared helpers | Pending review |
| `src/utils/json_utils.py` | JSON parsing/sanitising helpers | Likely `refactoring/src/shared/utils/json_utils.py` | Pending |
| `src/utils/time_utils.py` | Time formatting/duration helpers | Candidate for `shared/utils` | Pending |
| `src/utils/agent_logger.py` | Agent-specific logging | Copied to `refactoring/src/infrastructure/logging/agent_logging.py` (needs integration) | Ported (await adoption) |
| `src/core/config.py` | Config loader/defaults | `refactoring/src/infrastructure/config/config_loader.py` | Ported |
| `src/core/base.py` | Module lifecycle base class | Possibly domain-specific; defer for now | Needs decision |
| `src/clients/proxy_client.py` | HTTP proxy orchestration | `refactoring/src/infrastructure/transports/proxy_transport.py` | Ported |
| `src/clients/deepseek.py` | DeepSeek/OpenRouter API client | `refactoring/src/infrastructure/llm/openrouter_client.py` | Ported (multi-provider stack) |
| `src/clients/claude_api.py` | Claude API client | `refactoring/src/infrastructure/llm/claude_api_client.py` | Ported |
| `wip/clients/openai_client.py` | OpenAI API client | `refactoring/src/infrastructure/llm/openai_client.py` | Ported |
| `wip/clients/claude_sdk_client.py` | Claude SDK streaming bridge | `refactoring/src/infrastructure/llm/claude_sdk_client.py` | Ported |
| `wip/clients/registry.py` | Provider registry | `refactoring/src/infrastructure/llm/registry.py` | Ported |
| `src/clients/claude.py` | Legacy Claude wrapper | Determine if still needed; possibly retire | Needs decision |
| `src/clients/utils/python_fix.py` | Windows Python path helper | Possibly stay outside refactor scope | Needs decision |
| `src/update_checker.py` | Update checks (network + config) | Potential automation/infrastructure hybrid | Pending |
| `src/core/module_manager.py` | Module lifecycle orchestration | Might migrate later into automation | Pending |

Next steps:
- Integrate refactored transports into automation/domain layers and add contract tests.
- Decide whether to wrap remaining utils (`json_utils`, `time_utils`) under `shared/utils`.
- Confirm deprecation path for legacy Claude wrapper and Python path fix utility.
