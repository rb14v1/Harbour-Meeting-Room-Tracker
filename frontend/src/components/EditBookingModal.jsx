import { useState } from 'react';
import { api } from '../api.js';
import { Alert } from './common.jsx';
import { toPayload, validateBookingForm } from '../bookingForm.js';
import { timeOptions, todayISO } from '../utils.js';

const TIMES = timeOptions('08:00', '18:30');

export default function EditBookingModal({ booking, rooms, onClose, onSaved }) {
  const [form, setForm] = useState({
    room_id: String(booking.room_id),
    employee_name: booking.employee_name,
    employee_email: booking.email,
    department: booking.department,
    meeting_title: booking.meeting_title,
    booking_date: booking.booking_date,
    start_time: booking.start_time,
    end_time: booking.end_time,
  });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [saving, setSaving] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const roomOptions = rooms.filter((r) => r.status === 'Active' || r.room_id === booking.room_id);

  const submit = async (e) => {
    e.preventDefault();
    setSubmitError('');
    const found = validateBookingForm(form);
    setErrors(found);
    if (Object.keys(found).length) return;

    setSaving(true);
    try {
      const updated = await api.updateBooking(booking.booking_id, toPayload(form));
      onSaved(updated);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop-custom" onClick={onClose}>
      <form className="card detail-modal" role="dialog" aria-modal="true" noValidate
        onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <div className="card-header d-flex justify-content-between align-items-center">
          <span className="section-title">Edit booking #{booking.booking_id}</span>
          <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />
        </div>
        <div className="card-body">
          <Alert onClose={() => setSubmitError('')}>{submitError}</Alert>
          <div className="row g-3">
            <div className="col-12">
              <label className="form-label" htmlFor="e-room">Meeting room</label>
              <select id="e-room" className={`form-select ${errors.room_id ? 'is-invalid' : ''}`} value={form.room_id} onChange={set('room_id')}>
                {roomOptions.map((r) => (
                  <option key={r.room_id} value={r.room_id}>{r.room_name} · {r.capacity} seats{r.status !== 'Active' ? ' (inactive)' : ''}</option>
                ))}
              </select>
              <div className="invalid-feedback">{errors.room_id}</div>
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="e-name">Employee name</label>
              <input id="e-name" className={`form-control ${errors.employee_name ? 'is-invalid' : ''}`} value={form.employee_name} onChange={set('employee_name')} />
              <div className="invalid-feedback">{errors.employee_name}</div>
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="e-email">Work email</label>
              <input id="e-email" type="email" className={`form-control ${errors.employee_email ? 'is-invalid' : ''}`} value={form.employee_email} onChange={set('employee_email')} />
              <div className="invalid-feedback">{errors.employee_email}</div>
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="e-dept">Department</label>
              <input id="e-dept" className="form-control" value={form.department} onChange={set('department')} />
            </div>
            <div className="col-md-6">
              <label className="form-label" htmlFor="e-title">Meeting title</label>
              <input id="e-title" className={`form-control ${errors.meeting_title ? 'is-invalid' : ''}`} value={form.meeting_title} onChange={set('meeting_title')} />
              <div className="invalid-feedback">{errors.meeting_title}</div>
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="e-date">Date</label>
              <input id="e-date" type="date" min={todayISO()} className={`form-control ${errors.booking_date ? 'is-invalid' : ''}`} value={form.booking_date} onChange={set('booking_date')} />
              <div className="invalid-feedback">{errors.booking_date}</div>
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="e-start">Start</label>
              <select id="e-start" className={`form-select ${errors.start_time ? 'is-invalid' : ''}`} value={form.start_time} onChange={set('start_time')}>
                {TIMES.map((t) => <option key={t}>{t}</option>)}
              </select>
              <div className="invalid-feedback">{errors.start_time}</div>
            </div>
            <div className="col-md-4">
              <label className="form-label" htmlFor="e-end">End</label>
              <select id="e-end" className={`form-select ${errors.end_time ? 'is-invalid' : ''}`} value={form.end_time} onChange={set('end_time')}>
                {TIMES.map((t) => <option key={t}>{t}</option>)}
              </select>
              <div className="invalid-feedback">{errors.end_time}</div>
            </div>
          </div>
        </div>
        <div className="card-footer d-flex justify-content-end gap-2">
          <button type="button" className="btn btn-outline-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary px-4" disabled={saving}>
            <i className="bi bi-save me-2" />{saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
