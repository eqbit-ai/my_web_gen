import React, { useState, useEffect, useCallback, useRef } from 'react';
import { RefreshCw, Search, X } from 'lucide-react';
import AdminTable from './shared/AdminTable';
import { adminGetAuditLogs, adminGetUsers } from '../../services/adminApi';
import formatDate from './shared/formatDate';


export default function AuditLogPage() {
    const [page, setPage] = useState(1);
    const [actionType, setActionType] = useState('');
    const [userId, setUserId] = useState(null);
    const [userLabel, setUserLabel] = useState('');
    const [userSearch, setUserSearch] = useState('');
    const [userResults, setUserResults] = useState([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const searchTimeout = useRef(null);
    const dropdownRef = useRef(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetAuditLogs(page, 20, actionType || null, userId || null);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, actionType, userId]);

    useEffect(() => { load(); }, [load]);

    // Debounced user search
    useEffect(() => {
        if (!userSearch || userSearch.length < 2) {
            setUserResults([]);
            setShowDropdown(false);
            return;
        }
        clearTimeout(searchTimeout.current);
        searchTimeout.current = setTimeout(async () => {
            try {
                const res = await adminGetUsers(1, 10, userSearch);
                const users = res?.users || res?.items || [];
                setUserResults(users);
                setShowDropdown(users.length > 0);
            } catch { setUserResults([]); }
        }, 300);
        return () => clearTimeout(searchTimeout.current);
    }, [userSearch]);

    // Close dropdown on outside click
    useEffect(() => {
        const handleClick = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setShowDropdown(false);
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    const selectUser = (user) => {
        setUserId(user.id);
        setUserLabel(user.email || user.full_name || `User #${user.id}`);
        setUserSearch('');
        setShowDropdown(false);
        setPage(1);
    };

    const clearUser = () => {
        setUserId(null);
        setUserLabel('');
        setUserSearch('');
        setPage(1);
    };

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

            <div className="admin-toolbar" style={{ gap: 12 }}>
                <select className="admin-search" style={{ width: 'auto' }} value={actionType} onChange={e => { setActionType(e.target.value); setPage(1); }}>
                    <option value="">All Actions</option>
                    <option value="login">Login</option>
                    <option value="generate">Generate</option>
                    <option value="edit">Edit</option>
                    <option value="admin">Admin</option>
                    <option value="domain">Domain</option>
                    <option value="token">Token</option>
                </select>

                {/* User filter */}
                <div ref={dropdownRef} style={{ position: 'relative' }}>
                    {userId ? (
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px',
                            borderRadius: 8, background: '#818cf820', border: '1px solid #818cf850',
                            fontSize: 13, color: '#818cf8',
                        }}>
                            <span>{userLabel}</span>
                            <button onClick={clearUser} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#71717a', padding: 0, display: 'flex' }}>
                                <X size={14} />
                            </button>
                        </div>
                    ) : (
                        <div style={{ position: 'relative' }}>
                            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#71717a' }} />
                            <input
                                className="admin-search"
                                style={{ paddingLeft: 32, width: 220 }}
                                placeholder="Filter by user..."
                                value={userSearch}
                                onChange={e => setUserSearch(e.target.value)}
                                onFocus={() => userResults.length > 0 && setShowDropdown(true)}
                            />
                        </div>
                    )}
                    {showDropdown && (
                        <div style={{
                            position: 'absolute', top: '100%', left: 0, right: 0, marginTop: 4,
                            background: '#12121a', border: '1px solid #2a2a3a', borderRadius: 8,
                            maxHeight: 240, overflowY: 'auto', zIndex: 50, boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                        }}>
                            {userResults.map(u => (
                                <div
                                    key={u.id}
                                    onClick={() => selectUser(u)}
                                    style={{
                                        padding: '10px 14px', cursor: 'pointer', fontSize: 13, color: '#e4e4e7',
                                        borderBottom: '1px solid #2a2a3a', display: 'flex', justifyContent: 'space-between',
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.background = '#1a1a28'}
                                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                >
                                    <span>{u.email}</span>
                                    <span style={{ color: '#71717a', fontSize: 11 }}>{u.full_name || u.company_name || ''}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

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
