import React, { useState, useEffect } from 'react';
import { getHealthStatus } from '../api/healthService';

export default function Home() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHealthStatus();
      setHealth(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <main className="main-content">
      {/* Hero Section */}
      <section className="hero-section" id="overview">
        <h1 className="hero-title">AI-Enabled Smart Tourism Platform</h1>
        <p className="hero-subtitle">
          Personalized destination discovery, crowd forecasting, explainable scoring,
          and dynamic itinerary planning for travelers.
        </p>
      </section>

      {/* Backend & Database Connectivity Card */}
      <section className="status-section" id="status">
        <div className="card status-card">
          <div className="card-header">
            <h2>System Health & Connectivity</h2>
            <button
              onClick={fetchHealth}
              disabled={loading}
              className="refresh-btn"
              title="Re-check API status"
            >
              {loading ? 'Checking...' : 'Refresh Status'}
            </button>
          </div>

          <div className="card-body">
            {loading && (
              <div className="status-indicator loading">
                <span className="dot pulse"></span>
                <span>Connecting to backend API...</span>
              </div>
            )}

            {error && (
              <div className="status-indicator error">
                <span className="dot error-dot"></span>
                <div>
                  <strong>Backend Connection Failed</strong>
                  <p className="error-text">{error}</p>
                  <p className="hint-text">
                    Ensure FastAPI is running: <code>python run.py</code> inside <code>backend/</code>.
                  </p>
                </div>
              </div>
            )}

            {health && (
              <div className="status-grid">
                <div className="status-item">
                  <span className="status-label">Backend Status</span>
                  <span className={`status-pill ${health.status === 'healthy' ? 'pill-green' : 'pill-yellow'}`}>
                    {health.status.toUpperCase()}
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">Service Name</span>
                  <span className="status-value">{health.app_name}</span>
                </div>
                <div className="status-item">
                  <span className="status-label">API Version</span>
                  <span className="status-value">v{health.version}</span>
                </div>
                <div className="status-item">
                  <span className="status-label">Database Connected</span>
                  <span className={`status-pill ${health.database_connected ? 'pill-green' : 'pill-yellow'}`}>
                    {health.database_connected ? 'Connected' : 'Pending / Disconnected'}
                  </span>
                </div>
                <div className="status-item full-width">
                  <span className="status-label">Database Diagnostics</span>
                  <span className="status-mono">{health.database_status}</span>
                </div>
                <div className="status-item full-width">
                  <span className="status-label">Server Timestamp</span>
                  <span className="status-mono">{new Date(health.timestamp).toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Planned Modules Overview */}
      <section className="modules-section">
        <h2 className="section-title">Core Architecture Modules (Roadmap)</h2>
        <div className="modules-grid">
          <div className="module-card">
            <div className="module-icon">🔐</div>
            <h3>Authentication & Roles</h3>
            <p>JWT auth with role-based access for tourists, business owners, and admins.</p>
            <span className="module-tag">Next Phase</span>
          </div>
          <div className="module-card">
            <div className="module-icon">📍</div>
            <h3>Destinations & Database</h3>
            <p>PostgreSQL schema for tourist sites, attractions, categories, and tags.</p>
            <span className="module-tag">Next Phase</span>
          </div>
          <div className="module-card">
            <div className="module-icon">⚖️</div>
            <h3>Transparent Scoring Engine</h3>
            <p>Normalized multi-factor formula balancing preference, crowd, safety, cost & weather.</p>
            <span className="module-tag">Planned</span>
          </div>
          <div className="module-card">
            <div className="module-icon">👥</div>
            <h3>Crowd & Alternative Engine</h3>
            <p>Detect overcrowding patterns and recommend lesser-known hidden gems.</p>
            <span className="module-tag">Planned</span>
          </div>
          <div className="module-card">
            <div className="module-icon">🗺️</div>
            <h3>Map & Weather Integration</h3>
            <p>Interactive Leaflet/OSM map layer with live/simulated weather overlays.</p>
            <span className="module-tag">Planned</span>
          </div>
          <div className="module-card">
            <div className="module-icon">📅</div>
            <h3>Smart Itinerary Planner</h3>
            <p>Generate day-by-day itineraries tailored to duration and traveler preferences.</p>
            <span className="module-tag">Planned</span>
          </div>
        </div>
      </section>
    </main>
  );
}
