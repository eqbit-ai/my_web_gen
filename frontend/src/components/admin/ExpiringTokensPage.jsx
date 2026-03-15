import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import AdminTable from './shared/AdminTable';
import { adminGetExpiringTokens } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { success: '#34d399', warning: '#fbbf24', danger: '#f87171', muted: '#71717a' };


function daysUntil(d) {
    if (!d) return null;
    try {
        const diff = (new Date(d) - new Date()) / (1000 * 60 * 60 * 24);
        return Math.ceil(diff);
    } catch { return null; }
}

function daysColor(days) {
    if (days === null) return T.muted;
    if (days <= 3) return T.danger;
    if (days <= 7) return '#fb923c';
    if (days <= 14) return T.warning;
    return T.success;
}

export default function ExpiringTokensPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetExpiringTokens();
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const items = Array.isArray(data) ? data : data?.grants || data?.tokens || data?.items || [];

    const columns = [
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'amount', label: 'Tokens', render: v => <strong style={{ fontSize: 14 }}>{v ?? '—'}</strong> },
        { key: 'expires_at', label: 'Expires', render: v => {
            const days = daysUntil(v);
            return (
                <span style={{ fontWeight: 600, color: daysColor(days) }}>
                    {formatDate(v)}
                </span>
            );
        }},
        { key: 'days_remaining', label: 'Days Left', sortable: true, render: (v, row) => {
            const days = v ?? daysUntil(row.expires_at);
            if (days === null) return '—';
            return (
                <span style={{ fontWeight: 700, color: daysColor(days), fontSize: 14 }}>
                    {days}d
                </span>
            );
        }},
        { key: 'reason', label: 'Reason', render: v => v || '—' },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">
                    <AlertTriangle size={20} style={{ marginRight: 8, color: T.warning }} />
                    Expiring Tokens
                </h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <div style={{ marginBottom: 16, color: T.muted, fontSize: 13 }}>
                {items.length} token grant(s) expiring soon
            </div>

            <AdminTable
                columns={columns}
                data={items}
                loading={loading}
                emptyMessage="No expiring tokens"
            />
        </div>
    );
}
