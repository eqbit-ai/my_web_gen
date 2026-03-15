import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Plus, Edit3, Trash2, X, Eye } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetAnnouncements, adminCreateAnnouncement, adminUpdateAnnouncement, adminDeleteAnnouncement } from '../../services/adminApi';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', danger: '#f87171' };

export default function AnnouncementsPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [form, setForm] = useState({ title: '', message: '', type: 'info', is_active: true });
    const [saving, setSaving] = useState(false);
    const [preview, setPreview] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetAnnouncements();
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const announcements = Array.isArray(data) ? data : data?.announcements || data?.items || [];

    const handleSave = async () => {
        setSaving(true);
        try {
            if (editingId) await adminUpdateAnnouncement(editingId, form);
            else await adminCreateAnnouncement(form);
            setShowModal(false);
            setEditingId(null);
            setForm({ title: '', message: '', type: 'info', is_active: true });
            load();
        } catch {}
        setSaving(false);
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Delete this announcement?')) return;
        try { await adminDeleteAnnouncement(id); load(); } catch {}
    };

    const startEdit = (a) => {
        setEditingId(a.id);
        setForm({ title: a.title, message: a.message || '', type: a.type || 'info', is_active: a.is_active !== false });
        setShowModal(true);
    };

    const startCreate = () => {
        setEditingId(null);
        setForm({ title: '', message: '', type: 'info', is_active: true });
        setShowModal(true);
    };

    const typeColors = { info: T.accent, warning: '#fbbf24', success: '#34d399', maintenance: '#f59e0b' };

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Announcements</h1>
                <div className="admin-actions">
                    <button className="admin-btn admin-btn-primary" onClick={startCreate}><Plus size={14} /> New Announcement</button>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {/* Create/Edit Modal */}
            {showModal && (
                <>
                    <div className="admin-modal-backdrop" onClick={() => setShowModal(false)} />
                    <div className="admin-modal" style={{ width: 520 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                            <h3>{editingId ? 'Edit' : 'New'} Announcement</h3>
                            <button className="admin-btn admin-btn-sm" onClick={() => setShowModal(false)}><X size={14} /></button>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div>
                                <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Title</label>
                                <input className="admin-input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
                            </div>
                            <div>
                                <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Message</label>
                                <textarea className="admin-input" style={{ minHeight: 100, resize: 'vertical' }} value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} />
                            </div>
                            <div style={{ display: 'flex', gap: 12 }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Type</label>
                                    <select className="admin-input" value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}>
                                        <option value="info">Info</option>
                                        <option value="warning">Warning</option>
                                        <option value="maintenance">Maintenance</option>
                                        <option value="success">Success</option>
                                    </select>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: T.muted, fontSize: 13, cursor: 'pointer' }}>
                                        <input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} />
                                        Active
                                    </label>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                                <button className="admin-btn admin-btn-primary" onClick={handleSave} disabled={saving || !form.title || !form.message}>
                                    {saving ? 'Saving...' : 'Save'}
                                </button>
                                <button className="admin-btn" onClick={() => setShowModal(false)}>Cancel</button>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* Preview Modal */}
            {preview && (
                <>
                    <div className="admin-modal-backdrop" onClick={() => setPreview(null)} />
                    <div className="admin-modal">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                            <h3>{preview.title}</h3>
                            <button className="admin-btn admin-btn-sm" onClick={() => setPreview(null)}><X size={14} /></button>
                        </div>
                        <div style={{
                            padding: 16,
                            borderRadius: 8,
                            border: `1px solid ${typeColors[preview.type] || T.accent}40`,
                            background: `${typeColors[preview.type] || T.accent}10`,
                            color: typeColors[preview.type] || T.text,
                            fontSize: 14,
                            lineHeight: 1.6,
                        }}>
                            {preview.message}
                        </div>
                    </div>
                </>
            )}

            {/* Announcements List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {announcements.map(a => (
                    <div key={a.id} className="admin-card">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                    <strong style={{ color: T.text, fontSize: 15 }}>{a.title}</strong>
                                    <StatusBadge status={a.is_active !== false ? 'active' : 'inactive'} size="sm" />
                                    <StatusBadge status={a.type || 'info'} size="sm" />
                                </div>
                                <p style={{ color: T.muted, fontSize: 13, margin: 0, lineHeight: 1.5 }}>{a.message}</p>
                            </div>
                            <div className="admin-actions">
                                <button className="admin-btn admin-btn-sm" onClick={() => setPreview(a)}><Eye size={12} /></button>
                                <button className="admin-btn admin-btn-sm" onClick={() => startEdit(a)}><Edit3 size={12} /></button>
                                <button className="admin-btn admin-btn-sm admin-btn-danger" onClick={() => handleDelete(a.id)}><Trash2 size={12} /></button>
                            </div>
                        </div>
                    </div>
                ))}
                {announcements.length === 0 && <div className="admin-card"><div className="admin-empty">No announcements</div></div>}
            </div>
        </div>
    );
}
