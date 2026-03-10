// src/components/ContentForm.jsx
// Dynamic form to input text, images, and video for a section before generation

import React, { useState } from 'react';
import { X, Upload, Image, Video, Type, Loader } from 'lucide-react';
import { uploadFile } from '../services/api';

const ContentForm = ({ isOpen, onClose, sectionType, onSubmit, projectId }) => {
    const [fields, setFields] = useState({
        heading: '',
        subheading: '',
        description: '',
        buttonText: '',
        buttonUrl: '#',
        imageUrl: '',
        videoUrl: '',
    });
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (key, value) => {
        setFields(prev => ({ ...prev, [key]: value }));
    };

    const handleImageUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setUploading(true);
        setError('');
        try {
            const result = await uploadFile(file, projectId, 'image');
            handleChange('imageUrl', result.url);
        } catch (err) {
            setError('Failed to upload image: ' + err.message);
        }
        setUploading(false);
    };

    const handleVideoUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setUploading(true);
        setError('');
        try {
            const result = await uploadFile(file, projectId, 'video');
            handleChange('videoUrl', result.url);
        } catch (err) {
            setError('Failed to upload video: ' + err.message);
        }
        setUploading(false);
    };

    const handleSubmit = () => {
        // Filter out empty fields
        const content = {};
        Object.entries(fields).forEach(([k, v]) => {
            if (v && v.trim()) content[k] = v.trim();
        });
        onSubmit(content);
    };

    // Show relevant fields based on section type
    const showVideo = ['hero'].includes(sectionType);
    const showButton = ['hero', 'cta'].includes(sectionType);
    const showImage = !['navbar', 'footer', 'faq', 'stats'].includes(sectionType);

    if (!isOpen) return null;

    return (
        <div className="cf-overlay" onClick={onClose}>
            <div className="cf-modal" onClick={e => e.stopPropagation()}>
                <div className="cf-header">
                    <h3><Type size={16} /> Section Content</h3>
                    <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
                </div>

                <div className="cf-body">
                    <p className="cf-hint">Fill in your content or leave blank for AI-generated text.</p>

                    {error && <div className="cf-error">{error}</div>}

                    <div className="cf-field">
                        <label>Heading</label>
                        <input type="text" value={fields.heading} onChange={e => handleChange('heading', e.target.value)} placeholder="Main heading..." />
                    </div>

                    <div className="cf-field">
                        <label>Subheading</label>
                        <input type="text" value={fields.subheading} onChange={e => handleChange('subheading', e.target.value)} placeholder="Subtitle or tagline..." />
                    </div>

                    <div className="cf-field">
                        <label>Description</label>
                        <textarea value={fields.description} onChange={e => handleChange('description', e.target.value)} placeholder="Detailed description..." rows={3} />
                    </div>

                    {showButton && (
                        <div className="cf-row">
                            <div className="cf-field cf-half">
                                <label>Button Text</label>
                                <input type="text" value={fields.buttonText} onChange={e => handleChange('buttonText', e.target.value)} placeholder="Get Started" />
                            </div>
                            <div className="cf-field cf-half">
                                <label>Button URL</label>
                                <input type="text" value={fields.buttonUrl} onChange={e => handleChange('buttonUrl', e.target.value)} placeholder="#contact" />
                            </div>
                        </div>
                    )}

                    {showImage && (
                        <div className="cf-field">
                            <label><Image size={14} /> Image</label>
                            <div className="cf-upload-row">
                                <input type="text" value={fields.imageUrl} onChange={e => handleChange('imageUrl', e.target.value)} placeholder="Image URL or upload..." />
                                <label className="cf-upload-btn">
                                    {uploading ? <Loader size={14} className="spinning" /> : <Upload size={14} />}
                                    <input type="file" accept="image/*" onChange={handleImageUpload} hidden />
                                </label>
                            </div>
                            {fields.imageUrl && <img src={fields.imageUrl} alt="Preview" className="cf-img-preview" />}
                        </div>
                    )}

                    {showVideo && (
                        <div className="cf-field">
                            <label><Video size={14} /> Video</label>
                            <div className="cf-upload-row">
                                <input type="text" value={fields.videoUrl} onChange={e => handleChange('videoUrl', e.target.value)} placeholder="Video URL or upload..." />
                                <label className="cf-upload-btn">
                                    {uploading ? <Loader size={14} className="spinning" /> : <Upload size={14} />}
                                    <input type="file" accept="video/*" onChange={handleVideoUpload} hidden />
                                </label>
                            </div>
                        </div>
                    )}
                </div>

                <div className="cf-footer">
                    <button className="cf-skip" onClick={() => onSubmit(null)}>Skip (use AI content)</button>
                    <button className="cf-submit" onClick={handleSubmit}>Use My Content</button>
                </div>
            </div>
        </div>
    );
};

export default ContentForm;
