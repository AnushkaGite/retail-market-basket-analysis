"""
Benchmark script comparing custom Apriori vs custom FP-Growth on the prepared retail sample.
"""

import json
import time
from backend.algorithms.apriori import run_apriori
from backend.algorithms.fp_growth import run_fpgrowth


def main():
    sample_path = 'backend/data/samples/retail_sample_5k.json'
    print(f"Loading prepared sample from: {sample_path}")
    with open(sample_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    baskets = data['baskets']
    total_baskets = len(baskets)
    threshold = 0.02  # 2%

    print(f"Total baskets:           {total_baskets:,}")
    print(f"Minimum support:         {threshold} (2.0%)")
    print(f"Minimum count required:  35")
    print("=" * 65)

    # 1. Run custom Apriori
    print("Running custom Apriori...")
    res_apriori = run_apriori(baskets, min_support=threshold)
    print(f"  -> Apriori finished in {res_apriori['execution_time_seconds']} seconds.")
    print(f"  -> Frequent itemsets found: {res_apriori['itemset_count']:,}")

    # 2. Run custom FP-Growth
    print("\nRunning custom FP-Growth...")
    res_fpgrowth = run_fpgrowth(baskets, min_support=threshold)
    print(f"  -> FP-Growth finished in {res_fpgrowth['execution_time_seconds']} seconds.")
    print(f"  -> Frequent itemsets found: {res_fpgrowth['itemset_count']:,}")

    # 3. Verify exact agreement
    print("\n" + "=" * 65)
    print("Correctness Verification (Apriori vs FP-Growth):")
    apriori_map = {frozenset(x['items']): x['support_count'] for x in res_apriori['frequent_itemsets']}
    fpgrowth_map = {frozenset(x['items']): x['support_count'] for x in res_fpgrowth['frequent_itemsets']}

    match_sets = (set(apriori_map.keys()) == set(fpgrowth_map.keys()))
    match_counts = all(apriori_map[k] == fpgrowth_map[k] for k in apriori_map)

    print(f"  Itemsets exactly identical:    {match_sets}")
    print(f"  Support counts match for all:  {match_counts}")
    speedup = res_apriori['execution_time_seconds'] / max(res_fpgrowth['execution_time_seconds'], 0.0001)
    print(f"  FP-Growth speedup factor:      {speedup:.2f}x faster")
    print("=" * 65)


if __name__ == "__main__":
    main()
