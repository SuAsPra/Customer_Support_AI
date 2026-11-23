# Research Summary: Multi-Agent Design Patterns

## Definitions
- **AI agent (in this context)**: a component that uses an LLM (and/or tools like retrieval) with a specific role/prompt to perform a focused task and return a result.
- **Multi-agent system**: a system composed of multiple specialized agents that collaborate to solve a larger problem.
- **Orchestrator**: the coordinating logic that determines which agents run, in what order, with what inputs, and how outputs are combined.

## Important Terminologies
- **Single responsibility**: each agent handles one well-defined capability.
- **Structured I/O**: agents exchange data via defined schemas (e.g. JSON) rather than free-form text.
- **Sequential execution**: running agents in order when outputs are dependencies.
- **Parallel execution**: running independent agents concurrently to reduce latency.
- **DAG (Directed Acyclic Graph)**: dependency graph representing execution order/branches.
- **Shared state**: common context (session config, conversation history, artifacts) accessible to agents/orchestrator.
- **Idempotency/traceability**: ability to track outputs by IDs (session/message/turn) and reason about runs.
- **Fallback/retry**: strategies to handle agent failures or invalid outputs.

## Explanations
### Single-responsibility agents
- Narrow scope simplifies prompts, improves reliability, enables targeted evaluation, and isolates failures. Each agent can evolve independently.

### Structured inputs and outputs
- Explicit schemas (fields, types, enums) allow validation, persistence, UI rendering, and reliable downstream use. Outputs should include identifiers (e.g. `message_id`) for linkage.

### Sequential vs parallel execution
- **Parallel** when tasks are independent (e.g. analyze intent/sentiment and retrieve KB for the same message).
- **Sequential** when one task needs another's result (e.g. coaching suggestions need analysis and retrieved knowledge).
- Real systems often use hybrid pipelines: parallel stages joined at dependency points.

### Orchestration
- Central orchestrator manages invocation, context passing, parallelism, aggregation, timeouts, retries, and logging. For real-time UX, minimizing latency via safe parallelism is important.

### Shared state
- Maintain conversation history, session configuration, and per-turn outputs in durable storage and/or in-memory caches. Use consistent IDs and avoid hidden coupling; pass only necessary context to each agent.

## Real-World Examples
- **Customer support copilot**: one agent classifies intent/sentiment, another retrieves policy snippets, a third drafts a response, and a fourth checks compliance/tone—coordinated per message.
- **Document QA system**: retriever agent fetches passages while a reasoning agent answers; a verifier agent checks citations.
- **Workflow automation**: planner agent decomposes tasks, tool agents execute actions, critic agent validates results before finalizing.

## How This Applies to Our Project
- Six specialized agents with clear responsibilities: **Customer Simulator**, **Intent & Sentiment Analysis**, **Knowledge Recommendation (RAG)**, **Coaching & Response Suggestion**, **Escalation Risk Monitor**, **Post-Interaction Summary** (specs and sample JSON in `docs/design_document.md`).
- **Per-turn orchestration**: ingest message → run **Intent & Sentiment** and **Knowledge Recommendation** in parallel → run **Coaching** and **Escalation Risk** in parallel once inputs ready → persist/publish results to UI; trigger alert on high risk. **Simulator** generates next customer message on demand in simulator mode.
- **End-of-session orchestration**: run **Post-Interaction Summary** on full history and all per-turn outputs to produce the report.
- **Shared state**: session config, messages, and turn artifacts stored in the relational DB (scaffolded models) and linked by `session_id`/`message_id`/turn; vector DB holds KB chunks.
- This design supports Milestone 1 foundations (session/RAG modules) and scales to Milestones 2–4 by adding agent implementations behind the same structured contracts.
