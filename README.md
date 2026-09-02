# Neuro-Symbolic Firewall

Experimental code used for the neuro-symbolic firewall study. It places a Z3 policy gatekeeper after an Ollama-hosted local SLM: the model proposes firewall rules from observed flows, then the gatekeeper either verifies each `ALLOW` rule against explicit ZTNA invariants or blocks it with a concrete counterexample.

The repository has three reproducible paths:

1. deterministic Z3 benchmark over the included 100-rule corpus;
2. deterministic invariant-count ablation;
3. a local Ollama run using any installed chat-capable model, with complete request/response/run artifacts written to disk.

No cloud API, API key, model download, firewall deployment, or network policy change is performed by this code.

## Layout

```text
config/policy.json          the four policy violations checked by Z3
data/flows_250.json         frozen 250-flow SLM input from the exploratory work
data/test_rules.json        deterministic 100-rule gatekeeper corpus
paper_results/              frozen original experiment outputs
src/nesy_firewall/          data preparation, Ollama client, verifier, CLI
tests/                      offline behavior checks
scripts/                    reproducible shell entry points
```

## Installation

Requirements: Python 3.10+; an Ollama installation only for the live SLM path. Any installed Ollama model that follows JSON instructions can be used; `qwen2.5-coder:7b` was used in the original exploratory SLM pilot.

```bash
cd nesy-firewall
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Step 1: verify the deterministic gatekeeper

```bash
python -m pytest -q
bash scripts/smoke.sh
nesy-firewall benchmark --output runs/benchmark
nesy-firewall ablation --output runs/ablation.json
```

`runs/benchmark/verification.json` contains every decision and Z3 counterexample. `runs/benchmark/summary.json` is the compact count summary. Timing is intentionally regenerated and host-specific.

## Step 2: verify Ollama and select a model

Start Ollama if it is not already serving, then list models:

```bash
ollama serve                 # only when the service is not already running
nesy-firewall check-ollama
```

Choose one listed name, for example `qwen3:4b` or `qwen2.5-coder:7b`. The model must already be installed locally; the repository never runs `ollama pull`.

## Step 3: run the complete local SLM → Z3 experiment

```bash
bash scripts/run_ollama_example.sh qwen3:4b
# equivalent explicit command:
nesy-firewall run-ollama   --model qwen3:4b   --flows data/flows_250.json   --limit 25   --seed 42   --output runs/ollama-qwen3-4b
```

The run directory is the evidence bundle:

- `request.json`: exact Ollama request, including seed and temperature;
- `model_response.txt`: unmodified model output;
- `candidates.json`: parsed candidate rules;
- `verification.json`: one Z3 decision/counterexample per candidate;
- `summary.json` and `run.json`: aggregate result and run configuration.

Use `--limit 25`, `50`, and `100` to reproduce the original input-size protocol. A local model response is inherently model/version/hardware-dependent; the stored request and response make a run inspectable rather than pretending it is byte-identical to the original pilot.

## Optional: create flows from a local UCI-style CSV

The raw UCI dataset is not included. After independently acquiring it, transform a local CSV without downloading anything from this repository:

```bash
nesy-firewall prepare-flows   --input /path/to/firewall.csv   --output data/my_flows.json   --sample-size 250   --seed 1042
```

Then supply `--flows data/my_flows.json` to `run-ollama`.

## Policy and scope

`config/policy.json` defines the exact four example invariants: database isolation, a threat-intelligence source block, management SSH protection, and restricted external-to-internal ports. Replace it only after reviewing the meaning of each invariant. The supplied policy is an experiment fixture, not a complete production firewall policy or deployment guarantee.

See `docs/DATA_AND_RESULTS.md` for data and frozen-result provenance. The repository intentionally contains no credentials, model weights, private telemetry, or provider caches.
