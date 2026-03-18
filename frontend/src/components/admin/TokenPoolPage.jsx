import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import {
    ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { adminGetTokenPool, adminGetTokenConsumption } from '../../services/adminApi';

const T = { bg: '#0a0a0f', surface: '#12121a', border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399', warning: '#fbbf24', danger: '#f87171' };

function formatK(v) {
    if (v >= 1000000) return `${(v / 1000000).toFixed(1)}M`;
    if (v >= 1000) return `${(v / 1000).toFixed(0)}K`;
    return v;
}

const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null;
    return (
        <div className="admin-chart-tooltip">
            <div className="admin-chart-tooltip-label">{label}</div>
            {(payload || []).map((p, i) => (
                <div key={i} className="admin-chart-tooltip-row">
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', background: p.color || p.fill, display: 'inline-block' }} />
                        {p.name}
                    </span>
                    <strong style={{ color: p.color || p.fill }}>{(p.value || 0).toLocaleString()}</strong>
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
    const rawTrend = trend?.daily_spend || [];
    const topConsumers = p.top_consumers || p.top_users || [];

    // Build chart data with cumulative net and short date labels
    const trendData = (() => {
        let cumNet = 0;
        return rawTrend.map(d => {
            cumNet += (d.granted || 0) - (d.consumed || 0);
            return {
                date: d.date?.slice(5) || d.date,
                consumed: d.consumed || 0,
                granted: d.granted || 0,
                net: cumNet,
            };
        });
    })();

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
                <div className="admin-chart-title">
                    Consumption Trend
                    <span className="admin-chart-period">Last 30 days</span>
                </div>
                {trendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                        <ComposedChart data={trendData} barGap={2}>
                            <defs>
                                <linearGradient id="poolConsumedGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={T.warning} stopOpacity={0.9} />
                                    <stop offset="100%" stopColor={T.warning} stopOpacity={0.4} />
                                </linearGradient>
                                <linearGradient id="poolGrantedGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={T.success} stopOpacity={0.9} />
                                    <stop offset="100%" stopColor={T.success} stopOpacity={0.4} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} vertical={false} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} axisLine={{ stroke: T.border }} tickLine={false} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} tickFormatter={formatK} axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTooltip />} />
                            <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                            <Bar dataKey="consumed" name="Consumed" fill="url(#poolConsumedGrad)" radius={[4, 4, 0, 0]} barSize={trendData.length > 20 ? 10 : 18} />
                            <Bar dataKey="granted" name="Granted" fill="url(#poolGrantedGrad)" radius={[4, 4, 0, 0]} barSize={trendData.length > 20 ? 10 : 18} />
                            <Line type="monotone" dataKey="net" name="Net Balance" stroke="#c084fc" strokeWidth={2} dot={false} strokeDasharray="6 3" />
                        </ComposedChart>
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
