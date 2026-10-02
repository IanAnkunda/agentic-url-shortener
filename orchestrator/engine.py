from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Dict, List, Set


@dataclass
class NodeResult:
    node: str
    status: str
    output: dict = field(default_factory=dict)
    attempts: int = 0
    duration_ms: int = 0
    error: str | None = None


@dataclass
class RunState:
    run_id: str
    scenario: str
    requirement: str
    assumptions: List[str]
    approvals: Set[str]
    completed: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    retries: int = 0
    rollbacks: int = 0
    events: List[dict] = field(default_factory=list)
    artifacts: Dict[str, dict] = field(default_factory=dict)
    replans: int = 0


class SafeStop(RuntimeError):
    pass


class AgenticEngine:
    """Stateful SDLC dependency-graph orchestrator.

    Design Decision: Prioritized deterministic state transitions and explicit governance 
    over autonomous LLM looping. By keeping the orchestration layer separate from the 
    LLM generation logic, preventing runaway execution costs, enforce human approval 
    boundaries and guarantee audit-grade traceability
    """

    GRAPH: Dict[str, Set[str]] = {
        "requirements": set(),
        "architecture": {"requirements"},
        "security_review": {"architecture"},
        "implementation": {"architecture"},
        "test_plan": {"architecture"},
        "validation": {"implementation", "test_plan", "security_review"},
        "documentation": {"implementation", "validation"},
        "release_readiness": {"documentation", "validation"},
    }

    HUMAN_GATES = {"architecture": "design", "release_readiness": "release"}

    def __init__(self, run_root: Path, max_retries: int = 2):
        self.run_root = run_root
        self.max_retries = max_retries
        self.handlers: Dict[str, Callable[[RunState], dict]] = {
            "requirements": self.requirements_agent,
            "architecture": self.architecture_agent,
            "security_review": self.security_agent,
            "implementation": self.implementation_agent,
            "test_plan": self.test_agent,
            "validation": self.validation_agent,
            "documentation": self.docs_agent,
            "release_readiness": self.release_agent,
        }

    def run(self, scenario: dict, approvals: Set[str]) -> RunState:
        state = RunState(
            run_id=str(uuid.uuid4())[:8],
            scenario=scenario["name"],
            requirement=scenario["requirement"],
            assumptions=scenario.get("assumptions", []),
            approvals=approvals,
        )
        self._event(state, "run_started", scenario=state.scenario)

        pending = set(self.GRAPH)
        change_applied = False
        while pending:
            ready = sorted(node for node in pending if self.GRAPH[node].issubset(set(state.completed)))
            if not ready:
                raise SafeStop("No runnable nodes remain; dependency graph is blocked.")

            # Trade-off: While the graph resolves independent nodes e.g., security_review, 
            # implementation, test_plan as parallel-ready, they are executed synchronously 
            # in this prototype. This guarantees deterministic audit logs for review and 
            # avoids thread-safety complexity in local SQLite/RunState storage.
            self._event(state, "ready_set", nodes=ready)
            for node in ready:
                self._run_node(state, node)
                pending.remove(node)

                if node == "architecture" and scenario.get("change_event") and not change_applied:
                    self._replan(state, scenario["change_event"], pending)
                    change_applied = True

        self._event(state, "run_completed", metrics=self.metrics(state))
        self._persist(state)
        return state

    def _run_node(self, state: RunState, node: str) -> None:
        gate = self.HUMAN_GATES.get(node)
        if gate and gate not in state.approvals:
            self._event(state, "approval_required", node=node, approval=gate)
            self._persist(state)
            raise SafeStop(f"Human approval '{gate}' is required before {node} can complete.")

        handler = self.handlers[node]
        started = time.perf_counter()
        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                self._event(state, "node_started", node=node, attempt=attempt)
                output = handler(state)
                duration_ms = int((time.perf_counter() - started) * 1000)
                state.artifacts[node] = asdict(NodeResult(node, "success", output, attempt, duration_ms))
                state.completed.append(node)
                self._event(state, "node_completed", node=node, attempt=attempt, duration_ms=duration_ms)
                self._persist(state)
                return
            except Exception as exc:  
                # Fault Isolation Boundary: Catching broad exceptions here ensures that 
                # a hallucination or parsing error from downstream LLM agent cannot 
                # crash the core orchestrator. The failure is accounted for, the retry 
                # budget is decremented and system gracefully loops.
                last_error = str(exc)
                if attempt <= self.max_retries:
                    state.retries += 1
                    self._event(state, "node_retry", node=node, attempt=attempt, error=last_error)
                    continue
                state.failed.append(node)
                state.rollbacks += 1
                self._event(state, "rollback", node=node, reason=last_error)
                self._persist(state)
                raise SafeStop(f"{node} failed after bounded retries: {last_error}") from exc

    def _replan(self, state: RunState, change_event: dict, pending: Set[str]) -> None:
        state.replans += 1
        state.requirement += f"\nCHANGE: {change_event['description']}"
        impacted = change_event.get("invalidate", [])
        for node in impacted:
            if node in state.completed:
                state.completed.remove(node)
                pending.add(node)
                state.artifacts.pop(node, None)
        self._event(state, "replanned", change=change_event["description"], invalidated=impacted)
        self._persist(state)

    def metrics(self, state: RunState) -> dict:
        total = len(state.completed) + len(state.failed)
        return {
            "success_rate": round(len(state.completed) / total, 3) if total else 0,
            "retry_count": state.retries,
            "rollback_count": state.rollbacks,
            "replan_count": state.replans,
            "completed_nodes": len(state.completed),
        }

    def _event(self, state: RunState, event: str, **details) -> None:
        state.events.append({"ts": time.time(), "event": event, **details})

    def _persist(self, state: RunState) -> None:
        target = self.run_root / state.run_id
        target.mkdir(parents=True, exist_ok=True)
        payload = asdict(state)
        payload["approvals"] = sorted(state.approvals)
        (target / "state.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        with (target / "audit.jsonl").open("w", encoding="utf-8") as fh:
            for event in state.events:
                fh.write(json.dumps(event) + "\n")

    # -------------------------------------------------------------------------
    # Agent Handlers
    # 
    # Architecture Note: LLM provider integration is deliberately stubbed here. 
    # This ensures the prototype runs deterministically to prove the orchestration, 
    # governance and dynamic replanning logic. In a production state, these boundaries 
    # take the RunState and inject LangChain/OpenAI clients but the I/O contract 
    # remains strictly governed by the engine.
    # -------------------------------------------------------------------------
    def requirements_agent(self, state: RunState) -> dict:
        return {
            "normalized_problem": state.requirement,
            "assumptions": state.assumptions,
            "acceptance_criteria": [
                "Requirement is testable and traceable to implementation tasks",
                "Ambiguities are recorded rather than silently guessed",
                "High-impact decisions require human approval",
            ],
        }

    def architecture_agent(self, state: RunState) -> dict:
        return {
            "components": ["Spring Boot API", "PostgreSQL", "Agentic orchestrator", "Audit store"],
            "decisions": [
                "Use opaque Base62-style codes instead of hashing user URLs",
                "Keep analytics writes separate from redirect semantics",
                "Use explicit workflow dependencies and approval gates",
            ],
        }

    def security_agent(self, state: RunState) -> dict:
        return {
            "controls": [
                "HTTPS URLs only",
                "Input length and alias validation",
                "No secret values in audit logs",
                "Bounded retries and safe-stop on repeated failures",
            ],
            "risks": ["Abuse/phishing", "hot-key traffic", "analytics contention", "expired-link caching"],
        }

    def implementation_agent(self, state: RunState) -> dict:
        return {
            "target_modules": ["controller", "service", "repository", "schema migration"],
            "change_strategy": "Small backward-compatible changes with tests before release gate",
        }

    def test_agent(self, state: RunState) -> dict:
        return {
            "tests": [
                "Create and resolve URL",
                "Duplicate alias conflict",
                "Expired URL returns 410",
                "Analytics count increments",
                "Unknown code returns 404",
                "Agent safe-stop without approval",
                "Dynamic replan invalidates impacted stages",
            ]
        }

    def validation_agent(self, state: RunState) -> dict:
        return {
            "checks": ["API contract", "unit tests", "migration validity", "security review", "audit completeness"],
            "status": "review_required",
        }

    def docs_agent(self, state: RunState) -> dict:
        return {
            "documents": ["README", "architecture.md", "scenario reports", "tradeoffs.md"],
        }

    def release_agent(self, state: RunState) -> dict:
        return {
            "decision": "ready_if_ci_green",
            "rollback": "Revert deployment/database-compatible application change; preserve audit trail",
            "limitations": ["Single-region prototype", "No distributed cache in baseline", "Basic aggregate analytics"],
        }
