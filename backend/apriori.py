"""
Convenience module to expose Apriori directly under backend as requested in requirements.
"""
from backend.algorithms.apriori import run_apriori, normalize_min_support

__all__ = ['run_apriori', 'normalize_min_support']
