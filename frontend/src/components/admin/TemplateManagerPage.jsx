import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Edit3, Check, X, Eye } from 'lucide-react';
import { adminGetTemplates, adminUpdateTemplate } from '../../services/adminApi';
import config from '../../config';

const T = { bg: '#0a0a0f', surface: '#12121a', surfaceHover: '#1a1a28', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8' };
const API = config.apiUrl;

function TemplateThumbnail({ templateId, name, colors }) {
    const [html, setHtml] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            try {
                const res = await fetch(`${API}/api/templates/${templateId}/preview`);
                if (!res.ok) throw new Error('failed');
                const data = await res.json();
                if (!cancelled) {
                    const combined = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${data.css || ''}</style></head><body>${data.html || ''}</body></html>`;
                    setHtml(combined);
                }
            } catch {
                if (!cancelled) setError(true);
            }
            if (!cancelled) setLoading(false);
        };
        load();
        return () => { cancelled = true; };
    }, [templateId]);

    if (loading) {
        return (
            <div style={{ width: '100%', height: 180, background: T.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px 8px 0 0' }}>
                <RefreshCw size={18} style={{ color: T.muted, animation: 'spin 1s linear infinite' }} />
            </div>
        );
    }

    if (error || !html) {
        // Fallback: show color swatches
        return (
            <div style={{ width: '100%', height: 180, background: T.bg, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', borderRadius: '8px 8px 0 0', gap: 12 }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: T.text, opacity: 0.3 }}>{(name || '?')[0]}</div>
                {colors && colors.length > 0 && (
                    <div style={{ display: 'flex', gap: 4 }}>
                        {colors.map((c, i) => (
                            <div key={i} style={{ width: 20, height: 20, borderRadius: 4, background: c, border: `1px solid ${T.border}` }} />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div style={{ width: '100%', height: 180, overflow: 'hidden', borderRadius: '8px 8px 0 0', position: 'relative', background: '#fff' }}>
            <iframe
                srcDoc={html}
                title={name}
                style={{
                    width: 1280,
                    height: 900,
                    border: 'none',
                    transformOrigin: 'top left',
                    transform: 'scale(0.22)',
                    pointerEvents: 'none',
                }}
                sandbox="allow-same-origin"
                loading="lazy"
            />
        </div>
    );
}

export default function TemplateManagerPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [editing, setEditing] = useState(null);
    const [editData, setEditData] = useState({});
    const [saving, setSaving] = useState(false);
    const [preview, setPreview] = useState(null);
    const [filterCat, setFilterCat] = useState('all');

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetTemplates();
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const templates = Array.isArray(data) ? data : data?.templates || data?.items || [];
    const categories = ['all', ...new Set(templates.map(t => t.category).filter(Boolean))];
    const filtered = filterCat === 'all' ? templates : templates.filter(t => t.category === filterCat);

    const handleToggle = async (template) => {
        try {
            await adminUpdateTemplate(template.id, {
                enabled: template.enabled === false ? true : false,
            });
            load();
        } catch {}
    };

    const handleSave = async () => {
        if (!editing) return;
        setSaving(true);
        try { await adminUpdateTemplate(editing, editData); setEditing(null); load(); } catch {}
        setSaving(false);
    };

    const startEdit = (t) => {
        setEditing(t.id);
        setEditData({ name: t.name || t.title, category: t.category, description: t.description });
    };

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Templates</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: T.muted }}>Category:</span>
                {categories.map(cat => (
                    <button
                        key={cat}
                        onClick={() => setFilterCat(cat)}
                        style={{
                            padding: '4px 12px', borderRadius: 6, fontSize: 12, border: `1px solid ${T.border}`,
                            background: filterCat === cat ? T.accent : 'transparent',
                            color: filterCat === cat ? '#fff' : T.text,
                            cursor: 'pointer', textTransform: 'capitalize',
                        }}
                    >
                        {cat}
                    </button>
                ))}
                <span style={{ marginLeft: 'auto', fontSize: 12, color: T.muted }}>
                    {filtered.length} template{filtered.length !== 1 ? 's' : ''}
                </span>
            </div>

            {/* Edit Modal */}
            {editing && (
                <>
                    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 999 }} onClick={() => setEditing(null)} />
                    <div style={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: T.surface, border: `1px solid ${T.border}`, borderRadius: 12, padding: 24, zIndex: 1000, width: 420, maxWidth: '90vw' }}>
                        <h3 style={{ color: T.text, marginTop: 0 }}>Edit Template</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 16 }}>
                            <div>
                                <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Name</label>
                                <input className="admin-input" value={editData.name || ''} onChange={e => setEditData({ ...editData, name: e.target.value })} />
                            </div>
                            <div>
                                <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Category</label>
                                <input className="admin-input" value={editData.category || ''} onChange={e => setEditData({ ...editData, category: e.target.value })} />
                            </div>
                            <div>
                                <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Description</label>
                                <textarea className="admin-input" style={{ minHeight: 80, resize: 'vertical' }} value={editData.description || ''} onChange={e => setEditData({ ...editData, description: e.target.value })} />
                            </div>
                            <div style={{ display: 'flex', gap: 8 }}>
                                <button className="admin-btn admin-btn-primary" onClick={handleSave} disabled={saving}>
                                    <Check size={14} /> {saving ? 'Saving...' : 'Save'}
                                </button>
                                <button className="admin-btn" onClick={() => setEditing(null)}><X size={14} /> Cancel</button>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* Preview Modal */}
            {preview && (
                <>
                    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 999 }} onClick={() => setPreview(null)} />
                    <div style={{ position: 'fixed', top: '3%', left: '5%', right: '5%', bottom: '3%', background: '#fff', borderRadius: 12, zIndex: 1000, overflow: 'hidden' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 16px', background: T.surface, borderBottom: `1px solid ${T.border}` }}>
                            <span style={{ color: T.text, fontSize: 14, fontWeight: 600 }}>{preview.name}</span>
                            <button onClick={() => setPreview(null)} style={{ background: 'none', border: 'none', color: T.text, cursor: 'pointer', padding: 4 }}><X size={18} /></button>
                        </div>
                        <iframe
                            src={`${API}/api/templates/${preview.id}/preview`}
                            srcDoc={preview._html || undefined}
                            title={preview.name}
                            style={{ width: '100%', height: 'calc(100% - 40px)', border: 'none' }}
                        />
                    </div>
                </>
            )}

            {/* Template Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: 20,
            }}>
                {filtered.map(t => (
                    <div key={t.id} style={{
                        background: T.surface,
                        borderRadius: 12,
                        border: `1px solid ${T.border}`,
                        overflow: 'hidden',
                        opacity: t.enabled === false ? 0.5 : 1,
                        transition: 'all 0.2s',
                    }}>
                        {/* Thumbnail */}
                        <TemplateThumbnail templateId={t.id} name={t.name} colors={t.colors} />

                        {/* Info */}
                        <div style={{ padding: '12px 16px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                                <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: T.text }}>{t.name || t.title}</h4>
                                <span style={{
                                    fontSize: 10, padding: '2px 8px', borderRadius: 4,
                                    background: t.enabled === false ? 'rgba(248,113,113,0.15)' : 'rgba(52,211,153,0.15)',
                                    color: t.enabled === false ? '#f87171' : '#34d399',
                                }}>
                                    {t.enabled === false ? 'Disabled' : 'Active'}
                                </span>
                            </div>
                            <div style={{ fontSize: 11, color: T.accent, marginBottom: 6 }}>{t.category || 'Uncategorized'}</div>
                            <p style={{ fontSize: 12, color: T.muted, margin: '0 0 12px', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                {t.description}
                            </p>

                            {/* Color swatches */}
                            {t.colors && t.colors.length > 0 && (
                                <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
                                    {t.colors.map((c, i) => (
                                        <div key={i} title={c} style={{ width: 16, height: 16, borderRadius: 3, background: c, border: `1px solid ${T.border}` }} />
                                    ))}
                                </div>
                            )}

                            {/* Actions */}
                            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                <button
                                    onClick={() => {
                                        fetch(`${API}/api/templates/${t.id}/preview`)
                                            .then(r => r.json())
                                            .then(d => {
                                                const fullHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${d.css || ''}</style></head><body>${d.html || ''}</body></html>`;
                                                setPreview({ ...t, _html: fullHtml });
                                            })
                                            .catch(() => setPreview(t));
                                    }}
                                    style={{ padding: '5px 10px', borderRadius: 6, fontSize: 11, border: `1px solid ${T.border}`, background: 'transparent', color: T.text, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
                                >
                                    <Eye size={12} /> Preview
                                </button>
                                <button
                                    onClick={() => startEdit(t)}
                                    style={{ padding: '5px 10px', borderRadius: 6, fontSize: 11, border: `1px solid ${T.border}`, background: 'transparent', color: T.text, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
                                >
                                    <Edit3 size={12} /> Edit
                                </button>
                                <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 11, color: T.muted }}>
                                    <div
                                        onClick={() => handleToggle(t)}
                                        style={{
                                            width: 34, height: 18, borderRadius: 9, position: 'relative', cursor: 'pointer',
                                            background: t.enabled === false ? T.border : '#34d399',
                                            transition: 'background 0.2s',
                                        }}
                                    >
                                        <div style={{
                                            width: 14, height: 14, borderRadius: '50%', background: '#fff',
                                            position: 'absolute', top: 2,
                                            left: t.enabled === false ? 2 : 18,
                                            transition: 'left 0.2s',
                                        }} />
                                    </div>
                                </label>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {filtered.length === 0 && (
                <div style={{ textAlign: 'center', padding: 60, color: T.muted }}>
                    No templates found{filterCat !== 'all' ? ` in "${filterCat}"` : ''}
                </div>
            )}
        </div>
    );
}
