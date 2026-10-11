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
  BarChart2,
  CheckCircle2,
  Search,
  Filter,
  Info
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
  // Backend dataset metadata state
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [loadingDataset, setLoadingDataset] = useState(true);

  // Analysis Configuration States
  const [selectedPreset, setSelectedPreset] = useState('sample_1.7k');
  const [selectedAlgo, setSelectedAlgo] = useState('compare');
  
  // Exact numeric input values
  const [minSupport, setMinSupport] = useState('2.0');
  const [minConfidence, setMinConfidence] = useState('50.0');
  const [minLift, setMinLift] = useState('1.2');

  // Input validation error states
  const [inputErrors, setInputErrors] = useState({});

  // Analysis Execution States
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [serverError, setServerError] = useState(null);

  // Search & Filter state for rules table
  const [ruleSearch, setRuleSearch] = useState('');
  const [itemsetSearch, setItemsetSearch] = useState('');

  // Initial load: Fetch real dataset metadata
  useEffect(() => {
    async function loadDataset() {
      try {
        setLoadingDataset(true);
        const data = await fetchDatasetInfo();
        setDatasetInfo(data);
        setServerError(null);
      } catch (err) {
        setServerError(`Unable to connect to Flask backend (${err.message}). Ensure backend server is running.`);
      } finally {
        setLoadingDataset(false);
      }
    }
    loadDataset();
  }, []);

  // Update default recommended thresholds when user changes dataset preset
  const handlePresetChange = (presetId) => {
    setSelectedPreset(presetId);
    if (presetId === 'toy_5') {
      setMinSupport('60.0');
      setMinConfidence('70.0');
      setMinLift('1.0');
    } else if (presetId === 'full_36k') {
      setMinSupport('1.0');
      setMinConfidence('50.0');
      setMinLift('1.2');
    } else {
      setMinSupport('2.0');
      setMinConfidence('50.0');
      setMinLift('1.2');
    }
    setInputErrors({});
  };

  // Live input validation helper
  const validateInputs = () => {
    const errors = {};

    const supNum = parseFloat(minSupport);
    if (isNaN(supNum) || supNum <= 0 || supNum > 100) {
      errors.support = 'Must be between 0.01% and 100%';
    }

    const confNum = parseFloat(minConfidence);
    if (isNaN(confNum) || confNum <= 0 || confNum > 100) {
      errors.confidence = 'Must be between 0.01% and 100%';
    }

    const liftNum = parseFloat(minLift);
    if (isNaN(liftNum) || liftNum < 0) {
      errors.lift = 'Must be 0.0 or greater';
    }

    setInputErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Run Market Basket Analysis Handler
  const handleRunAnalysis = async () => {
    if (isAnalyzing) return; // Prevent duplicate concurrent submissions

    if (!validateInputs()) {
      return;
    }

    try {
      setIsAnalyzing(true);
      setServerError(null);

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
      setServerError(err.message || 'An unexpected error occurred during analysis.');
      setAnalysisResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Derived filtered rules based on product search
  const activeRules = analysisResult?.association_rules?.rules || [];
  const filteredRules = activeRules.filter(r => {
    const query = ruleSearch.trim().toLowerCase();
    if (!query) return true;
    return (
      r.antecedent.some(item => item.toLowerCase().includes(query)) ||
      r.consequent.some(item => item.toLowerCase().includes(query))
    );
  });

  // Export Association Rules to CSV Handler
  const handleExportCSV = async () => {
    const hasSearch = ruleSearch.trim() !== '';
    if (hasSearch && filteredRules.length === 0) {
      setServerError('No matching rules found to export for the current search filter.');
      return;
    }
    const rulesToExport = hasSearch ? filteredRules : activeRules;
    if (!rulesToExport.length || isExporting) return;
    try {
      setIsExporting(true);
      await exportRulesToCSV(rulesToExport);
    } catch (err) {
      setServerError(`CSV export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  // Derived filtered itemsets based on product search
  const activeItemsets = analysisResult?.frequent_itemsets?.itemsets || [];
  const filteredItemsets = activeItemsets.filter(itemset => {
    const query = itemsetSearch.trim().toLowerCase();
    if (!query) return true;
    return itemset.items.some(name => name.toLowerCase().includes(query));
  });

  // Benchmark chart data
  const chartBenchmarkData = (analysisResult?.benchmark?.apriori_time_seconds != null && analysisResult?.benchmark?.fpgrowth_time_seconds != null)
    ? [
        {
          algorithm: 'Apriori',
          'Execution Time (s)': analysisResult.benchmark.apriori_time_seconds,
          fill: '#4338ca'
        },
        {
          algorithm: 'FP-Growth',
          'Execution Time (s)': analysisResult.benchmark.fpgrowth_time_seconds,
          fill: '#0d9488'
        }
      ]
    : [];

  // Top 8 rules by Lift for visualization
  const chartTopRules = activeRules
    .slice(0, 8)
    .map((r, i) => ({
      name: `R#${i + 1}: ${r.antecedent[0]?.slice(0, 16)}...`,
      lift: r.lift,
      confidence: r.confidence_percent
    }));

  return (
    <div>
      {/* SECTION A: Brand Header & Navigation */}
      <nav className="navbar">
        <div className="brand-wrapper">
          <div className="brand-icon-box">
            <ShoppingBag size={22} />
          </div>
          <div>
            <div className="brand-name">CartInsight Analytics</div>
            <div className="brand-tagline">Retail Market Basket Intelligence</div>
          </div>
        </div>

        <div className="nav-badges">
          <span className="pill-badge primary">
            <ShoppingCart size={13} /> E-Commerce Pattern Mining
          </span>
          <span className="pill-badge neutral">
            College Assignment Project
          </span>
        </div>
      </nav>

      <main className="app-container">
        {/* Server or Connection Error Banner */}
        {serverError && (
          <div className="feedback-box error">
            <AlertCircle size={20} />
            <div>
              <strong>Error Notice:</strong> {serverError}
            </div>
          </div>
        )}

        {/* SECTION A Continued: Introduction Hero */}
        <section className="hero-banner">
          <div className="hero-header-line">
            <Sparkles size={14} /> Market Basket Intelligence & Association Rules
          </div>
          <h1 className="hero-title">Discover High-Impact Product Bundles & Cross-Sell Opportunities</h1>
          <p className="hero-subtitle">
            Market Basket Analysis identifies products that customers frequently purchase together in retail transactions.
            This system runs custom implementations of <strong>Apriori</strong> and <strong>FP-Growth</strong> to calculate
            actual <em>Support</em>, <em>Confidence</em>, and <em>Lift</em> metrics directly from the Online Retail II dataset.
          </p>

          <div className="hero-highlights-grid">
            <div className="hero-highlight-box">
              <div className="hero-highlight-icon">
                <Database size={16} />
              </div>
              <div>
                <div className="hero-highlight-title">Target Dataset</div>
                <div className="hero-highlight-value">Online Retail II (UCI)</div>
              </div>
            </div>

            <div className="hero-highlight-box">
              <div className="hero-highlight-icon">
                <Layers size={16} />
              </div>
              <div>
                <div className="hero-highlight-title">Full Transactions</div>
                <div className="hero-highlight-value">1,067,371 records</div>
              </div>
            </div>

            <div className="hero-highlight-box">
              <div className="hero-highlight-icon">
                <CheckCircle2 size={16} />
              </div>
              <div>
                <div className="hero-highlight-title">Algorithm Validation</div>
                <div className="hero-highlight-value">Pure Custom vs mlxtend</div>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION B: Dataset Overview */}
        <section className="section-card">
          <div className="card-title-row">
            <div className="card-title">
              <Database className="card-title-icon" size={19} />
              Dataset Overview & Transaction Repositories
            </div>
            <span className="card-caption">Verified transactional statistics from backend API</span>
          </div>

          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
            The raw Online Retail II dataset contains international gift and lifestyle retail transactions. Preprocessing filters cancelled invoices, removes invalid quantities, and groups products into unique shopping baskets. Select an evaluation scope below:
          </p>

          <div className="dataset-tiles-grid">
            {/* Tile 1: Fast Sample */}
            <div className={`dataset-tile ${selectedPreset === 'sample_1.7k' ? 'active' : ''}`}>
              <div className="dataset-tile-header">
                <span className="dataset-tile-title">Fast Retail Sample</span>
                <span className="pill-badge primary" style={{ fontSize: '10px', padding: '2px 8px' }}>Recommended Demo</span>
              </div>
              <div className="dataset-tile-count">1,710 Baskets</div>
              <div className="dataset-tile-desc">
                Balanced retail sample (~50k raw rows) capturing top seasonal products. Provides fast sub-second execution for FP-Growth and ~10–20s for Apriori.
              </div>
            </div>

            {/* Tile 2: Full Cleaned Dataset */}
            <div className={`dataset-tile ${selectedPreset === 'full_36k' ? 'active' : ''}`}>
              <div className="dataset-tile-header">
                <span className="dataset-tile-title">Full Cleaned Dataset</span>
                <span className="pill-badge neutral" style={{ fontSize: '10px', padding: '2px 8px' }}>Comprehensive</span>
              </div>
              <div className="dataset-tile-count">36,307 Baskets</div>
              <div className="dataset-tile-desc">
                All multi-item transactions extracted from the full 1.06M raw records across the 2-year retail period (5,336 unique catalog items).
              </div>
            </div>

            {/* Tile 3: Textbook Dataset */}
            <div className={`dataset-tile ${selectedPreset === 'toy_5' ? 'active' : ''}`}>
              <div className="dataset-tile-header">
                <span className="dataset-tile-title">Textbook Verification Sample</span>
                <span className="pill-badge neutral" style={{ fontSize: '10px', padding: '2px 8px' }}>Correctness Test</span>
              </div>
              <div className="dataset-tile-count">5 Baskets</div>
              <div className="dataset-tile-desc">
                Standard 5-transaction textbook example (Bread, Milk, Diaper, Beer) with manually verified ground-truth values for professor evaluation.
              </div>
            </div>
          </div>
        </section>

        {/* SECTION C: Analysis Configuration */}
        <section className="section-card">
          <div className="card-title-row">
            <div className="card-title">
              <Sliders className="card-title-icon" size={19} />
              Analysis Parameters & Algorithm Configuration
            </div>
            <span className="card-caption">Configure exact mathematical thresholds</span>
          </div>

          <div className="config-grid">
            {/* Dataset Scale Selector */}
            <div className="form-field">
              <label className="field-label" htmlFor="dataset-preset-select">
                <span>Dataset Scale</span>
                <span className="field-hint">Scope of Baskets</span>
              </label>
              <select
                id="dataset-preset-select"
                className="form-select"
                value={selectedPreset}
                onChange={(e) => handlePresetChange(e.target.value)}
                disabled={isAnalyzing}
              >
                <option value="sample_1.7k">Fast Retail Sample (1,710 Baskets - Recommended)</option>
                <option value="full_36k">Full Cleaned Retail Dataset (36,307 Baskets)</option>
                <option value="toy_5">Textbook Verification Dataset (5 Baskets)</option>
              </select>
            </div>

            {/* Algorithm Selector */}
            <div className="form-field">
              <label className="field-label">
                <span>Algorithm Selection</span>
                <span className="field-hint">Mining Engine</span>
              </label>
              <div className="segmented-picker">
                <button
                  type="button"
                  className={`segmented-option ${selectedAlgo === 'apriori' ? 'active' : ''}`}
                  onClick={() => setSelectedAlgo('apriori')}
                  disabled={isAnalyzing}
                >
                  Apriori
                </button>
                <button
                  type="button"
                  className={`segmented-option ${selectedAlgo === 'fpgrowth' ? 'active' : ''}`}
                  onClick={() => setSelectedAlgo('fpgrowth')}
                  disabled={isAnalyzing}
                >
                  FP-Growth
                </button>
                <button
                  type="button"
                  className={`segmented-option ${selectedAlgo === 'compare' ? 'active' : ''}`}
                  onClick={() => setSelectedAlgo('compare')}
                  disabled={isAnalyzing}
                >
                  Compare Both
                </button>
              </div>
            </div>

            {/* Minimum Support Numeric Input */}
            <div className="form-field">
              <label className="field-label" htmlFor="input-support">
                <span>Minimum Support</span>
                <span className="field-hint">Frequency Threshold</span>
              </label>
              <div className="input-affix-group">
                <input
                  id="input-support"
                  type="number"
                  className={`form-input ${inputErrors.support ? 'error' : ''}`}
                  step="0.1"
                  min="0.01"
                  max="100"
                  value={minSupport}
                  onChange={(e) => setMinSupport(e.target.value)}
                  onBlur={validateInputs}
                  disabled={isAnalyzing}
                  placeholder="e.g. 2.0"
                />
                <span className="input-affix">%</span>
              </div>
              {inputErrors.support && <span className="field-error-msg">{inputErrors.support}</span>}
            </div>

            {/* Minimum Confidence Numeric Input */}
            <div className="form-field">
              <label className="field-label" htmlFor="input-confidence">
                <span>Minimum Confidence</span>
                <span className="field-hint">Rule Reliability</span>
              </label>
              <div className="input-affix-group">
                <input
                  id="input-confidence"
                  type="number"
                  className={`form-input ${inputErrors.confidence ? 'error' : ''}`}
                  step="1"
                  min="0.01"
                  max="100"
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(e.target.value)}
                  onBlur={validateInputs}
                  disabled={isAnalyzing}
                  placeholder="e.g. 50"
                />
                <span className="input-affix">%</span>
              </div>
              {inputErrors.confidence && <span className="field-error-msg">{inputErrors.confidence}</span>}
            </div>

            {/* Minimum Lift Numeric Input */}
            <div className="form-field">
              <label className="field-label" htmlFor="input-lift">
                <span>Minimum Lift</span>
                <span className="field-hint">Strength of Association</span>
              </label>
              <div className="input-affix-group">
                <input
                  id="input-lift"
                  type="number"
                  className={`form-input ${inputErrors.lift ? 'error' : ''}`}
                  step="0.1"
                  min="0"
                  value={minLift}
                  onChange={(e) => setMinLift(e.target.value)}
                  onBlur={validateInputs}
                  disabled={isAnalyzing}
                  placeholder="e.g. 1.2"
                />
                <span className="input-affix">ratio</span>
              </div>
              {inputErrors.lift && <span className="field-error-msg">{inputErrors.lift}</span>}
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="action-toolbar">
            <div className="action-status-hint">
              <Info size={15} />
              <span>
                {selectedAlgo === 'compare'
                  ? 'Both Apriori and FP-Growth will execute on the exact same transactions.'
                  : `Running custom ${selectedAlgo === 'apriori' ? 'Apriori' : 'FP-Growth'} mining engine.`}
              </span>
            </div>

            <button
              className="btn-run"
              onClick={handleRunAnalysis}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <Clock size={16} className="animate-spin" /> Computing Patterns...
                </>
              ) : (
                <>
                  <Play size={16} /> Run Market Basket Analysis
                </>
              )}
            </button>
          </div>
        </section>

        {/* SECTION D: Results Dashboard */}
        {analysisResult && (
          <>
            {/* KPI Summary Tiles */}
            <div className="kpi-row">
              <div className="kpi-tile">
                <div className="kpi-tile-icon indigo">
                  <ShoppingCart size={22} />
                </div>
                <div>
                  <div className="kpi-tile-value">
                    {analysisResult.parameters.baskets_analyzed.toLocaleString()}
                  </div>
                  <div className="kpi-tile-label">Baskets Analyzed</div>
                </div>
              </div>

              <div className="kpi-tile">
                <div className="kpi-tile-icon teal">
                  <Layers size={22} />
                </div>
                <div>
                  <div className="kpi-tile-value">
                    {analysisResult.frequent_itemsets.total_count.toLocaleString()}
                  </div>
                  <div className="kpi-tile-label">Frequent Itemsets</div>
                </div>
              </div>

              <div className="kpi-tile">
                <div className="kpi-tile-icon amber">
                  <Sparkles size={22} />
                </div>
                <div>
                  <div className="kpi-tile-value">
                    {analysisResult.association_rules.total_count.toLocaleString()}
                  </div>
                  <div className="kpi-tile-label">Association Rules</div>
                </div>
              </div>

              <div className="kpi-tile">
                <div className="kpi-tile-icon violet">
                  <Clock size={22} />
                </div>
                <div>
                  <div className="kpi-tile-value">
                    {analysisResult.parameters.algorithm === 'compare'
                      ? `${analysisResult.benchmark.fpgrowth_time_seconds}s`
                      : `${analysisResult.frequent_itemsets.execution_time_seconds}s`}
                  </div>
                  <div className="kpi-tile-label">
                    {analysisResult.parameters.algorithm === 'compare' ? 'FP-Growth Runtime' : 'Execution Runtime'}
                  </div>
                </div>
              </div>
            </div>

            {/* Visualizations Section */}
            <div className="viz-grid">
              {/* Chart 1: Performance Benchmark (Visible when Compare Both is chosen) */}
              {chartBenchmarkData.length > 0 && (
                <div className="viz-card">
                  <div className="viz-card-header">
                    <span className="viz-card-title">Algorithm Runtime Benchmark</span>
                    <span className="pill-badge" style={{ backgroundColor: 'var(--teal-light)', color: 'var(--teal-hover)' }}>
                      {analysisResult.benchmark.speedup_factor}x Speedup
                    </span>
                  </div>
                  <div style={{ height: 260 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartBenchmarkData} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis type="number" unit="s" />
                        <YAxis type="category" dataKey="algorithm" />
                        <Tooltip formatter={(value) => [`${value}s`, 'Runtime']} />
                        <Bar dataKey="Execution Time (s)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Chart 2: Top Association Rules by Lift */}
              {chartTopRules.length > 0 && (
                <div className="viz-card">
                  <div className="viz-card-header">
                    <span className="viz-card-title">Top Association Rules by Lift Ratio</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Cross-Sell Strength</span>
                  </div>
                  <div style={{ height: 260 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartTopRules} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="name" angle={-25} textAnchor="end" height={50} interval={0} fontSize={11} />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="lift" fill="#4338ca" name="Lift Ratio" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION E: Association Rules & Filtering */}
            <section className="section-card">
              <div className="card-title-row">
                <div>
                  <div className="card-title">
                    <Sparkles className="card-title-icon" size={19} />
                    Mined Association Rules (Product Recommendations)
                  </div>
                  <span className="card-caption">
                    Customers who bought items in the <strong>Antecedent</strong> are likely to also purchase the <strong>Consequent</strong>.
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Search product in rules..."
                      value={ruleSearch}
                      onChange={(e) => setRuleSearch(e.target.value)}
                      style={{ paddingLeft: '32px', width: '230px', paddingRight: '10px', fontSize: '13px' }}
                    />
                    <Search size={15} style={{ position: 'absolute', left: '10px', top: '11px', color: '#94a3b8' }} />
                  </div>

                  <button
                    className="btn-export"
                    onClick={handleExportCSV}
                    disabled={isExporting || (ruleSearch.trim() !== '' ? filteredRules.length === 0 : activeRules.length === 0)}
                  >
                    <Download size={15} />
                    {isExporting ? 'Exporting...' : 'Export CSV'}
                  </button>
                </div>
              </div>

              {filteredRules.length > 0 ? (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th style={{ width: '50px' }}>#</th>
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
                              <span key={i} className="product-tag">{item}</span>
                            ))}
                          </td>
                          <td style={{ textAlign: 'center', color: 'var(--primary)' }}>
                            <ArrowRight size={15} />
                          </td>
                          <td>
                            {rule.consequent.map((item, i) => (
                              <span key={i} className="product-tag consequent">{item}</span>
                            ))}
                          </td>
                          <td>
                            <span className="metric-highlight">{(rule.support * 100).toFixed(2)}%</span>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({rule.support_count} baskets)</div>
                          </td>
                          <td>
                            <span className="metric-highlight" style={{ color: rule.confidence_percent >= 70 ? 'var(--emerald)' : 'var(--navy-900)' }}>
                              {rule.confidence_percent.toFixed(1)}%
                            </span>
                          </td>
                          <td>
                            <span className={`lift-pill ${rule.lift >= 15 ? 'high' : rule.lift >= 5 ? 'medium' : 'standard'}`}>
                              {rule.lift.toFixed(2)}x
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredRules.length > 50 && (
                    <div style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', backgroundColor: '#f8fafc' }}>
                      Showing top 50 rules of {filteredRules.length}. Click 'Export CSV' to download all mined rules.
                    </div>
                  )}
                </div>
              ) : (
                <div className="state-empty">
                  <ShoppingCart className="state-empty-icon" />
                  <div className="state-empty-title">No Matching Association Rules</div>
                  <div className="state-empty-text">
                    {ruleSearch ? (
                      `No rules found matching "${ruleSearch}". Try clearing your search keyword.`
                    ) : (
                      `No rules satisfy Minimum Confidence of ${minConfidence}% and Minimum Lift of ${minLift}x. Try lowering these thresholds in the controls above.`
                    )}
                  </div>
                </div>
              )}
            </section>

            {/* Frequent Itemsets Table */}
            <section className="section-card">
              <div className="card-title-row">
                <div>
                  <div className="card-title">
                    <Layers className="card-title-icon" size={19} />
                    Discovered Frequent Itemsets
                  </div>
                  <span className="card-caption">
                    Product combinations meeting or exceeding Minimum Support ({minSupport}%).
                  </span>
                </div>

                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search itemsets..."
                    value={itemsetSearch}
                    onChange={(e) => setItemsetSearch(e.target.value)}
                    style={{ paddingLeft: '32px', width: '220px', paddingRight: '10px', fontSize: '13px' }}
                  />
                  <Search size={15} style={{ position: 'absolute', left: '10px', top: '11px', color: '#94a3b8' }} />
                </div>
              </div>

              {filteredItemsets.length > 0 ? (
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th style={{ width: '50px' }}>#</th>
                        <th>Product Items</th>
                        <th style={{ width: '100px' }}>Itemset Size</th>
                        <th style={{ width: '140px' }}>Basket Support Count</th>
                        <th style={{ width: '120px' }}>Support %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredItemsets.slice(0, 50).map((itemset, idx) => (
                        <tr key={idx}>
                          <td style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{idx + 1}</td>
                          <td>
                            {itemset.items.map((item, i) => (
                              <span key={i} className="product-tag">{item}</span>
                            ))}
                          </td>
                          <td>
                            <span className="pill-badge neutral" style={{ fontSize: '11px', padding: '2px 8px' }}>
                              {itemset.size} {itemset.size === 1 ? 'item' : 'items'}
                            </span>
                          </td>
                          <td style={{ fontWeight: 600 }}>
                            {itemset.support_count.toLocaleString()}
                          </td>
                          <td>
                            <span className="metric-highlight" style={{ color: 'var(--primary)' }}>
                              {itemset.support_percent.toFixed(2)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredItemsets.length > 50 && (
                    <div style={{ padding: '12px 16px', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', backgroundColor: '#f8fafc' }}>
                      Showing top 50 itemsets of {filteredItemsets.length}.
                    </div>
                  )}
                </div>
              ) : (
                <div className="state-empty">
                  <Layers className="state-empty-icon" />
                  <div className="state-empty-title">No Frequent Itemsets Found</div>
                  <div className="state-empty-text">
                    No product bundles meet the current Minimum Support threshold of {minSupport}%. Try entering a lower percentage.
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
