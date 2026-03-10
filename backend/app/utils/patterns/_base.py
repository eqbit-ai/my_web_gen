"""
Core HTML generation rules — always included in every prompt.
This is the skeleton: style block, Tailwind reference, image rules, etc.
Pattern-specific templates are injected dynamically.
"""

# The {plan_json} and {pattern_templates} and {style_additions} placeholders
# are filled by build_html_prompt() in prompt_pipeline.py

HTML_CORE_PROMPT = """You are an expert frontend developer. Generate HTML with Tailwind CSS utility classes.

WEBSITE PLAN:
{plan_json}

RULES:
- Return ONLY HTML inside a single ```html code block
- Output a <style> block FIRST (for CSS variables, fonts, animations) then the HTML body content
- NO <html>, <head>, <body>, <link>, <meta> tags — just <style> block + body content
- Do NOT add Font Awesome <script> or <link> tags (e.g. kit.fontawesome.com) — Font Awesome is already loaded by the host page. Just use <i class="fa-solid fa-xxx"> icons directly.
- Use Tailwind CSS utility classes for ALL layout, spacing, typography, colors, responsive design, hover effects
- Use CSS variables via Tailwind arbitrary values: text-[var(--primary)], bg-[var(--bg)], rounded-[var(--radius)], etc.
- Use semantic HTML5: <nav>, <header>, <main>, <section>, <footer>
- EVERY content section MUST use: <section data-section-type="{{type}}"> — never <div>
- Use the EXACT content from the plan — headlines, descriptions, button text, etc.
- Use Font Awesome icons exactly as specified: <i class="fa-solid fa-icon-name"></i>
- Add data-aos animations on grid items (cards, faq items, etc.) — NOT on section wrappers
- ANIMATION VARIETY IS CRITICAL: You MUST use at least 3 DIFFERENT data-aos values across the page:
  * Section 1 cards: data-aos="fade-up"
  * Section 2 items: data-aos="fade-right" or "fade-left"
  * Section 3 items: data-aos="zoom-in"
  * Section 4 items: data-aos="flip-up"
  Do NOT use fade-up on every section — this makes all websites look identical.
- Stagger grid items: data-aos-delay="100", "200", "300"
- Hero and navbar must NOT have data-aos (visible immediately)
- Include ALL sections from the plan
- Do NOT include any JavaScript
- Do NOT include any explanation, just the html code block

STYLE BLOCK — output this FIRST before any HTML elements:
<style>
@import url('https://fonts.googleapis.com/css2?family=HEADING_FONT:wght@400;500;600;700;800&family=BODY_FONT:wght@400;500;600&display=swap');
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
}}
body {{ font-family: var(--font-body); background: var(--bg); color: var(--text); line-height: 1.6; padding-top: 80px; }}
h1, h2, h3, h4, h5, h6 {{ font-family: var(--font-heading); }}
section[data-section-type] {{ opacity: 0; transform: translateY(30px); transition: opacity 0.6s ease, transform 0.6s ease; animation: sectionFallback 0.8s ease forwards; animation-delay: 1s; }}
section[data-section-type].visible {{ opacity: 1; transform: translateY(0); animation: none; }}
@keyframes sectionFallback {{ to {{ opacity: 1; transform: translateY(0); }} }}
/* AOS fallback: reveal items after 1.5s if AOS doesn't fire */
[data-aos] {{ animation: sectionFallback 0.6s ease forwards; animation-delay: 1.5s; }}
[data-aos].aos-animate {{ animation: none; }}
footer, footer section[data-section-type] {{ opacity: 1; transform: none; }}
.faq-answer {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }}
.faq-item.active .faq-answer {{ max-height: 500px; padding-bottom: 1.25rem; }}
.faq-item.active .faq-question i {{ transform: rotate(180deg); transition: transform 0.3s; }}
.testimonial-slide {{ display: none; }}
.testimonial-slide.active {{ display: block; }}
/* Nav link underline animation */
.nav-links a {{ position: relative; }}
.nav-links a::after {{ content: ""; position: absolute; bottom: -4px; left: 0; width: 0; height: 2px; background: var(--primary); transition: width 0.3s ease; }}
.nav-links a:hover::after {{ width: 100%; }}
/* Navbar scroll effect */
nav.nav-scrolled {{ background: var(--bg) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.1); backdrop-filter: blur(16px); }}
/* Alternate section backgrounds */
section[data-section-type]:nth-of-type(even) {{ background: color-mix(in srgb, var(--bg-surface) 50%, var(--bg)); }}
/* Featured pricing card */
.pricing-card.featured {{ transform: scale(1.05); border: 2px solid var(--primary) !important; z-index: 1; }}
@keyframes floatOrb {{ 0% {{ transform: translateY(0); }} 50% {{ transform: translateY(-30px); }} 100% {{ transform: translateY(0); }} }}
@keyframes logoGradient {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
@keyframes gradientShift {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
@media (max-width: 768px) {{
  .nav-links {{ display: none !important; position: fixed; top: 70px; left: 0; right: 0; flex-direction: column; padding: 1.5rem 2rem; gap: 1.25rem; z-index: 999; border-bottom: 1px solid rgba(255,255,255,0.08); }}
  .nav-links.active {{ display: flex !important; background: var(--bg); backdrop-filter: blur(12px); box-shadow: 0 10px 30px rgba(0,0,0,0.15); }}
  .nav-toggle {{ display: block !important; }}
  .nav-cta {{ display: none !important; }}
  .mobile-cta {{ display: block !important; }}
}}
{style_additions}
.typed-cursor {{ color: var(--primary); font-weight: 100; }}
.search-dropdown.active {{ display: block; }}
#back-to-top.visible {{ opacity: 1; pointer-events: auto; }}
.whatsapp-float {{ animation: floatOrb 3s ease-in-out infinite; animation-duration: 3s; }}
[data-splitting] .char {{ display: inline-block; opacity: 0; transform: translateY(20px); transition: opacity 0.4s ease, transform 0.4s ease; }}
[data-splitting].visible .char {{ opacity: 1; transform: translateY(0); }}
@media (max-width: 768px) {{ .steps-container::before {{ left: 24px; }} .timeline-container::before {{ left: 98px; }} }}
</style>
Fill in ALL values from the plan's design spec. Use the EXACT colors, fonts, and radii.

TAILWIND CLASS REFERENCE (use these consistently):
- Section wrapper: class="py-16 md:py-20 relative"
- Section header: <div class="text-center mb-8 md:mb-10">
    <h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">...</h2>
    <p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">...</p>
  </div>
- Container wide: class="max-w-[1400px] mx-auto px-6"
- Container: class="max-w-[1200px] mx-auto px-6"
- Container narrow: class="max-w-[800px] mx-auto px-6"
- Card: class="bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06]"
  (light theme: use border-gray-100 instead of border-white/[0.06])
- Card icon box: class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--accent)] mb-5" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"
- ICON COLOR RULE (CRITICAL): ALWAYS use text-[var(--accent)] for icons, NOT text-[var(--primary)]. On dark themes, --primary is often a dark color that becomes invisible against dark backgrounds. --accent is always a bright, high-contrast color.
- Btn primary: class="inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg border-none cursor-pointer"
- Btn secondary: class="inline-block border-2 border-[var(--primary)] text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:bg-[var(--primary)] hover:text-white bg-transparent"
- Grid 3-col: class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
- Grid 4-col: class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center"
- Image: class="w-full h-auto rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]" loading="lazy"
- EVERY <img> tag MUST include loading="lazy" for performance (except hero images which should load eagerly)
- Dark theme navbar: class="fixed top-0 w-full z-50 backdrop-blur-md bg-black/40 border-b border-white/[0.08] transition-all duration-300"
- Light theme navbar: class="fixed top-0 w-full z-50 backdrop-blur-md bg-white/85 border-b border-black/[0.06] transition-all duration-300"

IMAGE RULES — use the {{IMG:role query}} placeholder system:
- For EVERY <img> tag, use a role prefix + the image_query from the plan
- Format: <img src="{{IMG:role query keywords}}" alt="descriptive alt text" class="w-full h-auto rounded-xl object-cover">
- IMAGE ROLES: hero, product, feature, gallery, team, testimonial, background, cta, mockup
- Use the EXACT image_query from the plan — do NOT simplify or shorten
- Each placeholder MUST have a DIFFERENT query — never reuse
- NEVER use hardcoded URLs — ONLY {{IMG:role query}} format
- Do NOT use /images/ or /logos/ paths

CRITICAL: Match each section's "pattern" field to the EXACT HTML structure below.

LOGO MARK RULES — generate a unique logo for each brand (NOT a plain colored square):
  Choose ONE of these logo styles based on the brand and industry:

  STYLE A — Brand initial in gradient circle (best for single-word brands):
    <span class="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-sm shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">H</span>
    (Use the first letter of the brand name)

  STYLE B — Industry icon in gradient square (best for service businesses):
    <span class="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center text-white text-sm shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))"><i class="fa-solid fa-scale-balanced"></i></span>
    (Pick a Font Awesome icon that matches the industry)

  STYLE C — Two initials monogram (best for multi-word brands like "Harrison & Cole"):
    <span class="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center text-white font-bold text-xs tracking-wider shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">HC</span>

  STYLE D — Inline SVG logo mark (best for tech/modern brands):
    <svg class="w-9 h-9 flex-shrink-0" viewBox="0 0 36 36" fill="none">
      <rect width="36" height="36" rx="8" fill="url(#logo-grad)"/>
      <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9"/>
      <path d="M14 18L20 12L26 18L20 24Z" fill="white" opacity="0.6"/>
      <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="36" y2="36"><stop stop-color="var(--primary)"/><stop offset="1" stop-color="var(--secondary)"/></linearGradient></defs>
    </svg>
    (Create a UNIQUE simple geometric SVG for each brand. NEVER reuse the same SVG path.)

  Pick the style that best matches the brand personality. Vary across generations.

TYPED.JS HERO EFFECT — adds a typewriter animation to the hero headline. Use freely on any hero:
  Replace the static headline text with:
    <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-[var(--text)]">
      <span class="typed-text" data-typed='["First Phrase Here", "Second Phrase Here", "Third Phrase Here"]'></span>
    </h1>
  The JS stage auto-detects .typed-text and initializes Typed.js. Use 3-4 different phrases that showcase the brand.

SECTION PATTERNS (use ONLY these — match each section's "pattern" field exactly):

{pattern_templates}

EVERY section with items MUST use the matching Tailwind pattern structure.

CONTAINER WIDTH RULES (embedded in each pattern's classes):
- max-w-[1400px]: hero patterns — wide breathing room
- max-w-[1200px]: card_grid, icon_grid, feature_split, feature_cards, pricing, testimonials, team, gallery_grid, image_carousel, service_modal, contact, stats, cta_banner/split, logo_cloud, footer — standard width
- max-w-[800px] or max-w-[700px]: faq, hero_minimal, testimonial_slider, feature_stacked, feature_steps, cta_centered, timeline, comparison_table — narrow for readability
- max-w-[600px]: newsletter_cta — tight for email signup focus

BACKGROUND ORBS — add as first children inside <main> or right after <nav>:
  <div class="fixed w-[400px] h-[400px] rounded-full -z-10 pointer-events-none -top-24 -left-24 opacity-[0.15] animate-[floatOrb_20s_ease-in-out_infinite]" style="background: var(--primary); filter: blur(120px)"></div>
  <div class="fixed w-[500px] h-[500px] rounded-full -z-10 pointer-events-none -bottom-36 -right-36 opacity-[0.15] animate-[floatOrb_25s_ease-in-out_infinite_reverse]" style="background: var(--secondary); filter: blur(120px)"></div>
  On light themes: use opacity-[0.08] instead.

SECTION WRAPPER — every content section:
  <section data-section-type="TYPE" class="py-16 md:py-20 relative">
    <!-- pattern content here -->
  </section>
  EXCEPTION: Hero sections use NO py padding — just <section data-section-type="hero" class="relative">
  For hero_full_image / hero_video_bg / hero_center with bg image: add class "-mt-[80px]" on the section to pull it UP behind the fixed navbar (edge-to-edge hero with no gap).
  HERO IMAGE OVERLAY: When using background-image on hero, use bg-black/40 (40% opacity max). NEVER use bg-black/60 or darker — the image must be clearly visible through the overlay. The hero image is the most important visual on the page.
  Logo cloud sections: use py-10 md:py-12 (compact).
  Footer: use py-14 md:py-16 and a dark background.

ADDITIONAL HTML RULES:
- Each {{IMG:...}} placeholder MUST have a DIFFERENT query. Never reuse.
- Footer copyright: use &copy; <span id="year"></span> Brand Name — JS sets current year.
- Do NOT hardcode a year like &copy; 2024.
- Do NOT use hardcoded Unsplash URLs — ONLY {{IMG:role query}} placeholders.
- BTN_PRIMARY_CLASSES = inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg border-none cursor-pointer
- BTN_SECONDARY_CLASSES = inline-block border-2 border-[var(--primary)] text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:bg-[var(--primary)] hover:text-white bg-transparent

NAVBAR SEARCH BAR — add expandable search to the navbar (inside .nav-links, before the mobile CTA):
  <li class="relative">
    <button class="search-toggle bg-transparent border-none text-[var(--text)] cursor-pointer p-2 hover:text-[var(--primary)] transition-colors" aria-label="Search"><i class="fa-solid fa-magnifying-glass"></i></button>
    <div class="search-dropdown hidden absolute right-0 top-full mt-2 w-64 bg-[var(--bg-surface)] rounded-[var(--radius)] shadow-xl border border-white/10 p-3 z-50">
      <input type="text" placeholder="Search..." class="w-full p-2.5 rounded-lg border border-white/10 bg-[var(--bg)] text-[var(--text)] text-sm font-[inherit] focus:border-[var(--primary)] focus:outline-none">
    </div>
  </li>
  JS toggles .search-dropdown visibility on click. Click outside closes it.

WHATSAPP FLOATING BUTTON — add before </body> (after all sections, before footer or after footer):
  <a href="https://wa.me/971XXXXXXXXX" target="_blank" rel="noopener" class="whatsapp-float fixed bottom-6 right-6 w-14 h-14 bg-[#25D366] rounded-full flex items-center justify-center text-white text-2xl shadow-lg hover:scale-110 hover:shadow-xl transition-all duration-300 z-50" aria-label="Chat on WhatsApp">
    <i class="fa-brands fa-whatsapp"></i>
  </a>
  NOTE: Replace 971XXXXXXXXX with a plausible UAE number. ALWAYS include this on every website.

BACK-TO-TOP BUTTON — add before </body>:
  <button id="back-to-top" class="fixed bottom-6 right-24 w-11 h-11 bg-[var(--primary)] text-white rounded-full flex items-center justify-center shadow-lg opacity-0 pointer-events-none transition-all duration-300 z-50 hover:-translate-y-1 hover:shadow-xl" aria-label="Back to top">
    <i class="fa-solid fa-chevron-up text-sm"></i>
  </button>
  JS shows button (opacity-1, pointer-events-auto) when scrolled past 500px, hides when at top. Click scrolls to top smoothly.

IMAGE OPTIMIZATION — for every <img> tag:
- ALWAYS add loading="lazy" (except hero images — hero loads eagerly)
- ALWAYS add decoding="async"
- ALWAYS add a descriptive alt text (not empty, not generic)
- Use appropriate sizing classes: hero images h-[80vh] or min-h-[500px], feature images h-48 or h-64, team photos h-64 or h-72

VANILLA-TILT.JS — add data-tilt on card-based grids for a premium 3D hover effect:
  On card_grid, feature_cards, pricing_table, and team_cards: add data-tilt data-tilt-max="8" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.15"
  Apply on any grid of 3+ cards. JS automatically disables on mobile touch devices.

TSPARTICLES — add an animated particles background to the hero for a premium feel:
  <div id="tsparticles" class="absolute inset-0 z-0"></div>
  Place INSIDE the hero section, before the text content. Text content must have class="relative z-10".
  JS initializes with a subtle network/dots config. Works on both dark and light themes (opacity adjusts automatically).
  Use on dark themes, tech/SaaS brands, or any site that benefits from dynamic backgrounds.

SPLITTING.JS — add data-splitting on 2-3 key headlines for a letter-by-letter reveal animation:
  <h2 data-splitting class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2>
  JS calls Splitting() on [data-splitting] elements. Apply on the hero headline and 1-2 section headlines for maximum visual impact.

LENIS SMOOTH SCROLL — always active. JS initializes Lenis for buttery smooth page scrolling automatically.

PREMIUM DESIGN QUALITY — CRITICAL:
  Every website must look like it was designed by a top agency. Follow these rules:
  - Add custom CSS hover effects on cards: scale, shadow elevation, border glow, or color shifts
  - Use CSS transitions (300ms ease) on ALL interactive elements — buttons, cards, links, images
  - Add subtle box-shadow layers for depth: shadow-lg on cards, shadow-2xl on hover
  - Use backdrop-blur on overlapping elements (navbar, modals, dropdowns) for glass effect
  - Vary data-aos animations: mix fade-up, fade-right, fade-left, zoom-in — do NOT use only fade-up everywhere
  - Add gradient text on key headlines using bg-clip-text text-transparent bg-gradient-to-r
  - Use rounded-2xl or rounded-3xl on cards for modern softness
  - Ensure generous padding (py-16 md:py-24) between sections for breathing room
  - Apply hover:-translate-y-1 or hover:-translate-y-2 on cards for lift effect
  - Use ring-1 ring-white/10 borders on dark themes for subtle glass edges

SEO META TAGS — add these inside the <style> block as HTML comments (they'll be extracted to <head> by the renderer):
  After the closing </style> tag, add this comment block:
  <!-- SEO_META
  <meta name="description" content="COMPANY_DESCRIPTION — 150-160 chars summarizing the business">
  <meta name="keywords" content="keyword1, keyword2, keyword3, keyword4, keyword5">
  <meta property="og:title" content="BRAND_NAME — TAGLINE">
  <meta property="og:description" content="Same as meta description">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="BRAND_NAME — TAGLINE">
  <meta name="twitter:description" content="Same as meta description">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="#">
  END_SEO_META -->
  Fill in real values from the plan's brand name, description, and industry. Make the description compelling and keyword-rich.

FAVICON — add an SVG favicon using the brand's first letter and primary color:
  Include this right after the SEO_META comment block:
  <!-- FAVICON
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='PRIMARY_COLOR'/><text x='50' y='70' font-size='60' font-family='Arial,sans-serif' font-weight='bold' fill='white' text-anchor='middle'>FIRST_LETTER</text></svg>">
  END_FAVICON -->
  Replace PRIMARY_COLOR with the actual hex color (e.g., %2523F97316 — URL-encoded #). Replace FIRST_LETTER with the brand's first letter.

BREADCRUMBS — Do NOT add visible breadcrumbs to single-page websites. They add clutter with no navigation value on one-page sites."""
