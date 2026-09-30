# Risks, Trade-offs, Assumptions, and Limitations

## Trade-offs

- **PostgreSQL vs distributed key-value store:** PostgreSQL is simpler and provides durable consistency for the prototype. At high redirect volume, a cache or specialized key-value lookup tier would reduce database load.
- **Synchronous analytics increment:** Simple and strongly tied to a successful lookup, but a hot short code can cause write contention. A production-scale version could emit click events to Kafka and aggregate asynchronously.
- **Random 7-character codes:** Easy to generate and opaque. Collisions are handled by a uniqueness constraint plus bounded retry. Larger scale may require a coordinated ID strategy.
- **Aggregate analytics only:** Meets the prototype need while avoiding privacy-sensitive raw click-event storage.

## Risks and controls

- Abuse/phishing: HTTPS-only validation, clear extension point for reputation/policy checks, and documented need for policy-owner approval before automatic blocking.
- Code collisions: database uniqueness plus bounded retries and safe error handling.
- Expired links: checked before redirect; production caching must preserve expiry semantics.
- Agent runaway behavior: explicit graph, bounded retry, human gates, safe stop, and audit trail.
- Requirement drift: change events can invalidate prior stage outputs and force replanning.
- Sensitive data in reasoning/audit: the reference artifacts record engineering decisions, not secrets or credentials.

## Assumptions

- Prototype is single-region.
- Authentication/tenant isolation is outside the baseline assignment scope.
- Click count is the required analytics depth unless clarified otherwise.
- Database backups, HA, WAF, secrets management, and production deployment policies would be supplied by the target platform.

## Limitations

- No distributed cache.
- No Kafka/event-stream analytics pipeline in the baseline.
- No malicious-domain reputation provider.
- Agent handlers are deterministic/reviewable by default; they are designed so an LLM provider adapter can replace or augment individual handlers without changing workflow governance.
