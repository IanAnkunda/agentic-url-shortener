# Interview Demo Flow (8-10 minutes)

1. **Frame the assignment:** “I treated the URL shortener as the workload, but the main design problem as governed agentic SDLC orchestration.”
2. **Show architecture:** point to the explicit dependency graph and explain why implementation, security, and test planning can branch after design.
3. **Show controlled autonomy:** run a scenario without approvals and show the safe stop at the design gate.
4. **Run greenfield scenario:** approve design/release, then show `state.json`, `audit.jsonl`, and reliability metrics.
5. **Run brownfield scenario:** show the requirement-change event, invalidation, and replan rather than continuing with stale upstream assumptions.
6. **Run ambiguous scenario:** show how ambiguity is recorded as assumptions instead of silently guessed, with policy-sensitive behavior held behind human approval.
7. **Demo API:** create a URL, redirect it, then show analytics and expiry behavior.
8. **Close with trade-offs:** explain PostgreSQL baseline, synchronous analytics contention, future Kafka/cache path, and why the prototype keeps governance explicit.
