"""
Benchmark script to run Apriori on the prepared retail sample dataset.
"""

import json
import time
from backend.algorithms.apriori import run_apriori


def main():
    sample_path = 'backend/data/samples/retail_sample_5k.json'
    print(f"Loading prepared sample from: {sample_path}")
    with open(sample_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    baskets = data['baskets']
    total_baskets = len(baskets)
    print(f"Total baskets loaded: {total_baskets:,}")

    threshold = 0.02
    print(f"\nExecuting Apriori with min_support = {threshold} (2.0%)...")
    res = run_apriori(baskets, min_support=threshold)

    print("\n" + "=" * 60)
    print("Apriori Benchmark Results")
    print("=" * 60)
    print(f"Algorithm:               {res['algorithm']}")
    print(f"Baskets Analyzed:        {res['total_baskets']:,}")
    print(f"Min Support Fraction:    {res['min_support_fraction']}")
    print(f"Min Support Percentage:  {res['min_support_percent']}%")
    print(f"Min Support Count:       {res['min_support_count']}")
    print(f"Frequent Itemsets Found: {res['itemset_count']:,}")
    print(f"Execution Time:          {res['execution_time_seconds']} seconds")

    print("\nTop 10 Frequent Itemsets:")
    for idx, item in enumerate(res['frequent_itemsets'][:10], 1):
        items_str = ", ".join(item['items'])
        print(f"  {idx:2d}. [{items_str}]")
        print(f"      Size: {item['size']}, Count: {item['support_count']}, Support: {item['support_percent']}%")


if __name__ == "__main__":
    main()
