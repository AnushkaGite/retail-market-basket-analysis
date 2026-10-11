"""
Pure Python Association Rule Mining Module.

Generates association rules of the form Antecedent (X) -> Consequent (Y)
from frequent itemsets discovered by Apriori or FP-Growth.

Metrics:
- Support(X -> Y) = Support(X U Y)
- Confidence(X -> Y) = Support(X U Y) / Support(X)
- Lift(X -> Y) = Confidence(X -> Y) / Support(Y) = Support(X U Y) / (Support(X) * Support(Y))
- Leverage(X -> Y) = Support(X U Y) - (Support(X) * Support(Y))
- Conviction(X -> Y) = (1 - Support(Y)) / (1 - Confidence(X -> Y)) if Confidence < 1 else infinity
"""

from typing import List, Set, Tuple, Dict, Any, Union, FrozenSet, Optional
from itertools import combinations
import time


def normalize_confidence_and_lift(
    min_confidence: Union[float, int],
    min_lift: Union[float, int]
) -> Tuple[float, float]:
    """
    Normalizes confidence and lift thresholds.
    
    Confidence:
    - If min_confidence > 1.0 (e.g., 50 or 80.0), it is treated as a percentage and divided by 100.0.
    - Must be in (0.0, 1.0].
    
    Lift:
    - Must be >= 0.0 (typically >= 1.0 for positive association).
    """
    if not isinstance(min_confidence, (int, float)):
        raise TypeError(f"min_confidence must be numeric, got {type(min_confidence).__name__}")
    if not isinstance(min_lift, (int, float)):
        raise TypeError(f"min_lift must be numeric, got {type(min_lift).__name__}")

    conf = float(min_confidence)
    if conf <= 0.0:
        raise ValueError(f"min_confidence must be strictly positive, got {min_confidence}")
    if conf > 1.0:
        if conf <= 100.0:
            conf = conf / 100.0
        else:
            raise ValueError(f"min_confidence percentage cannot exceed 100, got {min_confidence}")

    lift = float(min_lift)
    if lift < 0.0:
        raise ValueError(f"min_lift cannot be negative, got {min_lift}")

    return conf, lift


def generate_rules(
    frequent_itemsets: List[Dict[str, Any]],
    min_confidence: Union[float, int] = 0.5,
    min_lift: Union[float, int] = 1.0,
    total_baskets: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generates association rules from frequent itemsets.
    
    Args:
        frequent_itemsets: List of frequent itemset dictionaries containing 'items', 'support', 'support_count'.
                           Directly compatible with output of run_apriori and run_fpgrowth.
        min_confidence: Minimum confidence threshold (fraction in (0, 1] or percentage in (1, 100]).
        min_lift: Minimum lift threshold (float >= 0.0).
        total_baskets: Optional total transaction count.
        
    Returns:
        Structured dictionary suitable for JSON serialization and API / UI consumption:
        {
            "rule_count": int,
            "min_confidence": float,
            "min_confidence_percent": float,
            "min_lift": float,
            "rules": [
                {
                    "antecedent": ["Bread"],
                    "consequent": ["Milk"],
                    "support": 0.6,
                    "confidence": 0.75,
                    "lift": 1.25,
                    "support_count": 3
                },
                ...
            ]
        }
    """
    start_time = time.time()
    norm_conf, norm_lift = normalize_confidence_and_lift(min_confidence, min_lift)

    if not frequent_itemsets:
        return {
            "rule_count": 0,
            "min_confidence": norm_conf,
            "min_confidence_percent": round(norm_conf * 100.0, 4),
            "min_lift": norm_lift,
            "execution_time_seconds": round(time.time() - start_time, 4),
            "rules": []
        }

    # Map itemset frozenset -> (support, support_count)
    support_map: Dict[FrozenSet[str], float] = {}
    count_map: Dict[FrozenSet[str], int] = {}
    
    for itemset_info in frequent_itemsets:
        fset = frozenset(itemset_info['items'])
        support_map[fset] = itemset_info['support']
        count_map[fset] = itemset_info.get('support_count', 0)

    rules = []

    # For each frequent itemset of size >= 2, generate all non-empty antecedent -> consequent splits
    for fset, itemset_support in support_map.items():
        k = len(fset)
        if k < 2:
            continue

        item_list = list(fset)

        # Generate non-empty antecedent X of size 1 to k-1
        for ante_size in range(1, k):
            for ante_combo in combinations(item_list, ante_size):
                ante = frozenset(ante_combo)
                cons = fset - ante

                if not cons:
                    continue

                ante_support = support_map.get(ante)
                cons_support = support_map.get(cons)

                # Skip if support of antecedent or consequent is missing or non-positive
                if ante_support is None or ante_support <= 0.0 or cons_support is None or cons_support <= 0.0:
                    continue

                # Compute Confidence
                confidence = itemset_support / ante_support

                if confidence < norm_conf:
                    continue

                # Compute Lift
                lift = confidence / cons_support

                if lift < norm_lift:
                    continue

                rules.append({
                    "antecedent": sorted(list(ante)),
                    "consequent": sorted(list(cons)),
                    "antecedent_support": round(ante_support, 6),
                    "consequent_support": round(cons_support, 6),
                    "support": round(itemset_support, 6),
                    "support_count": count_map.get(fset, 0),
                    "confidence": round(confidence, 6),
                    "confidence_percent": round(confidence * 100.0, 4),
                    "lift": round(lift, 6)
                })

    # Sort rules descending by lift, then confidence, then support
    rules.sort(key=lambda r: (-r["lift"], -r["confidence"], -r["support"], r["antecedent"], r["consequent"]))

    elapsed = time.time() - start_time

    return {
        "rule_count": len(rules),
        "min_confidence": norm_conf,
        "min_confidence_percent": round(norm_conf * 100.0, 4),
        "min_lift": norm_lift,
        "execution_time_seconds": round(elapsed, 4),
        "rules": rules
    }
