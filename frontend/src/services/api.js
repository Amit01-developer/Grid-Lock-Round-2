const PRODUCTION_API_BASE_URL = 'https://grid-lock-round-2.onrender.com';

function getApiBaseUrl() {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  if (typeof window !== 'undefined' && window.location.hostname.endsWith('vercel.app')) {
    return PRODUCTION_API_BASE_URL;
  }

  return '/api';
}

const API_BASE_URL = getApiBaseUrl();

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    let message = 'Request failed. Please try again.';
    let details = {};
    try {
      const payload = await response.json();
      message = payload.message || payload.detail?.message || payload.detail || message;
      details = payload.details || {};
    } catch {
      message = `${response.status} ${response.statusText}`;
    }
    const error = new Error(message);
    error.status = response.status;
    error.details = details;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function getAnalytics(days = 30) {
  return request(`/analytics?days=${days}`);
}

export function getViolations(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, value);
    }
  });
  return request(`/violations?${search.toString()}`);
}

export function getViolation(id) {
  return request(`/violations/${id}`);
}

export function getRecommendations(params = {}) {
  const search = new URLSearchParams({
    days: params.days || 30,
    min_violation_count: params.minViolationCount || 3,
  });
  return request(`/recommendations?${search.toString()}`);
}

export function getHeatmap(params = {}) {
  const search = new URLSearchParams();
  search.set('days', params.days || 30);
  if (params.violationType) {
    search.set('violation_type', params.violationType);
  }
  return request(`/heatmap?${search.toString()}`);
}

export function uploadImage({ file, cameraId, capturedAt }) {
  const formData = new FormData();
  formData.append('file', file);
  if (cameraId) {
    formData.append('camera_id', cameraId);
  }
  if (capturedAt) {
    formData.append('captured_at', capturedAt);
  }
  return request('/upload', {
    method: 'POST',
    body: formData,
  });
}

export function getImageUrl(path) {
  if (!path) {
    return '';
  }
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
    return path;
  }
  const root = API_BASE_URL === '/api' ? '' : API_BASE_URL;
  return `${root}${path}`;
}

