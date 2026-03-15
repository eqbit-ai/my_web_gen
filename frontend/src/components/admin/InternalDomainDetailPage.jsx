import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetInternalDomainDetail } from '../../services/adminApi';
import formatDate from './shared/formatDate';


export default function InternalDomainDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [domain, setDomain] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetInternalDomainDetail(id);
            setDomain(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [id]);

    useEffect(() => { load(); }, [load]);

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    if (!domain) return <div className="admin-empty">Domain not found</div>;

    const infoFields = [
        { label: 'Domain', value: domain.domain_name },
        { label: 'TLD', value: domain.tld },
        { label: 'Registrar', value: domain.registrar },
        { label: 'Status', value: domain.status, badge: true },
        { label: 'DNS Status', value: domain.dns_status, badge: true },
        { label: 'SSL Status', value: domain.ssl_status, badge: true },
        { label: 'SSL Expires', value: formatDate(domain.ssl_expires_at) },
        { label: 'Verification', value: domain.verification_status, badge: true },
        { label: 'Licence Number', value: domain.licence_number },
        { label: 'Auto Renew', value: domain.auto_renew ? 'Yes' : 'No' },
        { label: 'Registered', value: formatDate(domain.registered_at) },
        { label: 'Expires', value: formatDate(domain.expires_at) },
        { label: 'Created', value: formatDate(domain.created_at) },
        { label: 'Updated', value: formatDate(domain.updated_at) },
    ];

    return (
        <div>
            <div className="admin-page-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button className="admin-back" onClick={() => navigate('/admin/domains-internal')}><ArrowLeft size={16} /></button>
                    <h1 className="admin-page-title" style={{ marginBottom: 0 }}>{domain.domain_name || `Domain #${id}`}</h1>
                    <StatusBadge status={domain.status} />
                </div>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-card-title">Domain Details</div>
                <div className="admin-detail-grid">
                    {infoFields.map(({ label, value, badge }) => (
                        <div key={label} className="admin-detail-item">
                            <span className="admin-detail-label">{label}</span>
                            {badge ? (
                                <StatusBadge status={value || 'none'} size="sm" />
                            ) : (
                                <strong>{value || '—'}</strong>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {domain.verification_notes && (
                <div className="admin-card" style={{ marginBottom: 24 }}>
                    <div className="admin-card-title">Verification Notes</div>
                    <p style={{ color: '#e4e4e7', margin: 0, padding: 12 }}>{domain.verification_notes}</p>
                </div>
            )}

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

            {domain.site && (
                <div className="admin-card">
                    <div className="admin-card-title">Linked Site</div>
                    <div className="admin-detail-grid">
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Site Name</span>
                            <strong>{domain.site.name || '—'}</strong>
                        </div>
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">Status</span>
                            <StatusBadge status={domain.site.status} size="sm" />
                        </div>
                        <div className="admin-detail-item">
                            <span className="admin-detail-label">URL</span>
                            <strong style={{ fontSize: '0.8rem', wordBreak: 'break-all' }}>{domain.site.deployed_url || '—'}</strong>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
