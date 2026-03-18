import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    Activity, Globe, AlertTriangle, Clock, Shield, ShoppingCart,
    Users, UserCheck, Receipt, Database, Timer, Coins,
    FileText, ClipboardList, Bell, Terminal, Server,
    TrendingUp, BarChart3, PieChart,
    ChevronDown, ChevronLeft, ChevronRight, ArrowLeft, LogOut, Menu,
} from 'lucide-react';

const NAV_SECTIONS = [
    {
        label: 'Dashboard',
        items: [
            { path: '/admin', label: 'Overview', icon: Activity, end: true },
        ],
    },
    {
        label: 'Sites & Generation',
        items: [
            { path: '/admin/sites', label: 'Sites', icon: Globe },
            { path: '/admin/generation-queue', label: 'Generation Queue', icon: Clock },
            { path: '/admin/failed-generations', label: 'Failed Generations', icon: AlertTriangle },
        ],
    },
    {
        label: 'Domains',
        items: [
            { path: '/admin/domains', label: 'External Domains', icon: Shield },
            { path: '/admin/domains-internal', label: 'Internal Domains', icon: ShoppingCart },
        ],
    },
    {
        label: 'Users',
        items: [
            { path: '/admin/users', label: 'User List', icon: Users },
            { path: '/admin/pending-approvals', label: 'Pending Approvals', icon: UserCheck },
        ],
    },
    {
        label: 'Tokens',
        items: [
            { path: '/admin/token-requests', label: 'Token Requests', icon: Coins },
            { path: '/admin/token-ledger', label: 'Transaction Ledger', icon: Receipt },
            { path: '/admin/token-pool', label: 'Token Pool', icon: Database },
            { path: '/admin/expiring-tokens', label: 'Expiring Tokens', icon: Timer },
        ],
    },
    {
        label: 'Operations',
        items: [
            { path: '/admin/templates', label: 'Templates', icon: FileText },
            { path: '/admin/audit-logs', label: 'Audit Logs', icon: ClipboardList },
            { path: '/admin/announcements', label: 'Announcements', icon: Bell },
            { path: '/admin/prompts', label: 'Prompt Manager', icon: Terminal },
            { path: '/admin/system', label: 'System Health', icon: Server },
        ],
    },
    {
        label: 'Analytics',
        items: [
            { path: '/admin/growth', label: 'Growth', icon: TrendingUp },
            { path: '/admin/generation-stats', label: 'Generation Stats', icon: BarChart3 },
            { path: '/admin/token-trends', label: 'Token Consumption', icon: PieChart },
        ],
    },
];

function buildBreadcrumbs(pathname) {
    const crumbs = [{ label: 'Admin', path: '/admin' }];
    for (const section of NAV_SECTIONS) {
        for (const item of section.items) {
            if (pathname === item.path || (pathname.startsWith(item.path + '/') && item.path !== '/admin')) {
                if (item.path !== '/admin') {
                    crumbs.push({ label: item.label, path: item.path });
                }
            }
        }
    }
    // Check for detail routes like /admin/users/123
    const segments = pathname.split('/').filter(Boolean);
    if (segments.length > 2) {
        const id = segments[segments.length - 1];
        if (!isNaN(id) || id.length > 5) {
            crumbs.push({ label: `#${id}`, path: pathname });
        }
    }
    return crumbs;
}

export default function AdminLayout() {
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const [openSections, setOpenSections] = useState(() => {
        const initial = {};
        NAV_SECTIONS.forEach((s, i) => { initial[i] = true; });
        return initial;
    });
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuth();

    const breadcrumbs = buildBreadcrumbs(location.pathname);

    const toggleSection = (idx) => {
        setOpenSections(prev => ({ ...prev, [idx]: !prev[idx] }));
    };

    const isItemActive = (item) => {
        if (item.end) return location.pathname === item.path;
        return location.pathname === item.path || location.pathname.startsWith(item.path + '/');
    };

    const activeSectionIdx = NAV_SECTIONS.findIndex(section =>
        section.items.some(item => isItemActive(item))
    );

    return (
        <div className="admin-page admin-layout">
            {/* Mobile overlay */}
            {mobileOpen && (
                <div className="admin-sidebar-overlay" onClick={() => setMobileOpen(false)} />
            )}

            {/* Sidebar */}
            <aside className={`admin-sidebar${collapsed ? ' collapsed' : ''}${mobileOpen ? ' mobile-open' : ''}`}>
                <div className="admin-sidebar-header">
                    {!collapsed && <h1 className="admin-sidebar-title">Admin Panel</h1>}
                    <button className="admin-sidebar-toggle" onClick={() => { setCollapsed(c => !c); setMobileOpen(false); }}>
                        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    </button>
                </div>

                <nav className="admin-sidebar-nav">
                    {NAV_SECTIONS.map((section, sIdx) => (
                        <div key={sIdx} className={`admin-sidebar-section${activeSectionIdx === sIdx ? ' section-active' : ''}`}>
                            {!collapsed && (
                                <button
                                    className="admin-sidebar-section-header"
                                    onClick={() => toggleSection(sIdx)}
                                >
                                    <span>{section.label}</span>
                                    <ChevronDown
                                        size={12}
                                        className={`admin-sidebar-chevron${openSections[sIdx] ? ' open' : ''}`}
                                    />
                                </button>
                            )}
                            {(collapsed || openSections[sIdx]) && section.items.map(item => {
                                const Icon = item.icon;
                                const active = isItemActive(item);
                                return (
                                    <NavLink
                                        key={item.path}
                                        to={item.path}
                                        end={item.end}
                                        className={`admin-sidebar-item${active ? ' active' : ''}`}
                                        onClick={() => setMobileOpen(false)}
                                    >
                                        <Icon size={16} />
                                        {!collapsed && <span>{item.label}</span>}
                                    </NavLink>
                                );
                            })}
                        </div>
                    ))}
                </nav>

                {/* Footer */}
                <div className="admin-sidebar-footer">
                    <button
                        className="admin-sidebar-footer-btn"
                        onClick={() => navigate('/dashboard')}
                    >
                        <ArrowLeft size={16} />
                        {!collapsed && <span>Back to App</span>}
                    </button>
                    <button
                        className="admin-sidebar-footer-btn admin-sidebar-footer-logout"
                        onClick={() => { logout(); navigate('/login'); }}
                    >
                        <LogOut size={16} />
                        {!collapsed && <span>Logout</span>}
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <div className={`admin-main${collapsed ? ' sidebar-collapsed' : ''}`}>
                {/* Header */}
                <header className="admin-header">
                    <div className="admin-header-left">
                        <button className="admin-mobile-menu" onClick={() => setMobileOpen(true)}>
                            <Menu size={18} />
                        </button>
                        <div className="admin-breadcrumbs">
                            {breadcrumbs.map((crumb, i) => (
                                <React.Fragment key={i}>
                                    {i > 0 && <span className="admin-breadcrumb-sep">/</span>}
                                    {i === breadcrumbs.length - 1 ? (
                                        <span className="admin-breadcrumb-active">{crumb.label}</span>
                                    ) : (
                                        <NavLink to={crumb.path} className="admin-breadcrumb">{crumb.label}</NavLink>
                                    )}
                                </React.Fragment>
                            ))}
                        </div>
                    </div>
                    <div className="admin-header-right">
                        <div className="admin-header-live">
                            <span className="admin-live-dot" />
                            Live
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div className="admin-content">
                    <Outlet />
                </div>
            </div>
        </div>
    );
}
