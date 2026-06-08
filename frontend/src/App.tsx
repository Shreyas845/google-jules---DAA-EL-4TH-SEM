import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Activity, BarChart2, Server, Folder, PlayCircle } from 'lucide-react';
import './App.css';

const API_URL = 'http://127.0.0.1:8000/api';

const Sidebar = () => (
  <div className="sidebar">
    <h2>ISL Dashboard</h2>
    <nav>
      <ul>
        <li><Link to="/"><Activity size={18} /> Overview</Link></li>
        <li><Link to="/validations"><BarChart2 size={18} /> Validations</Link></li>
        <li><Link to="/experiments"><PlayCircle size={18} /> Experiments</Link></li>
        <li><Link to="/graph"><Folder size={18} /> Graph Viewer</Link></li>
      </ul>
    </nav>
  </div>
);

const Overview = () => (
  <div className="content">
    <h1>Project Overview</h1>
    <p>Welcome to the Incremental Significance-Leiden (ISL) research dashboard.</p>

    <h2>Architecture Overview</h2>
    <div className="architecture-grid">
      <div className="arch-card">
        <h3>Graph Engine</h3>
        <p>Manages igraph structure and edge streams.</p>
        <span className="status operational">Operational</span>
      </div>
      <div className="arch-card">
        <h3>Community State</h3>
        <p>Tracks sigma, M, p, and dwell counters.</p>
        <span className="status operational">Operational</span>
      </div>
      <div className="arch-card">
        <h3>Local Moves Engine</h3>
        <p>O(d_v) localized optimization.</p>
        <span className="status operational">Operational</span>
      </div>
      <div className="arch-card">
        <h3>Periodic Recompute</h3>
        <p>Gap recovery mechanism.</p>
        <span className="status operational">Operational</span>
      </div>
      <div className="arch-card">
        <h3>Experiment Runner</h3>
        <p>Benchmarks and aggregations.</p>
        <span className="status operational">Operational</span>
      </div>
    </div>
  </div>
);

const Validations = () => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    axios.get(`${API_URL}/validations`).then(res => setData(res.data));
  }, []);

  if (!data) return <div className="content">Loading validations...</div>;

  return (
    <div className="content">
      <h1>Validation Result Explorer</h1>

      <div className="validation-section">
        <h2>Validation A: Approximation Accuracy</h2>
        <img src={`${API_URL}/images/validation_a_plot.png`} alt="Validation A" className="plot" />
        <p>Result: <strong>FAIL</strong> (Under Surprise), leading to methodology shift.</p>
      </div>

      <div className="validation-section">
        <h2>Validation B: Warm-Start Effectiveness</h2>
        <div className="plots-row">
          <img src={`${API_URL}/images/validation_b_significance_nmi_plot.png`} alt="Val B NMI" className="plot half" />
          <img src={`${API_URL}/images/validation_b_significance_speedup_plot.png`} alt="Val B Speedup" className="plot half" />
        </div>
        <p>Result: <strong>Speedup bounded</strong>, but partition stability is exceptionally high (NMI ~ 1.0).</p>
      </div>

      <div className="validation-section">
        <h2>Validation C: Over-Partitioning Bias</h2>
        <div className="plots-row">
          <img src={`${API_URL}/images/validation_c_significance_community_count_plot.png`} alt="Val C Count" className="plot half" />
          <img src={`${API_URL}/images/validation_c_significance_nmi_plot.png`} alt="Val C NMI" className="plot half" />
        </div>
        <p>Result: <strong>PASS</strong> (Using Significance).</p>
      </div>
    </div>
  );
};

const Experiments = () => {
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<any>(null);

  const runExperiment = () => {
    setRunning(true);
    axios.post(`${API_URL}/experiment/run`, {
      n: 5000,
      mu: 0.1,
      min_community: 20,
      max_community: 100,
      algorithm: 'isl_1hop'
    }).then(res => {
      setTimeout(() => {
        axios.get(`${API_URL}/experiment/status/${res.data.job_id}`).then(s => {
          setStatus(s.data);
          setRunning(false);
        });
      }, 2000);
    });
  };

  return (
    <div className="content">
      <h1>Experiment Configuration</h1>
      <div className="config-panel">
        <div>
          <label>Algorithm Variant</label>
          <select><option>ISL-1hop</option><option>ISL-adaptive</option></select>
        </div>
        <div>
          <label>Graph Size (n)</label>
          <input type="number" defaultValue={5000} />
        </div>
        <button onClick={runExperiment} disabled={running}>
          {running ? 'Running...' : 'Start Experiment'}
        </button>
      </div>

      {status && (
        <div className="status-panel">
          <h3>Run Status: {status.status}</h3>
          <p>Progress: {status.progress}%</p>
          <p>Final NMI: {status.results.nmi}</p>
        </div>
      )}
    </div>
  );
};

const GraphViewer = () => (
  <div className="content">
    <h1>Graph Upload & Visualization</h1>
    <div className="placeholder-box">
      <Server size={48} className="icon-placeholder" />
      <p>Graph upload functionality awaiting backend completion.</p>
      <p className="mock-label">Placeholder Data</p>
    </div>

    <h2>Community Visualization</h2>
    <div className="placeholder-box">
      <Server size={48} className="icon-placeholder" />
      <p>Incremental update simulation visualization awaiting backend completion.</p>
    </div>
  </div>
);

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/validations" element={<Validations />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/graph" element={<GraphViewer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
