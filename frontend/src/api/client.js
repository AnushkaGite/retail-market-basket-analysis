/**
 * CartInsight Retail - Market Basket Analysis API Client
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api';

export async function fetchDatasetInfo() {
  const response = await fetch(`${API_BASE_URL}/dataset-info`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Failed to fetch dataset info (HTTP ${response.status})`);
  }
  return response.json();
}

export async function runMarketBasketAnalysis(params) {
  const response = await fetch(`${API_BASE_URL}/run-analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || `Analysis failed (HTTP ${response.status})`);
  }
  return data;
}

export async function exportRulesToCSV(rules) {
  const response = await fetch(`${API_BASE_URL}/export-rules`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ rules }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `Export failed (HTTP ${response.status})`);
  }

  // Trigger browser file download via Blob
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = `market_basket_rules_${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
