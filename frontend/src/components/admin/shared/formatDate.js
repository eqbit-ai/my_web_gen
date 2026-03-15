/**
 * Format a date value for display in admin pages.
 * Handles ISO strings, Unix timestamps (seconds), and epoch milliseconds.
 */
export default function formatDate(d) {
    if (!d) return '—';
    try {
        let date;
        // Unix timestamp (seconds, possibly float) — e.g. "1773566627.98816"
        if (typeof d === 'number' || (typeof d === 'string' && /^\d+(\.\d+)?$/.test(d))) {
            const num = parseFloat(d);
            // If < 1e12, it's seconds; otherwise milliseconds
            date = new Date(num < 1e12 ? num * 1000 : num);
        } else {
            date = new Date(d);
        }
        if (isNaN(date.getTime())) return String(d);
        return date.toLocaleDateString(undefined, {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
    } catch {
        return String(d);
    }
}
