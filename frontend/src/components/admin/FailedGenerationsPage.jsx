import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import { adminGetFailedGenerations, adminGetRedisFailedJobs, adminRetryGeneration } from '../../services/adminApi';
import formatDate from './shared/formatDate';


export default function FailedGenerationsPage() {
    const [dbFailures, setDbFailures] = useState([]);
    const [redisFailures, setRedisFailures] = useState([]);
    const [dbTotal, setDbTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [retrying, setRetrying] = useState(null);
    const limit = 20;

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [dbRes, redisRes] = await Promise.all([
                adminGetFailedGenerations(page, limit).catch(() => null),
                adminGetRedisFailedJobs().catch(() => null),
            ]);
            setDbFailures(dbRes?.failed_generations || []);
            setDbTotal(dbRes?.total || 0);
            setRedisFailures(redisRes?.failed_jobs || []);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page]);

    useEffect(() => { load(); }, [load]);

    const handleRetry = async (logId) => {
        setRetrying(logId);
        try {
            await adminRetryGeneration(logId);
            load();
        } catch { /* ignore */ }
        finally { setRetrying(null); }
    };

    const totalPages = Math.ceil(dbTotal / limit) || 1;

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Failed Generations</h1>
                <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
            </div>

            {/* Redis Failed Jobs (Live) */}
            <div className="admin-card" style={{ marginBottom: 24 }}>
                <div className="admin-card-title">Failed Jobs — Redis (Live Queue)</div>
                {loading ? (
                    <div className="admin-loading-page" style={{ minHeight: 100 }}><RefreshCw size={16} className="admin-spinner" /> Loading...</div>
                ) : redisFailures.length > 0 ? (
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Job ID</th>
                                <th>User</th>
                                <th>Stage</th>
                                <th>Error</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {redisFailures.map(f => (
                                <tr key={f.id}>
                                    <td style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>{f.id?.slice(0, 12) || '—'}</td>
                                    <td>{f.user_id || '—'}</td>
                                    <td><StatusBadge status={f.stage || 'unknown'} size="sm" /></td>
                                    <td style={{ color: '#f87171', maxWidth: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {f.error || '—'}
                                    </td>
                                    <td><span className="admin-date-cell">{formatDate(f.completed_at || f.created_at)}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div style={{ padding: 24, textAlign: 'center', color: '#71717a' }}>No failed jobs in Redis queue</div>
                )}
            </div>

            {/* DB Failed Generations */}
            <div className="admin-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <div className="admin-card-title" style={{ margin: 0 }}>Failed Generations — Database ({dbTotal})</div>
                    {totalPages > 1 && (
                        <div className="admin-pagination">
                            <button className="admin-btn admin-btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
                            <span style={{ fontSize: 13, color: '#71717a' }}>Page {page} / {totalPages}</span>
                            <button className="admin-btn admin-btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
                        </div>
                    )}
                </div>
                {loading ? (
                    <div className="admin-loading-page" style={{ minHeight: 100 }}><RefreshCw size={16} className="admin-spinner" /> Loading...</div>
                ) : dbFailures.length > 0 ? (
                    <table className="admin-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>User</th>
                                <th>Stage</th>
                                <th>Error</th>
                                <th>Duration</th>
                                <th>Tokens</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {dbFailures.map(f => (
                                <tr key={f.id}>
                                    <td><span className="admin-date-cell">{formatDate(f.created_at)}</span></td>
                                    <td>{f.user_email || f.user_id || '—'}</td>
                                    <td><StatusBadge status={f.stage_failed || 'unknown'} size="sm" /></td>
                                    <td style={{ color: '#f87171', maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                        {f.error_message || '—'}
                                    </td>
                                    <td>{f.duration_ms ? `${(f.duration_ms / 1000).toFixed(1)}s` : '—'}</td>
                                    <td>{f.tokens_consumed ?? '—'}</td>
                                    <td>
                                        <button
                                            className="admin-btn admin-btn-sm"
                                            disabled={retrying === f.id}
                                            onClick={() => handleRetry(f.id)}
                                        >
                                            {retrying === f.id ? '...' : 'Retry'}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div style={{ padding: 24, textAlign: 'center', color: '#71717a' }}>No failed generations in database</div>
                )}
            </div>
        </div>
    );
}
