// src/components/SwapPreviewModal.jsx
// Side-by-side preview modal: Current section vs New variant

import React, { useRef, useEffect } from 'react';
import { X, Check, Loader, ArrowRight } from 'lucide-react';

const SwapPreviewModal = ({ isOpen, onClose, currentHtml, currentCss, previewHtml, previewCss, onConfirm, loading }) => {
    const currentRef = useRef(null);
    const previewRef = useRef(null);

    useEffect(() => {
        if (!isOpen) return;
        renderPreview(currentRef, currentHtml, currentCss);
        renderPreview(previewRef, previewHtml, previewCss);
    }, [isOpen, currentHtml, previewHtml, currentCss, previewCss]);

    const renderPreview = (ref, html, css) => {
        if (!ref.current || !html) return;
        const doc = ref.current.contentDocument;
        doc.open();
        doc.write(`<!DOCTYPE html><html><head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.tailwindcss.com"><\/script>
            <style>${css || ''}</style>
            <style>body{margin:0;overflow:hidden;font-family:system-ui,sans-serif;}</style>
        </head><body>${html}</body></html>`);
        doc.close();
    };

    if (!isOpen) return null;

    return (
        <div className="spm-overlay" onClick={onClose}>
            <div className="spm-modal" onClick={e => e.stopPropagation()}>
                <div className="spm-header">
                    <h3>Preview Changes</h3>
                    <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
                </div>
                <div className="spm-body">
                    <div className="spm-pane">
                        <div className="spm-pane-label">Current</div>
                        <iframe ref={currentRef} className="spm-iframe" title="Current section" />
                    </div>
                    <div className="spm-arrow"><ArrowRight size={24} /></div>
                    <div className="spm-pane">
                        <div className="spm-pane-label spm-pane-label-new">New</div>
                        <iframe ref={previewRef} className="spm-iframe" title="New section" />
                    </div>
                </div>
                <div className="spm-footer">
                    <button className="spm-cancel" onClick={onClose}>Cancel</button>
                    <button className="spm-confirm" onClick={onConfirm} disabled={loading}>
                        {loading ? <Loader size={14} className="spinning" /> : <Check size={14} />}
                        Apply Changes
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SwapPreviewModal;
