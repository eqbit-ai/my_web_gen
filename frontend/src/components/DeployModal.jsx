import config from '../config';
import React, { useState, useEffect, useRef } from 'react';
import { X, Rocket, Check, Loader2, ExternalLink, Copy, AlertCircle, Globe, Search, ShoppingCart, Zap, Shield, ArrowRight, Sparkles, CheckCircle2, Clock, ChevronDown } from 'lucide-react';
import { searchDomains, purchaseDomain } from '../services/api';

const DeployModal = ({ isOpen, onClose, sessionId, html, css, js, existingSiteId, onDeployed }) => {
    const [isDeploying, setIsDeploying] = useState(false);
    const [deployed, setDeployed] = useState(null);
    const [siteName, setSiteName] = useState('');
    const [error, setError] = useState(null);
    const [copied, setCopied] = useState(false);

    // Domain flow state
    const [activeTab, setActiveTab] = useState('success'); // 'success' | 'domain'
    const [domainQuery, setDomainQuery] = useState('');
    const [domainResults, setDomainResults] = useState(null);
    const [searchingDomain, setSearchingDomain] = useState(false);
    const [purchasingDomain, setPurchasingDomain] = useState(null);
    const [domainPurchased, setDomainPurchased] = useState(null);
    const [domainError, setDomainError] = useState(null);
    const [selectedTlds, setSelectedTlds] = useState(['com', 'ae', 'net', 'io', 'org', 'co']);
    const [showTldPicker, setShowTldPicker] = useState(false);
    const [ownedDomains, setOwnedDomains] = useState([]);
    const [connectingDomain, setConnectingDomain] = useState(null);
    const searchInputRef = useRef(null);

    const allTlds = ['com', 'ae', 'net', 'io', 'org', 'co', 'dev', 'app', 'me', 'info', 'biz', 'xyz'];

    useEffect(() => {
        if (deployed && activeTab === 'domain' && searchInputRef.current) {
            searchInputRef.current.focus();
        }
    }, [activeTab, deployed]);

    // Fetch user's available (unconnected) domains when domain tab is shown
    useEffect(() => {
        if (deployed?.site_id && activeTab === 'domain') {
            const token = localStorage.getItem('token');
            fetch(`${config.apiUrl}/api/deploy/${deployed.site_id}/available-domains`, {
                headers: { 'Authorization': `Bearer ${token}` },
            })
                .then(r => r.json())
                .then(data => setOwnedDomains(data.available_domains || []))
                .catch(() => setOwnedDomains([]));
        }
    }, [deployed?.site_id, activeTab]);

    const handleConnectOwnedDomain = async (domainName) => {
        setConnectingDomain(domainName);
        setDomainError(null);
        try {
            const token = localStorage.getItem('token');
            const resp = await fetch(`${config.apiUrl}/api/deploy/${deployed.site_id}/connect-domain`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ domain_name: domainName }),
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || 'Failed to connect domain');
            setDomainPurchased({ domain: domainName, ...data });
        } catch (err) {
            setDomainError(err.message);
        } finally {
            setConnectingDomain(null);
        }
    };

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
                    site_id: existingSiteId || undefined,
                }),
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || 'Deployment failed');
            setDeployed(data);
            // Notify parent of site_id so future deploys overwrite the same S3 folder
            if (onDeployed && data.site_id) onDeployed(data.site_id);
            // Pre-fill domain search with site name
            const cleanName = siteName.trim().replace(/[^a-z0-9]/gi, '').toLowerCase();
            if (cleanName) setDomainQuery(cleanName);
        } catch (err) {
            setError(err.message || 'Deployment failed. Please try again.');
        } finally {
            setIsDeploying(false);
        }
    };

    const handleCopyUrl = (url) => {
        if (url) {
            navigator.clipboard.writeText(url);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleClose = () => {
        setDeployed(null);
        setSiteName('');
        setError(null);
        setActiveTab('success');
        setDomainResults(null);
        setDomainPurchased(null);
        setDomainError(null);
        setDomainQuery('');
        setShowTldPicker(false);
        onClose();
    };

    const handleDomainSearch = async (e) => {
        e.preventDefault();
        if (!domainQuery.trim()) return;
        setSearchingDomain(true);
        setDomainError(null);
        setDomainResults(null);
        try {
            const data = await searchDomains(domainQuery.trim(), selectedTlds);
            setDomainResults(data.results || []);
        } catch (err) {
            setDomainError(err.message);
        } finally {
            setSearchingDomain(false);
        }
    };

    const handleDomainPurchase = async (sld, tld) => {
        setPurchasingDomain(`${sld}.${tld}`);
        setDomainError(null);
        try {
            const data = await purchaseDomain(sld, tld, deployed?.site_id, 1);
            setDomainPurchased(data);
        } catch (err) {
            setDomainError(err.message);
        } finally {
            setPurchasingDomain(null);
        }
    };

    const toggleTld = (tld) => {
        setSelectedTlds(prev =>
            prev.includes(tld) ? prev.filter(t => t !== tld) : [...prev, tld]
        );
    };

    const availableDomains = domainResults?.filter(r => r.status === 'free') || [];
    const takenDomains = domainResults?.filter(r => r.status !== 'free') || [];
    const cheapest = availableDomains.length > 0
        ? availableDomains.reduce((a, b) => (a.price?.amount || Infinity) < (b.price?.amount || Infinity) ? a : b)
        : null;

    // ── Render: Deploy Form ──
    if (!deployed) {
        return (
            <div className="dm-overlay" onClick={handleClose}>
                <div className="dm-container dm-deploy-form" onClick={e => e.stopPropagation()}>
                    <button className="dm-close" onClick={handleClose}><X size={18} /></button>
                    <div className="dm-header">
                        <div className="dm-icon-wrap"><Rocket size={24} /></div>
                        <h2>Deploy Website</h2>
                        <p>Go live on the internet in seconds</p>
                    </div>
                    <div className="dm-body">
                        <div className="dm-field">
                            <label>Site Name</label>
                            <input
                                type="text" value={siteName}
                                onChange={(e) => setSiteName(e.target.value)}
                                placeholder="my-awesome-website"
                                disabled={isDeploying}
                            />
                            <span className="dm-hint">Deployed to AWS S3 with global CDN</span>
                        </div>
                        <div className="dm-features">
                            <div className="dm-feature"><Shield size={14} /><span>SSL encrypted</span></div>
                            <div className="dm-feature"><Zap size={14} /><span>Global CDN</span></div>
                            <div className="dm-feature"><Check size={14} /><span>Instant deploy</span></div>
                        </div>
                        {error && <div className="dm-error"><AlertCircle size={15} />{error}</div>}
                        <button className="dm-btn dm-btn-primary dm-btn-deploy" onClick={handleDeploy} disabled={isDeploying}>
                            {isDeploying ? (<><Loader2 className="spinning" size={18} />Deploying...</>)
                                : (<><Rocket size={18} />Deploy Now</>)}
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // ── Render: Domain Purchase/Connect Success ──
    if (domainPurchased) {
        // Determine real status from backend response
        const ds = domainPurchased.domain_status || 'pending_validation';
        const reused = domainPurchased.reused_infrastructure;
        const sslDone = ds === 'pending_deployment' || ds === 'active';
        const cdnDone = ds === 'active';
        const cdnDeploying = ds === 'pending_deployment';

        return (
            <div className="dm-overlay" onClick={handleClose}>
                <div className="dm-container dm-wide" onClick={e => e.stopPropagation()}>
                    <button className="dm-close" onClick={handleClose}><X size={18} /></button>
                    <div className="dm-header dm-header-success">
                        <div className="dm-icon-wrap dm-icon-success"><CheckCircle2 size={24} /></div>
                        <h2>Domain Connected!</h2>
                        <p className="dm-domain-highlight">{domainPurchased.domain}</p>
                    </div>
                    <div className="dm-body">
                        <div className="dm-progress-pipeline">
                            <div className="dm-pipeline-step dm-step-done">
                                <div className="dm-step-icon"><Check size={14} /></div>
                                <div className="dm-step-info">
                                    <span className="dm-step-label">{reused ? 'Domain Linked' : 'Domain Registered'}</span>
                                    <span className="dm-step-detail">{reused ? 'Reconnected to site' : 'via OpenProvider'}</span>
                                </div>
                            </div>
                            <div className="dm-pipeline-connector dm-connector-done" />
                            <div className="dm-pipeline-step dm-step-done">
                                <div className="dm-step-icon"><Check size={14} /></div>
                                <div className="dm-step-info">
                                    <span className="dm-step-label">DNS Configured</span>
                                    <span className="dm-step-detail">Route53 zone + nameservers</span>
                                </div>
                            </div>
                            <div className={`dm-pipeline-connector ${sslDone ? 'dm-connector-done' : 'dm-connector-active'}`} />
                            <div className={`dm-pipeline-step ${sslDone ? 'dm-step-done' : 'dm-step-active'}`}>
                                <div className="dm-step-icon">
                                    {sslDone ? <Check size={14} /> : <Loader2 className="spinning" size={14} />}
                                </div>
                                <div className="dm-step-info">
                                    <span className="dm-step-label">SSL Certificate</span>
                                    <span className="dm-step-detail">{sslDone ? 'Issued' : 'Validating (5-15 min)'}</span>
                                </div>
                            </div>
                            <div className={`dm-pipeline-connector ${cdnDone ? 'dm-connector-done' : sslDone ? 'dm-connector-active' : ''}`} />
                            <div className={`dm-pipeline-step ${cdnDone ? 'dm-step-done' : cdnDeploying ? 'dm-step-active' : 'dm-step-pending'}`}>
                                <div className="dm-step-icon">
                                    {cdnDone ? <Check size={14} /> : cdnDeploying ? <Loader2 className="spinning" size={14} /> : <Zap size={14} />}
                                </div>
                                <div className="dm-step-info">
                                    <span className="dm-step-label">CDN Distribution</span>
                                    <span className="dm-step-detail">
                                        {cdnDone ? 'Live' : cdnDeploying ? 'Deploying (~5 min)' : 'Auto-created after SSL'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="dm-live-url-card">
                            <span className="dm-live-label">
                                {cdnDone ? 'Your site is live at' : cdnDeploying ? 'Almost live — CDN deploying' : 'Your site will be live at'}
                            </span>
                            <div className="dm-live-url">
                                <a href={`https://${domainPurchased.domain}`} target="_blank" rel="noopener noreferrer">
                                    https://{domainPurchased.domain}
                                </a>
                                <button className="dm-copy-btn" onClick={() => handleCopyUrl(`https://${domainPurchased.domain}`)}>
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                            </div>
                        </div>

                        <div className="dm-actions">
                            <a href={deployed.url} target="_blank" rel="noopener noreferrer" className="dm-btn dm-btn-outline">
                                <ExternalLink size={16} />S3 Preview
                            </a>
                            <button className="dm-btn dm-btn-primary" onClick={handleClose}>Done</button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // ── Render: Post-Deploy (Success + Domain Search Tabs) ──
    return (
        <div className="dm-overlay" onClick={handleClose}>
            <div className="dm-container dm-wide" onClick={e => e.stopPropagation()}>
                <button className="dm-close" onClick={handleClose}><X size={18} /></button>

                {/* Tab Header */}
                <div className="dm-tabs">
                    <button
                        className={`dm-tab ${activeTab === 'success' ? 'active' : ''}`}
                        onClick={() => setActiveTab('success')}
                    >
                        <CheckCircle2 size={16} />
                        <span>Deployed</span>
                    </button>
                    <button
                        className={`dm-tab ${activeTab === 'domain' ? 'active' : ''}`}
                        onClick={() => setActiveTab('domain')}
                    >
                        <Globe size={16} />
                        <span>Custom Domain</span>
                        <span className="dm-tab-badge">NEW</span>
                    </button>
                </div>

                {/* ── Tab: Deploy Success ── */}
                {activeTab === 'success' && (
                    <div className="dm-body dm-tab-content">
                        <div className="dm-success-hero">
                            <div className="dm-success-check"><Check size={28} /></div>
                            <h2>Your website is live!</h2>
                        </div>

                        <div className="dm-live-url-card">
                            <div className="dm-live-url">
                                <a href={deployed.url} target="_blank" rel="noopener noreferrer">
                                    {deployed.url}
                                    <ExternalLink size={14} />
                                </a>
                                <button className="dm-copy-btn" onClick={() => handleCopyUrl(deployed.url)}>
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                            </div>
                        </div>

                        {deployed.is_multipage && (
                            <div className="dm-meta">{deployed.page_count} pages deployed</div>
                        )}

                        <div className="dm-upgrade-banner" onClick={() => setActiveTab('domain')}>
                            <div className="dm-upgrade-left">
                                <Globe size={20} />
                                <div>
                                    <strong>Get a custom domain</strong>
                                    <span>Make it yours — yourname.com</span>
                                </div>
                            </div>
                            <ArrowRight size={18} />
                        </div>

                        <div className="dm-actions">
                            <a href={deployed.url} target="_blank" rel="noopener noreferrer" className="dm-btn dm-btn-primary">
                                <ExternalLink size={16} />Visit Website
                            </a>
                            <button className="dm-btn dm-btn-outline" onClick={handleClose}>Done</button>
                        </div>
                    </div>
                )}

                {/* ── Tab: Domain Search ── */}
                {activeTab === 'domain' && (
                    <div className="dm-body dm-tab-content">
                        {/* Show user's owned but unconnected domains first */}
                        {ownedDomains.length > 0 && (
                            <div className="dm-owned-domains">
                                <div className="dm-owned-header">
                                    <Globe size={18} />
                                    <div>
                                        <strong>Your Domains</strong>
                                        <span>Connect an existing domain instantly</span>
                                    </div>
                                </div>
                                <div className="dm-owned-list">
                                    {ownedDomains.map(d => (
                                        <div key={d.id} className="dm-owned-row">
                                            <div className="dm-owned-info">
                                                <span className="dm-owned-name">{d.domain_name}</span>
                                                {d.instant_connect && (
                                                    <span className="dm-instant-badge"><Zap size={10} /> Instant</span>
                                                )}
                                            </div>
                                            <button
                                                className="dm-btn dm-btn-sm dm-btn-connect"
                                                onClick={() => handleConnectOwnedDomain(d.domain_name)}
                                                disabled={!!connectingDomain}
                                            >
                                                {connectingDomain === d.domain_name ? (
                                                    <Loader2 className="spinning" size={13} />
                                                ) : (
                                                    <>Connect<ArrowRight size={14} /></>
                                                )}
                                            </button>
                                        </div>
                                    ))}
                                </div>
                                <div className="dm-owned-divider">
                                    <span>or register a new domain</span>
                                </div>
                            </div>
                        )}

                        <div className="dm-domain-hero">
                            <h2>{ownedDomains.length > 0 ? 'Register a new domain' : 'Find your perfect domain'}</h2>
                            <p>Search, register, and connect — all in one step</p>
                        </div>

                        <form onSubmit={handleDomainSearch} className="dm-search-form">
                            <div className="dm-search-input-wrap">
                                <Search size={18} className="dm-search-icon" />
                                <input
                                    ref={searchInputRef}
                                    type="text"
                                    value={domainQuery}
                                    onChange={e => setDomainQuery(e.target.value)}
                                    placeholder="Enter your domain name..."
                                    autoFocus
                                />
                                <button type="submit" className="dm-search-submit" disabled={searchingDomain || !domainQuery.trim()}>
                                    {searchingDomain ? <Loader2 className="spinning" size={16} /> : 'Search'}
                                </button>
                            </div>
                            <div className="dm-tld-row">
                                <div className="dm-tld-chips">
                                    {selectedTlds.slice(0, 6).map(tld => (
                                        <span key={tld} className="dm-tld-chip active" onClick={() => toggleTld(tld)}>
                                            .{tld} <X size={10} />
                                        </span>
                                    ))}
                                    <button type="button" className="dm-tld-more" onClick={() => setShowTldPicker(!showTldPicker)}>
                                        <ChevronDown size={14} /> More
                                    </button>
                                </div>
                                {showTldPicker && (
                                    <div className="dm-tld-picker">
                                        {allTlds.map(tld => (
                                            <label key={tld} className="dm-tld-option">
                                                <input
                                                    type="checkbox"
                                                    checked={selectedTlds.includes(tld)}
                                                    onChange={() => toggleTld(tld)}
                                                />
                                                <span>.{tld}</span>
                                            </label>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </form>

                        {domainError && <div className="dm-error"><AlertCircle size={15} />{domainError}</div>}

                        {searchingDomain && (
                            <div className="dm-searching">
                                <Loader2 className="spinning" size={24} />
                                <span>Checking availability across {selectedTlds.length} extensions...</span>
                            </div>
                        )}

                        {domainResults && !searchingDomain && (
                            <div className="dm-results">
                                {/* Featured/Best Match */}
                                {cheapest && (
                                    <div className="dm-result-featured">
                                        <div className="dm-featured-badge"><Sparkles size={12} /> Best Value</div>
                                        <div className="dm-featured-body">
                                            <div className="dm-featured-domain">
                                                <span className="dm-domain-name">{cheapest.sld}</span>
                                                <span className="dm-domain-ext">.{cheapest.tld}</span>
                                            </div>
                                            <div className="dm-featured-right">
                                                {cheapest.price && (
                                                    <div className="dm-featured-price">
                                                        <span className="dm-price-amount">${Number(cheapest.price.amount).toFixed(2)}</span>
                                                        <span className="dm-price-period">/year</span>
                                                    </div>
                                                )}
                                                <button
                                                    className="dm-btn dm-btn-register"
                                                    onClick={() => handleDomainPurchase(cheapest.sld, cheapest.tld)}
                                                    disabled={!!purchasingDomain}
                                                >
                                                    {purchasingDomain === cheapest.domain ? (
                                                        <Loader2 className="spinning" size={14} />
                                                    ) : (
                                                        <>Register<ArrowRight size={14} /></>
                                                    )}
                                                </button>
                                            </div>
                                        </div>
                                        <div className="dm-featured-perks">
                                            <span><Shield size={12} /> Free SSL</span>
                                            <span><Zap size={12} /> Auto DNS</span>
                                            <span><Globe size={12} /> CDN included</span>
                                        </div>
                                    </div>
                                )}

                                {/* Available Domains */}
                                {availableDomains.filter(r => r !== cheapest).length > 0 && (
                                    <div className="dm-result-section">
                                        <div className="dm-result-section-label">
                                            <CheckCircle2 size={14} /> Available
                                        </div>
                                        {availableDomains.filter(r => r !== cheapest).map(r => (
                                            <div key={r.domain} className="dm-result-row">
                                                <div className="dm-result-domain">
                                                    <span className="dm-domain-name">{r.sld}</span>
                                                    <span className="dm-domain-ext">.{r.tld}</span>
                                                </div>
                                                <div className="dm-result-right">
                                                    {r.price && (
                                                        <span className="dm-result-price">
                                                            ${Number(r.price.amount).toFixed(2)}/yr
                                                        </span>
                                                    )}
                                                    <button
                                                        className="dm-btn dm-btn-sm dm-btn-register"
                                                        onClick={() => handleDomainPurchase(r.sld, r.tld)}
                                                        disabled={!!purchasingDomain}
                                                    >
                                                        {purchasingDomain === r.domain ? (
                                                            <Loader2 className="spinning" size={13} />
                                                        ) : (
                                                            <>Register</>
                                                        )}
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Taken Domains */}
                                {takenDomains.length > 0 && (
                                    <div className="dm-result-section">
                                        <div className="dm-result-section-label dm-label-taken">
                                            <X size={14} /> Unavailable
                                        </div>
                                        {takenDomains.map(r => (
                                            <div key={r.domain} className="dm-result-row dm-row-taken">
                                                <div className="dm-result-domain">
                                                    <span className="dm-domain-name">{r.sld}</span>
                                                    <span className="dm-domain-ext">.{r.tld}</span>
                                                </div>
                                                <span className="dm-taken-tag">Taken</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {availableDomains.length === 0 && (
                                    <div className="dm-no-results">
                                        <Globe size={32} />
                                        <p>No domains available for "{domainQuery}"</p>
                                        <span>Try a different name or add more extensions</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default DeployModal;
