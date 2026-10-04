import React from 'react';

export function LoadingSpinner({ message = 'Loading destinations...' }) {
  return (
    <div className="state-container">
      <div className="status-indicator loading" style={{ justifyContent: 'center' }}>
        <span className="dot pulse"></span>
        <span style={{ fontSize: '1.05rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
          {message}
        </span>
      </div>
    </div>
  );
}

export function DestinationSkeletons({ count = 6 }) {
  return (
    <div className="destinations-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-shimmer"></div>
        </div>
      ))}
    </div>
  );
}

export default function LoadingState({ message }) {
  return <LoadingSpinner message={message} />;
}
