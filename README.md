# Retail Market Basket Analysis Using Frequent Itemset Mining & Association Rule Mining

A full-stack, retail-themed Market Basket Analysis (MBA) web application built to discover customer purchasing patterns, cross-selling affinities, and product associations using custom, from-scratch Python implementations of the **Apriori** and **FP-Growth (Frequent Pattern Growth)** algorithms.

---

## 📌 Project Overview

Market basket analysis is a core data-mining technique used by omnichannel and e-commerce retailers to optimize catalog recommendations, promotional cross-bundles, and shelf placements. 

This project was developed for a computer science data mining / analytics assignment. It provides:
1. **From-Scratch Algorithm Implementations:** Pure Python implementations of Apriori (candidate generation and downward-closure pruning) and FP-Growth (compact FP-Tree construction and recursive conditional pattern base mining), without relying on external mining libraries for core execution.
2. **Standard-Conforming Association Rule Mining:** Generates disjoint non-empty rules $X \to Y$ evaluating Support, Confidence, and Lift.
3. **Comparative Benchmarking:** Head-to-head performance analysis measuring wall-clock execution time, throughput, itemset identity verification, and relative acceleration ratio between candidate generation (Apriori) and pattern-growth (FP-Growth).
4. **Interactive Retail-Themed Dashboard:** A clean, modern e-commerce analytics interface built with React, Vite, and Recharts, connected to a Flask REST API.

---

## 🏗️ Architecture & Technology Stack

```
┌────────────────────────────────────────────────────────┐
│             React + Vite Frontend (SPA)               │
│  - Retail-Themed Dashboard & Parameter Sliders/Inputs   │
│  - Interactive Comparison Charts (Recharts)           │
│  - Searchable Rule & Itemset Tables with CSV Export   │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP REST (JSON)
┌───────────────────────────▼────────────────────────────┐
│                  Flask REST API Backend                │
│  - GET  /api/dataset-info                              │
│  - POST /api/run-analysis (Apriori, FP-Growth, Both)   │
│  - POST /api/export-rules (Stream CSV)                 │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│             Custom Data Mining Engine                  │
│  ├── Preprocessing & Basket Builder (Pandas / NumPy)   │
│  ├── Custom Apriori Miner                              │
│  ├── Custom FP-Growth Miner (FPNode / FPTree)          │
│  └── Association Rule Miner (Confidence & Lift)        │
└────────────────────────────────────────────────────────┘
```

- **Frontend:** React 19, Vite, Recharts, Lucide React, Modern CSS Grid & Variables.
- **Backend:** Python 3.13, Flask, Flask-CORS.
- **Data Processing:** Pandas, NumPy.
- **Benchmarking & Validation:** Validated against ground truth and `mlxtend` test suites using `pytest`.

---

## 📊 Dataset & Preprocessing

The primary data source is the **Online Retail II** dataset (UCI Machine Learning Repository / Kaggle), containing 1,067,371 transnational transactions from a UK-based online giftware retailer.

### Preprocessing Rules Applied:
1. **Invoice Type Filtering:** Cancelled transactions (invoices starting with `'C'`) are filtered out.
2. **Quality & Anomaly Cleansing:** Non-positive quantities ($Quantity \le 0$) and zero unit prices ($UnitPrice \le 0$) are removed.
3. **Service Charge Exclusion:** Non-product SKU entries (e.g., `POST`, `POSTAGE`, `MANUAL`, `BANK CHARGES`, `AMAZON FEE`) and missing product descriptions are stripped.
4. **Item Deduplication:** Multiple line-items of identical products within the same transaction are consolidated into a unique basket set.

### Available Dataset Presets:
- **Toy Dataset (5 baskets):** Standard text-book verification set for manual calculation checks.
- **Representative Retail Sample (1,710 baskets):** 5,000 raw invoice rows processed into 1,710 unique transaction baskets (ideal for rapid interactive parameter tuning and real-time Apriori vs FP-Growth benchmarks).
- **Full Cleaned Retail Dataset (36,307 baskets):** The complete clean transactional corpus spanning 2009–2011.

---

## 🧮 Algorithm Details & Mathematical Formulations

### 1. Apriori Algorithm
Operates by candidate generation level by level based on the downward-closure (Apriori) property: *All non-empty subsets of a frequent itemset must also be frequent.*
- **Pass 1:** Count individual item support to find $L_1$.
- **Pass $k$ ($k \ge 2$):** Join $L_{k-1}$ with itself to generate candidate $C_k$, prune candidates whose $(k-1)$-subsets are not frequent, and scan the dataset to determine frequent itemsets $L_k$.

### 2. FP-Growth (Frequent Pattern Growth)
Eliminates candidate generation bottleneck via a 2-pass divide-and-conquer strategy:
1. **Header Table & Tree Construction:** Scans the database to compute item frequencies, filters infrequent items, sorts items in descending order of frequency, and builds a compact Prefix Tree (`FP-Tree`) with node links.
2. **Recursive Pattern Mining:** For each item in reverse frequency order, traverses prefix paths via node-links to build a **Conditional Pattern Base**, constructs a **Conditional FP-Tree**, and recursively derives frequent patterns.

### 3. Association Rule Mining
Given frequent itemset $I$ and all disjoint non-empty partitions $X \to Y$ (where $X \cup Y = I$ and $X \cap Y = \emptyset$):
- **Support:**
  $$\text{Support}(X \to Y) = P(X \cup Y) = \frac{\text{count}(X \cup Y)}{N}$$
- **Confidence:**
  $$\text{Confidence}(X \to Y) = P(Y \mid X) = \frac{\text{Support}(X \cup Y)}{\text{Support}(X)}$$
- **Lift:**
  $$\text{Lift}(X \to Y) = \frac{\text{Confidence}(X \to Y)}{\text{Support}(Y)} = \frac{P(X \cup Y)}{P(X) \cdot P(Y)}$$
  - $\text{Lift} > 1$: Positive affinity (items co-occur more frequently than expected by chance).
  - $\text{Lift} = 1$: Independent occurrences.
  - $\text{Lift} < 1$: Negative affinity / substitute items.

---

## 🚀 Local Installation & Setup

> **Note:** This project is designed and configured to run locally. No external cloud deployment or external database is required.

### Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **Node.js 18+** and **npm**

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/AnushkaGite/retail-market-basket-analysis.git
cd retail-market-basket-analysis
```

---

### Step 2: Set Up Backend Environment

1. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv backend\.venv
   backend\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Start the Flask API:
   ```bash
   python -m backend.app
   ```
   The Flask server will start at `http://127.0.0.1:5000`.

---

### Step 3: Set Up Frontend Environment

In a separate terminal window:

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
   Open your browser and navigate to `http://localhost:5173`.

---

### Production Frontend Build (Optional)
To verify or serve the optimized production static build:
```bash
cd frontend
npm run build
npm run preview
```

---

## 🧪 Automated Testing & Verification

The test suite validates algorithmic correctness, edge cases, numerical normalization, and API behavior:

```bash
# From the project root
python -m pytest -v backend/tests
```

### Test Suite Structure (25 Tests Passing):
- **`backend/tests/test_apriori.py`:**
  - Support normalization (fractions and percentages).
  - Ground truth validation on toy dataset.
  - Edge cases (high support thresholds, empty baskets).
  - Cross-validation against `mlxtend.frequent_patterns.apriori`.
- **`backend/tests/test_fpgrowth.py`:**
  - Ground truth verification on toy dataset.
  - Order-independent exact agreement with Apriori across multiple thresholds.
  - Edge cases (single-item transactions, zero-support items).
  - Cross-validation against `mlxtend.frequent_patterns.fpgrowth`.
- **`backend/tests/test_association_rules.py`:**
  - Confidence and lift bounds checking.
  - Verification of rule generation on manual benchmarks.
  - Exact rule agreement between Apriori and FP-Growth pipelines.
- **`backend/tests/test_preprocessing.py`:**
  - Cancellation code filtering (`C` invoices).
  - Invalid quantity and unit price removal.
  - Non-product SKU cleaning and deduplication.
  - Basket generation from synthetic data.
- **`backend/tests/test_api.py`:**
  - `GET /api/dataset-info` status and metadata validation.
  - `POST /api/run-analysis` parameter validation and algorithm runs.
  - `Compare Both` mode validation including strict itemset equality and mismatch detection.
  - CSV rule export endpoint verification.

---

## ⚡ Performance Characteristics & Practical Usage Notes

- **Apriori vs. FP-Growth:**
  - On dense retail transactional datasets with thousands of items, **Apriori** experiences exponential growth in candidate generation when thresholds are low ($\le 1\%$).
  - **FP-Growth** avoids candidate generation entirely by mining the prefix tree recursively, typically achieving **50x to 100x+ faster execution** on typical retail baskets.
- **Recommended Settings:**
  - For interactive parameter experimentation and real-time algorithm comparisons, the **1.7k Basket Preset** (`retail_sample_5k.json`) with minimum support between `1.5%` and `3.0%` provides instant (< 1s) responses.
  - When analyzing the **36k Full Dataset**, use **FP-Growth** with support $\ge 2.0\%$ for optimal throughput.

---

## 📁 Repository Structure

```
retail-market-basket-analysis/
├── PROJECT_PLAN.md               # Development roadmap & phase tracking
├── README.md                     # Comprehensive technical documentation
├── .gitignore                    # Git exclusion rules
│
├── backend/
│   ├── app.py                   # Flask REST API entrypoint
│   ├── requirements.txt         # Python dependencies
│   ├── algorithms/
│   │   ├── apriori.py           # Custom Apriori implementation
│   │   ├── fp_growth.py         # Custom FP-Growth implementation
│   │   └── association_rules.py # Custom Association Rule miner
│   ├── preprocessing/
│   │   ├── cleaner.py           # Transaction cleaner and filter
│   │   └── basket_builder.py    # Basket grouping and JSON serializer
│   ├── data/
│   │   └── samples/             # Staged JSON basket samples (toy, 1.7k, 36k)
│   └── tests/                   # 25 automated pytest suites
│
└── frontend/
    ├── index.html               # Web application shell
    ├── package.json             # Frontend dependencies and scripts
    ├── vite.config.js           # Vite build configuration
    └── src/
        ├── App.jsx              # Main Market Basket Analysis dashboard
        ├── index.css            # Retail design system styles
        └── main.jsx             # React entrypoint
```

---

## 👤 Author & Academic Context

- **Author:** Anushka Gite  
- **Repository:** [https://github.com/AnushkaGite/retail-market-basket-analysis](https://github.com/AnushkaGite/retail-market-basket-analysis)  
- **Coursework:** Computer Science / Data Mining Assignment  
- **Topic:** Retail Market Basket Analysis Using Frequent Itemset Mining and Association Rule Mining
