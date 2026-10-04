import React from 'react';
import { Link } from 'react-router-dom';
import { getDestinationImageUrl, handleImageError } from '../utils/imageHelper';

export default function DestinationCard({ destination }) {
  if (!destination) return null;

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
    <Link to={`/destinations/${destination.id}`} className="destination-card">
      <div className="card-media-wrapper">
        <img
          src={imageUrl}
          alt={destination.name}
          className="card-media-img"
          onError={(e) => handleImageError(e, destination.category)}
          loading="lazy"
        />
        <div className="card-media-badges">
          <span className="category-badge">{destination.category}</span>
          {destination.is_hidden_gem && (
            <span className="gem-badge-pill">
              <span>🌿</span>
              <span>Hidden Gem</span>
            </span>
          )}
        </div>
      </div>

      <div className="card-body">
        <h3 className="card-title">{destination.name}</h3>
        <div className="card-location">
          <span>📍</span>
          <span>
            {destination.city}, {destination.state}
          </span>
        </div>

        <div className="card-meta-row">
          <span className={`crowd-pill ${crowdLevel}`}>
            <span>●</span>
            <span style={{ textTransform: 'capitalize' }}>{crowdLevel} crowd</span>
          </span>

          <span className="card-cost-info">{getCostLabel()}</span>
        </div>
      </div>
    </Link>
  );
}
