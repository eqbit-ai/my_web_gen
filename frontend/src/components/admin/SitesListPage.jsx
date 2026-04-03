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

    const loadGens = useCallback(async () => {
        setGenLoading(true);
        try {
            const res = await adminGetGenerations(genPage, 20, genStatus || null);
            setGenData(res);
        } catch {}
        finally { setGenLoading(false); }
    }, [genPage, genStatus]);

    useEffect(() => { loadGens(); }, [loadGens]);

    const gens = genData?.generations || [];
    const gensTotal = genData?.total || gens.length;

    // Sum total cost on this page
    const pageCost = gens.reduce((s, g) => s + (g.estimated_cost || 0), 0);
    const pageTokens = gens.reduce((s, g) => s + (g.tokens_consumed || 0), 0);

    const genColumns = [
        { key: 'user_id', label: 'User', render: (v, row) => <span style={{ fontSize: 12 }}>{row.user_email || `#${v}`}</span> },
        { key: 'prompt', label: 'Prompt', render: v => <span style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', fontSize: 12 }} title={v}>{v || '—'}</span> },
        { key: 'status', label: 'Status', render: v => <StatusBadge status={v} size="sm" /> },
        { key: 'page_count', label: 'Pages', render: (v, row) => <span>{row.is_multipage ? `${v}p` : '1p'}</span> },
        { key: 'duration_ms', label: 'Duration', render: v => v ? `${(v / 1000).toFixed(1)}s` : '—' },
        { key: 'tokens_consumed', label: 'Tokens', render: v => <span style={{ fontWeight: 600, fontSize: 12 }}>{v ? Number(v).toLocaleString() : '—'}</span> },
        { key: 'estimated_cost', label: 'Cost', render: v => <span style={{ fontWeight: 600, color: T.warning, fontSize: 12 }}>{v ? `$${v.toFixed(4)}` : '—'}</span> },
        { key: 'created_at', label: 'Date', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
    ];

    return (
        <div style={{ marginTop: 32 }}>
            <div className="admin-page-header" style={{ marginBottom: 12 }}>
                <h2 className="admin-page-title" style={{ fontSize: 16 }}>Generation Logs</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <select className="admin-search" style={{ width: 'auto', fontSize: 12, padding: '4px 8px' }} value={genStatus} onChange={e => { setGenStatus(e.target.value); setGenPage(1); }}>
                        <option value="">All</option>
                        <option value="completed">Completed</option>
                        <option value="failed">Failed</option>
                    </select>
                    {pageCost > 0 && <span style={{ fontSize: 11, color: T.muted }}>Page: {pageTokens.toLocaleString()} tokens • ${pageCost.toFixed(2)}</span>}
                    <button className="admin-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={loadGens}><RefreshCw size={12} /> Refresh</button>
                </div>
            </div>
            <AdminTable
                columns={genColumns}
                data={gens}
                loading={genLoading}
                emptyMessage="No generations found"
                page={genPage}
                total={gensTotal}
                limit={20}
                onPageChange={setGenPage}
            />
        </div>
    );
}
