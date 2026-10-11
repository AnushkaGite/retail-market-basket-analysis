import pytest
import json
from backend.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_api_dataset_info(client):
    response = client.get('/api/dataset-info')
    assert response.status_code == 200
    data = response.get_json()

    assert data['status'] == 'success'
    assert 'Online Retail II' in data['dataset_name']
    assert data['total_raw_rows'] == 1067371
    assert isinstance(data['presets'], list)
    assert len(data['presets']) >= 3

    # Check preset keys
    preset_ids = [p['id'] for p in data['presets']]
    assert 'toy_5' in preset_ids
    assert 'sample_1.7k' in preset_ids


def test_api_run_analysis_toy_preset_apriori(client):
    payload = {
        "preset": "toy_5",
        "algorithm": "apriori",
        "min_support": 0.60,
        "min_confidence": 0.70,
        "min_lift": 1.0
    }
    response = client.post('/api/run-analysis', json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data['status'] == 'success'
    assert data['parameters']['baskets_analyzed'] == 5
    assert data['frequent_itemsets']['total_count'] == 8
    assert data['association_rules']['total_count'] == 2

    # Verify actual computed rules
    rules = data['association_rules']['rules']
    rule_pairs = [(r['antecedent'], r['consequent']) for r in rules]
    assert (['Beer'], ['Diaper']) in rule_pairs
    assert (['Diaper'], ['Beer']) in rule_pairs


def test_api_run_analysis_toy_preset_fpgrowth(client):
    payload = {
        "preset": "toy_5",
        "algorithm": "fpgrowth",
        "min_support": 0.60,
        "min_confidence": 0.70,
        "min_lift": 1.0
    }
    response = client.post('/api/run-analysis', json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data['status'] == 'success'
    assert data['frequent_itemsets']['total_count'] == 8
    assert data['association_rules']['total_count'] == 2


def test_api_run_analysis_compare_mode(client):
    payload = {
        "preset": "toy_5",
        "algorithm": "compare",
        "min_support": 0.40,
        "min_confidence": 0.50,
        "min_lift": 1.0
    }
    response = client.post('/api/run-analysis', json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data['status'] == 'success'
    assert data['benchmark']['itemsets_match'] is True
    assert data['benchmark']['apriori_time_seconds'] is not None
    assert data['benchmark']['fpgrowth_time_seconds'] is not None
    assert data['benchmark']['speedup_factor'] is not None


def test_api_run_analysis_compare_mode_mismatch_detection(monkeypatch, client):
    """
    Verifies that compare mode correctly detects differences in actual itemsets or
    support counts, even when the overall itemset count is identical.
    """
    import backend.app as app_module

    # Scenario A: Equal count, but different itemsets
    def fake_run_fpgrowth_different_itemsets(baskets, min_support):
        real_res = app_module.run_apriori(baskets, min_support=min_support)
        modified_itemsets = [dict(x) for x in real_res["frequent_itemsets"]]
        if modified_itemsets:
            # Change items of the first itemset while keeping count unchanged
            modified_itemsets[0]["items"] = ["FAKE_ITEM_DIFFERENT"]
        return {
            **real_res,
            "algorithm": "FP-Growth",
            "frequent_itemsets": modified_itemsets
        }

    monkeypatch.setattr(app_module, "run_fpgrowth", fake_run_fpgrowth_different_itemsets)
    res = client.post('/api/run-analysis', json={
        "preset": "toy_5",
        "algorithm": "compare",
        "min_support": 0.40,
        "min_confidence": 0.50,
        "min_lift": 1.0
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['benchmark']['itemsets_match'] is False

    # Scenario B: Same itemsets, but different support count
    def fake_run_fpgrowth_different_counts(baskets, min_support):
        real_res = app_module.run_apriori(baskets, min_support=min_support)
        modified_itemsets = [dict(x) for x in real_res["frequent_itemsets"]]
        if modified_itemsets:
            modified_itemsets[0]["support_count"] = modified_itemsets[0]["support_count"] + 999
        return {
            **real_res,
            "algorithm": "FP-Growth",
            "frequent_itemsets": modified_itemsets
        }

    monkeypatch.setattr(app_module, "run_fpgrowth", fake_run_fpgrowth_different_counts)
    res_b = client.post('/api/run-analysis', json={
        "preset": "toy_5",
        "algorithm": "compare",
        "min_support": 0.40,
        "min_confidence": 0.50,
        "min_lift": 1.0
    })
    assert res_b.status_code == 200
    data_b = res_b.get_json()
    assert data_b['benchmark']['itemsets_match'] is False


def test_api_run_analysis_invalid_parameters(client):
    # 1. Invalid algorithm
    res_algo = client.post('/api/run-analysis', json={"algorithm": "invalid_algo"})
    assert res_algo.status_code == 400
    assert "Unsupported algorithm" in res_algo.get_json()['message']

    # 2. Negative support
    res_sup = client.post('/api/run-analysis', json={"min_support": -0.1})
    assert res_sup.status_code == 400
    assert "Invalid min_support" in res_sup.get_json()['message']

    # 3. Invalid confidence
    res_conf = client.post('/api/run-analysis', json={"min_confidence": 1.5})
    # Confidence > 1 and <= 100 is normalized as %, but > 100 raises error
    res_conf_bad = client.post('/api/run-analysis', json={"min_confidence": 150})
    assert res_conf_bad.status_code == 400
    assert "Invalid rule threshold" in res_conf_bad.get_json()['message']

    # 4. Unknown preset
    res_preset = client.post('/api/run-analysis', json={"preset": "nonexistent_preset"})
    assert res_preset.status_code == 404

    # 5. Non-JSON body
    res_empty = client.post('/api/run-analysis', data="not json")
    assert res_empty.status_code == 400


def test_api_run_analysis_empty_results(client):
    # Setting an unreachable threshold on toy dataset
    payload = {
        "preset": "toy_5",
        "algorithm": "fpgrowth",
        "min_support": 1.0,
        "min_confidence": 1.0,
        "min_lift": 10.0
    }
    response = client.post('/api/run-analysis', json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data['frequent_itemsets']['total_count'] == 0
    assert data['frequent_itemsets']['itemsets'] == []
    assert data['association_rules']['total_count'] == 0
    assert data['association_rules']['rules'] == []


def test_api_export_rules_csv(client):
    sample_rules = [
        {
            "antecedent": ["Bread"],
            "consequent": ["Milk"],
            "support": 0.6,
            "confidence": 0.75,
            "lift": 1.25,
            "support_count": 3
        }
    ]
    response = client.post('/api/export-rules', json={"rules": sample_rules})
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment; filename=market_basket_rules_" in response.headers.get("Content-Disposition", "")

    csv_text = response.data.decode("utf-8")
    assert "Bread" in csv_text
    assert "Milk" in csv_text
    assert "1.25" in csv_text
    assert "Antecedent (Customer Bought)" in csv_text
