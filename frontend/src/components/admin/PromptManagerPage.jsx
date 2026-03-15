import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Save, Check, Terminal } from 'lucide-react';
import { adminGetPrompts, adminSavePrompt, adminPublishPrompt } from '../../services/adminApi';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399', warning: '#fbbf24' };

export default function PromptManagerPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedKey, setSelectedKey] = useState(null);
    const [editContent, setEditContent] = useState('');
    const [saving, setSaving] = useState(false);
    const [dirty, setDirty] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetPrompts();
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    // Normalize prompts: could be object keyed by name, array, or {items: [...]}
    const prompts = (() => {
        if (!data) return [];
        if (Array.isArray(data)) return data;
        if (Array.isArray(data?.prompts)) return data.prompts;
        if (Array.isArray(data?.items)) return data.items;
        if (typeof data === 'object') {
            return Object.entries(data).map(([key, val]) => ({
                key,
                ...(typeof val === 'object' && val !== null ? val : { content: String(val) }),
            }));
        }
        return [];
    })();

    const selectedPrompt = prompts.find(p => (p.key || p.name) === selectedKey);

    const selectPrompt = (p) => {
        const key = p.key || p.name;
        setSelectedKey(key);
        setEditContent(p.content || p.text || '');
        setDirty(false);
    };

    const handleSave = async () => {
        if (!selectedKey) return;
        setSaving(true);
        try {
            await adminSavePrompt(selectedKey, editContent);
            setDirty(false);
            load();
        } catch {}
        setSaving(false);
    };

    const handlePublish = async (key, version) => {
        try { await adminPublishPrompt(key, version); load(); } catch {}
    };

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Prompt Manager</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            <div className="admin-prompt-layout">
                {/* Key List */}
                <div className="admin-prompt-list">
                    <div style={{ padding: '12px 14px', borderBottom: `1px solid ${T.border}`, fontSize: 11, color: T.muted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Prompts ({prompts.length})
                    </div>
                    {prompts.map((p, i) => {
                        const key = p.key || p.name || `prompt-${i}`;
                        const active = selectedKey === key;
                        return (
                            <button
                                key={key}
                                className={`admin-prompt-item${active ? ' active' : ''}`}
                                onClick={() => selectPrompt(p)}
                            >
                                <Terminal size={14} />
                                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{key}</span>
                                <span className="admin-prompt-version">v{p.active_version || p.version || p.published_version || 1}</span>
                            </button>
                        );
                    })}
                    {prompts.length === 0 && (
                        <div style={{ padding: 20, color: T.muted, fontSize: 13, textAlign: 'center' }}>No prompts configured</div>
                    )}
                </div>

                {/* Editor */}
                <div className="admin-prompt-editor">
                    {selectedKey ? (
                        <>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                <div>
                                    <h3 style={{ fontSize: 16, fontWeight: 600, color: T.text, margin: 0 }}>{selectedKey}</h3>
                                    <span style={{ fontSize: 12, color: T.muted }}>
                                        v{selectedPrompt?.active_version || selectedPrompt?.version || 1}
                                        {selectedPrompt?.draft_version && (
                                            <span style={{ color: T.warning, marginLeft: 8 }}>
                                                Draft v{selectedPrompt.draft_version}
                                            </span>
                                        )}
                                    </span>
                                </div>
                                <div className="admin-actions">
                                    <button className="admin-btn admin-btn-primary" onClick={handleSave} disabled={saving || !dirty}>
                                        <Save size={14} /> {saving ? 'Saving...' : 'Save Draft'}
                                    </button>
                                    {selectedPrompt?.draft_version && (
                                        <button
                                            className="admin-btn admin-btn-success"
                                            onClick={() => handlePublish(selectedKey, selectedPrompt.draft_version)}
                                        >
                                            <Check size={14} /> Publish v{selectedPrompt.draft_version}
                                        </button>
                                    )}
                                </div>
                            </div>

                            <textarea
                                className="admin-prompt-textarea"
                                style={{ minHeight: 400 }}
                                value={editContent}
                                onChange={e => { setEditContent(e.target.value); setDirty(true); }}
                            />

                            {/* Version History */}
                            {selectedPrompt?.versions && (Array.isArray(selectedPrompt.versions) ? selectedPrompt.versions : []).length > 0 && (
                                <div style={{ marginTop: 20 }}>
                                    <h4 style={{ fontSize: 13, fontWeight: 600, color: T.text, marginBottom: 12 }}>Version History</h4>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {(selectedPrompt.versions || []).map((v, i) => (
                                            <div key={i} className="admin-prompt-version-row">
                                                <div>
                                                    <span style={{ color: T.text, fontWeight: 600, fontSize: 13 }}>v{v.version || i + 1}</span>
                                                    <span style={{ color: T.muted, fontSize: 12, marginLeft: 8 }}>
                                                        {v.created_at ? new Date(v.created_at).toLocaleDateString() : ''}
                                                    </span>
                                                    {v.version === (selectedPrompt.active_version || selectedPrompt.published_version) && (
                                                        <span style={{ color: T.success, fontSize: 11, marginLeft: 8, fontWeight: 600 }}>ACTIVE</span>
                                                    )}
                                                </div>
                                                <button
                                                    className="admin-btn admin-btn-sm"
                                                    onClick={() => { setEditContent(v.content || v.text || ''); setDirty(true); }}
                                                >
                                                    Load
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: T.muted, fontSize: 14 }}>
                            Select a prompt to edit
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
