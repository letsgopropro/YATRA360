import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  getDestinationById,
  getDestinationSafety,
  getDestinationReviews,
  createDestinationReview,
  scoreDestination,
} from '../api/destinationService';
import { getAlternativesForDestination } from '../api/recommendationService';
import { useAuth } from '../context/AuthContext';
import { getDestinationImageUrl, handleImageError } from '../utils/imageHelper';
import ScoreBreakdown from '../components/ScoreBreakdown';
import AlternativeDestinationCard from '../components/AlternativeDestinationCard';
import { LoadingSpinner } from '../components/LoadingState';
import ErrorState from '../components/ErrorState';

export default function DestinationDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [destination, setDestination] = useState(null);
  const [safety, setSafety] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [scoreData, setScoreData] = useState(null);
  const [alternativesData, setAlternativesData] = useState(null);

  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'safety' | 'reviews'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [loadingAlternatives, setLoadingAlternatives] = useState(false);

  // Review submission state
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [reviewCrowd, setReviewCrowd] = useState('moderate');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState(null);

  const fetchDestinationData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const destData = await getDestinationById(id);
      setDestination(destData);

      // Concurrently fetch safety, reviews, and baseline suitability score
      const [safetyData, reviewsData, scoreResp] = await Promise.allSettled([
        getDestinationSafety(id),
        getDestinationReviews(id),
        scoreDestination(id),
      ]);

      if (safetyData.status === 'fulfilled') setSafety(safetyData.value);
      if (reviewsData.status === 'fulfilled') {
        setReviews(Array.isArray(reviewsData.value) ? reviewsData.value : []);
      }
      if (scoreResp.status === 'fulfilled') setScoreData(scoreResp.value);
    } catch (err) {
      setError(err.message || 'Failed to load destination details.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchDestinationData();
    // Reset alternatives on route change
    setAlternativesData(null);
  }, [fetchDestinationData]);

  // Handle Find Alternatives action
  const handleFindAlternatives = async () => {
    setLoadingAlternatives(true);
    try {
      const altResponse = await getAlternativesForDestination(id, 4);
      setAlternativesData(altResponse);
      // Smooth scroll down to alternatives section
      setTimeout(() => {
        const el = document.getElementById('alternatives-section');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.warn('Failed to fetch alternatives:', err.message);
    } finally {
      setLoadingAlternatives(false);
    }
  };

  // Submit Review Handler
  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    setSubmittingReview(true);
    setReviewError(null);
    try {
      const newReview = await createDestinationReview(id, {
        rating: Number(reviewRating),
        comment: reviewComment.trim() || undefined,
        reported_crowd_level: reviewCrowd,
      });

      setReviews((prev) => [newReview, ...prev]);
      setReviewComment('');
    } catch (err) {
      setReviewError(err.message || 'Failed to post review.');
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="main-content" style={{ padding: '6rem 1.5rem' }}>
        <LoadingSpinner message="Loading destination details & suitability insights..." />
      </div>
    );
  }

  if (error || !destination) {
    return (
      <div className="main-content" style={{ padding: '6rem 1.5rem' }}>
        <ErrorState
          title="Destination Not Found"
          message={error || "We couldn't retrieve information for this destination."}
          onRetry={fetchDestinationData}
        />
      </div>
    );
  }

  const imageUrl = getDestinationImageUrl(destination);
  const crowdLevel = (destination.base_crowd_level || 'moderate').toLowerCase();

  const getCostLabel = () => {
    const fee = destination.entry_fee;
    if (fee === 0 || fee === null || fee === undefined) return 'Free Entry';
    if (fee < 50) return `₹ (Budget · ₹${fee})`;
    if (fee <= 250) return `₹₹ (Moderate · ₹${fee})`;
    return `₹₹₹ (Premium · ₹${fee})`;
  };

  return (
    <div className="main-content">
      {/* ===================================================================
          DESTINATION HERO BANNER
          =================================================================== */}
      <section className="details-hero">
        <img
          src={imageUrl}
          alt={destination.name}
          className="details-hero-img"
          onError={(e) => handleImageError(e, destination.category)}
        />
        <div className="details-hero-overlay"></div>

        <div className="details-hero-content">
          <Link to="/destinations" className="back-link-btn">
            ← Back to Destinations
          </Link>

          <h1 className="details-hero-title">{destination.name}</h1>

          <div className="details-hero-location">
            <span>📍</span>
            <span>
              {destination.city}, {destination.state}
            </span>
          </div>

          <div className="details-badges-bar">
            <span className="details-badge-item">
              <span>🏷️</span>
              <span>{destination.category}</span>
            </span>

            <span className="details-badge-item">
              <span>👥</span>
              <span style={{ textTransform: 'capitalize' }}>
                {crowdLevel} crowd
              </span>
            </span>

            <span className="details-badge-item">
              <span>🎟️</span>
              <span>{getCostLabel()}</span>
            </span>

            {destination.safety_rating && (
              <span className="details-badge-item">
                <span>🛡️</span>
                <span>Safety: {destination.safety_rating.toFixed(1)} / 5</span>
              </span>
            )}

            {destination.is_hidden_gem && (
              <span className="details-badge-item highlight-gem">
                <span>🌿</span>
                <span>Hidden Gem Destination</span>
              </span>
            )}
          </div>
        </div>
      </section>

      {/* ===================================================================
          MAIN CONTENT AREA (TWO COLUMNS)
          =================================================================== */}
      <div className="page-container" style={{ paddingTop: '1.5rem' }}>
        <div className="details-layout-grid">
          {/* Left Column: Tabs & Sections */}
          <div className="details-main-col">
            {/* Tab navigation */}
            <div className="details-tabs-header">
              <button
                type="button"
                className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                Overview
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'safety' ? 'active' : ''}`}
                onClick={() => setActiveTab('safety')}
              >
                Safety & Advisory
              </button>
              <button
                type="button"
                className={`tab-btn ${activeTab === 'reviews' ? 'active' : ''}`}
                onClick={() => setActiveTab('reviews')}
              >
                Reviews ({reviews.length})
              </button>
            </div>

            {/* TAB 1: OVERVIEW */}
            {activeTab === 'overview' && (
              <div>
                {/* About Destination */}
                <div className="info-card-section">
                  <h3 className="section-h3">About this destination</h3>
                  <p className="destination-desc-p">{destination.description}</p>
                </div>

                {/* Key Information Grid */}
                <div className="info-card-section">
                  <h3 className="section-h3">Key Information</h3>
                  <div className="key-info-grid">
                    <div className="key-info-item">
                      <span className="key-info-icon">🏷️</span>
                      <div>
                        <div className="key-info-label">Category</div>
                        <div className="key-info-value">{destination.category}</div>
                      </div>
                    </div>

                    <div className="key-info-item">
                      <span className="key-info-icon">📍</span>
                      <div>
                        <div className="key-info-label">Location / City</div>
                        <div className="key-info-value">{destination.city}</div>
                      </div>
                    </div>

                    <div className="key-info-item">
                      <span className="key-info-icon">🏛️</span>
                      <div>
                        <div className="key-info-label">State / Region</div>
                        <div className="key-info-value">{destination.state}</div>
                      </div>
                    </div>

                    <div className="key-info-item">
                      <span className="key-info-icon">🎟️</span>
                      <div>
                        <div className="key-info-label">Admission / Cost</div>
                        <div className="key-info-value">{getCostLabel()}</div>
                      </div>
                    </div>

                    <div className="key-info-item">
                      <span className="key-info-icon">👥</span>
                      <div>
                        <div className="key-info-label">Base Crowd Level</div>
                        <div
                          className="key-info-value"
                          style={{ textTransform: 'capitalize' }}
                        >
                          {crowdLevel}
                        </div>
                      </div>
                    </div>

                    <div className="key-info-item">
                      <span className="key-info-icon">⏱️</span>
                      <div>
                        <div className="key-info-label">Estimated Visit Duration</div>
                        <div className="key-info-value">
                          {destination.estimated_visit_duration
                            ? `${destination.estimated_visit_duration} minutes`
                            : '2 – 3 hours'}
                        </div>
                      </div>
                    </div>

                    <div className="key-info-item" style={{ gridColumn: '1 / -1' }}>
                      <span className="key-info-icon">♿</span>
                      <div>
                        <div className="key-info-label">Accessibility Information</div>
                        <div className="key-info-value">
                          {destination.accessibility_info ||
                            'Standard public walkways and pedestrian access.'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: SAFETY ADVISORY */}
            {activeTab === 'safety' && (
              <div className="info-card-section">
                <h3 className="section-h3">Safety & Travel Advisory</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      padding: '1rem',
                      backgroundColor: 'var(--emerald-50)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid #a7f3d0',
                    }}
                  >
                    <span style={{ fontSize: '2rem' }}>🛡️</span>
                    <div>
                      <div style={{ fontWeight: 700, color: 'var(--emerald-700)', fontSize: '1.1rem' }}>
                        Safety Rating: {destination.safety_rating.toFixed(1)} / 5.0 (
                        {safety?.safety_level || 'Safe'})
                      </div>
                      <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                        {safety?.risk_description || 'Standard travel safety precautions advised.'}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 style={{ margin: '0 0 0.4rem 0', fontSize: '1rem', color: 'var(--text-primary)' }}>
                      Emergency Contacts & Facilities
                    </h4>
                    <p style={{ margin: 0, fontSize: '0.92rem', color: 'var(--text-secondary)' }}>
                      {safety?.emergency_information ||
                        'National Tourist Helpline: 1363 (24x7 Toll Free). Police Emergency: 112.'}
                    </p>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Advisory Source: {safety?.source || 'YATRA360 Safety Advisory'}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: REVIEWS */}
            {activeTab === 'reviews' && (
              <div>
                {/* Submit Review Card */}
                <div className="info-card-section">
                  <h3 className="section-h3">Leave a Review</h3>
                  {isAuthenticated ? (
                    <form onSubmit={handleReviewSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {reviewError && (
                        <div className="auth-error-banner">{reviewError}</div>
                      )}

                      <div className="form-grid-2col">
                        <div className="form-field">
                          <label>Star Rating (1 - 5)</label>
                          <select
                            value={reviewRating}
                            onChange={(e) => setReviewRating(e.target.value)}
                            className="custom-select"
                          >
                            <option value="5">★★★★★ (5 - Excellent)</option>
                            <option value="4">★★★★☆ (4 - Very Good)</option>
                            <option value="3">★★★☆☆ (3 - Average)</option>
                            <option value="2">★★☆☆☆ (2 - Poor)</option>
                            <option value="1">★☆☆☆☆ (1 - Terrible)</option>
                          </select>
                        </div>

                        <div className="form-field">
                          <label>Reported Crowd Footfall</label>
                          <select
                            value={reviewCrowd}
                            onChange={(e) => setReviewCrowd(e.target.value)}
                            className="custom-select"
                          >
                            <option value="low">Low (Peaceful & Quiet)</option>
                            <option value="moderate">Moderate (Normal)</option>
                            <option value="high">High (Packed / Crowded)</option>
                          </select>
                        </div>
                      </div>

                      <div className="form-field">
                        <label>Your Experience Feedback</label>
                        <textarea
                          rows="3"
                          value={reviewComment}
                          onChange={(e) => setReviewComment(e.target.value)}
                          placeholder="Share tips regarding timing, crowds, photography, or accessibility..."
                          style={{
                            padding: '0.75rem',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-light)',
                            fontFamily: 'inherit',
                            fontSize: '0.95rem',
                            outline: 'none',
                          }}
                        ></textarea>
                      </div>

                      <button
                        type="submit"
                        disabled={submittingReview}
                        className="btn-action-primary"
                        style={{ alignSelf: 'flex-start' }}
                      >
                        {submittingReview ? 'Posting Review...' : 'Submit Review'}
                      </button>
                    </form>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '1.5rem', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
                      <p style={{ margin: '0 0 1rem 0', color: 'var(--text-secondary)' }}>
                        Sign in to share your traveler review and crowd observation.
                      </p>
                      <Link to="/login" className="btn-action-primary" style={{ display: 'inline-flex', width: 'auto' }}>
                        Login to Review
                      </Link>
                    </div>
                  )}
                </div>

                {/* Reviews List */}
                <div className="info-card-section">
                  <h3 className="section-h3">Traveler Reviews</h3>
                  {reviews.length === 0 ? (
                    <p style={{ color: 'var(--text-muted)' }}>
                      No reviews recorded yet for this destination. Be the first to share your experience!
                    </p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      {reviews.map((rev) => (
                        <div
                          key={rev.id}
                          style={{
                            paddingBottom: '1.2rem',
                            borderBottom: '1px solid var(--border-subtle)',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                                {rev.user_name || 'Verified Traveler'}
                              </span>
                              <span style={{ color: '#f59e0b' }}>
                                {'★'.repeat(rev.rating)}
                                {'☆'.repeat(5 - rev.rating)}
                              </span>
                            </div>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              {new Date(rev.created_at).toLocaleDateString()}
                            </span>
                          </div>

                          {rev.reported_crowd_level && (
                            <span
                              style={{
                                fontSize: '0.75rem',
                                padding: '0.15rem 0.5rem',
                                borderRadius: 'var(--radius-pill)',
                                backgroundColor: 'var(--bg-muted)',
                                color: 'var(--text-secondary)',
                                display: 'inline-block',
                                marginBottom: '0.5rem',
                              }}
                            >
                              Observed Crowd: {rev.reported_crowd_level}
                            </span>
                          )}

                          <p style={{ margin: 0, fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            {rev.comment || 'Traveler rated this destination.'}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Quick Actions & Scoring Card */}
          <div className="details-sidebar-col">
            {/* Quick Actions Card */}
            <div className="sidebar-action-card">
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>
                Quick Actions
              </h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: '0 0 1rem 0' }}>
                Explore tailored options for your visit.
              </p>

              <div className="action-btn-stack">
                <Link
                  to={`/recommend?category=${encodeURIComponent(destination.category)}`}
                  className="btn-action-primary"
                >
                  🎯 Get Recommendations
                </Link>

                <button
                  type="button"
                  onClick={handleFindAlternatives}
                  disabled={loadingAlternatives}
                  className="btn-action-outline"
                >
                  {loadingAlternatives ? 'Analyzing Alternatives...' : '🔄 Find Alternatives'}
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('safety')}
                  className="btn-action-outline"
                >
                  🛡️ View Safety Advisory
                </button>
              </div>
            </div>

            {/* Transparent Suitability Score Component */}
            {scoreData && (
              <ScoreBreakdown
                overallScore={scoreData.overall_score}
                components={scoreData.components}
                scoreBreakdown={scoreData.score_breakdown}
                dataQuality={scoreData.data_quality}
                explanations={scoreData.explanations}
                title="Transparent Suitability Score"
              />
            )}
          </div>
        </div>

        {/* ===================================================================
            ALTERNATIVE DESTINATIONS SECTION (Panel 7)
            =================================================================== */}
        {alternativesData && (
          <section id="alternatives-section" className="alternatives-container">
            <h3 className="alternatives-heading">Looking for alternatives?</h3>
            <p className="alternatives-subtitle">
              Here are verified alternatives to{' '}
              <strong>{alternativesData.source_destination_name}</strong> (currently{' '}
              <span style={{ textTransform: 'capitalize' }}>
                {alternativesData.source_crowd_level}
              </span>{' '}
              crowd), selected for lower crowd pressure and similar travel experiences.
            </p>

            {alternativesData.alternatives && alternativesData.alternatives.length > 0 ? (
              <div className="alternatives-grid">
                {alternativesData.alternatives.map((alt) => (
                  <AlternativeDestinationCard
                    key={alt.destination_id}
                    alternative={alt}
                    sourceDestinationName={alternativesData.source_destination_name}
                    sourceCrowdLevel={alternativesData.source_crowd_level}
                  />
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>
                No direct lower-crowd alternatives discovered for this category yet.
              </p>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
