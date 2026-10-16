# Open WebUI × GraphHack: Feasibility Report

> **Question:** Does Open WebUI already have agent memory coordination, and can we customize it for all three GraphHack tracks smoothly?
> **Researched:** 16 Oct 2026, against Open WebUI **v0.12.2** (latest, released 14 Oct).
> **Short answer:** **Yes, integration is feasible and fairly smooth, but only if Open WebUI is the *UI shell* and FalkorDB is the *brain*.** Open WebUI's built-in memory is **not** what the judges want, and leaving it on would hurt us under the "removal test."
> **Spike status (16 Oct 2026, ~11:45 IST): ✅ VERIFIED end-to-end.** See §0.

---

## 0. Spike results (run locally, not just read from docs)

Stack: `spike/docker-compose.yml` runs `falkordb/falkordb:latest` + `falkordb/mcpserver:latest` (`MCP_TRANSPORT=http`) + `ghcr.io/open-webui/open-webui:v0.12.2`. The LLM is `gpt-oss:20b-cloud` via the host's Ollama. Data: 7 synthetic nodes (`spike/seed.cypher`). Automation: `spike/run_spike.py`.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | FalkorDB seeded + multi-hop read | ✅ | `System←AFFECTS-Decision-DECIDED_IN→Doc` returned the decision + `https://example.org/adr/7` in 0.6 ms |
| 2 | FalkorDB MCP server speaks Streamable HTTP | ✅ | `initialize` → `serverInfo: falkordb`. `tools/list` → 7 tools. `query_graph_readonly` returned `Payments / billing-service / event-bus` |
| 3 | Open WebUI verifies + registers the MCP server | ✅ | `POST /api/v1/configs/tool_servers/verify` → `status: true` with tool specs. Registration HTTP 200 |
| 4 | **LLM in the Open WebUI chat calls FalkorDB via MCP** | ✅ | UI showed "Explored 2 falkordb_query_graph_readonly, falkordb_get_graph_schema". Correct answer: depends on **event-bus**, owned by **Payments**, facts that exist only in FalkorDB |
| 5 | Pipe function queries FalkorDB inside Open WebUI | ✅ | "Ask the Org (spike)" model answered "Use Kafka for billing events (2026-09-02), made by Asha Rao. Owner team: Payments" |
| 6 | Pipe `status` event renders | ✅ | "Traversed System←Decision→Doc: 1 row(s)" shown under the model name |
| 7 | Pipe `source` event renders | ✅ | "1 Source" citation chip linking to ADR-7 |
| 8 | Pipe `embeds` event renders HTML | ✅ | Sandboxed iframe showing the graph path `billing-service → decision → ADR-7 → Asha Rao` |

### Lessons the spike taught us (fold these into the scaffold)

1. **LLM-written Cypher is unreliable.** The model's first query used a non-existent label (`:Service`), returned nothing, then self-corrected after reading the schema. → The product must use a **fixed, typed tool catalogue** (our own MCP server). The generic FalkorDB MCP server is for exploration only.
2. **The generic FalkorDB MCP server exposes `delete_graph` and write-capable `query_graph`.** → Never attach it to a demo model, or run it with `FALKORDB_DEFAULT_READONLY=true`.
3. **Open WebUI downloads a Hugging Face embedding model on first boot** (slow; stalled here). → Set `OFFLINE_MODE=True`, since we don't use its document search anyway. The harmless `SentenceTransformer` error in the logs is expected.
4. **`OFFLINE_MODE` also skips installing a function's `requirements:`** (the Pipe failed with `No module named 'falkordb'` until the client was installed into the container by hand). → **Functions must stay thin and call our brain service over HTTP** (`httpx` ships in the image). Don't depend on in-container pip installs.
5. **New Pipes need a model-list refresh** (`GET /api/models?refresh=true`) or the API returns "Model not found".
6. **Through the bare `/api/chat/completions` API (no chat session), Open WebUI returns `tool_calls` instead of running the tool loop.** The browser UI runs the loop. → Demo through the UI. Scripted tests of the agent go to our brain service directly.
7. **Embed iframes don't inherit the dark theme.** → Give embed HTML explicit text and background colours.
8. **Local ops:** host port 3000 was taken by another local project (FalkorDB Browser moved to **3010**, Open WebUI on **3001**). Pulls from ghcr.io stalled once and needed a restart.
9. **A Pipe is invisible to non-admin users** until it has a saved workspace model entry with a read grant (`{principal_type:'user', principal_id:'*', permission:'read'}`). Without it, both chat and Action calls fail with "Model not found". (`spike/run_action_spike.py`, 16 Oct.)
10. **Action functions get a trustworthy `__user__`** from the verified session. A fake `user` field in the request body is ignored, and acting on another user's chat returns 404. Global actions attach to every model, including Pipes. → The Approve button is safe to build on.

### How to reproduce

```bash
cd spike && docker compose up -d
```
```bash
docker compose exec -T falkordb redis-cli GRAPH.QUERY org:spike "$(grep -v '^//' seed.cypher | tr '\n' ' ')"
```
```bash
docker compose exec -T open-webui pip install falkordb
```
```bash
python run_spike.py
```
Then open http://localhost:3001 (test admin credentials are generated into `spike/.env`, which is gitignored) and chat with **Ask the Org (spike)** and **Graph Agent (spike, MCP)**.

---

## 1. Verdict at a glance

| Question | Answer | Confidence |
|---|---|---|
| Does Open WebUI have memory? | **Yes, but it's a simple per-user note store**, kept in Open WebUI's own database. It isn't a graph, and agents don't share it. | High (official docs) |
| Does it have agent coordination? | **Partly.** It has **sub-agents** (since v0.11.0, off by default): a parent chat hands tasks to background helpers that report back. **No documented shared state** between helpers. | High (official blog) |
| Does it meet Track 2 requirements out of the box? | **No.** There are no episodic/semantic/procedural types, no agent handoff state, no per-tenant graph, and the default vector store is "**NOT SAFE** for multi-worker." | High |
| Can we plug FalkorDB in? | **Yes, through 4 official extension points:** native **MCP**, **Pipe**, **Filter**, and **Event** functions. | High |
| Is FalkorDB a supported Open WebUI vector DB? | **No.** Supported backends are Chroma, pgvector, Milvus, Qdrant, OpenSearch, Pinecone, and others. We integrate through tools and functions, not as a storage backend. | Medium-high |
| Does an existing FalkorDB ↔ Open WebUI integration exist? | **None found.** We build it, which is good for originality. | Medium |
| Allowed under hackathon rules? | **Yes.** Third-party tools and OSS are explicitly allowed. | High (Rules page) |
| License risk? | **Low for us.** BSD-3 plus a branding clause: don't remove "Open WebUI" branding unless you have ≤50 end users in any rolling 30 days. | High |
| Smooth? | **Yes, if we follow the architecture in §4.** The rough edges are Docker networking, RAM for deployment, and pinning the version. | — |

---

## 2. Evidence: what Open WebUI actually ships

### 2.1 Memory (official docs: [Memory](https://docs.openwebui.com/features/chat-conversations/memory))

- Storage: "stored locally in your Open WebUI database and **scoped to your user account**". It is **not** shared with other users.
- Two memory types only: `user` (facts/preferences) and `context` (durable context). Optional hierarchical *paths*.
- Model-callable tools: `add_memory`, `update_memory`, `replace_memory_content`, `delete_memory`, `search_memories`, `list_memories`, `list_memory_paths`, `read_memory_path`.
- Injected into the system prompt by default (`ENABLE_MEMORY_SYSTEM_CONTEXT`), with a cap of `MEMORIES_*_CHAR_LIMIT` = 2000 chars.
- Optional background review every 10 turns (`ENABLE_MEMORY_BACKGROUND_REVIEW`, **off** by default).
- Code-level analysis says retrieval uses the configured vector DB filtered by `user.id` ([DeepWiki](https://deepwiki.com/open-webui/open-webui/6.4-memory-and-context-management)).
- The default ChromaDB is "**NOT SAFE** for multi-worker (`UVICORN_WORKERS > 1`) or multi-replica deployments" ([Performance guide](https://docs.openwebui.com/troubleshooting/performance.md)).

**→ Gap vs Track 2:** no relationships, no episodic/procedural memory, no shared agent state, no handoffs, no graph-based tenant isolation, and no concurrency story.

### 2.2 Multi-agent (official: [v0.11.0 blog](https://openwebui.com/blog/v0-11-0-the-interface-reorganized), 27 Jul 2026)

- "Sub-agents let a model hand parts of a task to background helpers… each helper runs its own tool-driven conversation and reports back."
- Admin controls: concurrency, tool-loop count, output size, inherited system prompt. **Disabled by default.**
- The blog says **nothing about shared memory/state** between sub-agents.

**→ Gap vs Track 2:** coordination exists only as "delegate and report back". There's no shared, persistent, queryable state. We supply that with FalkorDB.

### 2.3 Extension points (all official)

| Mechanism | What it is | Evidence |
|---|---|---|
| **Native MCP** | Since **v0.6.31**. Transport is **Streamable HTTP only**. Auth: none, Bearer, or OAuth 2.1. Added under Admin → External Tools. | [MCP docs](https://docs.openwebui.com/features/mcp) |
| **OpenAPI tool servers** | Any FastAPI app with an OpenAPI spec; each endpoint becomes a tool. Docs call this "the preferred integration path". | [Tools docs](https://docs.openwebui.com/features/extensibility/plugin/tools.md) |
| **Workspace Tools** | In-process Python `class Tools`. Native function calling is the default since v0.10.0. | same |
| **Pipe function** | A custom "model" in the model picker. `pipe()` handles the **whole request**, and **no LLM backend is required**. Gets `__user__`, `__metadata__`, `__event_emitter__`. Can call other models internally. | [Pipe docs](https://docs.openwebui.com/features/extensibility/plugin/functions/pipe.md) |
| **Filter function** | `inlet` (before the LLM), `stream`, `outlet` (after the reply). Can insert a system message with context. Can be **Global** (all models). `__metadata__` includes `chat_id` and `session_id`. | [Filter docs](https://docs.openwebui.com/features/extensibility/plugin/functions/filter.md) |
| **Event function** | New in **v0.10.0**. Runs Python on app-wide events (sign-ups, config changes, **file uploads**). | [Functions docs](https://docs.openwebui.com/features/extensibility/plugin/functions/), [v0.10.0 release](https://github.com/open-webui/open-webui/releases/tag/v0.10.0) |
| **Event emitter** | `status` (live trace), `source`/`citation` (with URLs → clickable sources), `embeds` (**raw HTML in a sandboxed iframe, with scripts allowed**), `notification`, `files`. | [Events docs](https://docs.openwebui.com/features/extensibility/plugin/development/events.md) |
| **Automations** | Scheduled prompts on recurring schedules. | [v0.10.0 release](https://github.com/open-webui/open-webui/releases/tag/v0.10.0) |
| **Channels / shared chats** | Multi-user rooms. v0.12.1 added external apps in channels. | [Releases](https://github.com/open-webui/open-webui/releases) |

### 2.4 FalkorDB side (already researched)

- The **official FalkorDB MCP server** supports `MCP_TRANSPORT=http` (Streamable HTTP) with an optional `MCP_API_KEY` Bearer. That matches Open WebUI's native MCP **directly**, with no proxy needed. ([README](https://cdn.jsdelivr.net/gh/falkordb/falkordb-mcpserver@main/README.md))
- No existing FalkorDB ↔ Open WebUI integration was found in docs or search.

---

## 3. Track-by-track mapping

| Track requirement (official) | Open WebUI native? | How we deliver it | Effort |
|---|---|---|---|
| **T1** Multi-hop reasoning | ❌ | MCP/OpenAPI tools running our fixed Cypher on FalkorDB | Low |
| **T1** Algorithms as agent tools | ❌ | Tools wrapping `algo.pageRank`, `algo.WCC`, `algo.SPpaths`, and others | Low |
| **T1** **Tool selection through MCP** | ✅ **native** | Our MCP server is registered in Admin → External Tools. Picking a tool is visible in the chat UI. | **Very low** |
| **T1** Actions based on graph | ⚠️ tools only | Action tools (create `:Case`, notify) plus Open WebUI's `notify` tool and Action buttons | Low |
| **T1** Explainable results | ⚠️ citations UI exists | `source` events with node IDs + **`embeds` HTML path graph** | Medium |
| **T2** Episodic / semantic / procedural memory | ❌ (only `user`/`context`) | **Global Filter**: `inlet` recalls from FalkorDB, `outlet` writes an `:Episode` → consolidation into `:Fact`/`:Procedure` | Medium |
| **T2** Persistent conversation history | ⚠️ in Open WebUI's DB | Mirror every turn into FalkorDB `(:Session)-[:CONTAINS]->(:Episode)` via `outlet` | Low |
| **T2** Shared state & handoffs | ⚠️ sub-agents, no shared state | Agents inside our **Pipe** (or MCP tools) write `:Task`/`:Handoff` nodes that every agent reads | Medium |
| **T2** High-concurrency reads/writes | ❌ (Chroma unsafe multi-worker) | Benchmark script hitting **our** service directly, with FalkorDB per-tenant graphs | Medium |
| **T2** Separate memory per user/tenant | ✅ per-user (its own DB) | `__user__["id"]` → `db.select_graph(f"mem:{user_id}")` | **Very low** |
| **T3** Docs/tickets/chats in one graph | ⚠️ Knowledge = vector RAG | **Event function on file upload** → our ingest pipeline → FalkorDB nodes | Medium |
| **T3** Who owns / knows what | ❌ | Cypher tools over `OWNS` / `KNOWS_ABOUT` | Low |
| **T3** Trace decisions to source | ⚠️ citation UI exists | `source` events carrying `source_url` from `(:Decision)-[:DECIDED_IN]->(:Doc)` | Low |
| **T3** Keep knowledge current | ⚠️ Automations exist | Automation or Event function triggers incremental re-ingest (MERGE on `source_id`) | Medium |
| **T3** Answers with clear sources | ✅ **native citation UI** | We feed it graph-derived sources | **Very low** |

**Summary:** Open WebUI gives us the **UI, auth, multi-user, MCP client, citation rendering, HTML embeds, and event hooks for free**. Everything the judges score (graph reasoning, memory model, coordination, provenance) must be **our FalkorDB code**. That split is exactly what we want.

---

## 4. The smooth architecture (recommended)

```
┌──────────────────────── Open WebUI v0.12.2 (pinned) ──────────────────────────┐
│  "Ask the Org" PIPE model ─┐   Global FILTER (memory)   EVENT fn (file upload)│
│  (agent loop, emits status,│   inlet: recall           → POST /ingest         │
│   sources, HTML graph embed)│  outlet: write Episode                          │
│  Native MCP client ────────┼───────────────────┬──────────────────────────────┘
└────────────────────────────┼───────────────────┼─────────────────────────────
                             ▼                   ▼
             ┌──────────── brain service (our code, FastAPI + FastMCP) ─────────┐
             │ /mcp  (Streamable HTTP: curated typed tools)                      │
             │ /ask  /recall  /remember  /ingest  /handoff  (REST for functions) │
             │ agent loop · validator · embeddings · extraction · GNN/reranker   │
             └───────────────────────────────┬───────────────────────────────────┘
                                             ▼
                          FalkorDB (multigraph: org:{tenant}, mem:{user})
```

**Rules that keep it smooth and compliant:**

1. **Open WebUI functions stay thin.** They only make HTTP calls to the brain service. Heavy dependencies (falkordb, torch, sentence-transformers) live in **our** container, not inside Open WebUI's Python. This avoids dependency conflicts and the "internal APIs may change" warning on the Pipe page.
2. **Turn off native memory** for demo models (`ENABLE_MEMORIES=False`, or disable the Memory builtin tool per model). Otherwise Open WebUI's DB does memory work and FalkorDB looks like decoration. **This is the single most important setting.**
3. **Don't use Open WebUI "Knowledge" (Chroma RAG)** for core answers. Ingest uploads into FalkorDB and use FalkorDB's own vector index.
4. **Pin the image**: `ghcr.io/open-webui/open-webui:v0.12.2`. Releases ship often and internals change.
5. **Docker networking:** register the MCP URL as `http://brain:8000/mcp` (Compose service name). `localhost` won't work from inside the Open WebUI container.
6. **Model must support native function calling** (the default since v0.10.0). Small local models may call tools unreliably, so use a strong API model for the demo.
7. **Keep the "Open WebUI" branding visible** (license). Our product name can appear as the Pipe model name ("Ask the Org").
8. **README must state the removal test explicitly**: "Open WebUI is the chat shell; turn FalkorDB off and Ask the Org returns nothing."

### Minimal skeletons (to adapt)

```python
# Global Filter: FalkorDB-backed memory (Track 2)
import httpx
from typing import Optional

class Filter:
    async def inlet(self, body: dict, __user__: Optional[dict] = None, __metadata__: Optional[dict] = None) -> dict:
        q = body["messages"][-1]["content"]
        r = httpx.post("http://brain:8000/recall", json={"user": __user__["id"], "q": q}, timeout=10).json()
        if r["memories"]:
            body["messages"].insert(0, {"role": "system", "content": "Known from memory graph:\n" + r["text"]})
        return body

    async def outlet(self, body: dict, __user__: Optional[dict] = None, __metadata__: Optional[dict] = None) -> dict:
        httpx.post("http://brain:8000/remember", json={
            "user": __user__["id"], "chat": __metadata__.get("chat_id"), "messages": body["messages"][-2:]}, timeout=10)
        return body
```

```python
# Pipe: "Ask the Org" agent (Track 3 + 1), streaming trace + sources + graph embed
import httpx

class Pipe:
    async def pipe(self, body: dict, __user__: dict, __event_emitter__=None):
        await __event_emitter__({"type": "status", "data": {"description": "Resolving entities in graph…", "done": False}})
        res = httpx.post("http://brain:8000/ask", json={"user": __user__["id"], "messages": body["messages"]}, timeout=60).json()
        for s in res["sources"]:
            await __event_emitter__({"type": "source", "data": {"source": {"name": s["title"], "id": s["id"]},
                                     "document": [s["quote"]], "metadata": [{"source": s["url"], "name": s["title"], "url": s["url"]}]}})
        await __event_emitter__({"type": "embeds", "data": {"embeds": [res["path_graph_html"]]}})
        await __event_emitter__({"type": "status", "data": {"description": f"{len(res['trace'])} graph calls", "done": True}})
        return res["answer"]
```

---

## 5. Risks and how we neutralise them

| Risk | Impact | Mitigation |
|---|---|---|
| Judges see Open WebUI doing the work (native memory/RAG on) | **Fails the removal test** | Disable native memory and Knowledge. Show FalkorDB Browser live in the demo. |
| "Just a plugin for an existing app" perception | Originality score | Unique graph-path embeds, trace panel, handoff graph. README credits Open WebUI as the shell. |
| Open WebUI is heavy to deploy live (~1–2 GB RAM) | Live demo | FalkorDB Cloud (free) + brain service on Render/Railway + Open WebUI on Railway (template exists) **or** a local deploy plus a strong demo video (allowed by the rules). |
| Version drift / internal API changes | Broken functions | Pin v0.12.2. Functions only use HTTP plus the documented event emitter. |
| Tool calls fail with weak models | Flaky demo | Use a strong tool-calling model and keep a fallback answer built from query rows. |
| Branding clause | Legal | Don't remove Open WebUI branding (or keep ≤50 users in any rolling 30 days). |
| Docker `localhost` confusion | Lost hours | Use Compose service names. Add a health check on `/mcp`. |
| Open WebUI sub-agents compete with our coordination story | Confusing narrative | Leave sub-agents off. Coordination is demoed through FalkorDB `:Handoff` nodes. |

---

## 6. Decision

**Proceed with Open WebUI as the front end** for "Ask the Org" (T3 core + T2 memory layer, with T1-style MCP tools as a bonus claim). It saves roughly a day of UI/auth/chat work and natively shows MCP tool selection, citations, and multi-user. The judged substance stays in our FalkorDB brain service.

**Before committing (30-minute spike):**
1. `docker compose up` with `falkordb/falkordb`, `falkordb/mcpserver` (`MCP_TRANSPORT=http`), and `open-webui:v0.12.2`.
2. Register the MCP server in Admin → External Tools and ask "list the graphs" → confirm the tool call works.
3. Paste a 10-line Pipe that emits a `source` and an `embeds` event → confirm both render.

If all 3 pass, the integration is proven and we scaffold.

---

### Sources
- Open WebUI: [Memory](https://docs.openwebui.com/features/chat-conversations/memory) · [MCP](https://docs.openwebui.com/features/mcp) · [Functions](https://docs.openwebui.com/features/extensibility/plugin/functions/) · [Pipe](https://docs.openwebui.com/features/extensibility/plugin/functions/pipe.md) · [Filter](https://docs.openwebui.com/features/extensibility/plugin/functions/filter.md) · [Tools](https://docs.openwebui.com/features/extensibility/plugin/tools.md) · [Events](https://docs.openwebui.com/features/extensibility/plugin/development/events.md) · [Performance](https://docs.openwebui.com/troubleshooting/performance.md) · [License](https://docs.openwebui.com/license/) · [v0.10.0 release](https://github.com/open-webui/open-webui/releases/tag/v0.10.0) · [v0.11.0 blog](https://openwebui.com/blog/v0-11-0-the-interface-reorganized) · [Releases](https://github.com/open-webui/open-webui/releases)
- Third-party: [DeepWiki memory analysis](https://deepwiki.com/open-webui/open-webui/6.4-memory-and-context-management) · [DeepWiki vector DB options](https://deepwiki.com/open-webui/docs/7.2-vector-database-options) · [MCP connect guide](https://www.simplified.guide/open-webui/mcp-server-connect)
- FalkorDB: [MCP server README](https://cdn.jsdelivr.net/gh/falkordb/falkordb-mcpserver@main/README.md) · [Graphiti + FalkorDB MCP](https://www.falkordb.com/blog/mcp-knowledge-graph-graphiti-falkordb/)
- GraphHack: [Rules](https://www.wemakedevs.org/hackathons/falkordb/rules)
