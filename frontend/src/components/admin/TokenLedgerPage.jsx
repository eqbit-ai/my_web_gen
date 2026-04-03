import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Coins, Plus } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetTransactions, adminGetTokenPool, adminGrantTokensWithExpiry, adminGetUsers } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { text: '#e4e4e7', muted: '#71717a', success: '#34d399', danger: '#f87171', warning: '#fbbf24' };
function fmt(v) { return v != null && v !== '—' ? Number(v).toLocaleString() : '—'; }


// Token cost rates (per 1M tokens) — based on Anthropic/OpenAI pricing
const COST_RATES = {
    'anthropic': 3.00,   // ~$3 per 1M input tokens (Sonnet)
    'openai': 2.00,      // ~$2 per 1M tokens (GPT-4.1)
    'default': 2.50,     // blended average
};

function estimateCost(amount, reason) {
    const tokens = Math.abs(Number(amount) || 0);
    if (tokens === 0) return 0;
    const provider = (reason || '').includes('anthropic') ? 'anthropic' : (reason || '').includes('openai') ? 'openai' : 'default';
    return (tokens / 1_000_000) * COST_RATES[provider];
}

export default function TokenLedgerPage() {
    const [page, setPage] = useState(1);
    const [txType, setTxType] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [data, setData] = useState(null);
    const [pool, setPool] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showGrant, setShowGrant] = useState(false);
    const [grantForm, setGrantForm] = useState({ userId: '', amount: '', expiry: '', reason: '' });
    const [granting, setGranting] = useState(false);
    const [userSearch, setUserSearch] = useState('');
    const [userResults, setUserResults] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [userSearching, setUserSearching] = useState(false);
    const userSearchTimer = React.useRef(null);

    const dateRange = (dateFrom || dateTo) ? { from: dateFrom || '2020-01-01', to: dateTo || new Date().toISOString().split('T')[0] } : null;

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [tx, p] = await Promise.all([
                adminGetTransactions(page, 20, null, null, dateRange),
                adminGetTokenPool(dateFrom || null, dateTo || null).catch(() => null),
            ]);
            setData(tx);
            setPool(p);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, dateFrom, dateTo]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => { load(); }, [load]);

    const handleUserSearch = (query) => {
        setUserSearch(query);
        setSelectedUser(null);
        setGrantForm(f => ({ ...f, userId: '' }));
        if (userSearchTimer.current) clearTimeout(userSearchTimer.current);
        if (!query || query.length < 2) { setUserResults([]); return; }
        setUserSearching(true);
        userSearchTimer.current = setTimeout(async () => {
            try {
                const res = await adminGetUsers(1, 10, query);
                setUserResults(res?.users || res?.items || (Array.isArray(res) ? res : []));
            } catch { setUserResults([]); }
            setUserSearching(false);
        }, 300);
    };

    const selectUser = (user) => {
        setSelectedUser(user);
        setGrantForm(f => ({ ...f, userId: String(user.id) }));
        setUserSearch('');
        setUserResults([]);
    };

    const handleGrant = async (e) => {
        e.preventDefault();
        if (!grantForm.userId || !grantForm.amount) return;
        setGranting(true);
        try {
            await adminGrantTokensWithExpiry(parseInt(grantForm.userId), parseInt(grantForm.amount), grantForm.expiry || null, grantForm.reason);
            setGrantForm({ userId: '', amount: '', expiry: '', reason: '' });
            setSelectedUser(null);
            setShowGrant(false);
            load();
        } catch {}
        setGranting(false);
    };

    const transactions = Array.isArray(data) ? data : data?.transactions || data?.items || [];
    const total = data?.total || transactions.length;

    // Calculate total cost from visible transactions
    const totalCost = transactions.reduce((sum, tx) => {
        const amt = Number(tx.amount || 0);
        if (amt < 0) return sum + estimateCost(amt, tx.reason);
        return sum;
    }, 0);

    const columns = [
        { key: 'id', label: 'ID', width: 60 },
        { key: 'user_id', label: 'User', render: (v, row) => (
            <span>{row.user_email || row.email || `#${v}`}</span>
        )},
        { key: 'type', label: 'Type', render: (v, row) => <StatusBadge status={v || row.transaction_type} size="sm" /> },
        { key: 'amount', label: 'Tokens', render: (v) => {
            const num = Number(v);
            const positive = num > 0;
            return (
                <span style={{ fontWeight: 600, color: positive ? T.success : T.danger }}>
                    {positive ? '+' : ''}{num.toLocaleString()}
                </span>
            );
        }},
        { key: 'amount', label: 'Est. Cost', render: (v, row) => {
            const num = Number(v);
            if (num >= 0) return <span style={{ color: T.muted }}>—</span>;
            const cost = estimateCost(v, row.reason);
            return (
                <span style={{ fontWeight: 600, color: T.warning, fontSize: 12 }}>
                    ${cost.toFixed(4)}
                </span>
            );
        }},
        { key: 'reason', label: 'Reason', render: v => <span style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={v}>{v || '—'}</span> },
        { key: 'created_at', label: 'Date', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Transaction Ledger</h1>
                <div className="admin-actions">
                    <button className="admin-btn admin-btn-primary" onClick={() => setShowGrant(!showGrant)}>
                        <Plus size={14} /> Grant Tokens
                    </button>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {/* Summary Cards — all values come from pool endpoint which respects date filter */}
            {pool && (() => {
                const issued = Number(pool.total_granted ?? pool.total_issued ?? 0);
                const used = Number(pool.total_consumed ?? pool.total_used ?? 0);
                const outstanding = pool.date_filtered ? (issued - used) : Number(pool.total_remaining ?? pool.outstanding ?? 0);
                const costVal = (used / 1_000_000) * COST_RATES.default;
                const isFiltered = pool.date_filtered;
                return (<>
                    <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 16 }}>
                        <div className="admin-stat-card admin-stat-accent-blue">
                            <div className="admin-stat-icon"><Coins size={22} /></div>
                            <div className="admin-stat-body">
                                <div className="admin-stat-value">{fmt(issued)}</div>
                                <div className="admin-stat-label">{isFiltered ? 'Issued (period)' : 'Total Issued'}</div>
                            </div>
                        </div>
                        <div className="admin-stat-card admin-stat-accent-orange">
                            <div className="admin-stat-icon"><Coins size={22} /></div>
                            <div className="admin-stat-body">
                                <div className="admin-stat-value">{fmt(used)}</div>
                                <div className="admin-stat-label">{isFiltered ? 'Used (period)' : 'Total Used'}</div>
                            </div>
                        </div>
                        <div className="admin-stat-card admin-stat-accent-green">
                            <div className="admin-stat-icon"><Coins size={22} /></div>
                            <div className="admin-stat-body">
                                <div className="admin-stat-value">{fmt(outstanding)}</div>
                                <div className="admin-stat-label">{isFiltered ? 'Net (period)' : 'Outstanding'}</div>
                            </div>
                        </div>
                    </div>
                    <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)', marginBottom: 24 }}>
                        <div className="admin-stat-card admin-stat-accent-purple">
                            <div className="admin-stat-icon"><Coins size={22} /></div>
                            <div className="admin-stat-body">
                                <div className="admin-stat-value" style={{ color: T.warning }}>{fmt(pool.weekly_burn_rate)}</div>
                                <div className="admin-stat-label">Weekly Burn Rate</div>
                            </div>
                        </div>
                        <div className="admin-stat-card" style={{ borderLeft: '3px solid #f59e0b' }}>
                            <div className="admin-stat-icon" style={{ color: '#f59e0b', fontSize: 22, fontWeight: 700 }}>$</div>
                            <div className="admin-stat-body">
                                <div className="admin-stat-value" style={{ color: '#f59e0b' }}>
                                    ${costVal.toFixed(2)}
                                </div>
                                <div className="admin-stat-label">{isFiltered ? 'Est. Cost (period)' : 'Est. Total Cost'}</div>
                            </div>
                        </div>
                    </div>
                </>);
            })()}

            {/* Grant Form */}
            {showGrant && (
                <div className="admin-card" style={{ marginBottom: 24 }}>
                    <div className="admin-card-title">Grant Tokens</div>
                    <form onSubmit={handleGrant} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                        <div style={{ position: 'relative' }}>
                            <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>User</label>
                            {selectedUser ? (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#27272a', border: '1px solid #3f3f46', borderRadius: 6, padding: '6px 10px', fontSize: 13 }}>
                                    <span style={{ color: '#e4e4e7' }}>{selectedUser.email || selectedUser.company_name}</span>
                                    <span style={{ color: '#71717a', fontSize: 11 }}>#{selectedUser.id}</span>
                                    <button type="button" onClick={() => { setSelectedUser(null); setGrantForm(f => ({ ...f, userId: '' })); }}
                                        style={{ background: 'none', border: 'none', color: '#71717a', cursor: 'pointer', padding: '0 2px', fontSize: 16, lineHeight: 1 }}>&times;</button>
                                </div>
                            ) : (
                                <>
                                    <input
                                        className="admin-input"
                                        style={{ width: 240 }}
                                        value={userSearch}
                                        onChange={e => handleUserSearch(e.target.value)}
                                        placeholder="Search by email or company..."
                                        autoComplete="off"
                                    />
                                    {(userResults.length > 0 || userSearching) && (
                                        <div style={{
                                            position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50,
                                            background: '#1e1e22', border: '1px solid #3f3f46', borderRadius: 6,
                                            maxHeight: 200, overflowY: 'auto', marginTop: 4, boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                                        }}>
                                            {userSearching && <div style={{ padding: '8px 12px', color: T.muted, fontSize: 12 }}>Searching...</div>}
                                            {userResults.map(u => (
                                                <div
                                                    key={u.id}
                                                    onClick={() => selectUser(u)}
                                                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') selectUser(u); }}
                                                    role="button"
                                                    tabIndex={0}
                                                    style={{
                                                        padding: '8px 12px', cursor: 'pointer', fontSize: 13,
                                                        borderBottom: '1px solid #27272a', display: 'flex', justifyContent: 'space-between',
                                                    }}
                                                    onMouseEnter={e => e.currentTarget.style.background = '#27272a'}
                                                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                                >
                                                    <span style={{ color: '#e4e4e7' }}>{u.email}</span>
                                                    <span style={{ color: '#71717a', fontSize: 11 }}>{u.company_name || `#${u.id}`}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                        <div>
                            <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Amount</label>
                            <input className="admin-input" style={{ width: 120 }} type="number" value={grantForm.amount} onChange={e => setGrantForm({ ...grantForm, amount: e.target.value })} placeholder="e.g. 500000" required />
                        </div>
                        <div>
                            <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Expiry (optional)</label>
                            <input className="admin-input" style={{ width: 160 }} type="date" value={grantForm.expiry} onChange={e => setGrantForm({ ...grantForm, expiry: e.target.value })} />
                        </div>
                        <div>
                            <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Reason (optional)</label>
                            <input className="admin-input" style={{ width: 180 }} value={grantForm.reason} onChange={e => setGrantForm({ ...grantForm, reason: e.target.value })} placeholder="e.g. Monthly quota" />
                        </div>
                        <button type="submit" className="admin-btn admin-btn-primary" disabled={granting || !selectedUser}>
                            {granting ? 'Granting...' : 'Grant'}
                        </button>
                        <button type="button" className="admin-btn" onClick={() => { setShowGrant(false); setSelectedUser(null); setUserSearch(''); setUserResults([]); }}>Cancel</button>
                    </form>
                </div>
            )}

            {/* Date Filter */}
            <div className="admin-toolbar" style={{ gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <label style={{ fontSize: 12, color: T.muted, fontWeight: 500 }}>From</label>
                    <input type="date" className="admin-input" style={{ width: 150, padding: '6px 10px', fontSize: 13 }} value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPage(1); }} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <label style={{ fontSize: 12, color: T.muted, fontWeight: 500 }}>To</label>
                    <input type="date" className="admin-input" style={{ width: 150, padding: '6px 10px', fontSize: 13 }} value={dateTo} onChange={e => { setDateTo(e.target.value); setPage(1); }} />
                </div>
                {/* Quick date presets */}
                <div style={{ display: 'flex', gap: 4 }}>
                    <button className="admin-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={() => { const t = new Date().toISOString().split('T')[0]; setDateFrom(t); setDateTo(t); setPage(1); }}>Today</button>
                    <button className="admin-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={() => { const d = new Date(); d.setDate(d.getDate() - 7); setDateFrom(d.toISOString().split('T')[0]); setDateTo(new Date().toISOString().split('T')[0]); setPage(1); }}>7 days</button>
                    <button className="admin-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={() => { const d = new Date(); d.setDate(d.getDate() - 30); setDateFrom(d.toISOString().split('T')[0]); setDateTo(new Date().toISOString().split('T')[0]); setPage(1); }}>30 days</button>
                    {(dateFrom || dateTo) && (
                        <button className="admin-btn" style={{ padding: '4px 10px', fontSize: 11, color: T.danger }} onClick={() => { setDateFrom(''); setDateTo(''); setPage(1); }}>Clear</button>
                    )}
                </div>
                <span className="admin-count" style={{ marginLeft: 'auto' }}>{total} transactions</span>
            </div>

            <AdminTable
                columns={columns}
                data={transactions}
                loading={loading}
                emptyMessage="No transactions found"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
            />
        </div>
    );
}
