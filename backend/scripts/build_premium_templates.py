"""
Build the curated set of 10 premium hand-crafted templates with DISTINCT
layouts per template (not just recolors).

Each template picks its own combination of:
  • hero_layout       — split | full_image | center | asymmetric
  • services_layout   — card_grid | feature_steps | feature_cards | feature_split
  • about_layout      — feature_split | stats_row
  • gallery_layout    — gallery_grid_3 | gallery_grid_4 | logo_cloud
  • button_shape      — rounded | pill | square
  • navbar_style      — light | dark
  • extra_css         — per-template flourishes (type scale, density, accents)

Every section type emitted maps to a key in COMPONENT_PATTERNS so the chat-edit
router can recognize and edit them.

Run:
    cd backend
    PYTHONPATH=. python3 -m scripts.build_premium_templates
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

# ─── Shared base CSS ───────────────────────────────────────────────────────

BASE_CSS = r"""
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: var(--font-body); background: var(--bg); color: var(--text); line-height: 1.6; padding-top: 80px; overflow-x: hidden; min-height: 100vh; }
h1, h2, h3, h4, h5, h6 { font-family: var(--font-heading); font-weight: 700; line-height: 1.18; color: var(--text); }
a { text-decoration: none; color: inherit; }
img { max-width: 100%; height: auto; }
ul { list-style: none; padding: 0; margin: 0; }

/* ─── Layout ─── */
.container { max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }
.container-wide { max-width: 1400px; margin: 0 auto; padding: 0 1.5rem; }
.container-narrow { max-width: 800px; margin: 0 auto; padding: 0 1.5rem; }
.container-xs { max-width: 600px; margin: 0 auto; padding: 0 1.5rem; }

/* ─── Grid ─── */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
@media (max-width: 1024px) {
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
  .grid-4 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .grid-2 { grid-template-columns: 1fr; }
  .grid-3 { grid-template-columns: 1fr; }
  .grid-4 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .grid-4 { grid-template-columns: 1fr; }
}
.text-center { text-align: center; }

/* ─── Sections ─── */
section[data-section-type] { padding: 4.5rem 0; position: relative; }
@media (min-width: 769px) {
  section[data-section-type] { padding: 6rem 0; }
}
.section-header { text-align: center; margin-bottom: 3rem; }
.section-title { font-size: clamp(1.85rem, 3vw, 2.6rem); margin-bottom: 0.75rem; letter-spacing: -0.02em; }
.section-subtitle { font-size: 1.05rem; color: var(--text-muted); max-width: 38rem; margin: 0 auto; line-height: 1.7; }
.section-label { display: inline-flex; align-items: center; gap: 0.75rem; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.28em; font-weight: 600; color: var(--accent); margin-bottom: 1.25rem; }
.label-line { width: 2.5rem; height: 2px; background: var(--accent); display: inline-block; }

section[data-section-type="card_grid"],
section[data-section-type="feature_cards"],
section[data-section-type="feature_steps"],
section[data-section-type="stats_row"] { background: var(--bg-surface); }
section[data-section-type="testimonial_cards"],
section[data-section-type="logo_cloud"] { background: color-mix(in srgb, var(--primary) 4%, var(--bg)); }

/* ─── Buttons ─── */
.btn-primary { display: inline-block; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 0.85rem 2rem; border-radius: var(--radius-btn); font-weight: 600; font-family: inherit; font-size: 0.95rem; border: none; cursor: pointer; transition: var(--transition); text-align: center; letter-spacing: 0.01em; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 12px 32px color-mix(in srgb, var(--primary) 32%, transparent); }
.btn-secondary { display: inline-block; border: 2px solid var(--primary); color: var(--primary); padding: 0.78rem 1.85rem; border-radius: var(--radius-btn); font-weight: 600; font-family: inherit; font-size: 0.95rem; background: transparent; cursor: pointer; transition: var(--transition); text-align: center; }
.btn-secondary:hover { background: var(--primary); color: white; transform: translateY(-2px); }
.btn-primary-light { display: inline-block; background: white; color: var(--primary); padding: 0.85rem 2rem; border-radius: var(--radius-btn); font-weight: 600; border: none; cursor: pointer; transition: var(--transition); }
.btn-primary-light:hover { transform: translateY(-2px); box-shadow: 0 14px 30px rgba(0,0,0,0.22); }
.btn-secondary-light { display: inline-block; border: 2px solid white; color: white; padding: 0.78rem 1.85rem; border-radius: var(--radius-btn); font-weight: 600; background: transparent; cursor: pointer; transition: var(--transition); }
.btn-secondary-light:hover { background: white; color: var(--primary); }
.btn-group { display: flex; flex-wrap: wrap; gap: 1rem; }
.btn-group.center { justify-content: center; }

/* ─── Cards ─── */
.card { background: var(--bg-surface); border-radius: var(--radius); padding: 2rem; box-shadow: var(--shadow); transition: var(--transition); border: 1px solid color-mix(in srgb, var(--text) 6%, transparent); position: relative; overflow: hidden; }
.card:hover { transform: translateY(-8px); box-shadow: var(--shadow-hover); }
.card::after { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--primary), var(--accent)); opacity: 0; transition: opacity 0.3s; }
.card:hover::after { opacity: 1; }
.card-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.6rem; line-height: 1.3; }
.card-text { color: var(--text-muted); line-height: 1.7; font-size: 0.95rem; }
.card-body { padding: 1.5rem; }
.card-image { width: 100%; height: 220px; object-fit: cover; display: block; }
.icon-box { width: 3.5rem; height: 3.5rem; border-radius: 0.85rem; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; color: white; margin-bottom: 1.25rem; flex-shrink: 0; background: linear-gradient(135deg, var(--primary), var(--secondary)); }
.card-link { color: var(--primary); font-weight: 600; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.5rem; transition: gap 0.3s; }
.card-link:hover { gap: 0.75rem; }

/* ─── Images ─── */
.img-cover { width: 100%; height: auto; border-radius: var(--radius); object-fit: cover; transition: transform 0.5s ease; }
.img-cover:hover { transform: scale(1.02); }
.img-wrapper { overflow: hidden; border-radius: var(--radius); }

/* ─── Navbar ─── */
.navbar { position: fixed; top: 0; left: 0; right: 0; z-index: 50; backdrop-filter: blur(14px); transition: var(--transition); padding: 1rem 0; }
.navbar-light { background: rgba(255,255,255,0.85); border-bottom: 1px solid rgba(0,0,0,0.06); }
.navbar-dark { background: rgba(10,10,15,0.55); border-bottom: 1px solid rgba(255,255,255,0.08); }
.navbar-dark .nav-brand, .navbar-dark .nav-links a { color: white; }
.navbar-dark .nav-toggle { color: white; }
nav.nav-scrolled { background: var(--bg) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
.navbar-inner { display: flex; justify-content: space-between; align-items: center; }
.nav-brand { display: flex; align-items: center; gap: 0.7rem; font-weight: 700; font-size: 1.15rem; color: var(--text); font-family: var(--font-heading); }
.nav-links { display: flex; align-items: center; gap: 2rem; }
.nav-links a { font-weight: 500; color: var(--text); transition: color 0.3s; position: relative; }
.nav-links a::after { content: ""; position: absolute; bottom: -6px; left: 0; width: 0; height: 2px; background: var(--primary); transition: width 0.3s ease; }
.nav-links a:hover { color: var(--primary); }
.nav-links a:hover::after { width: 100%; }
.nav-toggle { display: none; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--text); padding: 0.5rem; min-width: 44px; min-height: 44px; align-items: center; justify-content: center; }
.nav-cta { display: inline-block; }
.mobile-cta { display: none; }
@media (max-width: 768px) {
  .nav-links { display: none !important; position: fixed; top: 70px; left: 0; right: 0; flex-direction: column; padding: 1.5rem 2rem; gap: 1.25rem; z-index: 999; }
  .nav-links.active { display: flex !important; background: var(--bg); backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0,0,0,0.15); }
  .nav-toggle { display: flex !important; }
  .nav-cta { display: none !important; }
  .mobile-cta { display: block !important; }
}
.logo-mark { width: 2.4rem; height: 2.4rem; border-radius: 0.6rem; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 0.95rem; flex-shrink: 0; box-shadow: 0 6px 18px rgba(0,0,0,0.18); }

/* ─── Hero base ─── */
.hero-section { position: relative; overflow: hidden; }
.hero-heading { font-size: clamp(2.4rem, 5.4vw, 4.2rem); font-weight: 800; line-height: 1.05; margin-bottom: 1.5rem; letter-spacing: -0.025em; }
.hero-subtitle { font-size: clamp(1.05rem, 1.3vw, 1.2rem); color: var(--text-muted); line-height: 1.75; margin-bottom: 2rem; max-width: 36rem; }
.hero-ctas { display: flex; flex-wrap: wrap; gap: 1rem; }
.trust-line { font-size: 0.875rem; color: var(--text-muted); margin-top: 1rem; }

/* hero_split */
.hero-split { padding: 9rem 0 5rem; min-height: 80vh; display: flex; align-items: center; }
.hero-split-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; }
.hero-split-asymmetric { grid-template-columns: 55% 45%; }
@media (max-width: 768px) {
  .hero-split { min-height: auto; padding-top: 7rem; }
  .hero-split-grid { grid-template-columns: 1fr; }
}
.hero-image-stack { position: relative; }
.hero-image-stack img { width: 100%; aspect-ratio: 4/5; object-fit: cover; border-radius: var(--radius); display: block; }
.floating-card { position: absolute; bottom: -1.25rem; left: -1.25rem; background: var(--bg-surface); border-radius: var(--radius); padding: 1.1rem 1.4rem; box-shadow: var(--shadow-hover); display: flex; align-items: center; gap: 0.75rem; z-index: 10; border: 1px solid color-mix(in srgb, var(--text) 6%, transparent); }
@media (max-width: 768px) { .floating-card { display: none; } }
.hero-accent-border { position: absolute; top: 1rem; right: 1rem; width: 100px; height: 100px; border: 2px solid color-mix(in srgb, var(--primary) 35%, transparent); border-radius: var(--radius); z-index: 1; }
@media (max-width: 768px) { .hero-accent-border { display: none; } }

/* hero_full_image */
.hero-fullbg { margin-top: -80px; min-height: 100vh; display: flex; align-items: center; padding: 9rem 0 5rem; background-size: cover; background-position: center; position: relative; }
.hero-fullbg::before { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.45) 50%, rgba(0,0,0,0.3) 100%); z-index: 1; }
.hero-fullbg > .container, .hero-fullbg > .container-wide { position: relative; z-index: 2; max-width: 1100px; }
.hero-fullbg .hero-heading, .hero-fullbg .section-label, .hero-fullbg .hero-subtitle, .hero-fullbg .trust-line { color: white; }
.hero-fullbg .hero-subtitle { color: rgba(255,255,255,0.88); }
.hero-fullbg .section-label { color: rgba(255,255,255,0.92); }
.hero-fullbg .label-line { background: rgba(255,255,255,0.7); }
.hero-fullbg .trust-line { color: rgba(255,255,255,0.78); }
.hero-fullbg-content { max-width: 36rem; }

/* hero_center */
.hero-center { padding: 11rem 0 6rem; text-align: center; }
.hero-center .hero-heading { font-size: clamp(2.8rem, 7vw, 5rem); margin-left: auto; margin-right: auto; max-width: 22ch; }
.hero-center .hero-subtitle { margin-left: auto; margin-right: auto; max-width: 38rem; }
.hero-center .hero-ctas { justify-content: center; }
.hero-center .section-label { display: inline-flex; }

/* hero_asymmetric — same as split but with reversed proportions (60/40 image left) */
.hero-asym { padding: 9rem 0 5rem; }
.hero-asym-grid { display: grid; grid-template-columns: 5fr 4fr; gap: 4rem; align-items: center; }
@media (max-width: 768px) { .hero-asym-grid { grid-template-columns: 1fr; } .hero-asym { padding-top: 7rem; } }
.hero-asym-image { position: relative; }
.hero-asym-image img { width: 100%; aspect-ratio: 4/5; object-fit: cover; border-radius: var(--radius); }

/* ─── Stats Row ─── */
.stat-item { display: flex; flex-direction: column; gap: 0.6rem; }
.stat-icon { width: 3rem; height: 3rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; color: var(--accent); }
.stat-number { font-size: clamp(2.5rem, 4.5vw, 3.5rem); font-weight: 800; line-height: 1; color: var(--primary); }
.stat-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.22em; font-weight: 600; color: var(--text-muted); }
.stat-sub { font-size: 0.85rem; color: var(--text-muted); margin-top: 0.5rem; line-height: 1.5; }

/* ─── Steps ─── */
.step-item { display: flex; gap: 2rem; padding: 2rem 0; border-top: 1px solid color-mix(in srgb, var(--text) 8%, transparent); }
.step-item:first-child { border-top: none; }
.step-num { font-family: var(--font-heading); font-size: clamp(2.2rem, 4vw, 3rem); font-weight: 700; color: var(--primary); min-width: 4rem; line-height: 1; }
.step-body { flex: 1; }
.step-body h3 { font-size: 1.4rem; margin-bottom: 0.6rem; }
.step-body p { color: var(--text-muted); line-height: 1.75; }
@media (max-width: 640px) { .step-item { flex-direction: column; gap: 0.5rem; } .step-num { font-size: 2rem; } }

/* ─── Image Card (services_image_cards / gallery_4col) ─── */
.image-card { background: var(--bg-surface); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); transition: var(--transition); border: 1px solid color-mix(in srgb, var(--text) 6%, transparent); }
.image-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-hover); }
.image-card-img { width: 100%; height: 220px; object-fit: cover; display: block; }
.image-card-body { padding: 1.5rem 1.5rem 1.75rem; }
.image-card-body h3 { font-size: 1.2rem; margin-bottom: 0.5rem; }
.image-card-body p { color: var(--text-muted); font-size: 0.92rem; line-height: 1.65; }

/* ─── Gallery ─── */
.gallery-item { overflow: hidden; border-radius: var(--radius); cursor: pointer; }
.gallery-image { width: 100%; height: 16rem; object-fit: cover; transition: transform 0.55s ease; }
.gallery-item:hover .gallery-image { transform: scale(1.08); }
.gallery-grid-3 .gallery-image { height: 17rem; }
.gallery-grid-4 .gallery-image { height: 13rem; }

/* ─── Logo Cloud ─── */
.logo-cloud { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.5rem 3rem; align-items: center; }
@media (max-width: 768px) { .logo-cloud { grid-template-columns: repeat(2, 1fr); } }
.logo-item { font-family: var(--font-heading); font-size: 1.4rem; font-weight: 700; text-align: center; opacity: 0.5; transition: opacity 0.3s; letter-spacing: -0.01em; color: var(--text); }
.logo-item:hover { opacity: 1; }

/* ─── Testimonials ─── */
.stars { color: #f59e0b; margin-bottom: 0.75rem; }
.testimonial-quote { color: var(--text-muted); line-height: 1.75; font-style: italic; margin-bottom: 1.25rem; }
.testimonial-author { display: flex; align-items: center; gap: 0.75rem; }
.testimonial-card { background: var(--bg-surface); border-radius: var(--radius); padding: 2rem; box-shadow: var(--shadow); border: 1px solid color-mix(in srgb, var(--text) 6%, transparent); position: relative; overflow: hidden; }
.testimonial-card::before { content: '"'; position: absolute; top: 1rem; left: 1.5rem; font-size: 3rem; color: var(--primary); opacity: 0.18; font-family: var(--font-heading); line-height: 1; }

/* ─── Footer ─── */
footer { margin-top: 4rem; position: relative; z-index: 1; }
.footer-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; }
@media (max-width: 1024px) { .footer-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .footer-grid { grid-template-columns: 1fr; } }
.footer-description { font-size: 0.9rem; color: rgba(255,255,255,0.62); line-height: 1.65; max-width: 280px; }
.footer-heading { font-weight: 700; color: white; margin-bottom: 1rem; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.06em; }
.footer-links { list-style: none; padding: 0; margin: 0; }
.footer-links li { margin-bottom: 0.5rem; }
.footer-links a { color: rgba(255,255,255,0.7); transition: color 0.3s; font-size: 0.9rem; }
.footer-links a:hover { color: white; }
.social-links { display: flex; gap: 0.75rem; margin-top: 1rem; }
.social-link { width: 2.5rem; height: 2.5rem; border-radius: 50%; background: rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; color: white; border: 1px solid rgba(255,255,255,0.1); transition: var(--transition); }
.social-link:hover { background: var(--primary); border-color: var(--primary); transform: translateY(-2px); }
.footer-bottom { border-top: 1px solid rgba(255,255,255,0.08); margin-top: 2.5rem; padding-top: 1.5rem; text-align: center; font-size: 0.875rem; color: rgba(255,255,255,0.5); }

/* ─── Contact form ─── */
.contact-form { display: flex; flex-direction: column; gap: 1rem; }
.contact-form .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 640px) { .contact-form .form-row { grid-template-columns: 1fr; } }
.form-input { width: 100%; padding: 1rem; border-radius: var(--radius); border: 1px solid color-mix(in srgb, var(--text) 12%, transparent); background: var(--bg-surface); color: var(--text); font-family: inherit; font-size: 1rem; transition: border-color 0.3s; box-sizing: border-box; }
.form-input:focus { border-color: var(--primary); outline: none; box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 12%, transparent); }
.form-input::placeholder { color: var(--text-muted); }
.form-textarea { resize: vertical; min-height: 120px; }
.contact-info-card { background: var(--bg-surface); border-radius: var(--radius); padding: 2rem; border: 1px solid color-mix(in srgb, var(--text) 6%, transparent); box-shadow: var(--shadow); }
.contact-item { display: flex; gap: 1rem; align-items: flex-start; margin-bottom: 1rem; }
.contact-icon { color: var(--accent); width: 1.25rem; margin-top: 0.25rem; flex-shrink: 0; }

/* ─── Misc ─── */
.relative { position: relative; }
.gradient-text { background: linear-gradient(135deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
"""

TOKENS_TEMPLATE = """:root {{
  --primary: {primary};
  --secondary: {secondary};
  --accent: {accent};
  --bg: {bg};
  --bg-surface: {bg_surface};
  --text: {text};
  --text-muted: {text_muted};
  --font-heading: {font_heading};
  --font-body: {font_body};
  --radius: {radius};
  --radius-btn: {radius_btn};
  --shadow: 0 6px 24px 0 color-mix(in srgb, {primary} 9%, transparent);
  --shadow-hover: 0 24px 60px rgba(0,0,0,0.18);
  --transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}}
"""


# ─── Template definition ───────────────────────────────────────────────────


@dataclass
class Template:
    id: str
    name: str
    category: str
    description: str
    niche: str
    brand: str
    initials: str

    primary: str
    secondary: str
    accent: str
    bg: str
    bg_surface: str
    text: str
    text_muted: str
    fonts: tuple

    # Layout choices — each picks a distinct visual variant
    hero_layout: str = "split"           # split | full_image | center | asymmetric
    services_layout: str = "card_grid"   # card_grid | feature_steps | feature_cards
    about_layout: str = "feature_split"  # feature_split | stats_row
    gallery_layout: str = "gallery_grid_3"  # gallery_grid_3 | gallery_grid_4 | logo_cloud

    # Personality
    button_shape: str = "rounded"        # rounded | pill | square
    navbar_style: str = "light"          # light | dark
    extra_css: str = ""

    # Content
    hero_title: str = ""
    hero_kicker: str = ""
    hero_subtitle: str = ""
    hero_image: str = ""             # used by split/asymmetric
    hero_bg_image: str = ""          # used by full_image
    hero_cta_primary: str = ""
    hero_cta_secondary: str = ""
    hero_trust: str = ""

    services_label: str = ""
    services_title: str = ""
    services_subtitle: str = ""
    services: list = field(default_factory=list)        # [(icon, title, body), ...]
    services_images: list = field(default_factory=list) # used by feature_cards layout

    about_label: str = ""
    about_title: str = ""
    about_body: str = ""
    about_image: str = ""
    about_bullets: list = field(default_factory=list)
    about_stats: list = field(default_factory=list)     # used by stats_row: [(num,label,sub),...]

    gallery_title: str = ""
    gallery_label: str = ""
    gallery_images: list = field(default_factory=list)
    logos: list = field(default_factory=list)            # used by logo_cloud

    testimonials_title: str = ""
    testimonials_label: str = ""
    testimonials: list = field(default_factory=list)

    cta_title: str = ""
    cta_body: str = ""

    contact_phone: str = ""
    contact_email: str = ""
    contact_address: str = ""
    contact_hours: str = ""

    footer_tagline: str = ""
    footer_columns: list = field(default_factory=list)
    footer_bg: str = "#0b0b14"


# ─── Section renderers ─────────────────────────────────────────────────────


def render_navbar(t: Template) -> str:
    klass = "navbar-dark" if t.navbar_style == "dark" else "navbar-light"
    return f"""
<nav data-section-id="section-0" class="navbar {klass}">
  <div class="container navbar-inner">
    <a href="#hero" class="nav-brand">
      <span class="logo-mark" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">{t.initials}</span>
      <span>{t.brand}</span>
    </a>
    <button class="nav-toggle" aria-label="Toggle menu"><i class="fa-solid fa-bars"></i></button>
    <ul class="nav-links">
      <li><a href="#hero">Home</a></li>
      <li><a href="#services">Services</a></li>
      <li><a href="#about">About</a></li>
      <li><a href="#gallery">Gallery</a></li>
      <li><a href="#testimonials">Reviews</a></li>
      <li><a href="#contact">Contact</a></li>
      <li class="mobile-cta"><a href="#contact" class="btn-primary">Get in Touch</a></li>
    </ul>
    <a href="#contact" class="nav-cta btn-primary">Get in Touch</a>
  </div>
</nav>
"""


# ─── HEROES (4 variants) ────────────────────────────────────────────────


def render_hero_split(t: Template) -> str:
    return f"""
<section data-section-id="hero" data-section-type="hero_split" id="hero" class="hero-section hero-split">
  <div class="container-wide">
    <div class="hero-split-grid hero-split-asymmetric">
      <div>
        <span class="section-label"><span class="label-line"></span>{t.hero_kicker}</span>
        <h1 class="hero-heading">{t.hero_title}</h1>
        <p class="hero-subtitle">{t.hero_subtitle}</p>
        <div class="hero-ctas">
          <a href="#contact" class="btn-primary">{t.hero_cta_primary}</a>
          <a href="#services" class="btn-secondary">{t.hero_cta_secondary}</a>
        </div>
        <p class="trust-line">{t.hero_trust}</p>
      </div>
      <div class="hero-image-stack">
        <img src="{t.hero_image}" alt="{t.brand}" loading="eager" decoding="async">
        <div class="floating-card">
          <div class="icon-box" style="width: 2.5rem; height: 2.5rem; margin-bottom: 0;">
            <i class="fa-solid fa-star" style="color: #f59e0b;"></i>
          </div>
          <div>
            <div style="font-weight: 700; font-size: 0.875rem; color: var(--text);">Trusted by 1,200+</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">5-star rated clients</div>
          </div>
        </div>
        <div class="hero-accent-border"></div>
      </div>
    </div>
  </div>
</section>
"""


def render_hero_full_image(t: Template) -> str:
    bg = t.hero_bg_image or t.hero_image
    return f"""
<section data-section-id="hero" data-section-type="hero_full_image" id="hero" class="hero-section hero-fullbg" style="background-image:url('{bg}');">
  <div class="container">
    <div class="hero-fullbg-content">
      <span class="section-label"><span class="label-line"></span>{t.hero_kicker}</span>
      <h1 class="hero-heading">{t.hero_title}</h1>
      <p class="hero-subtitle">{t.hero_subtitle}</p>
      <div class="hero-ctas">
        <a href="#contact" class="btn-primary-light">{t.hero_cta_primary}</a>
        <a href="#services" class="btn-secondary-light">{t.hero_cta_secondary}</a>
      </div>
      <p class="trust-line">{t.hero_trust}</p>
    </div>
  </div>
</section>
"""


def render_hero_center(t: Template) -> str:
    return f"""
<section data-section-id="hero" data-section-type="hero_center" id="hero" class="hero-section hero-center">
  <div class="container">
    <span class="section-label"><span class="label-line"></span>{t.hero_kicker}</span>
    <h1 class="hero-heading">{t.hero_title}</h1>
    <p class="hero-subtitle">{t.hero_subtitle}</p>
    <div class="hero-ctas">
      <a href="#contact" class="btn-primary">{t.hero_cta_primary}</a>
      <a href="#services" class="btn-secondary">{t.hero_cta_secondary}</a>
    </div>
    <p class="trust-line">{t.hero_trust}</p>
  </div>
</section>
"""


def render_hero_asymmetric(t: Template) -> str:
    return f"""
<section data-section-id="hero" data-section-type="hero_asymmetric" id="hero" class="hero-section hero-asym">
  <div class="container-wide">
    <div class="hero-asym-grid">
      <div class="hero-asym-image">
        <img src="{t.hero_image}" alt="{t.brand}" loading="eager" decoding="async">
        <div class="floating-card">
          <div class="icon-box" style="width: 2.5rem; height: 2.5rem; margin-bottom: 0;">
            <i class="fa-solid fa-star" style="color: #f59e0b;"></i>
          </div>
          <div>
            <div style="font-weight: 700; font-size: 0.875rem; color: var(--text);">5-star service</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">800+ regulars</div>
          </div>
        </div>
        <div class="hero-accent-border"></div>
      </div>
      <div>
        <span class="section-label"><span class="label-line"></span>{t.hero_kicker}</span>
        <h1 class="hero-heading">{t.hero_title}</h1>
        <p class="hero-subtitle">{t.hero_subtitle}</p>
        <div class="hero-ctas">
          <a href="#contact" class="btn-primary">{t.hero_cta_primary}</a>
          <a href="#services" class="btn-secondary">{t.hero_cta_secondary}</a>
        </div>
        <p class="trust-line">{t.hero_trust}</p>
      </div>
    </div>
  </div>
</section>
"""


HERO_RENDERERS = {
    "split": render_hero_split,
    "full_image": render_hero_full_image,
    "center": render_hero_center,
    "asymmetric": render_hero_asymmetric,
}


# ─── SERVICES (4 variants) ─────────────────────────────────────────────


def render_services_card_grid(t: Template) -> str:
    cards = "\n".join(
        f"""      <div class="card">
        <div class="icon-box"><i class="fa-solid {icon}"></i></div>
        <h3 class="card-title">{title}</h3>
        <p class="card-text">{body}</p>
      </div>""" for (icon, title, body) in t.services
    )
    return f"""
<section data-section-id="services" data-section-type="card_grid" id="services">
  <div class="container">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.services_label}</span>
      <h2 class="section-title">{t.services_title}</h2>
      <p class="section-subtitle">{t.services_subtitle}</p>
    </div>
    <div class="grid-3">
{cards}
    </div>
  </div>
</section>
"""


def render_services_feature_steps(t: Template) -> str:
    steps = ""
    for i, (_icon, title, body) in enumerate(t.services, start=1):
        steps += f"""      <div class="step-item">
        <div class="step-num">{i:02}</div>
        <div class="step-body">
          <h3>{title}</h3>
          <p>{body}</p>
        </div>
      </div>
"""
    return f"""
<section data-section-id="services" data-section-type="feature_steps" id="services">
  <div class="container-narrow">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.services_label}</span>
      <h2 class="section-title">{t.services_title}</h2>
      <p class="section-subtitle">{t.services_subtitle}</p>
    </div>
    <div>
{steps}
    </div>
  </div>
</section>
"""


def render_services_feature_cards(t: Template) -> str:
    images = t.services_images or [
        "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=600&fit=crop"
    ] * len(t.services)
    cards = ""
    for (icon, title, body), img in zip(t.services, images):
        cards += f"""      <div class="image-card">
        <img src="{img}" alt="{title}" class="image-card-img" loading="lazy" decoding="async">
        <div class="image-card-body">
          <h3>{title}</h3>
          <p>{body}</p>
        </div>
      </div>
"""
    return f"""
<section data-section-id="services" data-section-type="feature_cards" id="services">
  <div class="container-wide">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.services_label}</span>
      <h2 class="section-title">{t.services_title}</h2>
      <p class="section-subtitle">{t.services_subtitle}</p>
    </div>
    <div class="grid-3">
{cards}
    </div>
  </div>
</section>
"""


SERVICES_RENDERERS = {
    "card_grid": render_services_card_grid,
    "feature_steps": render_services_feature_steps,
    "feature_cards": render_services_feature_cards,
}


# ─── ABOUT (2 variants) ────────────────────────────────────────────────


def render_about_feature_split(t: Template) -> str:
    bullets = "\n".join(
        f'        <li style="display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:0.85rem;color:var(--text-muted);"><i class="fa-solid fa-check" style="color:var(--accent);margin-top:0.4rem;"></i><span>{b}</span></li>'
        for b in t.about_bullets
    )
    return f"""
<section data-section-id="about" data-section-type="feature_split" id="about">
  <div class="container">
    <div class="grid-2">
      <div>
        <img src="{t.about_image}" alt="{t.brand} story" class="img-cover" loading="lazy" decoding="async" style="aspect-ratio: 5/4; object-fit: cover;">
      </div>
      <div>
        <span class="section-label"><span class="label-line"></span>{t.about_label}</span>
        <h2 class="section-title">{t.about_title}</h2>
        <p style="color:var(--text-muted);line-height:1.8;margin-bottom:1.5rem;font-size:1rem;">{t.about_body}</p>
        <ul style="list-style:none;padding:0;margin:0 0 2rem;">
{bullets}
        </ul>
        <a href="#contact" class="btn-primary">{t.hero_cta_primary}</a>
      </div>
    </div>
  </div>
</section>
"""


def render_about_stats_row(t: Template) -> str:
    stats = "\n".join(
        f"""        <div class="stat-item">
          <div class="stat-number">{num}</div>
          <div class="stat-label">{lbl}</div>
          <div class="stat-sub">{sub}</div>
        </div>""" for (num, lbl, sub) in t.about_stats
    )
    return f"""
<section data-section-id="about" data-section-type="stats_row" id="about">
  <div class="container">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.about_label}</span>
      <h2 class="section-title">{t.about_title}</h2>
      <p class="section-subtitle">{t.about_body}</p>
    </div>
    <div class="grid-4" style="margin-top:3rem;">
{stats}
    </div>
  </div>
</section>
"""


ABOUT_RENDERERS = {
    "feature_split": render_about_feature_split,
    "stats_row": render_about_stats_row,
}


# ─── GALLERY (3 variants) ──────────────────────────────────────────────


def render_gallery_grid_3(t: Template) -> str:
    items = "\n".join(
        f'      <div class="gallery-item"><img src="{img}" alt="Gallery {i+1}" class="gallery-image" loading="lazy" decoding="async"></div>'
        for i, img in enumerate(t.gallery_images[:6])
    )
    return f"""
<section data-section-id="gallery" data-section-type="gallery_grid" id="gallery" class="gallery-grid-3">
  <div class="container-wide">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.gallery_label}</span>
      <h2 class="section-title">{t.gallery_title}</h2>
    </div>
    <div class="grid-3">
{items}
    </div>
  </div>
</section>
"""


def render_gallery_grid_4(t: Template) -> str:
    items = "\n".join(
        f'      <div class="gallery-item"><img src="{img}" alt="Gallery {i+1}" class="gallery-image" loading="lazy" decoding="async"></div>'
        for i, img in enumerate(t.gallery_images[:8])
    )
    return f"""
<section data-section-id="gallery" data-section-type="gallery_grid" id="gallery" class="gallery-grid-4">
  <div class="container-wide">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.gallery_label}</span>
      <h2 class="section-title">{t.gallery_title}</h2>
    </div>
    <div class="grid-4">
{items}
    </div>
  </div>
</section>
"""


def render_gallery_logo_cloud(t: Template) -> str:
    items = "\n".join(
        f'      <div class="logo-item">{logo}</div>' for logo in t.logos
    )
    return f"""
<section data-section-id="gallery" data-section-type="logo_cloud" id="gallery">
  <div class="container">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.gallery_label}</span>
      <h2 class="section-title">{t.gallery_title}</h2>
    </div>
    <div class="logo-cloud">
{items}
    </div>
  </div>
</section>
"""


GALLERY_RENDERERS = {
    "gallery_grid_3": render_gallery_grid_3,
    "gallery_grid_4": render_gallery_grid_4,
    "logo_cloud": render_gallery_logo_cloud,
}


# ─── Testimonials / CTA / Contact / Footer (one variant each) ─────────


def render_testimonials(t: Template) -> str:
    cards = "\n".join(
        f"""      <div class="testimonial-card">
        <div class="stars">
          <i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>
        </div>
        <p class="testimonial-quote">"{quote}"</p>
        <div class="testimonial-author">
          <div style="width:2.75rem;height:2.75rem;border-radius:50%;background:linear-gradient(135deg,var(--primary),var(--secondary));color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.95rem;">{author[0]}</div>
          <div>
            <div style="font-weight:600;font-size:0.95rem;color:var(--text);">{author}</div>
            <div style="font-size:0.8rem;color:var(--text-muted);">{role}</div>
          </div>
        </div>
      </div>""" for (quote, author, role) in t.testimonials
    )
    return f"""
<section data-section-id="testimonials" data-section-type="testimonial_cards" id="testimonials">
  <div class="container">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>{t.testimonials_label}</span>
      <h2 class="section-title">{t.testimonials_title}</h2>
    </div>
    <div class="grid-3">
{cards}
    </div>
  </div>
</section>
"""


def render_cta(t: Template) -> str:
    return f"""
<section data-section-id="cta" data-section-type="cta_centered" id="cta" style="background:linear-gradient(135deg,var(--primary),var(--secondary));color:white;">
  <div class="container-narrow text-center">
    <h2 class="section-title" style="color:white;">{t.cta_title}</h2>
    <p class="section-subtitle" style="color:rgba(255,255,255,0.86);max-width:42rem;">{t.cta_body}</p>
    <div class="btn-group center" style="margin-top:2rem;">
      <a href="#contact" class="btn-primary-light">{t.hero_cta_primary}</a>
    </div>
  </div>
</section>
"""


def render_contact(t: Template) -> str:
    return f"""
<section data-section-id="contact" data-section-type="contact" id="contact">
  <div class="container">
    <div class="section-header">
      <span class="section-label"><span class="label-line"></span>GET IN TOUCH</span>
      <h2 class="section-title">Let's Talk</h2>
      <p class="section-subtitle">Reach out and we'll get back to you within one business day.</p>
    </div>
    <div class="grid-2">
      <div class="contact-info-card">
        <h3 style="margin-bottom:1.5rem;font-size:1.25rem;">Visit / Call</h3>
        <div class="contact-item">
          <i class="fa-solid fa-phone contact-icon"></i>
          <div>
            <div style="font-weight:600;margin-bottom:0.25rem;">Phone</div>
            <div style="color:var(--text-muted);">{t.contact_phone}</div>
          </div>
        </div>
        <div class="contact-item">
          <i class="fa-solid fa-envelope contact-icon"></i>
          <div>
            <div style="font-weight:600;margin-bottom:0.25rem;">Email</div>
            <div style="color:var(--text-muted);">{t.contact_email}</div>
          </div>
        </div>
        <div class="contact-item">
          <i class="fa-solid fa-location-dot contact-icon"></i>
          <div>
            <div style="font-weight:600;margin-bottom:0.25rem;">Address</div>
            <div style="color:var(--text-muted);">{t.contact_address}</div>
          </div>
        </div>
        <div class="contact-item">
          <i class="fa-solid fa-clock contact-icon"></i>
          <div>
            <div style="font-weight:600;margin-bottom:0.25rem;">Hours</div>
            <div style="color:var(--text-muted);">{t.contact_hours}</div>
          </div>
        </div>
      </div>
      <div class="contact-info-card">
        <h3 style="margin-bottom:1.5rem;font-size:1.25rem;">Send a Message</h3>
        <form class="contact-form">
          <div class="form-row">
            <input type="text" class="form-input" placeholder="Your Name" required>
            <input type="email" class="form-input" placeholder="Your Email" required>
          </div>
          <input type="tel" class="form-input" placeholder="Phone Number">
          <textarea class="form-input form-textarea" placeholder="How can we help you?" rows="4"></textarea>
          <button type="submit" class="btn-primary" style="width:100%;">Send Message</button>
        </form>
      </div>
    </div>
  </div>
</section>
"""


def render_footer(t: Template) -> str:
    columns = ""
    for heading, links in t.footer_columns:
        items = "\n".join(f'        <li><a href="#">{l}</a></li>' for l in links)
        columns += f"""
    <div>
      <h4 class="footer-heading">{heading}</h4>
      <ul class="footer-links">
{items}
      </ul>
    </div>
"""
    return f"""
<footer data-section-type="footer" style="background:{t.footer_bg};padding:4rem 0 2rem;">
  <div class="container footer-grid">
    <div>
      <a href="#" class="nav-brand" style="color:white;margin-bottom:1rem;display:inline-flex;">
        <span class="logo-mark" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">{t.initials}</span>
        <span>{t.brand}</span>
      </a>
      <p class="footer-description">{t.footer_tagline}</p>
      <div class="social-links">
        <a href="#" class="social-link" aria-label="Instagram"><i class="fa-brands fa-instagram"></i></a>
        <a href="#" class="social-link" aria-label="Facebook"><i class="fa-brands fa-facebook"></i></a>
        <a href="#" class="social-link" aria-label="LinkedIn"><i class="fa-brands fa-linkedin"></i></a>
        <a href="#" class="social-link" aria-label="X"><i class="fa-brands fa-x-twitter"></i></a>
      </div>
    </div>
{columns}
  </div>
  <div class="container">
    <div class="footer-bottom">© 2026 {t.brand}. All rights reserved.</div>
  </div>
</footer>
"""


# ─── Personality (button shapes, type scale) ─────────────────────────


def shape_css(button_shape: str) -> tuple[str, str]:
    """Return (radius, radius_btn) for the button shape."""
    if button_shape == "pill":
        return "20px", "999px"
    if button_shape == "square":
        return "4px", "4px"
    return "16px", "12px"  # rounded (default)


# ─── Build a single template file ─────────────────────────────────────


def build_template(t: Template) -> str:
    radius, radius_btn = shape_css(t.button_shape)
    google_url = f"https://fonts.googleapis.com/css2?family={t.fonts[2]}&display=swap"
    css = f"@import url('{google_url}');\n\n" + TOKENS_TEMPLATE.format(
        primary=t.primary, secondary=t.secondary, accent=t.accent,
        bg=t.bg, bg_surface=t.bg_surface, text=t.text, text_muted=t.text_muted,
        font_heading=t.fonts[0], font_body=t.fonts[1],
        radius=radius, radius_btn=radius_btn,
    ) + BASE_CSS

    if t.extra_css:
        css += "\n/* ─── Per-template overrides ─── */\n" + t.extra_css.strip() + "\n"

    sections = (
        render_navbar(t)
        + HERO_RENDERERS[t.hero_layout](t)
        + SERVICES_RENDERERS[t.services_layout](t)
        + ABOUT_RENDERERS[t.about_layout](t)
        + GALLERY_RENDERERS[t.gallery_layout](t)
        + render_testimonials(t)
        + render_cta(t)
        + render_contact(t)
        + render_footer(t)
    )
    return f"<style>\n{css}\n</style>\n{sections}"


# ─── 10 templates with distinct layout combinations ───────────────────


TEMPLATES: list[Template] = [

    # 1. RESTAURANT — full-bleed dark hero, card grid services, image+text about, 3-col gallery
    Template(
        id="restaurant",
        name="Lumière Fine Dining",
        category="Restaurant",
        description="Full-bleed cinematic hero, classic French serif, dark navbar, three-column gallery.",
        niche="restaurant",
        brand="Lumière",
        initials="L",
        primary="#b8860b",
        secondary="#8b6508",
        accent="#0f3a2e",
        bg="#fbf7f0",
        bg_surface="#ffffff",
        text="#1a120b",
        text_muted="#6b5a4a",
        fonts=("'Playfair Display', serif", "'Inter', sans-serif", "Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@500;600;700;800"),
        hero_layout="full_image",
        services_layout="card_grid",
        about_layout="feature_split",
        gallery_layout="gallery_grid_3",
        button_shape="rounded",
        navbar_style="dark",
        extra_css=".hero-heading{font-size:clamp(3rem,7vw,5.5rem);font-weight:800;}.section-title{font-family:var(--font-heading);}.btn-primary{padding:1rem 2.4rem;}",
        hero_title="An evening to remember",
        hero_kicker="MICHELIN-INSPIRED CUISINE",
        hero_subtitle="Seasonal tasting menus crafted by Chef Auguste Beaumont, paired with wines from our cellar of 600+ vintages.",
        hero_image="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1200&h=1500&fit=crop",
        hero_bg_image="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1800&h=1200&fit=crop",
        hero_cta_primary="Reserve a table",
        hero_cta_secondary="View the menu",
        hero_trust="✦ Awarded Best Restaurant 2025 · 4.9★ on OpenTable · 1,200+ guest reviews",
        services_label="THE EXPERIENCE",
        services_title="What awaits you tonight",
        services_subtitle="Three rooms, one chef, and a story for every dish.",
        services=[
            ("fa-utensils", "Tasting Menu", "Seven seasonal courses showcasing the best produce from our partner farms across Provence."),
            ("fa-wine-glass", "Wine Pairing", "Sommelier-curated pairings from our 600-bottle cellar — biodynamic, classic, and natural."),
            ("fa-champagne-glasses", "Private Dining", "Two intimate rooms for celebrations of up to 14, with bespoke menus and wine service."),
        ],
        about_label="OUR STORY",
        about_title="Six years. One obsession.",
        about_body="Lumière opened in 2019 as a love letter to Provençal cuisine. Every dish on our menu starts in our morning markets and finishes at your table no more than six hours later.",
        about_image="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1000&h=800&fit=crop",
        about_bullets=[
            "Two-Michelin-key sustainability certification",
            "Chef Auguste Beaumont — 22 years in starred kitchens",
            "Direct partnerships with 14 organic producers",
            "Vegan and gluten-free tasting menus on request",
        ],
        gallery_label="THE TABLE",
        gallery_title="Tonight on the menu",
        gallery_images=[
            "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1432139509613-5c4255815697?w=900&h=700&fit=crop",
        ],
        testimonials_label="KIND WORDS",
        testimonials_title="What our guests say",
        testimonials=[
            ("The most elegant dinner I've had in years. Every course felt deliberate — and the wine pairing was extraordinary.", "Sofia Marchetti", "Food critic, Le Soir"),
            ("The only place I take clients when the deal really matters. Service is silent and the food does the talking.", "James Whitfield", "Managing Partner, Whitfield Capital"),
            ("Our anniversary dinner was perfect from the welcome glass to the petit fours. We'll be back every year.", "Aisha Rahman", "Returning guest"),
        ],
        cta_title="Book your table",
        cta_body="Tables open 30 days in advance. Tasting menu must be reserved at least 48 hours ahead.",
        contact_phone="+971 4 555 8200",
        contact_email="reserve@lumiere-dining.ae",
        contact_address="Building 7, City Walk, Dubai, UAE",
        contact_hours="Tue–Sun · 6:00pm – 11:00pm · Closed Mondays",
        footer_tagline="A modern French tasting menu in the heart of City Walk. Six rooms, one chef, no shortcuts.",
        footer_columns=[
            ("Visit", ["The Menu", "Wine List", "Private Dining", "Gift Cards"]),
            ("Lumière", ["Our Story", "Press", "Careers", "Partner Farms"]),
            ("Contact", ["Reservations", "Events", "Press Inquiries", "Newsletter"]),
        ],
        footer_bg="#1a120b",
    ),

    # 2. BUSINESS CONSULTANCY — centered editorial hero, numbered steps, stats, logo cloud
    Template(
        id="business_consultancy",
        name="Veridia Strategy",
        category="Business Consultancy",
        description="Editorial centered hero with no image, numbered process, stats row, client logo cloud. Quiet, confident, lots of whitespace.",
        niche="consulting",
        brand="Veridia Strategy",
        initials="V",
        primary="#0b3b3a",
        secondary="#125858",
        accent="#c9a45a",
        bg="#f7f5ef",
        bg_surface="#ffffff",
        text="#0a1a1a",
        text_muted="#5b6b6b",
        fonts=("'Cormorant Garamond', serif", "'Inter', sans-serif", "Cormorant+Garamond:wght@500;600;700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="center",
        services_layout="feature_steps",
        about_layout="stats_row",
        gallery_layout="logo_cloud",
        button_shape="rounded",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,7vw,5.5rem);font-weight:600;letter-spacing:-0.03em;}
        .section-title{font-family:var(--font-heading);font-weight:600;}
        .hero-center{padding:13rem 0 7rem;}
        section[data-section-type]{padding:7rem 0;}
        """,
        hero_title="Strategy that survives the boardroom.",
        hero_kicker="STRATEGY · M&A · TRANSFORMATION",
        hero_subtitle="We work with founders and executives on the decisions that won't show up in a slide deck — the ones that quietly compound into the next decade of growth.",
        hero_image="",
        hero_cta_primary="Book a discovery call",
        hero_cta_secondary="Our practice areas",
        hero_trust="Trusted by 80+ founders and operators across the GCC, Europe, and South Asia.",
        services_label="HOW WE WORK",
        services_title="Four practices, one principle",
        services_subtitle="Independent advice, no resale of products, no kickbacks. We're paid to be wrong with you, not right at you.",
        services=[
            ("", "Discovery", "Two weeks alongside your team to understand the real problem — not the one in the brief. We go to the warehouse, the call centre, the boardroom."),
            ("", "Strategy", "Three-year strategic plans, scenario modeling, and a board-ready narrative. Senior partners only — no analyst pyramid behind the curtain."),
            ("", "Execution", "We embed alongside your team for 6–12 months and stay on the hook until the numbers move. The plan is only worth the implementation."),
            ("", "Transition", "A clear handover to your team. We don't believe in permanent advisors — every engagement is designed to make us redundant."),
        ],
        about_label="THE FIRM",
        about_title="Twenty-six years. Senior partners only.",
        about_body="No leverage model, no analyst pyramid. Every engagement is led by a partner with 15+ years of operating experience.",
        about_stats=[
            ("80+", "FOUNDERS SERVED", "Across the GCC, Europe and South Asia"),
            ("4", "CLIENTS / PARTNER", "Capped engagement load — depth over volume"),
            ("82%", "REPEAT REVENUE", "Of new work comes from existing clients"),
            ("100%", "INDEPENDENT", "No resale, no kickbacks, no software tie-ins"),
        ],
        gallery_label="OUR CLIENTS",
        gallery_title="Some of the people who trust us",
        logos=["Atlas Group", "Lenz & Müller", "Iyer Holdings", "Nordvik", "Halcyon Bank", "Marais SA", "Pinnacle Foods", "Visma Industries"],
        testimonials_label="CLIENTS",
        testimonials_title="What founders say",
        testimonials=[
            ("Veridia's partner sat in our board meetings for four months. The plan they wrote with us is the one we still run today.", "Hala Sharif", "CEO, Atlas Logistics Group"),
            ("They told us not to do the deal. They were right. Three years later we did the right one — also with them.", "Marco Lenz", "Founder, Lenz & Müller"),
            ("Best strategy work we've ever bought. No theatre, no padding, no junior analysts.", "Priya Iyer", "Group COO, Iyer Holdings"),
        ],
        cta_title="A 30-minute call. No deck, no pitch.",
        cta_body="Tell us what's on your desk this quarter. We'll tell you whether we can help — and who's actually better suited if we can't.",
        contact_phone="+971 4 422 3300",
        contact_email="partners@veridia-strategy.com",
        contact_address="DIFC Gate Village 4, Dubai, UAE",
        contact_hours="Mon–Fri · 9:00am – 6:00pm GST",
        footer_tagline="An independent boutique advising founders and boards on the decisions that compound. Senior partners only.",
        footer_columns=[
            ("Practice", ["Strategy", "M&A Advisory", "Transformation", "Sector Expertise"]),
            ("Firm", ["Partners", "Approach", "Press", "Careers"]),
            ("Contact", ["Discovery Call", "DIFC Office", "Newsletter", "Privacy"]),
        ],
        footer_bg="#0a1a1a",
    ),

    # 3. TECH — split dark hero, card grid services, stats row, 4-col gallery
    Template(
        id="tech",
        name="Nexus Cloud Platform",
        category="Technology",
        description="Dark gradient split hero, monospace accents, square buttons, dense 4-col gallery — modern SaaS feel.",
        niche="tech_startup",
        brand="Nexus Cloud",
        initials="N",
        primary="#6366f1",
        secondary="#8b5cf6",
        accent="#22d3ee",
        bg="#0a0e1a",
        bg_surface="#111827",
        text="#f3f4f6",
        text_muted="#94a3b8",
        fonts=("'Space Grotesk', sans-serif", "'Inter', sans-serif", "Space+Grotesk:wght@500;600;700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="split",
        services_layout="card_grid",
        about_layout="stats_row",
        gallery_layout="gallery_grid_4",
        button_shape="square",
        navbar_style="dark",
        extra_css="""
        .nav-brand,.nav-links a{color:#f3f4f6;}
        .hero-heading{font-family:var(--font-heading);font-weight:700;}
        .section-title{font-family:var(--font-heading);}
        .stat-number{background:linear-gradient(135deg,var(--primary),var(--accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
        .card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);}
        .testimonial-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);}
        .contact-info-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);}
        section[data-section-type="card_grid"],section[data-section-type="stats_row"]{background:rgba(255,255,255,0.02);}
        section[data-section-type="testimonial_cards"]{background:rgba(99,102,241,0.04);}
        .form-input{background:rgba(255,255,255,0.04);border-color:rgba(255,255,255,0.1);color:#f3f4f6;}
        .image-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);}
        .floating-card{background:#111827;border-color:rgba(255,255,255,0.1);}
        .hero-split{background:radial-gradient(ellipse at top right,rgba(99,102,241,0.18),transparent 60%);}
        """,
        hero_title="Ship infrastructure. Not config files.",
        hero_kicker="DEVELOPER PLATFORM",
        hero_subtitle="Nexus Cloud is the platform engineering layer for product teams. One CLI, every cloud, zero YAML. Deploy in 90 seconds — including the database.",
        hero_image="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1200&h=1500&fit=crop",
        hero_cta_primary="Start free trial",
        hero_cta_secondary="See it in action",
        hero_trust="Trusted by 4,200+ engineering teams · Used in production at Fortune 500 · SOC 2 Type II",
        services_label="WHAT YOU GET",
        services_title="A platform engineering team in a box",
        services_subtitle="Stop renting platform engineers. Stop maintaining Terraform. Just ship.",
        services=[
            ("fa-rocket", "One-command deploys", "git push and we handle the rest — networking, secrets, scaling, rollbacks. Works on AWS, GCP, and Azure."),
            ("fa-shield-halved", "Built-in observability", "Logs, traces, metrics, and alerts wired in by default. No agent install, no extra invoice."),
            ("fa-bolt", "Preview environments", "Every pull request gets a real, throwaway environment with its own database. Reviewing code stops being a chore."),
        ],
        about_label="WHY TEAMS SWITCH",
        about_title="Numbers from production",
        about_body="What customers report after their first 90 days on Nexus.",
        about_stats=[
            ("4,200", "TEAMS USING NEXUS", "Across startups and Fortune 500"),
            ("90s", "AVG DEPLOY TIME", "git push to live URL"),
            ("99.99%", "CONTROL-PLANE UPTIME", "Over the past 18 months"),
            ("$24M", "SERIES A FUNDING", "From a16z and Greylock"),
        ],
        gallery_label="UNDER THE HOOD",
        gallery_title="What you get on day one",
        gallery_images=[
            "https://images.unsplash.com/photo-1518770660439-4636190af475?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1550439062-609e1531270e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1607799279861-4dd421887fb3?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1551434678-e076c223a692?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1581094288338-2314dddb7ece?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1542903660-eedba2cda473?w=900&h=700&fit=crop",
        ],
        testimonials_label="LOVED BY",
        testimonials_title="Engineers who used to hate platform engineering",
        testimonials=[
            ("We replaced a 4-person platform team with Nexus and shipped 3x faster. The math doesn't lie.", "Jordan Kim", "VP Engineering, Brightlane"),
            ("First infra tool that didn't ask me to learn a new YAML schema. I almost cried.", "Emilia Costa", "Staff Engineer, Quanta Labs"),
            ("Preview environments alone paid for the contract. Code review stopped being a guessing game.", "Theo Anders", "Engineering Manager, Reflex"),
        ],
        cta_title="Try Nexus on your next deploy",
        cta_body="Free up to 5 services and 3 environments. No credit card. Production-ready from day one.",
        contact_phone="+1 415 555 0190",
        contact_email="hello@nexuscloud.dev",
        contact_address="475 Brannan St, San Francisco, CA",
        contact_hours="On-call 24/7 · Sales Mon–Fri 9–6 PT",
        footer_tagline="The platform engineering layer for product teams. One CLI, every cloud, zero YAML.",
        footer_columns=[
            ("Product", ["Features", "Integrations", "Pricing", "Changelog"]),
            ("Developers", ["Docs", "API", "CLI", "Status"]),
            ("Company", ["About", "Blog", "Careers", "Security"]),
        ],
        footer_bg="#06080f",
    ),

    # 4. PET SHOP — split friendly hero, image-card services, image+text about, 3-col gallery, pill buttons
    Template(
        id="pet_shop",
        name="Pawhaus",
        category="Pet Care",
        description="Friendly split hero, image-top service cards, pill buttons, warm coral palette.",
        niche="pet_shop",
        brand="Pawhaus",
        initials="P",
        primary="#e85d2f",
        secondary="#f08c4d",
        accent="#0c5e60",
        bg="#fff8f1",
        bg_surface="#ffffff",
        text="#1f1611",
        text_muted="#6b5a4a",
        fonts=("'Fraunces', serif", "'Nunito', sans-serif", "Fraunces:wght@500;600;700&family=Nunito:wght@400;500;600;700"),
        hero_layout="split",
        services_layout="feature_cards",
        about_layout="feature_split",
        gallery_layout="gallery_grid_3",
        button_shape="pill",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-weight:700;}
        .image-card{border-radius:24px;}
        .image-card-img{border-radius:24px 24px 0 0;}
        .card{border-radius:24px;}
        .icon-box{border-radius:18px;}
        """,
        hero_title="The good life, for the good ones.",
        hero_kicker="PET CARE · GROOMING · SUPPLIES",
        hero_subtitle="Pawhaus is the neighbourhood spot for grooming, premium food, vet-grade supplies, and grown-ups who think their dog is a person.",
        hero_image="https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=1200&h=1500&fit=crop",
        hero_cta_primary="Book a grooming",
        hero_cta_secondary="Shop the store",
        hero_trust="🐾 4.9★ on Google · 600+ happy regulars · Trusted by local vets",
        services_label="WHAT WE DO",
        services_title="Everything your pet asks you for",
        services_subtitle="Grooming room, vet-clean retail floor, training corner. One stop, every wagging tail.",
        services=[
            ("fa-shower", "Spa & Grooming", "Full grooming for dogs of every size and coat. Hypoallergenic shampoos, blueberry facials, the works."),
            ("fa-bone", "Premium Supplies", "Curated dry and raw food, treats, beds, and accessories — nothing on our shelf we wouldn't give our own pets."),
            ("fa-stethoscope", "Vet-Linked Care", "Monthly visits from a partner veterinarian, microchipping, and a direct line to a 24/7 emergency clinic."),
        ],
        services_images=[
            "https://images.unsplash.com/photo-1576201836106-db1758fd1c97?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1583511655826-05700d52f4d9?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=900&h=700&fit=crop",
        ],
        about_label="OUR STORY",
        about_title="Started by pet parents. Run by pet parents.",
        about_body="Pawhaus opened in 2021 because we couldn't find a single place that did grooming, food, and care without making us feel like we were buying it from a warehouse. Every product we stock has been tested on our own dogs first — and yes, they have opinions.",
        about_image="https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=1000&h=800&fit=crop",
        about_bullets=[
            "Family-run, neighbourhood-loved since 2021",
            "Certified grooming team — 6+ years experience each",
            "Only food brands with full ingredient transparency",
            "Free nail trims for rescues, every Wednesday",
        ],
        gallery_label="OUR REGULARS",
        gallery_title="Our happiest customers",
        gallery_images=[
            "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1583511655826-05700d52f4d9?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=900&h=700&fit=crop",
        ],
        testimonials_label="HOOMAN REVIEWS",
        testimonials_title="Words from our human regulars",
        testimonials=[
            ("Best grooming Bella's ever had. She doesn't usually like new places — at Pawhaus she pulls me to the door.", "Lina Hassan", "Mom to Bella (Cavoodle)"),
            ("They actually know what's in the food they sell. I came in for a leash and left with a much better diet plan.", "Marco Diaz", "Dad to two greyhounds"),
            ("My rescue was nervous around clippers — now he naps through grooming. They worked magic.", "Yara Khoury", "Foster volunteer"),
        ],
        cta_title="Book your pet's next visit",
        cta_body="Grooming slots fill up a week in advance. Same-day spots open most mornings — call us.",
        contact_phone="+971 4 222 6677",
        contact_email="hello@pawhaus.ae",
        contact_address="Al Wasl Square, Jumeirah 1, Dubai",
        contact_hours="Daily · 9:00am – 8:00pm",
        footer_tagline="Neighbourhood pet care done right. Grooming, premium food, and the good kind of pampering.",
        footer_columns=[
            ("Services", ["Grooming", "Day Care", "Training", "Adoption"]),
            ("Shop", ["Food", "Toys", "Accessories", "Health"]),
            ("Pawhaus", ["About", "Our Team", "Events", "Press"]),
        ],
        footer_bg="#1f1611",
    ),

    # 5. RENTAL — full-bleed dark car hero, image-card fleet, stats row, 4-col gallery, square buttons
    Template(
        id="rental",
        name="Drift Premium Car Rental",
        category="Rental",
        description="Cinematic full-bleed hero, fleet shown as image cards, dense 4-col gallery, dark navbar, square buttons.",
        niche="car_dealership",
        brand="Drift",
        initials="D",
        primary="#ea580c",
        secondary="#dc2626",
        accent="#fbbf24",
        bg="#0a0a0a",
        bg_surface="#161616",
        text="#f5f5f4",
        text_muted="#a8a29e",
        fonts=("'Bebas Neue', sans-serif", "'Inter', sans-serif", "Bebas+Neue&family=Inter:wght@300;400;500;600;700"),
        hero_layout="full_image",
        services_layout="feature_cards",
        about_layout="stats_row",
        gallery_layout="gallery_grid_4",
        button_shape="square",
        navbar_style="dark",
        extra_css="""
        .nav-brand,.nav-links a{color:#f5f5f4;}
        .hero-heading{font-family:var(--font-heading);letter-spacing:0.01em;font-size:clamp(3rem,8vw,6rem);font-weight:400;}
        .section-title{font-family:var(--font-heading);font-weight:400;font-size:clamp(2rem,4vw,3rem);}
        .image-card{background:#1a1a1a;border:1px solid rgba(255,255,255,0.06);}
        .image-card-body h3{color:#f5f5f4;}
        .image-card-body p{color:#a8a29e;}
        .testimonial-card{background:#161616;border:1px solid rgba(255,255,255,0.06);}
        .contact-info-card{background:#161616;border:1px solid rgba(255,255,255,0.06);}
        section[data-section-type="feature_cards"],section[data-section-type="stats_row"]{background:#0f0f0f;}
        section[data-section-type="testimonial_cards"]{background:#1a0a05;}
        .form-input{background:#0a0a0a;border-color:rgba(255,255,255,0.1);color:#f5f5f4;}
        .stat-number{color:var(--accent);}
        """,
        hero_title="Rent the keys. Skip the queue.",
        hero_kicker="LUXURY · SPORT · OFF-ROAD",
        hero_subtitle="Drift puts the GCC's best fleet of premium cars in your hands — from a daily Range Rover to a weekend Lamborghini Huracán. Delivered to your door, picked up when you're done.",
        hero_image="https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1200&h=1500&fit=crop",
        hero_bg_image="https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=1800&h=1200&fit=crop",
        hero_cta_primary="Reserve a car",
        hero_cta_secondary="Browse the fleet",
        hero_trust="🏁 240+ vehicles · Same-day delivery in Dubai & Abu Dhabi · 100% deposit refunds",
        services_label="OUR FLEET",
        services_title="Three categories. Zero compromise.",
        services_subtitle="Every car serviced after every rental. Detailed before delivery. Insured to the maximum.",
        services=[
            ("fa-car", "Luxury Daily", "Range Rover, G-Class, S-Class, BMW 7 — the ones you actually want to be seen in. From AED 850/day."),
            ("fa-flag-checkered", "Sport & Supercars", "Lamborghini, Ferrari, McLaren, Porsche. For the weekend you'll be telling stories about for a year."),
            ("fa-route", "Off-Road & 4x4", "Wrangler Rubicon, Land Cruiser, Ford Raptor — fully kitted for the dunes. Rooftop tents on request."),
        ],
        services_images=[
            "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=900&h=700&fit=crop",
        ],
        about_label="WHY DRIFT",
        about_title="Concierge rental, not a car park",
        about_body="Why renters keep coming back to Drift instead of the airport queues.",
        about_stats=[
            ("240+", "VEHICLES IN FLEET", "Across 3 categories"),
            ("98%", "ON-TIME DELIVERY", "To your hotel or residence"),
            ("24/7", "CONCIERGE SUPPORT", "For breakdowns and changes"),
            ("0", "HIDDEN FEES", "All-inclusive day rate"),
        ],
        gallery_label="THE FLEET",
        gallery_title="Some of what's available now",
        gallery_images=[
            "https://images.unsplash.com/photo-1542362567-b07e54358753?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1600712242805-5f78671b24da?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=900&h=700&fit=crop",
        ],
        testimonials_label="CLIENT TALK",
        testimonials_title="What our clients say",
        testimonials=[
            ("Rented a Huracán for a wedding. Delivered to the venue, picked up the next morning, no fuss. Class act.", "Ahmed Khalifa", "Repeat client"),
            ("I rent a G-Class from Drift every time I'm in town. Always immaculate, always on time.", "Sarah Lin", "Business traveller"),
            ("First rental I've done where the deposit refund actually showed up the same day. Wild.", "James O'Brien", "First-time renter"),
        ],
        cta_title="Pick up the car. Skip the airport line.",
        cta_body="Delivery to your hotel, residence, or DXB terminal. Average reservation takes 90 seconds online.",
        contact_phone="+971 4 555 7474",
        contact_email="concierge@driftdubai.ae",
        contact_address="Al Quoz Industrial 3, Dubai, UAE",
        contact_hours="Concierge 24/7 · Office Mon–Sun 8:00am – 11:00pm",
        footer_tagline="Premium car rental for people who don't have time for queues. Delivered, detailed, drama-free.",
        footer_columns=[
            ("Fleet", ["Luxury", "Sport", "Off-Road", "Long Term"]),
            ("Service", ["Delivery", "Chauffeur", "Insurance", "Wedding Cars"]),
            ("Drift", ["About", "Press", "Careers", "Locations"]),
        ],
        footer_bg="#0a0a0a",
    ),

    # 6. LAW — centered editorial hero, numbered steps, image+text about, logo cloud
    Template(
        id="law",
        name="Halverson & Reed",
        category="Law Firm",
        description="Editorial centered hero, numbered practice areas, deep navy + brass, lots of whitespace, client logo cloud.",
        niche="law_firm",
        brand="Halverson & Reed",
        initials="HR",
        primary="#1e293b",
        secondary="#334155",
        accent="#a8743d",
        bg="#f9f7f1",
        bg_surface="#ffffff",
        text="#0f172a",
        text_muted="#52525b",
        fonts=("'Cormorant Garamond', serif", "'Inter', sans-serif", "Cormorant+Garamond:wght@500;600;700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="center",
        services_layout="feature_steps",
        about_layout="feature_split",
        gallery_layout="logo_cloud",
        button_shape="rounded",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,7vw,5.5rem);font-weight:600;letter-spacing:-0.025em;}
        .section-title{font-family:var(--font-heading);font-weight:600;}
        .hero-center{padding:13rem 0 7rem;}
        section[data-section-type]{padding:7rem 0;}
        .step-num{font-weight:600;}
        """,
        hero_title="Counsel for what matters most.",
        hero_kicker="A BOUTIQUE LAW FIRM SINCE 1998",
        hero_subtitle="Halverson & Reed represents founders, families, and institutions when the stakes won't allow for a near-miss. Discreet, prepared, and unafraid of the courtroom.",
        hero_image="",
        hero_cta_primary="Request a consultation",
        hero_cta_secondary="Practice areas",
        hero_trust="Recognised by Chambers Global · 26 years in practice · 14 partners across two offices",
        services_label="OUR PROCESS",
        services_title="How we work with you",
        services_subtitle="Four steps from first call to outcome. No mystery, no surprises.",
        services=[
            ("", "First Call", "A 30-minute confidential conversation to understand your matter. We tell you whether we can help — and what we'd charge if we can."),
            ("", "Discovery", "We review every document, interview every witness, and map every contingency. Preparation is the only variable we control."),
            ("", "Strategy", "A written legal strategy approved by you before any action. You always know what we're doing and why."),
            ("", "Outcome", "Whether we settle, mediate, or fight in court — we handle it end to end. You'll never wonder where things stand."),
        ],
        about_label="THE FIRM",
        about_title="Twenty-six years. Two principles.",
        about_body="Halverson & Reed was founded in 1998 by two former Magic Circle partners who wanted to build a firm where senior lawyers actually do the work. We don't take more clients than we can serve well.",
        about_image="https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=1000&h=800&fit=crop",
        about_bullets=[
            "14 partners — every matter led by one of them",
            "Offices in Dubai (DIFC) and London (Mayfair)",
            "Chambers Global Band 1 — Litigation",
            "97% client retention over the past 5 years",
        ],
        gallery_label="REPRESENTATIVE CLIENTS",
        gallery_title="Some of the institutions we've served",
        logos=["Mansoori Holdings", "Lenz Group", "Atlas Capital", "Bellevue Bank", "Halcyon Aero", "Vinland Trust", "Marigold Estates", "Northgate Industries"],
        testimonials_label="CLIENTS",
        testimonials_title="In their words",
        testimonials=[
            ("Halverson & Reed are the lawyers we call when something must not go wrong. They've never let us down.", "Khalid Al-Mansoori", "CEO, Mansoori Holdings"),
            ("Calm, prepared, and incredibly direct. The opposing side underestimated them once — never again.", "Vanessa Hartmann", "General Counsel, Lenz Group"),
            ("They handled our family trust restructuring with the kind of discretion you can't price.", "Anonymous", "Private client"),
        ],
        cta_title="Request a confidential consultation",
        cta_body="A 30-minute call to understand your matter and let you know whether we can help — and what we'd charge if we can.",
        contact_phone="+971 4 360 8800",
        contact_email="enquiries@halverson-reed.com",
        contact_address="Gate Village 6, DIFC, Dubai · 12 Charles St, Mayfair, London",
        contact_hours="Mon–Fri · 9:00am – 6:00pm GST/GMT",
        footer_tagline="A boutique law firm representing founders, families and institutions. Senior partners only. Two offices. One standard.",
        footer_columns=[
            ("Practice", ["Litigation", "M&A", "Family & Trusts", "Regulatory"]),
            ("Firm", ["Partners", "Offices", "Press", "Careers"]),
            ("Contact", ["Dubai", "London", "Confidential Form", "Privacy"]),
        ],
        footer_bg="#0f172a",
    ),

    # 7. REAL ESTATE — full-bleed estate hero, image-card properties, stats row, 4-col gallery
    Template(
        id="real_estate",
        name="Atelier Estates",
        category="Real Estate",
        description="Full-bleed hero, properties shown as image cards, market stats, dense 4-col property gallery.",
        niche="real_estate",
        brand="Atelier Estates",
        initials="AE",
        primary="#0f3a2e",
        secondary="#1c5a48",
        accent="#bd8b3a",
        bg="#f4f1eb",
        bg_surface="#ffffff",
        text="#0e1f1a",
        text_muted="#5e6a64",
        fonts=("'Cormorant Garamond', serif", "'Manrope', sans-serif", "Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@300;400;500;600;700"),
        hero_layout="full_image",
        services_layout="feature_cards",
        about_layout="stats_row",
        gallery_layout="gallery_grid_4",
        button_shape="rounded",
        navbar_style="dark",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,7vw,5.5rem);font-weight:600;letter-spacing:-0.025em;}
        .section-title{font-family:var(--font-heading);font-weight:600;}
        .image-card{border-radius:8px;}
        .image-card-img{border-radius:8px 8px 0 0;height:280px;}
        """,
        hero_title="Homes worth crossing oceans for.",
        hero_kicker="LUXURY PROPERTIES · DUBAI · LONDON · LISBON",
        hero_subtitle="Atelier Estates curates a small portfolio of villas, penthouses, and waterfront residences. We don't list properties we wouldn't live in ourselves.",
        hero_image="https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200&h=1500&fit=crop",
        hero_bg_image="https://images.unsplash.com/photo-1613977257363-707ba9348227?w=1800&h=1200&fit=crop",
        hero_cta_primary="Request a viewing",
        hero_cta_secondary="See current listings",
        hero_trust="✦ AED 4.2B sold in 2025 · 80+ off-market exclusives · Founded 2011",
        services_label="HOW WE WORK",
        services_title="A different kind of agency",
        services_subtitle="No volume targets, no spam viewings, no pressure. Just three things, done properly.",
        services=[
            ("fa-house-chimney", "Curated Listings", "We list 30–40 homes a year — not 4,000. Every one is photographed, filmed, and priced by people who know the asset."),
            ("fa-key", "Buyer Representation", "We work for the buyer — not the listing. Off-market access, neighbourhood expertise, and a hard line on price."),
            ("fa-chart-line", "Investment Advisory", "Yield analysis, exit planning, and quiet introductions to managers who actually return calls."),
        ],
        services_images=[
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=900&h=700&fit=crop",
        ],
        about_label="THE NUMBERS",
        about_title="Selective by design",
        about_body="Why a small agency outperforms a big one when the property is worth getting right.",
        about_stats=[
            ("AED 4.2B", "TRANSACTED 2025", "Across the three cities"),
            ("30–40", "LISTINGS / YEAR", "We turn down most"),
            ("80+", "OFF-MARKET HOMES", "Available at any time"),
            ("9 yr", "AVG ADVISOR TENURE", "On the ground"),
        ],
        gallery_label="CURRENT EXCLUSIVES",
        gallery_title="A small selection from this month",
        gallery_images=[
            "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1592595896616-c37162298647?w=900&h=700&fit=crop",
        ],
        testimonials_label="BUYERS & SELLERS",
        testimonials_title="What our clients say",
        testimonials=[
            ("Atelier showed us a villa that wasn't even on the market yet. Three weeks later it was ours, and at the right price.", "Hannah Reyes", "Bought in Emirates Hills"),
            ("They sold our place in eleven days for the asking price. Their photographer alone is worth the call.", "Daniel Voss", "Sold in Palm Jumeirah"),
            ("After a decade of bad agents, finally one who picks up the phone and tells you the truth.", "Maya Sharma", "Buyer, Downtown Dubai"),
        ],
        cta_title="Looking for somewhere quieter to live?",
        cta_body="Tell us your budget and what you actually want. We'll show you three things — not thirty — and none of them by accident.",
        contact_phone="+971 4 555 1188",
        contact_email="advisors@atelier-estates.ae",
        contact_address="Al Wasl Tower, Sheikh Zayed Road, Dubai, UAE",
        contact_hours="Daily · 9:00am – 8:00pm · Viewings by appointment",
        footer_tagline="A small agency for serious homes. Curated listings, honest pricing, and the long view.",
        footer_columns=[
            ("Listings", ["Villas", "Penthouses", "Off-Market", "International"]),
            ("Services", ["Buy", "Sell", "Invest", "Concierge"]),
            ("Atelier", ["About", "Advisors", "Press", "Privacy"]),
        ],
        footer_bg="#0e1f1a",
    ),

    # 8. HEALTHCARE — split portrait hero, card grid services, image+text about, 3-col gallery, soft palette
    Template(
        id="healthcare",
        name="Lumen Clinic",
        category="Healthcare",
        description="Soft split hero with clinical portrait, card grid services, light teal palette, friendly and clean.",
        niche="dentist",
        brand="Lumen Clinic",
        initials="LC",
        primary="#0e7490",
        secondary="#0891b2",
        accent="#5eead4",
        bg="#f0fdfa",
        bg_surface="#ffffff",
        text="#0f1a1d",
        text_muted="#4b5563",
        fonts=("'Lora', serif", "'Inter', sans-serif", "Lora:wght@500;600;700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="split",
        services_layout="card_grid",
        about_layout="feature_split",
        gallery_layout="gallery_grid_3",
        button_shape="pill",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-weight:600;}
        .icon-box{border-radius:50%;width:4rem;height:4rem;}
        .card{border-radius:24px;}
        .image-card{border-radius:24px;}
        """,
        hero_title="Healthcare, the way it should feel.",
        hero_kicker="GENERAL PRACTICE · PEDIATRICS · WELLNESS",
        hero_subtitle="Lumen Clinic is a modern multi-specialty clinic in Dubai. Same-day appointments, board-certified doctors, and 30-minute consults — because rushed care isn't care.",
        hero_image="https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1200&h=1500&fit=crop",
        hero_cta_primary="Book an appointment",
        hero_cta_secondary="Meet the doctors",
        hero_trust="🩺 12,000+ patients served · Insurance accepted: AXA, Daman, Cigna, Aetna",
        services_label="OUR SPECIALTIES",
        services_title="Care across the family",
        services_subtitle="A small, deliberate set of specialties — done by senior consultants, supported by modern diagnostics.",
        services=[
            ("fa-stethoscope", "General Practice", "Adult medicine, preventive screening, chronic-condition management. Same-day for urgent matters."),
            ("fa-baby", "Pediatrics", "Newborn to teen, with consultants who actually like talking to children. Vaccinations, growth tracking, second opinions."),
            ("fa-spa", "Wellness & Diagnostics", "Annual health checks, bloodwork on-site, lifestyle medicine, and a dietitian on the team."),
        ],
        about_label="THE CLINIC",
        about_title="Built around the 30-minute consult",
        about_body="Lumen was founded by three doctors who were tired of seven-minute slots. Our consultations are scheduled at 30 minutes minimum, our waiting room never holds more than four people, and our results land in your phone within hours, not days.",
        about_image="https://images.unsplash.com/photo-1582750433449-648ed127bb54?w=1000&h=800&fit=crop",
        about_bullets=[
            "30-minute consults — minimum, not maximum",
            "On-site lab and imaging — same-day results",
            "Insurance direct billing for major networks",
            "DHA-licensed, JCI-aligned protocols",
        ],
        gallery_label="THE PRACTICE",
        gallery_title="Inside Lumen",
        gallery_images=[
            "https://images.unsplash.com/photo-1551601651-2a8555f1a136?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1631815589968-fdb09a223b1e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1666214280391-8ff5bd3c0bf0?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1666214280557-f1b5022eb634?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=900&h=700&fit=crop",
        ],
        testimonials_label="PATIENT VOICES",
        testimonials_title="From our patients",
        testimonials=[
            ("First doctor in years who actually listened. I left with a plan, not just a prescription.", "Reema A.", "Patient since 2024"),
            ("My kids hate clinics. They asked when we're going back to Lumen. That's a first.", "Marco F.", "Father of three"),
            ("Walked in for a scan, walked out two hours later with the report and a clear next step.", "Dr. Sarah K.", "Patient and physician"),
        ],
        cta_title="Book your first appointment",
        cta_body="New patient registration takes 90 seconds. We'll email you the intake form and confirm within an hour.",
        contact_phone="+971 4 433 2299",
        contact_email="reception@lumen-clinic.ae",
        contact_address="Bay Square Building 12, Business Bay, Dubai",
        contact_hours="Sat–Thu · 8:00am – 8:00pm · Fri 9:00am – 1:00pm",
        footer_tagline="A modern clinic built around the 30-minute consult. Senior doctors, real conversations, same-day care.",
        footer_columns=[
            ("Care", ["General Practice", "Pediatrics", "Wellness", "Lab & Imaging"]),
            ("Visit", ["Book Online", "Insurance", "Location", "FAQ"]),
            ("Lumen", ["About", "Doctors", "Careers", "Privacy"]),
        ],
        footer_bg="#0f1a1d",
    ),

    # 9. CREATIVE STUDIO — bold typographic centered hero, numbered process, stats row, 4-col gallery
    Template(
        id="creative_studio",
        name="Studio Mira",
        category="Creative Studio",
        description="Bold typographic hero with no image, numbered process, dense 4-col project gallery, square buttons, vibrant colors.",
        niche="portfolio",
        brand="Studio Mira",
        initials="SM",
        primary="#7c3aed",
        secondary="#a855f7",
        accent="#fb923c",
        bg="#fdf6ff",
        bg_surface="#ffffff",
        text="#1a0a2e",
        text_muted="#6b6480",
        fonts=("'Syne', sans-serif", "'Manrope', sans-serif", "Syne:wght@500;600;700;800&family=Manrope:wght@300;400;500;600;700"),
        hero_layout="center",
        services_layout="feature_steps",
        about_layout="stats_row",
        gallery_layout="gallery_grid_4",
        button_shape="square",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,9vw,7rem);font-weight:800;letter-spacing:-0.04em;line-height:0.95;}
        .section-title{font-family:var(--font-heading);font-weight:800;letter-spacing:-0.02em;}
        .hero-center{padding:14rem 0 7rem;}
        .step-num{font-family:var(--font-heading);font-weight:800;color:var(--accent);}
        .stat-number{color:var(--primary);}
        """,
        hero_title="Brands worth a second glance.",
        hero_kicker="BRAND · IDENTITY · DIGITAL",
        hero_subtitle="Studio Mira is a six-person creative studio in Dubai. We work with founders who care about taste, and don't have time to brief seven freelancers to get there.",
        hero_image="",
        hero_cta_primary="Start a project",
        hero_cta_secondary="See our work",
        hero_trust="✦ Awwwards Site of the Day × 4 · D&AD Wood Pencil 2025 · 80+ brands launched",
        services_label="OUR PROCESS",
        services_title="Three things, all the way down",
        services_subtitle="We don't do everything — we do brand, identity and digital, and we do them very, very well.",
        services=[
            ("", "Brand Strategy", "Naming, positioning, voice, and the long-form story behind it. Two-week intensives — no 80-page PDFs that nobody reads."),
            ("", "Visual Identity", "Logos, type systems, colour, and a brand book your team will actually open. Built for the long run, not the next pitch."),
            ("", "Digital Design", "Websites, product UI, and launch campaigns. Designed and built — never handed off to someone else's developers."),
        ],
        about_label="BY THE NUMBERS",
        about_title="A studio built for depth",
        about_body="Why six people and four-week sprints beat a hundred-person agency every time.",
        about_stats=[
            ("6", "PEOPLE TOTAL", "Senior partners on every project"),
            ("14", "PROJECTS / YEAR", "Total. We turn down most."),
            ("4×", "AWWWARDS SOTD", "In 2025 alone"),
            ("80+", "BRANDS LAUNCHED", "Across MENA, EU and US"),
        ],
        gallery_label="SELECTED WORK",
        gallery_title="Recent projects",
        gallery_images=[
            "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1561070791-32e95fcb1eb1?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1626785774573-4b799315345d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1558655146-9f40138edfeb?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1561070791-2526d30994b8?w=900&h=700&fit=crop",
        ],
        testimonials_label="CLIENT WORDS",
        testimonials_title="From people we've worked with",
        testimonials=[
            ("Studio Mira gave us the only brand book we've ever actually used. Two years on, we still open it.", "Diana Tan", "Founder, Bloom Beauty"),
            ("They turned down our first brief and proposed a better one. We made them lead the whole launch.", "Omar Saleh", "CEO, Yalla Eats"),
            ("They care more about our brand than we do — and we care a lot. That's what you want.", "Nina Petrova", "CMO, Lyra Audio"),
        ],
        cta_title="Got a brief in your head?",
        cta_body="Book a 30-minute call. We'll either love it, or tell you exactly which studio to call instead.",
        contact_phone="+971 4 388 4422",
        contact_email="hello@studiomira.co",
        contact_address="Alserkal Avenue, Al Quoz, Dubai",
        contact_hours="Mon–Fri · 10:00am – 6:00pm",
        footer_tagline="A six-person creative studio. Brand, identity, digital — done properly, the long way.",
        footer_columns=[
            ("Work", ["Selected Projects", "Brands", "Clients", "Process"]),
            ("Studio", ["About", "Approach", "Press", "Careers"]),
            ("Contact", ["Start a Project", "Hello", "Newsletter", "Instagram"]),
        ],
        footer_bg="#1a0a2e",
    ),

    # 10. BEAUTY SPA — asymmetric editorial hero, image-card service menu, image+text about, 3-col gallery, pill buttons
    Template(
        id="beauty_spa",
        name="Saskia & Co.",
        category="Beauty & Spa",
        description="Editorial asymmetric hero (image-left), image-card treatment menu, dusty rose palette, pill buttons.",
        niche="beauty_salon",
        brand="Saskia & Co.",
        initials="S",
        primary="#b8678c",
        secondary="#d49ab0",
        accent="#a8743d",
        bg="#fdf6f3",
        bg_surface="#ffffff",
        text="#1a0f12",
        text_muted="#6b5560",
        fonts=("'DM Serif Display', serif", "'Outfit', sans-serif", "DM+Serif+Display&family=Outfit:wght@300;400;500;600;700"),
        hero_layout="asymmetric",
        services_layout="feature_cards",
        about_layout="feature_split",
        gallery_layout="gallery_grid_3",
        button_shape="pill",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-weight:400;font-size:clamp(2.8rem,6vw,4.5rem);}
        .section-title{font-family:var(--font-heading);font-weight:400;}
        .image-card{border-radius:24px;}
        .image-card-img{border-radius:24px 24px 0 0;}
        .card{border-radius:24px;}
        """,
        hero_title="An hour for you, and only you.",
        hero_kicker="HAIR · SKIN · NAILS · WELLNESS",
        hero_subtitle="Saskia & Co. is a private beauty atelier in Jumeirah. Six rooms, six specialists, no rushing. The kind of beauty appointment you actually want to look forward to.",
        hero_image="https://images.unsplash.com/photo-1560750588-73207b1ef5b8?w=1200&h=1500&fit=crop",
        hero_cta_primary="Book a session",
        hero_cta_secondary="View the menu",
        hero_trust="✦ 5★ on Google · 800+ regulars · Founded 2018 · Discreet, private, never rushed",
        services_label="THE MENU",
        services_title="What we do",
        services_subtitle="A short, considered menu of treatments. Each booking is a private room, your specialist, and never less than an hour.",
        services=[
            ("fa-scissors", "Hair Atelier", "Cuts, colour, balayage, and treatments by senior stylists. Olaplex and Davines only — no bargain-bin chemicals."),
            ("fa-spa", "Skin & Facials", "Bespoke facials, dermaplaning, and hydration treatments. Every regimen designed around your skin, not a leaflet."),
            ("fa-hand-sparkles", "Nails & Wellness", "Gel and dip manicures, spa pedicures, and add-on hand massages. Private rooms, no shared tables."),
        ],
        services_images=[
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1604654894610-df63bc536371?w=900&h=700&fit=crop",
        ],
        about_label="OUR PHILOSOPHY",
        about_title="Beauty without the rush",
        about_body="Saskia opened the atelier in 2018 because she couldn't find a salon that didn't feel like a conveyor belt. Every appointment here is private, every product is hand-picked, and your specialist sees one client at a time — the way it used to be done.",
        about_image="https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=1000&h=800&fit=crop",
        about_bullets=[
            "Six private treatment rooms — no shared spaces",
            "Senior specialists only — average 8 years experience",
            "Davines, Olaplex, Biologique Recherche, Augustinus Bader",
            "Walk-in coffee bar with herbal blends and matcha",
        ],
        gallery_label="THE ATELIER",
        gallery_title="Inside the rooms",
        gallery_images=[
            "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1633681926022-84c23e8cb2d6?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1600334129128-685c5582fd35?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1571646034647-52e6ea84b28c?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1519415943484-9fa1873496d4?w=900&h=700&fit=crop",
        ],
        testimonials_label="REGULAR LOVE",
        testimonials_title="From our regulars",
        testimonials=[
            ("Best balayage I've ever had — and I've had a lot. The room felt like a holiday, not a salon.", "Lila Hadid", "Regular since 2022"),
            ("My facials at Saskia have completely changed my skin. I won't go anywhere else.", "Ines Marchetti", "Regular since 2021"),
            ("It's the only place where I leave actually relaxed. No conveyor belt energy.", "Maya Brennan", "Bride, 2025"),
        ],
        cta_title="Book a private appointment",
        cta_body="Saturdays book up two weeks ahead — weekday slots are usually open within 48 hours.",
        contact_phone="+971 4 344 7700",
        contact_email="hello@saskia-co.ae",
        contact_address="Jumeirah Beach Road 248, Jumeirah 1, Dubai",
        contact_hours="Tue–Sun · 10:00am – 8:00pm · Closed Mondays",
        footer_tagline="A private beauty atelier in Jumeirah. Six rooms, six specialists, never rushed.",
        footer_columns=[
            ("Treatments", ["Hair Atelier", "Facials", "Nails", "Wellness"]),
            ("Atelier", ["About", "Our Team", "Press", "Gift Cards"]),
            ("Visit", ["Book", "Location", "Newsletter", "Instagram"]),
        ],
        footer_bg="#1a0f12",
    ),

    # 11. FITNESS GYM — neon-green on black, full-image hero, pill buttons
    Template(
        id="fitness_gym",
        name="Ironhaus Strength Club",
        category="Fitness & Gym",
        description="High-energy strength gym template — full-bleed hero, card grid services, stats row, neon-green accents on black.",
        niche="fitness",
        brand="Ironhaus",
        initials="I",
        primary="#a3e635",
        secondary="#65a30d",
        accent="#fde047",
        bg="#0a0a0a",
        bg_surface="#141414",
        text="#f5f5f5",
        text_muted="#a3a3a3",
        fonts=("'Oswald', sans-serif", "'Inter', sans-serif", "Oswald:wght@500;600;700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="full_image",
        services_layout="card_grid",
        about_layout="stats_row",
        gallery_layout="gallery_grid_3",
        button_shape="pill",
        navbar_style="dark",
        extra_css="""
        .nav-brand,.nav-links a{color:#f5f5f5;}
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3.2rem,8vw,6rem);text-transform:uppercase;letter-spacing:-0.01em;font-weight:700;}
        .section-title{font-family:var(--font-heading);text-transform:uppercase;letter-spacing:-0.005em;}
        .section-label{color:var(--primary);}
        .card{background:rgba(255,255,255,0.04);border:1px solid rgba(163,230,53,0.2);}
        .card:hover{border-color:var(--primary);transform:translateY(-4px);}
        .stat-number{color:var(--primary);font-family:var(--font-heading);font-size:clamp(2.8rem,5vw,4rem);}
        .testimonial-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);}
        .image-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);}
        .form-input{background:rgba(255,255,255,0.04);border-color:rgba(255,255,255,0.1);color:#f5f5f5;}
        section[data-section-type="card_grid"],section[data-section-type="stats_row"]{background:#111111;}
        .btn-primary{background:var(--primary);color:#0a0a0a;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;}
        .btn-primary:hover{box-shadow:0 0 0 4px rgba(163,230,53,0.25);}
        .btn-secondary{border-color:var(--primary);color:var(--primary);}
        """,
        hero_title="Train like you mean it.",
        hero_kicker="STRENGTH · CONDITIONING · COMMUNITY",
        hero_subtitle="No mirrors. No gimmicks. Two floors of platforms, racks, and coaches who actually know the difference between a good set and a wasted one.",
        hero_image="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1200&h=1400&fit=crop",
        hero_bg_image="https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1800&h=1200&fit=crop",
        hero_cta_primary="Book a trial session",
        hero_cta_secondary="See the gym",
        hero_trust="Open 5am–11pm · 4,800 sqft · 14 coaches · Since 2018",
        services_label="WHAT WE OFFER",
        services_title="Built for serious work",
        services_subtitle="Four programs, one standard. We build athletes, not aesthetics.",
        services=[
            ("fa-dumbbell", "Strength Block", "12-week periodized programs on the main platforms. Squat, bench, deadlift, overhead — logged and coached every session."),
            ("fa-fire", "Metcon Classes", "Group conditioning capped at 14 lifters. Barbell + kettlebell intervals designed to move real loads, not just elevate heart rate."),
            ("fa-user-group", "1-on-1 Coaching", "Weekly sessions with a senior coach: technique, programming, nutrition, and check-ins between. Six-month minimum."),
            ("fa-medal", "Competition Prep", "For powerlifting and strongman athletes peaking for a meet. Attempt selection, cut management, warm-up timing — we handle the details."),
        ],
        about_label="THE FLOOR",
        about_title="Three thousand members. Zero excuses.",
        about_body="Ironhaus was founded by two former national lifters who got tired of commercial gyms charging for Wi-Fi and calling it strength training.",
        about_stats=[
            ("3,200", "MEMBERS", "Across three floors in Dubai Design District"),
            ("14", "COACHES", "All certified, all actively competing"),
            ("24", "PLATFORMS", "Eleven squat racks, four comp platforms"),
            ("7", "YEARS", "Building Dubai's strongest community"),
        ],
        gallery_label="THE SPACE",
        gallery_title="Inside the gym",
        gallery_images=[
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1534258936925-c58bed479fcb?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1540497077202-7c8a3999166f?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1594381898411-846e7d193883?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1526506118085-60ce8714f8c5?w=900&h=700&fit=crop",
        ],
        testimonials_label="MEMBERS",
        testimonials_title="What our lifters say",
        testimonials=[
            ("Added 40kg to my deadlift in 18 months. The coaches actually coach — not just count reps.", "Omar Khalil", "Member since 2023"),
            ("I was nervous walking into a 'serious' gym. The culture here is welcoming without ever being soft.", "Priya Chandran", "First-time lifter"),
            ("Best strength coaching in the city. Full stop.", "Luka Novak", "Powerlifter, national team"),
        ],
        cta_title="Come train with us.",
        cta_body="Free trial session for new members — 90 minutes with a coach, full gym access, no pitch.",
        contact_phone="+971 4 512 8800",
        contact_email="train@ironhaus.ae",
        contact_address="Warehouse 22, Dubai Design District",
        contact_hours="Mon–Fri · 5am–11pm · Sat–Sun · 7am–9pm",
        footer_tagline="Dubai's serious strength gym. Two floors, fourteen coaches, zero nonsense.",
        footer_columns=[
            ("Train", ["Classes", "1-on-1 Coaching", "Comp Prep", "Programs"]),
            ("Ironhaus", ["About", "The Coaches", "Membership", "Press"]),
            ("Visit", ["Book a Trial", "Location", "Hours", "Newsletter"]),
        ],
        footer_bg="#0a0a0a",
    ),

    # 12. WEDDING PLANNER — asymmetric hero, feature cards, blush/gold, elegant serif
    Template(
        id="wedding_planner",
        name="Amélie & Wren Weddings",
        category="Wedding Planner",
        description="Elegant wedding planning template — asymmetric hero with floating couple photo, feature cards services, soft blush and gold palette.",
        niche="wedding_planner",
        brand="Amélie & Wren",
        initials="A",
        primary="#c97b84",
        secondary="#a8613c",
        accent="#bfa66b",
        bg="#fdf8f5",
        bg_surface="#ffffff",
        text="#1f1612",
        text_muted="#78625a",
        fonts=("'Cormorant Garamond', serif", "'Montserrat', sans-serif", "Cormorant+Garamond:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700"),
        hero_layout="asymmetric",
        services_layout="feature_cards",
        about_layout="feature_split",
        gallery_layout="gallery_grid_3",
        button_shape="rounded",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-weight:500;font-size:clamp(3rem,7vw,5.8rem);font-style:italic;letter-spacing:-0.02em;}
        .section-title{font-family:var(--font-heading);font-weight:500;font-style:italic;}
        .hero-heading em, .section-title em{font-style:normal;color:var(--accent);}
        .section-label{color:var(--primary);letter-spacing:0.35em;}
        .card,.image-card{box-shadow:0 8px 40px rgba(201,123,132,0.08);}
        section[data-section-type="card_grid"],section[data-section-type="feature_cards"]{background:#fbf2ee;}
        .btn-primary{background:var(--primary);letter-spacing:0.05em;text-transform:uppercase;font-size:0.8rem;font-weight:600;}
        .btn-primary:hover{background:var(--secondary);}
        """,
        hero_title="Every detail, quietly loved.",
        hero_kicker="FULL-SERVICE WEDDING PLANNING",
        hero_subtitle="We design weddings the way your favourite love story was written — slowly, deliberately, and entirely about the two of you.",
        hero_image="https://images.unsplash.com/photo-1519741497674-611481863552?w=1100&h=1400&fit=crop",
        hero_cta_primary="Start your consultation",
        hero_cta_secondary="See our weddings",
        hero_trust="Featured in Vogue, Brides, and Harper's Bazaar · Planning weddings since 2016",
        services_label="WHAT WE DO",
        services_title="Three ways to work together",
        services_subtitle="From full-service planning to month-of coordination — we meet you where you need us.",
        services=[
            ("fa-heart", "Full-Service Planning", "Twelve months of planning, from venue search to the last dance. Vendor curation, design direction, weekend coordination — everything handled."),
            ("fa-calendar-check", "Partial Planning", "You've booked the venue and vibe. We step in at month four to refine design, manage vendors, and run the wedding week."),
            ("fa-compass", "Month-of Coordination", "You planned it all yourselves — we make sure it actually runs. Four weeks of handovers, timelines, and flawless day-of execution."),
        ],
        services_images=[
            "https://images.unsplash.com/photo-1519741497674-611481863552?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1464207687429-7505649dae38?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1520854221256-17451cc331bf?w=900&h=700&fit=crop",
        ],
        about_label="THE TEAM",
        about_title="Two planners. One obsession.",
        about_body="Amélie and Wren met planning a friend's vineyard wedding in 2016 and never looked back. Today we plan 18 weddings a year — by choice — so every couple gets our full attention.",
        about_image="https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=1000&h=1100&fit=crop",
        about_bullets=[
            "18 weddings a year, never more — capacity is a design choice",
            "Full creative direction from mood boards to stationery",
            "A vetted network of 40+ vendors across the UAE and Europe",
            "Destination weddings in France, Italy, Greece and the Maldives",
        ],
        gallery_label="PAST WEDDINGS",
        gallery_title="Love stories we've told",
        gallery_images=[
            "https://images.unsplash.com/photo-1519741497674-611481863552?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1464207687429-7505649dae38?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1520854221256-17451cc331bf?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1525258946800-98cfd641d0de?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1606800052052-a08af7148866?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=900&h=700&fit=crop",
        ],
        testimonials_label="OUR COUPLES",
        testimonials_title="Kind words from past brides",
        testimonials=[
            ("Amélie made the most stressful year of my life feel effortless. Our vineyard wedding in Tuscany was everything we dreamed of.", "Emma & James", "Married in Montepulciano, 2024"),
            ("The attention to detail is unreal. Every guest still brings up how thoughtful the evening felt.", "Layla & Nour", "Dubai Hills wedding, 2024"),
            ("We came to Wren with a vague vision and a tight timeline. She delivered something better than we imagined.", "Isabella & Matteo", "Maldives elopement, 2023"),
        ],
        cta_title="Let's tell your story.",
        cta_body="Consultations are free and take about 45 minutes. Bring your Pinterest boards — we'll handle the rest.",
        contact_phone="+971 4 344 2200",
        contact_email="hello@amelieandwren.com",
        contact_address="Alserkal Avenue, Al Quoz, Dubai",
        contact_hours="Tue–Sat · 10am – 6pm · Consultations by appointment",
        footer_tagline="An intimate wedding planning studio based in Dubai and Provence. Eighteen weddings a year, every one loved.",
        footer_columns=[
            ("Services", ["Full Planning", "Partial Planning", "Coordination", "Destination"]),
            ("Studio", ["About Us", "Our Couples", "Press", "Journal"]),
            ("Visit", ["Consultation", "Vendors", "Location", "Instagram"]),
        ],
        footer_bg="#1f1612",
    ),

    # 13. ARCHITECTURE FIRM — centered editorial, square buttons, charcoal/sand, minimal
    Template(
        id="architecture_firm",
        name="Meridian & Stone Architects",
        category="Architecture",
        description="Minimal editorial architecture studio — centered hero, no images up top, dense 4-column project grid, charcoal and warm sand palette.",
        niche="architecture",
        brand="Meridian & Stone",
        initials="M",
        primary="#2a2a2a",
        secondary="#525252",
        accent="#b8925a",
        bg="#f2efe9",
        bg_surface="#ffffff",
        text="#1a1a1a",
        text_muted="#6b6863",
        fonts=("'Syne', sans-serif", "'Inter', sans-serif", "Syne:wght@500;600;700;800&family=Inter:wght@300;400;500;600;700"),
        hero_layout="center",
        services_layout="card_grid",
        about_layout="feature_split",
        gallery_layout="gallery_grid_4",
        button_shape="square",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,8vw,6.5rem);font-weight:800;letter-spacing:-0.045em;line-height:1;}
        .hero-center{padding:13rem 0 8rem;}
        .section-title{font-family:var(--font-heading);font-weight:700;letter-spacing:-0.03em;}
        .section-label{letter-spacing:0.3em;color:var(--accent);}
        section[data-section-type]{padding:7rem 0;border-top:1px solid rgba(26,26,26,0.08);}
        .card{background:var(--bg-surface);border:1px solid rgba(26,26,26,0.08);box-shadow:none;border-radius:0;}
        .card:hover{border-color:var(--accent);}
        .btn-primary{background:var(--primary);font-size:0.82rem;letter-spacing:0.1em;text-transform:uppercase;font-weight:600;}
        .btn-secondary{border-color:var(--primary);color:var(--primary);font-size:0.82rem;letter-spacing:0.1em;text-transform:uppercase;}
        .image-card{border-radius:0;}
        """,
        hero_title="Architecture is a long conversation.",
        hero_kicker="RESIDENTIAL · CULTURAL · COMMERCIAL",
        hero_subtitle="We design buildings that age well — with the landscape, with the client, and with the decades that follow.",
        hero_image="",
        hero_cta_primary="See our work",
        hero_cta_secondary="About the studio",
        hero_trust="Twenty-two built projects across the GCC, India, and East Africa · Founded 2011",
        services_label="PRACTICE AREAS",
        services_title="Four disciplines, one hand",
        services_subtitle="From private villas to cultural institutions — every project, every drawing, signed off by a principal architect.",
        services=[
            ("fa-house", "Residential", "Private houses and apartment retrofits where the brief is 'we want to live here for thirty years'. Full architecture and interiors."),
            ("fa-landmark", "Cultural", "Museums, libraries, and community centres. Public buildings that earn their place on a street over time."),
            ("fa-building", "Commercial", "Boutique hotels, offices, and mixed-use buildings for clients who value craft over capital efficiency."),
            ("fa-map", "Masterplanning", "Urban strategy and campus design for developers and institutions thinking fifteen years ahead, not five."),
        ],
        about_label="THE STUDIO",
        about_title="A practice of sixteen. No leverage model.",
        about_body="We're a small studio by design. Every project is led by a principal, drawn by a senior architect, and built under our site supervision. We don't grow faster than we can keep standards.",
        about_image="https://images.unsplash.com/photo-1486304873000-235643847519?w=1000&h=1100&fit=crop",
        about_bullets=[
            "16 architects, 4 principals — every project led by a partner",
            "Two RIBA International Prize shortlists (2021, 2023)",
            "Member of the UIA and the Gulf Architects Council",
            "Studios in Dubai and Ahmedabad",
        ],
        gallery_label="SELECTED WORK",
        gallery_title="Twenty-two built projects",
        gallery_images=[
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1487958449943-2429e8be8625?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1496307653780-42ee777d4833?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1449844908441-8829872d2607?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1460574283810-2aab119d8511?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1464146072230-91cabc968266?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=900&h=700&fit=crop",
        ],
        testimonials_label="CLIENTS",
        testimonials_title="What our clients say",
        testimonials=[
            ("They understood our land better than we did. The house feels inevitable — as if it had always been there.", "Farah Khoury", "Private client, Lebanon"),
            ("The finished library is exactly what the community needed — and nothing it didn't.", "Dr Anand Raghavan", "Director, Bombay Public Library Trust"),
            ("A rare firm that says no when the brief is wrong. We listen when they do.", "Sheikh Rashid Al Mansouri", "Board Chair, Gulf Cultural Foundation"),
        ],
        cta_title="Start a project conversation.",
        cta_body="We take on eight new projects a year. Initial conversations are informal — send us the brief and we'll reply within the week.",
        contact_phone="+971 4 566 4400",
        contact_email="studio@meridianstone.com",
        contact_address="Warehouse 14, Alserkal Avenue, Dubai",
        contact_hours="Mon–Thu · 9am – 6pm · Friday by appointment",
        footer_tagline="An architecture practice of sixteen in Dubai and Ahmedabad. Buildings that age well, signed off by a partner.",
        footer_columns=[
            ("Practice", ["Residential", "Cultural", "Commercial", "Masterplanning"]),
            ("Studio", ["About", "Team", "Press", "Awards"]),
            ("Contact", ["Start a Project", "Locations", "Journal", "Instagram"]),
        ],
        footer_bg="#1a1a1a",
    ),

    # 14. PHOTOGRAPHY STUDIO — full-bleed dark hero, feature steps, black + amber
    Template(
        id="photography_studio",
        name="North & Field Photography",
        category="Photography",
        description="Image-first photographer portfolio — cinematic full-bleed hero, numbered workflow, feature split about, dense 4-col gallery, amber accents on black.",
        niche="photography",
        brand="North & Field",
        initials="N",
        primary="#f59e0b",
        secondary="#d97706",
        accent="#fbbf24",
        bg="#0a0a0a",
        bg_surface="#1a1a1a",
        text="#f5f5f4",
        text_muted="#a8a29e",
        fonts=("'Archivo Black', sans-serif", "'Inter', sans-serif", "Archivo+Black&family=Inter:wght@300;400;500;600;700"),
        hero_layout="full_image",
        services_layout="feature_steps",
        about_layout="feature_split",
        gallery_layout="gallery_grid_4",
        button_shape="rounded",
        navbar_style="dark",
        extra_css="""
        .nav-brand,.nav-links a{color:#f5f5f4;}
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3.2rem,9vw,7rem);font-weight:900;letter-spacing:-0.03em;line-height:0.95;text-transform:uppercase;}
        .section-title{font-family:var(--font-heading);text-transform:uppercase;letter-spacing:-0.015em;}
        .section-label{color:var(--accent);}
        section[data-section-type]{background:#0a0a0a;}
        section[data-section-type="feature_steps"],section[data-section-type="testimonial_cards"]{background:#141414;}
        .step-number{color:var(--accent);font-family:var(--font-heading);font-size:4rem;opacity:0.3;}
        .card,.testimonial-card,.image-card,.contact-info-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);}
        .form-input{background:rgba(255,255,255,0.04);border-color:rgba(255,255,255,0.1);color:#f5f5f4;}
        .btn-primary{background:var(--primary);color:#0a0a0a;}
        .btn-secondary{border-color:var(--primary);color:var(--primary);}
        """,
        hero_title="Light. Story. Stillness.",
        hero_kicker="EDITORIAL · FASHION · DOCUMENTARY",
        hero_subtitle="A quiet photography studio shooting cinematic editorial work for magazines, brands, and the occasional very patient private commission.",
        hero_image="https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1200&h=1500&fit=crop",
        hero_bg_image="https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1800&h=1200&fit=crop",
        hero_cta_primary="See the portfolio",
        hero_cta_secondary="Commission a shoot",
        hero_trust="Recent work for Vogue Arabia, Kinfolk, Monocle, and The New York Times T Magazine",
        services_label="HOW WE SHOOT",
        services_title="A considered workflow",
        services_subtitle="We don't do quick turnarounds. Every shoot starts with a conversation and ends with prints you'll want to frame.",
        services=[
            ("", "Concept Call", "A 60-minute conversation to understand what you want to say — not just what you want to photograph. Reference images welcome."),
            ("", "Pre-Production", "Location scouting, styling, and lighting plans. For editorial work we partner with stylists, prop masters, and producers we've worked with for years."),
            ("", "The Shoot", "Calm, slow, and deliberate. Usually a single day for editorial, up to five for campaigns. We shoot on film and digital, depending on the story."),
            ("", "Delivery", "Edited selects within ten days, final retouched images within four weeks. Prints and books available for all commissions."),
        ],
        about_label="THE STUDIO",
        about_title="Shot on four cameras. Built on patience.",
        about_body="North & Field is a two-person studio: Laila on camera, Oren producing. Between us, we've been making pictures for fifteen years — for magazines, brands, and private clients who share our patience.",
        about_image="https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=1000&h=1100&fit=crop",
        about_bullets=[
            "Published in Vogue Arabia, Kinfolk, Monocle, T Magazine",
            "Shortlisted for the Sony World Photography Awards (2022, 2024)",
            "Campaigns for Hermès, Aesop, and The Standard Hotels",
            "Film and darkroom work still a core part of our practice",
        ],
        gallery_label="SELECTED WORK",
        gallery_title="From the archives",
        gallery_images=[
            "https://images.unsplash.com/photo-1502680390469-be75c86b636f?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1511367461989-f85a21fda167?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1519682337058-a94d519337bc?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1488376739367-9ed1d6fcb5f4?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1504214208698-ea1916a2195a?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1517331671406-56fc5277e9ef?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=900&h=700&fit=crop",
        ],
        testimonials_label="CLIENTS",
        testimonials_title="Kind words",
        testimonials=[
            ("Laila and Oren brought a story to my jewellery line I didn't know was there. The images changed how we sold.", "Yumi Tanaka", "Founder, Yumi Studio"),
            ("The calmest shoot day I've had in a decade of editorial. And the pictures were the best we ran that year.", "Marcus Weldon", "Editor-in-chief, Kinfolk"),
            ("They photographed my mother's home in Beirut with more love than I thought possible.", "Rima Haddad", "Private commission, 2024"),
        ],
        cta_title="Commission a story.",
        cta_body="We take on six commissions a quarter. Tell us what you want to say — reply within 48 hours.",
        contact_phone="+971 50 887 4400",
        contact_email="studio@northandfield.co",
        contact_address="Studio 18, Al Quoz Creative Zone, Dubai",
        contact_hours="By appointment · We reply within 48 hours",
        footer_tagline="A two-person photography studio shooting editorial and commissioned work from Dubai and wherever the story lives.",
        footer_columns=[
            ("Work", ["Editorial", "Fashion", "Documentary", "Commissions"]),
            ("Studio", ["About", "Process", "Journal", "Archive"]),
            ("Contact", ["Commission", "Prints", "Newsletter", "Instagram"]),
        ],
        footer_bg="#0a0a0a",
    ),

    # 15. YOGA STUDIO — split hero, feature steps, stats row, sage + terracotta
    Template(
        id="yoga_studio",
        name="Still & Soft Yoga",
        category="Yoga Studio",
        description="Calming yoga studio template — split hero with nature imagery, feature steps for class journey, sage and terracotta palette, pill buttons.",
        niche="yoga_studio",
        brand="Still & Soft",
        initials="S",
        primary="#87a96b",
        secondary="#5b7a48",
        accent="#c47b4d",
        bg="#f8f5ef",
        bg_surface="#ffffff",
        text="#2a2a1f",
        text_muted="#6b6558",
        fonts=("'Fraunces', serif", "'Inter', sans-serif", "Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="split",
        services_layout="feature_steps",
        about_layout="stats_row",
        gallery_layout="gallery_grid_3",
        button_shape="pill",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-weight:500;font-size:clamp(2.8rem,6.5vw,5rem);letter-spacing:-0.02em;}
        .hero-heading em{font-style:italic;color:var(--accent);font-weight:400;}
        .section-title{font-family:var(--font-heading);font-weight:500;}
        .section-label{color:var(--accent);letter-spacing:0.3em;}
        section[data-section-type="feature_steps"],section[data-section-type="stats_row"]{background:#f1ebe0;}
        .step-number{background:var(--primary);color:white;}
        .stat-number{color:var(--primary);font-family:var(--font-heading);font-weight:600;}
        .btn-primary{background:var(--primary);font-weight:500;}
        .btn-primary:hover{background:var(--secondary);}
        """,
        hero_title="Softer mornings. Stiller minds.",
        hero_kicker="YOGA · BREATH · REST",
        hero_subtitle="A sun-filled studio in the old city where the pace is slow, the teachers are kind, and the first class is always free.",
        hero_image="https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=1100&h=1300&fit=crop",
        hero_cta_primary="Book your first class",
        hero_cta_secondary="See the schedule",
        hero_trust="Fifty classes a week · Six teachers · Unlimited membership AED 480/month",
        services_label="CLASS TYPES",
        services_title="Start where you are",
        services_subtitle="Five class styles, each taught by a senior teacher with at least a decade of practice. No prior yoga experience expected — ever.",
        services=[
            ("", "Gentle Flow", "A slow 60-minute vinyasa with plenty of rest. The class we'd send anyone new to yoga to — or anyone who needs to exhale."),
            ("", "Vinyasa", "A 75-minute dynamic flow linking breath and movement. Great for building strength, balance, and self-trust."),
            ("", "Yin & Restore", "Ninety minutes of long, supported holds. Deep tissue release, nervous system reset, and usually a short nap at the end."),
            ("", "Pranayama", "Breath work sessions rooted in traditional pranayama. Calming for beginners, profound for long-time practitioners."),
        ],
        about_label="THE STUDIO",
        about_title="Seven years. Kindness first.",
        about_body="Still & Soft opened in 2018 as a quiet alternative to fitness-style yoga. We teach the tradition, not the trend — and we welcome every body, every age, every level.",
        about_stats=[
            ("3,400", "STUDENTS", "Across our Dubai and Ras Al Khaimah studios"),
            ("50", "CLASSES / WEEK", "Yoga, pranayama, meditation, and sound baths"),
            ("6", "SENIOR TEACHERS", "All E-RYT 500 certified, all practicing 10+ years"),
            ("7", "YEARS", "Of teaching gently and deliberately"),
        ],
        gallery_label="THE SPACE",
        gallery_title="A quiet corner of the city",
        gallery_images=[
            "https://images.unsplash.com/photo-1545389336-cf090694435e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1588286840104-8957b019727f?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1575052814086-f385e2e2ad1b?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1593810450967-f9c42742e326?w=900&h=700&fit=crop",
        ],
        testimonials_label="STUDENTS",
        testimonials_title="What our students say",
        testimonials=[
            ("I came for the stretching and stayed for the community. My sleep, my temper, and my posture all quietly improved.", "Sarah Bennett", "Student since 2021"),
            ("After a neck injury I thought yoga was off the table. Amina taught me otherwise — patiently, every week.", "Rajiv Menon", "Student since 2023"),
            ("The Yin classes are extraordinary. I leave feeling ten years younger every time.", "Layla Mansour", "Founding member"),
        ],
        cta_title="Come as you are.",
        cta_body="The first class is always free. No mat? We'll lend you one. No clue where to start? Any teacher will point you to the right one.",
        contact_phone="+971 4 388 9900",
        contact_email="hello@stillandsoft.ae",
        contact_address="Off Jumeirah Beach Road, Umm Suqeim 1, Dubai",
        contact_hours="Daily · 6am – 9:30pm · Reception 8am – 7pm",
        footer_tagline="A gentle yoga studio in Umm Suqeim. Fifty classes a week, six teachers, kindness first.",
        footer_columns=[
            ("Practice", ["Schedule", "Teachers", "Workshops", "Retreats"]),
            ("Studio", ["About", "Membership", "Gift Cards", "Press"]),
            ("Visit", ["First Class", "Location", "Newsletter", "Instagram"]),
        ],
        footer_bg="#2a2a1f",
    ),

    # 16. COFFEE SHOP — asymmetric hero, card grid, cream/espresso, artisan warm
    Template(
        id="coffee_shop",
        name="Fernside Coffee Roasters",
        category="Coffee Shop",
        description="Warm artisan coffee roaster template — asymmetric hero with floating brew card, card grid services, cream and espresso palette.",
        niche="coffee_shop",
        brand="Fernside",
        initials="F",
        primary="#8b4513",
        secondary="#d2691e",
        accent="#daa520",
        bg="#faf6f0",
        bg_surface="#ffffff",
        text="#2b1d0f",
        text_muted="#6b5847",
        fonts=("'DM Serif Display', serif", "'Inter', sans-serif", "DM+Serif+Display&family=Inter:wght@300;400;500;600;700"),
        hero_layout="asymmetric",
        services_layout="card_grid",
        about_layout="feature_split",
        gallery_layout="gallery_grid_3",
        button_shape="rounded",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,7vw,5.8rem);font-weight:400;letter-spacing:-0.02em;}
        .section-title{font-family:var(--font-heading);font-weight:400;}
        .section-label{color:var(--primary);letter-spacing:0.28em;}
        section[data-section-type="card_grid"]{background:#f3ebde;}
        section[data-section-type="testimonial_cards"]{background:#f3ebde;}
        .card{background:var(--bg-surface);border:1px solid rgba(139,69,19,0.1);}
        .card:hover{border-color:var(--primary);}
        .floating-card{background:var(--bg-surface);border-color:rgba(139,69,19,0.15);}
        .btn-primary{background:var(--primary);letter-spacing:0.02em;}
        .btn-primary:hover{background:var(--secondary);}
        .btn-secondary{border-color:var(--primary);color:var(--primary);}
        """,
        hero_title="Single origin. Small roasts. Good mornings.",
        hero_kicker="SPECIALTY COFFEE · ROASTED IN DUBAI",
        hero_subtitle="A neighbourhood café and roastery sourcing directly from farms in Ethiopia, Colombia, and Panama. Coffee strong enough to stand a spoon in.",
        hero_image="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=1100&h=1400&fit=crop",
        hero_cta_primary="See this week's beans",
        hero_cta_secondary="Visit the café",
        hero_trust="Rated 4.9 on Google · Direct trade with 6 farms · Featured in Time Out Dubai",
        services_label="WHAT WE DO",
        services_title="Coffee, done properly",
        services_subtitle="From the bean to your cup — every step is ours, every decision considered.",
        services=[
            ("fa-seedling", "Direct Trade", "We source green beans directly from six farms across three continents. No middle men, no commodity pricing, fair wages at origin."),
            ("fa-fire", "Small-Batch Roasting", "Every bag is roasted within 48 hours of sale in our 5kg Probat behind the café. Nothing sits — ever."),
            ("fa-mug-hot", "The Café", "Seventy seats across two rooms, baristas who know their science, and pastries from our own kitchen. Open daily."),
            ("fa-box", "Subscriptions", "250g of fresh beans delivered every week or every month — choose your roast level, caffeine, and origin. Pause anytime."),
        ],
        about_label="THE ROASTERY",
        about_title="Two baristas. One Probat. A whole lot of coffee.",
        about_body="Fernside started in 2019 as a weekend pop-up in a friend's bookshop. Today we run a full café, a roastery, and a subscription service that ships across the GCC — still just the two of us in charge.",
        about_image="https://images.unsplash.com/photo-1559496417-e7f25cb247f3?w=1000&h=1100&fit=crop",
        about_bullets=[
            "Direct trade relationships with six farms in Ethiopia, Colombia, Panama",
            "Roasted daily on a 5kg Probat P5 — still small by choice",
            "SCA-certified baristas, Q-grader head roaster",
            "Subscriptions ship to 12 GCC cities every week",
        ],
        gallery_label="THE CAFÉ",
        gallery_title="Mornings at Fernside",
        gallery_images=[
            "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1442550528053-c431ecb55509?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1445116572660-236099ec97a0?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1498804103079-a6351b050096?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=900&h=700&fit=crop",
        ],
        testimonials_label="REGULARS",
        testimonials_title="What our regulars say",
        testimonials=[
            ("The Ethiopian natural is the best coffee in the city. Full stop. I come twice a week.", "Tarek Hamdan", "Regular since 2020"),
            ("The subscription box feels like a gift to myself every Monday morning.", "Jenny Laurence", "Subscriber since 2021"),
            ("The staff actually know how to roast — and they'll spend twenty minutes explaining it if you ask.", "Dhruv Kapoor", "Regular since 2022"),
        ],
        cta_title="Come for coffee. Stay a while.",
        cta_body="Weekday mornings are our favourite. First brew's on us if you mention this site at the till.",
        contact_phone="+971 4 345 6677",
        contact_email="hi@fernside.coffee",
        contact_address="45 Al Marsa Street, Dubai Marina Walk",
        contact_hours="Daily · 6:30am – 8:30pm",
        footer_tagline="A specialty coffee roastery and café in Dubai Marina. Direct trade, small batches, one Probat.",
        footer_columns=[
            ("Coffee", ["This Week's Beans", "Subscriptions", "Wholesale", "Equipment"]),
            ("Roastery", ["About", "Our Farms", "Process", "Journal"]),
            ("Visit", ["The Café", "Hours", "Newsletter", "Instagram"]),
        ],
        footer_bg="#2b1d0f",
    ),

    # 17. FASHION BOUTIQUE — split hero, feature cards, mono + magenta, square buttons
    Template(
        id="fashion_boutique",
        name="Maison Linde",
        category="Fashion Boutique",
        description="Modern fashion boutique — split hero with lookbook imagery, feature cards services, stats row, monochrome base with magenta accent.",
        niche="ecommerce",
        brand="Maison Linde",
        initials="M",
        primary="#111111",
        secondary="#262626",
        accent="#e11d74",
        bg="#fafafa",
        bg_surface="#ffffff",
        text="#111111",
        text_muted="#737373",
        fonts=("'Bodoni Moda', serif", "'Inter', sans-serif", "Bodoni+Moda:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700"),
        hero_layout="split",
        services_layout="feature_cards",
        about_layout="stats_row",
        gallery_layout="gallery_grid_4",
        button_shape="square",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,8vw,6.2rem);font-weight:800;letter-spacing:-0.035em;line-height:1;}
        .section-title{font-family:var(--font-heading);font-weight:700;}
        .section-label{color:var(--accent);letter-spacing:0.3em;font-size:0.72rem;}
        section[data-section-type="feature_cards"]{background:#f4f4f5;}
        .card,.image-card{border-radius:0;box-shadow:none;border:1px solid rgba(17,17,17,0.08);}
        .stat-number{color:var(--primary);font-family:var(--font-heading);}
        .btn-primary{background:var(--primary);font-size:0.8rem;letter-spacing:0.12em;text-transform:uppercase;font-weight:600;padding:0.95rem 2.2rem;}
        .btn-primary:hover{background:var(--accent);}
        .btn-secondary{border:1px solid var(--primary);color:var(--primary);font-size:0.8rem;letter-spacing:0.12em;text-transform:uppercase;}
        """,
        hero_title="A wardrobe for the considered life.",
        hero_kicker="AUTUMN / WINTER 2026",
        hero_subtitle="An independent fashion house designing slow, seasonless pieces in natural fibres. Made in small runs at workshops we visit twice a year.",
        hero_image="https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1100&h=1400&fit=crop",
        hero_cta_primary="Shop the collection",
        hero_cta_secondary="Our story",
        hero_trust="Stocked at Matches, Net-a-Porter, and our Dubai flagship · Founded 2019",
        services_label="WHAT WE MAKE",
        services_title="Four capsules a year",
        services_subtitle="No more, no less. We design four small collections a year — each one a continuation of the last, not a reinvention.",
        services=[
            ("fa-shirt", "The Shirt Room", "Seven shirts, each made from Italian and Japanese cottons and linens. Worn by journalists, artists, and anyone tired of disposable fashion."),
            ("fa-user-tie", "Tailoring", "Seasonless jackets, trousers, and dresses cut at our Lisbon workshop. Made-to-measure for flagship clients."),
            ("fa-gem", "Accessories", "A small line of leather bags, shoes, and scarves. Everything made in Italy by workshops we've worked with for a decade."),
        ],
        services_images=[
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1551232864-3f0890e580d9?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900&h=700&fit=crop",
        ],
        about_label="THE HOUSE",
        about_title="Six years. Four capsules a year. Zero sales.",
        about_body="Maison Linde was founded in 2019 by designer Kari Linde after twelve years designing for Jil Sander and The Row. We believe in paying our makers well, making less, and never putting anything on sale.",
        about_stats=[
            ("4", "CAPSULES / YEAR", "Small, seasonless collections designed to compound"),
            ("12", "WORKSHOPS", "Across Italy, Portugal, and Japan — all paid fair wages"),
            ("0", "DISCOUNTS EVER", "We never mark anything down — it's a promise to our makers"),
            ("6", "YEARS", "Of building a wardrobe that outlasts trends"),
        ],
        gallery_label="THE LOOKBOOK",
        gallery_title="Autumn / Winter 2026",
        gallery_images=[
            "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1524275066040-46f4aa9afb1d?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1485230405346-71acb9518d9c?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=900&h=700&fit=crop",
        ],
        testimonials_label="PRESS",
        testimonials_title="What the press say",
        testimonials=[
            ("The cleanest, quietest wardrobe you can buy in Dubai right now. Cuts to last a decade.", "Leila Farah", "Style Editor, The National"),
            ("Kari Linde is the rare designer whose clothes feel designed for grown-ups, not algorithms.", "Olivia Stern", "Features Editor, Vogue Arabia"),
            ("Everything I've ever bought from Maison Linde still looks brand new five years later.", "Nadia Kassim", "Reader, Harper's Bazaar Arabia"),
        ],
        cta_title="Visit the flagship.",
        cta_body="The full collection lives at our flagship on Jumeirah Beach Road. Private appointments available for tailoring.",
        contact_phone="+971 4 388 5500",
        contact_email="atelier@maisonlinde.com",
        contact_address="Jumeirah Beach Road 182, Jumeirah 1, Dubai",
        contact_hours="Tue–Sat · 11am – 7pm · Sunday by appointment",
        footer_tagline="An independent fashion house designing small, slow collections in natural fibres. Made honestly, never discounted.",
        footer_columns=[
            ("Shop", ["New In", "Shirts", "Tailoring", "Accessories"]),
            ("House", ["About", "Workshops", "Press", "Journal"]),
            ("Help", ["Appointments", "Shipping", "Returns", "Care"]),
        ],
        footer_bg="#111111",
    ),

    # 18. MUSIC STUDIO — full-bleed dark hero, feature steps, stats, black/crimson
    Template(
        id="music_studio",
        name="Gravel Room Recording",
        category="Music Studio",
        description="Recording studio template — full-bleed dark hero with studio photo, numbered session workflow, black and crimson palette.",
        niche="music_artist",
        brand="Gravel Room",
        initials="G",
        primary="#dc2626",
        secondary="#991b1b",
        accent="#f59e0b",
        bg="#0a0a0a",
        bg_surface="#141414",
        text="#f4f4f5",
        text_muted="#a1a1aa",
        fonts=("'Anton', sans-serif", "'Inter', sans-serif", "Anton&family=Inter:wght@300;400;500;600;700"),
        hero_layout="full_image",
        services_layout="feature_steps",
        about_layout="stats_row",
        gallery_layout="gallery_grid_4",
        button_shape="square",
        navbar_style="dark",
        extra_css="""
        .nav-brand,.nav-links a{color:#f4f4f5;}
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3.5rem,10vw,7.5rem);letter-spacing:-0.01em;line-height:0.92;text-transform:uppercase;}
        .section-title{font-family:var(--font-heading);text-transform:uppercase;letter-spacing:-0.01em;}
        .section-label{color:var(--primary);}
        section[data-section-type]{background:#0a0a0a;}
        section[data-section-type="feature_steps"],section[data-section-type="stats_row"]{background:#141414;}
        .step-number{color:var(--primary);font-family:var(--font-heading);font-size:4.5rem;line-height:1;}
        .stat-number{color:var(--primary);font-family:var(--font-heading);font-size:clamp(3rem,6vw,5rem);}
        .card,.testimonial-card,.image-card,.contact-info-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);}
        .form-input{background:rgba(255,255,255,0.04);border-color:rgba(255,255,255,0.1);color:#f4f4f5;}
        .btn-primary{background:var(--primary);color:white;letter-spacing:0.08em;text-transform:uppercase;font-weight:700;}
        .btn-primary:hover{background:var(--secondary);}
        .btn-secondary{border-color:#f4f4f5;color:#f4f4f5;letter-spacing:0.08em;text-transform:uppercase;}
        """,
        hero_title="Tape still sounds better.",
        hero_kicker="TRACKING · MIXING · MASTERING",
        hero_subtitle="A hybrid analog / digital recording studio built around a vintage API console, a Studer 2-inch tape machine, and enough patience to get the take right.",
        hero_image="https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=1200&h=1500&fit=crop",
        hero_bg_image="https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=1800&h=1200&fit=crop",
        hero_cta_primary="Book a session",
        hero_cta_secondary="See the live room",
        hero_trust="Credits include Grammy-nominated albums from Khalid, Mitski, and The National",
        services_label="HOW WE WORK",
        services_title="A full-service studio",
        services_subtitle="Everything from the first demo to the final master — and the freedom to use as much or as little of it as you need.",
        services=[
            ("", "Pre-Production", "A week on-site or remote, working with our in-house producers to shape arrangements, tempos, and keys. Then we plan the session."),
            ("", "Tracking", "Two tracking rooms, one 28ft live room. API console, Studer A827 2-inch tape, and a mic cabinet with 120+ pieces."),
            ("", "Mixing", "Hybrid mixing on the API plus hardware outboard. We print through the tape machine on request — it still makes a difference."),
            ("", "Mastering", "A dedicated mastering room with Dangerous, Maselec, and Pultec EQs. CD, vinyl, and hi-res digital masters."),
        ],
        about_label="THE STUDIO",
        about_title="Twelve years. Thousand sessions.",
        about_body="Gravel Room was built in 2013 by producer Michael Obeng after years freelancing in London. The goal: a studio where the gear stays out of the way and the music gets to breathe.",
        about_stats=[
            ("1,200+", "SESSIONS", "Across twelve years and four continents"),
            ("28", "GRAMMY NOMS", "On records tracked or mixed at Gravel Room"),
            ("120+", "MICROPHONES", "A cabinet spanning 1950s Neumann to 2024 Ear Trumpet"),
            ("1", "TAPE MACHINE", "A pristine Studer A827 — still our secret weapon"),
        ],
        gallery_label="THE SPACE",
        gallery_title="Inside the studio",
        gallery_images=[
            "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1519508234439-4f23643125c1?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1571974599782-87624638275c?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1445375011782-2384686778a0?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1516280440614-37939bbacd81?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=900&h=700&fit=crop",
        ],
        testimonials_label="ARTISTS",
        testimonials_title="What artists say",
        testimonials=[
            ("The best-sounding drums I've ever cut. Michael's a wizard with the API and a saint with the clock.", "Idris Khoury", "Drummer, The National (touring)"),
            ("They printed my vocal through the tape machine on a whim — it's now the only way I record.", "Aya Khalid", "Singer-songwriter"),
            ("Gravel Room is where my last three albums lived. It's a second home.", "Pablo Moreno", "Producer, Latin Grammy winner 2023"),
        ],
        cta_title="Book a session.",
        cta_body="Day rates include engineer, console time, and full mic cabinet. Multi-day bookings get a discount — just ask.",
        contact_phone="+971 4 589 2200",
        contact_email="book@gravelroom.studio",
        contact_address="Warehouse 12, Al Quoz Industrial 3, Dubai",
        contact_hours="Sessions daily · Office Mon–Fri · 10am – 6pm",
        footer_tagline="A full-service hybrid recording studio in Al Quoz. Analog console, tape machine, and 120 mics.",
        footer_columns=[
            ("Services", ["Tracking", "Mixing", "Mastering", "Pre-Production"]),
            ("Studio", ["The Space", "The Gear", "Engineers", "Credits"]),
            ("Book", ["Day Rates", "Multi-Day", "Remote Mixing", "Contact"]),
        ],
        footer_bg="#0a0a0a",
    ),

    # 19. TRAVEL AGENCY — asymmetric hero, feature cards, ocean + coral
    Template(
        id="travel_agency",
        name="Meridian Atlas Travel",
        category="Travel Agency",
        description="Boutique travel agency template — asymmetric hero with destination photo, feature cards for trip types, ocean blue and coral palette.",
        niche="travel_agency",
        brand="Meridian Atlas",
        initials="M",
        primary="#0e5f87",
        secondary="#0a4361",
        accent="#ff6b6b",
        bg="#f5f9fc",
        bg_surface="#ffffff",
        text="#0a1f33",
        text_muted="#5a7386",
        fonts=("'Lora', serif", "'Inter', sans-serif", "Lora:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="asymmetric",
        services_layout="feature_cards",
        about_layout="feature_split",
        gallery_layout="gallery_grid_4",
        button_shape="pill",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(3rem,7vw,5.5rem);font-weight:600;letter-spacing:-0.025em;}
        .section-title{font-family:var(--font-heading);font-weight:600;}
        .section-label{color:var(--accent);letter-spacing:0.3em;}
        section[data-section-type="feature_cards"]{background:linear-gradient(135deg,#e8f2f8,#f5f9fc);}
        .card,.image-card{box-shadow:0 10px 40px rgba(14,95,135,0.06);}
        .card:hover{box-shadow:0 16px 50px rgba(14,95,135,0.12);}
        .btn-primary{background:var(--primary);font-weight:600;}
        .btn-primary:hover{background:var(--secondary);}
        .btn-secondary{border-color:var(--primary);color:var(--primary);}
        """,
        hero_title="The world, properly planned.",
        hero_kicker="BESPOKE TRAVEL DESIGN",
        hero_subtitle="A small travel design agency building itineraries for people who want more than a destination — and less than a tour group.",
        hero_image="https://images.unsplash.com/photo-1528127269322-539801943592?w=1100&h=1400&fit=crop",
        hero_cta_primary="Start planning a trip",
        hero_cta_secondary="Our destinations",
        hero_trust="Planned 800+ trips across 42 countries · Featured in Condé Nast Traveler Gold List",
        services_label="HOW WE TRAVEL",
        services_title="Four ways to go",
        services_subtitle="Every trip is custom — but these are the four shapes most of our travellers end up choosing.",
        services=[
            ("fa-map-location", "Signature Journeys", "Our most complete trips — 12 to 21 days, multi-country, concierge support on the ground. For travellers who want zero logistics."),
            ("fa-compass", "Curated Escapes", "Seven to ten day trips built around one destination and one story — a wine region, a festival, a family history."),
            ("fa-heart", "Honeymoons", "Private guides, private villas, and the occasional private plane. Designed for the trip you'll reference for the rest of your life."),
            ("fa-users", "Small Group Tours", "Our own hand-built group tours — capped at 12 travellers, led by specialists, in destinations we know inside out."),
        ],
        services_images=[
            "https://images.unsplash.com/photo-1528127269322-539801943592?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1504609813442-a8924e83f76e?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1493558103817-58b2924bce98?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1530789253388-582c481c54b0?w=900&h=700&fit=crop",
        ],
        about_label="THE AGENCY",
        about_title="Fifteen years. Forty-two countries.",
        about_body="Meridian Atlas was founded by two former travel writers who got tired of handing off their recommendations for free. Today we plan roughly 100 trips a year — and still scout every destination ourselves.",
        about_image="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1000&h=1100&fit=crop",
        about_bullets=[
            "Trips to 42 countries across six continents — and counting",
            "On-the-ground partners in every destination we sell",
            "24/7 concierge support while you're travelling",
            "Members of Virtuoso and the Indagare travel networks",
        ],
        gallery_label="WHERE WE GO",
        gallery_title="A few of our destinations",
        gallery_images=[
            "https://images.unsplash.com/photo-1528181304800-259b08848526?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1508923567004-3a6b8004f3d7?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1526392060635-9d6019884377?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=900&h=700&fit=crop",
            "https://images.unsplash.com/photo-1499696010180-025ef6e1a8f9?w=900&h=700&fit=crop",
        ],
        testimonials_label="TRAVELLERS",
        testimonials_title="What our travellers say",
        testimonials=[
            ("Our three weeks in Japan were perfect — down to the last ryokan. Meridian Atlas earned our lifetime loyalty.", "Samira & Faisal Al Awadhi", "Signature journey, 2024"),
            ("The honeymoon itinerary they built was magical. Not once did we have to think about logistics.", "Elena & Marco Ferri", "Honeymoon, Maldives + Kenya"),
            ("A small group tour through Georgia and Armenia that none of us will ever forget. Brilliant guides.", "Dr. Patel", "Small group tour, 2023"),
        ],
        cta_title="Start planning your next trip.",
        cta_body="Initial planning calls are free and take about 30 minutes. We'll respond within two working days.",
        contact_phone="+971 4 423 1200",
        contact_email="travel@meridianatlas.com",
        contact_address="DIFC Gate Village 11, Dubai, UAE",
        contact_hours="Mon–Fri · 9am – 6pm · Weekend by appointment",
        footer_tagline="A boutique travel design agency planning roughly 100 bespoke trips a year. Forty-two countries, every destination scouted.",
        footer_columns=[
            ("Travel", ["Signature Journeys", "Curated Escapes", "Honeymoons", "Small Groups"]),
            ("Agency", ["About", "Destinations", "Press", "Journal"]),
            ("Start", ["Plan a Trip", "Contact", "Newsletter", "Instagram"]),
        ],
        footer_bg="#0a1f33",
    ),

    # 20. ONLINE ACADEMY — split hero, card grid, stats row, logo cloud, indigo + amber
    Template(
        id="online_academy",
        name="Verdant Academy",
        category="Online Academy",
        description="Online education platform — split hero, card grid courses, stats row, logo cloud for partner universities, indigo and amber palette.",
        niche="coding_bootcamp",
        brand="Verdant Academy",
        initials="V",
        primary="#4f46e5",
        secondary="#7c3aed",
        accent="#f59e0b",
        bg="#fdfcf9",
        bg_surface="#ffffff",
        text="#1e1b2e",
        text_muted="#6b6583",
        fonts=("'Poppins', sans-serif", "'Inter', sans-serif", "Poppins:wght@500;600;700&family=Inter:wght@300;400;500;600;700"),
        hero_layout="split",
        services_layout="card_grid",
        about_layout="stats_row",
        gallery_layout="logo_cloud",
        button_shape="rounded",
        navbar_style="light",
        extra_css="""
        .hero-heading{font-family:var(--font-heading);font-size:clamp(2.8rem,6.5vw,4.8rem);font-weight:700;letter-spacing:-0.025em;}
        .section-title{font-family:var(--font-heading);font-weight:600;}
        .section-label{color:var(--primary);letter-spacing:0.25em;}
        section[data-section-type="card_grid"]{background:#f5f3ff;}
        section[data-section-type="stats_row"]{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:white;}
        section[data-section-type="stats_row"] .section-title,section[data-section-type="stats_row"] .section-subtitle{color:white;}
        section[data-section-type="stats_row"] .stat-number{color:var(--accent);}
        section[data-section-type="stats_row"] .stat-label{color:rgba(255,255,255,0.85);}
        section[data-section-type="stats_row"] .stat-sub{color:rgba(255,255,255,0.65);}
        .card{box-shadow:0 8px 30px rgba(79,70,229,0.08);}
        .card:hover{box-shadow:0 12px 40px rgba(79,70,229,0.15);transform:translateY(-4px);}
        .btn-primary{background:var(--primary);font-weight:600;}
        .btn-primary:hover{background:var(--secondary);}
        """,
        hero_title="Learn the skills that actually hire.",
        hero_kicker="ONLINE COURSES · LIVE COHORTS · 1-ON-1 MENTORING",
        hero_subtitle="An independent academy teaching software engineering, product design, and data science — with real mentors, cohort-based learning, and a hiring guarantee.",
        hero_image="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1100&h=1300&fit=crop",
        hero_cta_primary="Browse courses",
        hero_cta_secondary="How it works",
        hero_trust="4,200+ graduates · 89% hired within 6 months · Partners with 140+ companies",
        services_label="COURSES",
        services_title="Four tracks. One standard.",
        services_subtitle="Every cohort is capped at 24 learners and led by a senior practitioner. No pre-recorded lectures — just live teaching and real projects.",
        services=[
            ("fa-code", "Software Engineering", "A 16-week cohort covering modern web, cloud, and systems design. Taught by engineers from Meta, Stripe, and Shopify."),
            ("fa-palette", "Product Design", "A 14-week design cohort — research, interaction, prototyping, and a full case-study portfolio. Taught by practicing design leads."),
            ("fa-chart-line", "Data & Analytics", "Twelve weeks of SQL, Python, statistics, and dashboards. Capstone is a real dataset from a partner company, delivered to their team."),
            ("fa-robot", "AI Engineering", "A new 12-week track on building LLM products — prompting, RAG, evaluations, and deploying real systems. Starts every eight weeks."),
        ],
        about_label="WHY VERDANT",
        about_title="Built differently.",
        about_body="We're a small academy on purpose. Every cohort is capped, every instructor is actively practicing, and every learner gets direct mentor time every week.",
        about_stats=[
            ("4,200+", "GRADUATES", "Across five years of cohorts"),
            ("89%", "HIRED", "Within six months of graduating"),
            ("140+", "COMPANY PARTNERS", "Hiring from our graduate pool"),
            ("4.9 / 5", "LEARNER RATING", "Across 2,000+ published reviews"),
        ],
        gallery_label="OUR HIRING PARTNERS",
        gallery_title="Where our graduates go",
        logos=["Careem", "Noon", "Stripe", "Shopify", "Klarna", "Revolut", "Talabat", "Deliveroo"],
        testimonials_label="GRADUATES",
        testimonials_title="What our graduates say",
        testimonials=[
            ("I came in as a marketing manager. Sixteen weeks later I had two engineering offers. Verdant changed my life.", "Yasmin Haddad", "Software Engineering · Class of 2024"),
            ("The mentor time alone was worth the tuition. My mentor still sends me job leads two years after graduating.", "Chen Wei", "Product Design · Class of 2023"),
            ("I've been hiring from Verdant for three years. Their graduates come in more prepared than most three-year vets.", "Rahul Mehta", "Head of Engineering, Careem"),
        ],
        cta_title="Apply to the next cohort.",
        cta_body="Cohorts start every eight weeks. Applications take about twenty minutes and we review every one personally.",
        contact_phone="+971 4 566 7900",
        contact_email="hello@verdant.academy",
        contact_address="DMCC Business Centre, Jumeirah Lakes Towers, Dubai",
        contact_hours="Mon–Fri · 9am – 7pm · Weekend support by Slack",
        footer_tagline="An independent online academy for software, design, data, and AI. Small cohorts, real mentors, a hiring promise.",
        footer_columns=[
            ("Courses", ["Software Engineering", "Product Design", "Data & Analytics", "AI Engineering"]),
            ("Academy", ["How It Works", "Mentors", "Hiring Partners", "Press"]),
            ("Learners", ["Apply", "Financial Aid", "Student Login", "Newsletter"]),
        ],
        footer_bg="#1e1b2e",
    ),
]


# ─── Writer ────────────────────────────────────────────────────────────────


def main() -> int:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(here, "app", "templates_data")
    if not os.path.isdir(out_dir):
        print(f"ERROR: templates_data dir not found: {out_dir}", file=sys.stderr)
        return 1

    removed = 0
    for entry in os.listdir(out_dir):
        if entry.endswith(".html"):
            os.remove(os.path.join(out_dir, entry))
            removed += 1
    print(f"Removed {removed} existing templates")

    for t in TEMPLATES:
        path = os.path.join(out_dir, f"{t.id}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_template(t))
        size = os.path.getsize(path)
        print(f"Wrote {t.id:22} | {t.hero_layout:11} {t.services_layout:14} {t.about_layout:14} {t.gallery_layout:15} ({size:,} bytes)")

    print(f"\n✓ Built {len(TEMPLATES)} premium templates in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
