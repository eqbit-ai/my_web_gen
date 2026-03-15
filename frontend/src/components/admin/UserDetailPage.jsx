import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Ban, Check, Key, Eye, Coins } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import {
    adminGetUserDetail, adminGetUserAudit, adminGetUserLogins,
    adminDisableUser, adminEnableUser, adminGrantTokens,
    adminResetPassword, adminVerifyLicence, adminImpersonateUser,
} from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', danger: '#f87171', success: '#34d399' };


export default function UserDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [tab, setTab] = useState('overview');
    const [user, setUser] = useState(null);
    const [audit, setAudit] = useState(null);
    const [logins, setLogins] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);
    const [grantAmount, setGrantAmount] = useState('');

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [u, a, l] = await Promise.all([
                adminGetUserDetail(id),
                adminGetUserAudit(id).catch(() => null),
                adminGetUserLogins(id).catch(() => null),
            ]);
            setUser(u);
            setAudit(a);
            setLogins(l);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [id]);

    useEffect(() => { load(); }, [load]);

    const handleAction = async (action) => {
        setActionLoading(true);
        try {
            if (action === 'disable') await adminDisableUser(id);
            else if (action === 'enable') await adminEnableUser(id);
            else if (action === 'reset-password') await adminResetPassword(id);
            else if (action === 'verify-licence') await adminVerifyLicence(id, true);
            else if (action === 'impersonate') {
                const result = await adminImpersonateUser(id);
                if (result?.token) {
                    // Save admin token so we can switch back
                    const adminToken = localStorage.getItem('token');
                    localStorage.setItem('admin_token_backup', adminToken);
                    // Switch to impersonated user's token
                    localStorage.setItem('token', result.token);
                    localStorage.setItem('impersonating', JSON.stringify({
                        userId: id,
                        email: result.user?.email || '',
                        readOnly: result.read_only,
                        expiresIn: result.expires_in_minutes,
                    }));
                    // Redirect to dashboard as the impersonated user
                    window.location.href = '/dashboard';
                    return;
                }
            }
            else if (action === 'grant' && grantAmount) {
                await adminGrantTokens(id, parseInt(grantAmount));
                setGrantAmount('');
            }
            load();
        } catch {}
        setActionLoading(false);
    };

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    if (!user) return <div className="admin-empty">User not found</div>;

    const auditLogs = audit?.items || audit?.logs || (Array.isArray(audit) ? audit : []);
    const loginList = logins?.items || logins?.logins || (Array.isArray(logins) ? logins : []);

    const tabs = ['overview', 'sites', 'tokens', 'logins', 'audit'];

    return (
        <div>
            <div className="admin-page-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button className="admin-back" onClick={() => navigate('/admin/users')}><ArrowLeft size={16} /></button>
                    <div>
                        <h1 className="admin-page-title" style={{ marginBottom: 0 }}>
                            {user.company_name || user.name || user.email}
                        </h1>
                        <span style={{ color: T.muted, fontSize: 13 }}>{user.email}</span>
                    </div>
                    <StatusBadge status={user.is_active !== false ? 'active' : 'disabled'} />
                </div>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Actions */}
            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-card-title">Actions</div>
                <div className="admin-actions" style={{ flexWrap: 'wrap', gap: 8 }}>
                    <button
                        className={`admin-btn ${user.is_active !== false ? 'admin-btn-danger' : 'admin-btn-success'}`}
                        onClick={() => handleAction(user.is_active !== false ? 'disable' : 'enable')}
                        disabled={actionLoading}
                    >
                        {user.is_active !== false ? <><Ban size={12} /> Disable</> : <><Check size={12} /> Enable</>}
                    </button>
                    <button className="admin-btn" onClick={() => handleAction('verify-licence')} disabled={actionLoading}>
                        <Check size={12} /> Verify Licence
                    </button>
                    <button className="admin-btn" onClick={() => handleAction('reset-password')} disabled={actionLoading}>
                        <Key size={12} /> Reset Password
                    </button>
                    <button className="admin-btn" onClick={() => handleAction('impersonate')} disabled={actionLoading}>
                        <Eye size={12} /> Impersonate
                    </button>
                    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                        <input
                            className="admin-input"
                            style={{ width: 80 }}
                            placeholder="Amount"
                            type="number"
                            value={grantAmount}
                            onChange={e => setGrantAmount(e.target.value)}
                        />
                        <button className="admin-btn admin-btn-primary" onClick={() => handleAction('grant')} disabled={actionLoading || !grantAmount}>
                            <Coins size={12} /> Grant
                        </button>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="admin-tabs" style={{ marginBottom: 24 }}>
                {tabs.map(t => (
                    <button key={t} className={`admin-tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {tab === 'overview' && (
                <div className="admin-card">
                    <div className="admin-detail-grid">
                        {Object.entries(user)
                            .filter(([k, v]) => !['password', 'hashed_password'].includes(k) && typeof v !== 'object')
                            .map(([k, v]) => (
                            <div key={k} className="admin-detail-item">
                                <span className="admin-detail-label">{k.replace(/_/g, ' ')}</span>
                                {typeof v === 'boolean' ? (
                                    <StatusBadge status={v ? 'active' : 'disabled'} size="sm" />
                                ) : (
                                    <strong>{v === null ? '—' : k.includes('_at') ? formatDate(v) : String(v)}</strong>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {tab === 'sites' && (
                <div className="admin-card">
                    <div className="admin-card-title">User Sites</div>
                    {user.sites && (Array.isArray(user.sites) ? user.sites : []).length > 0 ? (
                        <AdminTable
                            columns={[
                                { key: 'id', label: 'ID' },
                                { key: 'domain', label: 'Domain', render: v => v || '—' },
                                { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
                                { key: 'created_at', label: 'Created', render: v => formatDate(v) },
                            ]}
                            data={user.sites || []}
                        />
                    ) : (
                        <div className="admin-empty">No sites for this user</div>
                    )}
                </div>
            )}

            {tab === 'tokens' && (
                <div className="admin-card">
                    <div className="admin-card-title">Token Balance</div>
                    <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 16 }}>
                        <div className="admin-stat-card admin-stat-accent-blue">
                            <div className="admin-stat-body">
                                <div className="admin-stat-value">{user.token_balance ?? user.tokens ?? '—'}</div>
                                <div className="admin-stat-label">Current Balance</div>
                            </div>
                        </div>
                        <div className="admin-stat-card admin-stat-accent-green">
                            <div className="admin-stat-body">
                                <div className="admin-stat-value">{user.total_granted ?? '—'}</div>
                                <div className="admin-stat-label">Total Granted</div>
                            </div>
                        </div>
                        <div className="admin-stat-card admin-stat-accent-orange">
                            <div className="admin-stat-body">
                                <div className="admin-stat-value">{user.total_consumed ?? '—'}</div>
                                <div className="admin-stat-label">Total Consumed</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {tab === 'logins' && (
                <div className="admin-card">
                    <div className="admin-card-title">Login History</div>
                    <AdminTable
                        columns={[
                            { key: 'created_at', label: 'Time', render: (v, row) => formatDate(v || row.timestamp) },
                            { key: 'ip_address', label: 'IP', render: (v, row) => v || row.ip || '—' },
                            { key: 'user_agent', label: 'User Agent', render: v => (
                                <span style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>
                                    {v || '—'}
                                </span>
                            )},
                        ]}
                        data={loginList}
                        emptyMessage="No login history"
                    />
                </div>
            )}

            {tab === 'audit' && (
                <div className="admin-card">
                    <div className="admin-card-title">Audit Log</div>
                    <AdminTable
                        columns={[
                            { key: 'created_at', label: 'Time', render: (v, row) => formatDate(v || row.timestamp) },
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
                        ]}
                        data={auditLogs}
                        emptyMessage="No audit logs"
                    />
                </div>
            )}
        </div>
    );
}
