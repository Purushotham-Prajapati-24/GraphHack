# Track 3 Research Report: Company Brain with FalkorDB

**Selected track:** Company Brain

**Research question:** How should a FalkorDB-centered Company Brain connect people, teams, projects, documents, tickets, chats, decisions, ownership, expertise, and changing organizational knowledge so an agent can answer questions, take authorized actions, and provide clear source evidence?

## Executive Summary

A trustworthy Company Brain should be an evidence-linked organizational graph, not a document chatbot: FalkorDB should represent people, teams, projects, work items, documents, conversations, decisions, capabilities, ownership, permissions, and temporal changes as connected entities that the agent actively traverses. The most defensible architecture combines graph traversal with full-text and vector retrieval, preserves provenance from every answer back to source passages or system records, and treats ownership, access control, freshness, and contradiction handling as first-class graph concerns. The evidence supports GraphRAG for multi-hop and corpus-level questions, but current benchmarks show that retrieval systems still struggle with dynamic, complex, long-tail facts; therefore the product must expose confidence, cite sources, and abstain when the graph cannot support a claim.

## Key Findings

- **A Company Brain is fundamentally a relationship problem.**
  - The core questions are not only “What does this document say?” but also:
    - Who owns this project?
    - Which team maintains this service?
    - Who has worked on a similar incident?
    - Which decision changed the current roadmap?
    - What evidence led to that decision?
    - Which ticket, document, or conversation records the latest status?
    - What changed since the previous plan?
  - These questions require links between entities and time-aware facts. FalkorDB should therefore be the primary graph database and should perform the product’s core retrieval, explanation, ownership, and decision-tracing work.
  - If FalkorDB were removed and the product still delivered the same value through flat documents and a separate vector database, the graph would be decorative rather than central.

- **Use one canonical graph model with source-specific ingestion adapters.**
  - A Company Brain may ingest from documentation, issue trackers, source repositories, chat, project-management tools, incident systems, and organizational directories.
  - Do not create a separate disconnected schema for each connector. Normalize all sources into a shared ontology while retaining source-specific identifiers and URLs.
  - Example canonical node labels:
    - `Organization`
    - `Person`
    - `Team`
    - `Role`
    - `Project`
    - `Product`
    - `Service`
    - `Repository`
    - `Document`
    - `DocumentVersion`
    - `Chunk`
    - `Conversation`
    - `Message`
    - `Ticket`
    - `Issue`
    - `PullRequest`
    - `Commit`
    - `Decision`
    - `Goal`
    - `Milestone`
    - `Incident`
    - `Skill`
    - `Topic`
    - `SourceSystem`
    - `PermissionScope`
    - `Evidence`
    - `ChangeEvent`
  - Example relationship types:
    - `MEMBER_OF`
    - `REPORTS_TO`
    - `LEADS`
    - `OWNS`
    - `MAINTAINS`
    - `CONTRIBUTES_TO`
    - `ASSIGNED_TO`
    - `PART_OF`
    - `DEPENDS_ON`
    - `BLOCKS`
    - `IMPLEMENTS`
    - `MENTIONS`
    - `DISCUSSED_IN`
    - `DOCUMENTS`
    - `EVIDENCED_BY`
    - `SUPPORTED_BY`
    - `CONTRADICTS`
    - `SUPERSEDES`
    - `DECIDED_IN`
    - `PROPOSED_BY`
    - `APPROVED_BY`
    - `REJECTED_BY`
    - `RELEVANT_TO`
    - `HAS_VERSION`
    - `DERIVED_FROM`
    - `SYNCHRONIZED_FROM`
    - `VISIBLE_TO`
    - `HAS_PERMISSION`
  - The precise ontology should be deliberately narrower than the entire company vocabulary at first. A constrained ontology reduces extraction noise and makes graph queries explainable.

- **Represent facts as attributed, temporal claims rather than unqualified properties.**
  - “Alice owns Project Atlas” should not be stored only as a mutable property on `Project`.
  - Store a claim or relationship with:
    - `source_system`;
    - `source_record_id`;
    - `source_url`;
    - `observed_at`;
    - `valid_from`;
    - `valid_until`;
    - `confidence`;
    - `authority` or source priority;
    - `extraction_method`;
    - `last_verified_at`;
    - `schema_version`;
    - `content_hash`;
    - `visibility_scope`.
  - Preserve competing claims instead of silently overwriting them. Derive the “current” view through a deterministic policy that considers validity, source authority, recency, and explicit supersession.
  - This is consistent with the W3C PROV model, which defines provenance as information about entities, activities, and people involved in producing data and identifies versioning, derivation, reproducibility, and procedure representation as provenance requirements. [W3C PROV overview](https://www.w3.org/TR/prov-overview/)

- **Ownership and expertise require different edge types.**
  - “Who owns what?” should use authoritative organizational or work-management signals:
    - `(Person)-[:OWNS]->(Project)`;
    - `(Team)-[:MAINTAINS]->(Service)`;
    - `(Person)-[:ASSIGNED_TO]->(Ticket)`;
    - `(Team)-[:RESPONSIBLE_FOR]->(Capability)`.
  - “Who knows what?” should be modeled as evidence-backed expertise, not as a permanent inferred label:
    - `(Person)-[:CONTRIBUTED_TO]->(Repository)`;
    - `(Person)-[:RESOLVED]->(Incident)`;
    - `(Person)-[:AUTHORED]->(Document)`;
    - `(Person)-[:DISCUSSED]->(Topic)`;
    - `(Person)-[:REVIEWED]->(PullRequest)`.
  - Add `evidence_count`, `last_seen_at`, `recency_decay`, `role_context`, and `confidence` to expertise edges or supporting claim nodes.
  - Distinguish “current owner,” “historical contributor,” “frequent author,” and “subject-matter expert.” They are not interchangeable.

- **Decision tracing should be a graph-native user experience.**
  - A decision response should be able to traverse:
    - `Decision` → `DECIDED_IN` → `Conversation` or `Meeting`;
    - `Decision` → `SUPPORTED_BY` → `Document`, `Message`, `Ticket`, or `Metric`;
    - `Decision` → `AFFECTS` → `Project`, `Service`, `Goal`, or `Team`;
    - `Decision` → `SUPERSEDES` → prior `Decision`;
    - `Decision` → `PROPOSED_BY` / `APPROVED_BY` → `Person` or `Role`.
  - The final answer should show a concise conclusion and an expandable evidence path with source names, timestamps, links, and relevant excerpts.
  - Do not cite only an LLM-generated summary. Cite the source record and the exact chunk, message, ticket, or decision entry that supports the claim.

- **FalkorDB’s GraphRAG architecture provides a strong baseline for Company Brain ingestion.**
  - FalkorDB’s GraphRAG SDK documents a pipeline of load, chunk, lexical graph creation, extraction, schema pruning, resolution, batched writes, mention-edge creation, and embedding/index updates. [FalkorDB GraphRAG architecture](https://docs.falkordb.com/graphrag/architecture)
  - Its documented source graph uses `Document`, `Chunk`, `__Entity__`, `PART_OF`, `NEXT_CHUNK`, `MENTIONED_IN`, and `RELATES` structures.
  - For a Company Brain, extend that baseline with organizational and operational nodes: `Person`, `Team`, `Project`, `Ticket`, `Decision`, `Conversation`, `Repository`, `Service`, `Incident`, `Goal`, and `PermissionScope`.
  - Keep the lexical source chain intact even after entity resolution, because entity and relationship claims must remain traceable to the original source.

- **Use hybrid retrieval rather than vector-only search.**
  - Use exact graph lookup for IDs, project keys, ticket numbers, repository names, and current ownership.
  - Use full-text search for names, terms, acronyms, document titles, messages, and issue text.
  - Use vector search for semantically similar documents, descriptions, decisions, incident narratives, and expertise evidence.
  - Use Cypher traversal for multi-hop organizational questions:
    - “Which team owns the service used by Project Atlas?”
    - “Which decision caused the roadmap item to move?”
    - “Who worked on incidents related to this repository?”
    - “Which projects depend on the service maintained by Team Delta?”
  - FalkorDB supports range, full-text, and vector indexes, with vector search over nodes and relationships. [FalkorDB indexing overview](https://docs.falkordb.com/cypher/indexing/)
  - FalkorDB full-text search supports stemming, stopwords, prefix and fuzzy matching, phonetic search, and relevance scores. [FalkorDB full-text indexing](https://docs.falkordb.com/cypher/indexing/fulltext-index/)
  - FalkorDB vector indexes use HNSW and support cosine or Euclidean similarity; the documentation describes dimension, `M`, `efConstruction`, and `efRuntime` parameters. [FalkorDB vector indexing](https://docs.falkordb.com/cypher/indexing/vector-index/)

- **A recommended Company Brain query pipeline is policy-first and graph-first.**
  1. Authenticate the requester and resolve organization, workspace, team, and permission scope.
  2. Identify the question type: ownership, expertise, project status, decision rationale, dependency, historical change, or document synthesis.
  3. Resolve exact identifiers and named entities through range and full-text indexes.
  4. Run vector retrieval over relevant documents, facts, decisions, incidents, and relationship evidence.
  5. Expand authorized graph neighborhoods around high-confidence people, teams, projects, services, and decisions.
  6. Apply temporal filters to exclude superseded or expired claims unless the user asks for history.
  7. Traverse provenance edges to source passages, tickets, messages, repository events, or meeting records.
  8. Re-rank by source authority, freshness, graph path relevance, semantic score, and permission scope.
  9. Detect conflicting or stale claims.
  10. Generate a bounded answer with source citations and an uncertainty statement where needed.
  11. For action requests, require a separate authorization and confirmation step; retrieval must not implicitly grant write permission.
  - FalkorDB’s GraphRAG SDK describes a similar multi-path pipeline using entity discovery, relationship expansion, vector retrieval, full-text retrieval, source-chunk traversal, optional text-to-Cypher, reranking, and structured context assembly. [FalkorDB multi-path retrieval](https://docs.falkordb.com/graphrag/retrieval)

- **GraphRAG is especially relevant to global Company Brain questions.**
  - A question such as “What are the company’s main strategic priorities and how do they affect engineering?” is not a single-document lookup.
  - [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130) builds an entity graph, forms communities of related entities, pre-generates community summaries, and combines partial responses for global corpus-level questions.
  - The paper reports substantial improvements over a conventional RAG baseline for comprehensiveness and diversity on a class of global questions over datasets in the 1-million-token range.
  - For a Company Brain, community summaries could represent domains such as engineering, sales, security, product, or a project portfolio, but summaries must retain links to the underlying decisions and documents.
  - Do not treat community summaries as authoritative facts. They are derived navigation and synthesis artifacts that must be refreshable from source claims.

- **Graph-based retrieval is promising for multi-hop questions but not universally superior.**
  - [HippoRAG](https://arxiv.org/abs/2405.14831) combines language models, knowledge graphs, and Personalized PageRank for long-term knowledge integration.
  - In its reported experiments, HippoRAG improved selected multi-hop QA results by up to 20% and was reported as 10–30 times cheaper and 6–13 times faster than an iterative retrieval comparison in some settings.
  - These figures are benchmark-specific and should not be generalized to an enterprise Company Brain without reproducing them on company-style data, permissions, temporal updates, and noisy documents.
  - The practical conclusion is narrower: graph propagation can help connect related facts that independent chunk similarity misses.

- **A Company Brain needs temporal modeling because organizational knowledge changes continuously.**
  - Store both event time and ingestion time. A document may describe an older decision while being uploaded later.
  - Track source version, content hash, last-modified timestamp, and synchronization cursor.
  - Model lifecycle edges and states:
    - `(newOwner)-[:SUPERSEDES]->(oldOwnerClaim)`;
    - `(newDecision)-[:SUPERSEDES]->(oldDecision)`;
    - `(Project)-[:HAS_STATUS]->(StatusClaim)`;
    - `(DocumentVersion)-[:REVISION_OF]->(DocumentVersion)`;
    - `(ChangeEvent)-[:CHANGED]->(Document|Ticket|Project|Decision)`.
  - Every answer should be able to distinguish “current as of now,” “current as of a date,” and “what was believed at that time.”
  - [LongMemEval](https://arxiv.org/abs/2410.10813) identifies knowledge updates and temporal reasoning as separate long-term memory capabilities and reports a roughly 30% accuracy drop for commercial assistants and long-context models on sustained-interaction memory.

- **Incremental synchronization is a core requirement, not an operational detail.**
  - A Company Brain built once from documents will become misleading as projects, owners, tickets, and decisions change.
  - FalkorDB’s GraphRAG SDK documents `update()`, `delete_document()`, `apply_changes()`, and `finalize()` primitives for incremental graph updates, orphan cleanup, re-indexing, and crash-safe cutover. [FalkorDB incremental updates](https://docs.falkordb.com/graphrag/incremental-updates)
  - The documented model keeps document content hashes, chunks, mention edges, and relationship provenance. It removes stale relationships sourced only from deleted chunks while preserving entities still referenced elsewhere.
  - The documented `apply_changes()` flow processes deletes, updates, and additions in a controlled order and warns that concurrent updates should be serialized unless shared-entity safety is independently guaranteed.
  - For connectors such as Slack, Jira, GitHub, or SharePoint, use source-native event IDs, updated timestamps, pagination cursors, webhooks, or change tokens to drive idempotent updates.

- **Connector ingestion must preserve source permissions.**
  - A Company Brain should not become a permission bypass by aggregating documents that a user could not access in the original system.
  - Slack’s Events API documentation states that delivered events are tied to OAuth scopes and that apps receive only events visible to users who authorized the app; private-channel visibility depends on the authorized user’s access. [Slack Events API](https://docs.slack.dev/apis/events-api)
  - Jira’s Cloud REST documentation states that operations require permissions and that access can be granted through users, groups, project roles, and issue roles. [Jira Cloud REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
  - Microsoft Graph’s SharePoint API exposes sites, lists, drives, list items, creators, modifiers, timestamps, and resource identifiers; applications should preserve these access and provenance attributes when ingesting. [Microsoft Graph SharePoint resources](https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0)
  - Each graph node or claim should carry a source access scope such as workspace, channel, project, repository, site, folder, document, or ticket visibility.
  - Retrieval should apply permission filtering before returning graph results or embeddings to the model. Post-filtering after generation is too late.

- **Treat connector events as an ingestion log, not as direct truth.**
  - Event delivery can be delayed, retried, duplicated, rate-limited, or incomplete.
  - Slack documents a three-second acknowledgement expectation, up to three retries with backoff, and an app-level rate limit of 30,000 events per workspace per 60 minutes. [Slack Events API](https://docs.slack.dev/apis/events-api)
  - Use an ingestion envelope with:
    - `source_system`;
    - `source_workspace`;
    - `source_event_id`;
    - `source_record_id`;
    - `source_version` or update timestamp;
    - `received_at`;
    - `processed_at`;
    - `payload_hash`;
    - `permission_snapshot`;
    - `processing_status`;
    - `retry_count`.
  - A connector should acknowledge quickly, enqueue the event, deduplicate by source event ID, and process graph writes asynchronously.
  - Keep a dead-letter path and reconciliation job that compares the graph’s synchronization cursor with the source system.

- **Use canonical identity resolution for people, teams, projects, and systems.**
  - The same person may appear under an email address, employee ID, Slack user ID, GitHub handle, Jira account ID, or display name.
  - The same project may appear under a roadmap name, Jira key, repository name, document folder, or chat channel.
  - Use deterministic external identifiers wherever possible:
    - `(Person {org_id, canonical_id})`;
    - `(Project {org_id, canonical_id})`;
    - `(SourceRecord {source_system, source_workspace, source_id})`.
  - Preserve aliases and external references with `ALIAS_OF`, `IDENTIFIED_AS`, or source-reference properties.
  - For ambiguous matches, create a candidate `SAME_AS` claim with confidence and evidence; do not merge merely because names are similar.
  - Keep `DISTINCT_FROM` evidence for known non-matches to prevent repeated or unsafe reconciliation.

- **Model decisions as first-class organizational knowledge.**
  - A `Decision` node should contain:
    - `decision_id`;
    - title and statement;
    - status such as proposed, approved, rejected, superseded, or disputed;
    - decision date;
    - effective date;
    - review date;
    - scope;
    - confidence;
    - source authority;
    - owner;
    - content hash and schema version.
  - Link decisions to:
    - alternatives considered;
    - constraints and goals;
    - approvers and participants;
    - projects, services, teams, and risks affected;
    - source meeting, document, ticket, or message;
    - later outcomes and reversals.
  - This allows questions such as “Why did we choose PostgreSQL?” to return both the decision and the supporting reasoning, while “Is that still current?” can traverse supersession and review edges.

- **Distinguish evidence from inference.**
  - Evidence nodes represent source facts such as a ticket assignment, an explicit document statement, a dated meeting message, or a repository commit.
  - Inferred nodes represent model-produced conclusions such as “Alice is likely the expert on service X.”
  - Store `assertion_type` values such as `source_fact`, `extracted_fact`, `derived_fact`, `summary`, and `recommendation`.
  - Never present a derived expertise score or inferred owner as if it were an explicit organizational record.
  - A generated answer should state whether a conclusion is directly documented, inferred from activity, or uncertain.

- **Source-linked answers reduce unsupported generation but do not guarantee truth.**
  - FalkorDB’s GraphRAG grounding guidance explicitly states that retrieval techniques reduce unsupported answers but do not eliminate hallucinations.
  - It identifies common failure modes: missing connecting facts, topically similar but non-answer-bearing chunks, and models filling gaps when context is incomplete. [FalkorDB grounding guidance](https://docs.falkordb.com/graphrag/reducing-llm-hallucinations)
  - The documented SDK uses `MENTIONED_IN` edges to trace entities to source chunks and supports returning retrieval context for inspection.
  - Implement an explicit abstention path. If no sufficiently relevant, authorized, current evidence exists, return a fixed evidence-insufficient response rather than a plausible guess.
  - Log the answer, graph query, evidence node IDs, source URLs, source versions, and retrieval scores for later review.

- **Long context is not a substitute for graph-based retrieval.**
  - [Lost in the Middle](https://arxiv.org/abs/2307.03172) found that language-model performance can degrade when relevant information is placed in the middle of long contexts, even for long-context models.
  - [Large Language Models Can Be Easily Distracted by Irrelevant Context](https://arxiv.org/abs/2302.00093), published at ICML 2023, reported that irrelevant context can dramatically reduce model performance on its evaluation task.
  - A Company Brain should therefore select a small, structured evidence subgraph instead of appending large undifferentiated archives to every prompt.
  - Rank evidence by authority and graph relevance, not only embedding similarity.

- **A practical FalkorDB Company Brain architecture has five layers.**
  1. **Connector layer:** Slack, Jira, GitHub, SharePoint, document stores, calendars, incident systems, and HR/organizational directories.
  2. **Ingestion and normalization layer:** source adapters, event deduplication, pagination, permission capture, content hashing, identity mapping, and change cursors.
  3. **FalkorDB graph layer:** canonical nodes, relationships, temporal claims, provenance, permissions, decision records, ownership, and derived summaries.
  4. **Retrieval and reasoning layer:** exact lookup, full-text search, vector search, Cypher traversal, evidence expansion, conflict resolution, freshness checks, and abstention.
  5. **Agent action layer:** read-only answers by default, with separately authorized actions such as creating a ticket, assigning work, updating a project, or requesting an approval.
  - The agent should never access source systems directly using arbitrary model-generated API calls. Tools should be typed, scope-limited, auditable, and validated by application code.

- **Use graph-key boundaries deliberately.**
  - FalkorDB clustering distributes Redis keys across hash slots, and its documentation states that each graph is a single Redis key located on one shard; different graphs can distribute across shards, but a single graph is not split across shards. [FalkorDB cluster documentation](https://docs.falkordb.com/operations/cluster/)
  - Recommended deployment options:
    - one Company Brain graph per organization or security domain;
    - separate control-plane graph for connector credentials, tenant routing, and schema versions;
    - optional shared public or product-knowledge graph for data permitted across organizations;
    - separate regulated or high-sensitivity graphs when isolation requirements justify them.
  - A single graph for every organization can simplify cross-company administration but increases blast radius and may turn one graph key into a write and shard-scaling bottleneck.
  - Centralization should mean a central service, ontology, audit trail, and retrieval contract—not unrestricted access to one global graph.

- **Enforce access control before graph retrieval.**
  - The security context should be derived from authenticated credentials and source-system permissions, not from the user’s wording or the model’s decision.
  - Every query should be constrained by:
    - organization or tenant;
    - principal identity;
    - workspace or project scope;
    - source-system access;
    - channel, folder, repository, or issue permissions;
    - data classification;
    - current permission version.
  - Apply filters before vector retrieval and before graph expansion. Otherwise a private node can influence candidates, reranking, summaries, or model outputs even if the final answer is filtered later.
  - Preserve a `VISIBLE_TO` or `ACCESSIBLE_IN` claim path from a source record to the principal or scope. Cache keys, embeddings, summaries, and community reports must also be permission-aware.
  - Revocation should trigger graph and index updates, cache invalidation, and a verification query proving that the record is no longer retrievable.

- **Treat retrieved company content as untrusted input to the model.**
  - Documents, chat messages, tickets, and comments can contain text that looks like instructions to an agent.
  - [Greshake et al.](https://arxiv.org/abs/2302.12173) demonstrated indirect prompt-injection attacks in which attackers place malicious instructions in data likely to be retrieved by LLM-integrated applications; the paper discusses data theft, ecosystem contamination, arbitrary behavior, and API-control risks.
  - [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) recommends least privilege, external-content segregation, output validation, human approval for high-risk actions, and adversarial testing.
  - Separate system instructions from retrieved data using explicit typed context sections.
  - Treat retrieved text as evidence, never as executable instruction.
  - Strip or quarantine suspicious instructions when they are irrelevant to the user’s question.
  - Use deterministic policy code for all writes, API calls, permission changes, and destructive operations.

- **Keep write actions outside the answer-generation path.**
  - A Company Brain may eventually “get work done,” but reading knowledge and changing systems have different risk levels.
  - Recommended action flow:
    1. retrieve graph evidence;
    2. propose a typed action with target, fields, source evidence, and expected effect;
    3. validate authorization and business rules;
    4. show a confirmation or request human approval for consequential changes;
    5. execute through a pre-defined connector function;
    6. record the request, approval, tool call, result, and follow-up status in FalkorDB.
  - A write should create an auditable `Action` or `ChangeEvent` node linked to the agent, principal, target object, evidence, and external-system response.

- **Use parameterized Cypher and bounded traversals.**
  - FalkorDB’s `GRAPH.QUERY` documentation supports parameterized queries and recommends them for execution-plan reuse and Cypher-injection prevention. [FalkorDB GRAPH.QUERY](https://docs.falkordb.com/commands/graph.query/)
  - Use `GRAPH.RO_QUERY` for safe read paths where appropriate; FalkorDB documents that it rejects write queries and can be distributed to read replicas. [FalkorDB GRAPH.RO_QUERY](https://docs.falkordb.com/commands/graph.ro_query/)
  - If text-to-Cypher is enabled:
    - expose only an allowlisted ontology;
    - permit read-only queries by default;
    - inject tenant and permission predicates outside the model;
    - reject unknown labels and relationship types;
    - enforce `LIMIT` and query timeouts;
    - deny schema-changing or write clauses;
    - log the generated query and validation decision.
  - Do not interpolate user-provided or model-generated labels, relationship types, property names, or values directly into Cypher.

- **Use idempotent, versioned graph writes for freshness and concurrency.**
  - Store a source cursor or version on every synchronized `Document`, `Ticket`, `Message`, `Issue`, and `Decision` node.
  - Reject an older source update if a newer version has already been applied.
  - Use deterministic identity and source-event idempotency keys to prevent duplicate ingestion.
  - Use `MERGE` for known entities and relationships, but bind endpoints separately. FalkorDB’s `MERGE` documentation warns that a full-path merge can create duplicate nodes when part of the path fails to match. [FalkorDB MERGE](https://docs.falkordb.com/cypher/merge/)
  - Keep raw source events or synchronization records so a failed extractor or ontology upgrade can replay the source without refetching everything.

- **Use asynchronous ingestion with explicit freshness observability.**
  - The ingestion path should acknowledge the source event after durable queueing or event persistence, not after all extraction and embedding work completes.
  - Measure separately:
    - source-to-event latency;
    - queue delay;
    - extraction latency;
    - graph-write latency;
    - embedding latency;
    - index lag;
    - permission-sync lag;
    - reconciliation lag;
    - dead-letter count.
  - Show “last synchronized at” and “evidence last updated at” in the user interface.
  - Do not claim that knowledge is current merely because the graph query succeeded.

- **Use backups and replication as operational controls, not evidence of correctness.**
  - FalkorDB supports RDB snapshots, AOF logging, and graph-specific `DUMP`/`RESTORE` operations. [FalkorDB durability documentation](https://docs.falkordb.com/operations/durability/)
  - FalkorDB replication uses a primary/replica model and is asynchronous, so replicas may lag. [FalkorDB replication documentation](https://docs.falkordb.com/operations/replication/)
  - Use primary reads for current ownership, permission revocation, decision supersession, and action preconditions.
  - Use replicas for historical search or non-critical analytics only when bounded staleness is acceptable.
  - Test restoring a Company Brain graph, rebuilding indexes, replaying missed connector events, and preserving provenance after restore.

- **Evaluate Company Brain behavior with a task-specific benchmark.**
  - Build an evaluation set from synthetic or authorized data with questions in at least these categories:
    - owner lookup;
    - team and responsibility lookup;
    - expertise discovery;
    - project status;
    - dependency traversal;
    - decision rationale;
    - decision supersession;
    - cross-document synthesis;
    - temporal “as of” questions;
    - source citation;
    - permission denial;
    - stale or conflicting knowledge;
    - action proposal and approval.
  - Measure:
    - answer correctness;
    - evidence precision and recall;
    - citation correctness;
    - provenance-path completeness;
    - ownership precision;
    - expertise precision;
    - freshness lag;
    - temporal reasoning accuracy;
    - contradiction detection;
    - abstention correctness;
    - cross-scope leakage rate;
    - permission-revocation propagation time;
    - p50/p95/p99 retrieval latency;
    - graph growth and index memory;
    - action authorization error rate.
  - Include negative cases where the correct answer is “unknown,” “stale,” “not authorized,” or “two sources conflict.”

- **Use existing benchmarks as warning signals, not as Company Brain certification.**
  - [CRAG](https://arxiv.org/abs/2406.04744) contains 4,409 question-answer pairs and mock APIs across five domains and eight question categories, including temporal dynamism and long-tail facts.
  - CRAG reports that most advanced LLMs achieved 34% accuracy or less, straightforward RAG improved accuracy only to 44%, and state-of-the-art industry RAG solutions answered 63% of questions without hallucination in the reported setup.
  - The benchmark found lower accuracy for more dynamic, less popular, and more complex facts—conditions that closely resemble changing company knowledge.
  - These numbers are not a direct forecast for a FalkorDB Company Brain. They show why evaluation must include dynamic updates, authority, source quality, and abstention.

- **Add an explicit authorization guardrail layer for role-based graph access.**
  - Role-based access control must be enforced by trusted application code before a graph query is constructed, not by an LLM instruction and not only after results are returned.
  - Recommended authorization entities:
    - `Principal` — authenticated user, service account, or agent;
    - `Role` — such as employee, manager, project-member, security-admin, or read-only-agent;
    - `Permission` — such as `graph.read`, `graph.read_sensitive`, `graph.write`, `decision.read`, `ticket.create`, or `admin.audit`;
    - `Scope` — organization, workspace, team, project, repository, channel, folder, document, ticket, or classification boundary;
    - `Policy` — deny/allow rules, source-system constraints, expiry, and approval requirements.
  - Suggested graph relationships:
    - `(principal)-[:HAS_ROLE]->(role)`;
    - `(role)-[:GRANTS]->(permission)`;
    - `(permission)-[:APPLIES_TO]->(scope)`;
    - `(sourceRecord)-[:VISIBLE_TO]->(scope)`;
    - `(policy)-[:GOVERNS]->(permission)`.
  - Resolve the effective authorization context from the authenticated session:
    - principal ID;
    - organization ID;
    - active roles;
    - permitted graph key(s);
    - allowed labels and relationship types;
    - allowed source systems;
    - allowed sensitivity levels;
    - read/write capability;
    - policy version and expiry.
  - The LLM may request an intent such as “find project ownership,” but it must not select its own tenant, role, graph key, permission scope, or unrestricted Cypher.

- **Use deny-by-default query guardrails for FalkorDB.**
  - Reject a request if the authenticated principal has no explicit read permission for the requested scope.
  - Reject graph labels, relationship types, property names, and source systems outside the server-side allowlist.
  - Reject write clauses such as `CREATE`, `SET`, `DELETE`, `DETACH DELETE`, and unsafe `MERGE` in read-only retrieval paths.
  - Use `GRAPH.RO_QUERY` for read-only retrieval where appropriate; FalkorDB documents that it rejects writes. [FalkorDB GRAPH.RO_QUERY](https://docs.falkordb.com/commands/graph.ro_query/)
  - Use parameterized Cypher and inject authorization predicates from trusted code. FalkorDB documents parameterized queries as a protection against Cypher injection and a way to reuse execution plans. [FalkorDB GRAPH.QUERY](https://docs.falkordb.com/commands/graph.query/)
  - Require bounded traversal depth, result limits, query timeouts, and response-size limits.
  - Require an audit record for every sensitive graph read, denied query, policy decision, and write action.
  - If authorization metadata is unavailable or stale, fail closed for sensitive data rather than falling back to broad retrieval.

- **Apply authorization before every retrieval stage, including vector and summary layers.**
  - Permission filtering must happen before:
    1. exact lookup;
    2. full-text search;
    3. vector search;
    4. graph expansion;
    5. community-summary retrieval;
    6. reranking;
    7. prompt assembly;
    8. answer caching.
  - A post-generation filter is insufficient because a private document may already have influenced the selected context or generated answer.
  - Store permission scope and policy version on source records, chunks, facts, relationships, summaries, and embeddings.
  - Partition cache keys by organization, principal, role set, permission version, and query scope.
  - When a role is revoked, invalidate affected caches and mark derived summaries and embeddings for revalidation.

- **Separate read, suggest, and execute capabilities.**
  - `READ` permits retrieval of authorized graph evidence.
  - `SUGGEST` permits the agent to propose an action, answer, assignment, or decision summary, but not modify source systems.
  - `EXECUTE` permits a typed operation only after policy validation and, for high-impact actions, explicit human approval.
  - Example guardrail policy:
    - an ordinary employee can read project and public-document evidence;
    - a project member can read project-private tickets;
    - a manager can read team-level ownership and staffing evidence;
    - a security-admin can access sensitive incident records;
    - an agent can suggest ticket assignments but cannot change them without approval;
    - a service account can write synchronization events but cannot read unrelated private chat content.
  - Record the requested capability, policy decision, approver, tool call, external response, and resulting graph change as an auditable `Action` or `ChangeEvent` subgraph.

- **Return pinpoint evidence with every substantive answer.**
  - The answer contract should contain separate fields for:
    - `answer` — concise natural-language response;
    - `confidence` — calibrated or categorical confidence, not an unsupported numeric claim;
    - `evidence` — exact supporting records;
    - `uncertainties` — conflicts, stale data, or missing evidence;
    - `freshness` — last source synchronization and source-record update time;
    - `permissions` — the scope under which the evidence was visible;
    - `retrieval_trace_id` — audit correlation ID.
  - Each evidence item should include:
    - `evidence_id`;
    - `source_system`;
    - `source_record_id`;
    - `title`;
    - `canonical_url`;
    - `direct_url` or permalink to the exact source object;
    - `locator` such as page, paragraph, heading, line range, issue comment ID, message timestamp, or document chunk ID;
    - `excerpt` copied from the authorized source;
    - `source_updated_at`;
    - `ingested_at`;
    - `content_hash`;
    - `relevance_reason`;
    - `access_scope`.
  - The model should never invent a URL. Links must be generated from connector metadata or validated against the source system before being shown to the user.

- **Use source-specific pinpoint-link strategies.**
  - **Documents and knowledge pages:** store the canonical URL plus heading, section, paragraph index, page number where applicable, chunk ID, and content hash. If the source supports anchors, generate a heading or fragment URL.
  - **Slack:** store workspace, channel ID, message timestamp, thread timestamp, and the official message permalink. Slack event records include event and message timestamps that can be used to resolve the exact message context. [Slack Events API](https://docs.slack.dev/apis/events-api)
  - **Jira:** store cloud/site URL, project key, issue key, comment ID where applicable, and the issue or comment URL. Preserve the source permission context because Jira operations require permissions. [Jira Cloud REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
  - **GitHub:** store repository, commit SHA, pull-request or issue number, file path, and line range. Prefer immutable commit or blob URLs over a mutable default-branch URL.
  - **SharePoint:** store site ID, drive/list ID, item ID, web URL, version or ETag, and page/heading/chunk locator. Microsoft Graph exposes resource IDs, creators, modifiers, and modified timestamps for SharePoint resources. [Microsoft Graph SharePoint resources](https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0)
  - **Tickets and incidents:** store issue ID, comment or event ID, status at ingestion, source version, and the exact source link.

- **Make evidence links verifiable and resilient.**
  - Validate that the user is authorized to open the link before displaying it, or clearly label it as “available only with source-system access.”
  - Keep both a stable source URL and a source snapshot reference. A source page can change after the answer is generated.
  - Store the excerpt and content hash used at answer time so auditors can compare the current source with the original evidence.
  - If a source is deleted, moved, or permission-revoked, mark the evidence item as unavailable and do not silently replace it with a different source.
  - When a source system cannot provide a stable deep link, return the canonical record URL plus a precise locator and a short excerpt.

- **Show a graph evidence path, not just a list of documents.**
  - For “Who owns the service used by Project Atlas?”, show a path such as:
    - `Project Atlas`
    - `DEPENDS_ON`
    - `Service X`
    - `MAINTAINS`
    - `Team Delta`
    - `OWNS` or `LEADS`
    - `Person Y`
    - `SUPPORTED_BY`
    - Jira issue / service catalog / decision document.
  - For each edge, provide the supporting evidence link or indicate that the edge is an inferred relationship and list the claims used to derive it.
  - This directly demonstrates that FalkorDB is performing graph work rather than serving as a visualization layer.

- **Use an evidence-aware response format in the product.**
  - Recommended display:

    ```text
    Answer: Team Delta owns Service X, with Maya Chen listed as the current service lead.

    Evidence:
    1. Service X → maintained by → Team Delta
       Source: Service catalog, "Service X" section
       Open source: https://example.com/service-x#ownership
       Updated: 2026-10-16

    2. Team Delta → service lead → Maya Chen
       Source: Jira project configuration, project DELTA
       Open source: https://example.atlassian.net/browse/DELTA
       Updated: 2026-10-15

    Graph path:
    Project Atlas → DEPENDS_ON → Service X → MAINTAINS → Team Delta

    Caveat: A Slack discussion from 2026-10-14 suggests a possible ownership transition;
    it is marked as an unconfirmed claim and is not used as the current owner.
    ```

  - The exact URLs above are illustrative only. Production URLs must come from validated connector metadata.
  - Do not present a source link unless the evidence item actually participated in retrieval or graph derivation.

- **Test the guardrails and evidence behavior explicitly.**
  - Authorization tests:
    - user with no project membership cannot retrieve project-private documents;
    - role revocation removes access from graph, vector, full-text, summary, and cache paths;
    - a model-generated tenant ID cannot override the authenticated tenant;
    - generated Cypher cannot access forbidden labels, relationships, or graph keys;
    - write-capable tools require the required permission and approval.
  - Evidence tests:
    - every answer claim maps to at least one evidence item;
    - every evidence URL resolves to the source record or is marked unavailable;
    - source excerpts match the stored content hash at ingestion time;
    - the graph path shown to the user matches the Cypher result used for generation;
    - stale or conflicting evidence is disclosed;
    - unsupported questions produce a fixed abstention response.
  - Security tests:
    - prompt injection in a chat message cannot trigger an unauthorized tool call;
    - malicious text cannot alter the authorization policy;
    - private content cannot influence an answer for an unauthorized principal;
    - cache keys cannot cross organization or role boundaries.

### Core Company Brain Queries Explicitly Considered

The Two representative questions below are included as first-class requirements and should appear in the demo and evaluation set. They test distinct graph capabilities rather than simple document lookup.

#### 1. Who on the team has worked on this system before?

- **Capability tested:** expertise discovery, team membership, temporal validity, and evidence-weighted ranking.
- **Suggested graph path:**
  - `Team` → `HAS_MEMBER` → `Person`
  - `Person` → `CONTRIBUTED_TO` → `Repository`, `Service`, `Project`, `Incident`, `Ticket`, `PullRequest`, or `Document`
  - `Service` → `IMPLEMENTED_BY` / `MAINTAINED_BY` → `Team`
  - `Person` → `DISCUSSED` / `RESOLVED` / `REVIEWED` → relevant system or incident evidence
- **Required answer behavior:** rank people using evidence such as recent commits, incident resolution, ticket work, reviews, and authoritative ownership; show dates and evidence counts; separate current team members from former contributors.
- **Important limitation:** prior activity demonstrates evidence of work, not current availability, expertise level, or willingness to take the task.
- **Evaluation cases:** recent versus historical contributors, people who changed teams, indirect repository ownership, similar system names, sparse evidence, and conflicting organizational records.

#### 2. What breaks if this service goes down?

- **Capability tested:** dependency traversal, impact analysis, ownership lookup, and operational reasoning.
- **Suggested graph path:**
  - `Service` → `DEPENDS_ON` → `Service`, `Database`, `Queue`, `API`, or `ExternalSystem`
  - `Project` / `Product` / `Application` → `USES` → `Service`
  - `Service` → `BACKED_BY` → `Repository`, `Deployment`, `Database`, or `Infrastructure`
  - `Service` → `OWNED_BY` / `MAINTAINED_BY` → `Person` or `Team`
  - `Service` → `DOCUMENTED_BY` → `Runbook`, `Incident`, `Decision`, or `Document`
- **Required answer behavior:** return direct and bounded transitive dependencies, affected projects or products, likely user-facing capabilities, owners, known single points of failure, and source evidence. Mark inferred impact separately from explicitly documented impact.
- **Traversal requirement:** bound depth and fanout; an unbounded dependency walk can be expensive and can produce a misleading blast radius.
- **Evaluation cases:** direct dependency, two-hop dependency, optional dependency, degraded-but-not-downstream service, circular dependency, stale architecture document, and missing dependency edges.

These queries make FalkorDB essential: each answer depends on connected traversal, relationship types, temporal claims, provenance, and authorization—not merely on embedding similarity over isolated documents.

## Contradictions & Debate

- **[HIGH CONFIDENCE] A Company Brain needs a graph, but a graph alone is not enough.**
  - Organizational ownership, dependencies, provenance, and decision history are naturally relational and benefit from graph traversal.
  - Semantic search remains useful for finding relevant documents and entering the graph from natural-language questions.
  - Conclusion: use FalkorDB as the system of connected organizational knowledge, with vector and full-text indexes inside the graph as complementary retrieval mechanisms.

- **[CONFLICTING DATA] GraphRAG versus conventional RAG**
  - [Microsoft GraphRAG](https://arxiv.org/abs/2404.16130) reports improvements in comprehensiveness and diversity for global questions.
  - [CRAG](https://arxiv.org/abs/2406.04744) shows that even strong RAG systems remain far from fully trustworthy on dynamic and complex factual questions.
  - Conclusion: graph structure improves certain multi-hop and global queries, but it cannot compensate for incomplete ingestion, incorrect entity resolution, stale permissions, or weak source quality.

- **[HIGH CONFIDENCE] Source citations are necessary but not sufficient.**
  - A citation can be present but irrelevant, stale, inaccessible, or misinterpreted.
  - Source-linked evidence must include the exact record, timestamp, version, access scope, and relevant excerpt.
  - Evaluation should score citation entailment, not merely whether a URL appears in the answer.

- **[CONFLICTING DATA] Broad extraction versus constrained ontology**
  - Broad extraction captures more organizational concepts and may improve recall.
  - It also increases duplicate entities, ambiguous relationships, unsupported claims, and retrieval noise.
  - FalkorDB’s GraphRAG SDK prunes extraction against a schema before writing. This supports a narrower ontology as a practical precision safeguard.
  - Conclusion: begin with a deliberately constrained ontology and evolve it through measured failures rather than extracting every possible relation.

- **[HIGH CONFIDENCE] Current ownership is not the same as historical contribution.**
  - A person’s past commits, messages, or incident work can indicate experience but does not prove current ownership or availability.
  - Conclusion: separate authoritative ownership edges from evidence-based expertise edges and expose their different confidence and timestamps.

- **[CONFLICTING DATA] Centralized knowledge versus privacy and least privilege**
  - Centralization improves cross-source reasoning and reduces duplicated retrieval logic.
  - It also concentrates sensitive data and increases the consequences of a permission bug or prompt injection.
  - Conclusion: centralize the graph service and ontology while preserving source scopes, graph-key boundaries, field-level redaction, access-aware indexes, and auditable retrieval.

- **[HIGH CONFIDENCE] Freshness is a product feature, not only a pipeline metric.**
  - A Company Brain that cannot explain when a fact was synchronized is unsafe for ownership, staffing, project status, or decision questions.
  - Conclusion: expose freshness, source version, and update status in both the answer and the operational dashboard.

- **[CONFLICTING DATA] LLM-generated text-to-Cypher**
  - Text-to-Cypher can express counts, paths, ownership filters, and graph-specific questions that text retrieval cannot.
  - It adds latency, query-generation errors, injection risk, and authorization complexity. FalkorDB’s GraphRAG SDK keeps this path opt-in and documents validation requirements.
  - Conclusion: use typed query templates first; add constrained text-to-Cypher only for read-only, low-risk questions after measuring benefit.

- **[HIGH CONFIDENCE] The Company Brain should abstain.**
  - FalkorDB’s grounding guidance explicitly warns that retrieval does not eliminate hallucinations and describes an evidence-gated abstention path.
  - A confident answer to an unanswered ownership or policy question is worse than a transparent “unknown” response.
  - Conclusion: make abstention a tested product behavior, not merely a prompt instruction.

## Blind Spots & Missing Info

- Public research does not establish a universal ontology for company knowledge. Organizations differ in terminology, authority structures, systems, and decision processes.
- Most GraphRAG benchmarks evaluate question answering over documents or curated corpora, not full Company Brain behavior across people, teams, tickets, chats, source control, permissions, and actions.
- Vendor-reported GraphRAG SDK benchmark figures are implementation-specific and should be independently reproduced on the project’s schema and workload.
- The public evidence base is limited on “who knows what” accuracy. Contribution signals can identify activity, but expertise, availability, and current ownership are different constructs.
- Source-system event delivery is not guaranteed to be complete or ordered in every deployment. A reconciliation process is required, but its cost and coverage depend on each API.
- Permission models across Slack, Jira, GitHub, SharePoint, and other systems do not map perfectly to one shared graph permission model.
- The report does not determine legal compliance for employee communications, personal data, labor requirements, retention, e-discovery, or data residency.
- Storing full chat content can create disproportionate privacy and retention risk. A production design may need selective ingestion, redaction, retention tiers, or user-visible deletion controls.
- Entity resolution can incorrectly merge people with similar names or fail to merge aliases across systems. Both false merges and false splits can harm answers.
- Current-answer evaluation is difficult because organizational truth may be disputed, undocumented, or changing during the test.
- A cited document can be authoritative but still contain an outdated plan. Citation correctness must include temporal validity, not only textual entailment.
- No public source reviewed here proves zero data leakage, zero prompt-injection risk, perfect freshness, or universal superiority of graph retrieval over tuned hybrid search.

## References

### FalkorDB official documentation

- **docs.falkordb.com** — FalkorDB platform overview, property-graph model, OpenCypher, GraphRAG, indexes, and supported clients. [Source](https://docs.falkordb.com/)
- **docs.falkordb.com** — FalkorDB GraphRAG SDK pipeline architecture, provenance chain, graph schema, extraction, resolution, and retrieval flow. [Source](https://docs.falkordb.com/graphrag/architecture)
- **docs.falkordb.com** — FalkorDB GraphRAG multi-path retrieval with entity discovery, vector search, full-text search, relationship expansion, reranking, and optional text-to-Cypher. [Source](https://docs.falkordb.com/graphrag/retrieval)
- **docs.falkordb.com** — FalkorDB grounding guidance, source tracing, retrieval context, evidence checks, and abstention path. [Source](https://docs.falkordb.com/graphrag/reducing-llm-hallucinations)
- **docs.falkordb.com** — FalkorDB incremental graph updates, content hashes, document replacement, deletion, orphan cleanup, batch synchronization, and crash-safe semantics. [Source](https://docs.falkordb.com/graphrag/incremental-updates)
- **docs.falkordb.com** — FalkorDB full-text indexing, stemming, stopwords, fuzzy and prefix search, phonetics, and relevance scoring. [Source](https://docs.falkordb.com/cypher/indexing/fulltext-index/)
- **docs.falkordb.com** — FalkorDB vector indexing, HNSW, cosine and Euclidean similarity, node and relationship search, and tuning parameters. [Source](https://docs.falkordb.com/cypher/indexing/vector-index/)
- **docs.falkordb.com** — FalkorDB `GRAPH.QUERY`, parameterized Cypher, query timeouts, and plan caching. [Source](https://docs.falkordb.com/commands/graph.query/)
- **docs.falkordb.com** — FalkorDB `GRAPH.RO_QUERY`, read-only enforcement, read replicas, and bounded read behavior. [Source](https://docs.falkordb.com/commands/graph.ro_query/)
- **docs.falkordb.com** — FalkorDB `MERGE`, separate endpoint binding, and duplicate-path cautions. [Source](https://docs.falkordb.com/cypher/merge/)
- **docs.falkordb.com** — FalkorDB cluster keyspace sharding, graph-key placement, replicas, and the fact that a single graph is not split across shards. [Source](https://docs.falkordb.com/operations/cluster/)
- **docs.falkordb.com** — FalkorDB durability through RDB, AOF, and graph-specific backup operations. [Source](https://docs.falkordb.com/operations/durability/)
- **docs.falkordb.com** — FalkorDB primary/replica replication and asynchronous read lag. [Source](https://docs.falkordb.com/operations/replication/)

### Academic and benchmark sources

- **arxiv.org** — Edge et al., “From Local to Global: A Graph RAG Approach to Query-Focused Summarization,” submitted 24 April 2024, revised 19 February 2025. [Source](https://arxiv.org/abs/2404.16130)
- **arxiv.org** — Gutiérrez et al., “HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models,” submitted 23 May 2024, revised 14 January 2025; NeurIPS 2024. [Source](https://arxiv.org/abs/2405.14831)
- **arxiv.org** — Liu et al., “Lost in the Middle: How Language Models Use Long Contexts,” submitted 6 July 2023, revised 20 November 2023; published in TACL. [Source](https://arxiv.org/abs/2307.03172)
- **arxiv.org** — Shi et al., “Large Language Models Can Be Easily Distracted by Irrelevant Context,” submitted 31 January 2023, revised 6 June 2023; published at ICML 2023. [Source](https://arxiv.org/abs/2302.00093)
- **arxiv.org** — Wu et al., “LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory,” submitted 14 October 2024, revised 4 March 2025; listed as ICLR 2025. [Source](https://arxiv.org/abs/2410.10813)
- **arxiv.org** — Yang et al., “CRAG — Comprehensive RAG Benchmark,” submitted 7 June 2024, revised 1 November 2024; NeurIPS 2024 Datasets and Benchmarks Track. [Source](https://arxiv.org/abs/2406.04744)
- **arxiv.org** — Greshake et al., “Not what you’ve signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection,” submitted 23 February 2023, revised 5 May 2023. [Source](https://arxiv.org/abs/2302.12173)

### Provenance, security, and risk-management sources

- **w3.org** — W3C PROV overview covering provenance, attribution, derivation, versioning, reproducibility, and procedure representation. [Source](https://www.w3.org/TR/prov-overview/)
- **genai.owasp.org** — OWASP LLM01:2025 Prompt Injection, including indirect injection, external-content segregation, least privilege, validation, human approval, and adversarial testing. [Source](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- **nist.gov** — NIST AI Risk Management Framework, intended to improve the incorporation and evaluation of trustworthiness considerations in AI systems. [Source](https://www.nist.gov/itl/ai-risk-management-framework)

### Source-system integration documentation

- **docs.slack.dev** — Slack Events API, OAuth-scoped visibility, event delivery, retries, acknowledgements, rate limits, and source event envelopes. [Source](https://docs.slack.dev/apis/events-api)
- **developer.atlassian.com** — Jira Cloud REST API v3, authentication, permissions, pagination, timestamps, and asynchronous operations. [Source](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
- **learn.microsoft.com** — Microsoft Graph SharePoint resources, sites, lists, drives, list items, creators, modifiers, timestamps, and source identifiers. [Source](https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0)
- **docs.github.com** — GitHub search API, accessible-source filtering, search limits, incomplete-result indicators, issue and commit metadata, and permission-aware API behavior. [Source](https://docs.github.com/en/rest/search/search)

### Evidence-quality note

The report distinguishes official product documentation, standards, academic papers, benchmarks, and vendor-reported claims. FalkorDB documentation is authoritative for documented FalkorDB behavior but is not independent evidence that every architecture will meet a target latency, accuracy, or security requirement. Academic and benchmark results are reported for their stated datasets and experimental settings; they should be reproduced on authorized or synthetic Company Brain data before being used as product commitments.
