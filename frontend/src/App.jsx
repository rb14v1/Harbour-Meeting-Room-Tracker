import { Route, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Availability from './pages/Availability.jsx';
import BookRoom from './pages/BookRoom.jsx';
import Bookings from './pages/Bookings.jsx';
import Rooms from './pages/Rooms.jsx';
import Reports from './pages/Reports.jsx';

export default function App() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/availability" element={<Availability />} />
          <Route path="/book" element={<BookRoom />} />
          <Route path="/bookings" element={<Bookings />} />
          <Route path="/rooms" element={<Rooms />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="*" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  );
}
