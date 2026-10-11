"""
Unit test for dynamic parameter responsiveness using Flask test client.
"""

import pytest
from backend.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_parameter_sensitivity(client):
    """
    Verifies that altering support, confidence, and lift thresholds
    dynamically and monotonically affects itemset and rule counts.
    """
    # 1. Baseline run on toy dataset
    res_base = client.post('/api/run-analysis', json={
        'preset': 'toy_5',
        'algorithm': 'fpgrowth',
        'min_support': 0.40,
        'min_confidence': 0.50,
        'min_lift': 1.00
    })
    assert res_base.status_code == 200
    data_base = res_base.get_json()
    base_itemsets = data_base['frequent_itemsets']['total_count']
    base_rules = data_base['association_rules']['total_count']

    # 2. Increase support -> itemsets must decrease or stay equal
    res_sup = client.post('/api/run-analysis', json={
        'preset': 'toy_5',
        'algorithm': 'fpgrowth',
        'min_support': 0.60,
        'min_confidence': 0.50,
        'min_lift': 1.00
    })
    assert res_sup.status_code == 200
    sup_itemsets = res_sup.get_json()['frequent_itemsets']['total_count']
    assert sup_itemsets < base_itemsets

    # 3. Increase confidence -> rules must decrease or stay equal
    res_conf = client.post('/api/run-analysis', json={
        'preset': 'toy_5',
        'algorithm': 'fpgrowth',
        'min_support': 0.40,
        'min_confidence': 0.80,
        'min_lift': 1.00
    })
    assert res_conf.status_code == 200
    conf_rules = res_conf.get_json()['association_rules']['total_count']
    assert conf_rules < base_rules

    # 4. Increase lift -> rules must decrease or stay equal
    res_lift = client.post('/api/run-analysis', json={
        'preset': 'toy_5',
        'algorithm': 'fpgrowth',
        'min_support': 0.40,
        'min_confidence': 0.50,
        'min_lift': 1.30
    })
    assert res_lift.status_code == 200
    lift_rules = res_lift.get_json()['association_rules']['total_count']
    assert lift_rules < base_rules
