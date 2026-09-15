/**
 * API Client abstraction for YATRA360
 * Centralizes base URL configuration, headers, and request error handling.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // Response wasn't JSON, use status text
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    console.error(`[API Client Error] ${endpoint}:`, error);
    throw error;
  }
}

export default {
  get: (endpoint, headers) => request(endpoint, { method: 'GET', headers }),
  post: (endpoint, body, headers) => request(endpoint, { method: 'POST', body: JSON.stringify(body), headers }),
  put: (endpoint, body, headers) => request(endpoint, { method: 'PUT', body: JSON.stringify(body), headers }),
  delete: (endpoint, headers) => request(endpoint, { method: 'DELETE', headers }),
};
