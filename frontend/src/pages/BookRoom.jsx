import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../api.js';
import { Alert, PageHeader, Spinner } from '../components/common.jsx';
import { toPayload, validateBookingForm } from '../bookingForm.js';
import { timeOptions, todayISO } from '../utils.js';

const TIMES = timeOptions('08:00', '18:30');

const emptyForm = (prefill = {}) => ({
  room_id: prefill.roomId ? String(prefill.roomId) : '',
  employee_name: '',
  employee_email: '',
  department: '',
  meeting_title: '',
  booking_date: prefill.date || todayISO(),
  start_time: prefill.start || '10:00',
  end_time: prefill.end || '11:00',
});

export default function BookRoom() {
  const location = useLocation();
  const [rooms, setRooms] = useState(null);
  const [form, setForm] = useState(() => emptyForm(location.state || {}));
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [success, setSuccess] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.rooms(false).then(setRooms).catch((e) => setSubmitError(e.message));
  }, []);

  const selectedRoom = useMemo(
    () => rooms?.find((r) => String(r.room_id) === form.room_id),
    [rooms, form.room_id],
  );

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setSubmitError('');
    setSuccess(null);
    const found = validateBookingForm(form);
    setErrors(found);
    if (Object.keys(found).length) return;

    setSaving(true);
    try {
      const booking = await api.createBooking(toPayload(form));
      setSuccess(booking);
      setForm((prev) => ({ ...emptyForm(), room_id: prev.room_id, booking_date: prev.booking_date }));
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!rooms && !submitError) return <Spinner />;

  return (
    <>
      <PageHeader title="Book a Meeting Room" subtitle="Reserve a room for a date and time. Overlapping bookings are blocked automatically." />
      <div className="row g-4">
        <div className="col-lg-8">
          <form className="card" onSubmit={submit} noValidate>
            <div className="card-header"><span className="section-title">Booking details</span></div>
            <div className="card-body">
              <Alert onClose={() => setSubmitError('')}>{submitError}</Alert>
              {success && (
                <Alert kind="success" onClose={() => setSuccess(null)}>
                  <strong>Booked.</strong> {success.room_name}, {success.booking_date}, {success.start_time}–{success.end_time} for “{success.meeting_title}”.
                </Alert>
              )}
              <div className="row g-3">
                <div className="col-12">
                  <label className="form-label" htmlFor="b-room">Meeting room</label>
                  <select id="b-room" className={`form-select ${errors.room_id ? 'is-invalid' : ''}`} value={form.room_id} onChange={set('room_id')}>
                    <option value="">Choose a room…</option>
                    {rooms?.map((r) => (
                      <option key={r.room_id} value={r.room_id}>{r.room_name} · {r.location} · {r.capacity} seats</option>
                    ))}
                  </select>
                  <div className="invalid-feedback">{errors.room_id}</div>
                </div>
                <div className="col-md-6">
                  <label className="form-label" htmlFor="b-name">Your name</label>
                  <input id="b-name" className={`form-control ${errors.employee_name ? 'is-invalid' : ''}`} value={form.employee_name} onChange={set('employee_name')} />
                  <div className="invalid-feedback">{errors.employee_name}</div>
                </div>
                <div className="col-md-6">
                  <label className="form-label" htmlFor="b-email">Work email</label>
                  <input id="b-email" type="email" className={`form-control ${errors.employee_email ? 'is-invalid' : ''}`} value={form.employee_email} onChange={set('employee_email')} />
                  <div className="invalid-feedback">{errors.employee_email}</div>
                </div>
                <div className="col-md-6">
                  <label className="form-label" htmlFor="b-dept">Department <span className="text-muted small">(optional)</span></label>
                  <input id="b-dept" className="form-control" value={form.department} onChange={set('department')} />
                </div>
                <div className="col-md-6">
                  <label className="form-label" htmlFor="b-title">Meeting title</label>
                  <input id="b-title" className={`form-control ${errors.meeting_title ? 'is-invalid' : ''}`} value={form.meeting_title} onChange={set('meeting_title')} />
                  <div className="invalid-feedback">{errors.meeting_title}</div>
                </div>
                <div className="col-md-4">
                  <label className="form-label" htmlFor="b-date">Date</label>
                  <input id="b-date" type="date" min={todayISO()} className={`form-control ${errors.booking_date ? 'is-invalid' : ''}`} value={form.booking_date} onChange={set('booking_date')} />
                  <div className="invalid-feedback">{errors.booking_date}</div>
                </div>
                <div className="col-md-4">
                  <label className="form-label" htmlFor="b-start">Start</label>
                  <select id="b-start" className={`form-select ${errors.start_time ? 'is-invalid' : ''}`} value={form.start_time} onChange={set('start_time')}>
                    {TIMES.map((t) => <option key={t}>{t}</option>)}
                  </select>
                  <div className="invalid-feedback">{errors.start_time}</div>
                </div>
                <div className="col-md-4">
                  <label className="form-label" htmlFor="b-end">End</label>
                  <select id="b-end" className={`form-select ${errors.end_time ? 'is-invalid' : ''}`} value={form.end_time} onChange={set('end_time')}>
                    {TIMES.map((t) => <option key={t}>{t}</option>)}
                  </select>
                  <div className="invalid-feedback">{errors.end_time}</div>
                </div>
              </div>
            </div>
            <div className="card-footer d-flex justify-content-end gap-2">
              <button type="button" className="btn btn-outline-secondary" onClick={() => { setForm(emptyForm()); setErrors({}); setSubmitError(''); }}>Reset</button>
              <button className="btn btn-primary px-4" disabled={saving}>
                <i className="bi bi-check2-circle me-2" />{saving ? 'Booking…' : 'Confirm booking'}
              </button>
            </div>
          </form>
        </div>

        <div className="col-lg-4">
          <div className="card h-100">
            <div className="card-header"><span className="section-title">Room details</span></div>
            <div className="card-body">
              {selectedRoom ? (
                <>
                  <h2 className="h5 fw-bold">{selectedRoom.room_name}</h2>
                  <p className="text-muted mb-3"><i className="bi bi-geo-alt me-1" />{selectedRoom.location}</p>
                  <div className="detail-row"><span>Capacity</span><strong>{selectedRoom.capacity} people</strong></div>
                  <div className="detail-row"><span>Status</span><strong className="text-success">Active</strong></div>
                  <div className="mt-3 small text-muted mb-2">Facilities</div>
                  <div className="d-flex flex-wrap gap-1">
                    {selectedRoom.facilities.length
                      ? selectedRoom.facilities.map((f) => <span key={f} className="facility-tag">{f}</span>)
                      : <span className="text-muted small">None listed</span>}
                  </div>
                </>
              ) : (
                <div className="text-muted small">Select a room to see its capacity and facilities.</div>
              )}
              <hr />
              <div className="small text-muted">
                <i className="bi bi-info-circle me-1" />
                Bookings run in 30-minute slots. Back-to-back meetings are allowed (e.g. 10:00–11:00 then 11:00–12:00). Past dates and times are blocked.
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
