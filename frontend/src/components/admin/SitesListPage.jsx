import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, ExternalLink } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetSites } from '../../services/adminApi';
import formatDate from './shared/formatDate';



export default function SitesListPage() {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
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

    const sites = Array.isArray(data) ? data : data?.sites || data?.items || [];
    const total = data?.total || sites.length;

    const columns = [
        { key: 'id', label: 'ID', width: 60 },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        {
            key: 'domain', label: 'Domain / URL',
            render: (v, row) => {
                const url = v ? `https://${v}` : row.deployed_url;
                if (url) return (
                    <a href={url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem' }}>
                        {v || 'S3 Link'} <ExternalLink size={10} />
                    </a>
                );
                return '—';
            },
        },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'created_at', label: 'Created', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
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
