# Architecture Overview

## System components

1. **URL Shortener API (Spring Boot)** — validates requests, creates short codes/custom aliases, resolves redirects, exposes analytics, and deletes links.
2. **PostgreSQL** — system of record for link metadata and aggregate analytics.
3. **Agentic SDLC Orchestrator (Python)** — executes a dependency graph across requirements, architecture, implementation, testing, security, documentation, validation, and release readiness.
4. **Run State + Audit Store** — `.agent_runs/<run-id>/state.json` and `audit.jsonl` retain decision lineage and lifecycle events.
5. **Human approval gates** — design and release gates are explicit. Missing approval causes a safe stop rather than implicit continuation.

## Agent workflow

```text
requirements
    |
architecture --[human design approval]
   /    |      \
security implementation test_plan
   \      |       /
       validation
           |
     documentation
           |
release_readiness --[human release approval]
```

The graph exposes independent post-architecture work as a ready set, making parallel execution possible. The reference implementation executes ready nodes deterministically for easy review, while preserving the graph semantics required to move those nodes to workers later.

## Governance controls

- Entry dependencies and exit completion status for every node.
- Human approvals at architecture and release readiness.
- Maximum two retries after the first attempt.
- Safe stop on repeated failure or missing approvals.
- Rollback event accounting when a node exhausts retries.
- Audit events for starts, retries, approvals, replans, completion, and rollbacks.
- Replanning support when upstream requirements change; impacted completed nodes can be invalidated and rerun.
- Reliability metrics: success rate, retry count, rollback count, replan count, and completed node count.

## URL shortener data flow

```text
POST /api/v1/urls -> validate -> generate/reserve code -> PostgreSQL -> 201
GET /{code}       -> lookup -> expiry check -> analytics increment -> 302
GET analytics     -> lookup -> aggregate metrics -> 200
DELETE             -> lookup -> delete -> 204
```

## Key decisions

- Use random URL-safe identifiers rather than deterministic hashes to avoid leaking equality relationships between original URLs.
- Require HTTPS destinations in the prototype.
- Keep the API versioned from the beginning to support future schema evolution.
- Use Flyway migration scripts instead of application-managed schema mutation.
- Keep the baseline intentionally simple: no distributed cache and aggregate click analytics only. Those are explicit scaling trade-offs rather than hidden omissions.
