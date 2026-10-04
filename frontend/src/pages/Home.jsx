import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getHealthStatus } from '../api/healthService';
import { listDestinations } from '../api/destinationService';
import DestinationCard from '../components/DestinationCard';
import { DEFAULT_TRAVEL_HERO } from '../utils/imageHelper';

export default function Home() {
  const navigate = useNavigate();
  const [searchKeyword, setSearchKeyword] = useState('');
  const [featuredDestinations, setFeaturedDestinations] = useState([]);
  const [health, setHealth] = useState(null);
  const [showHealthDetails, setShowHealthDetails] = useState(false);

  useEffect(() => {
    // Fetch live system health status
    getHealthStatus()
      .then((data) => setHealth(data))
      .catch((err) => {
        console.warn('Health check issue:', err.message);
        setHealth({ status: 'offline', database_connected: false });
      });

    // Fetch featured destinations for preview
    listDestinations({ limit: 4 })
      .then((data) => {
        if (Array.isArray(data)) {
          setFeaturedDestinations(data);
        }
      })
      .catch((err) => {
        console.warn('Featured destinations fetch error:', err.message);
      });
  }, []);

  const handleHeroSearch = (e) => {
    e.preventDefault();
    if (searchKeyword.trim()) {
      navigate(`/destinations?search=${encodeURIComponent(searchKeyword.trim())}`);
    } else {
      navigate('/destinations');
    }
  };

  return (
    <div className="main-content">
      {/* ===================================================================
          CINEMATIC HERO (Inspiration A / Editorial Travel Aesthetic)
          =================================================================== */}
      <section className="cinematic-hero">
        <img
          src={DEFAULT_TRAVEL_HERO}
          alt="Majestic Indian Mountain Landscape at Dawn"
          className="hero-background-img"
        />
        <div className="hero-gradient-overlay"></div>

        <div className="hero-content">
          <span className="hero-tag">🧭 AI-Enabled Smart Tourism</span>

          <h1 className="hero-editorial-title">
            Find destinations that fit the way you travel.
          </h1>

          <p className="hero-description">
            YATRA360 combines your personal preferences with destination conditions,
            crowd levels, safety information and cost suitability to help you discover where to go next.
          </p>

          <div className="hero-cta-group">
            <Link to="/recommend" className="cta-btn-primary">
              Begin Your Journey →
            </Link>
            <Link to="/destinations" className="cta-btn-secondary">
              Explore Destinations
            </Link>
          </div>

          {/* Quick Search Bar */}
          <form onSubmit={handleHeroSearch} className="hero-quick-search">
            <span>🔍</span>
            <input
              type="text"
              placeholder="Where would you like to go? (e.g. Manali, beaches, temples)..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              aria-label="Search destination"
            />
            <button type="submit">Search</button>
          </form>
        </div>
      </section>

      {/* ===================================================================
          CORE VALUE PROPOSITIONS / FEATURES SECTION
          =================================================================== */}
      <section className="features-section">
        <div className="section-container">
          <div className="section-header">
            <span className="section-eyebrow">Smart Travel Intelligence</span>
            <h2 className="section-title">Designed for modern conscious travelers</h2>
            <p className="section-subtitle">
              Move beyond generic lists. YATRA360 uses explainable multi-criteria scoring
              to match your journey with verified destinations.
            </p>
          </div>

          <div className="features-grid">
            {/* Feature 1 */}
            <div className="feature-card">
              <div className="feature-icon-wrapper">🎯</div>
              <h3 className="feature-title">Personalized Recommendations</h3>
              <p className="feature-desc">
                Destinations shaped around your exact interests, budget constraints, travel
                duration, group composition, and accessibility requirements.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="feature-card">
              <div className="feature-icon-wrapper">👥</div>
              <h3 className="feature-title">Crowd-Aware Travel</h3>
              <p className="feature-desc">
                Avoid seasonal overcrowding. Discover serene, high-similarity alternatives
                that deliver the same wonder with lower visitor pressure.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="feature-card">
              <div className="feature-icon-wrapper">🛡️</div>
              <h3 className="feature-title">Safety Insights</h3>
              <p className="feature-desc">
                Access transparent safety ratings, local advisories, and emergency helpline
                directories before finalizing your trip itinerary.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="feature-card">
              <div className="feature-icon-wrapper">🌿</div>
              <h3 className="feature-title">Discover Hidden Gems</h3>
              <p className="feature-desc">
                Explore handpicked offbeat sanctuaries and heritage sites that preserve
                authentic local character away from tourist congestions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================================
          FEATURED DESTINATIONS PREVIEW
          =================================================================== */}
      {featuredDestinations.length > 0 && (
        <section style={{ padding: '4rem 1.5rem', backgroundColor: '#ffffff' }}>
          <div className="section-container">
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-end',
                justifyContent: 'space-between',
                marginBottom: '2rem',
                flexWrap: 'wrap',
                gap: '1rem',
              }}
            >
              <div>
                <span className="section-eyebrow">Curated Across India</span>
                <h2 className="section-title" style={{ margin: 0 }}>
                  Featured Destinations
                </h2>
              </div>
              <Link
                to="/destinations"
                style={{
                  color: 'var(--accent-blue)',
                  fontWeight: 600,
                  textDecoration: 'none',
                  fontSize: '0.95rem',
                }}
              >
                View all destinations ({featuredDestinations.length}+) →
              </Link>
            </div>

            <div className="destinations-grid">
              {featuredDestinations.map((destination) => (
                <DestinationCard key={destination.id} destination={destination} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ===================================================================
          SYSTEM STATUS SECTION (Subtle & Non-Dominating)
          =================================================================== */}
      <section style={{ padding: '0 1.5rem 3rem', backgroundColor: '#ffffff' }}>
        <div className="system-status-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span
              className={`status-live-dot ${
                health?.status === 'healthy' || health?.database_connected ? '' : 'offline'
              }`}
            ></span>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
              {health?.status === 'healthy' || health?.database_connected
                ? 'API Connected • All systems operational'
                : 'Connecting to YATRA360 Backend...'}
            </span>
          </div>

          <button
            type="button"
            onClick={() => setShowHealthDetails(!showHealthDetails)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '0.8rem',
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            {showHealthDetails ? 'Hide Diagnostics' : 'View Diagnostics'}
          </button>
        </div>

        {/* Expandable Health Diagnostic Details */}
        {showHealthDetails && health && (
          <div
            style={{
              maxWidth: '600px',
              margin: '1rem auto 0 auto',
              padding: '1.25rem',
              backgroundColor: 'var(--bg-subtle)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-light)',
              fontSize: '0.85rem',
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem' }}>
              <div>
                <strong>Service:</strong> {health.app_name || 'YATRA360 API'}
              </div>
              <div>
                <strong>Version:</strong> v{health.version || '0.1.0'}
              </div>
              <div>
                <strong>Database:</strong>{' '}
                <span
                  style={{
                    color: health.database_connected ? 'var(--emerald-700)' : 'var(--rose-700)',
                    fontWeight: 600,
                  }}
                >
                  {health.database_connected ? 'Connected' : 'Offline'}
                </span>
              </div>
              <div>
                <strong>Status:</strong> {health.status}
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
