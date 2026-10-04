import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { listDestinations } from '../api/destinationService';
import DestinationCard from '../components/DestinationCard';
import DestinationFilters from '../components/DestinationFilters';
import { DestinationSkeletons } from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';

export default function Destinations() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Read URL query params
  const initialSearch = searchParams.get('search') || '';
  const initialCategory = searchParams.get('category') || undefined;
  const initialState = searchParams.get('state') || undefined;
  const initialCrowd = searchParams.get('crowd_level') || undefined;
  const initialGem = searchParams.get('is_hidden_gem')
    ? searchParams.get('is_hidden_gem') === 'true'
    : undefined;

  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [filters, setFilters] = useState({
    category: initialCategory,
    state: initialState,
    crowd_level: initialCrowd,
    is_hidden_gem: initialGem,
  });

  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sync URL search params
  const updateUrlParams = useCallback((newSearch, newFilters) => {
    const params = new URLSearchParams();
    if (newSearch) params.set('search', newSearch);
    if (newFilters.category) params.set('category', newFilters.category);
    if (newFilters.state) params.set('state', newFilters.state);
    if (newFilters.crowd_level) params.set('crowd_level', newFilters.crowd_level);
    if (newFilters.is_hidden_gem !== undefined) {
      params.set('is_hidden_gem', String(newFilters.is_hidden_gem));
    }
    setSearchParams(params, { replace: true });
  }, [setSearchParams]);

  const fetchDestinations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = {
        limit: 60,
        search: searchQuery.trim() || undefined,
        category: filters.category || undefined,
        state: filters.state || undefined,
        crowd_level: filters.crowd_level || undefined,
        is_hidden_gem: filters.is_hidden_gem,
      };

      const data = await listDestinations(queryParams);
      setDestinations(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || 'Failed to load destinations.');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filters]);

  useEffect(() => {
    fetchDestinations();
  }, [fetchDestinations]);

  const handleFilterChange = (partialFilter) => {
    setFilters((prev) => {
      const updated = { ...prev, ...partialFilter };
      updateUrlParams(searchQuery, updated);
      return updated;
    });
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    updateUrlParams(searchQuery, filters);
    fetchDestinations();
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    const emptyFilters = {
      category: undefined,
      state: undefined,
      crowd_level: undefined,
      is_hidden_gem: undefined,
    };
    setFilters(emptyFilters);
    updateUrlParams('', emptyFilters);
  };

  return (
    <div className="main-content">
      <div className="page-container">
        {/* Hero Section */}
        <section className="page-hero-banner">
          <h1 className="page-hero-title">Explore Incredible Destinations</h1>
          <p className="page-hero-subtitle">
            Find your next adventure. Discover amazing places across India with smart
            filters, crowd awareness, and personalized insights.
          </p>

          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="explorer-search-bar">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search destinations... (e.g. Manali, beaches, temples)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search destinations"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  updateUrlParams('', filters);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                }}
              >
                ✕
              </button>
            )}
          </form>
        </section>

        {/* Filters Controls */}
        <DestinationFilters
          filters={filters}
          onFilterChange={handleFilterChange}
          onClearFilters={handleClearFilters}
          searchQuery={searchQuery}
        />

        {/* Results Counter */}
        {!loading && !error && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.5rem',
              fontSize: '0.9rem',
              color: 'var(--text-secondary)',
            }}
          >
            <span>
              Showing <strong>{destinations.length}</strong>{' '}
              {destinations.length === 1 ? 'destination' : 'destinations'}
            </span>
          </div>
        )}

        {/* Loading State */}
        {loading && <DestinationSkeletons count={8} />}

        {/* Error State */}
        {!loading && error && (
          <ErrorState
            title="We couldn't load destinations right now."
            message={error}
            onRetry={fetchDestinations}
          />
        )}

        {/* Empty State */}
        {!loading && !error && destinations.length === 0 && (
          <EmptyState
            title="No destinations match your current filters."
            message="Try broadening your search keywords or clearing some filters to explore more places."
            onClear={handleClearFilters}
          />
        )}

        {/* Destinations Grid */}
        {!loading && !error && destinations.length > 0 && (
          <div className="destinations-grid">
            {destinations.map((destination) => (
              <DestinationCard key={destination.id} destination={destination} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
