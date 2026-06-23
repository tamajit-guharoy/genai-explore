# Appendix — Reference, Cookbook & Glossary

## A. Full API Reference

### Base URL
```
http://localhost:8888
```

### Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API + database health check |
| GET | `/version` | API version and feature flags |
| GET | `/metrics` | Prometheus metrics |

### Memory Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/default/banks/{bank_id}/memories` | Retain memories |
| POST | `/v1/default/banks/{bank_id}/memories/recall` | Recall memories |
| POST | `/v1/default/banks/{bank_id}/memories/dry-run-extract` | Preview extraction |
| POST | `/v1/default/banks/{bank_id}/reflect` | Reflect/generate answer |
| GET | `/v1/default/banks/{bank_id}/memories/list` | List memories |
| GET | `/v1/default/banks/{bank_id}/memories/{id}` | Get single memory |
| PATCH | `/v1/default/banks/{bank_id}/memories/{id}` | Update/curate memory |
| GET | `/v1/default/banks/{bank_id}/memories/{id}/history` | Observation history |
| DELETE | `/v1/default/banks/{bank_id}/memories/{id}/observations` | Clear observations |
| DELETE | `/v1/default/banks/{bank_id}/memories` | Delete all memories |

### Bank Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/default/banks` | List all banks |
| PUT | `/v1/default/banks/{bank_id}` | Create/update bank |
| PATCH | `/v1/default/banks/{bank_id}` | Partial update bank |
| DELETE | `/v1/default/banks/{bank_id}` | Delete bank (irreversible) |
| GET | `/v1/default/banks/{bank_id}/stats` | Bank statistics |
| POST | `/v1/default/banks/{bank_id}/health/llm` | LLM health probe |
| GET | `/v1/default/banks/{bank_id}/stats/memories-timeseries` | Ingestion timeline |

### Tags, Graph & Scopes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/default/banks/{bank_id}/tags` | List tags |
| GET | `/v1/default/banks/{bank_id}/graph` | Entity graph data |
| GET | `/v1/default/banks/{bank_id}/observations/scopes` | Observation scopes |

---

## B. Python Client Quick Reference

### Installation
```bash
pip install hindsight-client
```

### Client Init
```python
from hindsight_client import Hindsight
client = Hindsight(base_url="http://localhost:8888", timeout=30.0, api_key=None)
```

### Operations Cheat Sheet

```python
# === Core ===
client.retain(bank_id, content, context=None, timestamp=None, document_id=None, metadata=None, retain_async=False)
client.retain_batch(bank_id, items, document_id=None, retain_async=False)
client.dry_run_extract(bank_id, content)

client.recall(bank_id, query, types=None, max_tokens=None, budget="mid", tags=None, tags_match="any", metadata_filter=None, include_chunks=False, max_chunk_tokens=500, include_entities=False, trace=False)
client.reflect(bank_id, query, budget="mid", max_tokens=4096, context=None, tags=None, tag_groups=None, fact_types=None, exclude_mental_models=False, exclude_mental_model_ids=None, response_schema=None)

# === Banks ===
client.create_bank(bank_id, name=None, reflect_mission=None, retain_mission=None, retain_extraction_mode="standard", retain_custom_instructions=None, retain_chunk_size=None, retain_structured_chunk_size=None, enable_observations=True, observations_mission=None, disposition=None, directives=None)
client.update_bank(bank_id, **kwargs)  # Partial update
client.list_banks()
client.get_bank_stats(bank_id)
client.check_bank_llm_health(bank_id)
client.delete_bank(bank_id)

# === Memory Management ===
client.list_memories(bank_id, type=None, search_query=None, limit=100, offset=0)
client.get_memory(bank_id, memory_id)
client.update_memory(bank_id, memory_id, text=None, context=None, state=None, reason=None)
client.delete_memories(bank_id, types=None)
client.get_memory_history(bank_id, memory_id)
client.clear_memory_observations(bank_id, memory_id)
client.get_memory_timeseries(bank_id, period="7d")

# === Mental Models ===
client.create_mental_model(bank_id, name, content, tags=None)
client.update_mental_model(bank_id, mental_model_id, content=None, name=None, tags=None)
client.list_mental_models(bank_id)
client.delete_mental_model(bank_id, mental_model_id)

# === Graph & Tags ===
client.get_graph(bank_id, type=None, tags=None)
client.list_tags(bank_id, search=None, source=None)
client.get_observation_scopes(bank_id)

# === Async ===
# All methods have async versions: aretain(), arecall(), areflect(), etc.
async with Hindsight(base_url="...") as client:
    await client.aretain(...)
```

---

## C. Cookbook Links

| Recipe | Description | URL |
|--------|-------------|-----|
| Quickstart | retain, recall, reflect basics | https://hindsight.vectorize.io/cookbook/quickstart |
| Per-User Memory | Metadata-based user isolation | https://hindsight.vectorize.io/cookbook/per-user-memory |
| Support Agent | Shared knowledge + per-user memory | https://hindsight.vectorize.io/cookbook/support-agent |
| LiteLLM Memory | Automatic memory via callbacks | https://hindsight.vectorize.io/cookbook/litellm |
| Routing Tool Learning | LLM learns which tool to use | https://hindsight.vectorize.io/cookbook/routing-tool |
| Fitness Coach | Personalized workout tracking | https://hindsight.vectorize.io/cookbook/fitness-coach |
| Healthcare Assistant | Patient history memory | https://hindsight.vectorize.io/cookbook/healthcare |
| Movie Recommendations | Preference learning | https://hindsight.vectorize.io/cookbook/movie-recommendations |
| Personal AI Assistant | General life context memory | https://hindsight.vectorize.io/cookbook/personal-assistant |
| Study Buddy | Learning progress tracking | https://hindsight.vectorize.io/cookbook/study-buddy |

---

## D. Glossary

| Term | Definition |
|------|-----------|
| **Bank** | Top-level memory container. One bank per user/agent/project. |
| **World Fact** | Objective fact about the world. "Alice works at Google." |
| **Experience Fact** | Agent's own actions. "I recommended Python to Bob." |
| **Observation** | Auto-consolidated knowledge from multiple related facts. |
| **Mental Model** | User-curated knowledge. Highest priority in reflect(). |
| **Opinion** | Subjective belief with confidence score, formed during reflect(). |
| **Retain** | Store new information in a bank. |
| **Recall** | Search memories using TEMPR multi-strategy retrieval. |
| **Reflect** | Reason over memories to generate an answer. |
| **TEMPR** | The 4-strategy retrieval system: T(emporal) + E(ntity Graph) + M(etadata) + P(arallel)? Actually: Semantic + Keyword + Graph + Temporal. |
| **RRF** | Reciprocal Rank Fusion — merges ranked results from multiple strategies. |
| **Cross-Encoder** | Reranker model that scores (query, document) pairs for final ordering. |
| **Disposition** | Personality traits (skepticism, literalism, empathy) influencing reflect(). |
| **Directives** | Hard guardrail rules that must never be violated during reflect(). |
| **Mission** | Bank's identity statement — what knowledge to prioritize. |
| **Consolidation** | Automatic process that merges related facts into observations. |
| **Entity Graph** | Network of entities and relationships extracted from facts. |
| **pgvector** | PostgreSQL extension for vector similarity search. |
| **pgvectorscale** | DiskANN-based vector extension — 28× lower latency at scale. |
| **BM25** | Okapi BM25 — keyword-based retrieval algorithm. |
| **Chunk** | Segments of original text stored alongside extracted facts. |
| **Metadata** | Custom key-value pairs on memories for filtering and isolation. |
| **Document ID** | Groups related retains (e.g., all turns in one conversation). |

---

## E. Environment Variables Quick Reference

| Variable | Purpose | Default |
|----------|---------|---------|
| `HINDSIGHT_API_LLM_PROVIDER` | LLM provider name | `openai` |
| `HINDSIGHT_API_LLM_API_KEY` | LLM API key | — |
| `HINDSIGHT_API_LLM_MODEL` | LLM model name | `gpt-5-mini` |
| `HINDSIGHT_API_LLM_BASE_URL` | Custom LLM endpoint | provider default |
| `HINDSIGHT_API_LLM_MAX_CONCURRENT` | Max concurrent LLM calls | `32` |
| `HINDSIGHT_API_LLM_REASONING_EFFORT` | Reasoning effort level | `low` |
| `HINDSIGHT_API_DATABASE_URL` | PostgreSQL connection | `pg0` (embedded) |
| `HINDSIGHT_API_READ_DATABASE_URL` | Read replica URL | — |
| `HINDSIGHT_API_VECTOR_EXTENSION` | pgvector/pgvectorscale/vchord/scann | `pgvector` |
| `HINDSIGHT_API_TEXT_SEARCH_EXTENSION` | native/vchord/pgroonga/pg_search | `native` |
| `HINDSIGHT_API_WORKER_ID` | Stable worker identity | container hostname |
| `HINDSIGHT_API_HOST` | Bind address | `0.0.0.0` |
| `HINDSIGHT_API_PORT` | Server port | `8888` |
| `HINDSIGHT_API_KEY` | API authentication key | — |
| `HINDSIGHT_DB_PASSWORD` | PostgreSQL password (Docker Compose) | — |

---

## F. Supported LLM Providers

| Provider | `LLM_PROVIDER` value | Notes |
|----------|---------------------|-------|
| OpenAI | `openai` | GPT-4o, GPT-4o-mini, GPT-5-mini |
| Anthropic | `anthropic` | Claude Opus, Sonnet, Haiku |
| Google Gemini | `gemini` | Gemini 2.5 Flash/Pro |
| Groq | `groq` | Llama 4, Mixtral |
| Ollama | `ollama` | Local models |
| LM Studio | `lmstudio` | Local models |
| OpenRouter | `openrouter` | 200+ models |
| DeepSeek | `deepseek` | DeepSeek-V3, R1 |
| xAI | `xai` | Grok |
| AWS Bedrock | `bedrock` | Claude, Llama on AWS |
| Azure Foundry | `azure_foundry` | Azure-hosted models |
| Vertex AI | `vertexai` | Google Cloud models |
| Fireworks | `fireworks` | Fast inference |
| Custom | `litellm` | Any LiteLLM-compatible endpoint |
| Local | `llamacpp` | Built-in llama.cpp (Gemma 4 E2B) |

---

## G. Resources

- **GitHub**: https://github.com/vectorize-io/hindsight
- **Documentation**: https://hindsight.vectorize.io
- **Cookbook**: https://hindsight.vectorize.io/cookbook
- **API Reference**: https://hindsight.vectorize.io/api-reference
- **Research Paper**: https://arxiv.org/abs/2512.12818
- **Hindsight Cloud**: https://ui.hindsight.vectorize.io/signup
- **Benchmarks**: https://benchmarks.hindsight.vectorize.io
- **Slack Community**: https://join.slack.com/t/hindsight-space/shared_invite/...
- **Integrations Hub**: https://hindsight.vectorize.io/integrations
