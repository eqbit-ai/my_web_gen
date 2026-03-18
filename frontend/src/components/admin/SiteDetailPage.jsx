import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, ExternalLink, Clock, RotateCcw, CheckCircle } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetSiteDetail, adminGetSiteVersions, adminRestoreSiteVersion } from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a' };


export default function SiteDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [site, setSite] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [tab, setTab] = useState('info'); // 'info' | 'preview' | 'versions'
    const [versions, setVersions] = useState([]);
    const [versionsLoading, setVersionsLoading] = useState(false);
    const [restoring, setRestoring] = useState(null);
    const [restoreMsg, setRestoreMsg] = useState(null);

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

    const loadVersions = async () => {
        setVersionsLoading(true);
        try {
            const data = await adminGetSiteVersions(id);
            setVersions(data.versions || []);
        } catch (e) { setError(e.message); }
        setVersionsLoading(false);
    };

    const handleRestore = async (deploymentTime) => {
        if (!window.confirm(`Restore site to deployment from ${deploymentTime}?`)) return;
        setRestoring(deploymentTime);
        setRestoreMsg(null);
        try {
            const result = await adminRestoreSiteVersion(id, deploymentTime);
            setRestoreMsg({ type: 'success', text: result.message || 'Restored successfully' });
            loadVersions();
        } catch (e) {
            setRestoreMsg({ type: 'error', text: e.message || 'Restore failed' });
        }
        setRestoring(null);
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
                    <h1 className="admin-page-title" style={{ marginBottom: 0 }}>{site.name || `Site #${id}`}</h1>
                    <StatusBadge status={site.status} />
                </div>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Owner info bar */}
            {site.owner && (
                <div style={{ display: 'flex', gap: 16, fontSize: 13, color: T.muted, marginBottom: 16 }}>
                    <span>Owner: <strong style={{ color: T.text }}>{site.owner.full_name || site.owner.email}</strong></span>
                    {site.owner.company_name && <span>Company: <strong style={{ color: T.text }}>{site.owner.company_name}</strong></span>}
                    <span>User ID: <strong style={{ color: T.text }}>{site.user_id}</strong></span>
                </div>
            )}

            {/* Tabs */}
            <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: `1px solid ${T.border}` }}>
                {['info', 'preview', 'versions'].map(t => (
                    <button key={t} onClick={() => { setTab(t); if (t === 'versions' && versions.length === 0) loadVersions(); }}
                        style={{ padding: '10px 20px', background: 'none', border: 'none', borderBottom: tab === t ? '2px solid #818cf8' : '2px solid transparent', color: tab === t ? T.text : T.muted, fontSize: 14, fontWeight: 500, cursor: 'pointer', textTransform: 'capitalize' }}>
                        {t === 'versions' ? 'Deployment History' : t === 'info' ? 'Overview' : 'Preview'}
                    </button>
                ))}
            </div>

            {/* Overview Tab */}
            {tab === 'info' && (
                <div className="admin-card">
                    <div className="admin-detail-grid">
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">ID</span>
                            <strong style={{ fontSize: '0.8rem', fontFamily: 'monospace' }}>{site.id}</strong>
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
                            <span className="admin-detail-label">Multipage</span>
                            <strong>{site.is_multipage ? `Yes (${site.page_count} pages)` : 'No'}</strong>
                        </div>
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Last Deployed</span>
                            <strong>{formatDate(site.last_deployed_at)}</strong>
                        </div>
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Created</span>
                            <strong>{formatDate(site.created_at)}</strong>
                        </div>
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">CloudFront</span>
                            <strong style={{ fontSize: '0.8rem' }}>{site.cloudfront_domain || '—'}</strong>
                        </div>
                    </div>
                </div>
            )}

            {/* Preview Tab */}
            {tab === 'preview' && (
                <div className="admin-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <div className="admin-card-title" style={{ margin: 0 }}>Live Preview</div>
                        {(site.deployed_url || site.domain) && (
                            <a href={site.domain ? `https://${site.domain}` : site.deployed_url} target="_blank" rel="noopener noreferrer" className="admin-btn admin-btn-sm" style={{ display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none' }}>
                                <ExternalLink size={12} /> Open in new tab
                            </a>
                        )}
                    </div>
                    {site.deployed_url ? (
                        <div style={{ borderRadius: 8, overflow: 'hidden', border: `1px solid ${T.border}`, background: '#fff' }}>
                            <iframe src={site.deployed_url} title="Site Preview" style={{ width: '100%', height: 600, border: 'none' }} sandbox="allow-scripts allow-same-origin" />
                        </div>
                    ) : (
                        <div className="admin-empty">No deployed URL available</div>
                    )}
                </div>
            )}

            {/* Deployment History Tab */}
            {tab === 'versions' && (
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <p style={{ color: T.muted, fontSize: 13 }}>{versions.length} deployment{versions.length !== 1 ? 's' : ''} found</p>
                        <button className="admin-btn admin-btn-sm" onClick={loadVersions}><RefreshCw size={12} /> Refresh</button>
                    </div>

                    {restoreMsg && (
                        <div className={`admin-alert ${restoreMsg.type === 'success' ? 'admin-alert-success' : 'admin-alert-error'}`} style={{ marginBottom: 16 }}>
                            {restoreMsg.text}
                        </div>
                    )}

                    {versionsLoading ? (
                        <div style={{ padding: 40, textAlign: 'center', color: T.muted }}>Loading deployment history...</div>
                    ) : versions.length === 0 ? (
                        <div style={{ padding: 60, textAlign: 'center' }}>
                            <Clock size={48} style={{ color: T.muted, marginBottom: 16 }} />
                            <h3 style={{ color: T.text, marginBottom: 8 }}>No deployment history</h3>
                            <p style={{ color: T.muted }}>S3 versioning was just enabled. Future deployments will be tracked here.</p>
                        </div>
                    ) : (
                        <div style={{ display: 'grid', gap: 8 }}>
                            {versions.map((v, i) => (
                                <div key={v.deployment_time} style={{
                                    background: T.surface, border: `1px solid ${T.border}`, borderRadius: 10,
                                    padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                                        <div style={{
                                            width: 36, height: 36, borderRadius: '50%',
                                            background: v.is_current ? 'rgba(34,197,94,0.12)' : 'rgba(113,113,122,0.12)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            color: v.is_current ? '#22c55e' : T.muted,
                                        }}>
                                            {v.is_current ? <CheckCircle size={18} /> : <Clock size={18} />}
                                        </div>
                                        <div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <strong style={{ color: T.text, fontSize: 14 }}>
                                                    {v.deployment_time}
                                                </strong>
                                                {v.is_current && (
                                                    <span style={{ fontSize: 10, fontWeight: 600, color: '#22c55e', background: 'rgba(34,197,94,0.12)', padding: '2px 8px', borderRadius: 4 }}>Current</span>
                                                )}
                                            </div>
                                            <div style={{ fontSize: 12, color: T.muted, marginTop: 2 }}>
                                                {v.file_count} file{v.file_count !== 1 ? 's' : ''} · {v.total_size_kb} KB
                                            </div>
                                        </div>
                                    </div>
                                    {!v.is_current && (
                                        <button
                                            className="admin-btn admin-btn-sm"
                                            onClick={() => handleRestore(v.deployment_time)}
                                            disabled={!!restoring}
                                            style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                                        >
                                            <RotateCcw size={12} />
                                            {restoring === v.deployment_time ? 'Restoring...' : 'Restore'}
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
