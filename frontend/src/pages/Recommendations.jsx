import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { getRecommendations, getAlternativesForDestination } from '../api/recommendationService';
import RecommendationCard from '../components/RecommendationCard';
import AlternativeDestinationCard from '../components/AlternativeDestinationCard';
import { LoadingSpinner } from '../components/LoadingState';
import ErrorState from '../components/ErrorState';

export default function Recommendations() {
  const location = useLocation();

  const [recommendationsData, setRecommendationsData] = useState(
    location.state?.recommendationsData || null
  );
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Alternative destinations modal/state
  const [activeAlternativeModal, setActiveAlternativeModal] = useState(null);
  const [loadingAlternatives, setLoadingAlternatives] = useState(false);

  useEffect(() => {
    // If state was not passed via navigation, check sessionStorage
    if (!recommendationsData) {
      const cached = sessionStorage.getItem('yatra360_recommendations');
      if (cached) {
        try {
          setRecommendationsData(JSON.parse(cached));
          return;
        } catch {
          // ignore parse error
        }
      }

      // If no cached recommendations, fetch default personalized recommendations
      setLoading(true);
      getRecommendations({
        interests: ['Nature', 'Heritage'],
        budget: 15000,
        limit: 10,
        apply_diversity: true,
      })
        .then((data) => {
          setRecommendationsData(data);
          sessionStorage.setItem('yatra360_recommendations', JSON.stringify(data));
        })
        .catch((err) => {
          setError(err.message || 'Failed to load recommendations.');
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [recommendationsData]);

  const handleFindAlternatives = async (recommendation) => {
    setLoadingAlternatives(true);
    try {
      const altData = await getAlternativesForDestination(
        recommendation.destination_id,
        4
      );
      setActiveAlternativeModal(altData);
    } catch (err) {
      console.warn('Failed to fetch alternatives:', err.message);
    } finally {
      setLoadingAlternatives(false);
    }
  };

  if (loading) {
    return (
      <div className="main-content" style={{ padding: '6rem 1.5rem' }}>
        <LoadingSpinner message="Calculating personalized suitability scores & ranking destinations..." />
      </div>
    );
  }

  if (error && !recommendationsData) {
    return (
      <div className="main-content" style={{ padding: '6rem 1.5rem' }}>
        <ErrorState
          title="Could not generate recommendations"
          message={error}
          onRetry={() => {
            setError(null);
            setLoading(true);
            getRecommendations({ limit: 10 }).then(setRecommendationsData).finally(() => setLoading(false));
          }}
        />
      </div>
    );
  }

  const items = recommendationsData?.recommendations || [];

  // Available categories in results
  const categoriesInResults = ['All', ...new Set(items.map((it) => it.category))];

  // Filter items in memory by selectedCategory
  const filteredItems =
    selectedCategory === 'All'
      ? items
      : items.filter((it) => it.category === selectedCategory);

  return (
    <div className="main-content">
      <div className="page-container">
        {/* Header */}
        <div className="recommendations-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1 className="recommendations-title">Your Personalized Recommendations</h1>
              <p className="recommendations-subtitle">
                Based on your preferences, here are the destinations that best fit your trip.
              </p>
            </div>
            <Link
              to="/recommend"
              className="state-action-btn"
              style={{ padding: '0.6rem 1.2rem', fontSize: '0.9rem' }}
            >
              ⚙️ Adjust Preferences
            </Link>
          </div>

          {/* Category filter chips */}
          <div className="filter-chips-group" style={{ marginTop: '1.25rem' }}>
            {categoriesInResults.map((cat) => {
              const count =
                cat === 'All'
                  ? items.length
                  : items.filter((it) => it.category === cat).length;
              return (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`filter-chip ${selectedCategory === cat ? 'active' : ''}`}
                >
                  {cat} ({count})
                </button>
              );
            })}
          </div>
        </div>

        {/* Results List */}
        {loadingAlternatives && (
          <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--accent-blue)', fontWeight: 600 }}>
            Analyzing alternative destinations with lower crowd pressure...
          </div>
        )}

        {filteredItems.length === 0 ? (
          <div className="state-container">
            <h3 className="state-title">No recommendations match category "{selectedCategory}"</h3>
            <p className="state-text">Select "All" to view all ranked recommendations.</p>
            <button
              onClick={() => setSelectedCategory('All')}
              className="state-action-btn"
            >
              View All Recommendations
            </button>
          </div>
        ) : (
          <div className="recommendations-list">
            {filteredItems.map((rec) => (
              <RecommendationCard
                key={rec.destination_id}
                recommendation={rec}
                onFindAlternatives={handleFindAlternatives}
              />
            ))}
          </div>
        )}

        {/* Modal / Overlay for Alternatives */}
        {activeAlternativeModal && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(15, 23, 42, 0.75)',
              backdropFilter: 'blur(8px)',
              zIndex: 1000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '1.5rem',
            }}
            onClick={() => setActiveAlternativeModal(null)}
          >
            <div
              style={{
                backgroundColor: '#ffffff',
                borderRadius: 'var(--radius-xl)',
                maxWidth: '850px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto',
                padding: '2rem',
                boxShadow: 'var(--shadow-xl)',
                position: 'relative',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '1.5rem',
                }}
              >
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.5rem', fontFamily: 'var(--font-serif)' }}>
                    Alternatives for {activeAlternativeModal.source_destination_name}
                  </h3>
                  <p style={{ margin: '0.3rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    Sites with lower crowd pressure (currently {activeAlternativeModal.source_crowd_level}) offering similar experiences.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveAlternativeModal(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '1.5rem',
                    cursor: 'pointer',
                    color: 'var(--text-muted)',
                  }}
                >
                  ✕
                </button>
              </div>

              {activeAlternativeModal.alternatives && activeAlternativeModal.alternatives.length > 0 ? (
                <div className="alternatives-grid">
                  {activeAlternativeModal.alternatives.map((alt) => (
                    <AlternativeDestinationCard
                      key={alt.destination_id}
                      alternative={alt}
                      sourceDestinationName={activeAlternativeModal.source_destination_name}
                      sourceCrowdLevel={activeAlternativeModal.source_crowd_level}
                    />
                  ))}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>
                  No lower-crowd alternatives discovered for this destination.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
