import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('tourist');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      setLoading(false);
      return;
    }

    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        role,
      });
      navigate('/', { replace: true });
    } catch (err) {
      setError(
        err.message || 'Registration failed. Please check your information and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-content">
      <div className="auth-page-container">
        <div className="auth-card">
          <div className="auth-header">
            <div className="auth-logo-icon">🧭</div>
            <h1 className="auth-title">Join YATRA360</h1>
            <p className="auth-subtitle">
              Create an account to personalize destination scoring and save custom travel plans.
            </p>
          </div>

          {error && <div className="auth-error-banner">{error}</div>}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-field">
              <label htmlFor="reg-name">Full Name</label>
              <input
                id="reg-name"
                type="text"
                required
                placeholder="Priya Sharma"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="name"
              />
            </div>

            <div className="form-field">
              <label htmlFor="reg-email">Email Address</label>
              <input
                id="reg-email"
                type="email"
                required
                placeholder="priya@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="form-field">
              <label htmlFor="reg-password">Password (min 6 characters)</label>
              <input
                id="reg-password"
                type="password"
                required
                minLength={6}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>

            <div className="form-field">
              <label htmlFor="reg-role">Account Type</label>
              <select
                id="reg-role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="custom-select"
              >
                <option value="tourist">Tourist / Traveler</option>
                <option value="business">Local Tourism Business</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="auth-submit-btn"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account? <Link to="/login">Sign in here</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
