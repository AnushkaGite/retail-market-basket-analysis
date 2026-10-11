import React, { useState, useEffect } from 'react';
import {
  ShoppingBag,
  ShoppingCart,
  Sliders,
  Play,
  TrendingUp,
  Clock,
  Layers,
  Download,
  AlertCircle,
  Database,
  ArrowRight,
  Sparkles,
  BarChart2
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

import {
  fetchDatasetInfo,
  runMarketBasketAnalysis,
  exportRulesToCSV
} from './api/client';

export default function App() {
  // State for dataset metadata
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [loadingDataset, setLoadingDataset] = useState(true);

  // Form Controls
  const [selectedPreset, setSelectedPreset] = useState('sample_1.7k');
  const [selectedAlgo, setSelectedAlgo] = useState('compare');
  const [minSupport, setMinSupport] = useState(2.0); // stored as percentage in UI
  const [minConfidence, setMinConfidence] = useState(50.0); // stored as percentage
  const [minLift, setMinLift] = useState(1.2);

  // Analysis Results
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Search & Filter in Tables
  const [ruleSearch, setRuleSearch] = useState('');
  const [itemsetSearch, setItemsetSearch] = useState('');

  // Initial load: Fetch dataset info
  useEffect(() => {
    async function init() {
      try {
        setLoadingDataset(true);
        const data = await fetchDatasetInfo();
        setDatasetInfo(data);
        setErrorMessage(null);
      } catch (err) {
        setErrorMessage(`Backend API connection error: ${err.message}. Please ensure Flask is running.`);
      } finally {
        setLoadingDataset(false);
      }
    }
    init();
  }, []);

  // Run Market Basket Analysis Handler
  const handleRunAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      setErrorMessage(null);

      const params = {
        preset: selectedPreset,
        algorithm: selectedAlgo,
        min_support: parseFloat(minSupport) / 100.0,
        min_confidence: parseFloat(minConfidence) / 100.0,
        min_lift: parseFloat(minLift)
      };

      const result = await runMarketBasketAnalysis(params);
      setAnalysisResult(result);
    } catch (err) {
      setErrorMessage(err.message || 'An error occurred during analysis.');
      setAnalysisResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // CSV Export Handler
  const handleExportCSV = async () => {
    if (!analysisResult?.association_rules?.rules?.length) return;
    try {
      setIsExporting(true);
      await exportRulesToCSV(analysisResult.association_rules.rules);
    } catch (err) {
      setErrorMessage(`CSV export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  // Derived filtered tables
  const filteredRules = (analysisResult?.association_rules?.rules || []).filter(r => {
    const q = ruleSearch.toLowerCase();
    return (
      r.antecedent.some(item => item.toLowerCase().includes(q)) ||
      r.consequent.some(item => item.toLowerCase().includes(q))
    );
  });

  const filteredItemsets = (analysisResult?.frequent_itemsets?.itemsets || []).filter(item => {
    const q = itemsetSearch.toLowerCase();
    return item.items.some(name => name.toLowerCase().includes(q));
  });

  // Visualization Data Preparation
  const chartBenchmarkData = analysisResult?.benchmark?.apriori_time_seconds != null
    ? [
        {
          algorithm: 'Apriori',
          'Execution Time (s)': analysisResult.benchmark.apriori_time_seconds,
          fill: '#f97316'
        },
        {
          algorithm: 'FP-Growth',
          'Execution Time (s)': analysisResult.benchmark.fpgrowth_time_seconds,
          fill: '#059669'
        }
      ]
    : [];

  // Top 8 rules by lift
  const chartTopRules = (analysisResult?.association_rules?.rules || [])
    .slice(0, 8)
    .map((r, i) => ({
      name: `R#${i + 1}: ${r.antecedent[0]?.slice(0, 14)}...`,
      lift: r.lift,
      confidence: r.confidence_percent
    }));

  return (
    <div>
      {/* Top Navbar */}
      <nav className="navbar">
        <div className="brand-container">
          <div className="brand-icon-wrapper">
            <ShoppingBag size={22} />
          </div>
          <div>
            <div className="brand-title">CartInsight Analytics</div>
            <div className="brand-subtitle">Retail Market Basket Intelligence</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span className="badge-tag">
            <ShoppingCart size={14} /> E-Commerce Pattern Mining
          </span>
          <span className="badge-tag" style={{ backgroundColor: '#f1f5f9', color: '#475569', borderColor: '#cbd5e1' }}>
            College Assignment Project
          </span>
        </div>
      </nav>

      <main className="app-container">
        {/* Error Notification */}
        {errorMessage && (
          <div className="alert-error">
            <AlertCircle size={20} />
            <div>
              <strong>Alert:</strong> {errorMessage}
            </div>
          </div>
        )}

        {/* Hero Section */}
        <section className="hero-card">
          <div className="hero-content">
            <h1 className="hero-title">Discover High-Value Cross-Sell Bundles</h1>
            <p className="hero-desc">
              Harness custom <strong>Apriori</strong> and <strong>FP-Growth</strong> algorithms to discover frequent itemsets
              and calculate <em>Support</em>, <em>Confidence</em>, and <em>Lift</em> across retail transactions from the
              Online Retail II dataset.
            </p>
            <div className="hero-stats-row">
              <div className="hero-stat-pill">
                <Database size={16} /> Dataset: <strong>Online Retail II (UCI)</strong>
              </div>
              <div className="hero-stat-pill">
                <Layers size={16} /> Total Records: <strong>1,067,371 rows</strong>
              </div>
              <div className="hero-stat-pill">
                <TrendingUp size={16} /> Mined Baskets: <strong>36,307 cleaned</strong>
              </div>
            </div>
          </div>
        </section>

        {/* Controls Card */}
        <section className="card">
          <div className="section-header">
            <div className="section-title">
              <Sliders size={20} color="var(--primary)" />
              Market Basket Configuration & Parameters
            </div>
            {datasetInfo && (
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Backend Status: <strong style={{ color: '#16a34a' }}>Connected</strong>
              </span>
            )}
          </div>

          <div className="controls-grid">
            {/* Dataset Preset Selector */}
            <div className="form-group">
              <label className="form-label">
                <span>Dataset Scale</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Transaction Scope</span>
              </label>
              <select
                className="form-select"
                value={selectedPreset}
                onChange={(e) => setSelectedPreset(e.target.value)}
                disabled={isAnalyzing}
              >
                <option value="sample_1.7k">Fast Retail Sample (1,710 Baskets - Recommended)</option>
                <option value="full_36k">Full Retail Dataset (36,307 Cleaned Baskets)</option>
                <option value="toy_5">Textbook Verification Dataset (5 Baskets)</option>
              </select>
            </div>

            {/* Algorithm Switcher */}
            <div className="form-group">
              <label className="form-label">
                <span>Mining Algorithm</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Execution Engine</span>
              </label>
              <div className="segmented-control">
                <button
                  type="button"
                  className={`segmented-btn ${selectedAlgo === 'apriori' ? 'active' : ''}`}
                  onClick={() => setSelectedAlgo('apriori')}
                  disabled={isAnalyzing}
                >
                  Apriori
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${selectedAlgo === 'fpgrowth' ? 'active' : ''}`}
                  onClick={() => setSelectedAlgo('fpgrowth')}
                  disabled={isAnalyzing}
                >
                  FP-Growth
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${selectedAlgo === 'compare' ? 'active' : ''}`}
                  onClick={() => setSelectedAlgo('compare')}
                  disabled={isAnalyzing}
                >
                  Compare Both
                </button>
              </div>
            </div>

            {/* Min Support Slider */}
            <div className="form-group">
              <div className="form-label">
                <span>Min Support (%)</span>
                <span className="slider-value">{minSupport}%</span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  className="slider-input"
                  min="0.5"
                  max="15.0"
                  step="0.5"
                  value={minSupport}
                  onChange={(e) => setMinSupport(e.target.value)}
                  disabled={isAnalyzing}
                />
              </div>
            </div>

            {/* Min Confidence Slider */}
            <div className="form-group">
              <div className="form-label">
                <span>Min Confidence (%)</span>
                <span className="slider-value">{minConfidence}%</span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  className="slider-input"
                  min="10"
                  max="90"
                  step="5"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(e.target.value)}
                  disabled={isAnalyzing}
                />
              </div>
            </div>

            {/* Min Lift Input */}
            <div className="form-group">
              <div className="form-label">
                <span>Min Lift Ratio</span>
                <span className="slider-value">{minLift}x</span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  className="slider-input"
                  min="1.0"
                  max="5.0"
                  step="0.1"
                  value={minLift}
                  onChange={(e) => setMinLift(e.target.value)}
                  disabled={isAnalyzing}
                />
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="actions-bar">
            <button
              className="btn-primary"
              onClick={handleRunAnalysis}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <Clock className="animate-spin" size={18} /> Mining Patterns...
                </>
              ) : (
                <>
                  <Play size={18} /> Run Market Basket Analysis
                </>
              )}
            </button>
          </div>
        </section>

        {/* Results Overview */}
        {analysisResult && (
          <>
            {/* KPI Cards */}
            <div className="kpi-grid">
              <div className="kpi-card">
                <div className="kpi-icon blue">
                  <ShoppingCart size={24} />
                </div>
                <div>
                  <div className="kpi-value">{analysisResult.parameters.baskets_analyzed.toLocaleString()}</div>
                  <div className="kpi-label">Baskets Analyzed</div>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-icon green">
                  <Layers size={24} />
                </div>
                <div>
                  <div className="kpi-value">{analysisResult.frequent_itemsets.total_count.toLocaleString()}</div>
                  <div className="kpi-label">Frequent Itemsets</div>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-icon amber">
                  <Sparkles size={24} />
                </div>
                <div>
                  <div className="kpi-value">{analysisResult.association_rules.total_count.toLocaleString()}</div>
                  <div className="kpi-label">Association Rules</div>
                </div>
              </div>

              <div className="kpi-card">
                <div className="kpi-icon purple">
                  <Clock size={24} />
                </div>
                <div>
                  <div className="kpi-value">
                    {analysisResult.parameters.algorithm === 'compare'
                      ? `${analysisResult.benchmark.fpgrowth_time_seconds}s`
                      : `${analysisResult.frequent_itemsets.execution_time_seconds}s`}
                  </div>
                  <div className="kpi-label">
                    {analysisResult.parameters.algorithm === 'compare' ? 'FP-Growth Speed' : 'Execution Time'}
                  </div>
                </div>
              </div>
            </div>

            {/* Visualizations (Recharts) */}
            <div className="charts-grid">
              {/* Benchmark chart if Compare mode */}
              {chartBenchmarkData.length > 0 && (
                <div className="chart-card">
                  <div className="chart-title">
                    <span>Algorithm Execution Benchmark</span>
                    <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: 'bold' }}>
                      {analysisResult.benchmark.speedup_factor}x Speedup
                    </span>
                  </div>
                  <div style={{ height: 260 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartBenchmarkData} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis type="number" unit="s" />
                        <YAxis type="category" dataKey="algorithm" />
                        <Tooltip formatter={(value) => [`${value} seconds`, 'Runtime']} />
                        <Bar dataKey="Execution Time (s)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Top Rules Lift Chart */}
              {chartTopRules.length > 0 && (
                <div className="chart-card">
                  <div className="chart-title">
                    <span>Top Association Rules by Lift</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Strength of Relationship</span>
                  </div>
                  <div style={{ height: 260 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartTopRules} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="name" angle={-25} textAnchor="end" height={50} interval={0} fontSize={11} />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="lift" fill="#4f46e5" name="Lift Ratio" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>

            {/* Association Rules Table */}
            <section className="card">
              <div className="section-header">
                <div>
                  <div className="section-title">
                    <Sparkles size={20} color="var(--primary)" />
                    Mined Association Rules (Cross-Sell Recommendations)
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Identifies product combinations where purchasing items in the <strong>Antecedent</strong> strongly predicts buying the <strong>Consequent</strong>.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    placeholder="Search products in rules..."
                    className="form-input"
                    style={{ width: '220px', padding: '6px 12px', fontSize: '13px' }}
                    value={ruleSearch}
                    onChange={(e) => setRuleSearch(e.target.value)}
                  />
                  <button
                    className="btn-secondary"
                    onClick={handleExportCSV}
                    disabled={isExporting || analysisResult.association_rules.total_count === 0}
                  >
                    <Download size={16} /> {isExporting ? 'Exporting...' : 'Export CSV'}
                  </button>
                </div>
              </div>

              {filteredRules.length > 0 ? (
                <div className="table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th style={{ width: '60px' }}>#</th>
                        <th>Antecedent (Customer Bought)</th>
                        <th style={{ width: '40px', textAlign: 'center' }}></th>
                        <th>Consequent (Recommended Next)</th>
                        <th>Support</th>
                        <th>Confidence</th>
                        <th>Lift</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRules.slice(0, 50).map((rule, idx) => (
                        <tr key={idx}>
                          <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{idx + 1}</td>
                          <td>
                            {rule.antecedent.map((item, i) => (
                              <span key={i} className="item-tag">{item}</span>
                            ))}
                          </td>
                          <td style={{ textAlign: 'center', color: 'var(--primary)' }}>
                            <ArrowRight size={16} />
                          </td>
                          <td>
                            {rule.consequent.map((item, i) => (
                              <span key={i} className="item-tag consequent">{item}</span>
                            ))}
                          </td>
                          <td>
                            <strong>{(rule.support * 100).toFixed(2)}%</strong>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({rule.support_count} orders)</div>
                          </td>
                          <td>
                            <strong style={{ color: rule.confidence_percent >= 70 ? '#059669' : 'var(--text-main)' }}>
                              {rule.confidence_percent.toFixed(1)}%
                            </strong>
                          </td>
                          <td>
                            <span className={`lift-badge ${rule.lift >= 15 ? 'high' : rule.lift >= 5 ? 'medium' : 'standard'}`}>
                              {rule.lift.toFixed(2)}x
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredRules.length > 50 && (
                    <div style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
                      Showing top 50 rules of {filteredRules.length}. Export to CSV to view all rules.
                    </div>
                  )}
                </div>
              ) : (
                <div className="empty-state">
                  <ShoppingCart className="empty-state-icon" />
                  <div className="empty-state-title">No Association Rules Found</div>
                  <div className="empty-state-desc">
                    No rules satisfy the current minimum confidence ({minConfidence}%) and lift ({minLift}x).
                    Try adjusting the parameters in the control panel above.
                  </div>
                </div>
              )}
            </section>

            {/* Frequent Itemsets Table */}
            <section className="card">
              <div className="section-header">
                <div>
                  <div className="section-title">
                    <Layers size={20} color="var(--primary)" />
                    Frequent Itemsets
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Product bundles meeting or exceeding the minimum support threshold ({minSupport}%).
                  </p>
                </div>
                <input
                  type="text"
                  placeholder="Search itemsets..."
                  className="form-input"
                  style={{ width: '220px', padding: '6px 12px', fontSize: '13px' }}
                  value={itemsetSearch}
                  onChange={(e) => setItemsetSearch(e.target.value)}
                />
              </div>

              {filteredItemsets.length > 0 ? (
                <div className="table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th style={{ width: '60px' }}>#</th>
                        <th>Itemset Products</th>
                        <th style={{ width: '100px' }}>Size</th>
                        <th style={{ width: '120px' }}>Basket Count</th>
                        <th style={{ width: '120px' }}>Support %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredItemsets.slice(0, 50).map((itemset, idx) => (
                        <tr key={idx}>
                          <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{idx + 1}</td>
                          <td>
                            {itemset.items.map((item, i) => (
                              <span key={i} className="item-tag">{item}</span>
                            ))}
                          </td>
                          <td>
                            <span className="badge-tag" style={{ fontSize: '11px', padding: '2px 8px' }}>
                              {itemset.size} {itemset.size === 1 ? 'item' : 'items'}
                            </span>
                          </td>
                          <td style={{ fontWeight: 600 }}>{itemset.support_count.toLocaleString()}</td>
                          <td>
                            <strong style={{ color: 'var(--primary-dark)' }}>{itemset.support_percent.toFixed(2)}%</strong>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredItemsets.length > 50 && (
                    <div style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
                      Showing top 50 itemsets of {filteredItemsets.length}.
                    </div>
                  )}
                </div>
              ) : (
                <div className="empty-state">
                  <Layers className="empty-state-icon" />
                  <div className="empty-state-title">No Frequent Itemsets Discovered</div>
                  <div className="empty-state-desc">
                    Lower the minimum support threshold to discover product bundles.
                  </div>
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
