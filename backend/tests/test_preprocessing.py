import pytest
from backend.preprocessing.cleaner import is_valid_transaction_row, build_baskets_from_iterable


def test_cleaner_cancellation_invoices():
    # Cancellation starting with 'C'
    valid, desc = is_valid_transaction_row("C489434", "85048", "RED LIGHTS", "12", "6.95")
    assert not valid
    assert desc is None

    # Lowercase 'c'
    valid, desc = is_valid_transaction_row("c489434", "85048", "RED LIGHTS", "12", "6.95")
    assert not valid
    assert desc is None


def test_cleaner_invalid_quantities_and_prices():
    # Negative quantity
    valid, desc = is_valid_transaction_row("489434", "85048", "RED LIGHTS", "-5", "6.95")
    assert not valid

    # Zero quantity
    valid, desc = is_valid_transaction_row("489434", "85048", "RED LIGHTS", "0", "6.95")
    assert not valid

    # Negative price
    valid, desc = is_valid_transaction_row("489434", "85048", "RED LIGHTS", "5", "-2.0")
    assert not valid

    # Zero price
    valid, desc = is_valid_transaction_row("489434", "85048", "RED LIGHTS", "5", "0.0")
    assert not valid


def test_cleaner_non_product_and_missing_descriptions():
    # Missing description
    valid, desc = is_valid_transaction_row("489434", "85048", "", "5", "10.0")
    assert not valid

    # Administrative postage/manual
    valid, desc = is_valid_transaction_row("489434", "POST", "POSTAGE", "1", "15.0")
    assert not valid

    valid, desc = is_valid_transaction_row("489434", "M", "MANUAL", "1", "10.0")
    assert not valid


def test_build_baskets_synthetic_dataset():
    synthetic_rows = [
        # Invoice 1: 3 valid items, 1 duplicate item
        ["INV001", "A1", "Milk", "1", "2026-01-01", "2.0", "101", "UK"],
        ["INV001", "A2", "Bread", "2", "2026-01-01", "1.5", "101", "UK"],
        ["INV001", "A1", "Milk", "1", "2026-01-01", "2.0", "101", "UK"], # duplicate row in same basket
        ["INV001", "A3", "Butter", "1", "2026-01-01", "3.0", "101", "UK"],

        # Invoice 2: Cancelled invoice
        ["CINV002", "A1", "Milk", "-1", "2026-01-01", "2.0", "101", "UK"],

        # Invoice 3: Single item basket (filtered if min_items=2)
        ["INV003", "A2", "Bread", "1", "2026-01-01", "1.5", "102", "UK"],

        # Invoice 4: Invalid price
        ["INV004", "A1", "Milk", "1", "2026-01-01", "0.0", "103", "UK"],
        ["INV004", "A2", "Bread", "1", "2026-01-01", "1.5", "103", "UK"],

        # Invoice 5: 2 valid items
        ["INV005", "A2", "Bread", "1", "2026-01-01", "1.5", "104", "UK"],
        ["INV005", "A3", "Butter", "1", "2026-01-01", "3.0", "104", "UK"],
    ]

    baskets, stats = build_baskets_from_iterable(synthetic_rows, min_items=2)

    assert stats['total_source_rows'] == 10
    assert stats['retained_baskets_count'] == 2 # INV001 (Milk, Bread, Butter) and INV005 (Bread, Butter)
    assert len(baskets) == 2
    assert baskets[0] == ["BREAD", "BUTTER", "MILK"]
    assert baskets[1] == ["BREAD", "BUTTER"]
