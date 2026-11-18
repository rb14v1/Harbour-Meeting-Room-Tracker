import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { Alert, EmptyState, PageHeader, Spinner, StatCard, StatusBadge } from '../components/common.jsx';
import { formatDate, formatTimestamp, todayISO } from '../utils.js';

export default function Dashboard() {
  const [date, setDate] = useState(todayISO());
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setData(null);
    api.dashboard(date).then(setData).catch((e) => setError(e.message));
  }, [date]);

  const isToday = date === todayISO();

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle={`Room activity for ${formatDate(date)}`}
        actions={
          <>
            <input type="date" className="form-control" style={{ maxWidth: 180 }} value={date}
              onChange={(e) => e.target.value && setDate(e.target.value)} aria-label="Dashboard date" />
            <Link to="/book" className="btn btn-primary"><i className="bi bi-calendar-plus me-2" />New booking</Link>
          </>
        }
      />
      <Alert onClose={() => setError('')}>{error}</Alert>
      {!data && !error && <Spinner />}
      {data && (
        <>
          <div className="row g-3 mb-4">
            <div className="col-6 col-xl"><StatCard icon="bi-door-open" label="Total rooms" value={data.total_rooms} hint={`${data.inactive_rooms} inactive`} /></div>
            <div className="col-6 col-xl"><StatCard icon="bi-check-circle" tone="success" label={isToday ? 'Available now' : 'Active rooms'} value={data.available_now} hint={isToday ? 'Free at this moment' : ''} /></div>
            <div className="col-6 col-xl"><StatCard icon="bi-x-circle" tone="danger" label={isToday ? 'Occupied now' : 'Occupied'} value={data.occupied_now} hint={isToday ? 'In a meeting' : ''} /></div>
            <div className="col-6 col-xl"><StatCard icon="bi-calendar-check" tone="info" label="Bookings" value={data.bookings_today} hint="Confirmed this day" /></div>
            <div className="col-6 col-xl"><StatCard icon="bi-clock-history" tone="warning" label="Upcoming" value={data.upcoming_meetings.length} hint="Remaining today" /></div>
          </div>

          <div className="row g-4">
            <div className="col-xl-8">
              <div className="card h-100">
                <div className="card-header d-flex justify-content-between align-items-center">
                  <span className="section-title">Room availability overview</span>
                  <Link to="/availability" className="small">Check by time</Link>
                </div>
                <div className="card-body">
                  {data.room_overview.length === 0 ? <EmptyState text="No rooms configured yet." /> : (
                    <div className="row g-3">
                      {data.room_overview.map((r) => {
                        const state = !isToday ? 'Available' : r.occupied_now ? 'Occupied' : 'Available';
                        return (
                          <div className="col-md-6" key={r.room_id}>
                            <div className={`room-tile ${state === 'Occupied' ? 'tile-occupied' : 'tile-available'}`}>
                              <div className="d-flex justify-content-between align-items-start gap-2">
                                <div>
                                  <div className="fw-semibold">{r.room_name}</div>
                                  <div className="small text-muted">{r.location} · {r.capacity} seats</div>
                                </div>
                                <StatusBadge state={state} />
                              </div>
                              <div className="small mt-2">
                                {r.current_meeting && <div><i className="bi bi-record-circle text-danger me-1" />Now: {r.current_meeting.meeting_title} (until {r.current_meeting.end_time})</div>}
                                {r.next_meeting && <div className="text-muted"><i className="bi bi-clock me-1" />Next: {r.next_meeting.start_time} {r.next_meeting.meeting_title}</div>}
                                {!r.current_meeting && !r.next_meeting && <div className="text-muted">No meetings scheduled</div>}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="col-xl-4">
              <div className="card h-100">
                <div className="card-header"><span className="section-title">Upcoming meetings</span></div>
                <div className="card-body">
                  {data.upcoming_meetings.length === 0 ? <EmptyState icon="bi-calendar2-check" text="No more meetings for this day." /> : (
                    <ul className="timeline list-unstyled mb-0">
                      {data.upcoming_meetings.map((m) => (
                        <li key={m.booking_id}>
                          <div className="timeline-time">{m.start_time} – {m.end_time}</div>
                          <div className="fw-semibold">{m.meeting_title}</div>
                          <div className="small text-muted">{m.room_name} · {m.employee_name}</div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>

            <div className="col-12">
              <div className="card">
                <div className="card-header"><span className="section-title">Recent booking activity</span></div>
                <div className="table-responsive">
                  <table className="table table-modern align-middle mb-0">
                    <thead><tr><th>Booked</th><th>Meeting</th><th>Room</th><th>Employee</th><th>Date & time</th><th>Status</th></tr></thead>
                    <tbody>
                      {data.recent_activity.length === 0 && <tr><td colSpan="6" className="text-center text-muted py-4">No activity yet.</td></tr>}
                      {data.recent_activity.map((b) => (
                        <tr key={b.booking_id}>
                          <td className="text-muted small">{formatTimestamp(b.created_at)}</td>
                          <td className="fw-semibold">{b.meeting_title}</td>
                          <td>{b.room_name}</td>
                          <td>{b.employee_name}</td>
                          <td>{formatDate(b.booking_date)} · {b.start_time}–{b.end_time}</td>
                          <td><StatusBadge state={b.status} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
