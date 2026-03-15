import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, RotateCcw, AlertTriangle } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetFailedGenerations, adminRetryGeneration } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

export default function FailedGenerationsPage() {
    const [page, setPage] = useState(1);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [retrying, setRetrying] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetFailedGenerations(page);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page]);

    useEffect(() => { load(); }, [load]);

    const handleRetry = async (e, logId) => {
        e.stopPropagation();
        setRetrying(logId);
        try { await adminRetryGeneration(logId); load(); } catch {}
        setRetrying(null);
    };

    const items = Array.isArray(data) ? data : data?.failed_generations || data?.items || data?.generations || [];
    const total = data?.total || items.length;

    const columns = [
        { key: 'id', label: 'ID', width: 60 },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'error_message', label: 'Error', render: v => (
            <span style={{ color: '#f87171', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>
                {v || '—'}
            </span>
        )},
        { key: 'duration_ms', label: 'Duration', render: v => v ? `${(v / 1000).toFixed(1)}s` : '—' },
        { key: 'created_at', label: 'Failed At', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
        {
            key: 'actions', label: 'Actions', sortable: false,
            render: (_, row) => (
                <button
                    className="admin-btn admin-btn-sm admin-btn-primary"
                    onClick={(e) => handleRetry(e, row.id)}
                    disabled={retrying === row.id}
                >
                    <RotateCcw size={12} /> {retrying === row.id ? '...' : 'Retry'}
                </button>
            ),
        },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title"><AlertTriangle size={20} style={{ marginRight: 8, color: '#f87171' }} /> Failed Generations</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <AdminTable
                columns={columns}
                data={items}
                loading={loading}
                emptyMessage="No failed generations"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
            />
        </div>
    );
}
