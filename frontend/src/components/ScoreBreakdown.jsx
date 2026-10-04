import React from 'react';

/**
 * Standard proposal scoring factors and weights:
 * - Preference Match: 25%
 * - Safety: 20%
 * - Crowd Suitability: 20%
 * - Accessibility / Distance: 15%
 * - Cost Suitability: 10%
 * - Weather / Condition Suitability: 10%
 */
const SCORING_FACTORS = [
  {
    key: 'preference',
    altKey: 'preference_match',
    label: 'Preference Match',
    weight: '25%',
    weightNum: 0.25,
    color: '#10b981', // emerald
  },
  {
    key: 'safety',
    altKey: 'safety',
    label: 'Safety Score',
    weight: '20%',
    weightNum: 0.2,
    color: '#3b82f6', // blue
  },
  {
    key: 'crowd',
    altKey: 'crowd_suitability',
    label: 'Crowd Suitability',
    weight: '20%',
    weightNum: 0.2,
    color: '#8b5cf6', // purple
  },
  {
    key: 'accessibility',
    altKey: 'accessibility_distance',
    label: 'Accessibility / Distance',
    weight: '15%',
    weightNum: 0.15,
    color: '#f59e0b', // amber
  },
  {
    key: 'cost',
    altKey: 'cost_suitability',
    label: 'Cost Suitability',
    weight: '10%',
    weightNum: 0.1,
    color: '#06b6d4', // cyan
  },
  {
    key: 'weather',
    altKey: 'weather_condition',
    label: 'Weather / Condition',
    weight: '10%',
    weightNum: 0.1,
    color: '#ec4899', // pink
  },
];

export default function ScoreBreakdown({
  overallScore,
  components = {},
  scoreBreakdown = {},
  dataQuality = {},
  explanations = {},
  title = "Why this destination got this score?",
}) {
  // Normalize overall score to 0-10 or 0-100 display
  const rawScore = Number(overallScore) || 0;
  const normalized10 = (rawScore > 10 ? rawScore / 10 : rawScore).toFixed(1);
  const normalized100 = (rawScore > 10 ? rawScore : rawScore * 10).toFixed(1);

  return (
    <div className="score-breakdown-card">
      <h4 className="breakdown-title">{title}</h4>

      {/* Radial overall score summary */}
      <div className="breakdown-overview-row">
        <div className="breakdown-radial-score">
          <span className="radial-score-val">{normalized10}</span>
          <span className="radial-score-sub">Overall</span>
        </div>
        <div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {normalized100} / 100 Multi-Factor Suitability
          </div>
          <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Transparent weighted score based on 6 core travel dimensions.
          </p>
        </div>
      </div>

      {/* Factors progress bars */}
      <div className="factors-list">
        {SCORING_FACTORS.map((factor) => {
          // Check components or scoreBreakdown
          const val =
            components[factor.altKey] ??
            components[factor.key] ??
            scoreBreakdown[factor.key] ??
            70;
          const scorePercent = Math.min(Math.max(Number(val) || 0, 0), 100);
          const quality = dataQuality[factor.key] || 'baseline';
          const reason = explanations[factor.key] || explanations[factor.altKey];

          return (
            <div key={factor.key} className="factor-item">
              <div className="factor-header-row">
                <span className="factor-name">
                  <span>{factor.label}</span>
                  <span className="factor-weight-tag">{factor.weight}</span>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      color: quality === 'real' ? 'var(--emerald-700)' : 'var(--text-muted)',
                      textTransform: 'capitalize',
                      marginLeft: '0.2rem',
                    }}
                  >
                    ({quality})
                  </span>
                </span>
                <span className="factor-score-val">{Math.round(scorePercent)}%</span>
              </div>

              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{
                    width: `${scorePercent}%`,
                    backgroundColor: factor.color,
                  }}
                ></div>
              </div>

              {reason && (
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                  {reason}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Data Quality Notice */}
      <div className="data-quality-notice">
        <span>ℹ️</span>
        <span>
          Some score components are calculated using baseline or historical travel data and do not imply live telemetry.
        </span>
      </div>
    </div>
  );
}
