# Project Agent Rules

These rules govern all design, coding, data, documentation, and submission work for this project.

## 1. Team and participation

- A project may be completed solo or by a team of up to four members.
- Each participant may belong to only one team.
- Any team member may contribute code, design, research, testing, documentation, or presentation material, but every member must understand the submitted project.

## 2. FalkorDB is mandatory and central

- FalkorDB must be the primary graph database.
- FalkorDB must support a central part of the product’s functionality.
- The graph must perform real application work. It must not be only a visualization layer over ordinary storage.
- Before adding a feature, confirm that removing FalkorDB would materially break or degrade the product’s core behavior.
- Core product behavior should depend on graph operations such as:
  - graph traversal and multi-hop reasoning;
  - relationship-aware retrieval;
  - agent memory and coordination;
  - entity and fact resolution;
  - provenance and explainability;
  - graph-based planning or decision-making.
- If FalkorDB is removed, the project must not continue to provide its primary value through an unrelated database with the graph reduced to decoration.

## 3. Deployment and technology choices

- FalkorDB may run through Docker, a self-hosted instance, FalkorDB Cloud, or another accepted FalkorDB deployment.
- Any language, framework, frontend, backend, hosting provider, open-source library, public API, template, or deployment platform may be used alongside FalkorDB.
- Use official FalkorDB clients and documented OpenCypher behavior where possible.
- Do not assume Neo4j-only syntax or procedures without checking FalkorDB compatibility.
- Prefer parameterized Cypher queries. Do not interpolate untrusted user or model-generated values into Cypher.
- Keep graph writes idempotent and use deterministic identifiers where practical.
- Use read-only graph queries for retrieval when appropriate and bound expensive traversals with limits and timeouts.

## 4. Tracks

The project may enter one, two, or all three tracks:

- **Agents That Act on Connected Data**
- **Agent Memory and Coordination**
- **Company Brain**

The selected track or tracks must be named in the README, demo materials, and final submission. The implementation and demo must clearly show how the product satisfies each selected track.

## 5. Data-use restrictions

- Only use data that the team is authorized to use.
- Acceptable data includes:
  - public data;
  - synthetic data;
  - data created by the team;
  - data for which the team has explicit permission.
- Do not load private, login-protected, paywalled, personal, confidential, proprietary, or otherwise restricted information into FalkorDB or project artifacts.
- Do not commit credentials, tokens, cookies, private payloads, or restricted datasets.
- Document the origin and license or permission status of every external dataset and asset.
- When in doubt, use synthetic or clearly public data instead of importing questionable content.

## 6. Hackathon timing

- The hackathon runs from **October 15, 12:01 AM IST through October 18, 11:59 PM IST**.
- Submissions close at the end of that window.
- Before the hackathon starts, permitted preparation includes:
  - discussing ideas;
  - writing notes;
  - sketching the graph model;
  - preparing diagrams;
  - reviewing public documentation;
  - preparing non-product planning material.
- Main coding and design work must begin after the hackathon starts.
- Do not represent pre-hackathon planning or scaffolding as original hackathon implementation work.
- Keep a lightweight record of major implementation milestones if the timing of work may need to be demonstrated.

## 7. Required graph-first architecture

- Define the graph model before implementing major product behavior.
- The README must document:
  - node labels;
  - relationship types;
  - key properties;
  - identity and uniqueness rules;
  - tenant or user-scope rules, if applicable;
  - provenance and source relationships;
  - the queries or algorithms that make the graph essential.
- The product should preserve source evidence for important facts, decisions, agent actions, and generated answers.
- For agent memory or coordination features, represent relevant state and handoffs as graph data rather than only transient in-process variables.
- For connected-data features, demonstrate meaningful traversal, relationship filtering, or multi-hop reasoning.
- For Company Brain features, demonstrate how the graph connects people, teams, projects, documents, decisions, systems, or capabilities.

## 8. Required submission artifacts

Every submission must include:

1. A public source-code repository.
2. A README with:
   - project purpose;
   - selected track or tracks;
   - setup instructions;
   - FalkorDB deployment instructions;
   - graph data model;
   - data sources and licensing;
   - architecture overview;
   - limitations and known trade-offs.
3. The Cypher queries and/or graph algorithms the product depends on.
4. A demo video showing the working project and the graph doing real work.
5. A live deployment, or complete local setup instructions when live deployment is not practical.
6. A clear disclosure of AI coding-assistant use.

## 9. Demo and verification requirements

- The demo must show a working end-to-end flow, not only screenshots or architecture diagrams.
- Show at least one user action whose result depends on FalkorDB data or graph traversal.
- When possible, show the graph query, graph result, or explainability path behind the product behavior.
- Demonstrate the selected track or tracks explicitly.
- Make the local setup reproducible from a clean environment using the README.
- Verify that the documented commands, environment variables, FalkorDB startup process, seed data, and demo flow actually work before submission.
- Do not claim a feature, benchmark, deployment, or test is complete unless it has been run and verified.

## 10. AI coding-assistant policy

- AI coding assistants are allowed.
- Their use must be disclosed in the README and submission materials.
- Participants remain responsible for all generated or AI-assisted code.
- Every participant must understand and be able to explain:
  - the graph model;
  - the FalkorDB deployment;
  - the Cypher queries and graph algorithms;
  - the agent architecture;
  - the retrieval, memory, or coordination flow;
  - the security and data-use decisions;
  - the project’s technical trade-offs.
- Projects that are entirely generated by AI without meaningful participant contribution, verification, or technical understanding may be rejected.
- Review, test, and simplify AI-generated code before committing it.
- Never accept AI-generated claims about FalkorDB syntax, performance, security, or compatibility without checking official documentation or running a focused test.

## 11. Quality and integrity rules

- Do not plagiarize code, designs, documentation, datasets, demos, or project ideas without complying with their licenses and clearly attributing them.
- Do not manipulate benchmarks, demos, judging inputs, or evaluation results.
- Do not misrepresent pre-hackathon work as hackathon work.
- Do not hide known limitations, broken setup steps, missing dependencies, or unsupported claims.
- Record third-party licenses and attribution requirements.
- Keep secrets and restricted information out of the repository, logs, screenshots, demo video, and documentation.

## 12. Prizes and intellectual property

- The total prize pool is worth **$20,000**.
- The best project in each track wins a prize:
  - **Agents That Act on Connected Data:** iPhone 18 Pro.
  - **Agent Memory and Coordination:** PS5 with GTA VI.
  - **Company Brain:** M6 Mac Mini.
- Every member of a winning team receives the prize for that team’s winning track.
- Intellectual property developed during the hackathon belongs to the participant or team that created it.
- Teams should agree internally on ownership, licensing, reuse, and attribution before submission.

## 13. Conduct and disqualification

- Treat participants, organizers, sponsors, speakers, judges, and community members with respect.
- Harassment, discrimination, plagiarism, or attempts to manipulate the judging process result in disqualification.
- Failure to follow these rules or the WeMakeDevs Code of Conduct may result in disqualification.

## 14. Agent operating checklist

Before implementing a feature, confirm:

- [ ] The feature belongs to one or more declared tracks.
- [ ] FalkorDB is required for the feature’s core behavior.
- [ ] The graph model and relevant Cypher queries are documented or will be documented.
- [ ] All input data is public, synthetic, team-created, or explicitly authorized.
- [ ] Tenant, user, agent, and permission boundaries are defined where relevant.
- [ ] The implementation uses safe, parameterized, bounded graph queries.
- [ ] AI-assisted work will be disclosed and reviewed.
- [ ] The result can be demonstrated in a reproducible local or live setup.

Before submitting, confirm:

- [ ] The repository is public.
- [ ] The README contains setup instructions and the graph data model.
- [ ] The required Cypher queries or graph algorithms are included.
- [ ] The demo video shows the working product and FalkorDB doing real work.
- [ ] The selected track or tracks are named everywhere required.
- [ ] Dataset sources, licenses, and permissions are documented.
- [ ] AI coding-assistant use is disclosed.
- [ ] The clean setup and demo flow have been run successfully.
- [ ] No restricted data, secrets, or credentials are included.
