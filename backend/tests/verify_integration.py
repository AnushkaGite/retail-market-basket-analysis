"""
End-to-end integration verification script testing the live Flask server.
"""

import urllib.request
import json

BASE_URL = 'http://127.0.0.1:5000/api'

def run_tests():
    # 1. Dataset overview verification
    req_info = urllib.request.Request(f'{BASE_URL}/dataset-info')
    with urllib.request.urlopen(req_info) as resp:
        data_info = json.loads(resp.read().decode())
        print('1. GET /dataset-info:')
        print(f'   Status: {data_info["status"]}')
        print(f'   Presets found: {[p["id"] for p in data_info["presets"]]}')

    # 2. Apriori analysis on retail sample
    payload_apriori = {
        'preset': 'sample_1.7k',
        'algorithm': 'apriori',
        'min_support': 0.02,
        'min_confidence': 0.50,
        'min_lift': 1.20
    }
    req_apriori = urllib.request.Request(
        f'{BASE_URL}/run-analysis',
        data=json.dumps(payload_apriori).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req_apriori) as resp:
        data_ap = json.loads(resp.read().decode())
        print('\n2. POST /run-analysis (Apriori):')
        print(f'   Baskets analyzed: {data_ap["parameters"]["baskets_analyzed"]}')
        print(f'   Itemsets mined: {data_ap["frequent_itemsets"]["total_count"]}')
        print(f'   Rules mined: {data_ap["association_rules"]["total_count"]}')
        print(f'   Apriori time: {data_ap["benchmark"]["apriori_time_seconds"]}s')

    # 3. FP-Growth analysis on retail sample with identical thresholds
    payload_fp = {
        'preset': 'sample_1.7k',
        'algorithm': 'fpgrowth',
        'min_support': 0.02,
        'min_confidence': 0.50,
        'min_lift': 1.20
    }
    req_fp = urllib.request.Request(
        f'{BASE_URL}/run-analysis',
        data=json.dumps(payload_fp).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req_fp) as resp:
        data_fp = json.loads(resp.read().decode())
        print('\n3. POST /run-analysis (FP-Growth):')
        print(f'   Itemsets mined: {data_fp["frequent_itemsets"]["total_count"]}')
        print(f'   Rules mined: {data_fp["association_rules"]["total_count"]}')
        print(f'   FP-Growth time: {data_fp["benchmark"]["fpgrowth_time_seconds"]}s')
        same_itemsets = (data_ap["frequent_itemsets"]["total_count"] == data_fp["frequent_itemsets"]["total_count"])
        same_rules = (data_ap["association_rules"]["total_count"] == data_fp["association_rules"]["total_count"])
        print(f'   Identical itemsets count check: {same_itemsets}')
        print(f'   Identical rules count check: {same_rules}')

    # 4. CSV export verification
    sample_rule = data_fp['association_rules']['rules'][:3]
    req_export = urllib.request.Request(
        f'{BASE_URL}/export-rules',
        data=json.dumps({'rules': sample_rule}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req_export) as resp:
        csv_bytes = resp.read()
        print('\n4. POST /export-rules:')
        print(f'   HTTP status: {resp.status}')
        print(f'   Content-Type: {resp.headers.get("Content-Type")}')
        print(f'   Content-Disposition: {resp.headers.get("Content-Disposition")}')
        print(f'   CSV preview:\n{csv_bytes[:200].decode()}')

if __name__ == '__main__':
    run_tests()
