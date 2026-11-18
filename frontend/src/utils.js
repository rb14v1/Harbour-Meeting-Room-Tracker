export function todayISO() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function timeOptions(from = '08:00', to = '18:00', stepMinutes = 30) {
  const toMin = (t) => Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5));
  const out = [];
  for (let m = toMin(from); m <= toMin(to); m += stepMinutes) {
    out.push(`${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`);
  }
  return out;
}

export function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
}

export function shortDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

export function formatTimestamp(ts) {
  if (!ts) return '';
  return new Date(ts.replace(' ', 'T')).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

export const STATE_META = {
  Available: { cls: 'state-available', icon: 'bi-check-circle-fill', label: 'Available' },
  Occupied: { cls: 'state-occupied', icon: 'bi-x-circle-fill', label: 'Occupied' },
  Upcoming: { cls: 'state-upcoming', icon: 'bi-clock-fill', label: 'Upcoming' },
  Inactive: { cls: 'state-inactive', icon: 'bi-slash-circle-fill', label: 'Inactive' },
  Confirmed: { cls: 'state-available', icon: 'bi-check2', label: 'Confirmed' },
  Cancelled: { cls: 'state-inactive', icon: 'bi-x', label: 'Cancelled' },
};
