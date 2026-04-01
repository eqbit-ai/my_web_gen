"""
Premium CSS post-processor — enforces agency-grade visual quality on every generation.

Runs AFTER the LLM generates HTML/CSS, BEFORE deployment. Fixes the 5 biggest
quality killers: weak heroes, bad colors, cramped spacing, generic fonts, inconsistent cards.

Also injects premium animations that make sites feel alive.
"""

import re
import random
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════
# 1. CURATED COLOR PALETTES (proven combinations from top designs)
# ═══════════════════════════════════════════════════════════════════════

CURATED_PALETTES = [
    # Dark themes
    {"bg": "#0a0a0f", "surface": "#141418", "primary": "#6366f1", "accent": "#f59e0b", "text": "#e5e7eb", "muted": "#9ca3af", "name": "midnight-indigo"},
    {"bg": "#0c0a14", "surface": "#1a1625", "primary": "#7c5cfc", "accent": "#c4b5fd", "text": "#f0eef5", "muted": "#8b85a0", "name": "violet-night"},
    {"bg": "#0a1628", "surface": "#112240", "primary": "#64ffda", "accent": "#f5a623", "text": "#ccd6f6", "muted": "#8892b0", "name": "deep-navy"},
    {"bg": "#09090b", "surface": "#18181b", "primary": "#3ecf8e", "accent": "#1c8656", "text": "#fafafa", "muted": "#a1a1aa", "name": "emerald-dark"},
    {"bg": "#0d0d0d", "surface": "#171717", "primary": "#e11d48", "accent": "#fbbf24", "text": "#f5f5f5", "muted": "#a3a3a3", "name": "crimson-dark"},
    {"bg": "#060606", "surface": "#111111", "primary": "#c9a84c", "accent": "#d4af37", "text": "#f5f0e8", "muted": "#8a8578", "name": "luxury-gold"},
    {"bg": "#0a0a0a", "surface": "#141414", "primary": "#06b6d4", "accent": "#22d3ee", "text": "#f0f9ff", "muted": "#94a3b8", "name": "cyan-tech"},
    {"bg": "#0f0f0f", "surface": "#1a1a1a", "primary": "#ff6b6b", "accent": "#feca57", "text": "#f8f8f8", "muted": "#999999", "name": "coral-dark"},
    # Light themes
    {"bg": "#fafaf9", "surface": "#ffffff", "primary": "#1e40af", "accent": "#f59e0b", "text": "#1e293b", "muted": "#64748b", "name": "clean-blue"},
    {"bg": "#faf8f5", "surface": "#ffffff", "primary": "#7c3aed", "accent": "#06b6d4", "text": "#1c1917", "muted": "#78716c", "name": "warm-purple"},
    {"bg": "#f8f9fa", "surface": "#ffffff", "primary": "#0d9488", "accent": "#f97316", "text": "#111827", "muted": "#6b7280", "name": "teal-modern"},
    {"bg": "#fefce8", "surface": "#ffffff", "primary": "#b45309", "accent": "#16a34a", "text": "#1c1917", "muted": "#78716c", "name": "warm-amber"},
    {"bg": "#f0f9ff", "surface": "#ffffff", "primary": "#2563eb", "accent": "#ec4899", "text": "#0f172a", "muted": "#64748b", "name": "sky-blue"},
    {"bg": "#fdf2f8", "surface": "#ffffff", "primary": "#be185d", "accent": "#7c3aed", "text": "#1e1b4b", "muted": "#6b7280", "name": "rose-elegant"},
    {"bg": "#f5f3f0", "surface": "#ffffff", "primary": "#292524", "accent": "#c2410c", "text": "#1c1917", "muted": "#78716c", "name": "stone-minimal"},
    {"bg": "#f7f4ef", "surface": "#ffffff", "primary": "#1e3a5f", "accent": "#c9a84c", "text": "#1a1a2e", "muted": "#6b7280", "name": "corporate-navy"},
    # Bold themes
    {"bg": "#0a2540", "surface": "#0d3356", "primary": "#635bff", "accent": "#00d4aa", "text": "#f6f9fc", "muted": "#adbdcc", "name": "stripe-inspired"},
    {"bg": "#1a1a2e", "surface": "#16213e", "primary": "#e94560", "accent": "#0f3460", "text": "#eee", "muted": "#999", "name": "bold-red"},
    {"bg": "#2d1b69", "surface": "#1a0f40", "primary": "#ff6b9d", "accent": "#c44dff", "text": "#f0e6ff", "muted": "#b39ddb", "name": "electric-purple"},
    {"bg": "#003135", "surface": "#004d40", "primary": "#00bfa5", "accent": "#ff6f00", "text": "#e0f2f1", "muted": "#80cbc4", "name": "deep-teal"},
]

# Generic colors that should be replaced (Tailwind defaults)
GENERIC_COLORS = {
    "#3b82f6", "#22c55e", "#ef4444", "#eab308", "#8b5cf6",
    "#ec4899", "#f97316", "#06b6d4", "#14b8a6", "#f43f5e",
}

# Banned heading fonts (too generic)
BANNED_HEADING_FONTS = {"inter", "roboto", "arial", "helvetica", "open sans", "system-ui", "sans-serif"}


def get_random_palette(theme: str = "dark") -> dict:
    """Get a random curated color palette matching the theme."""
    if theme == "dark":
        pool = [p for p in CURATED_PALETTES if p["bg"].startswith("#0") or p["bg"].startswith("#1")]
    elif theme == "light":
        pool = [p for p in CURATED_PALETTES if not p["bg"].startswith("#0") and not p["bg"].startswith("#1")]
    else:
        pool = CURATED_PALETTES
    return random.choice(pool) if pool else random.choice(CURATED_PALETTES)


# ═══════════════════════════════════════════════════════════════════════
# 2. HERO HARDENER
# ═══════════════════════════════════════════════════════════════════════

def harden_hero(html: str, css: str) -> tuple[str, str]:
    """Ensure hero section meets premium standards."""
    hero_match = re.search(
        r'(<section[^>]*data-section-type="hero"[^>]*>)(.*?)(</section>)',
        html, re.DOTALL
    )
    if not hero_match:
        return html, css

    hero_tag = hero_match.group(1)
    hero_content = hero_match.group(2)
    hero_close = hero_match.group(3)
    fixes = []

    # Check for background image — look specifically in hero section HTML and hero-related CSS
    hero_html = hero_tag + hero_content + hero_close
    hero_css_sections = re.findall(r'(?:hero|data-section-type="hero")[^{]*\{[^}]*\}', css, re.IGNORECASE | re.DOTALL)
    hero_css_text = ' '.join(hero_css_sections)
    check_text = hero_html + ' ' + hero_css_text

    has_bg_image = bool(re.search(
        r'background[^;]*url\(|background-image[^;]*url\(|\{\{IMG:',
        check_text, re.IGNORECASE
    ))
    # Also check for <img> inside hero with hero-related classes
    has_hero_img = bool(re.search(r'<img[^>]*(?:hero|cover|banner)[^>]*>', hero_html, re.IGNORECASE))

    if not has_bg_image and not has_hero_img:
        # The pre-resolution _ensure_hero_has_image should have handled this.
        # As a final safety net, inject a generic background via CSS.
        fixes.append("/* Hero: fallback background */")
        fixes.append("""section[data-section-type="hero"] {
  background: linear-gradient(135deg, rgba(10,10,20,0.8), rgba(20,20,40,0.85)),
              url('https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=1920') !important;
  background-size: cover !important;
  background-position: center !important;
}""")

    # Enforce minimum height
    has_min_height = bool(re.search(r'hero.*min-height|hero.*height:\s*[7-9]\d|hero.*80vh|hero.*90vh|hero.*100vh', css, re.IGNORECASE))
    if not has_min_height:
        fixes.append('section[data-section-type="hero"] { min-height: 80vh; }')

    # Enforce white/light text
    has_light_text = bool(re.search(r'hero.*color:\s*#[f-F]|hero.*color:\s*white|hero.*color:\s*#e|hero.*color:\s*#d', css, re.IGNORECASE))
    if not has_light_text:
        fixes.append('section[data-section-type="hero"] h1, section[data-section-type="hero"] p { color: #ffffff; }')

    # Enforce text shadow for readability
    if "text-shadow" not in css or "hero" not in css.split("text-shadow")[0][-200:]:
        fixes.append('section[data-section-type="hero"] h1 { text-shadow: 0 2px 20px rgba(0,0,0,0.4); }')
        fixes.append('section[data-section-type="hero"] p { text-shadow: 0 1px 10px rgba(0,0,0,0.3); }')

    if fixes:
        css = css.rstrip() + "\n\n/* === Hero hardening === */\n" + "\n".join(fixes) + "\n"
        logger.info(f"[HERO HARDEN] Applied {len(fixes)} fixes")

    return html, css


# ═══════════════════════════════════════════════════════════════════════
# 3. WHITESPACE ENFORCER
# ═══════════════════════════════════════════════════════════════════════

def enforce_whitespace(css: str) -> str:
    """Enforce generous whitespace on all sections, cards, and headings."""
    fixes = []

    # Section padding (minimum 5rem vertical)
    if not re.search(r'section.*padding:\s*[5-9]rem|section.*padding:\s*[8-9]\dpx|section.*py-2[0-4]', css):
        fixes.append("""
/* Whitespace: generous section padding */
section[data-section-type] { padding: 6rem 1.5rem; }
section[data-section-type="hero"] { padding: 0; }
section[data-section-type="navbar"] { padding: 0; }
section[data-section-type="footer"] { padding: 4rem 1.5rem; }""")

    # Card internal padding
    fixes.append("""
/* Whitespace: card breathing room */
[class*="card"], [class*="Card"] {
  padding: clamp(1.25rem, 2vw, 2rem);
}""")

    # Heading margins
    fixes.append("""
/* Whitespace: heading spacing */
section[data-section-type] h2 { margin-bottom: 1rem; }
section[data-section-type] h2 + p { margin-bottom: 3rem; }""")

    # Grid gaps
    fixes.append("""
/* Whitespace: grid gaps */
.grid, [class*="grid"] { gap: clamp(1.5rem, 3vw, 2.5rem); }""")

    if fixes:
        css = css.rstrip() + "\n" + "\n".join(fixes) + "\n"

    return css


# ═══════════════════════════════════════════════════════════════════════
# 4. CARD NORMALIZER
# ═══════════════════════════════════════════════════════════════════════

def normalize_cards(css: str, theme: str = "light") -> str:
    """Normalize all cards to consistent, premium styling."""
    if theme == "dark":
        card_css = """
/* Card normalization (dark) */
[class*="card"], [class*="Card"] {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s;
}
[class*="card"]:hover, [class*="Card"]:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
  border-color: rgba(255,255,255,0.15);
}"""
    else:
        card_css = """
/* Card normalization (light) */
[class*="card"], [class*="Card"] {
  background: #ffffff;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
[class*="card"]:hover, [class*="Card"]:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}"""

    return css.rstrip() + "\n" + card_css + "\n"


# ═══════════════════════════════════════════════════════════════════════
# 5. PREMIUM ANIMATION INJECTION
# ═══════════════════════════════════════════════════════════════════════

PREMIUM_ANIMATIONS_CSS = """
/* ═══ Premium Animations ═══ */

/* Hero entrance — staggered fade up */
section[data-section-type="hero"] > * {
  opacity: 0;
  transform: translateY(30px);
  animation: premiumFadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
section[data-section-type="hero"] > *:nth-child(1) { animation-delay: 0.1s; }
section[data-section-type="hero"] > *:nth-child(2) { animation-delay: 0.25s; }
section[data-section-type="hero"] > *:nth-child(3) { animation-delay: 0.4s; }
section[data-section-type="hero"] > *:nth-child(4) { animation-delay: 0.55s; }

@keyframes premiumFadeUp {
  to { opacity: 1; transform: translateY(0); }
}

/* Hero background subtle zoom (ken burns) */
section[data-section-type="hero"]::before {
  content: '';
  position: absolute;
  inset: 0;
  background: inherit;
  background-size: cover;
  background-position: center;
  animation: kenBurns 20s ease-in-out infinite alternate;
  z-index: -1;
}
@keyframes kenBurns {
  0% { transform: scale(1); }
  100% { transform: scale(1.05); }
}

/* Scroll reveal — elements slide up when entering viewport */
.scroll-reveal {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1), transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}
.scroll-reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}

/* Staggered children reveal */
.scroll-reveal.revealed > * {
  opacity: 0;
  transform: translateY(20px);
  animation: childReveal 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
.scroll-reveal.revealed > *:nth-child(1) { animation-delay: 0.05s; }
.scroll-reveal.revealed > *:nth-child(2) { animation-delay: 0.1s; }
.scroll-reveal.revealed > *:nth-child(3) { animation-delay: 0.15s; }
.scroll-reveal.revealed > *:nth-child(4) { animation-delay: 0.2s; }
.scroll-reveal.revealed > *:nth-child(5) { animation-delay: 0.25s; }
.scroll-reveal.revealed > *:nth-child(6) { animation-delay: 0.3s; }
@keyframes childReveal {
  to { opacity: 1; transform: translateY(0); }
}

/* Button hover glow */
[class*="btn"], button[class] {
  position: relative;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
}
[class*="btn"]:hover, button[class]:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--primary-rgb, 99,102,241), 0.3);
}
[class*="btn"]::after, button[class]::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.15) 50%, transparent 70%);
  transform: translateX(-100%);
  transition: transform 0.6s;
}
[class*="btn"]:hover::after, button[class]:hover::after {
  transform: translateX(100%);
}

/* Image hover zoom */
[class*="card"] img, [class*="Card"] img {
  transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
[class*="card"]:hover img, [class*="Card"]:hover img {
  transform: scale(1.05);
}

/* Navbar scroll effect */
section[data-section-type="navbar"].scrolled,
nav.scrolled, header.scrolled {
  background: rgba(10,10,15,0.95) !important;
  backdrop-filter: blur(12px);
  box-shadow: 0 1px 20px rgba(0,0,0,0.15);
}

/* Stats counter glow */
[data-section-type="stats"] [class*="number"],
[data-section-type="stats"] [class*="count"],
[data-section-type="stats"] .stat-value {
  background: linear-gradient(135deg, var(--primary, #6366f1), var(--accent, #f59e0b));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Section divider line */
section[data-section-type]:not([data-section-type="hero"]):not([data-section-type="navbar"]):not([data-section-type="footer"])::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, var(--primary, #6366f1), var(--accent, #f59e0b));
  border-radius: 2px;
}
section[data-section-type] {
  position: relative;
}

/* Smooth image loading */
img {
  opacity: 0;
  transition: opacity 0.4s ease;
}
img.loaded, img[src] {
  opacity: 1;
}
"""

PREMIUM_ANIMATIONS_JS = """
/* ═══ Premium Animations JS ═══ */
(function(){
  // Scroll reveal observer
  var revealObserver = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(entry.isIntersecting){
        entry.target.classList.add('revealed');
        revealObserver.unobserve(entry.target);
      }
    });
  }, {threshold: 0.1, rootMargin: '0px 0px -50px 0px'});

  // Auto-add scroll-reveal to all content sections
  document.querySelectorAll('section[data-section-type]:not([data-section-type="hero"]):not([data-section-type="navbar"])').forEach(function(section){
    if(!section.classList.contains('scroll-reveal')){
      section.classList.add('scroll-reveal');
      revealObserver.observe(section);
    }
  });

  // Navbar scroll effect
  var navbar = document.querySelector('section[data-section-type="navbar"], nav, header');
  if(navbar){
    var scrollThreshold = 50;
    window.addEventListener('scroll', function(){
      if(window.scrollY > scrollThreshold){
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    }, {passive: true});
  }

  // Counter animation
  var counterObserver = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if(entry.isIntersecting){
        var el = entry.target;
        var text = el.textContent.trim();
        var match = text.match(/(\\d[\\d,]*)/);
        if(match){
          var target = parseInt(match[1].replace(/,/g,''));
          var suffix = text.replace(match[1],'');
          var duration = 2000;
          var start = 0;
          var startTime = null;
          function animate(ts){
            if(!startTime) startTime = ts;
            var progress = Math.min((ts - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = Math.floor(eased * target);
            el.textContent = current.toLocaleString() + suffix;
            if(progress < 1) requestAnimationFrame(animate);
          }
          requestAnimationFrame(animate);
        }
        counterObserver.unobserve(el);
      }
    });
  }, {threshold: 0.5});

  document.querySelectorAll('[data-section-type="stats"] [class*="number"], [data-section-type="stats"] [class*="count"], [data-section-type="stats"] .stat-value, [data-section-type="stats"] h3').forEach(function(el){
    var text = el.textContent.trim();
    if(/\\d/.test(text)) counterObserver.observe(el);
  });

  // Image lazy load animation
  document.querySelectorAll('img').forEach(function(img){
    if(img.complete){
      img.classList.add('loaded');
    } else {
      img.addEventListener('load', function(){ img.classList.add('loaded'); });
      img.addEventListener('error', function(){ img.classList.add('loaded'); });
    }
  });

  // Smooth anchor scrolling with offset
  document.querySelectorAll('a[href^="#"]').forEach(function(a){
    a.addEventListener('click', function(e){
      var target = document.querySelector(this.getAttribute('href'));
      if(target){
        e.preventDefault();
        var offset = 80;
        var top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({top: top, behavior: 'smooth'});
      }
    });
  });
})();
"""


def inject_premium_animations(html: str, css: str) -> tuple[str, str]:
    """Inject premium animations CSS and JS into the page."""
    # Add CSS
    if "premiumFadeUp" not in css:
        css = css.rstrip() + "\n" + PREMIUM_ANIMATIONS_CSS

    # Add JS before </body>
    if "scroll-reveal" not in html and "premiumFadeUp" not in html:
        js_block = f"\n<script>{PREMIUM_ANIMATIONS_JS}</script>\n"
        if "</body>" in html:
            html = html.replace("</body>", f"{js_block}</body>", 1)

    return html, css


# ═══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def enforce_sizing(css: str) -> str:
    """Enforce sensible image heights and font sizes across all sections.

    Prevents oversized section images and excessively large typography that
    make generated sites look unpolished on standard screens.
    """
    sizing_rules = """
/* Sizing: constrain section images */
section img:not(.logo):not(.icon):not([width]) {
  max-height: 400px;
  object-fit: cover;
  width: 100%;
}
.card-image, [class*="card"] img {
  max-height: 240px;
  object-fit: cover;
}
.team-photo {
  height: 14rem;
  max-height: 14rem;
  object-fit: cover;
}
.gallery-image {
  max-height: 280px;
  object-fit: cover;
}

/* Sizing: tame font sizes */
h1, .hero-heading { font-size: clamp(2rem, 5vw, 3.5rem) !important; }
h2, .section-title { font-size: clamp(1.5rem, 3vw, 2.25rem) !important; }
h3 { font-size: clamp(1.15rem, 2vw, 1.5rem) !important; }
h4 { font-size: clamp(1rem, 1.5vw, 1.25rem) !important; }
p, .card-text, li { font-size: clamp(0.95rem, 1vw, 1.05rem); line-height: 1.7; }
.hero-subtitle { font-size: clamp(1rem, 1.2vw, 1.15rem) !important; }

/* Sizing: hero max height + navbar clearance */
.hero-section { min-height: min(80vh, 700px); }
.hero-bg-cover { min-height: min(90vh, 800px); }
body { padding-top: 80px !important; }
section:first-of-type, .hero-section, [data-section-type="hero"] {
  padding-top: max(5rem, 80px) !important;
}

/* Mobile nav: hidden by default, shown only when .active */
@media (max-width: 768px) {
  .nav-links, .nav-menu, .navbar-links, .navbar-menu, .menu-items, nav ul:not(.footer-links) {
    display: none !important;
    position: fixed;
    top: 70px;
    left: 0;
    right: 0;
    flex-direction: column;
    padding: 1.5rem 2rem;
    gap: 0.75rem;
    z-index: 9999;
    background: var(--bg, #0a0a0f);
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }
  .nav-links.active, .nav-links.open,
  .nav-menu.active, .nav-menu.open,
  .navbar-links.active, .navbar-links.open,
  .navbar-menu.active, .navbar-menu.open,
  .menu-items.active, .menu-items.open,
  nav ul.active:not(.footer-links), nav ul.open:not(.footer-links) {
    display: flex !important;
  }
  .nav-links a, .nav-menu a, .navbar-links a, .navbar-menu a, .menu-items a, nav ul:not(.footer-links) a {
    padding: 0.5rem 0;
    font-size: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }
  .nav-cta { display: none !important; }
  .mobile-cta { display: block !important; }
  .mobile-cta a { display: block; text-align: center; margin-top: 0.5rem; }
  .nav-toggle, .hamburger, .mobile-toggle, .menu-toggle {
    display: flex !important;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: none;
    border: none;
    color: inherit;
    font-size: 1.25rem;
    cursor: pointer;
    z-index: 10000;
  }
}
"""
    return css.rstrip() + "\n" + sizing_rules + "\n"


def apply_premium_postprocessing(html: str, css: str, theme: str = "light") -> tuple[str, str]:
    """Apply all premium post-processing to generated HTML/CSS.

    Runs: hero hardening → whitespace → card normalization → sizing → animations.
    """
    # 1. Hero hardening
    html, css = harden_hero(html, css)

    # 2. Whitespace enforcement
    css = enforce_whitespace(css)

    # 3. Card normalization
    css = normalize_cards(css, theme)

    # 4. Image & font sizing constraints
    css = enforce_sizing(css)

    # 5. Premium animations
    html, css = inject_premium_animations(html, css)

    logger.info("[PREMIUM] All post-processing applied (hero, whitespace, cards, sizing, animations)")
    return html, css
