from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any


def normalize_rule(value: dict[str, Any]) -> dict[str, Any]:
    match = value.get("match", value)
    return {"source": match.get("source", match.get("source_cidr", match.get("src"))), "destination": match.get("destination", match.get("destination_cidr", match.get("dst"))), "destination_port": match.get("destination_port", match.get("port", match.get("dst_port"))), "protocol": str(match.get("protocol", "TCP")).upper(), "action": str(value.get("action", match.get("action", "ALLOW"))).upper()}


def parse_model_rules(text: str) -> list[dict[str, Any]]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    decoded = json.loads(text)
    values = decoded["rules"] if isinstance(decoded, dict) else decoded
    if not isinstance(values, list) or not all(isinstance(value, dict) for value in values): raise ValueError("model response must be a JSON list or an object with a rules list")
    return [normalize_rule(value) for value in values]


class OllamaClient:
    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434", timeout: int = 180):
        self.model, self.base_url, self.timeout = model, base_url.rstrip("/"), timeout

    def available_models(self) -> list[str]:
        with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=10) as response:
            return [item["name"] for item in json.load(response).get("models", [])]

    def generate(self, flows: list[dict[str, Any]], seed: int = 42) -> tuple[dict[str, Any], str]:
        prompt = """Convert these observed firewall flows into a conservative JSON object with one key, rules. Each rule must contain source CIDR, destination CIDR, destination_port integer, protocol TCP/UDP/ICMP, and action ALLOW/DENY. Return JSON only. Do not broaden a source or destination unless all included flows justify it.

Flows:
""" + json.dumps(flows, separators=(",", ":"))
        payload = {"model": self.model, "stream": False, "format": "json", "options": {"temperature": 0, "seed": seed}, "messages": [{"role": "user", "content": prompt}]}
        request = urllib.request.Request(f"{self.base_url}/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response: body = json.load(response)
        except urllib.error.URLError as error:
            raise RuntimeError(f"Ollama is unavailable at {self.base_url}: {error}") from error
        return payload, body.get("message", {}).get("content", "")
