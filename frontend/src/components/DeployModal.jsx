import config from '../config';
import React, { useState } from 'react';
import { X, Rocket, Check, Loader2, ExternalLink, Copy, AlertCircle, RefreshCw } from 'lucide-react';

const DeployModal = ({ isOpen, onClose, sessionId, html, css, js }) => {
    const [isDeploying, setIsDeploying] = useState(false);
    const [deployed, setDeployed] = useState(null);
    const [siteName, setSiteName] = useState('');
    const [error, setError] = useState(null);
    const [copied, setCopied] = useState(false);

    if (!isOpen) return null;

    const handleDeploy = async () => {
        if (!sessionId) {
            setError('No active session. Please generate a website first.');
            return;
        }

        setIsDeploying(true);
        setError(null);

        try {
            const token = localStorage.getItem('token');
            const resp = await fetch(`${config.apiUrl}/api/deploy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    site_name: siteName.trim() || '',
                }),
            });

            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.detail || 'Deployment failed');
            }

            setDeployed(data);
        } catch (err) {
            setError(err.message || 'Deployment failed. Please try again.');
        } finally {
            setIsDeploying(false);
        }
    };

    const handleCopyUrl = () => {
        if (deployed?.url) {
            navigator.clipboard.writeText(deployed.url);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleClose = () => {
        setDeployed(null);
        setSiteName('');
        setError(null);
        onClose();
    };

    return (
        <div className="modal-overlay" onClick={handleClose}>
            <div className="modal-content deploy-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={handleClose}>
                    <X size={20} />
                </button>

                {!deployed ? (
                    <>
                        <div className="modal-header">
                            <Rocket className="modal-icon" size={32} />
                            <h2>Deploy Your Website</h2>
                            <p>Make your website live on the internet in seconds</p>
                        </div>

                        <div className="modal-body">
                            <div className="input-group">
                                <label>Site Name</label>
                                <input
                                    type="text"
                                    value={siteName}
                                    onChange={(e) => setSiteName(e.target.value)}
                                    placeholder="my-awesome-website"
                                    className="modal-input"
                                    disabled={isDeploying}
                                />
                                <span className="input-hint">
                                    Your site will be deployed to AWS S3
                                </span>
                            </div>

                            <div className="deploy-info">
                                <div className="deploy-info-item">
                                    <Check size={14} />
                                    <span>Hosted on AWS S3</span>
                                </div>
                                <div className="deploy-info-item">
                                    <Check size={14} />
                                    <span>Fast and reliable static hosting</span>
                                </div>
                                <div className="deploy-info-item">
                                    <Check size={14} />
                                    <span>Instant deployment</span>
                                </div>
                            </div>

                            {error && (
                                <div className="modal-error">
                                    <AlertCircle size={16} />
                                    {error}
                                </div>
                            )}

                            <button
                                className="deploy-button"
                                onClick={handleDeploy}
                                disabled={isDeploying}
                            >
                                {isDeploying ? (
                                    <>
                                        <Loader2 className="spinning" size={20} />
                                        Deploying to AWS...
                                    </>
                                ) : (
                                    <>
                                        <Rocket size={20} />
                                        Deploy Now
                                    </>
                                )}
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="modal-header success">
                            <Check className="modal-icon success" size={32} />
                            <h2>Website is Live!</h2>
                            <p>Your website has been deployed successfully</p>
                        </div>

                        <div className="modal-body">
                            <div className="deployed-url-box">
                                <a href={deployed.url} target="_blank" rel="noopener noreferrer">
                                    {deployed.url}
                                    <ExternalLink size={16} />
                                </a>
                                <button className="copy-button" onClick={handleCopyUrl} title="Copy URL">
                                    {copied ? <Check size={16} /> : <Copy size={16} />}
                                </button>
                            </div>

                            {deployed.is_multipage && (
                                <div className="deploy-meta">
                                    {deployed.page_count} pages deployed
                                </div>
                            )}

                            <div className="deploy-actions">
                                <a
                                    href={deployed.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="deploy-button visit"
                                >
                                    <ExternalLink size={18} />
                                    Visit Website
                                </a>
                                <button className="deploy-button secondary" onClick={handleClose}>
                                    Done
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default DeployModal;
