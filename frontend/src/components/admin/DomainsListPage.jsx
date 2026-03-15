import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, Shield } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetDomains, adminGetDomainHealth, adminReprovisionSSL } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch { return d; }
}

export default function DomainsListPage() {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState('');
    const [tld, setTld] = useState('');
    const [data, setData] = useState(null);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sslLoading, setSslLoading] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [res, h] = await Promise.all([
                adminGetDomains(page, 20, status || null, tld || null),
                adminGetDomainHealth().catch(() => null),
            ]);
            setData(res);
            setHealth(h);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, status, tld]);

    useEffect(() => { load(); }, [load]);

    const handleSSL = async (e, domainId) => {
        e.stopPropagation();
        setSslLoading(domainId);
        try { await adminReprovisionSSL(domainId); load(); } catch {}
        setSslLoading(null);
    };

    const domains = Array.isArray(data) ? data : data?.domains || data?.items || [];
    const total = data?.total || domains.length;

    const columns = [
        { key: 'domain', label: 'Domain', render: (v, row) => v || row.name || '—' },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        { key: 'tld', label: 'TLD', render: v => v || '—' },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'ssl_status', label: 'SSL', render: v => <StatusBadge status={v || 'unknown'} size="sm" /> },
        { key: 'expires_at', label: 'Expires', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
        {
            key: 'actions', label: 'Actions', sortable: false,
            render: (_, row) => (
                <button className="admin-btn admin-btn-sm" onClick={(e) => handleSSL(e, row.id)} disabled={sslLoading === row.id}>
                    <Shield size={12} /> SSL
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
                <h1 className="admin-page-title">All Domains</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* DNS Health Summary */}
            {health && (
                <div className="admin-card" style={{ marginBottom: 24 }}>
                    <div className="admin-card-title">DNS Health</div>
                    <div className="admin-card-stats">
                        {Object.entries(health).map(([k, v]) => (
                            <div key={k}>
                                <span className="admin-card-stat-label">{k.replace(/_/g, ' ')}</span>
                                <strong>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</strong>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="admin-toolbar">
                <div style={{ display: 'flex', gap: 8 }}>
                    <select className="admin-search" style={{ width: 'auto' }} value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
                        <option value="">All Status</option>
                        <option value="active">Active</option>
                        <option value="pending">Pending</option>
                        <option value="expired">Expired</option>
                    </select>
                    <select className="admin-search" style={{ width: 'auto' }} value={tld} onChange={e => { setTld(e.target.value); setPage(1); }}>
                        <option value="">All TLDs</option>
                        <option value=".com">.com</option>
                        <option value=".ae">.ae</option>
                        <option value=".net">.net</option>
                        <option value=".org">.org</option>
                    </select>
                </div>
                <span className="admin-count">{total} domains</span>
            </div>

            <AdminTable
                columns={columns}
                data={domains}
                loading={loading}
                emptyMessage="No domains found"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
                onRowClick={(row) => navigate(`/admin/domains/${row.id}`)}
            />
        </div>
    );
}
