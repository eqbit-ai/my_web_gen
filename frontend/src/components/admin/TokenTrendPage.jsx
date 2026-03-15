import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import {
    AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { adminGetTokenConsumption } from '../../services/adminApi';

const T = { border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399', warning: '#fbbf24', danger: '#f87171' };
const PIE_COLORS = [T.accent, T.success, T.warning, T.danger, '#c084fc', '#60a5fa'];

const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null;
    return (
        <div className="admin-chart-tooltip">
            <div className="admin-chart-tooltip-label">{label}</div>
            {(payload || []).map((p, i) => (
                <div key={i} className="admin-chart-tooltip-row">
                    <span>{p.name}</span>
                    <strong style={{ color: p.color || p.fill }}>{p.value}</strong>
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

    const chartData = data?.data || data?.items || (Array.isArray(data) ? data : []);
    const byType = data?.by_type || data?.breakdown || null;

    // Compute totals
    const totalConsumed = chartData.reduce((s, d) => s + (d.consumed || 0), 0);
    const totalGranted = chartData.reduce((s, d) => s + (d.granted || 0), 0);

    // Build pie data from by_type object or from totals
    const pieData = (() => {
        if (byType && typeof byType === 'object') {
            return Object.entries(byType).map(([name, value]) => ({ name, value: typeof value === 'number' ? value : 0 })).filter(d => d.value > 0);
        }
        // Fallback: consumed vs granted
        return [
            { name: 'Consumed', value: totalConsumed },
            { name: 'Granted', value: totalGranted },
        ].filter(d => d.value > 0);
    })();

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

            {/* Summary */}
            <div className="admin-stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
                <div className="admin-stat-card admin-stat-accent-orange">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{totalConsumed}</div>
                        <div className="admin-stat-label">Total Consumed</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-green">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{totalGranted}</div>
                        <div className="admin-stat-label">Total Granted</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-blue">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">
                            {totalGranted > 0 ? `${Math.round((totalConsumed / totalGranted) * 100)}%` : '—'}
                        </div>
                        <div className="admin-stat-label">Utilization</div>
                    </div>
                </div>
            </div>

            {/* Main Area Chart */}
            <div className="admin-chart-card admin-chart-full" style={{ marginBottom: 24 }}>
                <div className="admin-chart-title">
                    Daily Consumption
                    <span className="admin-chart-period">Last {days} days</span>
                </div>
                {loading ? (
                    <div className="admin-loading-page" style={{ minHeight: 300 }}><RefreshCw size={20} className="admin-spinner" /> Loading...</div>
                ) : chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                            <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                            <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                            <Tooltip content={<ChartTooltip />} />
                            <Legend />
                            <Area type="monotone" dataKey="consumed" name="Consumed" stroke={T.warning} fill={`${T.warning}30`} strokeWidth={2} />
                            <Area type="monotone" dataKey="granted" name="Granted" stroke={T.success} fill={`${T.success}30`} strokeWidth={2} />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : <div className="admin-chart-empty">No token data available for this period</div>}
            </div>

            {/* Breakdown Pie */}
            <div className="admin-charts-row">
                <div className="admin-chart-card">
                    <div className="admin-chart-title">Breakdown by Type</div>
                    {pieData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                                    {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                                </Pie>
                                <Tooltip content={<ChartTooltip />} />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : <div className="admin-chart-empty">No breakdown data</div>}
                </div>

                {/* Consumption Table */}
                <div className="admin-chart-card">
                    <div className="admin-chart-title">Recent Daily Data</div>
                    {chartData.length > 0 ? (
                        <div style={{ maxHeight: 280, overflowY: 'auto' }}>
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Consumed</th>
                                        <th>Granted</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {chartData.slice(-10).reverse().map((d, i) => (
                                        <tr key={i}>
                                            <td>{d.date}</td>
                                            <td style={{ color: T.warning, fontWeight: 600 }}>{d.consumed || 0}</td>
                                            <td style={{ color: T.success, fontWeight: 600 }}>{d.granted || 0}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : <div className="admin-chart-empty">No data</div>}
                </div>
            </div>
        </div>
    );
}
