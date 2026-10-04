import apiClient from './apiClient';

/**
 * Authentication Service for YATRA360
 */

export async function register(userData) {
  return await apiClient.post('/auth/register', userData);
}

export async function login(credentials) {
  const data = await apiClient.post('/auth/login', credentials);
  if (data?.access_token) {
    localStorage.setItem('yatra360_token', data.access_token);
  }
  return data;
}

export async function getMe() {
  return await apiClient.get('/auth/me');
}

export function logout() {
  localStorage.removeItem('yatra360_token');
}

export function isAuthenticated() {
  return !!localStorage.getItem('yatra360_token');
}

export default {
  register,
  login,
  getMe,
  logout,
  isAuthenticated,
};
