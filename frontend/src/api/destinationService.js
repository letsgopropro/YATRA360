import apiClient from './apiClient';

/**
 * Destination API Service for YATRA360
 * Interacts with /destinations backend endpoints.
 */

export async function listDestinations(params = {}) {
  return await apiClient.get('/destinations', params);
}

export async function getDestinationById(id) {
  return await apiClient.get(`/destinations/${id}`);
}

export async function getDestinationBySlug(slug) {
  return await apiClient.get(`/destinations/slug/${slug}`);
}

export async function getDestinationCrowd(id) {
  return await apiClient.get(`/destinations/${id}/crowd`);
}

export async function getDestinationSafety(id) {
  return await apiClient.get(`/destinations/${id}/safety`);
}

export async function getDestinationReviews(id, params = {}) {
  return await apiClient.get(`/destinations/${id}/reviews`, params);
}

export async function createDestinationReview(id, reviewData) {
  return await apiClient.post(`/destinations/${id}/reviews`, reviewData);
}

export async function scoreDestination(id, travelRequest = null) {
  return await apiClient.post(`/destinations/${id}/score`, travelRequest || {});
}

export default {
  listDestinations,
  getDestinationById,
  getDestinationBySlug,
  getDestinationCrowd,
  getDestinationSafety,
  getDestinationReviews,
  createDestinationReview,
  scoreDestination,
};
