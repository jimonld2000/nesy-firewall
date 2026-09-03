# Neuro-Symbolic Firewall: Formal Verification for SLM-Generated Firewall Rules

Experimental code created for the ICASC 2026 paper **“A Neuro-Symbolic Middleware Architecture for Just-in-Time Formal Verification of Edge-Deployed Network Firewall Configurations.”**

ICASC 2026: <https://www.itim-cj.ro/icasc/>

## Overview

This project implements a neuro-symbolic firewall workflow for edge network operations:

1. **Local SLM generation** — an Ollama-hosted model converts observed flow records into candidate firewall rules.
2. **Compiler layer** — CIDR, port, and action fields are normalized into an explicit rule schema.
3. **Z3 policy gatekeeper** — each `ALLOW` rule is checked against declarative Zero Trust Network Access (ZTNA) invariants [1], [2].
4. **Auditable outcome** — verified rules are marked safe; unsafe rules include a concrete counterexample packet produced by the solver.

The gatekeeper uses QF_BV-style bit-vector constraints in Z3 [3], while the included flow corpus is a deterministic synthetic-IP transformation of the UCI Internet Firewall Dataset [4]. The local SLM path uses Ollama [5] and works with any already-installed, chat-capable local model that can follow JSON instructions.

No cloud API, API key, model download, firewall deployment, or policy change is performed by this repository.

## Project Structure

```text
nesy-firewall/
├── config/
│   └── policy.json                  # Four explicit example ZTNA policy violations
├── data/
│   ├── flows_250.json               # Frozen 250-flow input used by the SLM experiment
│   └── test_rules.json              # Deterministic 100-rule verification corpus
├── docs/
│   └── DATA_AND_RESULTS.md          # Data, result, and claim provenance
├── paper_results/                   # Frozen outputs from the exploratory study
│   ├── benchmark_analysis.json
│   ├── ablation_study.json
│   └── slm_experiment.json
├── references/
│   └── icasc2026_nesy_firewall.bib  # Complete bibliography from the paper
├── scripts/
│   ├── smoke.sh                     # Offline 10-rule smoke run
│   └── run_ollama_example.sh        # Local SLM → Z3 example
├── src/nesy_firewall/
│   ├── gatekeeper.py                # Z3 rule verifier and counterexample extraction
│   ├── ollama.py                    # Ollama client, JSON parser, schema normalization
│   ├── experiment.py                # Live-run evidence bundle writer
│   ├── prepare.py                   # Deterministic CSV → flow transformation
│   └── cli.py                       # benchmark, ablation, Ollama, and preparation commands
├── tests/                           # Offline unit tests
├── pyproject.toml
├── LICENSE
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.10 or newer;
- Ollama only for the live SLM experiment;
- any installed Ollama model for the live path, for example `qwen3:4b` or `qwen2.5-coder:7b`.

```bash
cd nesy-firewall
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### Step 1: Run the Offline Verification Workflow

The offline benchmark needs no Ollama service, GPU, network, or credentials.

```bash
python -m pytest -q
bash scripts/smoke.sh
nesy-firewall benchmark --output runs/benchmark
nesy-firewall ablation --output runs/ablation.json
```

Outputs:

- `runs/benchmark/verification.json` — one decision and counterexample per candidate rule;
- `runs/benchmark/summary.json` — verified, blocked, and invalid-rule counts;
- `runs/ablation.json` — fresh host-specific timing across one to four invariants.

### Step 2: Check Local Ollama

Start Ollama only if its service is not running, then inspect local models:

```bash
ollama serve
nesy-firewall check-ollama
```

The project never runs `ollama pull`; select a model already listed by `check-ollama`.

### Step 3: Run the Full Local SLM → Z3 Experiment

```bash
bash scripts/run_ollama_example.sh qwen3:4b
```

Equivalent explicit command:

```bash
nesy-firewall run-ollama \
  --model qwen3:4b \
  --flows data/flows_250.json \
  --limit 25 \
  --seed 42 \
  --output runs/ollama-qwen3-4b
```

The output directory is a complete local evidence bundle:

| Artifact | Purpose |
|---|---|
| `request.json` | Exact Ollama request, seed, and generation options |
| `model_response.txt` | Unmodified local-model response |
| `candidates.json` | Parsed and normalized candidate firewall rules |
| `verification.json` | Z3 outcome and counterexample for each candidate |
| `summary.json` | Candidate, verified, blocked, and invalid counts |
| `run.json` | Model, endpoint, seed, input count, and summary |

Run the original input-size protocol with `--limit 25`, `50`, and `100`. Local-model output is model/version/hardware dependent; preserving the request and raw response makes each result inspectable without claiming byte-identical generations.

## Experimental Components

### Formal Policy Gatekeeper

`config/policy.json` contains the four explicit example policies used in the experiment:

1. block external access to `10.0.3.0/24:3306` (database isolation);
2. block source CIDR `198.51.100.0/24` (threat-intelligence fixture);
3. block external SSH access to `10.0.4.0/24` (management protection);
4. restrict external-to-internal traffic to ports `80`, `443`, and `8080`.

The gatekeeper tests whether an `ALLOW` rule can match any packet that violates one of these invariants. SAT means unsafe and yields a counterexample; UNSAT means verified under this policy. A restrictive action (`DENY`, `DROP`, `REJECT`) is accepted without an over-permission query. Malformed or unknown actions fail closed.

### Local SLM Generation

`run-ollama` uses Ollama’s local `/api/chat` endpoint with JSON output, temperature `0`, and a recorded seed. The parser accepts both `source`/`destination` and common `source_cidr`/`destination_cidr` model field names, then sends every candidate through the same gatekeeper. This makes the SLM-generated configuration measurable while keeping formal acceptance independent from model trustworthiness.

### Dataset Preparation

The repository includes the frozen `flows_250.json` input used by the study. To transform an independently acquired local UCI-style CSV with deterministic synthetic IP assignments:

```bash
nesy-firewall prepare-flows \
  --input /path/to/firewall.csv \
  --output data/my_flows.json \
  --sample-size 250 \
  --seed 1042
```

Then replace `--flows data/flows_250.json` with `--flows data/my_flows.json` in the local SLM command. The raw UCI data is not redistributed; see `docs/DATA_AND_RESULTS.md`.

## Reported Exploratory Results

The original exploratory outputs are retained under `paper_results/` as frozen artifacts. They are not silently regenerated or presented as fresh results. In the original 100-rule benchmark, the saved analysis reports 56 verified-safe and 44 blocked rules, a median solver latency of 1,417.90 μs, and a P95 latency of 2,276.64 μs. New timing runs are expected to differ by host, Python, and Z3 version.

The original local SLM pilot used `qwen2.5-coder:7b` through Ollama. Its frozen summary is available as `paper_results/slm_experiment.json`; fresh Ollama executions must be evaluated from their own evidence bundles.

## Tools and References

[1] S. Rose, O. Borchert, S. Mitchell, and S. Connelly, “Zero Trust Architecture,” NIST SP 800-207, 2020. <https://doi.org/10.6028/NIST.SP.800-207>

[2] A. Piplai et al., “Knowledge-enhanced Neuro-Symbolic AI for Cybersecurity and Privacy,” *IEEE Internet Computing*, 2023. <https://doi.org/10.48550/arXiv.2308.02031>

[3] L. de Moura and N. Bjørner, “Z3: An Efficient SMT Solver,” *TACAS*, 2008. <https://doi.org/10.1007/978-3-540-78800-3_24>. Z3 bit-vector guide: <https://microsoft.github.io/z3guide/docs/theories/Bitvectors/>.

[4] UCI Machine Learning Repository, “Internet Firewall Dataset,” 2020. <https://archive.ics.uci.edu/ml/datasets/Internet+Firewall+Dataset>

[5] Ollama, local model runtime and API documentation. <https://ollama.com/>

[6] C. Diekmann, L. Hupel, and G. Carle, “Semantics-Preserving Simplification of Real-World Firewall Rule Sets,” *FM 2015*, 2016. <https://doi.org/10.1007/978-3-319-19249-9_13>

[7] T. Nelson et al., “The Margrave Tool for Firewall Analysis,” *LISA*, 2010.

[8] D. Kreutz et al., “Software-Defined Networking: A Comprehensive Survey,” *Proceedings of the IEEE*, 2015. <https://doi.org/10.1109/JPROC.2014.2371999>

The complete bibliography from the ICASC paper is included as `references/icasc2026_nesy_firewall.bib`.

## Scope and Responsible Use

This is the experimental code used for the ICASC 2026 paper, not a production firewall or a complete network-policy analysis system. The example invariants are intentionally narrow. Operational deployment requires a complete policy model, protocol/state semantics, integration testing, change control, and independent security review.

---

**Version:** 2.0.0

**Last Updated:** 2026-09-03

**Maintainer:** Daniel Jimon

**Paper Context:** ICASC 2026 — <https://www.itim-cj.ro/icasc/>
