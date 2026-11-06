/**
 * YATRA360 — Curated Destination Imagery & Fallback System
 * Provides high-resolution, reliable travel photography tailored to Indian destinations.
 * In compliance with zero-broken-image policies, gracefully cascades from database
 * URLs to specific destination photography to category-level photography, with an
 * inline SVG data-URI as the ultimate offline fallback.
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

// Canonical mapping for category normalization
const CATEGORY_MAP = {
  culture: 'Cultural',
  cultural: 'Cultural',
  history: 'Heritage',
  heritage: 'Heritage',
  nature: 'Nature',
  natural: 'Nature',
  adventure: 'Adventure',
  beach: 'Beach',
  beaches: 'Beach',
  spiritual: 'Spiritual',
  wildlife: 'Wildlife',
  'hill station': 'Hill Station',
  hillstation: 'Hill Station',
  hills: 'Hill Station',
  photography: 'Nature',
  wellness: 'Spiritual',
};

export const SVG_FALLBACK_DATA_URI =
  "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='500' viewBox='0 0 800 500'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%231e293b'/%3E%3Cstop offset='100%25' stop-color='%230f172a'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23g)'/%3E%3Ccircle cx='400' cy='220' r='55' fill='%23334155'/%3E%3Ctext x='400' y='235' font-size='38' text-anchor='middle' fill='%2394a3b8'%3E%F0%9F%8F%9E%EF%B8%8F%3C/text%3E%3Ctext x='400' y='320' font-family='system-ui,-apple-system,sans-serif' font-size='20' font-weight='600' text-anchor='middle' fill='%23f8fafc'%3EYATRA360 Destination%3C/text%3E%3C/svg%3E";

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
 * Resolve canonical category name safely
 */
export function resolveCategoryName(rawCategory) {
  if (!rawCategory || typeof rawCategory !== 'string') return null;
  const key = rawCategory.trim().toLowerCase();
  return CATEGORY_MAP[key] || rawCategory;
}

/**
 * Returns a high-res travel image URL for a destination.
 */
export function getDestinationImageUrl(destination) {
  if (!destination) return DEFAULT_TRAVEL_HERO;

  // 1. If backend has an image URL
  if (destination.image_url && typeof destination.image_url === 'string' && destination.image_url.trim().length > 0) {
    return destination.image_url.trim();
  }

  // 2. Check by slug keywords or name keywords
  const slug = (destination.slug || '').toLowerCase();
  const name = (destination.name || destination.destination_name || '').toLowerCase();

  for (const [key, url] of Object.entries(DESTINATION_IMAGE_MAP)) {
    if (slug.includes(key) || name.includes(key)) {
      return url;
    }
  }

  // 3. Fallback to category with normalization
  const resolvedCategory = resolveCategoryName(destination.category);
  if (resolvedCategory && CATEGORY_FALLBACK_IMAGES[resolvedCategory]) {
    return CATEGORY_FALLBACK_IMAGES[resolvedCategory];
  }

  // 4. Default aesthetic scenery
  return DEFAULT_TRAVEL_HERO;
}

/**
 * Image error handler to replace broken URLs with category-level safe photography,
 * cascading to an inline SVG if remote network images fail.
 */
export function handleImageError(e, category) {
  const target = e.currentTarget;
  if (!target) return;

  const resolvedCategory = resolveCategoryName(category);
  const categoryFallback =
    (resolvedCategory && CATEGORY_FALLBACK_IMAGES[resolvedCategory]) || DEFAULT_TRAVEL_HERO;

  // If we haven't tried the category fallback yet, try it once
  if (!target.dataset.fallbackTried && target.src !== categoryFallback) {
    target.dataset.fallbackTried = 'true';
    target.src = categoryFallback;
    return;
  }

  // If category fallback failed or was already attempted, use guaranteed inline SVG
  target.onerror = null; // Prevent any further onerror triggers
  target.src = SVG_FALLBACK_DATA_URI;
}
