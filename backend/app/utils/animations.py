"""
Animation CSS & JS utilities for generated websites.

Provides 20+ animation/effect types that get injected into generated sites:
scroll-based, hover effects, loading/entrance, background effects, and micro-interactions.

Usage:
    from app.utils.animations import (
        get_animation_css,
        get_animation_js,
        get_animation_prompt,
        get_animations_for_section,
    )
"""

# ---------------------------------------------------------------------------
# 1. ANIMATION_CSS — all keyframes, utility classes, effects
# ---------------------------------------------------------------------------

ANIMATION_CSS = """
/* ========================================================================
   ANIMATION & EFFECT LIBRARY
   ======================================================================== */

/* ---------- Global: Smooth Scroll ---------- */
html {
  scroll-behavior: smooth;
}

/* ==========================================================================
   SCROLL-BASED ANIMATIONS
   ========================================================================== */

/* ---------- Parallax Background ---------- */
.parallax-bg {
  position: relative;
  background-attachment: scroll;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
}
.parallax-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.05) 100%);
  z-index: 1;
  pointer-events: none;
}
.parallax-bg > * {
  position: relative;
  z-index: 2;
}

/* ---------- Stagger Reveal ---------- */
.stagger-reveal .stagger-child {
  opacity: 0;
  transform: translateY(32px);
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
.stagger-reveal .stagger-child.visible {
  opacity: 1;
  transform: translateY(0);
}

/* ---------- Scroll Progress Bar ---------- */
#scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  width: 0%;
  height: 3px;
  background: linear-gradient(90deg, var(--primary, #6366f1), var(--accent, #a78bfa));
  z-index: 99999;
  transition: width 0.05s linear;
  border-radius: 0 2px 2px 0;
}

/* ---------- Number Counter ---------- */
.counter[data-target] {
  font-variant-numeric: tabular-nums;
  display: inline-block;
  min-width: 1.5em;
  text-align: center;
}

/* ==========================================================================
   HOVER EFFECTS
   ========================================================================== */

/* ---------- Magnetic Button ---------- */
.magnetic-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}
.magnetic-btn:hover {
  /* transform applied via JS for magnetic pull */
}

/* ---------- Image Reveal (clip on hover) ---------- */
.image-reveal {
  overflow: hidden;
  position: relative;
}
.image-reveal img {
  transform: scale(1.15);
  transition: transform 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}
.image-reveal::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--primary, #6366f1);
  transform-origin: left;
  transform: scaleX(1);
  transition: transform 0.7s cubic-bezier(0.65, 0, 0.35, 1);
}
.image-reveal.revealed::after {
  transform: scaleX(0);
  transform-origin: right;
}
.image-reveal.revealed img {
  transform: scale(1);
}

/* ---------- Card Lift ---------- */
.card-lift {
  transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.4s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform, box-shadow;
}
.card-lift:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.15),
              0 8px 16px -8px rgba(0, 0, 0, 0.1);
}

/* ---------- Nav Link Slide Underline ---------- */
.nav-link-slide {
  position: relative;
  text-decoration: none;
}
.nav-link-slide::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background: currentColor;
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.4s cubic-bezier(0.65, 0, 0.35, 1);
}
.nav-link-slide:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}

/* ---------- Button Gradient Shift ---------- */
.btn-gradient-shift {
  background-size: 200% 200%;
  background-image: linear-gradient(
    135deg,
    var(--primary, #6366f1) 0%,
    var(--accent, #a78bfa) 50%,
    var(--primary, #6366f1) 100%
  );
  background-position: 0% 50%;
  transition: background-position 0.5s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.3s ease;
  border: none;
  color: #fff;
  cursor: pointer;
}
.btn-gradient-shift:hover {
  background-position: 100% 50%;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px -4px rgba(99, 102, 241, 0.4);
}

/* ==========================================================================
   LOADING / ENTRANCE ANIMATIONS
   ========================================================================== */

/* ---------- Hero Text Stagger ---------- */
.hero-stagger span {
  display: inline-block;
  opacity: 0;
  transform: translateY(40px) rotateX(-15deg);
  animation: heroWordIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes heroWordIn {
  to {
    opacity: 1;
    transform: translateY(0) rotateX(0deg);
  }
}

/* ---------- Logo Reveal ---------- */
.logo-reveal {
  opacity: 0;
  transform: scale(0.85) translateY(-10px);
  animation: logoIn 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.2s forwards;
}
@keyframes logoIn {
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* ---------- Navbar Slide Down ---------- */
.navbar-slidedown {
  transform: translateY(-100%);
  animation: navSlideIn 0.6s cubic-bezier(0.22, 1, 0.36, 1) 0.1s forwards;
}
@keyframes navSlideIn {
  to {
    transform: translateY(0);
  }
}

/* ---------- Image Shimmer (skeleton loader) ---------- */
.img-shimmer {
  position: relative;
  overflow: hidden;
  background: #e2e8f0;
}
.img-shimmer::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.5) 50%,
    transparent 100%
  );
  animation: shimmer 1.8s ease-in-out infinite;
}
.img-shimmer.loaded::after {
  display: none;
}
@keyframes shimmer {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* ==========================================================================
   BACKGROUND EFFECTS
   ========================================================================== */

/* ---------- Gradient Mesh ---------- */
.gradient-mesh {
  position: relative;
  overflow: hidden;
}
.gradient-mesh::before {
  content: '';
  position: absolute;
  inset: -50%;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(168,85,247,0.25) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(59,130,246,0.2) 0%, transparent 50%);
  animation: meshShift 12s ease-in-out infinite alternate;
  z-index: -1;
  pointer-events: none;
}
.gradient-mesh > * {
  position: relative;
  z-index: 1;
}
@keyframes meshShift {
  0%   { transform: translate(0, 0) rotate(0deg) scale(1); }
  33%  { transform: translate(5%, -3%) rotate(2deg) scale(1.05); }
  66%  { transform: translate(-3%, 5%) rotate(-1deg) scale(0.98); }
  100% { transform: translate(2%, -2%) rotate(1deg) scale(1.02); }
}

/* ---------- Floating Shapes / Blobs ---------- */
.floating-shapes {
  position: relative;
  overflow: hidden;
}
.floating-shapes .shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
  filter: blur(60px);
  pointer-events: none;
  z-index: 0;
  will-change: transform;
}
.floating-shapes .shape:nth-child(1) {
  width: 400px;
  height: 400px;
  background: var(--primary, #6366f1);
  top: -10%;
  left: -5%;
  animation: floatBlob1 18s ease-in-out infinite;
}
.floating-shapes .shape:nth-child(2) {
  width: 300px;
  height: 300px;
  background: var(--accent, #a78bfa);
  bottom: -5%;
  right: -5%;
  animation: floatBlob2 22s ease-in-out infinite;
}
.floating-shapes .shape:nth-child(3) {
  width: 250px;
  height: 250px;
  background: var(--secondary, #3b82f6);
  top: 40%;
  left: 60%;
  animation: floatBlob3 15s ease-in-out infinite;
}
@keyframes floatBlob1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25%      { transform: translate(40px, -30px) scale(1.08); }
  50%      { transform: translate(-20px, 40px) scale(0.95); }
  75%      { transform: translate(30px, 20px) scale(1.04); }
}
@keyframes floatBlob2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25%      { transform: translate(-35px, 25px) scale(1.06); }
  50%      { transform: translate(25px, -35px) scale(0.97); }
  75%      { transform: translate(-15px, -20px) scale(1.03); }
}
@keyframes floatBlob3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%      { transform: translate(30px, -40px) scale(1.1); }
  66%      { transform: translate(-25px, 30px) scale(0.92); }
}

/* ---------- Grain / Noise Overlay ---------- */
.grain-overlay {
  position: relative;
}
.grain-overlay::after {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.035;
  pointer-events: none;
  z-index: 10;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 128px 128px;
}

/* ---------- Aurora Glow ---------- */
.aurora-glow {
  position: relative;
  overflow: hidden;
}
.aurora-glow::before {
  content: '';
  position: absolute;
  top: -40%;
  left: -20%;
  width: 140%;
  height: 140%;
  background: conic-gradient(
    from 180deg at 50% 50%,
    rgba(99,102,241,0.25) 0deg,
    rgba(168,85,247,0.2) 60deg,
    rgba(59,130,246,0.18) 120deg,
    rgba(16,185,129,0.15) 180deg,
    rgba(99,102,241,0.2) 240deg,
    rgba(244,63,94,0.15) 300deg,
    rgba(99,102,241,0.25) 360deg
  );
  filter: blur(80px);
  animation: auroraRotate 20s linear infinite;
  z-index: 0;
  pointer-events: none;
}
.aurora-glow > * {
  position: relative;
  z-index: 1;
}
@keyframes auroraRotate {
  0%   { transform: rotate(0deg) scale(1); }
  50%  { transform: rotate(180deg) scale(1.1); }
  100% { transform: rotate(360deg) scale(1); }
}

/* ==========================================================================
   MICRO-INTERACTIONS
   ========================================================================== */

/* ---------- Back-to-Top Button with Progress Ring ---------- */
.back-to-top {
  position: fixed;
  bottom: 88px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--primary, #6366f1);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  transform: translateY(16px);
  transition: opacity 0.35s cubic-bezier(0.22, 1, 0.36, 1),
              visibility 0.35s,
              transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
              background 0.2s ease;
  z-index: 9990;
  box-shadow: 0 4px 16px -4px rgba(99, 102, 241, 0.4);
}
.back-to-top.visible {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}
.back-to-top:hover {
  background: var(--accent, #a78bfa);
  transform: translateY(-3px);
}
.back-to-top svg {
  width: 20px;
  height: 20px;
}
.back-to-top .progress-ring {
  position: absolute;
  inset: -3px;
  width: 54px;
  height: 54px;
}
.back-to-top .progress-ring circle {
  fill: none;
  stroke: var(--primary, #6366f1);
  stroke-width: 2;
  stroke-dasharray: 157;
  stroke-dashoffset: 157;
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dashoffset 0.1s linear;
}

/* ---------- Float Input (label float on focus) ---------- */
.float-input {
  position: relative;
  margin-bottom: 1.5rem;
}
.float-input input,
.float-input textarea {
  width: 100%;
  padding: 1rem 0.75rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  background: transparent;
  outline: none;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.float-input input:focus,
.float-input textarea:focus {
  border-color: var(--primary, #6366f1);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}
.float-input label {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1rem;
  color: #9ca3af;
  pointer-events: none;
  transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  background: transparent;
  padding: 0 4px;
}
.float-input input:focus ~ label,
.float-input input:not(:placeholder-shown) ~ label,
.float-input textarea:focus ~ label,
.float-input textarea:not(:placeholder-shown) ~ label {
  top: 0;
  transform: translateY(-50%);
  font-size: 0.75rem;
  color: var(--primary, #6366f1);
  background: #fff;
}

/* ---------- Toast Notification ---------- */
.toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%) translateY(120%);
  padding: 0.875rem 1.5rem;
  border-radius: 12px;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 500;
  z-index: 99999;
  opacity: 0;
  transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1),
              opacity 0.5s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 8px 32px -8px rgba(0, 0, 0, 0.25);
  white-space: nowrap;
  max-width: 90vw;
  overflow: hidden;
  text-overflow: ellipsis;
}
.toast.toast-success { background: #059669; }
.toast.toast-error   { background: #dc2626; }
.toast.toast-info    { background: #6366f1; }
.toast.show {
  transform: translateX(-50%) translateY(0);
  opacity: 1;
}

/* ---------- WhatsApp Float Button ---------- */
.whatsapp-float {
  position: fixed;
  bottom: 32px;
  left: 32px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #25D366;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  text-decoration: none;
  z-index: 9990;
  box-shadow: 0 4px 16px -2px rgba(37, 211, 102, 0.45);
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.3s ease;
  animation: whatsappPulse 3s ease-in-out infinite;
}
.whatsapp-float:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 28px -4px rgba(37, 211, 102, 0.5);
}
.whatsapp-float svg {
  width: 28px;
  height: 28px;
}
@keyframes whatsappPulse {
  0%, 100% { box-shadow: 0 4px 16px -2px rgba(37, 211, 102, 0.45); }
  50%      { box-shadow: 0 4px 28px 2px rgba(37, 211, 102, 0.3), 0 0 0 8px rgba(37, 211, 102, 0.08); }
}

/* ==========================================================================
   UTILITY: Fade variants for IntersectionObserver
   ========================================================================== */
.fade-up {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
.fade-up.visible {
  opacity: 1;
  transform: translateY(0);
}
.fade-in {
  opacity: 0;
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
.fade-in.visible {
  opacity: 1;
}
.scale-in {
  opacity: 0;
  transform: scale(0.92);
  transition: opacity 0.6s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}
.scale-in.visible {
  opacity: 1;
  transform: scale(1);
}

/* ---------- Image Fade Zoom (alternative to image-reveal) ---------- */
.image-fade-zoom {
  overflow: hidden;
  position: relative;
}
.image-fade-zoom img {
  opacity: 0;
  transform: scale(1.12);
  transition: opacity 0.8s cubic-bezier(0.22, 1, 0.36, 1),
              transform 1s cubic-bezier(0.22, 1, 0.36, 1);
}
.image-fade-zoom.revealed img {
  opacity: 1;
  transform: scale(1);
}

/* ---------- Image Slide Up (alternative to image-reveal) ---------- */
.image-slide-up {
  overflow: hidden;
  position: relative;
}
.image-slide-up img {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
}
.image-slide-up.revealed img {
  opacity: 1;
  transform: translateY(0);
}

/* ---------- Image Blur In (alternative to image-reveal) ---------- */
.image-blur-in {
  overflow: hidden;
  position: relative;
}
.image-blur-in img {
  opacity: 0;
  filter: blur(12px);
  transform: scale(1.05);
  transition: opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
              filter 0.8s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}
.image-blur-in.revealed img {
  opacity: 1;
  filter: blur(0);
  transform: scale(1);
}

/* ---------- CSS Fallbacks (if JS observers don't fire) ---------- */
.image-fade-zoom img,
.image-slide-up img,
.image-blur-in img {
  animation: imgRevealFallback 0.8s ease forwards;
  animation-delay: 1.5s;
}
.image-fade-zoom.revealed img,
.image-slide-up.revealed img,
.image-blur-in.revealed img {
  animation: none;
}
.image-reveal.revealed ~ .image-reveal:not(.revealed)::after,
.image-reveal:not(.revealed)::after {
  animation: imgOverlayFallback 0.8s ease forwards;
  animation-delay: 1.5s;
}
.stagger-reveal .stagger-child {
  animation: imgRevealFallback 0.6s ease forwards;
  animation-delay: 1.5s;
}
.stagger-reveal .stagger-child.visible {
  animation: none;
}
@keyframes imgRevealFallback {
  to { opacity: 1; transform: none; filter: none; }
}
@keyframes imgOverlayFallback {
  to { transform: scaleX(0); }
}
"""


# ---------------------------------------------------------------------------
# 2. ANIMATION_JS — all interactive animation logic (vanilla JS)
# ---------------------------------------------------------------------------

ANIMATION_JS = """
/* ========================================================================
   ANIMATION & EFFECT LIBRARY — JavaScript
   ======================================================================== */
document.addEventListener('DOMContentLoaded', function() {

  /* ------------------------------------------------------------------
     Mobile Hamburger Menu Toggle — Event Delegation
     ------------------------------------------------------------------ */
  (function() {
    var tSel = '.nav-toggle,.hamburger,.mobile-toggle,.menu-toggle,.navbar-toggle,button[aria-label="Menu"],button[aria-label="Toggle menu"],.mobile-menu-btn,.burger,[class*="-menu-toggle"],[class*="-mobile-toggle"],[class*="nav-hamburger"],[class*="__hamburger"],[class*="__menu-toggle"]';
    var mSel = '.nav-links,.nav-menu,.mobile-menu,.navbar-menu,.navbar-links,.menu-items,.mobile-nav,[class*="-nav-links"],[class*="-menu-items"],[class*="-nav-menu"],[class*="__nav-links"],[class*="__menu-items"]';

    // Capture phase + stopImmediatePropagation — defeats LLM-generated
    // duplicate handlers that would re-toggle the class and cancel ours.
    document.addEventListener('click', function(e) {
      var btn = e.target.closest(tSel);
      if (btn) {
        e.preventDefault();
        e.stopPropagation();
        if (typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();
        var m = document.querySelector(mSel);
        if (m) {
          m.classList.toggle('active');
          m.classList.toggle('open');
          btn.classList.toggle('active');
          var isOpen = m.classList.contains('active');
          btn.setAttribute('aria-expanded', isOpen);
          btn.innerHTML = isOpen
            ? '<i class="fa-solid fa-xmark"></i>'
            : '<i class="fa-solid fa-bars"></i>';
        }
        return;
      }
      // Close on nav link click
      var nl = e.target.closest(mSel + ' a');
      if (nl) {
        var t = document.querySelector(tSel);
        var m2 = document.querySelector(mSel);
        if (t && m2) {
          m2.classList.remove('active', 'open');
          t.classList.remove('active');
          t.setAttribute('aria-expanded', 'false');
          t.innerHTML = '<i class="fa-solid fa-bars"></i>';
        }
        return;
      }
      // Close on outside click
      var t2 = document.querySelector(tSel);
      var m3 = document.querySelector(mSel);
      if (t2 && m3 && m3.classList.contains('active') && !t2.contains(e.target) && !m3.contains(e.target)) {
        m3.classList.remove('active', 'open');
        t2.classList.remove('active');
        t2.setAttribute('aria-expanded', 'false');
        t2.innerHTML = '<i class="fa-solid fa-bars"></i>';
      }
    }, true);
  })();

  /* ------------------------------------------------------------------
     Scroll Progress Bar
     ------------------------------------------------------------------ */
  (function() {
    var bar = document.getElementById('scroll-progress');
    if (!bar) return;
    function updateProgress() {
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      var docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      var pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      bar.style.width = pct + '%';
    }
    window.addEventListener('scroll', updateProgress, { passive: true });
    updateProgress();
  })();

  /* ------------------------------------------------------------------
     Number Counter (IntersectionObserver)
     ------------------------------------------------------------------ */
  (function() {
    var counters = document.querySelectorAll('.counter[data-target]');
    if (!counters.length) return;

    function animateCounter(el) {
      var target = parseInt(el.getAttribute('data-target'), 10);
      if (isNaN(target)) return;
      var suffix = el.getAttribute('data-suffix') || '';
      var prefix = el.getAttribute('data-prefix') || '';
      var duration = 2000;
      var startTime = null;

      function step(ts) {
        if (!startTime) startTime = ts;
        var progress = Math.min((ts - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = Math.floor(eased * target);
        el.textContent = prefix + current.toLocaleString() + suffix;
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          el.textContent = prefix + target.toLocaleString() + suffix;
        }
      }
      requestAnimationFrame(step);
    }

    var counterObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.3 });

    counters.forEach(function(c) { counterObserver.observe(c); });
  })();

  /* ------------------------------------------------------------------
     Magnetic Button Effect
     ------------------------------------------------------------------ */
  (function() {
    var btns = document.querySelectorAll('.magnetic-btn');
    btns.forEach(function(btn) {
      btn.addEventListener('mousemove', function(e) {
        var rect = btn.getBoundingClientRect();
        var x = e.clientX - rect.left - rect.width / 2;
        var y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = 'translate(' + (x * 0.25) + 'px, ' + (y * 0.25) + 'px)';
      });
      btn.addEventListener('mouseleave', function() {
        btn.style.transform = 'translate(0, 0)';
      });
    });
  })();

  /* ------------------------------------------------------------------
     Stagger Reveal (IntersectionObserver)
     ------------------------------------------------------------------ */
  (function() {
    var containers = document.querySelectorAll('.stagger-reveal');
    if (!containers.length) return;

    var staggerObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          var children = entry.target.querySelectorAll('.stagger-child');
          children.forEach(function(child, i) {
            child.style.transitionDelay = (i * 0.1) + 's';
            child.classList.add('visible');
          });
          staggerObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    containers.forEach(function(c) { staggerObserver.observe(c); });
  })();

  /* ------------------------------------------------------------------
     Generic Fade/Scale-in Observer (fade-up, fade-in, scale-in)
     ------------------------------------------------------------------ */
  (function() {
    var els = document.querySelectorAll('.fade-up, .fade-in, .scale-in');
    if (!els.length) return;

    var fadeObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          fadeObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    els.forEach(function(el) { fadeObserver.observe(el); });
  })();

  /* ------------------------------------------------------------------
     Image Reveal / Fade-Zoom / Slide-Up / Blur-In (IntersectionObserver)
     ------------------------------------------------------------------ */
  (function() {
    var reveals = document.querySelectorAll('.image-reveal, .image-fade-zoom, .image-slide-up, .image-blur-in');
    if (!reveals.length) return;

    var revealObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.25 });

    reveals.forEach(function(el) { revealObserver.observe(el); });
  })();

  /* ------------------------------------------------------------------
     Hero Text Stagger — DISABLED.
     The original implementation called el.innerHTML = '' and rebuilt the
     element as a flat list of word spans, which destroyed the hero's HTML
     structure (h1, subtitle, buttons, background) whenever the class was
     applied to a <section> wrapper instead of a single heading. LLMs apply
     it inconsistently and the destructive behaviour wiped the entire hero.
     The deploy pipeline now also strips the class from class="" attributes
     as a belt-and-braces measure.
     ------------------------------------------------------------------ */

  /* ------------------------------------------------------------------
     Back-to-Top with Scroll Progress Ring
     ------------------------------------------------------------------ */
  (function() {
    // Match both .back-to-top (animation library convention) and #back-to-top
    // (what the generator prompt tells the LLM to emit). Either one works.
    var btn = document.querySelector('.back-to-top, #back-to-top');
    if (!btn) return;

    var ring = btn.querySelector('.progress-ring circle');

    // LLM often emits inline opacity:0 / pointer-events:none on #back-to-top,
    // which would keep the button invisible even after we add the .visible
    // class. Clear those inline props so the scroll handler can actually
    // reveal the button.
    btn.style.opacity = '';
    btn.style.pointerEvents = '';

    function update() {
      var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      var docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      var pct = docHeight > 0 ? scrollTop / docHeight : 0;

      if (scrollTop > 400) {
        btn.classList.add('visible');
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
      } else {
        btn.classList.remove('visible');
        btn.style.opacity = '0';
        btn.style.pointerEvents = 'none';
      }

      if (ring) {
        var circumference = 157; // 2 * PI * 25
        ring.style.strokeDashoffset = circumference - (pct * circumference);
      }
    }

    window.addEventListener('scroll', update, { passive: true });
    update();

    btn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  })();

  /* ------------------------------------------------------------------
     Smooth Scroll for Anchor Links
     ------------------------------------------------------------------ */
  (function() {
    document.querySelectorAll('a[href^="#"]').forEach(function(link) {
      link.addEventListener('click', function(e) {
        var hash = this.getAttribute('href');
        if (hash.length < 2) return;
        var target = document.querySelector(hash);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Update URL without jump
          if (history.pushState) {
            history.pushState(null, null, hash);
          }
        }
      });
    });
  })();

  /* ------------------------------------------------------------------
     Toast Notification Utility
     ------------------------------------------------------------------ */
  window.showToast = function(message, type, duration) {
    type = type || 'info';
    duration = duration || 3000;

    // Remove existing toast
    var existing = document.querySelector('.toast');
    if (existing) existing.remove();

    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger reflow then show
    toast.offsetHeight;
    toast.classList.add('show');

    setTimeout(function() {
      toast.classList.remove('show');
      setTimeout(function() { toast.remove(); }, 500);
    }, duration);
  };

  /* ------------------------------------------------------------------
     Image Shimmer — Remove shimmer once image loads
     ------------------------------------------------------------------ */
  (function() {
    var shimmers = document.querySelectorAll('.img-shimmer');
    shimmers.forEach(function(wrapper) {
      var img = wrapper.querySelector('img');
      if (!img) return;
      if (img.complete && img.naturalWidth > 0) {
        wrapper.classList.add('loaded');
      } else {
        img.addEventListener('load', function() {
          wrapper.classList.add('loaded');
        });
        img.addEventListener('error', function() {
          wrapper.classList.add('loaded');
        });
      }
    });
  })();

  /* ------------------------------------------------------------------
     Navbar Slide-down Trigger
     ------------------------------------------------------------------ */
  (function() {
    var nav = document.querySelector('.navbar-slidedown');
    if (!nav) return;
    // Animation is CSS-driven, just ensure it runs after paint
    requestAnimationFrame(function() {
      nav.style.animationPlayState = 'running';
    });
  })();

});
"""


# ---------------------------------------------------------------------------
# 3. ANIMATION_PROMPT_SECTION — injected into the HTML generation prompt
# ---------------------------------------------------------------------------

ANIMATION_PROMPT_SECTION = """
AVAILABLE ANIMATIONS & EFFECTS:
You have access to these CSS classes and effects. Use them to create polished, interactive websites.
The animation CSS and JS are already injected — you only need to apply the correct classes and markup.

SCROLL ANIMATIONS:
- Add `class="parallax-bg"` to sections with background images for parallax effect (includes dark overlay)
- Add `class="stagger-reveal"` to a container and `class="stagger-child"` to its children for staggered fade-in on scroll
- Add `<div id="scroll-progress"></div>` as the first child of <body> for a thin gradient progress bar at top of page
- Add `class="counter" data-target="500"` to a number element for animated count-up. Optional: `data-suffix="+"` or `data-prefix="$"`
- Add `class="fade-up"` to any element for fade-up-on-scroll reveal
- Add `class="scale-in"` to any element for scale-in-on-scroll reveal

HOVER EFFECTS:
- Add `class="magnetic-btn"` to buttons for magnetic cursor-follow effect
- Wrap images in `<div class="image-reveal"><img ...></div>` for solid-color clip-path reveal on scroll
- Wrap images in `<div class="image-fade-zoom"><img ...></div>` for fade-in + zoom-out reveal on scroll
- Wrap images in `<div class="image-slide-up"><img ...></div>` for slide-up reveal on scroll
- Wrap images in `<div class="image-blur-in"><img ...></div>` for blur-to-sharp reveal on scroll
- IMPORTANT: Vary the image animation — do NOT use the same one for every section. Mix image-reveal, image-fade-zoom, image-slide-up, and image-blur-in.
- Add `class="card-lift"` to cards for lift + depth shadow on hover
- Add `class="nav-link-slide"` to nav links for animated underline slide on hover
- Add `class="btn-gradient-shift"` to buttons for animated gradient color shift on hover

LOADING / ENTRANCE:
- Add `class="hero-stagger"` to hero headings — JS auto-splits words and animates them in sequence
- Add `class="logo-reveal"` to the site logo for a scale+fade entrance
- Add `class="navbar-slidedown"` to the navbar for slide-down entrance on load
- Wrap images in `<div class="img-shimmer"><img ...></div>` for skeleton shimmer while loading

BACKGROUND EFFECTS:
- Add `class="gradient-mesh"` to sections for animated gradient mesh background (shifting radial gradients)
- Add `class="floating-shapes"` to a section and add `<div class="shape"></div>` children (2-3) for floating blobs
- Add `class="grain-overlay"` to sections for subtle grain/noise texture overlay
- Add `class="aurora-glow"` to sections for an aurora/glow conic gradient behind content

MICRO-INTERACTIONS:
- Smooth scroll is enabled globally (html { scroll-behavior: smooth })
- Add this back-to-top button before </body>:
  `<button class="back-to-top" aria-label="Back to top"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 15l-6-6-6 6"/></svg><svg class="progress-ring" viewBox="0 0 54 54"><circle cx="27" cy="27" r="25"/></svg></button>`
- Use `<div class="float-input"><input placeholder=" " id="x"><label for="x">Name</label></div>` for floating label inputs
- Call `showToast("Message", "success")` in JS for toast notifications (types: success, error, info)
- Add WhatsApp float: `<a href="https://wa.me/PHONE" class="whatsapp-float" aria-label="Chat on WhatsApp"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.611.611l4.458-1.495A11.96 11.96 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.387 0-4.607-.798-6.384-2.147l-.108-.084-3.26 1.093 1.093-3.26-.084-.108A9.953 9.953 0 012 12C2 6.486 6.486 2 12 2s10 4.486 10 10-4.486 10-10 10z"/></svg></a>`

COMBINATION TIPS:
- Hero sections: use `parallax-bg` + `hero-stagger` + `gradient-mesh` or `aurora-glow`
- Feature cards: use `stagger-reveal` + `stagger-child` + `card-lift`
- Stats/numbers: use `counter` with `data-target` + `stagger-reveal`
- CTAs: use `btn-gradient-shift` or `magnetic-btn` + `gradient-mesh`
- Team: use `stagger-reveal` + `card-lift` + `image-slide-up`
- Testimonials: use `stagger-reveal` + `card-lift` + `image-fade-zoom`
- Gallery/portfolio: use `stagger-reveal` + `image-blur-in` or `image-fade-zoom`
- Navigation: use `navbar-slidedown` + `nav-link-slide` + `logo-reveal`
- Forms: use `float-input` for all inputs
- Always include back-to-top button and scroll-progress bar for polished feel
"""


# ---------------------------------------------------------------------------
# 4. Section-to-animation recommendation map
# ---------------------------------------------------------------------------

_SECTION_ANIMATION_MAP: dict[str, list[str]] = {
    "hero": [
        "parallax-bg",
        "hero-stagger",
        "gradient-mesh",
        "aurora-glow",
        "btn-gradient-shift",
        "floating-shapes",
    ],
    "navigation": [
        "navbar-slidedown",
        "nav-link-slide",
        "logo-reveal",
    ],
    "navbar": [
        "navbar-slidedown",
        "nav-link-slide",
        "logo-reveal",
    ],
    "features": [
        "stagger-reveal",
        "stagger-child",
        "card-lift",
        "fade-up",
    ],
    "services": [
        "stagger-reveal",
        "stagger-child",
        "card-lift",
        "fade-up",
    ],
    "stats": [
        "counter",
        "stagger-reveal",
        "stagger-child",
        "fade-up",
    ],
    "pricing": [
        "stagger-reveal",
        "stagger-child",
        "card-lift",
        "btn-gradient-shift",
    ],
    "testimonials": [
        "stagger-reveal",
        "stagger-child",
        "card-lift",
        "image-fade-zoom",
    ],
    "team": [
        "stagger-reveal",
        "stagger-child",
        "card-lift",
        "image-slide-up",
    ],
    "gallery": [
        "stagger-reveal",
        "stagger-child",
        "image-blur-in",
        "scale-in",
    ],
    "portfolio": [
        "stagger-reveal",
        "stagger-child",
        "image-fade-zoom",
        "scale-in",
    ],
    "cta": [
        "gradient-mesh",
        "btn-gradient-shift",
        "magnetic-btn",
        "aurora-glow",
    ],
    "contact": [
        "float-input",
        "fade-up",
        "gradient-mesh",
    ],
    "footer": [
        "fade-up",
        "nav-link-slide",
    ],
    "about": [
        "stagger-reveal",
        "stagger-child",
        "fade-up",
        "image-slide-up",
    ],
    "faq": [
        "stagger-reveal",
        "stagger-child",
        "fade-up",
    ],
    "blog": [
        "stagger-reveal",
        "stagger-child",
        "card-lift",
        "img-shimmer",
    ],
}


# ---------------------------------------------------------------------------
# 5. Public helper functions
# ---------------------------------------------------------------------------


def get_animation_css() -> str:
    """Return the full animation CSS string."""
    return ANIMATION_CSS


def get_animation_js() -> str:
    """Return the full animation JS string."""
    return ANIMATION_JS


def get_animation_prompt() -> str:
    """Return the prompt section describing available animations."""
    return ANIMATION_PROMPT_SECTION


def get_animation_prompt_compact() -> str:
    """Return a compact animation reference for edit prompts (much shorter than full prompt)."""
    return """ANIMATIONS & EFFECTS (pre-loaded CSS+JS — just add the classes/attributes):

SCROLL REVEAL: .fade-up, .fade-in, .scale-in (auto-animate on scroll via IntersectionObserver)
STAGGER: .stagger-reveal on container + .stagger-child on children (sequential fade-in)
IMAGE REVEAL: .image-reveal, .image-fade-zoom, .image-slide-up, .image-blur-in (wrap around <img>)
HOVER: .card-lift (lift+shadow), .magnetic-btn (cursor follow), .btn-gradient-shift (gradient animate), .nav-link-slide (underline slide)
ENTRANCE: .hero-stagger (word-by-word reveal), .logo-reveal, .navbar-slidedown
BACKGROUND FX: .gradient-mesh (animated mesh), .floating-shapes + .shape children (blobs), .aurora-glow (conic glow), .grain-overlay (noise texture), .parallax-bg (parallax scroll)
COUNTER: .counter data-target="500" data-suffix="+" (animated count-up on scroll)
TYPED TEXT: <span class="typed-text" data-typed='["Phrase 1","Phrase 2"]'></span> (typewriter effect, requires Typed.js CDN)
TILT: data-tilt data-tilt-max="8" data-tilt-glare data-tilt-max-glare="0.15" (3D tilt on hover, requires vanilla-tilt CDN)
TEXT SPLIT: data-splitting on headings (per-char animation, requires Splitting.js CDN)
SCROLL PROGRESS: <div id="scroll-progress"></div> as first body child
BACK TO TOP: <button class="back-to-top"> with progress ring SVG
FLOAT INPUT: .float-input wrapper with input + label for floating labels
TOAST: showToast("message", "success|error|info") in JS
WHATSAPP: (handled automatically — do NOT add a whatsapp float button; the platform injects it post-generation based on user settings)
GLASS: backdrop-filter: blur(10px); background: rgba(255,255,255,0.05)
GRADIENT TEXT: background: linear-gradient(...); -webkit-background-clip: text; -webkit-text-fill-color: transparent

MIX animations for premium feel — e.g. .stagger-reveal + .card-lift on feature cards, .parallax-bg + .hero-stagger on hero."""


def get_animations_for_section(section_type: str) -> str:
    """Return a concise recommendation of animations for a given section type.

    Args:
        section_type: e.g. "hero", "features", "stats", "cta", "contact"

    Returns:
        A human-readable string listing recommended CSS classes for the section.
    """
    key = section_type.lower().strip()
    animations = _SECTION_ANIMATION_MAP.get(key)
    if not animations:
        # Fallback: generic scroll animations
        animations = ["fade-up", "stagger-reveal", "stagger-child"]

    return f"Recommended animations for '{section_type}' section: " + ", ".join(f".{a}" for a in animations)
