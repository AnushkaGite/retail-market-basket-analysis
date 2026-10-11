"""
Pure Python Apriori Algorithm for Frequent Itemset Mining.

Time and Memory Considerations:
- Time Complexity:
  O(2^|I|) worst-case where |I| is the number of distinct items.
  In practice, the Apriori property (all non-empty subsets of a frequent itemset must also be frequent)
  prunes the search space dramatically.
  Candidate generation of size k joins L_{k-1} with L_{k-1} on the first k-2 items (F_k-1 x F_k-1 method),
  and prunes any candidate having an infrequent (k-1)-subset.
  Support counting performs multiple full scans over the dataset (one per level k). To optimize this,
  transactions are converted to Python sets (or frozensets) so subset checks are O(k) hashing operations.
- Memory Complexity:
  O(|C_k| + |L_k|) per level k. At intermediate levels (typically k=2 or k=3 with low min_support),
  the number of candidate itemsets can peak before shrinking.
  Storing transactions as a list of sets in memory is proportional to total item occurrences in baskets.
"""

from typing import List, Set, Tuple, Dict, Any, Union, FrozenSet
from itertools import combinations
import time


def normalize_min_support(min_support: Union[float, int]) -> float:
    """
    Normalizes min_support to a fractional float in the range (0.0, 1.0].
    
    Representation Convention:
    - If min_support > 1.0 (e.g., 5 or 20.0), it is treated as a percentage and divided by 100.0 (e.g., 0.05 or 0.20).
    - If min_support is in (0.0, 1.0], it is treated directly as a fraction.
    - If min_support <= 0 or > 100, a ValueError is raised.
    """
    if not isinstance(min_support, (int, float)):
        raise TypeError(f"min_support must be numeric, got {type(min_support).__name__}")

    s = float(min_support)
    if s <= 0.0:
        raise ValueError(f"min_support must be strictly positive, got {min_support}")
    if s > 1.0:
        if s <= 100.0:
            s = s / 100.0
        else:
            raise ValueError(f"min_support percentage cannot exceed 100, got {min_support}")

    return s


def generate_c1(baskets: List[Set[str]]) -> Set[FrozenSet[str]]:
    """Generates candidate 1-itemsets (C_1)."""
    c1 = set()
    for basket in baskets:
        for item in basket:
            c1.add(frozenset([item]))
    return c1


def filter_candidates(
    baskets: List[Set[str]],
    candidates: Set[FrozenSet[str]],
    min_count: int,
    total_baskets: int
) -> Tuple[Dict[FrozenSet[str], int], Dict[FrozenSet[str], float]]:
    """
    Counts frequency of candidate itemsets across all transaction baskets
    and filters those meeting the minimum support count.
    
    Returns:
        (frequent_itemset_counts, frequent_itemset_supports)
    """
    counts: Dict[FrozenSet[str], int] = {c: 0 for c in candidates}
    
    for basket in baskets:
        for c in candidates:
            if c.issubset(basket):
                counts[c] += 1

    frequent_counts = {}
    frequent_supports = {}
    for c, count in counts.items():
        if count >= min_count:
            frequent_counts[c] = count
            frequent_supports[c] = count / total_baskets if total_baskets > 0 else 0.0

    return frequent_counts, frequent_supports


def generate_ck(
    prev_frequent_itemsets: List[FrozenSet[str]],
    k: int
) -> Set[FrozenSet[str]]:
    """
    Generates candidate k-itemsets (C_k) by joining L_{k-1} with itself,
    and prunes candidates containing any infrequent (k-1)-subset (Apriori Property).
    
    Join Step:
    Sort items in each itemset. Two itemsets l1 and l2 are joinable if their first
    k-2 items are identical and l1[-1] < l2[-1].
    
    Prune Step:
    For every candidate of size k, verify that all k subsets of size k-1 are present in prev_frequent_itemsets.
    """
    candidates = set()
    prev_set = set(prev_frequent_itemsets)
    sorted_itemsets = [sorted(list(itemset)) for itemset in prev_frequent_itemsets]
    n = len(sorted_itemsets)

    for i in range(n):
        for j in range(i + 1, n):
            l1 = sorted_itemsets[i]
            l2 = sorted_itemsets[j]

            # Join condition: first k-2 items match
            if l1[:k - 2] == l2[:k - 2]:
                new_candidate = frozenset(l1).union(frozenset(l2))
                if len(new_candidate) == k:
                    # Prune step: check all (k-1) subsets
                    is_valid = True
                    for sub in combinations(new_candidate, k - 1):
                        if frozenset(sub) not in prev_set:
                            is_valid = False
                            break
                    if is_valid:
                        candidates.add(new_candidate)
            else:
                # Since itemsets are sorted, we can't necessarily break early unless sorted globally,
                # but with n moderately small per level, standard pair iteration is fast.
                pass

    return candidates


def run_apriori(
    baskets: List[List[str]],
    min_support: Union[float, int],
    max_k: int = 10
) -> Dict[str, Any]:
    """
    Runs the Apriori algorithm on a list of transaction baskets.
    
    Args:
        baskets: List of transaction baskets (each basket is a list of item name strings).
        min_support: Minimum support threshold (float in (0, 1] or percentage in (1, 100]).
        max_k: Maximum itemset size to explore (default 10).
        
    Returns:
        Structured dictionary suitable for JSON serialization and API / UI consumption:
        {
            "algorithm": "Apriori",
            "total_baskets": int,
            "min_support_fraction": float,
            "min_support_percent": float,
            "min_support_count": int,
            "itemset_count": int,
            "execution_time_seconds": float,
            "frequent_itemsets": [
                {
                    "items": ["BREAD", "MILK"],
                    "size": 2,
                    "support_count": 3,
                    "support": 0.6,
                    "support_percent": 60.0
                },
                ...
            ]
        }
    """
    start_time = time.time()
    normalized_support = normalize_min_support(min_support)

    total_baskets = len(baskets)
    if total_baskets == 0:
        return {
            "algorithm": "Apriori",
            "total_baskets": 0,
            "min_support_fraction": normalized_support,
            "min_support_percent": round(normalized_support * 100.0, 4),
            "min_support_count": 0,
            "itemset_count": 0,
            "execution_time_seconds": round(time.time() - start_time, 4),
            "frequent_itemsets": []
        }

    # Pre-convert each basket into a set for fast subset checking
    basket_sets = [set(b) for b in baskets if len(b) > 0]
    effective_baskets_count = len(basket_sets)

    import math
    # min_count: ceiling of total_baskets * normalized_support
    min_count = math.ceil(total_baskets * normalized_support)

    all_frequent_counts: Dict[FrozenSet[str], int] = {}
    all_frequent_supports: Dict[FrozenSet[str], float] = {}

    # Step 1: Generate C_1 and L_1
    c1 = generate_c1(basket_sets)
    l1_counts, l1_supports = filter_candidates(basket_sets, c1, min_count, total_baskets)
    all_frequent_counts.update(l1_counts)
    all_frequent_supports.update(l1_supports)

    current_lk = list(l1_counts.keys())
    k = 2

    # Step 2: Iteratively generate C_k and L_k
    while current_lk and k <= max_k:
        ck = generate_ck(current_lk, k)
        if not ck:
            break

        lk_counts, lk_supports = filter_candidates(basket_sets, ck, min_count, total_baskets)
        if not lk_counts:
            break

        all_frequent_counts.update(lk_counts)
        all_frequent_supports.update(lk_supports)
        current_lk = list(lk_counts.keys())
        k += 1

    # Format structured output
    formatted_itemsets = []
    for itemset, count in all_frequent_counts.items():
        sup = all_frequent_supports[itemset]
        sorted_items = sorted(list(itemset))
        formatted_itemsets.append({
            "items": sorted_items,
            "size": len(sorted_items),
            "support_count": count,
            "support": round(sup, 6),
            "support_percent": round(sup * 100.0, 4)
        })

    # Sort descending by support, then by size, then alphabetically
    formatted_itemsets.sort(key=lambda x: (-x["support"], -x["size"], x["items"]))

    elapsed = time.time() - start_time

    return {
        "algorithm": "Apriori",
        "total_baskets": total_baskets,
        "min_support_fraction": normalized_support,
        "min_support_percent": round(normalized_support * 100.0, 4),
        "min_support_count": min_count,
        "itemset_count": len(formatted_itemsets),
        "execution_time_seconds": round(elapsed, 4),
        "frequent_itemsets": formatted_itemsets
    }
