import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, CheckCircle, XCircle, Coins } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetTokenRequests, adminReviewTokenRequest } from '../../services/adminApi';
import formatDate from './shared/formatDate';

export default function TokenRequestsPage() {
    const [requests, setRequests] = useState([]);
    const [filter, setFilter] = useState('pending');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState({});
    const [grantAmounts, setGrantAmounts] = useState({});
    const [adminNotes, setAdminNotes] = useState({});

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetTokenRequests(filter);
            setRequests(Array.isArray(res) ? res : res?.requests || res?.items || []);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [filter]);

    useEffect(() => { load(); }, [load]);

    const handleReview = async (requestId, action) => {
        setActionLoading(prev => ({ ...prev, [requestId]: action }));
        try {
            await adminReviewTokenRequest(
                requestId,
                action,
                adminNotes[requestId] || '',
                action === 'approve' ? (parseInt(grantAmounts[requestId]) || null) : null,
            );
            setRequests(prev => prev.filter(r => r.id !== requestId));
        } catch (e) { setError(e.message); }
        setActionLoading(prev => ({ ...prev, [requestId]: null }));
    };

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Token Requests</h1>
                <div className="admin-actions">
                    <select className="admin-search" style={{ width: 'auto' }} value={filter} onChange={e => setFilter(e.target.value)}>
                        <option value="pending">Pending</option>
                        <option value="approved">Approved</option>
                        <option value="rejected">Rejected</option>
                        <option value="all">All</option>
                    </select>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {loading ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#71717a' }}>Loading...</div>
            ) : requests.length === 0 ? (
                <div style={{ padding: 60, textAlign: 'center' }}>
                    <Coins size={48} style={{ color: '#a1a1aa', marginBottom: 16 }} />
                    <h3 style={{ color: '#e4e4e7', marginBottom: 8 }}>No {filter} requests</h3>
                    <p style={{ color: '#71717a' }}>
                        {filter === 'pending' ? 'No token requests waiting for review.' : `No ${filter} token requests found.`}
                    </p>
                </div>
            ) : (
                <div style={{ display: 'grid', gap: 12 }}>
                    <p style={{ color: '#a1a1aa', fontSize: 14 }}>{requests.length} {filter} request{requests.length !== 1 ? 's' : ''}</p>
                    {requests.map(req => (
                        <div key={req.id} style={{
                            background: '#18181b', border: '1px solid #27272a', borderRadius: 12,
                            padding: '20px 24px',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <div style={{
                                        width: 36, height: 36, borderRadius: '50%', background: '#3f3f46',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        color: '#e4e4e7', fontWeight: 600, fontSize: 14,
                                    }}>
                                        {(req.user_name || req.user_email || 'U')[0].toUpperCase()}
                                    </div>
                                    <div>
                                        <strong style={{ color: '#e4e4e7' }}>{req.user_name || req.user_email}</strong>
                                        <div style={{ color: '#71717a', fontSize: 13 }}>{req.user_email}</div>
                                    </div>
                                </div>
                                <StatusBadge status={req.status === 'pending' ? 'pending' : req.status === 'approved' ? 'active' : 'disabled'} label={req.status} size="sm" />
                            </div>

                            <div style={{ display: 'flex', gap: 24, fontSize: 13, color: '#71717a', marginBottom: 12 }}>
                                <span>Requested: <strong style={{ color: '#fbbf24' }}>{(req.amount || 0).toLocaleString()} tokens</strong></span>
                                <span>Current balance: <strong style={{ color: '#a1a1aa' }}>{(req.user_balance || 0).toLocaleString()}</strong></span>
                                <span>{formatDate(req.created_at)}</span>
                            </div>

                            {req.reason && (
                                <div style={{ background: '#09090b', borderRadius: 8, padding: '10px 14px', marginBottom: 12, fontSize: 13, color: '#a1a1aa', borderLeft: '3px solid #3f3f46' }}>
                                    {req.reason}
                                </div>
                            )}

                            {filter === 'pending' && (
                                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                                    <input
                                        className="admin-search"
                                        type="number"
                                        placeholder="Grant amount (optional override)"
                                        value={grantAmounts[req.id] || ''}
                                        onChange={e => setGrantAmounts(prev => ({ ...prev, [req.id]: e.target.value }))}
                                        style={{ width: 200, fontSize: 13 }}
                                    />
                                    <input
                                        className="admin-search"
                                        placeholder="Admin note (optional)"
                                        value={adminNotes[req.id] || ''}
                                        onChange={e => setAdminNotes(prev => ({ ...prev, [req.id]: e.target.value }))}
                                        style={{ flex: 1, fontSize: 13 }}
                                    />
                                    <button
                                        className="admin-btn"
                                        onClick={() => handleReview(req.id, 'reject')}
                                        disabled={!!actionLoading[req.id]}
                                        style={{ color: '#ef4444', borderColor: '#ef444440' }}
                                    >
                                        <XCircle size={14} />
                                        {actionLoading[req.id] === 'reject' ? 'Rejecting...' : 'Reject'}
                                    </button>
                                    <button
                                        className="admin-btn admin-btn-primary"
                                        onClick={() => handleReview(req.id, 'approve')}
                                        disabled={!!actionLoading[req.id]}
                                        style={{ background: '#22c55e', borderColor: '#22c55e' }}
                                    >
                                        <CheckCircle size={14} />
                                        {actionLoading[req.id] === 'approve' ? 'Approving...' : 'Approve'}
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
