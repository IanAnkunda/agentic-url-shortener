import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.engine import AgenticEngine, SafeStop


class EngineTest(unittest.TestCase):
    def test_requires_human_design_approval(self):
        scenario = {"name": "x", "requirement": "build x", "assumptions": []}
        with tempfile.TemporaryDirectory() as d:
            engine = AgenticEngine(Path(d))
            with self.assertRaises(SafeStop):
                engine.run(scenario, approvals=set())

    def test_end_to_end_with_approvals(self):
        scenario = {"name": "x", "requirement": "build x", "assumptions": []}
        with tempfile.TemporaryDirectory() as d:
            engine = AgenticEngine(Path(d))
            state = engine.run(scenario, approvals={"design", "release"})
            self.assertIn("release_readiness", state.completed)
            self.assertEqual(8, len(state.completed))

    def test_dynamic_replan_is_audited(self):
        scenario = {
            "name": "x",
            "requirement": "build x",
            "assumptions": [],
            "change_event": {"description": "new requirement", "invalidate": ["requirements"]},
        }
        with tempfile.TemporaryDirectory() as d:
            engine = AgenticEngine(Path(d))
            state = engine.run(scenario, approvals={"design", "release"})
            self.assertEqual(1, state.replans)
            self.assertTrue(any(e["event"] == "replanned" for e in state.events))


if __name__ == "__main__":
    unittest.main()
