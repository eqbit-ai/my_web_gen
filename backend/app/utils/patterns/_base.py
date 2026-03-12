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
/* Intentional section background rhythm */
section[data-section-type="features"],
section[data-section-type="stats"] {{ background: var(--bg-surface); }}
section[data-section-type="testimonials"],
section[data-section-type="pricing"] {{ background: color-mix(in srgb, var(--primary) 4%, var(--bg)); }}
/* Featured pricing card */
.pricing-card.featured {{ transform: scale(1.05); border: 2px solid var(--primary) !important; z-index: 1; }}
/* Card hover choreography */
.card-hover {{ position: relative; overflow: hidden; border-left: 3px solid transparent; transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease; }}
.card-hover:hover {{ transform: translateY(-8px); box-shadow: 0 20px 60px rgba(0,0,0,0.12); border-left-color: var(--accent); }}
.card-hover::before {{ content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 8%, transparent), transparent); transition: left 0.6s ease; }}
.card-hover:hover::before {{ left: 100%; }}
.card-hover:hover h3 {{ color: var(--accent); transition: color 0.3s ease; }}
/* Gradient text utility */
.gradient-text {{ background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
/* Staggered grid reveals */
.card-grid > *:nth-child(3n+1) {{ transition-delay: 0ms; }}
.card-grid > *:nth-child(3n+2) {{ transition-delay: 120ms; }}
.card-grid > *:nth-child(3n+3) {{ transition-delay: 240ms; }}
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
The <style> block above is a MINIMUM — you MUST add MORE custom CSS below the closing comment for:
- Card hover effects (::before, ::after pseudo-elements for shine/border reveals)
- Hero decorative elements (.hero-bg-element, .gradient-text, etc.)
- Section-specific backgrounds and textures
- Custom animation @keyframes beyond the basics above
- Testimonial/slider transition styles
- Mobile responsive tweaks for custom layouts
A good website needs 150-300 lines of custom CSS. Do NOT rely only on Tailwind utilities.

TAILWIND CLASS REFERENCE (use these consistently):
- Section wrapper: class="py-16 md:py-20 relative"
- Section header: <div class="text-center mb-8 md:mb-10">
    <h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">...</h2>
    <p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">...</p>
  </div>
- Container wide: class="max-w-[1400px] mx-auto px-6"
- Container: class="max-w-[1200px] mx-auto px-6"
- Container narrow: class="max-w-[800px] mx-auto px-6"
- Card: class="card-hover bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md border border-white/[0.06]"
  (light theme: use border-gray-100 instead of border-white/[0.06])
  The card-hover class provides coordinated hover effects (translate, shadow, border-left, shine sweep, title color change) — do NOT add separate hover:-translate-y-2 hover:shadow-xl when using card-hover.
- Card icon box: class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--accent)] mb-5" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"
- ICON COLOR RULE (CRITICAL): ALWAYS use text-[var(--accent)] for icons and check marks, NOT text-[var(--primary)]. On dark themes, --primary is often a dark color that becomes invisible. --accent is always bright. This applies to: card icons, pricing check marks, stat icons, feature icons.
- Btn primary: class="inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg border-none cursor-pointer"
- Btn secondary: class="inline-block border-2 border-[var(--primary)] text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:bg-[var(--primary)] hover:text-white bg-transparent"
- Grid 3-col: class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
- Grid 4-col: class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center"
- Image: class="w-full h-auto rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]" loading="lazy"
- EVERY <img> tag MUST include loading="lazy" for performance (except hero images which should load eagerly)
- Dark theme navbar: class="fixed top-0 w-full z-50 backdrop-blur-md bg-black/40 border-b border-white/[0.08] transition-all duration-300"
- Light theme navbar: class="fixed top-0 w-full z-50 backdrop-blur-md bg-white/85 border-b border-black/[0.06] transition-all duration-300"

⚠️ MANDATORY IMAGE RULES — VIOLATION = BROKEN OUTPUT ⚠️
NEVER write real image URLs (pexels.com, unsplash.com, etc). They will ALL 404.
The ONLY way to include images is the {{IMG:role query}} placeholder system:
- For EVERY <img> tag: src="{{IMG:role query keywords}}"
- For EVERY background-image: url('{{IMG:background query keywords}}')
- Format: <img src="{{IMG:role query keywords}}" alt="descriptive alt text" class="w-full h-auto rounded-xl object-cover">
- IMAGE ROLES: hero, product, feature, gallery, team, testimonial, background, cta, mockup
- Use the EXACT image_query from the plan — do NOT simplify or shorten
- Each placeholder MUST have a DIFFERENT query — never reuse
- ABSOLUTELY NO hardcoded URLs from pexels.com, unsplash.com, or any other domain
- ABSOLUTELY NO /images/ or /logos/ paths
- If you write a real URL instead of {{IMG:...}}, the image WILL be broken

CRITICAL: Match each section's "pattern" field to the EXACT HTML structure below.

LOGO MARK — use a gradient icon/initial in navbar. Pick one:
  - Initial: <span class="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-sm shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">X</span>
  - Icon: same but with <i class="fa-solid fa-icon"></i> inside
  - Monogram: same but with two initials (e.g. "HC")
  Vary the style per brand.

TYPED.JS HERO EFFECT — adds a typewriter animation to the hero headline. Use freely on any hero:
  Replace the static headline text with:
    <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-none mb-6 text-[var(--text)]">
      <span class="typed-text" data-typed='["First Phrase Here", "Second Phrase Here", "Third Phrase Here"]'></span>
    </h1>
  The JS stage auto-detects .typed-text and initializes Typed.js. Use 3-4 different phrases that showcase the brand.

HERO DEPTH ELEMENTS — add at least 2 of these to every hero section for visual richness:
  1. Giant faded decorative text (absolute positioned behind hero content):
     <span class="absolute right-[5%] top-[10%] text-[clamp(100px,20vw,300px)] font-bold opacity-[0.04] pointer-events-none select-none" style="font-family: var(--font-heading)">01</span>
  2. Section label above headline (small uppercase tag):
     <span class="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[var(--accent)] mb-6"><span class="w-10 h-[2px] bg-[var(--accent)]"></span>LABEL TEXT</span>
  3. Staggered entrance: add class="hero-stagger" on headline, subheadline, and CTA wrapper with style="animation-delay: 0.2s/0.4s/0.6s"
  4. Stats mini-bar in hero (for dark themes): 2-3 key stats in a glassmorphism strip at bottom of hero

HERO HEADLINE SIZE — NEVER use text-3xl or text-4xl for hero headlines. MINIMUM is text-5xl md:text-6xl lg:text-7xl.
  - Display fonts (Oswald, Black Ops One, Bebas Neue): use text-6xl md:text-7xl lg:text-8xl
  - Serif display fonts (Playfair Display, DM Serif Display): use text-5xl md:text-6xl lg:text-7xl
  - Use leading-none or leading-tight on hero headlines (tight line-height = more impact)

SECTION PATTERNS (use ONLY these — match each section's "pattern" field exactly):

{pattern_templates}

EVERY section with items MUST use the matching Tailwind pattern structure.

CONTAINER WIDTH RULES (embedded in each pattern's classes):
- max-w-[1400px]: hero patterns — wide breathing room
- max-w-[1200px]: card_grid, icon_grid, feature_split, feature_cards, pricing, testimonials, team, gallery_grid, image_carousel, service_modal, contact, stats, cta_banner/split, logo_cloud, footer — standard width
- max-w-[800px] or max-w-[700px]: faq, hero_minimal, testimonial_slider, feature_stacked, feature_steps, cta_centered, timeline, comparison_table — narrow for readability
- max-w-[600px]: newsletter_cta — tight for email signup focus

BACKGROUND ORBS — TEMPLATE DECISION (not optional):
  IF theme == "dark": include these two orb divs (use --secondary and --accent for color, NEVER --primary which may be near-black):
  <div class="fixed w-[400px] h-[400px] rounded-full -z-10 pointer-events-none -top-24 -left-24 opacity-[0.15] animate-[floatOrb_20s_ease-in-out_infinite]" style="background: var(--secondary); filter: blur(120px)"></div>
  <div class="fixed w-[500px] h-[500px] rounded-full -z-10 pointer-events-none -bottom-36 -right-36 opacity-[0.15] animate-[floatOrb_25s_ease-in-out_infinite_reverse]" style="background: var(--accent); filter: blur(120px)"></div>
  IF theme == "light": OMIT orb divs entirely — do NOT generate them. Zero orb divs in output. They look muddy on light backgrounds.

SECTION WRAPPER — every content section:
  <section data-section-type="TYPE" class="py-16 md:py-20 relative">
    <!-- pattern content here -->
  </section>
  EXCEPTION: Hero sections use NO py padding — just <section data-section-type="hero" class="relative">
  For hero_full_image / hero_video_bg / hero_center with bg image: add class "-mt-[80px]" on the section to pull it UP behind the fixed navbar (edge-to-edge hero with no gap).
  HERO IMAGE OVERLAY: Use a GRADIENT overlay, not flat black. Options:
    - Left-to-right: bg-gradient-to-r from-black/60 via-black/40 to-transparent (text left, image visible right)
    - Top-to-bottom: bg-gradient-to-b from-black/50 via-black/40 to-black/60 (centered text)
    NEVER use flat bg-black/70 — the image must be clearly visible through the overlay.
  Logo cloud sections: use py-10 md:py-12 (compact).
  Footer: use py-14 md:py-16 and a dark background.

ADDITIONAL HTML RULES:
- Each {{IMG:...}} placeholder MUST have a DIFFERENT query. Never reuse.
- Footer copyright: use &copy; <span id="year"></span> Brand Name — JS sets current year.
- Do NOT hardcode a year like &copy; 2024.
- REMINDER: ALL images must use {{IMG:role query}} placeholders. Real URLs (pexels.com, unsplash.com) will 404.
- BTN_PRIMARY_CLASSES = inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg border-none cursor-pointer
- BTN_SECONDARY_CLASSES = inline-block border-2 border-[var(--primary)] text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:bg-[var(--primary)] hover:text-white bg-transparent

NAVBAR SEARCH — add a search toggle button in nav-links with a dropdown input. Class: search-toggle, search-dropdown.

WHATSAPP FLOAT — ALWAYS add: <a href="https://wa.me/971XXXXXXXXX" class="whatsapp-float fixed bottom-6 right-6 w-14 h-14 bg-[#25D366] rounded-full flex items-center justify-center text-white text-2xl shadow-lg hover:scale-110 transition-all z-50"><i class="fa-brands fa-whatsapp"></i></a>

BACK-TO-TOP — add: <button id="back-to-top" class="fixed bottom-6 right-24 w-11 h-11 bg-[var(--primary)] text-white rounded-full flex items-center justify-center shadow-lg opacity-0 pointer-events-none transition-all z-50"><i class="fa-solid fa-chevron-up text-sm"></i></button>

IMAGE OPTIMIZATION — for every <img> tag:
- ALWAYS add loading="lazy" (except hero images — hero loads eagerly)
- ALWAYS add decoding="async"
- ALWAYS add a descriptive alt text (not empty, not generic)
- Use appropriate sizing classes: hero images h-[80vh] or min-h-[500px], feature images h-48 or h-64, team photos h-64 or h-72

VANILLA-TILT.JS — add data-tilt ONLY on card_grid and feature_cards patterns (NOT on every card):
  On card_grid and feature_cards ONLY: add data-tilt data-tilt-max="8" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.15"
  Do NOT add data-tilt to pricing_table, team_cards, testimonials, or other sections. JS automatically disables on mobile touch devices.

TSPARTICLES — CONDITIONAL: ONLY add on dark-theme tech or creative sites. Do NOT add on light themes, food, health, wedding, corporate, or nature sites:
  <div id="tsparticles" class="absolute inset-0 z-0"></div>
  Place INSIDE the hero section, before the text content. Text content must have class="relative z-10".
  JS initializes with a subtle network/dots config. ONLY use when the design theme is dark AND the industry is tech, SaaS, creative, or gaming.

SPLITTING.JS — CONDITIONAL: ONLY add on creative, portfolio, or agency sites. Do NOT add on corporate, health, education, or food sites:
  <h2 data-splitting class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2>
  JS calls Splitting() on [data-splitting] elements. Only use for creative/portfolio/agency brands where dramatic text animation fits the aesthetic.

LENIS SMOOTH SCROLL — always active. JS initializes Lenis for buttery smooth page scrolling automatically.

DESIGN QUALITY — what makes a website look "designed" vs "generated":

  COMMIT TO AN AESTHETIC: The plan specifies a design style. Execute it with FULL commitment:
  - Dark themes: use near-black backgrounds (#0a0a0a), not dark gray (#333). Accent colors should POP.
  - Light themes: use warm whites (#faf9f6 or #f8f7f4), not pure white (#fff). Add depth with subtle tints.
  - Every design choice should reinforce the aesthetic. No mixing styles.

  TYPOGRAPHY (non-negotiable):
  - Hero headline: text-5xl md:text-6xl lg:text-7xl font-bold (MASSIVE and impactful — NEVER text-3xl or text-4xl)
  - NEVER use Inter, Roboto, Arial, or system-ui — these scream "generic"
  - Use the EXACT fonts from the plan. Make them distinctive.
  - Small labels/tags: text-xs uppercase tracking-widest font-semibold text-[var(--accent)]

  SPACING:
  - Sections: py-20 md:py-28 (generous — never cramped)
  - Hero: min-h-[85vh] with content vertically centered
  - Card padding: p-6 md:p-8 (never less than p-5)

  VISUAL DEPTH & TEXTURE (what separates good from great):
  - Large faded text as background texture: position absolute, font-size 6-8rem, opacity 0.03-0.06
  - Pseudo-elements (::before, ::after) for hover effects and decorative lines — never extra divs
  - CSS noise texture on dark themes: use SVG data URI feTurbulence as subtle overlay
  - Diagonal clip-path on at least one element (buttons or section dividers)
  - Sticky elements for interactive depth (e.g. sticky sidebar in program sections)
  - gap: 2px on grids for industrial seam effect (when bold/industrial aesthetic)

  ANIMATIONS (CSS-only, no libraries needed):
  - IntersectionObserver scroll reveals on all sections (JS stage adds this)
  - Hover transitions on ALL interactive elements: transform, box-shadow, border-color
  - Hero elements: staggered entrance with animation-delay (0.2s, 0.4s, 0.6s)
  - Counter animations on stats (JS stage handles)
  - Testimonial auto-scroll or marquee for social proof

  COLOR:
  - Gradient text on hero headline: bg-clip-text text-transparent bg-gradient-to-r
  - Use color-mix() for section alternation: color-mix(in srgb, var(--bg-surface) 50%, var(--bg))
  - Accent color for: CTAs, icons, links, tags, hover borders
  - Glass-morphism on dark: bg-white/[0.05] backdrop-blur-lg border border-white/[0.1]

  IMAGES:
  - Hero images: min-h-[500px] object-cover, use overlay gradient for text readability
  - EVERY <img> must have loading="lazy" decoding="async" (except hero)

SEO META — after </style>, add: <!-- SEO_META --> with meta description (150 chars), og:title, og:description, og:type, twitter:card, robots, canonical. <!-- END_SEO_META -->

FAVICON — after SEO block: <!-- FAVICON --> with SVG favicon using brand initial + primary color. <!-- END_FAVICON -->

Do NOT add breadcrumbs to single-page websites."""
