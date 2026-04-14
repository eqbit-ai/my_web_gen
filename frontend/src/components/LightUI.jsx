// ────────────────────────────────────────────────────────────────
// LightUI — experimental light theme enhancer
// Mounts three things:
//   1. SVG wave background inside .dash-main-gradient (home tab)
//   2. Cmd+K command palette for fast navigation
//   3. Simple toast stack (window.luiToast("message", "success"))
// All rollback via removing two [LIGHT-UI] lines in App.js.
// ────────────────────────────────────────────────────────────────
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

// ── Wave background injection ──────────────────────────────────
const WAVE_SVG = `
  <svg viewBox="0 0 1600 600" preserveAspectRatio="none">
    <defs>
      <linearGradient id="luiWaveA" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#0171E4" stop-opacity="0.22"/>
        <stop offset="50%" stop-color="#3B8EF5" stop-opacity="0.16"/>
        <stop offset="100%" stop-color="#60A5FA" stop-opacity="0.12"/>
      </linearGradient>
      <linearGradient id="luiWaveB" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#60A5FA" stop-opacity="0.10"/>
        <stop offset="100%" stop-color="#0171E4" stop-opacity="0.16"/>
      </linearGradient>
    </defs>
    <path class="lui-wave-path" fill="url(#luiWaveA)" d="M0,320 C200,260 400,420 600,360 C800,300 1000,440 1200,380 C1400,320 1600,420 1800,360 L1800,600 L0,600 Z"/>
    <path class="lui-wave-path-2" fill="url(#luiWaveB)" d="M0,420 C220,380 420,500 620,440 C820,380 1020,500 1220,460 C1420,420 1620,500 1820,440 L1820,600 L0,600 Z"/>
  </svg>
`;

function useWaveBackground() {
  const location = useLocation();
  useEffect(() => {
    // Attach a wave layer to the dashboard home tab AND the generator shell.
    const target = location.pathname === '/dashboard'
      ? { selector: '.dash-main-gradient', className: 'lui-waves' }
      : location.pathname === '/generator'
        ? { selector: '.gn-layout', className: 'gn-wave-host' }
        : null;
    if (!target) return;

    let attached = null;
    let rafId = null;

    const attach = () => {
      const host = document.querySelector(target.selector);
      if (!host) {
        rafId = requestAnimationFrame(attach);
        return;
      }
      if (host.querySelector(`.${target.className}`)) return; // idempotent
      const wrap = document.createElement('div');
      wrap.className = target.className;
      wrap.setAttribute('aria-hidden', 'true');
      wrap.innerHTML = WAVE_SVG;
      host.prepend(wrap);
      attached = wrap;
    };
    attach();
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      if (attached && attached.parentNode) attached.parentNode.removeChild(attached);
    };
  }, [location.pathname]);
}

// ── Command Palette ────────────────────────────────────────────
const PALETTE_ITEMS = [
  { group: 'Navigate', label: 'Dashboard',        path: '/dashboard',          keywords: 'home start',      icon: 'home' },
  { group: 'Navigate', label: 'Projects',         path: '/dashboard?tab=projects', keywords: 'sites websites', icon: 'folder' },
  { group: 'Navigate', label: 'Templates',        path: '/dashboard?tab=templates', keywords: 'designs',      icon: 'layout' },
  { group: 'Navigate', label: 'Domains',          path: '/dashboard?tab=domains', keywords: 'dns buy',       icon: 'globe' },
  { group: 'Navigate', label: 'Inbox',            path: '/dashboard?tab=inbox', keywords: 'messages forms', icon: 'mail' },
  { group: 'Navigate', label: 'Gallery',          path: '/dashboard?tab=gallery', keywords: 'images photos', icon: 'image' },
  { group: 'Create',   label: 'New Website',      path: '/generator',          keywords: 'create build generate', icon: 'sparkles' },
  { group: 'Account',  label: 'Admin Panel',      path: '/admin',              keywords: 'settings manage', icon: 'shield' },
];

const ICONS = {
  home:     'M3 12l9-9 9 9v9a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-5h-2v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9z',
  folder:   'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z',
  layout:   'M3 3h18v6H3zM3 11h8v10H3zM13 11h8v10h-8z',
  globe:    'M12 22c5.5 0 10-4.5 10-10S17.5 2 12 2 2 6.5 2 12s4.5 10 10 10zM2 12h20M12 2c2.5 3 4 6.5 4 10s-1.5 7-4 10c-2.5-3-4-6.5-4-10s1.5-7 4-10z',
  mail:     'M3 5h18v14H3zM3 5l9 8 9-8',
  image:    'M3 3h18v18H3zM8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM21 15l-5-5L3 21',
  sparkles: 'M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2zM19 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1z',
  shield:   'M12 2l8 3v7c0 5-3.5 9-8 10-4.5-1-8-5-8-10V5z',
};

function CmdIcon({ name }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d={ICONS[name] || ICONS.home} />
    </svg>
  );
}

function CommandPalette({ open, onClose }) {
  const [query, setQuery] = useState('');
  const [activeIdx, setActiveIdx] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
      setQuery('');
      setActiveIdx(0);
    }
  }, [open]);

  const filtered = PALETTE_ITEMS.filter((it) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      it.label.toLowerCase().includes(q) ||
      it.keywords.toLowerCase().includes(q) ||
      it.group.toLowerCase().includes(q)
    );
  });

  useEffect(() => { setActiveIdx(0); }, [query]);

  const run = useCallback((item) => {
    if (!item) return;
    onClose();
    // Split out query param so react-router sees path + search
    const [path, search] = item.path.split('?');
    navigate(search ? { pathname: path, search: `?${search}` } : path);
  }, [navigate, onClose]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); onClose(); }
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIdx((i) => Math.min(i + 1, filtered.length - 1));
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIdx((i) => Math.max(i - 1, 0));
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        run(filtered[activeIdx]);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, filtered, activeIdx, onClose, run]);

  if (!open) return null;

  // Group items
  const groups = {};
  filtered.forEach((it, i) => {
    if (!groups[it.group]) groups[it.group] = [];
    groups[it.group].push({ ...it, _idx: i });
  });

  return (
    <div className="lui-cmdk-overlay" role="dialog" aria-modal="true" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="lui-cmdk">
        <div className="lui-cmdk-input-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            ref={inputRef}
            className="lui-cmdk-input"
            placeholder="Type to search, jump, or run a command..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoComplete="off"
            spellCheck="false"
          />
          <span className="lui-cmdk-kbd">ESC</span>
        </div>

        <div className="lui-cmdk-list">
          {filtered.length === 0 && <div className="lui-cmdk-empty">No results</div>}
          {Object.entries(groups).map(([group, items]) => (
            <div key={group}>
              <div className="lui-cmdk-group-label">{group}</div>
              {items.map((item) => (
                <div
                  key={item.label}
                  className={`lui-cmdk-item ${item._idx === activeIdx ? 'active' : ''}`}
                  onMouseEnter={() => setActiveIdx(item._idx)}
                  onMouseDown={(e) => { e.preventDefault(); run(item); }}
                  role="button"
                  tabIndex={-1}
                >
                  <CmdIcon name={item.icon} />
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          ))}
        </div>

        <div className="lui-cmdk-footer">
          <span><span className="lui-cmdk-kbd">↑↓</span> navigate</span>
          <span><span className="lui-cmdk-kbd">↵</span> select</span>
          <span><span className="lui-cmdk-kbd">⌘K</span> toggle</span>
        </div>
      </div>
    </div>
  );
}

// ── Toast stack ────────────────────────────────────────────────
function ToastStack({ toasts, onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="lui-toast-stack">
      {toasts.map((t) => (
        <div key={t.id} className={`lui-toast ${t.type || ''}`} role="status">
          <span style={{ flex: 1 }}>{t.message}</span>
          <button
            onClick={() => onDismiss(t.id)}
            aria-label="Dismiss"
            style={{ background: 'none', border: 'none', color: '#9CA3AF', cursor: 'pointer', fontSize: 16, lineHeight: 1, padding: 0 }}
          >×</button>
        </div>
      ))}
    </div>
  );
}

// ── Root component ─────────────────────────────────────────────
export default function LightUI() {
  useWaveBackground();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [toasts, setToasts] = useState([]);

  // Expose a window-level toast helper so any page can call luiToast(...)
  useEffect(() => {
    const push = (message, type = 'info', ttl = 3500) => {
      const id = Math.random().toString(36).slice(2);
      setToasts((ts) => [...ts, { id, message, type }]);
      if (ttl) setTimeout(() => setToasts((ts) => ts.filter((x) => x.id !== id)), ttl);
    };
    window.luiToast = push;
    return () => { delete window.luiToast; };
  }, []);

  // Global Cmd+K / Ctrl+K shortcut
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const dismiss = useCallback((id) => {
    setToasts((ts) => ts.filter((x) => x.id !== id));
  }, []);

  return (
    <>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      <ToastStack toasts={toasts} onDismiss={dismiss} />
    </>
  );
}
