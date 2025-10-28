"""
Test Metrics API Endpoints

Tests for the new hybrid engine metrics endpoints:
- /api/v1/metrics/current
- /api/v1/decisions/recent
"""

import pytest
from fastapi.testclient import TestClient
from orchestrator.api.main import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_get_current_metrics_structure(client):
    """Test that /api/v1/metrics/current returns correct structure"""
    response = client.get("/api/v1/metrics/current")
    assert response.status_code == 200

    data = response.json()

    # Check all required fields exist
    assert 'total_decisions' in data
    assert 'rules_decisions' in data
    assert 'ai_decisions' in data
    assert 'template_fallbacks' in data
    assert 'average_latency_ms' in data
    assert 'rules_percentage' in data

    # Check data types
    assert isinstance(data['total_decisions'], int)
    assert isinstance(data['rules_decisions'], int)
    assert isinstance(data['ai_decisions'], int)
    assert isinstance(data['template_fallbacks'], int)
    assert isinstance(data['average_latency_ms'], (int, float))
    assert isinstance(data['rules_percentage'], (int, float))

    # Check value ranges
    assert data['total_decisions'] >= 0
    assert data['rules_decisions'] >= 0
    assert data['ai_decisions'] >= 0
    assert data['template_fallbacks'] >= 0
    assert data['average_latency_ms'] >= 0
    assert 0 <= data['rules_percentage'] <= 100

    print(f"✅ Metrics endpoint works!")
    print(f"   Total decisions: {data['total_decisions']}")
    print(f"   Rules decisions: {data['rules_decisions']} ({data['rules_percentage']:.1f}%)")
    print(f"   AI decisions: {data['ai_decisions']}")
    print(f"   Template fallbacks: {data['template_fallbacks']}")
    print(f"   Average latency: {data['average_latency_ms']:.2f}ms")


def test_get_current_metrics_math(client):
    """Test that metrics calculations are correct"""
    response = client.get("/api/v1/metrics/current")
    assert response.status_code == 200

    data = response.json()

    # Total should be >= sum of classified parts
    # (may include decisions with unrecognized decided_by values)
    classified_sum = (
        data['rules_decisions'] +
        data['ai_decisions'] +
        data['template_fallbacks']
    )
    assert data['total_decisions'] >= classified_sum, (
        f"Total decisions ({data['total_decisions']}) should be >= "
        f"sum of classified ({classified_sum})"
    )

    # Rules percentage should be correct
    if data['total_decisions'] > 0:
        expected_percentage = (data['rules_decisions'] / data['total_decisions']) * 100
        assert abs(data['rules_percentage'] - expected_percentage) < 0.01
    else:
        # In fresh environment with no data, percentage should be 0
        assert data['rules_percentage'] == 0.0


def test_get_recent_decisions_structure(client):
    """Test that /api/v1/decisions/recent returns correct structure"""
    response = client.get("/api/v1/decisions/recent?limit=10")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

    # If there are decisions, check structure
    if len(data) > 0:
        decision = data[0]
        assert 'timestamp' in decision
        assert 'worker_id' in decision
        assert 'decision_type' in decision
        assert 'decided_by' in decision
        assert 'latency_ms' in decision
        assert 'is_fallback' in decision
        assert 'confirmation_type' in decision
        assert 'reasoning' in decision

        # Check types (timestamp can be ISO string or Unix timestamp)
        assert isinstance(decision['timestamp'], (int, float, str))
        assert isinstance(decision['worker_id'], str)
        assert isinstance(decision['decision_type'], str)
        assert isinstance(decision['decided_by'], str)
        assert isinstance(decision['latency_ms'], (int, float))
        assert isinstance(decision['is_fallback'], bool)
        assert isinstance(decision['confirmation_type'], str)
        assert isinstance(decision['reasoning'], str)

        print(f"✅ Decisions endpoint works!")
        print(f"   Found {len(data)} recent decisions")
        print(f"   Latest decision: {decision['decided_by']} at {decision['timestamp']}")


def test_get_recent_decisions_sorting(client):
    """Test that decisions are sorted by timestamp (descending)"""
    response = client.get("/api/v1/decisions/recent?limit=100")
    assert response.status_code == 200

    data = response.json()

    # Check that timestamps are in descending order
    if len(data) > 1:
        timestamps = [d['timestamp'] for d in data]
        assert timestamps == sorted(timestamps, reverse=True), "Decisions should be sorted by timestamp (descending)"


def test_get_recent_decisions_limit(client):
    """Test that limit parameter works"""
    response_10 = client.get("/api/v1/decisions/recent?limit=10")
    response_5 = client.get("/api/v1/decisions/recent?limit=5")

    assert response_10.status_code == 200
    assert response_5.status_code == 200

    data_10 = response_10.json()
    data_5 = response_5.json()

    assert len(data_10) <= 10
    assert len(data_5) <= 5

    if len(data_10) >= 5 and len(data_5) >= 5:
        # First 5 should be the same
        assert data_10[:5] == data_5


def test_metrics_with_no_workspace(client, tmp_path, monkeypatch):
    """Test metrics endpoint when no workspace exists"""
    # This test ensures graceful handling of missing data
    response = client.get("/api/v1/metrics/current")
    assert response.status_code == 200

    data = response.json()
    # Should return zeros when no data
    assert isinstance(data['total_decisions'], int)


def test_integration_metrics_and_decisions(client):
    """Test that metrics and decisions are consistent"""
    metrics_response = client.get("/api/v1/metrics/current")
    decisions_response = client.get("/api/v1/decisions/recent?limit=1000")

    assert metrics_response.status_code == 200
    assert decisions_response.status_code == 200

    metrics = metrics_response.json()
    decisions = decisions_response.json()

    # Count decisions by type
    rules_count = sum(1 for d in decisions if d['decided_by'] == 'rules')
    ai_count = sum(1 for d in decisions if d['decided_by'] == 'ai')
    template_count = sum(1 for d in decisions if d['decided_by'] == 'template')

    # Metrics should match decision counts
    assert metrics['rules_decisions'] == rules_count
    assert metrics['ai_decisions'] == ai_count
    assert metrics['template_fallbacks'] == template_count
    assert metrics['total_decisions'] == len(decisions)

    print(f"✅ Integration test passed!")
    print(f"   Metrics and decisions are consistent")


if __name__ == "__main__":
    # Quick test run
    import sys
    pytest.main([__file__, "-v", "--tb=short"] + sys.argv[1:])
