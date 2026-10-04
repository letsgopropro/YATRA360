import apiClient from './apiClient';

/**
 * Safety Advisory API Service for YATRA360
 */

export async function getSafetyByDestinationId(destinationId) {
  return await apiClient.get(`/safety/${destinationId}`);
}

export default {
  getSafetyByDestinationId,
};
