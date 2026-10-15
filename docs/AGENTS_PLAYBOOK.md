# AGENTS.md: GraphHack Build Playbook

> The operating manual for this repo, written for **both** the human team and any AI coding agent (Claude Code, Copilot, Cursor, Codex) working here.
> Companion file: [GRAPHHACK_BRIEF.md](GRAPHHACK_BRIEF.md) covers what the organizers want, the rules, the open-source policy and the submission checklist.
>
> **Hard deadline: 18 Oct 2026, 11:59 PM IST.** Our internal deadline is **18 Oct, 6:00 PM IST** (submitted, video uploaded, deploy live).

---

## 0. The five laws (every decision must pass these)

1. **The Removal Law.** If FalkorDB were deleted, the agent must break. Graph traversals and algorithms decide what the agent does. *(Official rule: otherwise "the graph counts as decoration.")*
2. **The Path Law.** Every answer carries the path or sources that produced it, built **from query rows**, never from model prose.
3. **The Memory Law.** What the agent learns is written back to the graph as nodes and edges, with a timestamp and session, and read **before** the next traversal.
4. **The Honesty Law.** "Not in the graph" ≠ "nothing". The agent says when the graph lacks data and refuses to guess. (The organizers' blog says judges trust this more than an always-confident agent.)
5. **The Ownership Law.** Humans write the Cypher. The LLM **selects** tools and **fills typed arguments**. It never concatenates strings into queries.

If a feature doesn't serve one of these laws or a track's "key focus" bullet, cut it.

---

## 1. Reference architecture (use for every track)

```
                ┌──────────────────────────────────────────────────────────┐
 user / event ─►│  ORCHESTRATOR AGENT (LLM: picks tools, writes 1-2 lines) │
                └───────────────┬──────────────────────────────────────────┘
                                │ MCP tool calls (typed args only)
     ┌──────────────────────────┼───────────────────────────────────────┐
     ▼                          ▼                                       ▼
 resolve_entity()        graph tools (fixed Cypher)              action tools
 (full-text + vector     multi-hop / algo.* / recall()           (open ticket, page
  index → exact node)    → rows incl. nodes(path)                 on-call, write Finding)
     │                          │                                       │
     └──────────────► FalkorDB (multigraph: one graph per tenant) ◄─────┘
                                │
                     Answer object built FROM ROWS
                                │
                     Validator (no invented entities) ─► UI: answer + path graph + trace
```

### 1.1 The agent loop

1. **Resolve.** Map user text to real nodes (full-text index → vector index fallback). Unknown → stop with "Unknown X".
2. **Recall.** Read prior `Finding`/`Episode` nodes for those entities (dated).
3. **Traverse/compute.** Call 1–3 fixed graph tools (multi-hop Cypher or `algo.*`).
4. **Decide & act.** Choose an action tool based on the rows.
5. **Write back.** Persist the conclusion as a `Finding` node linked to the entities and the session.
6. **Explain.** Return `{outcome, answer, paths, sources, trace}`. A validator rejects any entity named in the prose that is absent from the rows.

### 1.2 Fixed tool catalogue pattern (from the organizers' blog)

```python
TOOLS = {
  "blast_radius": {"args": {"service": "service_name", "depth": "int<=4"}},
  "path_between": {"args": {"from": "service_name", "to": "service_name"}},
  "load_bearing": {"args": {"limit": "int<=20"}},
  "recall":       {"args": {"service": "service_name"}},
}
```

- Each tool = one parameterised Cypher string in `queries/*.cypher`, executed with `params`.
- Validate names **against the graph** (`MATCH (s:Service {name:$name}) RETURN s.name`), not with a regex.
- Use `graph.ro_query()` for every read and `graph.query()` only for deliberate writes.
- Log a **trace row per call**: tool, args, latency ms, row count. Show it in the UI. Judges love it.

### 1.3 Answer outcomes (always one of these)

| Outcome | When |
|---|---|
| `answered_with_path` | Traversal returned rows → show hops |
| `answered_from_memory` | A prior Finding answers it → show its date and session |
| `not_in_graph` | Entity exists but the relationship isn't modelled → say so explicitly |
| `unknown_entity` | Name didn't resolve → no query runs |

### 1.4 Expose tools via MCP (Track 1 calls this out explicitly)

- **Option A (fastest):** the official FalkorDB MCP server, `npx -y @falkordb/mcpserver@latest`, with tools `query_graph`, `query_graph_readonly`, `get_graph_schema`, `get_node_schema`, `get_relationship_schema`, `list_graphs`. Good for exploration, but it lets the model write raw Cypher.
- **Option B (recommended for the product):** our **own MCP server** (Python `mcp` SDK or `fastmcp`) exposing **only** our curated, typed tools. Mention in the README *why* (injection safety, determinism).
- Do both: use A in dev/Claude Desktop to explore, ship B.

---

## 2. FalkorDB cheat sheet (syntax verified against docs.falkordb.com)

```bash
docker run --rm -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest   # DB + Browser UI at :3000
pip install falkordb                                                 # official Python client
```

```python
from falkordb import FalkorDB
db = FalkorDB(host="localhost", port=6379)
g  = db.select_graph(f"tenant:{tenant_id}")      # multigraph = per-tenant isolation
rows = g.ro_query("MATCH (n:Service {name:$n}) RETURN n", {"n": "payments"}).result_set
```

**Multi-hop with the path returned (the core move):**
```cypher
MATCH path = (up:Service)-[:DEPENDS_ON*1..$depth]->(s:Service {name:$name})
RETURN DISTINCT up.name AS service, length(path) AS hops, [n IN nodes(path) | n.name] AS via
ORDER BY hops, service
```

**Algorithms (`CALL algo.*`):**
| Algorithm | Call | Agent use |
|---|---|---|
| PageRank | `CALL algo.pageRank('Service','DEPENDS_ON') YIELD node, score` | most load-bearing / influential node |
| Betweenness | `CALL algo.betweenness({nodeLabels:['Person'], relationshipTypes:['KNOWS']}) YIELD node, score` | brokers, bottlenecks, single points of failure |
| WCC | `CALL algo.WCC({nodeLabels:['Account']}) YIELD node, componentId` | fraud rings, islands, orphaned systems |
| Label propagation | `CALL algo.labelPropagation({maxIterations:10}) YIELD node, communityId` | communities, team clusters, topic clusters |
| BFS | `MATCH (a {name:$n}) CALL algo.bfs(a, 3, 'DEPENDS_ON') YIELD nodes, edges` | bounded neighbourhood expansion |
| Shortest path | `CALL algo.SPpaths({sourceNode:a, targetNode:b, relTypes:['DEPENDS_ON'], relDirection:'outgoing', weightProp:'weight', pathCount:1}) YIELD path, pathWeight` | "how is X connected to Y?" |
| Others | SSpaths, A*, harmonic centrality, MSF, MaxFlow | capacity, routing, reachability |

> Put a `weight` on every edge from day one (even all 1s) so weighted algorithms just work.

**Indexes:**
```cypher
CREATE INDEX FOR (p:Person) ON (p.email)                                           -- range
CREATE FULLTEXT INDEX FOR (d:Doc) ON (d.title)                                     -- full-text
CALL db.idx.fulltext.queryNodes('Doc', 'kafka migration') YIELD node, score
CREATE VECTOR INDEX FOR (c:Chunk) ON (c.embedding) OPTIONS {dimension:768, similarityFunction:'cosine'}
CREATE (c:Chunk {text:$t, embedding: vecf32($vec)})
CALL db.idx.vector.queryNodes('Chunk','embedding', 5, vecf32($q)) YIELD node, score
```
Vector limits: dims 1–4096, approximate (HNSW), **doesn't combine well with property filters**, so do vector → get node IDs → then traverse.

**Known Cypher gotchas** (from the [limitations page](https://docs.falkordb.com/cypher/known-limitations)):
- An unreferenced relationship in a pattern matches "at least one exists". Bind and reference it (`WHERE ID(e) >= 0`) when counting parallel edges.
- `LIMIT` doesn't stop eager ops (CREATE/SET/DELETE/MERGE run fully first).
- `<>` filters can't use indexes. Check with `GRAPH.EXPLAIN`.
- No aggregation inside pattern comprehensions. Aggregate in a `WITH` instead.

**Concurrency:** reads run in parallel. Treat writes to the *same graph* as serialized, so keep write queries small, use `MERGE` for idempotent upserts, and shard hot write paths across per-tenant graphs. Benchmark it for Track 2.

---

## 3. Where neural networks fit (and where they must NOT)

**Principle:** neural nets **feed the graph or rank inside it**. They never replace the traversal. NN outputs are stored **as graph data with provenance** (`model`, `version`, `score`, `at`) so they become traversable and explainable. A pure-NN answer path fails the Removal Law.

| # | Neural component | What it does | Track(s) | Stored in graph as |
|---|---|---|---|---|
| N1 | **Text embedding model** (sentence-transformers e.g. `bge-small`/`all-MiniLM`, or an API embedder) | Fuzzy **entry-point resolution**: user text → nearest nodes, then traverse | 1, 2, 3 | `embedding: vecf32(...)` + vector index |
| N2 | **NER / relation extraction** (GLiNER, spaCy transformer, or LLM via GraphRAG-SDK) | Turn docs/tickets/chats into `Person`, `Project`, `Decision` nodes and edges | **3**, 2 | Nodes/edges with `source_id`, `extractor`, `confidence` |
| N3 | **Graph Neural Network** (GraphSAGE / GAT via `falkordb-pyg`) | **Link prediction** (hidden fraud links, "who likely knows X") or **node classification** (risky account, vulnerable service) | **1**, 3 | `(:Account)-[:SUSPECTED_LINK {score, model:'sage-v1'}]->(:Account)` or `n.risk_score` |
| N4 | **Cross-encoder reranker** (`bge-reranker`, `ms-marco-MiniLM`) | Rerank candidate subgraphs/paths/chunks before the LLM sees them | 3, 1 | Not stored. Logged in the trace. |
| N5 | **Small classifier** (fine-tuned DistilBERT or logistic regression on embeddings) | Route a new memory into **episodic / semantic / procedural**, or classify intent → tool | **2** | Label on `:Memory` node: `:Episodic`, `:Semantic`, `:Procedural` |
| N6 | **Graph embeddings** (Node2Vec / GNN embeddings) | Similarity between entities by *structure* ("accounts that behave like this ring") | 1 | `struct_emb: vecf32(...)` + vector index |
| N7 | **Anomaly model** (autoencoder / isolation forest on graph features like degree, PageRank, WCC size) | Flag outliers to investigate → the agent then traverses | 1 | `n.anomaly_score` + `:Alert` node |
| N8 | **Contradiction / NLI model** (`cross-encoder/nli-deberta`) | Detect when a new fact contradicts an old one → supersede it | **2**, 3 | `(:Fact)-[:SUPERSEDED_BY {at}]->(:Fact)`, `valid_to` |
| N9 | **The LLM itself** | Tool selection, argument filling, 1–2 sentence summary | all | `:Episode` node per turn |

**GNN quick path (Track 1 differentiator):**
```bash
pip install 'falkordb-pyg[torch]'
```
```python
from falkordb_pyg import get_remote_backend
from torch_geometric.loader import NeighborLoader
fs, gs = get_remote_backend(host="localhost", port=6379, graph_name="fraud")
loader = NeighborLoader(data=(fs, gs), num_neighbors={("Account","SENT","Account"): [10,10]},
                        batch_size=64, input_nodes=("Account", train_ids))
# train GraphSAGE → predict → WRITE BACK with the falkordb client (write-back isn't documented in falkordb-pyg):
# g.query("MATCH (a:Account) WHERE ID(a)=$id SET a.risk_score=$s, a.risk_model='sage-v1'", {...})
```
The demo line: *"The GNN proposes, the graph proves."* GNN flags a suspected link → agent runs `SPpaths`/`WCC` to find the real evidence path → acts only if the evidence exists.

**Time-box NN work.** N1 (embeddings) is near-mandatory and cheap. Pick **one** signature NN per track (N3 for T1, N5/N8 for T2, N2+N4 for T3). Don't train anything that takes more than about 30 minutes on a laptop CPU.

---

## 4. Track 01: Agents That Act on Connected Data

### 4.1 What evaluators will check
| Official focus | How we prove it on screen |
|---|---|
| Multi-hop reasoning | Same question at depth 1 vs depth 4. The deeper result finds something a SQL join wouldn't. |
| Graph queries & algorithms as tools | ≥3 `algo.*` calls exposed as tools (PageRank, WCC, SPpaths, betweenness) |
| Tool selection through MCP | Agent connects to our MCP server. The trace shows which tool it chose and why. |
| Actions based on the graph | The agent *does* something (creates `:Case`, freezes account, opens GitHub issue, pages on-call), and the action is gated on the rows |
| Explainable results | Rendered path graph + hop list + trace for every answer |

### 4.2 Idea bank (ranked)
1. **⭐ Fraud ring investigator.** A transaction is flagged → agent expands accounts/devices/IPs/addresses (multi-hop) → `WCC` finds the ring → PageRank finds the mule hub → GNN link-prediction suggests hidden links → agent opens a `:Case` with the evidence path and recommends freezes. Synthetic data generator included. *Most "graph-native" story.*
2. **Security triage agent.** CVE findings → packages → services → internet-exposed endpoints → data stores holding PII. Ranks findings by **reachable blast radius**, not CVSS. Opens tickets for the top N with the attack path.
3. **Codebase navigator.** Parse a public repo (tree-sitter) into `File/Function/Class/CALLS/IMPORTS` → "what breaks if I change X?" → agent drafts a PR checklist / test plan.
4. **On-call blast radius** (the organizers' own demo). Avoid copying it. If chosen, extend it heavily.

### 4.3 Schema template (fraud)
```
(:Account {id, opened_at, risk_score})-[:SENT {amount, at, weight}]->(:Account)
(:Account)-[:USES_DEVICE]->(:Device {fingerprint})
(:Account)-[:LOGGED_FROM]->(:IP {addr, geo})
(:Account)-[:HAS_ADDRESS]->(:Address)
(:Person)-[:OWNS]->(:Account)
(:Alert {id, at, reason})-[:ON]->(:Transaction)
(:Case {id, status, opened_at})-[:INVOLVES]->(:Account)
(:Finding {text, at, session})-[:ABOUT]->(:Account)
(:Account)-[:SUSPECTED_LINK {score, model}]->(:Account)     // GNN output
```

### 4.4 Must-have tools
`resolve_account`, `expand_neighbourhood(depth≤4)`, `find_ring` (WCC), `rank_hubs` (PageRank/betweenness), `evidence_path(a,b)` (SPpaths), `recall(entity)`, `open_case(accounts, evidence)` **(action)**, `write_finding`.

### 4.5 Demo beats (≤3 min)
1. Flagged txn → depth 1 shows 2 accounts. Depth 4 reveals a 9-account ring through a shared device.
2. WCC + PageRank pick the hub. Show the scores.
3. GNN suggests 1 hidden link → agent verifies the path → **opens a case** (node appears live in FalkorDB Browser).
4. Ask about an unrelated account → "not in graph, no shared entities found", **no hallucination**.
5. New session → agent recalls yesterday's case first.

---

## 5. Track 02: Agent Memory and Coordination

### 5.1 What evaluators will check
| Official focus | How we prove it on screen |
|---|---|
| Episodic, semantic, procedural memory | Three labeled memory types in the schema, each **used** differently |
| Persistent conversation history | Kill the process → restart → agent continues with full context from the graph |
| Shared state & handoffs | ≥2 (ideally 3) agents. Agent A writes a `:Handoff` node, agent B picks it up. Visible in the graph. |
| High-concurrency reads/writes | A load script runs N agents in parallel. Show p50/p95 latency and zero lost writes. |
| Separate memory per user/tenant | `select_graph(f"mem:{tenant}")`. Show tenant B can't see tenant A's memory. |

### 5.2 Memory model (the core design)
```
(:User {id})-[:HAD]->(:Session {id, started_at})-[:CONTAINS]->(:Episode {turn, role, text, at, embedding})
(:Episode)-[:NEXT]->(:Episode)                                  // conversation chain
(:Episode)-[:MENTIONS]->(:Entity {name, type})                  // episodic → semantic bridge
(:Fact {text, confidence, valid_from, valid_to, embedding})-[:ABOUT]->(:Entity)   // SEMANTIC
(:Fact)-[:DERIVED_FROM]->(:Episode)                             // provenance
(:Fact)-[:SUPERSEDED_BY {at, reason}]->(:Fact)                  // memory updates over time
(:Procedure {name, steps, success_count, fail_count})-[:SOLVES]->(:TaskType)      // PROCEDURAL
(:Agent {name, role})-[:WROTE]->(:Fact|:Episode|:Procedure)
(:Agent)-[:HANDED_OFF {at, reason}]->(:Task {id, status})<-[:CLAIMED_BY]-(:Agent)
(:Task)-[:NEEDS_CONTEXT]->(:Fact)
```

- **Episodic** = what happened (Episodes in Sessions).
- **Semantic** = what's true (Facts about Entities, versioned with `valid_from`/`valid_to`).
- **Procedural** = how to do things (Procedures with success stats, so agents pick the best-performing one).
- **Consolidation job:** episodes → extract facts (N2/LLM) → NLI contradiction check (N8) → supersede old facts. This is the "memory updates over time" proof.
- **Retrieval** = vector search on Episodes/Facts → expand 2 hops through `MENTIONS`/`ABOUT` → rank by recency × confidence × PageRank.
- **Shortcut option:** Graphiti (`pip install graphiti-core[falkordb]`) gives temporal facts out of the box. Mem0 and Cognee also support FalkorDB. If you use one, **still own the multi-agent coordination layer yourself**; that's the judged part.

### 5.3 Idea bank
1. **⭐ Multi-agent support desk with shared memory.** Triage agent → Specialist agent → QA agent, per-customer tenant graphs. Session 2: "What did I ask last month, and was it resolved?" (the organizers' own example question).
2. **Research swarm.** Planner, Searcher and Writer agents share a fact graph. Contradictions get resolved via `SUPERSEDED_BY`.
3. **Personal dev assistant** that learns procedures (how *this* user deploys) and hands off to a review agent.

### 5.4 Demo beats
1. Session 1: user tells agent A preferences/issue → graph grows live.
2. Restart. Session 2: a different agent B answers using A's memory, citing the episode date.
3. User corrects a fact → old Fact gets `SUPERSEDED_BY` → the answer changes.
4. Concurrency script: 50 agents × 200 ops. Show the latency table.
5. Tenant isolation: same question in tenant B → nothing leaks.

---

## 6. Track 03: Company Brain

### 6.1 What evaluators will check
| Official focus | How we prove it on screen |
|---|---|
| Docs, tickets, chats in one graph | 3+ source types ingested into one graph (synthetic company or a public OSS org: GitHub issues/PRs + docs + public Discord/mailing-list exports if allowed) |
| Who owns what / who knows what | `OWNS` (explicit) vs `KNOWS_ABOUT` (inferred from authored/commented, scored) |
| Tracing decisions to source | `(:Decision)-[:DECIDED_IN]->(:Meeting|:Thread|:Doc)` with quotes and links |
| Keeping knowledge current | Incremental ingest. A new doc supersedes a decision. Staleness detection. |
| Answers with clear sources | Every answer lists the source nodes (doc/ticket/message IDs + URLs) |

### 6.2 Schema template
```
(:Person {name, email})-[:MEMBER_OF]->(:Team)-[:OWNS]->(:Project|:System)
(:Person)-[:AUTHORED|:COMMENTED {at}]->(:Doc|:Ticket|:Message)
(:Doc|:Ticket|:Message)-[:MENTIONS]->(:Project|:System|:Person|:Decision)
(:Decision {title, status, at, rationale})-[:DECIDED_IN]->(:Doc|:Meeting|:Thread)
(:Decision)-[:MADE_BY]->(:Person)
(:Decision)-[:SUPERSEDES]->(:Decision)
(:Decision)-[:AFFECTS]->(:Project|:System)
(:Person)-[:KNOWS_ABOUT {score, evidence_count, last_at}]->(:System)    // derived
(:Chunk {text, embedding})-[:PART_OF]->(:Doc)
```

### 6.3 Ingestion pipeline
1. Loaders (Markdown docs, GitHub issues/PRs API, chat JSON) → `:Doc/:Ticket/:Message` with `source_url`.
2. Chunk + embed (N1) → `:Chunk` with vector index.
3. Extract entities/decisions (N2: GLiNER/spaCy + LLM, or **GraphRAG-SDK** `pip install "graphrag-sdk[all]"`) → MERGE nodes/edges with `source_id`.
4. Derive `KNOWS_ABOUT` scores with Cypher aggregation (authored ×3, commented ×1, recency decay).
5. Run `labelPropagation` (topic/team clusters) and `betweenness` (key connectors / bus-factor risks).
6. Re-ingest is **incremental** (MERGE on `source_id`, set `updated_at`, mark removed items `stale:true`).

### 6.4 Agent abilities ("gets work done")
- "Who should review a change to the billing service?" → `KNOWS_ABOUT` + `OWNS` + availability.
- "Why did we pick Kafka?" → Decision → DECIDED_IN → source quote + author + date, plus any `SUPERSEDES` chain.
- "What's stale?" → Decisions whose AFFECTS-system changed after the decision date.
- **Actions:** draft an onboarding plan for a new hire on Team X; route a question to the 2 best people; flag bus-factor-1 systems.

### 6.5 Idea bank
1. **⭐ "Ask the Org"** over a public OSS project (e.g. a CNCF repo's issues, PRs, docs and ADRs) treated as a company. Real data, fully public, easy for judges to verify.
2. **New-hire onboarding brain:** generates a personalised onboarding path (people to meet, docs to read, decisions to know) from graph traversals.
3. **Decision ledger:** traces every architectural decision to its source thread and flags contradictions.

### 6.6 Demo beats
1. Ingest 3 sources live (or show counts) → graph view.
2. "Who knows the auth service?" → ranked people **with evidence paths**.
3. "Why did we choose X?" → decision → source quote with a link.
4. Add a new doc that reverses the decision → re-ingest → answer updates and the old decision shows `SUPERSEDED`.
5. Action: agent drafts the onboarding plan / routes the question.

---

## 7. Multi-track strategy (enter more than one, legally)

Rules allow entering 1–3 tracks with **one project**. The highest-leverage design is a **Track 1 or 3 core plus a real Track 2 memory layer**:

- e.g. **Fraud investigator (T1)** whose analyst agent + case-writer agent share episodic/semantic memory per bank tenant (T2).
- e.g. **Company Brain (T3)** where ingest, Q&A and action agents coordinate through `:Task`/`:Handoff` nodes and remember each user's past questions (T2).

Only claim a track if its "key focus" bullets are **visibly demoed**. A thin claim dilutes the story. Write a "Track fit" table in the README mapping each official bullet → feature → timestamp in the video.

---

## 8. Repo layout (target)

```
/
├─ AGENTS.md                  ← this file
├─ GRAPHHACK_BRIEF.md
├─ README.md                  ← judges read this first (template in §10)
├─ LICENSE                    ← MIT
├─ docker-compose.yml         ← falkordb + api + (optional) mcp server + ui
├─ .env.example
├─ queries/                   ← EVERY Cypher query the product depends on (required by rules)
│   ├─ tools/*.cypher
│   └─ algorithms/*.cypher
├─ schema/
│   ├─ model.md               ← graph data model + mermaid diagram (required by rules)
│   └─ indexes.cypher
├─ seed/                      ← synthetic/public data generators + loaders
├─ agent/
│   ├─ tools.py               ← fixed tool catalogue (params only)
│   ├─ mcp_server.py          ← exposes tools over MCP
│   ├─ loop.py                ← resolve → recall → traverse → act → write → explain
│   ├─ validator.py           ← rejects invented entities
│   └─ memory.py
├─ ml/                        ← embeddings, GNN, reranker, classifiers (one signature model per track)
├─ ui/                        ← chat + live graph view (path highlight) + trace panel
├─ bench/                     ← concurrency/latency scripts (Track 2)
└─ tests/                     ← golden questions → expected outcome + path
```

---

## 9. Build timeline (from now: 16 Oct → 18 Oct 6 PM IST)

| Block | Deliverable | Owner |
|---|---|---|
| **D2 AM** | Pick idea + track(s). Write `schema/model.md`. Write 10 **golden questions** with expected paths. Test queries in FalkorDB Browser. | all |
| **D2 PM** | Seed generator + indexes. Fixed tool catalogue + `ro_query`. Agent loop end-to-end (ugly is fine). | backend |
| **D2 night** | MCP server. Validator. Memory write-back + recall. Trace logging. | backend |
| **D3 AM** | Signature NN (§3). UI with path highlighting. Deploy (FalkorDB Cloud + Render/Railway/Fly/Vercel). | ml / frontend |
| **D3 PM** | Golden-question tests pass. README + queries + model diagram. Record video. **Submit by 6 PM.** | all |
| **D3 buffer** | Blog post (AirPods prize). Fix deploy. Re-record if needed. | writer |

**Feature freeze: 18 Oct 12:00 PM IST.** After that, only bug fixes, docs and video.

---

## 10. README template (judges' first impression)

1. **One-liner + 20-second GIF** of the agent answering with a highlighted path
2. **Tracks entered** + "Track fit" table (official bullet → our feature → video timestamp)
3. **Why a graph?** The question we answer and why vector RAG / SQL can't (the removal test, stated explicitly)
4. **Graph data model:** mermaid diagram + label/edge table
5. **Cypher & algorithms we depend on:** each query, what tool uses it, why
6. **Architecture:** diagram from §1
7. **Neural components:** what model, where its output lives in the graph
8. **Live demo link** + **demo video link**
9. **Local setup:** `docker compose up` + `python seed/run.py` (copy-paste works on a clean machine)
10. **Data sources:** public/synthetic declaration
11. **AI-assistant disclosure:** tools used and for what (required)
12. **Limitations & next steps** (honesty scores points)
13. Team + license

---

## 11. Demo video script (2.5–3 min; check Discord for the limit)

| Time | Shot |
|---|---|
| 0:00–0:15 | The problem in one sentence + the question that needs connections |
| 0:15–0:30 | Graph model in FalkorDB Browser (labels, edges, counts) |
| 0:30–1:45 | Live agent run: resolve → traverse (depth 1 vs 4) → algorithm → **action** → path highlighted + trace |
| 1:45–2:10 | Memory: new session recalls the prior finding (date shown) |
| 2:10–2:25 | Honesty: question the graph can't answer → `not_in_graph` |
| 2:25–2:45 | Architecture + NN + MCP in one slide |
| 2:45–3:00 | Track-fit recap + links |

---

## 12. Anti-patterns (instant score killers)

- ❌ Vector DB / Postgres doing the real work while FalkorDB renders a pretty graph
- ❌ LLM writing free-form Cypher in production paths (OK only behind the official MCP server in dev/exploration mode, and even then read-only)
- ❌ Answers whose explanation is model prose instead of query rows
- ❌ "Memory" stored in a Python dict or JSON file
- ❌ Single agent pretending to be "multi-agent" (Track 2)
- ❌ One-shot static import with no update path (Track 3)
- ❌ Real customer/personal/private data (rules violation)
- ❌ No README data model, no queries listed (explicit submission requirements)
- ❌ Undisclosed AI-assistant use
- ❌ Submitting at 11:50 PM IST

---

## 13. Instructions for AI coding agents working in this repo

You are helping a hackathon team. Follow these rules strictly:

1. **Never** bypass FalkorDB for core logic. If you're about to store entities, memory, or relationships anywhere else, stop and use the graph.
2. All Cypher lives in `queries/` as parameterised strings (`$param`). **Never** build queries with f-strings or concatenation from user/LLM input.
3. Use `ro_query` for reads. Use `query` only in functions whose name starts with `write_`/`create_`/`upsert_`.
4. Every graph-tool function returns rows that include the path/sources (`nodes(path)`, `source_url`, `id`).
5. Every new label/edge type must be added to `schema/model.md` in the same change.
6. Every new query must be added to the README "Cypher & algorithms" section.
7. Before using any Cypher feature, check it against the [known limitations](https://docs.falkordb.com/cypher/known-limitations). Prefer syntax shown in §2.
8. Tenant/user scoping is done by **graph name** (`select_graph(f"{kind}:{tenant}")`), not by `WHERE` filters.
9. NN outputs are written to the graph with `model`, `version`, `score`, `at` properties.
10. Data must be public, synthetic, or the team's own. Never add scrapers for login-protected or personal data.
11. Keep the demo path working at all times. Run `tests/` golden questions before declaring a task done.
12. Humans on the team must be able to explain every file. Prefer simple, readable code over clever abstractions, and add a one-line docstring explaining *why* each graph tool exists.
13. Log AI-assistant usage in `README.md#ai-disclosure` when you generate substantial code.
