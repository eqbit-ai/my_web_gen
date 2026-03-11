/* eslint-disable no-console */
// src/components/WebsiteGenerator.jsx
// Layout: Lovable/Base44 style — Chat sidebar (left) + Preview (right)

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import JSZip from 'jszip';
import {
    Download, Code, Eye, RefreshCw, Rocket, Sparkles,
    MousePointer2, X, Send, ArrowLeft, Undo2, Redo2,
    Save, Search, Palette, RotateCcw,
    Monitor, Smartphone, ExternalLink, Layers,
    AlertTriangle, CheckCircle, Info, Keyboard, Wifi, WifiOff,
    ChevronRight, Type, MessageSquare, FileText
} from 'lucide-react';
import Preview from './Preview';
import CodeEditor from './CodeEditor';
import DeployModal from './DeployModal';
import DesignSystemPanel from './DesignSystemPanel';
import SectionEditor from './SectionEditor';
import {
    generateWebsiteStream, clearSession, editElement,
    saveProject, getTemplates, getTemplateFull, getSections, syncSession,
    submitJob, getJobStatus, restoreSession,
} from '../services/api';
import config from '../config';

const SESSION_STORAGE_KEY = 'meydan_generator_session';
const ONBOARDING_KEY = 'meydan_onboarding_complete';

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
        <div className="shortcuts-overlay" onClick={onClose}>
            <div className="shortcuts-modal" onClick={(e) => e.stopPropagation()}>
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
            <div className="gen-progress-time">Meydan AI is designing your website -- this takes about few minutes</div>
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
            <div className="onboarding-overlay" onClick={onSkip} />
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
(function(){document.querySelectorAll(".hero-stagger").forEach(function(el){var text=el.textContent.trim();if(!text)return;var words=text.split(/\\s+/);el.innerHTML="";words.forEach(function(word,i){var span=document.createElement("span");span.textContent=word;span.style.animationDelay=(0.15+i*0.08)+"s";el.appendChild(span);if(i<words.length-1)el.appendChild(document.createTextNode(" "))})})})();
(function(){var btn=document.querySelector(".back-to-top");if(!btn)return;var ring=btn.querySelector(".progress-ring circle");function up(){var st=window.pageYOffset||document.documentElement.scrollTop;var dh=document.documentElement.scrollHeight-document.documentElement.clientHeight;var pct=dh>0?st/dh:0;if(st>400)btn.classList.add("visible");else btn.classList.remove("visible");if(ring){ring.style.strokeDashoffset=157-(pct*157)}}window.addEventListener("scroll",up,{passive:true});up();btn.addEventListener("click",function(){window.scrollTo({top:0,behavior:"smooth"})})})();
(function(){document.querySelectorAll('a[href^="#"]').forEach(function(link){link.addEventListener("click",function(e){var hash=this.getAttribute("href");if(hash.length<2)return;var target=document.querySelector(hash);if(target){e.preventDefault();target.scrollIntoView({behavior:"smooth",block:"start"});if(history.pushState)history.pushState(null,null,hash)}})})})();
window.showToast=function(msg,type,dur){type=type||"info";dur=dur||3000;var ex=document.querySelector(".toast");if(ex)ex.remove();var t=document.createElement("div");t.className="toast toast-"+type;t.textContent=msg;document.body.appendChild(t);t.offsetHeight;t.classList.add("show");setTimeout(function(){t.classList.remove("show");setTimeout(function(){t.remove()},500)},dur)};
(function(){document.querySelectorAll(".img-shimmer").forEach(function(w){var img=w.querySelector("img");if(!img)return;if(img.complete&&img.naturalWidth>0)w.classList.add("loaded");else{img.addEventListener("load",function(){w.classList.add("loaded")});img.addEventListener("error",function(){w.classList.add("loaded")})}})})();
(function(){var nav=document.querySelector(".navbar-slidedown");if(!nav)return;requestAnimationFrame(function(){nav.style.animationPlayState="running"})})();
});
`;

const WebsiteGenerator = () => {
    const location = useLocation();
    const navigate = useNavigate();
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

    // Design System, Sections, Components
    const [designSystem, setDesignSystem] = useState(null);
    const [sections, setSections] = useState([]);
    const [showDesignSystem, setShowDesignSystem] = useState(false);
    const [showSectionEditor, setShowSectionEditor] = useState(false);
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
            // Restore multipage data from metadata
            const meta = pd.metadata || {};
            if (meta.isMultipage && meta.pages) {
                setIsMultipage(true);
                setPages(meta.pages);
                setCurrentPage(meta.currentPage || 'index');
                // Load the saved current page's html/css
                const savedPage = meta.pages[meta.currentPage || 'index'];
                if (savedPage) {
                    setHtml(savedPage.html || pd.html || '');
                    setCss(savedPage.css || pd.css || '');
                }
            }
            const v = { html: pd.html, css: pd.css, js: pd.js || '', prompt: pd.isTemplate ? 'Loaded from template' : 'Loaded from project', isMultipage: meta.isMultipage || false, pages: meta.pages || {} };
            setVersions([v]); setCurrentVersion(0);
            // Restore chat history from metadata if available, otherwise show default message
            if (!pd.isTemplate && meta.messages && meta.messages.length > 0) {
                setMessages([...meta.messages, { role: 'assistant', text: 'Session restored. What would you like to change?', timestamp: new Date().toLocaleTimeString() }]);
            } else {
                setMessages([{ role: 'assistant', text: pd.isTemplate ? `Template "${pd.name}" loaded. Describe the changes you'd like to make.` : 'Project loaded. What would you like to change?', timestamp: new Date().toLocaleTimeString() }]);
            }

            // Hydrate backend session so chat, sections, design system all work
            restoreSession(pd.html || '', pd.css || '', pd.js || '', pd.id || null)
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
                        restoreSession(d.html, d.css || '', d.js || '', d.projectId || null)
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
            }
        }
        // else: newSession flag with no prompt — fresh empty state (nothing to do)

        // Clear navigation state so browser back/forward doesn't re-trigger
        if (isNewNavigation) {
            navigate('/generator', { replace: true, state: {} });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Persist to sessionStorage
    useEffect(() => {
        if (sessionId || html) {
            sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({
                sessionId, html, css, js, messages, versions, currentVersion, projectId,
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
            const allPages = isMultipage ? { ...pages, [currentPage]: { html, css } } : {};
            const metadata = JSON.stringify({ isMultipage, currentPage, pages: allPages, messages: messages.slice(-50) });
            saveProject({
                project_id: projectId,
                name: projectName || 'Untitled Project',
                html, css, js,
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
    }, [messages, isLoading]);

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
        if (!done && !html && !isLoading && !onboardingShown.current) {
            onboardingShown.current = true;
            const timer = setTimeout(() => setOnboardingStep(0), 1000);
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

    // ── Computed ─────────────────────────────────────────────────────────

    const categories = useMemo(() => {
        const cats = new Set(templates.map(t => t.category).filter(Boolean));
        return ['All', ...Array.from(cats).sort()];
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
                    if (result.designSystem) setDesignSystem(result.designSystem);
                    if (result.sections) setSections(result.sections);

                    // Multi-page support for async jobs
                    const mp = result.isMultipage || false;
                    setIsMultipage(mp);
                    if (mp && result.pages) { setPages(result.pages); setCurrentPage('index'); }

                    const newVersion = { html: newHtml, css: newCss, js: newJs, prompt: '[async job]', isMultipage: mp, pages: mp ? result.pages : {} };
                    setVersions(prev => {
                        const updated = [...prev, newVersion];
                        setCurrentVersion(updated.length - 1);
                        return updated;
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

    // ── Generation ──────────────────────────────────────────────────────

    const streamControllerRef = useRef(null);

    const handleGenerate = async (text, niche, templateId = null) => {
        const promptText = text || prompt.trim();
        if (!promptText || isGeneratingRef.current) return;

        isGeneratingRef.current = true;
        setIsLoading(true);
        setError(null);
        setLoadingMessage(versions.length === 0 ? 'Analyzing your request...' : 'Applying changes...');
        setPrompt('');

        setMessages(prev => [...prev, { role: 'user', text: promptText, timestamp: new Date().toLocaleTimeString() }]);

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
                return;
            }
        }

        // Use SSE streaming for all generation (new + iterations)
        {
            const isNew = !sessionId || versions.length === 0;
            const planMsgId = Date.now();
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
                    setHtml(newHtml); setCss(newCss); setJs(newJs);
                    setSessionId(result.sessionId);
                    setIsNewDesign(result.isNewDesign !== false);
                    if (result.meta) setSiteMeta(result.meta);
                    if (result.designSystem) setDesignSystem(result.designSystem);
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
                        // Normal iteration (chat edit)
                        mp = result.isMultipage || isMultipage;
                        if (mp && result.pages) {
                            // Backend sent updated pages dict — use it
                            resultPages = result.pages;
                            setIsMultipage(true);
                            setPages(result.pages);
                        } else if (isMultipage && currentPage) {
                            // Fallback: update just the current page locally
                            resultPages = { ...pages, [currentPage]: { html: newHtml, css: newCss } };
                            setPages(resultPages);
                        }
                        msgText = 'Changes applied! What else would you like to adjust?';
                    }

                    const newVersion = { html: newHtml, css: newCss, js: newJs, prompt: promptText, isMultipage: mp, pages: resultPages };
                    setVersions(prev => {
                        const updated = [...prev, newVersion];
                        setCurrentVersion(updated.length - 1);
                        return updated;
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

                    autoSave(newHtml, newCss, newJs, projectName || promptText.substring(0, 50));

                    setIsLoading(false); setLoadingMessage('');
                    setGenerationProgress({ stage: 0, total: 5, message: '' });
                    isGeneratingRef.current = false;
                    addToast(result.addedPage ? `${result.addedPage.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} page added!` : (isNew && mp) ? `${Object.keys(result.pages || {}).length}-page website generated!` : isNew ? 'Website generated successfully!' : 'Changes applied!', 'success');
                },
                // onError
                (errorMsg) => {
                    streamControllerRef.current = null;
                    setErrorBanner(errorMsg);
                    lastRetryPrompt.current = promptText;
                    setMessages(prev => [...prev, {
                        role: 'assistant', text: `Error: ${errorMsg}`,
                        timestamp: new Date().toLocaleTimeString(), isError: true,
                    }]);
                    setIsLoading(false); setLoadingMessage('');
                    setGenerationProgress({ stage: 0, total: 5, message: '' });
                    isGeneratingRef.current = false;
                },
                templateId,
                currentPage,
            );
        }
    };

    // ── Rollback to a specific message version ──────────────────────────

    const handleRollback = (versionIndex) => {
        if (versionIndex < 0 || versionIndex >= versions.length) return;
        const v = versions[versionIndex];
        setHtml(v.html); setCss(v.css); setJs(v.js);
        setCurrentVersion(versionIndex);
        // Restore multi-page state from version
        setIsMultipage(v.isMultipage || false);
        setPages(v.pages || {});
        setCurrentPage('index');
        setMessages(prev => [...prev, {
            role: 'system',
            text: `Rolled back to version ${versionIndex + 1}`,
            timestamp: new Date().toLocaleTimeString(),
        }]);
        // Sync backend session
        if (sessionId) syncSession(sessionId, v.html, v.css, v.js, 'index')
            .then(d => { if (d.sections) setSections(d.sections); })
            .catch(() => { });
    };

    // ── Undo / Redo ─────────────────────────────────────────────────────

    const canUndo = currentVersion > 0;
    const canRedo = currentVersion < versions.length - 1;

    const handleUndo = useCallback(() => {
        if (currentVersion <= 0) return;
        const prev = currentVersion - 1;
        const v = versions[prev];
        setHtml(v.html); setCss(v.css); setJs(v.js);
        setCurrentVersion(prev);
        // Sync backend session so sections list matches
        if (sessionId) syncSession(sessionId, v.html, v.css, v.js, currentPage)
            .then(d => { if (d.sections) setSections(d.sections); })
            .catch(() => { });
    }, [currentVersion, versions, sessionId, currentPage]);

    const handleRedo = useCallback(() => {
        if (currentVersion >= versions.length - 1) return;
        const next = currentVersion + 1;
        const v = versions[next];
        setHtml(v.html); setCss(v.css); setJs(v.js);
        setCurrentVersion(next);
        // Sync backend session so sections list matches
        if (sessionId) syncSession(sessionId, v.html, v.css, v.js, currentPage)
            .then(d => { if (d.sections) setSections(d.sections); })
            .catch(() => { });
    }, [currentVersion, versions, sessionId, currentPage]);

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
            if (e.data?.type !== 'cms-edit') return;
            const { editType } = e.data;
            console.log('[CMS] Received edit:', editType);
            const st = cmsStateRef.current;

            // Extract updated HTML directly from the iframe DOM (no fragile selector matching)
            const iframe = document.querySelector('.preview-iframe');
            const cmsRoot = iframe?.contentDocument?.getElementById('__cms_root__');
            if (!cmsRoot) {
                console.warn('[CMS] Could not find __cms_root__ in iframe');
                return;
            }

            // Clean up any CMS UI artifacts before extracting
            cmsRoot.querySelectorAll('.cms-hover-outline').forEach(el => el.classList.remove('cms-hover-outline'));
            cmsRoot.querySelectorAll('.cms-editing').forEach(el => {
                el.classList.remove('cms-editing');
                el.removeAttribute('contenteditable');
            });

            const newHtml = cmsRoot.innerHTML;
            console.log('[CMS] Extracted HTML length:', newHtml.length);

            if (newHtml === st.html) {
                console.log('[CMS] No change detected');
                return;
            }

            setHtml(newHtml);

            // Update multi-page state
            if (st.isMultipage) {
                setPages(prev => ({ ...prev, [st.currentPage]: { html: newHtml, css: st.css } }));
            }

            // Push to version history for undo support
            const newVersion = { html: newHtml, css: st.css, js: st.js, prompt: `[CMS: ${editType} edit]`, isMultipage: st.isMultipage, pages: st.isMultipage ? { ...st.pages, [st.currentPage]: { html: newHtml, css: st.css } } : {} };
            const newVersions = [...st.versions.slice(0, st.currentVersion + 1), newVersion];
            setVersions(newVersions);
            setCurrentVersion(newVersions.length - 1);

            // Sync to backend Redis session so AI edits work on updated HTML
            if (st.sessionId) syncSession(st.sessionId, newHtml, st.css, st.js, st.currentPage)
                .then(d => { if (d.sections) setSections(d.sections); })
                .catch(() => {});

            // Auto-save to project if project exists
            if (st.projectId) {
                handleSaveProject({ html: newHtml, css: st.css, js: st.js });
            }

            addToast('Content updated', 'success');
        };

        window.addEventListener('message', handleCmsMessage);
        return () => window.removeEventListener('message', handleCmsMessage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [addToast]); // stable deps only — state accessed via ref

    // ── Element Editing ─────────────────────────────────────────────────

    const handleElementSelect = (element) => { setSelectedElement(element); setElementPrompt(''); };

    const handleElementEdit = async () => {
        console.log('[ElementEdit] Called — selectedElement:', !!selectedElement, 'prompt:', elementPrompt?.trim()?.substring(0, 50), 'isEditing:', isEditingRef.current, 'sessionId:', sessionId);
        if (!selectedElement || !elementPrompt.trim() || isEditingRef.current) return;
        isEditingRef.current = true;
        setIsEditingElement(true);
        setError(null);

        try {
            console.log('[ElementEdit] Sending → path:', selectedElement.path, 'outerHTML length:', selectedElement.outerHTML?.length, 'html length:', html?.length, 'currentPage:', currentPage);
            const result = await editElement(sessionId, selectedElement.outerHTML, selectedElement.path, elementPrompt, { html, css }, currentPage);
            console.log('[ElementEdit] Response →', { success: result.success, manualReplace: result.manualReplace, htmlLength: result.website?.html?.length, cssLength: result.website?.css?.length });
            if (result.success && !result.manualReplace) {
                const newHtml = result.website.html;
                const newCss = result.website.css || css; // Preserve existing CSS if backend returns empty
                const newJs = result.website.js || js;
                setHtml(newHtml); setCss(newCss);
                if (result.website.js) setJs(result.website.js);

                // Update multi-page state
                if (isMultipage) {
                    setPages(prev => ({ ...prev, [currentPage]: { html: newHtml, css: newCss } }));
                }

                const newVersion = { html: newHtml, css: newCss, js: newJs, prompt: `[Element: ${selectedElement.path}] ${elementPrompt}`, isMultipage, pages: isMultipage ? { ...pages, [currentPage]: { html: newHtml, css: newCss } } : {} };
                setVersions(prev => { const u = [...prev.slice(0, currentVersion + 1), newVersion]; setCurrentVersion(u.length - 1); return u; });

                // Sync to backend Redis session
                if (sessionId) syncSession(sessionId, newHtml, newCss, newJs, currentPage)
                    .then(d => { if (d.sections) setSections(d.sections); })
                    .catch(() => {});

                setMessages(prev => [...prev,
                { role: 'user', text: `Edit ${selectedElement.tagName}: ${elementPrompt}`, timestamp: new Date().toLocaleTimeString() },
                { role: 'assistant', text: 'Element updated!', timestamp: new Date().toLocaleTimeString(), versionIndex: versions.length },
                ]);
                setSelectedElement(null); setElementPrompt(''); setEditMode(false);
                addToast('Section updated', 'success');
                // Auto-save to project
                if (projectId) handleSaveProject({ html: newHtml, css: newCss, js: newJs });
            } else {
                setError('Failed to edit element');
            }
        } catch (err) {
            console.error('[ElementEdit] Error:', err.message || err);
            setError(err.message || 'Failed to edit element');
        } finally {
            setIsEditingElement(false);
            isEditingRef.current = false;
        }
    };

    const handleCancelEdit = () => { setSelectedElement(null); setElementPrompt(''); setEditMode(false); };

    // ── Save ────────────────────────────────────────────────────────────

    const handleSaveProject = async (overrideData) => {
        const h = overrideData?.html || html;
        const c = overrideData?.css || css;
        const j = overrideData?.js || js;
        const name = overrideData?.name || projectName || messages.find(m => m.role === 'user')?.text?.substring(0, 50) || 'Untitled Project';
        if (!h) return;
        setSaveStatus('saving');
        // For multipage: save all pages (with current page's live html/css) in metadata
        const allPages = isMultipage ? { ...pages, [currentPage]: { html: h, css: c } } : {};
        const metadata = JSON.stringify({
            isMultipage,
            currentPage,
            pages: allPages,
            messages: messages.slice(-50), // persist last 50 chat messages
        });
        try {
            const result = await saveProject({
                project_id: projectId || undefined,
                name,
                html: h, css: c, js: j,
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
    const autoSave = useCallback((newHtml, newCss, newJs, name) => {
        setTimeout(() => {
            handleSaveProject({ html: newHtml, css: newCss, js: newJs, name });
        }, 500);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectId, projectName]);

    const buildFullHTML = (title, forExport = false, overrideHtml = null, overrideCss = null) => {
        const t = title || siteMeta.title || 'Website';
        const d = siteMeta.description || '';
        const pageHtml = overrideHtml !== null ? overrideHtml : html;
        const pageCss = overrideCss !== null ? overrideCss : css;
        // For preview: use absolute URL (works from blob: and about:blank). For export: use CDN.
        const tailwindSrc = forExport ? 'https://cdn.tailwindcss.com' : window.location.origin + '/tailwind.js';
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
            '  <script src="' + tailwindSrc + '"></script>',
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
            '      // Mobile hamburger — universal',
            '      (function(){',
            '        var tSel=[".nav-toggle",".hamburger",".mobile-toggle",".menu-toggle",".navbar-toggle","button[aria-label=\\"Menu\\"]",".mobile-menu-btn",".burger"];',
            '        var mSel=[".nav-links",".nav-menu",".mobile-menu",".navbar-menu",".navbar-links",".menu-items","nav ul",".mobile-nav"];',
            '        var tog=null,men=null;',
            '        for(var i=0;i<tSel.length;i++){tog=document.querySelector(tSel[i]);if(tog)break;}',
            '        for(var j=0;j<mSel.length;j++){men=document.querySelector(mSel[j]);if(men)break;}',
            '        if(tog&&men){',
            '          tog.addEventListener("click",function(e){e.stopPropagation();men.classList.toggle("active");men.classList.toggle("open");tog.classList.toggle("active")});',
            '          men.querySelectorAll("a").forEach(function(a){a.addEventListener("click",function(){men.classList.remove("active");men.classList.remove("open");tog.classList.remove("active")})});',
            '          document.addEventListener("click",function(e){if(!tog.contains(e.target)&&!men.contains(e.target)){men.classList.remove("active");men.classList.remove("open");tog.classList.remove("active")}});',
            '        }',
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

    const handleFullPreview = () => {
        const full = buildFullHTML(siteMeta.title || 'Preview', false);
        const blob = new Blob([full], { type: 'text/html' });
        window.open(URL.createObjectURL(blob), '_blank');
    };

    const handleReset = async () => {
        if (sessionId) { try { await clearSession(sessionId); } catch (e) { /* */ } }
        setHtml(''); setCss(''); setJs(''); setError(null);
        setSessionId(null); setIsNewDesign(true);
        setMessages([]); setVersions([]); setCurrentVersion(-1);
        setEditMode(false); setCmsMode(false); setSelectedElement(null); setElementPrompt('');
        setProjectId(null); setSaveStatus(null);
        setIsMultipage(false); setPages({}); setCurrentPage('index');
        setOnboardingStep(-1); // don't re-show tour
        hasAutoGenerated.current = false;
        sessionStorage.removeItem(SESSION_STORAGE_KEY);
    };

    // DEBUG: Log multipage state on every render
    console.log('[MP State] isMultipage:', isMultipage, 'currentPage:', currentPage, 'pages:', Object.keys(pages), 'html length:', html?.length);

    // ── Multi-page: switch active page ────────────────────────────────
    const pagesRef = useRef(pages);
    pagesRef.current = pages;
    const htmlRef = useRef(html);
    htmlRef.current = html;
    const cssRef = useRef(css);
    cssRef.current = css;
    const currentPageRef = useRef(currentPage);
    currentPageRef.current = currentPage;
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

        console.log('[PageSwitch] Request:', slug, 'current:', curPage, 'available:', Object.keys(curPages), 'pages count:', Object.keys(curPages).length);

        if (!curPages[slug]) {
            console.warn('[PageSwitch] Cannot switch to', slug, '— available pages:', Object.keys(curPages));
            return;
        }
        if (slug === curPage) {
            console.log('[PageSwitch] Already on', slug, '— skipping');
            return;
        }

        // 1. Save current page's live html/css
        const updated = { ...curPages, [curPage]: { html: curHtml, css: curCss } };
        // 2. Read target page
        const target = updated[slug];
        console.log('[PageSwitch]', curPage, '→', slug, 'target html length:', target?.html?.length, 'target css length:', target?.css?.length);

        // 3. Update all state in one batch (outside any functional updater)
        setPages(updated);
        setHtml(target?.html || '');
        setCss(target?.css || curCss);
        setCurrentPage(slug);

        // 4. Sync the NEW page's HTML to the backend session so section edits target the right page
        if (curSessionId && target?.html) {
            syncSession(curSessionId, target.html, target.css || curCss, jsRef.current || '', slug)
                .then(() => {
                    // 5. Refresh sections list for the new page
                    getSections(curSessionId, slug).then(d => setSections(d.sections || [])).catch(() => {});
                })
                .catch(() => {});
        }
    }, []);

    // ── Inter-page navigation from iframe links ─────────────────────────
    useEffect(() => {
        const handlePageNavigate = (e) => {
            if (e.data?.type === 'page-navigate' && e.data.slug && isMultipage) {
                handlePageSwitch(e.data.slug);
            }
        };
        window.addEventListener('message', handlePageNavigate);
        return () => window.removeEventListener('message', handlePageNavigate);
    }, [isMultipage, handlePageSwitch]);

    // ── Keep pages[currentPage] in sync with live html/css after any edit ──
    useEffect(() => {
        if (!isMultipage || !currentPage || !html) return;
        setPages(prev => {
            const cur = prev[currentPage];
            // Only update if html or css actually changed
            if (cur && cur.html === html && cur.css === css) return prev;
            return { ...prev, [currentPage]: { html, css } };
        });
    }, [html, css, isMultipage, currentPage]);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleGenerate(); }
    };

    // ── Section/Component handlers ──────────────────────────────────────

    const handleSectionUpdate = (newHtml, newCss, newJs, actionLabel) => {
        setHtml(newHtml); setCss(newCss); if (newJs !== undefined) setJs(newJs);
        // Refresh sections for the current page
        if (sessionId) getSections(sessionId, currentPage).then(d => setSections(d.sections || [])).catch(() => { });
        // Push version
        const label = actionLabel || 'Section edit';
        const newVersion = { html: newHtml, css: newCss, js: newJs || js, prompt: `[${label}]` };
        const newVersions = [...versions.slice(0, currentVersion + 1), newVersion];
        setVersions(newVersions);
        setCurrentVersion(newVersions.length - 1);
        // Add chat messages
        setMessages(prev => [
            ...prev,
            { role: 'user', text: label, timestamp: new Date().toLocaleTimeString() },
            { role: 'assistant', text: `Done! ${label}.`, timestamp: new Date().toLocaleTimeString(), versionIndex: newVersions.length - 1 },
        ]);
        addToast('Section updated', 'success');
        // Auto-save to project
        if (projectId) handleSaveProject({ html: newHtml, css: newCss, js: newJs || js });
    };

    const handleDesignSystemUpdate = (newDs, newCss) => {
        setDesignSystem(newDs);
        if (newCss) setCss(newCss);
    };

    const handleCardClick = (item) => {
        // Generate using template as reference + description as prompt
        handleGenerate(
            `Create a ${item.name} website. ${item.description || ''}`,
            item.niche || null,
            item.id || null,
        );
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

    return (
        <div className="gn-layout">
            {/* ─── LEFT: Chat Sidebar ─── */}
            <aside ref={sidebarRef} className={`gn-chat-sidebar ${isMobile && mobileTab !== 'chat' ? 'gn-hidden' : ''}`} style={!isMobile ? { width: sidebarWidth, minWidth: sidebarWidth } : undefined}>
                {/* Chat header */}
                <div className="gn-chat-header">
                    <button className="gn-icon-btn" onClick={() => navigate('/dashboard')} title="Dashboard">
                        <ArrowLeft size={18} />
                    </button>
                    <img src="/mfz-logo.webp" alt="MFZ" className="gn-chat-logo" />
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
                    {messages.length === 0 && !isLoading && (
                        <div className="gn-chat-welcome">
                            <Sparkles size={24} />
                            <h3>Welcome to Meydan AI</h3>
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

                    <div ref={chatEndRef} />
                </div>

                {/* Chat input */}
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
                    <div className="gn-chat-input-wrap">
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
            </aside>

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
                                    <button className="gn-dt-btn" onClick={handleFullPreview} title="Open in new window">
                                        <ExternalLink size={15} />
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
                            <button className={`gn-tb-btn ${showDesignSystem ? 'active' : ''}`} onClick={() => setShowDesignSystem(!showDesignSystem)} title="Design System">
                                <Palette size={15} />
                            </button>
                            <button className={`gn-tb-btn ${editMode ? 'active' : ''}`} onClick={() => { setEditMode(!editMode); if (!editMode) setCmsMode(false); if (editMode) handleCancelEdit(); }} title="Click to Edit">
                                <MousePointer2 size={15} />
                            </button>
                            <button className={`gn-tb-btn ${cmsMode ? 'active' : ''}`} onClick={() => {
                                // When exiting CMS mode, tell iframe to finalize any pending edit
                                if (cmsMode) {
                                    const iframe = document.querySelector('.preview-iframe');
                                    if (iframe?.contentWindow) {
                                        iframe.contentWindow.postMessage({ type: 'cms-finish-edit' }, '*');
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
                                                        srcDoc={`<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script src="${window.location.origin}/tailwind.js"></script><style>body{margin:0;overflow:hidden;pointer-events:none}${preview.css || ''}</style></head><body>${preview.html || ''}</body></html>`}
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
                            </div>
                        ) : (
                            <GenerationProgress currentStage={generationProgress.stage} message={loadingMessage} />
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
                        <button className="gn-mobile-tool-btn" onClick={() => { setShowDesignSystem(true); setMobileTab('preview'); }}>
                            <Palette size={18} /> Design System
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
                    <div className="gn-backdrop" onClick={handleCancelEdit} />
                    <div className="gn-element-panel">
                        <div className="gn-ep-header">
                            <div className="gn-ep-info">
                                <span className="gn-ep-tag">&lt;{selectedElement.tagName}&gt;</span>
                                <span className="gn-ep-path">{selectedElement.path}</span>
                            </div>
                            <button className="gn-icon-btn" onClick={handleCancelEdit}><X size={18} /></button>
                        </div>
                        <div className="gn-ep-body">
                            <input type="text" className="gn-ep-input" placeholder="Describe what you want to change..."
                                value={elementPrompt} onChange={(e) => setElementPrompt(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleElementEdit()} disabled={isEditingElement} autoFocus />
                            <button className="gn-ep-submit" onClick={handleElementEdit} disabled={isEditingElement || !elementPrompt.trim()}>
                                {isEditingElement ? <span className="gn-spinner" /> : <Send size={18} />}
                            </button>
                        </div>
                    </div>
                </>
            )}

            <DeployModal isOpen={showDeployModal} onClose={() => setShowDeployModal(false)} html={html} css={css} js={js} />

            {/* Design System Panel */}
            <DesignSystemPanel
                isOpen={showDesignSystem}
                onClose={() => setShowDesignSystem(false)}
                designSystem={designSystem}
                sessionId={sessionId}
                onUpdate={handleDesignSystemUpdate}
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
            {onboardingStep >= 0 && !html && !isLoading && (
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
