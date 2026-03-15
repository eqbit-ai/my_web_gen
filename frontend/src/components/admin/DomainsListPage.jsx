import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetDomains, adminGetDomainHealth } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch { return d; }
}

export default function DomainsListPage() {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState('');
    const [data, setData] = useState(null);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [res, h] = await Promise.all([
                adminGetDomains(page, 20, status || null),
                adminGetDomainHealth().catch(() => null),
            ]);
            setData(res);
            setHealth(h);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, status]);

    useEffect(() => { load(); }, [load]);

    const domains = Array.isArray(data) ? data : data?.domains || data?.items || [];
    const total = data?.total || domains.length;

    const columns = [
        { key: 'domain', label: 'Domain', render: v => v || '—' },
        { key: 'site_name', label: 'Site', render: v => v || '—' },
        { key: 'user_email', label: 'User', render: v => v || '—' },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'ssl_status', label: 'SSL', render: v => <StatusBadge status={v || 'none'} size="sm" /> },
        { key: 'cloudfront_domain', label: 'CloudFront', render: v => v ? <span style={{ fontSize: '0.75rem' }}>{v}</span> : '—' },
        { key: 'created_at', label: 'Connected', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Connected Domains</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {health && !health.error && (
                <div className="admin-card" style={{ marginBottom: 24 }}>
                    <div className="admin-card-title">Domain Health</div>
                    <div className="admin-card-stats">
                        <div>
                            <span className="admin-card-stat-label">Total Domains</span>
                            <strong>{health.total_domains || 0}</strong>
                        </div>
                        <div>
                            <span className="admin-card-stat-label">SSL Active</span>
                            <strong>{health.ssl_active || 0}</strong>
                        </div>
                        <div>
                            <span className="admin-card-stat-label">SSL None</span>
                            <strong>{health.ssl_none || 0}</strong>
                        </div>
                        {health.domain_status && Object.entries(health.domain_status).map(([k, v]) => (
                            <div key={k}>
                                <span className="admin-card-stat-label">{k}</span>
                                <strong>{v}</strong>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="admin-toolbar">
                <select className="admin-search" style={{ width: 'auto' }} value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="pending_validation">Pending Validation</option>
                    <option value="pending_deployment">Pending Deployment</option>
                </select>
                <span className="admin-count">{total} domains</span>
            </div>

            <AdminTable
                columns={columns}
                data={domains}
                loading={loading}
                emptyMessage="No connected domains"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
                onRowClick={(row) => navigate(`/admin/domains/${row.id}`)}
            />
        </div>
    );
}
