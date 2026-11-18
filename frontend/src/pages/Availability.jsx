import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import { Alert, EmptyState, PageHeader, StatusBadge } from '../components/common.jsx';
import { formatDate, timeOptions, todayISO } from '../utils.js';

const TIMES = timeOptions('07:00', '20:00');
const FACILITY_OPTIONS = ['Projector', 'Wi-Fi', 'Whiteboard', 'TV Screen', 'Video Conferencing', 'Speakerphone'];

export default function Availability() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    date: todayISO(), start: '10:00', end: '11:00', capacity: '', search: '', facilities: [],
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const toggleFacility = (f) => setForm((prev) => ({
    ...prev,
    facilities: prev.facilities.includes(f) ? prev.facilities.filter((x) => x !== f) : [...prev.facilities, f],
  }));

  const search = async (e) => {
    e?.preventDefault();
    setError('');
    if (form.end <= form.start) return setError('End time must be later than start time.');
    setLoading(true);
    try {
      setResults(await api.availability({
        date: form.date, start: form.start, end: form.end,
        capacity: form.capacity || undefined, search: form.search || undefined, facilities: form.facilities,
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const book = (room) => navigate('/book', {
    state: { roomId: room.room_id, date: form.date, start: form.start, end: form.end },
  });

  const available = results?.filter((r) => r.available).length ?? 0;
  const occupied = results?.filter((r) => r.state === 'Occupied').length ?? 0;

  return (
    <>
      <PageHeader title="Room Availability" subtitle="Check which rooms are free for a specific date and time window." />
      <div className="card mb-4">
        <form className="card-body" onSubmit={search}>
          <div className="row g-3 align-items-end">
            <div className="col-md-3 col-6">
              <label className="form-label" htmlFor="av-date">Date</label>
              <input id="av-date" type="date" className="form-control" min={todayISO()} value={form.date} onChange={set('date')} required />
            </div>
            <div className="col-md-2 col-6">
              <label className="form-label" htmlFor="av-start">Start</label>
              <select id="av-start" className="form-select" value={form.start} onChange={set('start')}>
                {TIMES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div className="col-md-2 col-6">
              <label className="form-label" htmlFor="av-end">End</label>
              <select id="av-end" className="form-select" value={form.end} onChange={set('end')}>
                {TIMES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div className="col-md-2 col-6">
              <label className="form-label" htmlFor="av-cap">Min. capacity</label>
              <input id="av-cap" type="number" min="1" className="form-control" placeholder="Any" value={form.capacity} onChange={set('capacity')} />
            </div>
            <div className="col-md-3">
              <label className="form-label" htmlFor="av-search">Room name</label>
              <div className="input-group">
                <span className="input-group-text"><i className="bi bi-search" /></span>
                <input id="av-search" className="form-control" placeholder="Search rooms" value={form.search} onChange={set('search')} />
              </div>
            </div>
          </div>
          <div className="mt-3">
            <div className="form-label mb-2">Facilities</div>
            <div className="d-flex flex-wrap gap-2">
              {FACILITY_OPTIONS.map((f) => (
                <button type="button" key={f} onClick={() => toggleFacility(f)}
                  className={`chip ${form.facilities.includes(f) ? 'chip-active' : ''}`} aria-pressed={form.facilities.includes(f)}>
                  {form.facilities.includes(f) && <i className="bi bi-check me-1" />}{f}
                </button>
              ))}
            </div>
          </div>
          <div className="d-flex justify-content-end mt-4">
            <button className="btn btn-primary px-4" disabled={loading}>
              <i className="bi bi-search me-2" />{loading ? 'Checking…' : 'Check availability'}
            </button>
          </div>
        </form>
      </div>

      <Alert onClose={() => setError('')}>{error}</Alert>

      {results && (
        <>
          <div className="d-flex flex-wrap gap-3 align-items-center mb-3 small">
            <span className="fw-semibold">{formatDate(form.date)} · {form.start}–{form.end}</span>
            <span className="status-badge state-available"><i className="bi bi-check-circle-fill" /> {available} available</span>
            <span className="status-badge state-occupied"><i className="bi bi-x-circle-fill" /> {occupied} occupied</span>
          </div>
          {results.length === 0 ? <EmptyState icon="bi-funnel" text="No rooms match these filters." /> : (
            <div className="row g-3">
              {results.map((r) => (
                <div className="col-md-6 col-xl-4" key={r.room_id}>
                  <div className={`card room-card h-100 ${r.available ? 'card-available' : r.state === 'Occupied' ? 'card-occupied' : 'card-inactive'}`}>
                    <div className="card-body d-flex flex-column">
                      <div className="d-flex justify-content-between align-items-start gap-2">
                        <div>
                          <h2 className="h6 fw-bold mb-1">{r.room_name}</h2>
                          <div className="small text-muted"><i className="bi bi-geo-alt me-1" />{r.location}</div>
                        </div>
                        <StatusBadge state={r.state} />
                      </div>
                      <div className="d-flex gap-3 small mt-3 text-muted">
                        <span><i className="bi bi-people me-1" />{r.capacity} seats</span>
                      </div>
                      <div className="d-flex flex-wrap gap-1 mt-2">
                        {r.facilities.map((f) => <span key={f} className="facility-tag">{f}</span>)}
                      </div>
                      {r.conflicts.length > 0 && (
                        <div className="small mt-3 conflict-list">
                          {r.conflicts.map((c, i) => (
                            <div key={i}><i className="bi bi-calendar-x me-1" />{c.start_time}–{c.end_time} · {c.meeting_title}</div>
                          ))}
                        </div>
                      )}
                      <div className="mt-auto pt-3">
                        {r.available ? (
                          <button className="btn btn-success w-100" onClick={() => book(r)}>
                            <i className="bi bi-calendar-plus me-2" />Book this room
                          </button>
                        ) : (
                          <button className="btn btn-outline-secondary w-100" disabled>
                            {r.state === 'Inactive' ? 'Room inactive' : 'Not available'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </>
  );
}
