import React from 'react';

export default function EmptyState({
  title = "No destinations match your current filters.",
  message = "Try broadening your search keywords or clearing active filters to discover more places.",
  onClear,
  clearLabel = "Clear All Filters",
}) {
  return (
    <div className="state-container">
      <div className="state-icon">🧭</div>
      <h3 className="state-title">{title}</h3>
      <p className="state-text">{message}</p>
      {onClear && (
        <button onClick={onClear} className="state-action-btn">
          {clearLabel}
        </button>
      )}
    </div>
  );
}
