import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, RotateCcw, Trash2, Globe, FolderOpen } from 'lucide-react';
import { adminGetDeletedItems, adminRestoreDeletedSite, adminRestoreDeletedProject, adminPurgeDeletedSite } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a' };

export default function TrashPage() {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState({});
    const [msg, setMsg] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetDeletedItems();
            setItems(res.items || []);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleRestore = async (item) => {
        const key = `${item.type}-${item.id}`;
        setActionLoading(prev => ({ ...prev, [key]: 'restore' }));
        setMsg(null);
        try {
            if (item.type === 'site') {
                await adminRestoreDeletedSite(item.id);
            } else {
                await adminRestoreDeletedProject(item.id, item.db_schema);
            }
            setMsg({ type: 'success', text: `${item.type === 'site' ? 'Site' : 'Project'} "${item.name}" restored successfully` });
            setItems(prev => prev.filter(i => !(i.type === item.type && i.id === item.id)));
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        }
        setActionLoading(prev => ({ ...prev, [key]: null }));
    };

    const handlePurge = async (item) => {
        if (!window.confirm(`Permanently delete "${item.name}"? This cannot be undone.`)) return;
        const key = `${item.type}-${item.id}`;
        setActionLoading(prev => ({ ...prev, [key]: 'purge' }));
        setMsg(null);
        try {
            if (item.type === 'site') {
                await adminPurgeDeletedSite(item.id);
            }
            setMsg({ type: 'success', text: `"${item.name}" permanently deleted` });
            setItems(prev => prev.filter(i => !(i.type === item.type && i.id === item.id)));
        } catch (e) {
            setMsg({ type: 'error', text: e.message });
        }
        setActionLoading(prev => ({ ...prev, [key]: null }));
    };

    return (
        <div>
            <div className="admin-page-header">
                <div>
                    <h1 className="admin-page-title">Trash</h1>
                    <p style={{ color: T.muted, fontSize: 13, marginTop: 4 }}>
                        Deleted sites and projects can be restored here
                    </p>
                </div>
                <button className="admin-btn" onClick={load} disabled={loading}>
                    <RefreshCw size={14} className={loading ? 'admin-spinner' : ''} /> Refresh
                </button>
            </div>

            {msg && (
                <div className={`admin-alert ${msg.type === 'success' ? 'admin-alert-success' : 'admin-alert-error'}`} style={{ marginBottom: 16 }}>
                    {msg.text}
                </div>
            )}

            {error && (
                <div className="admin-alert admin-alert-error" style={{ marginBottom: 16 }}>{error}</div>
            )}

            {loading ? (
                <div style={{ padding: 60, textAlign: 'center', color: T.muted }}>
                    <RefreshCw size={20} className="admin-spinner" style={{ marginBottom: 12 }} />
                    <p>Loading...</p>
                </div>
            ) : items.length === 0 ? (
                <div style={{ padding: 80, textAlign: 'center' }}>
                    <Trash2 size={48} style={{ color: T.muted, marginBottom: 16 }} />
                    <h3 style={{ color: T.text, marginBottom: 8 }}>Trash is empty</h3>
                    <p style={{ color: T.muted }}>No deleted sites or projects</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gap: 8 }}>
                    {items.map(item => {
                        const key = `${item.type}-${item.id}`;
                        const isLoading = actionLoading[key];
                        return (
                            <div key={key} style={{
                                background: T.surface, border: `1px solid ${T.border}`, borderRadius: 10,
                                padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 14, flex: 1, minWidth: 0 }}>
                                    <div style={{
                                        width: 40, height: 40, borderRadius: '50%',
                                        background: item.type === 'site' ? 'rgba(129,140,248,0.12)' : 'rgba(251,191,36,0.12)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        color: item.type === 'site' ? '#818cf8' : '#fbbf24', flexShrink: 0,
                                    }}>
                                        {item.type === 'site' ? <Globe size={18} /> : <FolderOpen size={18} />}
                                    </div>
                                    <div style={{ minWidth: 0 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                            <strong style={{ color: T.text, fontSize: 14 }}>{item.name}</strong>
                                            <span style={{
                                                fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 4,
                                                color: item.type === 'site' ? '#818cf8' : '#fbbf24',
                                                background: item.type === 'site' ? 'rgba(129,140,248,0.12)' : 'rgba(251,191,36,0.12)',
                                            }}>
                                                {item.type === 'site' ? 'Site' : 'Project'}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: 12, color: T.muted, marginTop: 2, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                            <span>{item.user_name || item.user_email}</span>
                                            <span>Deleted {formatDate(item.deleted_at)}</span>
                                        </div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                                    <button
                                        className="admin-btn admin-btn-sm"
                                        onClick={() => handleRestore(item)}
                                        disabled={!!isLoading}
                                        style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#22c55e', borderColor: '#22c55e' }}
                                    >
                                        <RotateCcw size={12} />
                                        {isLoading === 'restore' ? 'Restoring...' : 'Restore'}
                                    </button>
                                    {item.type === 'site' && (
                                        <button
                                            className="admin-btn admin-btn-sm"
                                            onClick={() => handlePurge(item)}
                                            disabled={!!isLoading}
                                            style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#ef4444', borderColor: '#ef4444' }}
                                        >
                                            <Trash2 size={12} />
                                            {isLoading === 'purge' ? 'Deleting...' : 'Purge'}
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
