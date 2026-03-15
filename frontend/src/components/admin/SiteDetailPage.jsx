import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, RotateCcw, ExternalLink } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetSiteDetail, adminGetSitePreview, adminRebuildSite } from '../../services/adminApi';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a' };

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

export default function SiteDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [site, setSite] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [rebuilding, setRebuilding] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [detail, prev] = await Promise.all([
                adminGetSiteDetail(id),
                adminGetSitePreview(id).catch(() => null),
            ]);
            setSite(detail);
            setPreview(prev);
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
                <button className="admin-btn admin-btn-primary" onClick={handleRebuild} disabled={rebuilding}>
                    <RotateCcw size={14} /> {rebuilding ? 'Rebuilding...' : 'Rebuild'}
                </button>
            </div>

            {/* Site Info */}
            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-detail-grid">
                    {Object.entries(site).filter(([k]) => !['html', 'css', 'js', 'preview', 'pages'].includes(k)).map(([k, v]) => (
                        <div key={k} className="admin-detail-item">
                            <span className="admin-detail-label">{k.replace(/_/g, ' ')}</span>
                            {typeof v === 'boolean' ? (
                                <StatusBadge status={v ? 'active' : 'disabled'} size="sm" />
                            ) : (
                                <strong>{v === null ? '—' : k.includes('_at') || k.includes('date') ? formatDate(v) : String(v)}</strong>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Preview */}
            <div className="admin-card">
                <div className="admin-card-title">Preview</div>
                {preview?.html || preview?.url ? (
                    <div style={{ borderRadius: 8, overflow: 'hidden', border: `1px solid ${T.border}`, background: '#fff' }}>
                        {preview.url ? (
                            <iframe
                                src={preview.url}
                                title="Site Preview"
                                style={{ width: '100%', height: 500, border: 'none' }}
                            />
                        ) : (
                            <iframe
                                srcDoc={preview.html}
                                title="Site Preview"
                                style={{ width: '100%', height: 500, border: 'none' }}
                            />
                        )}
                    </div>
                ) : (
                    <div className="admin-empty">No preview available</div>
                )}
            </div>
        </div>
    );
}
