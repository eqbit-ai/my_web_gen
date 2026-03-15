import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { adminGetGrowthAnalytics } from '../../services/adminApi';

const T = { border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399' };

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

    const chartData = data?.data || data?.items || (Array.isArray(data) ? data : []);

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

            {/* Summary stats from chart data */}
            {chartData.length > 0 && (
                <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
                    <div className="admin-stat-card admin-stat-accent-blue">
                        <div className="admin-stat-body">
                            <div className="admin-stat-value">
                                {chartData[chartData.length - 1]?.total_users ?? '—'}
                            </div>
                            <div className="admin-stat-label">Total Users (latest)</div>
                        </div>
                    </div>
                    <div className="admin-stat-card admin-stat-accent-green">
                        <div className="admin-stat-body">
                            <div className="admin-stat-value">
                                {chartData.reduce((sum, d) => sum + (d.new_users || 0), 0)}
                            </div>
                            <div className="admin-stat-label">New Users ({days}d)</div>
                        </div>
                    </div>
                    <div className="admin-stat-card admin-stat-accent-purple">
                        <div className="admin-stat-body">
                            <div className="admin-stat-value">
                                {chartData[chartData.length - 1]?.active_users ?? '—'}
                            </div>
                            <div className="admin-stat-label">Active Users (latest)</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Chart */}
            <div className="admin-chart-card admin-chart-full">
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
                            <Area type="monotone" dataKey="total_users" name="Total Users" stroke={T.accent} fill={`${T.accent}30`} strokeWidth={2} />
                            <Area type="monotone" dataKey="new_users" name="New Users" stroke={T.success} fill={`${T.success}30`} strokeWidth={2} />
                            <Area type="monotone" dataKey="active_users" name="Active Users" stroke="#c084fc" fill="#c084fc30" strokeWidth={2} />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="admin-chart-empty">No growth data available for this period</div>
                )}
            </div>
        </div>
    );
}
