import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, RotateCcw, ExternalLink } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetSiteDetail, adminRebuildSite } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a' };


export default function SiteDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [site, setSite] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [rebuilding, setRebuilding] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const detail = await adminGetSiteDetail(id);
            setSite(detail);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [id]);

    useEffect(() => { load(); }, [load]);

    const handleRebuild = async () => {
        setRebuilding(true);
        try { await adminRebuildSite(id); load(); } catch {}
        setRebuilding(false);
    };

    if (loading) {
        return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    }

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    if (!site) return <div className="admin-empty">Site not found</div>;

    return (
        <div>
            <div className="admin-page-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button className="admin-back" onClick={() => navigate('/admin/sites')}><ArrowLeft size={16} /></button>
                    <h1 className="admin-page-title" style={{ marginBottom: 0 }}>Site #{id}</h1>
                    <StatusBadge status={site.status} />
                </div>
                {/* Rebuild button hidden — deployment pipeline not yet implemented */}
            </div>

            {/* Site Info */}
            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-detail-grid">
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">ID</span>
                        <strong style={{ fontSize: '0.8rem', fontFamily: 'monospace' }}>{site.id}</strong>
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">User ID</span>
                        <strong>{site.user_id ?? '—'}</strong>
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Owner</span>
                        <strong>{site.owner?.email || site.owner?.full_name || '—'}</strong>
                    </div>
                    {site.owner?.company_name && (
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Company</span>
                            <strong>{site.owner.company_name}</strong>
                        </div>
                    )}
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Name</span>
                        <strong>{site.name || '—'}</strong>
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Domain</span>
                        {site.domain ? (
                            <a href={`https://${site.domain}`} target="_blank" rel="noopener noreferrer" style={{ color: '#818cf8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                                {site.domain} <ExternalLink size={12} />
                            </a>
                        ) : <strong>—</strong>}
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Live URL</span>
                        {site.deployed_url ? (
                            <a href={site.deployed_url} target="_blank" rel="noopener noreferrer" style={{ color: '#34d399', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem', wordBreak: 'break-all' }}>
                                {site.deployed_url} <ExternalLink size={12} />
                            </a>
                        ) : <strong>—</strong>}
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Status</span>
                        <StatusBadge status={site.status} size="sm" />
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Is Multipage</span>
                        <StatusBadge status={site.is_multipage ? 'active' : 'disabled'} size="sm" />
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Page Count</span>
                        <strong>{site.page_count ?? '—'}</strong>
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Last Deployed At</span>
                        <strong>{formatDate(site.last_deployed_at)}</strong>
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Created At</span>
                        <strong>{formatDate(site.created_at)}</strong>
                    </div>
                    <div className="admin-detail-item">
                        <span className="admin-detail-label">Updated At</span>
                        <strong>{formatDate(site.updated_at)}</strong>
                    </div>
                </div>
            </div>

            {/* Preview */}
            <div className="admin-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <div className="admin-card-title" style={{ margin: 0 }}>Preview</div>
                    {(site.deployed_url || site.domain) && (
                        <a
                            href={site.domain ? `https://${site.domain}` : site.deployed_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="admin-btn admin-btn-sm"
                            style={{ display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none' }}
                        >
                            <ExternalLink size={12} /> Open in new tab
                        </a>
                    )}
                </div>
                {site.deployed_url ? (
                    <div style={{ borderRadius: 8, overflow: 'hidden', border: `1px solid ${T.border}`, background: '#fff' }}>
                        <iframe
                            src={site.deployed_url}
                            title="Site Preview"
                            style={{ width: '100%', height: 600, border: 'none' }}
                            sandbox="allow-scripts allow-same-origin"
                        />
                    </div>
                ) : (
                    <div className="admin-empty">No deployed URL available</div>
                )}
            </div>
        </div>
    );
}
