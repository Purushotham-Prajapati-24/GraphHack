# GraphHack Brief: What the Organizers Actually Want

> **Event:** Graph Hacks: Context for AI Agents (WeMakeDevs × FalkorDB)
> **Source pages:** [Overview](https://www.wemakedevs.org/hackathons/falkordb) · [Rules](https://www.wemakedevs.org/hackathons/falkordb/rules) · [Resources](https://www.wemakedevs.org/hackathons/falkordb/resources) · [Schedule](https://www.wemakedevs.org/hackathons/falkordb/schedule) · [Official tutorial blog](https://www.wemakedevs.org/blogs/how-to-build-an-agent-that-reasons-over-a-graph)
> **Researched:** 16 Oct 2026. The hackathon is **live now**.

---

## 0. TL;DR (read this if nothing else)

| Item | Fact |
|---|---|
| Window | **15 Oct 2026 12:01 AM IST → 18 Oct 2026 11:59 PM IST** (hard close) |
| Team | Solo or up to 4. One team per person. |
| Prize pool | $20,000. iPhone 18 Pro (Track 1), PS5 + GTA VI (Track 2), M6 Mac Mini (Track 3), AirPods 5 (best blog post), t-shirts for the top 50 teams |
| Mandatory | **FalkorDB as the primary graph database, doing a central job.** |
| The one-line brief | "Build an agent that **acts on connected data**, **remembers what it learns**, and **shows how it reached each answer**." |
| The killer test | **The removal test:** "If the product still works with FalkorDB removed, the graph counts as decoration." Decoration fails. |
| Open-source tools | **Allowed.** Frameworks, OSS libraries, public APIs, templates, third-party tools, and public datasets are explicitly permitted. |
| AI coding assistants | **Allowed but must be disclosed.** You must be able to explain the graph model, the queries, the architecture and your decisions. |
| Judging rubric | **Not published.** See §6 for what we can reliably infer. |

---

## 1. The problem they are pointing at

Their framing (paraphrased from the Overview page):

- Agents today **see fragments**. They pull a few records or chunks and have to guess how they relate.
- Agents **forget**. They lose track of earlier sessions.
- Agents **miss relationships** between people, systems and records.
- Agents **can't explain** their choices.

**The shift they want:** store context as **nodes and edges** (data, memory and company knowledge) so the agent reasons over real relationships instead of guessing joins.

The official blog states the anti-pattern directly: vector RAG ("embed the question, pull back the closest few chunks") breaks when the answer depends on how several records relate. The model "invents joins", can't persist conclusions, and can't show its work. **The graph traversal path *is* the explanation.**

### The five capabilities they list as "required graph work"

Every strong project should visibly do most of these:

1. **Follow connections across data** (multi-hop traversal)
2. **Remember across sessions** (memory persisted as graph nodes)
3. **Share state between agents** (multiple agents reading/writing one graph)
4. **Connect people, projects and decisions** (an organizational graph)
5. **Show the path behind an answer** (explainability from `nodes(path)`)



If your agent's core question doesn't look like one of these (a question about **relationships**, not a single record), rethink it.

---

## 2. The three tracks: what each one is really asking for

You may enter **one, two or all three** tracks, and you **must name every track** at submission. (The tutorial blog says "you enter one track". The Rules page says "one or more", and the Rules page is authoritative.)

### Track 01: Agents That Act on Connected Data (iPhone 18 Pro)

> "Build an agent that uses the graph to **decide and act**."

- **Examples they give:** investigating fraud, triaging security findings, working through a codebase.
- **Key focus (official):**
  - Multi-hop reasoning
  - Graph queries and **algorithms as agent tools**
  - **Tool selection through MCP**
  - **Actions** based on what the graph shows
  - Explainable results
- **Read between the lines:** a chatbot that only *answers* is weak. The agent must **do something** (open a ticket, freeze an account, page on-call, file a PR, write a finding back to the graph) **because of** what a traversal or algorithm returned.

### Track 02: Agent Memory and Coordination (PS5 + GTA VI)

> "Build agents that **remember across sessions** and **share state**. Memory should persist, update over time, and be available to every agent that needs it."

- **Key focus (official):**
  - **Episodic, semantic and procedural** memory
  - Persistent conversation history
  - Shared state and **handoffs between agents**
  - **High-concurrency reads and writes**
  - **Separate memory per user or tenant**
- **Read between the lines:** they want to see **≥2 agents**, a **second session** that clearly benefits from the first, memory that **changes** (gets updated, superseded or decays), and **tenant isolation** (FalkorDB's multigraph: one graph per tenant). Concurrency is called out, so show parallel agents hitting the graph.

### Track 03: Company Brain (M6 Mac Mini)

> "Build an agent that **understands how a company works**. Connect people, teams, projects, documents and decisions in one graph so the agent can answer questions **and get work done**."

- **Key focus (official):**
  - Knowledge from **docs, tickets and chats** in one graph
  - **Who owns what, and who knows what**
  - **Tracing decisions back to their source**
  - **Keeping knowledge current** as things change
  - Answers with **clear sources**
- **Read between the lines:** ingestion from heterogeneous sources into one graph, provenance on every fact, incremental updates (not a one-shot static import), and an expertise/ownership graph. "Gets work done" means it should also *act* (route a question to the right person, draft an onboarding plan, flag a stale decision).

---

## 3. Where FalkorDB is mandatory, and what "central" means

From the Rules page, verbatim intent:

- FalkorDB **must be the primary graph database** and **must support a central part of the product**.
- **"The graph must do real work."** A visualization layered over ordinary storage **does not qualify**.
- **"If the product still works with FalkorDB removed, the graph counts as decoration."**
- From the Overview page: **"The graph must shape what the agent does, not sit on the side."**

**Practical meaning: FalkorDB must be on the agent's critical path.**

| Must live in FalkorDB | Can live elsewhere |
|---|---|
| The entities and relationships the agent reasons over | Raw file blobs (PDFs, images) as long as their *nodes* live in the graph |
| Agent memory (findings, episodes, facts, procedures) | LLM provider, embedding model |
| Shared state between agents | Frontend, auth, job queue |
| Embeddings used for retrieval (use FalkorDB's **vector index**, don't add Pinecone/Chroma as the primary store) | Logs and telemetry |
| The traversal/algorithm results that drive decisions | |

Deployment options allowed: **Docker, self-hosted, or FalkorDB Cloud** (free tier at app.falkordb.cloud).

---

## 4. Can we use open-source tools? **Yes.** Here's the exact scope.

From the Rules page, "Originality and third-party material":

> Frameworks, open-source libraries, public APIs, templates, third-party tools, and public datasets or assets **are allowed**. The original work completed during the hackathon is what gets judged.

| Question | Answer | Source |
|---|---|---|
| OSS libraries/frameworks (LangChain, LangGraph, LlamaIndex, PyTorch, FastAPI, React…)? | ✅ Yes | Rules |
| FalkorDB ecosystem (GraphRAG-SDK, MCP Server, QueryWeaver, Graphiti, Cognee, Mem0)? | ✅ Yes, and the organizers advertise them | Overview + Resources |
| Public APIs (OpenAI, Anthropic, Gemini, GitHub API…)? | ✅ Yes | Rules |
| Open-weight / local LLMs (Ollama, Llama, Qwen…)? | ✅ Yes (any LLM provider; the blog says "any provider works") | Blog + Rules |
| Templates / boilerplate? | ✅ Yes | Rules + FAQ |
| Public datasets? | ✅ Yes | Rules |
| Any language / framework / frontend / host? | ✅ Yes | Rules + FAQ |
| AI coding assistants (Claude Code, Copilot, Cursor)? | ✅ Yes, **but disclose it** in the README | Rules |
| Continue a pre-existing project? | ⚠️ Only general libs/templates/infra may be reused. **The submission and its main FalkorDB implementation must be new work done during the event.** Main coding/design starts after 15 Oct 12:01 AM IST. Ideas, notes and graph-model sketches may be prepared beforehand. | Rules + FAQ |
| Another graph DB (Neo4j etc.) as primary? | ❌ No. FalkorDB must be primary. | Rules |
| Private / login-protected / paywalled / personal data? | ❌ No. Only **public, synthetic, or your own** data. | Rules |
| Fully AI-generated project with no real understanding? | ❌ "May be rejected." | Rules |

**License notes:**
- **FalkorDB server** is under **SSPLv1** (source-available, "open-source" in their marketing). Using it in a hackathon project is fine. The client libraries are MIT/BSD.
- **No license is required** for your submission, but the repo **must be public**. Recommend adding an **MIT** `LICENSE` file for clarity.
- IP stays with the team. Agree on ownership internally before submitting.

---

## 5. Submission checklist (from the Rules + Schedule pages)

Required:

- [ ] **Public source-code repository**
- [ ] **README** with **setup instructions** and the **graph data model**
- [ ] **The Cypher queries or graph algorithms** the product depends on (put them in the README *and* a `queries/` folder)
- [ ] **Demo video** showing the working project
- [ ] **Live deployment** (preferred) **or** complete local setup instructions plus a working demo video
- [ ] **Track(s) entered**, all named explicitly
- [ ] **AI-assistant disclosure** (which tools, and for what)

Optional but worth it:

- [ ] **Blog post** about the project (separate AirPods 5 prize)
- [ ] Top-50 quality gives every member a t-shirt

---

## 6. How judging will likely work (inferred: **no official rubric is published**)

The Rules, Overview, Schedule and Resources pages publish **no criteria or weights**. The signals below come from the rules text, the track "key focus" lists, and the organizers' own tutorial blog, which says judges trust an agent that **declines when the graph lacks data** more than one that is always confident, and that judging centres on **whether the graph does work the agent couldn't do without it**.

Our best estimate of what evaluators will weigh:

| Likely criterion | What they'll look for | Evidence |
|---|---|---|
| **Graph centrality** (pass/fail gate + heavy weight) | Passes the removal test. Traversals/algorithms drive the agent's decisions. | Rules (explicit) |
| **Track fit** | Hits the track's "key focus" bullets visibly | Track descriptions |
| **Technical depth with FalkorDB** | Multi-hop Cypher, `algo.*` procedures, vector/full-text indexes, multigraph tenancy, MCP | Overview, Resources, blog |
| **Explainability** | Every answer shows its path/sources. No invented facts. | All three tracks + blog |
| **Working product** | Live demo that actually runs. Video shows real queries. | Rules |
| **Agentic behaviour** | Tool selection, actions, multi-agent handoffs, not a static Q&A | Tracks 1 and 2 |
| **Honesty / safety** | "Not in the graph" ≠ "nothing", validated outputs, no model-written Cypher injection | Blog |
| **Originality & usefulness** | A real problem where the answer depends on connections | "Pick one agent problem where the answer depends on connections" |
| **Submission quality** | Clear README, data model diagram, queries listed, clean demo | Rules |

---

## 7. Official resources (from the Resources tab)

| Resource | Link |
|---|---|
| Getting started | https://docs.falkordb.com/getting-started/ |
| Docs | https://docs.falkordb.com |
| Docker / Compose | https://docs.falkordb.com/operations/docker |
| FalkorDB Cloud (no local setup) | https://app.falkordb.cloud |
| FalkorDB Browser (visual query tool, port 3000) | https://docs.falkordb.com/browser/ |
| Cypher reference | https://docs.falkordb.com/cypher/ |
| Known Cypher limitations (**read early**) | https://docs.falkordb.com/cypher/known-limitations |
| Client libraries (Py, Node, Java, Rust, Go, PHP, C#) | https://docs.falkordb.com/getting-started/clients |
| Graph algorithms | https://docs.falkordb.com/algorithms/ |
| Integrations | https://docs.falkordb.com/integration/ |
| GraphRAG-SDK | https://github.com/FalkorDB/GraphRAG-SDK |
| MCP Server | https://github.com/FalkorDB/FalkorDB-MCPServer · `npx -y @falkordb/mcpserver@latest` |
| Agentic memory (Graphiti, Cognee, Mem0) | https://docs.falkordb.com/agentic-memory/ |
| PyTorch Geometric (GNNs on FalkorDB) | https://docs.falkordb.com/integration/pyg |
| Community projects | https://www.falkordb.com/community-projects/ |
| Tutorial blog (**the organizers' reference design**) | https://www.wemakedevs.org/blogs/how-to-build-an-agent-that-reasons-over-a-graph |
| Discord (help + teammates) | https://discord.com/invite/Y2mMT9VdMy |
| Videos | [Effective Cypher](https://www.youtube.com/watch?v=emUQmEitSGY) · [Advanced algorithms](https://www.youtube.com/watch?v=aFkgUT0ubYY) · [Graph & RAG talks](https://www.youtube.com/playlist?list=PL_SzmSBoVe82kQKf5l_hDxu2yj7FEJDHB) · [Cloud setup](https://www.youtube.com/playlist?list=PL_SzmSBoVe82pWDPjSDH8QZP6kGxfVjut) |

---

## 8. Disqualification triggers (avoid at all costs)

- FalkorDB used as decoration (fails the removal test)
- Main code written before 15 Oct 12:01 AM IST
- Private, scraped-behind-login, paywalled or personal data in the graph
- Undisclosed AI-assistant use, or inability to explain your own code
- Plagiarism, judging manipulation, Code of Conduct violations
- Missed deadline (18 Oct 11:59 PM IST, so submit with hours of buffer)

---


