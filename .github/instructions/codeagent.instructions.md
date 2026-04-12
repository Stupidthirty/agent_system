---
description: Describe when these instructions should be loaded by the agent based on task context
# applyTo: 'Describe when these instructions should be loaded by the agent based on task context' # when provided, instructions will automatically be added to the request context when the pattern matches an attached file
---

<!-- Tip: Use /create-instructions in chat to generate content with agent assistance -->

This file provides comprehensive guidelines for the AI agent when working with the repository. It covers:

- **When to load these instructions**: Automatically apply whenever any file in the `agent_system` workspace is touched or when the user asks for help with agents, skills, or tools.
- **Project context**: This is a multi‑agent framework built around Python, FastAPI, Redis, RabbitMQ, and LangGraph. Agents register capabilities and handle tasks via a router. The system is modular, with clear separation between API, main agent, router, workers, and concrete agent implementations.
- **Coding conventions**: Follow existing style, use `async`/`await` for I/O, prefer Pydantic models for data validation, add docstrings to new classes/methods, keep imports organized and avoid unused dependencies.
- **Skills and Tools**: When introducing or working with agent skills (`_get_skills`) or tools (`_get_tools`), ensure the names are descriptive and register them in the router. New tools should be simple wrappers around external APIs or utility functions.
- **MCP invocation**: For Python code modifications, use the MCP (Multi‑Code Prompt) tools when appropriate, such as `mcp_pylance_mcp_s_pylanceInvokeRefactoring` for refactoring or `mcp_pylance_mcp_s_pylanceRunCodeSnippet` to validate snippets. When asked to inspect or modify workspace files, use relevant MCP tools to analyze imports, syntax, or environment details.
- **General workflow**: Before writing code, explore the repository with search or the `Explore` agent. Document changes clearly, update README or relevant markdown, and ensure any new dependencies are added to `requirements.txt`.

Below are more detailed notes and examples to make them actionable:

---

### 🔧 1. Skills & Tools Guidelines
- **Skills**: Represent capabilities an agent can perform (e.g. `weather`, `track_task`). They are declared by overriding `_get_skills()` in the agent subclass. When adding a skill:
  1. Choose a concise, noun-like identifier (`"send_email"`, not `"doTheThing"`).
  2. Implement a handler method named `<skill>_handler(self, task)` or `async def` variant. It should return an `AgentResponse` (dict or model).
  3. Update the router registration logic if the skill needs special routing behavior.
- **Tools**: External APIs or utility functions usable by agents (e.g. `openai_api`, `redis_client`). Tools are listed via `_get_tools()` and may be injected into agent context. Keep tools stateless and dependency‑free when possible.

### 🧪 2. MCP (Multi-Code Prompt) Usage
- **Refactoring**: When asked to clean up code, add type hints, or remove unused imports, prefer `mcp_pylance_mcp_s_pylanceInvokeRefactoring` with the appropriate refactor name. Example:
  ```json
  {
    "fileUri": "file:///.../agent_system/agent_base.py",
    "name": "source.fixAll.pylance"
  }
  ```
- **Run snippets**: To verify logic or test imports, use `mcp_pylance_mcp_s_pylanceRunCodeSnippet` with a brief snippet and working directory.
- **Environment introspection**: Use `mcp_pylance_mcp_s_pylanceImports` or `mcp_pylance_mcp_s_pylanceInstalledTopLevelModules` to check available modules before adding new dependencies.
- **Syntax check**: Invoke `mcp_pylance_mcp_s_pylanceFileSyntaxErrors` when generating or editing longer Python code to ensure no syntax problems.

### 🗺️ 3. When to apply these rules
- Editing or creating any file under `agent_system/`.
- Answering questions about agent behavior, task flow, or routing logic.
- Working on tooling/integration (RabbitMQ, Redis, FastAPI) inside the repo.
- The agent should not inject these instructions when dealing with unrelated files (e.g. `pyaudio_test.py` unless asked explicitly).

---

By following these enhanced guidelines, the AI will produce code and explanations that match the project's conventions, effectively manage skills/tools, and leverage MCP tools for robust editing and analysis.

---

### ✅ 4. Testing & Validation
- **Unit tests**: Add tests under a `tests/` directory mirroring code structure. Use `pytest` and name functions with `test_` prefix. Mock external services (Redis, RabbitMQ, OpenAI) using `unittest.mock` or `pytest-mock`.
- **Integration tests**: For end-to-end scenarios, spin up local Redis/RabbitMQ (e.g., via Docker compose) and exercise the API endpoints. Use `httpx` or `requests` to call the FastAPI app.
- **Continuous integration**: Ensure any submitted PR runs the test suite. The AI should suggest adding tests for new functionality.

### 🔍 5. Code Review & Commit Guidelines
- **Commit messages**: Use imperative mood (`Add`, `Fix`, `Update`). Include ticket IDs if applicable. Keep messages concise but descriptive.
- **PRs**: Describe the problem, solution, and any migration steps. Link to relevant issues. Run `flake8`/`black` and `pytest` locally before requesting review.
- **Review focus areas**: readability, test coverage, adherence to conventions, performance implications, security aspects.

### 🛠️ 6. Debugging & Logging
- Use Python's `logging` module; set loggers per module (`logger = logging.getLogger(__name__)`).
- For async functions, use `logger.debug` liberally when tracing control flow.
- Suggest adding try/except with clear error messages and, if appropriate, re-raising custom exceptions.

### 📦 7. Dependency Management
- Add new libraries to `agent_system/requirements.txt`. Pin versions if stability is required.
- Before adding, check existing imports with `mcp_pylance_mcp_s_pylanceImports` to avoid duplicates.
- Periodically run `pip list --outdated` and propose upgrades when beneficial.

### 🔐 8. Security Considerations
- Validate all external inputs (e.g., task data) using Pydantic models.
- Escape or sanitize any content passed to external services.
- Be cautious with storing secrets; recommend using environment variables or secure vaults.

### 📈 9. Performance & Scalability
- Encourage asynchronous I/O to prevent blocking worker threads.
- Suggest using Redis pub/sub or streams if broadcast volume grows.
- For high-load scenarios, propose scaling worker nodes horizontally and tuning RabbitMQ prefetch counts.

With these additions, the instructions offer a full lifecycle reference—from coding through testing, review, and deployment—ensuring the AI can guide or generate work appropriately across the project.