const BASE = import.meta.env.VITE_API_BASE || '/api';

function formatError(data, status) {
  if (!data) return `Request failed (${status})`;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => (e.field ? `${e.field}: ${e.message}` : e.message)).join('; ');
  }
  return `Request failed (${status})`;
}

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(formatError(data, res.status));
  return data;
}

function query(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    if (Array.isArray(value)) value.forEach((v) => usp.append(key, v));
    else usp.append(key, value);
  });
  const s = usp.toString();
  return s ? `?${s}` : '';
}

export const api = {
  dashboard: (date) => request(`/dashboard${query({ date })}`),
  rooms: (includeInactive = true) => request(`/rooms${query({ include_inactive: includeInactive })}`),
  createRoom: (body) => request('/rooms', { method: 'POST', body: JSON.stringify(body) }),
  updateRoom: (id, body) => request(`/rooms/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteRoom: (id) => request(`/rooms/${id}`, { method: 'DELETE' }),
  availability: (params) => request(`/availability${query(params)}`),
  bookings: (params) => request(`/bookings${query(params)}`),
  createBooking: (body) => request('/bookings', { method: 'POST', body: JSON.stringify(body) }),
  updateBooking: (id, body) => request(`/bookings/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  cancelBooking: (id) => request(`/bookings/${id}/cancel`, { method: 'POST' }),
  reports: () => request('/reports/summary'),
};
