import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, ArrowDown, Search, Calendar, X } from 'lucide-react';
import { adminGetUserConsumption } from '../../services/adminApi';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a' };

function fmt(n) {
    if (n == null) return '0';
    return Number(n).toLocaleString();
}

function fmtDate(d) {
    if (!d) return '—';
    const dt = new Date(d);
    if (isNaN(dt)) return '—';
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function fmtDateTime(d) {
    if (!d) return '—';
    const dt = new Date(d);
    if (isNaN(dt)) return '—';
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function toISODate(date) {
    if (!date) return '';
    return date.toISOString().split('T')[0];
}

const PRESETS = [
    { label: 'Today', days: 0 },
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 30 days', days: 30 },
    { label: 'Last 90 days', days: 90 },
    { label: 'All time', days: null },
];

export default function UserConsumptionPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [search, setSearch] = useState('');
    const [sortKey, setSortKey] = useState('total_used');
    const [sortDir, setSortDir] = useState('desc');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [activePreset, setActivePreset] = useState('All time');

    const load = useCallback(async (sd, ed) => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetUserConsumption(sd || '', ed || '');
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(startDate, endDate); }, [load, startDate, endDate]);

    const applyPreset = (preset) => {
        setActivePreset(preset.label);
        if (preset.days === null) {
            setStartDate('');
            setEndDate('');
        } else {
            const end = new Date();
            const start = new Date();
            if (preset.days === 0) {
                // today
            } else {
                start.setDate(start.getDate() - preset.days);
            }
            setStartDate(toISODate(start));
            setEndDate(toISODate(end));
        }
    };

    const clearDates = () => {
        setStartDate('');
        setEndDate('');
        setActivePreset('All time');
    };

    const handleSort = (key) => {
        if (sortKey === key) {
            setSortDir(d => d === 'desc' ? 'asc' : 'desc');
        } else {
            setSortKey(key);
            setSortDir('desc');
        }
    };

    const filtered = data?.users?.filter(u => {
        if (!search) return true;
        const q = search.toLowerCase();
        return u.email.toLowerCase().includes(q) ||
            u.full_name.toLowerCase().includes(q) ||
            u.company_name.toLowerCase().includes(q);
    }) || [];

    const sorted = [...filtered].sort((a, b) => {
        if (sortKey === 'email' || sortKey === 'full_name') {
            const aVal = (a[sortKey] || '').toLowerCase();
            const bVal = (b[sortKey] || '').toLowerCase();
            return sortDir === 'desc' ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
        }
        const aVal = a[sortKey] ?? 0;
        const bVal = b[sortKey] ?? 0;
        return sortDir === 'desc' ? bVal - aVal : aVal - bVal;
    });

    const SortHeader = ({ label, field, align }) => (
        <th
            onClick={() => handleSort(field)}
            style={{
                cursor: 'pointer', textAlign: align || 'left', padding: '10px 12px',
                color: sortKey === field ? '#818cf8' : T.muted, fontSize: 12, fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '0.05em', userSelect: 'none',
                whiteSpace: 'nowrap',
            }}
        >
            {label} {sortKey === field && (
                <ArrowDown size={10} style={{ transform: sortDir === 'asc' ? 'rotate(180deg)' : 'none', verticalAlign: 'middle' }} />
            )}
        </th>
    );

    const inputStyle = {
        padding: '7px 10px',
        background: T.surface,
        border: `1px solid ${T.border}`,
        borderRadius: 8,
        color: T.text,
        fontSize: 13,
        outline: 'none',
    };

    return (
        <div>
            <div className="admin-page-header">
                <div>
                    <h1 className="admin-page-title">User Consumption</h1>
                    <p style={{ color: T.muted, fontSize: 13, marginTop: 4 }}>
                        Per-user token usage, generations, edits, and estimated cost
                    </p>
                </div>
                <button className="admin-btn" onClick={() => load(startDate, endDate)} disabled={loading}>
                    <RefreshCw size={14} className={loading ? 'admin-spinner' : ''} /> Refresh
                </button>
            </div>

            {/* Date Range Filter */}
            <div className="admin-card" style={{ padding: '16px 20px', marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <Calendar size={16} style={{ color: '#818cf8' }} />
                    <span style={{ fontSize: 13, fontWeight: 600, color: T.text, marginRight: 8 }}>Date Range:</span>

                    {/* Presets */}
                    {PRESETS.map(p => (
                        <button
                            key={p.label}
                            onClick={() => applyPreset(p)}
                            style={{
                                padding: '5px 12px',
                                fontSize: 12,
                                fontWeight: 500,
                                borderRadius: 6,
                                border: `1px solid ${activePreset === p.label ? '#818cf8' : T.border}`,
                                background: activePreset === p.label ? 'rgba(129,140,248,0.15)' : 'transparent',
                                color: activePreset === p.label ? '#818cf8' : T.muted,
                                cursor: 'pointer',
                                transition: 'all 0.15s',
                            }}
                        >
                            {p.label}
                        </button>
                    ))}

                    <span style={{ color: T.muted, margin: '0 4px' }}>|</span>

                    {/* Custom date inputs */}
                    <input
                        type="date"
                        value={startDate}
                        onChange={e => { setStartDate(e.target.value); setActivePreset(''); }}
                        style={{ ...inputStyle, width: 150, colorScheme: 'dark' }}
                        max={endDate || undefined}
                    />
                    <span style={{ color: T.muted, fontSize: 12 }}>to</span>
                    <input
                        type="date"
                        value={endDate}
                        onChange={e => { setEndDate(e.target.value); setActivePreset(''); }}
                        style={{ ...inputStyle, width: 150, colorScheme: 'dark' }}
                        min={startDate || undefined}
                    />

                    {(startDate || endDate) && (
                        <button
                            onClick={clearDates}
                            style={{
                                padding: '5px 10px', fontSize: 12, borderRadius: 6,
                                border: `1px solid ${T.border}`, background: 'transparent',
                                color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
                            }}
                        >
                            <X size={12} /> Clear
                        </button>
                    )}
                </div>
                {(startDate || endDate) && (
                    <div style={{ fontSize: 11, color: T.muted, marginTop: 8, paddingLeft: 24 }}>
                        Showing data {startDate ? `from ${fmtDate(startDate + 'T00:00:00')}` : ''} {endDate ? `to ${fmtDate(endDate + 'T00:00:00')}` : ''}
                        {' '}(balance column always shows current balance)
                    </div>
                )}
            </div>

            {/* Summary Cards */}
            {data?.totals && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 24 }}>
                    {[
                        { label: 'Total Granted', value: fmt(data.totals.total_granted), color: '#22c55e', icon: '↑' },
                        { label: 'Total Used', value: fmt(data.totals.total_used), color: '#f59e0b', icon: '↓' },
                        { label: 'Total Balance', value: fmt(data.totals.total_balance), color: '#818cf8', icon: '≡' },
                        { label: 'Est. Total Cost', value: `$${data.totals.total_est_cost}`, color: '#ef4444', icon: '$' },
                    ].map((card, i) => (
                        <div key={i} className="admin-card" style={{ padding: '20px 24px', borderLeft: `3px solid ${card.color}` }}>
                            <div style={{ fontSize: 28, fontWeight: 700, color: card.color }}>{card.value}</div>
                            <div style={{ fontSize: 11, color: T.muted, fontWeight: 600, textTransform: 'uppercase', marginTop: 4 }}>{card.label}</div>
                        </div>
                    ))}
                </div>
            )}

            {error && (
                <div className="admin-alert admin-alert-error" style={{ marginBottom: 16 }}>{error}</div>
            )}

            {/* Search */}
            <div style={{ marginBottom: 16, position: 'relative' }}>
                <Search size={14} style={{ position: 'absolute', left: 12, top: 10, color: T.muted }} />
                <input
                    type="text"
                    placeholder="Search by name, email, or company..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    style={{
                        width: '100%', maxWidth: 400, padding: '8px 12px 8px 32px',
                        background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8,
                        color: T.text, fontSize: 13, outline: 'none',
                    }}
                />
            </div>

            {loading ? (
                <div style={{ padding: 60, textAlign: 'center', color: T.muted }}>
                    <RefreshCw size={20} className="admin-spinner" style={{ marginBottom: 12 }} />
                    <p>Loading consumption data...</p>
                </div>
            ) : (
                <div className="admin-card" style={{ padding: 0, overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 900 }}>
                        <thead>
                            <tr style={{ borderBottom: `1px solid ${T.border}` }}>
                                <th style={{ padding: '10px 12px', textAlign: 'left', color: T.muted, fontSize: 12, fontWeight: 600, textTransform: 'uppercase' }}>#</th>
                                <SortHeader label="User" field="email" />
                                <SortHeader label="Granted" field="total_granted" align="right" />
                                <SortHeader label="Used" field="total_used" align="right" />
                                <SortHeader label="Balance" field="balance" align="right" />
                                <SortHeader label="Generations" field="generations" align="right" />
                                <SortHeader label="Edits" field="edits" align="right" />
                                <SortHeader label="Est. Cost" field="est_cost" align="right" />
                                <SortHeader label="Last Active" field="last_activity" align="right" />
                                <th style={{ padding: '10px 12px', textAlign: 'right', color: T.muted, fontSize: 12, fontWeight: 600, textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Usage %</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.map((u, i) => {
                                const usagePct = u.total_granted > 0 ? Math.round((u.total_used / u.total_granted) * 100) : 0;
                                const barColor = usagePct > 90 ? '#ef4444' : usagePct > 70 ? '#f59e0b' : '#22c55e';
                                return (
                                    <tr key={u.user_id} style={{ borderBottom: `1px solid ${T.border}` }}>
                                        <td style={{ padding: '12px', color: T.muted, fontSize: 12 }}>{i + 1}</td>
                                        <td style={{ padding: '12px' }}>
                                            <div style={{ fontWeight: 600, color: T.text, fontSize: 13 }}>
                                                {u.full_name || u.email}
                                            </div>
                                            <div style={{ fontSize: 11, color: T.muted }}>
                                                {u.full_name ? u.email : ''}{u.company_name ? ` · ${u.company_name}` : ''}
                                            </div>
                                            {u.joined && (
                                                <div style={{ fontSize: 10, color: T.muted, marginTop: 2 }}>
                                                    Joined {fmtDate(u.joined)}
                                                </div>
                                            )}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', color: '#22c55e', fontWeight: 600, fontSize: 13 }}>
                                            {fmt(u.total_granted)}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', color: '#f59e0b', fontWeight: 600, fontSize: 13 }}>
                                            {fmt(u.total_used)}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', color: '#818cf8', fontWeight: 600, fontSize: 13 }}>
                                            {fmt(u.balance)}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', color: T.text, fontSize: 13 }}>
                                            {u.generations || 0}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', color: T.text, fontSize: 13 }}>
                                            {u.edits || 0}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', color: '#ef4444', fontWeight: 500, fontSize: 13 }}>
                                            ${u.est_cost?.toFixed(2)}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', color: T.muted, fontSize: 12, whiteSpace: 'nowrap' }}>
                                            {fmtDateTime(u.last_activity)}
                                        </td>
                                        <td style={{ padding: '12px', textAlign: 'right', width: 120 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                                                <div style={{ width: 60, height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                                                    <div style={{ width: `${Math.min(usagePct, 100)}%`, height: '100%', background: barColor, borderRadius: 3 }} />
                                                </div>
                                                <span style={{ fontSize: 12, color: T.muted, minWidth: 32 }}>{usagePct}%</span>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                            {sorted.length === 0 && (
                                <tr>
                                    <td colSpan={10} style={{ padding: 40, textAlign: 'center', color: T.muted }}>
                                        {search ? 'No matching users' : 'No user data available'}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            <div style={{ color: T.muted, fontSize: 11, marginTop: 12, textAlign: 'right' }}>
                {sorted.length} user{sorted.length !== 1 ? 's' : ''} · Sorted by {sortKey.replace(/_/g, ' ')} ({sortDir})
                {(startDate || endDate) && ` · Filtered by date`}
            </div>
        </div>
    );
}
