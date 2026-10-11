import pytest
import json
import os
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori as mlx_apriori
from backend.algorithms.apriori import run_apriori, normalize_min_support


def load_toy_dataset():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'samples', 'toy_baskets.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['baskets']


def test_normalize_min_support():
    # Fractional
    assert normalize_min_support(0.05) == 0.05
    assert normalize_min_support(0.5) == 0.5
    assert normalize_min_support(1.0) == 1.0

    # Percentage
    assert normalize_min_support(5) == 0.05
    assert normalize_min_support(20.0) == 0.20
    assert normalize_min_support(60) == 0.60
    assert normalize_min_support(100.0) == 1.0

    # Invalid thresholds
    with pytest.raises(ValueError):
        normalize_min_support(0.0)
    with pytest.raises(ValueError):
        normalize_min_support(-0.1)
    with pytest.raises(ValueError):
        normalize_min_support(105)
    with pytest.raises(TypeError):
        normalize_min_support("invalid")


def test_apriori_toy_dataset_manual_verification():
    """
    Toy dataset: 5 transactions:
    T1: Bread, Milk
    T2: Bread, Diaper, Beer, Eggs
    T3: Milk, Diaper, Beer, Cola
    T4: Bread, Milk, Diaper, Beer
    T5: Bread, Milk, Diaper, Cola
    
    Total baskets = 5.
    min_support = 0.6 (min_count = 3):
    1-itemsets:
    - Bread: 4 (T1, T2, T4, T5) -> 0.8
    - Milk: 4 (T1, T3, T4, T5) -> 0.8
    - Diaper: 4 (T2, T3, T4, T5) -> 0.8
    - Beer: 3 (T2, T3, T4) -> 0.6
    (Eggs: 1, Cola: 2 are pruned)
    
    2-itemsets:
    - {Bread, Milk}: 3 (T1, T4, T5) -> 0.6
    - {Bread, Diaper}: 3 (T2, T4, T5) -> 0.6
    - {Bread, Beer}: 2 -> Pruned
    - {Milk, Diaper}: 3 (T3, T4, T5) -> 0.6
    - {Milk, Beer}: 2 -> Pruned
    - {Diaper, Beer}: 3 (T2, T3, T4) -> 0.6
    
    3-itemsets:
    - {Bread, Milk, Diaper}: 2 (T4, T5) -> Pruned (< 3)
    """
    baskets = load_toy_dataset()
    res = run_apriori(baskets, min_support=0.6)

    assert res['total_baskets'] == 5
    assert res['min_support_count'] == 3
    assert res['min_support_fraction'] == 0.6

    itemsets_dict = {tuple(x['items']): x['support_count'] for x in res['frequent_itemsets']}

    # Expected frequent 1-itemsets
    assert itemsets_dict[('Bread',)] == 4
    assert itemsets_dict[('Milk',)] == 4
    assert itemsets_dict[('Diaper',)] == 4
    assert itemsets_dict[('Beer',)] == 3

    # Expected frequent 2-itemsets
    assert itemsets_dict[('Bread', 'Milk')] == 3
    assert itemsets_dict[('Bread', 'Diaper')] == 3
    assert itemsets_dict[('Diaper', 'Milk')] == 3
    assert itemsets_dict[('Beer', 'Diaper')] == 3

    # Confirm pruned itemsets are not present
    assert ('Eggs',) not in itemsets_dict
    assert ('Cola',) not in itemsets_dict
    assert ('Beer', 'Bread') not in itemsets_dict
    assert ('Bread', 'Diaper', 'Milk') not in itemsets_dict

    assert res['itemset_count'] == 8


def test_apriori_edge_cases():
    # 1. Empty transactions list
    res_empty = run_apriori([], min_support=0.2)
    assert res_empty['total_baskets'] == 0
    assert res_empty['itemset_count'] == 0
    assert res_empty['frequent_itemsets'] == []

    # 2. Threshold producing no itemsets (min_support = 1.0 on diverse baskets)
    baskets = load_toy_dataset()
    res_high = run_apriori(baskets, min_support=1.0)
    # No single item appears in all 5 baskets
    assert res_high['itemset_count'] == 0
    assert res_high['frequent_itemsets'] == []

    # 3. All identical transactions
    identical_baskets = [["Apple", "Banana"], ["Apple", "Banana"], ["Apple", "Banana"]]
    res_identical = run_apriori(identical_baskets, min_support=1.0)
    assert res_identical['itemset_count'] == 3  # {Apple}, {Banana}, {Apple, Banana}
    assert res_identical['frequent_itemsets'][0]['support'] == 1.0


def test_apriori_validation_against_mlxtend():
    """
    Independent validation comparing our pure Python Apriori implementation
    against mlxtend.frequent_patterns.apriori.
    """
    baskets = load_toy_dataset()
    min_sup = 0.4  # min count = 2

    # Run custom Apriori
    custom_res = run_apriori(baskets, min_support=min_sup)
    custom_map = {frozenset(x['items']): round(x['support'], 4) for x in custom_res['frequent_itemsets']}

    # Run mlxtend Apriori
    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    mlx_res = mlx_apriori(df, min_support=min_sup, use_colnames=True)

    mlx_map = {frozenset(row['itemsets']): round(row['support'], 4) for _, row in mlx_res.iterrows()}

    # Check identical itemset sets and support values
    assert set(custom_map.keys()) == set(mlx_map.keys())
    for itemset, sup in custom_map.items():
        assert sup == mlx_map[itemset]
