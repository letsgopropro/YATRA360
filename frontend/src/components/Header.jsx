import React, { useState, useEffect } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const location = useLocation();
  const { user, logout, isAuthenticated } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isHome = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 40) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const headerClass = `app-header ${isHome ? 'header-transparent' : ''} ${
    scrolled ? 'scrolled' : ''
  }`;

  return (
    <header className={headerClass}>
      <div className="header-inner">
        {/* Logo / Brand */}
        <Link to="/" className="brand-link">
          <span className="brand-icon">🧭</span>
          <span className="brand-title">
            YATRA<span>360</span>
          </span>
        </Link>

        {/* Desktop Navigation */}
        <ul className="nav-links">
          <li className="nav-item">
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
              Home
            </NavLink>
          </li>
          <li className="nav-item">
            <NavLink
              to="/destinations"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              Explore
            </NavLink>
          </li>
          <li className="nav-item">
            <NavLink
              to="/recommend"
              className={({ isActive }) => (isActive ? 'active' : '')}
            >
              Get Recommendations
            </NavLink>
          </li>
        </ul>

        {/* Right side actions */}
        <div className="header-actions">
          {isAuthenticated && user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
              <span className="header-user-badge">
                <span>👤</span>
                <span>{user.full_name || user.email}</span>
              </span>
              <button
                onClick={logout}
                className="header-btn header-btn-outline"
                style={{ padding: '0.45rem 1rem', fontSize: '0.85rem' }}
                title="Log out of YATRA360"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <Link to="/login" className="header-btn header-btn-primary">
              Login / Register
            </Link>
          )}

          {/* Mobile hamburger button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="mobile-menu-btn"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileMenuOpen && (
        <div
          style={{
            backgroundColor: 'rgba(15, 23, 42, 0.98)',
            padding: '1.5rem',
            borderBottom: '1px solid rgba(255, 255, 255, 0.15)',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}
        >
          <NavLink
            to="/"
            end
            style={{ color: '#ffffff', textDecoration: 'none', fontSize: '1.1rem', fontWeight: 600 }}
          >
            Home
          </NavLink>
          <NavLink
            to="/destinations"
            style={{ color: '#ffffff', textDecoration: 'none', fontSize: '1.1rem', fontWeight: 600 }}
          >
            Explore Destinations
          </NavLink>
          <NavLink
            to="/recommend"
            style={{ color: '#ffffff', textDecoration: 'none', fontSize: '1.1rem', fontWeight: 600 }}
          >
            Get Recommendations
          </NavLink>
          <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.2)', paddingTop: '1rem' }}>
            {isAuthenticated ? (
              <button
                onClick={logout}
                className="header-btn header-btn-outline"
                style={{ width: '100%', color: '#fff', borderColor: '#fff' }}
              >
                Sign Out ({user?.full_name || 'User'})
              </button>
            ) : (
              <Link
                to="/login"
                className="header-btn header-btn-primary"
                style={{ width: '100%', textAlign: 'center', display: 'block' }}
              >
                Login / Register
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
