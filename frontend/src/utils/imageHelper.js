/**
 * YATRA360 — Curated Destination Imagery & Fallback System
 * Provides high-resolution, reliable travel photography tailored to Indian destinations.
 * In compliance with zero-broken-image policies, gracefully cascades from database
 * URLs to specific destination photography to category-level photography.
 */

// Category curated imagery
export const CATEGORY_FALLBACK_IMAGES = {
  Nature:
    'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
  Heritage:
    'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?auto=format&fit=crop&w=1200&q=80',
  Adventure:
    'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80',
  Beach:
    'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80',
  'Hill Station':
    'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=1200&q=80',
  Spiritual:
    'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80',
  Wildlife:
    'https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&w=1200&q=80',
  Cultural:
    'https://images.unsplash.com/photo-1600100397608-f010f4439c27?auto=format&fit=crop&w=1200&q=80',
};

// Destination specific mappings
const DESTINATION_IMAGE_MAP = {
  // Northern India & Himalayas
  'kasol': 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=1200&q=80',
  'manali': 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?auto=format&fit=crop&w=1200&q=80',
  'shimla': 'https://images.unsplash.com/photo-1597074866923-dc0589150358?auto=format&fit=crop&w=1200&q=80',
  'rishikesh': 'https://images.unsplash.com/photo-1598890777032-bde13fba5be3?auto=format&fit=crop&w=1200&q=80',
  'varanasi': 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80',
  'varanasi-ghats': 'https://images.unsplash.com/photo-1561361513-2d000a50f0dc?auto=format&fit=crop&w=1200&q=80',
  'taj-mahal': 'https://images.unsplash.com/photo-1564507592333-c60657eea523?auto=format&fit=crop&w=1200&q=80',
  'fatehpur-sikri': 'https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=1200&q=80',
  'tawang': 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=1200&q=80',
  'tirthan-valley': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
  'mcleod-ganj': 'https://images.unsplash.com/photo-1571401835393-8c5f35328320?auto=format&fit=crop&w=1200&q=80',
  'leh-ladakh': 'https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?auto=format&fit=crop&w=1200&q=80',
  'pangong': 'https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?auto=format&fit=crop&w=1200&q=80',
  
  // Western India & Rajasthan
  'jaipur': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80',
  'hawa-mahal': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1200&q=80',
  'amber-fort': 'https://images.unsplash.com/photo-1600100397608-f010f4439c27?auto=format&fit=crop&w=1200&q=80',
  'udaipur': 'https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=1200&q=80',
  'jaisalmer': 'https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80',
  'lonar': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80',
  'ellora': 'https://images.unsplash.com/photo-1600100397608-f010f4439c27?auto=format&fit=crop&w=1200&q=80',
  'ajanta': 'https://images.unsplash.com/photo-1600100397608-f010f4439c27?auto=format&fit=crop&w=1200&q=80',

  // Southern India
  'gokarna': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80',
  'hampi': 'https://images.unsplash.com/photo-1600100397608-f010f4439c27?auto=format&fit=crop&w=1200&q=80',
  'chikmagalur': 'https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=1200&q=80',
  'jog-falls': 'https://images.unsplash.com/photo-1432405972618-c60b0225b8f9?auto=format&fit=crop&w=1200&q=80',
  'munnar': 'https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=1200&q=80',
  'alleppey': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80',
  'coorg': 'https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=1200&q=80',
  'ooty': 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=1200&q=80',
  'kodaikanal': 'https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=1200&q=80',

  // Eastern & Northeast
  'kaziranga': 'https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&w=1200&q=80',
  'darjeeling': 'https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=1200&q=80',
  'sundarbans': 'https://images.unsplash.com/photo-1534177616072-ef7dc120449d?auto=format&fit=crop&w=1200&q=80',
  'puri': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=80',
  'konark': 'https://images.unsplash.com/photo-1600100397608-f010f4439c27?auto=format&fit=crop&w=1200&q=80',
};

export const DEFAULT_TRAVEL_HERO =
  'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1920&q=85';

/**
 * Returns a high-res travel image URL for a destination.
 */
export function getDestinationImageUrl(destination) {
  if (!destination) return DEFAULT_TRAVEL_HERO;

  // 1. If backend has an image URL
  if (destination.image_url && destination.image_url.trim().length > 0) {
    return destination.image_url;
  }

  // 2. Check by slug keywords or name keywords
  const slug = (destination.slug || '').toLowerCase();
  const name = (destination.name || destination.destination_name || '').toLowerCase();

  for (const [key, url] of Object.entries(DESTINATION_IMAGE_MAP)) {
    if (slug.includes(key) || name.includes(key)) {
      return url;
    }
  }

  // 3. Fallback to category
  const category = destination.category;
  if (category && CATEGORY_FALLBACK_IMAGES[category]) {
    return CATEGORY_FALLBACK_IMAGES[category];
  }

  // 4. Default aesthetic scenery
  return DEFAULT_TRAVEL_HERO;
}

/**
 * Image error handler to replace broken URLs with category-level safe photography.
 */
export function handleImageError(e, category) {
  e.currentTarget.onerror = null; // Prevent infinite loop
  const fallback =
    (category && CATEGORY_FALLBACK_IMAGES[category]) || DEFAULT_TRAVEL_HERO;
  e.currentTarget.src = fallback;
}
