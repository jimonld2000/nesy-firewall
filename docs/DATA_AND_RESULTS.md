# Data and result provenance

`data/flows_250.json` and `data/test_rules.json` were copied from the exploratory ICASC neuro-symbolic firewall project. `flows_250.json` is a deterministic, synthetic-IP transformation of an UCI Internet Firewall Dataset sample, not raw UCI data. The original UCI records are not redistributed here.

`prepare-flows` reproduces the transformation from a user-supplied CSV using seed `1042`; it is deliberately offline and does not download a source dataset. It accepts common destination-port/action column names.

`paper_results/` contains original frozen outputs. The benchmark and ablation commands produce fresh timing results, so values will differ by host. `run-ollama` captures the exact request, raw model response, candidates, verification records, and summary in a new run directory. It does not claim that a new model run reproduces a prior model response.
