from __future__ import annotations

import ipaddress
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any
from z3 import And, BitVec, BitVecVal, Not, Or, Solver, sat, unsat

ROOT = Path(__file__).resolve().parents[2]


class Gatekeeper:
    def __init__(self, policy: dict[str, Any], timeout_ms: int = 30_000):
        self.policy = policy
        self.solver = Solver(); self.solver.set("timeout", timeout_ms)
        self.source, self.destination, self.port = BitVec("source", 32), BitVec("destination", 32), BitVec("port", 16)
        self.invariants = [Not(self._violation(item)) for item in policy["violations"]]

    @classmethod
    def default(cls) -> "Gatekeeper":
        return cls(json.loads((ROOT / "config" / "policy.json").read_text()))

    @staticmethod
    def _network(value: str) -> tuple[int, int]:
        net = ipaddress.IPv4Network(value, strict=False)
        return int(net.network_address), net.prefixlen

    def _in_cidr(self, symbol: Any, cidr: str) -> Any:
        address, prefix = self._network(cidr)
        if prefix == 0: return True
        mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
        return (symbol & BitVecVal(mask, 32)) == BitVecVal(address & mask, 32)

    def _violation(self, item: dict[str, Any]) -> Any:
        terms = []
        if "source_in" in item: terms.append(self._in_cidr(self.source, item["source_in"]))
        if "source_not_in" in item: terms.append(Not(self._in_cidr(self.source, item["source_not_in"])))
        if "destination_in" in item: terms.append(self._in_cidr(self.destination, item["destination_in"]))
        if "destination_port" in item: terms.append(self.port == int(item["destination_port"]))
        if "destination_port_not_in" in item: terms.append(Not(Or(*[self.port == int(port) for port in item["destination_port_not_in"]])))
        return And(*terms)

    @staticmethod
    def _validate(rule: dict[str, Any]) -> tuple[str, str, int] | None:
        try:
            source, destination = str(rule["source"]), str(rule["destination"])
            ipaddress.IPv4Network(source, strict=False); ipaddress.IPv4Network(destination, strict=False)
            port = int(rule["destination_port"])
            if not 0 <= port <= 65535: raise ValueError
            return source, destination, port
        except (KeyError, TypeError, ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            return None

    def evaluate(self, rule: dict[str, Any]) -> dict[str, Any]:
        action = str(rule.get("action", "")).upper()
        if action in {"DENY", "DROP", "REJECT", "RESET-BOTH", "RESET_BOTH"}:
            return {"safe": True, "reason": "restrictive_action", "counterexample": None, "latency_us": 0.0, "memory_mb": 0.0}
        parsed = self._validate(rule)
        if action != "ALLOW" or parsed is None:
            return {"safe": False, "reason": "invalid_action" if action != "ALLOW" else "invalid_rule", "counterexample": None, "latency_us": 0.0, "memory_mb": 0.0}
        source, destination, port = parsed
        tracemalloc.start(); started = time.perf_counter_ns(); self.solver.push()
        try:
            allowed = And(self._in_cidr(self.source, source), self._in_cidr(self.destination, destination), self.port == port)
            self.solver.add(And(allowed, Not(And(*self.invariants))))
            outcome = self.solver.check()
            latency_us = (time.perf_counter_ns() - started) / 1000
            _, peak = tracemalloc.get_traced_memory()
            if outcome == sat:
                model = self.solver.model()
                value = lambda symbol: model.eval(symbol, model_completion=True).as_long()
                counterexample = {"source": str(ipaddress.IPv4Address(value(self.source))), "destination": str(ipaddress.IPv4Address(value(self.destination))), "destination_port": value(self.port)}
                return {"safe": False, "reason": "policy_violation", "counterexample": counterexample, "latency_us": latency_us, "memory_mb": peak / 1048576}
            return {"safe": outcome == unsat, "reason": "verified" if outcome == unsat else "solver_unknown", "counterexample": None, "latency_us": latency_us, "memory_mb": peak / 1048576}
        finally:
            self.solver.pop(); tracemalloc.stop()
