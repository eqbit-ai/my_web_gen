// src/components/FooterEditor.jsx
// Edit footer columns, copyright text, social links, and logo

import React, { useState } from 'react';
import { X, Plus, Trash2, Save, Loader, Columns, Type } from 'lucide-react';
import { updateFooterConfig } from '../services/api';
import LogoUploader from './LogoUploader';

const SOCIAL_PLATFORMS = [
    { key: 'facebook', label: 'Facebook' },
    { key: 'instagram', label: 'Instagram' },
    { key: 'twitter', label: 'X (Twitter)' },
    { key: 'linkedin', label: 'LinkedIn' },
    { key: 'youtube', label: 'YouTube' },
    { key: 'tiktok', label: 'TikTok' },
    { key: 'whatsapp', label: 'WhatsApp' },
    { key: 'snapchat', label: 'Snapchat' },
];

const FooterEditor = ({ isOpen, onClose, sessionId, projectId, logoUrl, onUpdate, onLogoChange }) => {
    const [columns, setColumns] = useState([
        { heading: 'Company', links: [{ label: 'About Us', href: '#about' }, { label: 'Services', href: '#services' }] },
        { heading: 'Support', links: [{ label: 'Contact', href: '#contact' }, { label: 'FAQ', href: '#faq' }] },
    ]);
    const [copyrightText, setCopyrightText] = useState(`${new Date().getFullYear()} Company Name. All rights reserved.`);
    const [socialLinks, setSocialLinks] = useState([]);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const addColumn = () => {
        setColumns(prev => [...prev, { heading: 'New Column', links: [] }]);
    };

    const removeColumn = (index) => {
        setColumns(prev => prev.filter((_, i) => i !== index));
    };

    const updateColumn = (colIndex, field, value) => {
        setColumns(prev => prev.map((col, i) => i === colIndex ? { ...col, [field]: value } : col));
    };

    const addLink = (colIndex) => {
        setColumns(prev => prev.map((col, i) =>
            i === colIndex ? { ...col, links: [...col.links, { label: '', href: '#' }] } : col
        ));
    };

    const removeLink = (colIndex, linkIndex) => {
        setColumns(prev => prev.map((col, i) =>
            i === colIndex ? { ...col, links: col.links.filter((_, li) => li !== linkIndex) } : col
        ));
    };

    const updateLink = (colIndex, linkIndex, field, value) => {
        setColumns(prev => prev.map((col, i) =>
            i === colIndex ? {
                ...col,
                links: col.links.map((link, li) => li === linkIndex ? { ...link, [field]: value } : link)
            } : col
        ));
    };

    const toggleSocial = (platform) => {
        setSocialLinks(prev => {
            const exists = prev.find(s => s.platform === platform);
            if (exists) return prev.filter(s => s.platform !== platform);
            return [...prev, { platform, url: '' }];
        });
    };

    const updateSocialUrl = (platform, url) => {
        setSocialLinks(prev => prev.map(s => s.platform === platform ? { ...s, url } : s));
    };

    const handleSave = async () => {
        setSaving(true);
        setError('');
        try {
            const result = await updateFooterConfig(sessionId, columns, copyrightText, socialLinks);
            if (result.success) {
                onUpdate(result.html, result.css, result.js);
                onClose();
            }
        } catch (err) {
            setError('Failed to update: ' + err.message);
        }
        setSaving(false);
    };

    if (!isOpen) return null;

    return (
        <div className="fe-overlay" onClick={onClose} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClose(e); }} role="button" tabIndex={0}>
            <div className="fe-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                <div className="fe-header">
                    <h3><Columns size={16} /> Footer Editor</h3>
                    <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
                </div>

                <div className="fe-body">
                    <LogoUploader logoUrl={logoUrl} onLogoChange={onLogoChange} projectId={projectId} />

                    {/* Copyright */}
                    <div className="fe-section">
                        <label><Type size={14} /> Copyright Text</label>
                        <input type="text" value={copyrightText} onChange={e => setCopyrightText(e.target.value)} />
                    </div>

                    {/* Social Links */}
                    <div className="fe-section">
                        <label>Social Media</label>
                        <div className="fe-social-grid">
                            {SOCIAL_PLATFORMS.map(p => {
                                const active = socialLinks.find(s => s.platform === p.key);
                                return (
                                    <div key={p.key} className={`fe-social-item ${active ? 'active' : ''}`}>
                                        <label>
                                            <input type="checkbox" checked={!!active} onChange={() => toggleSocial(p.key)} />
                                            <span>{p.label}</span>
                                        </label>
                                        {active && (
                                            <input
                                                type="text"
                                                value={active.url}
                                                onChange={e => updateSocialUrl(p.key, e.target.value)}
                                                placeholder={`${p.label} URL...`}
                                            />
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Columns */}
                    <div className="fe-section">
                        <div className="fe-columns-header">
                            <label>Footer Columns ({columns.length})</label>
                            <button onClick={addColumn} disabled={columns.length >= 4}><Plus size={14} /> Add Column</button>
                        </div>
                        {columns.map((col, ci) => (
                            <div key={ci} className="fe-column">
                                <div className="fe-column-header">
                                    <input type="text" value={col.heading} onChange={e => updateColumn(ci, 'heading', e.target.value)} placeholder="Column heading" />
                                    <button onClick={() => removeColumn(ci)}><Trash2 size={14} /></button>
                                </div>
                                {col.links.map((link, li) => (
                                    <div key={li} className="fe-link-row">
                                        <input type="text" value={link.label} onChange={e => updateLink(ci, li, 'label', e.target.value)} placeholder="Label" />
                                        <input type="text" value={link.href} onChange={e => updateLink(ci, li, 'href', e.target.value)} placeholder="#href" />
                                        <button onClick={() => removeLink(ci, li)}><Trash2 size={12} /></button>
                                    </div>
                                ))}
                                <button className="fe-add-link" onClick={() => addLink(ci)}><Plus size={12} /> Add Link</button>
                            </div>
                        ))}
                    </div>

                    {error && <div className="fe-error">{error}</div>}
                </div>

                <div className="fe-footer">
                    <button className="fe-cancel" onClick={onClose}>Cancel</button>
                    <button className="fe-save" onClick={handleSave} disabled={saving}>
                        {saving ? <Loader size={14} className="spinning" /> : <Save size={14} />}
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FooterEditor;
