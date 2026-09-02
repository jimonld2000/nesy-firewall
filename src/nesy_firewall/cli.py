from __future__ import annotations

import argparse
import json
from pathlib import Path
from .experiment import run_ollama, verify_candidates
from .gatekeeper import Gatekeeper
from .ollama import OllamaClient
from .prepare import write_flows

ROOT = Path(__file__).resolve().parents[2]

def load_json(path: Path) -> list[dict]: return json.loads(path.read_text())

def benchmark(args: argparse.Namespace) -> int:
    rules = load_json(args.rules)[:args.limit] if args.limit else load_json(args.rules)
    candidates = [{**rule.get("match", rule), "action": rule.get("action", "ALLOW")} for rule in rules]
    print(json.dumps(verify_candidates(candidates, args.output), indent=2)); return 0

def ablation(args: argparse.Namespace) -> int:
    rules = load_json(args.rules)[:args.limit] if args.limit else load_json(args.rules); report = {}
    for count in range(1, 5):
        gatekeeper = Gatekeeper.default(); gatekeeper.invariants = gatekeeper.invariants[:count]
        records = [gatekeeper.evaluate({**rule.get("match", rule), "action": rule.get("action", "ALLOW")}) for rule in rules]
        report[str(count)] = {"invariants": count, "rules": len(records), "verified": sum(item["safe"] for item in records), "blocked": sum(not item["safe"] for item in records), "median_latency_us": sorted(item["latency_us"] for item in records)[len(records)//2]}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(report, indent=2) + "\n"); print(json.dumps(report, indent=2)); return 0

def live(args: argparse.Namespace) -> int:
    flows = load_json(args.flows)[:args.limit] if args.limit else load_json(args.flows)
    print(json.dumps(run_ollama(flows, args.output, args.model, args.base_url, args.seed), indent=2)); return 0

def check(args: argparse.Namespace) -> int:
    models = OllamaClient("unused", args.base_url).available_models(); print("\n".join(models)); return 0

def prepare(args: argparse.Namespace) -> int:
    print(f"Wrote {write_flows(args.input, args.output, args.sample_size, args.seed)} flows to {args.output}"); return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Neuro-symbolic firewall experiments"); commands = parser.add_subparsers(dest="command", required=True)
    def common(name: str):
        sub = commands.add_parser(name); sub.add_argument("--rules", type=Path, default=ROOT / "data" / "test_rules.json"); sub.add_argument("--limit", type=int); return sub
    sub = common("benchmark"); sub.add_argument("--output", type=Path, default=ROOT / "runs" / "benchmark"); sub.set_defaults(fn=benchmark)
    sub = common("ablation"); sub.add_argument("--output", type=Path, default=ROOT / "runs" / "ablation.json"); sub.set_defaults(fn=ablation)
    sub = commands.add_parser("run-ollama"); sub.add_argument("--model", required=True); sub.add_argument("--base-url", default="http://127.0.0.1:11434"); sub.add_argument("--flows", type=Path, default=ROOT / "data" / "flows_250.json"); sub.add_argument("--limit", type=int, default=25); sub.add_argument("--seed", type=int, default=42); sub.add_argument("--output", type=Path, default=ROOT / "runs" / "ollama"); sub.set_defaults(fn=live)
    sub = commands.add_parser("check-ollama"); sub.add_argument("--base-url", default="http://127.0.0.1:11434"); sub.set_defaults(fn=check)
    sub = commands.add_parser("prepare-flows"); sub.add_argument("--input", type=Path, required=True); sub.add_argument("--output", type=Path, required=True); sub.add_argument("--sample-size", type=int, default=250); sub.add_argument("--seed", type=int, default=1042); sub.set_defaults(fn=prepare)
    args = parser.parse_args(); return args.fn(args)

if __name__ == "__main__": raise SystemExit(main())
