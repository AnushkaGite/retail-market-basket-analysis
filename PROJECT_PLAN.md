# Project Plan: Retail Market Basket Analysis

**Project Title:** Retail Market Basket Analysis Using Frequent Itemset Mining and Association Rule Mining  
**Dataset:** Online Retail II (UCI / Kaggle)  
**Technology Stack:**
- **Frontend:** React, HTML, CSS, Chart.js / Recharts, Lucide React
- **Backend:** Python, Flask, Flask-CORS
- **Data Processing:** Pandas, NumPy
- **Algorithms:** Custom Apriori, Custom FP-Growth, Association Rule Miner
- **Validation:** Independent mlxtend benchmark test suites

---

## Progress Overview

- [x] **Phase 1: Environment Setup & Dataset Verification** (Completed)
  - Python 3.13 venv created, dependencies installed (`flask`, `pandas`, `numpy`, `mlxtend`, `pytest`).
  - Git initialized with `.gitignore` excluding raw CSVs, cache, and `.venv`.
  - Raw dataset verified: 1,067,371 rows, 8 columns, 94.8 MB.

- [x] **Phase 2: Data Preprocessing and Staged Dataset Preparation** (Completed)
  - Streaming cleaner and basket builder created (`backend/preprocessing/`).
  - Business rules applied: filter cancellations (`'C'`), non-positive quantities/prices, non-product charges (`POSTAGE`, etc.).
  - Deduplicated itemsets per invoice basket.
  - Staged samples generated: `toy_baskets.json`, `retail_sample_5k.json` (1,710 baskets), `retail_full_cleaned.json` (36,307 baskets).

- [x] **Phase 3: Custom Apriori Implementation** (Completed)
  - Pure Python Apriori with $C_k$ join step and subset pruning (`backend/algorithms/apriori.py`).
  - Normalized support convention (fractions or percentages).
  - Validated against manual ground truth on toy dataset and `mlxtend.frequent_patterns.apriori`.

- [x] **Phase 4: Custom FP-Growth Implementation** (Completed)
  - Custom FP-Tree data structure (`FPNode`, `FPTree`, header tables, node links) (`backend/algorithms/fp_growth.py`).
  - Recursive conditional pattern base mining without candidate generation.
  - 100% agreement with Apriori verified across multiple thresholds.
  - ~96x speedup demonstrated on retail sample.

- [x] **Phase 5: Association Rule Generation** (Completed)
  - Rule miner for non-empty disjoint partitions $X \to Y$ (`backend/algorithms/association_rules.py`).
  - Metrics computed: Support($X \cup Y$), Confidence, Lift.
  - Validated on synthetic dataset and confirmed identical output whether fed from Apriori or FP-Growth.

- [x] **Phase 6: Retail-Themed Frontend and Backend Integration Planning** (Completed)
  - Designed Flask REST API endpoints, request/response contracts, and UI components.

- [x] **Phase 7: Backend API Implementation (Flask)** (Completed)
  - Implemented `backend/app.py` with `/api/dataset-info`, `/api/run-analysis`, and `/api/export-rules`.
  - Added full test suite in `backend/tests/test_api.py` (all passing).

- [x] **Phase 8: Retail-Themed React Frontend Implementation** (Completed)
  - Scaffolding via Vite + React 19 + Recharts + Lucide React.
  - Retail UI design system in `frontend/src/index.css`.
  - Interactive controls, comparison charts, searchable tables, CSV export in `frontend/src/App.jsx`.

- [x] **Phase 9: End-to-End Verification and Assignment Finalization** (Completed)
  - Backend tests passed.
  - Production frontend build verified (`dist/`).
  - Live HTTP integration verified for all endpoints and comparison benchmarks.
  - Original raw CSV verified untouched (94,850,204 bytes).

- [x] **Phase 10: Source Review Refinements & Documentation** (Completed)
  - Fixed algorithm comparison in `backend/app.py`: switched `itemsets_match` from simple count equality to strict, order-independent verification of frequent itemsets and exact support counts between Apriori and FP-Growth. Added mismatch detection unit tests.
  - Fixed CSV export in `frontend/src/App.jsx`: export strictly honors the active search query and exports filtered rules; raises a helpful user notification and disables export if 0 search matches occur; exports all rules when search is empty.
  - Full backend test suite passing: 25 of 25 tests passed in 1.95s.
  - Frontend production build verified (`npm run build` succeeds cleanly in 765ms).
  - Comprehensive documentation generated in `README.md`.

