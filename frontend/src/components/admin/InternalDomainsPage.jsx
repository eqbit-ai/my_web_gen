import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetInternalDomains, adminGetInternalDomainHealth } from '../../services/adminApi';
import formatDate from './shared/formatDate';


export default function InternalDomainsPage() {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState('');
    const [verification, setVerification] = useState('');
    const [data, setData] = useState(null);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [res, h] = await Promise.all([
                adminGetInternalDomains(20, (page - 1) * 20, status || null, verification || null),
                adminGetInternalDomainHealth().catch(() => null),
            ]);
            setData(res);
            setHealth(h);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, status, verification]);

    useEffect(() => { load(); }, [load]);

    const domains = data?.domains || [];
    const total = data?.total || domains.length;

    const columns = [
        { key: 'domain_name', label: 'Domain', render: v => v || '—' },
        { key: 'tld', label: 'TLD', render: v => v || '—' },
        { key: 'user_email', label: 'User', render: v => v || '—' },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'verification_status', label: 'Verification', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'ssl_status', label: 'SSL', render: v => <StatusBadge status={v || 'none'} size="sm" /> },
        { key: 'expires_at', label: 'Expires', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
        { key: 'auto_renew', label: 'Renew', render: v => v ? 'Yes' : 'No' },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Internal Domains</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {health && !health.error && (
                <div className="admin-card" style={{ marginBottom: 24 }}>
                    <div className="admin-card-title">Domain Health</div>
                    <div className="admin-card-stats">
                        <div>
                            <span className="admin-card-stat-label">Total Registered</span>
                            <strong>{health.total_domains || 0}</strong>
                        </div>
                        {health.domain_status && Object.entries(health.domain_status).map(([k, v]) => (
                            <div key={k}>
                                <span className="admin-card-stat-label">{k}</span>
                                <strong>{v}</strong>
                            </div>
                        ))}
                        {health.verification_status && Object.entries(health.verification_status).map(([k, v]) => (
                            <div key={`v-${k}`}>
                                <span className="admin-card-stat-label">Verify: {k}</span>
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
                    <option value="pending">Pending</option>
                    <option value="expired">Expired</option>
                    <option value="suspended">Suspended</option>
                </select>
                <select className="admin-search" style={{ width: 'auto' }} value={verification} onChange={e => { setVerification(e.target.value); setPage(1); }}>
                    <option value="">All Verification</option>
                    <option value="pending">Pending</option>
                    <option value="verified">Verified</option>
                    <option value="rejected">Rejected</option>
                </select>
                <span className="admin-count">{total} domains</span>
            </div>

            <AdminTable
                columns={columns}
                data={domains}
                loading={loading}
                emptyMessage="No internal domains registered"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
                onRowClick={(row) => navigate(`/admin/domains-internal/${row.id}`)}
            />
        </div>
    );
}
