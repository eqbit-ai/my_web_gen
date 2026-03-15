import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import {
    AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { adminGetGrowthAnalytics } from '../../services/adminApi';

const T = { border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399' };
const PIE_COLORS = [T.success, '#f87171', T.accent, '#fbbf24'];

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

export default function GrowthChartPage() {
    const [days, setDays] = useState(30);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await adminGetGrowthAnalytics(days);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [days]);

    useEffect(() => { load(); }, [load]);

    // Merge daily_signups and daily_active into a single chart dataset
    const signups = data?.daily_signups || [];
    const active = data?.daily_active || [];
    const statusBreakdown = data?.status_breakdown || [];

    const chartData = (() => {
        const map = {};
        signups.forEach(d => { map[d.date] = { date: d.date, signups: d.count, active: 0 }; });
        active.forEach(d => {
            if (!map[d.date]) map[d.date] = { date: d.date, signups: 0, active: 0 };
            map[d.date].active = d.count;
        });
        return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
    })();

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">User Growth</h1>
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

            {/* Summary */}
            <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
                <div className="admin-stat-card admin-stat-accent-blue">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{data?.total_users ?? '—'}</div>
                        <div className="admin-stat-label">Total Users</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-green">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{data?.new_this_week ?? '—'}</div>
                        <div className="admin-stat-label">New This Week</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-purple">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">
                            {signups.reduce((s, d) => s + d.count, 0)}
                        </div>
                        <div className="admin-stat-label">Signups ({days}d)</div>
                    </div>
                </div>
            </div>

            <div className="admin-charts-row">
                {/* Main Chart */}
                <div className="admin-chart-card" style={{ flex: 2 }}>
                    <div className="admin-chart-title">
                        Signups & Active Users
                        <span className="admin-chart-period">Last {days} days</span>
                    </div>
                    {loading ? (
                        <div className="admin-loading-page" style={{ minHeight: 300 }}><RefreshCw size={20} className="admin-spinner" /> Loading...</div>
                    ) : chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={350}>
                            <AreaChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                                <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                                <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                                <Tooltip content={<ChartTooltip />} />
                                <Legend />
                                <Area type="monotone" dataKey="signups" name="Signups" stroke={T.success} fill={`${T.success}30`} strokeWidth={2} />
                                <Area type="monotone" dataKey="active" name="Active Users" stroke={T.accent} fill={`${T.accent}30`} strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="admin-chart-empty">No growth data available for this period</div>
                    )}
                </div>

                {/* Status Breakdown Pie */}
                <div className="admin-chart-card" style={{ flex: 1 }}>
                    <div className="admin-chart-title">User Status</div>
                    {statusBreakdown.length > 0 ? (
                        <ResponsiveContainer width="100%" height={350}>
                            <PieChart>
                                <Pie data={statusBreakdown} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                                    {statusBreakdown.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                                </Pie>
                                <Tooltip content={<ChartTooltip />} />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : <div className="admin-chart-empty">No status data</div>}
                </div>
            </div>
        </div>
    );
}
