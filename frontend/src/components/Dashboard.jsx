// src/components/Dashboard.jsx

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listProjects, getProject, deleteProject, listTemplateCatalog, getTemplateFull } from '../services/api';

// CSS override injected into iframe srcDoc to force-show elements hidden by scroll animations
const IFRAME_VISIBILITY_FIX = `* { opacity: 1 !important; transform: none !important; transition: none !important; animation: none !important; } img { display: inline-block !important; }`;

const buildSrcDoc = (css, html, withScripts = false) =>
    `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${IFRAME_VISIBILITY_FIX}</style><style>${css || ''}</style></head><body>${html || ''}${withScripts ? '' : ''}</body></html>`;

const mockDomains = [
    {
        id: 1,
        name: 'mycompany.meydanfz.ae',
        status: 'active',
        nameservers: ['ns1.meydanfz.ae', 'ns2.meydanfz.ae'],
        dnsRecords: [
            { type: 'A', name: '@', value: '192.168.1.1', ttl: 3600 },
            { type: 'CNAME', name: 'www', value: 'mycompany.meydanfz.ae', ttl: 3600 },
            { type: 'MX', name: '@', value: 'mail.mycompany.meydanfz.ae', ttl: 3600 },
        ],
        address: {
            registrant: 'Salim Al Falasi',
            organization: 'My Company LLC',
            email: 'admin@mycompany.com',
            street: 'Meydan Free Zone, Building A',
            city: 'Dubai',
            country: 'UAE',
        },
    },
    {
        id: 2,
        name: 'brandsite.meydanfz.ae',
        status: 'pending',
        nameservers: ['ns1.meydanfz.ae', 'ns2.meydanfz.ae'],
        dnsRecords: [
            { type: 'A', name: '@', value: '10.0.0.5', ttl: 3600 },
            { type: 'TXT', name: '@', value: 'v=spf1 include:meydanfz.ae ~all', ttl: 3600 },
        ],
        address: {
            registrant: 'Jane Smith',
            organization: 'Brand Site LLC',
            email: 'info@brandsite.com',
            street: 'Meydan Free Zone, Building C',
            city: 'Dubai',
            country: 'UAE',
        },
    },
];

const Dashboard = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [prompt, setPrompt] = useState('');
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [activeTab, setActiveTab] = useState('home');
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

    const statusColor = (status) => {
        if (status === 'active') return 'green';
        if (status === 'pending') return 'yellow';
        return 'gray';
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    };

    return (
        <div className="dashboard">
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
                        onClick={() => navigate('/generator', { state: { newSession: true } })}
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
                                                <button className="dash-template-use-btn" onClick={() => handleUseTemplate(template.id)}>
                                                    Use Template
                                                </button>
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
                            <button className="dash-domain-add-btn">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                                </svg>
                                Add Domain
                            </button>
                        </div>

                        <div className="dash-domain-list">
                            {mockDomains.map(domain => (
                                <div key={domain.id} className="dash-domain-card">
                                    <div className="dash-domain-card-header">
                                        <div className="dash-domain-name-row">
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                            </svg>
                                            <h3 className="dash-domain-name">{domain.name}</h3>
                                            <span className={`dash-domain-status ${statusColor(domain.status)}`}>
                                                {domain.status.charAt(0).toUpperCase() + domain.status.slice(1)}
                                            </span>
                                        </div>
                                    </div>

                                    {/* DNS Records */}
                                    <div className="dash-domain-section">
                                        <button className="dash-domain-section-toggle" onClick={() => toggleSection(domain.id, 'dns')}>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                                                style={{ transform: isSectionExpanded(domain.id, 'dns') ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                                                <polyline points="9 18 15 12 9 6" />
                                            </svg>
                                            DNS Records
                                        </button>
                                        {isSectionExpanded(domain.id, 'dns') && (
                                            <div className="dash-domain-section-content">
                                                <table className="dash-domain-table">
                                                    <thead>
                                                        <tr><th>Type</th><th>Name</th><th>Value</th><th>TTL</th><th></th></tr>
                                                    </thead>
                                                    <tbody>
                                                        {domain.dnsRecords.map((rec, i) => (
                                                            <tr key={i}>
                                                                <td><span className="dash-domain-type-badge">{rec.type}</span></td>
                                                                <td>{rec.name}</td>
                                                                <td className="dash-domain-value-cell">{rec.value}</td>
                                                                <td>{rec.ttl}</td>
                                                                <td>
                                                                    <button className="dash-domain-edit-btn" title="Edit">
                                                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                                                                        </svg>
                                                                    </button>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        )}
                                    </div>

                                    {/* Nameservers */}
                                    <div className="dash-domain-section">
                                        <button className="dash-domain-section-toggle" onClick={() => toggleSection(domain.id, 'ns')}>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                                                style={{ transform: isSectionExpanded(domain.id, 'ns') ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                                                <polyline points="9 18 15 12 9 6" />
                                            </svg>
                                            Nameservers
                                        </button>
                                        {isSectionExpanded(domain.id, 'ns') && (
                                            <div className="dash-domain-section-content">
                                                <div className="dash-domain-ns-list">
                                                    {domain.nameservers.map((ns, i) => (
                                                        <div key={i} className="dash-domain-ns-item">
                                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                                <rect x="2" y="2" width="20" height="8" rx="2" ry="2" /><rect x="2" y="14" width="20" height="8" rx="2" ry="2" /><line x1="6" y1="6" x2="6.01" y2="6" /><line x1="6" y1="18" x2="6.01" y2="18" />
                                                            </svg>
                                                            <span>{ns}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Address Details */}
                                    <div className="dash-domain-section">
                                        <button className="dash-domain-section-toggle" onClick={() => toggleSection(domain.id, 'address')}>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                                                style={{ transform: isSectionExpanded(domain.id, 'address') ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                                                <polyline points="9 18 15 12 9 6" />
                                            </svg>
                                            Address Details
                                        </button>
                                        {isSectionExpanded(domain.id, 'address') && (
                                            <div className="dash-domain-section-content">
                                                <div className="dash-domain-address-grid">
                                                    {Object.entries(domain.address).map(([key, val]) => (
                                                        <div key={key} className="dash-domain-address-field">
                                                            <label>{key.charAt(0).toUpperCase() + key.slice(1)}</label>
                                                            <span>{val}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Transfer */}
                                    <div className="dash-domain-card-footer">
                                        {transferSuccess === domain.id && (
                                            <div className="dash-domain-success-toast">Transfer request submitted successfully!</div>
                                        )}
                                        <button className="dash-domain-transfer-btn" onClick={() => setTransferModal(domain.id)}>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <polyline points="17 1 21 5 17 9" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><polyline points="7 23 3 19 7 15" /><path d="M21 13v2a4 4 0 0 1-4 4H3" />
                                            </svg>
                                            Request Transfer
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Transfer Confirmation Modal */}
                {transferModal && (
                    <div className="dash-domain-modal-overlay" onClick={() => setTransferModal(null)}>
                        <div className="dash-domain-modal" onClick={e => e.stopPropagation()}>
                            <div className="dash-domain-modal-icon">
                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="17 1 21 5 17 9" /><path d="M3 11V9a4 4 0 0 1 4-4h14" /><polyline points="7 23 3 19 7 15" /><path d="M21 13v2a4 4 0 0 1-4 4H3" />
                                </svg>
                            </div>
                            <h3>Request Domain Transfer</h3>
                            <p>Request domain transfer? Our team will contact you to begin the process.</p>
                            <div className="dash-domain-modal-actions">
                                <button className="dash-domain-modal-cancel" onClick={() => setTransferModal(null)}>Cancel</button>
                                <button className="dash-domain-modal-confirm" onClick={() => handleTransferConfirm(transferModal)}>Confirm Transfer</button>
                            </div>
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
                    width: 100%;
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
