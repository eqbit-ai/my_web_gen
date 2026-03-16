// src/components/Dashboard.jsx

import config from '../config';
import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listProjects, getProject, deleteProject, listTemplateCatalog, getTemplateFull, listDeployedSites, deleteDeployedSite, connectDomain, getDomainStatus, disconnectDomain, listDnsRecords, addDnsRecord, deleteDnsRecord, getDnsNameservers, getActiveAnnouncements, searchDomains, purchaseDomain, retryDomainActivation, listUserDomains, getDomainContact, updateDomainContact, requestDomainTransfer, cancelDomainTransfer, requestTokens, getMyTokenRequests } from '../services/api';

// CSS override injected into iframe srcDoc to force-show elements hidden by scroll animations
const IFRAME_VISIBILITY_FIX = `* { opacity: 1 !important; transform: none !important; transition: none !important; animation: none !important; } img { display: inline-block !important; }`;

const buildSrcDoc = (css, html, withScripts = false) =>
    `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${IFRAME_VISIBILITY_FIX}</style><style>${css || ''}</style></head><body>${html || ''}${withScripts ? '' : ''}</body></html>`;


const Dashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [prompt, setPrompt] = useState('');
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [activeTab, setActiveTab] = useState(() => {
        const hash = window.location.hash.replace('#', '');
        return ['home', 'projects', 'templates', 'domains'].includes(hash) ? hash : 'home';
    });
    const [expandedSections, setExpandedSections] = useState({});
    const textareaRef = useRef(null);
    const userMenuRef = useRef(null);

    // Projects state
    const [projects, setProjects] = useState([]);
    const [projectsLoading, setProjectsLoading] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState(null);

    // Templates state
    const [templates, setTemplates] = useState([]);
    const [templatesLoading, setTemplatesLoading] = useState(false);
    const [templatePreviews, setTemplatePreviews] = useState({});
    const [previewModal, setPreviewModal] = useState(null);

    // Domains state
    const [deployedSites, setDeployedSites] = useState([]);
    const [domainsLoading, setDomainsLoading] = useState(false);
    const [connectModal, setConnectModal] = useState(null); // site_id to connect
    const [domainInput, setDomainInput] = useState('');
    const [connecting, setConnecting] = useState(false);
    const [connectResult, setConnectResult] = useState(null);
    const [modalOwnedDomains, setModalOwnedDomains] = useState([]);
    const [connectingOwned, setConnectingOwned] = useState(null);
    const [disconnectConfirm, setDisconnectConfirm] = useState(null);
    const [dnsRecords, setDnsRecords] = useState({}); // { siteId: records[] }
    const [addRecordModal, setAddRecordModal] = useState(null); // site_id
    const [newRecord, setNewRecord] = useState({ name: '', type: 'A', value: '', ttl: 300 });
    const [addingRecord, setAddingRecord] = useState(false);
    const [deleteSiteConfirm, setDeleteSiteConfirm] = useState(null);
    const [newDesignModal, setNewDesignModal] = useState(false);
    const [newDesignPreview, setNewDesignPreview] = useState(null); // template id for preview inside new design modal
    const [nameservers, setNameservers] = useState({}); // { siteId: string[] }
    const [contactInfo, setContactInfo] = useState({}); // { domainRecordId: contactObj }
    const [contactLoading, setContactLoading] = useState({});
    const [contactEditing, setContactEditing] = useState(null); // domainRecordId being edited
    const [contactForm, setContactForm] = useState({});
    const [contactSaving, setContactSaving] = useState(false);
    const [transferModal, setTransferModal] = useState(null); // domainRecordId
    const [transferReason, setTransferReason] = useState('');
    const [transferSubmitting, setTransferSubmitting] = useState(false);
    const [transferResult, setTransferResult] = useState(null);

    // Token request state
    const [tokenRequestModal, setTokenRequestModal] = useState(false);
    const [tokenRequestAmount, setTokenRequestAmount] = useState('500000');
    const [tokenRequestReason, setTokenRequestReason] = useState('');
    const [tokenRequestSubmitting, setTokenRequestSubmitting] = useState(false);
    const [tokenRequests, setTokenRequests] = useState([]);
    const [tokenRequestsLoaded, setTokenRequestsLoaded] = useState(false);
    const domainPollRef = useRef(null);
    const [announcements, setAnnouncements] = useState([]);
    const [dismissedAnnouncements, setDismissedAnnouncements] = useState(() => {
        try { return JSON.parse(localStorage.getItem('dismissed_announcements') || '[]'); } catch { return []; }
    });

    // Fetch active announcements
    useEffect(() => {
        getActiveAnnouncements().then(res => {
            setAnnouncements(res?.announcements || []);
        }).catch(() => {});
    }, []);

    const dismissAnnouncement = (id) => {
        const updated = [...dismissedAnnouncements, id];
        setDismissedAnnouncements(updated);
        localStorage.setItem('dismissed_announcements', JSON.stringify(updated));
    };

    const visibleAnnouncements = announcements.filter(a => !dismissedAnnouncements.includes(a.id));

    // Fetch user's available (unconnected) domains when connect modal opens
    useEffect(() => {
        if (!connectModal) { setModalOwnedDomains([]); return; }
        const token = localStorage.getItem('token');
        fetch(`${config.apiUrl}/api/deploy/${connectModal}/available-domains`, {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(r => r.json())
            .then(data => setModalOwnedDomains(data.available_domains || []))
            .catch(() => setModalOwnedDomains([]));
    }, [connectModal]);

    // Persist active tab in URL hash
    useEffect(() => {
        window.location.hash = activeTab;
    }, [activeTab]);

    const firstName = user?.full_name?.split(' ')[0] || 'there';

    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return 'Good morning';
        if (hour < 18) return 'Good afternoon';
        return 'Good evening';
    };

    const toggleSection = (domainId, section) => {
        const key = `${domainId}-${section}`;
        setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const isSectionExpanded = (domainId, section) => {
        return expandedSections[`${domainId}-${section}`] === true;
    };

    const loadContactInfo = async (domainRecordId) => {
        if (!domainRecordId || contactInfo[domainRecordId] || contactLoading[domainRecordId]) return;
        setContactLoading(prev => ({ ...prev, [domainRecordId]: true }));
        try {
            const data = await getDomainContact(domainRecordId);
            setContactInfo(prev => ({ ...prev, [domainRecordId]: data.contact || false }));
        } catch (err) {
            console.error('Failed to load contact:', err);
            setContactInfo(prev => ({ ...prev, [domainRecordId]: false }));
        } finally {
            setContactLoading(prev => ({ ...prev, [domainRecordId]: false }));
        }
    };

    const handleContactEdit = (domainRecordId) => {
        const c = contactInfo[domainRecordId];
        setContactForm({
            first_name: c?.first_name || '',
            last_name: c?.last_name || '',
            company_name: c?.company_name || '',
            email: c?.email || '',
            phone: c?.phone || '',
        });
        setContactEditing(domainRecordId);
    };

    const handleContactSave = async (domainRecordId) => {
        setContactSaving(true);
        try {
            await updateDomainContact(domainRecordId, contactForm);
            setContactInfo(prev => ({ ...prev, [domainRecordId]: { ...prev[domainRecordId], ...contactForm } }));
            setContactEditing(null);
        } catch (err) {
            alert(err.message);
        } finally {
            setContactSaving(false);
        }
    };

    const handleTransferRequest = async () => {
        if (!transferModal) return;
        setTransferSubmitting(true);
        try {
            const result = await requestDomainTransfer(transferModal, transferReason);
            setTransferResult(result);
            // Refresh sites
            const data = await listDeployedSites();
            setDeployedSites(data.sites || []);
        } catch (err) {
            setTransferResult({ status: 'error', message: err.message });
        } finally {
            setTransferSubmitting(false);
        }
    };

    const handleCancelTransfer = async (domainRecordId) => {
        try {
            await cancelDomainTransfer(domainRecordId);
            const data = await listDeployedSites();
            setDeployedSites(data.sites || []);
        } catch (err) {
            alert(err.message);
        }
    };

    // ── Token request handlers ──
    const loadTokenRequests = async () => {
        try {
            const data = await getMyTokenRequests();
            setTokenRequests(data.requests || []);
            setTokenRequestsLoaded(true);
        } catch {}
    };

    const handleTokenRequest = async () => {
        const amount = parseInt(tokenRequestAmount);
        if (!amount || amount <= 0) return;
        setTokenRequestSubmitting(true);
        try {
            await requestTokens(amount, tokenRequestReason);
            setTokenRequestModal(false);
            setTokenRequestAmount('500000');
            setTokenRequestReason('');
            loadTokenRequests();
            alert('Token request submitted! Admin will review it shortly.');
        } catch (err) {
            alert(err.message);
        }
        setTokenRequestSubmitting(false);
    };

    // ── Domain handlers ──
    const loadDeployedSites = async () => {
        setDomainsLoading(true);
        try {
            const data = await listDeployedSites();
            const sites = data.sites || [];
            setDeployedSites(sites);
            // Auto-load DNS records and nameservers for connected domains
            for (const site of sites) {
                if (site.domain) {
                    loadDnsRecords(site.id);
                    loadNameservers(site.id);
                }
            }
        } catch (e) { console.error('Failed to load sites:', e); }
        setDomainsLoading(false);
    };

    const loadDnsRecords = async (siteId) => {
        try {
            const data = await listDnsRecords(siteId);
            setDnsRecords(prev => ({ ...prev, [siteId]: data.records || [] }));
        } catch (e) {
            console.error('Failed to load DNS:', e);
            setDnsRecords(prev => ({ ...prev, [siteId]: [] }));
        }
    };

    const loadNameservers = async (siteId) => {
        try {
            const data = await getDnsNameservers(siteId);
            setNameservers(prev => ({ ...prev, [siteId]: data.nameservers || [] }));
        } catch (e) {
            console.error('Failed to load nameservers:', e);
            setNameservers(prev => ({ ...prev, [siteId]: [] }));
        }
    };

    const [connectError, setConnectError] = useState(null);
    const [domainSearchResults, setDomainSearchResults] = useState(null);
    const [purchasing, setPurchasing] = useState(false);

    const handleConnectDomain = async () => {
        if (!connectModal || !domainInput.trim()) return;
        setConnecting(true);
        setConnectError(null);
        setDomainSearchResults(null);
        try {
            const result = await connectDomain(connectModal, domainInput.trim());
            setConnectResult(result);
            loadDeployedSites();
        } catch (e) {
            const msg = e.message || 'Failed to connect domain';
            if (msg.includes('not registered')) {
                setConnectError('not_registered');
                // Auto-search for the domain to show pricing
                try {
                    const d = domainInput.trim();
                    const parts = d.includes('.') ? d.split('.') : [d];
                    const sld = parts[0];
                    const results = await searchDomains(sld, ['com', 'ae', 'net', 'org', 'io', 'co']);
                    setDomainSearchResults(results.results || []);
                } catch { /* ignore search error */ }
            } else {
                setConnectError(msg);
            }
        }
        setConnecting(false);
    };

    const handleConnectOwnedDomain = async (domainName) => {
        if (!connectModal) return;
        setConnectingOwned(domainName);
        setConnectError(null);
        try {
            const result = await connectDomain(connectModal, domainName);
            setConnectResult(result);
            loadDeployedSites();
        } catch (e) {
            setConnectError(e.message || 'Failed to connect domain');
        }
        setConnectingOwned(null);
    };

    const handleQuickPurchase = async (sld, tld, siteId) => {
        setPurchasing(true);
        try {
            await purchaseDomain(sld, tld, siteId, 1);
            setConnectModal(null);
            setConnectError(null);
            setDomainSearchResults(null);
            loadDeployedSites();
            alert(`${sld}.${tld} purchased and connected successfully!`);
        } catch (e) {
            const msg = typeof e.message === 'string' ? e.message : JSON.stringify(e.message);
            alert(msg || 'Purchase failed');
        }
        setPurchasing(false);
    };

    const handleDisconnect = async (siteId) => {
        try {
            await disconnectDomain(siteId);
            setDisconnectConfirm(null);
            loadDeployedSites();
        } catch (e) { alert(e.message || 'Failed to disconnect'); }
    };

    const handleAddRecord = async () => {
        if (!addRecordModal || !newRecord.name || !newRecord.value) return;
        setAddingRecord(true);
        try {
            await addDnsRecord(addRecordModal, newRecord);
            setAddRecordModal(null);
            setNewRecord({ name: '', type: 'A', value: '', ttl: 300 });
            loadDnsRecords(addRecordModal);
        } catch (e) { alert(e.message || 'Failed to add record'); }
        setAddingRecord(false);
    };

    const [deleteRecordConfirm, setDeleteRecordConfirm] = useState(null); // { siteId, record }

    const handleDeleteRecord = async (siteId, record) => {
        try {
            await deleteDnsRecord(siteId, { name: record.name, type: record.type, value: record.value });
            loadDnsRecords(siteId);
        } catch (e) { alert(e.message || 'Failed to delete record'); }
    };

    const handleDeleteSite = async (siteId) => {
        try {
            await deleteDeployedSite(siteId);
            setDeleteSiteConfirm(null);
            loadDeployedSites();
        } catch (e) { alert(e.message || 'Failed to delete site'); }
    };

    const statusColor = (s) => {
        if (s === 'active' || s === 'published') return 'green';
        if (s === 'pending' || s === 'pending_validation' || s === 'pending_deployment') return 'yellow';
        if (s === 'failed' || s === 'offline') return 'red';
        return 'gray';
    };

    useEffect(() => {
        if (activeTab === 'domains') {
            loadDeployedSites();
            // Poll domain status every 30s for sites with pending statuses
            domainPollRef.current = setInterval(async () => {
                try {
                    const data = await listDeployedSites();
                    const sites = data.sites || [];
                    setDeployedSites(sites);
                    // For any site with pending status, poll domain-status to trigger Phase 2
                    for (const site of sites) {
                        if (site.domain && (site.domain_status === 'pending_validation' || site.domain_status === 'pending_deployment' || site.domain_status === 'creating_cdn')) {
                            try { await getDomainStatus(site.id); } catch (_) {}
                        }
                    }
                } catch (_) {}
            }, 30000);
        }
        return () => { if (domainPollRef.current) clearInterval(domainPollRef.current); };
    }, [activeTab]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!prompt.trim()) return;
        navigate('/generator', { state: { initialPrompt: prompt.trim() } });
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    // Load projects/templates when their tab is active
    useEffect(() => {
        if (activeTab === 'projects') {
            loadProjects();
        } else if (activeTab === 'templates') {
            loadTemplates();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab]);

    const loadProjects = async () => {
        setProjectsLoading(true);
        try {
            const data = await listProjects();
            setProjects(data.projects || []);
        } catch (err) {
            console.error('Failed to load projects:', err);
        } finally {
            setProjectsLoading(false);
        }
    };

    const loadTemplates = async () => {
        if (templates.length > 0) return; // already loaded
        setTemplatesLoading(true);
        try {
            const data = await listTemplateCatalog();
            setTemplates(data.templates || []);
            // Load previews for all templates
            for (const t of (data.templates || [])) {
                getTemplateFull(t.id).then(full => {
                    setTemplatePreviews(prev => ({ ...prev, [t.id]: full }));
                }).catch(() => {});
            }
        } catch (err) {
            console.error('Failed to load templates:', err);
        } finally {
            setTemplatesLoading(false);
        }
    };

    const handleUseTemplate = async (templateId) => {
        try {
            const data = await getTemplateFull(templateId);
            navigate('/generator', {
                state: {
                    projectData: {
                        name: data.name,
                        html: data.html,
                        css: data.css,
                        js: '',
                        isTemplate: true,
                    },
                },
            });
        } catch (err) {
            console.error('Failed to load template:', err);
        }
    };

    const handleOpenProject = async (projectId) => {
        try {
            const data = await getProject(projectId);
            navigate('/generator', { state: { projectData: data } });
        } catch (err) {
            console.error('Failed to open project:', err);
        }
    };

    const handleDeleteProject = async (projectId) => {
        try {
            await deleteProject(projectId);
            setProjects(prev => prev.filter(p => p.id !== projectId));
            setDeleteConfirm(null);
        } catch (err) {
            console.error('Failed to delete project:', err);
        }
    };

    // Auto-resize textarea
    useEffect(() => {
        const ta = textareaRef.current;
        if (ta) {
            ta.style.height = 'auto';
            ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
        }
    }, [prompt]);

    // Close user menu on outside click
    useEffect(() => {
        const handleClick = (e) => {
            if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
                setUserMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);


    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    };

    const impersonating = localStorage.getItem('impersonating');
    const impersonateInfo = impersonating ? JSON.parse(impersonating) : null;

    const stopImpersonating = () => {
        const adminToken = localStorage.getItem('admin_token_backup');
        if (adminToken) {
            localStorage.setItem('token', adminToken);
            localStorage.removeItem('admin_token_backup');
        }
        localStorage.removeItem('impersonating');
        window.location.href = '/admin';
    };

    return (
        <div className={`dashboard${impersonateInfo ? ' impersonating' : ''}`}>
            {impersonateInfo && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
                    background: '#f59e0b', color: '#000', padding: '8px 16px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
                    fontSize: 14, fontWeight: 600,
                }}>
                    <span>Viewing as: {impersonateInfo.email} (read-only, {impersonateInfo.expiresIn}min)</span>
                    <button onClick={stopImpersonating} style={{
                        background: '#000', color: '#fff', border: 'none', borderRadius: 4,
                        padding: '4px 12px', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                    }}>
                        Stop Impersonating
                    </button>
                </div>
            )}
            {/* Sidebar */}
            <aside className={`dash-sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
                <div className="dash-sidebar-top">
                    <div className="dash-sidebar-header">
                        <div className="dash-logo">
                            <img src="/mfz-logo.webp" alt="Meydan Free Zone" style={{ height: 28 }} />
                        </div>
                        <button
                            className="dash-sidebar-toggle"
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            aria-label="Toggle sidebar"
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                {sidebarOpen ? (
                                    <><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="15" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></>
                                ) : (
                                    <><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></>
                                )}
                            </svg>
                        </button>
                    </div>

                    <button
                        className="dash-new-chat"
                        onClick={() => { setNewDesignModal(true); if (templates.length === 0) loadTemplates(); }}
                    >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        {sidebarOpen && <span>New Design</span>}
                    </button>

                    <nav className="dash-nav">
                        <button
                            className={`dash-nav-item ${activeTab === 'home' ? 'active' : ''}`}
                            onClick={() => setActiveTab('home')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
                            </svg>
                            {sidebarOpen && <span>Home</span>}
                        </button>
                        <button
                            className={`dash-nav-item ${activeTab === 'projects' ? 'active' : ''}`}
                            onClick={() => setActiveTab('projects')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                            </svg>
                            {sidebarOpen && <span>Projects</span>}
                        </button>
                        <button
                            className={`dash-nav-item ${activeTab === 'templates' ? 'active' : ''}`}
                            onClick={() => setActiveTab('templates')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
                            </svg>
                            {sidebarOpen && <span>Templates</span>}
                        </button>
                        <button
                            className={`dash-nav-item ${activeTab === 'domains' ? 'active' : ''}`}
                            onClick={() => setActiveTab('domains')}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                            </svg>
                            {sidebarOpen && <span>Domains</span>}
                        </button>
                        {user?.is_admin && (
                            <button
                                className="dash-nav-item"
                                onClick={() => navigate('/admin')}
                            >
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                                    <circle cx="12" cy="12" r="3" />
                                </svg>
                                {sidebarOpen && <span>Admin</span>}
                            </button>
                        )}
                    </nav>
                </div>

                {/* User profile at bottom */}
                <div className="dash-sidebar-bottom" ref={userMenuRef}>
                    {userMenuOpen && (
                        <div className="dash-user-menu">
                            <div className="dash-user-menu-header">
                                <span className="dash-user-menu-name">{user?.full_name}</span>
                                <span className="dash-user-menu-email">{user?.email}</span>
                            </div>
                            <div className="dash-user-menu-divider" />
                            <button className="dash-user-menu-item" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                                </svg>
                                Generator
                            </button>
                            <div className="dash-user-menu-divider" />
                            <button className="dash-user-menu-item danger" onClick={handleLogout}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
                                </svg>
                                Log out
                            </button>
                        </div>
                    )}
                    <button
                        className="dash-user-profile"
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                    >
                        <div className="dash-avatar">
                            {firstName.charAt(0).toUpperCase()}
                        </div>
                        {sidebarOpen && (
                            <div className="dash-user-info">
                                <span className="dash-user-name">{user?.full_name}</span>
                                <span className="dash-user-company">{user?.company_name}</span>
                            </div>
                        )}
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className={`dash-main ${activeTab === 'home' ? 'dash-main-gradient' : ''}`}>
                {/* Announcements */}
                {visibleAnnouncements.length > 0 && (
                    <div style={{ padding: '12px 24px 0', display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {visibleAnnouncements.map(a => {
                            const colors = { info: '#818cf8', warning: '#fbbf24', maintenance: '#f59e0b', success: '#34d399' };
                            const color = colors[a.type] || colors.info;
                            return (
                                <div key={a.id} style={{
                                    background: `${color}15`, border: `1px solid ${color}40`, borderRadius: 8,
                                    padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                                }}>
                                    <div>
                                        <strong style={{ color, fontSize: 13 }}>{a.title}</strong>
                                        <span style={{ color: '#e4e4e7', fontSize: 13, marginLeft: 8 }}>{a.message}</span>
                                    </div>
                                    <button onClick={() => dismissAnnouncement(a.id)} style={{
                                        background: 'none', border: 'none', color: '#71717a', cursor: 'pointer', fontSize: 16, padding: '0 4px',
                                    }}>×</button>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* ── Home Tab ────────────────────────────────────────── */}
                {activeTab === 'home' && (
                    <div className="dash-content">
                        <div className="dash-greeting">
                            <h1 className="dash-greeting-text">
                                {getGreeting()}, {firstName}
                            </h1>
                            <p className="dash-greeting-sub">
                                Create websites by chatting with Meydan AI
                            </p>
                            {user?.token_balance != null && (
                                <div className="dash-token-bar">
                                    <div className="dash-token-info">
                                        <span>Token Balance</span>
                                        <span>{(user.token_balance || 0).toLocaleString()} / 1,000,000</span>
                                    </div>
                                    <div className="dash-token-track">
                                        <div className="dash-token-fill" style={{ width: `${Math.min(100, ((user.token_balance || 0) / 1000000) * 100)}%` }} />
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                                        <button
                                            onClick={() => { setTokenRequestModal(true); if (!tokenRequestsLoaded) loadTokenRequests(); }}
                                            style={{ background: 'none', border: '1px solid rgba(255,255,255,0.15)', color: '#818cf8', padding: '4px 10px', borderRadius: 6, fontSize: 12, cursor: 'pointer' }}
                                        >
                                            Request More Tokens
                                        </button>
                                        {tokenRequests.some(r => r.status === 'pending') && (
                                            <span style={{ fontSize: 11, color: '#fbbf24' }}>Pending request</span>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="dash-input-area">
                            <form className="dash-input-form" onSubmit={handleSubmit}>
                                <div className="dash-input-wrapper">
                                    <textarea
                                        ref={textareaRef}
                                        className="dash-textarea"
                                        value={prompt}
                                        onChange={(e) => setPrompt(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        placeholder="Describe the website you want to create..."
                                        rows={1}
                                    />
                                    <button
                                        type="submit"
                                        className={`dash-send-btn ${prompt.trim() ? 'active' : ''}`}
                                        disabled={!prompt.trim()}
                                    >
                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" />
                                        </svg>
                                    </button>
                                </div>
                                <span className="dash-input-hint">
                                    Press Enter to send, Shift+Enter for new line
                                </span>
                            </form>
                        </div>
                    </div>
                )}

                {/* ── Projects Tab ────────────────────────────────────── */}
                {activeTab === 'projects' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <h1 className="dash-domain-title">My Projects</h1>
                            <button className="dash-domain-add-btn" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                                </svg>
                                New Project
                            </button>
                        </div>

                        {projectsLoading ? (
                            <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
                                Loading projects...
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="dash-projects-empty">
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#ccc' }}>
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                                </svg>
                                <h3>No projects yet</h3>
                                <p>Generate a website and save it to see it here</p>
                                <button className="dash-domain-add-btn" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                    Create Your First Website
                                </button>
                            </div>
                        ) : (
                            <div className="dash-projects-grid">
                                {projects.map(project => (
                                    <div key={project.id} className="dash-project-card" onClick={() => handleOpenProject(project.id)}>
                                        <div className="dash-project-thumb">
                                            {project.html ? (
                                                <iframe
                                                    title={project.name}
                                                    srcDoc={buildSrcDoc(project.css, project.html)}
                                                    sandbox="allow-same-origin allow-scripts"
                                                    scrolling="no"
                                                    className="dash-project-iframe"
                                                />
                                            ) : (
                                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#86EFCB' }}>
                                                    <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                                                </svg>
                                            )}
                                        </div>
                                        <div className="dash-project-body">
                                            <h4 className="dash-project-name">{project.name}</h4>
                                            <div className="dash-project-meta">
                                                <span>v{project.current_version}</span>
                                                <span>{formatDate(project.updated_at)}</span>
                                            </div>
                                        </div>
                                        <div className="dash-project-actions" onClick={e => e.stopPropagation()}>
                                            <button className="dash-project-open" onClick={() => handleOpenProject(project.id)}>Open</button>
                                            <button className="dash-project-delete" onClick={() => setDeleteConfirm(project.id)}>
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Delete confirmation */}
                        {deleteConfirm && (
                            <div className="dash-domain-modal-overlay" onClick={() => setDeleteConfirm(null)}>
                                <div className="dash-domain-modal" onClick={e => e.stopPropagation()}>
                                    <h3>Delete Project</h3>
                                    <p>Are you sure? This will delete all versions and cannot be undone.</p>
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setDeleteConfirm(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleDeleteProject(deleteConfirm)}>Delete</button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Templates Tab ──────────────────────────────────── */}
                {activeTab === 'templates' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <h1 className="dash-domain-title">Website Templates</h1>
                            <p style={{ color: '#666', fontSize: 14, margin: 0 }}>Choose a template and customize it with AI</p>
                        </div>

                        {templatesLoading ? (
                            <div style={{ textAlign: 'center', padding: '3rem', color: '#888' }}>
                                Loading templates...
                            </div>
                        ) : (
                            <div className="dash-templates-grid">
                                {templates.map(template => {
                                    const preview = templatePreviews[template.id];
                                    return (
                                        <div key={template.id} className="dash-template-card">
                                            <div className="dash-template-thumb" onClick={() => setPreviewModal(template.id)}>
                                                {preview ? (
                                                    <iframe
                                                        title={template.name}
                                                        srcDoc={buildSrcDoc(preview.css, preview.html)}
                                                        sandbox="allow-same-origin allow-scripts"
                                                        scrolling="no"
                                                        className="dash-template-iframe"
                                                    />
                                                ) : (
                                                    <div className="dash-template-placeholder">
                                                        <div className="dash-template-colors">
                                                            {(template.colors || []).map((c, i) => (
                                                                <span key={i} className="dash-template-swatch" style={{ background: c }} />
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                <div className="dash-template-overlay">
                                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
                                                    </svg>
                                                    Preview
                                                </div>
                                            </div>
                                            <div className="dash-template-body">
                                                <span className="dash-template-category">{template.category}</span>
                                                <h4 className="dash-template-name">{template.name}</h4>
                                                <p className="dash-template-desc">{template.description}</p>
                                                <div style={{ display: 'flex', gap: 8 }}>
                                                    <button className="dash-template-preview-btn" onClick={() => setPreviewModal(template.id)}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
                                                        </svg>
                                                        Preview
                                                    </button>
                                                    <button className="dash-template-use-btn" onClick={() => handleUseTemplate(template.id)}>
                                                        Use Template
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {/* Full-screen preview modal */}
                        {previewModal && templatePreviews[previewModal] && (
                            <div className="dash-template-modal-overlay" onClick={() => setPreviewModal(null)}>
                                <div className="dash-template-modal" onClick={e => e.stopPropagation()}>
                                    <div className="dash-template-modal-header">
                                        <h3>{templates.find(t => t.id === previewModal)?.name}</h3>
                                        <div className="dash-template-modal-actions">
                                            <button className="dash-template-use-btn" onClick={() => { setPreviewModal(null); handleUseTemplate(previewModal); }}>
                                                Use This Template
                                            </button>
                                            <button className="dash-template-modal-close" onClick={() => setPreviewModal(null)}>
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                    <iframe
                                        title="Template Preview"
                                        srcDoc={`<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${templatePreviews[previewModal].css || ''}</style></head><body>${templatePreviews[previewModal].html || ''}</body></html>`}
                                        className="dash-template-modal-iframe"
                                        sandbox="allow-same-origin allow-scripts"
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Domains Tab ─────────────────────────────────────── */}
                {activeTab === 'domains' && (
                    <div className="dash-domain-container">
                        <div className="dash-domain-header">
                            <div>
                                <h1 className="dash-domain-title">Deployed Sites</h1>
                                <p className="dash-domain-subtitle">Manage your websites, domains, and DNS configuration</p>
                            </div>
                        </div>

                        {domainsLoading ? (
                            <div className="dash-projects-empty"><p>Loading sites...</p></div>
                        ) : deployedSites.length === 0 ? (
                            <div className="dsite-empty">
                                <div className="dsite-empty-icon">
                                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></svg>
                                </div>
                                <h3>No deployed sites yet</h3>
                                <p>Deploy a website first, then manage domains here</p>
                                <button className="dsite-cta-btn" onClick={() => navigate('/generator', { state: { newSession: true } })}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                                    Create Website
                                </button>
                            </div>
                        ) : (
                            <div className="dsite-list">
                                {deployedSites.map(site => {
                                    const sColor = statusColor(site.domain_status || site.status);
                                    const sLabel = (site.domain_status || site.status || 'draft').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                                    return (
                                    <div key={site.id} className="dsite-card">
                                        {/* Card Header */}
                                        <div className="dsite-card-top">
                                            <div className="dsite-info">
                                                <div className="dsite-icon-wrap">
                                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                                    </svg>
                                                </div>
                                                <div className="dsite-meta">
                                                    <h3 className="dsite-name">{site.domain || site.name}</h3>
                                                    {site.url && (
                                                        <a href={site.url} target="_blank" rel="noopener noreferrer" className="dsite-url">
                                                            {site.url}
                                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>
                                                        </a>
                                                    )}
                                                </div>
                                            </div>
                                            <span className={`dsite-badge dsite-badge-${sColor}`}>{sLabel}</span>
                                        </div>

                                        {/* Quick Stats */}
                                        <div className="dsite-stats-row">
                                            <div className="dsite-stat">
                                                <span className="dsite-stat-label">Domain</span>
                                                <span className="dsite-stat-value">{site.domain || 'Not connected'}</span>
                                            </div>
                                            <div className="dsite-stat">
                                                <span className="dsite-stat-label">SSL</span>
                                                <span className="dsite-stat-value">{site.domain ? (site.cloudfront_domain ? 'Active' : 'Pending') : '—'}</span>
                                            </div>
                                            <div className="dsite-stat">
                                                <span className="dsite-stat-label">CDN</span>
                                                <span className="dsite-stat-value">{site.cloudfront_domain ? 'Active' : '—'}</span>
                                            </div>
                                            {site.last_deployed_at && (
                                                <div className="dsite-stat">
                                                    <span className="dsite-stat-label">Deployed</span>
                                                    <span className="dsite-stat-value">{new Date(site.last_deployed_at).toLocaleDateString()}</span>
                                                </div>
                                            )}
                                        </div>

                                        {/* Actions Bar */}
                                        <div className="dsite-actions">
                                            {!site.domain && site.status === 'published' && (
                                                <button className="dsite-action-btn dsite-action-primary" onClick={() => { setConnectModal(site.id); setConnectResult(null); setDomainInput(''); }}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                                                    Connect Domain
                                                </button>
                                            )}
                                            {site.url && (
                                                <a href={site.url} target="_blank" rel="noopener noreferrer" className="dsite-action-btn">
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>
                                                    Visit Site
                                                </a>
                                            )}
                                            {site.domain && (
                                                <button className="dsite-action-btn" onClick={() => { toggleSection(site.id, 'dns'); if (!dnsRecords[site.id]) loadDnsRecords(site.id); }}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></svg>
                                                    DNS Records
                                                </button>
                                            )}
                                            {site.domain && (
                                                <button className="dsite-action-btn" onClick={() => { toggleSection(site.id, 'ns'); if (!nameservers[site.id]) loadNameservers(site.id); }}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
                                                    Nameservers
                                                </button>
                                            )}
                                            {site.domain_record_id && (
                                                <button className="dsite-action-btn" onClick={() => { toggleSection(site.id, 'contact'); loadContactInfo(site.domain_record_id); }}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                                                    Contact Info
                                                </button>
                                            )}
                                            <div className="dsite-actions-right">
                                                {site.domain && (
                                                    <button className="dsite-action-btn dsite-action-danger" onClick={() => setDisconnectConfirm(site.id)}>Disconnect</button>
                                                )}
                                                <button className="dsite-action-btn dsite-action-danger" onClick={() => setDeleteSiteConfirm(site.id)}>
                                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /><path d="M10 11v6" /><path d="M14 11v6" /></svg>
                                                    Delete
                                                </button>
                                            </div>
                                        </div>

                                        {/* DNS Records Panel */}
                                        {site.domain && isSectionExpanded(site.id, 'dns') && (
                                            <div className="dsite-panel">
                                                <div className="dsite-panel-header">
                                                    <h4>DNS Records</h4>
                                                    <button className="dsite-panel-btn" onClick={() => setAddRecordModal(site.id)}>+ Add Record</button>
                                                </div>
                                                <table className="dash-domain-table">
                                                    <thead>
                                                        <tr><th>Type</th><th>Name</th><th>Value</th><th>TTL</th><th></th></tr>
                                                    </thead>
                                                    <tbody>
                                                        {(dnsRecords[site.id] || []).map((rec, i) => (
                                                            <tr key={i}>
                                                                <td><span className="dash-domain-type-badge">{rec.type}</span></td>
                                                                <td style={{ fontSize: 13 }}>{rec.name}</td>
                                                                <td className="dash-domain-value-cell">{rec.is_alias ? `ALIAS \u2192 ${rec.alias_target || rec.value}` : rec.value}</td>
                                                                <td>{rec.ttl || '\u2014'}</td>
                                                                <td>
                                                                    {!rec.managed ? (
                                                                        <button className="dash-domain-edit-btn" title="Delete" onClick={() => setDeleteRecordConfirm({ siteId: site.id, record: rec })} style={{ color: '#ef4444' }}>
                                                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /><path d="M10 11v6" /><path d="M14 11v6" /></svg>
                                                                        </button>
                                                                    ) : <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>System</span>}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                        {!dnsRecords[site.id] && (
                                                            <tr><td colSpan="5" className="dsite-panel-empty">Loading records...</td></tr>
                                                        )}
                                                        {dnsRecords[site.id] && dnsRecords[site.id].length === 0 && (
                                                            <tr><td colSpan="5" className="dsite-panel-empty">
                                                                {site.route53_zone_id ? 'No DNS records found' : 'No hosted zone \u2014 connect a domain first'}
                                                            </td></tr>
                                                        )}
                                                    </tbody>
                                                </table>
                                            </div>
                                        )}

                                        {/* Nameservers Panel */}
                                        {site.domain && isSectionExpanded(site.id, 'ns') && (
                                            <div className="dsite-panel">
                                                <div className="dsite-panel-header">
                                                    <h4>Nameservers</h4>
                                                </div>
                                                <p className="dsite-panel-hint">Point your domain to these nameservers at your registrar:</p>
                                                <div className="dsite-ns-grid">
                                                    {!nameservers[site.id] ? (
                                                        <p className="dsite-panel-empty">Loading nameservers...</p>
                                                    ) : nameservers[site.id].length > 0 ? (
                                                        nameservers[site.id].map((ns, i) => (
                                                            <div key={i} className="dsite-ns-item">
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
                                                                <code>{ns}</code>
                                                            </div>
                                                        ))
                                                    ) : (
                                                        <p className="dsite-panel-empty">
                                                            {site.route53_zone_id ? 'No nameservers found' : 'No hosted zone \u2014 connect a domain first'}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* Contact Info Panel */}
                                        {site.domain_record_id && isSectionExpanded(site.id, 'contact') && (
                                            <div className="dsite-panel">
                                                <div className="dsite-panel-header">
                                                    <h4>Contact Information</h4>
                                                    {contactInfo[site.domain_record_id] && contactEditing !== site.domain_record_id && (
                                                        <button className="dsite-panel-btn" onClick={() => handleContactEdit(site.domain_record_id)}>Edit</button>
                                                    )}
                                                </div>
                                                {contactLoading[site.domain_record_id] || !(site.domain_record_id in contactInfo) ? (
                                                    <p className="dsite-panel-empty">Loading contact info...</p>
                                                ) : !contactInfo[site.domain_record_id] ? (
                                                    <p className="dsite-panel-empty">No contact information available</p>
                                                ) : contactEditing === site.domain_record_id ? (
                                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, padding: '8px 0' }}>
                                                        {['first_name', 'last_name', 'company_name', 'email', 'phone'].map(field => (
                                                            <div key={field} style={field === 'company_name' ? { gridColumn: '1 / -1' } : {}}>
                                                                <label style={{ fontSize: 11, color: '#9ca3af', textTransform: 'capitalize', display: 'block', marginBottom: 3 }}>{field.replace(/_/g, ' ')}</label>
                                                                <input
                                                                    value={contactForm[field] || ''}
                                                                    onChange={e => setContactForm(prev => ({ ...prev, [field]: e.target.value }))}
                                                                    style={{ width: '100%', padding: '6px 10px', fontSize: 13, background: '#1f2937', border: '1px solid #374151', borderRadius: 6, color: '#f3f4f6', outline: 'none', boxSizing: 'border-box' }}
                                                                />
                                                            </div>
                                                        ))}
                                                        <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
                                                            <button onClick={() => setContactEditing(null)} style={{ padding: '6px 14px', fontSize: 12, background: 'none', border: '1px solid #4b5563', borderRadius: 6, color: '#9ca3af', cursor: 'pointer' }}>Cancel</button>
                                                            <button onClick={() => handleContactSave(site.domain_record_id)} disabled={contactSaving} style={{ padding: '6px 14px', fontSize: 12, background: '#3b82f6', border: 'none', borderRadius: 6, color: '#fff', cursor: 'pointer', opacity: contactSaving ? 0.5 : 1 }}>{contactSaving ? 'Saving...' : 'Save'}</button>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 20px', padding: '8px 0' }}>
                                                        {[
                                                            ['Name', `${contactInfo[site.domain_record_id].first_name || ''} ${contactInfo[site.domain_record_id].last_name || ''}`.trim()],
                                                            ['Company', contactInfo[site.domain_record_id].company_name],
                                                            ['Email', contactInfo[site.domain_record_id].email],
                                                            ['Phone', contactInfo[site.domain_record_id].phone],
                                                        ].map(([label, value]) => (
                                                            <div key={label}>
                                                                <span style={{ fontSize: 11, color: '#6b7280', display: 'block' }}>{label}</span>
                                                                <span style={{ fontSize: 13, color: '#e5e7eb' }}>{value || '—'}</span>
                                                            </div>
                                                        ))}
                                                        {contactInfo[site.domain_record_id].address && (
                                                            <div style={{ gridColumn: '1 / -1' }}>
                                                                <span style={{ fontSize: 11, color: '#6b7280', display: 'block' }}>Address</span>
                                                                <span style={{ fontSize: 13, color: '#e5e7eb' }}>
                                                                    {[contactInfo[site.domain_record_id].address.street, contactInfo[site.domain_record_id].address.number, contactInfo[site.domain_record_id].address.city, contactInfo[site.domain_record_id].address.state, contactInfo[site.domain_record_id].address.country].filter(Boolean).join(', ')}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                {/* Transfer Request section */}
                                                <div style={{ borderTop: '1px solid #374151', marginTop: 12, paddingTop: 12 }}>
                                                    {site.transfer_requested_at ? (
                                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                                                                <span style={{ fontSize: 13, color: '#fbbf24' }}>Transfer requested on {new Date(site.transfer_requested_at).toLocaleDateString()}</span>
                                                            </div>
                                                            <button onClick={() => handleCancelTransfer(site.domain_record_id)} style={{ fontSize: 12, background: 'none', border: '1px solid #4b5563', borderRadius: 6, padding: '4px 10px', color: '#9ca3af', cursor: 'pointer' }}>Cancel</button>
                                                        </div>
                                                    ) : (
                                                        <button
                                                            onClick={() => { setTransferModal(site.domain_record_id); setTransferReason(''); setTransferResult(null); }}
                                                            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, background: 'none', border: '1px solid #4b5563', borderRadius: 6, padding: '6px 14px', color: '#9ca3af', cursor: 'pointer' }}
                                                        >
                                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></svg>
                                                            Request Domain Transfer
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        )}

                                        {/* Pending status notice with refresh */}
                                        {(site.domain_status === 'pending_validation' || site.domain_status === 'pending_deployment' || site.domain_status === 'creating_cdn') && (
                                            <div className="dsite-notice" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                                                    {site.domain_status === 'pending_validation' ? 'SSL certificate pending validation...' :
                                                     site.domain_status === 'creating_cdn' ? 'Creating CDN distribution...' :
                                                     'CloudFront deployment in progress...'}
                                                </div>
                                                <button
                                                    onClick={async (e) => {
                                                        const btn = e.currentTarget;
                                                        btn.disabled = true;
                                                        btn.textContent = 'Checking...';
                                                        try {
                                                            const result = await getDomainStatus(site.id);
                                                            // Refresh the sites list
                                                            const data = await listDeployedSites();
                                                            setDeployedSites(data.sites || []);
                                                            if (result.domain_status === 'active') {
                                                                btn.textContent = 'Active!';
                                                                btn.style.color = '#34d399';
                                                            } else {
                                                                btn.textContent = 'Still pending';
                                                                setTimeout(() => { btn.textContent = 'Refresh'; btn.disabled = false; }, 2000);
                                                            }
                                                        } catch (err) {
                                                            btn.textContent = 'Error';
                                                            setTimeout(() => { btn.textContent = 'Refresh'; btn.disabled = false; }, 2000);
                                                        }
                                                    }}
                                                    style={{ background: 'none', border: '1px solid #4b5563', borderRadius: 6, padding: '4px 12px', color: '#9ca3af', fontSize: 12, cursor: 'pointer', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 4 }}
                                                >
                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" /></svg>
                                                    Refresh
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* Connect Domain Modal */}
                {connectModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => { setConnectModal(null); setConnectResult(null); setConnectError(null); }}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
                            {connectError === 'not_registered' ? (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: '#fef3c7' }}>
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Domain Not Registered</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 12 }}>
                                        <strong style={{ color: '#e5e7eb' }}>{domainInput}</strong> is not registered yet. Purchase it below and it will be auto-connected to your site.
                                    </p>

                                    {domainSearchResults === null ? (
                                        <div style={{ textAlign: 'center', padding: 16, color: '#9ca3af', fontSize: 13 }}>Searching available domains...</div>
                                    ) : domainSearchResults.length > 0 ? (
                                        <div style={{ maxHeight: 220, overflowY: 'auto', marginBottom: 16, borderRadius: 8, border: '1px solid #374151' }}>
                                            {domainSearchResults.filter(r => r.status === 'free').map((r, i) => (
                                                <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: i < domainSearchResults.filter(x => x.status === 'free').length - 1 ? '1px solid #374151' : 'none' }}>
                                                    <div>
                                                        <span style={{ fontWeight: 600, fontSize: 14, color: '#f3f4f6' }}>{r.sld}</span>
                                                        <span style={{ color: '#9ca3af', fontSize: 14 }}>.{r.tld}</span>
                                                    </div>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                                        {r.price && <span style={{ fontSize: 13, color: '#34d399', fontWeight: 600 }}>${r.price.amount}/yr</span>}
                                                        <button
                                                            onClick={() => handleQuickPurchase(r.sld, r.tld, connectModal)}
                                                            disabled={purchasing}
                                                            style={{ padding: '5px 14px', borderRadius: 6, border: 'none', background: '#2563eb', color: '#fff', fontSize: 12, fontWeight: 600, cursor: purchasing ? 'wait' : 'pointer', opacity: purchasing ? 0.6 : 1 }}
                                                        >
                                                            {purchasing ? '...' : 'Buy & Connect'}
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                            {domainSearchResults.filter(r => r.status !== 'free').length > 0 && (
                                                <div style={{ padding: '8px 14px', fontSize: 12, color: '#6b7280', background: '#1f2937' }}>
                                                    {domainSearchResults.filter(r => r.status !== 'free').map(r => r.domain).join(', ')} — already taken
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>No domains available. Try a different name.</p>
                                    )}

                                    <div className="dash-domain-modal-actions" style={{ gap: 8 }}>
                                        <button className="dash-domain-modal-cancel" onClick={() => { setConnectError(null); setDomainSearchResults(null); }}>Try Another Domain</button>
                                    </div>
                                </>
                            ) : connectError ? (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: '#fef2f2' }}>
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Connection Failed</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>{connectError}</p>
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setConnectError(null)}>Try Again</button>
                                    </div>
                                </>
                            ) : !connectResult ? (
                                <>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Connect Custom Domain</h3>

                                    {/* Owned domains available for quick connect */}
                                    {modalOwnedDomains.length > 0 && (
                                        <div style={{ marginBottom: 16 }}>
                                            <p style={{ fontSize: 12, color: '#9ca3af', marginBottom: 8 }}>Your available domains</p>
                                            <div style={{ borderRadius: 8, border: '1px solid #374151', overflow: 'hidden' }}>
                                                {modalOwnedDomains.map((d, i) => (
                                                    <div key={d.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: i < modalOwnedDomains.length - 1 ? '1px solid #374151' : 'none', background: '#1f2937' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                            <span style={{ fontSize: 14, fontWeight: 600, color: '#f3f4f6' }}>{d.domain_name}</span>
                                                            {d.instant_connect && (
                                                                <span style={{ fontSize: 10, fontWeight: 600, color: '#fbbf24', background: 'rgba(251,191,36,0.12)', padding: '2px 6px', borderRadius: 4, display: 'flex', alignItems: 'center', gap: 3 }}>
                                                                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>
                                                                    Instant
                                                                </span>
                                                            )}
                                                        </div>
                                                        <button
                                                            onClick={() => handleConnectOwnedDomain(d.domain_name)}
                                                            disabled={!!connectingOwned}
                                                            style={{ padding: '5px 14px', borderRadius: 6, border: 'none', background: '#2563eb', color: '#fff', fontSize: 12, fontWeight: 600, cursor: connectingOwned ? 'wait' : 'pointer', opacity: connectingOwned ? 0.6 : 1, display: 'flex', alignItems: 'center', gap: 4 }}
                                                        >
                                                            {connectingOwned === d.domain_name ? 'Connecting...' : 'Connect'}
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '14px 0', color: '#6b7280', fontSize: 12 }}>
                                                <div style={{ flex: 1, height: 1, background: '#374151' }} />
                                                <span>or enter a domain</span>
                                                <div style={{ flex: 1, height: 1, background: '#374151' }} />
                                            </div>
                                        </div>
                                    )}

                                    {modalOwnedDomains.length === 0 && (
                                        <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                            Enter a domain you own. We'll verify it's registered, then set up SSL and DNS automatically.
                                        </p>
                                    )}
                                    <input
                                        type="text"
                                        value={domainInput}
                                        onChange={e => setDomainInput(e.target.value)}
                                        placeholder="mybusiness.ae"
                                        style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid #374151', background: '#1f2937', color: '#f3f4f6', fontSize: 14, marginBottom: 16 }}
                                        disabled={connecting}
                                        onKeyDown={e => e.key === 'Enter' && handleConnectDomain()}
                                    />
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setConnectModal(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" onClick={handleConnectDomain} disabled={connecting || !domainInput.trim()}>
                                            {connecting ? 'Verifying...' : 'Connect'}
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: '#ecfdf5' }}>
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Domain Connected!</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                        {connectResult.instructions}
                                    </p>
                                    {connectResult.nameservers && (
                                        <div style={{ background: '#1f2937', borderRadius: 8, padding: 16, marginBottom: 16, border: '1px solid #374151' }}>
                                            <p style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#d1d5db' }}>Set these nameservers at your registrar:</p>
                                            {connectResult.nameservers.map((ns, i) => (
                                                <div key={i} style={{ fontFamily: 'monospace', fontSize: 13, padding: '4px 0', color: '#e5e7eb' }}>{ns}</div>
                                            ))}
                                        </div>
                                    )}
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-confirm" onClick={() => { setConnectModal(null); setConnectResult(null); }}>Done</button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* Add DNS Record Modal */}
                {addRecordModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => setAddRecordModal(null)}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
                            <h3 style={{ marginBottom: 12 }}>Add DNS Record</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                <select value={newRecord.type} onChange={e => setNewRecord({ ...newRecord, type: e.target.value })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }}>
                                    {['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV', 'CAA'].map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                                <input placeholder="Name (e.g. mail, @, subdomain)" value={newRecord.name} onChange={e => setNewRecord({ ...newRecord, name: e.target.value })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }} />
                                <input placeholder={newRecord.type === 'MX' ? '10 mail.google.com' : 'Value'} value={newRecord.value} onChange={e => setNewRecord({ ...newRecord, value: e.target.value })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }} />
                                <input type="number" placeholder="TTL (default 300)" value={newRecord.ttl} onChange={e => setNewRecord({ ...newRecord, ttl: parseInt(e.target.value) || 300 })}
                                    style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid #d1d5db', fontSize: 13 }} />
                            </div>
                            <div className="dash-domain-modal-actions" style={{ marginTop: 16 }}>
                                <button className="dash-domain-modal-cancel" onClick={() => setAddRecordModal(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" onClick={handleAddRecord} disabled={addingRecord || !newRecord.name || !newRecord.value}>
                                    {addingRecord ? 'Adding...' : 'Add Record'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Disconnect Confirmation Modal */}
                {disconnectConfirm && (
                    <div className="dash-domain-modal-overlay" onClick={() => setDisconnectConfirm(null)}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()}>
                            <h3>Disconnect Domain?</h3>
                            <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>
                                This will remove the custom domain, SSL certificate, CDN, and DNS zone from our platform. Your site will still be accessible via the S3 URL.
                            </p>
                            <p style={{ fontSize: 13, color: '#f59e0b', margin: '0 0 16px', fontWeight: 500 }}>
                                Important: You must manually update your nameservers back to default at your domain registrar (e.g. GoDaddy), otherwise your domain will stop resolving.
                            </p>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setDisconnectConfirm(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleDisconnect(disconnectConfirm)}>Disconnect</button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Delete Site Confirmation Modal */}
                {deleteSiteConfirm && (
                    <div className="dash-domain-modal-overlay" onClick={() => setDeleteSiteConfirm(null)}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()}>
                            <h3>Delete Deployed Site?</h3>
                            <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>
                                This will permanently remove the site from S3, delete all associated domain resources (SSL, DNS, CDN), and cannot be undone.
                            </p>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setDeleteSiteConfirm(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => handleDeleteSite(deleteSiteConfirm)}>Delete</button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Delete DNS Record Confirmation Modal */}
                {deleteRecordConfirm && (
                    <div className="dash-domain-modal-overlay" onClick={() => setDeleteRecordConfirm(null)}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()}>
                            <h3>Delete DNS Record?</h3>
                            <p style={{ fontSize: 13, color: '#6b7280', margin: '8px 0 16px' }}>
                                Deleting this record cannot be undone. This may affect email delivery, domain verification, or other services using this record.
                            </p>
                            <div style={{ background: '#1f2937', borderRadius: 6, padding: 12, marginBottom: 16, fontSize: 13 }}>
                                <strong>{deleteRecordConfirm.record.type}</strong> {deleteRecordConfirm.record.name} → {deleteRecordConfirm.record.value}
                            </div>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setDeleteRecordConfirm(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#ef4444' }} onClick={() => { handleDeleteRecord(deleteRecordConfirm.siteId, deleteRecordConfirm.record); setDeleteRecordConfirm(null); }}>Delete Record</button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Transfer Request Modal */}
                {transferModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => { setTransferModal(null); setTransferResult(null); }}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 440 }}>
                            {transferResult ? (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: transferResult.status === 'error' ? '#fef2f2' : '#ecfdf5' }}>
                                        {transferResult.status === 'error' ? (
                                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                                        ) : (
                                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                                        )}
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>{transferResult.status === 'error' ? 'Error' : 'Transfer Requested'}</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>{transferResult.message}</p>
                                    <button className="dash-domain-modal-confirm" style={{ background: '#3b82f6', width: '100%' }} onClick={() => { setTransferModal(null); setTransferResult(null); }}>OK</button>
                                </>
                            ) : (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: '#fef3c7' }}>
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></svg>
                                    </div>
                                    <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Request Domain Transfer</h3>
                                    <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                        Submit a request to transfer this domain away from the platform. Our team will review and process your request within 24-48 hours.
                                    </p>
                                    <div style={{ marginBottom: 16 }}>
                                        <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Reason (optional)</label>
                                        <textarea
                                            value={transferReason}
                                            onChange={e => setTransferReason(e.target.value)}
                                            placeholder="e.g. Moving to a different hosting provider..."
                                            rows={3}
                                            style={{ width: '100%', padding: '8px 12px', fontSize: 13, background: '#1f2937', border: '1px solid #374151', borderRadius: 8, color: '#f3f4f6', outline: 'none', resize: 'vertical', boxSizing: 'border-box' }}
                                        />
                                    </div>
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setTransferModal(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" style={{ background: '#f59e0b' }} onClick={handleTransferRequest} disabled={transferSubmitting}>
                                            {transferSubmitting ? 'Submitting...' : 'Submit Request'}
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* Token Request Modal */}
                {tokenRequestModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => setTokenRequestModal(false)}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 440 }}>
                            <div className="dash-domain-modal-icon" style={{ background: '#ede9fe' }}>
                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 18V6"/></svg>
                            </div>
                            <h3 style={{ marginBottom: 8, color: '#f3f4f6' }}>Request More Tokens</h3>
                            <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                                Submit a request to the admin for additional tokens. You'll be notified when it's reviewed.
                            </p>
                            <div style={{ marginBottom: 12 }}>
                                <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Amount</label>
                                <select
                                    value={tokenRequestAmount}
                                    onChange={e => setTokenRequestAmount(e.target.value)}
                                    style={{ width: '100%', padding: '8px 12px', background: '#1f2937', color: '#f3f4f6', border: '1px solid #374151', borderRadius: 8, fontSize: 14 }}
                                >
                                    <option value="100000">100,000 tokens</option>
                                    <option value="250000">250,000 tokens</option>
                                    <option value="500000">500,000 tokens</option>
                                    <option value="1000000">1,000,000 tokens</option>
                                    <option value="2000000">2,000,000 tokens</option>
                                </select>
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <label style={{ fontSize: 12, color: '#9ca3af', display: 'block', marginBottom: 4 }}>Reason (optional)</label>
                                <textarea
                                    value={tokenRequestReason}
                                    onChange={e => setTokenRequestReason(e.target.value)}
                                    placeholder="e.g. Need more tokens for a large project..."
                                    style={{ width: '100%', minHeight: 70, padding: '8px 12px', background: '#1f2937', color: '#f3f4f6', border: '1px solid #374151', borderRadius: 8, fontSize: 13, resize: 'vertical' }}
                                />
                            </div>

                            {/* Show past requests */}
                            {tokenRequests.length > 0 && (
                                <div style={{ marginBottom: 16, maxHeight: 120, overflow: 'auto' }}>
                                    <label style={{ fontSize: 11, color: '#6b7280', display: 'block', marginBottom: 4 }}>Your Requests</label>
                                    {tokenRequests.map(r => (
                                        <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <span style={{ color: '#d1d5db' }}>{parseInt(r.amount).toLocaleString()} tokens</span>
                                            <span style={{ color: r.status === 'approved' ? '#34d399' : r.status === 'rejected' ? '#f87171' : '#fbbf24', fontWeight: 600 }}>
                                                {r.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div style={{ display: 'flex', gap: 8 }}>
                                <button className="dash-domain-modal-cancel" onClick={() => setTokenRequestModal(false)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" style={{ background: '#7c3aed' }} onClick={handleTokenRequest} disabled={tokenRequestSubmitting}>
                                    {tokenRequestSubmitting ? 'Submitting...' : 'Submit Request'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* New Design Modal */}
                {newDesignModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => { setNewDesignModal(false); setNewDesignPreview(null); }}>
                        <div className="dash-newdesign-modal" onClick={e => e.stopPropagation()}>
                            {!newDesignPreview ? (
                                <>
                                    <div className="dash-newdesign-header">
                                        <h2>New Design</h2>
                                        <button className="dash-template-modal-close" onClick={() => setNewDesignModal(false)}>
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                            </svg>
                                        </button>
                                    </div>

                                    {/* Start from scratch */}
                                    <div className="dash-newdesign-scratch" onClick={() => { setNewDesignModal(false); navigate('/generator', { state: { newSession: true } }); }}>
                                        <div className="dash-newdesign-scratch-icon">
                                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h4 style={{ margin: 0, fontSize: 15, color: '#e5e7eb' }}>Start from Scratch</h4>
                                            <p style={{ margin: '4px 0 0', fontSize: 13, color: '#9ca3af' }}>Describe your website and let AI build it</p>
                                        </div>
                                    </div>

                                    {/* Or pick a template */}
                                    <div style={{ padding: '0 24px 8px', fontSize: 13, color: '#6b7280', fontWeight: 500 }}>Or start from a template</div>

                                    <div className="dash-newdesign-templates">
                                        {templatesLoading ? (
                                            <div style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>Loading templates...</div>
                                        ) : (
                                            templates.map(template => {
                                                const preview = templatePreviews[template.id];
                                                return (
                                                    <div key={template.id} className="dash-newdesign-template-row">
                                                        <div className="dash-newdesign-template-thumb">
                                                            {preview ? (
                                                                <iframe
                                                                    title={template.name}
                                                                    srcDoc={buildSrcDoc(preview.css, preview.html)}
                                                                    sandbox="allow-same-origin allow-scripts"
                                                                    scrolling="no"
                                                                    tabIndex={-1}
                                                                />
                                                            ) : (
                                                                <div style={{ background: '#1f2937', width: '100%', height: '100%', borderRadius: 6 }} />
                                                            )}
                                                        </div>
                                                        <div className="dash-newdesign-template-info">
                                                            <span style={{ fontSize: 11, color: '#6366f1', textTransform: 'uppercase', fontWeight: 600 }}>{template.category}</span>
                                                            <h4 style={{ margin: '2px 0', fontSize: 14, color: '#e5e7eb' }}>{template.name}</h4>
                                                            <p style={{ margin: 0, fontSize: 12, color: '#9ca3af', lineHeight: 1.4 }}>{template.description}</p>
                                                        </div>
                                                        <div className="dash-newdesign-template-actions">
                                                            <button className="dash-template-preview-btn" onClick={() => setNewDesignPreview(template.id)}>
                                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
                                                                </svg>
                                                                Preview
                                                            </button>
                                                            <button className="dash-template-use-btn" style={{ padding: '8px 16px', fontSize: 13 }} onClick={() => { setNewDesignModal(false); handleUseTemplate(template.id); }}>
                                                                Use
                                                            </button>
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        )}
                                    </div>
                                </>
                            ) : (
                                <>
                                    {/* Template preview inside new design modal */}
                                    <div className="dash-newdesign-header">
                                        <button className="dash-template-preview-btn" onClick={() => setNewDesignPreview(null)} style={{ gap: 4 }}>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <polyline points="15 18 9 12 15 6" />
                                            </svg>
                                            Back
                                        </button>
                                        <h3 style={{ margin: 0, flex: 1, textAlign: 'center' }}>{templates.find(t => t.id === newDesignPreview)?.name}</h3>
                                        <button className="dash-template-use-btn" style={{ width: 'auto', padding: '8px 20px', fontSize: 13 }} onClick={() => { setNewDesignModal(false); setNewDesignPreview(null); handleUseTemplate(newDesignPreview); }}>
                                            Use This Template
                                        </button>
                                    </div>
                                    <iframe
                                        title="Template Preview"
                                        srcDoc={templatePreviews[newDesignPreview] ? `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${templatePreviews[newDesignPreview].css || ''}</style></head><body>${templatePreviews[newDesignPreview].html || ''}</body></html>` : ''}
                                        className="dash-newdesign-preview-iframe"
                                        sandbox="allow-same-origin allow-scripts"
                                    />
                                </>
                            )}
                        </div>
                    </div>
                )}
            </main>

            {/* Projects tab styles */}
            <style>{`
                .dash-projects-empty {
                    text-align: center;
                    padding: 4rem 2rem;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 12px;
                }
                .dash-projects-empty h3 {
                    font-size: 18px;
                    font-weight: 600;
                    color: #333;
                    margin: 0;
                }
                .dash-projects-empty p {
                    color: #888;
                    font-size: 14px;
                    margin: 0;
                }
                .dash-projects-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
                    gap: 16px;
                    padding: 0 0 24px;
                }
                .dash-project-card {
                    background: white;
                    border: 1px solid #e5e5e5;
                    border-radius: 12px;
                    overflow: hidden;
                    transition: all 0.2s;
                    cursor: pointer;
                }
                .dash-project-card:hover {
                    border-color: #6366f1;
                    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.1);
                }
                .dash-project-thumb {
                    height: 140px;
                    background: #f8f9fa;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    position: relative;
                    cursor: pointer;
                }
                .dash-project-iframe {
                    width: 1280px;
                    height: 900px;
                    border: none;
                    pointer-events: none;
                    transform: scale(0.22);
                    transform-origin: top left;
                    position: absolute;
                    top: 0;
                    left: 0;
                }
                .dash-project-body {
                    padding: 12px 16px 8px;
                }
                .dash-project-name {
                    font-size: 15px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin: 0;
                    cursor: pointer;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .dash-project-name:hover {
                    color: #6366f1;
                }
                .dash-project-meta {
                    display: flex;
                    gap: 12px;
                    margin-top: 6px;
                    font-size: 12px;
                    color: #888;
                }
                .dash-project-actions {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 8px 16px 12px;
                }
                .dash-project-open {
                    background: #6366f1;
                    color: white;
                    border: none;
                    padding: 6px 20px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .dash-project-open:hover {
                    background: #4f46e5;
                }
                .dash-project-delete {
                    background: none;
                    border: 1px solid #e5e5e5;
                    padding: 6px 8px;
                    border-radius: 8px;
                    cursor: pointer;
                    color: #888;
                    transition: all 0.2s;
                }
                .dash-project-delete:hover {
                    border-color: #ef4444;
                    color: #ef4444;
                    background: rgba(239, 68, 68, 0.05);
                }

                /* ── Templates Tab ─────────────────────────────── */
                .dash-templates-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    padding: 0 0 24px;
                }
                .dash-template-card {
                    background: white;
                    border: 1px solid #e5e5e5;
                    border-radius: 12px;
                    overflow: hidden;
                    transition: all 0.2s;
                }
                .dash-template-card:hover {
                    border-color: #6366f1;
                    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.12);
                    transform: translateY(-2px);
                }
                .dash-template-thumb {
                    height: 200px;
                    background: #f4f4f5;
                    overflow: hidden;
                    position: relative;
                    cursor: pointer;
                }
                .dash-template-iframe {
                    width: 1280px;
                    height: 900px;
                    border: none;
                    pointer-events: none;
                    transform: scale(0.25);
                    transform-origin: top left;
                    position: absolute;
                    top: 0;
                    left: 0;
                }
                .dash-template-placeholder {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .dash-template-colors {
                    display: flex;
                    gap: 8px;
                }
                .dash-template-swatch {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    border: 2px solid white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
                }
                .dash-template-overlay {
                    position: absolute;
                    inset: 0;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: 500;
                    opacity: 0;
                    transition: opacity 0.2s;
                }
                .dash-template-thumb:hover .dash-template-overlay {
                    opacity: 1;
                }
                .dash-template-body {
                    padding: 16px;
                }
                .dash-template-category {
                    display: inline-block;
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    color: #6366f1;
                    background: rgba(99, 102, 241, 0.08);
                    padding: 3px 8px;
                    border-radius: 4px;
                    margin-bottom: 8px;
                }
                .dash-template-name {
                    font-size: 16px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin: 8px 0 6px;
                }
                .dash-template-desc {
                    font-size: 13px;
                    color: #666;
                    line-height: 1.5;
                    margin: 0 0 14px;
                }
                .dash-template-use-btn {
                    flex: 1;
                    background: #6366f1;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .dash-template-use-btn:hover {
                    background: #4f46e5;
                }
                .dash-template-preview-btn {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    background: transparent;
                    color: #9ca3af;
                    border: 1px solid #374151;
                    padding: 10px 16px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }
                .dash-template-preview-btn:hover {
                    color: #e5e7eb;
                    border-color: #6366f1;
                    background: rgba(99, 102, 241, 0.1);
                }

                /* New Design Modal */
                .dash-newdesign-modal {
                    background: #111827;
                    border-radius: 16px;
                    width: 95vw;
                    max-width: 1200px;
                    height: 90vh;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    border: 1px solid #1f2937;
                }
                .dash-newdesign-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 20px 24px;
                    border-bottom: 1px solid #1f2937;
                }
                .dash-newdesign-header h2 {
                    margin: 0;
                    font-size: 18px;
                    color: #f3f4f6;
                }
                .dash-newdesign-scratch {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 20px 24px;
                    margin: 16px 24px;
                    background: #1f2937;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 1px solid transparent;
                }
                .dash-newdesign-scratch:hover {
                    border-color: #6366f1;
                    background: rgba(99, 102, 241, 0.08);
                }
                .dash-newdesign-scratch-icon {
                    width: 48px;
                    height: 48px;
                    border-radius: 12px;
                    background: rgba(99, 102, 241, 0.15);
                    color: #6366f1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                }
                .dash-newdesign-templates {
                    flex: 1;
                    overflow-y: auto;
                    padding: 0 24px 24px;
                }
                .dash-newdesign-template-row {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 14px;
                    border-radius: 10px;
                    border: 1px solid #1f2937;
                    margin-bottom: 10px;
                    transition: border-color 0.2s;
                }
                .dash-newdesign-template-row:hover {
                    border-color: #374151;
                }
                .dash-newdesign-template-thumb {
                    width: 100px;
                    height: 64px;
                    border-radius: 6px;
                    overflow: hidden;
                    flex-shrink: 0;
                    position: relative;
                    background: #1f2937;
                }
                .dash-newdesign-template-thumb iframe {
                    width: 400%;
                    height: 400%;
                    border: none;
                    transform: scale(0.25);
                    transform-origin: top left;
                    pointer-events: none;
                }
                .dash-newdesign-template-info {
                    flex: 1;
                    min-width: 0;
                }
                .dash-newdesign-template-actions {
                    display: flex;
                    gap: 8px;
                    flex-shrink: 0;
                }
                .dash-newdesign-preview-iframe {
                    flex: 1;
                    border: none;
                    width: 100%;
                    min-height: 0;
                }

                /* Template Preview Modal */
                .dash-template-modal-overlay {
                    position: fixed;
                    inset: 0;
                    background: rgba(0,0,0,0.7);
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 24px;
                }
                .dash-template-modal {
                    background: white;
                    border-radius: 16px;
                    width: 100%;
                    max-width: 1200px;
                    height: 85vh;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                .dash-template-modal-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 16px 20px;
                    border-bottom: 1px solid #e5e5e5;
                }
                .dash-template-modal-header h3 {
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: #1a1a1a;
                }
                .dash-template-modal-actions {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                }
                .dash-template-modal-actions .dash-template-use-btn {
                    width: auto;
                    padding: 8px 20px;
                }
                .dash-template-modal-close {
                    background: none;
                    border: 1px solid #e5e5e5;
                    border-radius: 8px;
                    padding: 6px;
                    cursor: pointer;
                    color: #666;
                    display: flex;
                    align-items: center;
                    transition: all 0.2s;
                }
                .dash-template-modal-close:hover {
                    border-color: #999;
                    color: #333;
                }
                .dash-template-modal-iframe {
                    flex: 1;
                    width: 100%;
                    border: none;
                }
            `}</style>
        </div>
    );
};

export default Dashboard;
