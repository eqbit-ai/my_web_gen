import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { RefreshCw, RotateCcw, Trash2, Globe, FolderOpen, Search, ChevronDown, ChevronRight, User, Clock } from 'lucide-react';
import { adminGetDeletedItems, adminRestoreDeletedSite, adminRestoreDeletedProject, adminPurgeDeletedSite } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a' };

const PURGE_DAYS = 15;

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const then = new Date(dateStr);
    const diffMs = now - then;
    const mins = Math.floor(diffMs / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    const months = Math.floor(days / 30);
    return `${months}mo ago`;
}

function daysLeft(dateStr) {
    if (!dateStr) return PURGE_DAYS;
    const deletedAt = new Date(dateStr);
    const purgeAt = new Date(deletedAt.getTime() + PURGE_DAYS * 24 * 60 * 60 * 1000);
    const now = new Date();
    const remaining = Math.ceil((purgeAt - now) / (24 * 60 * 60 * 1000));
    return Math.max(0, remaining);
}

export default function TrashPage() {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState({});
    const [msg, setMsg] = useState(null);
    const [search, setSearch] = useState('');
    const [collapsedUsers, setCollapsedUsers] = useState({});

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

    // Filter by search
    const filtered = useMemo(() => {
        if (!search) return items;
        const q = search.toLowerCase();
        return items.filter(item =>
            (item.name || '').toLowerCase().includes(q) ||
            (item.user_name || '').toLowerCase().includes(q) ||
            (item.user_email || '').toLowerCase().includes(q) ||
            (item.type || '').toLowerCase().includes(q)
        );
    }, [items, search]);

    // Group by user
    const grouped = useMemo(() => {
        const map = {};
        for (const item of filtered) {
            const userKey = item.user_id || 'unknown';
            if (!map[userKey]) {
                map[userKey] = {
                    userId: userKey,
                    userName: item.user_name || item.user_email || 'Unknown User',
                    userEmail: item.user_email || '',
                    items: [],
                };
            }
            map[userKey].items.push(item);
        }
        // Sort users by most recent deletion
        return Object.values(map).sort((a, b) => {
            const aDate = a.items[0]?.deleted_at || '';
            const bDate = b.items[0]?.deleted_at || '';
            return bDate.localeCompare(aDate);
        });
    }, [filtered]);

    const toggleUser = (userId) => {
        setCollapsedUsers(prev => ({ ...prev, [userId]: !prev[userId] }));
    };

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

    const totalSites = items.filter(i => i.type === 'site').length;
    const totalProjects = items.filter(i => i.type === 'project').length;

    return (
        <div>
            <div className="admin-page-header">
                <div>
                    <h1 className="admin-page-title">Trash</h1>
                    <p style={{ color: T.muted, fontSize: 13, marginTop: 4 }}>
                        Deleted sites and projects — auto-purged after {PURGE_DAYS} days
                    </p>
                </div>
                <button className="admin-btn" onClick={load} disabled={loading}>
                    <RefreshCw size={14} className={loading ? 'admin-spinner' : ''} /> Refresh
                </button>
            </div>

            {/* Summary cards */}
            {items.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 20 }}>
                    <div className="admin-card" style={{ padding: '16px 20px', borderLeft: '3px solid #818cf8' }}>
                        <div style={{ fontSize: 24, fontWeight: 700, color: '#818cf8' }}>{totalSites}</div>
                        <div style={{ fontSize: 11, color: T.muted, fontWeight: 600, textTransform: 'uppercase', marginTop: 2 }}>Deleted Sites</div>
                    </div>
                    <div className="admin-card" style={{ padding: '16px 20px', borderLeft: '3px solid #fbbf24' }}>
                        <div style={{ fontSize: 24, fontWeight: 700, color: '#fbbf24' }}>{totalProjects}</div>
                        <div style={{ fontSize: 11, color: T.muted, fontWeight: 600, textTransform: 'uppercase', marginTop: 2 }}>Deleted Projects</div>
                    </div>
                    <div className="admin-card" style={{ padding: '16px 20px', borderLeft: '3px solid #22c55e' }}>
                        <div style={{ fontSize: 24, fontWeight: 700, color: '#22c55e' }}>{grouped.length}</div>
                        <div style={{ fontSize: 11, color: T.muted, fontWeight: 600, textTransform: 'uppercase', marginTop: 2 }}>Users Affected</div>
                    </div>
                </div>
            )}

            {msg && (
                <div className={`admin-alert ${msg.type === 'success' ? 'admin-alert-success' : 'admin-alert-error'}`} style={{ marginBottom: 16 }}>
                    {msg.text}
                </div>
            )}

            {error && (
                <div className="admin-alert admin-alert-error" style={{ marginBottom: 16 }}>{error}</div>
            )}

            {/* Search */}
            {items.length > 0 && (
                <div style={{ marginBottom: 16, position: 'relative' }}>
                    <Search size={14} style={{ position: 'absolute', left: 12, top: 10, color: T.muted }} />
                    <input
                        type="text"
                        placeholder="Search by name, user, email, or type..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        style={{
                            width: '100%', maxWidth: 400, padding: '8px 12px 8px 32px',
                            background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8,
                            color: T.text, fontSize: 13, outline: 'none',
                        }}
                    />
                </div>
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
            ) : filtered.length === 0 ? (
                <div style={{ padding: 60, textAlign: 'center', color: T.muted }}>
                    No results matching "{search}"
                </div>
            ) : (
                <div style={{ display: 'grid', gap: 12 }}>
                    {grouped.map(group => {
                        const isCollapsed = collapsedUsers[group.userId];
                        return (
                            <div key={group.userId} className="admin-card" style={{ padding: 0, overflow: 'hidden' }}>
                                {/* User header */}
                                <div
                                    onClick={() => toggleUser(group.userId)}
                                    style={{
                                        padding: '14px 20px', cursor: 'pointer',
                                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                        background: 'rgba(255,255,255,0.02)',
                                        borderBottom: isCollapsed ? 'none' : `1px solid ${T.border}`,
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        {isCollapsed ? <ChevronRight size={16} style={{ color: T.muted }} /> : <ChevronDown size={16} style={{ color: T.muted }} />}
                                        <div style={{
                                            width: 32, height: 32, borderRadius: '50%',
                                            background: 'rgba(129,140,248,0.12)', display: 'flex',
                                            alignItems: 'center', justifyContent: 'center', color: '#818cf8',
                                        }}>
                                            <User size={14} />
                                        </div>
                                        <div>
                                            <div style={{ fontWeight: 600, color: T.text, fontSize: 14 }}>{group.userName}</div>
                                            {group.userEmail && group.userName !== group.userEmail && (
                                                <div style={{ fontSize: 11, color: T.muted }}>{group.userEmail}</div>
                                            )}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <span style={{
                                            fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 12,
                                            background: 'rgba(255,255,255,0.06)', color: T.muted,
                                        }}>
                                            {group.items.length} item{group.items.length !== 1 ? 's' : ''}
                                        </span>
                                    </div>
                                </div>

                                {/* Items list */}
                                {!isCollapsed && (
                                    <div>
                                        {group.items.map(item => {
                                            const key = `${item.type}-${item.id}`;
                                            const isLoading = actionLoading[key];
                                            return (
                                                <div key={key} style={{
                                                    padding: '12px 20px 12px 52px',
                                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                                    borderBottom: `1px solid ${T.border}`,
                                                }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
                                                        <div style={{
                                                            width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                                                            background: item.type === 'site' ? 'rgba(129,140,248,0.1)' : 'rgba(251,191,36,0.1)',
                                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                            color: item.type === 'site' ? '#818cf8' : '#fbbf24',
                                                        }}>
                                                            {item.type === 'site' ? <Globe size={14} /> : <FolderOpen size={14} />}
                                                        </div>
                                                        <div style={{ minWidth: 0 }}>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                                                <span style={{ fontWeight: 600, color: T.text, fontSize: 13 }}>{item.name}</span>
                                                                <span style={{
                                                                    fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                                                                    color: item.type === 'site' ? '#818cf8' : '#fbbf24',
                                                                    background: item.type === 'site' ? 'rgba(129,140,248,0.12)' : 'rgba(251,191,36,0.12)',
                                                                    textTransform: 'uppercase', letterSpacing: '0.05em',
                                                                }}>
                                                                    {item.type}
                                                                </span>
                                                            </div>
                                                            <div style={{ fontSize: 11, color: T.muted, marginTop: 2, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                                                <Clock size={10} />
                                                                <span>Deleted {timeAgo(item.deleted_at)}</span>
                                                                <span style={{ color: 'rgba(255,255,255,0.15)' }}>|</span>
                                                                <span>{formatDate(item.deleted_at)}</span>
                                                                <span style={{ color: 'rgba(255,255,255,0.15)' }}>|</span>
                                                                {(() => {
                                                                    const dl = daysLeft(item.deleted_at);
                                                                    const color = dl <= 3 ? '#ef4444' : dl <= 7 ? '#f59e0b' : T.muted;
                                                                    return <span style={{ color, fontWeight: dl <= 3 ? 600 : 400 }}>
                                                                        {dl === 0 ? 'Purging soon' : `${dl}d until auto-purge`}
                                                                    </span>;
                                                                })()}
                                                                {item.type === 'project' && !item.has_content && (
                                                                    <>
                                                                        <span style={{ color: 'rgba(255,255,255,0.15)' }}>|</span>
                                                                        <span style={{ color: '#f59e0b' }}>Empty</span>
                                                                    </>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
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
                    })}
                </div>
            )}

            <div style={{ color: T.muted, fontSize: 11, marginTop: 16, textAlign: 'right' }}>
                {filtered.length} item{filtered.length !== 1 ? 's' : ''} in trash
                {search && ` (filtered from ${items.length})`}
            </div>
        </div>
    );
}
