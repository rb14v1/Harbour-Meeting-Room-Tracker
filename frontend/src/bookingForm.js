import { todayISO } from './utils.js';

export const NAME_RE = /^[A-Za-z]+(?: [A-Za-z]+)*$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function normaliseName(value) {
  return value.trim().split(/\s+/).join(' ');
}

function nowHM() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

export function validateBookingForm(form) {
  const e = {};
  if (!form.room_id) e.room_id = 'Select a room.';

  const name = normaliseName(form.employee_name);
  if (name.length < 2) e.employee_name = 'Enter your name.';
  else if (!NAME_RE.test(name)) e.employee_name = 'Use English letters and single spaces only.';

  if (!EMAIL_RE.test(form.employee_email.trim())) e.employee_email = 'Enter a valid email address.';
  if (form.meeting_title.trim().length < 3) e.meeting_title = 'Meeting title needs at least 3 characters.';

  if (!form.booking_date) e.booking_date = 'Select a date.';
  else if (form.booking_date < todayISO()) e.booking_date = 'Booking date cannot be in the past.';
  if (form.booking_date === todayISO() && form.start_time <= nowHM()) {
    e.start_time = 'Start time has already passed today.';
  }
  if (form.end_time <= form.start_time) e.end_time = 'End time must be later than start time.';
  return e;
}

export function toPayload(form) {
  return {
    room_id: Number(form.room_id),
    employee_name: normaliseName(form.employee_name),
    employee_email: form.employee_email.trim(),
    department: form.department.trim() || 'General',
    meeting_title: form.meeting_title.trim(),
    booking_date: form.booking_date,
    start_time: form.start_time,
    end_time: form.end_time,
  };
}
