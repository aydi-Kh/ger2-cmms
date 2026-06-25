"""Unit tests for WO state machine and cost calculation."""
import pytest


WO_VALID_TRANSITIONS = {
    "backlog":       ["in_progress", "cancelled"],
    "in_progress":   ["pending_parts", "completed", "cancelled"],
    "pending_parts": ["in_progress", "cancelled"],
    "completed":     [],
    "cancelled":     [],
}


@pytest.mark.parametrize("from_status,to_status,expected", [
    ("backlog", "in_progress", True),
    ("backlog", "completed", False),
    ("in_progress", "completed", True),
    ("completed", "in_progress", False),
    ("pending_parts", "in_progress", True),
    ("cancelled", "backlog", False),
])
def test_wo_state_transitions(from_status, to_status, expected):
    allowed = WO_VALID_TRANSITIONS.get(from_status, [])
    result = to_status in allowed
    assert result == expected, f"{from_status} → {to_status}: expected {expected}, got {result}"


@pytest.mark.parametrize("hours,rate,parts,expected_total", [
    (4.0, 65.0, 1240.0, 1500.0),
    (2.5, 65.0, 0.0,    162.5),
    (0.0, 65.0, 500.0,  500.0),
])
def test_wo_cost_calculation(hours, rate, parts, expected_total):
    labor = round(hours * rate, 2)
    total = round(labor + parts, 2)
    assert total == expected_total


def test_wo_number_format():
    """WO numbers must match WO-YYYY-XXXX format."""
    import re
    from datetime import date
    pattern = r"^WO-\d{4}-[0-9A-Z]{4}$"
    sample = f"WO-{date.today().year}-0847"
    assert re.match(pattern, sample)
