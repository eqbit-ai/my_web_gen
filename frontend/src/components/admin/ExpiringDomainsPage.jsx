import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertTriangle, Clock } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetExpiringDomains } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch { return d; }
}

function daysUntil(d) {
    if (!d) return null;
    try {
        const diff = (new Date(d) - new Date()) / (1000 * 60 * 60 * 24);
        return Math.ceil(diff);
    } catch { return null; }
}

export default function ExpiringDomainsPage() {
    const [data7, setData7] = useState(null);
    const [data30, setData30] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [r7, r30] = await Promise.all([
                adminGetExpiringDomains(7),
                adminGetExpiringDomains(30),
            ]);
            setData7(r7);
            setData30(r30);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const list7 = Array.isArray(data7) ? data7 : data7?.domains || data7?.items || [];
    const list30raw = Array.isArray(data30) ? data30 : data30?.domains || data30?.items || [];
    // Filter 30-day list to exclude items already in 7-day list
    const ids7 = new Set(list7.map(d => d.id));
    const list30 = list30raw.filter(d => !ids7.has(d.id));

    const columns = [
        { key: 'domain', label: 'Domain', render: (v, row) => v || row.name || '—' },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'tld', label: 'TLD', render: v => v || '—' },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'expires_at', label: 'Expires', render: v => {
            const days = daysUntil(v);
            const color = days !== null && days <= 7 ? '#f87171' : '#fbbf24';
            return (
                <span style={{ color, fontWeight: 600, fontSize: 13 }}>
                    {formatDate(v)} {days !== null && `(${days}d)`}
                </span>
            );
        }},
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Expiring Domains</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Critical: 7 days */}
            <div style={{ marginBottom: 32 }}>
                <h2 className="admin-section-title" style={{ color: '#f87171' }}>
                    <AlertTriangle size={16} /> Expiring within 7 days ({list7.length})
                </h2>
                {list7.length > 0 ? (
                    <AdminTable columns={columns} data={list7} loading={loading} emptyMessage="None" />
                ) : (
                    <div className="admin-card"><div className="admin-empty">No domains expiring within 7 days</div></div>
                )}
            </div>

            {/* Warning: 8-30 days */}
            <div>
                <h2 className="admin-section-title" style={{ color: '#fbbf24' }}>
                    <Clock size={16} /> Expiring within 8-30 days ({list30.length})
                </h2>
                {list30.length > 0 ? (
                    <AdminTable columns={columns} data={list30} loading={loading && !data30} emptyMessage="None" />
                ) : (
                    <div className="admin-card"><div className="admin-empty">No domains expiring in this range</div></div>
                )}
            </div>
        </div>
    );
}
