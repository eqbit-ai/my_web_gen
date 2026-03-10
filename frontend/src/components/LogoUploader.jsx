// src/components/LogoUploader.jsx
// Upload and manage logo for navbar/footer

import React, { useState } from 'react';
import { Upload, X, Loader, Image } from 'lucide-react';
import { uploadFile } from '../services/api';

const LogoUploader = ({ logoUrl, onLogoChange, projectId }) => {
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type
        const validTypes = ['image/png', 'image/jpeg', 'image/svg+xml', 'image/webp', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            setError('Please upload PNG, JPG, SVG, or WebP');
            return;
        }

        // Validate file size (2MB for logos)
        if (file.size > 2 * 1024 * 1024) {
            setError('Logo must be under 2MB');
            return;
        }

        setUploading(true);
        setError('');
        try {
            const result = await uploadFile(file, projectId, 'logo');
            onLogoChange(result.url);
        } catch (err) {
            setError('Upload failed: ' + err.message);
        }
        setUploading(false);
    };

    const handleRemove = () => {
        onLogoChange('');
    };

    return (
        <div className="lu-container">
            <label className="lu-label"><Image size={14} /> Logo</label>
            {logoUrl ? (
                <div className="lu-preview">
                    <img src={logoUrl} alt="Logo" className="lu-img" />
                    <button className="lu-remove" onClick={handleRemove} title="Remove logo"><X size={12} /></button>
                </div>
            ) : (
                <label className="lu-upload-area">
                    {uploading ? <Loader size={16} className="spinning" /> : <Upload size={16} />}
                    <span>{uploading ? 'Uploading...' : 'Upload logo'}</span>
                    <input type="file" accept="image/png,image/jpeg,image/svg+xml,image/webp" onChange={handleUpload} hidden />
                </label>
            )}
            {error && <div className="lu-error">{error}</div>}
        </div>
    );
};

export default LogoUploader;
