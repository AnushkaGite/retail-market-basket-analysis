"""
Basket builder utility to process the Online Retail II CSV in chunks/streams
and produce configurable staged sample datasets.
"""

import csv
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from backend.preprocessing.cleaner import build_baskets_from_iterable


def load_baskets_from_csv(
    csv_path: str,
    max_rows: Optional[int] = None,
    min_items: int = 2,
    max_baskets: Optional[int] = None
) -> Tuple[List[List[str]], Dict[str, Any]]:
    """
    Streams CSV without reading entire file into a giant DataFrame,
    cleaning rows and assembling baskets.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found at: {csv_path}")

    def row_generator():
        with open(csv_path, mode='r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader)
            count = 0
            for r in reader:
                yield r
                count += 1
                if max_rows and count >= max_rows:
                    break

    baskets, stats = build_baskets_from_iterable(
        row_generator(),
        min_items=min_items,
        max_baskets=max_baskets
    )
    return baskets, stats


def save_baskets_to_json(baskets: List[List[str]], output_path: str, metadata: Optional[Dict[str, Any]] = None):
    """Saves baskets and optional metadata to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    payload = {
        'metadata': metadata or {},
        'basket_count': len(baskets),
        'baskets': baskets
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


def load_baskets_from_json(json_path: str) -> Tuple[List[List[str]], Dict[str, Any]]:
    """Loads baskets and metadata from a pre-saved JSON file."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Basket JSON not found: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('baskets', []), data.get('metadata', {})
