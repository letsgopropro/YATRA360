import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { listDestinations, getDestinationsCount } from '../api/destinationService';
import DestinationCard from '../components/DestinationCard';
import DestinationFilters from '../components/DestinationFilters';
import { DestinationSkeletons } from '../components/LoadingState';
import ErrorState from '../components/ErrorState';
import EmptyState from '../components/EmptyState';

function getPageNumbers(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  const pages = [];
  if (current <= 4) {
    for (let i = 1; i <= 5; i++) pages.push(i);
    pages.push('...');
    pages.push(total);
  } else if (current >= total - 3) {
    pages.push(1);
    pages.push('...');
    for (let i = total - 4; i <= total; i++) pages.push(i);
  } else {
    pages.push(1);
    pages.push('...');
    pages.push(current - 1);
    pages.push(current);
    pages.push(current + 1);
    pages.push('...');
    pages.push(total);
  }
  return pages;
}

export default function Destinations() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Read URL query params directly from searchParams
  const urlSearch = searchParams.get('search') || '';
  const urlCategory = searchParams.get('category') || undefined;
  const urlState = searchParams.get('state') || undefined;
  const urlCrowd = searchParams.get('crowd_level') || undefined;
  const urlGem =
    searchParams.get('is_hidden_gem') !== null
      ? searchParams.get('is_hidden_gem') === 'true'
      : undefined;
  const urlPage = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
  const urlPageSize = parseInt(searchParams.get('page_size') || '24', 10);
  const urlSortBy = searchParams.get('sort_by') || 'id';
  const urlSortOrder = searchParams.get('sort_order') || 'asc';

  const [searchQuery, setSearchQuery] = useState(urlSearch);
  const [destinations, setDestinations] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Keep searchQuery input in sync when URL search param changes externally
  useEffect(() => {
    setSearchQuery(urlSearch);
  }, [urlSearch]);

  const filters = {
    category: urlCategory,
    state: urlState,
    crowd_level: urlCrowd,
    is_hidden_gem: urlGem,
  };

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
    // Retain page size if customized
    const currentSize = searchParams.get('page_size');
    if (currentSize && currentSize !== '24') {
      params.set('page_size', currentSize);
    }
    // Retain sort options if customized
    const currentSort = searchParams.get('sort_by');
    if (currentSort && currentSort !== 'id') {
      params.set('sort_by', currentSort);
      const order = searchParams.get('sort_order');
      if (order) params.set('sort_order', order);
    }
    // Filter/search change resets to page 1
    setSearchParams(params, { replace: true });
  }, [searchParams, setSearchParams]);

  const fetchDestinations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = {
        limit: urlPageSize,
        skip: (urlPage - 1) * urlPageSize,
        search: urlSearch.trim() || undefined,
        category: urlCategory,
        state: urlState,
        crowd_level: urlCrowd,
        is_hidden_gem: urlGem,
        sort_by: urlSortBy,
        sort_order: urlSortOrder,
      };

      const data = await listDestinations(queryParams);
      const items = Array.isArray(data) ? data : [];
      // De-duplicate any potential duplicate IDs
      const uniqueItems = Array.from(new Map(items.map((d) => [d.id, d])).values());
      setDestinations(uniqueItems);

      if (data.totalCount !== undefined) {
        setTotalCount(data.totalCount);
      } else {
        try {
          const countData = await getDestinationsCount(queryParams);
          setTotalCount(countData?.total ?? uniqueItems.length);
        } catch {
          setTotalCount(uniqueItems.length);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to load destinations.');
    } finally {
      setLoading(false);
    }
  }, [
    urlPage,
    urlPageSize,
    urlSortBy,
    urlSortOrder,
    urlSearch,
    urlCategory,
    urlState,
    urlCrowd,
    urlGem,
  ]);

  useEffect(() => {
    fetchDestinations();
  }, [fetchDestinations]);

  const handleFilterChange = (partialFilter) => {
    const updated = { ...filters, ...partialFilter };
    updateUrlParams(searchQuery, updated);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    updateUrlParams(searchQuery.trim(), filters);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setSearchParams(new URLSearchParams(), { replace: true });
  };

  const handlePageChange = (newPage) => {
    const params = new URLSearchParams(searchParams);
    if (newPage > 1) {
      params.set('page', String(newPage));
    } else {
      params.delete('page');
    }
    setSearchParams(params);
    window.scrollTo({ top: 320, behavior: 'smooth' });
  };

  const handleSortChange = (e) => {
    const val = e.target.value;
    const params = new URLSearchParams(searchParams);
    params.delete('page'); // Reset to page 1 on sort change
    if (val === 'name_asc') {
      params.set('sort_by', 'name');
      params.set('sort_order', 'asc');
    } else if (val === 'name_desc') {
      params.set('sort_by', 'name');
      params.set('sort_order', 'desc');
    } else if (val === 'rating_desc') {
      params.set('sort_by', 'safety_rating');
      params.set('sort_order', 'desc');
    } else if (val === 'fee_asc') {
      params.set('sort_by', 'entry_fee');
      params.set('sort_order', 'asc');
    } else {
      params.delete('sort_by');
      params.delete('sort_order');
    }
    setSearchParams(params);
  };

  const handlePageSizeChange = (e) => {
    const val = e.target.value;
    const params = new URLSearchParams(searchParams);
    params.delete('page'); // Reset to page 1
    if (val && val !== '24') {
      params.set('page_size', val);
    } else {
      params.delete('page_size');
    }
    setSearchParams(params);
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / urlPageSize));
  const startItem = totalCount === 0 ? 0 : (urlPage - 1) * urlPageSize + 1;
  const endItem = Math.min(urlPage * urlPageSize, totalCount);

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

        {/* Results Toolbar with Counter, Sorting, and Page Size */}
        {!loading && !error && (
          <div className="explorer-toolbar">
            <div className="explorer-counter">
              Showing <strong>{startItem}–{endItem}</strong> of <strong>{totalCount}</strong>{' '}
              {totalCount === 1 ? 'destination' : 'destinations'}
            </div>

            <div className="explorer-toolbar-controls">
              <label className="toolbar-select-label">
                <span>Sort by:</span>
                <select
                  value={
                    urlSortBy === 'name' && urlSortOrder === 'desc'
                      ? 'name_desc'
                      : urlSortBy === 'name'
                      ? 'name_asc'
                      : urlSortBy === 'safety_rating'
                      ? 'rating_desc'
                      : urlSortBy === 'entry_fee'
                      ? 'fee_asc'
                      : 'default'
                  }
                  onChange={handleSortChange}
                  className="toolbar-select"
                  aria-label="Sort destinations"
                >
                  <option value="default">Default (Featured)</option>
                  <option value="name_asc">Name (A → Z)</option>
                  <option value="name_desc">Name (Z → A)</option>
                  <option value="rating_desc">Safety Rating (High to Low)</option>
                  <option value="fee_asc">Entry Fee (Low to High)</option>
                </select>
              </label>

              <label className="toolbar-select-label">
                <span>Per page:</span>
                <select
                  value={String(urlPageSize)}
                  onChange={handlePageSizeChange}
                  className="toolbar-select"
                  aria-label="Items per page"
                >
                  <option value="24">24</option>
                  <option value="48">48</option>
                  <option value="96">96</option>
                  <option value="300">All ({totalCount || 250})</option>
                </select>
              </label>
            </div>
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
          <>
            <div className="destinations-grid">
              {destinations.map((destination) => (
                <DestinationCard key={destination.id} destination={destination} />
              ))}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <nav className="pagination-wrapper" aria-label="Destinations pagination">
                <button
                  type="button"
                  onClick={() => handlePageChange(urlPage - 1)}
                  disabled={urlPage <= 1}
                  className="pagination-btn"
                  aria-label="Previous page"
                >
                  ‹ Prev
                </button>

                {getPageNumbers(urlPage, totalPages).map((p, idx) =>
                  p === '...' ? (
                    <span key={`ellipsis-${idx}`} className="pagination-ellipsis">
                      …
                    </span>
                  ) : (
                    <button
                      key={p}
                      type="button"
                      onClick={() => handlePageChange(p)}
                      className={`pagination-btn ${p === urlPage ? 'active' : ''}`}
                      aria-current={p === urlPage ? 'page' : undefined}
                    >
                      {p}
                    </button>
                  )
                )}

                <button
                  type="button"
                  onClick={() => handlePageChange(urlPage + 1)}
                  disabled={urlPage >= totalPages}
                  className="pagination-btn"
                  aria-label="Next page"
                >
                  Next ›
                </button>
              </nav>
            )}
          </>
        )}
      </div>
    </div>
  );
}
