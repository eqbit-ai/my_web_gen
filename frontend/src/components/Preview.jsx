/* eslint-disable no-useless-escape */
// src/components/Preview.jsx

import React, { useEffect, useRef, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Built-in Animation CSS (from animations.py — key classes only)
// ---------------------------------------------------------------------------
const BUILTIN_ANIMATION_CSS = `
/* Animation & Effect Library */
html{scroll-behavior:smooth}
/* Parallax */
.parallax-bg{position:relative;background-attachment:scroll;background-position:center;background-repeat:no-repeat;background-size:cover}
.parallax-bg::before{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15) 0%,rgba(0,0,0,.05) 100%);z-index:1;pointer-events:none}
.parallax-bg>*{position:relative;z-index:2}
/* Stagger Reveal */
.stagger-reveal .stagger-child{opacity:0;transform:translateY(32px);transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .7s cubic-bezier(.22,1,.36,1)}
.stagger-reveal .stagger-child.visible{opacity:1;transform:translateY(0)}
/* Scroll Progress Bar */
#scroll-progress{position:fixed;top:0;left:0;width:0%;height:3px;background:linear-gradient(90deg,var(--primary,#6366f1),var(--accent,#a78bfa));z-index:99999;transition:width .05s linear;border-radius:0 2px 2px 0}
/* Counter */
.counter[data-target]{font-variant-numeric:tabular-nums;display:inline-block;min-width:1.5em;text-align:center}
/* Magnetic Button */
.magnetic-btn{position:relative;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;transition:transform .35s cubic-bezier(.22,1,.36,1);will-change:transform}
/* Image Reveal */
.image-reveal{overflow:hidden;position:relative}
.image-reveal img{transform:scale(1.15);transition:transform .8s cubic-bezier(.22,1,.36,1)}
.image-reveal::after{content:'';position:absolute;inset:0;background:var(--primary,#6366f1);transform-origin:left;transform:scaleX(1);transition:transform .7s cubic-bezier(.65,0,.35,1)}
.image-reveal.revealed::after{transform:scaleX(0);transform-origin:right}
.image-reveal.revealed img{transform:scale(1)}
/* Image Fade Zoom */
.image-fade-zoom{overflow:hidden;position:relative}
.image-fade-zoom img{opacity:0;transform:scale(1.12);transition:opacity .8s cubic-bezier(.22,1,.36,1),transform 1s cubic-bezier(.22,1,.36,1)}
.image-fade-zoom.revealed img{opacity:1;transform:scale(1)}
/* Image Slide Up */
.image-slide-up{overflow:hidden;position:relative}
.image-slide-up img{opacity:0;transform:translateY(40px);transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .7s cubic-bezier(.22,1,.36,1)}
.image-slide-up.revealed img{opacity:1;transform:translateY(0)}
/* Image Blur In */
.image-blur-in{overflow:hidden;position:relative}
.image-blur-in img{opacity:0;filter:blur(12px);transform:scale(1.05);transition:opacity .7s cubic-bezier(.22,1,.36,1),filter .8s cubic-bezier(.22,1,.36,1),transform .8s cubic-bezier(.22,1,.36,1)}
.image-blur-in.revealed img{opacity:1;filter:blur(0);transform:scale(1)}
/* CSS Fallbacks for image animations */
.image-fade-zoom img,.image-slide-up img,.image-blur-in img{animation:imgFallback .8s ease 1.5s forwards}
.image-fade-zoom.revealed img,.image-slide-up.revealed img,.image-blur-in.revealed img{animation:none}
.stagger-reveal .stagger-child{animation:imgFallback .6s ease 1.5s forwards}
.stagger-reveal .stagger-child.visible{animation:none}
@keyframes imgFallback{to{opacity:1;transform:none;filter:none}}
/* Card Lift */
.card-lift{transition:transform .4s cubic-bezier(.22,1,.36,1),box-shadow .4s cubic-bezier(.22,1,.36,1);will-change:transform,box-shadow}
.card-lift:hover{transform:translateY(-8px);box-shadow:0 20px 40px -12px rgba(0,0,0,.15),0 8px 16px -8px rgba(0,0,0,.1)}
/* Nav Link Slide */
.nav-link-slide{position:relative;text-decoration:none}
.nav-link-slide::after{content:'';position:absolute;bottom:-2px;left:0;width:100%;height:2px;background:currentColor;transform:scaleX(0);transform-origin:right;transition:transform .4s cubic-bezier(.65,0,.35,1)}
.nav-link-slide:hover::after{transform:scaleX(1);transform-origin:left}
/* Button Gradient Shift */
.btn-gradient-shift{background-size:200% 200%;background-image:linear-gradient(135deg,var(--primary,#6366f1) 0%,var(--accent,#a78bfa) 50%,var(--primary,#6366f1) 100%);background-position:0% 50%;transition:background-position .5s cubic-bezier(.22,1,.36,1),transform .3s cubic-bezier(.22,1,.36,1),box-shadow .3s ease;border:none;color:#fff;cursor:pointer}
.btn-gradient-shift:hover{background-position:100% 50%;transform:translateY(-2px);box-shadow:0 8px 24px -4px rgba(99,102,241,.4)}
/* Hero Stagger */
.hero-stagger span{display:inline-block;opacity:0;transform:translateY(40px) rotateX(-15deg);animation:heroWordIn .7s cubic-bezier(.22,1,.36,1) forwards}
@keyframes heroWordIn{to{opacity:1;transform:translateY(0) rotateX(0deg)}}
/* Navbar Slidedown */
.navbar-slidedown{transform:translateY(-100%);animation:navSlideIn .6s cubic-bezier(.22,1,.36,1) .1s forwards}
@keyframes navSlideIn{to{transform:translateY(0)}}
/* Image Shimmer */
.img-shimmer{position:relative;overflow:hidden;background:#e2e8f0}
.img-shimmer::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,.5) 50%,transparent 100%);animation:shimmer 1.8s ease-in-out infinite}
.img-shimmer.loaded::after{display:none}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
/* Gradient Mesh */
.gradient-mesh{position:relative;overflow:hidden}
.gradient-mesh::before{content:'';position:absolute;inset:-50%;background:radial-gradient(ellipse at 20% 50%,rgba(99,102,241,.3) 0%,transparent 50%),radial-gradient(ellipse at 80% 20%,rgba(168,85,247,.25) 0%,transparent 50%),radial-gradient(ellipse at 50% 80%,rgba(59,130,246,.2) 0%,transparent 50%);animation:meshShift 12s ease-in-out infinite alternate;z-index:-1;pointer-events:none}
.gradient-mesh>*{position:relative;z-index:1}
@keyframes meshShift{0%{transform:translate(0,0) rotate(0deg) scale(1)}33%{transform:translate(5%,-3%) rotate(2deg) scale(1.05)}66%{transform:translate(-3%,5%) rotate(-1deg) scale(.98)}100%{transform:translate(2%,-2%) rotate(1deg) scale(1.02)}}
/* Floating Shapes */
.floating-shapes{position:relative;overflow:hidden}
.floating-shapes .shape{position:absolute;border-radius:50%;opacity:.12;filter:blur(60px);pointer-events:none;z-index:0;will-change:transform}
.floating-shapes .shape:nth-child(1){width:400px;height:400px;background:var(--primary,#6366f1);top:-10%;left:-5%;animation:floatBlob1 18s ease-in-out infinite}
.floating-shapes .shape:nth-child(2){width:300px;height:300px;background:var(--accent,#a78bfa);bottom:-5%;right:-5%;animation:floatBlob2 22s ease-in-out infinite}
.floating-shapes .shape:nth-child(3){width:250px;height:250px;background:var(--secondary,#3b82f6);top:40%;left:60%;animation:floatBlob3 15s ease-in-out infinite}
@keyframes floatBlob1{0%,100%{transform:translate(0,0) scale(1)}25%{transform:translate(40px,-30px) scale(1.08)}50%{transform:translate(-20px,40px) scale(.95)}75%{transform:translate(30px,20px) scale(1.04)}}
@keyframes floatBlob2{0%,100%{transform:translate(0,0) scale(1)}25%{transform:translate(-35px,25px) scale(1.06)}50%{transform:translate(25px,-35px) scale(.97)}75%{transform:translate(-15px,-20px) scale(1.03)}}
@keyframes floatBlob3{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(30px,-40px) scale(1.1)}66%{transform:translate(-25px,30px) scale(.92)}}
/* Grain Overlay */
.grain-overlay{position:relative}
.grain-overlay::after{content:'';position:absolute;inset:0;opacity:.035;pointer-events:none;z-index:10;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");background-repeat:repeat;background-size:128px 128px}
/* Aurora Glow */
.aurora-glow{position:relative;overflow:hidden}
.aurora-glow::before{content:'';position:absolute;top:-40%;left:-20%;width:140%;height:140%;background:conic-gradient(from 180deg at 50% 50%,rgba(99,102,241,.25) 0deg,rgba(168,85,247,.2) 60deg,rgba(59,130,246,.18) 120deg,rgba(16,185,129,.15) 180deg,rgba(99,102,241,.2) 240deg,rgba(244,63,94,.15) 300deg,rgba(99,102,241,.25) 360deg);filter:blur(80px);animation:auroraRotate 20s linear infinite;z-index:0;pointer-events:none}
.aurora-glow>*{position:relative;z-index:1}
@keyframes auroraRotate{0%{transform:rotate(0deg) scale(1)}50%{transform:rotate(180deg) scale(1.1)}100%{transform:rotate(360deg) scale(1)}}
/* WhatsApp Float */
.whatsapp-float{position:fixed;bottom:32px;left:32px;width:56px;height:56px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;color:#fff;text-decoration:none;z-index:9990;box-shadow:0 4px 16px -2px rgba(37,211,102,.45);transition:transform .3s cubic-bezier(.22,1,.36,1),box-shadow .3s ease;animation:whatsappPulse 3s ease-in-out infinite}
.whatsapp-float:hover{transform:scale(1.1);box-shadow:0 8px 28px -4px rgba(37,211,102,.5)}
.whatsapp-float svg{width:28px;height:28px}
@keyframes whatsappPulse{0%,100%{box-shadow:0 4px 16px -2px rgba(37,211,102,.45)}50%{box-shadow:0 4px 28px 2px rgba(37,211,102,.3),0 0 0 8px rgba(37,211,102,.08)}}
/* Back-to-Top */
.back-to-top{position:fixed;bottom:88px;right:24px;width:48px;height:48px;border-radius:50%;background:var(--primary,#6366f1);color:#fff;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;opacity:0;visibility:hidden;transform:translateY(16px);transition:opacity .35s cubic-bezier(.22,1,.36,1),visibility .35s,transform .35s cubic-bezier(.22,1,.36,1),background .2s ease;z-index:9990;box-shadow:0 4px 16px -4px rgba(99,102,241,.4)}
.back-to-top.visible{opacity:1;visibility:visible;transform:translateY(0)}
.back-to-top:hover{background:var(--accent,#a78bfa);transform:translateY(-3px)}
.back-to-top svg{width:20px;height:20px}
.back-to-top .progress-ring{position:absolute;inset:-3px;width:54px;height:54px}
.back-to-top .progress-ring circle{fill:none;stroke:var(--primary,#6366f1);stroke-width:2;stroke-dasharray:157;stroke-dashoffset:157;transform:rotate(-90deg);transform-origin:center;transition:stroke-dashoffset .1s linear}
/* Float Input */
.float-input{position:relative;margin-bottom:1.5rem}
.float-input input,.float-input textarea{width:100%;padding:1rem .75rem .5rem;border:1px solid #d1d5db;border-radius:8px;font-size:1rem;background:transparent;outline:none;transition:border-color .25s ease,box-shadow .25s ease}
.float-input input:focus,.float-input textarea:focus{border-color:var(--primary,#6366f1);box-shadow:0 0 0 3px rgba(99,102,241,.12)}
.float-input label{position:absolute;left:.75rem;top:50%;transform:translateY(-50%);font-size:1rem;color:#9ca3af;pointer-events:none;transition:all .25s cubic-bezier(.22,1,.36,1);background:transparent;padding:0 4px}
.float-input input:focus~label,.float-input input:not(:placeholder-shown)~label,.float-input textarea:focus~label,.float-input textarea:not(:placeholder-shown)~label{top:0;transform:translateY(-50%);font-size:.75rem;color:var(--primary,#6366f1);background:#fff}
/* Toast */
.toast{position:fixed;bottom:32px;left:50%;transform:translateX(-50%) translateY(120%);padding:.875rem 1.5rem;border-radius:12px;color:#fff;font-size:.9rem;font-weight:500;z-index:99999;opacity:0;transition:transform .5s cubic-bezier(.22,1,.36,1),opacity .5s cubic-bezier(.22,1,.36,1);box-shadow:0 8px 32px -8px rgba(0,0,0,.25);white-space:nowrap;max-width:90vw;overflow:hidden;text-overflow:ellipsis}
.toast.toast-success{background:#059669}.toast.toast-error{background:#dc2626}.toast.toast-info{background:#6366f1}
.toast.show{transform:translateX(-50%) translateY(0);opacity:1}
/* Fade variants */
.fade-up{opacity:0;transform:translateY(30px);transition:opacity .7s cubic-bezier(.22,1,.36,1),transform .7s cubic-bezier(.22,1,.36,1)}
.fade-up.visible{opacity:1;transform:translateY(0)}
.fade-in{opacity:0;transition:opacity .7s cubic-bezier(.22,1,.36,1)}
.fade-in.visible{opacity:1}
.scale-in{opacity:0;transform:scale(.92);transition:opacity .6s cubic-bezier(.22,1,.36,1),transform .6s cubic-bezier(.22,1,.36,1)}
.scale-in.visible{opacity:1;transform:scale(1)}
/* Logo Reveal */
.logo-reveal{opacity:0;transform:scale(.85) translateY(-10px);animation:logoIn .8s cubic-bezier(.22,1,.36,1) .2s forwards}
@keyframes logoIn{to{opacity:1;transform:scale(1) translateY(0)}}
`;

// ---------------------------------------------------------------------------
// Detail Modal CSS (injected when data-detail-title attributes are present)
// ---------------------------------------------------------------------------
const DETAIL_MODAL_CSS = `
.detail-modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);z-index:9999;padding:2rem;overflow-y:auto}
.detail-modal-overlay.active{display:flex;align-items:center;justify-content:center}
.detail-modal{background:white;border-radius:16px;max-width:720px;width:100%;max-height:85vh;overflow-y:auto;box-shadow:0 25px 60px rgba(0,0,0,0.3);animation:modalSlideUp 0.3s ease;position:relative}
@keyframes modalSlideUp{from{transform:translateY(30px);opacity:0}to{transform:translateY(0);opacity:1}}
.detail-modal-close{position:absolute;top:16px;right:16px;width:36px;height:36px;border-radius:50%;border:none;background:rgba(0,0,0,0.08);color:#333;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:10;transition:background 0.2s}
.detail-modal-close:hover{background:rgba(0,0,0,0.15)}
.detail-modal-image{width:100%;height:280px;object-fit:cover;border-radius:16px 16px 0 0}
.detail-modal-body{padding:2rem}
.detail-modal-title{font-size:1.75rem;font-weight:700;color:#1a1a1a;margin-bottom:0.75rem}
.detail-modal-desc{color:#555;line-height:1.7;margin-bottom:1.5rem;font-size:1.05rem}
.detail-modal-features{list-style:none;padding:0;margin:0 0 1.5rem 0;display:grid;grid-template-columns:1fr 1fr;gap:0.5rem}
.detail-modal-features li{display:flex;align-items:center;gap:0.5rem;color:#444;font-size:0.95rem;padding:0.4rem 0}
.detail-modal-features li::before{content:'\\2713';color:var(--primary,#4f46e5);font-weight:bold;flex-shrink:0}
.detail-modal-cta{display:inline-flex;align-items:center;gap:0.5rem;padding:0.75rem 1.75rem;background:var(--primary,#4f46e5);color:white;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;transition:transform 0.2s,box-shadow 0.2s;text-decoration:none}
.detail-modal-cta:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(79,70,229,0.4);color:white}
@media(max-width:640px){.detail-modal-overlay{padding:1rem}.detail-modal-image{height:200px}.detail-modal-body{padding:1.25rem}.detail-modal-features{grid-template-columns:1fr}}
`;

// ---------------------------------------------------------------------------
// Built-in Animation JS (from animations.py — all interactive behaviors)
// ---------------------------------------------------------------------------
const BUILTIN_ANIMATION_JS = `
(function(){
/* Scroll Progress Bar */
(function(){var bar=document.getElementById("scroll-progress");if(!bar)return;function up(){var st=window.pageYOffset||document.documentElement.scrollTop;var dh=document.documentElement.scrollHeight-document.documentElement.clientHeight;bar.style.width=(dh>0?(st/dh)*100:0)+"%"}window.addEventListener("scroll",up,{passive:true});up()})();
/* Number Counter */
(function(){var counters=document.querySelectorAll(".counter[data-target]");if(!counters.length)return;function anim(el){var target=parseInt(el.getAttribute("data-target"),10);if(isNaN(target))return;var suffix=el.getAttribute("data-suffix")||"";var prefix=el.getAttribute("data-prefix")||"";var dur=2000,st=null;function step(ts){if(!st)st=ts;var p=Math.min((ts-st)/dur,1);var eased=1-Math.pow(1-p,3);el.textContent=prefix+Math.floor(eased*target).toLocaleString()+suffix;if(p<1)requestAnimationFrame(step);else el.textContent=prefix+target.toLocaleString()+suffix}requestAnimationFrame(step)}var co=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){anim(e.target);co.unobserve(e.target)}})},{threshold:0.3});counters.forEach(function(c){co.observe(c)})})();
/* Magnetic Button */
(function(){document.querySelectorAll(".magnetic-btn").forEach(function(btn){btn.addEventListener("mousemove",function(e){var r=btn.getBoundingClientRect();var x=e.clientX-r.left-r.width/2;var y=e.clientY-r.top-r.height/2;btn.style.transform="translate("+(x*.25)+"px,"+(y*.25)+"px)"});btn.addEventListener("mouseleave",function(){btn.style.transform="translate(0,0)"})})})();
/* Stagger Reveal */
(function(){var c=document.querySelectorAll(".stagger-reveal");if(!c.length)return;var so=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){entry.target.querySelectorAll(".stagger-child").forEach(function(ch,i){ch.style.transitionDelay=(i*.1)+"s";ch.classList.add("visible")});so.unobserve(entry.target)}})},{threshold:0.15});c.forEach(function(el){so.observe(el)})})();
/* Fade/Scale Observer */
(function(){var els=document.querySelectorAll(".fade-up,.fade-in,.scale-in");if(!els.length)return;var fo=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){e.target.classList.add("visible");fo.unobserve(e.target)}})},{threshold:0.12});els.forEach(function(el){fo.observe(el)})})();
/* Image Reveal / Fade-Zoom / Slide-Up / Blur-In */
(function(){var r=document.querySelectorAll(".image-reveal,.image-fade-zoom,.image-slide-up,.image-blur-in");if(!r.length)return;var ro=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){e.target.classList.add("revealed");ro.unobserve(e.target)}})},{threshold:0.25});r.forEach(function(el){ro.observe(el)})})();
/* Hero Text Stagger */
(function(){document.querySelectorAll(".hero-stagger").forEach(function(el){if(el.hasAttribute("data-splitting"))return;if(el.querySelector("span"))return;var text=el.textContent.trim();if(!text)return;var words=text.split(/\\s+/);el.innerHTML="";words.forEach(function(word,i){var span=document.createElement("span");span.textContent=word;span.style.animationDelay=(0.15+i*0.08)+"s";el.appendChild(span);if(i<words.length-1)el.appendChild(document.createTextNode(" "))})})})();
/* Back-to-Top with Progress Ring */
(function(){var btn=document.querySelector(".back-to-top");if(!btn)return;var ring=btn.querySelector(".progress-ring circle");function up(){var st=window.pageYOffset||document.documentElement.scrollTop;var dh=document.documentElement.scrollHeight-document.documentElement.clientHeight;var pct=dh>0?st/dh:0;if(st>400)btn.classList.add("visible");else btn.classList.remove("visible");if(ring){ring.style.strokeDashoffset=157-(pct*157)}}window.addEventListener("scroll",up,{passive:true});up();btn.addEventListener("click",function(){window.scrollTo({top:0,behavior:"smooth"})})})();
/* Smooth Scroll Anchors */
(function(){document.querySelectorAll('a[href^="#"]').forEach(function(link){link.addEventListener("click",function(e){var hash=this.getAttribute("href");if(hash.length<2)return;var target=document.querySelector(hash);if(target){e.preventDefault();target.scrollIntoView({behavior:"smooth",block:"start"});if(history.pushState)history.pushState(null,null,hash)}})})})();
/* Toast Utility */
window.showToast=function(msg,type,dur){type=type||"info";dur=dur||3000;var ex=document.querySelector(".toast");if(ex)ex.remove();var t=document.createElement("div");t.className="toast toast-"+type;t.textContent=msg;document.body.appendChild(t);t.offsetHeight;t.classList.add("show");setTimeout(function(){t.classList.remove("show");setTimeout(function(){t.remove()},500)},dur)};
/* Image Shimmer Remove */
(function(){document.querySelectorAll(".img-shimmer").forEach(function(w){var img=w.querySelector("img");if(!img)return;if(img.complete&&img.naturalWidth>0)w.classList.add("loaded");else{img.addEventListener("load",function(){w.classList.add("loaded")});img.addEventListener("error",function(){w.classList.add("loaded")})}})})();
/* Navbar Slidedown */
(function(){var nav=document.querySelector(".navbar-slidedown");if(!nav)return;requestAnimationFrame(function(){nav.style.animationPlayState="running"})})();
})();
`;

const Preview = ({ html, css, js, siteMeta = {}, editMode = false, cmsMode = false, onElementSelect, selectedElement }) => {
    const iframeRef = useRef(null);

    // Inject selection mode styles and handlers into iframe
    const getSelectionScript = useCallback(() => {
        if (!editMode) return '';

        return `
        <script>
        (function() {
            let selectedEl = null;
            let hoverEl = null;

            const overlay = document.createElement('div');
            overlay.id = 'element-selector-overlay';
            overlay.style.cssText = 'position: fixed; pointer-events: none; border: 2px dashed #3b82f6; background: rgba(59, 130, 246, 0.1); z-index: 99999; display: none; transition: all 0.15s ease;';
            document.body.appendChild(overlay);

            const selectedOverlay = document.createElement('div');
            selectedOverlay.id = 'element-selected-overlay';
            selectedOverlay.style.cssText = 'position: fixed; pointer-events: none; border: 3px solid #10b981; background: rgba(16, 185, 129, 0.15); z-index: 99998; display: none;';
            document.body.appendChild(selectedOverlay);

            const label = document.createElement('div');
            label.id = 'element-selector-label';
            label.style.cssText = 'position: fixed; background: #3b82f6; color: white; padding: 2px 8px; font-size: 11px; font-family: monospace; z-index: 100000; display: none; border-radius: 3px; pointer-events: none;';
            document.body.appendChild(label);

            function getElementPath(el) {
                if (!el || el === document.body) return 'body';
                const parts = [];
                let node = el;
                while (node && node !== document.body) {
                    let seg = node.tagName.toLowerCase();
                    if (node.id) { seg += '#' + node.id; parts.unshift(seg); break; }
                    if (node.className && typeof node.className === 'string') {
                        const cls = node.className.trim().split(/\\s+/).filter(c => !c.startsWith('aos-')).slice(0, 2).join('.');
                        if (cls) seg += '.' + cls;
                    }
                    // Add nth-child for disambiguation
                    const parent = node.parentElement;
                    if (parent) {
                        const siblings = Array.from(parent.children).filter(c => c.tagName === node.tagName);
                        if (siblings.length > 1) {
                            const idx = siblings.indexOf(node) + 1;
                            seg += ':nth-child(' + idx + ')';
                        }
                    }
                    parts.unshift(seg);
                    // Stop at section boundaries
                    if (node.tagName === 'SECTION' || node.tagName === 'NAV' || node.tagName === 'FOOTER' || node.tagName === 'HEADER') break;
                    node = node.parentElement;
                }
                return parts.join(' > ');
            }

            function positionOverlay(overlayEl, targetEl) {
                const rect = targetEl.getBoundingClientRect();
                overlayEl.style.left = rect.left + 'px';
                overlayEl.style.top = rect.top + 'px';
                overlayEl.style.width = rect.width + 'px';
                overlayEl.style.height = rect.height + 'px';
                overlayEl.style.display = 'block';
            }

            function isValidElement(el) {
                if (!el || el === document.body || el === document.documentElement) return false;
                if (el.id && el.id.startsWith('element-selector')) return false;
                const tag = el.tagName.toLowerCase();
                return ['div', 'section', 'header', 'footer', 'nav', 'main', 'article', 'aside',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'a', 'button', 'img',
                        'ul', 'ol', 'li', 'form', 'input', 'textarea', 'label', 'figure', 'figcaption'].includes(tag);
            }

            document.addEventListener('mousemove', function(e) {
                const el = document.elementFromPoint(e.clientX, e.clientY);
                if (!el || !isValidElement(el)) {
                    overlay.style.display = 'none';
                    label.style.display = 'none';
                    hoverEl = null;
                    return;
                }
                if (el !== hoverEl) {
                    hoverEl = el;
                    positionOverlay(overlay, el);
                    label.textContent = getElementPath(el);
                    label.style.left = e.clientX + 10 + 'px';
                    label.style.top = e.clientY + 10 + 'px';
                    label.style.display = 'block';
                }
            });

            document.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const el = document.elementFromPoint(e.clientX, e.clientY);
                if (!el || !isValidElement(el)) return;
                selectedEl = el;
                positionOverlay(selectedOverlay, el);
                // Gather context: sibling elements around the clicked one
                let contextBefore = '';
                let contextAfter = '';
                const prev = el.previousElementSibling;
                const next = el.nextElementSibling;
                if (prev) contextBefore = prev.outerHTML.substring(0, 300);
                if (next) contextAfter = next.outerHTML.substring(0, 300);

                // Find the parent section for section-level context
                let sectionEl = el.closest('section[data-section-type], nav, footer, header');
                const sectionId = sectionEl ? (sectionEl.getAttribute('data-section-id') || '') : '';
                const sectionType = sectionEl ? (sectionEl.getAttribute('data-section-type') || sectionEl.tagName.toLowerCase()) : '';

                const elementInfo = {
                    tagName: el.tagName.toLowerCase(),
                    id: el.id || null,
                    className: el.className || null,
                    path: getElementPath(el),
                    outerHTML: el.outerHTML,
                    textContent: el.textContent?.substring(0, 100) || '',
                    rect: el.getBoundingClientRect(),
                    contextBefore: contextBefore,
                    contextAfter: contextAfter,
                    sectionId: sectionId,
                    sectionType: sectionType,
                    parentTag: el.parentElement ? el.parentElement.tagName.toLowerCase() : '',
                    parentClass: el.parentElement?.className || '',
                };
                window.parent.postMessage({ type: 'element-selected', element: elementInfo }, '*');
            }, true);

            document.addEventListener('scroll', function() {
                if (selectedEl) positionOverlay(selectedOverlay, selectedEl);
            });
        })();
        <\/script>
        `;
    }, [editMode]);

    // Inject CMS inline-editing mode script into iframe
    const getCmsScript = useCallback(() => {
        if (!cmsMode) return '';

        return `
        <style>
            .cms-hover-outline {
                outline: 2px dashed rgba(59, 130, 246, 0.5) !important;
                outline-offset: 2px;
                cursor: text !important;
                position: relative;
            }
            .cms-editing {
                outline: 2px solid #10b981 !important;
                outline-offset: 2px;
                min-height: 1em;
            }
            .cms-tooltip {
                position: fixed;
                background: #3b82f6;
                color: white;
                padding: 3px 8px;
                font-size: 11px;
                font-family: -apple-system, sans-serif;
                border-radius: 4px;
                pointer-events: none;
                z-index: 100000;
                white-space: nowrap;
                display: none;
            }
            .cms-img-panel {
                position: fixed;
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                z-index: 100000;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                display: flex;
                flex-direction: column;
                gap: 8px;
                min-width: 320px;
                font-family: -apple-system, sans-serif;
            }
            .cms-img-panel label {
                color: #94a3b8;
                font-size: 11px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .cms-img-panel input {
                width: 100%;
                padding: 8px 10px;
                background: #0f172a;
                border: 1px solid #475569;
                border-radius: 6px;
                color: #e2e8f0;
                font-size: 13px;
                outline: none;
                box-sizing: border-box;
            }
            .cms-img-panel input:focus {
                border-color: #3b82f6;
            }
            .cms-img-panel-btns {
                display: flex;
                gap: 8px;
                justify-content: flex-end;
            }
            .cms-img-panel-btns button {
                padding: 6px 14px;
                border-radius: 6px;
                border: none;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
            }
            .cms-img-apply {
                background: #10b981;
                color: white;
            }
            .cms-img-apply:hover {
                background: #059669;
            }
            .cms-img-cancel {
                background: #334155;
                color: #e2e8f0;
            }
            .cms-img-cancel:hover {
                background: #475569;
            }
            .cms-img-outline {
                outline: 2px solid #3b82f6 !important;
                outline-offset: 2px;
            }
        </style>
        <script>
        (function() {
            var TEXT_TAGS = ['H1','H2','H3','H4','H5','H6','P','SPAN','A','BUTTON','LI','LABEL','FIGCAPTION','BLOCKQUOTE','TD','TH','DT','DD'];
            var tooltip = document.createElement('div');
            tooltip.className = 'cms-tooltip';
            document.body.appendChild(tooltip);

            var activeImgPanel = null;
            var activeImg = null;
            var editingEl = null;

            function getUniqueSelector(el) {
                if (el.id) return '#' + CSS.escape(el.id);
                // Build a precise path from el up to body using nth-child
                var path = [];
                var cur = el;
                while (cur && cur !== document.body && cur !== document.documentElement) {
                    var parent = cur.parentElement;
                    if (!parent) break;
                    if (cur.id) {
                        path.unshift('#' + CSS.escape(cur.id));
                        break;
                    }
                    var index = Array.from(parent.children).indexOf(cur) + 1;
                    path.unshift(cur.tagName.toLowerCase() + ':nth-child(' + index + ')');
                    cur = parent;
                }
                return path.join(' > ');
            }

            function isEditableText(el) {
                return el && TEXT_TAGS.indexOf(el.tagName) !== -1;
            }

            function isEditableImage(el) {
                return el && el.tagName === 'IMG';
            }

            function isCmsUi(el) {
                if (!el) return false;
                return el.closest('.cms-img-panel') || el.closest('.cms-tooltip');
            }

            function closeImgPanel() {
                if (activeImgPanel) {
                    activeImgPanel.remove();
                    activeImgPanel = null;
                }
                if (activeImg) {
                    activeImg.classList.remove('cms-img-outline');
                    activeImg = null;
                }
            }

            function showImgPanel(img) {
                closeImgPanel();
                activeImg = img;
                img.classList.add('cms-img-outline');

                var panel = document.createElement('div');
                panel.className = 'cms-img-panel';

                var lbl = document.createElement('label');
                lbl.textContent = 'Image URL';
                panel.appendChild(lbl);

                var input = document.createElement('input');
                input.type = 'text';
                input.value = img.src;
                input.placeholder = 'https://...';
                panel.appendChild(input);

                var btns = document.createElement('div');
                btns.className = 'cms-img-panel-btns';

                var cancelBtn = document.createElement('button');
                cancelBtn.className = 'cms-img-cancel';
                cancelBtn.textContent = 'Cancel';
                cancelBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    closeImgPanel();
                });
                btns.appendChild(cancelBtn);

                var applyBtn = document.createElement('button');
                applyBtn.className = 'cms-img-apply';
                applyBtn.textContent = 'Apply';
                applyBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    var newSrc = input.value.trim();
                    if (newSrc && newSrc !== img.src) {
                        img.src = newSrc;
                        window.parent.postMessage({
                            type: 'cms-edit',
                            editType: 'image',
                            selector: getUniqueSelector(img),
                            newSrc: newSrc
                        }, '*');
                    }
                    closeImgPanel();
                });
                btns.appendChild(applyBtn);
                panel.appendChild(btns);

                document.body.appendChild(panel);
                activeImgPanel = panel;

                // Position near the image
                var rect = img.getBoundingClientRect();
                var panelW = 340;
                var left = rect.left + rect.width / 2 - panelW / 2;
                if (left < 8) left = 8;
                if (left + panelW > window.innerWidth - 8) left = window.innerWidth - panelW - 8;
                var top = rect.bottom + 8;
                if (top + 120 > window.innerHeight) top = rect.top - 128;
                if (top < 8) top = 8;
                panel.style.left = left + 'px';
                panel.style.top = top + 'px';

                input.focus();
                input.select();
            }

            // Hover
            document.addEventListener('mousemove', function(e) {
                if (editingEl || isCmsUi(e.target)) {
                    tooltip.style.display = 'none';
                    return;
                }
                var el = document.elementFromPoint(e.clientX, e.clientY);
                if (!el || isCmsUi(el)) {
                    tooltip.style.display = 'none';
                    return;
                }

                // Remove previous hover outlines
                document.querySelectorAll('.cms-hover-outline').forEach(function(h) {
                    if (h !== editingEl) h.classList.remove('cms-hover-outline');
                });

                if (isEditableText(el) || isEditableImage(el)) {
                    el.classList.add('cms-hover-outline');
                    tooltip.textContent = isEditableImage(el) ? 'Click to change image' : 'Click to edit';
                    tooltip.style.left = (e.clientX + 12) + 'px';
                    tooltip.style.top = (e.clientY + 12) + 'px';
                    tooltip.style.display = 'block';
                } else {
                    tooltip.style.display = 'none';
                }
            });

            // Click
            document.addEventListener('click', function(e) {
                if (isCmsUi(e.target)) return;

                var el = e.target;

                // If clicking outside current editing or img panel, finish
                if (editingEl && el !== editingEl && !editingEl.contains(el)) {
                    finishTextEdit(editingEl);
                }
                if (activeImgPanel && !el.closest('.cms-img-panel') && el !== activeImg) {
                    closeImgPanel();
                }

                if (isEditableImage(el)) {
                    e.preventDefault();
                    e.stopPropagation();
                    showImgPanel(el);
                    return;
                }

                if (isEditableText(el)) {
                    e.preventDefault();
                    e.stopPropagation();
                    startTextEdit(el);
                    return;
                }
            }, true);

            function startTextEdit(el) {
                if (editingEl === el) return;
                if (editingEl) finishTextEdit(editingEl);
                editingEl = el;
                el._cmsOriginal = el.textContent;
                el.contentEditable = 'true';
                el.classList.remove('cms-hover-outline');
                el.classList.add('cms-editing');
                el.focus();
                // Select all text for easy replacement
                var range = document.createRange();
                range.selectNodeContents(el);
                var sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            }

            function finishTextEdit(el) {
                if (!el) return;
                var newContent = el.textContent;
                var oldContent = el._cmsOriginal || '';
                el.contentEditable = 'false';
                el.classList.remove('cms-editing');
                editingEl = null;

                // Only send if content actually changed
                if (newContent !== oldContent) {
                    window.parent.postMessage({
                        type: 'cms-edit',
                        editType: 'text',
                        selector: getUniqueSelector(el),
                        newContent: newContent,
                        oldContent: oldContent
                    }, '*');
                }
            }

            // Enter key finishes text edit (Shift+Enter for newline)
            document.addEventListener('keydown', function(e) {
                if (editingEl && e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    finishTextEdit(editingEl);
                }
                if (editingEl && e.key === 'Escape') {
                    e.preventDefault();
                    editingEl.contentEditable = 'false';
                    editingEl.classList.remove('cms-editing');
                    editingEl = null;
                }
            });

            // Listen for parent telling us to finalize any pending edit (when exiting CMS mode)
            window.addEventListener('message', function(e) {
                if (e.data && e.data.type === 'cms-finish-edit' && editingEl) {
                    finishTextEdit(editingEl);
                }
            });
        })();
        <\/script>
        `;
    }, [cmsMode]);

    useEffect(() => {
        const iframe = iframeRef.current;
        if (!iframe) return;
        const writeContent = () => {
            const doc = iframe.contentDocument || iframe.contentWindow?.document;
            if (!doc) { return; }

            const selectionScript = getSelectionScript();
            const cmsScript = getCmsScript();
            const editModeStyles = editMode ? `
                * { cursor: crosshair !important; }
                *:hover { outline: 1px dashed rgba(59, 130, 246, 0.5) !important; }
            ` : '';

            const siteTitle = siteMeta.title || 'Preview';
            const siteDesc = siteMeta.description || '';
            // Extract SEO meta tags from HTML comments
            const seoMatch = (html || '').match(/<!-- SEO_META\s*([\s\S]*?)\s*END_SEO_META -->/);
            const seoMetaRaw = seoMatch ? seoMatch[1].trim() : `<meta name="description" content="${siteDesc}">\n  <meta property="og:title" content="${siteTitle}">\n  <meta property="og:description" content="${siteDesc}">\n  <meta property="og:type" content="website">`;
            const seoMeta = seoMetaRaw.replace(/<meta[^>]*X-Frame-Options[^>]*\/?>/gi, '');
            // Extract favicon from HTML comments
            const faviconMatch = (html || '').match(/<!-- FAVICON\s*([\s\S]*?)\s*END_FAVICON -->/);
            const favicon = faviconMatch ? faviconMatch[1].trim() : `<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌐</text></svg>">`;
            // Clean comment blocks and placeholder FA kit scripts from HTML body
            const cleanHtmlBody = (html || '')
                .replace(/<!-- SEO_META[\s\S]*?END_SEO_META -->/g, '')
                .replace(/<!-- FAVICON[\s\S]*?END_FAVICON -->/g, '')
                .replace(/<script[^>]*src=["']https?:\/\/kit\.fontawesome\.com\/[^"']*["'][^>]*><\/script>/gi, '')
                .replace(/<meta[^>]*X-Frame-Options[^>]*\/?>/gi, '');

            const fullHTML = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${siteTitle}</title>
  ${seoMeta}
  ${favicon}
  <!-- Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css">
  <!-- Animations -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.css">
  <style>
    ${css || ''}
    ${BUILTIN_ANIMATION_CSS}
    ${editModeStyles}
    ${html && html.includes('data-detail-title') ? DETAIL_MODAL_CSS : ''}
  </style>
  <script>
    // Early navigation interceptor — prevents iframe from navigating to app routes
    document.addEventListener('click', function(e) {
      var link = e.target.closest('a[href]');
      if (!link) return;
      var href = link.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto') || href.startsWith('tel') || href.startsWith('javascript')) return;
      e.preventDefault();
      e.stopPropagation();
      // Map href to page slug
      var slug = 'index';
      if (href === '/' || href === '/index.html' || href === 'index.html' || href === '/index' || href === '/home' || href === '/home.html') {
        slug = 'index';
      } else {
        var m = href.match(/^\\/?([a-z0-9][a-z0-9_-]*?)(?:\\.html)?$/i);
        if (m) slug = m[1];
      }
      window.parent.postMessage({ type: 'page-navigate', slug: slug }, '*');
    }, true);
  <\/script>
</head>
<body>
  <div id="__cms_root__" style="display:contents">${cleanHtmlBody || '<p style="padding: 20px; color: #666; font-family: sans-serif;">Enter a prompt to generate your website...</p>'}</div>
  <!-- Animation library -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js"><\/script>
  <script src="https://cdn.jsdelivr.net/npm/typed.js@2.0.16/dist/typed.umd.js"><\/script>
  <script src="https://cdn.jsdelivr.net/npm/vanilla-tilt@1.8.1/dist/vanilla-tilt.min.js"><\/script>
  <script src="https://cdn.jsdelivr.net/npm/tsparticles-slim@2.12.0/tsparticles.slim.bundle.min.js"><\/script>
  <script src="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.min.js"><\/script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.css">
  <script src="https://cdn.jsdelivr.net/npm/lenis@1.0.42/dist/lenis.min.js"><\/script>
  <script>
    // Built-in animation behaviors (counters, stagger, magnetic, etc.)
    ${BUILTIN_ANIMATION_JS}

    // Init AOS with offset 0 so iframe elements animate immediately
    if (typeof AOS !== 'undefined') {
      AOS.init({ duration: 800, once: true, offset: 0, disable: false });
      setTimeout(function() { AOS.refresh(); }, 300);
      // Force all AOS elements visible after a delay in case observer doesn't fire
      setTimeout(function() {
        document.querySelectorAll('[data-aos]').forEach(function(el) {
          el.classList.add('aos-animate');
        });
      }, 1000);
    }
    // Force visibility for any hidden-by-default animation elements
    setTimeout(function() {
      var s = document.createElement('style');
      s.textContent = '[data-aos]{opacity:1!important;transform:none!important;transition:none!important}' +
        '.stagger-child{opacity:1!important;transform:none!important}' +
        '.fade-in,.slide-up,.slide-in-left,.slide-in-right{opacity:1!important;transform:none!important}';
      document.head.appendChild(s);
    }, 2000);

    // Mobile hamburger menu — universal fallback
    (function() {
      var toggleSelectors = ['.nav-toggle', '.hamburger', '.mobile-toggle', '.menu-toggle', '.navbar-toggle', '[data-toggle="menu"]', 'button[aria-label="Menu"]', 'button[aria-label="menu"]', '.mobile-menu-btn', '.burger'];
      var menuSelectors = ['.nav-links', '.nav-menu', '.mobile-menu', '.navbar-menu', '.navbar-links', '.menu-items', 'nav ul', '.mobile-nav'];
      var navToggle = null, navLinks = null;
      for (var i = 0; i < toggleSelectors.length; i++) {
        navToggle = document.querySelector(toggleSelectors[i]);
        if (navToggle) break;
      }
      for (var j = 0; j < menuSelectors.length; j++) {
        navLinks = document.querySelector(menuSelectors[j]);
        if (navLinks) break;
      }
      if (navToggle && navLinks) {
        navToggle.addEventListener('click', function(e) {
          e.stopPropagation();
          navLinks.classList.toggle('active');
          navLinks.classList.toggle('open');
          navToggle.classList.toggle('active');
        });
        navLinks.querySelectorAll('a').forEach(function(link) {
          link.addEventListener('click', function() {
            navLinks.classList.remove('active');
            navLinks.classList.remove('open');
            navToggle.classList.remove('active');
          });
        });
        document.addEventListener('click', function(e) {
          if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
            navLinks.classList.remove('active');
            navLinks.classList.remove('open');
            navToggle.classList.remove('active');
          }
        });
      }
    })();

    // Universal testimonial slider fallback
    (function() {
      // Find testimonial slides — use display:none/block approach matching the CSS
      var slides = document.querySelectorAll('.testimonial-slide');
      if (slides.length <= 1) return;

      var wrapper = slides[0].parentElement;
      var section = wrapper.closest('section') || wrapper.closest('[data-section-type]');
      if (!section) return;

      var currentIdx = 0;
      var total = slides.length;

      function showSlide(idx) {
        for (var i = 0; i < total; i++) {
          slides[i].classList.toggle('active', i === idx);
        }
        var dots = section.querySelectorAll('.slider-dot, .carousel-dot, [data-slide]');
        for (var d = 0; d < dots.length; d++) {
          dots[d].classList.toggle('active', d === idx);
        }
        currentIdx = idx;
      }

      // Wire dot clicks
      var dots = section.querySelectorAll('.slider-dot, [data-slide]');
      for (var d = 0; d < dots.length; d++) {
        (function(idx) {
          dots[idx].style.cursor = 'pointer';
          dots[idx].addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            showSlide(idx);
          });
        })(d);
      }

      // Wire prev/next
      var prevBtn = section.querySelector('.slider-prev, [data-prev]');
      var nextBtn = section.querySelector('.slider-next, [data-next]');
      if (prevBtn) prevBtn.addEventListener('click', function(e) { e.preventDefault(); showSlide((currentIdx - 1 + total) % total); });
      if (nextBtn) nextBtn.addEventListener('click', function(e) { e.preventDefault(); showSlide((currentIdx + 1) % total); });

      // Auto-rotate every 5s
      var autoTimer = setInterval(function() { showSlide((currentIdx + 1) % total); }, 5000);
      section.addEventListener('mouseenter', function() { clearInterval(autoTimer); });
      section.addEventListener('mouseleave', function() {
        autoTimer = setInterval(function() { showSlide((currentIdx + 1) % total); }, 5000);
      });
    })();

    // Universal image carousel fallback
    (function() {
      var container = document.querySelector('.carousel-container');
      if (!container) return;
      var track = container.querySelector('.carousel-track');
      var slides = container.querySelectorAll('.carousel-slide');
      var dots = container.querySelectorAll('.carousel-dot');
      var prevBtn = container.querySelector('.carousel-prev');
      var nextBtn = container.querySelector('.carousel-next');
      if (!track || slides.length <= 1) return;

      var currentSlide = 0;
      var totalSlides = slides.length;

      function goToSlide(index) {
        currentSlide = index;
        track.style.transform = 'translateX(-' + (index * 100) + '%)';
        for (var d = 0; d < dots.length; d++) {
          dots[d].classList.toggle('active', d === index);
        }
      }

      if (prevBtn) prevBtn.addEventListener('click', function(e) { e.preventDefault(); goToSlide((currentSlide - 1 + totalSlides) % totalSlides); });
      if (nextBtn) nextBtn.addEventListener('click', function(e) { e.preventDefault(); goToSlide((currentSlide + 1) % totalSlides); });

      for (var d = 0; d < dots.length; d++) {
        (function(idx) {
          dots[idx].addEventListener('click', function(e) { e.preventDefault(); goToSlide(idx); });
        })(d);
      }

      var autoTimer = setInterval(function() { goToSlide((currentSlide + 1) % totalSlides); }, 5000);
      container.addEventListener('mouseenter', function() { clearInterval(autoTimer); });
      container.addEventListener('mouseleave', function() {
        autoTimer = setInterval(function() { goToSlide((currentSlide + 1) % totalSlides); }, 5000);
      });
    })();

    // Fallback: force all hidden elements visible after 2s in case AOS/scroll observer don't fire in iframe
    setTimeout(function() {
      document.querySelectorAll('section[data-section-type]').forEach(function(s) {
        s.classList.add('visible');
      });
      // Force AOS elements visible too — AOS may load but not trigger in iframes
      document.querySelectorAll('[data-aos]').forEach(function(el) {
        el.style.opacity = '1';
        el.style.transform = 'none';
        el.style.transition = 'none';
        el.classList.add('aos-animate');
      });
    }, 2000);

    // Intercept inter-page navigation links
    document.addEventListener('click', function(e) {
        var link = e.target.closest('a[href]');
        if (!link) return;
        var href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto') || href.startsWith('tel')) return;
        // Match "/" or "/index.html" as index
        if (href === '/' || href === '/index.html' || href === 'index.html' || href === '/index' || href === '/home' || href === '/home.html' || href === 'home.html') {
            e.preventDefault();
            e.stopPropagation();
            window.parent.postMessage({ type: 'page-navigate', slug: 'index' }, '*');
            return;
        }
        // Match page links: "/about.html", "/about", "about.html", "about"
        var pageMatch = href.match(/^\\/?([a-z0-9][a-z0-9-]*?)(?:\\.html)?$/i);
        if (pageMatch) {
            e.preventDefault();
            e.stopPropagation();
            window.parent.postMessage({ type: 'page-navigate', slug: pageMatch[1] }, '*');
            return;
        }
    });

  <\/script>
  ${selectionScript}
  ${cmsScript}
  ${html && html.includes('data-detail-title') ? `
  <!-- Detail Modal System -->
  <div id="detail-modal-overlay" class="detail-modal-overlay">
    <div class="detail-modal" id="detail-modal-content"></div>
  </div>
  <script>
  (function(){
    var overlay = document.getElementById('detail-modal-overlay');
    var modal = document.getElementById('detail-modal-content');
    console.log('[Modal] Init:', !!overlay, !!modal);
    if(!overlay || !modal){ console.error('[Modal] Overlay or modal element NOT found!'); return; }
    overlay.addEventListener('click', function(e){ if(e.target===overlay){closeM();} });
    document.addEventListener('keydown', function(e){ if(e.key==='Escape'){closeM();} });

    function openM(card){
      console.log('[Modal] openM called, title:', card.getAttribute('data-detail-title'));
      var t = card.getAttribute('data-detail-title')||'';
      var d = card.getAttribute('data-detail-desc')||'';
      var f = (card.getAttribute('data-detail-features')||'').split('|').filter(Boolean);
      var img = card.getAttribute('data-detail-image')||'';
      var cta = card.getAttribute('data-detail-cta')||'Book Appointment';
      var link = card.getAttribute('data-detail-cta-link')||'#contact';
      var h = '<button class="detail-modal-close" id="dm-close">&times;</button>';
      if(img) h += '<img class="detail-modal-image" src="'+img+'" alt="'+t+'" loading="lazy">';
      h += '<div class="detail-modal-body"><h3 class="detail-modal-title">'+t+'</h3>';
      h += '<p class="detail-modal-desc">'+d+'</p>';
      if(f.length){ h+='<ul class="detail-modal-features">'; f.forEach(function(x){h+='<li>'+x.trim()+'</li>';}); h+='</ul>'; }
      h += '<a href="'+link+'" class="detail-modal-cta">'+cta+' &rarr;</a></div>';
      modal.innerHTML = h;
      document.getElementById('dm-close').addEventListener('click', closeM);
      overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      console.log('[Modal] Overlay active:', overlay.classList.contains('active'), 'display:', window.getComputedStyle(overlay).display);
    }
    function closeM(){
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    }
    // Click anywhere on a card with data-detail-title opens the modal
    document.addEventListener('click', function(e){
      var card = e.target.closest('[data-detail-title]');
      if(!card) return;
      console.log('[Modal] Card clicked:', card.getAttribute('data-detail-title'));
      e.preventDefault(); e.stopPropagation(); openM(card);
    });
    // Make all cards look clickable
    var cards = document.querySelectorAll('[data-detail-title]');
    console.log('[Modal] Found', cards.length, 'cards with data-detail-title');
    cards.forEach(function(c){ c.style.cursor='pointer'; });
  })();
  <\\/script>
  ` : ''}
</body>
</html>`;

            doc.open();
            doc.write(fullHTML);
            doc.close();

            // Scroll to top on content change
            try { iframe.contentWindow.scrollTo(0, 0); } catch(e) {}

            // Inject user JS via DOM — wait for CDN libs (Typed.js, Lenis, etc.) to load first
            if (js) {
                try {
                    // Test if JS parses without errors before injecting
                    new Function(js); // eslint-disable-line no-new-func

                    let injected = false;
                    const injectUserJS = () => {
                        if (injected) return;
                        injected = true;
                        try {
                            const script = doc.createElement('script');
                            script.textContent = `(function(){${js}})();`;
                            doc.body.appendChild(script);
                        } catch (e) {
                            console.warn('[Preview] JS injection failed:', e.message);
                        }
                    };

                    // Wait for iframe load event (fires after all CDN scripts loaded)
                    iframe.contentWindow.addEventListener('load', injectUserJS, { once: true });
                    // Fallback: if load already fired or takes too long, inject after 2s
                    setTimeout(injectUserJS, 2000);
                } catch (e) {
                    console.warn('[Preview] JS has syntax error, skipping:', e.message);
                }
            }
        };

        // Write content synchronously — always write on every html/css change
        writeContent();
    }, [html, css, js, siteMeta, editMode, cmsMode, getSelectionScript, getCmsScript]);

    // Listen for messages from iframe
    useEffect(() => {
        const handleMessage = (event) => {
            if (event.data?.type === 'element-selected' && onElementSelect) {
                onElementSelect(event.data.element);
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [onElementSelect]);

    return (
        <div className="preview-container">
            <iframe
                ref={iframeRef}
                title="Website Preview"
                sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"
                className="preview-iframe"
                srcDoc="<!DOCTYPE html><html><body></body></html>"
            />
        </div>
    );
};

export default Preview;
