import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, RotateCcw } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetSites, adminRebuildSite } from '../../services/adminApi';

const T = { muted: '#71717a', text: '#e4e4e7' };

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

export default function SitesListPage() {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [rebuilding, setRebuilding] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetSites(page, 20, status || null);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, status]);

    useEffect(() => { load(); }, [load]);

    const handleRebuild = async (e, siteId) => {
        e.stopPropagation();
        setRebuilding(siteId);
        try { await adminRebuildSite(siteId); load(); } catch {}
        setRebuilding(null);
    };

    const sites = Array.isArray(data) ? data : data?.sites || data?.items || [];
    const total = data?.total || sites.length;

    const columns = [
        { key: 'id', label: 'ID', width: 60 },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'domain', label: 'Domain', render: v => v || '—' },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'created_at', label: 'Created', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
        {
            key: 'actions', label: 'Actions', sortable: false,
            render: (_, row) => (
                <button
                    className="admin-btn admin-btn-sm"
                    onClick={(e) => handleRebuild(e, row.id)}
                    disabled
                >
                    <RotateCcw size={12} /> {rebuilding === row.id ? '...' : 'Rebuild'}
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
                <h1 className="admin-page-title">Sites</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <div className="admin-toolbar">
                <select
                    className="admin-search"
                    style={{ width: 'auto' }}
                    value={status}
                    onChange={e => { setStatus(e.target.value); setPage(1); }}
                >
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="published">Published</option>
                    <option value="draft">Draft</option>
                </select>
                <span className="admin-count">{total} sites</span>
            </div>

            <AdminTable
                columns={columns}
                data={sites}
                loading={loading}
                emptyMessage="No sites found"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
                onRowClick={(row) => navigate(`/admin/sites/${row.id}`)}
            />
        </div>
    );
}
