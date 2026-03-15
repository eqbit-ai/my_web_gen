import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Coins, TrendingUp } from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { adminGetTokenPool, adminGetTokenConsumption } from '../../services/adminApi';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399', warning: '#fbbf24', danger: '#f87171' };

const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null;
    return (
        <div className="admin-chart-tooltip">
            <div className="admin-chart-tooltip-label">{label}</div>
            {(payload || []).map((p, i) => (
                <div key={i} className="admin-chart-tooltip-row">
                    <span>{p.name}</span>
                    <strong style={{ color: p.color }}>{p.value}</strong>
                </div>
            ))}
        </div>
    );
};

export default function TokenPoolPage() {
    const [pool, setPool] = useState(null);
    const [trend, setTrend] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [p, t] = await Promise.all([
                adminGetTokenPool(),
                adminGetTokenConsumption(30).catch(() => null),
            ]);
            setPool(p);
            setTrend(t);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    if (loading) return <div className="admin-loading-page"><RefreshCw size={20} className="admin-spinner" /> Loading...</div>;
    if (error) return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;

    const p = pool || {};
    const trendData = trend?.data || trend?.items || (Array.isArray(trend) ? trend : []);
    const topConsumers = p.top_consumers || p.top_users || [];

    const totalIssued = p.total_granted ?? p.total_issued ?? 0;
    const totalUsed = p.total_consumed ?? p.total_used ?? 0;
    const totalRemaining = p.total_remaining ?? p.outstanding ?? 0;
    const utilization = totalIssued ? Math.round((totalUsed / totalIssued) * 100) : 0;

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Token Pool</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Pool Hero */}
            <div className="admin-card admin-token-hero" style={{ marginBottom: 24 }}>
                <div className="admin-token-hero-header">
                    <div>
                        <div className="admin-card-title">Pool Utilization</div>
                        <div className="admin-token-hero-sub">
                            {totalUsed.toLocaleString()} of {totalIssued.toLocaleString()} tokens consumed
                        </div>
                    </div>
                    <div className="admin-token-hero-pct">{utilization}%</div>
                </div>
                <div className="admin-gauge-track admin-gauge-xl">
                    <div
                        className="admin-gauge-fill"
                        style={{
                            width: `${utilization}%`,
                            background: utilization > 80
                                ? `linear-gradient(90deg, ${T.warning}, ${T.danger})`
                                : `linear-gradient(90deg, ${T.accent}, #c084fc)`,
                        }}
                    />
                </div>
                <div className="admin-card-stats" style={{ marginTop: 16 }}>
                    <div>
                        <span className="admin-card-stat-label">Total Issued</span>
                        <strong>{totalIssued.toLocaleString()}</strong>
                    </div>
                    <div>
                        <span className="admin-card-stat-label">Total Used</span>
                        <strong>{totalUsed.toLocaleString()}</strong>
                    </div>
                    <div>
                        <span className="admin-card-stat-label">Outstanding</span>
                        <strong>{totalRemaining.toLocaleString()}</strong>
                    </div>
                    <div>
                        <span className="admin-card-stat-label">Weekly Burn Rate</span>
                        <strong style={{ color: T.warning }}>{(p.weekly_burn_rate ?? 0).toLocaleString()}</strong>
                    </div>
                </div>
            </div>

            {/* Consumption Trend */}
            <div className="admin-chart-card admin-chart-full" style={{ marginBottom: 24 }}>
                <div className="admin-chart-title">Consumption Trend (30d)</div>
                {trendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={trendData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                            <Tooltip content={<ChartTooltip />} />
                            <Area type="monotone" dataKey="consumed" name="Consumed" stroke={T.warning} fill={`${T.warning}30`} />
                            <Area type="monotone" dataKey="granted" name="Granted" stroke={T.success} fill={`${T.success}30`} />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : <div className="admin-chart-empty">No consumption data available</div>}
            </div>

            {/* Top Consumers */}
            {(topConsumers || []).length > 0 && (
                <div className="admin-card">
                    <div className="admin-card-title">Top Consumers</div>
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th style={{ width: 40 }}>Rank</th>
                                <th>User</th>
                                <th>Consumed</th>
                                <th>Balance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(topConsumers || []).map((u, i) => (
                                <tr key={u.user_id || i}>
                                    <td><span className="admin-rank">{i + 1}</span></td>
                                    <td>{u.email || u.user_id || '—'}</td>
                                    <td style={{ fontWeight: 600, color: T.warning }}>{(u.tokens_used ?? u.consumed ?? '—').toLocaleString?.() || (u.tokens_used ?? u.consumed ?? '—')}</td>
                                    <td>{u.balance ?? u.token_balance ?? '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
