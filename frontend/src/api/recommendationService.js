import apiClient from './apiClient';

/**
 * Recommendation API Service for YATRA360
 * Interacts with /recommendations endpoints.
 */

export async function getRecommendations(preferences = {}) {
  return await apiClient.post('/recommendations', preferences);
}

export async function getAlternativesForDestination(destinationId, limit = 5) {
  return await apiClient.get(`/recommendations/alternatives/${destinationId}`, { limit });
}

export async function getAlternativesByRequest(data = {}) {
  return await apiClient.post('/recommendations/alternatives', data);
}

export default {
  getRecommendations,
  getAlternativesForDestination,
  getAlternativesByRequest,
};
