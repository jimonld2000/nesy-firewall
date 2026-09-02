from nesy_firewall.ollama import parse_model_rules


def test_parses_and_normalizes_a_model_response():
    raw = '{"rules": [{"source_cidr": "203.0.113.0/24", "destination_cidr": "10.0.1.0/24", "destination_port": 443, "protocol": "tcp", "action": "allow"}]}'
    rules = parse_model_rules(raw)
    assert rules == [{"source": "203.0.113.0/24", "destination": "10.0.1.0/24", "destination_port": 443, "protocol": "TCP", "action": "ALLOW"}]
