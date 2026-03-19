// src/components/ImageLibrary.jsx
// Image library panel — My Uploads + Stock Photo Search

import React, { useState, useEffect } from 'react';
import { X, Search, Upload, Trash2, Download, Loader, Image, Camera } from 'lucide-react';
import { listUploads, deleteUpload, uploadFile, searchImages, saveStockPhoto } from '../services/api';

const ImageLibrary = ({ isOpen, onClose, projectId, onSelect }) => {
    const [tab, setTab] = useState('uploads'); // uploads | stock
    const [uploads, setUploads] = useState([]);
    const [stockResults, setStockResults] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (isOpen && projectId) loadUploads();
    }, [isOpen, projectId]);

    const loadUploads = async () => {
        if (!projectId) return;
        setLoading(true);
        try {
            const data = await listUploads(projectId);
            setUploads(data.files || []);
        } catch (err) {
            setError('Failed to load images');
        }
        setLoading(false);
    };

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setUploading(true);
        setError('');
        try {
            const result = await uploadFile(file, projectId, 'image');
            setUploads(prev => [result, ...prev]);
        } catch (err) {
            setError('Upload failed: ' + err.message);
        }
        setUploading(false);
    };

    const handleDelete = async (mediaId) => {
        if (!window.confirm('Delete this image?')) return;
        try {
            await deleteUpload(mediaId);
            setUploads(prev => prev.filter(u => u.id !== mediaId));
        } catch (err) {
            setError('Delete failed');
        }
    };

    const handleStockSearch = async () => {
        if (!searchQuery.trim()) return;
        setLoading(true);
        setError('');
        try {
            const data = await searchImages(searchQuery, 20);
            setStockResults(data.images || []);
        } catch (err) {
            setError('Search failed');
        }
        setLoading(false);
    };

    const handleSaveStock = async (imageUrl) => {
        try {
            const result = await saveStockPhoto(imageUrl, projectId);
            setUploads(prev => [result, ...prev]);
        } catch (err) {
            setError('Failed to save to library');
        }
    };

    if (!isOpen) return null;

    return (
        <div className="il-overlay" onClick={onClose} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClose(e); }} role="button" tabIndex={0}>
            <div className="il-modal" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                <div className="il-header">
                    <h3><Image size={16} /> Image Library</h3>
                    <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
                </div>

                <div className="il-tabs">
                    <button className={`il-tab ${tab === 'uploads' ? 'active' : ''}`} onClick={() => setTab('uploads')}>
                        My Uploads
                    </button>
                    <button className={`il-tab ${tab === 'stock' ? 'active' : ''}`} onClick={() => setTab('stock')}>
                        <Camera size={14} /> Stock Photos
                    </button>
                </div>

                {error && <div className="il-error">{error}<button onClick={() => setError('')}><X size={12} /></button></div>}

                {tab === 'uploads' && (
                    <div className="il-body">
                        <label className="il-upload-area">
                            {uploading ? <Loader size={20} className="spinning" /> : <Upload size={20} />}
                            <span>{uploading ? 'Uploading...' : 'Click to upload image'}</span>
                            <input type="file" accept="image/*" onChange={handleUpload} hidden />
                        </label>
                        <div className="il-grid">
                            {uploads.map(img => (
                                <div key={img.id} className="il-item" onClick={() => onSelect(img.url)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(img.url); }} role="button" tabIndex={0}>
                                    <img src={img.url} alt={img.original_name || 'Upload'} />
                                    <div className="il-item-overlay">
                                        <button onClick={(e) => { e.stopPropagation(); handleDelete(img.id); }} title="Delete">
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {!loading && uploads.length === 0 && (
                            <div className="il-empty">No images uploaded yet. Upload or save from stock photos.</div>
                        )}
                    </div>
                )}

                {tab === 'stock' && (
                    <div className="il-body">
                        <div className="il-search">
                            <input
                                type="text"
                                placeholder="Search stock photos..."
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleStockSearch()}
                            />
                            <button onClick={handleStockSearch} disabled={loading}>
                                {loading ? <Loader size={14} className="spinning" /> : <Search size={14} />}
                            </button>
                        </div>
                        <div className="il-grid">
                            {stockResults.map(img => (
                                <div key={img.id} className="il-item" onClick={() => onSelect(img.url)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(img.url); }} role="button" tabIndex={0}>
                                    <img src={img.thumb || img.url} alt={img.alt || 'Stock photo'} />
                                    <div className="il-item-overlay">
                                        <span className="il-photographer">{img.photographer}</span>
                                        <button onClick={(e) => { e.stopPropagation(); handleSaveStock(img.url); }} title="Save to library">
                                            <Download size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {!loading && stockResults.length === 0 && searchQuery && (
                            <div className="il-empty">No results. Try a different search.</div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ImageLibrary;
