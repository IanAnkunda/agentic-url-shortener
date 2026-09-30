# Agentic URL Shortener

A production-oriented interview prototype demonstrating two things together:

1. A Java/Spring Boot URL-shortening service with analytics and reliability behavior.
2. A governed, stateful agentic SDLC workflow that turns requirements into reviewable engineering outputs.

## What is implemented

- `POST /api/v1/urls` — create generated or custom short URL, optional TTL.
- `GET /{code}` — validate expiry, increment analytics, redirect.
- `GET /api/v1/urls/{code}/analytics` — aggregate click metrics.
- `DELETE /api/v1/urls/{code}` — delete link.
- PostgreSQL + Flyway migration.
- Agent dependency graph covering requirements, architecture, security, implementation, test planning, validation, documentation, and release readiness.
- Human approval checkpoints for design and release.
- Bounded retries, safe stop, rollback accounting, audit trail, reliability metrics, and dynamic replanning.
- Greenfield, brownfield, and ambiguous requirement scenarios.

## Prerequisites

- Java 21
- Maven 3.9+
- Docker + Docker Compose
- Python 3.11+
- Git

No Python packages are required for the baseline orchestrator.

## Run the URL shortener

From the repository root:

```bash
docker compose up -d && cd backend && mvn spring-boot:run
```

Create a URL:

```bash
curl -s -X POST http://localhost:8080/api/v1/urls \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/path","customAlias":"demo1","ttlSeconds":3600}'
```

Resolve it:

```bash
curl -i http://localhost:8080/demo1
```

Analytics:

```bash
curl -s http://localhost:8080/api/v1/urls/demo1/analytics
```

## Run tests

```bash
cd backend && mvn test
```

```bash
python -m unittest orchestrator.test_engine
```

## Run the agentic scenarios

First demonstrate a governance safe stop:

```bash
python -m orchestrator.main --scenario scenarios/greenfield.json
```

Then run with explicit approvals:

```bash
python -m orchestrator.main --scenario scenarios/greenfield.json --approve design --approve release
python -m orchestrator.main --scenario scenarios/brownfield.json --approve design --approve release
python -m orchestrator.main --scenario scenarios/ambiguous.json --approve design --approve release
```

Each run writes reviewable state and audit history beneath `.agent_runs/<run-id>/`.

## Repository layout

```text
backend/          Spring Boot URL shortener
orchestrator/     Agentic SDLC dependency-graph engine
scenarios/        Greenfield, brownfield, ambiguous inputs
docs/             Architecture, OpenAPI, trade-offs, demo guidance
```

## Production evolution

For larger traffic, introduce a cache for redirect lookups and publish click events to Kafka for asynchronous aggregation. Add authentication/tenancy, abuse detection, rate limiting, secrets management, deployment policy integration, and a real LLM-provider adapter behind the governed agent handlers.
