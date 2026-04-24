import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, ExternalLink } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetSites, adminGetGenerations } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { muted: '#71717a', warning: '#fbbf24' };



export default function SitesListPage() {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetSites(page, 20, status || null);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, status]);

    useEffect(() => { load(); }, [load]);

    const sites = Array.isArray(data) ? data : data?.sites || data?.items || [];
    const total = data?.total || sites.length;

    const columns = [
        { key: 'id', label: 'ID', width: 60 },
        { key: 'user_id', label: 'User', render: (v, row) => row.user_email || v || '—' },
        {
            key: 'domain', label: 'Domain / URL',
            render: (v, row) => {
                const url = v ? `https://${v}` : row.deployed_url;
                if (url) return (
                    <a href={url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem' }}>
                        {v || 'S3 Link'} <ExternalLink size={10} />
                    </a>
                );
                return '—';
            },
        },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'created_at', label: 'Created', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
    ];

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Sites</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <div className="admin-toolbar">
                <select
                    className="admin-search"
                    style={{ width: 'auto' }}
                    value={status}
                    onChange={e => { setStatus(e.target.value); setPage(1); }}
                >
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="published">Published</option>
                    <option value="draft">Draft</option>
                </select>
                <span className="admin-count">{total} sites</span>
            </div>

            <AdminTable
                columns={columns}
                data={sites}
                loading={loading}
                emptyMessage="No sites found"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
                onRowClick={(row) => navigate(`/admin/sites/${row.id}`)}
            />

            {/* Generation Logs with per-website cost */}
            <GenerationLogs />
        </div>
    );
}


function GenerationLogs() {
    const [genPage, setGenPage] = useState(1);
    const [genStatus, setGenStatus] = useState('');
    const [genData, setGenData] = useState(null);
    const [genLoading, setGenLoading] = useState(true);
    const [userFilter, setUserFilter] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');


    const loadGens = useCallback(async () => {
        setGenLoading(true);
        try {
            const res = await adminGetGenerations(genPage, 20, genStatus || null, userFilter || null);
            setGenData(res);
        } catch {}
        finally { setGenLoading(false); }
    }, [genPage, genStatus, userFilter]);

    useEffect(() => { loadGens(); }, [loadGens]);

    // Client-side date filter (backend generations endpoint doesn't have date params)
    let gens = genData?.generations || [];
    if (dateFrom || dateTo) {
        gens = gens.filter(g => {
            const d = g.created_at ? new Date(g.created_at) : null;
            if (!d) return true;
            const dateStr = d.toISOString().split('T')[0];
            if (dateFrom && dateStr < dateFrom) return false;
            if (dateTo && dateStr > dateTo) return false;
            return true;
        });
    }
    const gensTotal = genData?.total || gens.length;

    const pageCost = gens.reduce((s, g) => s + (g.estimated_cost || 0), 0);
    const pageTokens = gens.reduce((s, g) => s + (g.tokens_consumed || 0), 0);

    const [expandedId, setExpandedId] = useState(null);

    const D = { bg: '#1a1a2e', border: '#2a2a3a', surface: '#22223a', text: '#e4e4e7' };

    return (
        <div style={{ marginTop: 32 }}>
            <div className="admin-page-header" style={{ marginBottom: 12 }}>
                <h2 className="admin-page-title" style={{ fontSize: 16 }}>Generation Logs</h2>
                <button className="admin-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={loadGens}><RefreshCw size={12} /> Refresh</button>
            </div>

            <div className="admin-toolbar" style={{ gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                <select className="admin-search" style={{ width: 'auto', fontSize: 12, padding: '4px 8px' }} value={genStatus} onChange={e => { setGenStatus(e.target.value); setGenPage(1); }}>
                    <option value="">All Status</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                </select>
                <input className="admin-input" style={{ width: 200, fontSize: 12, padding: '4px 8px' }} placeholder="Filter by user email..." value={userFilter} onChange={e => { setUserFilter(e.target.value); setGenPage(1); }} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <label style={{ fontSize: 11, color: T.muted }}>From</label>
                    <input type="date" className="admin-input" style={{ width: 130, padding: '4px 8px', fontSize: 12 }} value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <label style={{ fontSize: 11, color: T.muted }}>To</label>
                    <input type="date" className="admin-input" style={{ width: 130, padding: '4px 8px', fontSize: 12 }} value={dateTo} onChange={e => setDateTo(e.target.value)} />
                </div>
                {(dateFrom || dateTo) && <button className="admin-btn" style={{ padding: '4px 8px', fontSize: 11, color: '#f87171' }} onClick={() => { setDateFrom(''); setDateTo(''); }}>Clear</button>}
                <span className="admin-count" style={{ marginLeft: 'auto', fontSize: 11 }}>
                    {gens.length} results{pageTokens > 0 ? ` • ${pageTokens.toLocaleString()} tokens • $${pageCost.toFixed(2)}` : ''}
                </span>
            </div>

            <div className="admin-card" style={{ padding: 0, overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                        <tr style={{ borderBottom: `1px solid ${D.border}` }}>
                            {['User', 'Prompt', 'Status', 'Pages', 'Duration', 'Tokens', 'Cost', 'Date'].map(h => (
                                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontSize: 11, color: T.muted, textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {genLoading && <tr><td colSpan={8} style={{ padding: 24, textAlign: 'center', color: T.muted }}>Loading...</td></tr>}
                        {!genLoading && gens.length === 0 && <tr><td colSpan={8} style={{ padding: 24, textAlign: 'center', color: T.muted }}>No generations found</td></tr>}
                        {!genLoading && gens.map(g => (
                            <React.Fragment key={g.id}>
                                <tr
                                    onClick={() => setExpandedId(expandedId === g.id ? null : g.id)}
                                    style={{ borderBottom: `1px solid ${D.border}`, cursor: 'pointer', transition: 'background 0.15s' }}
                                    onMouseEnter={e => e.currentTarget.style.background = D.surface}
                                    onMouseLeave={e => e.currentTarget.style.background = ''}
                                >
                                    <td style={{ padding: '10px 12px', fontSize: 12 }}>{g.user_email || `#${g.user_id}`}</td>
                                    <td style={{ padding: '10px 12px', fontSize: 12, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={g.prompt}>{g.prompt || '—'}</td>
                                    <td style={{ padding: '10px 12px' }}><StatusBadge status={g.status} size="sm" /></td>
                                    <td style={{ padding: '10px 12px' }}>{g.is_multipage ? `${g.page_count}p` : '1p'}</td>
                                    <td style={{ padding: '10px 12px' }}>{g.duration_ms ? `${(g.duration_ms / 1000).toFixed(1)}s` : '—'}</td>
                                    <td style={{ padding: '10px 12px', fontWeight: 600, fontSize: 12 }}>{g.tokens_consumed ? Number(g.tokens_consumed).toLocaleString() : '—'}</td>
                                    <td style={{ padding: '10px 12px', fontWeight: 600, color: T.warning, fontSize: 12 }}>{g.estimated_cost ? `$${g.estimated_cost.toFixed(4)}` : '—'}</td>
                                    <td style={{ padding: '10px 12px' }}><span className="admin-date-cell">{formatDate(g.created_at)}</span></td>
                                </tr>
                                {expandedId === g.id && (
                                    <tr style={{ background: D.surface }}>
                                        <td colSpan={8} style={{ padding: '16px 20px' }}>
                                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px 24px', fontSize: 12 }}>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>Full Prompt</div>
                                                    <div style={{ color: D.text, lineHeight: 1.5 }}>{g.prompt || '—'}</div>
                                                </div>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>Session ID</div>
                                                    <div style={{ color: D.text, fontFamily: 'monospace', fontSize: 11 }}>{g.session_id || '—'}</div>
                                                </div>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>Generation ID</div>
                                                    <div style={{ color: D.text, fontFamily: 'monospace', fontSize: 11 }}>{g.id}</div>
                                                </div>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>HTML Size</div>
                                                    <div style={{ color: D.text }}>{g.html_size ? `${(g.html_size / 1024).toFixed(1)} KB` : '—'}</div>
                                                </div>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>Perf Score</div>
                                                    <div style={{ color: g.performance_score >= 85 ? '#34d399' : g.performance_score >= 70 ? T.warning : '#f87171', fontWeight: 600 }}>{g.performance_score ?? '—'}{g.performance_score ? '/100' : ''}</div>
                                                </div>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>SEO Score</div>
                                                    <div style={{ color: g.seo_score >= 85 ? '#34d399' : g.seo_score >= 70 ? T.warning : '#f87171', fontWeight: 600 }}>{g.seo_score ?? '—'}{g.seo_score ? '/100' : ''}</div>
                                                </div>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>Multipage</div>
                                                    <div style={{ color: D.text }}>{g.is_multipage ? `Yes (${g.page_count} pages)` : 'No (single page)'}</div>
                                                </div>
                                                <div>
                                                    <div style={{ color: T.muted, fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>Completed At</div>
                                                    <div style={{ color: D.text }}>{g.completed_at ? formatDate(g.completed_at) : '—'}</div>
                                                </div>
                                                {g.error_message && (
                                                    <div style={{ gridColumn: '1 / -1' }}>
                                                        <div style={{ color: '#f87171', fontSize: 10, textTransform: 'uppercase', marginBottom: 4 }}>Error</div>
                                                        <div style={{ color: '#f87171', fontFamily: 'monospace', fontSize: 11, background: 'rgba(248,113,113,0.1)', padding: '8px 12px', borderRadius: 6 }}>{g.error_message}</div>
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>
            </div>
            {gensTotal > 20 && (
                <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 12 }}>
                    <button className="admin-btn" disabled={genPage <= 1} onClick={() => setGenPage(p => p - 1)} style={{ padding: '4px 12px', fontSize: 12 }}>← Prev</button>
                    <span style={{ fontSize: 12, color: T.muted, padding: '6px 0' }}>Page {genPage} of {Math.ceil(gensTotal / 20)}</span>
                    <button className="admin-btn" disabled={genPage >= Math.ceil(gensTotal / 20)} onClick={() => setGenPage(p => p + 1)} style={{ padding: '4px 12px', fontSize: 12 }}>Next →</button>
                </div>
            )}
        </div>
    );
}
