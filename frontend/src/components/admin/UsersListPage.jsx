import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, Search, Download, Users } from 'lucide-react';
import StatusBadge from './shared/StatusBadge';
import AdminTable from './shared/AdminTable';
import { adminGetUsers, adminExportUsers, adminBulkAction } from '../../services/adminApi';

function formatDate(d) {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch { return d; }
}

export default function UsersListPage() {
    const navigate = useNavigate();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [activeFilter, setActiveFilter] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedIds, setSelectedIds] = useState([]);
    const [bulkAction, setBulkAction] = useState('');
    const [bulkLoading, setBulkLoading] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const isActive = activeFilter === '' ? null : activeFilter === 'true';
            const res = await adminGetUsers(page, 20, search, isActive);
            setData(res);
        } catch (e) { setError(e.message); }
        finally { setLoading(false); }
    }, [page, search, activeFilter]);

    useEffect(() => { load(); }, [load]);

    const handleSearch = (e) => {
        e.preventDefault();
        setSearch(searchInput);
        setPage(1);
    };

    const handleExport = async () => {
        try {
            const blob = await adminExportUsers();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'users_export.csv'; a.click();
            URL.revokeObjectURL(url);
        } catch {}
    };

    const handleBulkAction = async () => {
        if (!bulkAction || selectedIds.length === 0) return;
        setBulkLoading(true);
        try {
            await adminBulkAction(bulkAction, selectedIds);
            setSelectedIds([]);
            setBulkAction('');
            load();
        } catch {}
        setBulkLoading(false);
    };

    const users = Array.isArray(data) ? data : data?.users || data?.items || [];
    const total = data?.total || users.length;

    const columns = [
        { key: 'company_name', label: 'Name / Company', render: (v, row) => (
            <div className="admin-user-cell">
                <strong>{v || row.name || '—'}</strong>
                <span>{row.email}</span>
            </div>
        )},
        { key: 'email', label: 'Email', render: () => null },
        { key: 'license_number', label: 'Licence', render: (v, row) => (
            <span className="admin-license">{v || row.licence_number || '—'}</span>
        )},
        { key: 'token_balance', label: 'Tokens', render: (v, row) => v ?? row.tokens ?? '—' },
        { key: 'is_active', label: 'Status', render: v => (
            <StatusBadge status={v !== false ? 'active' : 'disabled'} size="sm" />
        )},
        { key: 'created_at', label: 'Created', render: v => <span className="admin-date-cell">{formatDate(v)}</span> },
    ];

    // Remove hidden email column
    const visibleColumns = columns.filter(c => c.key !== 'email');

    if (error) {
        return <div className="admin-alert admin-alert-error"><span>{error}</span><button onClick={load}>Retry</button></div>;
    }

    return (
        <div>
            <div className="admin-page-header">
                <h1 className="admin-page-title">Users</h1>
                <div className="admin-actions">
                    <button className="admin-btn" onClick={handleExport}><Download size={14} /> Export CSV</button>
                    <button className="admin-btn" onClick={load}><RefreshCw size={14} /> Refresh</button>
                </div>
            </div>

            {/* Search & Filter */}
            <div className="admin-toolbar">
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, flex: 1 }}>
                    <div style={{ position: 'relative', flex: 1, maxWidth: 400 }}>
                        <Search size={14} style={{ position: 'absolute', left: 10, top: 11, color: '#71717a' }} />
                        <input
                            className="admin-search"
                            style={{ paddingLeft: 32, width: '100%' }}
                            placeholder="Search by name, email, or licence..."
                            value={searchInput}
                            onChange={e => setSearchInput(e.target.value)}
                        />
                    </div>
                    <button type="submit" className="admin-btn admin-btn-primary">Search</button>
                    <select
                        className="admin-search"
                        style={{ width: 'auto' }}
                        value={activeFilter}
                        onChange={e => { setActiveFilter(e.target.value); setPage(1); }}
                    >
                        <option value="">All Users</option>
                        <option value="true">Active</option>
                        <option value="false">Disabled</option>
                    </select>
                </form>
                <span className="admin-count">{total} users</span>
            </div>

            {/* Bulk Actions */}
            {selectedIds.length > 0 && (
                <div className="admin-bulk-bar">
                    <span>{selectedIds.length} selected</span>
                    <select className="admin-input" style={{ width: 'auto' }} value={bulkAction} onChange={e => setBulkAction(e.target.value)}>
                        <option value="">Bulk action...</option>
                        <option value="disable">Disable</option>
                        <option value="enable">Enable</option>
                        <option value="verify_licence">Verify Licence</option>
                    </select>
                    <button className="admin-btn admin-btn-primary admin-btn-sm" onClick={handleBulkAction} disabled={!bulkAction || bulkLoading}>
                        {bulkLoading ? 'Applying...' : 'Apply'}
                    </button>
                    <button className="admin-btn admin-btn-sm" onClick={() => setSelectedIds([])}>Clear</button>
                </div>
            )}

            <AdminTable
                columns={visibleColumns}
                data={users}
                loading={loading}
                emptyMessage="No users found"
                page={page}
                total={total}
                limit={20}
                onPageChange={setPage}
                selectable
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
                onRowClick={(row) => navigate(`/admin/users/${row.id}`)}
            />
        </div>
    );
}
