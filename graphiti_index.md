# Graphiti In-Depth: The Complete Developer's Handbook — INDEX

> **Proposed table of contents for review. No content has been written yet — this is just the outline.**

---

## PART 0: FOUNDATIONS

### Chapter 0 — Preface & Who This Guide Is For
- Target audience (AI engineers hitting RAG limits, agent builders)
- Prerequisites (Python 3.10+, async/await, basic LLM concepts)
- What you'll build (25 workable examples)
- How this guide is structured

### Chapter 1 — What Problem Graphiti Solves
- The "stale facts" problem — RAG retrieves old and new facts equally
- The "when was this true?" problem — vector search has no notion of time
- The "what changed?" problem — no audit trail of fact evolution
- Why temporal knowledge graphs are the answer

### Chapter 2 — Graphiti vs RAG vs GraphRAG vs Cognee: Architectural Positioning
- The memory systems spectrum
- Comparison table: retrieval method, temporal support, ingestion model, accuracy ceiling
- Decision flowchart: Should I use Graphiti?
- Where Graphiti fits and where it doesn't

---

## PART 1: CORE CONCEPTS & ARCHITECTURE

### Chapter 3 — The Three-Layer Knowledge Graph Architecture
- Layer 1: Episodic Memory (EpisodicNode) — raw episodes with provenance
- Layer 2: Entity Knowledge (EntityNode + EntityEdge) — deduplicated entities and facts
- Layer 3: Community Clusters (CommunityNode) — groups of semantically related entities
- How the layers interact during ingestion and retrieval
- **Example 1: Hello Graphiti** (`01_hello_graphiti.py`)

### Chapter 4 — The Bi-Temporal Data Model (Deep Dive)
- `valid_at` / `invalid_at` — event time: when facts were true in reality
- `created_at` / `expired_at` — system time: when facts were ingested/superseded
- Why two time dimensions matter
- Point-in-time queries: "what did we know in January?"
- Fact lifecycle: birth → active → contradicted → expired (never deleted)
- **Example 2: Bi-Temporal Facts** (`02_bitemporal_facts.py`)

### Chapter 5 — Episode-Based Ingestion
- Episodes as the atomic unit of ingestion
- EpisodeType: `message`, `json`, `text`, `fact_triple`
- The ingestion pipeline: context retrieval → node resolution → edge resolution → community update
- Incremental processing — no full graph recomputation
- `EPISODE_WINDOW_LEN` and temporal context
- **Example 3: Episode Ingestion Patterns** (`03_episode_patterns.py`)

### Chapter 6 — Entity & Relationship Extraction Pipeline
- Step-by-step walkthrough of the extraction pipeline
- Node resolution: exact match → fuzzy similarity → LLM reasoning
- Edge resolution: relationship extraction + contradiction detection
- Combined extraction (v0.29.0): single LLM call for nodes + edges
- Multi-episode batching
- Confidence scores and deduplication
- **Example 4: Extraction Pipeline** (`04_extraction_pipeline.py`)

### Chapter 7 — Hybrid Search Architecture
- Three retrieval strategies: semantic embeddings + BM25 full-text + graph traversal
- Reciprocal Rank Fusion (RRF) for merging results
- Node-distance reranking with `center_node_uuid`
- Cross-encoder reranking
- Built-in search recipes (`COMBINED_HYBRID_SEARCH_CROSS_ENCODER`, `EDGE_HYBRID_SEARCH_RRF`, etc.)
- SearchConfig and SearchFilters
- **Example 5: Search Strategies** (`05_search_strategies.py`)

---

## PART 2: API DEEP DIVE

### Chapter 8 — The Graphiti Class: Construction & Configuration
- Constructor parameters: `uri`, `user`, `password`, `llm_client`, `embedder`, `cross_encoder`, `graph_driver`
- `max_coroutines` and concurrency control
- `store_raw_episode_content` trade-off
- `build_indices_and_constraints()`
- Lifecycle: create → use → close
- **Example 6: Graphiti Configuration** (`06_configuration.py`)

### Chapter 9 — Episode API (`add_episode` / `add_episode_bulk`)
- Complete function signatures
- Single episode ingestion with `add_episode()`
- Bulk ingestion with `add_episode_bulk()`
- `group_id` for multi-tenant/namespace isolation
- `reference_time` and temporal anchoring
- Queue system: per-group sequential processing
- Return values and error handling
- **Example 7: Episode API Workflow** (`07_episode_api.py`)

### Chapter 10 — Search API (`search` / `search_`)
- `search()` — basic hybrid search returning EntityEdge objects
- `search_()` — advanced search with SearchConfig
- Search filters: temporal, label-based, group-scoped
- `center_node_uuid` for graph-proximity ranking
- `num_results` and pagination
- Interpreting SearchResults (nodes, edges, episodes, communities)
- **Example 8: Search API Deep Dive** (`08_search_api.py`)

### Chapter 11 — Custom Entities with Pydantic
- Defining domain-specific entity types
- Custom edge types for typed relationships
- How the LLM uses your Pydantic models as extraction schema
- Built-in custom types: Preference, Procedure, Requirement
- Extending with your own types (Location, Event, Organization, Product, etc.)
- **Example 9: Custom Entities** (`09_custom_entities.py`)

### Chapter 12 — Community Detection & Graph Analysis
- `build_communities()` — when and how it runs
- Label propagation algorithm
- LLM-based community summarization
- Using communities to improve retrieval
- CommunityNode properties
- **Example 10: Community Detection** (`10_communities.py`)

### Chapter 13 — MCP Server
- What the MCP server exposes as tools
- Tool reference: `add_episode`, `search_nodes`, `search_facts`, `get_episodes`, `delete_entity_edge`, `clear_graph`
- Setup with Claude Desktop, Cursor, VS Code
- Environment configuration
- Transport options: stdio, SSE, Streamable HTTP
- **Example 11: MCP Server Setup** (`11_mcp_server/`)

### Chapter 14 — REST API Server
- FastAPI-based REST service
- Endpoint reference: `/ingest/messages`, `/ingest/entity-node`, `/retrieve/search`, `/retrieve/get-memory`
- Authentication patterns
- **Example 12: REST API Client** (`12_rest_api.py`)

---

## PART 3: ADVANCED FEATURES

### Chapter 15 — Temporal Reasoning & Point-in-Time Queries
- Querying facts as they existed at a specific time
- Tracking fact evolution over time
- The `valid_at` / `invalid_at` filter in searches
- Auditing "what changed between Q1 and Q2?"
- **Example 13: Temporal Queries** (`13_temporal_queries.py`)

### Chapter 16 — Contradiction Handling & Fact Expiration
- How Graphiti detects contradictory facts
- The expiration process: old edges marked `expired_at`, not deleted
- Confidence-based contradiction resolution
- Manual fact invalidation
- **Example 14: Contradiction Handling** (`14_contradictions.py`)

### Chapter 17 — Multi-Provider Plugin Architecture
- LLM clients: OpenAI, Azure OpenAI, Anthropic, Google Gemini, Groq, Ollama
- Embedders: OpenAI, Voyage, Cohere, local options
- Cross-encoders / rerankers
- Graph drivers: Neo4j, FalkorDB, Kuzu, Amazon Neptune
- How to swap providers at construction time
- **Example 15: Multi-Provider Setup** (`15_multi_provider.py`)

### Chapter 18 — Graph Database Backends
- Neo4j: primary/recommended (5.26+)
- FalkorDB: lighter alternative (1.1.2+)
- Kuzu: embedded, zero-dependency option (0.11.2+)
- Amazon Neptune: cloud option + OpenSearch Serverless
- Backend selection guide and trade-offs
- **Example 16: FalkorDB Backend** (`16_falkordb_backend.py`)

### Chapter 19 — Saga Abstraction & Narrative Rollups
- `summarize_saga(saga_id)` — what it does and when to use it
- Rolling up multi-episode narratives
- Saga vs Episode vs Community
- **Example 17: Saga Summarization** (`17_saga_summarization.py`)

### Chapter 20 — Combined Extraction & Bulk Processing
- Combined node + edge extraction (single LLM call)
- Multi-episode batching for throughput
- Decoupled timestamp resolution
- Performance benchmarks and trade-offs
- **Example 18: Bulk & Combined Extraction** (`18_bulk_combined.py`)

### Chapter 21 — Observability & LLM Cost Tracking
- Tracing episode processing latency
- LLM token usage monitoring
- Graph DB query performance
- OpenTelemetry integration patterns
- **Example 19: Observability** (`19_observability.py`)

---

## PART 4: REAL-WORLD USE CASES

### Chapter 22 — Customer Support Agent with Temporal Memory
- Scenario: support agent that remembers user history across sessions
- Ingesting support tickets, chat transcripts, knowledge base articles
- Temporal queries: "what issues did this user have last month?"
- Multi-hop: "which solutions worked for similar issues?"
- **Example 20: Support Agent** (`20_support_agent.py`)

### Chapter 23 — Personal Assistant with Preference Learning
- Scenario: AI assistant that learns user preferences over time
- Preference extraction with custom entity types
- Tracking changing preferences ("used to like X, now prefers Y")
- Procedure memory for repeated workflows
- **Example 21: Personal Assistant** (`21_personal_assistant.py`)

### Chapter 24 — Research & Knowledge Management
- Scenario: tracking research findings, papers, and evolving conclusions
- Ingesting paper summaries, experimental results
- Tracking "what was the consensus before paper X?"
- Community detection for research clusters
- **Example 22: Research Knowledge** (`22_research_knowledge.py`)

### Chapter 25 — Multi-Agent Collaboration Memory
- Scenario: shared memory across multiple AI agents
- `group_id`-based agent isolation with shared groups
- Cross-agent fact discovery
- Conflict resolution when agents disagree
- **Example 23: Multi-Agent Memory** (`23_multi_agent.py`)

### Chapter 26 — Codebase Evolution Tracking
- Scenario: tracking how a codebase changes over releases
- Entities: modules, classes, functions, APIs
- Temporal edges: "deprecated_in", "replaced_by", "introduced_in"
- Querying: "what broke when we changed this API?"
- **Example 24: Code Evolution** (`24_code_evolution.py`)

---

## PART 5: DEPLOYMENT & PRODUCTION

### Chapter 27 — Local Development
- Neo4j Desktop setup
- Docker Compose for local Graphiti + Neo4j
- Using Kuzu for zero-dependency development
- Ollama for fully local LLMs
- **Example 25: Local Dev Setup** (`25_local_dev/`)

### Chapter 28 — Production Deployment
- Docker Compose for production (Neo4j + Graphiti + MCP)
- Kubernetes considerations
- Zep Cloud vs self-hosted decision guide
- Neo4j replication and backups
- Health checks and monitoring
- **Example 26: Production Docker** (`26_production_docker/`)

### Chapter 29 — Scaling Strategies
- Parallel episode processing across groups
- Redis caching for frequent subgraphs
- Separating vector search from graph traversal (Zep's production pattern)
- LLM cost optimization: classical NLP fallbacks, prompt compression
- Scaling benchmarks and numbers
- **Example 27: Scaling Guide** (`27_scaling_guide.md`)

### Chapter 30 — Security, Multi-Tenancy & Compliance
- `group_id` for data isolation
- Neo4j authentication and network security
- API key management for LLM providers
- PII considerations
- GDPR: right-to-erasure via `delete_episode` / `clear_graph`
- SOC 2 / HIPAA (Zep Cloud vs self-hosted)
- **Example 28: Security Configuration** (`28_security.md`)

---

## PART 6: ARCHITECTURAL DECISIONS & TRADEOFFS

### Chapter 31 — Why Bi-Temporal? (Event Time vs System Time)
- The problem with single-timeline systems
- How bi-temporality enables audit trails and point-in-time queries
- The storage cost of keeping expired edges
- When bi-temporal is overkill

### Chapter 32 — Episode-Based vs Batch Processing
- Why episodes instead of document chunks
- Provenance: every fact traces back to its source episode
- The cost: more LLM calls for small updates
- When batch processing would be better

### Chapter 33 — Hybrid Search Rationale
- Why one retrieval method isn't enough
- Semantic: great for meaning, misses exact matches
- BM25: great for keywords, misses paraphrases
- Graph traversal: great for relationships, needs a starting point
- The RRF fusion approach and why it works

### Chapter 34 — LLM Dependency in Extraction: The Double-Edged Sword
- Why LLMs for entity extraction (vs classical NER)
- The structured output dependency
- Costs and latency implications
- Zep's production optimization: replacing LLM calls with classical NLP where possible

### Chapter 35 — Graph DB Choice: Neo4j vs FalkorDB vs Kuzu
- Neo4j: mature, feature-rich, operational overhead
- FalkorDB: Redis-based, lower latency, simpler ops
- Kuzu: embedded, zero-dependency, single-user
- Decision matrix

### Chapter 36 — Graphiti vs Building Your Own: Build vs Buy
- What Graphiti gives you (that you'd build yourself)
- Total DIY estimate
- When NOT to use Graphiti

---

## PART 7: PROS & CONS — THE HONEST ASSESSMENT

### Chapter 37 — Pros: Where Graphiti Shines
1. Temporal reasoning — only framework with true bi-temporal fact tracking
2. Incremental updates — no batch recomputation needed
3. Sub-second hybrid retrieval — semantic + BM25 + graph + rerank without LLM at query time
4. Fact provenance — every edge traces back to its source episode
5. Contradiction handling — old facts expired, not deleted; audit trail preserved
6. Multi-provider flexibility — swap LLMs, embedders, and graph DBs
7. Production battle-tested — Zep's 30x scaling story
8. MCP-native — first-class AI assistant integration
9. SDK breadth — Python, TypeScript, Go
10. Open source (Apache 2.0) with managed cloud option

### Chapter 38 — Cons & Gotchas
1. Graph DB dependency — must run and manage Neo4j/FalkorDB (operational complexity)
2. LLM costs at ingest — every episode triggers LLM calls for extraction
3. Not for static document corpora — GraphRAG/Cognee better for batch document processing
4. Limited multimodal support — text-focused; no native PDF/image/audio ingestion
5. Pre-1.0 — API still evolving; breaking changes possible
6. LongMemEval 63.8% — good but not best-in-class (Hindsight scores 91.4%)
7. Cold-start — needs episodes to build meaningful graph structure
8. Overkill for simple chat memory — use a buffer or vector store for basic use cases
9. No built-in visualization — must build your own graph UI
10. Self-hosting ≠ Zep Cloud — the managed platform has features (dashboard, analytics) absent from OSS Graphiti

### Chapter 39 — Comparison Matrix
| Feature | Graphiti | Cognee | MS GraphRAG | Mem0 | Hindsight | LlamaIndex |
|---|---|---|---|---|---|---|
| Knowledge Graph | Temporal KG | Poly-store KG | Communities | Vector + Graph (Pro) | Multi-strategy | PropertyGraph |
| Temporal Reasoning | Bi-temporal | Metadata only | Basic timestamps | No | Yes | No |
| Vector Search | Yes | Yes | Yes | Yes | Yes | Yes |
| Session Memory | Episode model | V2 API | No | Yes | Yes | No |
| Multi-Modal | Text-focused | Images/Audio/Video | Text only | No | No | Yes |
| Data Connectors | Episode-only | 30+ formats | Text only | API-based | Episode-based | 20+ |
| SDK Languages | Python, TS, Go | Python | Python | Python, TS | Python | Python, TS |
| Self-Hosted | Yes (Neo4j req) | Yes | Yes | Yes (Docker) | Yes (Docker) | Yes |
| Managed Cloud | Zep Cloud | Cognee Cloud | No | Yes | Yes | LlamaCloud |
| LongMemEval | 63.8% | Not published | Not published | 49.0% | 91.4% | Not published |
| License | Apache 2.0 | Apache 2.0 | MIT | Apache 2.0 | MIT | MIT |

---

## APPENDICES

### Appendix A — Quick Reference Card
- Graphiti constructor
- `add_episode()` / `add_episode_bulk()` signatures
- `search()` / `search_()` signatures
- `build_communities()` usage
- `retrieve_episodes()` usage
- EpisodeType enum
- SearchType recipes
- Custom entity Pydantic pattern

### Appendix B — Troubleshooting Common Issues
- Neo4j connection failures
- LLM rate limiting during bulk ingestion
- Empty search results
- Duplicate entities
- Memory/timeout issues with large episodes
- Kuzu file locking
- Community detection not running

### Appendix C — Configuration Reference
- All Graphiti constructor parameters
- Environment variables
- Neo4j settings
- LLM provider configuration
- Embedder configuration

### Appendix D — Glossary
- Episode, Entity, Community, Saga
- Bi-temporal, valid_at, invalid_at, expired_at
- RRF (Reciprocal Rank Fusion)
- Node resolution, Edge resolution
- group_id, reference_time
- Label propagation

### Appendix E — Migration Guide: Zep Community Edition → Raw Graphiti
- What was deprecated and when
- Session → Thread, Group → Graph mapping
- API differences
- Data migration strategies

### Appendix F — Further Reading & Resources
- Zep paper (arXiv:2501.13956)
- GitHub repository
- Official documentation
- Community projects and forks
- Benchmarks

---

## Summary of Examples (28 total)

| # | Chapter | File | What It Demonstrates |
|---|---|---|---|
| 1 | Ch.3 | `01_hello_graphiti.py` | Minimal working Graphiti: add episode, search |
| 2 | Ch.4 | `02_bitemporal_facts.py` | Facts evolving over time with valid_at/invalid_at |
| 3 | Ch.5 | `03_episode_patterns.py` | Message, text, JSON, fact_triple episode types |
| 4 | Ch.6 | `04_extraction_pipeline.py` | Entity & relationship extraction in detail |
| 5 | Ch.7 | `05_search_strategies.py` | Semantic, BM25, graph traversal, RRF, reranking |
| 6 | Ch.8 | `06_configuration.py` | All constructor options and their effects |
| 7 | Ch.9 | `07_episode_api.py` | add_episode, add_episode_bulk, group_id isolation |
| 8 | Ch.10 | `08_search_api.py` | search vs search_, filters, center_node_uuid |
| 9 | Ch.11 | `09_custom_entities.py` | Pydantic custom entity & edge types |
| 10 | Ch.12 | `10_communities.py` | Community detection, label propagation |
| 11 | Ch.13 | `11_mcp_server/` | MCP server setup with Claude Desktop config |
| 12 | Ch.14 | `12_rest_api.py` | REST API client examples |
| 13 | Ch.15 | `13_temporal_queries.py` | Point-in-time queries, fact evolution tracking |
| 14 | Ch.16 | `14_contradictions.py` | Fact expiration, contradiction resolution |
| 15 | Ch.17 | `15_multi_provider.py` | Anthropic, Ollama, Gemini provider setups |
| 16 | Ch.18 | `16_falkordb_backend.py` | FalkorDB as graph driver |
| 17 | Ch.19 | `17_saga_summarization.py` | summarize_saga API |
| 18 | Ch.20 | `18_bulk_combined.py` | Combined extraction + bulk episode processing |
| 19 | Ch.21 | `19_observability.py` | Tracing, token tracking, performance monitoring |
| 20 | Ch.22 | `20_support_agent.py` | Customer support agent with temporal memory |
| 21 | Ch.23 | `21_personal_assistant.py` | Preference learning personal assistant |
| 22 | Ch.24 | `22_research_knowledge.py` | Research paper tracking & knowledge management |
| 23 | Ch.25 | `23_multi_agent.py` | Shared memory across multiple agents |
| 24 | Ch.26 | `24_code_evolution.py` | Codebase change tracking over releases |
| 25 | Ch.27 | `25_local_dev/` | Docker Compose + Ollama fully local setup |
| 26 | Ch.28 | `26_production_docker/` | Production Neo4j + Graphiti + health checks |
| 27 | Ch.29 | `27_scaling_guide.md` | Scaling strategies, benchmarks, Redis caching |
| 28 | Ch.30 | `28_security.md` | Security hardening, multi-tenancy, compliance |

---

> **This is the proposed index.** It covers ~39 chapters across 7 parts + 6 appendices, with 28 workable examples. The structure mirrors the Cognee handbook for consistency but is tailored to Graphiti's unique features (bi-temporal model, episode-based ingestion, hybrid search, saga abstraction, MCP-native design).
>
> Please review and let me know what you'd like to add, remove, or restructure before I start writing the full tutorial.
