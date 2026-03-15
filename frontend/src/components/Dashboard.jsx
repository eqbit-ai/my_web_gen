// src/components/Dashboard.jsx

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listProjects, getProject, deleteProject, listTemplateCatalog, getTemplateFull, listDeployedSites, deleteDeployedSite, connectDomain, getDomainStatus, disconnectDomain, listDnsRecords, addDnsRecord, deleteDnsRecord, getDnsNameservers } from '../services/api';

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
    const [transferModal, setTransferModal] = useState(null);
    const [transferSuccess, setTransferSuccess] = useState(null);
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
    const [disconnectConfirm, setDisconnectConfirm] = useState(null);
    const [dnsRecords, setDnsRecords] = useState({}); // { siteId: records[] }
    const [addRecordModal, setAddRecordModal] = useState(null); // site_id
    const [newRecord, setNewRecord] = useState({ name: '', type: 'A', value: '', ttl: 300 });
    const [addingRecord, setAddingRecord] = useState(false);
    const [deleteSiteConfirm, setDeleteSiteConfirm] = useState(null);
    const [newDesignModal, setNewDesignModal] = useState(false);
    const [newDesignPreview, setNewDesignPreview] = useState(null); // template id for preview inside new design modal
    const [nameservers, setNameservers] = useState({}); // { siteId: string[] }
    const domainPollRef = useRef(null);

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
        return expandedSections[`${domainId}-${section}`] !== false;
    };

    const handleTransferConfirm = (domainId) => {
        setTransferModal(null);
        setTransferSuccess(domainId);
        setTimeout(() => setTransferSuccess(null), 3000);
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
        } catch (e) { console.error('Failed to load DNS:', e); }
    };

    const loadNameservers = async (siteId) => {
        try {
            const data = await getDnsNameservers(siteId);
            setNameservers(prev => ({ ...prev, [siteId]: data.nameservers || [] }));
        } catch (e) { console.error('Failed to load nameservers:', e); }
    };

    const handleConnectDomain = async () => {
        if (!connectModal || !domainInput.trim()) return;
        setConnecting(true);
        try {
            const result = await connectDomain(connectModal, domainInput.trim());
            setConnectResult(result);
            loadDeployedSites();
        } catch (e) {
            alert(e.message || 'Failed to connect domain');
        }
        setConnecting(false);
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
        <div className="dashboard">
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
                            <h1 className="dash-domain-title">Domain Management</h1>
                        </div>

                        {domainsLoading ? (
                            <div className="dash-projects-empty"><p>Loading sites...</p></div>
                        ) : deployedSites.length === 0 ? (
                            <div className="dash-projects-empty">
                                <p>No deployed sites yet. Deploy a website first, then connect a domain.</p>
                            </div>
                        ) : (
                            <div className="dash-domain-list">
                                {deployedSites.map(site => (
                                    <div key={site.id} className="dash-domain-card">
                                        <div className="dash-domain-card-header">
                                            <div className="dash-domain-name-row">
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                                </svg>
                                                <h3 className="dash-domain-name">{site.domain || site.name}</h3>
                                                <span className={`dash-domain-status ${statusColor(site.domain_status || site.status)}`}>
                                                    {(site.domain_status || site.status || 'draft').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                                </span>
                                            </div>
                                            {site.url && (
                                                <a href={site.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 13, color: '#6366f1', marginTop: 4, display: 'block' }}>
                                                    {site.url}
                                                </a>
                                            )}
                                        </div>

                                        {/* Connect Domain button + Delete (if no domain yet) */}
                                        {!site.domain && (
                                            <div className="dash-domain-card-footer">
                                                {site.status === 'published' && (
                                                    <button className="dash-domain-add-btn" onClick={() => { setConnectModal(site.id); setConnectResult(null); setDomainInput(''); }}>
                                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                                                        </svg>
                                                        Connect Domain
                                                    </button>
                                                )}
                                                <button className="dash-domain-transfer-btn" style={{ color: '#ef4444', borderColor: '#ef4444' }}
                                                    onClick={() => setDeleteSiteConfirm(site.id)}>
                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /><path d="M10 11v6" /><path d="M14 11v6" />
                                                    </svg>
                                                    Delete Site
                                                </button>
                                            </div>
                                        )}

                                        {/* Domain info (if connected) */}
                                        {site.domain && (
                                            <>
                                                {/* DNS Records */}
                                                <div className="dash-domain-section">
                                                    <button className="dash-domain-section-toggle" onClick={() => { toggleSection(site.id, 'dns'); if (!dnsRecords[site.id]) loadDnsRecords(site.id); }}>
                                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                                                            style={{ transform: isSectionExpanded(site.id, 'dns') ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                                                            <polyline points="9 18 15 12 9 6" />
                                                        </svg>
                                                        DNS Records
                                                    </button>
                                                    {isSectionExpanded(site.id, 'dns') && (
                                                        <div className="dash-domain-section-content">
                                                            <div style={{ marginBottom: 8, textAlign: 'right' }}>
                                                                <button className="dash-domain-add-btn" style={{ fontSize: 12, padding: '4px 12px' }} onClick={() => setAddRecordModal(site.id)}>
                                                                    + Add Record
                                                                </button>
                                                            </div>
                                                            <table className="dash-domain-table">
                                                                <thead>
                                                                    <tr><th>Type</th><th>Name</th><th>Value</th><th>TTL</th><th></th></tr>
                                                                </thead>
                                                                <tbody>
                                                                    {(dnsRecords[site.id] || []).map((rec, i) => (
                                                                        <tr key={i}>
                                                                            <td><span className="dash-domain-type-badge">{rec.type}</span></td>
                                                                            <td>{rec.name}</td>
                                                                            <td className="dash-domain-value-cell">{rec.is_alias ? `ALIAS → ${rec.alias_target || rec.value}` : rec.value}</td>
                                                                            <td>{rec.ttl || '—'}</td>
                                                                            <td>
                                                                                {!rec.managed && (
                                                                                    <button className="dash-domain-edit-btn" title="Delete" onClick={() => setDeleteRecordConfirm({ siteId: site.id, record: rec })}
                                                                                        style={{ color: '#ef4444' }}>
                                                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                                                            <polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /><path d="M10 11v6" /><path d="M14 11v6" />
                                                                                        </svg>
                                                                                    </button>
                                                                                )}
                                                                                {rec.managed && <span style={{ fontSize: 10, color: '#9ca3af' }}>System</span>}
                                                                            </td>
                                                                        </tr>
                                                                    ))}
                                                                    {(dnsRecords[site.id] || []).length === 0 && (
                                                                        <tr><td colSpan="5" style={{ textAlign: 'center', color: '#9ca3af' }}>Loading records...</td></tr>
                                                                    )}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Nameservers */}
                                                <div className="dash-domain-section">
                                                    <button className="dash-domain-section-toggle" onClick={() => { toggleSection(site.id, 'ns'); if (!nameservers[site.id]) loadNameservers(site.id); }}>
                                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                                                            style={{ transform: isSectionExpanded(site.id, 'ns') ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                                                            <polyline points="9 18 15 12 9 6" />
                                                        </svg>
                                                        Nameservers
                                                    </button>
                                                    {isSectionExpanded(site.id, 'ns') && (
                                                        <div className="dash-domain-section-content">
                                                            <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 8 }}>
                                                                Update your domain's nameservers at your registrar to:
                                                            </p>
                                                            <div className="dash-domain-ns-list">
                                                                {(nameservers[site.id] || []).length > 0 ? (
                                                                    (nameservers[site.id]).map((ns, i) => (
                                                                        <div key={i} style={{ fontFamily: 'monospace', fontSize: 13, padding: '4px 0', color: '#e5e7eb' }}>{ns}</div>
                                                                    ))
                                                                ) : (
                                                                    <p style={{ fontSize: 12, color: '#9ca3af' }}>Loading nameservers...</p>
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Disconnect + Delete */}
                                                <div className="dash-domain-card-footer">
                                                    {site.domain_status === 'pending_validation' && (
                                                        <span style={{ fontSize: 12, color: '#f59e0b' }}>Waiting for nameserver propagation...</span>
                                                    )}
                                                    <button className="dash-domain-transfer-btn" style={{ color: '#ef4444', borderColor: '#ef4444' }}
                                                        onClick={() => setDisconnectConfirm(site.id)}>
                                                        Disconnect Domain
                                                    </button>
                                                    <button className="dash-domain-transfer-btn" style={{ color: '#ef4444', borderColor: '#ef4444' }}
                                                        onClick={() => setDeleteSiteConfirm(site.id)}>
                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                            <polyline points="3 6 5 6 21 6" /><path d="M19 6l-2 14H7L5 6" /><path d="M10 11v6" /><path d="M14 11v6" />
                                                        </svg>
                                                        Delete Site
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Connect Domain Modal */}
                {connectModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => { setConnectModal(null); setConnectResult(null); }}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
                            {!connectResult ? (
                                <>
                                    <h3 style={{ marginBottom: 8 }}>Connect Custom Domain</h3>
                                    <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 16 }}>
                                        Enter your domain name. We'll set up SSL and DNS automatically.
                                    </p>
                                    <input
                                        type="text"
                                        value={domainInput}
                                        onChange={e => setDomainInput(e.target.value)}
                                        placeholder="mybusiness.ae"
                                        style={{ width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 14, marginBottom: 16 }}
                                        disabled={connecting}
                                        onKeyDown={e => e.key === 'Enter' && handleConnectDomain()}
                                    />
                                    <div className="dash-domain-modal-actions">
                                        <button className="dash-domain-modal-cancel" onClick={() => setConnectModal(null)}>Cancel</button>
                                        <button className="dash-domain-modal-confirm" onClick={handleConnectDomain} disabled={connecting || !domainInput.trim()}>
                                            {connecting ? 'Setting up...' : 'Connect'}
                                        </button>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="dash-domain-modal-icon" style={{ background: '#ecfdf5' }}>
                                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                                    </div>
                                    <h3 style={{ marginBottom: 8 }}>Domain Connected!</h3>
                                    <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 16 }}>
                                        {connectResult.instructions}
                                    </p>
                                    {connectResult.nameservers && (
                                        <div style={{ background: '#f9fafb', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                                            <p style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: '#374151' }}>Set these nameservers at your registrar:</p>
                                            {connectResult.nameservers.map((ns, i) => (
                                                <div key={i} style={{ fontFamily: 'monospace', fontSize: 13, padding: '4px 0', color: '#1f2937' }}>{ns}</div>
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
