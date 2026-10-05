# agent-frameworks-lab

A reference implementation of one document question-answering task across six agent and LLM-orchestration frameworks: **LlamaIndex, LangChain, LangGraph, LangSmith, CrewAI, and AutoGen / Microsoft Agent Framework**. Every framework solves the same task against the same data, so differences in state handling, control flow, observability, cost, and latency come from the framework rather than the problem.

## Scope

**Shared task.** Answer questions about a synthetic policy document, citing source chunk IDs, at three levels:

1. **Retrieve and answer** with citations.
2. **Corrective loop:** if retrieved chunks are weak, rewrite the query and retry (bounded to two retries).
3. **Multi-role with approval:** researcher and writer roles, with human approval before the answer is released.

**Cross-cutting concern: state management.** State schema and merge rules, short-term versus long-term memory, persistence and resume after failure, human pause points, and replay. Each framework is exercised against the same crash-and-resume test.

**Measured outputs.** Each implementation records token usage, estimated cost, latency, and pass rate against a golden question set. The final comparison uses these measurements.

**Design principle.** Implementations target current, supported APIs. AutoGen is in maintenance mode, so its concepts are documented briefly and the build target is its successor, Microsoft Agent Framework.

## Stack

- Python, managed with `uv` (`pyproject.toml` and a committed lock file)
- LLM providers: Google Gemini free tier first; local models where practical; OpenAI as a last resort behind a hard spending cap (see [Models and cost](#models-and-cost))
- Frameworks: LlamaIndex, LangChain, LangGraph, LangSmith, CrewAI, Microsoft Agent Framework
- Jupyter notebooks for exploration; scripts and modules for the maintained versions

## Roadmap

### Foundation
- [x] **0** Project setup: `uv`, configuration, provider abstraction, cost meter with a budget cap, shared task definition and golden questions
- [ ] **0b** Logging: standard-library `logging` configured once at the entry point, modules use `logging.getLogger(__name__)`, no `print` in library code, no secrets in log lines
- [ ] **0c** Type checking: type hints on new code and a static type checker as a development dependency, run before each commit (existing Phase 0 files are left as they are)

### LlamaIndex
- [ ] **1** Documents, nodes, metadata, and node parsers (sentence, token, semantic, hierarchical chunking)
- [ ] **2** `VectorStoreIndex`, retrievers versus query engines, response synthesizers, source nodes as citations, index persistence
- [ ] **3** Advanced retrieval: BM25 and vector fusion, rerank postprocessor, metadata filters, query transforms (HyDE, sub-question), router query engine, evaluation modules
- [ ] **4** Workflows: typed events, steps, shared `Context`, branching, loops, parallel steps, streaming, human-in-the-loop, durable runs; function-calling and ReAct agents on Workflows
- [ ] **4b** Managed document processing (LlamaParse) evaluation, subject to free-tier availability

### LangChain
- [ ] **5** Model I/O: chat models, messages, prompt templates, output parsers, structured output, streaming, batch, retries and fallbacks, usage metadata
- [ ] **6** Runnables and LCEL: sequence, parallel, passthrough, lambda, branch; where LCEL fits and where it stops
- [ ] **7** Retrieval and tools: embeddings, vector stores, retrievers, loaders, splitters, tool definition and calling, tool error handling
- [ ] **8** Agents with `create_agent` and middleware: model and tool hooks, prebuilt PII, summarization, and human-approval middleware, a custom citation-check middleware, runtime context, short-term memory, MCP tools

### LangGraph
- [ ] **9** `StateGraph`, state schemas, reducers, conditional edges, compile, invoke and stream modes; corrective retrieval graph
- [ ] **10** Persistence: checkpointers (in-memory, SQLite, Postgres), threads, state history, replay and fork from a checkpoint, `update_state`, crash recovery
- [ ] **11** Human-in-the-loop: `interrupt()`, `Command(resume=...)`, approve/edit/reject, breakpoints, idempotency of resumed nodes
- [ ] **12** Advanced control flow: `Command`, `Send` fan-out, subgraphs, supervisor and handoff patterns, long-term memory `Store`, retry policies, node caching, Functional API, typed streaming
- [ ] **12b** Serving: the LangGraph agent behind FastAPI with an SSE streaming endpoint, a resume endpoint continuing a paused run by `thread_id`, and a SQLite or Postgres checkpointer

### LangSmith
- [ ] **13** Tracing: environment setup, `@traceable`, runs, traces, threads, tags, metadata, cost and latency per step
- [ ] **14** Datasets and offline evaluation: heuristic, LLM-as-judge, pairwise, and custom evaluators; experiments and regression comparison
- [ ] **15** Online evaluation, annotation queues with rubrics, prompt versioning, monitoring; managed deployment options reviewed

### CrewAI
- [ ] **16** Crews: agents, tasks, tools, sequential and hierarchical processes, delegation, structured output, task guardrails
- [ ] **17** Flows and memory: typed flow state, start/listen/router steps, persisted state, human feedback, Crews inside Flows, unified memory, knowledge sources, planning, async execution, checkpointing

### AutoGen and Microsoft Agent Framework
- [ ] **18** AutoGen concepts and lineage (`AssistantAgent`, `GroupChat`, event-driven runtime) and the reasons for the move to Microsoft Agent Framework
- [ ] **19** Microsoft Agent Framework agents: multi-turn tool loop, conversation threads, tools, middleware, model clients
- [ ] **20** Microsoft Agent Framework workflows: graph orchestration, sequential, concurrent, group-chat, handoff, and Magentic patterns, approval steps, A2A and MCP interoperability

### Cross-cutting
- [ ] **21** Interoperability: one retrieval tool exposed as an MCP server and consumed by multiple frameworks
- [ ] **22** State management comparison: schema, merging, memory scopes, persistence, resume, human pause, replay, measured per framework
- [ ] **23** Cost, latency, and quality comparison across all implementations
- [ ] **24** Architecture decision records, onboarding guide, per-framework fit assessment, and a containerized HTTP service around the best-fit implementation
- [ ] **24b** Dependency supply-chain controls: locked installs (`uv sync --locked`), `uv audit` and Dependabot in CI, and a private package mirror pattern (local devpi) documented in an ADR

**Status:** 1 of 30 roadmap items complete.

## Models and cost

Providers are selected in this order, and every run goes through a cost meter that stops at a configured budget:

1. **Google Gemini free tier** (AI Studio key). Free-tier content may be used by the provider to improve its products, so only synthetic data is used.
2. **Local models**, where hardware allows.
3. **OpenAI**, as a last resort, using the cheapest suitable models and a low hard budget cap.

Prices, free-tier limits, and model names change frequently and are verified against current provider documentation before use.

## Configuration

Copy `.env.example` to `.env` and fill in the keys you intend to use. `.env` is git-ignored. Use synthetic data only: LangSmith and CrewAI tracing send traces to third-party services.

## Non-goals

Production deployment, real or sensitive data, and paid managed-platform deployments beyond free-tier evaluation.
