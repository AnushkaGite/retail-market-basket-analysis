import pytest
import json
import os
from backend.algorithms.apriori import run_apriori
from backend.algorithms.fp_growth import run_fpgrowth
from backend.algorithms.association_rules import generate_rules, normalize_confidence_and_lift


def load_toy_dataset():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'samples', 'toy_baskets.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['baskets']


def test_normalize_confidence_and_lift():
    # Fractional
    conf, lift = normalize_confidence_and_lift(0.5, 1.2)
    assert conf == 0.5
    assert lift == 1.2

    # Percentage confidence
    conf, lift = normalize_confidence_and_lift(75, 2.0)
    assert conf == 0.75
    assert lift == 2.0

    # Invalid confidence
    with pytest.raises(ValueError):
        normalize_confidence_and_lift(0.0, 1.0)
    with pytest.raises(ValueError):
        normalize_confidence_and_lift(-0.2, 1.0)
    with pytest.raises(ValueError):
        normalize_confidence_and_lift(105, 1.0)

    # Invalid lift
    with pytest.raises(ValueError):
        normalize_confidence_and_lift(0.5, -1.0)


def test_association_rules_toy_dataset_manual_verification():
    """
    Toy dataset: 5 transactions:
    T1: Bread, Milk
    T2: Bread, Diaper, Beer, Eggs
    T3: Milk, Diaper, Beer, Cola
    T4: Bread, Milk, Diaper, Beer
    T5: Bread, Milk, Diaper, Cola
    
    Frequent itemsets at min_support = 0.6:
    - 1-itemsets:
      Bread: 4/5 = 0.8
      Diaper: 4/5 = 0.8
      Milk: 4/5 = 0.8
      Beer: 3/5 = 0.6
    - 2-itemsets:
      {Bread, Milk}: 3/5 = 0.6
      {Bread, Diaper}: 3/5 = 0.6
      {Diaper, Milk}: 3/5 = 0.6
      {Beer, Diaper}: 3/5 = 0.6
      
    Rule evaluation at min_confidence = 0.7 (70%), min_lift = 1.0:
    1. {Beer} -> {Diaper}:
       support = 0.6
       confidence = support({Beer, Diaper}) / support({Beer}) = 0.6 / 0.6 = 1.0 (100%)
       lift = confidence / support({Diaper}) = 1.0 / 0.8 = 1.25
       -> Meets thresholds!
    2. {Diaper} -> {Beer}:
       confidence = 0.6 / 0.8 = 0.75 (75%)
       lift = 0.75 / 0.6 = 1.25
       -> Meets thresholds!
    3. {Bread} -> {Milk}:
       confidence = 0.6 / 0.8 = 0.75 (75%)
       lift = 0.75 / 0.8 = 0.9375 (< 1.0) -> Pruned by min_lift=1.0!
    4. {Milk} -> {Bread}:
       confidence = 0.6 / 0.8 = 0.75 (75%)
       lift = 0.75 / 0.8 = 0.9375 (< 1.0) -> Pruned!
    5. {Bread} -> {Diaper}:
       confidence = 0.6 / 0.8 = 0.75, lift = 0.9375 -> Pruned!
    6. {Diaper} -> {Bread}:
       confidence = 0.75, lift = 0.9375 -> Pruned!
    7. {Milk} -> {Diaper}:
       confidence = 0.75, lift = 0.9375 -> Pruned!
    8. {Diaper} -> {Milk}:
       confidence = 0.75, lift = 0.9375 -> Pruned!
       
    Therefore, with min_confidence=0.7 and min_lift=1.0, EXACTLY 2 rules should be retained:
    - {Beer} -> {Diaper} (conf: 1.0, lift: 1.25)
    - {Diaper} -> {Beer} (conf: 0.75, lift: 1.25)
    """
    baskets = load_toy_dataset()
    frequent_itemsets = run_apriori(baskets, min_support=0.6)['frequent_itemsets']

    res = generate_rules(frequent_itemsets, min_confidence=0.7, min_lift=1.0)

    assert res['rule_count'] == 2
    rule1 = res['rules'][0]
    rule2 = res['rules'][1]

    # Verify rule1: Beer -> Diaper
    assert rule1['antecedent'] == ['Beer']
    assert rule1['consequent'] == ['Diaper']
    assert rule1['support'] == 0.6
    assert rule1['confidence'] == 1.0
    assert rule1['lift'] == 1.25

    # Verify rule2: Diaper -> Beer
    assert rule2['antecedent'] == ['Diaper']
    assert rule2['consequent'] == ['Beer']
    assert rule2['support'] == 0.6
    assert rule2['confidence'] == 0.75
    assert rule2['lift'] == 1.25


def test_rules_from_apriori_and_fpgrowth_agree():
    """
    Ensures that rules generated from Apriori itemsets and FP-Growth itemsets
    are exactly identical when evaluated on identical transactions.
    """
    baskets = load_toy_dataset()

    apriori_itemsets = run_apriori(baskets, min_support=0.4)['frequent_itemsets']
    fpgrowth_itemsets = run_fpgrowth(baskets, min_support=0.4)['frequent_itemsets']

    rules_apriori = generate_rules(apriori_itemsets, min_confidence=0.5, min_lift=1.0)
    rules_fpgrowth = generate_rules(fpgrowth_itemsets, min_confidence=0.5, min_lift=1.0)

    assert rules_apriori['rule_count'] == rules_fpgrowth['rule_count']
    assert len(rules_apriori['rules']) == len(rules_fpgrowth['rules'])

    # Verify item-by-item agreement
    for r_a, r_f in zip(rules_apriori['rules'], rules_fpgrowth['rules']):
        assert r_a['antecedent'] == r_f['antecedent']
        assert r_a['consequent'] == r_f['consequent']
        assert r_a['support'] == r_f['support']
        assert r_a['confidence'] == r_f['confidence']
        assert r_a['lift'] == r_f['lift']


def test_association_rules_edge_cases():
    # 1. Empty frequent itemsets
    res_empty = generate_rules([])
    assert res_empty['rule_count'] == 0
    assert res_empty['rules'] == []

    # 2. Only 1-itemsets (cannot form X -> Y)
    only_1_itemsets = [
        {"items": ["Bread"], "support": 0.8, "support_count": 4},
        {"items": ["Milk"], "support": 0.8, "support_count": 4}
    ]
    res_single = generate_rules(only_1_itemsets)
    assert res_single['rule_count'] == 0
    assert res_single['rules'] == []

    # 3. Confidence threshold too high (e.g. 1.05 or strictly unreachable)
    baskets = load_toy_dataset()
    frequent_itemsets = run_apriori(baskets, min_support=0.6)['frequent_itemsets']
    res_high_lift = generate_rules(frequent_itemsets, min_lift=10.0)
    assert res_high_lift['rule_count'] == 0
    assert res_high_lift['rules'] == []
