import React from 'react';

export default function ErrorState({
  title = "We couldn't load destinations right now.",
  message = "Please check your network or try again.",
  onRetry,
}) {
  return (
    <div className="state-container">
      <div className="state-icon">⚠️</div>
      <h3 className="state-title">{title}</h3>
      <p className="state-text">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="state-action-btn">
          Try Again
        </button>
      )}
    </div>
  );
}
