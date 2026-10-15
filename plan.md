# Master Plan: Threadline — the explainable company graph agent

> Source: .pipeline/research-report.md · Author: solution-architect · Date: 2026-10-16

## 1. Product vision

Threadline is a local, FalkorDB-centered Company Brain for Northstar Labs, a fictional company fixture. It answers operational questions by traversing an inspectable graph of people, teams, projects, services, work, decisions, source records, and change events; every substantive answer exposes a bounded graph path, pinpoint evidence, freshness, uncertainty, and the synthetic permission scope used. The build delivers the evidence-path, ownership-versus-expertise, temporal decision ledger, bounded impact reasoning, and evidence-gated safe-action USPs from the research report. The primary track is **Company Brain**; the secondary Agents That Act on Connected Data framing is used only if the approval-gated local mutation passes its tests.

The MVP is deliberately reproducible on a laptop: synthetic/team-owned data is the default, one pinned public GitHub snapshot is optional, and no private credentials or live enterprise connectors are required. FalkorDB is the canonical relationship and provenance store; required demo answers must fail closed when the graph is unavailable rather than using a hidden flat-data fallback.

## 2. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 15 App Router + React + TypeScript + Tailwind CSS | One local app, typed UI, fast demo iteration, and a clear evidence-first console without a second frontend server. |
| Backend / API | Next.js route handlers + Zod validation + deterministic query classifier/answer assembler | Keeps the MVP small while separating READ, SUGGEST, and EXECUTE boundaries and validating every request server-side. |
| Data | FalkorDB in Docker, official `falkordb` JavaScript client, OpenCypher templates, versioned JSON fixture | FalkorDB is the primary graph and every required multi-hop answer executes against it. JSON is easy to review, seed, refresh, and keep synthetic. |
| Retrieval | Exact key lookup + FalkorDB full-text indexes + bounded graph traversal; no required embeddings | Covers the report's hybrid-retrieval requirement while keeping vector GraphRAG and broad text-to-Cypher out of MVP. |
| Auth / permissions | Synthetic principal selector backed by server-side allowlisted scopes (`public`, `team-private`, `project-private`) | Demonstrates deny-by-default filtering before retrieval without pretending to be production ACL synchronization. |
| Action layer | Typed application functions for one reversible local ticket/follow-up mutation plus `ActionEvent` receipt | Makes the secondary action track conditional, approval-gated, prompt-injection-safe, and easy to test. |
| Testing | Vitest unit/integration tests + Playwright e2e tests | Tests graph queries, contract/security boundaries, freshness, abstention, and the visible demo flow. |

**Run commands:** install `npm install` · dev `npm run dev` (port 3000) · build `npm run build` · unit/integration tests `npm run test:unit && npm run test:integration` · e2e `npm run test:e2e` · FalkorDB `docker compose up -d falkordb` · seed `npm run seed` · refresh fixture `npm run refresh -- --version 2`

Environment is documented in `app/.env.example`: `FALKORDB_URL=redis://localhost:6379`, `FALKORDB_GRAPH=threadline`, and optional `GITHUB_TOKEN` is never required for the default fixture. No secrets are checked in.

## 3. Features

| ID | Feature | Priority | USP | Phase |
|---|---|---|---|---|
| F1 | Constrained canonical ontology and schema version | must | #1, #2, #3, #4 | P0 |
| F2 | Attributed temporal claims and source provenance | must | #1, #2, #3 | P1 |
| F3 | FalkorDB-centered local graph and deterministic fixture loader | must | #1, #4 | P1 |
| F4 | Exact/full-text retrieval with bounded graph expansion | must | #1, #4 | P1 |
| F5 | “Who has worked on this system before?” expertise/history query | must | #1, #2 | P1 |
| F6 | “What breaks if this service goes down?” bounded impact query | must | #1, #4 | P1 |
| F7 | Decision ledger with rationale, source trace, and supersession | must | #1, #3 | P1 |
| F8 | Evidence contract, freshness, uncertainty, and deterministic abstention | must | #1, #3 | P1 |
| F9 | Versioned fixture refresh and visible change events | must | #3 | P1 |
| F10 | Synthetic permission filtering before retrieval and traversal | must | #1, #5 | P1 |
| F11 | READ/SUGGEST/EXECUTE action boundary with one approval-gated local mutation | must | #5 | P1 |
| F12 | Parameterized, allowlisted, bounded Cypher with trace logging | must | #1, #4, #5 | P1 |
| F13 | Evidence-first operator console and graph-path inspection | must | #1, #2, #3, #4 | P2 |
| F14 | Honest positive/negative evaluation harness and demo checks | must | #1, #5 | P3 |
| F15 | One pinned public GitHub enrichment snapshot with attribution | nice | #1, #2 | P1 |

## 4. Architecture

### Components and boundaries

1. **Web console (`src/app/brain`, `src/components`)**: question composer, synthetic principal/scope selector, answer cards, evidence drawer, graph-path panel, freshness/change panel, decision ledger panel, and action proposal/approval panel. It only calls typed HTTP endpoints and never imports server-side graph code.
2. **API boundary (`src/app/api`)**: validates input with Zod, resolves the synthetic principal in trusted server code, classifies the request into an allowlisted intent, invokes a known query template, and returns an `AnswerEnvelope`. Route handlers never accept raw Cypher, labels, relationship names, graph keys, or caller-selected scopes.
3. **Graph service (`src/server`)**: opens FalkorDB, loads/refreshes fixture records idempotently, applies scope predicates before candidate lookup/expansion, runs bounded parameterized queries, and logs a redacted retrieval trace. A missing graph connection is an explicit error/empty state; it cannot fall back to fixture JSON for answers.
4. **Query catalog (`src/queries`)**: checked-in OpenCypher templates for `ownership`, `expertise`, `impact`, `decision`, `freshness`, and `graph_summary`. Each template uses parameters, known labels/relationships, bounded depth/fanout, a result `LIMIT`, and source visibility predicates. Read paths use the client's read-only operation where supported; only typed loader/refresh/action functions write.
5. **Fixture and refresh service (`src/data`, `scripts`)**: Northstar Labs records with stable IDs, source-specific IDs, synthetic URIs, content hashes, fixture version, and deliberate positive/negative cases. Refresh rejects older versions, is idempotent, creates `ChangeEvent`, and makes stale/conflicting state visible.
6. **Typed action service (`src/server/actions`)**: only `assign_synthetic_ticket` or equivalent reversible local follow-up is accepted. SUGGEST creates a proposal without writing; EXECUTE requires an authenticated synthetic principal, server policy approval, explicit user approval token, target/evidence IDs from the preceding read, and emits an `ActionEvent` receipt. Retrieved text is evidence-only and cannot alter policy or call tools.

### Canonical graph model

The schema version is stored on every loaded source-backed node/edge. Core labels are `Person`, `Team`, `Project`, `Service`, `Repository`, `Ticket`, `Document`, `Conversation`, `Message`, `Decision`, `Skill`, `SourceRecord`, `ChangeEvent`, and `PermissionScope`; `ActionEvent` is an audit-only label. Stable `id` values are separate from source-specific IDs.

Core properties include:

- Identity/state: `id`, `name`/`title`, `status`, `role`, `kind`, `source_system`, `source_record_id`.
- Claims: `assertion_type` (`source_fact`, `extracted_fact`, `derived_fact`, `recommendation`), `confidence`, `authority`, `observed_at`, `valid_from`, `valid_until`, `last_verified_at`, `schema_version`.
- Evidence: `source_url` or stable `synthetic://northstar/...` URI, `locator`, `excerpt`, `content_hash`, `source_updated_at`, `ingested_at`, `visibility_scope`.
- Temporal/support: `decision_at`, `effective_at`, `review_at`, `source_version`, `event_type`, `changed_at`.

Relationships include `MEMBER_OF`, `OWNS`, `MAINTAINS`, `CONTRIBUTED_TO`, `RESOLVED`, `REVIEWED`, `AUTHORED`, `EXPERT_IN`, `USES`, `DEPENDS_ON`, `PART_OF`, `DISCUSSED_IN`, `SUPPORTED_BY`, `AFFECTS`, `SUPERSEDES`, `SOURCED_FROM`, `VISIBLE_TO`, `CHANGED`, and `MUTATED`. Mutable facts remain attributed and dated; ownership changes retain the old edge with `valid_until`. Conflicting facts use parallel attributed edges and are returned as `conflicting` uncertainty rather than silently overwritten.

### Answer contract

Every substantive read returns:

```text
{
  answer,
  claims: [{ claim, assertion_type, confidence, evidence_ids }],
  evidence: [{ source_system, record_id, canonical_url_or_uri, locator,
               excerpt, source_updated_at, ingested_at, content_hash,
               relevance_reason, access_scope }],
  graph_path: [{ from_id, relationship, to_id, edge_claim_status }],
  uncertainties: ["stale" | "conflicting" | "inferred" | "missing"],
  freshness: { last_source_update, last_ingested, freshness_status },
  permission_scope,
  retrieval_trace_id
}
```

If an authorized, current, relevant path cannot support the requested claim, the API returns the fixed deterministic abstention response: `Insufficient evidence in the authorized company graph to answer this question.` It includes `missing`/`stale` uncertainty and the trace ID, never a plausible guess. Expertise is labeled as demonstrated activity, separated from current ownership and availability. Inferred outage effects are labeled separately from documented effects.

### API contract

| Method | Path | Request | Response / behavior |
|---|---|---|---|
| GET | `/api/health` | none | FalkorDB connectivity, graph name, fixture version; no hidden fallback. |
| GET | `/api/graph/summary` | `principalId` query | Authorized node/edge counts and schema version. |
| POST | `/api/query` | `{ question, principalId, intent?: "auto"|"ownership"|"expertise"|"impact"|"decision"|"freshness" }` | `AnswerEnvelope`; intent is allowlisted and all values are parameters. |
| POST | `/api/fixture/refresh` | `{ version }` | Change summary, `ChangeEvent` IDs, before/after trace; local demo operation only. |
| POST | `/api/actions/propose` | `{ actionType, targetId, evidenceIds, principalId }` | Non-mutating typed proposal with policy decision and approval nonce. |
| POST | `/api/actions/execute` | `{ proposalId, approvalNonce, principalId }` | Reversible local mutation plus `ActionEvent` receipt, or a fail-closed denial. |

### Folder ownership shape

```text
app/
  docker-compose.yml
  .env.example
  src/
    app/                 # P0 shell + P2 brain route; P1 owns app/api
    components/          # P2 UI
    data/                # P1 fixture and refresh mappings
    lib/contracts/       # P0 shared request/response types
    lib/client/          # P2 fetch client
    queries/             # P1 allowlisted .cypher templates
    server/              # P1 graph, retrieval, policy, action services
  scripts/               # P1 seed/refresh utilities
  tests/                 # P3 unit/integration/evaluation; QA owns e2e during QA stage
```

### Local setup and fixture

`app/docker-compose.yml` starts `falkordb/falkordb:latest` with ports 6379 and 3000. The loader creates graph `threadline`, indexes exact names/source text as appropriate, and seeds a fictional Northstar Labs dataset containing an ownership change, former contributor, blocked dependency, two-hop outage impact, superseded decision, stale document, conflicting claim, unauthorized `team-private` record, and prompt-injection-looking message. The default demo uses no external data. F15 may add one pinned public GitHub repository snapshot only with commit SHA, record URL, path/line locator, retrieval date, license/attribution, and content hash; contributor activity is never treated as employment or availability.

### UI surfaces

- **Ask**: two one-click example prompts for the mandatory questions, free-text constrained classifier, principal/scope selector, loading/error/abstention states.
- **Answer**: concise deterministic answer, current owners, activity/history distinction, documented versus inferred impact, confidence and uncertainty badges.
- **Evidence**: source URI, locator, excerpt, hash, source/ingestion dates, visibility, and why each item supports its claim.
- **Graph path**: returned nodes/edges and query-template/trace metadata; no precomputed-only diagram.
- **Operations**: fixture version, change events, stale/conflicting markers, decision supersession, and optional action proposal/approval/receipt.
- **Trust cues**: explicit “synthetic fixture” labeling, “activity is not ownership or availability” caveat, and a graph-unavailable error state.

### Demo flow

1. Run `docker compose up -d falkordb`, `npm install`, `npm run seed`, and `npm run dev`; show the health/fixture status.
2. Ask “Who has worked on this system before?” for Atlas. Show current team members versus former contributors, dated activity evidence, sources, and the actual FalkorDB path/query trace.
3. Ask “What breaks if this service goes down?” for Atlas. Show bounded direct/two-hop effects, owners, documented versus inferred impact, and evidence.
4. Open a decision rationale and show the supporting source locator plus a superseded decision, then refresh the fixture to show a `ChangeEvent`, new version/hash, and changed answer.
5. Switch to the public principal and demonstrate that a `team-private` record cannot influence lookup or graph expansion; show deterministic abstention for a nonexistent service.
6. Open the prompt-injection-looking message as quoted evidence; verify it cannot change policy or invoke an action.
7. If and only if the action tests pass, propose and explicitly approve the reversible synthetic ticket/follow-up mutation, then show the `ActionEvent` receipt. Otherwise omit the secondary action-track claim.

### README/docs deliverables

The later `tech-writer` stage should produce `README.md` plus `docs/architecture.md`, `docs/data-model.md`, `docs/demo.md`, `docs/evaluation.md`, and `docs/security-boundaries.md`. They must document Docker/FalkorDB setup, commands, synthetic-data/license policy, schema and query catalog, evidence contract, permission and prompt-injection boundaries, optional GitHub enrichment, evaluation results, known limitations, and the explicit out-of-scope list: live connectors, production ACLs, distributed deployment, full vector GraphRAG, broad text-to-Cypher, and destructive/external writes.

## 5. Phases

The dependency graph, one line per edge:

```text
P0 → P1, P2
P1 → P3
P2 → P3
```

This yields Wave 1: `P0`; Wave 2: `P1 ∥ P2`; Wave 3: `P3`. P2 depends on shared contracts and the app shell, but not on unfinished backend code; it calls stable HTTP paths and can use loading/error fixtures while P1 is being built. The UI and backend own disjoint source globs.

### P0: Foundation and contracts (owner: phase-engineer)

- **Owns:** `package.json`, `package-lock.json`, `tsconfig.json`, `next.config.*`, `tailwind.config.*`, `postcss.config.*`, `docker-compose.yml`, `.env.example`, `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`, `src/lib/contracts/**`, `src/lib/config/**`
- **Depends on:** none
- **Features:** F1
- **Tasks:** scaffold the Next.js/TypeScript/Tailwind app; add scripts for dev/build/typecheck/unit/integration/e2e/seed/refresh; create the `/` redirect/shell and global tokens; define versioned `AnswerEnvelope`, evidence, graph path, trace, query, refresh, proposal, and receipt types; define synthetic principal IDs and scope enums without implementing policy; add Docker Compose for FalkorDB and `.env.example` with placeholders only.
- **Acceptance criteria:**
  - AC-P0-1: `npm install` and `npm run typecheck` succeed from `app/` with no private credentials.
  - AC-P0-2: `npm run build` succeeds with the minimal shell and stable `/brain` route contract target; no server implementation is required yet.
  - AC-P0-3: Shared contracts include schema version, evidence contract fields, `uncertainties`, `permission_scope`, and `retrieval_trace_id`, with no `any` escape hatch for API payloads.
  - AC-P0-4: `docker compose config` validates the local FalkorDB service on ports 6379/3000 and the documented graph environment variables.
- **Verify commands:** `npm install`; `npm run typecheck`; `npm run build`; `docker compose config`
- **Handoff expectations:** write `.pipeline/handoffs/phase-P0.md` with the exact commands/results, owned file list, contract type names and endpoint assumptions, Docker instructions, and any unresolved package/version choices. Do not write backend or test files outside owned globs.

### P1: FalkorDB graph, retrieval, API, and safe action boundary (owner: phase-engineer)

- **Owns:** `src/app/api/**`, `src/data/**`, `src/queries/**`, `src/server/**`, `scripts/**`
- **Depends on:** P0
- **Features:** F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, F15
- **Tasks:** implement the synthetic Northstar fixture and idempotent loader; create the canonical labels/relationships, indexes, source records, scope edges, and deliberate test cases; implement parameterized bounded `.cypher` templates and the graph client; implement pre-retrieval permission filtering, exact/full-text candidate resolution, temporal/supersession policy, evidence assembly, trace logging, deterministic abstention, and graph-unavailable failure; implement health/summary/query/refresh routes; implement typed suggest/execute with approval and `ActionEvent`; optionally add the pinned GitHub importer behind an explicit opt-in and immutable metadata.
- **Acceptance criteria:**
  - AC-P1-1: With only FalkorDB running, `npm run seed` loads a versioned graph whose required nodes, relationships, sources, scopes, and deliberate stale/conflict/injection cases are queryable; repeated seed is idempotent.
  - AC-P1-2: The expertise query and impact query execute actual parameterized FalkorDB traversals, include bounded depth/fanout and `LIMIT`, return graph paths and evidence IDs, and produce no answer if FalkorDB is unavailable.
  - AC-P1-3: Ownership is derived from authoritative current `OWNS`/`MAINTAINS` claims; expertise ranks dated activity and separates current members from former contributors without claiming ownership or availability.
  - AC-P1-4: Impact results distinguish documented from inferred effects and include owners, direct dependencies, two-hop results, and a bounded-result uncertainty when traversal is clipped.
  - AC-P1-5: Decision answers include rationale, effective/review dates, source locator, and `SUPERSEDES` handling; older/superseded decisions are not presented as current.
  - AC-P1-6: Every substantive response satisfies the shared evidence contract; missing/unauthorized/stale-only evidence returns the fixed abstention response with trace and uncertainty.
  - AC-P1-7: Refresh accepts only a newer fixture version, creates visible `ChangeEvent` records, updates hashes/observed times, preserves old evidence, and remains idempotent.
  - AC-P1-8: Scope filtering occurs before exact/full-text lookup and graph expansion; a public principal cannot be influenced by `team-private` or `project-private` records, and missing scope fails closed.
  - AC-P1-9: Prompt-injection-looking retrieved text is passed as evidence only; it cannot select a tool, scope, principal, graph, query, or policy. Raw Cypher, labels, relationship names, and unbounded limits are rejected at the API boundary.
  - AC-P1-10: EXECUTE rejects missing/invalid approval, unauthorized actors, mismatched evidence/target, destructive action types, and stale proposals; a valid approval performs one reversible local mutation and writes a complete `ActionEvent` receipt.
  - AC-P1-11: `npm run typecheck`, `npm run test:unit`, `npm run seed`, and `npm run refresh -- --version 2` pass against local FalkorDB; query template IDs and redacted trace fields are documented in the handoff.
- **Verify commands:** `docker compose up -d falkordb`; `npm run typecheck`; `npm run test:unit`; `npm run seed`; `npm run refresh -- --version 2`; `npm run build`
- **Handoff expectations:** write `.pipeline/handoffs/phase-P1.md` with graph schema/version, fixture cases, query-template IDs and bounds, endpoint payload examples, permission/action policy decisions, test output, seed/refresh instructions, and any optional GitHub enrichment status. Explicitly list any backend assumptions the frontend can rely on.

### P2: Evidence-first operator console (owner: frontend-engineer)

- **Owns:** `src/app/brain/**`, `src/components/**`, `src/lib/client/**`, `public/**`
- **Depends on:** P0
- **Features:** F13
- **Tasks:** implement the designed `/brain` console against P0 contracts and stable `/api/*` paths; add one-click representative prompts, principal selector, loading/error/abstention states, answer/claim cards, evidence drawer, graph-path inspector, freshness/change view, decision supersession view, and conditional action proposal/approval/receipt UI; visibly label synthetic data, activity-versus-ownership, inferred impact, freshness, uncertainty, and trace ID; keep all graph data rendered from API responses rather than hardcoded diagrams.
- **Acceptance criteria:**
  - AC-P2-1: `/brain` renders with no backend import and can be typechecked/build-tested using contract-shaped loading/error states.
  - AC-P2-2: The two mandatory prompts are visible and submit through the typed client with the selected synthetic principal; the UI renders answer, claims, graph path, evidence, freshness, uncertainty, permission scope, and trace ID.
  - AC-P2-3: The UI visibly separates current ownership from historical activity, documented impact from inferred impact, and stale/conflicting/missing evidence; it includes the activity/availability caveat.
  - AC-P2-4: Graph-path and evidence panels show returned IDs, relationships, source locators/excerpts, hashes, timestamps, scope, and query trace; no source link is shown unless it is in the response.
  - AC-P2-5: The console has clear states for graph unavailable, deterministic abstention, denied scope, refresh/change event, and action proposal/approval/receipt; no retrieved text is rendered as an instruction to the user or application.
  - AC-P2-6: `npm run typecheck` and `npm run build` pass after the backend is present, and the main demo flow is usable at `http://localhost:3000/brain` without private credentials.
- **Verify commands:** `npm run typecheck`; `npm run build`; `npm run dev` and manually exercise `/brain` with API responses/mocked loading states
- **Handoff expectations:** write `.pipeline/handoffs/phase-P2.md` with routes/screens implemented, design package decisions, API paths consumed, accessibility/empty-state notes, screenshots or capture guidance for QA, and any backend response-shape assumptions. Do not edit P1-owned API/server/data files.

### P3: Integration, security, and honest evaluation (owner: phase-engineer)

- **Owns:** `tests/**`, `eval/**`
- **Depends on:** P1, P2
- **Features:** F14
- **Tasks:** add unit/integration/evaluation coverage for the acceptance matrix using the synthetic fixture; test the two representative traversals, ownership/expertise separation, bounded impact, decisions/supersession, freshness/idempotency, evidence/abstention, pre-retrieval permission filtering, prompt-injection-safe boundaries, parameterization/bounds, graph-unavailable fail-closed behavior, and approval-gated reversible action; add a small evaluator that reports observed pass/fail and evidence/provenance/abstention/action metrics without importing external benchmark claims.
- **Acceptance criteria:**
  - AC-P3-1: Positive and negative cases from the research evaluation matrix run through FalkorDB and produce machine-readable results; the report distinguishes passed, failed, and not implemented.
  - AC-P3-2: Tests prove the public principal cannot retrieve or be influenced by private records, prompt-injection text cannot cause a tool/policy mutation, and invalid/raw/unbounded Cypher inputs are rejected.
  - AC-P3-3: Tests prove deterministic abstention for unknown/insufficient evidence, graph-unavailable failure, bounded/capped impact traversal, current-versus-superseded decisions, and older refresh rejection.
  - AC-P3-4: If the action path is claimed, tests prove explicit approval, authorization, target/evidence binding, reversibility, and `ActionEvent` receipt; otherwise the evaluation marks the secondary track as not implemented.
  - AC-P3-5: `npm run test:unit`, `npm run test:integration`, and the evaluator pass with honest observed results; the handoff gives QA exact setup and any known gaps.
- **Verify commands:** `npm run test:unit`; `npm run test:integration`; `npm run evaluate`; `npm run build`
- **Handoff expectations:** write `.pipeline/handoffs/phase-P3.md` with test/evaluation commands, observed results and coverage gaps, fixture prerequisites, security-boundary evidence, action-track verdict, and prioritized QA risks. Keep all test/evaluation changes inside owned globs.

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| FalkorDB becomes decorative | Required questions use real OpenCypher traversals; graph outage is a visible failure; UI displays returned paths and trace IDs. |
| Fixture or ontology grows beyond a hackathon | Stable IDs, a small fixed label/relationship allowlist, deterministic loader, and no live connectors or broad extraction. |
| Hallucinated or stale answer | Structured claims/evidence, dates/hashes, supersession policy, freshness events, deterministic abstention, and optional template synthesis only from returned fields. |
| Expertise is mistaken for ownership or availability | Separate authoritative ownership edges from dated activity; label inferred activity and show the caveat. |
| Permission leakage | Deny-by-default synthetic scopes are applied before candidate lookup, full-text retrieval, and graph expansion; tests include private records. |
| Prompt injection reaches action | Retrieved content is evidence-only; action functions accept typed IDs and server policy results, never model-selected tools or instructions. |
| Cypher injection or expensive traversal | Checked-in query templates, parameters for values, allowlisted schema, fixed depth/fanout, `LIMIT`, response-size caps, and redacted traces. |
| Freshness race or duplicate data | Fixture version/content hash/idempotency keys; reject older versions; retain old source evidence and create `ChangeEvent`. |
| Optional action is unsafe or incomplete | Keep it local and reversible; require explicit approval and receipt; omit the secondary-track claim if any test fails. |
| Team loses time to infrastructure | Docker Compose plus synthetic data, no required LLM/API key, no distributed deployment, no production connector/ACL work. |
| Evaluation overclaiming | Report only this fixture's observed metrics and limitations; do not transfer GraphRAG or competitor claims to Threadline. |

## 7. Definition of done

- Every must-have feature passes its phase acceptance criteria and the QA Playwright flow, including the two representative questions against FalkorDB.
- Fresh local setup starts FalkorDB and the app without private credentials; README/docs explain setup, synthetic data, schema, queries, trust boundaries, demo, evaluation, and known limitations.
- Ownership, evidence-backed expertise, bounded impact, decision rationale/supersession, freshness/change events, source evidence, deterministic abstention, synthetic permission filtering, prompt-injection-safe boundaries, and parameterized/allowlisted/bounded Cypher are visibly demonstrated.
- The optional action track is claimed only if authorization, explicit approval, reversibility, and `ActionEvent` tests pass; otherwise it is documented as not implemented.
- The app builds with no errors, test/evaluation results are honest, and no live connectors, private data, secrets, production ACL claims, distributed deployment, full vector GraphRAG, broad text-to-Cypher, or destructive external writes have entered MVP scope.
