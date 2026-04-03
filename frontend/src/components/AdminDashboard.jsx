import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import StatusBadge from './admin/shared/StatusBadge';
import {
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend, PieChart, Pie, Cell,
} from 'recharts';
import {
    Users, Globe, Coins, Settings, BarChart3, Activity, Shield,
    Search, ChevronLeft, ChevronRight, RefreshCw, Download, Eye, Ban,
    Check, X, Plus, Edit3, Trash2, AlertTriangle, ArrowLeft, ExternalLink,
    Clock, Zap, Server, Database, TrendingUp, FileText, Bell, Terminal, Key, LogOut,
} from 'lucide-react';
import {
    adminGetStats, adminGetSystemInfo, adminResetCircuit,
    adminGetSites, adminGetGenerations, adminGetGenerationQueue, adminGetGenerationSuccessRate, adminRetryGeneration,
    adminGetDomains, adminGetDomainHealth,
    adminGetUsers, adminGetUserDetail, adminGetUserAudit, adminGetUserLogins,
    adminDisableUser, adminEnableUser, adminGrantTokens, adminResetPassword,
    adminVerifyLicence, adminImpersonateUser, adminBulkAction, adminExportUsers,
    adminGetTransactions, adminGetTokenPool, adminGetExpiringTokens, adminGrantTokensWithExpiry,
    adminGetTemplates, adminUpdateTemplate, adminGetAuditLogs,
    adminGetAnnouncements, adminCreateAnnouncement, adminUpdateAnnouncement, adminDeleteAnnouncement,
    adminGetPrompts, adminSavePrompt, adminPublishPrompt,
    adminGetGrowthAnalytics, adminGetGenerationStats, adminGetTokenConsumption,
    adminGetTokenRequests, adminReviewTokenRequest,
} from '../services/adminApi';

/* ─── Design Tokens ─── */
const T = {
    bg: '#0a0a0f',
    surface: '#12121a',
    surfaceHover: '#1a1a28',
    border: '#2a2a3a',
    text: '#e4e4e7',
    muted: '#71717a',
    accent: '#818cf8',
    accentHover: '#6366f1',
    success: '#34d399',
    warning: '#fbbf24',
    danger: '#f87171',
};

const PIE_COLORS = ['#818cf8', '#34d399', '#fbbf24', '#f87171', '#c084fc'];

/* ─── Reusable Styles ─── */
const cardStyle = {
    background: T.surface, borderRadius: 12, border: `1px solid ${T.border}`, padding: 24,
};
const btnStyle = {
    background: T.accent, color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px',
    cursor: 'pointer', fontSize: 13, fontWeight: 500, display: 'inline-flex', alignItems: 'center', gap: 6,
};
const btnDanger = { ...btnStyle, background: T.danger };
const btnGhost = {
    ...btnStyle, background: 'transparent', border: `1px solid ${T.border}`, color: T.text,
};
const inputStyle = {
    background: T.bg, border: `1px solid ${T.border}`, borderRadius: 8, padding: '8px 12px',
    color: T.text, fontSize: 13, outline: 'none', width: '100%',
};
const tableStyle = {
    width: '100%', borderCollapse: 'collapse', fontSize: 13,
};
const thStyle = {
    textAlign: 'left', padding: '10px 12px', borderBottom: `1px solid ${T.border}`,
    color: T.muted, fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em',
};
const tdStyle = {
    padding: '10px 12px', borderBottom: `1px solid ${T.border}`, color: T.text,
};
const trHover = {
    cursor: 'pointer',
};

/* ─── Helpers ─── */
function Spinner() {
    return (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
            <RefreshCw size={24} style={{ color: T.accent, animation: 'spin 1s linear infinite' }} />
            <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
        </div>
    );
}

function ErrorBanner({ message, onRetry }) {
    return (
        <div style={{ background: 'rgba(248,113,113,0.1)', border: `1px solid ${T.danger}`, borderRadius: 8, padding: '12px 16px', color: T.danger, display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <AlertTriangle size={16} />
            <span style={{ flex: 1 }}>{message}</span>
            {onRetry && <button style={btnStyle} onClick={onRetry}>Retry</button>}
        </div>
    );
}

function Pagination({ page, total, limit, onPageChange }) {
    const totalPages = Math.max(1, Math.ceil(total / limit));
    if (totalPages <= 1) return null;
    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginTop: 16, color: T.muted, fontSize: 13 }}>
            <button style={{ ...btnGhost, padding: '6px 10px' }} onClick={() => onPageChange(page - 1)} disabled={page <= 1}>
                <ChevronLeft size={14} />
            </button>
            <span>{page} / {totalPages}</span>
            <button style={{ ...btnGhost, padding: '6px 10px' }} onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}>
                <ChevronRight size={14} />
            </button>
        </div>
    );
}

function StatCard({ icon: Icon, label, value, color }) {
    return (
        <div style={{ ...cardStyle, display: 'flex', alignItems: 'center', gap: 16, flex: '1 1 180px', minWidth: 180 }}>
            <div style={{ width: 42, height: 42, borderRadius: 10, background: `${color || T.accent}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={20} style={{ color: color || T.accent }} />
            </div>
            <div>
                <div style={{ fontSize: 22, fontWeight: 700, color: T.text }}>{value ?? '—'}</div>
                <div style={{ fontSize: 12, color: T.muted }}>{label}</div>
            </div>
        </div>
    );
}

function SectionHeader({ title, children }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: T.text, margin: 0 }}>{title}</h2>
            <div style={{ display: 'flex', gap: 8 }}>{children}</div>
        </div>
    );
}

function useApi(fetcher, deps = []) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await fetcher();
            setData(result);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, deps);
    useEffect(() => { load(); }, [load]);
    return { data, loading, error, reload: load, setData };
}

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return d; }
}

/* ═══════════════════════════════════════════════════════════════════════════
   OVERVIEW PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
function OverviewPage() {
    const { data: stats, loading, error, reload } = useApi(() => adminGetStats());
    const { data: sysInfo, loading: sysLoading } = useApi(() => adminGetSystemInfo());
    const [resetting, setResetting] = useState(null);

    const handleResetCircuit = async (provider) => {
        setResetting(provider);
        try { await adminResetCircuit(provider); reload(); } catch {}
        setResetting(null);
    };

    if (loading) return <Spinner />;
    if (error) return <ErrorBanner message={error} onRetry={reload} />;

    const s = stats || {};
    return (
        <div>
            <SectionHeader title="Overview">
                <button style={btnGhost} onClick={reload}><RefreshCw size={14} /> Refresh</button>
            </SectionHeader>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
                <StatCard icon={Users} label="Total Users" value={s.total_users} color={T.accent} />
                <StatCard icon={Activity} label="Active (7d)" value={s.active_users_7d} color={T.success} />
                <StatCard icon={Zap} label="Total Generations" value={s.total_generations} color={T.warning} />
                <StatCard icon={Server} label="Active Sessions" value={s.active_sessions} color="#c084fc" />
                <StatCard icon={Database} label="Queue Depth" value={s.queue_depth} color={T.danger} />
            </div>

            {/* Circuit Breakers */}
            <div style={{ ...cardStyle, marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Circuit Breakers</h3>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    {Object.entries(s.circuit_breakers || {}).map(([provider, cb]) => (
                        <div key={provider} style={{ ...cardStyle, padding: 16, flex: '1 1 200px', background: T.bg }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                                <span style={{ fontWeight: 600, color: T.text }}>{provider}</span>
                                <StatusBadge status={typeof cb === 'string' ? cb : cb.state || 'unknown'} size="sm" />
                            </div>
                            <div style={{ fontSize: 12, color: T.muted, marginBottom: 8 }}>
                                Failures: {(typeof cb === 'object' ? cb.failure_count : 0) || 0}
                            </div>
                            <button
                                style={{ ...btnGhost, padding: '4px 10px', fontSize: 11 }}
                                onClick={() => handleResetCircuit(provider)}
                                disabled={resetting === provider}
                            >
                                {resetting === provider ? 'Resetting...' : 'Reset'}
                            </button>
                        </div>
                    ))}
                    {(!s.circuit_breakers || s.circuit_breakers.length === 0) && (
                        <span style={{ color: T.muted, fontSize: 13 }}>No circuit breaker data available</span>
                    )}
                </div>
            </div>

            {/* System Info */}
            <div style={cardStyle}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>System Info</h3>
                {sysLoading ? <Spinner /> : sysInfo ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 12 }}>
                        {Object.entries(sysInfo).filter(([k, v]) => typeof v !== 'object').map(([k, v]) => (
                            <div key={k} style={{ background: T.bg, borderRadius: 8, padding: 12, border: `1px solid ${T.border}` }}>
                                <div style={{ fontSize: 11, color: T.muted, marginBottom: 4, textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</div>
                                <div style={{ fontSize: 13, color: T.text, fontWeight: 500 }}>{String(v)}</div>
                            </div>
                        ))}
                        {Object.entries(sysInfo).filter(([k, v]) => typeof v === 'object' && v !== null).map(([k, v]) => (
                            <div key={k} style={{ background: T.bg, borderRadius: 8, padding: 12, border: `1px solid ${T.border}`, gridColumn: Object.keys(v).length > 3 ? 'span 2' : 'span 1' }}>
                                <div style={{ fontSize: 11, color: T.muted, marginBottom: 8, textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</div>
                                {Object.entries(v).map(([sk, sv]) => (
                                    <div key={sk} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '3px 0', borderBottom: `1px solid ${T.border}` }}>
                                        <span style={{ color: T.muted }}>{sk.replace(/_/g, ' ')}</span>
                                        <span style={{ color: T.text, fontWeight: 500, textAlign: 'right', maxWidth: '60%' }}>
                                            {typeof sv === 'object' && sv !== null
                                                ? Object.entries(sv).map(([dk, dv]) => (
                                                    <div key={dk} style={{ fontSize: 11 }}>
                                                        <span style={{ color: T.muted }}>{dk.replace(/_/g, ' ')}: </span>
                                                        <span>{typeof dv === 'object' ? JSON.stringify(dv) : String(dv)}</span>
                                                    </div>
                                                ))
                                                : String(sv)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                ) : <span style={{ color: T.muted }}>Unable to load system info</span>}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SITES & GENERATION PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
function SitesPage() {
    const [sitePage, setSitePage] = useState(1);
    const [genPage, setGenPage] = useState(1);
    const [genStatus, setGenStatus] = useState(null);
    const { data: sitesData, loading: sitesLoading, error: sitesError, reload: reloadSites } = useApi(() => adminGetSites(sitePage), [sitePage]);
    const { data: genData, loading: genLoading, error: genError, reload: reloadGen } = useApi(() => adminGetGenerations(genPage, 20, genStatus), [genPage, genStatus]);
    const { data: queue } = useApi(() => adminGetGenerationQueue());
    const { data: successRate } = useApi(() => adminGetGenerationSuccessRate());
    const [retrying, setRetrying] = useState(null);

    const handleRetry = async (logId) => {
        setRetrying(logId);
        try { await adminRetryGeneration(logId); reloadGen(); } catch {}
        setRetrying(null);
    };

    const sites = sitesData?.sites || sitesData?.items || [];
    const sitesTotal = sitesData?.total || sites.length;
    const gens = genData?.generations || genData?.items || [];
    const gensTotal = genData?.total || gens.length;
    const rateData = Array.isArray(successRate) ? successRate : successRate?.data || [];

    return (
        <div>
            <SectionHeader title="Sites & Generation">
                <button style={btnGhost} onClick={() => { reloadSites(); reloadGen(); }}><RefreshCw size={14} /> Refresh</button>
            </SectionHeader>

            {/* Queue Status */}
            {queue && (
                <div style={{ ...cardStyle, marginBottom: 24, display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                    <div><span style={{ color: T.muted, fontSize: 12 }}>Pending</span><div style={{ fontSize: 20, fontWeight: 700, color: T.warning }}>{queue.pending || 0}</div></div>
                    <div><span style={{ color: T.muted, fontSize: 12 }}>Processing</span><div style={{ fontSize: 20, fontWeight: 700, color: T.accent }}>{queue.processing || 0}</div></div>
                    <div><span style={{ color: T.muted, fontSize: 12 }}>Failed</span><div style={{ fontSize: 20, fontWeight: 700, color: T.danger }}>{queue.failed || 0}</div></div>
                </div>
            )}

            {/* Success Rate Chart */}
            {rateData.length > 0 && (
                <div style={{ ...cardStyle, marginBottom: 24 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Success Rate</h3>
                    <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={rateData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                            <Tooltip contentStyle={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, color: T.text }} />
                            <Area type="monotone" dataKey="rate" stroke={T.success} fill={`${T.success}30`} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Sites Table */}
            <div style={{ ...cardStyle, marginBottom: 24, overflowX: 'auto' }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Sites</h3>
                {sitesLoading ? <Spinner /> : sitesError ? <ErrorBanner message={sitesError} onRetry={reloadSites} /> : (
                    <>
                        <table style={tableStyle}>
                            <thead>
                                <tr>
                                    <th style={thStyle}>ID</th>
                                    <th style={thStyle}>User</th>
                                    <th style={thStyle}>Domain</th>
                                    <th style={thStyle}>Status</th>
                                    <th style={thStyle}>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sites.map(s => (
                                    <tr key={s.id} style={trHover} onMouseOver={e => e.currentTarget.style.background = T.surfaceHover} onFocus={e => e.currentTarget.style.background = T.surfaceHover} onMouseOut={e => e.currentTarget.style.background = ''} onBlur={e => e.currentTarget.style.background = ''}>
                                        <td style={tdStyle}>{s.id}</td>
                                        <td style={tdStyle}>{s.user_id || s.user_email || '—'}</td>
                                        <td style={tdStyle}>{s.domain || '—'}</td>
                                        <td style={tdStyle}><StatusBadge status={s.status} size="sm" /></td>
                                        <td style={tdStyle}>{formatDate(s.created_at)}</td>
                                    </tr>
                                ))}
                                {sites.length === 0 && <tr><td colSpan={5} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No sites found</td></tr>}
                            </tbody>
                        </table>
                        <Pagination page={sitePage} total={sitesTotal} limit={20} onPageChange={setSitePage} />
                    </>
                )}
            </div>

            {/* Generations Table */}
            <div style={{ ...cardStyle, overflowX: 'auto' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, margin: 0 }}>Generation Logs</h3>
                    <select
                        value={genStatus || ''}
                        onChange={e => { setGenStatus(e.target.value || null); setGenPage(1); }}
                        style={{ ...inputStyle, width: 'auto' }}
                    >
                        <option value="">All</option>
                        <option value="success">Success</option>
                        <option value="failed">Failed</option>
                        <option value="processing">Processing</option>
                    </select>
                </div>
                {genLoading ? <Spinner /> : genError ? <ErrorBanner message={genError} onRetry={reloadGen} /> : (
                    <>
                        <table style={tableStyle}>
                            <thead>
                                <tr>
                                    <th style={thStyle}>User</th>
                                    <th style={thStyle}>Prompt</th>
                                    <th style={thStyle}>Status</th>
                                    <th style={thStyle}>Pages</th>
                                    <th style={thStyle}>Duration</th>
                                    <th style={thStyle}>Tokens</th>
                                    <th style={thStyle}>Cost</th>
                                    <th style={thStyle}>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {gens.map(g => (
                                    <tr key={g.id} onMouseOver={e => e.currentTarget.style.background = T.surfaceHover} onFocus={e => e.currentTarget.style.background = T.surfaceHover} onMouseOut={e => e.currentTarget.style.background = ''} onBlur={e => e.currentTarget.style.background = ''}>
                                        <td style={tdStyle}><span style={{ fontSize: 12 }}>{g.user_email || `#${g.user_id}`}</span></td>
                                        <td style={{ ...tdStyle, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={g.prompt}>{g.prompt || '—'}</td>
                                        <td style={tdStyle}><StatusBadge status={g.status} size="sm" /></td>
                                        <td style={tdStyle}>{g.is_multipage ? `${g.page_count}p` : '1p'}</td>
                                        <td style={tdStyle}>{g.duration_ms ? `${(g.duration_ms / 1000).toFixed(1)}s` : '—'}</td>
                                        <td style={tdStyle}><span style={{ fontWeight: 600, fontSize: 12 }}>{g.tokens_consumed ? Number(g.tokens_consumed).toLocaleString() : '—'}</span></td>
                                        <td style={tdStyle}><span style={{ fontWeight: 600, color: '#f59e0b', fontSize: 12 }}>{g.estimated_cost ? `$${g.estimated_cost.toFixed(4)}` : '—'}</span></td>
                                        <td style={tdStyle}>{formatDate(g.created_at)}</td>
                                    </tr>
                                ))}
                                {gens.length === 0 && <tr><td colSpan={8} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No generations found</td></tr>}
                            </tbody>
                        </table>
                        <Pagination page={genPage} total={gensTotal} limit={20} onPageChange={setGenPage} />
                    </>
                )}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   DOMAINS & DNS PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
function DomainsPage() {
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState(null);
    const { data: domData, loading, error, reload } = useApi(() => adminGetDomains(page, 20, status), [page, status]);
    const { data: health } = useApi(() => adminGetDomainHealth());

    const domains = domData?.domains || domData?.items || [];
    const total = domData?.total || domains.length;

    return (
        <div>
            <SectionHeader title="Connected Domains">
                <button style={btnGhost} onClick={reload}><RefreshCw size={14} /> Refresh</button>
            </SectionHeader>

            {/* Domain Health */}
            {health && !health.error && (
                <div style={{ ...cardStyle, marginBottom: 24, display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                    <div>
                        <span style={{ color: T.muted, fontSize: 12 }}>Total Domains</span>
                        <div style={{ fontSize: 20, fontWeight: 700, color: T.text }}>{health.total_domains || 0}</div>
                    </div>
                    <div>
                        <span style={{ color: T.muted, fontSize: 12 }}>SSL Active</span>
                        <div style={{ fontSize: 20, fontWeight: 700, color: T.text }}>{health.ssl_active || 0}</div>
                    </div>
                    <div>
                        <span style={{ color: T.muted, fontSize: 12 }}>SSL None</span>
                        <div style={{ fontSize: 20, fontWeight: 700, color: T.text }}>{health.ssl_none || 0}</div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <select value={status || ''} onChange={e => { setStatus(e.target.value || null); setPage(1); }} style={{ ...inputStyle, width: 'auto' }}>
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="pending_validation">Pending Validation</option>
                    <option value="pending_deployment">Pending Deployment</option>
                </select>
            </div>

            {/* Domains Table */}
            <div style={{ ...cardStyle, overflowX: 'auto' }}>
                {loading ? <Spinner /> : error ? <ErrorBanner message={error} onRetry={reload} /> : (
                    <>
                        <table style={tableStyle}>
                            <thead>
                                <tr>
                                    <th style={thStyle}>Domain</th>
                                    <th style={thStyle}>Site</th>
                                    <th style={thStyle}>User</th>
                                    <th style={thStyle}>Status</th>
                                    <th style={thStyle}>SSL</th>
                                    <th style={thStyle}>CloudFront</th>
                                </tr>
                            </thead>
                            <tbody>
                                {domains.map(d => (
                                    <tr key={d.id} onMouseOver={e => e.currentTarget.style.background = T.surfaceHover} onFocus={e => e.currentTarget.style.background = T.surfaceHover} onMouseOut={e => e.currentTarget.style.background = ''} onBlur={e => e.currentTarget.style.background = ''}>
                                        <td style={tdStyle}>{d.domain || '—'}</td>
                                        <td style={tdStyle}>{d.site_name || '—'}</td>
                                        <td style={tdStyle}>{d.user_email || '—'}</td>
                                        <td style={tdStyle}><StatusBadge status={d.status} size="sm" /></td>
                                        <td style={tdStyle}><StatusBadge status={d.ssl_status || 'none'} size="sm" /></td>
                                        <td style={{ ...tdStyle, fontSize: '0.75rem' }}>{d.cloudfront_domain || '—'}</td>
                                    </tr>
                                ))}
                                {domains.length === 0 && <tr><td colSpan={6} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No connected domains</td></tr>}
                            </tbody>
                        </table>
                        <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
                    </>
                )}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   USER MANAGEMENT PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
function UsersPage() {
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [selectedUser, setSelectedUser] = useState(null);
    const [detailTab, setDetailTab] = useState('info');
    const [selectedIds, setSelectedIds] = useState([]);
    const [bulkAction, setBulkAction] = useState('');
    const [grantAmount, setGrantAmount] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    const { data: usersData, loading, error, reload } = useApi(() => adminGetUsers(page, 20, search), [page, search]);
    const [userDetail, setUserDetail] = useState(null);
    const [userAudit, setUserAudit] = useState(null);
    const [userLogins, setUserLogins] = useState(null);

    const users = usersData?.users || usersData?.items || [];
    const total = usersData?.total || users.length;

    const openDetail = async (userId) => {
        setSelectedUser(userId);
        setDetailTab('info');
        try {
            const detail = await adminGetUserDetail(userId);
            setUserDetail(detail);
            const audit = await adminGetUserAudit(userId);
            setUserAudit(audit);
            const logins = await adminGetUserLogins(userId);
            setUserLogins(logins);
        } catch {}
    };

    const closeDetail = () => { setSelectedUser(null); setUserDetail(null); setUserAudit(null); setUserLogins(null); };

    const handleAction = async (action, userId) => {
        setActionLoading(true);
        try {
            if (action === 'disable') await adminDisableUser(userId);
            else if (action === 'enable') await adminEnableUser(userId);
            else if (action === 'reset-password') await adminResetPassword(userId);
            else if (action === 'verify-licence') await adminVerifyLicence(userId, true);
            else if (action === 'impersonate') await adminImpersonateUser(userId);
            else if (action === 'grant' && grantAmount) {
                await adminGrantTokens(userId, parseInt(grantAmount));
                setGrantAmount('');
            }
            reload();
            if (selectedUser === userId) openDetail(userId);
        } catch {}
        setActionLoading(false);
    };

    const handleBulkAction = async () => {
        if (!bulkAction || selectedIds.length === 0) return;
        setActionLoading(true);
        try { await adminBulkAction(bulkAction, selectedIds); reload(); setSelectedIds([]); setBulkAction(''); } catch {}
        setActionLoading(false);
    };

    const handleExport = async () => {
        try {
            const blob = await adminExportUsers();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'users_export.csv'; a.click();
            URL.revokeObjectURL(url);
        } catch {}
    };

    const toggleSelect = (id) => {
        setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
    };

    const handleSearch = (e) => {
        e.preventDefault();
        setSearch(searchInput);
        setPage(1);
    };

    return (
        <div>
            <SectionHeader title="User Management">
                <button style={btnGhost} onClick={handleExport}><Download size={14} /> Export</button>
                <button style={btnGhost} onClick={reload}><RefreshCw size={14} /> Refresh</button>
            </SectionHeader>

            {/* Search */}
            <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <div style={{ position: 'relative', flex: 1 }}>
                    <Search size={14} style={{ position: 'absolute', left: 10, top: 10, color: T.muted }} />
                    <input
                        style={{ ...inputStyle, paddingLeft: 32 }}
                        placeholder="Search by name, email, or licence..."
                        value={searchInput}
                        onChange={e => setSearchInput(e.target.value)}
                    />
                </div>
                <button type="submit" style={btnStyle}>Search</button>
            </form>

            {/* Bulk Actions */}
            {selectedIds.length > 0 && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
                    <span style={{ color: T.muted, fontSize: 13 }}>{selectedIds.length} selected</span>
                    <select value={bulkAction} onChange={e => setBulkAction(e.target.value)} style={{ ...inputStyle, width: 'auto' }}>
                        <option value="">Bulk action...</option>
                        <option value="disable">Disable</option>
                        <option value="enable">Enable</option>
                        <option value="verify_licence">Verify Licence</option>
                    </select>
                    <button style={btnStyle} onClick={handleBulkAction} disabled={!bulkAction || actionLoading}>Apply</button>
                </div>
            )}

            {/* User Detail Panel */}
            {selectedUser && (
                <div style={{ ...cardStyle, marginBottom: 24, position: 'relative' }}>
                    <button style={{ ...btnGhost, position: 'absolute', top: 16, right: 16, padding: '4px 8px' }} onClick={closeDetail}><X size={14} /></button>
                    {userDetail ? (
                        <>
                            <div style={{ marginBottom: 16 }}>
                                <h3 style={{ fontSize: 16, fontWeight: 600, color: T.text, margin: 0 }}>{userDetail.company_name || userDetail.name || userDetail.email}</h3>
                                <span style={{ color: T.muted, fontSize: 13 }}>{userDetail.email}</span>
                                <div style={{ marginTop: 8 }}>
                                    <StatusBadge status={userDetail.is_active ? 'active' : 'disabled'} size="sm" />
                                </div>
                            </div>

                            {/* Detail Actions */}
                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
                                <button style={userDetail.is_active ? btnDanger : { ...btnStyle, background: T.success }} onClick={() => handleAction(userDetail.is_active ? 'disable' : 'enable', selectedUser)} disabled={actionLoading}>
                                    {userDetail.is_active ? <><Ban size={12} /> Disable</> : <><Check size={12} /> Enable</>}
                                </button>
                                <button style={btnGhost} onClick={() => handleAction('verify-licence', selectedUser)} disabled={actionLoading}><Check size={12} /> Verify Licence</button>
                                <button style={btnGhost} onClick={() => handleAction('reset-password', selectedUser)} disabled={actionLoading}><Key size={12} /> Reset Password</button>
                                <button style={btnGhost} onClick={() => handleAction('impersonate', selectedUser)} disabled={actionLoading}><Eye size={12} /> Impersonate</button>
                                <div style={{ display: 'flex', gap: 4 }}>
                                    <input style={{ ...inputStyle, width: 80 }} placeholder="Amount" type="number" value={grantAmount} onChange={e => setGrantAmount(e.target.value)} />
                                    <button style={btnStyle} onClick={() => handleAction('grant', selectedUser)} disabled={actionLoading || !grantAmount}><Coins size={12} /> Grant</button>
                                </div>
                            </div>

                            {/* Tabs */}
                            <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
                                {['info', 'logins', 'audit'].map(tab => (
                                    <button key={tab} onClick={() => setDetailTab(tab)}
                                        style={{ ...btnGhost, background: detailTab === tab ? T.accent : 'transparent', color: detailTab === tab ? '#fff' : T.muted, padding: '6px 14px', fontSize: 12, textTransform: 'capitalize' }}>
                                        {tab}
                                    </button>
                                ))}
                            </div>

                            {detailTab === 'info' && (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, fontSize: 13 }}>
                                    {Object.entries(userDetail).filter(([k]) => !['password', 'hashed_password'].includes(k)).map(([k, v]) => (
                                        <div key={k}>
                                            <span style={{ color: T.muted }}>{k.replace(/_/g, ' ')}: </span>
                                            <span style={{ color: T.text }}>{v === true ? 'Yes' : v === false ? 'No' : v === null ? '—' : String(v)}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {detailTab === 'logins' && (
                                <div style={{ overflowX: 'auto' }}>
                                    <table style={tableStyle}>
                                        <thead><tr><th style={thStyle}>Time</th><th style={thStyle}>IP</th><th style={thStyle}>User Agent</th></tr></thead>
                                        <tbody>
                                            {(userLogins?.items || userLogins?.logins || []).map((l, i) => (
                                                <tr key={i}><td style={tdStyle}>{formatDate(l.created_at || l.timestamp)}</td><td style={tdStyle}>{l.ip_address || l.ip || '—'}</td><td style={{ ...tdStyle, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.user_agent || '—'}</td></tr>
                                            ))}
                                            {(userLogins?.items || userLogins?.logins || []).length === 0 && <tr><td colSpan={3} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No login history</td></tr>}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                            {detailTab === 'audit' && (
                                <div style={{ overflowX: 'auto' }}>
                                    <table style={tableStyle}>
                                        <thead><tr><th style={thStyle}>Time</th><th style={thStyle}>Action</th><th style={thStyle}>Details</th></tr></thead>
                                        <tbody>
                                            {(userAudit?.items || userAudit?.logs || []).map((a, i) => (
                                                <tr key={i}><td style={tdStyle}>{formatDate(a.created_at || a.timestamp)}</td><td style={tdStyle}>{a.action || a.action_type}</td><td style={{ ...tdStyle, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.details || a.description || '—'}</td></tr>
                                            ))}
                                            {(userAudit?.items || userAudit?.logs || []).length === 0 && <tr><td colSpan={3} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No audit logs</td></tr>}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </>
                    ) : <Spinner />}
                </div>
            )}

            {/* Users Table */}
            <div style={{ ...cardStyle, overflowX: 'auto' }}>
                {loading ? <Spinner /> : error ? <ErrorBanner message={error} onRetry={reload} /> : (
                    <>
                        <table style={tableStyle}>
                            <thead>
                                <tr>
                                    <th style={{ ...thStyle, width: 40 }}>
                                        <input type="checkbox" onChange={e => setSelectedIds(e.target.checked ? users.map(u => u.id) : [])} checked={selectedIds.length === users.length && users.length > 0} />
                                    </th>
                                    <th style={thStyle}>Name / Company</th>
                                    <th style={thStyle}>Email</th>
                                    <th style={thStyle}>Licence</th>
                                    <th style={thStyle}>Tokens</th>
                                    <th style={thStyle}>Status</th>
                                    <th style={thStyle}>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map(u => (
                                    <tr key={u.id} style={trHover} onClick={() => openDetail(u.id)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') openDetail(u.id); }} tabIndex={0} onMouseOver={e => e.currentTarget.style.background = T.surfaceHover} onFocus={e => e.currentTarget.style.background = T.surfaceHover} onMouseOut={e => e.currentTarget.style.background = ''} onBlur={e => e.currentTarget.style.background = ''}>
                                        <td style={tdStyle} onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                                            <input type="checkbox" checked={selectedIds.includes(u.id)} onChange={() => toggleSelect(u.id)} />
                                        </td>
                                        <td style={tdStyle}>{u.company_name || u.name || '—'}</td>
                                        <td style={tdStyle}>{u.email}</td>
                                        <td style={tdStyle}>{u.license_number || u.licence_number || '—'}</td>
                                        <td style={tdStyle}>{u.token_balance ?? u.tokens ?? '—'}</td>
                                        <td style={tdStyle}><StatusBadge status={u.is_active !== false ? 'active' : 'disabled'} size="sm" /></td>
                                        <td style={tdStyle}>{formatDate(u.created_at)}</td>
                                    </tr>
                                ))}
                                {users.length === 0 && <tr><td colSpan={7} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No users found</td></tr>}
                            </tbody>
                        </table>
                        <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
                    </>
                )}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TOKENS & BILLING PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
function TokensPage() {
    const [page, setPage] = useState(1);
    const [txType, setTxType] = useState(null);
    const [txUserId, setTxUserId] = useState('');
    const { data: txData, loading, error, reload } = useApi(() => adminGetTransactions(page, 20, txUserId || null, txType), [page, txType, txUserId]);
    const { data: pool } = useApi(() => adminGetTokenPool());
    const { data: expiring } = useApi(() => adminGetExpiringTokens());

    // Grant form
    const [grantUserId, setGrantUserId] = useState('');
    const [grantAmount, setGrantAmount] = useState('');
    const [grantExpiry, setGrantExpiry] = useState('');
    const [grantReason, setGrantReason] = useState('');
    const [granting, setGranting] = useState(false);

    // Token requests
    const [tokenRequests, setTokenRequests] = useState([]);
    const [requestsLoading, setRequestsLoading] = useState(false);
    const [reviewingId, setReviewingId] = useState(null);

    const loadRequests = useCallback(async () => {
        setRequestsLoading(true);
        try {
            const res = await adminGetTokenRequests('pending');
            setTokenRequests(res?.requests || []);
        } catch {}
        setRequestsLoading(false);
    }, []);
    useEffect(() => { loadRequests(); }, [loadRequests]);

    const handleReview = async (reqId, action, amount) => {
        setReviewingId(reqId);
        try {
            await adminReviewTokenRequest(reqId, action, '', action === 'approve' ? amount : null);
            loadRequests();
            reload();
        } catch {}
        setReviewingId(null);
    };

    const transactions = txData?.transactions || txData?.items || [];
    const total = txData?.total || transactions.length;
    const expiringList = expiring?.tokens || expiring?.items || (Array.isArray(expiring) ? expiring : []);

    const handleGrant = async (e) => {
        e.preventDefault();
        if (!grantUserId || !grantAmount) return;
        setGranting(true);
        try {
            await adminGrantTokensWithExpiry(parseInt(grantUserId), parseInt(grantAmount), grantExpiry || null, grantReason);
            setGrantUserId(''); setGrantAmount(''); setGrantExpiry(''); setGrantReason('');
            reload();
        } catch {}
        setGranting(false);
    };

    return (
        <div>
            <SectionHeader title="Tokens & Billing">
                <button style={btnGhost} onClick={reload}><RefreshCw size={14} /> Refresh</button>
            </SectionHeader>

            {/* Token Pool */}
            {pool && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
                    <StatCard icon={Coins} label="Total Issued" value={pool.total_issued} color={T.accent} />
                    <StatCard icon={Coins} label="Total Used" value={pool.total_used} color={T.warning} />
                    <StatCard icon={Coins} label="Outstanding" value={pool.outstanding} color={T.success} />
                    <StatCard icon={AlertTriangle} label="Expiring Soon" value={pool.expiring_soon} color={T.danger} />
                </div>
            )}

            {/* Expiring Tokens Alert */}
            {expiringList.length > 0 && (
                <div style={{ background: 'rgba(251,191,36,0.1)', border: `1px solid ${T.warning}`, borderRadius: 8, padding: '12px 16px', marginBottom: 24, color: T.warning }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}><AlertTriangle size={16} /><strong>{expiringList.length} token grant(s) expiring soon</strong></div>
                    {expiringList.slice(0, 5).map((t, i) => (
                        <div key={i} style={{ fontSize: 12, marginLeft: 24 }}>User {t.user_id}: {t.amount} tokens, expires {formatDate(t.expires_at)}</div>
                    ))}
                </div>
            )}

            {/* Grant Tokens Form */}
            <div style={{ ...cardStyle, marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Grant Tokens</h3>
                <form onSubmit={handleGrant} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    <div>
                        <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>User ID</label>
                        <input style={{ ...inputStyle, width: 100 }} value={grantUserId} onChange={e => setGrantUserId(e.target.value)} required />
                    </div>
                    <div>
                        <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Amount</label>
                        <input style={{ ...inputStyle, width: 100 }} type="number" value={grantAmount} onChange={e => setGrantAmount(e.target.value)} required />
                    </div>
                    <div>
                        <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Expiry (optional)</label>
                        <input style={{ ...inputStyle, width: 160 }} type="date" value={grantExpiry} onChange={e => setGrantExpiry(e.target.value)} />
                    </div>
                    <div>
                        <label style={{ fontSize: 11, color: T.muted, display: 'block', marginBottom: 4 }}>Reason</label>
                        <input style={{ ...inputStyle, width: 180 }} value={grantReason} onChange={e => setGrantReason(e.target.value)} placeholder="Optional" />
                    </div>
                    <button type="submit" style={btnStyle} disabled={granting}><Plus size={14} /> {granting ? 'Granting...' : 'Grant'}</button>
                </form>
            </div>

            {/* Token Requests from Users */}
            {tokenRequests.length > 0 && (
                <div style={{ ...cardStyle, marginBottom: 24, borderColor: T.warning, borderWidth: 1 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, color: T.warning, marginTop: 0, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Bell size={16} /> Token Requests ({tokenRequests.length} pending)
                    </h3>
                    {tokenRequests.map(r => (
                        <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: `1px solid ${T.border}`, gap: 16 }}>
                            <div style={{ flex: 1 }}>
                                <div style={{ color: T.text, fontSize: 13, fontWeight: 600 }}>{r.user_name || r.user_email}</div>
                                <div style={{ color: T.muted, fontSize: 12 }}>
                                    Requesting <span style={{ color: T.accent, fontWeight: 600 }}>{(r.amount || 0).toLocaleString()}</span> tokens
                                    {r.reason && <> — {r.reason}</>}
                                </div>
                                <div style={{ color: T.muted, fontSize: 11 }}>
                                    Current balance: {(r.user_balance || 0).toLocaleString()} | {formatDate(r.created_at)}
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: 6 }}>
                                <button
                                    onClick={() => handleReview(r.id, 'approve', r.amount)}
                                    disabled={reviewingId === r.id}
                                    style={{ ...btnStyle, background: T.success, color: '#000', padding: '6px 12px', fontSize: 12 }}
                                >
                                    <Check size={12} /> Approve
                                </button>
                                <button
                                    onClick={() => handleReview(r.id, 'reject')}
                                    disabled={reviewingId === r.id}
                                    style={{ ...btnGhost, border: `1px solid ${T.danger}`, color: T.danger, padding: '6px 12px', fontSize: 12 }}
                                >
                                    <X size={12} /> Reject
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Filters */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <select value={txType || ''} onChange={e => { setTxType(e.target.value || null); setPage(1); }} style={{ ...inputStyle, width: 'auto' }}>
                    <option value="">All Types</option>
                    <option value="grant">Grant</option>
                    <option value="consume">Consume</option>
                    <option value="refund">Refund</option>
                    <option value="expire">Expire</option>
                </select>
                <input style={{ ...inputStyle, width: 120 }} placeholder="User ID" value={txUserId} onChange={e => { setTxUserId(e.target.value); setPage(1); }} />
            </div>

            {/* Transactions Table */}
            <div style={{ ...cardStyle, overflowX: 'auto' }}>
                {loading ? <Spinner /> : error ? <ErrorBanner message={error} onRetry={reload} /> : (
                    <>
                        <table style={tableStyle}>
                            <thead>
                                <tr>
                                    <th style={thStyle}>ID</th>
                                    <th style={thStyle}>User</th>
                                    <th style={thStyle}>Type</th>
                                    <th style={thStyle}>Amount</th>
                                    <th style={thStyle}>Reason</th>
                                    <th style={thStyle}>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {transactions.map(t => (
                                    <tr key={t.id} onMouseOver={e => e.currentTarget.style.background = T.surfaceHover} onFocus={e => e.currentTarget.style.background = T.surfaceHover} onMouseOut={e => e.currentTarget.style.background = ''} onBlur={e => e.currentTarget.style.background = ''}>
                                        <td style={tdStyle}>{t.id}</td>
                                        <td style={tdStyle}>{t.user_id || '—'}</td>
                                        <td style={tdStyle}><StatusBadge status={t.type || t.transaction_type} size="sm" /></td>
                                        <td style={{ ...tdStyle, fontWeight: 600, color: (t.type === 'grant' || t.type === 'refund') ? T.success : T.danger }}>
                                            {(t.type === 'grant' || t.type === 'refund') ? '+' : '-'}{t.amount}
                                        </td>
                                        <td style={tdStyle}>{t.reason || '—'}</td>
                                        <td style={tdStyle}>{formatDate(t.created_at)}</td>
                                    </tr>
                                ))}
                                {transactions.length === 0 && <tr><td colSpan={6} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No transactions found</td></tr>}
                            </tbody>
                        </table>
                        <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
                    </>
                )}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   PLATFORM OPERATIONS PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
function OperationsPage() {
    const [activeTab, setActiveTab] = useState('templates');

    return (
        <div>
            <SectionHeader title="Platform Operations" />
            <div style={{ display: 'flex', gap: 4, marginBottom: 24, flexWrap: 'wrap' }}>
                {['templates', 'audit', 'announcements', 'prompts', 'system'].map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)}
                        style={{ ...btnGhost, background: activeTab === tab ? T.accent : 'transparent', color: activeTab === tab ? '#fff' : T.muted, padding: '8px 16px', fontSize: 13, textTransform: 'capitalize' }}>
                        {tab}
                    </button>
                ))}
            </div>
            {activeTab === 'templates' && <TemplatesTab />}
            {activeTab === 'audit' && <AuditTab />}
            {activeTab === 'announcements' && <AnnouncementsTab />}
            {activeTab === 'prompts' && <PromptsTab />}
            {activeTab === 'system' && <SystemTab />}
        </div>
    );
}

function TemplatesTab() {
    const { data, loading, error, reload } = useApi(() => adminGetTemplates());
    const [editing, setEditing] = useState(null);
    const [editData, setEditData] = useState({});
    const [saving, setSaving] = useState(false);

    const templates = data?.templates || data?.items || (Array.isArray(data) ? data : []);

    const handleSave = async () => {
        if (!editing) return;
        setSaving(true);
        try { await adminUpdateTemplate(editing, editData); setEditing(null); reload(); } catch {}
        setSaving(false);
    };

    if (loading) return <Spinner />;
    if (error) return <ErrorBanner message={error} onRetry={reload} />;

    return (
        <div style={cardStyle}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Templates ({templates.length})</h3>
            <div style={{ overflowX: 'auto' }}>
                <table style={tableStyle}>
                    <thead>
                        <tr>
                            <th style={thStyle}>Name</th>
                            <th style={thStyle}>Category</th>
                            <th style={thStyle}>Status</th>
                            <th style={thStyle}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {templates.map(t => (
                            <tr key={t.id} onMouseOver={e => e.currentTarget.style.background = T.surfaceHover} onFocus={e => e.currentTarget.style.background = T.surfaceHover} onMouseOut={e => e.currentTarget.style.background = ''} onBlur={e => e.currentTarget.style.background = ''}>
                                <td style={tdStyle}>
                                    {editing === t.id ? (
                                        <input style={inputStyle} value={editData.name || ''} onChange={e => setEditData({ ...editData, name: e.target.value })} />
                                    ) : t.name || t.title}
                                </td>
                                <td style={tdStyle}>
                                    {editing === t.id ? (
                                        <input style={inputStyle} value={editData.category || ''} onChange={e => setEditData({ ...editData, category: e.target.value })} />
                                    ) : t.category || '—'}
                                </td>
                                <td style={tdStyle}><StatusBadge status={t.status || 'active'} size="sm" /></td>
                                <td style={tdStyle}>
                                    {editing === t.id ? (
                                        <div style={{ display: 'flex', gap: 4 }}>
                                            <button style={{ ...btnStyle, padding: '4px 10px', fontSize: 11 }} onClick={handleSave} disabled={saving}><Check size={12} /></button>
                                            <button style={{ ...btnGhost, padding: '4px 10px', fontSize: 11 }} onClick={() => setEditing(null)}><X size={12} /></button>
                                        </div>
                                    ) : (
                                        <button style={{ ...btnGhost, padding: '4px 10px', fontSize: 11 }} onClick={() => { setEditing(t.id); setEditData({ name: t.name || t.title, category: t.category }); }}>
                                            <Edit3 size={12} /> Edit
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                        {templates.length === 0 && <tr><td colSpan={4} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No templates</td></tr>}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function AuditTab() {
    const [page, setPage] = useState(1);
    const [actionType, setActionType] = useState(null);
    const { data, loading, error, reload } = useApi(() => adminGetAuditLogs(page, 20, actionType), [page, actionType]);

    const logs = data?.logs || data?.items || [];
    const total = data?.total || logs.length;

    return (
        <div style={{ ...cardStyle, overflowX: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, margin: 0 }}>Audit Logs</h3>
                <select value={actionType || ''} onChange={e => { setActionType(e.target.value || null); setPage(1); }} style={{ ...inputStyle, width: 'auto' }}>
                    <option value="">All Actions</option>
                    <option value="login">Login</option>
                    <option value="generate">Generate</option>
                    <option value="edit">Edit</option>
                    <option value="admin">Admin</option>
                </select>
            </div>
            {loading ? <Spinner /> : error ? <ErrorBanner message={error} onRetry={reload} /> : (
                <>
                    <table style={tableStyle}>
                        <thead>
                            <tr>
                                <th style={thStyle}>Time</th>
                                <th style={thStyle}>User</th>
                                <th style={thStyle}>Action</th>
                                <th style={thStyle}>Details</th>
                                <th style={thStyle}>IP</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((l, i) => (
                                <tr key={l.id || i} onMouseOver={e => e.currentTarget.style.background = T.surfaceHover} onFocus={e => e.currentTarget.style.background = T.surfaceHover} onMouseOut={e => e.currentTarget.style.background = ''} onBlur={e => e.currentTarget.style.background = ''}>
                                    <td style={tdStyle}>{formatDate(l.created_at || l.timestamp)}</td>
                                    <td style={tdStyle}>{l.user_id || l.user_email || '—'}</td>
                                    <td style={tdStyle}>{l.action || l.action_type}</td>
                                    <td style={{ ...tdStyle, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.details || l.description || '—'}</td>
                                    <td style={tdStyle}>{l.ip_address || '—'}</td>
                                </tr>
                            ))}
                            {logs.length === 0 && <tr><td colSpan={5} style={{ ...tdStyle, textAlign: 'center', color: T.muted }}>No logs found</td></tr>}
                        </tbody>
                    </table>
                    <Pagination page={page} total={total} limit={20} onPageChange={setPage} />
                </>
            )}
        </div>
    );
}

function AnnouncementsTab() {
    const { data, loading, error, reload } = useApi(() => adminGetAnnouncements());
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [form, setForm] = useState({ title: '', content: '', type: 'info', active: true });
    const [saving, setSaving] = useState(false);

    const announcements = data?.announcements || data?.items || (Array.isArray(data) ? data : []);

    const handleSave = async () => {
        setSaving(true);
        try {
            if (editingId) await adminUpdateAnnouncement(editingId, form);
            else await adminCreateAnnouncement(form);
            setShowForm(false); setEditingId(null); setForm({ title: '', content: '', type: 'info', active: true });
            reload();
        } catch {}
        setSaving(false);
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Delete this announcement?')) return;
        try { await adminDeleteAnnouncement(id); reload(); } catch {}
    };

    const startEdit = (a) => {
        setEditingId(a.id);
        setForm({ title: a.title, content: a.content, type: a.type || 'info', active: a.active !== false });
        setShowForm(true);
    };

    if (loading) return <Spinner />;
    if (error) return <ErrorBanner message={error} onRetry={reload} />;

    return (
        <div>
            {showForm && (
                <div style={{ ...cardStyle, marginBottom: 24 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>{editingId ? 'Edit' : 'New'} Announcement</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <input style={inputStyle} placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
                        <textarea style={{ ...inputStyle, minHeight: 80, resize: 'vertical' }} placeholder="Content" value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} />
                        <div style={{ display: 'flex', gap: 8 }}>
                            <select value={form.type} onChange={e => setForm({ ...form, type: e.target.value })} style={{ ...inputStyle, width: 'auto' }}>
                                <option value="info">Info</option>
                                <option value="warning">Warning</option>
                                <option value="success">Success</option>
                                <option value="error">Error</option>
                            </select>
                            <label style={{ display: 'flex', alignItems: 'center', gap: 4, color: T.muted, fontSize: 13 }}>
                                <input type="checkbox" checked={form.active} onChange={e => setForm({ ...form, active: e.target.checked })} /> Active
                            </label>
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button style={btnStyle} onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
                            <button style={btnGhost} onClick={() => { setShowForm(false); setEditingId(null); }}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            <div style={cardStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, margin: 0 }}>Announcements ({announcements.length})</h3>
                    <button style={btnStyle} onClick={() => { setShowForm(true); setEditingId(null); setForm({ title: '', content: '', type: 'info', active: true }); }}><Plus size={14} /> New</button>
                </div>
                {announcements.map(a => (
                    <div key={a.id} style={{ background: T.bg, borderRadius: 8, padding: 16, marginBottom: 12, border: `1px solid ${T.border}` }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <strong style={{ color: T.text }}>{a.title}</strong>
                                <StatusBadge status={a.active !== false ? 'active' : 'inactive'} size="sm" />
                                <StatusBadge status={a.type || 'info'} size="sm" />
                            </div>
                            <div style={{ display: 'flex', gap: 4 }}>
                                <button style={{ ...btnGhost, padding: '4px 8px' }} onClick={() => startEdit(a)}><Edit3 size={12} /></button>
                                <button style={{ ...btnGhost, padding: '4px 8px', color: T.danger }} onClick={() => handleDelete(a.id)}><Trash2 size={12} /></button>
                            </div>
                        </div>
                        <p style={{ color: T.muted, fontSize: 13, margin: 0 }}>{a.content}</p>
                    </div>
                ))}
                {announcements.length === 0 && <span style={{ color: T.muted, fontSize: 13 }}>No announcements</span>}
            </div>
        </div>
    );
}

function PromptsTab() {
    const { data, loading, error, reload } = useApi(() => adminGetPrompts());
    const [editingKey, setEditingKey] = useState(null);
    const [editContent, setEditContent] = useState('');
    const [saving, setSaving] = useState(false);

    const prompts = Array.isArray(data) ? data : Array.isArray(data?.prompts) ? data.prompts : Array.isArray(data?.items) ? data.items : typeof data === 'object' && data !== null ? Object.entries(data).map(([key, val]) => ({ key, ...val })) : [];

    const handleSave = async () => {
        if (!editingKey) return;
        setSaving(true);
        try { await adminSavePrompt(editingKey, editContent); setEditingKey(null); reload(); } catch {}
        setSaving(false);
    };

    const handlePublish = async (key, version) => {
        try { await adminPublishPrompt(key, version); reload(); } catch {}
    };

    if (loading) return <Spinner />;
    if (error) return <ErrorBanner message={error} onRetry={reload} />;

    return (
        <div>
            {editingKey && (
                <div style={{ ...cardStyle, marginBottom: 24 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 12 }}>Editing: {editingKey}</h3>
                    <textarea style={{ ...inputStyle, minHeight: 200, fontFamily: 'monospace', fontSize: 12, resize: 'vertical' }} value={editContent} onChange={e => setEditContent(e.target.value)} />
                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                        <button style={btnStyle} onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Draft'}</button>
                        <button style={btnGhost} onClick={() => setEditingKey(null)}>Cancel</button>
                    </div>
                </div>
            )}

            <div style={cardStyle}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Prompt Versions</h3>
                {prompts.map((p, i) => (
                    <div key={p.key || i} style={{ background: T.bg, borderRadius: 8, padding: 16, marginBottom: 12, border: `1px solid ${T.border}` }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <strong style={{ color: T.text }}>{p.key || p.name}</strong>
                                <span style={{ color: T.muted, fontSize: 12, marginLeft: 8 }}>v{p.version || p.published_version || 1}</span>
                                {p.draft_version && <span style={{ color: T.warning, fontSize: 12, marginLeft: 8 }}>(draft v{p.draft_version})</span>}
                            </div>
                            <div style={{ display: 'flex', gap: 4 }}>
                                <button style={{ ...btnGhost, padding: '4px 10px', fontSize: 11 }} onClick={() => { setEditingKey(p.key || p.name); setEditContent(p.content || p.text || ''); }}>
                                    <Edit3 size={12} /> Edit
                                </button>
                                {p.draft_version && (
                                    <button style={{ ...btnStyle, padding: '4px 10px', fontSize: 11, background: T.success }} onClick={() => handlePublish(p.key || p.name, p.draft_version)}>
                                        <Check size={12} /> Publish
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
                {prompts.length === 0 && <span style={{ color: T.muted, fontSize: 13 }}>No prompts configured</span>}
            </div>
        </div>
    );
}

function SystemTab() {
    const { data: sysInfo, loading, error, reload } = useApi(() => adminGetSystemInfo());
    const [resetting, setResetting] = useState(null);

    const handleResetCircuit = async (provider) => {
        setResetting(provider);
        try { await adminResetCircuit(provider); reload(); } catch {}
        setResetting(null);
    };

    if (loading) return <Spinner />;
    if (error) return <ErrorBanner message={error} onRetry={reload} />;

    return (
        <div>
            <div style={cardStyle}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>System Info</h3>
                {sysInfo ? (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 12 }}>
                        {Object.entries(sysInfo).filter(([, v]) => typeof v !== 'object').map(([k, v]) => (
                            <div key={k} style={{ background: T.bg, borderRadius: 8, padding: 12, border: `1px solid ${T.border}` }}>
                                <div style={{ fontSize: 11, color: T.muted, marginBottom: 4, textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</div>
                                <div style={{ fontSize: 13, color: T.text, fontWeight: 500 }}>{String(v)}</div>
                            </div>
                        ))}
                        {Object.entries(sysInfo).filter(([, v]) => typeof v === 'object' && v !== null).map(([k, v]) => (
                            <div key={k} style={{ background: T.bg, borderRadius: 8, padding: 12, border: `1px solid ${T.border}`, gridColumn: Object.keys(v).length > 3 ? 'span 2' : 'span 1' }}>
                                <div style={{ fontSize: 11, color: T.muted, marginBottom: 8, textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</div>
                                {Object.entries(v).map(([sk, sv]) => (
                                    <div key={sk} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '3px 0', borderBottom: `1px solid ${T.border}` }}>
                                        <span style={{ color: T.muted }}>{sk.replace(/_/g, ' ')}</span>
                                        <span style={{ color: T.text, fontWeight: 500 }}>{typeof sv === 'object' ? JSON.stringify(sv) : String(sv)}</span>
                                    </div>
                                ))}
                            </div>
                        ))}
                    </div>
                ) : <span style={{ color: T.muted }}>No system info available</span>}
            </div>

            <div style={{ ...cardStyle, marginTop: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Circuit Breaker Controls</h3>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {['openai', 'anthropic'].map(provider => (
                        <button key={provider} style={btnGhost} onClick={() => handleResetCircuit(provider)} disabled={resetting === provider}>
                            <RefreshCw size={14} /> Reset {provider}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   ANALYTICS & REPORTING PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
function AnalyticsPage() {
    const [days, setDays] = useState(30);
    const { data: growth, loading: gLoading } = useApi(() => adminGetGrowthAnalytics(days), [days]);
    const { data: genStats, loading: gsLoading } = useApi(() => adminGetGenerationStats(days), [days]);
    const { data: tokenData, loading: tLoading } = useApi(() => adminGetTokenConsumption(days), [days]);

    const growthData = growth?.data || growth?.items || (Array.isArray(growth) ? growth : []);
    const genData = genStats?.data || genStats?.items || (Array.isArray(genStats) ? genStats : []);
    const tokenChartData = tokenData?.data || tokenData?.items || (Array.isArray(tokenData) ? tokenData : []);

    const chartTooltipStyle = { background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, color: T.text };

    return (
        <div>
            <SectionHeader title="Analytics & Reporting">
                <div style={{ display: 'flex', gap: 4 }}>
                    {[7, 30, 90].map(d => (
                        <button key={d} onClick={() => setDays(d)}
                            style={{ ...btnGhost, background: days === d ? T.accent : 'transparent', color: days === d ? '#fff' : T.muted, padding: '6px 14px', fontSize: 12 }}>
                            {d}d
                        </button>
                    ))}
                </div>
            </SectionHeader>

            {/* User Growth */}
            <div style={{ ...cardStyle, marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>User Growth</h3>
                {gLoading ? <Spinner /> : growthData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={growthData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                            <Tooltip contentStyle={chartTooltipStyle} />
                            <Legend />
                            <Area type="monotone" dataKey="total_users" name="Total Users" stroke={T.accent} fill={`${T.accent}30`} />
                            <Area type="monotone" dataKey="new_users" name="New Users" stroke={T.success} fill={`${T.success}30`} />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : <span style={{ color: T.muted, fontSize: 13 }}>No growth data available for this period</span>}
            </div>

            {/* Generation Stats */}
            <div style={{ ...cardStyle, marginBottom: 24 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Generation Stats</h3>
                {gsLoading ? <Spinner /> : genData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={genData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                            <Tooltip contentStyle={chartTooltipStyle} />
                            <Legend />
                            <Bar dataKey="success" name="Success" fill={T.success} radius={[4, 4, 0, 0]} />
                            <Bar dataKey="failed" name="Failed" fill={T.danger} radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                ) : <span style={{ color: T.muted, fontSize: 13 }}>No generation data available for this period</span>}
            </div>

            {/* Token Consumption */}
            <div style={cardStyle}>
                <h3 style={{ fontSize: 14, fontWeight: 600, color: T.text, marginTop: 0, marginBottom: 16 }}>Token Consumption</h3>
                {tLoading ? <Spinner /> : tokenChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={tokenChartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                            <Tooltip contentStyle={chartTooltipStyle} />
                            <Legend />
                            <Area type="monotone" dataKey="consumed" name="Consumed" stroke={T.warning} fill={`${T.warning}30`} />
                            <Area type="monotone" dataKey="granted" name="Granted" stroke={T.success} fill={`${T.success}30`} />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : <span style={{ color: T.muted, fontSize: 13 }}>No token data available for this period</span>}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   SIDEBAR NAV
   ═══════════════════════════════════════════════════════════════════════════ */
const NAV_ITEMS = [
    { path: '/admin', label: 'Overview', icon: Activity, exact: true },
    { path: '/admin/sites', label: 'Sites & Generation', icon: Globe },
    { path: '/admin/domains', label: 'Domains & DNS', icon: Shield },
    { path: '/admin/users', label: 'User Management', icon: Users },
    { path: '/admin/tokens', label: 'Tokens & Billing', icon: Coins },
    { path: '/admin/operations', label: 'Platform Operations', icon: Settings },
    { path: '/admin/analytics', label: 'Analytics & Reporting', icon: BarChart3 },
];

function Sidebar({ collapsed, onToggle }) {
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuth();

    const isActive = (item) => {
        if (item.exact) return location.pathname === item.path;
        return location.pathname.startsWith(item.path);
    };

    return (
        <div style={{
            width: collapsed ? 60 : 240, minHeight: '100vh', background: T.surface,
            borderRight: `1px solid ${T.border}`, display: 'flex', flexDirection: 'column',
            transition: 'width 0.2s ease', overflow: 'hidden', flexShrink: 0,
        }}>
            {/* Header */}
            <div style={{ padding: collapsed ? '20px 12px' : '20px 20px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', minHeight: 64 }}>
                {!collapsed && <span style={{ fontSize: 16, fontWeight: 700, color: T.text, whiteSpace: 'nowrap' }}>Admin Panel</span>}
                <button onClick={onToggle} style={{ background: 'none', border: 'none', color: T.muted, cursor: 'pointer', padding: 4, display: 'flex' }}>
                    {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>

            {/* Nav */}
            <nav style={{ flex: 1, padding: '12px 8px' }}>
                {NAV_ITEMS.map(item => {
                    const active = isActive(item);
                    const Icon = item.icon;
                    return (
                        <button key={item.path} onClick={() => navigate(item.path)}
                            style={{
                                width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                                padding: collapsed ? '10px 14px' : '10px 16px',
                                background: active ? `${T.accent}15` : 'transparent',
                                border: 'none', borderRadius: 8, cursor: 'pointer',
                                color: active ? T.accent : T.muted, marginBottom: 4,
                                transition: 'all 0.15s ease', whiteSpace: 'nowrap',
                            }}
                            onMouseOver={e => { if (!active) e.currentTarget.style.background = T.surfaceHover; }}
                            onFocus={e => { if (!active) e.currentTarget.style.background = T.surfaceHover; }}
                            onMouseOut={e => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                            onBlur={e => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                        >
                            <Icon size={18} />
                            {!collapsed && <span style={{ fontSize: 13, fontWeight: active ? 600 : 400 }}>{item.label}</span>}
                        </button>
                    );
                })}
            </nav>

            {/* Footer */}
            <div style={{ padding: '12px 8px', borderTop: `1px solid ${T.border}` }}>
                <button onClick={() => navigate('/dashboard')}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: collapsed ? '10px 14px' : '10px 16px', background: 'transparent', border: 'none', borderRadius: 8, cursor: 'pointer', color: T.muted, whiteSpace: 'nowrap' }}
                    onMouseOver={e => e.currentTarget.style.background = T.surfaceHover}
                    onFocus={e => e.currentTarget.style.background = T.surfaceHover}
                    onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                    onBlur={e => e.currentTarget.style.background = 'transparent'}
                >
                    <ArrowLeft size={18} />
                    {!collapsed && <span style={{ fontSize: 13 }}>Back to App</span>}
                </button>
                <button onClick={() => { logout(); navigate('/login'); }}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 12, padding: collapsed ? '10px 14px' : '10px 16px', background: 'transparent', border: 'none', borderRadius: 8, cursor: 'pointer', color: T.danger, marginTop: 4, whiteSpace: 'nowrap' }}
                    onMouseOver={e => e.currentTarget.style.background = T.surfaceHover}
                    onFocus={e => e.currentTarget.style.background = T.surfaceHover}
                    onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                    onBlur={e => e.currentTarget.style.background = 'transparent'}
                >
                    <LogOut size={18} />
                    {!collapsed && <span style={{ fontSize: 13 }}>Logout</span>}
                </button>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════════════════
   ADMIN DASHBOARD — MAIN LAYOUT
   ═══════════════════════════════════════════════════════════════════════════ */
export default function AdminDashboard() {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: T.bg, color: T.text }}>
            <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
            <main style={{ flex: 1, padding: 32, overflowY: 'auto', maxHeight: '100vh' }}>
                <Routes>
                    <Route index element={<OverviewPage />} />
                    <Route path="sites" element={<SitesPage />} />
                    <Route path="domains" element={<DomainsPage />} />
                    <Route path="users" element={<UsersPage />} />
                    <Route path="tokens" element={<TokensPage />} />
                    <Route path="operations" element={<OperationsPage />} />
                    <Route path="analytics" element={<AnalyticsPage />} />
                    <Route path="*" element={<Navigate to="/admin" replace />} />
                </Routes>
            </main>
        </div>
    );
}
