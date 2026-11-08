import React from 'react';

const CATEGORIES = [
  'All',
  'Nature',
  'Heritage',
  'Adventure',
  'Beach',
  'Hill Station',
  'Spiritual',
  'Wildlife',
  'Cultural',
];

const STATES = [
  'All States',
  'Andaman & Nicobar Islands',
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chandigarh',
  'Chhattisgarh',
  'Dadra and Nagar Haveli and Daman and Diu',
  'Delhi',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jammu & Kashmir',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Ladakh',
  'Lakshadweep',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Puducherry',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
];

export default function DestinationFilters({
  filters,
  onFilterChange,
  onClearFilters,
  searchQuery,
}) {
  const hasActiveFilters =
    searchQuery ||
    filters.category ||
    filters.state ||
    filters.crowd_level ||
    filters.is_hidden_gem !== undefined;

  return (
    <div className="filter-controls-bar">
      {/* Category Chips */}
      <div className="filter-row">
        <div className="filter-chips-group">
          {CATEGORIES.map((cat) => {
            const isSelected =
              (cat === 'All' && !filters.category) || filters.category === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() =>
                  onFilterChange({
                    category: cat === 'All' ? undefined : cat,
                  })
                }
                className={`filter-chip ${isSelected ? 'active' : ''}`}
              >
                {cat}
              </button>
            );
          })}
        </div>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={onClearFilters}
            className="clear-filters-btn"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Dropdown Filters Row */}
      <div className="filter-row">
        <div className="filter-selects-group">
          {/* State / Region Select */}
          <select
            value={filters.state || ''}
            onChange={(e) =>
              onFilterChange({ state: e.target.value || undefined })
            }
            className="filter-select"
            aria-label="Filter by state"
          >
            {STATES.map((st) => (
              <option key={st} value={st === 'All States' ? '' : st}>
                {st}
              </option>
            ))}
          </select>

          {/* Crowd Level Select */}
          <select
            value={filters.crowd_level || ''}
            onChange={(e) =>
              onFilterChange({ crowd_level: e.target.value || undefined })
            }
            className="filter-select"
            aria-label="Filter by crowd level"
          >
            <option value="">All Crowd Levels</option>
            <option value="low">Low Crowd (Peaceful)</option>
            <option value="moderate">Moderate Crowd</option>
            <option value="high">High Crowd (Popular)</option>
          </select>

          {/* Hidden Gem Select */}
          <select
            value={
              filters.is_hidden_gem === undefined
                ? ''
                : filters.is_hidden_gem
                ? 'true'
                : 'false'
            }
            onChange={(e) => {
              const val = e.target.value;
              onFilterChange({
                is_hidden_gem:
                  val === '' ? undefined : val === 'true' ? true : false,
              });
            }}
            className="filter-select"
            aria-label="Filter by hidden gems"
          >
            <option value="">All Destinations</option>
            <option value="true">Hidden Gems Only 🌿</option>
            <option value="false">Popular Sites Only</option>
          </select>
        </div>
      </div>
    </div>
  );
}
