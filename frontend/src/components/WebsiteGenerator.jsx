/* eslint-disable no-console */
// src/components/WebsiteGenerator.jsx
// Layout: Lovable/Base44 style — Chat sidebar (left) + Preview (right)

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import JSZip from 'jszip';
import {
    Download, Code, Eye, RefreshCw, Rocket, Sparkles,
    MousePointer2, X, Send, ArrowLeft, Undo2, Redo2,
    Save, Search, Palette, RotateCcw, Settings,
    Monitor, Smartphone, Layers,
    AlertTriangle, CheckCircle, Info, Keyboard, Wifi, WifiOff,
    ChevronRight, Type, MessageSquare, FileText, Paperclip, Square, ImageIcon
} from 'lucide-react';
import Preview from './Preview';
import CodeEditor from './CodeEditor';
import DeployModal from './DeployModal';
import SectionEditor from './SectionEditor';
import SeoEditor from './SeoEditor';
import GalleryPicker from './GalleryPicker';
import {
    generateWebsiteStream, clearSession, editElement, uploadFile, uploadFiles,
    saveProject, getTemplates, getTemplateFull, getSections, syncSession,
    submitJob, getJobStatus, restoreSession, getSession,
    searchDomains, purchaseDomain, purchaseDomainAndWait,
} from '../services/api';
import config from '../config';

const SESSION_STORAGE_KEY = 'meydan_generator_session';
const ONBOARDING_KEY = 'meydan_onboarding_complete';
// Cap on the in-memory undo/redo history. Each version stores full
// html/css/js + the multipage `pages` dict — roughly 50–100KB per entry.
// Without a cap, a long editing session can grow to 10s of MB and crash
// the tab on lower-end devices. 50 entries ≈ 5MB worst case.
const MAX_HISTORY_VERSIONS = 50;

// ---------------------------------------------------------------------------
// Error Banner Component (UX Enhancement #1)
// ---------------------------------------------------------------------------
const parseErrorType = (error) => {
    if (!error) return { type: 'error', message: 'Something went wrong. Please try again.', retryDelay: 0 };
    const msg = typeof error === 'string' ? error : error.message || '';
    const lower = msg.toLowerCase();
    if (lower.includes('circuit') || lower.includes('503') || lower.includes('unavailable')) {
        const match = msg.match(/(\d+)\s*second/);
        const secs = match ? parseInt(match[1], 10) : 30;
        return { type: 'warning', message: `AI service is temporarily unavailable. Retrying in ${secs} seconds...`, retryDelay: secs };
    }
    if (lower.includes('429') || lower.includes('rate limit') || lower.includes('too many')) {
        const match = msg.match(/(\d+)\s*second/);
        const secs = match ? parseInt(match[1], 10) : 60;
        return { type: 'warning', message: `Rate limit reached. Please wait ${secs} seconds before generating again.`, retryDelay: secs };
    }
    if (lower.includes('timeout') || lower.includes('took too long') || lower.includes('timed out')) {
        return { type: 'error', message: 'Generation took too long. Please try again.', retryDelay: 0 };
    }
    if (lower.includes('save') || lower.includes('auto-save')) {
        return { type: 'info', message: msg, retryDelay: 0, autoDismiss: true };
    }
    return { type: 'error', message: msg || 'Something went wrong. Please try again.', retryDelay: 0 };
};

const ErrorBanner = ({ error, onRetry, onDismiss }) => {
    const [dismissing, setDismissing] = useState(false);
    const parsed = useMemo(() => parseErrorType(error), [error]);

    useEffect(() => {
        if (parsed.autoDismiss) {
            const timer = setTimeout(() => handleDismiss(), 10000);
            return () => clearTimeout(timer);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [parsed.autoDismiss]);

    const handleDismiss = () => {
        setDismissing(true);
        setTimeout(() => onDismiss(), 300);
    };

    const iconMap = { error: AlertTriangle, warning: AlertTriangle, info: Info };
    const Icon = iconMap[parsed.type] || AlertTriangle;

    return (
        <div className={`error-banner error-banner-${parsed.type} ${dismissing ? 'error-banner-dismissing' : ''}`}>
            <span className="error-banner-icon"><Icon size={18} /></span>
            <div className="error-banner-content">
                <span className="error-banner-message">{parsed.message}</span>
            </div>
            <div className="error-banner-actions">
                {onRetry && <button className="error-banner-btn" onClick={onRetry}>Retry</button>}
                <button className="error-banner-dismiss" onClick={handleDismiss}><X size={16} /></button>
            </div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// Toast Notification System (UX Enhancement #5)
// ---------------------------------------------------------------------------
const ToastContainer = ({ toasts, onDismiss }) => {
    return (
        <div className="toast-container">
            {toasts.map((t) => (
                <ToastItem key={t.id} toast={t} onDismiss={() => onDismiss(t.id)} />
            ))}
        </div>
    );
};

// Thumbs up/down on each AI reply. Posts to /api/edit-feedback (uses
// session_id fallback to find the latest edit_log row server-side, so we
// don't need to plumb edit_log_id through the websocket/stream payload).
const FeedbackThumbs = ({ msgKey, sessionId, addToast }) => {
    const [picked, setPicked] = React.useState(null); // 'up' | 'down' | null
    const [busy, setBusy] = React.useState(false);
    const send = async (rating) => {
        if (busy || picked) return;
        setBusy(true);
        try {
            const { submitEditFeedback } = await import('../services/api');
            await submitEditFeedback({ sessionId, rating });
            setPicked(rating);
            if (addToast) addToast(rating === 'up' ? 'Thanks for the feedback!' : 'Got it — we\'ll improve this.', 'info', 2500);
        } catch (e) {
            if (addToast) addToast(e.message || 'Failed to send feedback', 'error');
        } finally {
            setBusy(false);
        }
    };
    return (
        <div className="gn-feedback-row" style={{ display: 'inline-flex', gap: 4, marginTop: 6 }}>
            <button
                type="button"
                className={`gn-feedback-btn ${picked === 'up' ? 'is-picked' : ''}`}
                onClick={() => send('up')}
                disabled={busy || !!picked}
                aria-label="Helpful"
                title="Helpful"
                style={{
                    background: picked === 'up' ? 'rgba(134,239,203,0.18)' : 'transparent',
                    border: '1px solid rgba(17,24,39,0.12)', borderRadius: 6,
                    padding: '3px 8px', cursor: picked || busy ? 'default' : 'pointer',
                    color: picked === 'up' ? '#065F46' : '#4B5563',
                    fontSize: 12, lineHeight: 1, transition: 'all 0.15s',
                }}
            >👍</button>
            <button
                type="button"
                className={`gn-feedback-btn ${picked === 'down' ? 'is-picked' : ''}`}
                onClick={() => send('down')}
                disabled={busy || !!picked}
                aria-label="Not helpful"
                title="Not helpful"
                style={{
                    background: picked === 'down' ? 'rgba(239,68,68,0.10)' : 'transparent',
                    border: '1px solid rgba(17,24,39,0.12)', borderRadius: 6,
                    padding: '3px 8px', cursor: picked || busy ? 'default' : 'pointer',
                    color: picked === 'down' ? '#991B1B' : '#4B5563',
                    fontSize: 12, lineHeight: 1, transition: 'all 0.15s',
                }}
            >👎</button>
        </div>
    );
};

const ToastItem = ({ toast, onDismiss }) => {
    const [dismissing, setDismissing] = useState(false);
    const iconMap = {
        success: <CheckCircle size={16} />,
        error: <AlertTriangle size={16} />,
        warning: <AlertTriangle size={16} />,
        info: <Info size={16} />,
    };

    const handleClose = () => {
        setDismissing(true);
        setTimeout(onDismiss, 300);
    };

    return (
        <div className={`toast-item toast-${toast.type} ${dismissing ? 'toast-dismissing' : ''}`}>
            <span className="toast-item-icon">{iconMap[toast.type] || iconMap.info}</span>
            <span className="toast-item-message">{toast.message}</span>
            <button className="toast-item-close" onClick={handleClose}><X size={14} /></button>
        </div>
    );
};

// ---------------------------------------------------------------------------
// Keyboard Shortcuts Modal (UX Enhancement #2)
// ---------------------------------------------------------------------------
const isMac = typeof navigator !== 'undefined' && /Mac/.test(navigator.platform);
const modKey = isMac ? 'Cmd' : 'Ctrl';

const SHORTCUTS = [
    {
        group: 'Editing',
        items: [
            { label: 'Undo', keys: [modKey, 'Z'] },
            { label: 'Redo', keys: [modKey, 'Shift', 'Z'] },
            { label: 'Save project', keys: [modKey, 'S'] },
        ],
    },
    {
        group: 'Generation',
        items: [
            { label: 'Send message', keys: [modKey, 'Enter'] },
        ],
    },
    {
        group: 'Actions',
        items: [
            { label: 'Download HTML', keys: [modKey, 'D'] },
            { label: 'Show keyboard shortcuts', keys: ['?'] },
        ],
    },
];

const KeyboardShortcutsModal = ({ onClose }) => {
    useEffect(() => {
        const handler = (e) => {
            if (e.key === 'Escape' || e.key === '?') { e.preventDefault(); onClose(); }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [onClose]);

    return (
        <div className="shortcuts-overlay" onClick={onClose} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClose(e); }} role="button" tabIndex={0}>
            <div className="shortcuts-modal" onClick={(e) => e.stopPropagation()} onKeyDown={e => e.stopPropagation()} role="presentation">
                <div className="shortcuts-header">
                    <h3><Keyboard size={18} /> Keyboard Shortcuts</h3>
                    <button className="gn-icon-btn" onClick={onClose}><X size={18} /></button>
                </div>
                <div className="shortcuts-body">
                    {SHORTCUTS.map((group) => (
                        <div key={group.group} className="shortcuts-group">
                            <div className="shortcuts-group-title">{group.group}</div>
                            <div className="shortcuts-list">
                                {group.items.map((item) => (
                                    <div key={item.label} className="shortcut-row">
                                        <span className="shortcut-label">{item.label}</span>
                                        <span className="shortcut-keys">
                                            {item.keys.map((k, ki) => (
                                                <React.Fragment key={ki}>
                                                    {ki > 0 && <span className="shortcut-plus">+</span>}
                                                    <span className="shortcut-key">{k}</span>
                                                </React.Fragment>
                                            ))}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
                <div className="shortcuts-footer">
                    Press <strong>?</strong> or <strong>Esc</strong> to close
                </div>
            </div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// Connection Status Indicator (UX Enhancement #3)
// ---------------------------------------------------------------------------
const ConnectionIndicator = ({ status }) => {
    const labels = { connected: 'Connected', reconnecting: 'Reconnecting...', disconnected: 'Disconnected' };
    const icons = { connected: Wifi, reconnecting: Wifi, disconnected: WifiOff };
    const Icon = icons[status] || Wifi;
    return (
        <div className={`connection-status ${status}`}>
            <span className="connection-dot" />
            <Icon size={12} />
            <span>{labels[status]}</span>
        </div>
    );
};

// ---------------------------------------------------------------------------
// Generation Progress Detail (UX Enhancement #4)
// ---------------------------------------------------------------------------
const GENERATION_STAGES = [
    { key: 'enhance', label: 'Analyzing your request...' },
    { key: 'plan', label: 'Planning website structure...' },
    { key: 'html', label: 'Building HTML layout...' },
    { key: 'js', label: 'Adding interactions...' },
    { key: 'post', label: 'Running quality checks...' },
];

const GenerationProgress = ({ currentStage, message }) => {
    const stageIndex = GENERATION_STAGES.findIndex(s => {
        const msgLower = (message || '').toLowerCase();
        if (s.key === 'enhance' && (msgLower.includes('analyz') || msgLower.includes('enhanc') || msgLower.includes('brief'))) return true;
        if (s.key === 'plan' && (msgLower.includes('plan') || msgLower.includes('structure'))) return true;
        if (s.key === 'html' && (msgLower.includes('html') || msgLower.includes('building') || msgLower.includes('generat'))) return true;
        if (s.key === 'js' && (msgLower.includes('javascript') || msgLower.includes('interaction') || msgLower.includes('js'))) return true;
        if (s.key === 'post' && (msgLower.includes('quality') || msgLower.includes('validat') || msgLower.includes('assembl'))) return true;
        return false;
    });
    const activeIdx = stageIndex >= 0 ? stageIndex : currentStage;
    const progressPct = Math.min(((activeIdx + 1) / GENERATION_STAGES.length) * 100, 100);

    return (
        <div className="gen-progress-overlay">
            <div className="gen-progress-spinner" />
            <div className="gen-progress-title">{message || 'Generating your website...'}</div>
            <div className="gen-progress-bar-wrap">
                <div className="gen-progress-bar">
                    <div className="gen-progress-bar-fill" style={{ width: `${progressPct}%` }} />
                </div>
            </div>
            <div className="gen-progress-stages">
                {GENERATION_STAGES.map((stage, i) => {
                    const isDone = i < activeIdx;
                    const isActive = i === activeIdx;
                    return (
                        <div key={stage.key} className={`gen-progress-stage ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`}>
                            <span className="gen-stage-icon">
                                {isDone ? (
                                    <CheckCircle size={16} className="gen-stage-check" />
                                ) : (
                                    <span className="gen-stage-dot" />
                                )}
                            </span>
                            <span>{stage.label}</span>
                        </div>
                    );
                })}
            </div>
            <div className="gen-progress-time">Web AI is designing your website -- this takes about few minutes</div>
        </div>
    );
};

// ---------------------------------------------------------------------------
// Onboarding Tour (UX Enhancement #6)
// ---------------------------------------------------------------------------
const ONBOARDING_STEPS = [
    {
        target: '.gn-chat-input',
        title: 'Describe Your Website',
        text: 'Type your business description here and our AI will build a complete website for you.',
        arrow: 'left',
        position: 'right',
    },
    {
        target: '.gn-card-grid',
        title: 'Or Pick a Template',
        text: 'Browse templates to get started quickly. Click any template to customize it with AI.',
        arrow: 'left',
        position: 'right',
    },
];

const OnboardingTour = ({ step, onNext, onSkip, totalSteps }) => {
    const [rect, setRect] = useState(null);
    const stepData = ONBOARDING_STEPS[step];

    useEffect(() => {
        if (!stepData) return;
        const el = document.querySelector(stepData.target);
        if (el) {
            const r = el.getBoundingClientRect();
            setRect({ top: r.top - 8, left: r.left - 8, width: r.width + 16, height: r.height + 16 });
        } else {
            setRect(null);
        }
    }, [step, stepData]);

    if (!stepData || !rect) return null;

    let tooltipStyle = {};
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const tooltipW = 320;
    const tooltipH = 180;
    if (stepData.position === 'right') {
        let top = rect.top;
        let left = rect.left + rect.width + 16;
        // If tooltip would go off-screen bottom, anchor above the target
        if (top + tooltipH > vh - 20) {
            top = Math.max(20, rect.top + rect.height - tooltipH);
        }
        // If tooltip would go off-screen right, show above target instead
        if (left + tooltipW > vw - 20) {
            top = Math.max(20, rect.top - tooltipH - 16);
            left = Math.max(20, rect.left);
        }
        tooltipStyle = { top, left };
    } else if (stepData.position === 'below') {
        let top = rect.top + rect.height + 16;
        let left = Math.max(20, rect.left - 100);
        if (top + tooltipH > vh - 20) {
            top = Math.max(20, rect.top - tooltipH - 16);
        }
        if (left + tooltipW > vw - 20) {
            left = vw - tooltipW - 20;
        }
        tooltipStyle = { top, left };
    }

    return (
        <>
            <div className="onboarding-overlay" onClick={onSkip} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSkip(e); }} role="button" tabIndex={0} />
            <div className="onboarding-highlight" style={{ top: rect.top, left: rect.left, width: rect.width, height: rect.height }} />
            <div className={`onboarding-tooltip arrow-${stepData.arrow}`} style={tooltipStyle}>
                <div className="onboarding-step-count">Step {step + 1} of {totalSteps}</div>
                <h4>{stepData.title}</h4>
                <p>{stepData.text}</p>
                <div className="onboarding-actions">
                    <button className="onboarding-skip" onClick={onSkip}>Skip tour</button>
                    <div className="onboarding-dots">
                        {Array.from({ length: totalSteps }, (_, i) => (
                            <span key={i} className={`onboarding-dot ${i === step ? 'active' : ''}`} />
                        ))}
                    </div>
                    <button className="onboarding-next" onClick={onNext}>
                        {step < totalSteps - 1 ? <>Next <ChevronRight size={14} /></> : 'Done'}
                    </button>
                </div>
            </div>
        </>
    );
};

// ---------------------------------------------------------------------------
// Built-in Animation CSS (from animations.py — compact version for downloads)
// ---------------------------------------------------------------------------
const BUILTIN_ANIMATION_CSS = `
/* Animation & Effect Library */
html{scroll-behavior:smooth}
.parallax-bg{position:relative;background-attachment:scroll;background-position:center;background-repeat:no-repeat;background-size:cover}
.parallax-bg::before{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15) 0%,rgba(0,0,0,.05) 100%);z-index:1;pointer-events:none}
.parallax-bg>*{position:relative;z-index:2}
.stagger-reveal .stagger-child{opacity:0;transform:translateY(32px);transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .7s cubic-bezier(.22,1,.36,1)}
.stagger-reveal .stagger-child.visible{opacity:1;transform:translateY(0)}
#scroll-progress{position:fixed;top:0;left:0;width:0%;height:3px;background:linear-gradient(90deg,var(--primary,#6366f1),var(--accent,#a78bfa));z-index:99999;transition:width .05s linear;border-radius:0 2px 2px 0}
.counter[data-target]{font-variant-numeric:tabular-nums;display:inline-block;min-width:1.5em;text-align:center}
.magnetic-btn{position:relative;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;transition:transform .35s cubic-bezier(.22,1,.36,1);will-change:transform}
.image-reveal{overflow:hidden;position:relative}
.image-reveal img{transform:scale(1.15);transition:transform .8s cubic-bezier(.22,1,.36,1)}
.image-reveal::after{content:'';position:absolute;inset:0;background:var(--primary,#6366f1);transform-origin:left;transform:scaleX(1);transition:transform .7s cubic-bezier(.65,0,.35,1)}
.image-reveal.revealed::after{transform:scaleX(0);transform-origin:right}
.image-reveal.revealed img{transform:scale(1)}
.card-lift{transition:transform .4s cubic-bezier(.22,1,.36,1),box-shadow .4s cubic-bezier(.22,1,.36,1);will-change:transform,box-shadow}
.card-lift:hover{transform:translateY(-8px);box-shadow:0 20px 40px -12px rgba(0,0,0,.15),0 8px 16px -8px rgba(0,0,0,.1)}
.nav-link-slide{position:relative;text-decoration:none}
.nav-link-slide::after{content:'';position:absolute;bottom:-2px;left:0;width:100%;height:2px;background:currentColor;transform:scaleX(0);transform-origin:right;transition:transform .4s cubic-bezier(.65,0,.35,1)}
.nav-link-slide:hover::after{transform:scaleX(1);transform-origin:left}
.btn-gradient-shift{background-size:200% 200%;background-image:linear-gradient(135deg,var(--primary,#6366f1) 0%,var(--accent,#a78bfa) 50%,var(--primary,#6366f1) 100%);background-position:0% 50%;transition:background-position .5s cubic-bezier(.22,1,.36,1),transform .3s cubic-bezier(.22,1,.36,1),box-shadow .3s ease;border:none;color:#fff;cursor:pointer}
.btn-gradient-shift:hover{background-position:100% 50%;transform:translateY(-2px);box-shadow:0 8px 24px -4px rgba(99,102,241,.4)}
.hero-stagger span{display:inline-block;opacity:0;transform:translateY(40px) rotateX(-15deg);animation:heroWordIn .7s cubic-bezier(.22,1,.36,1) forwards}
@keyframes heroWordIn{to{opacity:1;transform:translateY(0) rotateX(0deg)}}
.navbar-slidedown{transform:translateY(-100%);animation:navSlideIn .6s cubic-bezier(.22,1,.36,1) .1s forwards}
@keyframes navSlideIn{to{transform:translateY(0)}}
.img-shimmer{position:relative;overflow:hidden;background:#e2e8f0}
.img-shimmer::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,.5) 50%,transparent 100%);animation:shimmer 1.8s ease-in-out infinite}
.img-shimmer.loaded::after{display:none}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
.gradient-mesh{position:relative;overflow:hidden}
.gradient-mesh::before{content:'';position:absolute;inset:-50%;background:radial-gradient(ellipse at 20% 50%,rgba(99,102,241,.3) 0%,transparent 50%),radial-gradient(ellipse at 80% 20%,rgba(168,85,247,.25) 0%,transparent 50%),radial-gradient(ellipse at 50% 80%,rgba(59,130,246,.2) 0%,transparent 50%);animation:meshShift 12s ease-in-out infinite alternate;z-index:-1;pointer-events:none}
.gradient-mesh>*{position:relative;z-index:1}
@keyframes meshShift{0%{transform:translate(0,0) rotate(0deg) scale(1)}33%{transform:translate(5%,-3%) rotate(2deg) scale(1.05)}66%{transform:translate(-3%,5%) rotate(-1deg) scale(.98)}100%{transform:translate(2%,-2%) rotate(1deg) scale(1.02)}}
.floating-shapes{position:relative;overflow:hidden}
.floating-shapes .shape{position:absolute;border-radius:50%;opacity:.12;filter:blur(60px);pointer-events:none;z-index:0;will-change:transform}
.floating-shapes .shape:nth-child(1){width:400px;height:400px;background:var(--primary,#6366f1);top:-10%;left:-5%;animation:floatBlob1 18s ease-in-out infinite}
.floating-shapes .shape:nth-child(2){width:300px;height:300px;background:var(--accent,#a78bfa);bottom:-5%;right:-5%;animation:floatBlob2 22s ease-in-out infinite}
.floating-shapes .shape:nth-child(3){width:250px;height:250px;background:var(--secondary,#3b82f6);top:40%;left:60%;animation:floatBlob3 15s ease-in-out infinite}
@keyframes floatBlob1{0%,100%{transform:translate(0,0) scale(1)}25%{transform:translate(40px,-30px) scale(1.08)}50%{transform:translate(-20px,40px) scale(.95)}75%{transform:translate(30px,20px) scale(1.04)}}
@keyframes floatBlob2{0%,100%{transform:translate(0,0) scale(1)}25%{transform:translate(-35px,25px) scale(1.06)}50%{transform:translate(25px,-35px) scale(.97)}75%{transform:translate(-15px,-20px) scale(1.03)}}
@keyframes floatBlob3{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(30px,-40px) scale(1.1)}66%{transform:translate(-25px,30px) scale(.92)}}
.grain-overlay{position:relative}
.grain-overlay::after{content:'';position:absolute;inset:0;opacity:.035;pointer-events:none;z-index:10;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");background-repeat:repeat;background-size:128px 128px}
.aurora-glow{position:relative;overflow:hidden}
.aurora-glow::before{content:'';position:absolute;top:-40%;left:-20%;width:140%;height:140%;background:conic-gradient(from 180deg at 50% 50%,rgba(99,102,241,.25) 0deg,rgba(168,85,247,.2) 60deg,rgba(59,130,246,.18) 120deg,rgba(16,185,129,.15) 180deg,rgba(99,102,241,.2) 240deg,rgba(244,63,94,.15) 300deg,rgba(99,102,241,.25) 360deg);filter:blur(80px);animation:auroraRotate 20s linear infinite;z-index:0;pointer-events:none}
.aurora-glow>*{position:relative;z-index:1}
@keyframes auroraRotate{0%{transform:rotate(0deg) scale(1)}50%{transform:rotate(180deg) scale(1.1)}100%{transform:rotate(360deg) scale(1)}}
.whatsapp-float{position:fixed;bottom:32px;left:32px;width:56px;height:56px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;color:#fff;text-decoration:none;z-index:9990;box-shadow:0 4px 16px -2px rgba(37,211,102,.45);transition:transform .3s cubic-bezier(.22,1,.36,1),box-shadow .3s ease;animation:whatsappPulse 3s ease-in-out infinite}
.whatsapp-float:hover{transform:scale(1.1);box-shadow:0 8px 28px -4px rgba(37,211,102,.5)}
.whatsapp-float svg{width:28px;height:28px}
@keyframes whatsappPulse{0%,100%{box-shadow:0 4px 16px -2px rgba(37,211,102,.45)}50%{box-shadow:0 4px 28px 2px rgba(37,211,102,.3),0 0 0 8px rgba(37,211,102,.08)}}
.back-to-top{position:fixed;bottom:32px;right:32px;width:48px;height:48px;border-radius:50%;background:var(--primary,#6366f1);color:#fff;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;transform:translateY(16px);transition:opacity .35s cubic-bezier(.22,1,.36,1),visibility .35s,transform .35s cubic-bezier(.22,1,.36,1),background .2s ease;z-index:9990;box-shadow:0 4px 16px -4px rgba(99,102,241,.4)}
.back-to-top.visible{opacity:1;visibility:visible;transform:translateY(0)}
.back-to-top:hover{background:var(--accent,#a78bfa);transform:translateY(-3px)}
.back-to-top svg{width:20px;height:20px}
.back-to-top .progress-ring{position:absolute;inset:-3px;width:54px;height:54px}
.back-to-top .progress-ring circle{fill:none;stroke:var(--primary,#6366f1);stroke-width:2;stroke-dasharray:157;stroke-dashoffset:157;transform:rotate(-90deg);transform-origin:center;transition:stroke-dashoffset .1s linear}
.float-input{position:relative;margin-bottom:1.5rem}
.float-input input,.float-input textarea{width:100%;padding:1rem .75rem .5rem;border:1px solid #d1d5db;border-radius:8px;font-size:1rem;background:transparent;outline:none;transition:border-color .25s ease,box-shadow .25s ease}
.float-input input:focus,.float-input textarea:focus{border-color:var(--primary,#6366f1);box-shadow:0 0 0 3px rgba(99,102,241,.12)}
.float-input label{position:absolute;left:.75rem;top:50%;transform:translateY(-50%);font-size:1rem;color:#9ca3af;pointer-events:none;transition:all .25s cubic-bezier(.22,1,.36,1);background:transparent;padding:0 4px}
.float-input input:focus~label,.float-input input:not(:placeholder-shown)~label,.float-input textarea:focus~label,.float-input textarea:not(:placeholder-shown)~label{top:0;transform:translateY(-50%);font-size:.75rem;color:var(--primary,#6366f1);background:#fff}
.toast{position:fixed;bottom:32px;left:50%;transform:translateX(-50%) translateY(120%);padding:.875rem 1.5rem;border-radius:12px;color:#fff;font-size:.9rem;font-weight:500;z-index:99999;opacity:0;transition:transform .5s cubic-bezier(.22,1,.36,1),opacity .5s cubic-bezier(.22,1,.36,1);box-shadow:0 8px 32px -8px rgba(0,0,0,.25);white-space:nowrap;max-width:90vw;overflow:hidden;text-overflow:ellipsis}
.toast.toast-success{background:#059669}.toast.toast-error{background:#dc2626}.toast.toast-info{background:#6366f1}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
.fade-up{opacity:0;transform:translateY(30px);transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .7s cubic-bezier(.22,1,.36,1)}
.fade-up.visible{opacity:1;transform:translateY(0)}
.fade-in{opacity:0;transition:opacity .7s cubic-bezier(.22,1,.36,1)}
.fade-in.visible{opacity:1}
.scale-in{opacity:0;transform:scale(.92);transition:opacity .6s cubic-bezier(.22,1,.36,1),transform .6s cubic-bezier(.22,1,.36,1)}
.scale-in.visible{opacity:1;transform:scale(1)}
.logo-reveal{opacity:0;transform:scale(.85) translateY(-10px);animation:logoIn .8s cubic-bezier(.22,1,.36,1) .2s forwards}
@keyframes logoIn{to{opacity:1;transform:scale(1) translateY(0)}}
`;

// ---------------------------------------------------------------------------
// Built-in Animation JS (from animations.py — compact version for downloads)
// ---------------------------------------------------------------------------
const BUILTIN_ANIMATION_JS_DOWNLOAD = `
document.addEventListener("DOMContentLoaded",function(){
(function(){var bar=document.getElementById("scroll-progress");if(!bar)return;function up(){var st=window.pageYOffset||document.documentElement.scrollTop;var dh=document.documentElement.scrollHeight-document.documentElement.clientHeight;bar.style.width=(dh>0?(st/dh)*100:0)+"%"}window.addEventListener("scroll",up,{passive:true});up()})();
(function(){var counters=document.querySelectorAll(".counter[data-target]");if(!counters.length)return;function anim(el){var target=parseInt(el.getAttribute("data-target"),10);if(isNaN(target))return;var suffix=el.getAttribute("data-suffix")||"";var prefix=el.getAttribute("data-prefix")||"";var dur=2000,st=null;function step(ts){if(!st)st=ts;var p=Math.min((ts-st)/dur,1);var eased=1-Math.pow(1-p,3);el.textContent=prefix+Math.floor(eased*target).toLocaleString()+suffix;if(p<1)requestAnimationFrame(step);else el.textContent=prefix+target.toLocaleString()+suffix}requestAnimationFrame(step)}var co=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){anim(e.target);co.unobserve(e.target)}})},{threshold:0.3});counters.forEach(function(c){co.observe(c)})})();
(function(){document.querySelectorAll(".magnetic-btn").forEach(function(btn){btn.addEventListener("mousemove",function(e){var r=btn.getBoundingClientRect();var x=e.clientX-r.left-r.width/2;var y=e.clientY-r.top-r.height/2;btn.style.transform="translate("+(x*.25)+"px,"+(y*.25)+"px)"});btn.addEventListener("mouseleave",function(){btn.style.transform="translate(0,0)"})})})();
(function(){var c=document.querySelectorAll(".stagger-reveal");if(!c.length)return;var so=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){entry.target.querySelectorAll(".stagger-child").forEach(function(ch,i){ch.style.transitionDelay=(i*.1)+"s";ch.classList.add("visible")});so.unobserve(entry.target)}})},{threshold:0.15});c.forEach(function(el){so.observe(el)})})();
(function(){var els=document.querySelectorAll(".fade-up,.fade-in,.scale-in");if(!els.length)return;var fo=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){e.target.classList.add("visible");fo.unobserve(e.target)}})},{threshold:0.12});els.forEach(function(el){fo.observe(el)})})();
(function(){var r=document.querySelectorAll(".image-reveal");if(!r.length)return;var ro=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){e.target.classList.add("revealed");ro.unobserve(e.target)}})},{threshold:0.25});r.forEach(function(el){ro.observe(el)})})();
(function(){document.querySelectorAll(".hero-stagger").forEach(function(el){if(el.hasAttribute("data-splitting"))return;if(el.querySelector("span"))return;var text=el.textContent.trim();if(!text)return;var words=text.split(/\\s+/);el.innerHTML="";words.forEach(function(word,i){var span=document.createElement("span");span.textContent=word;span.style.animationDelay=(0.15+i*0.08)+"s";el.appendChild(span);if(i<words.length-1)el.appendChild(document.createTextNode(" "))})})})();
(function(){var btn=document.querySelector(".back-to-top");if(!btn)return;var ring=btn.querySelector(".progress-ring circle");function up(){var st=window.pageYOffset||document.documentElement.scrollTop;var dh=document.documentElement.scrollHeight-document.documentElement.clientHeight;var pct=dh>0?st/dh:0;if(st>400)btn.classList.add("visible");else btn.classList.remove("visible");if(ring){ring.style.strokeDashoffset=157-(pct*157)}}window.addEventListener("scroll",up,{passive:true});up();btn.addEventListener("click",function(){window.scrollTo({top:0,behavior:"smooth"})})})();
(function(){document.querySelectorAll('a[href^="#"]').forEach(function(link){link.addEventListener("click",function(e){var hash=this.getAttribute("href");if(hash.length<2)return;var target=document.querySelector(hash);if(target){e.preventDefault();target.scrollIntoView({behavior:"smooth",block:"start"});if(history.pushState)history.pushState(null,null,hash)}})})})();
window.showToast=function(msg,type,dur){type=type||"info";dur=dur||3000;var ex=document.querySelector(".toast");if(ex)ex.remove();var t=document.createElement("div");t.className="toast toast-"+type;t.textContent=msg;document.body.appendChild(t);t.offsetHeight;t.classList.add("show");setTimeout(function(){t.classList.remove("show");setTimeout(function(){t.remove()},500)},dur)};
(function(){document.querySelectorAll(".img-shimmer").forEach(function(w){var img=w.querySelector("img");if(!img)return;if(img.complete&&img.naturalWidth>0)w.classList.add("loaded");else{img.addEventListener("load",function(){w.classList.add("loaded")});img.addEventListener("error",function(){w.classList.add("loaded")})}})})();
(function(){var nav=document.querySelector(".navbar-slidedown");if(!nav)return;requestAnimationFrame(function(){nav.style.animationPlayState="running"})})();
});
`;

// ---------------------------------------------------------------------------
// Onboarding Wizard Configuration
// ---------------------------------------------------------------------------
const WIZARD_PALETTES = [
    // Premium & Corporate
    { name: 'Ocean Blue', colors: ['#1e3a5f', '#4a90d9', '#e8f4fd'], desc: 'Professional & trustworthy' },
    { name: 'Navy & Gold', colors: ['#0c1b33', '#c8a951', '#f5f0e3'], desc: 'Corporate & prestigious' },
    { name: 'Elegant Dark', colors: ['#1a1a2e', '#334155', '#e2e8f0'], desc: 'Sleek & modern' },
    { name: 'Midnight Onyx', colors: ['#0d0d0d', '#1f1f1f', '#d4af37'], desc: 'Ultra-premium & luxe' },
    // Nature & Organic
    { name: 'Forest Green', colors: ['#1b4332', '#2d6a4f', '#d8f3dc'], desc: 'Natural & growth' },
    { name: 'Earth Tones', colors: ['#3c2415', '#8b6f47', '#f5ebe0'], desc: 'Organic & grounded' },
    { name: 'Teal & Orange', colors: ['#134e4a', '#14b8a6', '#fb923c'], desc: 'Tech & startup' },
    // Warm & Vibrant
    { name: 'Sunset Warm', colors: ['#7c2d12', '#ea580c', '#fff7ed'], desc: 'Energetic & bold' },
    { name: 'Coral & Cream', colors: ['#9f1239', '#fb7185', '#fff1f2'], desc: 'Warm & friendly' },
    { name: 'Warm Gold', colors: ['#451a03', '#b45309', '#fef3c7'], desc: 'Luxury & warmth' },
    // Cool & Creative
    { name: 'Royal Purple', colors: ['#2d1b69', '#7c3aed', '#ede9fe'], desc: 'Creative & premium' },
    { name: 'Rose Pink', colors: ['#831843', '#ec4899', '#fdf2f8'], desc: 'Beauty & feminine' },
    { name: 'Ice Blue', colors: ['#0c4a6e', '#38bdf8', '#f0f9ff'], desc: 'Medical & healthcare' },
    // Neutral & Clean
    { name: 'Clean Minimal', colors: ['#0f172a', '#64748b', '#ffffff'], desc: 'Simple & clean' },
    { name: 'Pastel Soft', colors: ['#6366f1', '#a78bfa', '#fef9c3'], desc: 'Playful & gentle' },
    { name: 'Black & Red', colors: ['#0a0a0a', '#dc2626', '#fef2f2'], desc: 'Bold & powerful' },
    { name: 'Champagne', colors: ['#1c1917', '#a8926a', '#faf7f2'], desc: 'Refined & sophisticated' },
    // AI choice
    { name: 'Surprise Me', colors: ['#6366f1', '#ec4899', '#fbbf24'], desc: 'Let AI choose!', isSurprise: true },
];

const WIZARD_PURPOSES = [
    { value: 'lead_generation', label: 'Get leads & inquiries' },
    { value: 'portfolio', label: 'Showcase my work' },
    { value: 'informational', label: 'Share information' },
    { value: 'booking', label: 'Take bookings / appointments' },
    { value: 'corporate', label: 'Corporate / company presence' },
    { value: 'restaurant', label: 'Restaurant / food menu & reservations' },
    { value: 'landing_page', label: 'Product / service landing page' },
    { value: 'nonprofit', label: 'Nonprofit / charity / cause' },
    { value: 'event', label: 'Event / conference promotion' },
    { value: 'education', label: 'Courses / training / education' },
];

const WIZARD_PAGES = ['Home', 'About', 'Services', 'Contact', 'Blog', 'Gallery', 'FAQ', 'Team', 'Pricing', 'Portfolio'];

const composeWizardPrompt = (data) => {
    const isMulti = data.siteType === 'multi';
    let prompt = `Create a ${isMulti ? 'multi-page' : 'single-page'} website for "${data.companyName}".`;
    prompt += `\n\nBusiness description: ${data.businessDescription}`;
    if (data.tagline) prompt += `\nTagline: "${data.tagline}"`;
    prompt += `\nWebsite purpose: ${data.purpose.replace(/_/g, ' ')}`;
    if (isMulti && data.pages.length > 0) {
        prompt += `\nPages: ${data.pages.join(', ')}`;
    }
    if (data.colorScheme && !data.colorScheme.isSurprise) {
        prompt += `\nColor scheme: ${data.colorScheme.name} — use these colors: ${data.colorScheme.colors.join(', ')}`;
    }
    const ci = data.contactInfo || {};
    // ONLY phone/email/address/mapLink go in the LLM prompt — those belong
    // inside the contact section's body content. WhatsApp and social media
    // URLs are intentionally NOT mentioned to the LLM: they're floating UI
    // widgets injected programmatically post-generation, so generation
    // stays deterministic regardless of which platforms the user filled.
    if (ci.phone || ci.email || ci.address) {
        prompt += '\nContact details:';
        if (ci.phone) prompt += ` Phone: ${ci.phone}.`;
        if (ci.email) prompt += ` Email: ${ci.email}.`;
        if (ci.address) prompt += ` Address: ${ci.address}.`;
    }
    if (ci.mapLink) {
        // Pass the link verbatim. The BACKEND resolves any maps.app.goo.gl
        // / goo.gl/maps short URLs to embeddable lat,lng URLs BEFORE the
        // prompt reaches the LLM (see _resolve_google_maps_links in
        // generator.py). By the time the LLM sees this, the URL is either
        // already an embed-ready URL like
        // https://www.google.com/maps?q=lat,lng&output=embed&z=16
        // OR (if resolution failed) the original share URL.
        //
        // We tell the LLM to use the URL DIRECTLY as the iframe src.
        // Previously this prompt instructed the LLM to fall back to using
        // the address as the query when it saw a share URL, which produced
        // a map of the wrong location whenever the user's typed address
        // differed from the actual map pin.
        prompt += `\nGoogle Maps location: ${ci.mapLink}`;
        prompt += '\nMUST embed this Google Map as an <iframe> inside the contact section. ';
        prompt += 'Use the URL above DIRECTLY as the iframe src: ';
        prompt += '<iframe src="<URL_ABOVE>" width="100%" height="400" style="border:0;border-radius:12px" allowfullscreen loading="lazy"></iframe>. ';
        prompt += 'Do NOT replace it with a search query of the address — the URL has already been resolved to the correct location with coordinates.';
    }
    return prompt;
};

// Wizard question renderer (inline in chat)
const WizardQuestionUI = ({ step, data, onAnswer, onSkip, onBack, onGenerate, onBrowseTemplates, onFileUpload, uploadedFileCount, hasSelectedDomain, onRequestBuyDomain }) => {
    // Pre-fill text input from wizard data (e.g. dashboard chatbox prefill)
    const prefillMap = { 0: data.companyName, 1: data.businessDescription, 2: data.tagline };
    const [textVal, setTextVal] = React.useState(prefillMap[step] || '');
    const [selectedPages, setSelectedPages] = React.useState(data.pages || ['Home', 'About', 'Services', 'Contact']);
    const [contactPhone, setContactPhone] = React.useState(data.contactInfo?.phone || '');
    const [contactEmail, setContactEmail] = React.useState(data.contactInfo?.email || '');
    const [contactAddress, setContactAddress] = React.useState(data.contactInfo?.address || '');
    const [contactMapLink, setContactMapLink] = React.useState(data.contactInfo?.mapLink || '');
    const [contactWhatsapp, setContactWhatsapp] = React.useState(data.contactInfo?.whatsapp || '');
    const [contactSocialFb, setContactSocialFb] = React.useState(data.contactInfo?.social?.facebook || '');
    const [contactSocialIg, setContactSocialIg] = React.useState(data.contactInfo?.social?.instagram || '');
    const [contactSocialTk, setContactSocialTk] = React.useState(data.contactInfo?.social?.tiktok || '');
    const [contactSocialLi, setContactSocialLi] = React.useState(data.contactInfo?.social?.linkedin || '');
    const [contactSocialYt, setContactSocialYt] = React.useState(data.contactInfo?.social?.youtube || '');

    // ── Domain suggestion (step 0 only) ──
    // Debounced availability check on the typed company name. If the user
    // already secured a domain in the entry-flow modal, suppress suggestions.
    const [domainSuggestion, setDomainSuggestion] = React.useState(null); // { sld, results: [...] }
    const [suggestLoading, setSuggestLoading] = React.useState(false);

    React.useEffect(() => {
        if (step !== 0) return undefined;
        if (hasSelectedDomain) return undefined;
        const trimmed = textVal.trim();
        if (trimmed.length < 3) {
            setDomainSuggestion(null);
            return undefined;
        }
        // Slugify the typed company name into a candidate SLD
        const sld = trimmed.toLowerCase().replace(/[^a-z0-9]+/g, '').slice(0, 40);
        if (sld.length < 3) return undefined;

        let cancelled = false;
        const t = setTimeout(async () => {
            setSuggestLoading(true);
            try {
                // 5 popular extensions for the inline nudge — keeps the
                // suggestion compact (the dashboard buy modal still shows 15).
                const data2 = await searchDomains(sld, ['com', 'ae', 'shop', 'co', 'io']);
                if (cancelled) return;
                setDomainSuggestion({ sld, results: data2.results || [] });
            } catch {
                if (!cancelled) setDomainSuggestion(null);
            } finally {
                if (!cancelled) setSuggestLoading(false);
            }
        }, 700);
        return () => { cancelled = true; clearTimeout(t); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [textVal, step, hasSelectedDomain]);

    const handleTextSubmit = (e) => {
        e?.preventDefault();
        if (textVal.trim()) { onAnswer(textVal.trim()); setTextVal(''); }
    };

    // Pick the best free domain to surface — prefer .com, then .ae, then any free
    const bestSuggestion = React.useMemo(() => {
        if (!domainSuggestion?.results?.length) return null;
        const free = domainSuggestion.results.filter(r => r.status === 'free' && r.price);
        if (free.length === 0) return null;
        const order = ['com', 'ae', 'shop', 'co', 'io'];
        for (const tld of order) {
            const m = free.find(r => r.tld === tld);
            if (m) return m;
        }
        return free[0];
    }, [domainSuggestion]);

    const comDotResult = domainSuggestion?.results?.find(r => r.tld === 'com');
    const comTaken = comDotResult && comDotResult.status !== 'free';

    const renderInput = () => {
        switch (step) {
            case 0: // Company name
            case 1: // Business description
            case 2: // Tagline
                return (
                    <>
                        <form onSubmit={handleTextSubmit} className="wizard-text-input">
                            <input
                                type="text"
                                value={textVal}
                                onChange={e => setTextVal(e.target.value)}
                                placeholder={step === 0 ? 'e.g. Falcon Trading LLC' : step === 1 ? 'e.g. We import and distribute premium coffee beans across the UAE...' : 'e.g. Quality You Can Trust'}
                                autoFocus
                            />
                            <button type="submit" disabled={!textVal.trim()}>Next</button>
                            {step === 0 && onFileUpload && (
                                <>
                                    <input id="wizard-file-input" type="file" multiple accept=".pdf,.txt,.doc,.docx,.md,.rtf,.csv,.jpg,.jpeg,.png,.webp,.gif,.svg,.zip" style={{ display: 'none' }} onChange={e => { onFileUpload(e.target.files); e.target.value = ''; }} />
                                    <button type="button" className="wizard-skip-btn" onClick={() => document.getElementById('wizard-file-input')?.click()} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                                        <Paperclip size={13} /> Upload Files
                                    </button>
                                </>
                            )}
                            {step === 0 && uploadedFileCount > 0 && (
                                <span style={{ fontSize: 11, color: '#34d399', marginLeft: 4 }}>{uploadedFileCount} file{uploadedFileCount > 1 ? 's' : ''} ready</span>
                            )}
                            {step === 2 && <button type="button" className="wizard-skip-btn" onClick={() => onSkip()}>Skip</button>}
                        </form>

                        {/* Inline domain suggestion (step 0 only, hidden if user already secured a domain) */}
                        {step === 0 && !hasSelectedDomain && (suggestLoading || bestSuggestion) && (
                            <div style={{ marginTop: 10, padding: '12px 14px', background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.25)', borderRadius: 10, fontSize: 13 }}>
                                {suggestLoading && !bestSuggestion && (
                                    <span style={{ color: '#94a3b8' }}>Checking domain availability…</span>
                                )}
                                {bestSuggestion && (
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                                        <div style={{ flex: 1, minWidth: 200 }}>
                                            {comTaken && bestSuggestion.tld !== 'com' ? (
                                                <div style={{ color: '#cbd5e1' }}>
                                                    <strong style={{ color: '#fbbf24' }}>{domainSuggestion.sld}.com</strong> is taken — but{' '}
                                                    <strong style={{ color: '#60a5fa' }}>{bestSuggestion.sld}.{bestSuggestion.tld}</strong> is available.
                                                </div>
                                            ) : (
                                                <div style={{ color: '#cbd5e1' }}>
                                                    <strong style={{ color: '#60a5fa' }}>{bestSuggestion.sld}.{bestSuggestion.tld}</strong> is available.
                                                </div>
                                            )}
                                            <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>Secure it now and we'll auto-connect it after deploy.</div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => onRequestBuyDomain(bestSuggestion)}
                                            style={{ background: '#3b82f6', border: 'none', color: '#fff', padding: '8px 14px', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }}
                                        >
                                            ${bestSuggestion.price.amount}/yr · Buy
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </>
                );
            case 3: // Purpose
                return (
                    <div className="wizard-options">
                        {WIZARD_PURPOSES.map(p => (
                            <button key={p.value} className="wizard-option" onClick={() => onAnswer(p.value, p.label)}>
                                {p.label}
                            </button>
                        ))}
                    </div>
                );
            case 4: // Single vs multi
                return (
                    <div className="wizard-cards">
                        <button className="wizard-card" onClick={() => onAnswer('single')}>
                            <strong>Single Page</strong>
                            <span>All content on one scrollable page. Fast to generate (1-2 min). Great for most businesses.</span>
                            <span className="wizard-card-tag">Recommended</span>
                        </button>
                        <button className="wizard-card" onClick={() => onAnswer('multi')}>
                            <strong>Multiple Pages</strong>
                            <span>Separate pages (Home, About, Services, etc). Takes longer to generate (5-7 min). Better for content-heavy sites.</span>
                        </button>
                    </div>
                );
            case 5: // Pages (multipage only)
                return (
                    <div className="wizard-pages-select">
                        <div className="wizard-pages-grid">
                            {WIZARD_PAGES.map(p => (
                                <button
                                    key={p}
                                    className={`wizard-page-chip ${selectedPages.includes(p) ? 'selected' : ''} ${p === 'Home' ? 'locked' : ''}`}
                                    onClick={() => {
                                        if (p === 'Home') return;
                                        setSelectedPages(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
                                    }}
                                >
                                    {p === 'Home' ? 'Home (always included)' : p}
                                </button>
                            ))}
                        </div>
                        <button
                            className="wizard-confirm-btn"
                            disabled={selectedPages.length < 2}
                            onClick={() => onAnswer(selectedPages)}
                        >
                            Continue with {selectedPages.length} pages
                        </button>
                    </div>
                );
            case 6: // Color scheme
                return (
                    <div className="wizard-palettes">
                        {WIZARD_PALETTES.map(p => (
                            <button key={p.name} className="wizard-palette" onClick={() => onAnswer(p)}>
                                <div className="wizard-palette-colors">
                                    {p.colors.map((c, i) => <span key={i} style={{ background: c }} />)}
                                </div>
                                <div className="wizard-palette-info">
                                    <strong>{p.name}</strong>
                                    <span>{p.desc}</span>
                                </div>
                            </button>
                        ))}
                    </div>
                );
            case 7: // Contact info
                return (
                    <div className="wizard-contact-fields">
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#888', marginBottom: '0.25rem' }}>CONTACT DETAILS</div>
                        <input type="text" placeholder="Phone (e.g. +971 50 123 4567)" value={contactPhone} onChange={e => setContactPhone(e.target.value)} />
                        <input type="text" placeholder="WhatsApp number  (e.g. +971501234567)" value={contactWhatsapp} onChange={e => setContactWhatsapp(e.target.value)} />
                        <input type="email" placeholder="info@company.com" value={contactEmail} onChange={e => setContactEmail(e.target.value)} />
                        <input type="text" placeholder="Address (optional) " value={contactAddress} onChange={e => setContactAddress(e.target.value)} />
                        <input
                            type="text"
                            placeholder="Google Maps link (optional)"
                            value={contactMapLink}
                            onChange={e => setContactMapLink(e.target.value)}
                        />
                        <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '-0.25rem', marginLeft: '0.25rem' }}>
                            Tip: open Google Maps, search your business, click "Share" → "Embed a map", and paste the URL or the full embed code.
                        </div>

                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#888', marginTop: '0.75rem', marginBottom: '0.25rem' }}>SOCIAL LINKS — only filled platforms appear in the floating button</div>
                        <input type="url" placeholder="Facebook profile URL (optional)" value={contactSocialFb} onChange={e => setContactSocialFb(e.target.value)} />
                        <input type="url" placeholder="Instagram profile URL (optional)" value={contactSocialIg} onChange={e => setContactSocialIg(e.target.value)} />
                        <input type="url" placeholder="TikTok profile URL (optional)" value={contactSocialTk} onChange={e => setContactSocialTk(e.target.value)} />
                        <input type="url" placeholder="LinkedIn profile URL (optional)" value={contactSocialLi} onChange={e => setContactSocialLi(e.target.value)} />
                        <input type="url" placeholder="YouTube channel URL (optional)" value={contactSocialYt} onChange={e => setContactSocialYt(e.target.value)} />

                        <div className="wizard-contact-actions">
                            <button
                                className="wizard-confirm-btn"
                                onClick={() => onAnswer({
                                    phone: contactPhone.trim(),
                                    email: contactEmail.trim(),
                                    address: contactAddress.trim(),
                                    mapLink: contactMapLink.trim(),
                                    whatsapp: contactWhatsapp.trim(),
                                    social: {
                                        facebook: contactSocialFb.trim(),
                                        instagram: contactSocialIg.trim(),
                                        tiktok: contactSocialTk.trim(),
                                        linkedin: contactSocialLi.trim(),
                                        youtube: contactSocialYt.trim(),
                                    },
                                })}
                            >
                                Continue
                            </button>
                            <button className="wizard-skip-btn" onClick={() => onSkip()}>Skip</button>
                        </div>
                    </div>
                );
            case 8: // Summary
                return (
                    <div className="wizard-summary">
                        <div className="wizard-summary-items">
                            <div><strong>Company:</strong> {data.companyName}</div>
                            <div><strong>Business:</strong> {data.businessDescription}</div>
                            {data.tagline && <div><strong>Tagline:</strong> {data.tagline}</div>}
                            <div><strong>Purpose:</strong> {data.purposeLabel || data.purpose}</div>
                            <div><strong>Type:</strong> {data.siteType === 'multi' ? `Multi-page (${data.pages.join(', ')})` : 'Single page'}</div>
                            <div><strong>Colors:</strong> {data.colorScheme?.name || 'AI choice'}
                                {data.colorScheme && !data.colorScheme.isSurprise && (
                                    <span className="wizard-summary-colors">{data.colorScheme.colors.map((c, i) => <span key={i} style={{ background: c }} />)}</span>
                                )}
                            </div>
                            {(data.contactInfo?.phone || data.contactInfo?.email || data.contactInfo?.address) && (
                                <div><strong>Contact:</strong> {[data.contactInfo.phone, data.contactInfo.email, data.contactInfo.address].filter(Boolean).join(' | ')}</div>
                            )}
                            {data.contactInfo?.mapLink && (
                                <div><strong>Map:</strong> Embedded on contact page</div>
                            )}
                            {data.contactInfo?.whatsapp && (
                                <div><strong>WhatsApp:</strong> {data.contactInfo.whatsapp}</div>
                            )}
                            {(() => {
                                // Build a list of social platforms the user filled in.
                                // We render their PLATFORM NAME (not the full URL) for
                                // brevity in the summary card. The actual URLs are still
                                // in wizardData.contactInfo.social and get injected as
                                // floating-button hrefs by the backend after generation.
                                const social = data.contactInfo?.social || {};
                                const filled = [
                                    social.facebook && 'Facebook',
                                    social.instagram && 'Instagram',
                                    social.tiktok && 'TikTok',
                                    social.linkedin && 'LinkedIn',
                                    social.youtube && 'YouTube',
                                ].filter(Boolean);
                                if (filled.length === 0) return null;
                                return (
                                    <div><strong>Social:</strong> {filled.join(', ')}</div>
                                );
                            })()}
                        </div>
                        <div className="wizard-disclaimer">
                            <strong>Before we start:</strong>
                            <ul>
                                <li>AI-generated content may not be 100% accurate — please review all text after generation.</li>
                                <li>Generation takes {data.siteType === 'multi' ? '5-7 minutes' : '1-3 minutes'}. <strong>Please stay on this screen</strong> and do not close or refresh the browser.</li>
                                <li>You can edit anything after — colors, text, images, layout — using the chat.</li>
                            </ul>
                        </div>
                        <div className="wizard-summary-actions">
                            <button className="wizard-generate-btn" onClick={onGenerate}>Generate My Website</button>
                            <button className="wizard-back-link" onClick={onBack}>Edit answers</button>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    const questions = [
        "What's the name of your company or business?",
        "Tell me briefly — what does your business do? What products or services do you offer?",
        "Do you have a tagline or slogan? (You can skip this)",
        "What's the main purpose of your website?",
        "Would you like a single-page or multi-page website?",
        "Which pages would you like? Tap to select or deselect.",
        "Pick a color scheme that fits your brand:",
        "Any contact details to include on the website? (Phone, email, address)",
        null, // summary has no question text
    ];

    return (
        <div className="wizard-step">
            {questions[step] && (
                <div className="gn-msg gn-msg-assistant wizard-msg">
                    <div className="gn-avatar">AI</div>
                    <div className="gn-bubble">{questions[step]}</div>
                </div>
            )}
            {renderInput()}
            <div className="wizard-nav">
                {step > 0 && step < 8 && <button className="wizard-back-btn" onClick={onBack}>Back</button>}
                {step === 0 && <button className="wizard-browse-link" onClick={onBrowseTemplates}>or browse templates instead</button>}
            </div>
        </div>
    );
};

const WebsiteGenerator = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { user: authUser, refreshUser } = useAuth();
    const [html, setHtml] = useState('');
    const [css, setCss] = useState('');
    const [js, setJs] = useState('');
    const [siteMeta, setSiteMeta] = useState({ title: 'Preview', description: '' });
    const [isLoading, setIsLoading] = useState(false);
    const [prompt, setPrompt] = useState('');
    const textareaRef = useRef(null);
    const chatEndRef = useRef(null);

    const isGeneratingRef = useRef(false);
    const isEditingRef = useRef(false);
    const hasAutoGenerated = useRef(false);
    const [viewMode, setViewMode] = useState('preview');
    const [error, setError] = useState(null);
    const [showDeployModal, setShowDeployModal] = useState(false);
    const [deployedSiteId, _setDeployedSiteId] = useState(() => {
        // Restore from sessionStorage so redeploys after page refresh target the same site
        return sessionStorage.getItem('deployedSiteId') || null;
    });
    const setDeployedSiteId = (id) => {
        _setDeployedSiteId(id);
        if (id) sessionStorage.setItem('deployedSiteId', id);
        else sessionStorage.removeItem('deployedSiteId');
    };

    // Session
    const [sessionId, setSessionId] = useState(null);
    const [isNewDesign, setIsNewDesign] = useState(true); // eslint-disable-line no-unused-vars
    const [loadingMessage, setLoadingMessage] = useState('');
    const [currentNiche] = useState(null);

    // Chat messages (each has: role, text, timestamp, versionIndex, html/css/js snapshot)
    const [messages, setMessages] = useState([]);

    // Version history (each generation = a version)
    const [versions, setVersions] = useState([]); // [{html, css, js, prompt}]
    const [currentVersion, setCurrentVersion] = useState(-1);

    // Element editing
    const [editMode, setEditMode] = useState(false);
    const [cmsMode, setCmsMode] = useState(false);
    const [selectedElement, setSelectedElement] = useState(null);
    const [elementPrompt, setElementPrompt] = useState('');
    const [isEditingElement, setIsEditingElement] = useState(false);
    const [elementAttachment, setElementAttachment] = useState(null); // {file, preview, uploading, url}
    const elementFileInputRef = useRef(null);

    // File upload for generation
    const [uploadedFiles, setUploadedFiles] = useState({ text: '', images: [] }); // { text, images: [{url, filename, original_name}] }
    const [uploadingFiles, setUploadingFiles] = useState(false);
    const [imageAssignModal, setImageAssignModal] = useState(false); // show assignment UI
    const [imageAssignments, setImageAssignments] = useState({}); // {imageUrl: sectionType}
    const [pendingGenPrompt, setPendingGenPrompt] = useState(null); // prompt waiting for image assignment
    const fileInputRef = useRef(null);

    // Sections, Components
    const [sections, setSections] = useState([]);
    const [showSiteSettings, setShowSiteSettings] = useState(false);
    const [showSectionEditor, setShowSectionEditor] = useState(false);
    const [showGallery, setShowGallery] = useState(false);
    // Templates (for empty state marketplace)
    const [templates, setTemplates] = useState([]);
    const [templatePreviews, setTemplatePreviews] = useState({});
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');

    // Preview mode: 'desktop' | 'mobile'
    const [previewDevice, setPreviewDevice] = useState('desktop');

    // Mobile responsive
    const [mobileTab, setMobileTab] = useState('chat'); // 'chat' | 'preview' | 'tools'
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

    // Resizable sidebar
    const [sidebarWidth, setSidebarWidth] = useState(380);
    const isResizingRef = useRef(false);

    const sidebarRef = useRef(null);
    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isResizingRef.current) return;
            const newWidth = Math.min(Math.max(e.clientX, 280), 700);
            // Direct DOM manipulation during drag — avoids React re-render per pixel
            if (sidebarRef.current) {
                sidebarRef.current.style.width = newWidth + 'px';
                sidebarRef.current.style.minWidth = newWidth + 'px';
            }
            isResizingRef.current = newWidth; // store value for mouseup
        };
        const handleMouseUp = () => {
            if (isResizingRef.current !== false) {
                const finalWidth = typeof isResizingRef.current === 'number' ? isResizingRef.current : 380;
                isResizingRef.current = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                setSidebarWidth(finalWidth); // commit to React state once
            }
        };
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, []);

    const startResize = (e) => {
        e.preventDefault();
        isResizingRef.current = sidebarWidth; // store current width as truthy start value
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    };

    // Save
    const [saveStatus, setSaveStatus] = useState(null);
    const [projectId, setProjectId] = useState(null);
    const [projectName, setProjectName] = useState('');

    // Async job queue (background worker)
    const [useAsync] = useState(false);
    const [activeJobId, setActiveJobId] = useState(null);
    const [jobProgress, setJobProgress] = useState(0);
    const pollRef = useRef(null);

    // Multi-page state
    const [isMultipage, setIsMultipage] = useState(false);
    const [pages, setPages] = useState({}); // { slug: { html, css } }
    const [currentPage, setCurrentPage] = useState('index'); // active page slug
    // Refs for latest values (avoids stale closures in auto-save, page switch, etc.)
    const pagesRef = useRef(pages);
    pagesRef.current = pages;
    const currentPageRef = useRef(currentPage);
    currentPageRef.current = currentPage;

    // ── Onboarding Wizard State ───────────────────────────────────────
    const [wizardStep, setWizardStep] = useState(-1); // -1 = inactive
    const [wizardData, setWizardData] = useState({
        companyName: '', businessDescription: '', tagline: '', purpose: '', purposeLabel: '',
        siteType: '', pages: ['Home', 'About', 'Services', 'Contact'],
        colorScheme: null, contactInfo: { phone: '', email: '', address: '' },
    });
    const wizardActive = wizardStep >= 0;
    // Domain selected/bought via the dashboard entry-flow modal — used to
    // pre-fill the wizard and to auto-connect at deploy time.
    const [selectedDomain, setSelectedDomain] = useState(null);
    // In-wizard domain buy: when the user clicks the inline suggestion in
    // step 0, we pop a confirmation modal owned by this component.
    const [wizardBuyTarget, setWizardBuyTarget] = useState(null); // { sld, tld, price }
    const [wizardBuyState, setWizardBuyState] = useState({ purchasing: false, error: null });

    // ── UX Enhancement State ────────────────────────────────────────────
    const [showShortcuts, setShowShortcuts] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState('connected');
    const [generationProgress, setGenerationProgress] = useState({ stage: 0, total: 5, message: '' });
    const [toasts, setToasts] = useState([]);
    const [errorBanner, setErrorBanner] = useState(null);
    const [onboardingStep, setOnboardingStep] = useState(-1); // -1 = not showing
    const onboardingShown = useRef(false); // prevent re-showing after reset
    const lastRetryPrompt = useRef('');
    const healthCheckRef = useRef(null);

    const addToast = useCallback((message, type = 'info', duration = 5000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);

    const dismissToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    // ── Init ────────────────────────────────────────────────────────────

    useEffect(() => {
        let cancelled = false;
        getTemplates().then(d => {
            if (cancelled) return;
            const list = d.templates || [];
            setTemplates(list);
            // Lazy-load template previews in batches of 2 with delay to avoid rate limiting
            const loadPreviews = async () => {
                for (let i = 0; i < list.length; i += 2) {
                    if (cancelled) return;
                    const batch = list.slice(i, i + 2);
                    const results = await Promise.allSettled(
                        batch.map(t => getTemplateFull(t.id))
                    );
                    if (cancelled) return;
                    setTemplatePreviews(prev => {
                        const next = { ...prev };
                        results.forEach((r, idx) => {
                            if (r.status === 'fulfilled' && r.value) {
                                next[batch[idx].id] = r.value;
                            }
                        });
                        return next;
                    });
                    // Delay between batches to avoid rate limiting
                    if (i + 2 < list.length) await new Promise(r => setTimeout(r, 1000));
                }
            };
            loadPreviews();
        }).catch(() => { });
        return () => { cancelled = true; };
    }, []);

    // Session init: decide whether to restore, load project/template, or start fresh
    useEffect(() => {
        const state = location.state || {};
        const hasInitialPrompt = !!state.initialPrompt;
        const hasProjectData = !!state.projectData;
        const isNewNavigation = hasInitialPrompt || hasProjectData || state.newSession;

        // If navigated from dashboard with intent, clear old session first
        if (isNewNavigation) {
            sessionStorage.removeItem(SESSION_STORAGE_KEY);
        }

        if (hasProjectData && !hasAutoGenerated.current) {
            // Load from saved project or template
            const pd = state.projectData;
            hasAutoGenerated.current = true;
            setHtml(pd.html || ''); setCss(pd.css || ''); setJs(pd.js || '');
            setProjectId(pd.id || null); setIsNewDesign(false);
            if (pd.name) setProjectName(pd.name);

            // Templates arrive without a project_id, which means every edit
            // path (auto-save, handleSaveProject, element-edit, CMS, chat
            // edit) skips persisting because they all gate on `projectId`.
            // Create a fresh project row immediately so subsequent edits save.
            if (pd.isTemplate) {
                saveProject({
                    name: pd.name || 'Untitled Template Project',
                    html: pd.html || '',
                    css: pd.css || '',
                    js: pd.js || '',
                    prompt: `Loaded from template: ${pd.name || 'Untitled'}`,
                    metadata: JSON.stringify({
                        isMultipage: false,
                        currentPage: 'index',
                        pages: {},
                        messages: [],
                        fromTemplate: true,
                    }),
                })
                    .then(result => {
                        if (result?.project_id) {
                            setProjectId(result.project_id);
                        }
                    })
                    .catch(err => {
                        console.error('Failed to auto-create project from template:', err);
                        addToast('Could not save template as a project. Your edits may not persist until you click Save.', 'error', 8000);
                    });
            }
            // Restore multipage data from metadata
            const meta = pd.metadata || {};
            let restoreHtml = pd.html || '';
            let restoreCss = pd.css || '';
            let restoredPages = {};
            if (meta.isMultipage && meta.pages && Object.keys(meta.pages).length > 0) {
                setIsMultipage(true);
                const targetPage = meta.currentPage || 'index';
                setCurrentPage(targetPage);

                // Extract CSS from HTML if any page has CSS embedded in HTML but no separate CSS
                restoredPages = { ...meta.pages };
                for (const slug of Object.keys(restoredPages)) {
                    const pg = restoredPages[slug];
                    if (pg && pg.html && !pg.css) {
                        // Try to extract <style> blocks from HTML
                        const styleMatch = pg.html.match(/<style[^>]*>([\s\S]*?)<\/style>/gi);
                        if (styleMatch) {
                            let extractedCss = '';
                            let cleanHtml = pg.html;
                            styleMatch.forEach(block => {
                                const inner = block.replace(/<\/?style[^>]*>/gi, '');
                                extractedCss += inner + '\n';
                                cleanHtml = cleanHtml.replace(block, '');
                            });
                            restoredPages[slug] = { html: cleanHtml.trim(), css: extractedCss.trim() };
                        }
                    }
                }
                setPages(restoredPages);

                // Load the saved current page's html/css — fallback through page data → top-level → index page
                const savedPage = restoredPages[targetPage] || restoredPages['index'];
                if (savedPage) {
                    restoreHtml = savedPage.html || pd.html || '';
                    restoreCss = savedPage.css || pd.css || '';
                }
                // If current page CSS is empty, try index page CSS, then any page with CSS
                if (!restoreCss) {
                    restoreCss = restoredPages['index']?.css || pd.css || '';
                    if (!restoreCss) {
                        for (const slug of Object.keys(restoredPages)) {
                            if (restoredPages[slug]?.css) { restoreCss = restoredPages[slug].css; break; }
                        }
                    }
                }
            }
            setHtml(restoreHtml); setCss(restoreCss);
            // Restore deployedSiteId so redeploys update the same site
            if (meta.deployedSiteId) setDeployedSiteId(meta.deployedSiteId);
            // Restore the FULL version history if it was persisted in metadata.
            // Without this, every project re-open (close/reopen, login/logout)
            // wiped the React `versions` array down to one entry, which broke
            // every "Restore this version" button in the restored chat history
            // (those buttons reference versionIndex N but the array only had
            // [0]). Fall back to the legacy single-version behaviour for old
            // projects whose metadata predates the versions persistence.
            if (Array.isArray(meta.versions) && meta.versions.length > 0) {
                setVersions(meta.versions);
                const restoredCv = typeof meta.currentVersion === 'number'
                    ? Math.max(0, Math.min(meta.versions.length - 1, meta.currentVersion))
                    : meta.versions.length - 1;
                setCurrentVersion(restoredCv);
            } else {
                const v = { html: restoreHtml, css: restoreCss, js: pd.js || '', prompt: pd.isTemplate ? 'Loaded from template' : 'Loaded from project', isMultipage: meta.isMultipage || false, pages: restoredPages };
                setVersions([v]);
                setCurrentVersion(0);
            }
            // Restore chat history from metadata if available, otherwise show default message
            if (!pd.isTemplate && meta.messages && meta.messages.length > 0) {
                setMessages([...meta.messages, { role: 'assistant', text: 'Session restored. What would you like to change?', timestamp: new Date().toLocaleTimeString() }]);
            } else {
                setMessages([{ role: 'assistant', text: pd.isTemplate ? `Template "${pd.name}" loaded. Describe the changes you'd like to make.` : 'Project loaded. What would you like to change?', timestamp: new Date().toLocaleTimeString() }]);
            }

            // Hydrate backend session with FULL multipage data so chat/sections/edits work
            const restoreOpts = meta.isMultipage ? { isMultipage: true, pages: restoredPages, currentPage: meta.currentPage || 'index' } : {};
            restoreSession(restoreHtml, restoreCss, pd.js || '', pd.id || null, restoreOpts)
                .then(data => {
                    setSessionId(data.sessionId);
                    if (data.sections) setSections(data.sections);
                })
                .catch(err => console.error('Failed to restore session:', err));
        } else if (hasInitialPrompt && !hasAutoGenerated.current && !sessionStorage.getItem(SESSION_STORAGE_KEY)) {
            // Auto-generate from dashboard prompt (skip if session already exists — prevents hot-reload re-trigger)
            hasAutoGenerated.current = true;
            handleGenerate(state.initialPrompt, null);
        } else if (!isNewNavigation && !hasAutoGenerated.current) {
            // No navigation state — restore from sessionStorage (page refresh)
            const saved = sessionStorage.getItem(SESSION_STORAGE_KEY);
            if (saved) {
                try {
                    const d = JSON.parse(saved);
                    setHtml(d.html || ''); setCss(d.css || ''); setJs(d.js || '');
                    setMessages(d.messages || []); setVersions(d.versions || []);
                    setCurrentVersion(d.currentVersion ?? -1);
                    setProjectId(d.projectId || null);
                    setIsNewDesign(false); hasAutoGenerated.current = true;
                    // Restore multi-page state
                    if (d.isMultipage && d.pages && Object.keys(d.pages).length > 0) {
                        setIsMultipage(true);
                        setPages(d.pages);
                        const page = d.currentPage || 'index';
                        setCurrentPage(page);
                        // Ensure html/css match the current page from pages dict
                        const pageData = d.pages[page];
                        if (pageData) {
                            setHtml(pageData.html || d.html || '');
                            setCss(pageData.css || d.css || '');
                        }
                    }

                    // Re-hydrate backend session (may have been lost on server restart)
                    if (d.html) {
                        const ssRestoreOpts = (d.isMultipage && d.pages && Object.keys(d.pages).length > 0)
                            ? { isMultipage: true, pages: d.pages, currentPage: d.currentPage || 'index' }
                            : {};
                        const ssRestoreHtml = (d.isMultipage && d.pages?.[d.currentPage || 'index']?.html) || d.html;
                        const ssRestoreCss = (d.isMultipage && d.pages?.[d.currentPage || 'index']?.css) || d.css || '';
                        restoreSession(ssRestoreHtml, ssRestoreCss, d.js || '', d.projectId || null, ssRestoreOpts)
                            .then(data => {
                                setSessionId(data.sessionId);
                                if (data.sections) setSections(data.sections);
                            })
                            .catch(() => {
                                // Fallback: use old sessionId if restore fails
                                if (d.sessionId) setSessionId(d.sessionId);
                            });
                    } else if (d.sessionId) {
                        setSessionId(d.sessionId);
                    }
                } catch (e) { sessionStorage.removeItem(SESSION_STORAGE_KEY); }
            } else {
                // No saved session — start the onboarding wizard
                startWizard();
            }
        }
        // newSession flag — start the onboarding wizard (with optional prefill from dashboard prompt)
        else if (isNewNavigation && state?.newSession && !state?.initialPrompt) {
            startWizard();
            // If user typed something in the dashboard chatbox, pre-fill as business description
            if (state.wizardPrefill) {
                const prefill = state.wizardPrefill;
                setWizardData(prev => ({ ...prev, businessDescription: prefill }));
                setWizardStep(0); // still start at company name, but step 1 will be pre-filled
            }
            // If the user reached the generator after buying / picking a domain
            // in the entry-flow modal, pre-fill the company name from the
            // domain (e.g. "acme-shop.shop" → "Acme Shop") and store the domain
            // so the deploy step can auto-connect it later.
            if (state.wizardBrand || state.wizardDomain) {
                setWizardData(prev => ({
                    ...prev,
                    companyName: state.wizardBrand || prev.companyName,
                }));
                if (state.wizardDomain) {
                    setSelectedDomain(state.wizardDomain);
                }
                // Stay on step 0 so the user can confirm or edit the
                // pre-filled company name (the input renders prefillMap[0] =
                // data.companyName).
            }
            // Auto-open file picker if coming from dashboard with openFileUpload flag
            if (state.openFileUpload) {
                setTimeout(() => fileInputRef.current?.click(), 800);
            }
        }

        // Clear navigation state so browser back/forward doesn't re-trigger
        if (isNewNavigation) {
            navigate('/generator', { replace: true, state: {} });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Persist to sessionStorage (store lightweight version refs, not full HTML snapshots)
    useEffect(() => {
        if (sessionId || html) {
            // Strip heavy html/css/js/pages from version entries to avoid 5MB quota
            // Save last 3 full versions for undo/redo across refresh, rest as light
            const fullVersions = versions.slice(Math.max(0, versions.length - 3)).map(v => ({
                html: v.html, css: v.css, js: v.js, prompt: v.prompt,
                isMultipage: v.isMultipage, pages: v.pages,
            }));
            const lightVersions = versions.slice(0, Math.max(0, versions.length - 3)).map(v => ({
                prompt: v.prompt, _light: true,
            }));
            const allVersions = [...lightVersions, ...fullVersions];
            sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
                sessionId, html, css, js, messages, versions: allVersions, currentVersion, projectId,
                isMultipage, pages, currentPage,
            }));
        }
    }, [sessionId, html, css, js, messages, versions, currentVersion, projectId, isMultipage, pages, currentPage]);

    // Auto-save to project DB (debounced 3s after last html/css change)
    const autoSaveTimerRef = useRef(null);
    useEffect(() => {
        if (!projectId || !html || isLoading) return;
        if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
        autoSaveTimerRef.current = setTimeout(() => {
            setSaveStatus('saving');
            // Use refs to get latest pages/currentPage (avoids stale closure)
            const latestPages = pagesRef.current;
            const latestCurrentPage = currentPageRef.current;
            const allPages = isMultipage ? { ...latestPages, [latestCurrentPage]: { html, css } } : {};
            const metadata = JSON.stringify({ isMultipage, currentPage: latestCurrentPage, pages: allPages, messages: messages.slice(-50) });
            // For multipage, always save index page as top-level html/css for reliable restore
            const saveHtml = isMultipage && allPages['index']?.html ? allPages['index'].html : html;
            const saveCss = isMultipage && allPages['index']?.css ? allPages['index'].css : css;
            saveProject({
                project_id: projectId,
                name: projectName || 'Untitled Project',
                html: saveHtml, css: saveCss, js,
                prompt: messages.filter(m => m.role === 'user').pop()?.text || '',
                metadata,
            }).then(res => {
                setSaveStatus('saved');
                setTimeout(() => setSaveStatus(null), 2000);
            }).catch(() => {
                setSaveStatus('error');
                setTimeout(() => setSaveStatus(null), 3000);
            });
        }, 3000);
        return () => { if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [html, css, js, projectId]);

    // Scroll chat to bottom
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading, wizardStep]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
        }
    }, [prompt]);

    // Mobile resize listener
    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 768);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Auto-switch to preview tab after generation completes
    const prevHtmlRef = useRef(html);
    useEffect(() => {
        if (isMobile && html && !prevHtmlRef.current) {
            setMobileTab('preview');
        }
        prevHtmlRef.current = html;
    }, [html, isMobile]);

    // ── Onboarding check ──────────────────────────────────────────────
    useEffect(() => {
        const done = localStorage.getItem(ONBOARDING_KEY);
        if (!done && !onboardingShown.current) {
            onboardingShown.current = true;
            const timer = setTimeout(() => setOnboardingStep(0), 500);
            return () => clearTimeout(timer);
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Connection health check ─────────────────────────────────────────
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);
                const response = await fetch(`${config.apiUrl}/api/health`, {
                    method: 'GET',
                    signal: controller.signal,
                });
                clearTimeout(timeoutId);
                if (response.ok) {
                    setConnectionStatus('connected');
                } else {
                    setConnectionStatus('disconnected');
                }
            } catch {
                setConnectionStatus('disconnected');
            }
        };

        checkHealth();
        healthCheckRef.current = setInterval(checkHealth, 30000);
        return () => { if (healthCheckRef.current) clearInterval(healthCheckRef.current); };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Extended keyboard shortcuts ──────────────────────────────────────
    useEffect(() => {
        const handler = (e) => {
            // '?' for shortcuts modal (only when not in input)
            if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
                const tag = document.activeElement?.tagName;
                if (tag !== 'INPUT' && tag !== 'TEXTAREA' && !document.activeElement?.isContentEditable) {
                    e.preventDefault();
                    setShowShortcuts(prev => !prev);
                }
            }
            // Ctrl+S — save
            if ((e.metaKey || e.ctrlKey) && e.key === 's') {
                e.preventDefault();
                if (html) handleSaveProject();
            }
            // Ctrl+D — download
            if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
                e.preventDefault();
                if (html) handleExport();
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [html, addToast]);

    // ── Onboarding Wizard Handlers ──────────────────────────────────────

    const startWizard = useCallback(() => {
        setWizardStep(0);
        setWizardData({
            companyName: '', businessDescription: '', tagline: '', purpose: '', purposeLabel: '',
            siteType: '', pages: ['Home', 'About', 'Services', 'Contact'],
            colorScheme: null,
            contactInfo: {
                phone: '', email: '', address: '', mapLink: '',
                whatsapp: '',
                social: { facebook: '', instagram: '', tiktok: '', linkedin: '', youtube: '' },
            },
        });
        setMessages([{
            role: 'assistant',
            text: "Welcome! I'll help you build your website step by step. Let's start with a few quick questions so I can create something perfect for your business.",
            timestamp: new Date().toLocaleTimeString(),
        }]);
    }, []);

    const handleWizardAnswer = useCallback((value, displayLabel) => {
        const step = wizardStep;
        let displayText = '';
        const updated = { ...wizardData };

        switch (step) {
            case 0: updated.companyName = value; displayText = value; break;
            case 1: updated.businessDescription = value; displayText = value; break;
            case 2: updated.tagline = value; displayText = value; break;
            case 3: updated.purpose = value; updated.purposeLabel = displayLabel || value; displayText = displayLabel || value; break;
            case 4: updated.siteType = value; displayText = value === 'single' ? 'Single page' : 'Multiple pages'; break;
            case 5: updated.pages = value; displayText = value.join(', '); break;
            case 6: updated.colorScheme = value; displayText = value.name || 'Custom'; break;
            case 7: updated.contactInfo = value; displayText = [value.phone, value.email, value.address].filter(Boolean).join(', ') || 'Provided'; break;
            default: break;
        }

        setWizardData(updated);

        // Add user's answer as a message
        setMessages(prev => [...prev, {
            role: 'user', text: displayText, timestamp: new Date().toLocaleTimeString(),
        }]);

        // Advance to next step (skip step 5 if single page)
        let nextStep = step + 1;
        if (nextStep === 5 && updated.siteType === 'single') nextStep = 6;
        setWizardStep(nextStep);
    }, [wizardStep, wizardData]);

    const handleWizardSkip = useCallback(() => {
        setMessages(prev => [...prev, {
            role: 'user', text: 'Skipped', timestamp: new Date().toLocaleTimeString(),
        }]);
        let nextStep = wizardStep + 1;
        if (nextStep === 5 && wizardData.siteType === 'single') nextStep = 6;
        setWizardStep(nextStep);
    }, [wizardStep, wizardData.siteType]);

    const handleConfirmWizardDomainBuy = async () => {
        if (!wizardBuyTarget) return;
        setWizardBuyState({ purchasing: true, error: null });
        const fullDomain = `${wizardBuyTarget.sld}.${wizardBuyTarget.tld}`;
        const brandFromDomain = (s) => {
            const sld = String(s).split('.')[0] || '';
            return sld.split(/[-_]/).map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join(' ');
        };
        try {
            // Resilient buy: races purchase API with listUserDomains polling
            // so an ALB-timeout-induced fetch hang doesn't strand the spinner.
            await purchaseDomainAndWait(wizardBuyTarget.sld, wizardBuyTarget.tld, null, 1);
            setSelectedDomain(fullDomain);
            setWizardData(prev => ({ ...prev, companyName: prev.companyName || brandFromDomain(fullDomain) }));
            setWizardBuyTarget(null);
            setWizardBuyState({ purchasing: false, error: null });
            addToast(`${fullDomain} secured!`, 'success');
        } catch (e) {
            // Timeout case: domain is being registered in the background.
            // Treat as soft success — the user shouldn't be punished for our
            // backend being slow, and the domain WILL appear in My Domains.
            if (e.code === 'PURCHASE_TIMEOUT') {
                setSelectedDomain(fullDomain);
                setWizardData(prev => ({ ...prev, companyName: prev.companyName || brandFromDomain(fullDomain) }));
                setWizardBuyTarget(null);
                setWizardBuyState({ purchasing: false, error: null });
                addToast(`${fullDomain} is registering in the background. We'll connect it after deploy.`, 'info', 8000);
                return;
            }
            setWizardBuyState({ purchasing: false, error: e.message || 'Purchase failed' });
        }
    };

    const handleWizardBack = useCallback(() => {
        let prevStep = wizardStep - 1;
        if (prevStep === 5 && wizardData.siteType === 'single') prevStep = 4;
        // Remove last user+assistant message pair
        setMessages(prev => {
            const msgs = [...prev];
            // Remove last user message
            for (let i = msgs.length - 1; i >= 0; i--) {
                if (msgs[i].role === 'user') { msgs.splice(i, 1); break; }
            }
            return msgs;
        });
        setWizardStep(prevStep < 0 ? 0 : prevStep);
    }, [wizardStep, wizardData.siteType]);

    // handleWizardGenerate is defined after handleGenerate — see below

    const handleBrowseTemplates = useCallback(() => {
        setWizardStep(-1);
        setMessages([]);
    }, []);

    // ── Computed ─────────────────────────────────────────────────────────

    const categories = useMemo(() => {
        const cats = new Set(templates.map(t => t.category).filter(Boolean));
        return ['All', ...Array.from(cats).sort((a, b) => a.localeCompare(b))];
    }, [templates]);

    const filteredItems = useMemo(() => {
        let filtered = templates;
        if (selectedCategory !== 'All') filtered = filtered.filter(item => item.category === selectedCategory);
        if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            filtered = filtered.filter(item => item.name.toLowerCase().includes(q) || (item.category || '').toLowerCase().includes(q));
        }
        return filtered;
    }, [templates, selectedCategory, searchQuery]);

    // ── Job polling ─────────────────────────────────────────────────────

    const pollJob = useCallback((jobId) => {
        if (pollRef.current) clearInterval(pollRef.current);

        pollRef.current = setInterval(async () => {
            try {
                const job = await getJobStatus(jobId);
                setJobProgress(job.progress || 0);
                setLoadingMessage(job.progressMessage || 'Processing...');

                if (job.status === 'completed' && job.result) {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setActiveJobId(null);

                    const result = job.result;
                    const newHtml = result.website.html;
                    const newCss = result.website.css;
                    const newJs = result.website.js || '';
                    setHtml(newHtml); setCss(newCss); setJs(newJs);
                    setSessionId(job.sessionId || jobId);
                    setIsNewDesign(true);
                    if (result.meta) setSiteMeta(result.meta);

                    if (result.sections) setSections(result.sections);

                    // Multi-page support for async jobs
                    const mp = result.isMultipage || false;
                    setIsMultipage(mp);
                    if (mp && result.pages) { setPages(result.pages); setCurrentPage('index'); }

                    const newVersion = { html: newHtml, css: newCss, js: newJs, prompt: '[async job]', isMultipage: mp, pages: mp ? result.pages : {} };
                    setVersions(prev => {
                        // Truncate any redo branch (matches handleElementEdit pattern)
                        // and cap total history at MAX_VERSIONS to prevent unbounded
                        // memory growth on long editing sessions. Each version stores
                        // full html/css/js + the pages dict, so for multipage projects
                        // each version is ~100KB; without a cap, 500 edits = 50MB =
                        // browser tab OOM on lower-end devices.
                        const trimmed = prev.slice(0, currentVersion + 1);
                        const updated = [...trimmed, newVersion];
                        const capped = updated.length > MAX_HISTORY_VERSIONS
                            ? updated.slice(-MAX_HISTORY_VERSIONS)
                            : updated;
                        setCurrentVersion(capped.length - 1);
                        return capped;
                    });

                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        text: mp ? `Your ${Object.keys(result.pages || {}).length}-page website is ready!` : 'Here\'s your website! Let me know if you\'d like any changes.',
                        timestamp: new Date().toLocaleTimeString(),
                        versionIndex: versions.length,
                    }]);

                    setIsLoading(false);
                    setLoadingMessage('');
                    isGeneratingRef.current = false;
                    refreshUser(); // Update generation/edit counts
                    setUploadedFiles({ text: '', images: [] }); // Clear uploaded files
                } else if (job.status === 'failed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setActiveJobId(null);
                    setError(job.error || 'Job failed');
                    setMessages(prev => [...prev, {
                        role: 'assistant',
                        text: `Error: ${job.error || 'Generation failed'}`,
                        timestamp: new Date().toLocaleTimeString(),
                        isError: true,
                    }]);
                    setIsLoading(false);
                    setLoadingMessage('');
                    isGeneratingRef.current = false;
                    if (versions.length === 0) {
                        localStorage.removeItem(ONBOARDING_KEY);
                        onboardingShown.current = false;
                        setTimeout(() => setOnboardingStep(0), 1500);
                    }
                }
            } catch (err) {
                console.error('Poll error:', err);
            }
        }, 2000);
    }, [versions.length]);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, []);

    // ── Auto-recovery on screen wake / tab focus ─────────────────────────
    // When browser suspends JS (screen sleep, tab background), the SSE stream dies.
    // On wake, check if the backend finished generating while we were away.
    useEffect(() => {
        const handleVisibility = async () => {
            if (document.visibilityState !== 'visible') return;
            if (!isGeneratingRef.current || !sessionId) return;

            // Tab just became visible and we were generating — check if done
            try {
                const session = await getSession(sessionId);
                if (session && session.html) {
                    // Generation completed while screen was off!
                    setHtml(session.html);
                    setCss(session.css || '');
                    setJs(session.js || '');
                    if (session.pages) setPages(session.pages);
                    if (session.multipage) setIsMultipage(true);
                    setIsLoading(false);
                    setLoadingMessage('');
                    isGeneratingRef.current = false;
                    if (streamControllerRef.current) {
                        streamControllerRef.current.abort();
                        streamControllerRef.current = null;
                    }
                    setErrorBanner(null);
                    addToast('Connection recovered — website ready!', 'success');
                }
            } catch (_) { /* session not ready yet, stream will handle it */ }
        };

        document.addEventListener('visibilitychange', handleVisibility);
        return () => document.removeEventListener('visibilitychange', handleVisibility);
    }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Generation ──────────────────────────────────────────────────────

    const streamControllerRef = useRef(null);

    // ── Help response detection ────────────────────────────────────────
    const helpResponses = [
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(change|replace|add|use|upload).*(image|photo|picture|img)/i, /gallery/i, /my\s+images/i, /uploaded?\s+(image|photo)/i],
            answer: 'Use the **Gallery icon** (image icon) in the toolbar to browse your uploaded images and insert them into your site. Or simply type what you want, e.g. "change the hero image to a modern office photo".'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(add|connect|change|set).*(whatsapp|whats\s+app)/i, /whatsapp\s*(number|button|icon)/i],
            answer: 'Click the **Settings icon** (gear) in the toolbar → go to the **WhatsApp tab** → enter your phone number with country code (e.g. +971501234567). The floating WhatsApp button on your site will use that number.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(deploy|publish|launch|go\s+live|make.*live)/i, /deploy\s+my/i, /publish\s+my/i],
            answer: 'Click the **Deploy** button (green, top-right corner). Enter a site name and click Deploy. You\'ll get a live URL you can share with anyone.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(change|edit|modify|update).*(color|colour|font|theme|design\s+system)/i, /change\s+(the\s+)?color/i, /change\s+(the\s+)?font/i],
            answer: 'Click the **Settings icon** (gear) in the toolbar to open the design panel where you can change colors and fonts. Or type in chat: "change primary color to blue" or "use a dark theme".'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(add|remove|delete|reorder|move|rearrange).*(section)/i, /add\s+a?\s*new\s+section/i],
            answer: 'Click **Sections** in the top-left toolbar to see all sections. You can drag to reorder, delete, or duplicate sections. Or type in chat: "add a testimonials section" or "remove the pricing section".'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(edit|change|modify)\s+(the\s+)?text\s*(directly|inline|on\s+page)?/i, /cms\s+mode/i, /inline\s+edit/i, /edit\s+text\s+directly/i],
            answer: 'Click the **T icon** in the toolbar to enter CMS mode. Then click any text on the page to edit it directly — just type your changes and they\'ll update live.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(click|select|pick).*(edit|element|component)/i, /edit\s+mode/i, /element\s+edit/i, /click.*to.*edit/i, /pointer.*icon/i],
            answer: 'Click the **pointer icon** (↗) in the toolbar to enter Edit mode. Hover over any element — it highlights in blue. Click to select it, then describe what you want to change in the edit panel (e.g. "make this red", "change this image"). You can also attach an image to replace the selected element\'s image.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*save/i, /save\s+(my|the)\s+(work|project|site)/i],
            answer: 'Click **Save** in the toolbar, or press **Ctrl+S** (Cmd+S on Mac). Your project is saved to your Dashboard → Projects tab.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(undo|redo|revert|go\s+back|restore)/i, /undo/i, /redo/i],
            answer: 'Click the **undo/redo arrows** in the toolbar, or press **Ctrl+Z** to undo and **Ctrl+Shift+Z** to redo. You can also click **"Restore this version"** on any previous message in the chat to go back to that version.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(download|export|zip)/i, /download\s+(my|the)/i, /export/i],
            answer: 'Click the **download icon** (↓) in the toolbar to export your website as a ZIP file containing HTML, CSS, and JS files.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(switch|navigate|go\s+to).*(page)/i, /multipage/i, /other\s+page/i, /page\s+tab/i],
            answer: 'Use the **page tabs** above the preview area to switch between pages (Home, About, Contact, etc.). To add a new page, type: "add an About page".'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(add|create).*(contact\s+form|form)/i, /contact\s+form/i],
            answer: 'Type in chat: "add a contact form section". After deploying, all form submissions will appear in your **Dashboard → Inbox** tab.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(preview|view|see).*(mobile|phone|responsive)/i, /mobile\s+(view|preview)/i],
            answer: 'Click the **phone icon** next to the Preview button to toggle mobile view. All generated websites are mobile-responsive by default.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(connect|add|buy|register).*(domain|url|website\s+address)/i, /custom\s+domain/i, /my\s+own\s+domain/i],
            answer: 'After deploying, go to **Dashboard → Domains** tab → find your site → click **Connect Domain**. You can buy a new domain or connect one you already own by pointing its CNAME record.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(seo|meta|search\s+engine|google)/i, /seo\s+settings/i],
            answer: 'Click the **Settings icon** (gear) → **SEO & Meta tab**. Set your page title, meta description, keywords, and upload a favicon. These help your site rank in Google.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(custom\s+code|inject|script|tracking|analytics\s+code|google\s+tag)/i],
            answer: 'Go to **Dashboard → Domains** tab → find your deployed site → click **Code Inject**. You can add custom HTML/scripts to the head or body (e.g. Google Analytics, Facebook Pixel).'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(view|see|check|read).*(form|submission|inbox|message)/i, /form\s+submission/i, /inbox/i],
            answer: 'Go to **Dashboard → Inbox** tab. You can filter by site and read/unread status. Click any submission to see the full message and reply via email.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*upload/i, /upload\s+(image|photo|logo|file)/i],
            answer: 'Go to **Dashboard → Gallery** tab → click **Upload Images**. Then in the generator, click the **Gallery icon** in the toolbar to browse and use your uploaded images.'
        },
        {
            patterns: [/how\s+(do\s+i|to|can\s+i)\s+.*(start\s+over|reset|new\s+design|fresh|from\s+scratch)/i, /start\s+over/i],
            answer: 'Click the **refresh icon** (↻) next to the logo in the chat header to start a new design. Or click **Start Over** in the toolbar to reset everything.'
        },
        {
            patterns: [/keyboard\s+shortcut/i, /shortcut/i, /hotkey/i],
            answer: 'Press the **?** key to see all keyboard shortcuts. Quick ones: **Ctrl+Z** (undo), **Ctrl+S** (save), **Ctrl+Shift+Z** (redo), **Enter** (send message).'
        },
        {
            patterns: [/^help$/i, /what\s+can\s+(i|you)\s+do/i, /how\s+does\s+this\s+work/i, /how\s+to\s+use/i, /guide\s+me/i, /tutorial/i, /^what\s+is\s+this/i],
            answer: "I'm your AI website builder! Here's what you can do:\n\n• **Type a description** to generate a website (e.g. \"build a restaurant website\")\n• **Type changes** to edit (e.g. \"make the hero bigger\", \"add a team section\")\n• **Toolbar icons**: Sections, Settings, Click-to-Edit, CMS, Gallery\n• **Deploy** to publish your site live with one click\n• **Press ?** for keyboard shortcuts\n\nJust describe what you want and I'll make it happen!"
        },
    ];

    const getHelpResponse = (text) => {
        const trimmed = text.trim();

        // Gate: only attempt help-intent matching when the prompt actually
        // looks like a question. Otherwise the bare-keyword patterns below
        // (e.g. /gallery/i, /multipage/i, /inbox/i) hijack legitimate action
        // requests like "make this website multipage with gallery and
        // contact" — which clearly is a command, not a question.
        const looksLikeQuestion =
            // Starts with a question word
            /^(how|what|where|why|can\s+you|could\s+you|do\s+i|is\s+there|tell\s+me)\b/i.test(trimmed)
            // OR is a very short single-word query (≤3 words, ≤30 chars)
            || (trimmed.length <= 30 && trimmed.split(/\s+/).length <= 3)
            // OR ends with a question mark
            || trimmed.endsWith('?');
        if (!looksLikeQuestion) return null;

        for (const entry of helpResponses) {
            for (const pattern of entry.patterns) {
                if (pattern.test(trimmed)) return entry.answer;
            }
        }
        return null;
    };

    // ── File upload handler ──────────────────────────────────────────
    const handleFileUpload = async (files) => {
        if (!files || files.length === 0) return;
        setUploadingFiles(true);
        try {
            const result = await uploadFiles(Array.from(files));
            const newImages = result.images || [];
            const newText = result.extracted_text || '';

            setUploadedFiles(prev => ({
                text: prev.text ? prev.text + '\n\n' + newText : newText,
                images: [...prev.images, ...newImages],
            }));

            const parts = [];
            if (newText) parts.push(`Text extracted (${newText.length} chars)`);
            if (newImages.length) parts.push(`${newImages.length} image${newImages.length > 1 ? 's' : ''} uploaded`);
            if (result.errors?.length) parts.push(`${result.errors.length} error(s)`);
            addToast(parts.join(' · '), (newText || newImages.length) ? 'success' : 'info');

            // Show wizard so user can still pick colors, site type, etc.
            if (versions.length === 0 && onboardingStep < 0) {
                localStorage.removeItem(ONBOARDING_KEY);
                onboardingShown.current = false;
                setTimeout(() => setOnboardingStep(0), 500);
            }
        } catch (err) {
            addToast(err.message || 'Upload failed', 'error');
        }
        setUploadingFiles(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const handleImageAssign = (imageUrl, sectionType) => {
        setImageAssignments(prev => {
            const updated = { ...prev };
            // Remove previous assignment of this image
            Object.keys(updated).forEach(k => { if (updated[k] === sectionType && k !== imageUrl) delete updated[k]; });
            if (updated[imageUrl] === sectionType) {
                delete updated[imageUrl]; // Toggle off
            } else {
                updated[imageUrl] = sectionType;
            }
            return updated;
        });
    };

    const handleConfirmImageAssignment = () => {
        setImageAssignModal(false);
        const userImages = uploadedFiles.images.map(img => ({
            url: img.url,
            filename: img.filename,
            section: imageAssignments[img.url] || '',
        }));
        if (pendingGenPrompt) {
            handleGenerate(pendingGenPrompt, null, null, userImages);
            setPendingGenPrompt(null);
        }
    };

    const handleSkipImageAssignment = () => {
        setImageAssignModal(false);
        if (pendingGenPrompt) {
            handleGenerate(pendingGenPrompt, null, null, []);
            setPendingGenPrompt(null);
        }
    };

    const handleGenerate = async (text, niche, templateId = null, assignedImages = undefined, displayText = null) => {
        const promptText = text || prompt.trim();
        // displayPrompt is what we show in the chat bubble for the user's
        // message. It can differ from promptText so the wizard can include
        // info that the LLM should NOT see (e.g. WhatsApp number, social
        // media URLs — those are programmatically injected post-generation
        // and listing them in the LLM prompt would risk the model rendering
        // them as page elements that then collide with the floating widgets
        // we inject ourselves). Defaults to promptText when not provided.
        const displayPrompt = displayText || promptText;
        if (!promptText || isGeneratingRef.current) return;

        // Block e-commerce requests immediately
        const _lower = promptText.toLowerCase();
        const _ecomKeywords = ['e-commerce', 'ecommerce', 'e commerce', 'online store', 'online shop', 'shopping cart', 'add to cart', 'checkout', 'product listing', 'sell online', 'selling online', 'payment gateway', 'shopify', 'woocommerce', 'magento', 'webshop', 'web shop'];
        if (_ecomKeywords.some(kw => _lower.includes(kw))) {
            setPrompt('');
            setMessages(prev => [...prev,
            { role: 'user', text: displayPrompt, timestamp: new Date().toLocaleTimeString() },
            { role: 'assistant', text: 'E-commerce websites are not supported. Our platform generates informational and business websites only. For online stores, please use a dedicated e-commerce platform like Shopify or WooCommerce.', timestamp: new Date().toLocaleTimeString(), isError: true },
            ]);
            // Restart wizard if no website generated yet
            if (versions.length === 0) {
                localStorage.removeItem(ONBOARDING_KEY);
                onboardingShown.current = false;
                setTimeout(() => setOnboardingStep(0), 1000);
            }
            return;
        }

        // Block if no websites remaining (new generation only, skip for admins)
        if (versions.length === 0 && authUser && !authUser.is_admin) {
            const genCount = authUser.generation_count || 0;
            const maxGen = authUser.max_generations || 2;
            if (genCount >= maxGen) {
                setPrompt('');
                setMessages(prev => [...prev,
                { role: 'user', text: displayPrompt, timestamp: new Date().toLocaleTimeString() },
                { role: 'assistant', text: `You've used all ${maxGen} website generations. Request more from the dashboard.`, timestamp: new Date().toLocaleTimeString(), isError: true },
                ]);
                localStorage.removeItem(ONBOARDING_KEY);
                onboardingShown.current = false;
                setTimeout(() => setOnboardingStep(0), 1000);
                return;
            }
        }

        // If user uploaded images and this is a new generation, show assignment modal
        if (assignedImages === undefined && uploadedFiles.images.length > 0 && versions.length === 0) {
            setPendingGenPrompt(promptText);
            setImageAssignModal(true);
            return;
        }

        // Check if this is a help question — answer instantly without using LLM tokens
        const helpAnswer = getHelpResponse(promptText);
        if (helpAnswer && versions.length > 0) {
            setPrompt('');
            setMessages(prev => [
                ...prev,
                { role: 'user', text: displayPrompt, timestamp: new Date().toLocaleTimeString() },
                { role: 'assistant', text: helpAnswer, timestamp: new Date().toLocaleTimeString(), isHelp: true },
            ]);
            return;
        }

        isGeneratingRef.current = true;
        setIsLoading(true);
        setError(null);
        setLoadingMessage(versions.length === 0 ? 'Analyzing your request...' : 'Applying changes...');
        setPrompt('');

        setMessages(prev => [...prev, { role: 'user', text: displayPrompt, timestamp: new Date().toLocaleTimeString() }]);

        // Async mode: submit to job queue and poll
        if (useAsync && versions.length === 0) {
            try {
                const job = await submitJob(promptText, niche || currentNiche);
                setActiveJobId(job.jobId);
                setLoadingMessage('Job queued... waiting for worker');
                pollJob(job.jobId);
                return;
            } catch (err) {
                setError(err.message || 'Failed to submit job');
                setMessages(prev => [...prev, { role: 'assistant', text: `Error: ${err.message}`, timestamp: new Date().toLocaleTimeString(), isError: true }]);
                setIsLoading(false); setLoadingMessage(''); isGeneratingRef.current = false;
                if (versions.length === 0) {
                    localStorage.removeItem(ONBOARDING_KEY);
                    onboardingShown.current = false;
                    setTimeout(() => setOnboardingStep(0), 1500);
                }
                return;
            }
        }

        // Use SSE streaming for all generation (new + iterations)
        {
            const isNew = !sessionId || versions.length === 0;
            const planMsgId = Date.now();
            // CRITICAL: capture the target page slot AT SEND TIME, not when the
            // response arrives. If the user switches tabs while the LLM is
            // working, currentPageRef will have moved by the time onComplete
            // fires — we must apply the result to the page the user originally
            // requested the edit on, not the page they happen to be looking at
            // when the response lands. This is the same pattern handleElementEdit
            // already uses (see `targetPage` capture there).
            const editTargetPage = isNew ? 'index' : (currentPageRef.current || 'index');
            setMessages(prev => [...prev, {
                role: 'assistant',
                text: isNew ? 'Let me plan your website...' : 'Applying your changes...',
                timestamp: new Date().toLocaleTimeString(),
                isPlan: true,
                planId: planMsgId,
                planSteps: [],
            }]);

            streamControllerRef.current = generateWebsiteStream(
                promptText, sessionId, niche || currentNiche,
                // onStage
                (stageData) => {
                    setLoadingMessage(stageData.message || 'Processing...');
                    setGenerationProgress(prev => ({ ...prev, stage: stageData.stage || prev.stage, message: stageData.message || '' }));

                    if (stageData.status === 'done') {
                        setMessages(prev => prev.map(msg => {
                            if (msg.planId === planMsgId) {
                                const steps = [...(msg.planSteps || []), {
                                    stage: stageData.stage,
                                    name: stageData.name,
                                    message: stageData.message,
                                    detail: stageData.detail || '',
                                    data: stageData.data || null,
                                    enhancedPrompt: stageData.enhanced_prompt || null,
                                }];

                                let planText = isNew ? "Here's my plan for your website:\n\n" : "Applying changes:\n\n";
                                for (const step of steps) {
                                    planText += `✓ **${step.message}**`;
                                    if (step.detail) planText += `\n   ${step.detail}`;
                                    planText += '\n';
                                }
                                // Attach enhanced prompt for display
                                const ep = steps.find(s => s.enhancedPrompt)?.enhancedPrompt || msg.enhancedPrompt || null;
                                return { ...msg, text: planText, planSteps: steps, enhancedPrompt: ep };
                            }
                            return msg;
                        }));
                    }
                },
                // onComplete
                (result) => {
                    streamControllerRef.current = null;
                    const newHtml = result.website.html;
                    const newCss = result.website.css;
                    const newJs = result.website.js || '';
                    // Only update visible html/css/js if the user is still on
                    // the page this edit was originally for. Otherwise the
                    // visible state would briefly show the wrong page's HTML
                    // (and trigger the racy auto-sync useEffect) — see the
                    // editTargetPage capture above for the full reasoning.
                    // For new generations (isNew=true), always update — there
                    // is no "other tab" the user could have switched to yet.
                    const stillOnTargetPage = isNew || currentPageRef.current === editTargetPage;
                    if (stillOnTargetPage) {
                        setHtml(newHtml); setCss(newCss); setJs(newJs);
                    }
                    setSessionId(result.sessionId);
                    setIsNewDesign(result.isNewDesign !== false);
                    if (result.meta) setSiteMeta(result.meta);

                    if (result.sections) setSections(result.sections);

                    // Multi-page support
                    let mp = false;
                    let resultPages = {};
                    let msgText = '';

                    if (result.addedPage && result.pages) {
                        // A new page was added (single→multipage or adding to existing multipage)
                        mp = true;
                        resultPages = result.pages;
                        setIsMultipage(true);
                        setPages(result.pages);
                        setCurrentPage(result.addedPage);
                        const addedTitle = result.addedPage.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                        msgText = `${addedTitle} page added! Use the page tabs to switch between pages.`;
                    } else if (isNew) {
                        // New generation: use whatever the backend says
                        mp = result.isMultipage || false;
                        setIsMultipage(mp);
                        if (mp && result.pages) {
                            resultPages = result.pages;
                            setPages(result.pages);
                            setCurrentPage('index');
                            msgText = `Your ${Object.keys(result.pages).length}-page website is ready! Use the page tabs above the preview to switch between pages.`;
                        } else {
                            setPages({});
                            setCurrentPage('index');
                            msgText = 'Your website is ready! Let me know if you\'d like any changes.';
                        }
                    } else {
                        // Normal iteration (chat edit) — uses the editTargetPage
                        // captured at SEND TIME (see top of this block). Do NOT
                        // re-read currentPageRef here: the user may have switched
                        // tabs while the LLM was working, and re-reading would
                        // route the result into the wrong slot.
                        mp = result.isMultipage || isMultipage;
                        if (mp && result.pages) {
                            // Backend sent updated pages dict — merge with current to prevent
                            // stale backend data from overwriting pages edited locally
                            const latestPgs = pagesRef.current;
                            const merged = { ...latestPgs };
                            for (const [slug, pgData] of Object.entries(result.pages)) {
                                if (slug === editTargetPage) {
                                    // Always use the edited page from the backend result
                                    merged[slug] = pgData;
                                } else if (!merged[slug]) {
                                    // New page from backend — add it
                                    merged[slug] = pgData;
                                }
                                // For other existing pages, keep the local version (fresher)
                            }
                            resultPages = merged;
                            setIsMultipage(true);
                            setPages(merged);
                        } else if (isMultipage && editTargetPage) {
                            // Fallback: update just the current page locally
                            const latestPgs = pagesRef.current;
                            resultPages = { ...latestPgs, [editTargetPage]: { html: newHtml, css: newCss } };
                            setPages(resultPages);
                        }
                        msgText = 'Changes applied! What else would you like to adjust?';
                    }

                    const newVersion = { html: newHtml, css: newCss, js: newJs, prompt: promptText, isMultipage: mp, pages: resultPages };
                    setVersions(prev => {
                        // See note on the async-job setVersions call above —
                        // truncate redo branch + cap total history at
                        // MAX_HISTORY_VERSIONS to prevent unbounded memory
                        // growth.
                        const trimmed = prev.slice(0, currentVersion + 1);
                        const updated = [...trimmed, newVersion];
                        const capped = updated.length > MAX_HISTORY_VERSIONS
                            ? updated.slice(-MAX_HISTORY_VERSIONS)
                            : updated;
                        setCurrentVersion(capped.length - 1);
                        return capped;
                    });

                    setMessages(prev => {
                        const vIdx = prev.filter(m => m.versionIndex !== undefined).length;
                        return [...prev, {
                            role: 'assistant',
                            text: msgText,
                            timestamp: new Date().toLocaleTimeString(),
                            versionIndex: vIdx,
                        }];
                    });

                    // Pass the merged pages dict so autosave targets the
                    // correct slot — `resultPages` was just computed above
                    // using the captured editTargetPage / addedPage / new
                    // generation result.
                    autoSave(
                        newHtml, newCss, newJs,
                        projectName || promptText.substring(0, 50),
                        mp && Object.keys(resultPages || {}).length ? resultPages : undefined,
                    );

                    setIsLoading(false); setLoadingMessage('');
                    setGenerationProgress({ stage: 0, total: 5, message: '' });
                    isGeneratingRef.current = false;
                    refreshUser(); // Update generation/edit counts
                    setUploadedFiles({ text: '', images: [] }); // Clear uploaded files
                    addToast(result.recovered ? 'Connection recovered — website ready!' : result.addedPage ? `${result.addedPage.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} page added!` : (isNew && mp) ? `${Object.keys(result.pages || {}).length}-page website generated!` : isNew ? 'Website generated successfully!' : 'Changes applied!', 'success');
                },
                // onError
                (errorMsg) => {
                    streamControllerRef.current = null;
                    const isRestricted = errorMsg.includes('[RESTRICTED]');
                    const displayMsg = errorMsg.replace('[RESTRICTED] ', '');
                    if (isRestricted) {
                        addToast(displayMsg, 'error', 8000);
                    } else {
                        setErrorBanner(errorMsg);
                    }
                    lastRetryPrompt.current = promptText;
                    setMessages(prev => [...prev, {
                        role: 'assistant', text: isRestricted ? `Restricted: ${displayMsg}` : `Error: ${errorMsg}`,
                        timestamp: new Date().toLocaleTimeString(), isError: true,
                    }]);
                    setIsLoading(false); setLoadingMessage('');
                    setGenerationProgress({ stage: 0, total: 5, message: '' });
                    isGeneratingRef.current = false;
                    // Restart wizard if no website generated yet
                    if (versions.length === 0) {
                        localStorage.removeItem(ONBOARDING_KEY);
                        onboardingShown.current = false;
                        setTimeout(() => setOnboardingStep(0), 1500);
                    }
                },
                templateId,
                currentPage,
                assignedImages || null,
                // Wizard-collected floating widgets (WhatsApp + social FAB).
                // The backend injects them after Stage 3, so the LLM never
                // sees them — generation stays deterministic.
                wizardData?.contactInfo ? {
                    recipientEmail: wizardData.contactInfo.email || '',
                    whatsapp: wizardData.contactInfo.whatsapp || '',
                    mapLink: wizardData.contactInfo.mapLink || '',
                    social: wizardData.contactInfo.social || {},
                } : null,
            );
        }
    };

    // ── Wizard: trigger generation after handleGenerate is defined ─────
    const handleWizardGenerate = () => {
        let composedPrompt = composeWizardPrompt(wizardData);
        // Append uploaded text content if any
        if (uploadedFiles.text) {
            composedPrompt += `\n\nAdditional business information from uploaded files:\n${uploadedFiles.text}`;
        }

        // Build a DISPLAY-ONLY version of the prompt for the chat bubble.
        // This includes the WhatsApp number and social media platforms the
        // user filled in — things the user wants to SEE confirmed in the
        // chat, but that we deliberately keep OUT of the LLM prompt
        // (composedPrompt) because they're injected as floating widgets
        // post-generation. Listing them in the LLM prompt would risk the
        // model rendering its own buttons that then collide with the
        // floating ones we inject ourselves.
        let displayPrompt = composedPrompt;
        const ci = wizardData.contactInfo || {};
        const extras = [];
        if (ci.whatsapp) {
            extras.push(`WhatsApp button: ${ci.whatsapp}`);
        }
        const social = ci.social || {};
        const filledSocial = [
            social.facebook && 'Facebook',
            social.instagram && 'Instagram',
            social.tiktok && 'TikTok',
            social.linkedin && 'LinkedIn',
            social.youtube && 'YouTube',
        ].filter(Boolean);
        if (filledSocial.length > 0) {
            extras.push(`Social media floating button: ${filledSocial.join(', ')}`);
        }
        if (extras.length > 0) {
            displayPrompt += `\n\n${extras.join('\n')}\n(These will be added automatically as floating buttons after the website is generated.)`;
        }

        setProjectName(wizardData.companyName);
        setWizardStep(-1);
        handleGenerate(composedPrompt, null, null, undefined, displayPrompt);
    };

    // ── Rollback to a specific message version ──────────────────────────

    const handleRollback = (versionIndex) => {
        if (versionIndex < 0 || versionIndex >= versions.length) return;
        const v = versions[versionIndex];
        if (!v.html || v.html.trim().length < 200) {
            addToast('This version has no content — cannot restore.', 'error');
            return;
        }
        setCurrentVersion(versionIndex);

        // Restore multi-page state from version
        const vIsMultipage = v.isMultipage || false;
        const vPages = (v.pages && Object.keys(v.pages).length > 0) ? v.pages : null;

        if (vIsMultipage && vPages) {
            // Version has full multipage data — restore it
            setIsMultipage(true);
            setPages(vPages);
            setCurrentPage('index');
            const indexData = vPages['index'];
            setHtml(indexData?.html || v.html);
            setCss(indexData?.css || v.css);
            setJs(v.js);
        } else if (isMultipage && !vPages) {
            // Currently multipage but version has no pages data —
            // update only the current page, don't wipe all pages
            const curPage = currentPageRef.current;
            setHtml(v.html); setCss(v.css); setJs(v.js);
            setPages(prev => ({ ...prev, [curPage]: { html: v.html, css: v.css } }));
        } else {
            // Single page — simple restore
            setHtml(v.html); setCss(v.css); setJs(v.js);
            setIsMultipage(false);
            setPages({});
            setCurrentPage('index');
        }

        setMessages(prev => [...prev, {
            role: 'system',
            text: `Rolled back to version ${versionIndex + 1}`,
            timestamp: new Date().toLocaleTimeString(),
        }]);
        // CRITICAL: sync EVERY page to the backend, not just the visible one.
        // See syncRolledBackVersionToBackend for the full reasoning. Without
        // this fix, settings save (which reads from the Redis session) would
        // silently clobber the restored React state with stale backend state.
        syncRolledBackVersionToBackend(v, v.html, v.css);
    };

    // ── Undo / Redo ─────────────────────────────────────────────────────

    // Skip light versions (no html data) — can only undo to versions with full content
    const canUndo = currentVersion > 0 && versions.slice(0, currentVersion).some(v => v.html);
    const canRedo = currentVersion < versions.length - 1 && versions.slice(currentVersion + 1).some(v => v.html);

    // Sync EVERY page in a multipage version back to the Redis session in
    // parallel. Used by handleRollback / handleUndo / handleRedo so the
    // backend session never lags behind the React state. See the comment
    // in handleRollback for the full reasoning — TL;DR: leaving other pages
    // stale on the backend caused settings save to clobber restored state.
    const syncRolledBackVersionToBackend = useCallback((v, fallbackHtml, fallbackCss) => {
        if (!sessionId) return;
        const visiblePage = currentPageRef.current || 'index';
        if (v.isMultipage && v.pages && Object.keys(v.pages).length > 0) {
            Promise.all(
                Object.entries(v.pages).map(([slug, pg]) =>
                    syncSession(sessionId, pg.html || '', pg.css || '', v.js, slug)
                        .catch(err => console.warn(`[VersionSync] Failed page ${slug}:`, err))
                )
            ).then(() => {
                const visible = v.pages[visiblePage];
                return syncSession(sessionId, visible?.html || fallbackHtml, visible?.css || fallbackCss, v.js, visiblePage)
                    .then(d => { if (d.sections) setSections(d.sections); });
            }).catch(() => { });
        } else {
            syncSession(sessionId, fallbackHtml, fallbackCss, v.js, visiblePage)
                .then(d => { if (d.sections) setSections(d.sections); })
                .catch(() => { });
        }
    }, [sessionId]);

    const handleUndo = useCallback(() => {
        if (currentVersion <= 0) return;
        // Find nearest previous version with full data
        let prev = currentVersion - 1;
        while (prev >= 0 && !versions[prev].html) prev--;
        if (prev < 0) return;
        const v = versions[prev];
        // For multipage: restore the correct page's content, not just v.html
        // v.html is whatever page was active at that version — use pages dict instead
        const curPage = currentPageRef.current;
        let restoreHtml = v.html;
        let restoreCss = v.css;
        if (v.isMultipage && v.pages && Object.keys(v.pages).length > 0) {
            // Use the version's full pages state (it was captured at that version)
            switchingPageRef.current = true;
            setPages(v.pages);
            setIsMultipage(true);
            // Use the current page's content from the version's pages dict
            const pageData = v.pages[curPage];
            if (pageData) {
                restoreHtml = pageData.html || v.html;
                restoreCss = pageData.css || v.css;
            } else {
                // Current page not in this version — keep current page's content unchanged
                const curPages = pagesRef.current;
                const curPageData = curPages[curPage];
                if (curPageData) {
                    restoreHtml = curPageData.html;
                    restoreCss = curPageData.css || v.css;
                }
            }
            requestAnimationFrame(() => { switchingPageRef.current = false; });
        }
        setHtml(restoreHtml); setCss(restoreCss); setJs(v.js);
        setCurrentVersion(prev);
        // Sync ALL multipage pages — see syncRolledBackVersionToBackend.
        syncRolledBackVersionToBackend(v, restoreHtml, restoreCss);
    }, [currentVersion, versions, syncRolledBackVersionToBackend]);

    const handleRedo = useCallback(() => {
        if (currentVersion >= versions.length - 1) return;
        // Find nearest next version with full data
        let next = currentVersion + 1;
        while (next < versions.length && !versions[next].html) next++;
        if (next >= versions.length) return;
        const v = versions[next];
        const curPage = currentPageRef.current;
        let restoreHtml = v.html;
        let restoreCss = v.css;
        if (v.isMultipage && v.pages && Object.keys(v.pages).length > 0) {
            // Use the version's full pages state (it was captured at that version)
            switchingPageRef.current = true;
            setPages(v.pages);
            setIsMultipage(true);
            const pageData = v.pages[curPage];
            if (pageData) {
                restoreHtml = pageData.html || v.html;
                restoreCss = pageData.css || v.css;
            } else {
                // Current page not in this version — keep current page's content unchanged
                const curPages = pagesRef.current;
                const curPageData = curPages[curPage];
                if (curPageData) {
                    restoreHtml = curPageData.html;
                    restoreCss = curPageData.css || v.css;
                }
            }
            requestAnimationFrame(() => { switchingPageRef.current = false; });
        }
        setHtml(restoreHtml); setCss(restoreCss); setJs(v.js);
        setCurrentVersion(next);
        // Sync ALL multipage pages — see syncRolledBackVersionToBackend.
        syncRolledBackVersionToBackend(v, restoreHtml, restoreCss);
    }, [currentVersion, versions, syncRolledBackVersionToBackend]);

    // Keyboard shortcuts: Ctrl+Z = undo, Ctrl+Shift+Z / Ctrl+Y = redo
    useEffect(() => {
        const handler = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                handleUndo();
            } else if ((e.metaKey || e.ctrlKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
                e.preventDefault();
                handleRedo();
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [handleUndo, handleRedo]);

    // ── CMS Mode (inline content editing) ──────────────────────────────

    // Use refs to always access latest state in the message handler (avoids stale closures)
    const cmsStateRef = useRef({});
    cmsStateRef.current = { html, css, js, versions, currentVersion, sessionId, isMultipage, pages, currentPage };

    useEffect(() => {
        const handleCmsMessage = (e) => {
            // SECURITY: only accept messages from our own origin. The preview
            // iframe is rendered via srcDoc with no `src` URL, so its
            // window.location.origin is the parent's origin (same-origin
            // sandbox). Any cross-origin postMessage is from an untrusted
            // source — drop it. Without this check, a malicious script in
            // a third-party tab targeting this window could trigger CMS
            // edits as if the user typed them.
            if (e.origin && e.origin !== window.location.origin) return;
            if (e.data?.type !== 'cms-edit') return;
            const { editType } = e.data;
            const st = cmsStateRef.current;

            // Extract updated HTML directly from the iframe DOM (no fragile selector matching)
            const iframe = document.querySelector('.preview-iframe');
            const cmsRoot = iframe?.contentDocument?.getElementById('__cms_root__');
            if (!cmsRoot) {
                console.warn('[CMS] Could not find __cms_root__ in iframe');
                return;
            }

            // Clean up any CMS UI artifacts before extracting.
            // Strip contenteditable unconditionally — if it leaks into saved
            // HTML, browsers make the element editable on the deployed site
            // and in admin previews without needing any script.
            cmsRoot.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
            cmsRoot.querySelectorAll('.cms-hover-outline, .cms-editing, .cms-img-outline').forEach(el => {
                el.classList.remove('cms-hover-outline', 'cms-editing', 'cms-img-outline');
            });

            const newHtml = cmsRoot.innerHTML;

            if (newHtml === st.html) {
                return;
            }

            setHtml(newHtml);

            // Build the merged pages dict ONCE off the captured st.currentPage
            // so the targeted slot is consistent across pages state, version
            // history and project autosave.
            const cmsTargetPage = st.currentPage;
            const cmsMergedPages = st.isMultipage
                ? { ...st.pages, [cmsTargetPage]: { html: newHtml, css: st.css } }
                : null;

            // Update multi-page state
            if (st.isMultipage) {
                setPages(cmsMergedPages);
            }

            // Push to version history for undo support. Cap at
            // MAX_HISTORY_VERSIONS to prevent unbounded memory growth.
            const newVersion = { html: newHtml, css: st.css, js: st.js, prompt: `[CMS: ${editType} edit]`, isMultipage: st.isMultipage, pages: cmsMergedPages || {} };
            const trimmed = st.versions.slice(0, st.currentVersion + 1);
            const newVersions = [...trimmed, newVersion];
            const cappedVersions = newVersions.length > MAX_HISTORY_VERSIONS
                ? newVersions.slice(-MAX_HISTORY_VERSIONS)
                : newVersions;
            setVersions(cappedVersions);
            setCurrentVersion(cappedVersions.length - 1);

            // Sync to backend Redis session so AI edits work on updated HTML
            if (st.sessionId) syncSession(st.sessionId, newHtml, st.css, st.js, cmsTargetPage)
                .then(d => { if (d.sections) setSections(d.sections); })
                .catch(() => { });

            // Auto-save to project if project exists — pass the merged pages
            // dict so the captured page slot is preserved.
            if (st.projectId) {
                handleSaveProject({ html: newHtml, css: st.css, js: st.js, pages: cmsMergedPages || undefined });
            }

            addToast('Content updated', 'success');
        };

        window.addEventListener('message', handleCmsMessage);
        return () => window.removeEventListener('message', handleCmsMessage);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [addToast]); // stable deps only — state accessed via ref

    // ── Element Editing ─────────────────────────────────────────────────

    const handleElementSelect = (element) => { setSelectedElement(element); setElementPrompt(''); };

    const handleElementAttach = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/svg+xml', 'image/gif'];
        if (!validTypes.includes(file.type)) { addToast('Only image files (JPG, PNG, WebP, SVG, GIF) are allowed', 'error'); return; }
        if (file.size > 5 * 1024 * 1024) { addToast('Image must be under 5MB', 'error'); return; }
        const preview = URL.createObjectURL(file);
        setElementAttachment({ file, preview, uploading: true, url: null });
        try {
            const result = await uploadFile(file, projectId || null, 'image');
            const absUrl = `${config.apiUrl}${result.url}`;
            setElementAttachment(prev => ({ ...prev, uploading: false, url: absUrl }));
        } catch (err) {
            addToast('Failed to upload image', 'error');
            URL.revokeObjectURL(preview);
            setElementAttachment(null);
        }
        e.target.value = '';
    };

    const handleRemoveAttachment = () => {
        if (elementAttachment?.preview) URL.revokeObjectURL(elementAttachment.preview);
        setElementAttachment(null);
    };

    const handleElementEdit = async () => {
        if (!selectedElement || !elementPrompt.trim() || isEditingRef.current) return;
        if (elementAttachment?.uploading) return;
        isEditingRef.current = true;
        setIsEditingElement(true);
        setError(null);

        // Capture target page NOW — before the async call, so tab switches don't corrupt it
        const targetPage = currentPageRef.current;

        try {
            let finalPrompt = elementPrompt;
            if (elementAttachment?.url) {
                finalPrompt += `\n\nUse this uploaded image URL: ${elementAttachment.url}`;
            }
            const result = await editElement(sessionId, selectedElement, finalPrompt, { html, css }, targetPage);
            if (result.success && !result.manualReplace) {
                const newHtml = result.website.html;
                // Safety: reject empty or near-empty HTML (LLM deleted everything)
                if (!newHtml || newHtml.trim().length < 200) {
                    addToast('Edit rejected — it would remove too much content. Use undo or try a different prompt.', 'error', 6000);
                    setIsEditingElement(false);
                    isEditingRef.current = false;
                    return;
                }
                const newCss = result.website.css || css; // Preserve existing CSS if backend returns empty
                const newJs = result.website.js || js;

                // Only update visible state if we're still on the same page
                if (currentPageRef.current === targetPage) {
                    setHtml(newHtml); setCss(newCss);
                    if (result.website.js) setJs(result.website.js);
                }

                // Build the merged pages dict ONCE — captured to targetPage,
                // not the live currentPageRef. Reused below for state, version
                // history and project autosave so they all agree on the slot.
                const latestPgs = pagesRef.current;
                const mergedPages = isMultipage
                    ? { ...latestPgs, [targetPage]: { html: newHtml, css: newCss } }
                    : null;

                // Update multi-page state — always use targetPage, not currentPage
                if (isMultipage) {
                    setPages(mergedPages);
                }

                const newVersion = { html: newHtml, css: newCss, js: newJs, prompt: `[Element: ${selectedElement.path}] ${elementPrompt}`, isMultipage, pages: mergedPages || {} };
                setVersions(prev => {
                    const u = [...prev.slice(0, currentVersion + 1), newVersion];
                    const capped = u.length > MAX_HISTORY_VERSIONS ? u.slice(-MAX_HISTORY_VERSIONS) : u;
                    setCurrentVersion(capped.length - 1);
                    return capped;
                });

                // Sync to backend Redis session — use targetPage
                if (sessionId) syncSession(sessionId, newHtml, newCss, newJs, targetPage)
                    .then(d => { if (d.sections) setSections(d.sections); })
                    .catch(() => { });

                setMessages(prev => [...prev,
                { role: 'user', text: `Edit ${selectedElement.tagName}: ${elementPrompt}`, timestamp: new Date().toLocaleTimeString() },
                { role: 'assistant', text: 'Element updated!', timestamp: new Date().toLocaleTimeString(), versionIndex: versions.length },
                ]);
                if (elementAttachment?.preview) URL.revokeObjectURL(elementAttachment.preview);
                setSelectedElement(null); setElementPrompt(''); setEditMode(false); setElementAttachment(null);
                addToast('Section updated', 'success');
                // Auto-save to project — pass the merged pages dict so the
                // save targets the captured page slot, even if the user
                // switched tabs while the edit was in flight.
                if (projectId) handleSaveProject({ html: newHtml, css: newCss, js: newJs, pages: mergedPages || undefined });
            } else {
                setError('Failed to edit element');
            }
        } catch (err) {
            console.error('[ElementEdit] Error:', err.message || err);
            const msg = err.message || 'Failed to edit element';
            if (msg.includes('[RESTRICTED]')) {
                addToast(msg.replace('[RESTRICTED] ', ''), 'error', 8000);
            } else {
                setError(msg);
            }
        } finally {
            setIsEditingElement(false);
            isEditingRef.current = false;
        }
    };

    const handleCancelEdit = () => {
        if (elementAttachment?.preview) URL.revokeObjectURL(elementAttachment.preview);
        setSelectedElement(null); setElementPrompt(''); setEditMode(false); setElementAttachment(null);
    };

    // ── Gallery Image Insert ─────────────────────────────────────────────
    const handleGallerySelect = (url, name) => {
        const fullUrl = url.startsWith('http') ? url : `${window.location.origin}${url}`;
        const insertPrompt = `Replace an image on the page with my uploaded image "${name}". Use this exact image URL: ${fullUrl}`;
        setPrompt(insertPrompt);
        setShowGallery(false);
        setTimeout(() => textareaRef.current?.focus(), 100);
    };

    // ── Save ────────────────────────────────────────────────────────────

    const handleSaveProject = async (overrideData) => {
        const h = overrideData?.html || html;
        const c = overrideData?.css || css;
        const j = overrideData?.js || js;
        const name = overrideData?.name || projectName || messages.find(m => m.role === 'user')?.text?.substring(0, 50) || 'Untitled Project';
        if (!h) return;
        setSaveStatus('saving');
        // For multipage: save all pages in metadata.
        // Prefer an explicit `pages` dict from the caller (edit handlers compute
        // this with the captured targetPage so the right slot is updated even
        // if the user switched tabs while the edit was in flight). Only fall
        // back to the live currentPageRef when no explicit dict is given.
        const latestPages = pagesRef.current;
        const latestCurrentPage = currentPageRef.current;
        const allPages = isMultipage
            ? (overrideData?.pages || { ...latestPages, [latestCurrentPage]: { html: h, css: c } })
            : {};
        // Persist version history in metadata so close/reopen + login/logout
        // restore the full undo/redo stack — not just the current snapshot.
        // Without this, the chat-message "Restore this version" buttons stop
        // working after reload because they reference versionIndex N but the
        // React `versions` array only has 1 entry on cold load.
        //
        // Cap at MAX_HISTORY_VERSIONS to bound metadata size. For multipage
        // projects each version stores ~30-100KB; 50 versions ≈ 5MB max.
        // Acceptable for PostgreSQL TEXT but worth watching if it grows.
        const trimmedVersions = versions.slice(-MAX_HISTORY_VERSIONS);
        // currentVersion is an index into the FULL versions array; if we
        // trimmed entries off the front, shift the index by the trim count.
        const trimOffset = versions.length - trimmedVersions.length;
        const persistedCurrentVersion = Math.max(0, currentVersion - trimOffset);

        const metadata = JSON.stringify({
            isMultipage,
            currentPage: latestCurrentPage,
            pages: allPages,
            messages: messages.slice(-50),
            versions: trimmedVersions,
            currentVersion: persistedCurrentVersion,
            deployedSiteId: deployedSiteId || undefined,
        });
        try {
            // For multipage, save index page as top-level for reliable restore
            const saveHtml = isMultipage && allPages['index']?.html ? allPages['index'].html : h;
            const saveCss = isMultipage && allPages['index']?.css ? allPages['index'].css : c;
            const result = await saveProject({
                project_id: projectId || undefined,
                name,
                html: saveHtml, css: saveCss, js: j,
                prompt: messages.filter(m => m.role === 'user').pop()?.text || '',
                metadata,
            });
            setProjectId(result.project_id);
            setSaveStatus('saved');
            addToast('Project saved', 'success');
            setTimeout(() => setSaveStatus(null), 2000);
        } catch (err) {
            console.error('Auto-save failed:', err);
            setSaveStatus('error');
            addToast('Failed to save project', 'error');
            setTimeout(() => setSaveStatus(null), 3000);
        }
    };

    // Auto-save after generation
    const autoSave = useCallback((newHtml, newCss, newJs, name, pages = undefined) => {
        setTimeout(() => {
            handleSaveProject({ html: newHtml, css: newCss, js: newJs, name, pages });
        }, 500);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectId, projectName]);

    const buildFullHTML = (title, forExport = false, overrideHtml = null, overrideCss = null) => {
        const t = title || siteMeta.title || 'Website';
        const d = siteMeta.description || '';
        const pageHtml = overrideHtml !== null ? overrideHtml : html;
        const pageCss = overrideCss !== null ? overrideCss : css;
        // Extract SEO meta tags from HTML comments
        const seoMatch = pageHtml.match(/<!-- SEO_META\s*([\s\S]*?)\s*END_SEO_META -->/);
        const seoMeta = seoMatch ? seoMatch[1].trim() : `<meta name="description" content="${d}">
  <meta property="og:title" content="${t}">
  <meta property="og:description" content="${d}">
  <meta property="og:type" content="website">`;
        // Extract favicon from HTML comments
        const faviconMatch = pageHtml.match(/<!-- FAVICON\s*([\s\S]*?)\s*END_FAVICON -->/);
        const favicon = faviconMatch ? faviconMatch[1].trim() : '';
        // Clean the comment blocks from the HTML body
        const cleanHtml = pageHtml.replace(/<!-- SEO_META[\s\S]*?END_SEO_META -->/g, '').replace(/<!-- FAVICON[\s\S]*?END_FAVICON -->/g, '');

        // Build JS block safely — avoid template literal to prevent backtick issues
        const parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '  <meta charset="UTF-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '  <title>' + t + '</title>',
            '  ' + seoMeta,
            '  ' + favicon,
            '  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
            '  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css">',
            '  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css">',
            '  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.css">',
            '  <style>',
            pageCss || '',
            BUILTIN_ANIMATION_CSS,
            '  </style>',
            '</head>',
            '<body>',
            cleanHtml || '',
            '  <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"></script>',
            '  <script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.16/dist/typed.umd.js"></script>',
            '  <script src="https://cdn.jsdelivr.net/npm/vanilla-tilt@1.8.1/dist/vanilla-tilt.min.js"></script>',
            '  <script src="https://cdn.jsdelivr.net/npm/tsparticles-slim@2.12.0/tsparticles.slim.bundle.min.js"></script>',
            '  <script src="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.min.js"></script>',
            '  <script src="https://cdn.jsdelivr.net/npm/lenis@1.0.42/dist/lenis.min.js"></script>',
            '  <script>',
            '    document.addEventListener("DOMContentLoaded", function() {',
            '      // AOS init',
            '      if(typeof AOS!=="undefined"){AOS.init({duration:800,once:true,offset:0});setTimeout(function(){AOS.refresh()},300);}',
            '      // Force visibility fallback',
            '      setTimeout(function(){document.querySelectorAll("[data-aos]").forEach(function(el){el.style.opacity="1";el.style.transform="none";el.classList.add("aos-animate")})},2000);',
            '      // Mobile hamburger — event delegation (works regardless of DOM timing)',
            '      (function(){',
            '        var tSel=".nav-toggle,.hamburger,.mobile-toggle,.menu-toggle,.navbar-toggle,button[aria-label=\\"Menu\\"],.mobile-menu-btn,.burger";',
            '        var mSel=".nav-links,.nav-menu,.mobile-menu,.navbar-menu,.navbar-links,.menu-items,.mobile-nav,nav>ul:not(.footer-links)";',
            '        document.addEventListener("click",function(e){',
            '          var btn=e.target.closest(tSel);if(btn){e.preventDefault();e.stopPropagation();var m=document.querySelector(mSel);if(m){m.classList.toggle("active");m.classList.toggle("open");btn.classList.toggle("active");var o=m.classList.contains("active");btn.setAttribute("aria-expanded",o);btn.innerHTML=o?"<i class=\\"fa-solid fa-xmark\\"></i>":"<i class=\\"fa-solid fa-bars\\"></i>";}return;}',
            '          var nl=e.target.closest(mSel+" a");if(nl){var t2=document.querySelector(tSel);var m2=document.querySelector(mSel);if(t2&&m2){m2.classList.remove("active","open");t2.classList.remove("active");t2.setAttribute("aria-expanded","false");t2.innerHTML="<i class=\\"fa-solid fa-bars\\"></i>";}return;}',
            '          var t3=document.querySelector(tSel);var m3=document.querySelector(mSel);if(t3&&m3&&m3.classList.contains("active")&&!t3.contains(e.target)&&!m3.contains(e.target)){m3.classList.remove("active","open");t3.classList.remove("active");t3.setAttribute("aria-expanded","false");t3.innerHTML="<i class=\\"fa-solid fa-bars\\"></i>";}',
            '        });',
            '      })();',
            '      // Testimonial carousel — universal',
            '      (function(){',
            '        var sec=document.querySelector("[data-section-type=\\"testimonials\\"]")||document.querySelector(".testimonials")||document.querySelector("#testimonials");',
            '        if(!sec)return;',
            '        var sSel=[".testimonial-card",".testimonial-item",".testimonial-slide",".testimonial",".review-card",".review-item",".slide",".carousel-item",".slider-item"];',
            '        var slides=[],wrap=null;',
            '        for(var s=0;s<sSel.length;s++){slides=sec.querySelectorAll(sSel[s]);if(slides.length>1){wrap=slides[0].parentElement;break;}}',
            '        if(slides.length<=1){var wSel=[".testimonial-wrapper",".testimonials-wrapper",".testimonial-container",".carousel-wrapper",".slider-wrapper",".slider",".carousel",".testimonial-track"];for(var w=0;w<wSel.length;w++){wrap=sec.querySelector(wSel[w]);if(wrap&&wrap.children.length>1){slides=wrap.children;break;}}}',
            '        if(slides.length<=1)return;',
            '        var cur=0,tot=slides.length;',
            '        if(wrap){wrap.style.position="relative";wrap.style.overflow="hidden";wrap.style.display="block";wrap.style.transform="none";}',
            '        for(var i=0;i<tot;i++){slides[i].style.position=i===0?"relative":"absolute";slides[i].style.top="0";slides[i].style.left="0";slides[i].style.width="100%";slides[i].style.transform="none";slides[i].style.opacity=i===0?"1":"0";slides[i].style.visibility=i===0?"visible":"hidden";slides[i].style.transition="opacity 0.4s ease";}',
            '        function getDots(){var d=sec.querySelectorAll(".dot,.carousel-dot,.slider-dot,.indicator,.pagination-dot,[data-slide]");if(!d.length){var dc=sec.querySelector(".dots,.pagination,.carousel-dots,.slider-dots,.indicators,.carousel-indicators");if(dc)d=dc.children;}return d;}',
            '        function show(idx){for(var i=0;i<tot;i++){slides[i].style.opacity=i===idx?"1":"0";slides[i].style.visibility=i===idx?"visible":"hidden";slides[i].style.position=i===idx?"relative":"absolute";}var d=getDots();for(var j=0;j<d.length;j++){d[j].classList.toggle("active",j===idx);d[j].style.opacity=j===idx?"1":"0.4";}cur=idx;}',
            '        var dots=getDots();for(var d=0;d<dots.length;d++){(function(i){dots[i].style.cursor="pointer";dots[i].addEventListener("click",function(e){e.preventDefault();show(i)})})(d);}',
            '        var prev=sec.querySelector(".prev,.prev-btn,.carousel-prev,.slider-prev,[data-prev]");',
            '        var next=sec.querySelector(".next,.next-btn,.carousel-next,.slider-next,[data-next]");',
            '        if(prev)prev.addEventListener("click",function(e){e.preventDefault();show((cur-1+tot)%tot)});',
            '        if(next)next.addEventListener("click",function(e){e.preventDefault();show((cur+1)%tot)});',
            '        var timer=setInterval(function(){show((cur+1)%tot)},5000);',
            '        sec.addEventListener("mouseenter",function(){clearInterval(timer)});',
            '        sec.addEventListener("mouseleave",function(){timer=setInterval(function(){show((cur+1)%tot)},5000)});',
            '      })();',
            '    });',
            '  </script>',
            '  <script>',
            BUILTIN_ANIMATION_JS_DOWNLOAD,
            '  </script>',
        ];

        // Add user JS as a SEPARATE script tag to avoid any escaping issues
        if (js && js.trim()) {
            parts.push('  <script>');
            parts.push(js);
            parts.push('  </script>');
        }

        parts.push('</body>');
        parts.push('</html>');

        return parts.join('\n');
    };

    const handleExport = async () => {
        if (isMultipage && Object.keys(pages).length > 0) {
            // Multi-page: export as ZIP
            const zip = new JSZip();
            // Save current page state back to pages first
            const allPages = { ...pages, [currentPage]: { html, css } };
            for (const [slug, pageData] of Object.entries(allPages)) {
                const filename = slug === 'index' ? 'index.html' : `${slug}.html`;
                const pageHtml = buildFullHTML(
                    slug === 'index' ? (siteMeta.title || 'Home') : slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                    true,
                    pageData.html,
                    pageData.css
                );
                zip.file(filename, pageHtml);
            }
            const blob = await zip.generateAsync({ type: 'blob' });
            const url = URL.createObjectURL(blob); const a = document.createElement('a');
            a.href = url; a.download = 'website.zip'; a.click(); URL.revokeObjectURL(url);
            addToast(`Downloaded ${Object.keys(allPages).length} pages as ZIP`, 'success');
        } else {
            // Single-page: export as HTML
            const full = buildFullHTML(siteMeta.title || 'Generated Website', true);
            const blob = new Blob([full], { type: 'text/html' });
            const url = URL.createObjectURL(blob); const a = document.createElement('a');
            a.href = url; a.download = 'website.html'; a.click(); URL.revokeObjectURL(url);
            addToast('Downloaded successfully', 'success');
        }
    };

    const handleReset = async () => {
        if (sessionId) { try { await clearSession(sessionId); } catch (e) { /* */ } }
        setHtml(''); setCss(''); setJs(''); setError(null);
        setSessionId(null); setIsNewDesign(true);
        setMessages([]); setVersions([]); setCurrentVersion(-1);
        setEditMode(false); setCmsMode(false); setSelectedElement(null); setElementPrompt('');
        setProjectId(null); setSaveStatus(null);
        setIsMultipage(false); setPages({}); setCurrentPage('index');
        setWizardStep(-1); // also exit the onboarding wizard
        setOnboardingStep(-1); // don't re-show tour
        hasAutoGenerated.current = false;
        sessionStorage.removeItem(SESSION_STORAGE_KEY);
    };

    // ── Multi-page: switch active page ────────────────────────────────
    const htmlRef = useRef(html);
    htmlRef.current = html;
    const cssRef = useRef(css);
    cssRef.current = css;
    const jsRef = useRef(js);
    jsRef.current = js;
    const sessionIdRef = useRef(sessionId);
    sessionIdRef.current = sessionId;

    const handlePageSwitch = useCallback((slug) => {
        const curPages = pagesRef.current;
        const curHtml = htmlRef.current;
        const curCss = cssRef.current;
        const curPage = currentPageRef.current;
        const curSessionId = sessionIdRef.current;

        // Try exact match first, then fuzzy match (e.g. "contact-us" → "contact", "book-now" → "booking")
        let targetSlug = slug;
        if (!curPages[targetSlug]) {
            // Try partial match: find a page whose slug contains the target or vice versa
            const pageKeys = Object.keys(curPages);
            const match = pageKeys.find(k =>
                k !== 'index' && (k.includes(targetSlug) || targetSlug.includes(k))
            );
            if (match) {
                targetSlug = match;
            } else {
                // Try common CTA mappings
                const ctaMap = {
                    'book': 'booking', 'book-now': 'booking', 'booknow': 'booking',
                    'reserve': 'booking', 'reservation': 'booking', 'appointment': 'booking', 'schedule': 'booking',
                    'contact-us': 'contact', 'contactus': 'contact', 'get-in-touch': 'contact', 'reach-us': 'contact',
                    'get-started': 'contact', 'getstarted': 'contact', 'our-services': 'services',
                    'about-us': 'about', 'our-menu': 'menu', 'our-rooms': 'rooms'
                };
                const mapped = ctaMap[targetSlug];
                if (mapped && curPages[mapped]) {
                    targetSlug = mapped;
                } else {
                    return;
                }
            }
        }
        if (targetSlug === curPage) {
            return;
        }
        slug = targetSlug;

        // 1. Save current page's live html/css
        const updated = { ...curPages, [curPage]: { html: curHtml, css: curCss } };
        // 2. Read target page
        const target = updated[slug];

        // 3. Set switching guard — prevents the useEffect sync from overwriting
        // pages during the transition when html changes before currentPage updates
        switchingPageRef.current = true;

        // 4. Update all state
        setPages(updated);
        setHtml(target?.html || '');
        setCss(target?.css || curCss);
        setCurrentPage(slug);

        // 5. Clear switching guard after React processes the batch
        // Use setTimeout to ensure all state updates and effects have been committed
        setTimeout(() => {
            switchingPageRef.current = false;
        }, 100);

        // 5b. Scroll iframe to top when switching pages
        try {
            const iframe = document.querySelector('.preview-iframe');
            if (iframe?.contentWindow) {
                iframe.contentWindow.scrollTo(0, 0);
            }
        } catch (e) { /* cross-origin safety */ }

        // 4. Sync the NEW page's HTML to the backend session so section edits target the right page
        if (curSessionId && target?.html) {
            syncSession(curSessionId, target.html, target.css || curCss, jsRef.current || '', slug)
                .then(() => {
                    // 5. Refresh sections list for the new page
                    getSections(curSessionId, slug).then(d => setSections(d.sections || [])).catch(() => { });
                })
                .catch(() => { });
        }
    }, []);

    // ── Inter-page navigation from iframe links ─────────────────────────
    useEffect(() => {
        const handlePageNavigate = (e) => {
            // SECURITY: same-origin only — see handleCmsMessage above for the
            // full reasoning. Drop any cross-origin postMessage.
            if (e.origin && e.origin !== window.location.origin) return;
            if (e.data?.type === 'page-navigate' && e.data.slug && isMultipage) {
                handlePageSwitch(e.data.slug);
            }
        };
        window.addEventListener('message', handlePageNavigate);
        return () => window.removeEventListener('message', handlePageNavigate);
    }, [isMultipage, handlePageSwitch]);

    // ── REMOVED: racy auto-sync useEffect ────────────────────────────────
    //
    // There used to be a useEffect here that wrote `pages[currentPage] = html`
    // whenever `html` changed. It was the source of the recurring multipage
    // corruption bug ("I edit Home, switch to Contact, now Contact has Home's
    // content"). The effect had no awareness of which page the current `html`
    // value actually belonged to — when a delayed edit response called
    // setHtml() after the user had switched tabs, the effect blindly wrote
    // the wrong page's HTML into the now-current slot.
    //
    // The defensive heuristics (size ratio, first-200-chars match,
    // switchingPageRef 100ms timeout) were band-aids that caught some races
    // but not all. The 100ms timeout in particular cleared too early for
    // late-arriving LLM responses.
    //
    // The fix: rely on EXPLICIT setPages calls in every edit handler, with
    // the target page captured AT SEND TIME (not at completion time).
    // Every multipage code path that calls setHtml is paired with a setPages
    // call that uses the captured slot. Verified call sites:
    //   - handleElementEdit       → setPages(mergedPages) with captured targetPage
    //   - handleGenerate onComplete → setPages(merged) with captured editTargetPage
    //   - CMS inline edit          → setPages(cmsMergedPages)
    //   - handleSectionUpdate      → setPages(sectionMergedPages)
    //   - handlePageSwitch         → setPages(updated) before setHtml
    //   - version restore          → setPages(v.pages)
    //
    // switchingPageRef is kept as a no-op ref so existing call sites still
    // compile; their writes are harmless. Can be cleaned up in a follow-up.
    const switchingPageRef = useRef(false);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleGenerate(); }
    };

    // ── Section/Component handlers ──────────────────────────────────────

    const handleSectionUpdate = (newHtml, newCss, newJs, actionLabel) => {
        setHtml(newHtml); setCss(newCss); if (newJs !== undefined) setJs(newJs);
        // Update multi-page state
        // Build the merged pages dict ONCE so state, version history and
        // project autosave all agree on the targeted page slot.
        const sectionTargetPage = currentPage;
        const sectionMergedPages = isMultipage
            ? { ...pagesRef.current, [sectionTargetPage]: { html: newHtml, css: newCss } }
            : null;

        if (isMultipage) {
            setPages(sectionMergedPages);
        }
        // Refresh sections for the current page
        if (sessionId) getSections(sessionId, sectionTargetPage).then(d => setSections(d.sections || [])).catch(() => { });
        // Push version
        const label = actionLabel || 'Section edit';
        const newVersion = { html: newHtml, css: newCss, js: newJs || js, prompt: `[${label}]`, isMultipage, pages: sectionMergedPages || {} };
        const trimmedSec = versions.slice(0, currentVersion + 1);
        const merged = [...trimmedSec, newVersion];
        const newVersions = merged.length > MAX_HISTORY_VERSIONS
            ? merged.slice(-MAX_HISTORY_VERSIONS)
            : merged;
        setVersions(newVersions);
        setCurrentVersion(newVersions.length - 1);
        // Add chat messages
        setMessages(prev => [
            ...prev,
            { role: 'user', text: label, timestamp: new Date().toLocaleTimeString() },
            { role: 'assistant', text: `Done! ${label}.`, timestamp: new Date().toLocaleTimeString(), versionIndex: newVersions.length - 1 },
        ]);
        addToast('Section updated', 'success');
        // Auto-save to project — pass the merged pages dict so the targeted
        // slot is preserved (avoids overwrite when user has switched tabs).
        if (projectId) handleSaveProject({ html: newHtml, css: newCss, js: newJs || js, pages: sectionMergedPages || undefined });
    };

    const handleCardClick = (item) => {
        // Load template directly — no regeneration. Exits the wizard so the
        // questionnaire doesn't keep rendering alongside the loaded template.
        setWizardStep(-1);
        setIsNewDesign(false);

        const loadInto = (tHtml, tCss, tJs) => {
            setHtml(tHtml);
            setCss(tCss);
            setJs(tJs);
            setMessages([{ role: 'assistant', text: `Template "${item.name}" loaded. Describe the changes you'd like to make.`, timestamp: new Date().toLocaleTimeString() }]);
            setVersions([{ html: tHtml, css: tCss, js: tJs, prompt: `Template: ${item.name}`, timestamp: new Date().toISOString() }]);
            setCurrentVersion(0);
            // Hydrate a fresh backend session so chat/element-edit/sections work.
            // (Previously called syncSession with an object as first arg, which
            // is typed as `sessionId: str` → 422 'Input should be a valid string'.)
            restoreSession(tHtml, tCss, tJs, null)
                .then(data => {
                    if (data?.sessionId) setSessionId(data.sessionId);
                    if (data?.sections) setSections(data.sections);
                })
                .catch(() => { /* non-fatal */ });
        };

        const preview = templatePreviews[item.id];
        if (preview && preview.html) {
            loadInto(preview.html, preview.css || '', preview.js || '');
        } else {
            getTemplateFull(item.id).then(data => {
                if (data && data.html) {
                    loadInto(data.html, data.css || '', data.js || '');
                }
            }).catch(() => {
                setMessages(prev => [...prev, { role: 'assistant', text: 'Failed to load template. Please try again.', timestamp: new Date().toLocaleTimeString(), isError: true }]);
            });
        }
    };

    // ── Onboarding handlers ────────────────────────────────────────────
    const handleOnboardingNext = () => {
        if (onboardingStep < ONBOARDING_STEPS.length - 1) {
            setOnboardingStep(prev => prev + 1);
        } else {
            setOnboardingStep(-1);
            localStorage.setItem(ONBOARDING_KEY, 'true');
        }
    };

    const handleOnboardingSkip = () => {
        setOnboardingStep(-1);
        localStorage.setItem(ONBOARDING_KEY, 'true');
    };

    // ── Stop generation handler ────────────────────────────────────────
    const handleStopGeneration = () => {
        // Abort SSE stream
        if (streamControllerRef.current) {
            streamControllerRef.current.abort();
            streamControllerRef.current = null;
        }
        // Cancel job polling
        if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
        }
        setActiveJobId(null);
        setIsLoading(false);
        setLoadingMessage('');
        setJobProgress(0);
        setGenerationProgress({ stage: 0, total: 5, message: '' });
        isGeneratingRef.current = false;
        setMessages(prev => [...prev, {
            role: 'assistant',
            text: 'Generation stopped. You can start again with a new prompt or pick a template.',
            timestamp: new Date().toLocaleTimeString(),
        }]);
    };

    // ── Error retry handler ─────────────────────────────────────────────
    const handleErrorRetry = () => {
        setErrorBanner(null);
        if (lastRetryPrompt.current) {
            handleGenerate(lastRetryPrompt.current);
        }
    };

    const hasContent = html || isLoading;

    // ═══════════════════════════════════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════════════════════════════════

    const impersonateInfo = (() => { try { const v = sessionStorage.getItem('impersonating') || localStorage.getItem('impersonating'); return v ? JSON.parse(v) : null; } catch { return null; } })();

    return (
        <div className="gn-layout" style={impersonateInfo ? { paddingTop: 40 } : undefined}>
            {impersonateInfo && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
                    background: '#f59e0b', color: '#000', padding: '6px 16px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
                    fontSize: 13, fontWeight: 600, height: 40,
                }}>
                    <span>Viewing as: {impersonateInfo.email} (read-only)</span>
                    <button onClick={() => {
                        const adminToken = sessionStorage.getItem('admin_token_backup') || localStorage.getItem('admin_token_backup');
                        if (adminToken) sessionStorage.setItem('token', adminToken);
                        sessionStorage.removeItem('admin_token_backup');
                        localStorage.removeItem('admin_token_backup');
                        sessionStorage.removeItem('impersonating');
                        localStorage.removeItem('impersonating');
                        window.location.href = '/admin';
                    }} style={{
                        background: '#000', color: '#fff', border: 'none', borderRadius: 4,
                        padding: '4px 12px', cursor: 'pointer', fontSize: 13, fontWeight: 600,
                    }}>Stop Impersonating</button>
                </div>
            )}
            {/* ─── LEFT: Chat Sidebar ─── */}
            <aside ref={sidebarRef} className={`gn-chat-sidebar ${isMobile && mobileTab !== 'chat' ? 'gn-hidden' : ''}`} style={!isMobile ? { width: sidebarWidth, minWidth: sidebarWidth } : undefined}>
                {/* Chat header */}
                <div className="gn-chat-header">
                    <button className="gn-icon-btn" onClick={() => navigate('/dashboard')} title="Dashboard">
                        <ArrowLeft size={18} />
                    </button>
                    <img src="/mfz-logo.webp" alt="Web AI" className="gn-chat-logo" />
                    <span className="gn-chat-title">AI Powered</span>
                    <ConnectionIndicator status={connectionStatus} />
                    <div style={{ flex: 1 }} />
                    {html && (
                        <button className="gn-icon-btn" onClick={handleReset} title="New Design">
                            <RefreshCw size={16} />
                        </button>
                    )}
                </div>

                {/* Chat messages */}
                <div className="gn-chat-messages">
                    {messages.length === 0 && !isLoading && !wizardActive && (
                        <div className="gn-chat-welcome">
                            <Sparkles size={24} />
                            <h3>Welcome to Web AI</h3>
                            <p>Describe the website you want, or pick a template from the right panel.</p>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div key={i} className={`gn-msg ${msg.role} ${msg.isError ? 'error' : ''}`}>
                            {msg.role === 'system' ? (
                                <div className="gn-msg-system">{msg.text}</div>
                            ) : (
                                <>
                                    <div className="gn-msg-avatar">
                                        {msg.role === 'user' ? 'You' : 'AI'}
                                    </div>
                                    <div className="gn-msg-content">
                                        {msg.isPlan && msg.planSteps?.length > 0 ? (
                                            <div className="gn-plan-steps">
                                                <div className="gn-plan-title">Here's my plan for your website:</div>
                                                {msg.planSteps.map((step, si) => (
                                                    <div key={si} className="gn-plan-step">
                                                        <span className="gn-plan-check">&#10003;</span>
                                                        <div className="gn-plan-step-content">
                                                            <span className="gn-plan-step-msg">{step.message}</span>
                                                            {step.detail && <span className="gn-plan-step-detail">{step.detail}</span>}
                                                            {step.data?.sections && (
                                                                <div className="gn-plan-pills">
                                                                    {step.data.sections.map((s, pi) => (
                                                                        <span key={pi} className="gn-plan-pill">{s.replace(/_/g, ' ')}</span>
                                                                    ))}
                                                                </div>
                                                            )}
                                                            {step.data?.primary && (
                                                                <div className="gn-plan-colors">
                                                                    <span className="gn-plan-swatch" style={{ background: step.data.primary }} title={step.data.primary} />
                                                                    {step.data.accent && <span className="gn-plan-swatch" style={{ background: step.data.accent }} title={step.data.accent} />}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                                {msg.enhancedPrompt && (
                                                    <details className="gn-enhanced-prompt">
                                                        <summary>View enhanced prompt</summary>
                                                        <pre>{msg.enhancedPrompt}</pre>
                                                    </details>
                                                )}
                                            </div>
                                        ) : (
                                            <div className="gn-msg-text">{msg.text}</div>
                                        )}
                                        <span className="gn-msg-time">{msg.timestamp}</span>
                                        {/* Rollback button under AI messages that have a version */}
                                        {msg.role === 'assistant' && msg.versionIndex !== undefined && msg.versionIndex !== currentVersion && (
                                            <button
                                                className="gn-rollback-btn"
                                                onClick={() => handleRollback(msg.versionIndex)}
                                            >
                                                <RotateCcw size={13} />
                                                Restore this version
                                            </button>
                                        )}
                                        {msg.role === 'assistant' && msg.versionIndex !== undefined && msg.versionIndex === currentVersion && (
                                            <span className="gn-version-tag">Current version</span>
                                        )}
                                        {/* Thumbs feedback — only on AI replies that resulted in a version (a real edit) */}
                                        {msg.role === 'assistant' && msg.versionIndex !== undefined && (
                                            <FeedbackThumbs
                                                msgKey={`${msg.versionIndex}-${msg.timestamp}`}
                                                sessionId={sessionId}
                                                addToast={addToast}
                                            />
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    ))}

                    {isLoading && (
                        <div className="gn-msg assistant">
                            <div className="gn-msg-avatar">AI</div>
                            <div className="gn-msg-content">
                                <div className="gn-typing">
                                    <span /><span /><span />
                                </div>
                                <span className="gn-msg-time">{loadingMessage}</span>
                            </div>
                        </div>
                    )}

                    {/* Wizard step UI */}
                    {wizardActive && !isLoading && (
                        <>
                            {selectedDomain && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', margin: '0 0 12px', background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.25)', borderRadius: 10, fontSize: 13, color: '#a7f3d0' }}>
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                                    <span>Building for <strong style={{ color: '#34d399' }}>{selectedDomain}</strong> — we'll connect this domain after deploy.</span>
                                </div>
                            )}
                            <WizardQuestionUI
                                step={wizardStep}
                                data={wizardData}
                                onAnswer={handleWizardAnswer}
                                onSkip={handleWizardSkip}
                                onBack={handleWizardBack}
                                onGenerate={handleWizardGenerate}
                                onBrowseTemplates={handleBrowseTemplates}
                                onFileUpload={handleFileUpload}
                                uploadedFileCount={uploadedFiles.images.length + (uploadedFiles.text ? 1 : 0)}
                                hasSelectedDomain={!!selectedDomain}
                                onRequestBuyDomain={(suggestion) => setWizardBuyTarget(suggestion)}
                            />
                        </>
                    )}

                    <div ref={chatEndRef} />
                </div>

                {/* Chat input — hidden during wizard (wizard provides its own inputs) */}
                {!wizardActive && (
                    <div className="gn-chat-input-area">
                        {!html && !isLoading && (
                            <div className="gn-project-name-row">
                                <input
                                    type="text"
                                    className="gn-project-name-input"
                                    placeholder="Project name (e.g. My Business Site)"
                                    value={projectName}
                                    onChange={(e) => setProjectName(e.target.value)}
                                    maxLength={60}
                                />
                            </div>
                        )}
                        {/* Uploaded images preview */}
                        {uploadedFiles.images.length > 0 && !html && (
                            <div style={{ display: 'flex', gap: 6, padding: '6px 12px', flexWrap: 'wrap' }}>
                                {uploadedFiles.images.map((img, i) => (
                                    <div key={i} style={{ position: 'relative', width: 40, height: 40, borderRadius: 6, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
                                        <img src={img.url} alt={img.filename} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                        <button onClick={() => setUploadedFiles(prev => ({ ...prev, images: prev.images.filter((_, j) => j !== i) }))} style={{ position: 'absolute', top: -2, right: -2, width: 14, height: 14, borderRadius: '50%', background: '#ef4444', border: 'none', color: '#fff', fontSize: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><X size={8} /></button>
                                    </div>
                                ))}
                                <span style={{ fontSize: 11, color: '#6b7280', alignSelf: 'center' }}>{uploadedFiles.images.length} image{uploadedFiles.images.length > 1 ? 's' : ''}</span>
                            </div>
                        )}
                        <div className="gn-chat-input-wrap">
                            {!html && (
                                <>
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        multiple
                                        accept=".pdf,.txt,.doc,.docx,.md,.rtf,.csv,.jpg,.jpeg,.png,.webp,.gif,.svg,.zip"
                                        style={{ display: 'none' }}
                                        onChange={(e) => handleFileUpload(e.target.files)}
                                    />
                                    <button
                                        className="gn-send-btn"
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={isLoading || uploadingFiles}
                                        title="Upload files (PDF, text, images)"
                                        style={{ opacity: 0.6 }}
                                    >
                                        {uploadingFiles ? <span className="gn-spinner" /> : <Paperclip size={16} />}
                                    </button>
                                </>
                            )}
                            <textarea
                                ref={textareaRef}
                                className="gn-chat-input"
                                placeholder={html ? 'Describe changes...' : 'Describe your website...'}
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                onKeyDown={handleKeyDown}
                                disabled={isLoading}
                                rows={1}
                            />
                            <button
                                className="gn-send-btn"
                                onClick={() => handleGenerate()}
                                disabled={!prompt.trim() || isLoading}
                            >
                                {isLoading ? <span className="gn-spinner" /> : <Send size={18} />}
                            </button>
                        </div>
                    </div>
                )}
            </aside>

            {/* ─── Image Assignment Modal ─── */}
            {imageAssignModal && uploadedFiles.images.length > 0 && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10000 }} onClick={() => { setImageAssignModal(false); setPendingGenPrompt(null); }}>
                    <div style={{ background: '#1a1a2e', borderRadius: 16, padding: '24px 28px', maxWidth: 520, width: '95%', maxHeight: '85vh', overflow: 'auto', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 20px 60px rgba(0,0,0,0.5)' }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                            <h3 style={{ color: '#f3f4f6', margin: 0, fontSize: 16 }}>Assign Images to Sections</h3>
                            <button onClick={() => { setImageAssignModal(false); setPendingGenPrompt(null); }} style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer' }}><X size={18} /></button>
                        </div>
                        <p style={{ fontSize: 13, color: '#9ca3af', marginBottom: 16 }}>
                            Click an image, then select which section it should appear in. Unassigned images will be used as extras or in gallery.
                        </p>

                        {/* Image thumbnails */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))', gap: 10, marginBottom: 20 }}>
                            {uploadedFiles.images.map((img, i) => {
                                const assigned = imageAssignments[img.url];
                                return (
                                    <div key={i} style={{ position: 'relative', borderRadius: 8, overflow: 'hidden', border: assigned ? '2px solid #34d399' : '2px solid rgba(255,255,255,0.08)', cursor: 'pointer', aspectRatio: '1' }} title={img.filename}>
                                        <img src={img.url} alt={img.filename} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                        {assigned && (
                                            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'rgba(0,0,0,0.75)', padding: '3px 6px', fontSize: 10, color: '#34d399', fontWeight: 600, textTransform: 'capitalize' }}>
                                                {assigned}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Section buttons */}
                        <div style={{ marginBottom: 16 }}>
                            <label style={{ fontSize: 12, color: '#6b7280', display: 'block', marginBottom: 8 }}>Assign selected images to:</label>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                {['hero', 'about', 'services', 'team', 'gallery', 'contact', 'features', 'portfolio'].map(section => {
                                    const count = Object.values(imageAssignments).filter(v => v === section).length;
                                    return (
                                        <button
                                            key={section}
                                            onClick={() => {
                                                // Find first unassigned image and assign it to this section
                                                const unassigned = uploadedFiles.images.find(img => !imageAssignments[img.url]);
                                                if (unassigned) handleImageAssign(unassigned.url, section);
                                            }}
                                            style={{
                                                padding: '6px 12px', borderRadius: 6, fontSize: 12, fontWeight: 500, cursor: 'pointer',
                                                textTransform: 'capitalize',
                                                background: count > 0 ? 'rgba(52,211,153,0.12)' : 'rgba(255,255,255,0.04)',
                                                border: count > 0 ? '1px solid rgba(52,211,153,0.3)' : '1px solid rgba(255,255,255,0.08)',
                                                color: count > 0 ? '#34d399' : '#9ca3af',
                                            }}
                                        >
                                            {section} {count > 0 && `(${count})`}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Clear + action buttons */}
                        <div style={{ display: 'flex', gap: 10 }}>
                            {Object.keys(imageAssignments).length > 0 && (
                                <button onClick={() => setImageAssignments({})} style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#9ca3af', fontSize: 13, cursor: 'pointer' }}>
                                    Clear All
                                </button>
                            )}
                            <button onClick={handleSkipImageAssignment} style={{ flex: 1, padding: '10px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#9ca3af', fontSize: 13, cursor: 'pointer' }}>
                                Skip — Use Stock Photos
                            </button>
                            <button onClick={handleConfirmImageAssignment} style={{ flex: 1, padding: '10px', borderRadius: 8, border: 'none', background: 'linear-gradient(135deg, #6366f1, #818cf8)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                                Generate with My Images
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ─── Resize Handle ─── */}
            {!isMobile && <div className="gn-resize-handle" onMouseDown={startResize} />}

            {/* ─── RIGHT: Preview / Marketplace ─── */}
            <main className={`gn-main ${isMobile && mobileTab !== 'preview' ? 'gn-hidden' : ''}`}>
                {/* Toolbar */}
                {html && (
                    <div className="gn-toolbar">
                        <div className="gn-toolbar-left">
                            <div className="gn-view-toggle">
                                <button className={`gn-vt-btn ${viewMode === 'preview' ? 'active' : ''}`} onClick={() => setViewMode('preview')}>
                                    <Eye size={15} /> Preview
                                </button>
                                <button className={`gn-vt-btn ${viewMode === 'code' ? 'active' : ''}`} onClick={() => setViewMode('code')}>
                                    <Code size={15} /> Code
                                </button>
                            </div>
                            {viewMode === 'preview' && (
                                <div className="gn-device-toggle">
                                    <button className={`gn-dt-btn ${previewDevice === 'desktop' ? 'active' : ''}`} onClick={() => setPreviewDevice('desktop')} title="Desktop view">
                                        <Monitor size={15} />
                                    </button>
                                    <button className={`gn-dt-btn ${previewDevice === 'mobile' ? 'active' : ''}`} onClick={() => setPreviewDevice('mobile')} title="Mobile view">
                                        <Smartphone size={15} />
                                    </button>
                                </div>
                            )}
                        </div>
                        {/* Multi-page tabs */}
                        {isMultipage && Object.keys(pages).length > 0 && (
                            <div className="gn-page-tabs">
                                {Object.keys(pages).sort((a, b) => a === 'index' ? -1 : b === 'index' ? 1 : a.localeCompare(b)).map(slug => (
                                    <button
                                        key={slug}
                                        className={`gn-page-tab ${currentPage === slug ? 'active' : ''}`}
                                        onClick={() => handlePageSwitch(slug)}
                                        title={slug === 'index' ? 'Home' : slug.replace(/-/g, ' ')}
                                    >
                                        <FileText size={13} />
                                        <span>{slug === 'index' ? 'Home' : slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
                                    </button>
                                ))}
                            </div>
                        )}

                        <div className="gn-toolbar-right">
                            <button className={`gn-tb-btn ${showSectionEditor ? 'active' : ''}`} onClick={() => setShowSectionEditor(!showSectionEditor)} title="Sections">
                                <Layers size={15} /> Sections
                            </button>
                            <button className={`gn-tb-btn ${showSiteSettings ? 'active' : ''}`} onClick={() => setShowSiteSettings(!showSiteSettings)} title="Site Settings (SEO, WhatsApp, Contact)">
                                <Settings size={15} />
                            </button>
                            <button className={`gn-tb-btn ${editMode ? 'active' : ''}`} onClick={() => { setEditMode(!editMode); if (!editMode) setCmsMode(false); if (editMode) handleCancelEdit(); }} title="Click to Edit">
                                <MousePointer2 size={15} />
                            </button>
                            <button className={`gn-tb-btn ${cmsMode ? 'active' : ''}`} onClick={() => {
                                // When exiting CMS mode, tell iframe to finalize any pending edit
                                if (cmsMode) {
                                    const iframe = document.querySelector('.preview-iframe');
                                    if (iframe?.contentWindow) {
                                        iframe.contentWindow.postMessage({ type: 'cms-finish-edit' }, window.location.origin);
                                    }
                                    // Small delay to let the cms-edit message arrive before re-render
                                    setTimeout(() => setCmsMode(false), 50);
                                } else {
                                    setCmsMode(true);
                                    setEditMode(false);
                                    handleCancelEdit();
                                }
                            }} title="Edit Content (CMS)">
                                <Type size={15} />
                            </button>
                            <button className={`gn-tb-btn ${showGallery ? 'active' : ''}`} onClick={() => setShowGallery(!showGallery)} title="My Images">
                                <ImageIcon size={15} />
                            </button>
                            <span className="gn-tb-divider" />
                            {/* Undo / Redo */}
                            <button className="gn-tb-btn" onClick={handleUndo} disabled={!canUndo} title="Undo (Ctrl+Z)">
                                <Undo2 size={15} />
                            </button>
                            <button className="gn-tb-btn" onClick={handleRedo} disabled={!canRedo} title="Redo (Ctrl+Shift+Z)">
                                <Redo2 size={15} />
                            </button>
                            <span className="gn-tb-divider" />
                            {/* Actions */}
                            <button className="gn-tb-btn" onClick={handleSaveProject} title="Save">
                                <Save size={15} /> {saveStatus === 'saved' ? 'Saved!' : 'Save'}
                            </button>
                            <button className="gn-tb-btn" onClick={handleExport} title="Download HTML"><Download size={15} /></button>
                            <button className="gn-tb-btn danger" onClick={handleReset} title="Start Over">
                                <RotateCcw size={15} />
                            </button>
                            <button className="gn-tb-btn primary" onClick={() => setShowDeployModal(true)}><Rocket size={15} /> Deploy</button>
                        </div>
                    </div>
                )}

                {/* Error banner (inline fallback) */}
                {error && !errorBanner && (
                    <div className="se-error" style={{ margin: '0 16px' }}>
                        <span>{error}</span>
                        <button onClick={() => setError(null)}><X size={12} /></button>
                    </div>
                )}

                {/* Content */}
                <div className="gn-content">
                    {!hasContent ? (
                        /* ═══ MARKETPLACE ═══ */
                        <div className="gn-marketplace">
                            <div className="gn-market-hero">
                                <h1>Choose a Starting Point</h1>
                                <p>Pick a template to get started, or describe your website in the chat</p>
                                <div className="gn-search-bar">
                                    <Search size={18} className="gn-search-icon" />
                                    <input
                                        type="text"
                                        className="gn-search-input"
                                        placeholder="Search templates..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="gn-categories">
                                {categories.map(cat => (
                                    <button key={cat} className={`gn-cat-chip ${selectedCategory === cat ? 'active' : ''}`} onClick={() => setSelectedCategory(cat)}>
                                        {cat}
                                    </button>
                                ))}
                            </div>

                            <div className="gn-card-grid">
                                {filteredItems.map((item, i) => {
                                    const preview = templatePreviews[item.id];
                                    const hasThumbnail = preview && preview.html;
                                    const gradientBg = Array.isArray(item.colors) && item.colors.length >= 3
                                        ? `linear-gradient(135deg, ${item.colors[0]} 0%, ${item.colors[1]} 50%, ${item.colors[2]} 100%)`
                                        : 'linear-gradient(135deg, #6366f1, #8b5cf6)';
                                    return (
                                        <button key={item.id || i} className="gn-card" onClick={() => handleCardClick(item)}>
                                            <div className="gn-card-preview" style={{ background: hasThumbnail ? '#111' : gradientBg }}>
                                                {hasThumbnail ? (
                                                    <iframe
                                                        title={item.name}
                                                        srcDoc={`<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;overflow:hidden;pointer-events:none}${preview.css || ''}</style></head><body>${preview.html || ''}</body></html>`}
                                                        className="gn-card-iframe"
                                                        sandbox="allow-scripts allow-same-origin"
                                                        loading="lazy"
                                                        tabIndex={-1}
                                                    />
                                                ) : (
                                                    <div className="gn-card-colors">
                                                        {Array.isArray(item.colors) && item.colors.map((c, ci) => (
                                                            <div key={ci} style={{ background: c, flex: 1, height: '100%' }} />
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="gn-card-body">
                                                <span className="gn-card-name">{item.name}</span>
                                                <span className="gn-card-category">{item.category}</span>
                                            </div>
                                        </button>
                                    );
                                })}
                                {filteredItems.length === 0 && (
                                    <div className="gn-no-results"><p>No results found</p></div>
                                )}
                            </div>
                        </div>
                    ) : isLoading && !html ? (
                        activeJobId ? (
                            <div className="gen-loading">
                                <div className="gen-spinner" />
                                <p>{loadingMessage}</p>
                                <div className="gn-job-progress">
                                    <div className="gn-job-progress-bar">
                                        <div className="gn-job-progress-fill" style={{ width: `${jobProgress}%` }} />
                                    </div>
                                    <span className="gn-job-progress-text">{Math.round(jobProgress)}%</span>
                                </div>
                                <button className="gn-stop-btn" onClick={handleStopGeneration}>
                                    <Square size={14} fill="currentColor" /> Stop Generation
                                </button>
                            </div>
                        ) : (
                            <div className="gen-loading">
                                <GenerationProgress currentStage={generationProgress.stage} message={loadingMessage} />
                                <button className="gn-stop-btn" onClick={handleStopGeneration}>
                                    <Square size={14} fill="currentColor" /> Stop Generation
                                </button>
                            </div>
                        )
                    ) : (
                        <div className={`gn-preview-wrap ${previewDevice === 'mobile' ? 'mobile-view' : ''}`}>
                            {viewMode === 'preview' ? (
                                <div className={`gn-device-frame ${previewDevice}`}>
                                    <Preview html={html} css={css} js={js} siteMeta={siteMeta} editMode={editMode} cmsMode={cmsMode} onElementSelect={handleElementSelect} selectedElement={selectedElement} />
                                </div>
                            ) : (
                                <CodeEditor html={html} css={css} js={js} onHtmlChange={setHtml} onCssChange={setCss} onJsChange={setJs} />
                            )}
                        </div>
                    )}
                </div>

                {/* Edit mode tip */}
                {editMode && !selectedElement && html && (
                    <div className="gen-edit-tip"><MousePointer2 size={16} /> Click any element in the preview to edit it</div>
                )}

                {/* CMS mode tip */}
                {cmsMode && html && (
                    <div className="gen-edit-tip"><Type size={16} /> Click any text or image to edit it directly</div>
                )}
            </main>

            {/* ─── Mobile Tools Panel ─── */}
            {isMobile && mobileTab === 'tools' && (
                <div className="gn-mobile-tools">
                    <div className="gn-mobile-tools-header">
                        <h3>Tools</h3>
                    </div>
                    <div className="gn-mobile-tools-content">
                        <button className="gn-mobile-tool-btn" onClick={() => { setShowSectionEditor(true); setMobileTab('preview'); }}>
                            <Layers size={18} /> Sections
                        </button>
                        <button className="gn-mobile-tool-btn" onClick={handleSaveProject}>
                            <Save size={18} /> Save Project
                        </button>
                        <button className="gn-mobile-tool-btn" onClick={handleExport}>
                            <Download size={18} /> Download
                        </button>
                        <button className="gn-mobile-tool-btn" onClick={() => setShowDeployModal(true)}>
                            <Rocket size={18} /> Deploy
                        </button>
                        <button className="gn-mobile-tool-btn" onClick={handleUndo} disabled={!canUndo}>
                            <Undo2 size={18} /> Undo
                        </button>
                        <button className="gn-mobile-tool-btn" onClick={handleRedo} disabled={!canRedo}>
                            <Redo2 size={18} /> Redo
                        </button>
                    </div>
                </div>
            )}

            {/* ─── Mobile Tab Bar ─── */}
            {isMobile && (
                <nav className="gn-mobile-tabs">
                    <button className={`gn-mobile-tab ${mobileTab === 'chat' ? 'active' : ''}`} onClick={() => setMobileTab('chat')}>
                        <MessageSquare size={20} />
                        <span>Chat</span>
                    </button>
                    <button className={`gn-mobile-tab ${mobileTab === 'preview' ? 'active' : ''}`} onClick={() => setMobileTab('preview')} disabled={!html}>
                        <Eye size={20} />
                        <span>Preview</span>
                        {html && <span className="gn-mobile-tab-dot" />}
                    </button>
                    <button className={`gn-mobile-tab ${mobileTab === 'tools' ? 'active' : ''}`} onClick={() => setMobileTab('tools')} disabled={!html}>
                        <Palette size={20} />
                        <span>Tools</span>
                    </button>
                </nav>
            )}

            {/* Element Edit Modal */}
            {selectedElement && (
                <>
                    <div className="gn-backdrop" onClick={handleCancelEdit} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleCancelEdit(); }} role="button" tabIndex={0} />
                    <div className="gn-element-panel">
                        <div className="gn-ep-header">
                            <div className="gn-ep-info">
                                <span className="gn-ep-tag">&lt;{selectedElement.tagName}&gt;</span>
                                <span className="gn-ep-path">{selectedElement.path}</span>
                            </div>
                            <button className="gn-icon-btn" onClick={handleCancelEdit}><X size={18} /></button>
                        </div>
                        {elementAttachment && (
                            <div className="gn-ep-attachment">
                                <img src={elementAttachment.preview} alt="Attached" className="gn-ep-attachment-img" />
                                {elementAttachment.uploading && <span className="gn-ep-attachment-uploading"><span className="gn-spinner" /></span>}
                                <button className="gn-ep-attachment-remove" onClick={handleRemoveAttachment}><X size={14} /></button>
                            </div>
                        )}
                        <div className="gn-ep-body">
                            <button className="gn-ep-attach-btn" onClick={() => elementFileInputRef.current?.click()}
                                disabled={isEditingElement} title="Attach image">
                                <Paperclip size={18} />
                            </button>
                            <input type="text" className="gn-ep-input" placeholder="Describe what you want to change..."
                                value={elementPrompt} onChange={(e) => setElementPrompt(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleElementEdit()} disabled={isEditingElement} autoFocus />
                            <button className="gn-ep-submit" onClick={handleElementEdit}
                                disabled={isEditingElement || !elementPrompt.trim() || elementAttachment?.uploading}>
                                {isEditingElement ? <span className="gn-spinner" /> : <Send size={18} />}
                            </button>
                        </div>
                        <input type="file" ref={elementFileInputRef} accept="image/*" style={{ display: 'none' }} onChange={handleElementAttach} />
                    </div>
                </>
            )}

            <DeployModal isOpen={showDeployModal} onClose={() => setShowDeployModal(false)} sessionId={sessionId} html={html} css={css} js={js} existingSiteId={deployedSiteId} onDeployed={(id) => { setDeployedSiteId(id); if (projectId) handleSaveProject(); }} />

            {/* Inline wizard domain-buy confirmation */}
            {wizardBuyTarget && (
                <div
                    style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}
                    onClick={() => { if (!wizardBuyState.purchasing) { setWizardBuyTarget(null); setWizardBuyState({ purchasing: false, error: null }); } }}
                    onKeyDown={(e) => { if (e.key === 'Escape' && !wizardBuyState.purchasing) { setWizardBuyTarget(null); setWizardBuyState({ purchasing: false, error: null }); } }}
                    role="button"
                    tabIndex={0}
                >
                    <div
                        onClick={e => e.stopPropagation()}
                        onKeyDown={e => e.stopPropagation()}
                        role="presentation"
                        style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 14, padding: '28px 26px', maxWidth: 420, width: 'calc(100% - 32px)', color: '#e5e7eb' }}
                    >
                        <h3 style={{ margin: '0 0 6px', fontSize: 18, fontWeight: 700, color: '#f3f4f6' }}>Secure your domain</h3>
                        <p style={{ margin: '0 0 18px', fontSize: 13, color: '#94a3b8' }}>Register this domain for 1 year. We'll auto-connect it after you deploy.</p>

                        <div style={{ background: '#020617', border: '1px solid #1e293b', borderRadius: 10, padding: 16, marginBottom: 16 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                                <span style={{ fontSize: 12, color: '#94a3b8' }}>Domain</span>
                                <span style={{ fontSize: 16, fontWeight: 700 }}>{wizardBuyTarget.sld}.{wizardBuyTarget.tld}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: 12, color: '#94a3b8' }}>Total (1 year)</span>
                                <span style={{ fontSize: 16, fontWeight: 700, color: '#34d399' }}>${wizardBuyTarget.price.amount}</span>
                            </div>
                        </div>

                        {wizardBuyState.error && (
                            <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5', padding: '10px 12px', borderRadius: 8, fontSize: 13, marginBottom: 12 }}>
                                {wizardBuyState.error}
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: 10 }}>
                            <button
                                onClick={() => { setWizardBuyTarget(null); setWizardBuyState({ purchasing: false, error: null }); }}
                                disabled={wizardBuyState.purchasing}
                                style={{ flex: 1, background: 'transparent', border: '1px solid #334155', color: '#cbd5e1', padding: '12px 16px', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: wizardBuyState.purchasing ? 'wait' : 'pointer' }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleConfirmWizardDomainBuy}
                                disabled={wizardBuyState.purchasing}
                                style={{ flex: 1, background: '#3b82f6', border: 'none', color: '#fff', padding: '12px 16px', borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: wizardBuyState.purchasing ? 'wait' : 'pointer' }}
                            >
                                {wizardBuyState.purchasing ? 'Registering…' : 'Confirm purchase'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Site Settings (SEO, WhatsApp, Contact) */}
            <SeoEditor
                isOpen={showSiteSettings}
                onClose={() => setShowSiteSettings(false)}
                sessionId={sessionId}
                siteMeta={siteMeta}
                currentPage={currentPage}
                onUpdate={(newHtml, newCss, newJs, newPages) => {
                    // Update the visible page state. newHtml is the HTML for
                    // the page the user is CURRENTLY viewing (settings save
                    // now passes pageSlug=currentPage so the backend returns
                    // the right page, not always index).
                    setHtml(newHtml);
                    if (newCss) setCss(newCss);
                    if (newJs) setJs(newJs);

                    // Multipage: also refresh every other page's slot from
                    // the full pages dict the backend now returns. Without
                    // this the OTHER pages stay stale and the floating
                    // widgets only appear on the page the user was viewing
                    // when they hit save — exactly the bug users hit when
                    // they added a social link from the home page and the
                    // FAB only showed up on home, not on contact/about/etc.
                    if (newPages && isMultipage) {
                        setPages(newPages);
                    }
                }}
            />

            {/* Section Editor Panel */}
            <SectionEditor
                isOpen={showSectionEditor}
                onClose={() => setShowSectionEditor(false)}
                sections={sections}
                sessionId={sessionId}
                onUpdate={handleSectionUpdate}
                pageSlug={currentPage}
            />

            <GalleryPicker
                isOpen={showGallery}
                onClose={() => setShowGallery(false)}
                onSelectImage={handleGallerySelect}
            />

            {/* Error Banner (fixed top-center) */}
            {errorBanner && (
                <ErrorBanner
                    error={errorBanner}
                    onRetry={lastRetryPrompt.current ? handleErrorRetry : null}
                    onDismiss={() => { setErrorBanner(null); setError(null); }}
                />
            )}

            {/* Toast Notifications (fixed bottom-right) */}
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />

            {/* Keyboard Shortcuts Modal */}
            {showShortcuts && <KeyboardShortcutsModal onClose={() => setShowShortcuts(false)} />}

            {/* Onboarding Tour */}
            {onboardingStep >= 0 && (
                <OnboardingTour
                    step={onboardingStep}
                    totalSteps={ONBOARDING_STEPS.length}
                    onNext={handleOnboardingNext}
                    onSkip={handleOnboardingSkip}
                />
            )}
        </div>
    );
};

export default WebsiteGenerator;
