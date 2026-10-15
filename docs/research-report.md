# Centralized Multi-Agent Memory with FalkorDB

## Executive Summary

For a centralized agent-memory platform, FalkorDB should be the authoritative graph of tenants, users, agents, conversations, events, facts, handoffs, skills, provenance, permissions, and relationships, with vectors and full-text indexes used as retrieval accelerators rather than as the source of truth. The recommended topology is one logical graph service with explicit tenant isolation, preferably one graph key per tenant or security domain when cluster sharding and isolation matter, plus a controlled registry graph for cross-tenant metadata; a single graph key can become a write and shard-scaling bottleneck. FalkorDB’s graph traversal, native vector/full-text indexing, read-only query path, replication, clustering, and GraphRAG SDK make it a strong fit, but durability, authorization, deletion, conflict handling, and memory-quality evaluation must be implemented as application-level controls.

## Key Findings

- **Adopt FalkorDB as the centralized relationship and memory layer, not merely as a vector store.**
  - FalkorDB models nodes, relationships, labels, and properties using a property-graph model and exposes OpenCypher through the Redis protocol.
  - Its current documentation lists range, full-text, vector, and graph-specific indexes, plus graph traversal and GraphRAG capabilities. [FalkorDB documentation](https://docs.falkordb.com/)
  - The central graph should answer questions such as:
    - Which agent handled this task?
    - Which user or tenant owns this conversation?
    - Which facts were extracted from which message?
    - Which agent handed work to another agent?
    - Which fact superseded or contradicts another?
    - Which skill produced a successful outcome?
    - Which evidence supports the answer returned to the user?
  - A vector-only architecture cannot represent these relationships as directly or explainably.

- **Use a graph data model that unifies episodic, semantic, procedural, and coordination memory.**
  - Recommended node labels:
    - `Tenant`
    - `User`
    - `Agent`
    - `Conversation`
    - `Session`
    - `Run`
    - `Message`
    - `ToolCall`
    - `Task`
    - `Handoff`
    - `Fact`
    - `Entity`
    - `Skill`
    - `SkillVersion`
    - `Document`
    - `Chunk`
    - `Policy`
    - `Permission`
    - `Source`
  - Recommended relationship types:
    - `BELONGS_TO`
    - `PARTICIPATED_IN`
    - `CONTAINS`
    - `NEXT`
    - `OBSERVED`
    - `PRODUCED`
    - `ABOUT`
    - `EXTRACTED_AS`
    - `SUPPORTS`
    - `CONTRADICTS`
    - `SUPERSEDES`
    - `DERIVED_FROM`
    - `DELEGATED_TO`
    - `HANDOFF_TO`
    - `EXECUTED`
     - `REQUIRES`
     - `AUTHORIZED_FOR`
     - `MENTIONED_IN`
     - `SAME_AS`
     - `SUPPORTED_BY`
  - Store identity, time, confidence, visibility, provenance, validity, and model/schema version as properties on facts and relationships.
  - Keep large raw payloads—such as long documents, images, and oversized tool outputs—in durable object storage when appropriate; store their content hash, URI, metadata, and searchable excerpts in FalkorDB. This preserves graph performance while retaining a complete evidence path.

- **Separate the graph topology from the logical memory taxonomy.**
  - **Episodic memory:** `Message`, `ToolCall`, `Observation`, `Run`, `Task`, `Handoff`, and `Outcome` nodes linked chronologically and causally.
  - **Semantic memory:** `Fact`, `Entity`, `Preference`, `Decision`, and `Policy` nodes linked to their supporting episodes and sources.
  - **Procedural memory:** `Skill`, `SkillVersion`, `Tool`, `Precondition`, `TestCase`, and `Outcome` nodes linked by capability and performance relationships.
  - **Conversation history:** immutable `Conversation` → `Session` → `Message` chains, with summaries and memory projections linked back to the original messages.
  - **Shared state:** `Task`, `Plan`, `Assignment`, `Handoff`, and `Agent` subgraphs with explicit ownership, status, lease, version, and authorization properties.
  - This preserves the distinctions established by [Generative Agents](https://arxiv.org/abs/2304.03442), [Reflexion](https://arxiv.org/abs/2303.11366), and [Voyager](https://arxiv.org/abs/2305.16291) while making the relationships queryable in one graph.

- **Use graph keys deliberately for tenant isolation and horizontal scaling.**
  - FalkorDB clustering distributes Redis keys across hash slots; its documentation states that each graph is a single Redis key and therefore resides entirely on one shard. Different graphs can land on different shards, but one graph is not split across multiple shards. [FalkorDB cluster documentation](https://docs.falkordb.com/operations/cluster/)
  - Recommended topology:
    1. **Control-plane graph:** platform metadata, tenant registry, schema versions, and routing information; keep it small and highly protected.
    2. **Tenant or security-domain graphs:** one graph key per tenant, regulated data domain, or isolation boundary.
    3. **Optional shared knowledge graphs:** curated, non-sensitive global or product knowledge that authorized tenants may read.
  - If the requirement truly demands one central graph key, use `tenant_id`, `user_id`, and authorization predicates on every node and relationship, but recognize that one graph remains a single-shard write domain in a cluster.
  - The best choice depends on cross-tenant traversal requirements, regulatory isolation, tenant size distribution, operational cost, and expected write concurrency.

- **Do not confuse “centralized” with “one unrestricted graph.”**
  - Centralization should mean a common memory service, common schema, common audit model, and common retrieval contract—not that every agent can inspect every tenant’s nodes.
  - For every graph request, derive an immutable security context containing:
    - `tenant_id`;
    - principal/user identity;
    - agent identity;
    - roles and capabilities;
    - project or workspace scope;
    - conversation and run scope;
    - permitted graph keys;
    - allowed read and write operations.
  - The model must never choose or override this context.
  - PostgreSQL row-level security is a useful conceptual reference for default-deny authorization, but it does not protect FalkorDB automatically; FalkorDB authorization must be implemented through deployment ACLs, graph routing, trusted query builders, tenant graph separation, and server-side policy enforcement. [PostgreSQL row security documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

- **Use FalkorDB’s native search capabilities as a multi-path retrieval system.**
  - Use range indexes for exact identifiers, status, version fields, and numeric time representations where supported.
  - Use full-text indexes for names, message excerpts, facts, descriptions, and keyword retrieval.
  - Use vector indexes for semantic similarity over fact text, message/chunk text, entity descriptions, and selected relationship properties.
  - Use Cypher traversal for explicit relationship, temporal, causal, and multi-hop questions.
  - FalkorDB’s vector indexes use HNSW and support cosine or Euclidean similarity; the documentation states that indexed vectors must have a consistent dimension and exposes `efRuntime`, `M`, and `efConstruction` tuning parameters. [FalkorDB vector-index documentation](https://docs.falkordb.com/cypher/indexing/vector-index/)
  - FalkorDB’s full-text indexes support tokenization, stemming, stopwords, prefix matching, fuzzy matching, phonetic search, and TF-IDF-style scores. [FalkorDB full-text documentation](https://docs.falkordb.com/cypher/indexing/fulltext-index/)

- **Recommended retrieval flow for an agent query:**
  1. Resolve the authenticated tenant graph and security context.
  2. Classify the query as conversational, factual, temporal, relational, procedural, or operational.
  3. Search recent episodic nodes for the current conversation and run.
  4. Run graph-safe exact filters for IDs, time ranges, status, and validity.
  5. Run full-text search for explicit names and terms.
  6. Run vector search over facts, entities, chunks, and relevant relationships.
  7. Expand only authorized one- or two-hop neighborhoods around high-confidence entities.
  8. Traverse provenance edges to supporting messages, documents, tool calls, or outcomes.
  9. Resolve `SUPERSEDES`, `CONTRADICTS`, `SAME_AS`, and validity relationships.
  10. Re-rank candidates using semantic score, graph distance, recency, source authority, confidence, importance, and task scope.
  11. Assemble a bounded evidence subgraph and cite the source nodes in the model context.
  12. Abstain when the graph contains insufficient, conflicting, unauthorized, or stale evidence.
  - FalkorDB’s GraphRAG SDK follows a similar multi-path pattern: entity discovery, relationship expansion, vector search, full-text search, source-chunk traversal, optional text-to-Cypher, reranking, and structured context assembly. [GraphRAG SDK retrieval documentation](https://docs.falkordb.com/graphrag/retrieval)

- **Use provenance edges as a first-class correctness mechanism.**
  - Every extracted fact should link to one or more source messages, chunks, tool outputs, or external documents.
  - Every summary should link to the events it summarizes.
  - Every procedural skill should link to the runs and outcomes that justify it.
  - Every answer should retain the IDs of the evidence subgraph used for generation.
  - FalkorDB’s GraphRAG SDK explicitly models `Document`, `Chunk`, `__Entity__`, `PART_OF`, `NEXT_CHUNK`, `MENTIONED_IN`, and relationship facts, preserving a path from extracted knowledge back to source text. [GraphRAG SDK architecture](https://docs.falkordb.com/graphrag/architecture)
  - Provenance allows the system to explain, invalidate, reprocess, or delete a memory without guessing which derived records depend on it.

- **Use immutable event nodes plus versioned projections rather than overwriting facts.**
  - Append `Message`, `ToolCall`, `Observation`, `Decision`, `Outcome`, and `Handoff` nodes.
  - Create or update semantic `Fact` projections using explicit version and validity properties.
  - Represent change using edges such as:
    - `(newFact)-[:SUPERSEDES]->(oldFact)`;
    - `(fact)-[:SUPPORTED_BY]->(source)`;
    - `(fact)-[:CONTRADICTS]->(otherFact)`;
    - `(fact)-[:VALID_DURING]->(timeWindow)`.
  - A new user statement should not erase an older fact; it should create an updated candidate and let a policy or adjudication process determine whether the old fact is superseded.
  - This is especially important for temporal reasoning and knowledge updates, which [LongMemEval](https://arxiv.org/abs/2410.10813) identifies as core long-term memory capabilities.

- **Use parameterized, idempotent Cypher writes.**
  - FalkorDB’s `GRAPH.QUERY` executes OpenCypher queries and supports parameterized queries; the documentation recommends parameters for query-plan reuse and Cypher-injection prevention. [GRAPH.QUERY documentation](https://docs.falkordb.com/commands/graph.query/)
  - Use separate `MERGE` operations for entity nodes and relationship edges so a partial pattern does not create unintended duplicate nodes.
  - FalkorDB’s `MERGE` documentation warns that merging a full path can create duplicates when one path element does not match; bind known endpoints with `MATCH`, then `MERGE` the relationship. [FalkorDB MERGE documentation](https://docs.falkordb.com/cypher/merge/)
  - Use deterministic IDs such as `tenant_id + source_system + external_id` for principals, documents, tasks, and entities where identity is known.
  - Use an idempotency key for every event ingestion and handoff write.

- **Design for FalkorDB’s write and read paths explicitly.**
  - Route all writes to the primary graph owner using `GRAPH.QUERY`.
  - Route safe reads through `GRAPH.RO_QUERY`; FalkorDB documents that this command rejects writes and can be distributed to read replicas in a clustered setup. [GRAPH.RO_QUERY documentation](https://docs.falkordb.com/commands/graph.ro_query/)
  - Treat replica reads as potentially stale because FalkorDB replication is asynchronous. The FalkorDB replication guide describes a single-primary model in which replicas serve read-only traffic and may lag under write load. [FalkorDB replication documentation](https://docs.falkordb.com/operations/replication/)
  - For read-your-writes behavior, route a run to the primary until its required graph version or replication offset is visible, or include the just-written event IDs directly in the current context.
  - Keep graph queries bounded with query timeouts and explicit `LIMIT` values.

- **Use Redis transaction semantics carefully for coordination.**
  - Redis transactions serialize queued commands and execute them sequentially, but Redis does not provide rollback; a command error does not automatically undo other commands in the transaction. [Redis transactions documentation](https://redis.io/docs/latest/develop/using-commands/transactions/)
  - Use `WATCH` for optimistic compare-and-set behavior around mutable coordination keys or version records, and retry on conflict.
  - Prefer a single idempotent `GRAPH.QUERY` for a related graph mutation rather than attempting a distributed transaction across unrelated graph keys.
  - In a cluster, keep commands that must be atomic within the same graph key/shard; do not assume a transaction can atomically span independently sharded tenant graphs.
  - For non-critical derived writes, use an outbox or Redis Stream. Redis Streams provide consumer groups, acknowledgements, pending-message inspection, claiming after consumer failure, and trimming controls. [Redis Streams documentation](https://redis.io/docs/latest/develop/data-types/streams/)

- **Use a durable graph event pipeline for high-concurrency writes.**
  - Synchronous path:
    1. validate the authenticated security context;
    2. validate the event schema;
    3. append the event node and its ownership edges;
    4. record the idempotency key;
    5. return the durable event ID.
  - Asynchronous path:
    1. consume extraction jobs;
    2. create candidate entities and facts;
    3. resolve identities and duplicates;
    4. generate embeddings;
    5. update vector/full-text indexes;
    6. create summaries and procedural candidates;
    7. emit success, retry, or dead-letter status.
  - FalkorDB’s GraphRAG SDK uses batched `UNWIND` writes, with batches of 500 in its documented storage layer, plus per-item fallback when a batch fails. This is a useful starting pattern, not a universal production limit. [GraphRAG SDK storage documentation](https://docs.falkordb.com/graphrag/storage)
  - Measure graph-query queueing, extraction lag, embedding lag, index lag, retry rate, and dead-letter volume separately.

- **Centralize handoffs and shared state in the graph.**
  - A handoff should be a durable `Handoff` node linked to:
    - source `Agent`;
    - destination `Agent`;
    - parent `Task`;
    - originating `Run`;
    - evidence nodes;
    - proposed next action;
    - authorization scope;
    - status;
    - lease owner;
    - expiration time;
    - acknowledgement event.
  - Recommended state transitions are append-only events such as `ASSIGNED`, `STARTED`, `BLOCKED`, `COMPLETED`, `FAILED`, `CANCELLED`, and `ACKNOWLEDGED`, with a derived current status for fast reads.
  - Do not store only a mutable `status` property; retain the transition history to diagnose races, retries, and agent disagreement.
  - Use a lease or claim record to prevent two agents from believing they exclusively own the same task.

- **Represent agent permissions as graph data but enforce them outside model reasoning.**
  - Suggested authorization subgraph:
    - `(principal:User|Agent)-[:HAS_ROLE]->(role:Role)`;
    - `(role)-[:GRANTS]->(permission:Permission)`;
    - `(permission)-[:APPLIES_TO]->(scope:Tenant|Project|Conversation|Skill|Tool)`.
  - The policy engine should calculate an allow/deny decision before constructing Cypher and before returning graph results.
  - Never permit the LLM to generate unrestricted Cypher against a central graph.
  - If text-to-Cypher is enabled, expose a read-only schema subset, validate labels and relationship types against an allowlist, enforce tenant scope in application code, add limits and timeouts, and execute through `GRAPH.RO_QUERY` where possible.
  - [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) warns that retrieved content can influence model behavior and recommends least privilege, separation of untrusted content, validation, adversarial testing, and human approval for high-risk actions.

- **Keep procedural memory as versioned graph-linked capability records.**
  - Model each skill as a `Skill` node and each revision as a `SkillVersion` node.
  - Link a skill version to:
    - supported tasks;
    - required tools;
    - preconditions;
    - input and output schemas;
    - tests;
    - successful and failed runs;
    - approval policy;
    - sandbox profile;
    - superseded versions.
  - Retrieve procedural memory by task type and capability requirements, not only by text similarity.
  - Treat executable code or tool plans as untrusted until tested, sandboxed, and authorized.
  - [Voyager](https://arxiv.org/abs/2305.16291) reports 3.3× more unique items, 2.3× greater travel distance, and up to 15.3× faster progress on selected Minecraft milestones using an executable skill library; these controlled-environment results support the design direction but do not establish enterprise safety or generalization.

- **Use GraphRAG principles, but extend the schema for agent memory.**
  - FalkorDB’s GraphRAG SDK is designed around document ingestion and knowledge-graph retrieval. Its documented pipeline loads and chunks source text, extracts entities and relations, prunes to schema, resolves entities, writes graph data, and indexes chunks and relationships.
  - Its documented graph schema provides a strong provenance foundation: `Document`, `Chunk`, `__Entity__`, `PART_OF`, `NEXT_CHUNK`, `MENTIONED_IN`, and `RELATES`. [GraphRAG SDK architecture](https://docs.falkordb.com/graphrag/architecture)
  - For agent memory, add `Conversation`, `Message`, `Run`, `ToolCall`, `Task`, `Handoff`, `Fact`, `Skill`, `Policy`, and explicit validity/conflict edges.
  - Reuse GraphRAG’s multi-path retrieval idea—vector, full-text, Cypher, entity discovery, relationship expansion, and provenance traversal—but make authorization filtering the first step rather than a post-processing step.
  - Treat the GraphRAG SDK’s claims of benchmark leadership or accuracy as vendor-reported until independently reproduced; use its architecture as implementation guidance, not as proof of universal memory quality.

- **Use graph structure to improve multi-hop and global reasoning, but do not overclaim accuracy.**
  - [Microsoft GraphRAG](https://arxiv.org/abs/2404.16130) builds an entity graph and community summaries, then uses local or global graph-based retrieval; its paper reports improvements over conventional RAG for comprehensiveness and diversity on global questions over approximately 1-million-token datasets.
  - [HippoRAG](https://arxiv.org/abs/2405.14831) combines LLMs, knowledge graphs, and Personalized PageRank; its paper reports up to 20% improvement on selected multi-hop QA settings, with lower cost and latency than an iterative retrieval baseline in its experiments.
  - These are evidence that graph structure can complement vector retrieval, not evidence that every centralized agent-memory workload will improve by the same amount.

- **Treat entity resolution and contradiction handling as core graph operations.**
  - Exact identity should use deterministic keys where available.
  - Fuzzy or LLM-assisted resolution should create candidates and evidence, not silently merge records.
  - Preserve aliases, source IDs, merge decisions, and rejected candidates.
  - Prefer `SAME_AS` or `DISTINCT_FROM` links when identity is uncertain.
  - For conflicting facts, preserve both facts, attach source authority and validity, and derive a current view through policy rather than deleting one fact.
  - A graph makes these decisions inspectable, but it does not make LLM extraction or identity resolution automatically correct.

- **Durability and disaster recovery are separate from graph correctness.**
  - FalkorDB is built on Redis and supports RDB snapshots, AOF logging, and graph-specific `DUMP`/`RESTORE` operations. [FalkorDB durability documentation](https://docs.falkordb.com/operations/durability/)
  - The documentation describes `appendfsync everysec` as a common balance, with a possible window of recent writes at risk, while `appendfsync always` favors durability at greater write cost.
  - Define a recovery point objective and recovery time objective for each memory class:
    - raw messages and task events;
    - derived facts;
    - embeddings and indexes;
    - procedural skills;
    - audit and deletion records.
  - Test restore of a single tenant graph, restore of the control-plane graph, index rebuild, and replay of incomplete extraction jobs.

- **Use replication for read scale and availability, not as a substitute for consistency.**
  - FalkorDB’s replication guide describes a primary that accepts writes and replicas that serve read-only queries; it explicitly notes that replication is asynchronous and may lag. [FalkorDB replication documentation](https://docs.falkordb.com/operations/replication/)
  - Read replicas are appropriate for historical search, analytics, and non-critical retrieval.
  - Primary reads are required when the answer depends on a just-committed handoff, permission revocation, task lease, or fact update.
  - Expose a consistency mode in the retrieval API: `primary`, `bounded_staleness`, or `eventual`.

- **Evaluate the graph memory system at the behavior level.**
  - Required metrics:
    - episodic recall accuracy;
    - semantic fact precision and recall;
    - temporal update accuracy;
    - multi-hop answer accuracy;
    - provenance completeness;
    - contradiction detection;
    - correct abstention;
    - handoff completeness;
    - duplicate entity rate;
    - merge false-positive rate;
    - cross-agent state consistency;
    - primary-to-replica staleness;
    - p95/p99 graph-query latency;
    - vector and full-text recall;
    - graph growth and memory usage;
    - cross-tenant leakage rate;
    - deletion propagation time;
    - prompt-injection success rate;
    - cost per interaction.
  - Include tests for stale facts, concurrent handoffs, duplicate retries, graph-key routing mistakes, failed replicas, partial index coverage, tenant-boundary queries, revoked permissions, malicious stored text, and user deletion requests.

## Contradictions & Debate

- **[HIGH CONFIDENCE] One central service is appropriate; one graph key is not always appropriate.**
  - A common FalkorDB service provides consistent schema, retrieval, auditing, and operational control.
  - FalkorDB’s cluster documentation states that each graph is one Redis key on one shard, so a single graph key cannot distribute its own graph across shards.
  - Conclusion: centralize the platform contract, but choose graph-key boundaries based on tenant isolation and write-scale requirements.

- **[CONFLICTING DATA] One graph per tenant versus one graph for all tenants**
  - A single graph can simplify cross-tenant administration and shared-entity traversal, but it increases the blast radius of query or authorization defects and creates one shard-level write domain.
  - Separate tenant graphs improve routing and isolation, but cross-tenant analytics and shared knowledge require explicit federation or controlled shared graphs.
  - Conclusion: default to one graph per tenant or security domain, with separate shared knowledge graphs and a small control-plane graph; use a single graph only when cross-tenant traversal is a firm requirement and the security model is independently tested.

- **[HIGH CONFIDENCE] Graph retrieval complements vectors; it does not replace them.**
  - [Microsoft GraphRAG](https://arxiv.org/abs/2404.16130) and [HippoRAG](https://arxiv.org/abs/2405.14831) report gains from entity graphs and graph-aware retrieval on selected multi-hop or global-query tasks.
  - FalkorDB supports vector, full-text, range, and graph traversal capabilities in the same platform.
  - Conclusion: use hybrid retrieval. Graph traversal is strongest for explicit relationships, constraints, and multi-hop reasoning; vectors remain valuable for semantic similarity and fuzzy entry-point discovery.

- **[CONFLICTING DATA] LLM-generated text-to-Cypher improves structural coverage but increases risk and latency.**
  - FalkorDB’s GraphRAG SDK documents an optional text-to-Cypher path for structural questions and validates or limits generated queries.
  - Generated queries can be wrong, expensive, injection-sensitive, or outside the tenant’s authorization scope.
  - Conclusion: keep text-to-Cypher read-only and opt-in, expose a restricted schema, enforce tenant scope outside the model, impose timeouts and limits, and measure its marginal accuracy against its latency and failure cost.

- **[HIGH CONFIDENCE] Redis transaction atomicity does not provide rollback semantics.**
  - Redis transactions serialize queued commands, but Redis documents that it does not support rollbacks and that command errors do not undo other successful commands in the transaction.
  - Conclusion: design graph writes to be idempotent, validate before `EXEC`, use `WATCH` for compare-and-set, and add compensating events for repair rather than assuming database rollback.

- **[CONFLICTING DATA] Replication improves reads but can return stale memory.**
  - FalkorDB documents read-only replicas and asynchronous replication, which are appropriate for read scale and availability.
  - A just-completed agent handoff, revoked permission, or superseding fact cannot safely depend on an arbitrary replica’s freshness.
  - Conclusion: expose consistency modes and route correctness-critical reads to the primary.

- **[HIGH CONFIDENCE] Graph provenance reduces hallucination risk but does not eliminate it.**
  - A source path from answer to fact to message/document makes evidence inspectable and supports abstention.
  - Extraction, entity resolution, graph traversal, and final generation can still be wrong or manipulated.
  - Conclusion: require evidence IDs, source authority, validity, and an abstention path; do not equate graph presence with truth.

- **[CONFLICTING DATA] Graph centralization versus raw-content retention**
  - Keeping messages and excerpts in the graph simplifies provenance and retrieval.
  - Storing large or sensitive payloads directly in a shared in-memory graph may increase memory cost, retention risk, and deletion complexity.
  - Conclusion: keep graph-native identifiers, metadata, excerpts, hashes, and relationships in FalkorDB; store large canonical payloads in a durable content store when scale or compliance requires it.

## Blind Spots & Missing Info

- FalkorDB documentation describes graph-key sharding but does not establish a universal graph-key topology for agent memory; the correct tenant boundary depends on workload and compliance constraints.
- Public documentation provides limited independent evidence for multi-tenant FalkorDB performance under simultaneous graph writes, high-cardinality relationships, large vector indexes, and heavy graph traversal.
- The GraphRAG SDK’s documented benchmark figures are implementation-specific and vendor-reported; they should be independently reproduced on the intended agent-memory schema and workload.
- FalkorDB’s native vector-index documentation notes that vector queries do not combine well with property filters; tenant filtering and authorization should therefore be validated with realistic query plans and possibly separate graph keys or indexes.
- The exact atomicity and isolation boundary between a single `GRAPH.QUERY`, Redis `MULTI/EXEC`, graph mutations, and clustered graph keys requires validation against the deployed FalkorDB version and client library rather than assumption from generic Redis or Neo4j behavior.
- Replica lag, failover behavior, backup restore time, and graph-index rebuild time are deployment-dependent and need measurement under production-like data volume.
- A central graph does not solve the semantic problem of deciding whether two extracted entities are the same real-world entity or whether a new fact supersedes an old one.
- There is no broadly adopted benchmark combining long-term conversation memory, graph traversal, concurrent multi-agent handoffs, tenant isolation, permission revocation, deletion propagation, and adversarial memory poisoning.
- Academic memory studies frequently use controlled or curated conversations and do not establish performance for noisy enterprise agent traces, tool failures, policy changes, or hundreds of concurrent agents.
- Privacy, retention, data residency, consent, and user-erasure requirements vary by jurisdiction and industry; FalkorDB’s persistence and deletion mechanisms do not independently establish legal compliance.
- I found no reliable public evidence establishing zero hallucinated memories, zero cross-tenant leakage, perfect deletion propagation, or linear write scaling for a single centralized FalkorDB graph under all failure modes.

## References

### FalkorDB official documentation and product sources

- **docs.falkordb.com** — FalkorDB platform overview, property graphs, OpenCypher, indexes, vector search, GraphRAG, and supported protocols. [Source](https://docs.falkordb.com/)
- **docs.falkordb.com** — FalkorDB Cypher language and compatibility coverage. [Source](https://docs.falkordb.com/cypher/)
- **docs.falkordb.com** — FalkorDB vector indexing, HNSW parameters, supported dimensions, similarity functions, and query procedures. [Source](https://docs.falkordb.com/cypher/indexing/vector-index/)
- **docs.falkordb.com** — FalkorDB full-text indexing, stemming, fuzzy/prefix search, phonetics, and scoring. [Source](https://docs.falkordb.com/cypher/indexing/fulltext-index/)
- **docs.falkordb.com** — FalkorDB `GRAPH.QUERY`, parameterized queries, query timeouts, and query plan caching. [Source](https://docs.falkordb.com/commands/graph.query/)
- **docs.falkordb.com** — FalkorDB `GRAPH.RO_QUERY`, read-only enforcement, read replicas, and query timeouts. [Source](https://docs.falkordb.com/commands/graph.ro_query/)
- **docs.falkordb.com** — FalkorDB `MERGE`, idempotency patterns, and duplicate-path cautions. [Source](https://docs.falkordb.com/cypher/merge/)
- **docs.falkordb.com** — FalkorDB clustering, Redis hash slots, graph-key placement, and the fact that a single graph is not split across shards. [Source](https://docs.falkordb.com/operations/cluster/)
- **docs.falkordb.com** — FalkorDB replication, primary/replica architecture, read scaling, and asynchronous lag. [Source](https://docs.falkordb.com/operations/replication/)
- **docs.falkordb.com** — FalkorDB RDB, AOF, `DUMP`/`RESTORE`, and durability trade-offs. [Source](https://docs.falkordb.com/operations/durability/)
- **docs.falkordb.com** — GraphRAG SDK overview, ingestion, hybrid retrieval, citations, and incremental graph updates. [Source](https://docs.falkordb.com/genai-tools/graphrag-sdk/)
- **docs.falkordb.com** — GraphRAG SDK ingestion/retrieval architecture, provenance chain, graph schema, and multi-path retrieval. [Source](https://docs.falkordb.com/graphrag/architecture)
- **docs.falkordb.com** — GraphRAG SDK multi-path retrieval, relationship expansion, text-to-Cypher, reranking, and context assembly. [Source](https://docs.falkordb.com/graphrag/retrieval)
- **docs.falkordb.com** — GraphRAG SDK GraphStore, VectorStore, batched `UNWIND`/`MERGE`, vector indexes, and entity resolution. [Source](https://docs.falkordb.com/graphrag/storage)

### Academic and research sources

- **arxiv.org** — Park et al., “Generative Agents: Interactive Simulacra of Human Behavior,” submitted 7 April 2023, revised 6 August 2023. [Source](https://arxiv.org/abs/2304.03442)
- **arxiv.org** — Shinn et al., “Reflexion: Language Agents with Verbal Reinforcement Learning,” submitted 20 March 2023, revised 10 October 2023. [Source](https://arxiv.org/abs/2303.11366)
- **arxiv.org** — Wang et al., “Voyager: An Open-Ended Embodied Agent with Large Language Models,” submitted 25 May 2023, revised 19 October 2023. [Source](https://arxiv.org/abs/2305.16291)
- **arxiv.org** — Liu et al., “Lost in the Middle: How Language Models Use Long Contexts,” submitted 6 July 2023, revised 20 November 2023; published in TACL. [Source](https://arxiv.org/abs/2307.03172)
- **arxiv.org** — Maharana et al., “Evaluating Very Long-Term Conversational Memory of LLM Agents,” submitted 27 February 2024. [Source](https://arxiv.org/abs/2402.17753)
- **arxiv.org** — Wu et al., “LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory,” submitted 14 October 2024, revised 4 March 2025; listed as ICLR 2025. [Source](https://arxiv.org/abs/2410.10813)
- **arxiv.org** — Edge et al., “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” submitted 24 April 2024, revised 19 February 2025. [Source](https://arxiv.org/abs/2404.16130)
- **arxiv.org** — Gutiérrez et al., “HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models,” submitted 23 May 2024, revised 14 January 2025; NeurIPS 2024. [Source](https://arxiv.org/abs/2405.14831)

### Redis, database, and security sources

- **redis.io** — Redis transactions, serialized command execution, lack of rollback, and `WATCH`-based optimistic locking. [Source](https://redis.io/docs/latest/develop/using-commands/transactions/)
- **redis.io** — Redis Streams, consumer groups, acknowledgements, pending messages, claiming, and trimming. [Source](https://redis.io/docs/latest/develop/data-types/streams/)
- **redis.io** — Redis replication, asynchronous replication, read replicas, offsets, and failover considerations. [Source](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)
- **postgresql.org** — PostgreSQL row-level security policies and default-deny behavior. [Source](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- **genai.owasp.org** — OWASP LLM01:2025 Prompt Injection, including indirect injection, least privilege, content segregation, validation, and human approval. [Source](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
