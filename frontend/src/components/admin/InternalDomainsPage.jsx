import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, ArrowRightLeft, Check } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetInternalDomains, adminGetInternalDomainHealth, adminGetTransferRequests, adminClearTransferRequest } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', danger: '#f87171', success: '#34d399', warning: '#fbbf24' };

export default function InternalDomainsPage() {
    const navigate = useNavigate();
    const [tab, setTab] = useState('domains');
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState('');
    const [verification, setVerification] = useState('');
    const [data, setData] = useState(null);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [transfers, setTransfers] = useState(null);
    const [transfersLoading, setTransfersLoading] = useState(false);
    const [clearingId, setClearingId] = useState(null);

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

    const loadTransfers = useCallback(async () => {
        setTransfersLoading(true);
        try {
            const res = await adminGetTransferRequests();
            setTransfers(res);
        } catch {}
        setTransfersLoading(false);
    }, []);

    const handleClearTransfer = async (domainId) => {
        setClearingId(domainId);
        try {
            await adminClearTransferRequest(domainId);
            loadTransfers();
        } catch {}
        setClearingId(null);
    };

    useEffect(() => { load(); }, [load]);
    useEffect(() => { if (tab === 'transfers') loadTransfers(); }, [tab, loadTransfers]);

    const domains = data?.domains || [];
    const total = data?.total || domains.length;
    const transferList = transfers?.requests || [];

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
                <button className="admin-btn" onClick={tab === 'transfers' ? loadTransfers : load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Tabs */}
            <div className="admin-tabs" style={{ marginBottom: 24 }}>
                <button className={`admin-tab${tab === 'domains' ? ' active' : ''}`} onClick={() => setTab('domains')}>
                    Domains
                </button>
                <button className={`admin-tab${tab === 'transfers' ? ' active' : ''}`} onClick={() => setTab('transfers')}>
                    <ArrowRightLeft size={14} style={{ marginRight: 4 }} />
                    Transfer Requests
                    {transferList.length > 0 && <span style={{ marginLeft: 6, background: T.danger, color: '#fff', borderRadius: 10, padding: '1px 7px', fontSize: 11, fontWeight: 600 }}>{transferList.length}</span>}
                </button>
            </div>

            {tab === 'domains' && (
                <>
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
                </>
            )}

            {tab === 'transfers' && (
                <div className="admin-card">
                    <div className="admin-card-title">Pending Transfer Requests</div>
                    {transfersLoading ? (
                        <div className="admin-loading-page"><RefreshCw size={16} className="admin-spinner" /> Loading...</div>
                    ) : transferList.length === 0 ? (
                        <div className="admin-empty">No pending transfer requests</div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: '12px 0' }}>
                            {transferList.map(req => (
                                <div key={req.id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 16 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                                                <strong style={{ color: T.text, fontSize: 15 }}>{req.domain_name}</strong>
                                                <StatusBadge status={req.status} size="sm" />
                                            </div>
                                            <div style={{ color: T.muted, fontSize: 13, marginBottom: 6 }}>
                                                Requested by: <span style={{ color: T.text }}>{req.user_email || '—'}</span>
                                                <span style={{ margin: '0 8px' }}>|</span>
                                                {formatDate(req.transfer_requested_at)}
                                            </div>
                                            {req.transfer_reason && (
                                                <div style={{ color: T.text, fontSize: 13, background: 'rgba(255,255,255,0.04)', padding: '8px 12px', borderRadius: 8, marginTop: 8 }}>
                                                    <span style={{ color: T.muted }}>Reason:</span> {req.transfer_reason}
                                                </div>
                                            )}
                                        </div>
                                        <button
                                            className="admin-btn admin-btn-success"
                                            onClick={() => handleClearTransfer(req.id)}
                                            disabled={clearingId === req.id}
                                            style={{ whiteSpace: 'nowrap' }}
                                        >
                                            <Check size={14} /> {clearingId === req.id ? 'Clearing...' : 'Mark Resolved'}
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
