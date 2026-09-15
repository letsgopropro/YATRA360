import apiClient from './apiClient';

/**
 * Service to check backend API and database health.
 */
export async function getHealthStatus() {
  return await apiClient.get('/health');
}
