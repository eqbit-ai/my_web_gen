import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetDomainDetail } from '../../services/adminApi';
import formatDate from './shared/formatDate';


export default function DomainDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [domain, setDomain] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetDomainDetail(id);
            setDomain(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [id]);

    useEffect(() => { load(); }, [load]);

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    if (!domain) return <div className="admin-empty">Domain not found</div>;

    const infoFields = [
        { label: 'Domain', value: domain.domain },
        { label: 'Site Name', value: domain.site_name },
        { label: 'Status', value: domain.status, badge: true },
        { label: 'SSL', value: domain.ssl_status, badge: true },
        { label: 'CloudFront Domain', value: domain.cloudfront_domain },
        { label: 'CloudFront Distribution', value: domain.cloudfront_distribution_id },
        { label: 'ACM Certificate', value: domain.acm_certificate_arn, mono: true },
        { label: 'Route53 Zone', value: domain.route53_zone_id },
        { label: 'Deployed URL', value: domain.deployed_url },
        { label: 'Created', value: formatDate(domain.created_at) },
        { label: 'Updated', value: formatDate(domain.updated_at) },
    ];

    return (
        <div>
            <div className="admin-page-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button className="admin-back" onClick={() => navigate('/admin/domains')}><ArrowLeft size={16} /></button>
                    <h1 className="admin-page-title" style={{ marginBottom: 0 }}>{domain.domain || `Domain #${id}`}</h1>
                    <StatusBadge status={domain.status} />
                </div>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Domain Info */}
            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-card-title">Domain Details</div>
                <div className="admin-detail-grid">
                    {infoFields.map(({ label, value, badge, mono }) => (
                        <div key={label} className="admin-detail-item">
                            <span className="admin-detail-label">{label}</span>
                            {badge ? (
                                <StatusBadge status={value || 'none'} size="sm" />
                            ) : (
                                <strong style={mono ? { fontSize: '0.75rem', wordBreak: 'break-all' } : undefined}>
                                    {value || '—'}
                                </strong>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Owner Info */}
            {domain.owner && (
                <div className="admin-card" style={{ marginBottom: 24 }}>
                    <div className="admin-card-title">Owner</div>
                    <div className="admin-detail-grid">
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Email</span>
                            <strong>{domain.owner.email || '—'}</strong>
                        </div>
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Name</span>
                            <strong>{domain.owner.full_name || '—'}</strong>
                        </div>
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Company</span>
                            <strong>{domain.owner.company_name || '—'}</strong>
                        </div>
                    </div>
                </div>
            )}

            {/* DNS Records */}
            {domain.dns_records && (
                <div className="admin-card">
                    <div className="admin-card-title">DNS Records</div>
                    <pre style={{ fontSize: '0.8rem', whiteSpace: 'pre-wrap', color: '#e4e4e7', margin: 0, padding: 12 }}>
                        {typeof domain.dns_records === 'string' ? domain.dns_records : JSON.stringify(domain.dns_records, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
