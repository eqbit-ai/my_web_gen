import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import AdminTable from './shared/AdminTable';
import { adminGetAuditLogs } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

export default function AuditLogPage() {
    const [page, setPage] = useState(1);
    const [actionType, setActionType] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetAuditLogs(page, 20, actionType || null);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, actionType]);

    useEffect(() => { load(); }, [load]);

    const logs = Array.isArray(data) ? data : data?.audit_logs || data?.logs || data?.items || [];
    const total = data?.total || logs.length;

    const columns = [
        { key: 'created_at', label: 'Time', render: (v, row) => (
            <span className="admin-date-cell">{formatDate(v || row.timestamp)}</span>
        )},
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'action', label: 'Action', render: (v, row) => v || row.action_type || '—' },
        { key: 'details', label: 'Details', render: (v, row) => {
            const val = v || row.description;
            const text = !val ? '—' : typeof val === 'object' ? Object.values(val).filter(Boolean).join(', ') : String(val);
            return (
                <span style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={text}>
                    {text}
                </span>
            );
        }},
        { key: 'ip_address', label: 'IP', render: v => v || '—' },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Audit Logs</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <div className="admin-toolbar">
                <select className="admin-search" style={{ width: 'auto' }} value={actionType} onChange={e => { setActionType(e.target.value); setPage(1); }}>
                    <option value="">All Actions</option>
                    <option value="login">Login</option>
                    <option value="generate">Generate</option>
                    <option value="edit">Edit</option>
                    <option value="admin">Admin</option>
                    <option value="domain">Domain</option>
                    <option value="token">Token</option>
                </select>
                <span className="admin-count">{total} entries</span>
            </div>

            <AdminTable
                columns={columns}
                data={logs}
                loading={loading}
                emptyMessage="No audit logs found"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
            />
        </div>
    );
}
