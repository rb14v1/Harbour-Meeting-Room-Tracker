import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { Alert, EmptyState, PageHeader, Spinner, StatusBadge } from '../components/common.jsx';
import EditBookingModal from '../components/EditBookingModal.jsx';
import { formatDate, formatTimestamp } from '../utils.js';

const VIEWS = [
  { key: 'all', label: 'All' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'past', label: 'Past' },
  { key: 'cancelled', label: 'Cancelled' },
];

export default function Bookings() {
  const [view, setView] = useState('upcoming');
  const [search, setSearch] = useState('');
  const [roomId, setRoomId] = useState('');
  const [date, setDate] = useState('');
  const [rooms, setRooms] = useState([]);
  const [bookings, setBookings] = useState(null);
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    api.rooms().then(setRooms).catch(() => {});
  }, []);

  const load = (overrides = {}) => {
    const params = { view, search: search.trim(), room_id: roomId, date, ...overrides };
    setBookings(null);
    api.bookings(params)
      .then(setBookings)
      .catch((e) => setError(e.message));
  };

  useEffect(load, [view, roomId, date]); // eslint-disable-line react-hooks/exhaustive-deps

  const cancel = async (b) => {
    if (!window.confirm(`Cancel "${b.meeting_title}" on ${formatDate(b.booking_date)} at ${b.start_time}?`)) return;
    try {
      await api.cancelBooking(b.booking_id);
      setNotice(`Cancelled “${b.meeting_title}”. The slot is free for others.`);
      setSelected(null);
      load();
    } catch (e) {
      setError(e.message);
    }
  };

  const canCancel = (b) => b.can_cancel;

  const saved = (updated) => {
    setEditing(null);
    setSelected(null);
    setNotice(`Booking updated: ${updated.meeting_title}, ${formatDate(updated.booking_date)} ${updated.start_time}–${updated.end_time} in ${updated.room_name}.`);
    load();
  };

  return (
    <>
      <PageHeader title="Bookings" subtitle="Review, search and cancel meeting room reservations." />

      <div className="card mb-4">
        <div className="card-body">
          <div className="d-flex flex-wrap gap-3 justify-content-between align-items-end">
            <div className="btn-group" role="tablist" aria-label="Booking views">
              {VIEWS.map((v) => (
                <button key={v.key} role="tab" aria-selected={view === v.key}
                  className={`btn ${view === v.key ? 'btn-primary' : 'btn-outline-primary'}`}
                  onClick={() => setView(v.key)}>{v.label}</button>
              ))}
            </div>
            <form className="d-flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); load(); }}>
              <div className="input-group" style={{ width: 240 }}>
                <span className="input-group-text"><i className="bi bi-person-search" /></span>
                <input className="form-control" placeholder="Employee name" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search by employee name" />
              </div>
              <select className="form-select" style={{ width: 200 }} value={roomId} onChange={(e) => setRoomId(e.target.value)} aria-label="Filter by room">
                <option value="">All rooms</option>
                {rooms.map((r) => <option key={r.room_id} value={r.room_id}>{r.room_name}</option>)}
              </select>
              <input type="date" className="form-control" style={{ width: 170 }} value={date} onChange={(e) => setDate(e.target.value)} aria-label="Filter by date" />
              <button className="btn btn-outline-secondary" type="submit">Search</button>
              {(search || roomId || date) && (
                <button type="button" className="btn btn-link" onClick={() => { setSearch(''); setRoomId(''); setDate(''); load({ search: '', room_id: '', date: '' }); }}>Clear</button>
              )}
            </form>
          </div>
        </div>
      </div>

      <Alert kind="success" onClose={() => setNotice('')}>{notice}</Alert>
      <Alert onClose={() => setError('')}>{error}</Alert>
      {!bookings && !error && <Spinner />}

      {bookings && (bookings.length === 0 ? <EmptyState icon="bi-calendar-x" text="No bookings match these filters." /> : (
        <div className="card">
          <div className="table-responsive">
            <table className="table table-modern align-middle mb-0">
              <thead>
                <tr><th>Meeting</th><th>Room</th><th>Employee</th><th>Date</th><th>Time</th><th>Status</th><th className="text-end">Actions</th></tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.booking_id}>
                    <td className="fw-semibold">{b.meeting_title}</td>
                    <td>{b.room_name}</td>
                    <td>{b.employee_name}<div className="small text-muted">{b.department}</div></td>
                    <td>{formatDate(b.booking_date)}</td>
                    <td>{b.start_time} – {b.end_time}</td>
                    <td><StatusBadge state={b.status} /></td>
                    <td className="text-end text-nowrap">
                      <button className="btn btn-sm btn-outline-primary me-1" onClick={() => setSelected(b)}>
                        <i className="bi bi-eye me-1" />Details
                      </button>
                      {b.can_edit && (
                        <button className="btn btn-sm btn-outline-secondary me-1" onClick={() => setEditing(b)}>
                          <i className="bi bi-pencil me-1" />Edit
                        </button>
                      )}
                      {canCancel(b) && (
                        <button className="btn btn-sm btn-outline-danger" onClick={() => cancel(b)}>
                          <i className="bi bi-x-lg me-1" />Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}

      {selected && (
        <div className="modal-backdrop-custom" onClick={() => setSelected(null)}>
          <div className="card detail-modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <div className="card-header d-flex justify-content-between align-items-center">
              <span className="section-title">Booking #{selected.booking_id}</span>
              <button className="btn-close" aria-label="Close" onClick={() => setSelected(null)} />
            </div>
            <div className="card-body">
              <h2 className="h5 fw-bold">{selected.meeting_title}</h2>
              <div className="mb-3"><StatusBadge state={selected.status} /></div>
              <div className="detail-row"><span>Room</span><strong>{selected.room_name} · {selected.location}</strong></div>
              <div className="detail-row"><span>Capacity</span><strong>{selected.capacity} people</strong></div>
              <div className="detail-row"><span>Date</span><strong>{formatDate(selected.booking_date)}</strong></div>
              <div className="detail-row"><span>Time</span><strong>{selected.start_time} – {selected.end_time}</strong></div>
              <div className="detail-row"><span>Organiser</span><strong>{selected.employee_name}</strong></div>
              <div className="detail-row"><span>Email</span><strong>{selected.email}</strong></div>
              <div className="detail-row"><span>Department</span><strong>{selected.department}</strong></div>
              <div className="detail-row"><span>Booked on</span><strong>{formatTimestamp(selected.created_at)}</strong></div>
            </div>
            <div className="card-footer d-flex justify-content-end gap-2">
              {selected.can_edit && (
                <button className="btn btn-outline-secondary" onClick={() => { setEditing(selected); setSelected(null); }}>
                  <i className="bi bi-pencil me-1" />Edit booking
                </button>
              )}
              {canCancel(selected) && (
                <button className="btn btn-outline-danger" onClick={() => cancel(selected)}>
                  <i className="bi bi-x-lg me-1" />Cancel booking
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setSelected(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {editing && (
        <EditBookingModal booking={editing} rooms={rooms} onClose={() => setEditing(null)} onSaved={saved} />
      )}
    </>
  );
}
