import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-inner">
        {/* Brand column */}
        <div>
          <h3 className="footer-brand-title">
            🧭 YATRA<span>360</span>
          </h3>
          <p className="footer-desc">
            AI-enabled smart tourism platform delivering personalized destination
            recommendations, crowd awareness, safety insights, and explainable multi-criteria scoring.
          </p>
        </div>

        {/* Quick Links */}
        <div>
          <h4 className="footer-col-title">Explore</h4>
          <ul className="footer-links">
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/destinations">Destination Explorer</Link>
            </li>
            <li>
              <Link to="/recommend">Get Recommendations</Link>
            </li>
            <li>
              <a
                href="http://127.0.0.1:8000/api/v1/docs"
                target="_blank"
                rel="noreferrer"
              >
                API Swagger Docs ↗
              </a>
            </li>
          </ul>
        </div>

        {/* Categories */}
        <div>
          <h4 className="footer-col-title">Themes</h4>
          <ul className="footer-links">
            <li>
              <Link to="/destinations?category=Nature">Nature & Scenic</Link>
            </li>
            <li>
              <Link to="/destinations?category=Heritage">Heritage & Culture</Link>
            </li>
            <li>
              <Link to="/destinations?category=Adventure">Adventure Travel</Link>
            </li>
            <li>
              <Link to="/destinations?category=Beach">Coastal & Beaches</Link>
            </li>
            <li>
              <Link to="/destinations?category=Hill%20Station">Hill Stations</Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <span>© 2026 YATRA360 — AI-Enabled Smart Tourism Platform. All rights reserved.</span>
        <span>Grounded on transparent multi-criteria destination scoring formula.</span>
      </div>
    </footer>
  );
}
