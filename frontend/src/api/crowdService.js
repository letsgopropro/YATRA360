import apiClient from './apiClient';

/**
 * Crowd Metrics API Service for YATRA360
 */

export async function getCrowdByDestinationId(destinationId) {
  return await apiClient.get(`/crowd/${destinationId}`);
}

export default {
  getCrowdByDestinationId,
};
