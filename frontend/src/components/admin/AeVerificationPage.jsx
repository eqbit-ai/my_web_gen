import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetAeQueue, adminVerifyDomain } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

export default function AeVerificationPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetAeQueue();
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleVerify = async (domainId, status) => {
        setActionLoading(domainId);
        try { await adminVerifyDomain(domainId, status); load(); } catch {}
        setActionLoading(null);
    };

    const queue = Array.isArray(data) ? data : data?.domains || data?.items || [];

    const columns = [
        { key: 'domain', label: 'Domain', render: (v, row) => v || row.name || '—' },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v || 'pending'} size="sm" /> },
        { key: 'created_at', label: 'Submitted', render: (v, row) => (
            <span className="admin-date-cell">{formatDate(v || row.submitted_at)}</span>
        )},
        {
            key: 'actions', label: 'Actions', sortable: false,
            render: (_, row) => (
                <div className="admin-actions">
                    <button
                        className="admin-btn admin-btn-sm admin-btn-success"
                        onClick={() => handleVerify(row.id, 'verified')}
                        disabled={actionLoading === row.id}
                    >
                        <CheckCircle size={12} /> Approve
                    </button>
                    <button
                        className="admin-btn admin-btn-sm admin-btn-danger"
                        onClick={() => handleVerify(row.id, 'rejected')}
                        disabled={actionLoading === row.id}
                    >
                        <XCircle size={12} /> Reject
                    </button>
                </div>
            ),
        },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">.ae Verification Queue</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <div style={{ marginBottom: 16, color: '#71717a', fontSize: 13 }}>
                {queue.length} domain(s) awaiting verification
            </div>

            <AdminTable
                columns={columns}
                data={queue}
                loading={loading}
                emptyMessage="No domains pending .ae verification"
            />
        </div>
    );
}
