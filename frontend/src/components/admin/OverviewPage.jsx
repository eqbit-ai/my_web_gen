import React, { useState, useEffect, useCallback } from 'react';
import {
    Users, Activity, Zap, Database, RefreshCw, Globe, Shield,
    TrendingUp, Clock, AlertTriangle, CheckCircle, ArrowUpRight, ArrowDownRight,
} from 'lucide-react';
import {
    AreaChart, Area, PieChart, Pie, Cell,
    XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import {
    adminGetStats, adminGetSystemInfo, adminResetCircuit,
    adminGetGrowthAnalytics, adminGetGenerationStats,
    adminGetUsers, adminGetGenerations,
} from '../../services/adminApi';
import formatDate from './shared/formatDate';

const T = {
    bg: '#0a0a0f', surface: '#12121a', surfaceHover: '#1a1a28', border: '#2a2a3a',
    text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', accentHover: '#6366f1',
    success: '#34d399', warning: '#fbbf24', danger: '#f87171',
};
const CHART_COLORS = ['#818cf8', '#34d399', '#fbbf24', '#f87171', '#c084fc', '#fb923c'];

const card = { background: T.surface, borderRadius: 12, border: `1px solid ${T.border}`, padding: 20 };
const chartTooltipStyle = { background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, fontSize: 12, color: T.text };

function formatUptime(seconds) {
    if (!seconds) return '—';
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return `${d}d ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
}


function MiniStat({ label, value, icon: Icon, color, sub, trend }) {
    return (
        <div style={{ ...card, display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{
                width: 48, height: 48, borderRadius: 12,
                background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
                <Icon size={22} style={{ color }} />
            </div>
            <div style={{ flex: 1 }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: T.text, lineHeight: 1.1 }}>{value ?? '—'}</div>
                <div style={{ fontSize: 12, color: T.muted, marginTop: 2 }}>{label}</div>
            </div>
            {trend !== undefined && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 2, fontSize: 12, color: trend >= 0 ? T.success : T.danger }}>
                    {trend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    {Math.abs(trend)}%
                </div>
            )}
            {sub && !trend && <div style={{ fontSize: 11, color: T.muted, textAlign: 'right' }}>{sub}</div>}
        </div>
    );
}

export default function OverviewPage() {
    const [stats, setStats] = useState(null);
    const [sysInfo, setSysInfo] = useState(null);
    const [growth, setGrowth] = useState([]);
    const [genStats, setGenStats] = useState([]);
    const [recentUsers, setRecentUsers] = useState([]);
    const [recentGens, setRecentGens] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [resetting, setResetting] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [s, sys, gr, gs, ru, rg] = await Promise.all([
                adminGetStats(),
                adminGetSystemInfo().catch(() => null),
                adminGetGrowthAnalytics(30).catch(() => ({})),
                adminGetGenerationStats(30).catch(() => ({})),
                adminGetUsers(1, 5).catch(() => ({})),
                adminGetGenerations(1, 5).catch(() => ({})),
            ]);
            setStats(s);
            setSysInfo(sys);
            // Merge daily_signups + daily_active into [{date, signups, active_users}]
            const signups = gr?.daily_signups || [];
            const actives = gr?.daily_active || [];
            const gMap = {};
            signups.forEach(d => { gMap[d.date] = { date: d.date, signups: d.count, active_users: 0 }; });
            actives.forEach(d => {
                if (!gMap[d.date]) gMap[d.date] = { date: d.date, signups: 0, active_users: 0 };
                gMap[d.date].active_users = d.count;
            });
            setGrowth(Object.values(gMap).sort((a, b) => a.date.localeCompare(b.date)));
            setGenStats(gs?.daily_stats || []);
            setRecentUsers(Array.isArray(ru) ? ru : ru?.users || ru?.items || []);
            setRecentGens(Array.isArray(rg) ? rg : rg?.generations || rg?.items || []);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);
    useEffect(() => {
        const interval = setInterval(load, 30000);
        return () => clearInterval(interval);
    }, [load]);

    const handleResetCircuit = async (provider) => {
        setResetting(provider);
        try { await adminResetCircuit(provider); await load(); } catch {}
        setResetting(null);
    };

    if (loading && !stats) {
        return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    }

    if (error) {
        return (
            <div className="admin-alert admin-alert-error">
                <span>{error}</span>
                <button onClick={load}>Retry</button>
            </div>
        );
    }

    const s = stats || {};
    const sys = sysInfo || {};
    const memoryPct = sys.memory?.percent || 0;
    const uptime = sys.uptime_seconds || 0;
    const cbEntries = Object.entries(s.circuit_breakers || {});
    const allCircuitsClosed = cbEntries.length === 0 || cbEntries.every(([, v]) => (typeof v === 'string' ? v : v?.state) === 'closed');

    // Build generation success/fail pie data
    const successRate = genStats.length > 0
        ? { success: genStats.reduce((a, d) => a + (d.success || d.completed || 0), 0), failed: genStats.reduce((a, d) => a + (d.failed || d.errors || 0), 0) }
        : null;
    const pieData = successRate ? [
        { name: 'Success', value: successRate.success || 0 },
        { name: 'Failed', value: successRate.failed || 0 },
    ] : [];

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Overview</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className="admin-auto-refresh"><RefreshCw size={12} /> Auto-refresh 30s</span>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {/* ── KPI Cards ── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
                <MiniStat icon={Users} label="Total Users" value={s.total_users} color={T.accent} sub={`${s.active_users_7d || 0} active this week`} />
                <MiniStat icon={Zap} label="Generations" value={s.total_generations} color={T.success} sub={`${s.queue_depth || 0} in queue`} />
                <MiniStat icon={Clock} label="Uptime" value={formatUptime(uptime)} color={T.warning} sub={`PID mem: ${sys.process_memory_mb || '—'} MB`} />
                <MiniStat
                    icon={allCircuitsClosed ? CheckCircle : AlertTriangle}
                    label="System Health"
                    value={allCircuitsClosed ? 'Healthy' : 'Degraded'}
                    color={allCircuitsClosed ? T.success : T.danger}
                    sub={`CPU: ${sys.cpu_percent ?? '—'}% | RAM: ${memoryPct}%`}
                />
            </div>

            {/* ── Row 2: Growth Chart + Generation Pie ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 24 }}>
                {/* User Growth Chart */}
                <div style={card}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: T.text }}>
                            <TrendingUp size={16} style={{ marginRight: 8, verticalAlign: -3, color: T.accent }} />
                            Platform Growth (30d)
                        </h3>
                    </div>
                    {growth.length > 0 ? (
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={growth}>
                                <defs>
                                    <linearGradient id="growthGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor={T.accent} stopOpacity={0.3} />
                                        <stop offset="100%" stopColor={T.accent} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                                <XAxis dataKey="date" stroke={T.muted} tick={{ fontSize: 10 }} tickFormatter={v => v?.slice(5) || v} />
                                <YAxis stroke={T.muted} tick={{ fontSize: 10 }} />
                                <Tooltip contentStyle={chartTooltipStyle} />
                                <Area type="monotone" dataKey="signups" stroke={T.accent} fill="url(#growthGrad)" strokeWidth={2} name="Signups" />
                                <Area type="monotone" dataKey="active_users" stroke={T.success} fill="none" strokeWidth={2} strokeDasharray="5 5" name="Active" />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: T.muted, fontSize: 13 }}>
                            No growth data yet — charts will populate as users sign up
                        </div>
                    )}
                </div>

                {/* Generation Success Rate Pie */}
                <div style={card}>
                    <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: T.text }}>
                        <Activity size={16} style={{ marginRight: 8, verticalAlign: -3, color: T.success }} />
                        Generation Success Rate
                    </h3>
                    {pieData.length > 0 && (pieData[0].value > 0 || pieData[1].value > 0) ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <ResponsiveContainer width="100%" height={160}>
                                <PieChart>
                                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={65} dataKey="value" stroke="none">
                                        <Cell fill={T.success} />
                                        <Cell fill={T.danger} />
                                    </Pie>
                                    <Tooltip contentStyle={chartTooltipStyle} />
                                </PieChart>
                            </ResponsiveContainer>
                            <div style={{ display: 'flex', gap: 20, marginTop: 8 }}>
                                <span style={{ fontSize: 12, color: T.success }}>● Success: {pieData[0].value}</span>
                                <span style={{ fontSize: 12, color: T.danger }}>● Failed: {pieData[1].value}</span>
                            </div>
                        </div>
                    ) : (
                        <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: T.muted, fontSize: 13 }}>
                            No generation data yet
                        </div>
                    )}
                </div>
            </div>

            {/* ── Row 3: Circuit Breakers + Quick Stats ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
                {/* Circuit Breakers */}
                <div style={card}>
                    <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: T.text }}>
                        <Shield size={16} style={{ marginRight: 8, verticalAlign: -3, color: T.accent }} />
                        API Circuit Breakers
                    </h3>
                    {cbEntries.length > 0 ? cbEntries.map(([provider, cb]) => {
                        const state = typeof cb === 'string' ? cb : (cb?.state || 'unknown');
                        const failures = typeof cb === 'object' ? (cb?.failure_count || 0) : 0;
                        const stateColor = state === 'closed' ? T.success : state === 'open' ? T.danger : T.warning;
                        return (
                            <div key={provider} style={{
                                display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: 8,
                                background: T.bg, marginBottom: 8, border: `1px solid ${T.border}`,
                            }}>
                                <div style={{ width: 10, height: 10, borderRadius: '50%', background: stateColor, marginRight: 12, boxShadow: `0 0 8px ${stateColor}40` }} />
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: T.text, textTransform: 'capitalize' }}>{provider}</div>
                                    <div style={{ fontSize: 11, color: T.muted }}>{state} · {failures} failures</div>
                                </div>
                                <button
                                    onClick={() => handleResetCircuit(provider)}
                                    disabled={resetting === provider}
                                    style={{
                                        padding: '4px 12px', borderRadius: 6, fontSize: 11, border: `1px solid ${T.border}`,
                                        background: 'transparent', color: T.text, cursor: 'pointer',
                                    }}
                                >
                                    {resetting === provider ? '...' : 'Reset'}
                                </button>
                            </div>
                        );
                    }) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 16, background: T.bg, borderRadius: 8 }}>
                            <CheckCircle size={16} style={{ color: T.success }} />
                            <span style={{ color: T.muted, fontSize: 13 }}>All systems operational</span>
                        </div>
                    )}
                </div>

                {/* Infrastructure Quick Stats */}
                <div style={card}>
                    <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: T.text }}>
                        <Database size={16} style={{ marginRight: 8, verticalAlign: -3, color: T.accent }} />
                        Infrastructure
                    </h3>
                    {[
                        { label: 'Memory Usage', value: `${sys.memory?.used_mb?.toFixed(0) || '—'} / ${sys.memory?.total_mb || '—'} MB`, pct: memoryPct, color: memoryPct > 85 ? T.danger : memoryPct > 70 ? T.warning : T.success },
                        { label: 'CPU', value: `${sys.cpu_percent ?? '—'}%`, pct: sys.cpu_percent || 0, color: (sys.cpu_percent || 0) > 80 ? T.danger : T.success },
                        { label: 'Redis Memory', value: `${sys.redis?.used_memory_mb || '—'} MB`, pct: null },
                        { label: 'DB Pool', value: `${sys.database_pool?.checked_out || 0} / ${sys.database_pool?.size || 20} connections`, pct: ((sys.database_pool?.checked_out || 0) / (sys.database_pool?.size || 20)) * 100, color: T.accent },
                    ].map((item, i) => (
                        <div key={i} style={{ marginBottom: 14 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                <span style={{ fontSize: 12, color: T.muted }}>{item.label}</span>
                                <span style={{ fontSize: 12, fontWeight: 600, color: T.text }}>{item.value}</span>
                            </div>
                            {item.pct !== null && (
                                <div style={{ height: 4, borderRadius: 2, background: T.border, overflow: 'hidden' }}>
                                    <div style={{ width: `${Math.min(item.pct, 100)}%`, height: '100%', borderRadius: 2, background: item.color || T.accent, transition: 'width 0.5s ease' }} />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Row 4: Recent Users + Recent Generations ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {/* Recent Users */}
                <div style={card}>
                    <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: T.text }}>
                        <Users size={16} style={{ marginRight: 8, verticalAlign: -3, color: T.accent }} />
                        Recent Users
                    </h3>
                    {recentUsers.length > 0 ? recentUsers.map((u, i) => (
                        <div key={u.id || i} style={{
                            display: 'flex', alignItems: 'center', padding: '10px 0',
                            borderBottom: i < recentUsers.length - 1 ? `1px solid ${T.border}` : 'none',
                        }}>
                            <div style={{
                                width: 32, height: 32, borderRadius: '50%', background: CHART_COLORS[i % CHART_COLORS.length] + '30',
                                display: 'flex', alignItems: 'center', justifyContent: 'center', marginRight: 12,
                                fontSize: 13, fontWeight: 600, color: CHART_COLORS[i % CHART_COLORS.length],
                            }}>
                                {(u.company_name || u.email || '?')[0].toUpperCase()}
                            </div>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 13, fontWeight: 500, color: T.text }}>{u.company_name || u.email}</div>
                                <div style={{ fontSize: 11, color: T.muted }}>{u.license_number || u.licence_number || '—'}</div>
                            </div>
                            <div style={{ fontSize: 11, color: T.muted }}>{formatDate(u.created_at)}</div>
                        </div>
                    )) : (
                        <div style={{ color: T.muted, fontSize: 13, padding: 16, textAlign: 'center' }}>No users yet</div>
                    )}
                </div>

                {/* Recent Generations */}
                <div style={card}>
                    <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600, color: T.text }}>
                        <Globe size={16} style={{ marginRight: 8, verticalAlign: -3, color: T.success }} />
                        Recent Generations
                    </h3>
                    {recentGens.length > 0 ? recentGens.map((g, i) => (
                        <div key={g.id || i} style={{
                            display: 'flex', alignItems: 'center', padding: '10px 0',
                            borderBottom: i < recentGens.length - 1 ? `1px solid ${T.border}` : 'none',
                        }}>
                            <div style={{
                                width: 8, height: 8, borderRadius: '50%', marginRight: 12,
                                background: g.status === 'completed' || g.status === 'success' ? T.success : g.status === 'failed' ? T.danger : T.warning,
                            }} />
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 13, fontWeight: 500, color: T.text }}>{g.prompt?.slice(0, 50) || g.business_type || 'Generation'}{g.prompt?.length > 50 ? '...' : ''}</div>
                                <div style={{ fontSize: 11, color: T.muted }}>
                                    {g.status || '—'} · {g.duration_ms ? `${(g.duration_ms / 1000).toFixed(1)}s` : '—'}
                                </div>
                            </div>
                            <div style={{ fontSize: 11, color: T.muted }}>{formatDate(g.created_at)}</div>
                        </div>
                    )) : (
                        <div style={{ color: T.muted, fontSize: 13, padding: 16, textAlign: 'center' }}>No generations yet — data will appear as users generate websites</div>
                    )}
                </div>
            </div>
        </div>
    );
}
