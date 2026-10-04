import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getRecommendations } from '../api/recommendationService';

const AVAILABLE_INTERESTS = [
  'Nature',
  'Adventure',
  'Heritage',
  'Cultural',
  'Beach',
  'Hill Station',
  'Spiritual',
  'Wildlife',
  'Photography',
  'Wellness',
];

const TIME_OPTIONS = [
  { label: 'Half Day (approx 4 hours)', minutes: 240, text: 'Half day' },
  { label: 'Full Day (approx 8 hours)', minutes: 480, text: '1 day' },
  { label: 'Weekend Trip (2 days)', minutes: 960, text: 'Weekend' },
  { label: '3 – 5 days', minutes: 1800, text: '3-5 days' },
  { label: '1 week or more', minutes: 3600, text: '1 week+' },
  { label: 'Flexible / Unconstrained', minutes: null, text: 'Flexible' },
];

export default function Recommend() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const initialCat = searchParams.get('category');

  // Form states
  const [selectedInterests, setSelectedInterests] = useState(
    initialCat ? [initialCat] : ['Nature', 'Heritage']
  );
  const [budget, setBudget] = useState(15000);
  const [availableTimeIdx, setAvailableTimeIdx] = useState(3); // '3 – 5 days'
  const [crowdLevel, setCrowdLevel] = useState('moderate');
  const [hiddenGems, setHiddenGems] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(initialCat || '');
  const [limit, setLimit] = useState(10);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const toggleInterest = (interest) => {
    setSelectedInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((item) => item !== interest)
        : [...prev, interest]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const selectedTime = TIME_OPTIONS[availableTimeIdx];

      const payload = {
        interests: selectedInterests.length > 0 ? selectedInterests : ['Nature'],
        budget: Number(budget),
        available_time: selectedTime.text,
        available_time_minutes: selectedTime.minutes || undefined,
        preferred_crowd_level: crowdLevel || undefined,
        prefer_hidden_gems: hiddenGems,
        category: selectedCategory || undefined,
        limit: Number(limit),
        apply_diversity: true,
      };

      const result = await getRecommendations(payload);

      // Save to sessionStorage for refresh resilience
      sessionStorage.setItem('yatra360_recommendations', JSON.stringify(result));
      sessionStorage.setItem('yatra360_preferences', JSON.stringify(payload));

      // Navigate to results page
      navigate('/recommendations', { state: { recommendationsData: result } });
    } catch (err) {
      setError(err.message || 'Failed to generate recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-content">
      <div className="form-page-container">
        {/* Header */}
        <div className="form-header-card">
          <h1 className="form-title">Tell us your travel preferences</h1>
          <p className="form-subtitle">
            Help us find destinations that fit the way you want to travel. Our
            explainable scoring engine considers your budget, time, crowd comfort, and interests.
          </p>
        </div>

        {/* Preference Form */}
        <form onSubmit={handleSubmit} className="preference-form-card">
          {error && <div className="auth-error-banner">{error}</div>}

          {/* 1. Interests */}
          <div className="form-group-section">
            <label className="group-label">
              <span>Your Interests</span>
              <span className="group-hint">Select one or more themes</span>
            </label>
            <div className="chips-select-grid">
              {AVAILABLE_INTERESTS.map((interest) => {
                const isSelected = selectedInterests.includes(interest);
                return (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => toggleInterest(interest)}
                    className={`selectable-chip ${isSelected ? 'selected' : ''}`}
                  >
                    {isSelected ? '✓ ' : '+ '}
                    {interest}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 2. Budget Slider */}
          <div className="form-group-section">
            <label className="group-label">
              <span>Budget (per person)</span>
              <span className="slider-value-display">
                ₹ {budget.toLocaleString('en-IN')}
              </span>
            </label>
            <div className="slider-container">
              <input
                type="range"
                min="1000"
                max="50000"
                step="1000"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="range-slider"
                aria-label="Budget range slider"
              />
              <div className="range-labels-row">
                <span>₹ 1,000 (Budget)</span>
                <span>₹ 25,000</span>
                <span>₹ 50,000+ (Luxury)</span>
              </div>
            </div>
          </div>

          {/* 3. Available Time & Preferred Crowd (2 cols) */}
          <div className="form-grid-2col">
            <div className="form-group-section">
              <label className="group-label">Available Time</label>
              <select
                value={availableTimeIdx}
                onChange={(e) => setAvailableTimeIdx(Number(e.target.value))}
                className="custom-select"
                aria-label="Available trip duration"
              >
                {TIME_OPTIONS.map((opt, idx) => (
                  <option key={idx} value={idx}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group-section">
              <label className="group-label">Preferred Crowd Level</label>
              <select
                value={crowdLevel}
                onChange={(e) => setCrowdLevel(e.target.value)}
                className="custom-select"
                aria-label="Preferred crowd level"
              >
                <option value="">Any Crowd Level</option>
                <option value="low">Low (Peaceful & Quiet)</option>
                <option value="moderate">Moderate (Balanced)</option>
                <option value="high">High (Lively & Vibrant)</option>
              </select>
            </div>
          </div>

          {/* 4. Hidden Gems Toggle */}
          <div className="toggle-row">
            <div>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                🌿 Prioritize Hidden Gems?
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Surface lesser-known, offbeat destinations with serene character.
              </div>
            </div>
            <label className="toggle-switch-input" aria-label="Toggle hidden gems">
              <input
                type="checkbox"
                checked={hiddenGems}
                onChange={(e) => setHiddenGems(e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          {/* 5. Specific Category Filter & Limit (2 cols) */}
          <div className="form-grid-2col">
            <div className="form-group-section">
              <label className="group-label">Specific Category Focus</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="custom-select"
                aria-label="Optional primary category filter"
              >
                <option value="">All Categories (Diverse)</option>
                <option value="Nature">Nature & Scenic</option>
                <option value="Heritage">Heritage & Historic</option>
                <option value="Adventure">Adventure</option>
                <option value="Beach">Beach & Coastal</option>
                <option value="Hill Station">Hill Station</option>
                <option value="Spiritual">Spiritual</option>
                <option value="Wildlife">Wildlife</option>
              </select>
            </div>

            <div className="form-group-section">
              <label className="group-label">Number of Results</label>
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="custom-select"
                aria-label="Recommendation results count limit"
              >
                <option value="5">Top 5 recommendations</option>
                <option value="10">Top 10 recommendations</option>
                <option value="15">Top 15 recommendations</option>
                <option value="20">Top 20 recommendations</option>
              </select>
            </div>
          </div>

          {/* Submit CTA */}
          <button
            type="submit"
            disabled={loading}
            className="submit-preferences-btn"
          >
            {loading ? (
              <span>Analyzing destinations & computing suitability...</span>
            ) : (
              <span>Get My Recommendations →</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
