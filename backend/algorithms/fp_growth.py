"""
Pure Python FP-Growth (Frequent Pattern Growth) Algorithm.

Key Characteristics:
- Compressed Representation: Encodes the transaction database into a compact Frequent Pattern Tree (FP-Tree).
- No Candidate Generation: Avoids generating combinatorial candidate sets C_k, unlike Apriori.
- Two Database Passes:
  1. Pass 1: Scan database to count item support, filter infrequent items, and determine global frequency order.
  2. Pass 2: Insert each transaction (filtered and sorted by descending support) into the FP-Tree with node links.
- Recursive Mining: Recursively mines conditional pattern bases and builds conditional FP-trees
  from bottom-up along the header table.
"""

from typing import List, Set, Tuple, Dict, Any, Union, Optional
from collections import defaultdict
import math
import time
from backend.algorithms.apriori import normalize_min_support


class FPNode:
    """Node representation in the FP-Tree."""
    __slots__ = ('item', 'count', 'parent', 'children', 'next_homonym')

    def __init__(self, item: Optional[str], count: int, parent: Optional['FPNode']):
        self.item = item
        self.count = count
        self.parent = parent
        self.children: Dict[str, 'FPNode'] = {}
        self.next_homonym: Optional['FPNode'] = None  # Pointer to next node with same item in header link list

    def increment(self, count: int = 1):
        self.count += count


class FPTree:
    """FP-Tree structure maintaining the root and header table."""

    def __init__(self):
        self.root = FPNode(item=None, count=0, parent=None)
        # Header table: item -> [total_support_count, head_node_pointer]
        self.header_table: Dict[str, List[Any]] = {}

    def insert_transaction(self, items: List[str], count: int = 1):
        """Inserts a sorted frequent transaction path into the FP-tree."""
        curr = self.root
        for item in items:
            if item in curr.children:
                curr.children[item].increment(count)
            else:
                new_node = FPNode(item=item, count=count, parent=curr)
                curr.children[item] = new_node

                # Update header table link list
                if self.header_table[item][1] is None:
                    self.header_table[item][1] = new_node
                else:
                    # Append to end of homonym linked list
                    tail = self.header_table[item][1]
                    while tail.next_homonym is not None:
                        tail = tail.next_homonym
                    tail.next_homonym = new_node

            curr = curr.children[item]


def build_fp_tree(
    baskets: List[List[str]],
    min_count: int
) -> Tuple[Optional[FPTree], Dict[str, int]]:
    """
    Constructs an FP-Tree from transaction baskets.
    
    Pass 1: Count frequency of 1-items.
    Pass 2: Insert frequent items into tree sorted by descending frequency (then alphabetically).
    """
    # Pass 1: Count item occurrences (deduplicating items within individual baskets)
    item_counts = defaultdict(int)
    for b in baskets:
        # Deduplicate repeated items within the same basket
        unique_b = set(b)
        for item in unique_b:
            item_counts[item] += 1

    # Filter infrequent items
    frequent_items = {item: count for item, count in item_counts.items() if count >= min_count}
    if not frequent_items:
        return None, {}

    # Initialize FP-Tree and header table
    tree = FPTree()
    for item, count in frequent_items.items():
        tree.header_table[item] = [count, None]

    # Rank function: descending by count, then ascending by item string for deterministic ties
    rank = {item: (-frequent_items[item], item) for item in frequent_items}

    # Pass 2: Filter and sort each basket, then insert into tree
    for b in baskets:
        filtered_sorted = [item for item in set(b) if item in frequent_items]
        filtered_sorted.sort(key=lambda x: rank[x])
        if filtered_sorted:
            tree.insert_transaction(filtered_sorted, count=1)

    return tree, frequent_items


def find_prefix_path(node: FPNode) -> List[str]:
    """Climbs the parent pointers from the node to the root to collect prefix items."""
    path = []
    curr = node.parent
    while curr is not None and curr.item is not None:
        path.append(curr.item)
        curr = curr.parent
    return path


def mine_fp_tree(
    tree: FPTree,
    min_count: int,
    prefix: Set[str],
    frequent_itemsets: Dict[frozenset, int]
):
    """
    Recursively mines frequent patterns from the FP-Tree using conditional pattern bases.
    """
    # Sort header table items by ascending support count (bottom-up mining)
    # Tie-breaking with item name ensures deterministic recursion
    sorted_items = sorted(
        tree.header_table.keys(),
        key=lambda item: (tree.header_table[item][0], item)
    )

    for item in sorted_items:
        support_count = tree.header_table[item][0]
        new_pattern = prefix.union({item})
        frequent_itemsets[frozenset(new_pattern)] = support_count

        # Step 1: Collect conditional pattern base for `item`
        cond_patterns: List[Tuple[List[str], int]] = []
        node = tree.header_table[item][1]
        while node is not None:
            prefix_path = find_prefix_path(node)
            if prefix_path:
                cond_patterns.append((prefix_path, node.count))
            node = node.next_homonym

        # Step 2: Build conditional FP-Tree
        cond_item_counts = defaultdict(int)
        for path, count in cond_patterns:
            for parent_item in path:
                cond_item_counts[parent_item] += count

        # Filter conditional frequent items
        cond_frequent = {p: cnt for p, cnt in cond_item_counts.items() if cnt >= min_count}
        if not cond_frequent:
            continue

        cond_tree = FPTree()
        for p, cnt in cond_frequent.items():
            cond_tree.header_table[p] = [cnt, None]

        rank = {p: (-cond_frequent[p], p) for p in cond_frequent}

        for path, count in cond_patterns:
            sorted_cond_path = [p for p in path if p in cond_frequent]
            sorted_cond_path.sort(key=lambda x: rank[x])
            if sorted_cond_path:
                # Insert path with the accumulated multiplicity count
                cond_curr = cond_tree.root
                for p in sorted_cond_path:
                    if p in cond_curr.children:
                        cond_curr.children[p].increment(count)
                    else:
                        new_node = FPNode(item=p, count=count, parent=cond_curr)
                        cond_curr.children[p] = new_node
                        if cond_tree.header_table[p][1] is None:
                            cond_tree.header_table[p][1] = new_node
                        else:
                            tail = cond_tree.header_table[p][1]
                            while tail.next_homonym is not None:
                                tail = tail.next_homonym
                            tail.next_homonym = new_node
                    cond_curr = cond_curr.children[p]

        # Step 3: Recursive mining on conditional tree
        mine_fp_tree(cond_tree, min_count, new_pattern, frequent_itemsets)


def run_fpgrowth(
    baskets: List[List[str]],
    min_support: Union[float, int]
) -> Dict[str, Any]:
    """
    Runs the custom FP-Growth algorithm on a list of transaction baskets.
    
    Args:
        baskets: List of transaction baskets (each basket is a list of item names).
        min_support: Minimum support threshold (float in (0, 1] or percentage in (1, 100]).
        
    Returns:
        Structured dictionary matching the Apriori output format:
        {
            "algorithm": "FP-Growth",
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
            "algorithm": "FP-Growth",
            "total_baskets": 0,
            "min_support_fraction": normalized_support,
            "min_support_percent": round(normalized_support * 100.0, 4),
            "min_support_count": 0,
            "itemset_count": 0,
            "execution_time_seconds": round(time.time() - start_time, 4),
            "frequent_itemsets": []
        }

    # min_count calculation: ceiling of total_baskets * normalized_support
    min_count = math.ceil(total_baskets * normalized_support)

    # Build initial FP-Tree
    tree, _ = build_fp_tree(baskets, min_count)

    frequent_itemsets_dict: Dict[frozenset, int] = {}
    if tree is not None:
        mine_fp_tree(tree, min_count, set(), frequent_itemsets_dict)

    # Format structured output compatible with Apriori
    formatted_itemsets = []
    for itemset, count in frequent_itemsets_dict.items():
        sup = count / total_baskets if total_baskets > 0 else 0.0
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
        "algorithm": "FP-Growth",
        "total_baskets": total_baskets,
        "min_support_fraction": normalized_support,
        "min_support_percent": round(normalized_support * 100.0, 4),
        "min_support_count": min_count,
        "itemset_count": len(formatted_itemsets),
        "execution_time_seconds": round(elapsed, 4),
        "frequent_itemsets": formatted_itemsets
    }
