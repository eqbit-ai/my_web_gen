// src/components/DesignSystemPanel.jsx
// Slide-out panel for viewing and editing the design system tokens

import React, { useState, useEffect, useCallback } from 'react';
import { X, RefreshCw, Check, Palette } from 'lucide-react';
import { updateDesignSystem, generateDesignSystem } from '../services/api';

const ColorSwatch = ({ label, value, onChange }) => (
    <div className="ds-color-item">
        <label className="ds-color-label">{label}</label>
        <div className="ds-color-preview">
            <input type="color" value={value || '#000000'} onChange={(e) => onChange(e.target.value)} />
            <span className="ds-color-hex">{value}</span>
        </div>
    </div>
);

const DesignSystemPanel = ({ isOpen, onClose, designSystem, sessionId, onUpdate }) => {
    const [ds, setDs] = useState(designSystem || {});
    const [saving, setSaving] = useState(false);
    const [regenerating, setRegenerating] = useState(false);

    useEffect(() => {
        if (designSystem) setDs(designSystem);
    }, [designSystem]);

    const updateColor = useCallback((key, value) => {
        setDs(prev => ({
            ...prev,
            colors: { ...prev.colors, [key]: value },
        }));
    }, []);

    const updateTypography = useCallback((key, value) => {
        setDs(prev => ({
            ...prev,
            typography: { ...prev.typography, [key]: value },
        }));
    }, []);

    const updateRadius = useCallback((key, value) => {
        setDs(prev => ({
            ...prev,
            borders: {
                ...prev.borders,
                radius: { ...(prev.borders?.radius || {}), [key]: value },
            },
        }));
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            const result = await updateDesignSystem(sessionId, ds);
            if (result.success && onUpdate) {
                onUpdate(ds, result.css);
            }
        } catch (err) {
            console.error('Failed to save design system:', err);
        } finally {
            setSaving(false);
        }
    };

    const handleRegenerate = async () => {
        setRegenerating(true);
        try {
            const result = await generateDesignSystem('regenerate design system with fresh colors');
            if (result.success) {
                setDs(result.designSystem);
            }
        } catch (err) {
            console.error('Failed to regenerate:', err);
        } finally {
            setRegenerating(false);
        }
    };

    if (!isOpen) return null;

    const colors = ds.colors || {};
    const typo = ds.typography || {};
    const borders = ds.borders || {};

    return (
        <div className="ds-panel-overlay">
            <div className="ds-panel">
                <div className="ds-panel-header">
                    <div className="ds-panel-title">
                        <Palette size={18} />
                        <span>Design System</span>
                    </div>
                    <div className="ds-panel-actions">
                        <button className="ds-btn-icon" onClick={handleRegenerate} disabled={regenerating} title="Regenerate">
                            <RefreshCw size={16} className={regenerating ? 'spinning' : ''} />
                        </button>
                        <button className="ds-btn-icon" onClick={onClose}><X size={18} /></button>
                    </div>
                </div>

                <div className="ds-panel-body">
                    {/* Colors */}
                    <div className="ds-section">
                        <h4 className="ds-section-title">Colors</h4>
                        <div className="ds-color-grid">
                            {['primary', 'primary_light', 'primary_dark', 'secondary', 'accent'].map(key => (
                                <ColorSwatch key={key} label={key.replace(/_/g, ' ')} value={colors[key]} onChange={(v) => updateColor(key, v)} />
                            ))}
                            {['background', 'surface', 'text', 'text_secondary', 'border'].map(key => (
                                <ColorSwatch key={key} label={key.replace(/_/g, ' ')} value={colors[key]} onChange={(v) => updateColor(key, v)} />
                            ))}
                        </div>
                    </div>

                    {/* Typography */}
                    <div className="ds-section">
                        <h4 className="ds-section-title">Typography</h4>
                        <div className="ds-form-row">
                            <label>Heading Font</label>
                            <input type="text" value={typo.heading_family || ''} onChange={(e) => updateTypography('heading_family', e.target.value)} placeholder="Inter" />
                        </div>
                        <div className="ds-form-row">
                            <label>Body Font</label>
                            <input type="text" value={typo.body_family || ''} onChange={(e) => updateTypography('body_family', e.target.value)} placeholder="Inter" />
                        </div>
                        <div className="ds-type-preview" style={{ fontFamily: `'${typo.heading_family || 'Inter'}', sans-serif` }}>
                            <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>Heading Preview</span>
                        </div>
                        <div className="ds-type-preview" style={{ fontFamily: `'${typo.body_family || 'Inter'}', sans-serif` }}>
                            <span style={{ fontSize: '1rem' }}>Body text preview — The quick brown fox jumps over the lazy dog.</span>
                        </div>
                    </div>

                    {/* Border Radius */}
                    <div className="ds-section">
                        <h4 className="ds-section-title">Border Radius</h4>
                        <div className="ds-radius-grid">
                            {['sm', 'md', 'lg', 'xl'].map(key => (
                                <div key={key} className="ds-radius-item">
                                    <div className="ds-radius-preview" style={{ borderRadius: borders.radius?.[key] || '8px', background: colors.primary || '#2563eb' }} />
                                    <input type="text" value={borders.radius?.[key] || ''} onChange={(e) => updateRadius(key, e.target.value)} />
                                    <span className="ds-radius-label">{key}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Layout */}
                    <div className="ds-section">
                        <h4 className="ds-section-title">Layout</h4>
                        <div className="ds-layout-info">
                            <span>Max Width: {ds.layout?.max_width || '1280px'}</span>
                            <span>Grid: {ds.layout?.columns || 12} columns</span>
                            <span>Gutter: {ds.layout?.gutter || '24px'}</span>
                        </div>
                    </div>
                </div>

                <div className="ds-panel-footer">
                    <button className="ds-btn-save" onClick={handleSave} disabled={saving}>
                        {saving ? <RefreshCw size={16} className="spinning" /> : <Check size={16} />}
                        {saving ? 'Applying...' : 'Apply Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DesignSystemPanel;
