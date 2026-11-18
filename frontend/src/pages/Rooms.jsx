import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { Alert, EmptyState, PageHeader, Spinner, StatusBadge } from '../components/common.jsx';

const FACILITY_OPTIONS = ['Projector', 'Wi-Fi', 'Whiteboard', 'TV Screen', 'Video Conferencing', 'Speakerphone'];
const BLANK = { room_name: '', location: '', capacity: 8, facilities: [], status: 'Active' };

export default function Rooms() {
  const [rooms, setRooms] = useState(null);
  const [editing, setEditing] = useState(null); // null | 'new' | room object
  const [form, setForm] = useState(BLANK);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => api.rooms().then(setRooms).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const open = (room) => {
    setError('');
    setEditing(room);
    setForm(room ? { ...room } : BLANK);
  };

  const toggleFacility = (f) => setForm((p) => ({
    ...p,
    facilities: p.facilities.includes(f) ? p.facilities.filter((x) => x !== f) : [...p.facilities, f],
  }));

  const save = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    const body = {
      room_name: form.room_name, location: form.location, capacity: Number(form.capacity),
      facilities: form.facilities, status: form.status,
    };
    try {
      if (editing === 'new') {
        await api.createRoom(body);
        setNotice(`Room “${body.room_name}” added.`);
      } else {
        await api.updateRoom(editing.room_id, body);
        setNotice(`Room “${body.room_name}” updated.`);
      }
      setEditing(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async (room) => {
    if (!window.confirm(`Remove “${room.room_name}”? Rooms with booking history are deactivated instead of deleted.`)) return;
    try {
      const res = await api.deleteRoom(room.room_id);
      setNotice(res.message);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <PageHeader
        title="Manage Meeting Rooms"
        subtitle="Add, edit and retire rooms. Inactive rooms stay visible but cannot be booked."
        actions={<button className="btn btn-primary" onClick={() => open('new')}><i className="bi bi-plus-lg me-2" />Add room</button>}
      />
      <Alert kind="success" onClose={() => setNotice('')}>{notice}</Alert>
      <Alert onClose={() => setError('')}>{!editing ? error : ''}</Alert>
      {!rooms && !error && <Spinner />}
      {rooms && rooms.length === 0 && <EmptyState icon="bi-door-closed" text="No rooms yet. Add the first one." />}
      {rooms && rooms.length > 0 && (
        <div className="card">
          <div className="table-responsive">
            <table className="table table-modern align-middle mb-0">
              <thead><tr><th>ID</th><th>Room</th><th>Location</th><th>Seats</th><th>Facilities</th><th>Status</th><th className="text-end">Actions</th></tr></thead>
              <tbody>
                {rooms.map((r) => (
                  <tr key={r.room_id}>
                    <td className="text-muted">#{r.room_id}</td>
                    <td className="fw-semibold">{r.room_name}</td>
                    <td>{r.location}</td>
                    <td>{r.capacity}</td>
                    <td><div className="d-flex flex-wrap gap-1">{r.facilities.map((f) => <span key={f} className="facility-tag">{f}</span>)}</div></td>
                    <td><StatusBadge state={r.status} /></td>
                    <td className="text-end text-nowrap">
                      <button className="btn btn-sm btn-outline-primary me-1" onClick={() => open(r)}><i className="bi bi-pencil me-1" />Edit</button>
                      <button className="btn btn-sm btn-outline-danger" onClick={() => remove(r)}><i className="bi bi-trash me-1" />Remove</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {editing && (
        <div className="modal-backdrop-custom" onClick={() => setEditing(null)}>
          <form className="card detail-modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()} onSubmit={save}>
            <div className="card-header d-flex justify-content-between align-items-center">
              <span className="section-title">{editing === 'new' ? 'Add meeting room' : `Edit ${editing.room_name}`}</span>
              <button type="button" className="btn-close" aria-label="Close" onClick={() => setEditing(null)} />
            </div>
            <div className="card-body">
              <Alert onClose={() => setError('')}>{error}</Alert>
              <div className="row g-3">
                <div className="col-md-6">
                  <label className="form-label" htmlFor="r-name">Room name</label>
                  <input id="r-name" className="form-control" required minLength={2} value={form.room_name} onChange={(e) => setForm({ ...form, room_name: e.target.value })} />
                </div>
                <div className="col-md-6">
                  <label className="form-label" htmlFor="r-loc">Floor / location</label>
                  <input id="r-loc" className="form-control" required minLength={2} value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
                </div>
                <div className="col-md-6">
                  <label className="form-label" htmlFor="r-cap">Seating capacity</label>
                  <input id="r-cap" type="number" min="1" max="500" className="form-control" required value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} />
                </div>
                <div className="col-md-6">
                  <label className="form-label" htmlFor="r-status">Status</label>
                  <select id="r-status" className="form-select" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                    <option>Active</option>
                    <option>Inactive</option>
                  </select>
                </div>
                <div className="col-12">
                  <div className="form-label">Facilities</div>
                  <div className="d-flex flex-wrap gap-2">
                    {FACILITY_OPTIONS.map((f) => (
                      <button type="button" key={f} onClick={() => toggleFacility(f)}
                        className={`chip ${form.facilities.includes(f) ? 'chip-active' : ''}`} aria-pressed={form.facilities.includes(f)}>
                        {form.facilities.includes(f) && <i className="bi bi-check me-1" />}{f}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="card-footer d-flex justify-content-end gap-2">
              <button type="button" className="btn btn-outline-secondary" onClick={() => setEditing(null)}>Cancel</button>
              <button className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save room'}</button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
