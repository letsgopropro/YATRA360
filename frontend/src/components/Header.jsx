import React from 'react';

export default function Header() {
  return (
    <header className="app-header">
      <div className="header-container">
        <div className="brand">
          <span className="brand-logo">🧭</span>
          <span className="brand-name">YATRA360</span>
          <span className="brand-badge">Prototype</span>
        </div>
        <nav className="header-nav">
          <a href="#overview" className="nav-link">Overview</a>
          <a href="#status" className="nav-link">System Status</a>
          <a href="http://127.0.0.1:8000/api/v1/docs" target="_blank" rel="noreferrer" className="nav-link external">
            API Docs ↗
          </a>
        </nav>
      </div>
    </header>
  );
}
