// src/components/SectionEditor.jsx
// Section management — reorder, delete, duplicate, regenerate

import React, { useState } from 'react';
import {
    GripVertical, Trash2, Copy, ChevronUp, ChevronDown,
    Layers, X, Send, Sparkles
} from 'lucide-react';
import {
    reorderSections, deleteSection, duplicateSection, regenerateSection,
} from '../services/api';

const SectionEditor = ({ isOpen, onClose, sections, sessionId, onUpdate, pageSlug = 'index' }) => {
    const [localSections, setLocalSections] = useState(sections || []);
    const [regenPrompt, setRegenPrompt] = useState('');
    const [regenTarget, setRegenTarget] = useState(null);
    const [loading, setLoading] = useState(null);
    const [dragIndex, setDragIndex] = useState(null);
    const [error, setError] = useState('');

    React.useEffect(() => {
        setLocalSections(sections || []);
    }, [sections]);

    // Helper to find section label by id
    const getSectionLabel = (sectionId) => {
        const s = localSections.find(s => s.id === sectionId);
        return s ? `${s.type.toUpperCase()} "${s.label}"` : sectionId;
    };

    const handleMoveUp = async (index) => {
        if (index === 0) return;
        const section = localSections[index];
        const newOrder = [...localSections];
        [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
        setLocalSections(newOrder);
        setLoading('reorder');
        try {
            const result = await reorderSections(sessionId, newOrder.map(s => s.id), pageSlug);
            if (result.success) onUpdate(result.html, result.css, result.js, `Moved ${section.type.toUpperCase()} section up`);
        } catch (e) { setError(e.message); }
        setLoading(null);
    };

    const handleMoveDown = async (index) => {
        if (index >= localSections.length - 1) return;
        const section = localSections[index];
        const newOrder = [...localSections];
        [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
        setLocalSections(newOrder);
        setLoading('reorder');
        try {
            const result = await reorderSections(sessionId, newOrder.map(s => s.id), pageSlug);
            if (result.success) onUpdate(result.html, result.css, result.js, `Moved ${section.type.toUpperCase()} section down`);
        } catch (e) { setError(e.message); }
        setLoading(null);
    };

    const handleDelete = async (sectionId) => {
        if (!window.confirm('Delete this section?')) return;
        const label = getSectionLabel(sectionId);
        setLoading(sectionId);
        try {
            const result = await deleteSection(sessionId, sectionId, pageSlug);
            if (result.success) {
                setLocalSections(prev => prev.filter(s => s.id !== sectionId));
                onUpdate(result.html, result.css, result.js, `Deleted ${label}`);
            }
        } catch (e) { setError(e.message); }
        setLoading(null);
    };

    const handleDuplicate = async (sectionId) => {
        const label = getSectionLabel(sectionId);
        setLoading(sectionId);
        try {
            const result = await duplicateSection(sessionId, sectionId, pageSlug);
            if (result.success) onUpdate(result.html, result.css, result.js, `Duplicated ${label}`);
        } catch (e) { setError(e.message); }
        setLoading(null);
    };

    const handleRegenerate = async (sectionId) => {
        if (!regenPrompt.trim()) return;
        const label = getSectionLabel(sectionId);
        const prompt = regenPrompt;
        setLoading(sectionId);
        try {
            const result = await regenerateSection(sessionId, sectionId, prompt, null, pageSlug);
            if (result.success) {
                onUpdate(result.html, result.css, result.js, `Regenerated ${label}: "${prompt}"`);
                if (result.sections) setLocalSections(result.sections);
            }
        } catch (e) { setError(e.message); }
        setRegenPrompt('');
        setRegenTarget(null);
        setLoading(null);
    };

    // Drag and drop
    const handleDragStart = (index) => setDragIndex(index);
    const handleDragOver = (e, index) => {
        e.preventDefault();
        if (dragIndex === null || dragIndex === index) return;
        const newOrder = [...localSections];
        const [dragged] = newOrder.splice(dragIndex, 1);
        newOrder.splice(index, 0, dragged);
        setLocalSections(newOrder);
        setDragIndex(index);
    };
    const handleDragEnd = async () => {
        if (dragIndex === null) return;
        setDragIndex(null);
        setLoading('reorder');
        try {
            const result = await reorderSections(sessionId, localSections.map(s => s.id), pageSlug);
            if (result.success) onUpdate(result.html, result.css, result.js, 'Reordered sections');
        } catch (e) { setError(e.message); }
        setLoading(null);
    };

    if (!isOpen) return null;

    return (
        <div className="se-panel">
            <div className="se-header">
                <div className="se-header-title">
                    <Layers size={18} />
                    <span>Sections ({localSections.length})</span>
                </div>
                <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
            </div>

            {error && (
                <div className="se-error">
                    <span>{error}</span>
                    <button onClick={() => setError('')}><X size={12} /></button>
                </div>
            )}

            <div className="se-body">
                {localSections.map((section, index) => (
                    <div
                        key={section.id}
                        className={`se-card ${loading === section.id ? 'loading' : ''} ${dragIndex === index ? 'dragging' : ''}`}
                        draggable
                        onDragStart={() => handleDragStart(index)}
                        onDragOver={(e) => handleDragOver(e, index)}
                        onDragEnd={handleDragEnd}
                    >
                        <div className="se-card-header">
                            <GripVertical size={16} className="se-drag-handle" />
                            <div className="se-card-info">
                                <span className="se-card-type">{section.type}</span>
                                <span className="se-card-label">{section.label}</span>
                            </div>
                            <div className="se-card-actions">
                                <button onClick={() => handleMoveUp(index)} disabled={index === 0} title="Move up">
                                    <ChevronUp size={16} />
                                </button>
                                <button onClick={() => handleMoveDown(index)} disabled={index === localSections.length - 1} title="Move down">
                                    <ChevronDown size={16} />
                                </button>
                                <button onClick={() => handleDuplicate(section.id)} title="Duplicate">
                                    <Copy size={16} />
                                </button>
                                <button onClick={() => setRegenTarget(regenTarget === section.id ? null : section.id)} title="Regenerate with AI">
                                    <Sparkles size={16} />
                                </button>
                                <button onClick={() => handleDelete(section.id)} title="Delete" className="se-delete-btn">
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        {/* Regenerate prompt */}
                        {regenTarget === section.id && (
                            <div className="se-regen-input">
                                <input
                                    type="text"
                                    placeholder="Describe changes for this section..."
                                    value={regenPrompt}
                                    onChange={(e) => setRegenPrompt(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleRegenerate(section.id)}
                                    autoFocus
                                />
                                <button onClick={() => handleRegenerate(section.id)} disabled={!regenPrompt.trim()}>
                                    <Send size={16} />
                                </button>
                            </div>
                        )}

                        {loading === section.id && <div className="se-loading-bar" />}
                    </div>
                ))}

                {localSections.length === 0 && (
                    <div className="se-empty">No sections detected. Generate a website first.</div>
                )}
            </div>
        </div>
    );
};

export default SectionEditor;
