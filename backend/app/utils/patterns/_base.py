"""
Core HTML generation rules — always included in every prompt.
This is the skeleton: style block, CSS framework, image rules, etc.
Pattern-specific templates are injected dynamically.
"""

# The {plan_json} and {pattern_templates} and {style_additions} placeholders
# are filled by build_html_prompt() in prompt_pipeline.py

HTML_CORE_PROMPT = """You are an expert frontend developer. Generate a complete, production-quality website using pure CSS (NO Tailwind, NO utility frameworks).

WEBSITE PLAN:
{plan_json}

RULES:
- Return ONLY HTML inside a single ```html code block
- Output a <style> block FIRST (for CSS variables, fonts, all layout/component styles) then the HTML body content
- NO <html>, <head>, <body>, <link>, <meta> tags — just <style> block + body content
- Do NOT add Font Awesome <script> or <link> tags (e.g. kit.fontawesome.com) — Font Awesome is already loaded by the host page. Just use <i class="fa-solid fa-xxx"> icons directly.
- Write ALL styling in the <style> block using CSS classes. NO Tailwind utility classes. NO utility framework.
- Use semantic CSS class names (e.g. .container, .card, .btn-primary, .hero-heading)
- Use CSS variables for colors, fonts, radii (defined in :root)
- Use semantic HTML5: <nav>, <header>, <main>, <section>, <footer>
- EVERY content section MUST use: <section data-section-type="{{type}}" id="{{type}}"> — never <div>. The id MUST match the data-section-type so navbar anchor links (#services, #about, etc.) scroll to the correct section.
- Use the EXACT content from the plan — headlines, descriptions, button text, etc.
- Use Font Awesome icons exactly as specified: <i class="fa-solid fa-icon-name"></i>
- Add data-aos animations on grid items (cards, faq items, etc.) — NOT on section wrappers
- Use data-aos for scroll-reveal animations. VARIETY IS CRITICAL:
  - Available animations: fade-up, fade-down, fade-left, fade-right, zoom-in, zoom-out, flip-up, flip-down, slide-up, slide-right
  - Available easings: ease, ease-in-out, ease-in-back, ease-out-cubic
  - Vary delay: data-aos-delay="100" through "600" (stagger items in grids)
  - Vary duration: data-aos-duration="600" through "1200"
  - NEVER use the same animation on consecutive sections
  - Cards in a grid should stagger (each card gets increasing delay)
  - Use fade-up for most content, but mix in zoom-in, slide-right, fade-left for variety
- Hero and navbar must NOT have data-aos (visible immediately)
- Include ALL sections from the plan
- Do NOT include any JavaScript
- Do NOT include any explanation, just the html code block
- CRITICAL: Use ONLY the CSS classes defined in the style block below and in the pattern templates. Do NOT invent extra decorative classes (no parallax-bg, gradient-mesh, concrete-texture, glass-card, neon-glow, magnetic-btn, etc.). If a class is not in the provided CSS framework or pattern template, do NOT use it.
- HERO TEXT VISIBILITY: The hero headline MUST be clearly readable against its background. CRITICAL RULES:
  1. Do NOT use gradient-text, -webkit-text-fill-color: transparent, or background-clip: text on hero headings — these make text invisible.
  2. When using a background image hero (.hero-bg-cover), ALL text MUST be white (#fff or white) and the overlay MUST have minimum 0.5 opacity. Use the provided .hero-overlay-left or .hero-overlay-center classes — do NOT create custom overlays with lower opacity.
  3. Do NOT override .hero-overlay opacity in your <style> block. The provided overlay classes are already optimized.
  4. NEVER use dark text (var(--text) or dark colors) on a hero with a background image — it will be invisible if the image is dark.
  5. The H1 heading MUST contain PLAIN, STATIC TEXT — NOT Typed.js spans, NOT data-typed attributes, NOT empty elements that rely on JS to fill text. The heading must be fully readable with JavaScript disabled. If you want typing animation effects, put them in a SEPARATE element BELOW the H1, never inside it.
- HERO ALIGNMENT CONSISTENCY: ALL elements inside the hero (heading, subtitle, CTAs, trust line) MUST have the SAME alignment. If the hero uses .hero-center-content, everything is centered. If it uses .hero-full-overlay (left-aligned), EVERYTHING must be left-aligned — do NOT center the subtitle or CTAs while left-aligning the heading. Never mix text-align values within a hero.
- NO DECORATIVE BACKGROUND NUMBERS: Do NOT add large background numbers/text (like "01", "02") behind hero or section content. No .bg-number elements.
- HERO NAVBAR CLEARANCE (CRITICAL — THIS IS A RECURRING BUG): The navbar is fixed at top (80px height). The hero section MUST have enough top padding so NO text is hidden behind the navbar. The .hero-section class has padding-top: 10rem. Do NOT override this padding with smaller values in your custom CSS. Do NOT set padding-top: 0 on .hero-section (only .hero-section-flush can have padding-top: 0 because it uses margin-top: -80px with .hero-bg-cover that has its own padding-top: 80px). For non-flush heroes, NEVER add padding-top less than 8rem. NEVER let hero content start at the very top of the viewport — the heading must be FULLY visible below the navbar.
- HERO IMAGES: EVERY page's hero section MUST include a high-quality image — either as a background image (using .hero-bg-cover with background-image) or as a side image in a split layout (using .hero-split-grid). No hero section should be text-only without any imagery. Use relevant Unsplash/Pexels images.
- HERO IS MANDATORY: The FIRST section after navbar MUST be the hero section. It MUST contain: a compelling headline (H1), a subtitle, at least one CTA button, and an image. The hero must be visually impactful and take up at least 80vh. NEVER skip the hero or make it empty. If the plan includes a hero, render ALL its content (headline, subtitle, CTAs, trust line, image). Do NOT output a page that starts with a content section instead of the hero.
- PATTERN COMPLIANCE:
  1. Each section's HTML should follow the provided pattern template's GENERAL STRUCTURE — same layout approach (grid, flex, etc.) and nesting concept.
  2. Use the class names from the CSS framework above and from the pattern template as your foundation.
  3. You MAY add additional custom CSS classes for enhanced styling — but you MUST define them in your <style> block. Every class you use must have CSS rules.
  4. Use the pattern template as a starting point, then ENHANCE it with richer visual elements: floating cards, glow effects, gradient accents, subtle animations.
  5. The key rule: if you reference a CSS class, it MUST exist either in the framework above OR in your custom <style> block. No undefined classes.

PREMIUM CSS QUALITY — Your CSS must be production-grade and visually impressive:
- Use subtle gradients, layered shadows, glassmorphism, smooth transitions
- Add micro-interactions: button hover transforms, card hover lifts, link underline animations
- Hero sections need depth: floating cards, glow effects, layered backgrounds
- Use backdrop-filter: blur() for glass effects where appropriate
- Create visual hierarchy with deliberate spacing rhythm (8px base grid)
- Every interactive element needs a hover/focus state
- Add subtle background textures or patterns where they enhance the design
- Use ::before/::after pseudo-elements for decorative accents (gradient lines, dots, glows)

STYLE BLOCK — output this FIRST before any HTML elements.
The <style> block must contain ALL CSS for the entire page. This is a COMPLETE website — every element must be styled.

<style>
@import url('https://fonts.googleapis.com/css2?family=HEADING_FONT:wght@400;500;600;700;800&family=BODY_FONT:wght@400;500;600&display=swap');

/* ═══ Design Tokens ═══ */
:root {{
  --primary: PRIMARY_COLOR;
  --secondary: SECONDARY_COLOR;
  --accent: ACCENT_COLOR;
  --bg: BACKGROUND_COLOR;
  --bg-surface: SURFACE_COLOR;
  --text: TEXT_COLOR;
  --text-muted: TEXT_MUTED_COLOR;
  --font-heading: 'HEADING_FONT', sans-serif;
  --font-body: 'BODY_FONT', sans-serif;
  --radius: CARD_RADIUS;
  --radius-btn: BUTTON_RADIUS;
  --shadow: 0 4px 24px rgba(0,0,0,0.08);
  --shadow-hover: 0 20px 60px rgba(0,0,0,0.15);
  --transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}}

/* ═══ Base Reset & Typography ═══ */
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: var(--font-body); background: var(--bg); color: var(--text); line-height: 1.6; padding-top: 80px; overflow-x: hidden; min-height: 100vh; }}
h1, h2, h3, h4, h5, h6 {{ font-family: var(--font-heading); font-weight: 700; line-height: 1.2; color: var(--text); }}
a {{ text-decoration: none; color: inherit; }}
img {{ max-width: 100%; height: auto; }}
ul {{ list-style: none; padding: 0; margin: 0; }}

/* ═══ Layout System ═══ */
.container {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
.container-wide {{ max-width: 1400px; margin: 0 auto; padding: 0 1.5rem; }}
.container-narrow {{ max-width: 800px; margin: 0 auto; padding: 0 1.5rem; }}
.container-xs {{ max-width: 600px; margin: 0 auto; padding: 0 1.5rem; }}

/* ═══ Grid System ═══ */
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; }}
.grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }}
.grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; }}
@media (max-width: 1024px) {{
  .grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
  .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 768px) {{
  .grid-2 {{ grid-template-columns: 1fr; }}
  .grid-3 {{ grid-template-columns: 1fr; }}
  .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 480px) {{
  .grid-4 {{ grid-template-columns: 1fr; }}
}}
.text-center {{ text-align: center; }}
.md-order-1 {{ order: 0; }}
.md-order-2 {{ order: 0; }}
@media (min-width: 769px) {{
  .md-order-1 {{ order: 1; }}
  .md-order-2 {{ order: 2; }}
}}

/* ═══ Section Styles ═══ */
section[data-section-type] {{ padding: 4rem 0; position: relative; opacity: 0; transform: translateY(30px); transition: opacity 0.6s ease, transform 0.6s ease; animation: sectionFallback 0.8s ease forwards; animation-delay: 1s; }}
section[data-section-type].visible {{ opacity: 1; transform: translateY(0); animation: none; }}
@keyframes sectionFallback {{ to {{ opacity: 1; transform: translateY(0); }} }}
[data-aos] {{ animation: sectionFallback 0.6s ease forwards; animation-delay: 1.5s; }}
[data-aos].aos-animate {{ animation: none; }}
footer, footer[data-section-type], footer section[data-section-type] {{ opacity: 1; transform: none; animation: none; }}
@media (min-width: 769px) {{
  section[data-section-type] {{ padding: 5rem 0; }}
}}
.section-header {{ text-align: center; margin-bottom: 3rem; }}
.section-title {{ font-size: clamp(1.75rem, 3vw, 2.5rem); margin-bottom: 0.75rem; letter-spacing: -0.02em; }}
.section-subtitle {{ font-size: 1.05rem; color: var(--text-muted); max-width: 36rem; margin: 0 auto; line-height: 1.7; }}

/* Section background rhythm */
section[data-section-type="features"],
section[data-section-type="stats"] {{ background: var(--bg-surface); }}
section[data-section-type="testimonials"],
section[data-section-type="pricing"] {{ background: color-mix(in srgb, var(--primary) 4%, var(--bg)); }}

/* ═══ Buttons ═══ */
.btn-primary {{ display: inline-block; background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 0.8rem 2rem; border-radius: var(--radius-btn); font-weight: 600; font-family: inherit; font-size: 0.95rem; border: none; cursor: pointer; transition: var(--transition); text-align: center; letter-spacing: 0.01em; }}
.btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px color-mix(in srgb, var(--primary) 30%, transparent); }}
.btn-secondary {{ display: inline-block; border: 2px solid var(--primary); color: var(--primary); padding: 0.75rem 1.75rem; border-radius: var(--radius-btn); font-weight: 600; font-family: inherit; font-size: 1rem; background: transparent; cursor: pointer; transition: var(--transition); text-align: center; }}
.btn-secondary:hover {{ background: var(--primary); color: white; transform: translateY(-2px); }}
.btn-primary-light {{ display: inline-block; background: white; color: var(--primary); padding: 0.75rem 1.75rem; border-radius: var(--radius-btn); font-weight: 600; border: none; cursor: pointer; transition: var(--transition); }}
.btn-primary-light:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.2); }}
.btn-secondary-light {{ display: inline-block; border: 2px solid white; color: white; padding: 0.75rem 1.75rem; border-radius: var(--radius-btn); font-weight: 600; background: transparent; cursor: pointer; transition: var(--transition); }}
.btn-secondary-light:hover {{ background: white; color: var(--primary); }}
.btn-group {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
.btn-group.center {{ justify-content: center; }}

/* ═══ Cards ═══ */
.card {{ background: var(--bg-surface); border-radius: var(--radius); padding: 1.5rem 2rem; box-shadow: var(--shadow); transition: var(--transition); border: 1px solid color-mix(in srgb, var(--text) 6%, transparent); position: relative; overflow: hidden; }}
.card:hover {{ transform: translateY(-8px); box-shadow: var(--shadow-hover); }}
.card::after {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--primary), var(--accent)); opacity: 0; transition: opacity 0.3s; }}
.card:hover::after {{ opacity: 1; }}
.card:hover h3 {{ color: var(--accent); transition: color 0.3s ease; }}
.card-title {{ font-size: 1.15rem; font-weight: 700; margin-bottom: 0.5rem; }}
.card-text {{ color: var(--text-muted); line-height: 1.7; font-size: 0.95rem; }}
.card-body {{ padding: 1.25rem; }}
.card-image {{ width: 100%; height: 14rem; max-height: 260px; object-fit: cover; display: block; }}
.icon-box {{ width: 3.5rem; height: 3.5rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; color: white; margin-bottom: 1.25rem; flex-shrink: 0; background: linear-gradient(135deg, var(--primary), var(--secondary)); }}
.card-link {{ color: var(--primary); font-weight: 600; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.5rem; transition: gap 0.3s; }}
.card-link:hover {{ gap: 0.75rem; }}

/* ═══ Images ═══ */
.img-cover {{ width: 100%; height: auto; border-radius: var(--radius); object-fit: cover; transition: transform 0.4s ease; }}
.img-cover:hover {{ transform: scale(1.02); }}
.img-wrapper {{ overflow: hidden; border-radius: var(--radius); }}
.team-photo {{ width: 100%; height: 14rem; max-height: 240px; object-fit: cover; display: block; }}

/* ═══ Navbar ═══ */
.navbar {{ position: fixed; top: 0; left: 0; right: 0; z-index: 50; backdrop-filter: blur(12px); transition: var(--transition); padding: 1rem 0; }}
body {{ padding-top: 80px; }}
.navbar-light {{ background: rgba(255,255,255,0.85); border-bottom: 1px solid rgba(0,0,0,0.06); }}
.navbar-dark {{ background: rgba(0,0,0,0.4); border-bottom: 1px solid rgba(255,255,255,0.08); }}
nav.nav-scrolled {{ background: var(--bg) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.1); backdrop-filter: blur(16px); }}
.navbar-inner {{ display: flex; justify-content: space-between; align-items: center; }}
.nav-brand {{ display: flex; align-items: center; gap: 0.625rem; font-weight: 700; font-size: 1.15rem; color: var(--text); }}
.nav-links {{ display: flex; align-items: center; gap: 2rem; }}
.nav-links a {{ font-weight: 500; color: var(--text); transition: color 0.3s; position: relative; }}
.nav-links a::after {{ content: ""; position: absolute; bottom: -4px; left: 0; width: 0; height: 2px; background: var(--primary); transition: width 0.3s ease; }}
.nav-links a:hover {{ color: var(--primary); }}
.nav-links a:hover::after {{ width: 100%; }}
.nav-toggle {{ display: none; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--text); padding: 0.5rem; min-width: 44px; min-height: 44px; align-items: center; justify-content: center; }}
.nav-cta {{ display: inline-block; }}
.mobile-cta {{ display: none; }}
@media (max-width: 768px) {{
  .nav-links {{ display: none !important; position: fixed; top: 70px; left: 0; right: 0; flex-direction: column; padding: 1.5rem 2rem; gap: 1.25rem; z-index: 999; border-bottom: 1px solid rgba(255,255,255,0.08); }}
  .nav-links.active {{ display: flex !important; background: var(--bg); backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0,0,0,0.15); }}
  .nav-toggle {{ display: flex !important; }}
  .nav-cta {{ display: none !important; }}
  .mobile-cta {{ display: block !important; }}
}}

/* ═══ Hero ═══ */
.hero-section {{ padding: 10rem 0 4rem !important; position: relative; overflow: hidden; min-height: min(80vh, 700px); display: flex; align-items: center; }}
@media (min-width: 769px) {{ .hero-section {{ padding: 10rem 0 5rem !important; }} }}
.hero-section.hero-section-flush {{ margin-top: -80px; padding-top: 0 !important; min-height: 100vh; }}
.hero-heading {{ font-size: clamp(2.25rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.08; margin-bottom: 1.5rem; color: var(--text); letter-spacing: -0.02em; }}
.hero-subtitle {{ font-size: clamp(1.05rem, 1.3vw, 1.2rem); color: var(--text-muted); line-height: 1.7; margin-bottom: 2rem; max-width: 36rem; }}
.hero-center-content .hero-subtitle {{ margin-left: auto; margin-right: auto; }}
.trust-line {{ font-size: 0.875rem; color: var(--text-muted); margin-top: 1rem; }}
.hero-ctas {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
.hero-center-content .hero-ctas {{ justify-content: center; }}
.hero-full-overlay {{ text-align: left; }}
.hero-full-overlay .hero-subtitle {{ margin-left: 0; margin-right: 0; }}
.hero-full-overlay .hero-ctas {{ justify-content: flex-start; }}
.hero-full-overlay .trust-line {{ text-align: left; }}
.hero-split-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; min-height: 70vh; }}
.hero-split-asymmetric {{ grid-template-columns: 55% 45%; }}
@media (max-width: 768px) {{ .hero-split-grid {{ grid-template-columns: 1fr; min-height: auto; }} }}
.hero-center-content {{ text-align: center; max-width: 48rem; margin: 0 auto; width: 100%; }}
.hero-bg-cover {{ position: relative; width: 100%; min-height: min(90vh, 800px); background-size: cover; background-position: center; background-repeat: no-repeat; display: flex; align-items: center; justify-content: center; padding-top: 80px; }}
.hero-bg-cover > .container, .hero-bg-cover > .container-wide, .hero-bg-cover > .container-narrow {{ width: 100%; }}
.hero-overlay {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 1; }}
.hero-overlay-left {{ background: linear-gradient(to right, rgba(0,0,0,0.55), rgba(0,0,0,0.35), rgba(0,0,0,0.1)); }}
.hero-overlay-center {{ background: linear-gradient(to bottom, rgba(0,0,0,0.45), rgba(0,0,0,0.35), rgba(0,0,0,0.5)); }}
.hero-overlay-modern {{ background: linear-gradient(135deg, rgba(0,0,0,0.55), rgba(0,0,0,0.25)); }}
.hero-bg-cover > *:not(.hero-overlay) {{ position: relative; z-index: 2; }}
.text-light {{ color: #fff !important; }}
.hero-animated-bg {{ min-height: 100vh; display: flex; align-items: center; position: relative; padding-top: 80px; background-size: 400% 400%; animation: gradientShift 8s ease infinite; }}
.text-light {{ color: white; }}
.text-light .hero-heading {{ color: white; }}
.text-light .hero-subtitle {{ color: rgba(255,255,255,0.85); }}
.text-light .trust-line {{ color: rgba(255,255,255,0.7); }}
.text-light .section-label {{ color: rgba(255,255,255,0.8); }}
.text-light .label-line {{ background: rgba(255,255,255,0.6); }}
.bg-number {{ display: none !important; }}
.hero-section > .container, .hero-section > .container-wide, .hero-section > .container-narrow {{ position: relative; z-index: 1; }}
.section-label {{ display: inline-flex; align-items: center; gap: 0.75rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.25em; font-weight: 600; color: var(--accent); margin-bottom: 1.5rem; }}
.label-line {{ width: 2.5rem; height: 2px; background: var(--accent); display: inline-block; }}
.floating-card {{ position: absolute; bottom: -1.25rem; left: -1.25rem; background: var(--bg-surface); border-radius: var(--radius); padding: 1.25rem 1.5rem; box-shadow: var(--shadow-hover); display: flex; align-items: center; gap: 0.75rem; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); z-index: 10; }}
@media (max-width: 768px) {{ .floating-card {{ display: none; }} }}
.browser-frame {{ border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-hover); border: 1px solid rgba(0,0,0,0.1); }}
.browser-dots {{ display: flex; gap: 0.375rem; padding: 0.75rem 1rem; background: rgba(0,0,0,0.04); }}
.browser-dots span {{ width: 0.625rem; height: 0.625rem; border-radius: 50%; }}
.browser-dots span:nth-child(1) {{ background: #ff5f57; }}
.browser-dots span:nth-child(2) {{ background: #ffbd2e; }}
.browser-dots span:nth-child(3) {{ background: #28c940; }}

/* ═══ Gradient & Decorative ═══ */
.gradient-text {{ background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
.card-grid > *:nth-child(3n+1) {{ transition-delay: 0ms; }}
.card-grid > *:nth-child(3n+2) {{ transition-delay: 120ms; }}
.card-grid > *:nth-child(3n+3) {{ transition-delay: 240ms; }}

/* ═══ Pricing ═══ */
.pricing-card.featured {{ transform: scale(1.05); border: 2px solid var(--primary) !important; z-index: 1; }}
.plan-price {{ font-size: clamp(2.5rem, 4vw, 3rem); font-weight: 700; color: var(--accent); margin: 1rem 0; }}
.plan-period {{ font-size: 1rem; font-weight: 400; color: var(--text-muted); }}
.plan-features {{ text-align: left; margin: 1.5rem 0; }}
.plan-feature {{ display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0; color: var(--text-muted); font-size: 0.9rem; }}
.popular-badge {{ position: absolute; top: -0.75rem; left: 50%; transform: translateX(-50%); background: var(--primary); color: white; font-size: 0.7rem; font-weight: 700; padding: 0.25rem 1rem; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.05em; }}

/* ═══ Stats ═══ */
.stat-item {{ display: flex; flex-direction: column; align-items: center; gap: 0.75rem; text-align: center; }}
.stat-icon {{ width: 3rem; height: 3rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; color: var(--accent); }}
.stat-number {{ font-size: clamp(2.5rem, 4vw, 3rem); font-weight: 700; line-height: 1; white-space: nowrap; }}
.stat-label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.2em; font-weight: 600; color: var(--text-muted); max-width: 180px; }}

/* ═══ FAQ ═══ */
.faq-item {{ border-bottom: 1px solid rgba(255,255,255,0.1); }}
.faq-question {{ width: 100%; background: transparent; border: none; padding: 1.25rem 0; display: flex; justify-content: space-between; align-items: center; font-size: 1rem; font-weight: 600; cursor: pointer; text-align: left; color: var(--text); font-family: inherit; }}
.faq-answer {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }}
.faq-item.active .faq-answer {{ max-height: 500px; padding-bottom: 1.25rem; }}
.faq-item.active .faq-question i {{ transform: rotate(180deg); transition: transform 0.3s; }}

/* ═══ Testimonials ═══ */
.stars {{ color: #f59e0b; margin-bottom: 0.75rem; }}
.testimonial-quote {{ color: var(--text-muted); line-height: 1.7; font-style: italic; margin-bottom: 1.25rem; }}
.testimonial-quote-lg {{ font-size: 1.2rem; font-style: italic; line-height: 1.8; margin: 1.5rem 0; }}
.testimonial-author {{ display: flex; align-items: center; gap: 0.75rem; }}
.testimonial-slide {{ display: none; }}
.testimonial-slide.active {{ display: block; }}
.slider-dots {{ display: flex; justify-content: center; gap: 0.5rem; margin-top: 2rem; }}
.slider-dot {{ width: 0.75rem; height: 0.75rem; border-radius: 50%; border: 2px solid var(--primary); background: transparent; cursor: pointer; padding: 0; transition: background 0.3s; }}
.slider-dot.active {{ background: var(--primary); }}

/* ═══ Footer ═══ */
footer {{ margin-top: 4rem; position: relative; z-index: 1; }}
.footer-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; }}
@media (max-width: 1024px) {{ .footer-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 640px) {{ .footer-grid {{ grid-template-columns: 1fr; }} }}
.footer-description {{ font-size: 0.9rem; color: rgba(255,255,255,0.6); line-height: 1.6; max-width: 280px; }}
.footer-heading {{ font-weight: 700; color: white; margin-bottom: 1rem; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }}
.footer-links {{ list-style: none; padding: 0; margin: 0; }}
.footer-links li {{ margin-bottom: 0.5rem; }}
.footer-links a {{ color: rgba(255,255,255,0.7); transition: color 0.3s; font-size: 0.9rem; }}
.footer-links a:hover {{ color: white; }}
.social-links {{ display: flex; gap: 0.75rem; margin-top: 1rem; }}
.social-link {{ width: 2.5rem; height: 2.5rem; border-radius: 50%; background: rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; color: white; border: 1px solid rgba(255,255,255,0.1); transition: var(--transition); }}
.social-link:hover {{ background: var(--primary); border-color: var(--primary); transform: translateY(-2px); }}
.footer-bottom {{ border-top: 1px solid rgba(255,255,255,0.08); margin-top: 2.5rem; padding-top: 1.5rem; text-align: center; font-size: 0.875rem; color: rgba(255,255,255,0.5); }}
.contact-item {{ display: flex; gap: 1rem; align-items: flex-start; margin-bottom: 1rem; }}
.contact-icon {{ color: var(--accent); width: 1.25rem; margin-top: 0.25rem; flex-shrink: 0; }}

/* ═══ Forms ═══ */
.contact-form {{ display: flex; flex-direction: column; gap: 1rem; }}
.contact-form .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
@media (max-width: 640px) {{ .contact-form .form-row {{ grid-template-columns: 1fr; }} }}
.form-input {{ width: 100%; padding: 1rem; border-radius: var(--radius, 0.5rem); border: 1px solid rgba(255,255,255,0.12); background: var(--bg-surface, rgba(255,255,255,0.05)); color: var(--text); font-family: inherit; font-size: 1rem; transition: border-color 0.3s; box-sizing: border-box; }}
.form-input:focus {{ border-color: var(--primary); outline: none; box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 10%, transparent); }}
.form-input::placeholder {{ color: var(--text-muted, rgba(255,255,255,0.4)); }}
.form-textarea {{ resize: vertical; min-height: 120px; }}
.newsletter-form {{ display: flex; gap: 0.75rem; max-width: 28rem; margin: 0 auto; }}
@media (max-width: 640px) {{ .newsletter-form {{ flex-direction: column; }} }}
.form-hint {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 0.75rem; opacity: 0.7; }}

/* ═══ Gallery & Carousel ═══ */
.gallery-item {{ overflow: hidden; border-radius: var(--radius); cursor: pointer; }}
.gallery-image {{ width: 100%; height: 14rem; max-height: 280px; object-fit: cover; transition: transform 0.5s ease; }}
.gallery-item:hover .gallery-image {{ transform: scale(1.1); }}
.gallery-lightbox {{ position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.9); display: none; align-items: center; justify-content: center; padding: 1rem; }}
.gallery-lightbox.active {{ display: flex; }}
.lightbox-close {{ position: absolute; top: 1.5rem; right: 1.5rem; color: white; font-size: 2rem; background: transparent; border: none; cursor: pointer; z-index: 10; }}
.lightbox-prev, .lightbox-next {{ position: absolute; top: 50%; transform: translateY(-50%); color: white; font-size: 1.5rem; background: rgba(0,0,0,0.3); border: none; cursor: pointer; border-radius: 50%; width: 3rem; height: 3rem; display: flex; align-items: center; justify-content: center; transition: background 0.3s; }}
.lightbox-prev {{ left: 1rem; }}
.lightbox-next {{ right: 1rem; }}
.lightbox-prev:hover, .lightbox-next:hover {{ background: rgba(0,0,0,0.6); }}
.lightbox-img {{ max-width: 90vw; max-height: 85vh; object-fit: contain; border-radius: 0.5rem; }}
.carousel-container {{ position: relative; overflow: hidden; border-radius: var(--radius); }}
.carousel-track {{ display: flex; transition: transform 0.5s ease-in-out; }}
.carousel-slide {{ min-width: 100%; position: relative; }}
.carousel-image {{ width: 100%; height: 20rem; max-height: 380px; object-fit: cover; }}
@media (min-width: 769px) {{ .carousel-image {{ height: 24rem; max-height: 400px; }} }}
.carousel-caption {{ position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.7), transparent); padding: 2rem; color: white; }}
.carousel-prev, .carousel-next {{ position: absolute; top: 50%; transform: translateY(-50%); width: 2.5rem; height: 2.5rem; border-radius: 50%; background: rgba(255,255,255,0.2); backdrop-filter: blur(4px); border: none; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.3s; z-index: 10; }}
.carousel-prev {{ left: 1rem; }}
.carousel-next {{ right: 1rem; }}
.carousel-prev:hover, .carousel-next:hover {{ background: rgba(255,255,255,0.4); }}
.carousel-dots {{ display: flex; justify-content: center; gap: 0.5rem; margin-top: 1.5rem; }}
.carousel-dot {{ width: 0.75rem; height: 0.75rem; border-radius: 50%; border: 2px solid var(--primary); background: transparent; cursor: pointer; padding: 0; transition: background 0.3s; }}
.carousel-dot.active {{ background: var(--primary); }}

/* ═══ Masonry ═══ */
.masonry-grid {{ column-count: 3; column-gap: 1.5rem; }}
@media (max-width: 1024px) {{ .masonry-grid {{ column-count: 2; }} }}
@media (max-width: 768px) {{ .masonry-grid {{ column-count: 1; }} }}
.masonry-item {{ break-inside: avoid; margin-bottom: 1.5rem; position: relative; border-radius: var(--radius); overflow: hidden; }}
.masonry-overlay {{ position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0,0,0,0.8)); color: white; padding: 1.5rem; transform: translateY(100%); transition: transform 0.3s ease; }}
.masonry-item:hover .masonry-overlay {{ transform: translateY(0); }}

/* ═══ Timeline ═══ */
.timeline-item {{ display: flex; gap: 1.5rem; align-items: flex-start; padding: 2rem 0; position: relative; }}
.timeline-date {{ min-width: 5rem; text-align: right; font-size: 0.875rem; font-weight: 700; color: var(--accent); }}
.timeline-dot {{ width: 1rem; height: 1rem; min-width: 1rem; border-radius: 50%; background: var(--primary); margin-top: 0.25rem; z-index: 10; box-shadow: 0 0 0 4px var(--bg); }}
.timeline-card {{ flex: 1; background: var(--bg-surface); border-radius: var(--radius); padding: 1.25rem; box-shadow: var(--shadow); }}

/* ═══ Logo Cloud ═══ */
.logo-cloud {{ display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 1.5rem; }}
.logo-item {{ padding: 0.75rem 1rem; }}
.logo-text {{ font-size: 1rem; font-weight: 700; letter-spacing: 0.02em; opacity: 0.4; transition: opacity 0.3s; white-space: nowrap; color: var(--text); }}
.logo-text:hover {{ opacity: 0.8; }}

/* ═══ Trust Badges ═══ */
.trust-badges {{ display: flex; flex-wrap: wrap; justify-content: center; align-items: center; gap: 2rem; }}
@media (min-width: 769px) {{ .trust-badges {{ gap: 3rem; }} }}
.trust-badge {{ display: flex; align-items: center; gap: 0.75rem; opacity: 0.6; transition: opacity 0.3s; }}
.trust-badge:hover {{ opacity: 1; }}
.badge-icon {{ font-size: 1.5rem; color: var(--accent); }}

/* ═══ Feature Patterns ═══ */
.feature-split-list {{ display: flex; flex-direction: column; gap: 3rem; }}
.feature-title {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 0.75rem; }}
.feature-text {{ color: var(--text-muted); line-height: 1.7; }}
.stacked-list {{ border-top: 1px solid rgba(255,255,255,0.1); }}
.stacked-item {{ display: flex; gap: 1.25rem; align-items: flex-start; padding: 2rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
@media (max-width: 768px) {{ .stacked-item {{ flex-direction: column; }} }}
.step-item {{ display: flex; gap: 1.5rem; align-items: flex-start; padding: 2rem 0; position: relative; }}
.step-number {{ width: 3.5rem; height: 3.5rem; min-width: 3.5rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; color: white; z-index: 10; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }}

/* ═══ Service Modal ═══ */
.modal-trigger {{ cursor: pointer; }}
.modal-trigger:hover .icon-box {{ transform: scale(1.1); transition: transform 0.3s; }}
.detail-modal {{ position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.6); display: none; align-items: center; justify-content: center; padding: 1rem; }}
.detail-modal.active {{ display: flex; }}
.modal-content {{ background: var(--bg); border-radius: var(--radius); max-width: 32rem; width: 100%; padding: 2rem; position: relative; box-shadow: var(--shadow-hover); max-height: 90vh; overflow-y: auto; }}
.modal-close {{ position: absolute; top: 1rem; right: 1rem; color: var(--text-muted); font-size: 1.25rem; background: transparent; border: none; cursor: pointer; }}
.modal-close:hover {{ color: var(--text); }}

/* ═══ Comparison Table ═══ */
.comparison-table {{ width: 100%; border-collapse: collapse; text-align: left; }}
.comparison-table th {{ padding: 1rem; font-size: 0.875rem; font-weight: 600; color: var(--text-muted); border-bottom: 1px solid rgba(255,255,255,0.1); }}
.comparison-table td {{ padding: 0.875rem 1rem; font-size: 0.875rem; border-bottom: 1px solid rgba(255,255,255,0.06); }}
.comparison-table tr:hover {{ background: rgba(255,255,255,0.02); }}
.check-icon {{ color: #10b981; }}
.xmark-icon {{ color: #ef4444; opacity: 0.5; }}

/* ═══ Animations ═══ */
@keyframes floatOrb {{ 0% {{ transform: translateY(0); }} 50% {{ transform: translateY(-30px); }} 100% {{ transform: translateY(0); }} }}
@keyframes logoGradient {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
@keyframes gradientShift {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}

/* ═══ Utilities ═══ */
.relative {{ position: relative; }}
.z-10 {{ z-index: 10; }}
.logo-mark {{ width: 2.25rem; height: 2.25rem; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 0.875rem; flex-shrink: 0; box-shadow: 0 4px 20px rgba(0,0,0,0.15); background-size: 200% 200%; animation: logoGradient 6s ease infinite; }}

{style_additions}
.typed-cursor {{ color: var(--primary); font-weight: 100; }}
.search-dropdown.active {{ display: block; }}
.whatsapp-float {{ position: fixed !important; bottom: 1.5rem !important; left: 1.5rem !important; right: auto !important; z-index: 50; animation: floatOrb 3s ease-in-out infinite; animation-duration: 3s; }}
#back-to-top {{ position: fixed !important; bottom: 1.5rem !important; right: 1.5rem !important; left: auto !important; z-index: 50; }}
#back-to-top.visible {{ opacity: 1; pointer-events: auto; }}
[data-splitting] .char {{ display: inline-block; opacity: 0; transform: translateY(20px); transition: opacity 0.4s ease, transform 0.4s ease; }}
[data-splitting].visible .char {{ opacity: 1; transform: translateY(0); }}
@media (max-width: 768px) {{ .steps-container::before {{ left: 24px; }} .timeline-container::before {{ left: 98px; }} }}
</style>
OUTPUT THE ENTIRE <style> BLOCK ABOVE as your first output, with ALL placeholder values filled in from the plan's design spec (colors, fonts, radii). Then APPEND additional CSS rules AFTER the framework above for:
- Section-specific backgrounds and textures
- Custom animation @keyframes beyond the basics above
- Any section-specific layout not covered by the framework (e.g. hero ::before/::after decorative elements)
- Light theme adjustments (e.g. border-color: rgba(0,0,0,0.08) instead of rgba(255,255,255,0.06))
IMPORTANT: Do NOT rewrite or replace the framework CSS above. Keep ALL of it intact and just ADD your custom rules at the end. The framework classes (.hero-section, .hero-bg-cover, .card, .btn-primary, .grid-2, .container, .navbar, .footer-grid, etc.) MUST remain unchanged. You are EXTENDING the framework, not replacing it.

⚠️ MANDATORY IMAGE RULES — VIOLATION = BROKEN OUTPUT ⚠️
NEVER write real image URLs (pexels.com, unsplash.com, etc). They will ALL 404.
The ONLY way to include images is the {{IMG:role query}} placeholder system:
- For EVERY <img> tag: src="{{IMG:role query keywords}}"
- For EVERY background-image: url('{{IMG:background query keywords}}')
- Format: <img src="{{IMG:role query keywords}}" alt="descriptive alt text" class="img-cover" loading="lazy">
- IMAGE ROLES: hero, product, feature, gallery, team, testimonial, background, cta, mockup
- Use the EXACT image_query from the plan — do NOT simplify or shorten
- Each placeholder MUST have a DIFFERENT query — never reuse
- ABSOLUTELY NO hardcoded URLs from pexels.com, unsplash.com, or any other domain
- ABSOLUTELY NO /images/ or /logos/ paths
- If you write a real URL instead of {{IMG:...}}, the image WILL be broken

CRITICAL: Match each section's "pattern" field to the EXACT HTML structure below.

LOGO MARK — use a gradient icon/initial in navbar. Pick one:
  - Initial: <span class="logo-mark" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">X</span>
  - Icon: same but with <i class="fa-solid fa-icon"></i> inside
  - Monogram: same but with two initials (e.g. "HC")
  Vary the style per brand.

TYPED.JS HERO EFFECT — adds a typewriter animation to the hero headline. Use freely on any hero:
  Replace the static headline text with:
    <h1 class="hero-heading">
      <span class="typed-text" data-typed='["First Phrase Here", "Second Phrase Here", "Third Phrase Here"]'></span>
    </h1>
  The JS stage auto-detects .typed-text and initializes Typed.js. Use 3-4 different phrases that showcase the brand.

HERO DEPTH ELEMENTS — add at least 1 of these to every hero section for visual richness:
  1. Section label above headline: <span class="section-label"><span class="label-line"></span>LABEL TEXT</span>
  2. Trust line below CTAs: <p class="trust-line">Trust signal text</p>
  Do NOT add custom animation classes (no hero-stagger, no hero-anim, no fade-in-up). AOS handles animations.

HERO HEADLINE SIZE — hero-heading class gives clamp(2rem, 5vw, 3.5rem). Do NOT override with larger inline font-size values. Max heading size is 3.5rem.
  Use line-height: 1.08 on hero headlines (tight = more impact).
  NEVER use gradient-text, -webkit-text-fill-color: transparent, or background-clip: text on hero headings.

SECTION PATTERNS (use ONLY these — match each section's "pattern" field exactly):

{pattern_templates}

EVERY section with items MUST use the matching pattern structure.

CONTAINER WIDTH RULES (embedded in pattern class names):
- container-wide (1400px): hero patterns — wide breathing room
- container (1200px): features, pricing, testimonials, team, gallery, contact, stats, cta, footer
- container-narrow (800px): faq, testimonial_slider, feature_stacked, feature_steps, cta_centered, timeline
- container-xs (600px): newsletter_cta

BACKGROUND ORBS — TEMPLATE DECISION (not optional):
  IF theme == "dark": include these two orb divs (use --secondary and --accent for color, NEVER --primary):
  <div style="position:fixed;width:400px;height:400px;border-radius:50%;z-index:-1;pointer-events:none;top:-6rem;left:-6rem;opacity:0.15;background:var(--secondary);filter:blur(120px);animation:floatOrb 20s ease-in-out infinite"></div>
  <div style="position:fixed;width:500px;height:500px;border-radius:50%;z-index:-1;pointer-events:none;bottom:-9rem;right:-9rem;opacity:0.15;background:var(--accent);filter:blur(120px);animation:floatOrb 25s ease-in-out infinite reverse"></div>
  IF theme == "light": OMIT orb divs entirely.

SECTION WRAPPER — every content section:
  <section data-section-type="TYPE">
    <!-- pattern content here -->
  </section>
  The CSS handles section padding via section[data-section-type].
  For hero_full_image / hero_video_bg / hero_center with bg image: add class "hero-edge" on the section.
  Logo cloud sections: add style="padding: 2.5rem 0" (compact).
  Footer: add a dark background via style="background: #1a1a2e".

ADDITIONAL HTML RULES:
- Each {{IMG:...}} placeholder MUST have a DIFFERENT query. Never reuse.
- Footer copyright: use &copy; <span id="year"></span> Brand Name — JS sets current year.
- Do NOT hardcode a year like &copy; 2024.
- REMINDER: ALL images must use {{IMG:role query}} placeholders. Real URLs will 404.
- ICON COLOR RULE: ALWAYS use color: var(--accent) for icons and check marks (via icon-box, stat-icon). On dark themes, --primary may be invisible. --accent is always bright.

NAVBAR SEARCH — add a search toggle button in nav-links with a dropdown input. Class: search-toggle, search-dropdown.

WHATSAPP FLOAT — ALWAYS add on the LEFT side: <a href="https://wa.me/971XXXXXXXXX" class="whatsapp-float" style="position:fixed;bottom:1.5rem;left:1.5rem;width:3.5rem;height:3.5rem;background:#25D366;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:1.5rem;box-shadow:0 4px 12px rgba(0,0,0,0.15);z-index:50;transition:transform 0.3s"><i class="fa-brands fa-whatsapp"></i></a>

BACK-TO-TOP — add on the RIGHT side (opposite to WhatsApp): <button id="back-to-top" style="position:fixed;bottom:1.5rem;right:1.5rem;width:2.75rem;height:2.75rem;background:var(--primary);color:white;border-radius:50%;display:flex;align-items:center;justify-content:center;border:none;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.15);opacity:0;pointer-events:none;transition:all 0.3s;z-index:50"><i class="fa-solid fa-chevron-up" style="font-size:0.8rem"></i></button>
IMPORTANT: WhatsApp button goes bottom-LEFT, Back-to-top goes bottom-RIGHT. They must be on OPPOSITE sides of the screen. NEVER put them on the same side.

IMAGE OPTIMIZATION — for every <img> tag:
- ALWAYS add loading="lazy" (except hero images — hero loads eagerly)
- ALWAYS add decoding="async"
- ALWAYS add a descriptive alt text

VANILLA-TILT.JS — add data-tilt ONLY on card_grid and feature_cards patterns (NOT on every card):
  On card_grid and feature_cards ONLY: add data-tilt data-tilt-max="8" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.15"

TSPARTICLES — CONDITIONAL: ONLY add on dark-theme tech or creative sites:
  <div id="tsparticles" style="position:absolute;inset:0;z-index:0"></div>
  Place INSIDE the hero section, before the text content. Text content must have class z-10.

SPLITTING.JS — CONDITIONAL: ONLY add on creative, portfolio, or agency sites:
  <h2 data-splitting class="section-title">Headline</h2>

LENIS SMOOTH SCROLL — always active. JS initializes Lenis automatically.

DESIGN QUALITY — what makes a website look "designed" vs "generated":

  COMMIT TO AN AESTHETIC: The plan specifies a design style. Execute it with FULL commitment:
  - Dark themes: use near-black backgrounds (#0a0a0f, #09090b, #0c0a14), NOT dark gray (#333 or #555). Surface should be 5-10% lighter than bg. Accent colors should POP against the dark base.
  - Light themes: use tinted whites (#faf8f5, #f5f3f0, #f8f9fa), NOT pure white (#ffffff for bg). Use pure white (#ffffff) only for surface/cards. Add depth with subtle warm or cool tints.
  - NEVER use raw Tailwind defaults (#3b82f6, #22c55e, #ef4444, #f59e0b) — desaturate 15-30% or shift hue to make them unique.
  - Text should NEVER be pure #000000 — use tinted blacks (#111827, #1a202c, #2a2520).
  - Every design choice should reinforce the aesthetic. No mixing styles.

  TYPOGRAPHY (non-negotiable):
  - Hero headline: hero-heading class = clamp(2.5rem, 6vw, 4.5rem) (MASSIVE and impactful)
  - NEVER use Inter, Roboto, Arial, or system-ui for HEADINGS — these scream "generic"
  - Use the EXACT fonts from the plan — heading fonts should be distinctive and memorable
  - Premium heading fonts: Playfair Display, Cormorant Garamond, DM Serif Display, Space Grotesk, Syne, Outfit, Cabinet Grotesk, Sora, Clash Display, Noto Serif Display, Libre Baskerville
  - Inter/DM Sans are acceptable ONLY for body text, never headings
  - Small labels/tags: use .section-label class

  VISUAL DEPTH & TEXTURE (what separates good from great):
  - Large faded text as background texture: .bg-number
  - Pseudo-elements (::before, ::after) for hover effects and decorative lines
  - Section-specific custom CSS
  - CSS noise texture on dark themes

  COLOR:
  - Gradient text on hero: use .gradient-text
  - Use color-mix() for section alternation
  - Accent color for: CTAs, icons, links, tags, hover borders
  - Glass-morphism on dark: background rgba(255,255,255,0.05), backdrop-filter blur(16px), border rgba(255,255,255,0.1)

  IMAGES:
  - Section images: max-height 400px, object-fit cover. Card images max-height 240px.
  - Do NOT add min-height > 400px on images. Let natural aspect ratio + max-height constrain them.
  - EVERY <img> must have loading="lazy" decoding="async" (except hero)

SEO META — after </style>, add: <!-- SEO_META --> with meta description (150 chars), og:title, og:description, og:type, twitter:card, robots, canonical. <!-- END_SEO_META -->

FAVICON — after SEO block: <!-- FAVICON --> with SVG favicon using brand initial + primary color. <!-- END_FAVICON -->

Do NOT add breadcrumbs to single-page websites.

FOOTER VISIBILITY — CRITICAL CSS RULES:
- NEVER use height:100vh on body, html, or any top-level wrapper. Use min-height:100vh instead.
- NEVER use overflow:hidden on body or html. Use overflow-x:hidden if needed (to prevent horizontal scroll).
- NEVER wrap the entire page content in a div with height:100vh or overflow:hidden — this clips the footer off-screen.
- The footer MUST always be visible at the bottom of the page after scrolling through all content.
- The body CSS is already set above with overflow-x:hidden and min-height:100vh — do NOT override these.

═══════════════════════════════════════════════════════════════
FINAL CHECKLIST — verify BEFORE outputting your HTML:
═══════════════════════════════════════════════════════════════
1. NAVBAR ANCHORS: Every navbar <a> links to a section using href="#section-type" (e.g. href="#services", href="#about", href="#contact"). NO dead links (href="#" or href="/").
2. SECTION IDs: Every <section data-section-type="X"> also has id="X" so anchor links work.
3. HERO IS PRESENT: The first section after <nav> is a hero with H1 heading, subtitle, CTA button, and an image (background or split).
4. HERO HAS IMAGE: Hero uses either background-image with {{IMG:...}} or an <img> tag. Never a plain solid color background.
5. HERO TEXT VISIBLE: White text on image heroes, dark text on light split heroes. Text-shadow on image heroes.
6. ALL PLAN CONTENT USED: Every section from the plan is included with its actual content — headlines, descriptions, items.
7. NO DEAD CTA LINKS: CTA buttons link to relevant sections (href="#contact", href="#services"), not href="#"."""
