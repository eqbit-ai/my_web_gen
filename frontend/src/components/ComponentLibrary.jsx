// src/components/ComponentLibrary.jsx
// Browse, insert, and swap component variants
// Modes: "insert" (append), "swap" (replace section), "insert-at" (insert at position)

import React, { useState, useEffect } from 'react';
import { X, Search, ChevronRight, Plus, Loader, RefreshCw, AlertCircle } from 'lucide-react';
import { getComponents, generateComponent, swapComponent, previewSwap } from '../services/api';

const SECTION_TYPE_ICONS = {
    navbar: '🧭', hero: '🏠', features: '⭐', testimonials: '💬',
    pricing: '💰', cta: '📣', contact: '✉️', footer: '📋',
    faq: '❓', stats: '📊', gallery: '🖼️', team: '👥',
};

const ComponentLibrary = ({
    isOpen, onClose, sessionId,
    // Callbacks
    onInsert,           // for insert/insert-at modes
    onSwapPreview,      // for swap mode — triggers preview modal
    onSwapConfirm,      // for swap mode — applies the swap
    // Mode control
    mode = 'insert',    // 'insert' | 'swap' | 'insert-at'
    targetSectionId,    // for swap/insert-at: which section
    targetSectionType,  // for swap: filter to matching type
    insertPosition,     // for insert-at: 'before' | 'after'
    insertRefId,        // for insert-at: reference section id
    // Content form
    onContentFormOpen,  // opens content form before generation
}) => {
    const [components, setComponents] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedType, setExpandedType] = useState(null);
    const [generating, setGenerating] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        if (isOpen) {
            setError('');
            getComponents()
                .then(data => {
                    setComponents(data.components || []);
                    // Auto-expand matching type in swap mode
                    if (mode === 'swap' && targetSectionType) {
                        setExpandedType(targetSectionType);
                    }
                })
                .catch(err => setError('Failed to load components: ' + err.message));
        }
    }, [isOpen, mode, targetSectionType]);

    const filteredComponents = components.filter(comp => {
        // In swap mode, only show matching type
        if (mode === 'swap' && targetSectionType) {
            return comp.key === targetSectionType;
        }
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        return comp.name.toLowerCase().includes(q) ||
            comp.variants.some(v => v.name.toLowerCase().includes(q) || v.description.toLowerCase().includes(q));
    });

    const handleVariantClick = async (componentType, variantKey) => {
        setGenerating(variantKey);
        setError('');

        try {
            if (mode === 'swap') {
                // Generate preview first
                if (onSwapPreview) {
                    const preview = await previewSwap(sessionId, targetSectionId, componentType, variantKey);
                    onSwapPreview(preview, componentType, variantKey);
                } else {
                    // Direct swap without preview
                    const result = await swapComponent(sessionId, targetSectionId, componentType, variantKey);
                    if (result.success && onSwapConfirm) onSwapConfirm(result);
                }
            } else {
                // Insert mode — check if content form should open
                if (onContentFormOpen) {
                    onContentFormOpen(componentType, variantKey);
                } else {
                    const result = await generateComponent(sessionId, componentType, variantKey);
                    if (result.success && onInsert) onInsert(result, insertRefId, insertPosition);
                }
            }
        } catch (err) {
            setError('Failed: ' + err.message);
        }
        setGenerating(null);
    };

    if (!isOpen) return null;

    const title = mode === 'swap' ? 'Swap Variant' : mode === 'insert-at' ? 'Insert Section' : 'Component Library';

    return (
        <div className="cl-panel">
            <div className="cl-header">
                <h3>{title}</h3>
                <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
            </div>

            {mode === 'swap' && (
                <div className="cl-mode-banner cl-mode-swap">
                    <RefreshCw size={14} />
                    <span>Pick a new layout for this section. Your content will be preserved.</span>
                </div>
            )}

            {mode === 'insert-at' && (
                <div className="cl-mode-banner cl-mode-insert">
                    <Plus size={14} />
                    <span>Pick a component to insert {insertPosition} the selected section.</span>
                </div>
            )}

            {/* Error banner */}
            {error && (
                <div className="cl-error">
                    <AlertCircle size={14} />
                    <span>{error}</span>
                    <button onClick={() => setError('')}><X size={12} /></button>
                </div>
            )}

            {mode !== 'swap' && (
                <div className="cl-search">
                    <Search size={16} className="cl-search-icon" />
                    <input
                        type="text"
                        placeholder="Search components..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            )}

            <div className="cl-body">
                {filteredComponents.map(comp => (
                    <div key={comp.key} className="cl-group">
                        <button
                            className={`cl-group-header ${expandedType === comp.key ? 'expanded' : ''}`}
                            onClick={() => setExpandedType(expandedType === comp.key ? null : comp.key)}
                        >
                            <span className="cl-group-icon">{SECTION_TYPE_ICONS[comp.key] || '📦'}</span>
                            <span className="cl-group-name">{comp.name}</span>
                            <span className="cl-group-count">{comp.variants.length}</span>
                            <ChevronRight size={16} className="cl-group-chevron" />
                        </button>

                        {expandedType === comp.key && (
                            <div className="cl-variants">
                                {comp.variants.map(variant => (
                                    <div key={variant.key} className="cl-variant">
                                        <div className="cl-variant-info">
                                            <span className="cl-variant-name">{variant.name}</span>
                                            <span className="cl-variant-desc">{variant.description}</span>
                                        </div>
                                        <button
                                            className="cl-variant-add"
                                            onClick={() => handleVariantClick(comp.key, variant.key)}
                                            disabled={generating !== null}
                                            title={mode === 'swap' ? 'Swap to this variant' : 'Add to website'}
                                        >
                                            {generating === variant.key
                                                ? <Loader size={14} className="spinning" />
                                                : mode === 'swap' ? <RefreshCw size={14} /> : <Plus size={14} />
                                            }
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}

                {filteredComponents.length === 0 && (
                    <div className="cl-empty">No components match your search.</div>
                )}
            </div>
        </div>
    );
};

export default ComponentLibrary;
