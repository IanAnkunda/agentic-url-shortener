from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator.engine import AgenticEngine, SafeStop


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an auditable agentic SDLC scenario")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON")
    parser.add_argument("--approve", action="append", default=[], choices=["design", "release"])
    parser.add_argument("--runs", default=".agent_runs", help="Run-state directory")
    args = parser.parse_args()

    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    engine = AgenticEngine(Path(args.runs))

    try:
        state = engine.run(scenario, set(args.approve))
    except SafeStop as exc:
        print(f"SAFE STOP: {exc}")
        return 2

    print(json.dumps({
        "run_id": state.run_id,
        "scenario": state.scenario,
        "completed": state.completed,
        "metrics": engine.metrics(state),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
