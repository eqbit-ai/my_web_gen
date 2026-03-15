import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import {
    ComposedChart, Bar, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { adminGetTokenConsumption } from '../../services/adminApi';

const T = { border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399', warning: '#fbbf24', danger: '#f87171' };
const PIE_COLORS = [T.accent, T.success, T.warning, T.danger, '#c084fc', '#60a5fa'];

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

export default function TokenTrendPage() {
    const [days, setDays] = useState(30);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetTokenConsumption(days);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [days]);

    useEffect(() => { load(); }, [load]);

    const dailySpend = data?.daily_spend || [];
    const tokenDist = data?.token_distribution || [];
    const topGenerators = data?.top_generators || [];

    const totalConsumed = dailySpend.reduce((s, d) => s + (d.consumed || 0), 0);
    const totalGranted = dailySpend.reduce((s, d) => s + (d.granted || 0), 0);
    const totalRefunded = dailySpend.reduce((s, d) => s + (d.refunded || 0), 0);

    // Build cumulative running balance data
    const chartData = (() => {
        let cumConsumed = 0;
        let cumGranted = 0;
        return dailySpend.map(d => {
            cumConsumed += (d.consumed || 0);
            cumGranted += (d.granted || 0);
            return {
                date: d.date?.slice(5) || d.date, // "03-15" format
                fullDate: d.date,
                consumed: d.consumed || 0,
                granted: d.granted || 0,
                refunded: d.refunded || 0,
                cumConsumed,
                cumGranted,
                net: cumGranted - cumConsumed,
            };
        });
    })();

    // Daily average
    const avgDaily = dailySpend.length > 0 ? Math.round(totalConsumed / dailySpend.length) : 0;

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Token Consumption</h1>
                <div className="admin-actions">
                    <div className="admin-tabs">
                        {[7, 30, 90].map(d => (
                            <button key={d} className={`admin-tab${days === d ? ' active' : ''}`} onClick={() => setDays(d)}>
                                {d}d
                            </button>
                        ))}
                    </div>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)', marginBottom: 24 }}>
                <div className="admin-stat-card admin-stat-accent-orange">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{formatK(totalConsumed)}</div>
                        <div className="admin-stat-label">Consumed ({days}d)</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-green">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{formatK(totalGranted)}</div>
                        <div className="admin-stat-label">Granted ({days}d)</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-blue">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{formatK(totalRefunded)}</div>
                        <div className="admin-stat-label">Refunded ({days}d)</div>
                    </div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{formatK(avgDaily)}</div>
                        <div className="admin-stat-label">Avg Daily Burn</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-purple">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">
                            {totalGranted > 0 ? `${Math.round((totalConsumed / totalGranted) * 100)}%` : '—'}
                        </div>
                        <div className="admin-stat-label">Utilization</div>
                    </div>
                </div>
            </div>

            {/* Main Chart: Bars for daily + Line for cumulative */}
            <div className="admin-chart-card admin-chart-full" style={{ marginBottom: 24 }}>
                <div className="admin-chart-title">
                    Daily Token Activity
                    <span className="admin-chart-period">Last {days} days</span>
                </div>
                {loading ? (
                    <div className="admin-loading-page" style={{ minHeight: 340 }}><RefreshCw size={20} className="admin-spinner" /> Loading...</div>
                ) : chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={340}>
                        <ComposedChart data={chartData} barGap={2}>
                            <defs>
                                <linearGradient id="consumedGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={T.warning} stopOpacity={0.9} />
                                    <stop offset="100%" stopColor={T.warning} stopOpacity={0.4} />
                                </linearGradient>
                                <linearGradient id="grantedGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={T.success} stopOpacity={0.9} />
                                    <stop offset="100%" stopColor={T.success} stopOpacity={0.4} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} vertical={false} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} axisLine={{ stroke: T.border }} tickLine={false} />
                            <YAxis yAxisId="daily" tick={{ fill: T.muted, fontSize: 11 }} tickFormatter={formatK} axisLine={false} tickLine={false} />
                            <YAxis yAxisId="cum" orientation="right" tick={{ fill: T.muted, fontSize: 10 }} tickFormatter={formatK} axisLine={false} tickLine={false} hide />
                            <Tooltip content={<ChartTooltip />} />
                            <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                            <Bar yAxisId="daily" dataKey="consumed" name="Consumed" fill="url(#consumedGrad)" radius={[4, 4, 0, 0]} barSize={chartData.length > 30 ? 8 : 16} />
                            <Bar yAxisId="daily" dataKey="granted" name="Granted" fill="url(#grantedGrad)" radius={[4, 4, 0, 0]} barSize={chartData.length > 30 ? 8 : 16} />
                            {totalRefunded > 0 && <Bar yAxisId="daily" dataKey="refunded" name="Refunded" fill={T.accent} radius={[4, 4, 0, 0]} barSize={chartData.length > 30 ? 8 : 16} />}
                            <Line yAxisId="daily" type="monotone" dataKey="net" name="Net Balance" stroke="#c084fc" strokeWidth={2} dot={false} strokeDasharray="6 3" />
                        </ComposedChart>
                    </ResponsiveContainer>
                ) : <div className="admin-chart-empty">No token data available for this period</div>}
            </div>

            {/* Cumulative Trend */}
            {chartData.length > 1 && (
                <div className="admin-chart-card admin-chart-full" style={{ marginBottom: 24 }}>
                    <div className="admin-chart-title">
                        Cumulative Trend
                        <span className="admin-chart-period">Running total over {days} days</span>
                    </div>
                    <ResponsiveContainer width="100%" height={240}>
                        <AreaChart data={chartData}>
                            <defs>
                                <linearGradient id="cumConsumedGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={T.warning} stopOpacity={0.3} />
                                    <stop offset="100%" stopColor={T.warning} stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="cumGrantedGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={T.success} stopOpacity={0.3} />
                                    <stop offset="100%" stopColor={T.success} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} vertical={false} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} axisLine={{ stroke: T.border }} tickLine={false} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} tickFormatter={formatK} axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTooltip />} />
                            <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                            <Area type="monotone" dataKey="cumGranted" name="Cumulative Granted" stroke={T.success} fill="url(#cumGrantedGrad)" strokeWidth={2} />
                            <Area type="monotone" dataKey="cumConsumed" name="Cumulative Consumed" stroke={T.warning} fill="url(#cumConsumedGrad)" strokeWidth={2} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            )}

            <div className="admin-charts-row">
                {/* Token Distribution Pie */}
                <div className="admin-chart-card">
                    <div className="admin-chart-title">User Balance Distribution</div>
                    {tokenDist.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie data={tokenDist} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                                    {tokenDist.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                                </Pie>
                                <Tooltip content={<ChartTooltip />} />
                                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : <div className="admin-chart-empty">No distribution data</div>}
                </div>

                {/* Top Generators Table */}
                <div className="admin-chart-card">
                    <div className="admin-chart-title">Top Generators</div>
                    {topGenerators.length > 0 ? (
                        <div style={{ maxHeight: 280, overflowY: 'auto' }}>
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>User</th>
                                        <th>Generations</th>
                                        <th>Tokens Used</th>
                                        <th>Balance</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {topGenerators.map((u, i) => (
                                        <tr key={i}>
                                            <td>{u.name || '—'}</td>
                                            <td style={{ fontWeight: 600 }}>{u.generations}</td>
                                            <td style={{ color: T.warning }}>{(u.tokens_used || 0).toLocaleString()}</td>
                                            <td style={{ color: T.success }}>{(u.token_balance || 0).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : <div className="admin-chart-empty">No generation activity</div>}
                </div>
            </div>
        </div>
    );
}
