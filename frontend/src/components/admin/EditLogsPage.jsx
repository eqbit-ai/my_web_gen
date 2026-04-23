import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Tag, ThumbsUp, ThumbsDown } from 'lucide-react';
import AdminTable from './shared/AdminTable';
import {
    adminGetEditLogs,
    adminGetEditLogStats,
    adminCategorizeEditLogs,
} from '../../services/adminApi';
import formatDate from './shared/formatDate';

const EDIT_KINDS = ['iterate', 'element-edit', 'section-edit', 'section-regen'];
const SUCCESS_OPTIONS = [
    { value: '', label: 'All' },
    { value: 'true', label: 'Succeeded' },
    { value: 'false', label: 'Failed' },
];

function StatPill({ label, value, tone }) {
    const toneColor = {
        ok: '#10b981',
        bad: '#ef4444',
        neutral: '#818cf8',
        muted: '#71717a',
    }[tone || 'neutral'];
    return (
        <div style={{
            padding: '10px 14px', borderRadius: 8, background: '#12121a',
            border: '1px solid #2a2a3a', minWidth: 120,
        }}>
            <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase', letterSpacing: 0.4 }}>{label}</div>
            <div style={{ fontSize: 20, fontWeight: 600, color: toneColor, marginTop: 4 }}>{value}</div>
        </div>
    );
}

export default function EditLogsPage() {
    const [page, setPage] = useState(1);
    const [category, setCategory] = useState('');
    const [editKind, setEditKind] = useState('');
    const [success, setSuccess] = useState('');
    const [data, setData] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [categorizing, setCategorizing] = useState(false);
    const [expandedId, setExpandedId] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const successFilter = success === '' ? null : success === 'true';
            const [logsRes, statsRes] = await Promise.all([
                adminGetEditLogs(page, 50, category || null, editKind || null, successFilter),
                adminGetEditLogStats(),
            ]);
            setData(logsRes);
            setStats(statsRes);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, category, editKind, success]);

    useEffect(() => { load(); }, [load]);

    const runCategorize = async () => {
        setCategorizing(true);
        try {
            const res = await adminCategorizeEditLogs(50);
            await load();
            alert(`Categorized ${res.categorized} prompts.`);
        } catch (e) {
            alert(`Failed: ${e.message}`);
        } finally {
            setCategorizing(false);
        }
    };

    const items = data?.items || [];
    const total = data?.total || 0;

    const categories = stats?.by_category || [];
    const fbMap = (stats?.feedback || []).reduce((acc, f) => { acc[f.rating] = f.count; return acc; }, {});

    const columns = [
        { key: 'created_at', label: 'Time', render: (v) => (
            <span className="admin-date-cell" style={{ whiteSpace: 'nowrap', fontSize: 11 }}>{formatDate(v)}</span>
        )},
        { key: 'edit_kind', label: 'Kind', render: (v) => (
            <span style={{
                fontSize: 10, padding: '2px 6px', borderRadius: 4,
                background: '#818cf820', color: '#818cf8', whiteSpace: 'nowrap',
            }}>{v || '—'}</span>
        )},
        { key: 'category', label: 'Category', render: (v) => v ? (
            <span style={{ fontSize: 11, color: '#a78bfa' }}>{v}</span>
        ) : <span style={{ color: '#52525b', fontSize: 11 }}>—</span> },
        { key: 'prompt', label: 'Prompt', render: (v, row) => {
            const text = v || '';
            const isExpanded = expandedId === row.id;
            const short = text.length > 50 ? text.slice(0, 50) + '…' : text;
            return (
                <button
                    type="button"
                    onClick={() => setExpandedId(isExpanded ? null : row.id)}
                    style={{
                        background: 'none', border: 'none', padding: 0, margin: 0,
                        color: '#e4e4e7', fontSize: 12, textAlign: 'left',
                        cursor: text.length > 50 ? 'pointer' : 'default',
                        whiteSpace: isExpanded ? 'pre-wrap' : 'nowrap',
                        wordBreak: 'break-word', maxWidth: 280, display: 'block',
                        overflow: isExpanded ? 'visible' : 'hidden',
                        textOverflow: 'ellipsis',
                    }}
                    title={text.length > 50 ? 'Click to expand' : ''}
                >
                    {isExpanded ? text : short}
                </button>
            );
        }},
        { key: 'target_page', label: 'Page', render: (v) => <span style={{ fontSize: 11 }}>{v || '—'}</span> },
        { key: 'success', label: 'Status', render: (v, row) => v ? (
            <span style={{ color: '#10b981', fontSize: 11 }}>✓</span>
        ) : (
            <span style={{ color: '#ef4444', fontSize: 11 }} title={row.error_kind || ''}>
                ✗ {row.error_kind || 'fail'}
            </span>
        )},
        { key: 'duration_ms', label: 'Duration', render: (v) => v != null ? (
            <span style={{ color: '#a1a1aa', fontSize: 11 }}>{(v / 1000).toFixed(1)}s</span>
        ) : '—' },
        { key: 'output_chars_delta', label: 'Δ', render: (v) => v != null ? (
            <span style={{ color: v > 0 ? '#10b981' : v < 0 ? '#ef4444' : '#71717a', fontSize: 11 }}>
                {v > 0 ? '+' : ''}{v}
            </span>
        ) : '—' },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Edit Prompt Logs</h1>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="admin-btn" onClick={runCategorize} disabled={categorizing}>
                        <Tag size={14} /> {categorizing ? 'Categorizing…' : `Categorize uncategorized (${stats?.uncategorized || 0})`}
                    </button>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {/* Stats row */}
            {stats && (
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
                    <StatPill label="Total" value={stats.total} tone="neutral" />
                    <StatPill label="Succeeded" value={stats.success_rate?.succeeded || 0} tone="ok" />
                    <StatPill label="Failed" value={stats.success_rate?.failed || 0} tone="bad" />
                    <StatPill label="Uncategorized" value={stats.uncategorized || 0} tone="muted" />
                    <div style={{
                        padding: '10px 14px', borderRadius: 8, background: '#12121a',
                        border: '1px solid #2a2a3a', display: 'flex', alignItems: 'center', gap: 12,
                    }}>
                        <div>
                            <div style={{ fontSize: 11, color: '#71717a', textTransform: 'uppercase', letterSpacing: 0.4 }}>Feedback</div>
                            <div style={{ display: 'flex', gap: 12, marginTop: 4, fontSize: 14 }}>
                                <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <ThumbsUp size={13} /> {fbMap.up || 0}
                                </span>
                                <span style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <ThumbsDown size={13} /> {fbMap.down || 0}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="admin-toolbar" style={{ gap: 12 }}>
                <select className="admin-search" style={{ width: 'auto' }} value={editKind} onChange={e => { setEditKind(e.target.value); setPage(1); }}>
                    <option value="">All Kinds</option>
                    {EDIT_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                </select>

                <select className="admin-search" style={{ width: 'auto' }} value={category} onChange={e => { setCategory(e.target.value); setPage(1); }}>
                    <option value="">All Categories</option>
                    {categories.map(c => (
                        <option key={c.category} value={c.category === 'uncategorized' ? '' : c.category}>
                            {c.category} ({c.count})
                        </option>
                    ))}
                </select>

                <select className="admin-search" style={{ width: 'auto' }} value={success} onChange={e => { setSuccess(e.target.value); setPage(1); }}>
                    {SUCCESS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>

                <span className="admin-count">{total} entries</span>
            </div>

            <div style={{ overflowX: 'auto' }}>
                <AdminTable
                    columns={columns}
                    data={items}
                    loading={loading}
                    emptyMessage="No edit logs yet"
                    page={page}
                    total={total}
                    limit={50}
                    onPageChange={setPage}
                />
            </div>
        </div>
    );
}
