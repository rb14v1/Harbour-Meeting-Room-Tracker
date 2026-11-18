import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { Alert, EmptyState, PageHeader, Spinner, StatCard } from '../components/common.jsx';
import { shortDate } from '../utils.js';

function BarChart({ items, labelKey, valueKey, format = (v) => v, tone = 'primary' }) {
  const max = Math.max(1, ...items.map((i) => i[valueKey]));
  return (
    <div className="bar-chart" role="img" aria-label="Bar chart">
      {items.map((i) => (
        <div className="bar-row" key={i[labelKey]}>
          <div className="bar-label" title={i[labelKey]}>{i[labelKey]}</div>
          <div className="bar-track">
            <div className={`bar-fill tone-${tone}`} style={{ width: `${(i[valueKey] / max) * 100}%` }} />
          </div>
          <div className="bar-value">{format(i[valueKey])}</div>
        </div>
      ))}
    </div>
  );
}

export default function Reports() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => { api.reports().then(setData).catch((e) => setError(e.message)); }, []);

  if (error) return <><PageHeader title="Reports" /><Alert>{error}</Alert></>;
  if (!data) return <><PageHeader title="Reports" /><Spinner /></>;

  const todayCount = data.daily[data.daily.length - 1]?.count ?? 0;
  const weekCount = data.weekly[data.weekly.length - 1]?.count ?? 0;
  const dailyItems = data.daily.map((d) => ({ ...d, label: shortDate(d.label) }));
  const weeklyItems = data.weekly.map((w) => ({ ...w, label: w.label.split(' to ')[0] }));

  return (
    <>
      <PageHeader title="Booking Reports" subtitle="Booking volume, room utilisation and employee activity." />

      <div className="row g-3 mb-4">
        <div className="col-6 col-xl-3"><StatCard icon="bi-calendar-day" label="Bookings today" value={todayCount} /></div>
        <div className="col-6 col-xl-3"><StatCard icon="bi-calendar-week" tone="info" label="Bookings this week" value={weekCount} /></div>
        <div className="col-6 col-xl-3">
          <StatCard icon="bi-trophy" tone="warning" label="Most booked room"
            value={data.most_booked_room ? data.most_booked_room.room_name : '—'}
            hint={data.most_booked_room ? `${data.most_booked_room.count} bookings` : 'No bookings yet'} />
        </div>
        <div className="col-6 col-xl-3"><StatCard icon="bi-person-check" tone="success" label="Active employees" value={data.employees.length} /></div>
      </div>

      <div className="row g-4 mb-4">
        <div className="col-lg-6">
          <div className="card h-100">
            <div className="card-header"><span className="section-title">Daily bookings (last 7 days)</span></div>
            <div className="card-body"><BarChart items={dailyItems} labelKey="label" valueKey="count" /></div>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="card h-100">
            <div className="card-header"><span className="section-title">Weekly bookings (last 4 weeks)</span></div>
            <div className="card-body"><BarChart items={weeklyItems} labelKey="label" valueKey="count" tone="info" /></div>
          </div>
        </div>
      </div>

      <div className="row g-4">
        <div className="col-lg-6">
          <div className="card h-100">
            <div className="card-header">
              <span className="section-title">Room utilisation</span>
              <span className="small text-muted ms-2">last {data.utilisation_window_days} days, 08:00–18:00</span>
            </div>
            <div className="card-body">
              {data.utilisation.length === 0 ? <EmptyState text="No rooms yet." /> : (
                <div className="bar-chart">
                  {data.utilisation.map((r) => (
                    <div className="bar-row" key={r.room_name}>
                      <div className="bar-label" title={r.room_name}>{r.room_name}{r.status !== 'Active' && <span className="text-muted small"> (inactive)</span>}</div>
                      <div className="bar-track">
                        <div className={`bar-fill ${r.utilisation_pct >= 50 ? 'tone-danger' : 'tone-success'}`} style={{ width: `${Math.min(100, r.utilisation_pct)}%` }} />
                      </div>
                      <div className="bar-value">{r.utilisation_pct}%</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="col-lg-6">
          <div className="card h-100">
            <div className="card-header"><span className="section-title">Employee booking statistics</span></div>
            <div className="table-responsive">
              <table className="table table-modern align-middle mb-0">
                <thead><tr><th>Employee</th><th>Department</th><th className="text-end">Confirmed</th><th className="text-end">Cancelled</th><th className="text-end">Hours booked</th></tr></thead>
                <tbody>
                  {data.employees.length === 0 && <tr><td colSpan="5" className="text-center text-muted py-4">No bookings yet.</td></tr>}
                  {data.employees.map((e) => (
                    <tr key={e.employee_name}>
                      <td className="fw-semibold">{e.employee_name}</td>
                      <td>{e.department}</td>
                      <td className="text-end">{e.confirmed}</td>
                      <td className="text-end">{e.cancelled}</td>
                      <td className="text-end">{e.hours}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
