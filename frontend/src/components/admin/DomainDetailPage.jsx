import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Shield, Save, CheckCircle, XCircle } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetDomainDetail, adminUpdateDomain, adminReprovisionSSL, adminVerifyDomain } from '../../services/adminApi';

const T = { bg: '#0a0a0f', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a' };

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

export default function DomainDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [domain, setDomain] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);
    const [editFields, setEditFields] = useState({});
    const [editing, setEditing] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetDomainDetail(id);
            setDomain(res);
            setEditFields(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [id]);

    useEffect(() => { load(); }, [load]);

    const handleSave = async () => {
        setSaving(true);
        try { await adminUpdateDomain(id, editFields); setEditing(false); load(); } catch {}
        setSaving(false);
    };

    const handleSSL = async () => {
        try { await adminReprovisionSSL(id); load(); } catch {}
    };

    const handleVerify = async (status) => {
        try { await adminVerifyDomain(id, status); load(); } catch {}
    };

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    if (!domain) return <div className="admin-empty">Domain not found</div>;

    return (
        <div>
            <div className="admin-page-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button className="admin-back" onClick={() => navigate('/admin/domains')}><ArrowLeft size={16} /></button>
                    <h1 className="admin-page-title" style={{ marginBottom: 0 }}>{domain.domain || domain.name || `Domain #${id}`}</h1>
                    <StatusBadge status={domain.status} />
                </div>
                <div className="admin-actions">
                    <button className="admin-btn" onClick={handleSSL}><Shield size={14} /> Reprovision SSL</button>
                    {!editing ? (
                        <button className="admin-btn admin-btn-primary" onClick={() => setEditing(true)}>Edit</button>
                    ) : (
                        <>
                            <button className="admin-btn admin-btn-primary" onClick={handleSave} disabled={saving}>
                                <Save size={14} /> {saving ? 'Saving...' : 'Save'}
                            </button>
                            <button className="admin-btn" onClick={() => { setEditing(false); setEditFields(domain); }}>Cancel</button>
                        </>
                    )}
                </div>
            </div>

            {/* Domain Info */}
            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-detail-grid">
                    {Object.entries(domain).filter(([k]) => typeof domain[k] !== 'object' || domain[k] === null).map(([k, v]) => (
                        <div key={k} className="admin-detail-item">
                            <span className="admin-detail-label">{k.replace(/_/g, ' ')}</span>
                            {editing && !['id', 'created_at', 'updated_at'].includes(k) ? (
                                <input
                                    className="admin-input"
                                    value={editFields[k] || ''}
                                    onChange={e => setEditFields({ ...editFields, [k]: e.target.value })}
                                />
                            ) : (
                                <strong>{v === null ? '—' : k.includes('_at') || k.includes('date') ? formatDate(v) : String(v)}</strong>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* SSL Info */}
            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-card-title">SSL Certificate</div>
                <div className="admin-card-stats">
                    <div>
                        <span className="admin-card-stat-label">Status</span>
                        <StatusBadge status={domain.ssl_status || 'unknown'} />
                    </div>
                    <div>
                        <span className="admin-card-stat-label">Expires</span>
                        <strong>{formatDate(domain.ssl_expires_at)}</strong>
                    </div>
                    <div>
                        <span className="admin-card-stat-label">Provider</span>
                        <strong>{domain.ssl_provider || '—'}</strong>
                    </div>
                </div>
            </div>

            {/* .ae Verification */}
            {domain.tld === '.ae' && (
                <div className="admin-card">
                    <div className="admin-card-title">.ae Verification</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 }}>
                        <StatusBadge status={domain.ae_verification_status || domain.verification_status || 'pending'} />
                        <button className="admin-btn admin-btn-success" onClick={() => handleVerify('verified')}>
                            <CheckCircle size={14} /> Approve
                        </button>
                        <button className="admin-btn admin-btn-danger" onClick={() => handleVerify('rejected')}>
                            <XCircle size={14} /> Reject
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
