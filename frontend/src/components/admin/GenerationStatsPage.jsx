import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import {
    BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { adminGetGenerationStats, adminGetGenerationSuccessRate } from '../../services/adminApi';

const T = { border: '#2a2a3a', text: '#e4e4e7', muted: '#71717a', accent: '#818cf8', success: '#34d399', danger: '#f87171', warning: '#fbbf24' };
const PIE_COLORS = [T.success, T.danger, T.warning, T.accent, '#c084fc'];

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

export default function GenerationStatsPage() {
    const [days, setDays] = useState(30);
    const [data, setData] = useState(null);
    const [successRate, setSuccessRate] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [d, sr] = await Promise.all([
                adminGetGenerationStats(days),
                adminGetGenerationSuccessRate().catch(() => null),
            ]);
            setData(d);
            setSuccessRate(sr);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [days]);

    useEffect(() => { load(); }, [load]);

    const chartData = data?.data || data?.items || (Array.isArray(data) ? data : []);
    const rateData = successRate?.data || successRate?.items || (Array.isArray(successRate) ? successRate : []);

    // Compute pie data from totals
    const totalSuccess = chartData.reduce((s, d) => s + (d.success || 0), 0);
    const totalFailed = chartData.reduce((s, d) => s + (d.failed || 0), 0);
    const pieData = [
        { name: 'Success', value: totalSuccess },
        { name: 'Failed', value: totalFailed },
    ].filter(d => d.value > 0);

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Generation Stats</h1>
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
                <div className="admin-stat-card admin-stat-accent-green">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{totalSuccess}</div>
                        <div className="admin-stat-label">Successful</div>
                    </div>
                </div>
                <div className="admin-stat-card">
                    <div className="admin-stat-icon" style={{ background: 'rgba(248,113,113,0.15)', color: T.danger }}><RefreshCw size={22} /></div>
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">{totalFailed}</div>
                        <div className="admin-stat-label">Failed</div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-blue">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">
                            {totalSuccess + totalFailed > 0
                                ? `${Math.round((totalSuccess / (totalSuccess + totalFailed)) * 100)}%`
                                : '—'}
                        </div>
                        <div className="admin-stat-label">Success Rate</div>
                    </div>
                </div>
            </div>

            <div className="admin-charts-row">
                {/* Success/Fail Pie */}
                <div className="admin-chart-card">
                    <div className="admin-chart-title">Success vs Failed</div>
                    {loading ? (
                        <div className="admin-chart-empty">Loading...</div>
                    ) : pieData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                                    {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                                </Pie>
                                <Tooltip content={<ChartTooltip />} />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : <div className="admin-chart-empty">No data</div>}
                </div>

                {/* Daily Bar */}
                <div className="admin-chart-card">
                    <div className="admin-chart-title">Daily Counts</div>
                    {loading ? (
                        <div className="admin-chart-empty">Loading...</div>
                    ) : chartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                                <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                                <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                                <Tooltip content={<ChartTooltip />} />
                                <Legend />
                                <Bar dataKey="success" name="Success" fill={T.success} radius={[4, 4, 0, 0]} />
                                <Bar dataKey="failed" name="Failed" fill={T.danger} radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : <div className="admin-chart-empty">No data</div>}
                </div>
            </div>
        </div>
    );
}
