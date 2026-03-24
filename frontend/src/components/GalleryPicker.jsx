import React, { useState, useEffect } from 'react';
import { X, Image as ImageIcon, Upload, Copy, Check } from 'lucide-react';
import { listAllUploads } from '../services/api';

const GalleryPicker = ({ isOpen, onClose, onSelectImage }) => {
    const [images, setImages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState('all');
    const [copied, setCopied] = useState(null);

    useEffect(() => {
        if (!isOpen) return;
        setLoading(true);
        listAllUploads()
            .then(data => setImages(data.files || []))
            .catch(() => setImages([]))
            .finally(() => setLoading(false));
    }, [isOpen]);

    if (!isOpen) return null;

    const filtered = filter === 'all'
        ? images
        : images.filter(img => img.category === filter);

    const handleCopyUrl = (e, url) => {
        e.stopPropagation();
        const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
        navigator.clipboard.writeText(fullUrl);
        setCopied(url);
        setTimeout(() => setCopied(null), 2000);
    };

    const formatSize = (bytes) => {
        if (!bytes) return '';
        if (bytes < 1024) return `${bytes}B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
    };

    return (
        <div className="gp-panel">
            <div className="gp-header">
                <div className="gp-header-title">
                    <ImageIcon size={16} />
                    <span>My Images</span>
                    <span className="gp-count">{filtered.length}</span>
                </div>
                <button className="gp-close" onClick={onClose}><X size={16} /></button>
            </div>

            <div className="gp-filters">
                {['all', 'image', 'logo', 'favicon'].map(cat => (
                    <button
                        key={cat}
                        className={`gp-filter-btn ${filter === cat ? 'active' : ''}`}
                        onClick={() => setFilter(cat)}
                    >
                        {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1) + 's'}
                    </button>
                ))}
            </div>

            <div className="gp-body">
                {loading ? (
                    <div className="gp-empty">Loading images...</div>
                ) : filtered.length === 0 ? (
                    <div className="gp-empty">
                        <Upload size={32} style={{ opacity: 0.4, marginBottom: 8 }} />
                        <p>No images uploaded yet</p>
                        <p style={{ fontSize: '0.75rem', marginTop: 4 }}>Upload images from the Dashboard Gallery tab</p>
                    </div>
                ) : (
                    filtered.map(img => (
                        <div
                            key={img.id}
                            className="gp-thumb"
                            onClick={() => onSelectImage(img.url, img.original_name)}
                            title={`Click to use "${img.original_name}" in your website`}
                        >
                            <img src={img.url.startsWith('http') ? img.url : `${window.location.origin}${img.url}`} alt={img.original_name} loading="lazy" />
                            <div className="gp-thumb-info">
                                <span className="gp-thumb-name">{img.original_name}</span>
                                <div className="gp-thumb-meta">
                                    {img.width && img.height && <span>{img.width}x{img.height}</span>}
                                    <span>{formatSize(img.size_bytes)}</span>
                                    <button
                                        className="gp-copy-btn"
                                        onClick={(e) => handleCopyUrl(e, img.url)}
                                        title="Copy URL"
                                    >
                                        {copied === img.url ? <Check size={12} /> : <Copy size={12} />}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            <div className="gp-footer">
                Click an image to insert it into your website via chat prompt
            </div>
        </div>
    );
};

export default GalleryPicker;
