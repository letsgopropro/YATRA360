import React from 'react';
import { Link } from 'react-router-dom';
import { getDestinationImageUrl, handleImageError } from '../utils/imageHelper';

export default function AlternativeDestinationCard({
  alternative,
  sourceDestinationName,
  sourceCrowdLevel,
}) {
  if (!alternative) return null;

  const imageUrl = getDestinationImageUrl({
    image_url: alternative.image_url,
    slug: alternative.slug,
    name: alternative.destination_name,
    category: alternative.category,
  });

  const crowdLevel = (alternative.base_crowd_level || 'moderate').toLowerCase();

  // Calculate similarity or display score
  const score = alternative.overall_score || 80;
  const similarityPercent = Math.min(Math.round(score * 0.95), 98);

  return (
    <div className="alternative-card">
      <div className="alt-media-wrapper">
        <img
          src={imageUrl}
          alt={alternative.destination_name}
          className="alt-media-img"
          onError={(e) => handleImageError(e, alternative.category)}
          loading="lazy"
        />
        <span className="alt-similarity-badge">
          {similarityPercent}% Similarity
        </span>
      </div>

      <div className="alt-card-body">
        <h4 className="alt-title">{alternative.destination_name}</h4>
        <div className="alt-location">
          📍 {alternative.city}, {alternative.state}
        </div>

        {/* Explainable comparison text */}
        <p className="alt-reason-text">
          {alternative.reasons && alternative.reasons[0]
            ? alternative.reasons[0]
            : `A similar ${alternative.category.toLowerCase()} destination offering lower crowd pressure (${crowdLevel}) compared to ${
                sourceDestinationName || 'the primary site'
              } (${sourceCrowdLevel || 'high crowd'}).`}
        </p>

        <div className="alt-footer-row">
          <span className={`crowd-pill ${crowdLevel}`}>
            <span>●</span>
            <span style={{ textTransform: 'capitalize' }}>{crowdLevel} crowd</span>
          </span>

          <Link
            to={`/destinations/${alternative.destination_id}`}
            style={{
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--accent-blue)',
              textDecoration: 'none',
            }}
          >
            View Details →
          </Link>
        </div>
      </div>
    </div>
  );
}
