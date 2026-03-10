// src/components/NavEditor.jsx
// Edit navigation links, toggle sticky, manage logo in navbar

import React, { useState } from 'react';
import { X, Plus, Trash2, GripVertical, Save, Loader, Link, Pin, ChevronUp, ChevronDown } from 'lucide-react';
import { updateNavConfig } from '../services/api';
import LogoUploader from './LogoUploader';

const NavEditor = ({ isOpen, onClose, sessionId, projectId, navItems: initialItems, sticky: initialSticky, logoUrl, onUpdate, onLogoChange }) => {
    const [items, setItems] = useState(initialItems || [
        { label: 'Home', href: '#home', isButton: false },
        { label: 'About', href: '#about', isButton: false },
        { label: 'Services', href: '#services', isButton: false },
        { label: 'Contact', href: '#contact', isButton: true },
    ]);
    const [sticky, setSticky] = useState(initialSticky || false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [dragIndex, setDragIndex] = useState(null);

    const addItem = () => {
        setItems(prev => [...prev, { label: '', href: '#', isButton: false }]);
    };

    const removeItem = (index) => {
        setItems(prev => prev.filter((_, i) => i !== index));
    };

    const updateItem = (index, field, value) => {
        setItems(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item));
    };

    const moveItem = (from, to) => {
        if (to < 0 || to >= items.length) return;
        const newItems = [...items];
        const [moved] = newItems.splice(from, 1);
        newItems.splice(to, 0, moved);
        setItems(newItems);
    };

    const handleDragStart = (index) => setDragIndex(index);
    const handleDragOver = (e, index) => {
        e.preventDefault();
        if (dragIndex === null || dragIndex === index) return;
        moveItem(dragIndex, index);
        setDragIndex(index);
    };
    const handleDragEnd = () => setDragIndex(null);

    const handleSave = async () => {
        setSaving(true);
        setError('');
        try {
            const result = await updateNavConfig(sessionId, items, sticky);
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
        <div className="ne-overlay" onClick={onClose}>
            <div className="ne-modal" onClick={e => e.stopPropagation()}>
                <div className="ne-header">
                    <h3><Link size={16} /> Navigation Editor</h3>
                    <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
                </div>

                <div className="ne-body">
                    <LogoUploader logoUrl={logoUrl} onLogoChange={onLogoChange} projectId={projectId} />

                    <div className="ne-sticky">
                        <label className="ne-toggle-label">
                            <Pin size={14} />
                            <span>Sticky Navbar</span>
                            <input type="checkbox" checked={sticky} onChange={e => setSticky(e.target.checked)} />
                            <span className="ne-toggle-switch" />
                        </label>
                    </div>

                    <div className="ne-items-header">
                        <span>Menu Items</span>
                        <button className="ne-add-btn" onClick={addItem}><Plus size={14} /> Add</button>
                    </div>

                    <div className="ne-items">
                        {items.map((item, index) => (
                            <div
                                key={index}
                                className={`ne-item ${dragIndex === index ? 'dragging' : ''}`}
                                draggable
                                onDragStart={() => handleDragStart(index)}
                                onDragOver={(e) => handleDragOver(e, index)}
                                onDragEnd={handleDragEnd}
                            >
                                <GripVertical size={14} className="ne-item-grip" style={{ cursor: 'grab' }} />
                                <input
                                    type="text"
                                    value={item.label}
                                    onChange={e => updateItem(index, 'label', e.target.value)}
                                    placeholder="Label"
                                    className="ne-item-label"
                                />
                                <input
                                    type="text"
                                    value={item.href}
                                    onChange={e => updateItem(index, 'href', e.target.value)}
                                    placeholder="#section"
                                    className="ne-item-href"
                                />
                                <label className="ne-item-btn-toggle" title="Show as button">
                                    <input type="checkbox" checked={item.isButton} onChange={e => updateItem(index, 'isButton', e.target.checked)} />
                                    <span>Btn</span>
                                </label>
                                <button className="ne-item-move" onClick={() => moveItem(index, index - 1)} disabled={index === 0} title="Move up">
                                    <ChevronUp size={14} />
                                </button>
                                <button className="ne-item-move" onClick={() => moveItem(index, index + 1)} disabled={index === items.length - 1} title="Move down">
                                    <ChevronDown size={14} />
                                </button>
                                <button className="ne-item-delete" onClick={() => removeItem(index)}>
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        ))}
                    </div>

                    {error && <div className="ne-error">{error}</div>}
                </div>

                <div className="ne-footer">
                    <button className="ne-cancel" onClick={onClose}>Cancel</button>
                    <button className="ne-save" onClick={handleSave} disabled={saving}>
                        {saving ? <Loader size={14} className="spinning" /> : <Save size={14} />}
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
};

export default NavEditor;
