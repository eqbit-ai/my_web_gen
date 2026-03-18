import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Server, Database, Cpu } from 'lucide-react';
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';
import { adminGetSystemInfo, adminGetStats, adminResetCircuit } from '../../services/adminApi';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399', warning: '#fbbf24', danger: '#f87171' };

function renderNestedValue(val, depth = 0) {
    if (val === null || val === undefined) return '—';
    if (typeof val !== 'object') return String(val);
    // Flatten nested objects into readable key-value pairs
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {Object.entries(val).map(([k, v]) => (
                <div key={k} style={{ fontSize: 12, display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                    <span style={{ color: T.muted }}>{k.replace(/_/g, ' ')}</span>
                    <span style={{ color: T.text, fontWeight: 500, textAlign: 'right' }}>
                        {typeof v === 'object' && v !== null
                            ? Object.entries(v).map(([dk, dv]) => `${dk}: ${String(dv)}`).join(', ')
                            : String(v)}
                    </span>
                </div>
            ))}
        </div>
    );
}

function GaugeCard({ label, value, max, unit, color, icon: Icon }) {
    const pct = max > 0 ? Math.round((value / max) * 100) : 0;
    const gaugeData = [{ value: pct, fill: color || T.accent }];

    return (
        <div className="admin-card admin-card-gauge">
            {Icon && <Icon size={20} style={{ color: T.muted, marginBottom: 8 }} />}
            <div className="admin-radial-gauge">
                <ResponsiveContainer width={120} height={120}>
                    <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="100%" startAngle={90} endAngle={-270} data={gaugeData} barSize={10}>
                        <RadialBar dataKey="value" cornerRadius={5} background={{ fill: 'rgba(51,65,85,0.3)' }} />
                    </RadialBarChart>
                </ResponsiveContainer>
                <div className="admin-radial-center">
                    <span className="admin-radial-value" style={{ color: color || T.text }}>{pct}%</span>
                    <span className="admin-radial-label">{label}</span>
                </div>
            </div>
            <div className="admin-gauge-detail">
                {value}{unit || ''} / {max}{unit || ''}
            </div>
        </div>
    );
}

export default function SystemHealthPage() {
    const [sysInfo, setSysInfo] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [resetting, setResetting] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [sys, s] = await Promise.all([
                adminGetSystemInfo(),
                adminGetStats().catch(() => null),
            ]);
            setSysInfo(sys);
            setStats(s);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleResetCircuit = async (provider) => {
        setResetting(provider);
        try { await adminResetCircuit(provider); load(); } catch {}
        setResetting(null);
    };

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;

    const sys = sysInfo || {};
    const mem = sys.memory || {};
    const redis = sys.redis || {};
    const dbPool = sys.database_pool || sys.db_pool || {};
    const metrics = sys.metrics || {};
    const errorRates = sys.error_rates || {};

    const cpuPct = sys.cpu_percent || sys.cpu_usage || 0;
    const memUsed = mem.used_mb || mem.used || 0;
    const memTotal = mem.total_mb || mem.total || 100;
    const circuitBreakers = stats?.circuit_breakers || {};

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">System Health</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* CPU / RAM Gauges */}
            <div className="admin-sys-gauges">
                <GaugeCard
                    label="CPU"
                    value={cpuPct}
                    max={100}
                    unit="%"
                    color={cpuPct > 80 ? T.danger : cpuPct > 50 ? T.warning : T.success}
                    icon={Cpu}
                />
                <GaugeCard
                    label="Memory"
                    value={memUsed}
                    max={memTotal}
                    unit="MB"
                    color={memTotal > 0 && (memUsed / memTotal) > 0.8 ? T.danger : T.accent}
                    icon={Server}
                />
                {sys.disk_percent != null && (
                    <GaugeCard
                        label="Disk"
                        value={sys.disk_percent}
                        max={100}
                        unit="%"
                        color={sys.disk_percent > 80 ? T.danger : T.success}
                        icon={Database}
                    />
                )}
            </div>

            {/* Circuit Breakers */}
            <div style={{ marginBottom: 24 }}>
                <h2 className="admin-section-title">Circuit Breakers</h2>
                <div className="admin-cb-grid">
                    {Object.entries(circuitBreakers).map(([provider, cb]) => {
                        const state = typeof cb === 'string' ? cb : (cb?.state || 'unknown');
                        const failures = typeof cb === 'object' ? (cb?.failure_count || 0) : 0;
                        return (
                            <div key={provider} className={`admin-cb-card admin-cb-${state}`}>
                                <div className="admin-status-dot" style={{ color: state === 'closed' ? T.success : state === 'open' ? T.danger : T.warning }} />
                                <div className="admin-cb-info">
                                    <strong>{provider}</strong>
                                    <span>{state} | {failures} failures</span>
                                </div>
                                <button className="admin-btn admin-btn-sm" onClick={() => handleResetCircuit(provider)} disabled={resetting === provider}>
                                    {resetting === provider ? '...' : 'Reset'}
                                </button>
                            </div>
                        );
                    })}
                    {Object.keys(circuitBreakers).length === 0 && (
                        <span style={{ color: T.muted, fontSize: 13 }}>No circuit breaker data</span>
                    )}
                </div>
            </div>

            {/* Redis & DB Status */}
            <div className="admin-charts-row" style={{ marginBottom: 24, marginTop: 0 }}>
                <div className="admin-card">
                    <div className="admin-card-title">Redis</div>
                    {Object.keys(redis).length > 0 ? Object.entries(redis).map(([k, v]) => (
                        <div key={k} className="admin-metric-row">
                            <span className="admin-metric-label">{k.replace(/_/g, ' ')}</span>
                            <span className="admin-metric-value">{renderNestedValue(v)}</span>
                        </div>
                    )) : <span style={{ color: T.muted, fontSize: 13 }}>No Redis info</span>}
                </div>
                <div className="admin-card">
                    <div className="admin-card-title">Database Pool</div>
                    {Object.keys(dbPool).length > 0 ? Object.entries(dbPool).map(([k, v]) => (
                        <div key={k} className="admin-metric-row">
                            <span className="admin-metric-label">{k.replace(/_/g, ' ')}</span>
                            <span className="admin-metric-value">{renderNestedValue(v)}</span>
                        </div>
                    )) : <span style={{ color: T.muted, fontSize: 13 }}>No database pool info</span>}
                </div>
            </div>

            {/* System Info — nested objects as key-value tables */}
            <div className="admin-sys-grid">
                {/* Scalar values */}
                {Object.entries(sys)
                    .filter(([k, v]) => typeof v !== 'object' || v === null)
                    .filter(([k]) => !['cpu_percent', 'cpu_usage', 'disk_percent'].includes(k))
                    .map(([k, v]) => (
                    <div key={k} className="admin-card">
                        <div className="admin-card-title" style={{ textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</div>
                        <div style={{ fontSize: 15, fontWeight: 600, color: T.text }}>{String(v ?? '—')}</div>
                    </div>
                ))}

                {/* Metrics */}
                {Object.keys(metrics).length > 0 && (
                    <div className="admin-card" style={{ gridColumn: Object.keys(metrics).length > 3 ? 'span 2' : 'span 1' }}>
                        <div className="admin-card-title">Metrics</div>
                        {Object.entries(metrics).map(([k, v]) => (
                            <div key={k} className="admin-metric-row">
                                <span className="admin-metric-label">{k.replace(/_/g, ' ')}</span>
                                <span className="admin-metric-value">{renderNestedValue(v)}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Error Rates */}
                {Object.keys(errorRates).length > 0 && (
                    <div className="admin-card">
                        <div className="admin-card-title">Error Rates</div>
                        {Object.entries(errorRates).map(([k, v]) => (
                            <div key={k} className="admin-metric-row">
                                <span className="admin-metric-label">{k.replace(/_/g, ' ')}</span>
                                <span className="admin-metric-value" style={{ color: (typeof v === 'number' && v > 5) ? T.danger : T.text }}>
                                    {renderNestedValue(v)}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
