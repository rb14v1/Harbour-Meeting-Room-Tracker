import { NavLink } from 'react-router-dom';

const LINKS = [
  { to: '/', label: 'Dashboard', icon: 'bi-grid-1x2-fill', end: true },
  { to: '/availability', label: 'Room Availability', icon: 'bi-search' },
  { to: '/book', label: 'Book a Room', icon: 'bi-calendar-plus' },
  { to: '/bookings', label: 'Bookings', icon: 'bi-list-check' },
  { to: '/rooms', label: 'Manage Rooms', icon: 'bi-door-open' },
  { to: '/reports', label: 'Reports', icon: 'bi-bar-chart-line' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar d-flex flex-column">
      <div className="brand d-flex align-items-center gap-2">
        <span className="brand-mark"><i className="bi bi-building" aria-hidden="true" /></span>
        <div>
          <div className="brand-name">Room Tracker</div>
          <div className="brand-sub">Meeting Rooms</div>
        </div>
      </div>
      <nav className="nav flex-column mt-3">
        {LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end} className="nav-link">
            <i className={`bi ${l.icon}`} aria-hidden="true" />
            <span>{l.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer mt-auto">
        <small>Internal tool · v1.0</small>
      </div>
    </aside>
  );
}
