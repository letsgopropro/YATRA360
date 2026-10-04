/**
 * API Client abstraction for YATRA360
 * Centralizes base URL configuration, auth token injection, headers, and request error handling.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export async function request(endpoint, options = {}) {
  let url = `${API_BASE_URL}${endpoint}`;

  if (options.params) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value);
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes('?') ? '&' : '?') + queryString;
    }
  }

  const token = localStorage.getItem('yatra360_token');
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const headers = {
    'Content-Type': 'application/json',
    ...authHeaders,
    ...(options.headers || {}),
  };

  try {
    const fetchOptions = {
      ...options,
      headers,
    };
    // Delete custom params from fetchOptions so fetch doesn't complain
    delete fetchOptions.params;

    const response = await fetch(url, fetchOptions);

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Response wasn't JSON, use status text
      }
      const err = new Error(errorMessage);
      err.status = response.status;
      throw err;
    }

    // If 204 No Content
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error(`[API Client Error] ${endpoint}:`, error);
    throw error;
  }
}

export default {
  get: (endpoint, params, headers) => request(endpoint, { method: 'GET', params, headers }),
  post: (endpoint, body, headers) =>
    request(endpoint, { method: 'POST', body: JSON.stringify(body), headers }),
  put: (endpoint, body, headers) =>
    request(endpoint, { method: 'PUT', body: JSON.stringify(body), headers }),
  delete: (endpoint, headers) => request(endpoint, { method: 'DELETE', headers }),
  request,
};
