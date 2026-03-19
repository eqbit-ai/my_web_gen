import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import {
    BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import StatusBadge from './shared/StatusBadge';
import { adminGetGenerationStats, adminGetFailedGenerations, adminGetRedisFailedJobs } from '../../services/adminApi';
import formatDate from './shared/formatDate';

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
    const navigate = useNavigate();
    const [days, setDays] = useState(30);
    const [data, setData] = useState(null);
    const [recentFailures, setRecentFailures] = useState([]);
    const [redisFailures, setRedisFailures] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [res, failedRes, redisRes] = await Promise.all([
                adminGetGenerationStats(days),
                adminGetFailedGenerations(1, 5).catch(() => null),
                adminGetRedisFailedJobs().catch(() => null),
            ]);
            setData(res);
            setRecentFailures(failedRes?.failed_generations || []);
            setRedisFailures(redisRes?.failed_jobs || []);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [days]);

    useEffect(() => { load(); }, [load]);

    const dailyStats = data?.daily_stats || [];
    const stageFailures = data?.stage_failures || [];
    const jobStatuses = data?.redis_job_statuses || [];

    const dbCompleted = dailyStats.reduce((s, d) => s + (d.completed || 0), 0);
    const dbFailed = dailyStats.reduce((s, d) => s + (d.failed || 0), 0);
    const dbPending = dailyStats.reduce((s, d) => s + (d.pending || 0), 0);

    // Merge Redis job status counts (Redis may have failures not logged to DB)
    const redisCompleted = jobStatuses.find(j => j.name === 'Completed')?.value || 0;
    const redisFailed = jobStatuses.find(j => j.name === 'Failed')?.value || 0;
    const redisPending = (jobStatuses.find(j => j.name === 'Pending')?.value || 0)
        + (jobStatuses.find(j => j.name === 'Processing')?.value || 0);

    // Use the higher of DB vs Redis counts to capture all failures
    const totalCompleted = Math.max(dbCompleted, redisCompleted);
    const totalFailed = Math.max(dbFailed, redisFailed);
    const totalPending = Math.max(dbPending, redisPending);

    const pieData = [
        { name: 'Completed', value: totalCompleted },
        { name: 'Failed', value: totalFailed },
        { name: 'Pending', value: totalPending },
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
                        <div className="admin-stat-value">{totalCompleted}</div>
                        <div className="admin-stat-label">Completed</div>
                    </div>
                </div>
                <div className="admin-stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/admin/failed-generations')} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate('/admin/failed-generations'); }} role="button" tabIndex={0}>
                    <div className="admin-stat-body">
                        <div className="admin-stat-value" style={{ color: T.danger }}>{totalFailed}</div>
                        <div className="admin-stat-label">Failed <span style={{ fontSize: 10, color: T.muted }}>→ view all</span></div>
                    </div>
                </div>
                <div className="admin-stat-card admin-stat-accent-blue">
                    <div className="admin-stat-body">
                        <div className="admin-stat-value">
                            {totalCompleted + totalFailed > 0
                                ? `${Math.round((totalCompleted / (totalCompleted + totalFailed)) * 100)}%`
                                : '—'}
                        </div>
                        <div className="admin-stat-label">Success Rate</div>
                    </div>
                </div>
            </div>

            <div className="admin-charts-row">
                {/* Success/Fail Pie */}
                <div className="admin-chart-card">
                    <div className="admin-chart-title">Completion Breakdown</div>
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
                    ) : <div className="admin-chart-empty">No generation data</div>}
                </div>

                {/* Daily Bar */}
                <div className="admin-chart-card">
                    <div className="admin-chart-title">Daily Generations</div>
                    {loading ? (
                        <div className="admin-chart-empty">Loading...</div>
                    ) : dailyStats.length > 0 ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={dailyStats}>
                                <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                                <XAxis dataKey="date" tick={{ fill: T.muted, fontSize: 11 }} />
                                <YAxis tick={{ fill: T.muted, fontSize: 11 }} />
                                <Tooltip content={<ChartTooltip />} />
                                <Legend />
                                <Bar dataKey="completed" name="Completed" fill={T.success} radius={[4, 4, 0, 0]} />
                                <Bar dataKey="failed" name="Failed" fill={T.danger} radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : <div className="admin-chart-empty">No daily data</div>}
                </div>
            </div>

            {/* Stage Failures & Redis Status */}
            {(stageFailures.length > 0 || jobStatuses.length > 0) && (
                <div className="admin-charts-row" style={{ marginTop: 24 }}>
                    {stageFailures.length > 0 && (
                        <div className="admin-chart-card">
                            <div className="admin-chart-title">Failures by Stage</div>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={stageFailures} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                                    <XAxis type="number" tick={{ fill: T.muted, fontSize: 11 }} />
                                    <YAxis type="category" dataKey="stage" tick={{ fill: T.muted, fontSize: 11 }} width={100} />
                                    <Tooltip content={<ChartTooltip />} />
                                    <Bar dataKey="count" name="Failures" fill={T.danger} radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                    {jobStatuses.length > 0 && (
                        <div className="admin-chart-card">
                            <div className="admin-chart-title">Redis Job Status (live)</div>
                            <ResponsiveContainer width="100%" height={250}>
                                <PieChart>
                                    <Pie data={jobStatuses} cx="50%" cy="50%" innerRadius={50} outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                                        {jobStatuses.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                                    </Pie>
                                    <Tooltip content={<ChartTooltip />} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>
            )}

            {/* Recent DB Failures */}
            {recentFailures.length > 0 && (
                <div className="admin-card" style={{ marginTop: 24 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <div className="admin-card-title" style={{ margin: 0 }}>Recent Failures (DB)</div>
                        <button className="admin-btn admin-btn-sm" onClick={() => navigate('/admin/failed-generations')}>View All →</button>
                    </div>
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>User</th>
                                <th>Stage</th>
                                <th>Error</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recentFailures.map(f => (
                                <tr key={f.id}>
                                    <td><span className="admin-date-cell">{formatDate(f.created_at)}</span></td>
                                    <td>{f.user_email || f.user_id || '—'}</td>
                                    <td><StatusBadge status={f.stage_failed || 'unknown'} size="sm" /></td>
                                    <td style={{ color: T.danger, maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {f.error_message || '—'}
                                    </td>
                                    <td>{f.duration_ms ? `${(f.duration_ms / 1000).toFixed(1)}s` : '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Redis Failed Jobs */}
            {redisFailures.length > 0 && (
                <div className="admin-card" style={{ marginTop: 24 }}>
                    <div className="admin-card-title">Failed Jobs (Redis - Live)</div>
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Job ID</th>
                                <th>User</th>
                                <th>Stage</th>
                                <th>Error</th>
                            </tr>
                        </thead>
                        <tbody>
                            {redisFailures.map(f => (
                                <tr key={f.id}>
                                    <td style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>{f.id?.slice(0, 8) || '—'}</td>
                                    <td>{f.user_id || '—'}</td>
                                    <td>{f.stage || '—'}</td>
                                    <td style={{ color: T.danger, maxWidth: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {f.error || '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
