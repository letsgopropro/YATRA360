import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { getDestinationImageUrl, handleImageError } from '../utils/imageHelper';
import ScoreBreakdown from './ScoreBreakdown';

export default function RecommendationCard({ recommendation, onFindAlternatives }) {
  const [showBreakdown, setShowBreakdown] = useState(false);

  if (!recommendation) return null;

  const imageUrl = getDestinationImageUrl({
    image_url: recommendation.image_url,
    slug: recommendation.slug,
    name: recommendation.destination_name,
    category: recommendation.category,
  });

  const rawScore = Number(recommendation.overall_score) || 0;
  const score10 = (rawScore > 10 ? rawScore / 10 : rawScore).toFixed(1);
  const crowdLevel = (recommendation.base_crowd_level || 'moderate').toLowerCase();

  const getCostLabel = () => {
    const fee = recommendation.entry_fee;
    if (fee === 0 || fee === null || fee === undefined) return 'Free Entry';
    if (fee < 50) return `₹ (Budget · ₹${fee})`;
    if (fee <= 250) return `₹₹ (Moderate · ₹${fee})`;
    return `₹₹₹ (Premium · ₹${fee})`;
  };

  return (
    <div className="recommendation-card-wrapper" style={{ display: 'flex', flexDirection: 'column' }}>
      <div className="recommendation-card">
        {/* Destination photo */}
        <div className="rec-media-wrapper">
          <img
            src={imageUrl}
            alt={recommendation.destination_name}
            className="rec-media-img"
            onError={(e) => handleImageError(e, recommendation.category)}
            loading="lazy"
          />
          <div className="card-media-badges">
            <span className="category-badge">{recommendation.category}</span>
            {recommendation.is_hidden_gem && (
              <span className="gem-badge-pill">
                <span>🌿</span>
                <span>Gem</span>
              </span>
            )}
          </div>
        </div>

        {/* Content Area */}
        <div className="rec-content-area">
          <div className="rec-title-row">
            <h3 className="rec-title">{recommendation.destination_name}</h3>
            <span className="rec-location">
              📍 {recommendation.city}, {recommendation.state}
            </span>
          </div>

          <div className="rec-badges-row">
            <span className={`crowd-pill ${crowdLevel}`}>
              <span>●</span>
              <span style={{ textTransform: 'capitalize' }}>{crowdLevel} crowd</span>
            </span>

            <span className="card-cost-info">{getCostLabel()}</span>

            {recommendation.safety_rating && (
              <span
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--emerald-700)',
                  backgroundColor: 'var(--emerald-50)',
                  padding: '0.2rem 0.6rem',
                  borderRadius: 'var(--radius-pill)',
                  fontWeight: 600,
                }}
              >
                🛡️ {recommendation.safety_rating.toFixed(1)} Safety
              </span>
            )}
          </div>

          {/* Why this matches you */}
          {recommendation.reasons && recommendation.reasons.length > 0 && (
            <div className="rec-reasons-box">
              <div className="rec-reasons-title">
                <span>✨</span>
                <span>Why this matches you:</span>
              </div>
              <ul className="rec-reasons-list">
                {recommendation.reasons.map((reason, idx) => (
                  <li key={idx} className="rec-reason-item">
                    <span className="rec-reason-icon">✓</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Prominent Score Column */}
        <div className="rec-score-column">
          <div className="overall-score-badge">
            <span className="score-num">{score10}</span>
            <span className="score-label">Overall Score</span>
          </div>

          <Link
            to={`/destinations/${recommendation.destination_id}`}
            className="rec-action-btn"
          >
            View Details →
          </Link>

          <button
            type="button"
            onClick={() => setShowBreakdown(!showBreakdown)}
            className="rec-action-btn"
            style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}
          >
            {showBreakdown ? 'Hide Scoring ▲' : 'Scoring Breakdown ▼'}
          </button>

          {onFindAlternatives && (
            <button
              type="button"
              onClick={() => onFindAlternatives(recommendation)}
              className="rec-action-btn"
              style={{ fontSize: '0.8rem', color: 'var(--accent-blue)' }}
            >
              Find Alternatives 🔄
            </button>
          )}
        </div>
      </div>

      {/* Expandable Score Breakdown component */}
      {showBreakdown && (
        <div style={{ marginTop: '0.75rem' }}>
          <ScoreBreakdown
            overallScore={recommendation.overall_score}
            components={recommendation.components}
            scoreBreakdown={recommendation.score_breakdown}
            dataQuality={recommendation.data_quality}
            title={`Detailed Scoring Breakdown for ${recommendation.destination_name}`}
          />
        </div>
      )}
    </div>
  );
}
