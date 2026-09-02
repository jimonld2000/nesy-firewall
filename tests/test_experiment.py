import json
from pathlib import Path
from nesy_firewall.experiment import verify_candidates


def test_verification_writes_a_reusable_summary(tmp_path: Path):
    summary = verify_candidates(
        [{"source": "203.0.113.0/24", "destination": "10.0.3.0/24", "destination_port": 3306, "protocol": "TCP", "action": "ALLOW"}],
        tmp_path,
    )
    assert summary["blocked"] == 1
    assert json.loads((tmp_path / "summary.json").read_text())["total_candidates"] == 1
