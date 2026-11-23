# Research Summary: Prompting for Structured Output

## Definitions
- **Structured output**: model responses formatted in a machine-readable structure (commonly JSON) that conforms to an expected schema.
- **Schema**: a formal definition of fields, types, required properties, and allowed values for the output.
- **Prompting for structured output**: designing instructions/examples/constraints so an LLM reliably produces schema-conformant data.

## Important Terminologies
- **JSON mode / structured response**: API features that constrain or encourage valid JSON outputs.
- **Function/tool calling**: model returns arguments matching a defined function/schema (provider-dependent).
- **Validation**: checking parsed output against schema/rules (types, ranges, enums, required fields).
- **Repair/retry**: re-prompting with error feedback to fix malformed or invalid outputs.
- **Few-shot example**: providing sample input-output pairs to demonstrate the desired format.
- **Enum**: restricted set of allowed values (e.g. `low|medium|high`).
- **Hallucinated fields/values**: invented keys or out-of-range values not grounded in input/schema.

## Explanations
### Writing prompts that return strict JSON
- Explicitly instruct: return **only valid JSON**, no extra prose (or define how to extract JSON).
- Provide the **exact schema** (field names, types, required/optional) and include a **sample JSON**.
- Constrain values with **enums/ranges** (e.g. scores 0–1, trends `improving|stable|declining`).
- Keep tasks **single-responsibility** and include necessary context; lower temperature can improve consistency.
- Use provider **structured-output/JSON features** when available for higher reliability.

### Validating and retrying when output is malformed
- **Parse safely** (handle code fences/trailing issues where feasible).
- **Validate** with schema tools (e.g. Pydantic/JSON Schema): required fields, types, ranges, enums, ID consistency.
- **Retry with repair**: send back the invalid output and validation error, request corrected JSON; cap retries (e.g. 2–3) to control latency/cost.
- **Fallbacks**: on persistent failure, return safe defaults (e.g. neutral analysis, empty recommendations) and log for review to keep the pipeline responsive.

## Real-World Examples
- **Sentiment classifier**: prompt requires `{"sentiment":"positive|neutral|negative","confidence":0-1}`; invalid confidence like `1.7` triggers validation failure and a repair retry.
- **Entity extraction**: output must be a list of objects with fixed keys; schema validation rejects missing `type` fields.
- **Support intent analysis**: agent returns intent, emotion, frustration level, and rationale in JSON so the UI can render badges and charts without parsing prose.

## How This Applies to Our Project
- **All six agents** must return **structured JSON** so the orchestrator, database, and UI can consume outputs reliably (sample schemas in `docs/design_document.md` Section 6).
- **Orchestration** depends on predictable fields: e.g. Intent & Sentiment feeds Coaching and Escalation; Knowledge Recommendation returns chunk references/scores; Summary Agent returns sentiment journey and resolution score.
- **Implementation approach (Milestones 2+)**: define Pydantic models per agent, validate responses, perform bounded repair retries on malformed JSON, and apply safe fallbacks to maintain real-time behavior.
- **Milestone 1 foundation**: data models and API schemas already use structured representations (sessions, KB results with source/score), aligning the system for strict agent JSON contracts in later milestones.
