from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any


def build_flows(csv_path: Path, sample_size: int, seed: int) -> list[dict[str, Any]]:
    rows = list(csv.DictReader(csv_path.open(newline="")))
    if not rows: raise ValueError("CSV has no rows")
    rng = random.Random(seed); chosen = rng.sample(rows, min(sample_size, len(rows))); flows = []
    for index, row in enumerate(chosen):
        lower = {str(key).strip().lower().replace(" ", "_"): value for key, value in row.items()}
        port = next((lower[key] for key in ("destination_port", "dst_port", "dport", "dest_port") if lower.get(key)), "80")
        action = next((lower[key] for key in ("action", "action_taken", "decision", "verdict") if lower.get(key)), "ALLOW")
        flows.append({"rule_id": f"flow_{index:04d}", "match": {"source": f"{rng.randint(11, 223)}.{rng.randrange(256)}.{rng.randrange(256)}.{rng.randint(1,254)}/32", "destination": f"10.{rng.randrange(256)}.{rng.randrange(256)}.{rng.randint(1,254)}/32", "destination_port": int(float(port)), "protocol": "TCP"}, "action": action.upper()})
    return flows


def write_flows(csv_path: Path, output: Path, sample_size: int, seed: int) -> int:
    flows = build_flows(csv_path, sample_size, seed); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(flows, indent=2) + "\n"); return len(flows)
