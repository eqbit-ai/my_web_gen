import React from 'react';

const STATUS_MAP = {
    active: 'green', published: 'green', verified: 'green', success: 'green', healthy: 'green',
    closed: 'green', enabled: 'green', completed: 'green', online: 'green',
    pending: 'yellow', processing: 'yellow', queued: 'yellow', half_open: 'yellow',
    scheduled: 'yellow', warning: 'yellow', provisioning: 'yellow',
    failed: 'red', expired: 'red', suspended: 'red', error: 'red', open: 'red',
    disabled: 'red', rejected: 'red', offline: 'red',
    draft: 'gray', inactive: 'gray', unknown: 'gray',
};

export default function StatusBadge({ status, label, size = 'md' }) {
    const normalized = (status || 'unknown').toLowerCase().replace(/[\s-]/g, '_');
    const color = STATUS_MAP[normalized] || 'gray';
    const cls = `admin-badge admin-badge-${color}${size === 'sm' ? ' admin-badge-sm' : ''}`;
    return <span className={cls}>{label || status || 'Unknown'}</span>;
}
