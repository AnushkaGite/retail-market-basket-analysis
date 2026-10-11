"""
Benchmark script mining association rules on the prepared retail sample.
"""

import json
from backend.algorithms.fp_growth import run_fpgrowth
from backend.algorithms.association_rules import generate_rules


def main():
    sample_path = 'backend/data/samples/retail_sample_5k.json'
    print(f"Loading prepared sample from: {sample_path}")
    with open(sample_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    baskets = data['baskets']
    print(f"Total baskets: {len(baskets):,}")

    min_sup = 0.02   # 2%
    min_conf = 0.50  # 50%
    min_lift = 1.20  # Lift > 1.2

    print(f"Mining frequent itemsets with FP-Growth (min_support = {min_sup})...")
    fp_res = run_fpgrowth(baskets, min_support=min_sup)
    print(f"  Frequent itemsets discovered: {fp_res['itemset_count']:,} in {fp_res['execution_time_seconds']}s")

    print(f"\nGenerating association rules (min_confidence = {min_conf}, min_lift = {min_lift})...")
    rule_res = generate_rules(fp_res['frequent_itemsets'], min_confidence=min_conf, min_lift=min_lift)
    print(f"  Rules generated: {rule_res['rule_count']:,} in {rule_res['execution_time_seconds']}s")

    print("\n" + "=" * 80)
    print(f"Top 10 Association Rules Discovered (by Lift):")
    print("=" * 80)
    for idx, r in enumerate(rule_res['rules'][:10], 1):
        ante = ", ".join(r['antecedent'])
        cons = ", ".join(r['consequent'])
        print(f"Rule #{idx:2d}: [{ante}]  ==>  [{cons}]")
        print(f"         Support: {r['support']*100:.2f}% | Confidence: {r['confidence_percent']:.2f}% | Lift: {r['lift']:.3f} | Count: {r['support_count']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
