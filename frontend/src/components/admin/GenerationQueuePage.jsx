import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Clock } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetGenerationQueue } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

export default function GenerationQueuePage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetGenerationQueue();
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    // Auto-refresh every 10s
    useEffect(() => {
        const interval = setInterval(load, 10000);
        return () => clearInterval(interval);
    }, [load]);

    const queue = data?.active_jobs || data?.items || data?.queue || (Array.isArray(data) ? data : []);
    const summary = {
        pending: data?.pending || queue.filter(q => q.status === 'pending').length,
        processing: data?.processing || queue.filter(q => q.status === 'processing').length,
        failed: data?.failed || queue.filter(q => q.status === 'failed').length,
    };

    const columns = [
        { key: 'id', label: 'ID', width: 60 },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'stage', label: 'Stage', render: v => v || '—' },
        { key: 'progress', label: 'Progress', render: v => v != null ? `${v}%` : '—' },
        { key: 'created_at', label: 'Submitted', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Generation Queue</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className="admin-auto-refresh"><Clock size={12} /> Auto-refresh 10s</span>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
                <div className="admin-stat-card admin-stat-accent-orange">
                    <div className="admin-stat-icon"><Clock size={22} /></div>
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{summary.pending}</div>
                        <div className="admin-stat-label">Pending</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-blue">
                    <div className="admin-stat-icon"><RefreshCw size={22} /></div>
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{summary.processing}</div>
                        <div className="admin-stat-label">Processing</div>
                    </div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-icon" style={{ background: 'rgba(248,113,113,0.15)', color: '#f87171' }}><RefreshCw size={22} /></div>
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{summary.failed}</div>
                        <div className="admin-stat-label">Failed</div>
                    </div>
                </div>
            </div>

            <AdminTable
                columns={columns}
                data={queue}
                loading={loading}
                emptyMessage="Queue is empty"
            />
        </div>
    );
}
