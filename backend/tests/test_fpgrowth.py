import pytest
import json
import os
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth as mlx_fpgrowth
from backend.algorithms.apriori import run_apriori
from backend.algorithms.fp_growth import run_fpgrowth


def load_toy_dataset():
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'samples', 'toy_baskets.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['baskets']


def test_fpgrowth_toy_dataset_manual_verification():
    """
    Toy dataset: 5 transactions:
    T1: Bread, Milk
    T2: Bread, Diaper, Beer, Eggs
    T3: Milk, Diaper, Beer, Cola
    T4: Bread, Milk, Diaper, Beer
    T5: Bread, Milk, Diaper, Cola
    
    Total baskets = 5.
    min_support = 0.6 (min_count = 3):
    Expected frequent 1-itemsets:
    - Bread: 4 (80%)
    - Milk: 4 (80%)
    - Diaper: 4 (80%)
    - Beer: 3 (60%)
    
    Expected frequent 2-itemsets:
    - {Bread, Milk}: 3 (60%)
    - {Bread, Diaper}: 3 (60%)
    - {Diaper, Milk}: 3 (60%)
    - {Beer, Diaper}: 3 (60%)
    
    Total = 8 itemsets.
    """
    baskets = load_toy_dataset()
    res = run_fpgrowth(baskets, min_support=0.6)

    assert res['total_baskets'] == 5
    assert res['min_support_count'] == 3
    assert res['min_support_fraction'] == 0.6
    assert res['itemset_count'] == 8

    itemsets_dict = {tuple(x['items']): (x['support_count'], x['support']) for x in res['frequent_itemsets']}

    # 1-itemsets
    assert itemsets_dict[('Bread',)] == (4, 0.8)
    assert itemsets_dict[('Diaper',)] == (4, 0.8)
    assert itemsets_dict[('Milk',)] == (4, 0.8)
    assert itemsets_dict[('Beer',)] == (3, 0.6)

    # 2-itemsets
    assert itemsets_dict[('Bread', 'Milk')] == (3, 0.6)
    assert itemsets_dict[('Bread', 'Diaper')] == (3, 0.6)
    assert itemsets_dict[('Diaper', 'Milk')] == (3, 0.6)
    assert itemsets_dict[('Beer', 'Diaper')] == (3, 0.6)

    # Infrequent items must not be present
    assert ('Eggs',) not in itemsets_dict
    assert ('Cola',) not in itemsets_dict
    assert ('Beer', 'Bread') not in itemsets_dict


def test_fpgrowth_agrees_with_apriori_multiple_thresholds():
    """
    Assert that custom FP-Growth and custom Apriori produce EXACTLY identical
    frequent itemsets and support counts across multiple thresholds.
    """
    baskets = load_toy_dataset()

    for threshold in [0.2, 0.4, 0.6, 0.8]:
        apriori_res = run_apriori(baskets, min_support=threshold)
        fpgrowth_res = run_fpgrowth(baskets, min_support=threshold)

        assert apriori_res['itemset_count'] == fpgrowth_res['itemset_count']
        assert apriori_res['min_support_count'] == fpgrowth_res['min_support_count']

        apriori_map = {frozenset(x['items']): (x['support_count'], round(x['support'], 6)) for x in apriori_res['frequent_itemsets']}
        fpgrowth_map = {frozenset(x['items']): (x['support_count'], round(x['support'], 6)) for x in fpgrowth_res['frequent_itemsets']}

        assert set(apriori_map.keys()) == set(fpgrowth_map.keys())
        for itemset in apriori_map:
            assert apriori_map[itemset] == fpgrowth_map[itemset]


def test_fpgrowth_edge_cases():
    # 1. Empty transactions
    res_empty = run_fpgrowth([], min_support=0.2)
    assert res_empty['total_baskets'] == 0
    assert res_empty['itemset_count'] == 0
    assert res_empty['frequent_itemsets'] == []

    # 2. No frequent itemsets (min_support = 1.0 on diverse dataset)
    baskets = load_toy_dataset()
    res_high = run_fpgrowth(baskets, min_support=1.0)
    assert res_high['itemset_count'] == 0
    assert res_high['frequent_itemsets'] == []

    # 3. Repeated items in a basket (deduplication)
    repeated_baskets = [
        ["Bread", "Bread", "Milk"],
        ["Bread", "Milk", "Milk", "Milk"]
    ]
    res_rep = run_fpgrowth(repeated_baskets, min_support=0.5)
    # Both have Bread and Milk -> count is 2, not inflated
    rep_map = {tuple(x['items']): x['support_count'] for x in res_rep['frequent_itemsets']}
    assert rep_map[('Bread',)] == 2
    assert rep_map[('Milk',)] == 2
    assert rep_map[('Bread', 'Milk')] == 2

    # 4. Invalid thresholds
    with pytest.raises(ValueError):
        run_fpgrowth(baskets, min_support=-0.5)
    with pytest.raises(ValueError):
        run_fpgrowth(baskets, min_support=0.0)
    with pytest.raises(ValueError):
        run_fpgrowth(baskets, min_support=150)


def test_fpgrowth_validation_against_mlxtend():
    """
    Independent validation comparing our custom FP-Growth against mlxtend.frequent_patterns.fpgrowth.
    """
    baskets = load_toy_dataset()
    min_sup = 0.4  # min count = 2

    # Run custom FP-Growth
    custom_res = run_fpgrowth(baskets, min_support=min_sup)
    custom_map = {frozenset(x['items']): round(x['support'], 4) for x in custom_res['frequent_itemsets']}

    # Run mlxtend FP-Growth
    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    mlx_res = mlx_fpgrowth(df, min_support=min_sup, use_colnames=True)

    mlx_map = {frozenset(row['itemsets']): round(row['support'], 4) for _, row in mlx_res.iterrows()}

    # Check identical itemset sets and support values
    assert set(custom_map.keys()) == set(mlx_map.keys())
    for itemset, sup in custom_map.items():
        assert sup == mlx_map[itemset]
