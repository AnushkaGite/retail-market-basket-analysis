"""
CLI script to run preprocessing and generate staged sample datasets.

Usage:
  python -m backend.preprocessing.run_preprocessing --rows 50000 --min-items 2 --max-baskets 5000
"""

import argparse
import os
import sys
import time
from backend.preprocessing.basket_builder import load_baskets_from_csv, save_baskets_to_json


def main():
    parser = argparse.ArgumentParser(description="Preprocess Online Retail II dataset into market baskets.")
    parser.add_argument("--csv", default="online_retail_II.csv", help="Path to raw CSV dataset")
    parser.add_argument("--rows", type=int, default=None, help="Max source rows to process (default: all)")
    parser.add_argument("--min-items", type=int, default=2, help="Minimum items required per basket (default: 2)")
    parser.add_argument("--max-baskets", type=int, default=None, help="Max baskets to retain (default: all)")
    parser.add_argument("--output", default="backend/data/samples/retail_sample.json", help="Path to save processed JSON")

    args = parser.parse_args()

    print("=" * 60)
    print("Online Retail II - Market Basket Preprocessing")
    print(f"Source CSV:       {args.csv}")
    print(f"Row Limit:        {args.rows if args.rows else 'Full Dataset (~1.06M rows)'}")
    print(f"Min Items/Basket: {args.min_items}")
    print(f"Max Baskets:      {args.max_baskets if args.max_baskets else 'Unlimited'}")
    print(f"Output Target:    {args.output}")
    print("=" * 60)

    start_time = time.time()
    baskets, stats = load_baskets_from_csv(
        csv_path=args.csv,
        max_rows=args.rows,
        min_items=args.min_items,
        max_baskets=args.max_baskets
    )
    elapsed = time.time() - start_time

    print("\n--- Preprocessing Results ---")
    print(f"Total Source Rows Read:   {stats['total_source_rows']:,}")
    print(f"Cleaned Valid Rows:       {stats['cleaned_rows']:,}")
    print(f"Unique Invoices (Raw):    {stats['unique_invoices_raw']:,}")
    print(f"Unique Products Mapped:   {stats['unique_products']:,}")
    print(f"Retained Baskets (>= {args.min_items}): {stats['retained_baskets_count']:,}")
    print(f"Elapsed Time:             {elapsed:.2f} seconds")

    save_baskets_to_json(baskets, args.output, metadata=stats)
    print(f"Saved baskets to:         {args.output}")

    if baskets:
        print("\nSample Basket Preview:")
        for idx, b in enumerate(baskets[:3]):
            print(f"  Basket {idx + 1} ({len(b)} items): {b[:4]}...")


if __name__ == "__main__":
    main()
