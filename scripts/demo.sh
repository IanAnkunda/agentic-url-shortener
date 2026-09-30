#!/usr/bin/env bash
set -euo pipefail
python -m orchestrator.main --scenario scenarios/greenfield.json --approve design --approve release
python -m orchestrator.main --scenario scenarios/brownfield.json --approve design --approve release
python -m orchestrator.main --scenario scenarios/ambiguous.json --approve design --approve release
