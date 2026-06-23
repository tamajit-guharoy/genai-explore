#!/usr/bin/env python3
"""Batch-generate all 10 Supermemory tutorial Jupyter notebooks + 3 example scripts."""
import json, os

BASE_NB = "/c/Users/guhar/ws/calude_tutorial/supermemory/notebooks"
BASE_EX = "/c/Users/guhar/ws/calude_tutorial/supermemory/examples"
os.makedirs(BASE_NB, exist_ok=True)
os.makedirs(BASE_EX, exist_ok=True)

M, C = "markdown", "code"

def nb_save(name, cells):
    nb = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.9.0"}
        },
        "cells": [{"cell_type": ct, "metadata": {}, "source": sl, "outputs": []} for ct, sl in cells]
    }
    with open(os.path.join(BASE_NB, name), "w") as f:
        json.dump(nb, f, indent=1)
    print(f"  OK  {name}")

def py_save(name, content):
    with open(os.path.join(BASE_EX, name), "w") as f:
        f.write(content)
    print(f"  OK  examples/{name}")

# ════════════════════════════════════════════════════
# NOTEBOOK 01: Introduction & Setup
# ════════════════════════════════════════════════════

nb_save("01_introduction_and_setup.ipynb", [

(M, ["# 01 -- Introduction & Setup\n", "\n",
     "## What We'll Cover\n",
     "1. What Supermemory is (the mental model)\n",
     "2. Getting an API key\n",
     "3. Installing the Python SDK\n",
     "4. Creating your first client\n",
     "5. Understanding the architecture\n",
     "6. Verifying connectivity\n"]),

(M, ["## 1.1 What Is Supermemory?\n", "\n",
     "Supermemory is a **memory and context engine** for AI agents. "
     "It solves the \"Goldfish Memory\" problem -- AI systems forgetting everything "
     "between conversations. Think of it as a **living knowledge graph** -- "
     "not a static document store.\n", "\n",
     "### Key Insight\n",
     "A 50-page PDF isn't just stored; it's broken into hundreds of interconnected "
     "memories, each understanding context and relationships to your other knowledge.\n", "\n",
     "### Core Capabilities\n",
     "| Capability | What It Does |\n",
     "|------------|-------------|\n",
     "| Memory Extraction | Reads conversations/docs and extracts meaningful facts |\n",
     "| User Profiles | Auto-builds static (long-term) and dynamic (recent) user context |\n",
     "| Hybrid Search | Vector + keyword search with sub-300ms latency |\n",
     "| Graph Relationships | Connects memories: updates, extends, derives |\n",
     "| Auto-Forgetting | Expired/temporary facts decay automatically |\n",
     "| Connectors | Google Drive, Notion, Gmail, OneDrive, GitHub sync |\n"]),

(M, ["## 1.2 Getting an API Key\n", "\n",
     "1. Go to **console.supermemory.ai** and sign up\n",
     "2. Navigate to **API Keys** -> **Create API Key**\n",
     "3. Name it and optionally set an expiry\n",
     "4. Copy the key -- it starts with `sm_`\n", "\n",
     "**Free Tier:** 100K tokens stored at no cost. Full API access.\n", "\n",
     "**Alternative:** Self-host for free (covered in Notebook 08):\n",
     "```bash\n",
     "curl -fsSL https://supermemory.ai/install | bash\n",
     "```\n"]),

(C, ["# 1.3 Install and verify the Python SDK\n",
     "# Run in terminal: pip install supermemory\n",
     "import supermemory\n",
     "print(f\"Supermemory SDK version: {supermemory.__version__}\")\n"]),

(C, ["# 1.4 Create your first client\n",
     "from supermemory import Supermemory\n", "\n",
     "# Reads SUPERMEMORY_API_KEY from environment automatically\n",
     "client = Supermemory()\n", "\n",
     "# Or pass explicitly: Supermemory(api_key=\"sm_...\")\n",
     "# Or for self-hosted: Supermemory(api_key=\"...\", base_url=\"http://localhost:6767\")\n", "\n",
     "print(f\"Client ready. Base URL: {client.base_url}\")\n"]),

(C, ["# 1.5 Add your first memory\n",
     "response = client.add(\n",
     '    content=\"Hello, Supermemory! My name is Alex, I am a software engineer '\n",
     '            specializing in distributed systems. I love Python and Rust.\",\n',
     '    container_tag=\"tutorial_user_alex\"\n',
     ")\n",
     "print(f\"Document ID: {response.id}\")\n",
     "print(f\"Status: {response.status}\")  # 'queued' means processing started\n"]),

(C, ["# 1.6 Retrieve context -- get user profile\n",
     "# profile() returns static + dynamic facts + relevant search results in ONE call\n",
     "profile = client.profile(\n",
     '    container_tag=\"tutorial_user_alex\",\n',
     '    q=\"What does Alex do?\"  # optional query for relevant memories\n',
     ")\n", "\n",
     "print(\"=== Static Profile (long-term facts) ===\")\n",
     "for fact in profile.profile.static:\n",
     "    print(f\"  - {fact}\")\n", "\n",
     "print(\"=== Dynamic Profile (recent context) ===\")\n",
     "for fact in profile.profile.dynamic:\n",
     "    print(f\"  - {fact}\")\n"]),

(C, ["# 1.7 Configuration options\n",
     "# Timeouts: Supermemory(timeout=120.0)\n",
     "# Retries: Supermemory(max_retries=5)  (default: 2 with exponential backoff)\n",
     "# Logging: os.environ[\"SUPERMEMORY_LOG\"] = \"debug\"\n", "\n",
     "print(\"Key config options: timeout, max_retries, base_url, SUPERMEMORY_LOG\")\n"]),

(M, ["## 1.8 Key Takeaways\n", "\n",
     "- Supermemory is a **living knowledge graph**, not static storage\n",
     "- The SDK auto-reads `SUPERMEMORY_API_KEY` from environment\n",
     "- `add()` ingests content -> extracts memories automatically\n",
     "- `profile()` returns user context (static + dynamic) in one call (~50ms)\n",
     "- Self-hosting is a single binary, zero config\n", "\n",
     "**Next:** Notebook 02 -- Adding Memories (text, URLs, files, bulk)\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 02: Adding Memories
# ════════════════════════════════════════════════════

nb_save("02_adding_memories.ipynb", [

(M, ["# 02 -- Adding Memories\n", "\n",
     "## What We'll Cover\n",
     "1. Adding text content\n",
     "2. Adding URLs (auto-extracted)\n",
     "3. Uploading files (PDFs, images, videos)\n",
     "4. Using `customId` for updates and deduplication\n",
     "5. Scoping with `containerTag` and `containerTags`\n",
     "6. Bulk ingestion strategies\n"]),

(M, ["## 2.1 The `add()` Method\n", "\n",
     "The core ingestion method. Send any raw content and Supermemory extracts memories automatically.\n", "\n",
     "**Parameters:**\n",
     "- `content` (str): Text, URL, or raw content to process\n",
     "- `container_tag` (str): Single tag for scoping (user ID, project ID)\n",
     "- `container_tags` (list[str]): Multiple tags for cross-cutting scopes\n",
     "- `metadata` (dict): Key-value pairs for filtering\n",
     "- `custom_id` (str): Your ID to enable updates and prevent duplicates\n",
     "- `user_id` (str): Partition data to a specific user space\n"]),

(C, ["# 2.2 Adding basic text content\n",
     "from supermemory import Supermemory\n",
     "client = Supermemory()\n", "\n",
     "# Simplest form -- just content and a container tag\n",
     "response = client.add(\n",
     '    content=\"Machine learning enables computers to learn from data without explicit programming.\",\n',
     '    container_tag=\"user_001\"\n',
     ")\n",
     "print(f\"ID: {response.id}, Status: {response.status}\")\n"]),

(C, ["# 2.3 Adding conversation transcripts (the primary use case)\n",
     "conversation = [\n",
     '    {\"role\": \"assistant\", \"content\": \"Hello! How can I help you today?\"},\n',
     '    {\"role\": \"user\", \"content\": \"Hi! I am Sarah. I am a product designer at Figma. I love Figma, design systems, and coffee.\"},\n',
     '    {\"role\": \"user\", \"content\": \"Can you help me design a dashboard layout?\"},\n',
     "]\n", "\n",
     "# Join the conversation into a single text block\n",
     'conv_text = \"\\n\".join(f\"{m[\"role\"]}: {m[\"content\"]}\" for m in conversation)\n',
     "print(\"Sending conversation:\")\n",
     "print(conv_text)\n", "\n",
     "response = client.add(\n",
     "    content=conv_text,\n",
     '    container_tag=\"user_sarah\",\n',
     '    metadata={\"type\": \"conversation\", \"topic\": \"design\"}\n',
     ")\n",
     "print(f\"\\nStored! ID: {response.id}, Status: {response.status}\")\n"]),

(C, ["# 2.4 Adding URLs -- Supermemory auto-extracts page content\n",
     "response = client.add(\n",
     '    content=\"https://supermemory.ai/docs/introduction\",\n',
     '    container_tag=\"knowledge_base\",\n',
     '    metadata={\"source\": \"web\", \"category\": \"documentation\"}\n',
     ")\n",
     "print(f\"URL queued for extraction: {response.id}\")\n",
     "print(\"Note: URL extraction happens asynchronously. Content will be searchable shortly.\")\n"]),

(C, ["# 2.5 Adding with containerTags -- multiple scoping dimensions\n",
     "# containerTags lets you scope a memory to multiple containers\n",
     "# e.g., a memory belongs to user_001 AND project_alpha AND team_engineering\n",
     "response = client.memory.create(\n",
     '    content=\"The authentication service needs to support OAuth2 and SAML for enterprise customers.\",\n',
     '    containerTags=[\"user_001\", \"project_auth\", \"team_engineering\"],\n',
     '    metadata={\"priority\": \"high\", \"status\": \"planned\"}\n',
     ")\n",
     "print(f\"Multi-tagged memory: {response.id}\")\n",
     "print(\"This memory is now scoped to: user_001, project_auth, team_engineering\")\n"]),

(C, ["# 2.6 Using customId -- prevent duplicates, enable updates\n",
     "# customId is YOUR identifier (conversation ID, document ID, etc.)\n",
     "# Sending with the same customId updates the existing memory\n", "\n",
     "# First addition\n",
     "r1 = client.add(\n",
     '    content=\"user: Hi, I am Sarah.\\nassistant: Nice to meet you, Sarah!\",\n',
     '    custom_id=\"conv_001\",\n',
     '    container_tag=\"user_sarah\"\n',
     ")\n",
     "print(f\"First add: {r1.id}\")\n", "\n",
     "# Later: add more to the same conversation (same customId)\n",
     "# Supermemory links these together intelligently\n",
     "r2 = client.add(\n",
     '    content=\"user: What is the weather today?\\nassistant: It is sunny and 72 degrees!\",\n',
     '    custom_id=\"conv_001\",  # Same ID -- Supermemory links them\n',
     '    container_tag=\"user_sarah\"\n',
     ")\n",
     "print(f\"Update add: {r2.id}\")\n",
     "print(\"Both fragments are now linked under conv_001\")\n"]),

(C, ["# 2.7 Uploading files (PDFs, images, videos)\n",
     "from pathlib import Path\n", "\n",
     "# Upload a PDF (extracts text + builds memories)\n",
     "# client.documents.upload_file(\n",
     "#     file=Path(\"/path/to/report.pdf\"),\n",
     "#     container_tags=[\"user_001\"],\n",
     "#     metadata={\"type\": \"report\"}\n",
     "# )\n", "\n",
     "# Supported formats:\n",
     "# - PDF: Text extraction + chunking + embedding\n",
     "# - Images: OCR for text in images\n",
     "# - Videos: Transcription\n",
     "# - Code: AST-aware chunking\n", "\n",
     "print(\"File uploads support: PDF, images (OCR), video (transcription), code files\")\n",
     "print(\"Processing times: PDF ~1-2 min, video ~5-10 min for 100 pages\")\n"]),

(C, ["# 2.8 Bulk ingestion -- add multiple items efficiently\n",
     "contents = [\n",
     '    (\"Alice is a backend engineer specializing in Go and Kubernetes.\", \"user_alice\"),\n',
     '    (\"Bob is a frontend engineer who loves React and design systems.\", \"user_bob\"),\n',
     '    (\"Carol is a data scientist working with PyTorch and JAX.\", \"user_carol\"),\n',
     '    (\"The team uses AWS for infrastructure and GitHub Actions for CI/CD.\", \"team_eng\"),\n',
     '    (\"Sprint 42 focuses on migrating the monolith to microservices.\", \"sprint_42\"),\n',
     "]\n", "\n",
     "results = []\n",
     "for content, tag in contents:\n",
     "    r = client.add(content=content, container_tag=tag)\n",
     "    results.append(r)\n",
     "    print(f\"Added [{tag}]: {r.id}\")\n", "\n",
     "print(f\"\\nTotal ingested: {len(results)} documents\")\n",
     "print(\"Tip: For very large batches, use AsyncSupermemory (see Notebook 07)\")\n"]),

(M, ["## 2.9 Content Types That Work\n", "\n",
     "| Type | Example | Processing |\n",
     "|------|---------|------------|\n",
     "| Text | Free-form text, notes | Direct extraction |\n",
     "| Conversations | Chat transcripts | Role-aware chunking |\n",
     "| URLs | Web pages | Full-content extraction + indexing |\n",
     "| PDFs | Documents, reports | Text extraction + chunking |\n",
     "| Images | Screenshots, photos | OCR for embedded text |\n",
     "| Videos | Recordings, tutorials | Transcription |\n",
     "| Code | Source files | AST-aware semantic chunking |\n", "\n",
     "## 2.10 Key Takeaways\n", "\n",
     "- Use `container_tag` for single-scope, `containerTags` for multi-scope\n",
     "- Use `custom_id` to link updates and prevent duplicates\n",
     "- URLs are auto-extracted -- just pass the URL as content\n",
     "- File uploads support PDFs, images (OCR), videos (transcription)\n",
     "- Processing is async -- status starts as `queued`\n", "\n",
     "**Next:** Notebook 03 -- Searching Memories\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 03: Searching Memories
# ════════════════════════════════════════════════════

nb_save("03_searching_memories.ipynb", [

(M, ["# 03 -- Searching Memories\n", "\n",
     "## What We'll Cover\n",
     "1. Basic semantic search\n",
     "2. Hybrid search (vector + keyword)\n",
     "3. Threshold tuning for precision/recall\n",
     "4. Pagination and result limits\n",
     "5. Search with container scope\n",
     "6. Search modes and relevance scoring\n"]),

(M, ["## 3.1 Two Search APIs\n", "\n",
     "Supermemory offers two search interfaces:\n",
     "- **`client.search.execute(q, ...)`** -- General search across everything\n",
     "- **`client.search.documents(q, container_tags, ...)`** -- Scoped search within containers\n", "\n",
     "Both support hybrid search (vector + keyword) with sub-300ms latency.\n"]),

(C, ["# 3.2 Basic semantic search\n",
     "from supermemory import Supermemory\n",
     "client = Supermemory()\n", "\n",
     "# Search across all accessible documents\n",
     "results = client.search.execute(\n",
     '    q=\"machine learning and AI concepts\"\n',
     ")\n", "\n",
     "print(f\"Found {len(results.results)} results:\")\n",
     "for i, r in enumerate(results.results[:5], 1):\n",
     "    # Each result has 'memory' (the text), 'score' (relevance), 'id'\n",
     "    memory_text = r.get(\"memory\", str(r))\n",
     "    score = r.get(\"score\", \"N/A\")\n",
     "    print(f\"  {i}. [{score}] {memory_text[:120]}...\")\n"]),

(C, ["# 3.3 Scoped search with container tags\n",
     "# Search only within specific containers\n",
     "results = client.search.documents(\n",
     '    q=\"design systems\",\n',
     '    container_tags=[\"user_sarah\"]\n',
     ")\n", "\n",
     "print(f\"Found {len(results.results)} results in user_sarah:\")\n",
     "for r in results.results[:5]:\n",
     "    print(f\"  - {r.get('memory', str(r))[:100]}...\")\n"]),

(C, ["# 3.4 Threshold tuning -- balance precision vs recall\n",
     "# threshold: 0.0-1.0 (higher = more precise, lower = more inclusive)\n", "\n",
     "print(\"=== High Precision (threshold=0.7) ===\")\n",
     "results_precise = client.search.documents(\n",
     '    q=\"distributed systems\",\n',
     "    document_threshold=0.7,\n",
     "    limit=5\n",
     ")\n",
     "print(f\"Results: {len(results_precise.results)}\")\n", "\n",
     "print(\"=== High Recall (threshold=0.3) ===\")\n",
     "results_broad = client.search.documents(\n",
     '    q=\"distributed systems\",\n',
     "    document_threshold=0.3,\n",
     "    limit=10\n",
     ")\n",
     "print(f\"Results: {len(results_broad.results)}\")\n", "\n",
     "print(\"Tip: Use 0.7+ for exact matches, 0.3-0.5 for exploratory searches\")\n"]),

(C, ["# 3.5 Pagination with offset and limit\n",
     "page_size = 3\n",
     "page = 0\n", "\n",
     "while True:\n",
     "    results = client.search.documents(\n",
     '        q=\"engineering\",\n',
     "        limit=page_size,\n",
     "        offset=page * page_size\n",
     "    )\n",
     "    \n",
     "    if not results.results:\n",
     "        break\n", "\n",
     "    print(f\"--- Page {page + 1} ---\")\n",
     "    for r in results.results:\n",
     "        print(f\"  {r.get('memory', str(r))[:80]}...\")\n",
     "    page += 1\n", "\n",
     "print(f\"\\nTotal pages: {page}\")\n"]),

(C, ["# 3.6 Search with onlyMatchingChunks for speed\n",
     "# When you only need the exact match snippets, skip full context\n",
     "results = client.search.documents(\n",
     '    q=\"Python programming\",\n',
     "    limit=5,\n",
     "    only_matching_chunks=True  # Faster, returns only matching chunks\n",
     ")\n",
     "print(f\"Fast search results: {len(results.results)}\")\n",
     "for r in results.results[:3]:\n",
     "    print(f\"  - {r.get('memory', str(r))[:100]}...\")\n"]),

(C, ["# 3.7 Advanced: profile() is search + profile combined\n",
     "# The profile() method combines user context + search in ONE call\n",
     "profile = client.profile(\n",
     '    container_tag=\"user_sarah\",\n',
     '    q=\"design tools and preferences\"  # search query for relevant memories\n',
     ")\n", "\n",
     "print(\"=== Static Facts (always available) ===\")\n",
     "for fact in profile.profile.static:\n",
     "    print(f\"  - {fact}\")\n", "\n",
     "print(\"=== Dynamic Facts (recent context) ===\")\n",
     "for fact in profile.profile.dynamic:\n",
     "    print(f\"  - {fact}\")\n", "\n",
     "print(\"=== Relevant Memories (from search) ===\")\n",
     "for r in profile.search_results.results[:3]:\n",
     "    print(f\"  - {r.get('memory', str(r))[:100]}...\")\n",
     "print(\"\\nThis is the recommended pattern for chatbots/agents!\")\n"]),

(M, ["## 3.8 Search Best Practices\n", "\n",
     "- **Use `profile()` for chatbots** -- combines context + search in one call\n",
     "- **Set `document_threshold`** -- 0.7+ for precise, 0.3-0.5 for exploratory\n",
     "- **Keep limits small** -- `limit=5` is usually enough; paginate for more\n",
     "- **Use `only_matching_chunks=True`** for speed when you don't need full context\n",
     "- **Scope with container tags** -- searches without tags are slower and less relevant\n", "\n",
     "**Next:** Notebook 04 -- User Profiles\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 04: User Profiles
# ════════════════════════════════════════════════════

nb_save("04_user_profiles.ipynb", [

(M, ["# 04 -- User Profiles\n", "\n",
     "## What We'll Cover\n",
     "1. Static vs Dynamic profiles\n",
     "2. How profiles auto-build from ingestion\n",
     "3. Using profiles for context injection\n",
     "4. Profile + Search combined\n",
     "5. Profile use cases (chatbots, support, education, dev tools)\n"]),

(M, ["## 4.1 Why Profiles?\n", "\n",
     "Traditional memory relies entirely on search. But search is **too narrow** -- "
     "when you search for \"project updates\", you miss that the user prefers bullet points, "
     "works in PST, and uses specific terminology.\n", "\n",
     "Profiles provide **the foundation**: a complete picture of who the user is -- always available, no search needed.\n", "\n",
     "**Profile call: ~50ms | Search call: 200-500ms | Context retrieval: 1 call instead of 3-5**\n"]),

(M, ["## 4.2 Static vs Dynamic Profiles\n", "\n",
     "### Static Profile (Long-term, Stable Facts)\n",
     "- \"Sarah is a senior software engineer at TechCorp\"\n",
     "- \"Sarah specializes in distributed systems\"\n",
     "- \"Sarah prefers technical docs over video tutorials\"\n", "\n",
     "### Dynamic Profile (Recent Context, Temporary States)\n",
     "- \"Sarah is migrating the payment service to microservices\"\n",
     "- \"Sarah is preparing for a conference talk next month\"\n",
     "- \"Sarah is debugging a memory leak in auth service\"\n", "\n",
     "Profiles separate these automatically. Static facts persist until contradicted. "
     "Dynamic facts evolve as the user's context changes.\n"]),

(C, ["# 4.3 Basic profile retrieval\n",
     "from supermemory import Supermemory\n",
     "client = Supermemory()\n", "\n",
     "# Get profile without a search query\n",
     "profile = client.profile(container_tag=\"user_sarah\")\n", "\n",
     "print(\"=== STATIC PROFILE ===\")\n",
     "for fact in profile.profile.static:\n",
     "    print(f\"  - {fact}\")\n",
     "print(f\"\\n=== DYNAMIC PROFILE ===\")\n",
     "for fact in profile.profile.dynamic:\n",
     "    print(f\"  - {fact}\")\n"]),

(C, ["# 4.4 Profile with search -- the recommended pattern\n",
     "# profile() + query = context + search in ONE call\n",
     "profile = client.profile(\n",
     '    container_tag=\"user_sarah\",\n',
     '    q=\"What design tools does Sarah use?\",  # search query\n',
     '    threshold=0.5  # relevance threshold\n',
     ")\n", "\n",
     "print(\"=== Static Facts ===\")\n",
     "for fact in profile.profile.static:\n",
     "    print(f\"  - {fact}\")\n",
     "print(f\"\\n=== Dynamic Facts ===\")\n",
     "for fact in profile.profile.dynamic:\n",
     "    print(f\"  - {fact}\")\n",
     "print(f\"\\n=== Relevant Search Memories ===\")\n",
     "for r in profile.search_results.results[:5]:\n",
     "    score = r.get(\"score\", \"N/A\")\n",
     "    memory = r.get(\"memory\", str(r))\n",
     "    print(f\"  [{score}] {memory[:100]}...\")\n"]),

(C, ["# 4.5 Building context for an LLM from a profile\n",
     "# This is the core chatbot/agent pattern\n",
     "def build_llm_context(profile, user_name=\"User\"):\n",
     '    \"\"\"Build a system prompt from a Supermemory profile.\"\"\"\n',
     "    static = \"\\n\".join(f\"- {f}\" for f in profile.profile.static)\n",
     "    dynamic = \"\\n\".join(f\"- {f}\" for f in profile.profile.dynamic)\n",
     "    memories = \"\\n\".join(\n",
     '        f\"- {r.get(\"memory\", str(r))}\" \n',
     "        for r in profile.search_results.results[:5]\n",
     "    )\n", "\n",
     '    system_prompt = f\"\"\"You are assisting {user_name}.\n',
     "\n",
     "Background (long-term):\n",
     "{static}\n",
     "\n",
     "Current focus (recent):\n",
     "{dynamic}\n",
     "\n",
     "Relevant past context:\n",
     "{memories}\n",
     "\n",
     'Adjust your responses to their expertise, preferences, and current work.\"\"\"\n',
     "    return system_prompt\n", "\n",
     "# Example usage\n",
     'prompt = build_llm_context(profile, user_name=\"Sarah\")\n',
     "print(prompt)\n",
     "print(\"\\n--- Now feed this system prompt to your LLM! ---\")\n"]),

(C, ["# 4.6 Profiles self-build -- just keep adding content\n",
     "# Add more conversations and the profile updates automatically\n",
     "more_conversations = [\n",
     '    \"user: I finished the dashboard design! It uses a 12-column grid.\\nassistant: Great work!\",\n',
     '    \"user: I prefer dark mode for all my design tools.\\nassistant: Noted.\",\n',
     '    \"user: The Figma component library needs an update for accessibility.\\nassistant: I can help with that.\",\n',
     "]\n", "\n",
     "for conv in more_conversations:\n",
     "    client.add(content=conv, container_tag=\"user_sarah\")\n",
     "    print(f\"Added: {conv[:60]}...\")\n", "\n",
     "# Check updated profile\n",
     "updated = client.profile(container_tag=\"user_sarah\")\n",
     "print(f\"\\nStatic facts: {len(updated.profile.static)}\")\n",
     "print(f\"Dynamic facts: {len(updated.profile.dynamic)}\")\n",
     "print(\"New facts have been extracted and merged into the profile!\")\n"]),

(M, ["## 4.7 Use Cases\n", "\n",
     "### Personalized AI Assistants\n",
     "Profiles provide: expertise level, communication preferences, tools used, current projects.\n", "\n",
     "### Customer Support\n",
     "Profiles provide: product usage, previous issues, tech proficiency.\n",
     "No more \"let me look up your account\" -- agents immediately understand context.\n", "\n",
     "### Educational Platforms\n",
     "Profiles provide: learning style, completed courses, strengths/weaknesses.\n", "\n",
     "### Development Tools\n",
     "Profiles provide: preferred languages, coding style, current project context.\n", "\n",
     "## 4.8 Key Takeaways\n", "\n",
     "- Profiles auto-build from ingestion -- no manual management needed\n",
     "- Static = long-term stable facts, Dynamic = recent context\n",
     "- `profile()` + query = context + search in one ~50ms call\n",
     "- Use profiles to build rich system prompts for LLMs\n", "\n",
     "**Next:** Notebook 05 -- Graph Memory & Relationships\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 05: Graph Memory & Relationships
# ════════════════════════════════════════════════════

nb_save("05_graph_memory_and_relationships.ipynb", [

(M, ["# 05 -- Graph Memory & Relationships\n", "\n",
     "## What We'll Cover\n",
     "1. The knowledge graph mental model\n",
     "2. Three relationship types: Updates, Extends, Derives\n",
     "3. How relationships form automatically\n",
     "4. Automatic forgetting and contradiction resolution\n",
     "5. Memory types: Facts, Preferences, Episodes\n"]),

(M, ["## 5.1 Not a Vector DB -- A Living Knowledge Graph\n", "\n",
     "Traditional vector databases store chunks independently. "
     "Supermemory builds a **graph** where memories connect to other memories through "
     "typed relationships. It's facts built on top of other facts.\n", "\n",
     "### Three Relationship Types\n", "\n",
     "**1. UPDATES -- Information Changes**\n",
     "When new info contradicts existing knowledge, the newer memory UPDATES the older one. "
     "The `isLatest` flag ensures searches return current information while preserving history.\n", "\n",
     "**2. EXTENDS -- Information Enriches**\n",
     "When new info adds detail without replacing, the newer memory EXTENDS the older one. "
     "Both remain valid -- searches get richer context.\n", "\n",
     "**3. DERIVES -- Information Infers**\n",
     "Supermemory infers new facts from patterns. These are insights you didn't explicitly state.\n"]),

(C, ["# 5.2 Demonstrating 'Updates' -- contradiction resolution\n",
     "from supermemory import Supermemory\n",
     "client = Supermemory()\n", "\n",
     "# Step 1: Add initial fact\n",
     "client.add(\n",
     '    content=\"Alex works at Google as a software engineer.\",\n',
     '    container_tag=\"user_alex\"\n',
     ")\n",
     "print(\"Step 1: Alex works at Google\")\n", "\n",
     "# Step 2: Later, Alex changes jobs -- new info contradicts old\n",
     "# Supermemory creates an UPDATE relationship automatically\n",
     "client.add(\n",
     '    content=\"Alex just started at Stripe as a Product Manager.\",\n',
     '    container_tag=\"user_alex\"\n',
     ")\n",
     "print(\"Step 2: Alex now works at Stripe (UPDATES previous fact)\")\n", "\n",
     "# Step 3: Query -- returns CURRENT info, not old info\n",
     "profile = client.profile(\n",
     '    container_tag=\"user_alex\",\n',
     '    q=\"Where does Alex work?\"\n',
     ")\n",
     "print(\"\\n=== Profile after updates ===\")\n",
     "for fact in profile.profile.static:\n",
     "    print(f\"  - {fact}\")\n",
     "print(\"\\nThe system tracked that Stripe is LATEST, Google is HISTORICAL.\")\n"]),

(C, ["# 5.3 Demonstrating 'Extends' -- adding richness\n",
     "# Extends adds detail without replacing\n",
     "client.add(\n",
     '    content=\"Alex works at Stripe as a PM.\",\n',
     '    container_tag=\"user_alex\"\n',
     ")\n",
     "client.add(\n",
     '    content=\"Alex focuses on payments infrastructure and leads a team of 5 engineers.\",\n',
     '    container_tag=\"user_alex\"\n',
     ")\n",
     "print(\"Added: Alex works at Stripe\")\n",
     "print(\"Added: Alex focuses on payments, leads team of 5\")\n",
     "print(\"\\nBoth facts remain valid -- searches return enriched context.\")\n",
     "print(\"The second fact EXTENDS the first.\")\n"]),

(C, ["# 5.4 Demonstrating 'Derives' -- inferred insights\n",
     "# Derives infers new facts from patterns\n",
     "client.add(\n",
     '    content=\"Alex is a PM at Stripe.\",\n',
     '    container_tag=\"user_alex\"\n',
     ")\n",
     "client.add(\n",
     '    content=\"Alex frequently discusses payment APIs and fraud detection.\",\n',
     '    container_tag=\"user_alex\"\n',
     ")\n",
     "print(\"Fact 1: Alex is a PM at Stripe\")\n",
     "print(\"Fact 2: Alex discusses payment APIs and fraud detection\")\n",
     "print(\"\\nSupermemory may DERIVE: Alex likely works on core payments.\")\n",
     "print(\"These inferences surface insights you never explicitly stated.\")\n"]),

(C, ["# 5.5 Automatic forgetting -- time-based decay\n",
     "from datetime import datetime\n", "\n",
     "# Temporary facts are automatically forgotten when expired\n",
     "client.add(\n",
     '    content=f\"I have an exam tomorrow ({datetime.now().strftime('%Y-%m-%d')}).\",\n',
     '    container_tag=\"user_alex\"\n',
     ")\n",
     "print(\"Added: I have an exam tomorrow\")\n",
     "print(\"Note: After the exam date passes, this will be automatically forgotten.\")\n", "\n",
     "# Other auto-forgetting examples:\n",
     "print(\"\\nExamples of auto-forgotten content:\")\n",
     "print(\"  - 'Meeting with Alex at 3pm today' -> forgotten after today\")\n",
     "print(\"  - 'I am at the airport' -> forgotten after some time\")\n",
     "print(\"  - Casual, non-meaningful content -> never becomes permanent\")\n"]),

(C, ["# 5.6 Memory types -- Facts, Preferences, Episodes\n",
     "print(\"Supermemory distinguishes memory types automatically:\")\n",
     "print()\n",
     "print(\"FACTS: Persist until updated\")\n",
     "print(\"  Example: 'Alex is a PM at Stripe'\")\n",
     "print()\n",
     "print(\"PREFERENCES: Strengthen with repetition\")\n",
     "print(\"  Example: 'Alex prefers morning meetings'\")\n",
     "print(\"  Example: 'Alex likes functional programming'\")\n",
     "print()\n",
     "print(\"EPISODES: Decay unless significant\")\n",
     "print(\"  Example: 'Met Alex for coffee Tuesday'\")\n",
     "print(\"  Example: 'Alex mentioned a new project idea'\")\n",
     "print()\n",
     "print(\"All of this is AUTOMATIC. You don't tag types, clean up, or resolve contradictions.\")\n"]),

(M, ["## 5.7 What You Don't Do\n", "\n",
     "All of this is automatic. You NEVER need to:\n",
     "- Define relationships manually\n",
     "- Tag memory types\n",
     "- Clean up old memories\n",
     "- Resolve contradictions\n",
     "- Manage knowledge versioning\n", "\n",
     "Just add content and search naturally. The graph maintains itself.\n", "\n",
     "**Next:** Notebook 06 -- Metadata & Advanced Filtering\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 06: Metadata & Advanced Filtering
# ════════════════════════════════════════════════════

nb_save("06_metadata_and_filtering.ipynb", [

(M, ["# 06 -- Metadata & Advanced Filtering\n", "\n",
     "## What We'll Cover\n",
     "1. Adding custom metadata to memories\n",
     "2. AND/OR compound filters\n",
     "3. Filtering by metadata fields\n",
     "4. Container-based organization strategies\n",
     "5. Filtered writes (context-aware ingestion)\n"]),

(C, ["# 6.1 Adding memories with rich metadata\n",
     "from supermemory import Supermemory\n",
     "client = Supermemory()\n", "\n",
     "# Metadata can be any key-value pairs (strings, numbers, booleans)\n",
     "docs = [\n",
     "    {\n",
     '        \"content\": \"Q4 revenue increased 23% YoY. Cloud services drove 60% of growth.\",\n',
     '        \"container_tag\": \"company_reports\",\n',
     '        \"metadata\": {\"category\": \"financial\", \"quarter\": \"Q4\", \"year\": 2025, \"priority\": \"high\"}\n',
     "    },\n",
     "    {\n",
     '        \"content\": \"New authentication service to launch in Q3. Supports OAuth2 and SAML.\",\n',
     '        \"container_tag\": \"company_reports\",\n',
     '        \"metadata\": {\"category\": \"engineering\", \"status\": \"planned\", \"team\": \"platform\"}\n',
     "    },\n",
     "    {\n",
     '        \"content\": \"Hiring: 3 senior engineers for the ML platform team. Remote-friendly.\",\n',
     '        \"container_tag\": \"company_reports\",\n',
     '        \"metadata\": {\"category\": \"hr\", \"status\": \"open\", \"team\": \"ml-platform\"}\n',
     "    },\n",
     "    {\n",
     '        \"content\": \"Customer satisfaction score reached 94% in Q4, up from 91%.\",\n',
     '        \"container_tag\": \"company_reports\",\n',
     '        \"metadata\": {\"category\": \"financial\", \"quarter\": \"Q4\", \"year\": 2025}\n',
     "    },\n",
     "]\n", "\n",
     "for doc in docs:\n",
     "    r = client.add(**doc)\n",
     "    print(f\"Added [{doc['metadata']['category']}]: {r.id}\")\n",
     "print(f\"\\nTotal: {len(docs)} documents with metadata\")\n"]),

(C, ["# 6.2 Search with metadata filters -- AND condition\n",
     "# Find financial documents from Q4 2025\n",
     "results = client.search.documents(\n",
     '    q=\"revenue growth\",\n',
     '    container_tags=[\"company_reports\"],\n',
     '    filters={\n',
     '        \"AND\": [\n',
     '            {\"key\": \"category\", \"value\": \"financial\"},\n',
     '            {\"key\": \"year\", \"value\": 2025}\n',
     '        ]\n',
     '    }\n',
     ")\n", "\n",
     "print(f\"Found {len(results.results)} financial documents from 2025:\")\n",
     "for r in results.results:\n",
     "    print(f\"  - {r.get('memory', str(r))[:100]}...\")\n"]),

(C, ["# 6.3 Search with OR filter\n",
     "# Find documents about engineering OR hr\n",
     "results = client.search.documents(\n",
     '    q=\"team updates\",\n',
     '    container_tags=[\"company_reports\"],\n',
     '    filters={\n',
     '        \"OR\": [\n',
     '            {\"key\": \"category\", \"value\": \"engineering\"},\n',
     '            {\"key\": \"category\", \"value\": \"hr\"}\n',
     '        ]\n',
     '    }\n',
     ")\n", "\n",
     "print(f\"Found {len(results.results)} engineering or HR documents:\")\n",
     "for r in results.results:\n",
     "    print(f\"  - {r.get('memory', str(r))[:100]}...\")\n"]),

(C, ["# 6.4 Combined AND/OR filters\n",
     "results = client.search.documents(\n",
     '    q=\"\",  # Empty query = return all matching filters\n',
     '    container_tags=[\"company_reports\"],\n',
     '    filters={\n',
     '        \"AND\": [\n',
     '            {\"OR\": [\n',
     '                {\"key\": \"category\", \"value\": \"financial\"},\n',
     '                {\"key\": \"category\", \"value\": \"engineering\"}\n',
     '            ]},\n',
     '            {\"key\": \"status\", \"value\": \"open\"}\n',
     '        ]\n',
     '    }\n',
     ")\n",
     "print(f\"Results: {len(results.results)}\")\n",
     "print(\"Filter: (category=financial OR category=engineering) AND status=open\")\n",
     "for r in results.results:\n",
     "    print(f\"  - {r.get('memory', str(r))[:100]}...\")\n"]),

(C, ["# 6.5 Container-based organization strategies\n",
     "print(\"Container Tag Strategy Patterns:\")\n",
     "print()\n",
     "print(\"1. USER-SCOPED: container_tag = 'user_<id>'\")\n",
     "print(\"   Best for: chatbots, personal assistants, per-user profiles\")\n",
     "print()\n",
     "print(\"2. PROJECT-SCOPED: container_tag = 'project_<name>'\")\n",
     "print(\"   Best for: team projects, codebases, documentation\")\n",
     "print()\n",
     "print(\"3. MULTI-DIMENSIONAL: containerTags = ['user_X', 'project_Y', 'team_Z']\")\n",
     "print(\"   Best for: cross-cutting concerns, matrix organizations\")\n",
     "print()\n",
     "print(\"4. TENANT-SCOPED: Use userId for strict data partitioning\")\n",
     "print(\"   Best for: multi-tenant SaaS, isolated customer data\")\n"]),

(C, ["# 6.6 Filtered writes -- context-aware ingestion\n",
     "# filterByMetadata: only use memories matching this filter as context during ingestion\n",
     "# This is for when you want the AI to only consider certain existing memories\n",
     "# when processing new content\n", "\n",
     "print(\"Filtered Write Example:\")\n",
     "print(\"When adding new content about the ML platform,\")\n",
     "print(\"only use existing memories tagged with team='ml-platform' as context.\")\n",
     "print()\n",
     "print(\"client.add(\")\n",
     "print(\"    content='New ML model deployment pipeline is ready',\")\n",
     "print(\"    container_tag='company_reports',\")\n",
     "print(\"    filter_by_metadata={'AND': [{'key': 'team', 'value': 'ml-platform'}]}\")\n",
     "print(\")\")\n",
     "print()\n",
     "print(\"This ensures the new memory connects to relevant existing context.\")\n"]),

(M, ["## 6.7 Key Takeaways\n", "\n",
     "- Metadata enables powerful filtering (AND, OR, nested combinations)\n",
     "- Container tags provide the primary scoping mechanism\n",
     "- Use `containerTags` for multi-dimensional organization\n",
     "- Filters work with search, list, and filtered writes\n",
     "- Organize early -- it's hard to retroactively add metadata\n", "\n",
     "**Next:** Notebook 07 -- Async Operations\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 07: Async Operations
# ════════════════════════════════════════════════════

nb_save("07_async_operations.ipynb", [

(M, ["# 07 -- Async Operations\n", "\n",
     "## What We'll Cover\n",
     "1. AsyncSupermemory client\n",
     "2. Concurrent ingestion\n",
     "3. Parallel profile lookups\n",
     "4. Async file uploads\n",
     "5. Error handling in async mode\n",
     "6. Performance comparison: sync vs async\n"]),

(C, ["# 7.1 Sync vs Async Clients\n",
     "from supermemory import Supermemory, AsyncSupermemory\n",
     "import asyncio\n", "\n",
     "# Sync client (what we've used so far)\n",
     "sync_client = Supermemory()\n", "\n",
     "# Async client -- identical API, but all methods are awaitable\n",
     "async_client = AsyncSupermemory()\n", "\n",
     "print(\"Sync client:\", type(sync_client).__name__)\n",
     "print(\"Async client:\", type(async_client).__name__)\n",
     "print(\"Functionality is identical -- only the calling pattern differs.\")\n"]),

(C, ["# 7.2 Basic async usage\n",
     "async def basic_async_example():\n",
     '    \"\"\"Demonstrate basic async pattern.\"\"\"\n',
     "    async with AsyncSupermemory() as client:\n",
     "        # Add a memory\n",
     "        response = await client.add(\n",
     '            content=\"Async operations are more efficient for bulk ingestion.\",\n',
     '            container_tag=\"async_demo\"\n',
     "        )\n",
     "        print(f\"Added: {response.id}\")\n", "\n",
     "        # Search\n",
     "        results = await client.search.execute(\n",
     '            q=\"async operations\"\n',
     "        )\n",
     "        print(f\"Search results: {len(results.results)}\")\n", "\n",
     "# Run it\n",
     "asyncio.run(basic_async_example())\n"]),

(C, ["# 7.3 Concurrent ingestion -- the killer async feature\n",
     "# Process many documents in parallel, not sequentially\n",
     "async def concurrent_ingestion():\n",
     '    \"\"\"Add 20 documents concurrently.\"\"\"\n',
     "    async with AsyncSupermemory() as client:\n",
     "        # Prepare 20 documents\n",
     "        docs = [\n",
     '            f\"Document {i}: This is content about topic {i} with some details.\"\n',
     "            for i in range(20)\n",
     "        ]\n", "\n",
     "        # Launch all add operations concurrently\n",
     "        tasks = [\n",
     "            client.add(content=doc, container_tag=\"bulk_test\")\n",
     "            for doc in docs\n",
     "        ]\n",
     "        \n",
     "        # Wait for all to complete\n",
     "        results = await asyncio.gather(*tasks)\n",
     "        \n",
     "        print(f\"Ingested {len(results)} documents concurrently!\")\n",
     "        for r in results[:5]:\n",
     "            print(f\"  {r.id}: {r.status}\")\n",
     "        print(f\"  ... and {len(results) - 5} more\")\n",
     "        \n",
     "        return results\n", "\n",
     "# Compare timing\n",
     "import time\n",
     "start = time.time()\n",
     "asyncio.run(concurrent_ingestion())\n",
     "print(f\"\\nTime: {time.time() - start:.2f}s (20 concurrent adds)\")\n",
     "print(\"Sequential would take ~20x longer!\")\n"]),

(C, ["# 7.4 Parallel profile lookups -- perfect for multi-tenant apps\n",
     "async def parallel_profiles(user_ids):\n",
     '    \"\"\"Look up profiles for multiple users in parallel.\"\"\"\n',
     "    async with AsyncSupermemory() as client:\n",
     "        # Launch all profile lookups concurrently\n",
     "        tasks = [\n",
     "            client.profile(container_tag=f\"user_{uid}\")\n",
     "            for uid in user_ids\n",
     "        ]\n",
     "        profiles = await asyncio.gather(*tasks)\n", "\n",
     "        for uid, profile in zip(user_ids, profiles):\n",
     "            static_count = len(profile.profile.static)\n",
     "            dynamic_count = len(profile.profile.dynamic)\n",
     "            print(f\"user_{uid}: {static_count} static, {dynamic_count} dynamic facts\")\n",
     "        \n",
     "        return dict(zip(user_ids, profiles))\n", "\n",
     "# Try with our tutorial users\n",
     "asyncio.run(parallel_profiles([\"alex\", \"sarah\", \"alice\", \"bob\"]))\n"]),

(C, ["# 7.5 Async error handling with retries\n",
     "from supermemory import RateLimitError, APIConnectionError\n", "\n",
     "async def robust_add(client, content, container_tag, max_retries=3):\n",
     '    \"\"\"Add a memory with retry logic for transient errors.\"\"\"\n',
     "    for attempt in range(max_retries):\n",
     "        try:\n",
     "            return await client.add(content=content, container_tag=container_tag)\n",
     "        except RateLimitError:\n",
     "            wait = 2 ** (attempt + 1)  # Exponential backoff: 2, 4, 8 seconds\n",
     "            print(f\"Rate limited, retrying in {wait}s (attempt {attempt+1}/{max_retries})...\")\n",
     "            await asyncio.sleep(wait)\n",
     "        except APIConnectionError as e:\n",
     "            print(f\"Connection error: {e}, retrying...\")\n",
     "            await asyncio.sleep(1)\n",
     "    raise Exception(f\"Failed after {max_retries} attempts\")\n", "\n",
     "async def demo_robust_add():\n",
     "    async with AsyncSupermemory() as client:\n",
     "        r = await robust_add(client, \"Important data that must be stored.\", \"critical\")\n",
     "        print(f\"Stored: {r.id}\")\n", "\n",
     "asyncio.run(demo_robust_add())\n"]),

(C, ["# 7.6 Async file upload\n",
     "from pathlib import Path\n", "\n",
     "async def async_file_upload():\n",
     '    \"\"\"Upload a file asynchronously.\"\"\"\n',
     "    async with AsyncSupermemory() as client:\n",
     "        # Async upload -- PathLike reads content asynchronously\n",
     "        # response = await client.documents.upload_file(\n",
     "        #     file=Path(\"/path/to/document.pdf\"),\n",
     "        #     container_tags=[\"user_001\"],\n",
     "        #     metadata={\"type\": \"report\"}\n",
     "        # )\n",
     "        # print(f\"File uploaded: {response.id}\")\n",
     "        print(\"Async file uploads work the same as sync -- just await them!\")\n", "\n",
     "asyncio.run(async_file_upload())\n"]),

(M, ["## 7.7 Performance Comparison\n", "\n",
     "| Operation | Sync | Async (concurrent) |\n",
     "|-----------|------|--------------------|\n",
     "| 1 document | ~100ms | ~100ms |\n",
     "| 10 documents | ~1000ms | ~150ms |\n",
     "| 100 documents | ~10s | ~500ms |\n",
     "| 10 user profiles | ~500ms | ~80ms |\n", "\n",
     "**Rule of thumb:** Use async when dealing with 3+ independent operations.\n", "\n",
     "**Next:** Notebook 08 -- Self-Hosting Supermemory\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 08: Self-Hosting Supermemory
# ════════════════════════════════════════════════════

nb_save("08_self_hosting.ipynb", [

(M, ["# 08 -- Self-Hosting Supermemory\n", "\n",
     "## What We'll Cover\n",
     "1. Installing the single binary\n",
     "2. Zero-config startup\n",
     "3. Bring-your-own-model (OpenAI, Anthropic, Ollama, etc.)\n",
     "4. Fully offline setup with Ollama\n",
     "5. Pointing SDKs to local server\n",
     "6. Self-hosted vs Platform comparison\n"]),

(M, ["## 8.1 Why Self-Host?\n", "\n",
     "- **Free, open source** -- no API key needed, no usage limits\n",
     "- **Privacy** -- your data never leaves your machine\n",
     "- **Air-gapped** -- works fully offline with local models\n",
     "- **Same API** -- drop-in compatible with the hosted platform\n",
     "- **One binary** -- no Docker, no database to provision, no config files\n"]),

(C, ["# 8.2 Installation -- one command\n",
     "print(\"Install and start the server:\")\n",
     "print()\n",
     "print(\"Option A: Install script\")\n",
     "print(\"  curl -fsSL https://supermemory.ai/install | bash\")\n",
     "print()\n",
     "print(\"Option B: npx\")\n",
     "print(\"  npx supermemory local\")\n",
     "print()\n",
     "print(\"On first boot:\")\n",
     "print(\"  - Embedded graph engine created automatically\")\n",
     "print(\"  - Built-in local embeddings (nothing sent externally)\")\n",
     "print(\"  - Auto-generated API key printed to console\")\n",
     "print(\"  - Full Memory API available at http://localhost:6767\")\n"]),

(C, ["# 8.3 Connecting SDK to local server\n",
     "from supermemory import Supermemory\n", "\n",
     "# Point to local server -- one line change\n",
     "client = Supermemory(\n",
     '    api_key=\"sm_local_key\",  # printed on first boot\n',
     '    base_url=\"http://localhost:6767\"\n',
     ")\n", "\n",
     "print(\"Connected to local Supermemory server!\")\n",
     "print()\n",
     "print(\"All the same methods work:\")\n",
     "print(\"  client.add(...)\")\n",
     "print(\"  client.profile(...)\")\n",
     "print(\"  client.search.documents(...)\")\n",
     "print(\"  client.documents.list(...)\")\n",
     "print()\n",
     "print(\"AI coding plugins (Claude Code, Codex, OpenCode) work too:\")\n",
     "print('  export SUPERMEMORY_API_URL=http://localhost:6767')\n"]),

(C, ["# 8.4 Bring your own model\n",
     "print(\"Supermemory needs an LLM for memory extraction. You can bring any provider:\")\n",
     "print()\n",
     "print(\"OpenAI:\")\n",
     "print('  OPENAI_API_KEY=sk-... OPENAI_MODEL=gpt-4o supermemory-server')\n",
     "print()\n",
     "print(\"Anthropic:\")\n",
     "print('  ANTHROPIC_API_KEY=sk-ant-... ANTHROPIC_MODEL=claude-sonnet-4-6 supermemory-server')\n",
     "print()\n",
     "print(\"Gemini:\")\n",
     "print('  GEMINI_API_KEY=... GEMINI_MODEL=gemini-2.5-pro supermemory-server')\n",
     "print()\n",
     "print(\"Groq:\")\n",
     "print('  GROQ_API_KEY=gsk_... GROQ_MODEL=llama-4-maverick supermemory-server')\n",
     "print()\n",
     "print(\"Any OpenAI-compatible endpoint works too.\")\n"]),

(C, ["# 8.5 Fully offline with Ollama\n",
     "print(\"For a fully offline setup (no internet needed after download):\")\n",
     "print()\n",
     "print(\"1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh\")\n",
     "print(\"2. Pull a model: ollama pull qwen3:32b\")\n",
     "print(\"3. Start Supermemory pointing to Ollama:\")\n",
     "print()\n",
     "print('  OPENAI_BASE_URL=http://localhost:11434/v1 \\\\')\n",
     "print('  OPENAI_API_KEY=ollama \\\\')\n",
     "print('  OPENAI_MODEL=qwen3:32b \\\\')\n",
     "print('  supermemory-server')\n",
     "print()\n",
     "print(\"Now: graph engine + embeddings + LLM are ALL local.\")\n",
     "print(\"Your data never leaves your machine.\")\n"]),

(C, ["# 8.6 Self-hosted vs Platform -- feature comparison\n",
     "print(\"Feature Comparison:\")\n",
     "print()\n",
     "print(f\"{'Feature':<40} {'Self-hosted':<15} {'Platform':<15}\")\n",
     "print(\"-\" * 70)\n",
     "features = [\n",
     "    (\"Full Memory API\", \"Yes\", \"Yes\"),\n",
     "    (\"Hybrid semantic search\", \"Yes\", \"Yes\"),\n",
     "    (\"Local embeddings\", \"On your machine\", \"Managed\"),\n",
     "    (\"File ingestion (PDFs, images)\", \"Yes\", \"Yes\"),\n",
     "    (\"Connectors (GDrive, Notion, etc.)\", \"No\", \"Yes\"),\n",
     "    (\"MCP Server\", \"No\", \"Yes\"),\n",
     "    (\"Memory extraction quality\", \"Your model\", \"Proprietary (best)\"),\n",
     "    (\"Cost\", \"Free\", \"Freemium\"),\n",
     "    (\"Infrastructure\", \"Your machine\", \"Globally distributed\"),\n",
     "]\n",
     "for name, self_h, plat in features:\n",
     "    print(f\"{name:<40} {self_h:<15} {plat:<15}\")\n",
     "print()\n",
     "print(\"Best of both worlds: develop locally, deploy on platform with one base_url change.\")\n"]),

(M, ["## 8.7 Key Takeaways\n", "\n",
     "- Self-hosting is a single binary -- `curl ... | bash` and you're running\n",
     "- Zero config: embedded database, auto-generated API key, built-in embeddings\n",
     "- Bring any model: OpenAI, Anthropic, Gemini, Groq, or local with Ollama\n",
     "- Fully offline possible: Ollama + Supermemory = local graph engine + local LLM\n",
     "- SDK code is identical -- just change `base_url`\n", "\n",
     "**Next:** Notebook 09 -- Integrating with LLMs\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 09: Integrating with LLMs
# ════════════════════════════════════════════════════

nb_save("09_integrating_with_llms.ipynb", [

(M, ["# 09 -- Integrating with LLMs\n", "\n",
     "## What We'll Cover\n",
     "1. The chatbot with memory pattern\n",
     "2. Agent memory workflow\n",
     "3. RAG with Supermemory\n",
     "4. OpenAI integration example\n",
     "5. Vercel AI SDK integration\n",
     "6. Multi-turn conversation management\n"]),

(M, ["## 9.1 The Core Pattern: Profile -> Chat -> Store\n", "\n",
     "Every LLM integration follows the same three-step pattern:\n",
     "\n",
     "1. **Profile**: Get user context before the LLM call\n",
     "2. **Chat**: Inject profile into system prompt, call LLM\n",
     "3. **Store**: Save the conversation for future context\n", "\n",
     "This ensures every conversation is personalized AND improves over time.\n"]),

(C, ["# 9.2 Complete chatbot with memory (OpenAI example)\n",
     "from supermemory import Supermemory\n",
     "# import openai  # Uncomment if you have openai installed\n", "\n",
     "class MemoryChatbot:\n",
     '    \"\"\"A chatbot that remembers users across conversations.\"\"\"\n', "\n",
     '    def __init__(self, user_id: str):\n',
     "        self.sm = Supermemory()\n",
     "        self.user_id = user_id\n",
     "        self.container_tag = f\"user_{user_id}\"\n",
     "        self.conversation_history = []\n", "\n",
     '    def _build_system_prompt(self, user_message: str) -> str:\n',
     '        \"\"\"Build a system prompt enriched with user profile and memories.\"\"\"\n',
     "        try:\n",
     "            profile = self.sm.profile(\n",
     "                container_tag=self.container_tag,\n",
     "                q=user_message  # Find memories relevant to the current question\n",
     "            )\n",
     "            \n",
     "            static = \"\\n\".join(f\"- {f}\" for f in profile.profile.static)\n",
     "            dynamic = \"\\n\".join(f\"- {f}\" for f in profile.profile.dynamic)\n",
     "            memories = \"\\n\".join(\n",
     '                f\"- {r.get(\"memory\", str(r))}\"\n',
     "                for r in profile.search_results.results[:5]\n",
     "            )\n",
     "            \n",
     '            return f\"\"\"You are a helpful, personalized assistant.\n",
     "\n",
     "User Profile (long-term facts):\n",
     "{static if static else 'No profile yet.'}\n",
     "\n",
     "Current Context (recent activity):\n",
     "{dynamic if dynamic else 'No recent context.'}\n",
     "\n",
     "Relevant Memories:\n",
     "{memories if memories else 'No relevant memories.'}\n",
     "\n",
     'Use this context to personalize your responses. Be concise and helpful.\"\"\"\n',
     "        except Exception as e:\n",
     '            print(f\"Profile lookup failed: {e}\")\n',
     '            return \"You are a helpful assistant.\"  # Fallback\n', "\n",
     '    def chat(self, user_message: str) -> str:\n',
     '        \"\"\"Process a user message and return a response.\"\"\"\n',
     '        # Step 1: Build enriched system prompt\n',
     "        system_prompt = self._build_system_prompt(user_message)\n", "\n",
     '        # Step 2: Call LLM (pseudo-code -- replace with actual API call)\n',
     '        # response = openai.chat.completions.create(\n',
     '        #     model=\"gpt-4o\",\n',
     '        #     messages=[\n',
     '        #         {\"role\": \"system\", \"content\": system_prompt},\n',
     '        #         *self.conversation_history[-10:],  # Last 10 turns\n',
     '        #         {\"role\": \"user\", \"content\": user_message}\n',
     '        #     ]\n',
     '        # )\n',
     '        # assistant_message = response.choices[0].message.content\n', "\n",
     '        # Placeholder response for demo\n',
     '        assistant_message = f\"[LLM would respond here, enriched with profile context]\"\n', "\n",
     '        # Step 3: Store the exchange for future context\n',
     "        self._store_conversation(user_message, assistant_message)\n", "\n",
     "        return assistant_message\n", "\n",
     '    def _store_conversation(self, user_msg: str, assistant_msg: str):\n',
     '        \"\"\"Persist the conversation to Supermemory.\"\"\"\n',
     "        conv_text = f\"user: {user_msg}\\nassistant: {assistant_msg}\"\n",
     "        try:\n",
     "            self.sm.add(\n",
     "                content=conv_text,\n",
     "                container_tag=self.container_tag\n",
     "            )\n",
     "        except Exception as e:\n",
     '            print(f\"Failed to store conversation: {e}\")\n',
     "        \n",
     "        # Keep local history too\n",
     "        self.conversation_history.append({\"role\": \"user\", \"content\": user_msg})\n",
     "        self.conversation_history.append({\"role\": \"assistant\", \"content\": assistant_msg})\n", "\n",
     "# Demo usage\n",
     'bot = MemoryChatbot(user_id=\"sarah\")\n',
     'print(\"Chatbot initialized for user: sarah\")\n',
     'print()\n',
     'response = bot.chat(\"Can you help me design a dashboard?\")\n',
     'print(f\"User: Can you help me design a dashboard?\")\n',
     'print(f\"Bot: {response}\")\n',
     "print()\n",
     "print(\"The system prompt was enriched with Sarah's profile (designer, Figma, etc.)\")\n"]),

(C, ["# 9.3 Agent memory pattern\n",
     "# An AI agent that remembers tasks, preferences, and outcomes\n",
     "class MemoryAgent:\n",
     '    \"\"\"An agent that uses Supermemory to persist task context.\"\"\"\n', "\n",
     '    def __init__(self, agent_id: str):\n',
     "        self.sm = Supermemory()\n",
     "        self.agent_id = agent_id\n",
     "        self.container_tag = f\"agent_{agent_id}\"\n", "\n",
     '    def get_context(self, task_description: str) -> str:\n',
     '        \"\"\"Get relevant context before executing a task.\"\"\"\n',
     "        profile = self.sm.profile(\n",
     "            container_tag=self.container_tag,\n",
     "            q=task_description\n",
     "        )\n",
     "        facts = profile.profile.static + profile.profile.dynamic\n",
     "        memories = [r.get(\"memory\", str(r)) for r in profile.search_results.results[:3]]\n",
     "        return \"\\n\".join(f\"- {x}\" for x in facts + memories)\n", "\n",
     '    def record_result(self, task: str, result: str, success: bool):\n',
     '        \"\"\"Record task outcome for future reference.\"\"\"\n',
     "        status = \"SUCCESS\" if success else \"FAILED\"\n",
     "        content = f\"TASK: {task}\\nRESULT ({status}): {result}\"\n",
     "        self.sm.add(\n",
     "            content=content,\n",
     "            container_tag=self.container_tag,\n",
     '            metadata={\"type\": \"task_result\", \"success\": success}\n',
     "        )\n", "\n",
     '    def record_preference(self, preference: str):\n',
     '        \"\"\"Record a user preference.\"\"\"\n',
     "        self.sm.add(\n",
     "            content=f\"PREFERENCE: {preference}\",\n",
     "            container_tag=self.container_tag,\n",
     '            metadata={\"type\": \"preference\"}\n',
     "        )\n", "\n",
     "# Demo\n",
     'agent = MemoryAgent(agent_id=\"devops_bot\")\n',
     'agent.record_preference(\"User prefers deployments on Tuesdays at 10am PST\")\n',
     'agent.record_result(\"Deploy v2.3 to staging\", \"Deployment completed, all tests passed\", True)\n',
     'agent.record_result(\"Database migration\", \"Migration failed due to lock timeout\", False)\n', "\n",
     'print(\"Agent memory recorded:\")\n',
     'print(\"  - Preference: Tuesday deployments at 10am\")\n',
     'print(\"  - Task: Deploy v2.3 -> SUCCESS\")\n',
     'print(\"  - Task: Database migration -> FAILED\")\n',
     "print()\n",
     'ctx = agent.get_context(\"deploy new version\")\n',
     'print(\"Context for 'deploy new version':\")\n',
     "print(ctx)\n"]),

(C, ["# 9.4 RAG with Supermemory\n",
     "# Use Supermemory as your knowledge base for RAG\n",
     "class SupermemoryRAG:\n",
     '    \"\"\"RAG pipeline backed by Supermemory.\"\"\"\n', "\n",
     '    def __init__(self, knowledge_base_tag: str = \"kb\"):\n',
     "        self.sm = Supermemory()\n",
     "        self.kb_tag = knowledge_base_tag\n", "\n",
     '    def ingest_document(self, content: str, metadata: dict = None):\n',
     '        \"\"\"Add a document to the knowledge base.\"\"\"\n',
     "        return self.sm.add(\n",
     "            content=content,\n",
     "            container_tag=self.kb_tag,\n",
     "            metadata=metadata or {}\n",
     "        )\n", "\n",
     '    def ingest_url(self, url: str, metadata: dict = None):\n',
     '        \"\"\"Ingest a web page.\"\"\"\n',
     "        return self.sm.add(\n",
     "            content=url,  # Supermemory auto-extracts\n",
     "            container_tag=self.kb_tag,\n",
     "            metadata=metadata or {}\n",
     "        )\n", "\n",
     '    def retrieve(self, query: str, top_k: int = 5) -> list[str]:\n',
     '        \"\"\"Retrieve the most relevant chunks for a query.\"\"\"\n',
     "        results = self.sm.search.documents(\n",
     "            q=query,\n",
     "            container_tags=[self.kb_tag],\n",
     "            limit=top_k,\n",
     "            document_threshold=0.5\n",
     "        )\n",
     '        return [r.get(\"memory\", str(r)) for r in results.results]\n', "\n",
     '    def generate_with_context(self, query: str) -> str:\n',
     '        \"\"\"Retrieve context and generate an answer (pseudo-code).\"\"\"\n',
     "        chunks = self.retrieve(query)\n",
     "        context = \"\\n\\n\".join(chunks)\n", "\n",
     '        # prompt = f\"\"\"Answer based on the following context:\n',
     '        # {context}\n',
     '        # Question: {query}\n',
     '        # Answer:\"\"\"\n',
     '        # return llm.generate(prompt)\n', "\n",
     '        return f\"Generated answer using {len(chunks)} relevant chunks.\"\n', "\n",
     "# Demo: build a knowledge base\n",
     'rag = SupermemoryRAG(knowledge_base_tag=\"company_kb\")\n',
     'rag.ingest_document("Our company was founded in 2020. We build AI-powered developer tools.\")\n',
     'rag.ingest_document(\"We have 50 employees across 12 countries. Remote-first culture.\")\n',
     'rag.ingest_document(\"Our flagship product is CodeAssist, an AI coding companion.\")\n', "\n",
     'chunks = rag.retrieve(\"tell me about the company\")\n',
     'print(\"Retrieved chunks:\")\n',
     "for i, chunk in enumerate(chunks, 1):\n",
     "    print(f\"  {i}. {chunk[:100]}...\")\n",
     "print()\n",
     'answer = rag.generate_with_context(\"What does the company do?\")\n',
     "print(f\"Answer: {answer}\")\n"]),

(C, ["# 9.5 Vercel AI SDK integration pattern\n",
     "print(\"For Vercel AI SDK users:\")\n",
     "print()\n",
     "print(\"TypeScript:\")\n",
     "print('  import { withSupermemory } from \"@supermemory/tools/ai-sdk\";')\n",
     "print()\n",
     "print('  const model = withSupermemory(openai(\"gpt-4o\"), {')\n",
     '  print(\'    containerTag: \"user_123\",\')\n',
     '  print(\'    customId: \"conv-1\"\')\n',
     "  print('  });')\n",
     "print()\n",
     "print(\"This automatically:\")\n",
     "print(\"  1. Injects user profile + memories into every request\")\n",
     "print(\"  2. Stores conversations for future context\")\n",
     "print(\"  3. Manages the entire memory lifecycle\")\n",
     "print()\n",
     "print(\"Also available for Mastra, LangChain, and other frameworks.\")\n"]),

(M, ["## 9.6 Best Practices for LLM Integration\n", "\n",
     "1. **Profile before every LLM call** -- it's fast (~50ms) and dramatically improves quality\n",
     "2. **Store after every exchange** -- conversations are the fuel for better profiles\n",
     "3. **Use customId for conversations** -- enables incremental updates without duplication\n",
     "4. **Limit memory injection** -- 3-5 most relevant memories, not everything\n",
     "5. **Handle profile failures gracefully** -- fall back to a generic system prompt\n",
     "6. **Combine profile + search** -- `profile(container_tag, q=user_message)` is the most efficient\n", "\n",
     "**Next:** Notebook 10 -- Production Patterns\n"]),
])

# ════════════════════════════════════════════════════
# NOTEBOOK 10: Production Patterns
# ════════════════════════════════════════════════════

nb_save("10_production_patterns.ipynb", [

(M, ["# 10 -- Production Patterns\n", "\n",
     "## What We'll Cover\n",
     "1. Error handling and retries\n",
     "2. Timeout configuration\n",
     "3. Rate limiting strategies\n",
     "4. Caching profiles\n",
     "5. Logging and monitoring\n",
     "6. Testing strategies\n",
     "7. Deployment checklist\n"]),

(C, ["# 10.1 Comprehensive error handling\n",
     "from supermemory import (\n",
     "    Supermemory, APIError, APIConnectionError, APIStatusError,\n",
     "    AuthenticationError, RateLimitError, PermissionDeniedError,\n",
     "    NotFoundError, BadRequestError, UnprocessableEntityError,\n",
     "    InternalServerError\n",
     ")\n",
     "import time\n", "\n",
     "class RobustSupermemoryClient:\n",
     '    \"\"\"A production-ready wrapper with comprehensive error handling.\"\"\"\n', "\n",
     '    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):\n',
     "        self.client = Supermemory()\n",
     "        self.max_retries = max_retries\n",
     "        self.base_delay = base_delay\n", "\n",
     '    def add_with_retry(self, content: str, container_tag: str, **kwargs):\n',
     '        \"\"\"Add content with intelligent retry logic.\"\"\"\n',
     "        for attempt in range(self.max_retries + 1):\n",
     "            try:\n",
     "                return self.client.add(\n",
     "                    content=content,\n",
     "                    container_tag=container_tag,\n",
     "                    **kwargs\n",
     "                )\n",
     "            except RateLimitError:\n",
     "                if attempt == self.max_retries:\n",
     "                    raise\n",
     "                delay = self.base_delay * (2 ** attempt)  # Exponential backoff\n",
     "                print(f\"Rate limited. Retrying in {delay}s...\")\n",
     "                time.sleep(delay)\n",
     "            except APIConnectionError:\n",
     "                if attempt == self.max_retries:\n",
     "                    raise\n",
     "                delay = self.base_delay * (2 ** attempt)\n",
     "                print(f\"Connection error. Retrying in {delay}s...\")\n",
     "                time.sleep(delay)\n",
     "            except (BadRequestError, UnprocessableEntityError) as e:\n",
     "                # Client errors -- don't retry\n",
     "                print(f\"Client error (not retrying): {e}\")\n",
     "                raise\n",
     "            except AuthenticationError:\n",
     "                print(\"Authentication failed. Check your API key.\")\n",
     "                raise\n",
     "            except PermissionDeniedError:\n",
     "                print(\"Permission denied. Check your API key scopes.\")\n",
     "                raise\n",
     "            except NotFoundError:\n",
     "                print(\"Resource not found.\")\n",
     "                raise\n",
     "            except InternalServerError:\n",
     "                if attempt == self.max_retries:\n",
     "                    raise\n",
     "                delay = self.base_delay * (2 ** attempt)\n",
     "                print(f\"Server error. Retrying in {delay}s...\")\n",
     "                time.sleep(delay)\n", "\n",
     "# Demo\n",
     "robust = RobustSupermemoryClient()\n",
     "print(\"Robust client ready. Error handling configured for:\")\n",
     "print(\"  - Rate limits: exponential backoff (1s, 2s, 4s)\")\n",
     "print(\"  - Connection errors: retry with backoff\")\n",
     "print(\"  - Client errors (400, 422): no retry, fast fail\")\n",
     "print(\"  - Auth errors (401, 403): no retry, alert immediately\")\n",
     "print(\"  - Server errors (500+): retry with backoff\")\n"]),

(C, ["# 10.2 Timeout configuration for different workloads\n",
     "import httpx\n", "\n",
     "# Fast operations: search, profile (sub-300ms normally)\n",
     "fast_client = Supermemory(timeout=10.0)\n", "\n",
     "# Slow operations: file uploads, URL extraction (1-10 min)\n",
     "# Use background processing or longer timeouts\n",
     "slow_client = Supermemory(\n",
     "    timeout=httpx.Timeout(600.0, connect=10.0, read=300.0, write=60.0)\n",
     ")\n", "\n",
     "# Per-request timeouts override global\n",
     "# fast_client.with_options(timeout=5.0).search.execute(q=\"quick search\")\n", "\n",
     "print(\"Timeout strategies:\")\n",
     "print(\"  Search/Profile: 10s (normally <1s)\")\n",
     "print(\"  File upload: 600s (large files need time)\")\n",
     "print(\"  URL extraction: 300s (page fetch + processing)\")\n",
     "print(\"  Use with_options() for per-call tuning\")\n"]),

(C, ["# 10.3 Rate limit handling strategy\n",
     "import asyncio\n",
     "from collections import deque\n",
     "from datetime import datetime\n", "\n",
     "# Simple token bucket rate limiter\n",
     "class TokenBucket:\n",
     '    \"\"\"Token bucket rate limiter for API calls.\"\"\"\n',
     '    def __init__(self, rate: float, burst: int):\n',
     "        self.rate = rate  # tokens per second\n",
     "        self.burst = burst  # max burst size\n",
     "        self.tokens = float(burst)\n",
     "        self.last_update = datetime.now()\n", "\n",
     '    def acquire(self) -> bool:\n',
     '        \"\"\"Try to acquire a token. Returns True if successful.\"\"\"\n',
     "        now = datetime.now()\n",
     "        elapsed = (now - self.last_update).total_seconds()\n",
     "        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)\n",
     "        self.last_update = now\n", "\n",
     "        if self.tokens >= 1.0:\n",
     "            self.tokens -= 1.0\n",
     "            return True\n",
     "        return False\n", "\n",
     "# Usage: limit to 10 requests per second with burst of 20\n",
     "limiter = TokenBucket(rate=10.0, burst=20)\n",
     "print(\"Rate limiter configured: 10 req/s, burst 20\")\n",
     "print(\"Use before each API call: if limiter.acquire(): make call else: wait\")\n"]),

(C, ["# 10.4 Profile caching for high-throughput applications\n",
     "from functools import lru_cache\n",
     "from datetime import datetime, timedelta\n", "\n",
     "class CachedProfileService:\n",
     '    \"\"\"Cache user profiles to reduce API calls in high-throughput scenarios.\"\"\"\n', "\n",
     '    def __init__(self, ttl_seconds: int = 60):\n',
     "        self.client = Supermemory()\n",
     "        self.ttl = ttl_seconds\n",
     "        self._cache = {}  # {container_tag: (profile, cached_at)}\n", "\n",
     '    def get_profile(self, container_tag: str, query: str = None):\n',
     '        \"\"\"Get profile with caching. Cache expires after TTL.\"\"\"\n',
     "        now = datetime.now()\n", "\n",
     "        # Check cache\n",
     "        if container_tag in self._cache:\n",
     "            cached_data, cached_at = self._cache[container_tag]\n",
     "            if (now - cached_at).total_seconds() < self.ttl:\n",
     "                print(f\"Cache HIT for {container_tag}\")\n",
     "                return cached_data\n", "\n",
     "        # Cache miss -- fetch from Supermemory\n",
     "        print(f\"Cache MISS for {container_tag}\")\n",
     "        profile = self.client.profile(\n",
     "            container_tag=container_tag,\n",
     "            q=query\n",
     "        )\n",
     "        self._cache[container_tag] = (profile, now)\n",
     "        return profile\n", "\n",
     '    def invalidate(self, container_tag: str):\n',
     '        \"\"\"Force-refresh a user's cache after adding new content.\"\"\"\n',
     "        self._cache.pop(container_tag, None)\n",
     "        print(f\"Cache invalidated for {container_tag}\")\n", "\n",
     "# Demo\n",
     "cache = CachedProfileService(ttl_seconds=30)\n",
     'p1 = cache.get_profile(\"user_sarah\")  # Cache MISS\n',
     'p2 = cache.get_profile(\"user_sarah\")  # Cache HIT (within 30s)\n',
     "print()\n",
     "print(\"Caching is critical for:\")\n",
     "print(\"  - High-throughput chatbots (100+ concurrent users)\")\n",
     "print(\"  - API endpoints that call profile() on every request\")\n",
     "print(\"  - Reducing latency by skipping network calls\")\n",
     "print(\"  Trade-off: cached profiles may be slightly stale\")\n"]),

(C, ["# 10.5 Logging and monitoring\n",
     "import os\n",
     "import logging\n", "\n",
     "# Enable Supermemory SDK logging\n",
     "os.environ[\"SUPERMEMORY_LOG\"] = \"info\"\n",
     "# os.environ[\"SUPERMEMORY_LOG\"] = \"debug\"  # More verbose\n", "\n",
     "# Set up structured logging for your application\n",
     "logging.basicConfig(\n",
     "    level=logging.INFO,\n",
     '    format=\"%(asctime)s [%(levelname)s] %(name)s: %(message)s\"\n',
     ")\n",
     "logger = logging.getLogger(\"myapp.supermemory\")\n", "\n",
     "class MonitoredClient:\n",
     '    \"\"\"Client wrapper with instrumentation.\"\"\"\n',
     '    def __init__(self):\n',
     "        self.client = Supermemory()\n",
     "        self.stats = {\"adds\": 0, \"searches\": 0, \"profiles\": 0, \"errors\": 0}\n", "\n",
     '    def add(self, *args, **kwargs):\n',
     "        try:\n",
     "            result = self.client.add(*args, **kwargs)\n",
     "            self.stats[\"adds\"] += 1\n",
     "            logger.info(f\"add() success: id={result.id}\")\n",
     "            return result\n",
     "        except Exception as e:\n",
     "            self.stats[\"errors\"] += 1\n",
     "            logger.error(f\"add() failed: {e}\")\n",
     "            raise\n", "\n",
     '    def profile(self, *args, **kwargs):\n',
     "        try:\n",
     "            result = self.client.profile(*args, **kwargs)\n",
     "            self.stats[\"profiles\"] += 1\n",
     "            return result\n",
     "        except Exception as e:\n",
     "            self.stats[\"errors\"] += 1\n",
     "            logger.error(f\"profile() failed: {e}\")\n",
     "            raise\n", "\n",
     '    def report(self):\n',
     '        \"\"\"Print usage statistics.\"\"\"\n',
     "        print(f\"Usage Report:\")\n",
     "        for k, v in self.stats.items():\n",
     "            print(f\"  {k}: {v}\")\n", "\n",
     "monitored = MonitoredClient()\n",
     "print(\"Monitored client ready with logging + stats tracking.\")\n"]),

(C, ["# 10.6 Testing strategies\n",
     "print(\"Testing Your Supermemory Integration:\")\n",
     "print()\n",
     "print(\"1. UNIT TESTS (mock the SDK)\")\n",
     "print(\"   from unittest.mock import patch, MagicMock\")\n",
     "print(\"   @patch('supermemory.Supermemory')\")\n",
     "print(\"   def test_chatbot_context(mock_sm): ...\")\n",
     "print()\n",
     "print(\"2. INTEGRATION TESTS (use self-hosted for CI)\")\n",
     "print(\"   # Start local Supermemory in CI pipeline\")\n",
     "print(\"   # npx supermemory local &\")\n",
     "print(\"   # Run tests against localhost:6767\")\n",
     "print()\n",
     "print(\"3. CONTRACT TESTS (verify API compatibility)\")\n",
     "print(\"   def test_add_returns_document_id():\")\n",
     "print(\"       r = client.add(content='test', container_tag='test')\")\n",
     "print(\"       assert r.id is not None\")\n",
     "print(\"       assert r.status in ('queued', 'done')\")\n",
     "print()\n",
     "print(\"4. PERFORMANCE TESTS\")\n",
     "print(\"   def test_profile_latency():\")\n",
     "print(\"       start = time.time()\")\n",
     "print(\"       client.profile(container_tag='test')\")\n",
     "print(\"       assert time.time() - start < 1.0  # Under 1 second\")\n"]),

(M, ["## 10.7 Production Deployment Checklist\n", "\n",
     "**Security:**\n",
     "- [ ] API keys stored in environment variables, never in source code\n",
     "- [ ] Use `.env` files only for local dev; use secrets manager in production\n",
     "- [ ] Rotate API keys regularly\n",
     "- [ ] Use separate API keys for dev/staging/production\n", "\n",
     "**Reliability:**\n",
     "- [ ] Implement retry logic with exponential backoff\n",
     "- [ ] Set appropriate timeouts for each operation type\n",
     "- [ ] Cache profiles for high-throughput scenarios\n",
     "- [ ] Graceful degradation: fall back to generic responses if Supermemory is unavailable\n", "\n",
     "**Performance:**\n",
     "- [ ] Use `profile()` with `q=` parameter (single call, not profile + search separately)\n",
     "- [ ] Limit search results to 3-5 items for context injection\n",
     "- [ ] Use `only_matching_chunks=True` for speed-critical searches\n",
     "- [ ] Consider async for concurrent operations\n", "\n",
     "**Observability:**\n",
     "- [ ] Log all API errors with context\n",
     "- [ ] Track latency percentiles (p50, p95, p99)\n",
     "- [ ] Monitor rate limit usage\n",
     "- [ ] Set up alerts for error rate spikes\n", "\n",
     "**Data Management:**\n",
     "- [ ] Use `container_tag` consistently across your application\n",
     "- [ ] Define a metadata schema for your domain\n",
     "- [ ] Implement data retention policies (delete old/unused memories)\n",
     "- [ ] Test with self-hosted Supermemory before going to production\n", "\n",
     "## 10.8 Key Takeaways\n", "\n",
     "- Handle errors by type: retry server errors, fail fast on client errors\n",
     "- Cache profiles for high-throughput apps (30-60s TTL is a good default)\n",
     "- Use self-hosted Supermemory for CI/testing\n",
     "- Always have a fallback path when memory is unavailable\n",
     "- Monitor: you can't improve what you can't measure\n"]),
])

# ════════════════════════════════════════════════════
# EXAMPLE SCRIPTS
# ════════════════════════════════════════════════════

py_save("chatbot_with_memory.py", """\
#!/usr/bin/env python3
\"\"\"
chatbot_with_memory.py -- Full chatbot with Supermemory-backed user profiles

This demonstrates the complete pattern:
  1. Profile: Get user context before LLM call
  2. Chat: Inject profile into system prompt
  3. Store: Save conversation for future context

Usage:
    python chatbot_with_memory.py

Requirements:
    pip install supermemory openai
    export SUPERMEMORY_API_KEY="sm_..."
    export OPENAI_API_KEY="sk-..."
\"\"\"

import os
import sys
from supermemory import Supermemory
from openai import OpenAI


class MemoryChatbot:
    \"\"\"A chatbot that remembers users across conversations using Supermemory.\"\"\"

    def __init__(self, user_id: str):
        self.sm = Supermemory()
        self.llm = OpenAI()
        self.user_id = user_id
        self.container_tag = f"user_{user_id}"
        self.conversation_history: list[dict] = []

    def _build_system_prompt(self, user_message: str) -> str:
        \"\"\"Build a system prompt enriched with user profile and relevant memories.\"\"\"
        try:
            profile = self.sm.profile(
                container_tag=self.container_tag,
                q=user_message,
            )

            static = "\\n".join(f"- {f}" for f in profile.profile.static)
            dynamic = "\\n".join(f"- {f}" for f in profile.profile.dynamic)
            memories = "\\n".join(
                f"- {r.get('memory', str(r))}"
                for r in profile.search_results.results[:5]
            )

            return f\"\"\"You are a helpful, personalized assistant.

USER PROFILE (long-term facts):
{static if static else 'No profile built yet. Keep conversing to build one.'}

CURRENT CONTEXT (recent activity):
{dynamic if dynamic else 'No recent context.'}

RELEVANT MEMORIES:
{memories if memories else 'No relevant past conversations.'}

Use this context to personalize your responses. Address the user by name if known.
Be concise, warm, and helpful.\"\"\"
        except Exception as e:
            print(f"[WARNING] Profile lookup failed: {e}", file=sys.stderr)
            return "You are a helpful assistant."

    def chat(self, user_message: str) -> str:
        \"\"\"Process a user message and return an LLM response with memory context.\"\"\"
        # Step 1: Build enriched system prompt
        system_prompt = self._build_system_prompt(user_message)

        # Step 2: Call LLM with profile-enriched context
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-20:],  # Last 10 exchanges
            {"role": "user", "content": user_message},
        ]

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        assistant_message = response.choices[0].message.content

        # Step 3: Store the exchange for future context
        self._store_conversation(user_message, assistant_message)

        return assistant_message

    def _store_conversation(self, user_msg: str, assistant_msg: str):
        \"\"\"Persist the conversation turn to Supermemory.\"\"\"
        conv_text = f"user: {user_msg}\\nassistant: {assistant_msg}"
        try:
            self.sm.add(content=conv_text, container_tag=self.container_tag)
        except Exception as e:
            print(f"[WARNING] Failed to store conversation: {e}", file=sys.stderr)

        # Keep local history for multi-turn context within this session
        self.conversation_history.append({"role": "user", "content": user_msg})
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_msg}
        )

    def clear_session_history(self):
        \"\"\"Clear local conversation history (memory persists in Supermemory).\"\"\"
        self.conversation_history.clear()


def main():
    user_id = input("Enter your user ID: ").strip() or "demo_user"
    bot = MemoryChatbot(user_id=user_id)

    print(f"\\n=== Memory Chatbot (user: {user_id}) ===")
    print("Type /clear to clear session history")
    print("Type /profile to see your stored profile")
    print("Type /exit to quit\\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "/exit":
            print("Goodbye!")
            break
        elif user_input.lower() == "/clear":
            bot.clear_session_history()
            print("[Session history cleared. Supermemory memories persist.]")
            continue
        elif user_input.lower() == "/profile":
            try:
                profile = bot.sm.profile(container_tag=bot.container_tag)
                print("\\n--- Your Stored Profile ---")
                print("Static facts:")
                for f in profile.profile.static:
                    print(f"  - {f}")
                print("Dynamic facts:")
                for f in profile.profile.dynamic:
                    print(f"  - {f}")
                print("---\\n")
            except Exception as e:
                print(f"Error fetching profile: {e}")
            continue

        response = bot.chat(user_input)
        print(f"Bot: {response}\\n")


if __name__ == "__main__":
    main()
""")

py_save("agent_memory.py", """\
#!/usr/bin/env python3
\"\"\"
agent_memory.py -- AI agent that remembers tasks, preferences, and results

Demonstrates:
  - Recording task outcomes for future learning
  - Storing user preferences that persist across sessions
  - Retrieving relevant context before executing new tasks
  - Error handling and graceful degradation

Usage:
    python agent_memory.py

Requirements:
    pip install supermemory
    export SUPERMEMORY_API_KEY="sm_..."
\"\"\"

import json
from datetime import datetime
from supermemory import Supermemory, APIError


class MemoryAgent:
    \"\"\"An AI agent with persistent memory via Supermemory.\"\"\"

    def __init__(self, agent_name: str):
        self.sm = Supermemory()
        self.agent_name = agent_name
        self.container_tag = f"agent_{agent_name}"

    # ── Context Retrieval ─────────────────────────────

    def get_context(self, task_description: str) -> dict:
        \"\"\"Get all relevant context before executing a task.\"\"\"
        try:
            profile = self.sm.profile(
                container_tag=self.container_tag,
                q=task_description,
            )
            return {
                "static_facts": profile.profile.static,
                "dynamic_facts": profile.profile.dynamic,
                "relevant_memories": [
                    r.get("memory", str(r))
                    for r in profile.search_results.results[:5]
                ],
            }
        except APIError as e:
            print(f"[WARNING] Context retrieval failed: {e}")
            return {
                "static_facts": [],
                "dynamic_facts": [],
                "relevant_memories": [],
            }

    def get_preferences(self) -> list[str]:
        \"\"\"Get stored user preferences.\"\"\"
        try:
            results = self.sm.search.documents(
                q="user preference",
                container_tags=[self.container_tag],
                limit=10,
            )
            return [
                r.get("memory", str(r))
                for r in results.results
                if "preference" in r.get("memory", "").lower()
            ]
        except APIError as e:
            print(f"[WARNING] Preference retrieval failed: {e}")
            return []

    # ── Memory Recording ──────────────────────────────

    def record_task(
        self,
        task: str,
        result: str,
        success: bool,
        metadata: dict | None = None,
    ):
        \"\"\"Record a completed task with its outcome.\"\"\"
        status = "SUCCESS" if success else "FAILED"
        content = (
            f"TASK EXECUTED: {task}\\n"
            f"OUTCOME ({status}): {result}\\n"
            f"AGENT: {self.agent_name}"
        )
        try:
            self.sm.add(
                content=content,
                container_tag=self.container_tag,
                metadata={
                    "type": "task_execution",
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {}),
                },
            )
            print(f"[MEMORY] Recorded task: {task[:60]}... -> {status}")
        except APIError as e:
            print(f"[ERROR] Failed to record task: {e}")

    def record_preference(self, preference: str):
        \"\"\"Record a user preference.\"\"\"
        content = f"USER PREFERENCE: {preference}"
        try:
            self.sm.add(
                content=content,
                container_tag=self.container_tag,
                metadata={"type": "preference"},
            )
            print(f"[MEMORY] Recorded preference: {preference[:60]}...")
        except APIError as e:
            print(f"[ERROR] Failed to record preference: {e}")

    def record_learning(self, lesson: str, category: str = "general"):
        \"\"\"Record a lesson learned for future reference.\"\"\"
        content = f"LESSON LEARNED [{category}]: {lesson}"
        try:
            self.sm.add(
                content=content,
                container_tag=self.container_tag,
                metadata={"type": "learning", "category": category},
            )
            print(f"[MEMORY] Recorded learning [{category}]: {lesson[:60]}...")
        except APIError as e:
            print(f"[ERROR] Failed to record learning: {e}")

    # ── Task History ──────────────────────────────────

    def get_task_history(self, limit: int = 10) -> list[str]:
        \"\"\"Get recent task execution history.\"\"\"
        try:
            results = self.sm.search.documents(
                q="TASK EXECUTED",
                container_tags=[self.container_tag],
                limit=limit,
            )
            return [r.get("memory", str(r)) for r in results.results]
        except APIError as e:
            print(f"[WARNING] Task history retrieval failed: {e}")
            return []

    def get_learnings(self, category: str | None = None) -> list[str]:
        \"\"\"Get lessons learned, optionally filtered by category.\"\"\"
        try:
            filters = {"AND": [{"key": "type", "value": "learning"}]}
            if category:
                filters["AND"].append({"key": "category", "value": category})
            results = self.sm.search.documents(
                q="LESSON LEARNED",
                container_tags=[self.container_tag],
                filters=filters,
                limit=20,
            )
            return [r.get("memory", str(r)) for r in results.results]
        except APIError as e:
            print(f"[WARNING] Learning retrieval failed: {e}")
            return []


def demo():
    \"\"\"Demonstrate the MemoryAgent capabilities.\"\"\"
    agent = MemoryAgent(agent_name="deployment_bot")

    print("=" * 60)
    print("MemoryAgent Demo -- Deployment Bot")
    print("=" * 60)

    # 1. Record preferences
    print("\\n--- Recording Preferences ---")
    agent.record_preference(
        "User prefers deployments on Tuesdays at 10:00 AM PST"
    )
    agent.record_preference(
        "Always run integration tests before deploying to production"
    )
    agent.record_preference(
        "Notify #engineering Slack channel after each deployment"
    )

    # 2. Execute and record tasks
    print("\\n--- Executing Tasks ---")
    agent.record_task(
        task="Deploy v2.3.1 to staging",
        result="Deployment successful. All 142 tests passed. "
               "No performance regressions detected.",
        success=True,
        metadata={"version": "2.3.1", "environment": "staging"},
    )
    agent.record_task(
        task="Deploy v2.3.1 to production",
        result="Deployment failed. Database migration lock timeout "
               "on users table. Rolled back successfully.",
        success=False,
        metadata={"version": "2.3.1", "environment": "production"},
    )

    # 3. Record learnings from failures
    print("\\n--- Recording Learnings ---")
    agent.record_learning(
        "Database migrations on large tables need a lock timeout "
        "of at least 60 seconds. Use `lock_timeout=60000` in migration config.",
        category="database",
    )
    agent.record_learning(
        "Always run migrations against a production-sized dataset "
        "in staging before deploying to production.",
        category="deployment",
    )

    # 4. Retrieve context for a new task
    print("\\n--- Context for New Task ---")
    ctx = agent.get_context("deploy to production")
    print(f"Static facts ({len(ctx['static_facts'])}):")
    for f in ctx["static_facts"]:
        print(f"  - {f}")
    print(f"Dynamic facts ({len(ctx['dynamic_facts'])}):")
    for f in ctx["dynamic_facts"]:
        print(f"  - {f}")
    print(f"Relevant memories ({len(ctx['relevant_memories'])}):")
    for m in ctx["relevant_memories"]:
        print(f"  - {m[:80]}...")

    # 5. Query learnings
    print("\\n--- Lessons Learned ---")
    learnings = agent.get_learnings()
    for i, l in enumerate(learnings, 1):
        print(f"  {i}. {l[:100]}...")

    print("\\n" + "=" * 60)
    print("Demo complete! The agent now has persistent memory.")
    print("Next deployment task will benefit from all recorded context.")


if __name__ == "__main__":
    demo()
""")

py_save("rag_with_supermemory.py", """\
#!/usr/bin/env python3
\"\"\"
rag_with_supermemory.py -- Full RAG pipeline using Supermemory as the knowledge store

Demonstrates:
  - Document ingestion (text + URLs)
  - Hybrid semantic search retrieval
  - Metadata-based filtering
  - Context-aware answer generation
  - Document management (list, delete)

Usage:
    python rag_with_supermemory.py

Requirements:
    pip install supermemory openai
    export SUPERMEMORY_API_KEY="sm_..."
    export OPENAI_API_KEY="sk-..."
\"\"\"

import os
import sys
from supermemory import Supermemory, APIError
from openai import OpenAI


class SupermemoryRAG:
    \"\"\"RAG (Retrieval-Augmented Generation) pipeline backed by Supermemory.\"\"\"

    def __init__(self, knowledge_base_name: str = "default_kb"):
        self.sm = Supermemory()
        self.llm = OpenAI()
        self.kb_tag = f"kb_{knowledge_base_name}"

    # ── Ingestion ─────────────────────────────────────

    def ingest_text(
        self,
        content: str,
        metadata: dict | None = None,
        title: str = "",
    ) -> str:
        \"\"\"Ingest a text document into the knowledge base.\"\"\"
        try:
            response = self.sm.add(
                content=f"{title}\\n{content}" if title else content,
                container_tag=self.kb_tag,
                metadata=metadata or {},
            )
            print(f"[INGEST] Added document: {response.id}")
            return response.id
        except APIError as e:
            print(f"[ERROR] Ingestion failed: {e}", file=sys.stderr)
            raise

    def ingest_url(self, url: str, metadata: dict | None = None) -> str:
        \"\"\"Ingest a web page (Supermemory auto-extracts content).\"\"\"
        try:
            response = self.sm.add(
                content=url,  # URL auto-extraction
                container_tag=self.kb_tag,
                metadata={
                    "source": "url",
                    "url": url,
                    **(metadata or {}),
                },
            )
            print(f"[INGEST] Queued URL: {response.id} ({url[:60]}...)")
            return response.id
        except APIError as e:
            print(f"[ERROR] URL ingestion failed: {e}", file=sys.stderr)
            raise

    def ingest_bulk(self, documents: list[tuple[str, dict]]) -> list[str]:
        \"\"\"Ingest multiple documents at once.\"\"\"
        ids = []
        for content, metadata in documents:
            try:
                doc_id = self.ingest_text(content, metadata)
                ids.append(doc_id)
            except APIError:
                continue  # Skip failed documents, continue with remaining
        print(f"[INGEST] Bulk: {len(ids)}/{len(documents)} documents ingested")
        return ids

    # ── Retrieval ─────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5,
        filters: dict | None = None,
    ) -> list[dict]:
        \"\"\"Retrieve the most relevant documents for a query.\"\"\"
        try:
            results = self.sm.search.documents(
                q=query,
                container_tags=[self.kb_tag],
                limit=top_k,
                document_threshold=threshold,
                filters=filters,
            )
            return [
                {
                    "content": r.get("memory", str(r)),
                    "score": r.get("score", 0.0),
                    "id": r.get("id", ""),
                }
                for r in results.results
            ]
        except APIError as e:
            print(f"[ERROR] Retrieval failed: {e}", file=sys.stderr)
            return []

    # ── Generation ────────────────────────────────────

    def generate_answer(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True,
    ) -> str:
        \"\"\"Generate an answer using retrieved context.\"\"\"
        # Step 1: Retrieve relevant context
        chunks = self.retrieve(question, top_k=top_k)
        if not chunks:
            return "I couldn't find any relevant information to answer your question."

        # Step 2: Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Document {i}] (score: {chunk['score']:.2f})")
            context_parts.append(chunk["content"])
        context = "\\n\\n".join(context_parts)

        # Step 3: Generate answer with LLM
        prompt = f\"\"\"You are a helpful assistant. Answer the question based ONLY on the 
provided context. If the context doesn't contain the answer, say so.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:\"\"\"

        response = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        answer = response.choices[0].message.content

        # Step 4: Optionally append sources
        if include_sources and chunks:
            sources = "\\n\\n---\\n**Sources:**\\n" + "\\n".join(
                f"- [{c['score']:.2f}] {c['content'][:100]}..."
                for c in chunks
            )
            answer += sources

        return answer

    # ── Management ────────────────────────────────────

    def list_documents(self, limit: int = 20) -> list[dict]:
        \"\"\"List documents in the knowledge base.\"\"\"
        try:
            docs = self.sm.documents.list(
                container_tags=[self.kb_tag],
                limit=limit,
            )
            return [
                {"id": d.get("id"), "metadata": d.get("metadata", {})}
                for d in (docs.documents if hasattr(docs, "documents") else [])
            ]
        except APIError as e:
            print(f"[ERROR] List failed: {e}", file=sys.stderr)
            return []

    def delete_document(self, doc_id: str):
        \"\"\"Delete a document from the knowledge base.\"\"\"
        try:
            self.sm.documents.delete(doc_id=doc_id)
            print(f"[DELETE] Removed document: {doc_id}")
        except APIError as e:
            print(f"[ERROR] Delete failed: {e}", file=sys.stderr)

    def search_by_metadata(
        self,
        query: str,
        metadata_filter: dict,
        top_k: int = 5,
    ) -> list[dict]:
        \"\"\"Search with metadata filtering.\"\"\"
        filters = {
            "AND": [
                {"key": k, "value": v} for k, v in metadata_filter.items()
            ]
        }
        return self.retrieve(query, top_k=top_k, filters=filters)


def demo():
    \"\"\"Demonstrate the RAG pipeline.\"\"\"
    rag = SupermemoryRAG(knowledge_base_name="company_wiki")

    print("=" * 60)
    print("RAG Pipeline Demo -- Company Knowledge Base")
    print("=" * 60)

    # 1. Ingest documents
    print("\\n--- Ingesting Documents ---")
    rag.ingest_text(
        title="Company Overview",
        content="Acme Corp was founded in 2020 by Jane Smith and John Doe. "
                "We build AI-powered developer productivity tools. "
                "Our headquarters is in San Francisco, CA.",
        metadata={"category": "company", "type": "overview"},
    )
    rag.ingest_text(
        title="Product: CodeAssist",
        content="CodeAssist is our flagship product -- an AI coding companion "
                "that integrates with VS Code, JetBrains, and Neovim. "
                "It supports 50+ programming languages and has 100K+ users. "
                "Key features: code completion, bug detection, refactoring, "
                "and natural language code generation.",
        metadata={"category": "product", "type": "documentation"},
    )
    rag.ingest_text(
        title="Pricing Tiers",
        content="Free: 100 completions/day, community support. "
                "Pro ($20/mo): unlimited completions, priority support. "
                "Enterprise ($50/user/mo): on-premise deployment, SSO, audit logs, SLA. "
                "Annual billing gives 20% discount on all tiers.",
        metadata={"category": "pricing", "type": "documentation"},
    )
    rag.ingest_text(
        title="Engineering Culture",
        content="We follow an engineering-driven culture. Teams have full autonomy. "
                "We use Rust for our core engine, TypeScript/React for the frontend, "
                "and Python for ML pipelines. CI/CD via GitHub Actions. "
                "Infrastructure on AWS with Kubernetes.",
        metadata={"category": "engineering", "type": "culture"},
    )

    # 2. Answer questions
    questions = [
        "Who founded the company and when?",
        "What are the pricing tiers for CodeAssist?",
        "What programming languages does the engineering team use?",
        "What is the main product and how many users does it have?",
    ]

    print("\\n--- Answering Questions ---\\n")
    for q in questions:
        print(f"Q: {q}")
        answer = rag.generate_answer(q, top_k=3)
        print(f"A: {answer[:200]}...\\n")

    # 3. Metadata-filtered search
    print("--- Filtered Search ---")
    results = rag.search_by_metadata(
        query="engineering",
        metadata_filter={"category": "engineering"},
        top_k=3,
    )
    for r in results:
        print(f"  [{r['score']:.2f}] {r['content'][:80]}...")

    print("\\n" + "=" * 60)
    print("RAG pipeline demo complete!")
    print("All documents are persistently stored in Supermemory.")


if __name__ == "__main__":
    demo()
""")

print("\\nAll files generated successfully!")
print(f"  Notebooks: {BASE_NB}/")
print(f"  Examples:  {BASE_EX}/")
