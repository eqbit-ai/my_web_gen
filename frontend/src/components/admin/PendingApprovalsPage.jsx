import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, UserCheck, UserX, Clock } from 'lucide-react';
import { adminGetUsers, adminApproveUser, adminDisableUser } from '../../services/adminApi';
import formatDate from './shared/formatDate';

export default function PendingApprovalsPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState({});

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetUsers(1, 100);
            const all = Array.isArray(res) ? res : res?.users || res?.items || [];
            // Only show users who have confirmed their email — unverified
            // signups stay hidden from admins until the user clicks the link.
            setUsers(all.filter(u => u.is_approved === false && u.email_verified === true));
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleApprove = async (userId) => {
        setActionLoading(prev => ({ ...prev, [userId]: 'approve' }));
        try {
            await adminApproveUser(userId);
            setUsers(prev => prev.filter(u => u.id !== userId));
        } catch (e) { setError(e.message); }
        setActionLoading(prev => ({ ...prev, [userId]: null }));
    };

    const handleReject = async (userId) => {
        setActionLoading(prev => ({ ...prev, [userId]: 'reject' }));
        try {
            await adminDisableUser(userId);
            setUsers(prev => prev.filter(u => u.id !== userId));
        } catch (e) { setError(e.message); }
        setActionLoading(prev => ({ ...prev, [userId]: null }));
    };

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Pending Approvals</h1>
                <div className="admin-actions">
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {loading ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#71717a' }}>Loading...</div>
            ) : users.length === 0 ? (
                <div style={{ padding: 60, textAlign: 'center' }}>
                    <UserCheck size={48} style={{ color: '#22c55e', marginBottom: 16 }} />
                    <h3 style={{ color: '#e4e4e7', marginBottom: 8 }}>All caught up!</h3>
                    <p style={{ color: '#71717a' }}>No pending user approvals.</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gap: 12 }}>
                    <p style={{ color: '#a1a1aa', fontSize: 14 }}>{users.length} user{users.length !== 1 ? 's' : ''} waiting for approval</p>
                    {users.map(user => (
                        <div key={user.id} style={{
                            background: '#18181b', border: '1px solid #27272a', borderRadius: 12,
                            padding: '20px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
                        }}>
                            <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                                    <div style={{
                                        width: 36, height: 36, borderRadius: '50%', background: '#3f3f46',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        color: '#e4e4e7', fontWeight: 600, fontSize: 14,
                                    }}>
                                        {(user.full_name || user.company_name || 'U')[0].toUpperCase()}
                                    </div>
                                    <div>
                                        <strong style={{ color: '#e4e4e7', fontSize: 15 }}>{user.full_name || '—'}</strong>
                                        <div style={{ color: '#a1a1aa', fontSize: 13 }}>{user.email}</div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: 24, marginTop: 10, fontSize: 13, color: '#71717a' }}>
                                    <span>Company: <strong style={{ color: '#a1a1aa' }}>{user.company_name || '—'}</strong></span>
                                    <span>Licence: <strong style={{ color: '#a1a1aa' }}>{user.license_number || user.licence_number || '—'}</strong></span>
                                    <span>Mobile: <strong style={{ color: '#a1a1aa' }}>{user.mobile || '—'}</strong></span>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                        <Clock size={12} /> {formatDate(user.created_at)}
                                    </span>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <button
                                    className="admin-btn"
                                    onClick={() => handleReject(user.id)}
                                    disabled={!!actionLoading[user.id]}
                                    style={{ color: '#ef4444', borderColor: '#ef444440' }}
                                >
                                    <UserX size={14} />
                                    {actionLoading[user.id] === 'reject' ? 'Rejecting...' : 'Reject'}
                                </button>
                                <button
                                    className="admin-btn admin-btn-primary"
                                    onClick={() => handleApprove(user.id)}
                                    disabled={!!actionLoading[user.id]}
                                    style={{ background: '#22c55e', borderColor: '#22c55e' }}
                                >
                                    <UserCheck size={14} />
                                    {actionLoading[user.id] === 'approve' ? 'Approving...' : 'Approve'}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
