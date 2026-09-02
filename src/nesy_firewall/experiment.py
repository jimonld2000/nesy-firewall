from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from .gatekeeper import Gatekeeper
from .ollama import OllamaClient, parse_model_rules


def verify_candidates(candidates: list[dict[str, Any]], output: Path, policy: Gatekeeper | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True); gatekeeper = policy or Gatekeeper.default(); records = []
    for index, candidate in enumerate(candidates):
        decision = gatekeeper.evaluate(candidate)
        records.append({"candidate_id": index, "rule": candidate, **decision})
    (output / "verification.json").write_text(json.dumps(records, indent=2) + "\n")
    summary = {"total_candidates": len(records), "verified": sum(record["safe"] for record in records), "blocked": sum(not record["safe"] for record in records), "invalid": sum(record["reason"].startswith("invalid") for record in records)}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def run_ollama(flows: list[dict[str, Any]], output: Path, model: str, base_url: str, seed: int) -> dict[str, Any]:
    client = OllamaClient(model, base_url); request, response = client.generate(flows, seed)
    output.mkdir(parents=True, exist_ok=True)
    (output / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (output / "model_response.txt").write_text(response + "\n")
    candidates = parse_model_rules(response)
    (output / "candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
    summary = verify_candidates(candidates, output)
    run = {"model": model, "base_url": base_url, "seed": seed, "input_flows": len(flows), **summary}
    (output / "run.json").write_text(json.dumps(run, indent=2) + "\n")
    return run
