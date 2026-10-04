import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../api/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadCurrentUser = useCallback(async () => {
    if (!authService.isAuthenticated()) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const profile = await authService.getMe();
      setUser(profile);
    } catch (err) {
      console.warn('Failed to load user session:', err.message);
      authService.logout();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  const login = async (email, password) => {
    setError(null);
    setLoading(true);
    try {
      await authService.login({ email, password });
      const profile = await authService.getMe();
      setUser(profile);
      return profile;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setError(null);
    setLoading(true);
    try {
      await authService.register(userData);
      // Automatically log in upon successful registration
      return await login(userData.email, userData.password);
    } catch (err) {
      setError(err.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
