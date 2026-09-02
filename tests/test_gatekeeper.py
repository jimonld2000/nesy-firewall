from nesy_firewall.gatekeeper import Gatekeeper


def rule(source, destination, port, action="ALLOW"):
    return {"source": source, "destination": destination, "destination_port": port, "action": action}


def test_blocks_external_database_access():
    decision = Gatekeeper.default().evaluate(rule("203.0.113.0/24", "10.0.3.0/24", 3306))
    assert decision["safe"] is False
    assert decision["counterexample"]["destination_port"] == 3306


def test_accepts_narrow_web_access_and_rejects_invalid_input():
    gatekeeper = Gatekeeper.default()
    assert gatekeeper.evaluate(rule("203.0.113.10/32", "10.0.1.50/32", 443))["safe"] is True
    assert gatekeeper.evaluate(rule("broken", "10.0.1.50/32", 443))["reason"] == "invalid_rule"
