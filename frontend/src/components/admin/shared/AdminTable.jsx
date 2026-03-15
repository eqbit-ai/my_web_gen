import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

const T = {
    bg: '#0a0a0f', surface: '#12121a', surfaceHover: '#1a1a28', border: '#2a2a3a',
    text: '#e4e4e7', muted: '#71717a', accent: '#818cf8',
};

export default function AdminTable({
    columns = [],
    data,
    loading = false,
    emptyMessage = 'No data found',
    page,
    total,
    limit = 20,
    onPageChange,
    selectable = false,
    selectedIds = [],
    onSelectionChange,
    onRowClick,
    rowKey = 'id',
}) {
    const [sortCol, setSortCol] = useState(null);
    const [sortDir, setSortDir] = useState('asc');

    const rows = data || [];

    const sorted = useMemo(() => {
        if (!sortCol) return rows;
        const col = columns.find(c => c.key === sortCol);
        if (!col) return rows;
        return [...rows].sort((a, b) => {
            const av = a[sortCol], bv = b[sortCol];
            if (av == null) return 1;
            if (bv == null) return -1;
            const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv));
            return sortDir === 'asc' ? cmp : -cmp;
        });
    }, [rows, sortCol, sortDir, columns]);

    const handleSort = (key) => {
        if (sortCol === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
        else { setSortCol(key); setSortDir('asc'); }
    };

    const toggleAll = (checked) => {
        if (onSelectionChange) {
            onSelectionChange(checked ? rows.map(r => r[rowKey]) : []);
        }
    };

    const toggleOne = (id) => {
        if (onSelectionChange) {
            onSelectionChange(
                selectedIds.includes(id) ? selectedIds.filter(x => x !== id) : [...selectedIds, id]
            );
        }
    };

    const totalPages = total && limit ? Math.max(1, Math.ceil(total / limit)) : 1;

    if (loading) {
        return (
            <div className="admin-table-wrap">
                <table className="admin-table">
                    <thead>
                        <tr>
                            {selectable && <th className="admin-table" style={{ width: 40 }}></th>}
                            {columns.map(col => (
                                <th key={col.key} style={col.width ? { width: col.width } : undefined}>
                                    <div className="admin-skeleton" style={{ width: '60%', height: 12 }} />
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {[...Array(5)].map((_, i) => (
                            <tr key={i}>
                                {selectable && <td><div className="admin-skeleton" style={{ width: 16, height: 16 }} /></td>}
                                {columns.map(col => (
                                    <td key={col.key}><div className="admin-skeleton" style={{ width: '80%', height: 14 }} /></td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    }

    return (
        <div>
            <div className="admin-table-wrap">
                <table className="admin-table">
                    <thead>
                        <tr>
                            {selectable && (
                                <th style={{ width: 40, padding: '10px 12px' }}>
                                    <input
                                        type="checkbox"
                                        className="admin-checkbox"
                                        checked={rows.length > 0 && selectedIds.length === rows.length}
                                        onChange={e => toggleAll(e.target.checked)}
                                    />
                                </th>
                            )}
                            {columns.map(col => (
                                <th
                                    key={col.key}
                                    style={{ cursor: col.sortable !== false ? 'pointer' : 'default', ...(col.width ? { width: col.width } : {}) }}
                                    onClick={() => col.sortable !== false && handleSort(col.key)}
                                >
                                    <div className="admin-th-inner">
                                        {col.label}
                                        {sortCol === col.key && (
                                            sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
                                        )}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {sorted.map((row, idx) => (
                            <tr
                                key={row[rowKey] || idx}
                                className={selectedIds.includes(row[rowKey]) ? 'admin-row-selected' : ''}
                                style={onRowClick ? { cursor: 'pointer' } : undefined}
                                onClick={() => onRowClick && onRowClick(row)}
                            >
                                {selectable && (
                                    <td style={{ padding: '10px 12px' }} onClick={e => e.stopPropagation()}>
                                        <input
                                            type="checkbox"
                                            className="admin-checkbox"
                                            checked={selectedIds.includes(row[rowKey])}
                                            onChange={() => toggleOne(row[rowKey])}
                                        />
                                    </td>
                                )}
                                {columns.map(col => (
                                    <td key={col.key}>
                                        {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                                    </td>
                                ))}
                            </tr>
                        ))}
                        {sorted.length === 0 && (
                            <tr>
                                <td colSpan={columns.length + (selectable ? 1 : 0)}>
                                    <div className="admin-empty">{emptyMessage}</div>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {onPageChange && totalPages > 1 && (
                <div className="admin-pagination">
                    <button onClick={() => onPageChange(page - 1)} disabled={page <= 1}>
                        <ChevronLeft size={14} />
                    </button>
                    <span>Page {page} of {totalPages}</span>
                    <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}>
                        <ChevronRight size={14} />
                    </button>
                </div>
            )}
        </div>
    );
}
