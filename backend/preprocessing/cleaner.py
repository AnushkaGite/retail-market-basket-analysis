"""
Clean and process Online Retail II transactions into market baskets.
"""

import csv
import os
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict


NON_PRODUCT_CODES = {
    'POST', 'D', 'M', 'PADS', 'DOT', 'CRUK', 'BANK CHARGES', 'AMAZONFEE', 'TEST'
}

NON_PRODUCT_DESCRIPTIONS = {
    'POSTAGE', 'MANUAL', 'CARRIAGE', 'DOTCOM POSTAGE', 'DISCOUNT', 'BANK CHARGES',
    'AMAZON FEE', 'CRUK COMMISSION', 'SAMPLES', 'ADJUST', 'ADJUSTMENT'
}


def clean_description(desc: Optional[str]) -> Optional[str]:
    """Cleans and standardizes product description."""
    if not desc:
        return None
    d = desc.strip().upper()
    d = re.sub(r'\s+', ' ', d)
    if not d or d in NON_PRODUCT_DESCRIPTIONS:
        return None
    return d


def is_valid_transaction_row(
    invoice: str,
    stock_code: str,
    description: Optional[str],
    quantity_str: str,
    price_str: str,
) -> Tuple[bool, Optional[str]]:
    """
    Validates a single row against retail cleaning criteria.
    Returns (is_valid, cleaned_description).
    """
    inv = invoice.strip()
    if not inv or inv.upper().startswith('C'):
        return False, None

    code = stock_code.strip().upper()
    if code in NON_PRODUCT_CODES:
        return False, None

    cleaned_desc = clean_description(description)
    if not cleaned_desc:
        return False, None

    try:
        qty = float(quantity_str)
        if qty <= 0:
            return False, None
    except (ValueError, TypeError):
        return False, None

    try:
        price = float(price_str)
        if price <= 0:
            return False, None
    except (ValueError, TypeError):
        return False, None

    return True, cleaned_desc


def build_baskets_from_iterable(
    row_iterable: Any,
    min_items: int = 2,
    max_baskets: Optional[int] = None
) -> Tuple[List[List[str]], Dict[str, Any]]:
    """
    Takes an iterable of raw rows (each row matching [Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country])
    and converts them into a list of transaction baskets.
    
    Returns:
        (baskets, stats_dict)
    """
    invoice_baskets = defaultdict(set)
    total_source_rows = 0
    cleaned_rows_count = 0
    unique_products_seen = set()

    for row in row_iterable:
        total_source_rows += 1
        if len(row) < 6:
            continue
        invoice = row[0]
        stock_code = row[1]
        description = row[2]
        quantity = row[3]
        price = row[5]

        valid, cleaned_desc = is_valid_transaction_row(
            invoice=invoice,
            stock_code=stock_code,
            description=description,
            quantity_str=quantity,
            price_str=price
        )

        if valid and cleaned_desc:
            cleaned_rows_count += 1
            inv_key = invoice.strip()
            invoice_baskets[inv_key].add(cleaned_desc)
            unique_products_seen.add(cleaned_desc)

    total_invoices_identified = len(invoice_baskets)

    # Convert to sorted list of lists for deterministic algorithms
    filtered_baskets = []
    for inv, items in invoice_baskets.items():
        if len(items) >= min_items:
            filtered_baskets.append(sorted(list(items)))
            if max_baskets and len(filtered_baskets) >= max_baskets:
                break

    stats = {
        'total_source_rows': total_source_rows,
        'cleaned_rows': cleaned_rows_count,
        'unique_invoices_raw': total_invoices_identified,
        'unique_products': len(unique_products_seen),
        'min_items_threshold': min_items,
        'retained_baskets_count': len(filtered_baskets)
    }

    return filtered_baskets, stats
