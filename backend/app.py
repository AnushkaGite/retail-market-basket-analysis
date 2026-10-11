"""
Flask REST API for Retail Market Basket Analysis.

Exposes endpoints for:
1. GET  /api/dataset-info: Metadata, available presets, and record counts.
2. POST /api/run-analysis: Executes custom Apriori, FP-Growth, or comparative analysis,
                           and generates association rules.
3. POST /api/export-rules: Exports association rules as a downloadable CSV stream.
"""

import os
import io
import csv
import json
import time
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from backend.preprocessing.basket_builder import load_baskets_from_json
from backend.algorithms.apriori import run_apriori, normalize_min_support
from backend.algorithms.fp_growth import run_fpgrowth
from backend.algorithms.association_rules import generate_rules, normalize_confidence_and_lift

app = Flask(__name__)
# Enable CORS for local React development
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Directory configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "data", "samples")

PRESET_FILES = {
    "sample_1.7k": os.path.join(SAMPLES_DIR, "retail_sample_5k.json"),
    "full_36k": os.path.join(SAMPLES_DIR, "retail_full_cleaned.json"),
    "toy_5": os.path.join(SAMPLES_DIR, "toy_baskets.json")
}

# In-memory preset cache: preset_key -> {"baskets": list, "metadata": dict}
PRESET_CACHE: Dict[str, Dict[str, Any]] = {}


def get_cached_baskets(preset_key: str) -> List[List[str]]:
    """Loads baskets into memory once per preset to ensure sub-second API responses."""
    if preset_key not in PRESET_FILES:
        raise ValueError(f"Unknown dataset preset: {preset_key}")

    if preset_key in PRESET_CACHE:
        return PRESET_CACHE[preset_key]["baskets"]

    file_path = PRESET_FILES[preset_key]
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Preset file not found: {os.path.basename(file_path)}")

    baskets, metadata = load_baskets_from_json(file_path)
    PRESET_CACHE[preset_key] = {
        "baskets": baskets,
        "metadata": metadata
    }
    return baskets


@app.route("/api/dataset-info", methods=["GET"])
def dataset_info():
    """Returns dataset overview and available sample presets."""
    try:
        # Check source raw CSV existence without exposing absolute paths
        raw_csv_exists = os.path.exists(os.path.join(BASE_DIR, "..", "online_retail_II.csv"))

        presets_info = []
        for key, path in PRESET_FILES.items():
            exists = os.path.exists(path)
            basket_count = 0
            meta = {}
            if exists:
                if key in PRESET_CACHE:
                    basket_count = len(PRESET_CACHE[key]["baskets"])
                    meta = PRESET_CACHE[key].get("metadata", {})
                else:
                    # Quick read metadata without loading all baskets
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    basket_count = len(data.get("baskets", []))
                    meta = data.get("metadata", {})

            presets_info.append({
                "id": key,
                "name": {
                    "sample_1.7k": "Fast Retail Sample (1,710 Baskets)",
                    "full_36k": "Full Cleaned Retail Dataset (36,307 Baskets)",
                    "toy_5": "Textbook Verification Dataset (5 Baskets)"
                }.get(key, key),
                "available": exists,
                "basket_count": basket_count,
                "recommended_min_support": 0.02 if key != "toy_5" else 0.60,
                "metadata": meta
            })

        return jsonify({
            "status": "success",
            "dataset_name": "Online Retail II (UCI / Kaggle)",
            "source_raw_csv_present": raw_csv_exists,
            "total_raw_rows": 1067371,
            "presets": presets_info
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/run-analysis", methods=["POST"])
def run_analysis():
    """
    Executes frequent itemset mining and association rule generation.
    
    Request payload:
    {
        "preset": "sample_1.7k",         # default: "sample_1.7k"
        "algorithm": "apriori" | "fpgrowth" | "compare",  # default: "fpgrowth"
        "min_support": 0.02,             # float in (0, 1] or percentage in (1, 100]
        "min_confidence": 0.50,          # float in (0, 1] or percentage in (1, 100]
        "min_lift": 1.20,                # float >= 0.0
        "max_baskets": 1000              # optional basket cap
    }
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON payload in request."
        }), 400

    preset = data.get("preset", "sample_1.7k")
    algorithm = str(data.get("algorithm", "fpgrowth")).lower().strip()
    raw_support = data.get("min_support", 0.02)
    raw_confidence = data.get("min_confidence", 0.50)
    raw_lift = data.get("min_lift", 1.0)
    max_baskets = data.get("max_baskets")

    # 1. Parameter Validation
    valid_algos = {"apriori", "fpgrowth", "compare"}
    if algorithm not in valid_algos:
        return jsonify({
            "status": "error",
            "message": f"Unsupported algorithm '{algorithm}'. Must be one of: {sorted(list(valid_algos))}."
        }), 400

    try:
        norm_support = normalize_min_support(raw_support)
    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": f"Invalid min_support: {str(e)}"}), 400

    try:
        norm_confidence, norm_lift = normalize_confidence_and_lift(raw_confidence, raw_lift)
    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": f"Invalid rule threshold: {str(e)}"}), 400

    # 2. Dataset Retrieval
    try:
        baskets = get_cached_baskets(preset)
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to load dataset: {str(e)}"}), 500

    if max_baskets and isinstance(max_baskets, int) and max_baskets > 0:
        baskets = baskets[:max_baskets]

    total_baskets = len(baskets)

    # 3. Algorithm Execution
    benchmark_metrics = {
        "apriori_time_seconds": None,
        "fpgrowth_time_seconds": None,
        "speedup_factor": None,
        "itemsets_match": None
    }

    itemsets_result = None

    try:
        if algorithm == "apriori":
            itemsets_result = run_apriori(baskets, min_support=norm_support)
            benchmark_metrics["apriori_time_seconds"] = itemsets_result["execution_time_seconds"]

        elif algorithm == "fpgrowth":
            itemsets_result = run_fpgrowth(baskets, min_support=norm_support)
            benchmark_metrics["fpgrowth_time_seconds"] = itemsets_result["execution_time_seconds"]

        elif algorithm == "compare":
            # Run both algorithms on identical transactions and thresholds
            apriori_res = run_apriori(baskets, min_support=norm_support)
            fpgrowth_res = run_fpgrowth(baskets, min_support=norm_support)

            benchmark_metrics["apriori_time_seconds"] = apriori_res["execution_time_seconds"]
            benchmark_metrics["fpgrowth_time_seconds"] = fpgrowth_res["execution_time_seconds"]

            # Compute speedup
            fp_time = max(fpgrowth_res["execution_time_seconds"], 0.0001)
            benchmark_metrics["speedup_factor"] = round(apriori_res["execution_time_seconds"] / fp_time, 2)

            # Verify identical itemset counts
            benchmark_metrics["itemsets_match"] = (apriori_res["itemset_count"] == fpgrowth_res["itemset_count"])

            # Use fpgrowth result for rule generation
            itemsets_result = fpgrowth_res

        # 4. Association Rule Generation
        frequent_itemsets_list = itemsets_result.get("frequent_itemsets", [])
        rules_result = generate_rules(
            frequent_itemsets=frequent_itemsets_list,
            min_confidence=norm_confidence,
            min_lift=norm_lift,
            total_baskets=total_baskets
        )

        return jsonify({
            "status": "success",
            "parameters": {
                "preset": preset,
                "baskets_analyzed": total_baskets,
                "algorithm": algorithm,
                "min_support_fraction": norm_support,
                "min_support_percent": round(norm_support * 100.0, 4),
                "min_confidence_fraction": norm_confidence,
                "min_confidence_percent": round(norm_confidence * 100.0, 4),
                "min_lift": norm_lift
            },
            "benchmark": benchmark_metrics,
            "frequent_itemsets": {
                "total_count": itemsets_result["itemset_count"],
                "execution_time_seconds": itemsets_result["execution_time_seconds"],
                "itemsets": frequent_itemsets_list
            },
            "association_rules": {
                "total_count": rules_result["rule_count"],
                "execution_time_seconds": rules_result["execution_time_seconds"],
                "rules": rules_result["rules"]
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Execution failed: {str(e)}"
        }), 500


@app.route("/api/export-rules", methods=["POST"])
def export_rules():
    """
    Exports association rules into a downloadable CSV file.
    
    Accepts JSON payload:
    {
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
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        return jsonify({"status": "error", "message": "'rules' must be a list."}), 400

    # In-memory CSV stream generation
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Rule #",
        "Antecedent (Customer Bought)",
        "Consequent (Recommended Next)",
        "Support",
        "Support %",
        "Confidence",
        "Confidence %",
        "Lift",
        "Support Count"
    ])

    for idx, r in enumerate(rules, 1):
        ante_str = ", ".join(r.get("antecedent", []))
        cons_str = ", ".join(r.get("consequent", []))
        sup = r.get("support", 0.0)
        conf = r.get("confidence", 0.0)
        lift = r.get("lift", 0.0)
        count = r.get("support_count", 0)

        writer.writerow([
            idx,
            ante_str,
            cons_str,
            round(sup, 6),
            f"{sup * 100.0:.2f}%",
            round(conf, 6),
            f"{conf * 100.0:.2f}%",
            round(lift, 4),
            count
        ])

    csv_data = output.getvalue()
    output.close()

    filename = f"market_basket_rules_{int(time.time())}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Retail Market Basket Analysis Flask Server on port {port}...")
    app.run(host="127.0.0.1", port=port, debug=True)
