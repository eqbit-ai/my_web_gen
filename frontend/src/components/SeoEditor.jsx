// src/components/SeoEditor.jsx
// Page title, meta description, favicon, WhatsApp, contact form config

import React, { useState } from 'react';
import { X, Save, Loader, Globe, Phone, Mail, FileText, Upload } from 'lucide-react';
import { updateSiteMeta, updateContactConfig, uploadFile } from '../services/api';

const SeoEditor = ({ isOpen, onClose, sessionId, projectId, siteMeta: initialMeta, contactConfig: initialContact, onUpdate }) => {
    const [meta, setMeta] = useState(initialMeta || {
        title: '',
        description: '',
        keywords: '',
    });
    const [faviconUrl, setFaviconUrl] = useState(initialMeta?.faviconUrl || '');
    const [whatsapp, setWhatsapp] = useState(initialMeta?.whatsappNumber || '');
    const [contact, setContact] = useState(initialContact || {
        recipientEmail: '',
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [tab, setTab] = useState('seo'); // seo | contact | whatsapp

    const handleFaviconUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        try {
            const result = await uploadFile(file, projectId, 'favicon');
            setFaviconUrl(result.url);
        } catch (err) {
            setError('Failed to upload favicon');
        }
    };

    const handleSaveMeta = async () => {
        setSaving(true);
        setError('');
        setSuccess('');
        try {
            const result = await updateSiteMeta(sessionId, {
                title: meta.title,
                description: meta.description,
                keywords: meta.keywords,
                faviconUrl,
                whatsappNumber: whatsapp,
            });
            if (result.success && onUpdate) {
                onUpdate(result.html, result.css, result.js);
                setSaving(false);
                onClose();
                return;
            }
        } catch (err) {
            setError('Failed to save: ' + err.message);
        }
        setSaving(false);
    };

    const handleSaveContact = async () => {
        setSaving(true);
        setError('');
        setSuccess('');
        try {
            const result = await updateContactConfig(sessionId, contact);
            if (result.success && onUpdate) {
                onUpdate(result.html, result.css, result.js);
                setSaving(false);
                onClose();
                return;
            }
        } catch (err) {
            setError('Failed to save: ' + err.message);
        }
        setSaving(false);
    };

    if (!isOpen) return null;

    return (
        <div className="seo-overlay" onClick={onClose} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClose(e); }} role="button" tabIndex={0}>
            <div className="seo-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                <div className="seo-header">
                    <h3><Globe size={16} /> Site Settings</h3>
                    <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
                </div>

                <div className="seo-tabs">
                    <button className={tab === 'seo' ? 'active' : ''} onClick={() => setTab('seo')}>
                        <FileText size={14} /> SEO & Meta
                    </button>
                    <button className={tab === 'contact' ? 'active' : ''} onClick={() => setTab('contact')}>
                        <Mail size={14} /> Contact Form
                    </button>
                    <button className={tab === 'whatsapp' ? 'active' : ''} onClick={() => setTab('whatsapp')}>
                        <Phone size={14} /> WhatsApp
                    </button>
                </div>

                <div className="seo-body">
                    {error && <div className="seo-error">{error}</div>}
                    {success && <div className="seo-success">{success}</div>}

                    {tab === 'seo' && (
                        <>
                            <div className="seo-field">
                                <label>Page Title</label>
                                <input type="text" value={meta.title} onChange={e => setMeta(m => ({ ...m, title: e.target.value }))} placeholder="My Business — Premium Services" />
                            </div>
                            <div className="seo-field">
                                <label>Meta Description</label>
                                <textarea value={meta.description} onChange={e => setMeta(m => ({ ...m, description: e.target.value }))} placeholder="A brief description for search engines..." rows={3} />
                                <span className="seo-char-count">{(meta.description || '').length}/160</span>
                            </div>
                            <div className="seo-field">
                                <label>Keywords</label>
                                <input type="text" value={meta.keywords} onChange={e => setMeta(m => ({ ...m, keywords: e.target.value }))} placeholder="business, services, Dubai..." />
                            </div>
                            <div className="seo-field">
                                <label>Favicon</label>
                                <div className="seo-favicon-row">
                                    {faviconUrl && <img src={faviconUrl} alt="Favicon" className="seo-favicon-preview" />}
                                    <label className="seo-upload-btn">
                                        <Upload size={14} /> {faviconUrl ? 'Change' : 'Upload'}
                                        <input type="file" accept="image/png,image/x-icon,image/ico,image/svg+xml" onChange={handleFaviconUpload} hidden />
                                    </label>
                                </div>
                            </div>
                            <div className="seo-footer">
                                <button className="seo-save" onClick={handleSaveMeta} disabled={saving}>
                                    {saving ? <Loader size={14} className="spinning" /> : <Save size={14} />} Save
                                </button>
                            </div>
                        </>
                    )}

                    {tab === 'contact' && (
                        <>
                            <div className="seo-field">
                                <label>Recipient Email</label>
                                <input type="email" value={contact.recipientEmail} onChange={e => setContact(c => ({ ...c, recipientEmail: e.target.value }))} placeholder="you@example.com" />
                                <span className="seo-hint">Contact form submissions will be sent to this email address.</span>
                            </div>
                            <div className="seo-footer">
                                <button className="seo-save" onClick={handleSaveContact} disabled={saving}>
                                    {saving ? <Loader size={14} className="spinning" /> : <Save size={14} />} Save
                                </button>
                            </div>
                        </>
                    )}

                    {tab === 'whatsapp' && (
                        <>
                            <div className="seo-field">
                                <label>WhatsApp Number</label>
                                <input type="text" value={whatsapp} onChange={e => setWhatsapp(e.target.value)} placeholder="+971501234567" />
                                <span className="seo-hint">Include country code. This number will appear on the floating WhatsApp button.</span>
                            </div>
                            <div className="seo-footer">
                                <button className="seo-save" onClick={handleSaveMeta} disabled={saving}>
                                    {saving ? <Loader size={14} className="spinning" /> : <Save size={14} />} Save
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SeoEditor;
