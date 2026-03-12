"""
Multi-stage AI website generation pipeline.

Stage 1: Plan      → GPT-4.1 analyzes prompt → JSON structure + layout patterns
Stage 2: HTML      → Claude generates HTML with pure CSS classes + <style> block
Stage 3: JS        → Claude generates interactions/animations

CSS is embedded as semantic classes in a <style> block in the HTML output.
"""

import json
import random
import re

from app.utils.patterns import (
    format_style_hint,
    get_patterns_for_plan,
    get_random_style_preset,
    get_rotation_hints,
    get_style_additions_for_plan,
)
from app.utils.patterns._base import HTML_CORE_PROMPT

# ═══════════════════════════════════════════════════════════════════════
# COMPONENT PATTERN LIBRARY
# ═══════════════════════════════════════════════════════════════════════

COMPONENT_PATTERNS = {
    # Hero variants
    "hero_split": "Two-column hero: headline + subtitle + CTAs on left, image on right",
    "hero_center": "Centered hero: large headline, subtitle, CTAs, optional background image",
    "hero_full_image": "Full-width background image hero with overlay text centered",
    "hero_minimal": "Minimal hero: just a big headline, one-line subtitle, single CTA, lots of whitespace",
    "hero_video_bg": "Hero with video/animated gradient background, centered text overlay",
    "hero_product_mockup": "Hero with centered text above a large device mockup image (laptop/phone showing product UI)",
    "hero_mockup_center": "Centered hero with browser/device frame mockup below headline — great for SaaS product showcase",
    "hero_asymmetric": "Asymmetric hero with offset text and overlapping image/card elements for a modern editorial feel",
    # Feature variants
    "card_grid": "Grid of cards with icon, title, description. 3 columns desktop, 1 mobile",
    "icon_grid": "Compact grid with icon + title + short text. 3-4 columns",
    "feature_split": "Alternating rows: image left/text right, then text left/image right",
    "feature_cards": "Large image-top cards with title + description below. 3 columns",
    "feature_stacked": "Vertical stack: each feature is a full-width row with icon, title, and long description",
    "feature_steps": "Numbered vertical steps with connecting line — ideal for processes, onboarding flows, how-it-works",
    # Testimonial variants
    "testimonial_cards": "Grid of quote cards with avatar, name, role, company",
    "testimonial_slider": "Single large testimonial displayed at a time with dots/arrows navigation",
    "testimonial_split": "Two-column: large quote on left, author photo + info on right",
    # Team variants
    "team_grid": "Grid of team member cards with photo, name, role",
    "team_cards": "Team cards with large photo, name, role, and short bio text",
    "team_masonry": "Staggered masonry layout for team photos with overlay name/role on hover",
    # CTA variants
    "cta_banner": "Full-width dark/colored banner with headline + CTA buttons",
    "cta_split": "Two-column CTA: text + buttons on left, image or illustration on right",
    "cta_gradient": "Gradient background CTA with centered text, glowing button effect",
    "cta_centered": "Clean centered CTA with headline, subtitle, and single primary button on subtle background",
    # Other sections
    "pricing_table": "Side-by-side pricing cards with plan name, price, features list, CTA",
    "faq_accordion": "Expandable accordion: click question to reveal answer",
    "stats_row": "Horizontal row of large numbers with labels",
    "gallery_grid": "Image gallery grid with lightbox modal — click any image to view full-size",
    "image_carousel": "Full-width image/content carousel with prev/next arrows and indicator dots",
    "service_modal": "Grid of service/feature cards that open a detail modal on click with expanded info",
    "trust_badges": "Row of certification/trust badges with icons — SSL, ISO, GDPR, industry certifications",
    "timeline": "Vertical timeline with milestones — great for company history, roadmap, project phases",
    "newsletter_cta": "Email signup section with input field + subscribe button + short pitch",
    "comparison_table": "Side-by-side comparison table (us vs competitor or plan vs plan) with check/cross icons",
    "contact_split": "Two columns: contact info on left, form on right",
    "logo_cloud": "Row of partner/client logos",
    "logo_carousel": "Auto-scrolling horizontal logo strip — smoother and more dynamic than static logo_cloud",
    "footer_columns": "Multi-column footer: brand info, link groups, social icons",
}


# ═══════════════════════════════════════════════════════════════════════
# STAGE 0: Prompt Enhancement (GPT-4.1-mini → enriched brief)
# ═══════════════════════════════════════════════════════════════════════

PROMPT_ENHANCE_SYSTEM = """You are a senior creative director at a top-tier web design agency.

Your job: take the user's raw website request and produce a DESIGN BRIEF with a bold, committed aesthetic vision.

CRITICAL: Before anything else, decide on a SPECIFIC aesthetic direction. Not "professional" — that means nothing. Choose a real design identity:
- Raw Industrial Brutalism (dark, heavy type, sharp angles, noise textures)
- Clean Swiss Minimalism (lots of whitespace, grid-based, monospace accents)
- Luxury Editorial (serif headlines, muted tones, generous spacing, gold accents)
- Bold Geometric (bright accent colors, clip-paths, angular shapes, large type)
- Dark Tech (near-black bg, neon accent, glassmorphism, code-inspired)
- Warm Organic (earth tones, rounded shapes, hand-drawn feel, soft shadows)
- High Contrast Modern (black + one vivid color, oversized headlines, dramatic)
Pick the one that BEST fits the industry. Commit fully. Never mix styles.

RULES:
- Keep the user's original intent and any specifics they mentioned
- Fill gaps with smart, industry-appropriate defaults
- Keep the brief under 300 words — concise but rich
- Write in directive style ("The website should...", "Include a section for...")
- Do NOT generate HTML, CSS, or JSON — just the text brief
- Do NOT use generic phrases: "cutting-edge", "world-class", "innovative", "seamless"
- If multipage, suggest 4-6 pages MAX

YOUR BRIEF MUST INCLUDE:
1. **Aesthetic direction**: Name the specific design style (from list above or your own bold choice)
2. **Color system**: One dominant dark/light base + one sharp accent color. Name exact mood.
3. **Typography direction**: Describe the type personality (e.g. "military uppercase condensed" or "elegant serif with thin sans body"). NEVER suggest Inter, Roboto, Arial, or system-ui.
4. **One unforgettable design element**: What makes this site visually memorable? (e.g. diagonal clip-path buttons, noise texture overlay, giant faded background numbers, animated gradient hero)
5. **Content sections**: What sections make sense for this business (7-9 max)
6. **Content direction**: What should headlines emphasize? Specific industry language.
7. **Social proof**: Concrete stats and testimonials (realistic for the industry)
8. **CTA strategy**: Primary conversion goal

EXAMPLES:

User: "make a website for a gym"
Enhanced: "AESTHETIC: Raw Industrial Brutalism. Dark iron-black background (#0a0a0a) with blood-red accent (#c0392b). Typography: heavy condensed uppercase for headlines (like Oswald or Barlow Condensed), clean sans-serif body. UNFORGETTABLE ELEMENT: Large faded numbers as background texture (opacity 0.04) behind each section + diagonal clip-path on CTA buttons. Create a website for 'IRONBLOOD MMA' — an elite combat training facility in Dubai. Include: full-viewport hero with animated counter stats (12+ years, 340+ fighters, 47+ champions), 6 discipline cards (Muay Thai, Wrestling, BJJ, Boxing, S&C, MMA), 3 elite coach profiles with fight records and specialties, interactive program selector (Beginner/Competitor/Fight Fitness/Youth/Private), weekly schedule grid color-coded by difficulty, 3-tier pricing (AED 999/1,999/3,499), and auto-scrolling testimonial marquee. Copy should be direct and tough — no corporate fluff. Stats should show real fighting credentials."

User: "law firm website"
Enhanced: "AESTHETIC: Luxury Editorial. Deep navy (#0d1b3e) with warm gold accent (#c9a84c) on ivory (#faf9f6). Typography: classic serif for headlines (like Playfair Display), thin sans-serif body (like Outfit or DM Sans). UNFORGETTABLE ELEMENT: Subtle parallax scroll on hero image + gold underline animations on section headings. Create a website for 'Al Rashid & Partners' — a corporate law firm in Dubai DIFC. Include: hero with Dubai skyline silhouette overlay, 5 practice area cards (Corporate, Real Estate, IP, Dispute Resolution, Compliance), 4 senior partner profiles with credentials and bar admissions, notable case results with anonymized outcomes (AED 50M+ recovered, 200+ cases), client testimonials from business leaders, FAQ for free zone legal questions, and consultation booking CTA. Copy should be authoritative and specific — cite real legal frameworks (UAE Commercial Companies Law, DIFC Courts). No generic 'trusted legal partner' language."

Return ONLY the enhanced brief text. No preamble, no explanations."""


# ═══════════════════════════════════════════════════════════════════════
# STAGE 1: Website Plan (GPT-4.1 → JSON)
# ═══════════════════════════════════════════════════════════════════════

PLAN_SYSTEM_PROMPT = """You are an expert UI/UX architect and creative director.

Analyze the user's website request and create a comprehensive website plan.
The brief may specify an AESTHETIC DIRECTION (e.g. "Raw Industrial Brutalism", "Luxury Editorial"). If so, your color, font, and layout choices MUST match that aesthetic. Execute it with full commitment — no diluting the vision with safe defaults.

INSTRUCTIONS:
- Determine the best page structure for this business/purpose
- Choose appropriate sections in the right order (user journey matters)
- Decide the visual direction: colors, fonts, mood
- Write the actual marketing content for each section
- For each section, choose a LAYOUT PATTERN from the approved list
- Be specific — no placeholders, no lorem ipsum

APPROVED LAYOUT PATTERNS (you MUST use one per section):

HERO (pick ONE — vary across generations):
CRITICAL: Hero MUST always include an image (background image, side image, or mockup). Never use a hero without a visual.
- hero_split: Two-column hero — text left, image right (RECOMMENDED — always looks great)
- hero_center: Centered hero text WITH background image (always use the background image variant)
- hero_full_image: Full-width background image with overlay text (RECOMMENDED — high impact)
- hero_product_mockup: Centered text above a large device mockup image — ONLY for SaaS/tech/software products. NEVER use for service businesses.
- hero_mockup_center: Centered headline with browser-frame mockup below — ONLY for SaaS/tech products. NEVER use for service businesses.
- hero_asymmetric: Offset text with overlapping image/card elements — modern editorial feel
- hero_minimal: Use ONLY if the next section immediately shows visuals. Still include image_query in plan.
- hero_video_bg: Animated gradient background with centered text — use sparingly

FEATURES / SERVICES (pick 1-2 — mix for variety):
- card_grid: Icon + title + description cards in 3-column grid (NO images — icons only)
- icon_grid: Compact icon grid (4 columns, short text) (NO images — icons only)
- feature_split: Alternating image + text rows (wide layout) (HAS images)
- feature_cards: Large image-top cards with title + description (3 columns) (HAS images — each card gets a photo)
- feature_stacked: Full-width vertical stack — each feature is its own row with icon + title + long text (NO images)
- feature_steps: Numbered vertical steps with connecting line — ONLY for how-it-works sections when a literal step-by-step process is essential. AVOID for general features/services — use card_grid, icon_grid, or feature_cards instead (NO images)

CRITICAL PATTERN SELECTION — card_grid vs feature_cards:
- card_grid = ICON-BASED (no images) — use for abstract services, digital features, capabilities
- feature_cards = IMAGE-BASED (each card has a photo) — use when visual content matters
- MUST use feature_cards for: restaurant menus, food items, fitness programs, real estate listings, portfolio/work samples, product showcases, travel destinations, hotel rooms, course catalogs
- MUST use card_grid or icon_grid for: abstract SaaS features, pricing benefits, digital capabilities, technology specs
- If the user mentions food, dishes, programs, projects, properties, courses, or physical items → ALWAYS choose feature_cards (NOT card_grid)
- If the user mentions features, capabilities, services (abstract) → use card_grid or icon_grid

TESTIMONIALS (pick ONE):
- testimonial_cards: Grid of quote cards with author info
- testimonial_slider: Single large featured testimonial with navigation dots
- testimonial_split: Two-column — large quote left, author photo right

TEAM (pick ONE — ALL team patterns use real portrait photos, NOT icons):
- team_grid: Standard photo + name + role cards (each member gets a portrait photo)
- team_cards: Larger cards with photo + name + role + short bio (each member gets a portrait photo)
- team_masonry: Staggered masonry photos with hover overlay for name/role (each member gets a portrait photo)
NOTE: Team members MUST have image_query for their portrait (e.g. "professional woman architect portrait studio"). NEVER use icons for team sections.

CTA (pick ONE):
- cta_banner: Full-width colored banner with headline + buttons
- cta_split: Two-column — text + buttons left, image right
- cta_gradient: Gradient background with glowing button effect
- cta_centered: Clean centered CTA — headline, subtitle, single button on subtle background

OTHER:
- pricing_table: Side-by-side pricing plans
- faq_accordion: Expandable Q&A accordion
- stats_row: Large numbers with labels
- gallery_grid: Image gallery grid with lightbox modal (click to enlarge)
- image_carousel: Full-width image/content carousel with arrows and dots — great for portfolios, project showcases, before/after, property tours
- service_modal: Grid of cards that open a detail modal on click — great for services, menu items, course details, product specs
- timeline: Vertical timeline with milestones — ONLY for company history or roadmap when dates/years are essential. AVOID for general processes — use feature_split or card_grid instead
- newsletter_cta: Email signup with input + button + pitch text — great for lead generation
- comparison_table: Side-by-side feature comparison with check/cross icons — great for SaaS, product differentiators
- trust_badges: Row of certification/security badges with icons — great after hero or before footer for trust building
- contact_split: Contact info + form side by side
- logo_cloud: Partner/client logo row (static)
- logo_carousel: Auto-scrolling logo strip — more dynamic than logo_cloud
- footer_columns: Multi-column footer

VARIETY RULE: Do NOT always default to hero_split + card_grid + testimonial_cards. Actively choose DIFFERENT variants for each generation to make every website feel unique.
AVOID feature_steps and timeline — these numbered step layouts are overused and look generic. Prefer card_grid, icon_grid, feature_split, or feature_cards instead. Only use feature_steps if the user EXPLICITLY asks for a step-by-step process section.

PATTERN SELECTION GUIDANCE (choose based on website type):
- SaaS / Software products → prefer hero_product_mockup or hero_mockup_center for hero
- Consultancy / services / agencies / restaurants / healthcare / legal / finance → MUST use hero_split or hero_full_image (these need real photographs, NOT mockups)
- Automation / onboarding / how-it-works → prefer feature_split or card_grid with clear descriptions
- Agencies / creative studios → prefer hero_asymmetric for editorial feel
- Simple landing pages → prefer cta_centered for clean conversion-focused CTA
- Product demos → prefer hero_mockup_center to showcase the interface
- Portfolio / photography / real estate / travel → prefer image_carousel for visual showcase
- Services with details / restaurants with menu items / courses → prefer service_modal for expandable detail cards
- Gallery / portfolio / work samples → prefer gallery_grid (has lightbox modal built-in)
- Company with history / milestones / roadmap → prefer stats_row or feature_split (avoid timeline unless there are actual dates)
- Blog / newsletter / lead generation → prefer newsletter_cta before footer
- SaaS with competitors / products with differentiators → prefer comparison_table
- Trust building / many partners → prefer logo_carousel over logo_cloud for dynamic feel

You MUST return ONLY valid JSON:
{{
  "brand": {{
    "name": "Company/brand name",
    "tagline": "A compelling tagline",
    "industry": "specific industry"
  }},
  "image_style": "cohesive visual theme for all images on this site — e.g. clean modern architecture photography natural light sustainable materials glass buildings greenery",
  "design": {{
    "theme": "dark or light",
    "primary_color": "#hex — the main brand color",
    "secondary_color": "#hex — supporting color",
    "accent_color": "#hex — for CTAs and highlights",
    "background_color": "#hex — page background",
    "surface_color": "#hex — card/section background (slightly different from bg)",
    "text_color": "#hex — primary text",
    "text_muted": "#hex — secondary/muted text",
    "heading_font": "Google Font name for headings (NEVER Inter, Roboto, Arial, Open Sans — these are banned. Use distinctive fonts like Playfair Display, Oswald, Barlow Condensed, Space Grotesk, Syne, DM Serif Display, Outfit, etc.)",
    "body_font": "Google Font name for body text",
    "style": "e.g. minimal, bold, elegant, playful, corporate",
    "card_radius": "8px or 12px or 16px",
    "button_radius": "8px or 50px (pill)",
    "shadow_style": "soft or sharp or none",
    "spacing": "compact or normal or spacious"
  }},
  "sections": [
    {{
      "type": "navbar",
      "pattern": "navbar",
      "content": {{
        "logo_text": "Brand Name",
        "logo_icon": "fa-solid fa-icon-name (pick an icon matching the industry — e.g. fa-scale-balanced for law, fa-code for tech, fa-utensils for food, fa-building for real estate, fa-stethoscope for health, fa-plane for travel)",
        "links": ["Services", "About", "Pricing", "Contact"],
        "cta_button": "Get Started (short text — max 3 words)"
      }}
    }},
    {{
      "type": "hero",
      "pattern": "hero_split or hero_center",
      "content": {{
        "headline": "Compelling main headline",
        "subheadline": "Supporting text that explains the value",
        "cta_primary": "Primary Button Text",
        "cta_secondary": "Secondary Button Text",
        "trust_line": "Trusted by 500+ companies worldwide",
        "image_query": "highly specific descriptive keywords for hero image"
      }}
    }},
    {{
      "type": "features|services|stats|testimonials|pricing|faq|cta|team|gallery|about|contact|footer",
      "pattern": "card_grid|icon_grid|feature_split|testimonial_cards|pricing_table|faq_accordion|stats_row|cta_banner|team_grid|gallery_grid|image_carousel|service_modal|timeline|newsletter_cta|comparison_table|contact_split|logo_carousel|footer_columns",
      "content": {{
        "headline": "Section headline",
        "subheadline": "Section description",
        "image_query": "highly specific descriptive keywords for section image (if section uses images)",
        "items": [
          {{
            "title": "Item title",
            "description": "Item description",
            "icon": "fa-solid fa-icon-name",
            "image_query": "highly specific descriptive keywords (for team/gallery/feature items with images)"
          }}
        ]
      }}
    }}
  ]
}}

VISUAL RHYTHM RULES (VERY IMPORTANT — follow these for professional layout flow):

Layout patterns fall into three density categories:

WIDE sections: hero_split, hero_center, hero_full_image, hero_minimal, hero_video_bg, hero_product_mockup, hero_mockup_center, hero_asymmetric, feature_split, feature_stacked, feature_steps, cta_banner, cta_split, cta_gradient, cta_centered, contact_split, testimonial_split
GRID sections: card_grid, icon_grid, testimonial_cards, testimonial_slider, team_grid, team_cards, team_masonry, gallery_grid, feature_cards, service_modal
SPECIAL sections: stats_row, pricing_table, faq_accordion, logo_cloud, logo_carousel, image_carousel, timeline, newsletter_cta, comparison_table, trust_badges

Rules:
- Do NOT place more than 2 GRID sections consecutively. Alternate between wide and grid layouts.
- Insert a stats_row or feature_split AFTER the hero when possible — this creates a strong visual break.
- Place testimonials AFTER services or features — not directly after hero.
- Place CTA near the end of the page, before contact or FAQ.
- End the page with contact or CTA before the footer.
- Every website MUST include at least one of: stats_row, feature_split, or logo_cloud.
- The layout should feel like a professionally designed landing page with visual variety.

SECTION COUNT LIMIT: Use 7-9 content sections (excluding navbar and footer). NEVER exceed 10 content sections — more sections make the page too long and dilute impact. Quality over quantity.

Examples of GOOD section orders (use DIFFERENT patterns each time — do NOT always copy one example):

FLOW A: navbar → hero_split → stats_row → card_grid → feature_split → testimonial_cards → cta_banner → faq_accordion → contact_split → footer_columns
FLOW B: navbar → hero_full_image → logo_cloud → icon_grid → feature_split → testimonial_slider → cta_gradient → contact_split → footer_columns
FLOW C: navbar → hero_center → stats_row → feature_cards → testimonial_split → team_masonry → cta_centered → faq_accordion → footer_columns
FLOW D: navbar → hero_minimal → service_modal → stats_row → testimonial_cards → pricing_table → cta_split → contact_split → footer_columns
FLOW E: navbar → hero_video_bg → icon_grid → feature_split → team_cards → cta_gradient → faq_accordion → contact_split → footer_columns
FLOW F: navbar → hero_product_mockup → stats_row → feature_cards → testimonial_slider → pricing_table → cta_banner → faq_accordion → footer_columns
FLOW G: navbar → hero_asymmetric → logo_cloud → feature_cards → feature_split → testimonial_split → cta_centered → contact_split → footer_columns
FLOW H: navbar → hero_full_image → stats_row → image_carousel → service_modal → testimonial_slider → cta_gradient → faq_accordion → footer_columns
FLOW I: navbar → hero_split → logo_carousel → gallery_grid → feature_split → testimonial_cards → cta_banner → contact_split → footer_columns
FLOW J: navbar → hero_center (typed.js) → logo_carousel → card_grid → comparison_table → testimonial_slider → pricing_table → newsletter_cta → faq_accordion → footer_columns
FLOW K: navbar → hero_asymmetric → logo_carousel → feature_cards → stats_row → testimonial_split → cta_gradient → newsletter_cta → footer_columns

CRITICAL VARIETY RULE: You MUST rotate through these patterns. Do NOT always use card_grid for services — also use icon_grid, feature_cards, feature_stacked, feature_steps. Do NOT always use testimonial_cards — also use testimonial_slider, testimonial_split. Do NOT always use cta_banner — also use cta_gradient, cta_split, cta_centered. Do NOT always use team_grid — also use team_cards, team_masonry.

Example of BAD section order (too many grids in a row):
  navbar → hero_split → card_grid → icon_grid → testimonial_cards → card_grid → footer_columns

Example of BAD variety (same patterns every time — AVOID):
  Always using: card_grid + feature_split + testimonial_cards + cta_banner. This makes every website look the same.

RULES:
- Include 7-10 sections (navbar + content sections + footer)
- Navbar links: MAX 5 links (pick the most important sections). Too many links overflow on desktop. If you have 8+ sections, only link the top 5 in the navbar — the rest are still on the page, just not in nav.
- EVERY section MUST have a "pattern" field from the approved list
- Write REAL content — specific to the business, persuasive, professional
- Choose Font Awesome icons (fa-solid fa-xxx) for features/services
- Testimonials need real-sounding names, roles, companies, and quotes
- Pricing needs realistic plan names, prices, and feature lists
- FAQ needs real questions and helpful answers
- Footer needs company info, link groups, social links

GRID ITEM COUNT RULES (CRITICAL — prevents broken layouts):
- card_grid: EXACTLY 6 items (fills 3-column grid evenly). Never 4 or 5.
- icon_grid: EXACTLY 6 items (fills 3-column grid evenly). Never 4 or 5.
- feature_cards: EXACTLY 6 items (fills 3-column grid evenly). Never 4 or 5.
- team_grid / team_cards: EXACTLY 3 or 6 items. Never 4 or 5.
- team_masonry: EXACTLY 6 items.
- gallery_grid: EXACTLY 6 or 9 items.
- image_carousel: 3-5 slides (each slide has image_query, title, description).
- service_modal: EXACTLY 3 or 6 items (each item has icon, title, short description, AND modal_detail with longer expanded description).
- timeline: 4-6 milestones (each has year/date, title, description).
- comparison_table: EXACTLY 2 columns (us vs competitor, or two products) with 5-8 feature rows.
- newsletter_cta: No items needed — just headline, subheadline, placeholder text, button text.
- logo_carousel: 6-10 company names (text only, no images).
- testimonial_cards: EXACTLY 3 items.
- pricing_table: EXACTLY 3 plans.
- stats_row: EXACTLY 4 stats (fills 4-column grid evenly). Never 3.
- feature_split: 2 or 3 alternating rows.
- feature_stacked: 4 or 5 items.
- feature_steps: 3 or 4 steps (numbered).
- NEVER generate 4 items for any 3-column grid layout. Use 3, 6, or 9.

STATS FORMATTING RULES:
- Every stat MUST have a clear, specific label that explains the number
- Format: number + suffix + descriptive label
- BAD examples: "120+", "45%", "18", "26M" (no context)
- GOOD examples:
  - "120+" with label "Projects Completed"
  - "45%" with label "Average Energy Reduction"
  - "18" with label "Sustainability Awards Won"
  - "26M" with label "Square Feet Optimized"
- Labels should use concrete industry-relevant terminology, not generic words

COPY STYLE RULES (CRITICAL — content must sound professional, not AI-generated):
- Write like a real professional company website in the given industry
- Use concrete domain-specific terminology, not generic marketing fluff
- BANNED phrases (NEVER use these — they sound like AI-generated fluff):
  "cutting-edge solutions", "innovative technology", "future-ready systems",
  "leverage synergies", "paradigm shift", "next-generation platform",
  "revolutionize", "disrupt", "world-class", "best-in-class",
  "seamless integration", "holistic approach", "empower your business",
  "unlock potential", "transform your journey", "elevate your experience",
  "supercharge", "turbocharge", "game-changing", "unleash", "harness the power",
  "reimagine", "take it to the next level", "at the forefront", "drive results"
- INSTEAD use concrete language specific to the industry:
  Architecture: "carbon-neutral design", "passive energy optimization", "biophilic architecture", "climate-responsive materials"
  Technology: "99.97% uptime SLA", "sub-200ms API response", "SOC 2 Type II certified", "end-to-end encryption"
  Healthcare: "evidence-based treatment protocols", "HIPAA-compliant telehealth", "board-certified specialists"
  Finance: "fiduciary-grade portfolio management", "tax-loss harvesting", "SEC-registered advisory"
  Real Estate: "net-zero energy certification", "walkability score 92", "smart home pre-wired"
- Headlines should be specific and benefit-driven, not vague
- Subheadlines should contain concrete details (numbers, specifics, outcomes)
- Every piece of text should sound like it was written by someone who actually works in the industry

IMAGE STYLE CONSISTENCY:
- The top-level "image_style" field defines the visual theme for ALL images on the site
- It should be a short phrase describing the photography style, mood, and visual elements
- Examples by industry:
  Architecture: "clean modern architecture photography, natural light, sustainable materials, glass buildings, greenery"
  Restaurant: "warm moody food photography, rustic wood tables, ambient candlelight, artisan plating"
  Tech startup: "bright modern workspace photography, diverse team collaboration, clean minimal desks, natural daylight"
  Fitness: "dynamic action sports photography, high contrast, powerful movement, gym equipment, motivated athletes"
- ALL image_query values throughout the plan should align with this image_style theme

IMAGE QUERY RULES (CRITICAL — determines image relevance):

Every image_query must describe a real photograph that matches the business industry.

QUERY FORMAT: subject + context (2-4 words ONLY)

STRICT LENGTH RULE: Unsplash and Pexels return MUCH better results with short, concrete queries.
- 2-3 words: BEST — "chef plating dish", "law office books", "woman portrait studio"
- 4 words: OK — "modern glass office building"
- 5+ words: TOO LONG — returns irrelevant images. NEVER exceed 4 words.

DO NOT include filler words: "professional", "beautiful", "high quality", "specific", "descriptive", "keywords", "showing", "featuring".
DO NOT include generic words alone: "modern", "business", "technology", "professional".
EVERY word must be a concrete, searchable noun or adjective.

RULE 1: Every query MUST include at least one industry-specific keyword:
  Architecture → building, facade, skyline, blueprint, structural, rooftop, construction site
  Restaurant → dish, chef, dining table, plated meal, kitchen, ingredients
  Fitness → athlete, workout, gym equipment, training, weights, stretching
  Technology → developer, laptop, coding, server rack, circuit board, programming
  Healthcare → doctor, clinic, medical equipment, patient, stethoscope, hospital
  Real Estate → house exterior, apartment interior, property, living room, kitchen
  Legal → courthouse, law books, gavel, legal office, contract signing
  Finance → trading floor, financial charts, vault, stock exchange, accounting
  Education → classroom, students studying, university campus, library, lecture hall
  Beauty/Spa → spa treatment room, facial massage, skincare products, salon chair

RULE 2: Match query to section type and choose the correct image role:
  Hero (industry scene) → role "hero" — large establishing shot (wide angle, dramatic)
  Hero (product/SaaS) → role "product" — dashboard UI, app screenshot, product interface
  Feature cards (UI) → role "product" — specific UI/dashboard showing the feature
  Feature cards (real-world) → role "feature" — visual of the service being performed
  Feature split → role "feature" — visual representation of each feature
  Team → role "team" — professional portrait with profession context clues
  Gallery → role "gallery" — real examples of work products, spaces, or projects
  Testimonials → role "testimonial" — professional headshot in neutral/studio setting
  CTA → role "cta" — aspirational scene showing positive outcome
  Device mockup → role "mockup" — MUST include device word (laptop, macbook, phone, tablet). NOTE: Stock photos don't have real SaaS dashboards — use realistic queries like "laptop workspace modern desk clean" or "macbook on desk minimalist office" instead of "dashboard interface UI"
  Background/ambient → role "background" — abstract, decorative, atmospheric

RULE 3: NEVER use generic words alone:
  BANNED as standalone: "modern", "technology", "business", "team", "office", "professional", "innovation"
  These MUST be combined with industry-specific subjects

BAD queries (generic, too long, or filler-heavy):
  "modern office" → too generic, could return ANY office
  "technology" → single generic word, useless
  "professional woman consultant portrait studio lighting" → 6 words, too long
  "team meeting business professionals discussing strategy" → 6 words, filler-heavy
  "high quality professional portrait" → filler words, no subject

GOOD queries (2-4 concrete words — returns relevant photos):
  Architecture: "architect reviewing blueprint"
  Architecture: "glass facade skyline"
  Restaurant: "chef plating dish"
  Restaurant: "rustic dining candlelight"
  Fitness: "athlete deadlift gym"
  Technology: "developer coding monitors"
  Healthcare: "dentist patient clinic"
  Real Estate: "penthouse living room"
  Legal: "law office books"
  Team portraits: "woman lawyer portrait"
  Team portraits: "man suit headshot"

RULE 4: Each query on the page MUST be unique — no duplicates
RULE 5: All queries must follow the top-level "image_style" visual theme
RULE 6: NEVER generate queries that could return a different industry
  Example: An architecture website must NEVER have queries about servers, code, or medical equipment

RULE 7: TESTIMONIAL PHOTOS — use professional headshot queries, NOT industry close-ups:
  GOOD: "woman business portrait", "man suit headshot", "young professional smiling"
  BAD: "teeth close-up dental", "patient dental chair", "elderly woman face"
  Testimonial photos show the PERSON giving the review, not the service they received.
  Use neutral/studio-style portraits of diverse, professional-looking people.
  NEVER use extreme close-ups of body parts (teeth, skin, eyes, hands).

RULE 8: AVOID INAPPROPRIATE OR AWKWARD IMAGES (CRITICAL):
  - NO extreme close-ups of body parts (mouths, teeth, skin texture, eyes, hands)
  - NO medical/clinical procedure photos (surgery, injections, dental tools in mouth)
  - NO elderly/vulnerable people unless the business specifically serves seniors
  - Hero images should be wide, professional, aspirational scenes — NOT close-ups
  - Feature images should show the service environment, NOT patient/client faces
  - For healthcare/dental/medical:
    GOOD: "dental clinic interior modern", "dentist patient smiling chair", "family dental office reception", "dentist consultation friendly"
    BAD: "teeth closeup", "straight teeth", "open mouth dental", "chipped tooth", "teeth whitening", "dental bridge", "teeth bonding"
    The query must show PEOPLE or ENVIRONMENTS, never isolated teeth/body parts
  - For fitness/wellness:
    GOOD: "gym modern equipment interior", "yoga class group session", "personal trainer client workout"
    BAD: "muscle closeup", "abs body", "sweat skin"
  - ALL gallery_grid image_query values must show ENVIRONMENTS, PEOPLE, or RESULTS (happy person) — never clinical close-ups
  - ALL feature_cards image_query values must show the SERVICE EXPERIENCE, not isolated body parts

IMAGE_QUERY MANDATORY SECTIONS (MUST include image_query):
- hero: section-level image_query (for hero background or hero-split image)
- feature_cards: MUST include image_query on EACH ITEM (each card gets its own photo — food, programs, projects, etc.)
- feature_split: MUST include image_query on EACH ITEM (each row gets an image)
- team_grid / team_cards / team_masonry: MUST include image_query on EACH ITEM (each person gets a portrait photo)
- gallery_grid: MUST include image_query on EACH ITEM (each gallery item is a photo)
- image_carousel: MUST include image_query on EACH ITEM (each carousel slide gets a photo)
- cta_split / testimonial_split: section-level image_query
- about: section-level image_query

Sections WITHOUT images (NO image_query needed):
- stats_row, faq_accordion, pricing_table, card_grid, icon_grid, cta_banner, cta_gradient, cta_centered, logo_cloud, logo_carousel, footer, feature_stacked, feature_steps, service_modal, timeline, newsletter_cta, comparison_table, trust_badges
IMPORTANT: logo_cloud uses TEXT-ONLY logos (<span> tags), NOT <img> tags. Do NOT add image_query to logo_cloud items.
IMPORTANT: card_grid and icon_grid use ICONS only — do NOT add image_query to their items.

SECTION INTELLIGENCE RULES:
- Plan sections like a professional conversion-optimized landing page
- Recommended flow: Hero → Social proof (stats/logos) → Services/Features → Deeper value (feature_split) → Testimonials → Team (optional) → CTA → FAQ/Contact → Footer
- NEVER place two GRID-density sections back to back without a WIDE or SPECIAL section between them
- stats_row works best right after hero as a trust-building element
- feature_split works best after a card_grid to break up the visual density
- CTA should appear in the bottom third of the page, before contact or FAQ
- testimonials should appear AFTER you've shown what the company does (after services/features)
- Every website MUST include at least one WIDE section between grid sections"""

PLAN_MULTIPAGE_ADDENDUM = """
MULTI-PAGE MODE:
The user has requested a multi-page website. Instead of a flat "sections" array, output a "pages" array.

RULES FOR MULTI-PAGE:
- Maximum 8 pages (Home + up to 7 subpages)
- Each page has: slug, title, sections[]
- Navbar and footer are SHARED across all pages — define them ONCE in "shared_sections"
- Navbar links should use real page hrefs: "/" for home, "/about.html" for about, "/services.html" for services, etc. Always use .html extension.
- Home page should have 5-7 content sections (hero, features/services, stats, testimonials, CTA)
- Subpages should have 3-5 content sections each
- Every page MUST have unique content — don't repeat sections across pages

JSON STRUCTURE for multi-page:
{{
  "brand": {{ ... same as single-page ... }},
  "image_style": "...",
  "design": {{ ... same as single-page ... }},
  "multipage": true,
  "shared_sections": [
    {{ "type": "navbar", "pattern": "navbar", "content": {{ "logo_text": "...", "links": [{{"label": "Home", "href": "/"}}, {{"label": "About", "href": "/about.html"}}, {{"label": "Services", "href": "/services.html"}}, {{"label": "Contact", "href": "/contact.html"}}], "cta_button": "Get Started" }} }},
    {{ "type": "footer", "pattern": "footer_columns", "content": {{ ... }} }}
  ],
  "pages": [
    {{
      "slug": "index",
      "title": "Home",
      "meta_description": "...",
      "sections": [
        {{ "type": "hero", "pattern": "hero_split", "content": {{ ... }} }},
        ... more sections ...
      ]
    }},
    {{
      "slug": "about",
      "title": "About Us",
      "meta_description": "...",
      "sections": [
        {{ "type": "hero", "pattern": "hero_center", "content": {{ "headline": "...", "subheadline": "...", "image_query": "..." }} }},
        ... more sections ...
      ]
    }}
  ]
}}

COMMON PAGE COMBINATIONS (pick what fits the business — use as many pages as the user's request needs):
- Business/Agency: Home, About, Services, Team, Contact
- SaaS/Product: Home, Features, Pricing, Docs, Contact
- Restaurant: Home, Menu, Gallery, About, Contact
- Portfolio: Home, Work, About, Testimonials, Contact
- E-commerce: Home, Products, About, FAQ, Contact
- Sports Club: Home, Team, Fixtures, News, Membership, Contact
- School/Academy: Home, Programs, Faculty, Admissions, Events, Contact

Use 4-8 pages depending on the scope of the user's request. More complex businesses need more pages.

Each subpage MUST start with a hero variant (hero_center or hero_full_image work best for subpages) followed by relevant content sections.

CRITICAL — IMAGES ON EVERY PAGE:
- EVERY page's hero section MUST include "image_query" with specific, descriptive keywords relevant to that page's content
- Example: About page hero → "image_query": "professional team meeting in modern glass office collaboration workspace"
- Example: Services page hero → "image_query": "modern business consulting meeting professional workspace"
- Example: Contact page hero → "image_query": "friendly customer service representative modern office"
- NEVER leave image_query empty or omit it from any hero section — every page deserves a strong visual
- Feature/gallery/team sections on subpages MUST also include image_query on each item
"""

PLAN_SHORT_PROMPT_ADDENDUM = """
NOTE: The user's request is brief. Make smart professional decisions to fill in all details.
Choose an appropriate industry, suggest a brand name, and create comprehensive content."""


# ═══════════════════════════════════════════════════════════════════════
# DYNAMIC PROMPT BUILDERS
# ═══════════════════════════════════════════════════════════════════════


def build_plan_prompt(base_prompt: str = None, niche_key: str = None, multipage: bool = False) -> str:
    """Build the planner prompt with rotation hints, style preset, fonts, design tokens, and niche guidance."""
    prompt = base_prompt or PLAN_SYSTEM_PROMPT

    # Add pattern rotation hints
    rotation_hints = get_rotation_hints()
    if rotation_hints:
        prompt += "\n" + rotation_hints

    # Style preset: inject frequently (60% chance) for design variety
    if random.random() < 0.60:
        preset_name, preset = get_random_style_preset()
        prompt += "\n" + format_style_hint(preset_name, preset)

    # Inject curated font pairing
    try:
        from app.utils.font_pairings import get_pairing_for_style, get_random_pairing

        style_hint = niche_key or ""
        pairing = get_pairing_for_style(style_hint) if style_hint else get_random_pairing()
        prompt += f"""

FONT PAIRING (use these exact fonts):
- Heading font: {pairing["heading"]}
- Body font: {pairing["body"]}
- Style: {pairing["style"]}
- Google import: {pairing["google_import"]}
Include this @import in the <style> block. Use these fonts in the design_tokens."""
    except Exception:
        pass

    # Design tokens removed from plan prompt — the design seed is the single source of truth
    # for color/style direction. Tokens were causing conflicting signals with the seed.

    # Inject niche-specific image guidance
    if niche_key:
        niche_hint = _build_niche_image_hint(niche_key)
        if niche_hint:
            prompt += "\n" + niche_hint

    # Append multi-page addendum if requested
    if multipage:
        prompt += "\n" + PLAN_MULTIPAGE_ADDENDUM

    return prompt


def _build_niche_image_hint(niche_key: str) -> str:
    """Build niche-specific image query guidance for the planner."""
    from app.utils.image_packs import get_image_pack
    from app.utils.niches import NICHES

    niche = NICHES.get(niche_key)
    if not niche:
        return ""

    lines = [
        f"\nNICHE IMAGE GUIDANCE — This is a {niche['name']} website.",
        f"Industry image keywords: {', '.join(niche.get('image_keywords', []))}",
        "",
        "Use these PROVEN image queries for this industry (adapt to specific business):",
    ]

    # Get curated image pack for this niche
    pack = get_image_pack(niche_key)
    if pack:
        for role, queries in pack.items():
            examples = queries[:3]  # Show up to 3 examples per role
            lines.append(f"  {role}: {' | '.join(examples)}")

    lines.append("")
    lines.append("IMPORTANT: Adapt these queries to the SPECIFIC business described in the prompt.")
    lines.append("Use the curated queries as a starting point — make them more specific to the business context.")
    lines.append("Every image_query MUST relate to this specific industry. Do NOT use generic stock photo queries.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# TEMPLATE-FIRST CUSTOMIZATION (faster, higher quality)
# ═══════════════════════════════════════════════════════════════════════

TEMPLATE_CUSTOMIZE_PROMPT = """You are an expert frontend developer. Study the REFERENCE TEMPLATE below, then generate a NEW website using pure CSS classes that matches the template's visual quality.

REFERENCE TEMPLATE (study this for design quality, layout patterns, hover effects, visual texture):
{template_html}

BUSINESS PLAN (use this content):
{plan_json}

YOUR TASK:
Create a website that looks AS GOOD as the reference template, using pure CSS classes + CSS variables. NO Tailwind, NO utility frameworks. Study the template's:
- Hero layout and visual impact
- Card hover effects and animations
- Section spacing and visual rhythm
- Typography scale and weight usage
- Color usage and gradients
- Background textures and decorative elements
Then recreate that level of quality using semantic CSS classes.

OUTPUT FORMAT:
- Return ONLY HTML inside a single ```html code block
- Output a <style> block FIRST (CSS variables, fonts, layout, components) then HTML body content
- NO <html>, <head>, <body>, <link>, <meta> tags
- Do NOT add Font Awesome <script> or <link> tags — FA is pre-loaded
- Do NOT include any JavaScript

MANDATORY STRUCTURE:
1. <style> block with:
   - @import for Google Fonts (from plan's heading_font + body_font)
   - :root {{ --primary, --secondary, --accent, --bg, --bg-surface, --text, --text-muted, --font-heading, --font-body, --radius, --radius-btn }}
   - Base reset, typography, layout system (.container, .grid-2, .grid-3, .grid-4)
   - Component styles (.card, .btn-primary, .btn-secondary, .icon-box, .img-cover)
   - Navbar (.navbar, .nav-brand, .nav-links, .nav-toggle, .nav-scrolled)
   - Hero (.hero-section, .hero-heading, .hero-subtitle, .hero-split-grid)
   - Footer (.footer-grid, .footer-heading, .footer-links, .social-links)
   - Mobile responsive @media queries
   - CUSTOM EFFECTS from the reference template (clip-paths, hover pseudo-elements, noise textures, faded background numbers)

2. HTML body with semantic CSS classes:
   - EVERY <section> MUST have data-section-type="TYPE" (hero, features, services, testimonials, team, gallery, contact, cta, faq, stats, pricing, footer)
   - Use <nav> for navbar, <footer> for footer, <section> for content
   - Use semantic CSS classes defined in <style> block
   - ⚠️ Use {{{{IMG:role query}}}} placeholders for ALL images — NEVER write real pexels.com/unsplash.com URLs (they will 404)
   - Use Font Awesome icons: <i class="fa-solid fa-icon-name"></i>
   - Include ALL sections from the plan

PRESERVE FROM REFERENCE (recreate in <style> block):
- Card hover choreography: border-left reveal, ::before gradient sweep, title color change
- Hero depth: faded background elements, gradient overlays, staggered entrance animations
- Section texture: alternating backgrounds, decorative elements
- Transition timing: cubic-bezier easing, staggered delays

ADD THESE ELEMENTS:
- <!-- SEO_META --> after </style> with meta description, og:title, og:description <!-- END_SEO_META -->
- <!-- FAVICON --> with SVG favicon <!-- END_FAVICON -->
- WhatsApp float button (fixed bottom-right, green background #25D366)
- Back-to-top button (fixed, hidden by default, shows on scroll)

Return ONLY the HTML. No explanation."""


def build_template_customize_prompt(template_html: str, plan: dict) -> str:
    """Build a prompt for customizing an existing template with plan content.

    This is MUCH smaller than the from-scratch prompt (~35K vs ~72K) and produces
    more reliable results because Claude modifies working code instead of generating
    from scratch.
    """
    # Strip long image URLs to reduce token count — Claude will replace them anyway
    import re as _re
    compressed = _re.sub(
        r'src="https://[^"]{50,}"',
        'src="REPLACE_ME"',
        template_html,
    )

    # Build minimal plan JSON with just the content Claude needs
    plan_content = {
        "brand": plan.get("brand", {}),
        "design": plan.get("design", {}),
        "image_style": plan.get("image_style", ""),
        "sections": plan.get("sections", []),
    }

    return TEMPLATE_CUSTOMIZE_PROMPT.format(
        template_html=compressed,
        plan_json=json.dumps(plan_content, indent=2),
    )


def build_html_prompt(plan: dict, enhanced_brief: str = None) -> str:
    """Build the HTML generation prompt with ONLY the needed pattern templates.

    This is the key optimization: instead of injecting all 38 patterns (~1200 lines),
    we inject only the 7-10 patterns the planner selected (~200-300 lines).
    """
    # Get only the patterns needed for this plan
    pattern_templates = get_patterns_for_plan(plan)

    # Get conditional CSS additions
    style_additions = get_style_additions_for_plan(plan)

    # Assemble the base prompt
    prompt = HTML_CORE_PROMPT.format(
        plan_json=json.dumps(plan, indent=2),
        pattern_templates=pattern_templates,
        style_additions=style_additions,
    )

    # Pre-build the Google Fonts URL so Claude doesn't get it wrong
    design = plan.get("design", {})
    heading_font = design.get("heading_font", "Space Grotesk").replace(" ", "+")
    body_font = design.get("body_font", "Inter").replace(" ", "+")
    font_import = f"@import url('https://fonts.googleapis.com/css2?family={heading_font}:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family={body_font}:wght@400;500;600;700&display=swap');"
    prompt += f"""

PRE-BUILT FONT IMPORT (use this EXACTLY in the <style> block — do not modify or rebuild it):
{font_import}
"""

    # Inject enhanced brief so the aesthetic vision carries through to HTML stage
    if enhanced_brief:
        prompt += f"""

AESTHETIC MANDATE (from creative brief — execute with FULL commitment):
{enhanced_brief}

The aesthetic described above MUST be visible in every element. If the brief says dark industrial — use near-black backgrounds, sharp angles, noise textures. If it says luxury editorial — use generous spacing, serif display fonts at massive scale, gold accents. Never dilute the vision with safe defaults.

CUSTOM CSS EFFECTS — add these in the <style> block:
- Card hover choreography: .card-hover::before {{ content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(var(--primary-rgb, 59,130,246), 0.1), transparent 60%); opacity: 0; transition: opacity 0.4s; }} .card-hover:hover::before {{ opacity: 1; }}
- Card left border reveal: .card-hover {{ border-left: 3px solid transparent; transition: border-color 0.3s; }} .card-hover:hover {{ border-left-color: var(--accent); }}
- Hero staggered entrance: .hero-stagger {{ opacity: 0; transform: translateY(30px); animation: heroIn 0.8s ease forwards; }} @keyframes heroIn {{ to {{ opacity: 1; transform: translateY(0); }} }}
  Use animation-delay: 0.2s, 0.4s, 0.6s on child elements for stagger effect
- Stats suffix accent: .stat-suffix {{ color: var(--accent); }} (wrap +, %, M in this class)
"""

    # Inject animation guidance
    try:
        from app.utils.animations import get_animation_prompt, get_animations_for_section

        prompt += "\n\n" + get_animation_prompt()

        # Add per-section animation recommendations
        sections = plan.get("sections", [])
        if sections:
            recs = []
            for sec in sections:
                sec_type = sec.get("type", "")
                if sec_type:
                    rec = get_animations_for_section(sec_type)
                    if rec:
                        recs.append(f"  - {sec_type}: {rec}")
            if recs:
                prompt += "\n\nRECOMMENDED ANIMATIONS PER SECTION:\n" + "\n".join(recs)
    except Exception:
        pass

    # Inject section-level reference templates
    try:
        from app.utils.section_templates import get_references_for_plan

        refs = get_references_for_plan(plan)
        if refs:
            prompt += "\n\n" + refs
    except Exception:
        pass

    return prompt


def build_page_html_prompt(plan: dict, page: dict, shared_sections: list) -> str:
    """Build HTML prompt for a single page in a multi-page site.

    The page gets the shared navbar + footer injected around its own sections.
    """
    # Create a synthetic single-page plan for this page
    page_plan = {
        "brand": plan.get("brand", {}),
        "image_style": plan.get("image_style", ""),
        "design": plan.get("design", {}),
        # Combine shared navbar + page sections + shared footer
        "sections": (
            [s for s in shared_sections if s.get("type") == "navbar"]
            + page.get("sections", [])
            + [s for s in shared_sections if s.get("type") == "footer"]
        ),
    }

    # Use existing build_html_prompt
    base_prompt = build_html_prompt(page_plan)

    # Add multi-page navigation context
    all_pages = plan.get("pages", [])
    nav_context = "\n\nMULTI-PAGE NAVIGATION RULES:\n"
    nav_context += "This is a MULTI-PAGE website. Navbar links MUST use real page hrefs, NOT anchor links.\n"
    nav_context += "Page links:\n"
    for p in all_pages:
        slug = p.get("slug", "index")
        href = "/" if slug == "index" else f"/{slug}.html"
        nav_context += f'- "{p.get("title", slug)}" -> href="{href}"\n'
    nav_context += "- Navbar CTA button should link to the contact page or relevant conversion page.\n"
    nav_context += (
        "- Within a page, section anchor links (#services, #about) should still work for same-page navigation.\n"
    )
    nav_context += f"\nYou are generating the '{page.get('title', 'Page')}' page (slug: {page.get('slug', 'index')}).\n"

    return base_prompt + nav_context


def is_multipage_request(prompt: str) -> bool:
    """Detect if user wants a multi-page website."""
    prompt_lower = prompt.lower()
    multipage_signals = [
        "multi-page",
        "multipage",
        "multiple pages",
        "separate pages",
        "different pages",
        "subpages",
        "sub-pages",
        "about page",
        "contact page",
        "services page",
        "pricing page",
        "menu page",
        "portfolio page",
        "several pages",
        "individual pages",
        "home page and",
        "homepage and",
        "pages for",
    ]
    return any(signal in prompt_lower for signal in multipage_signals)


# ── Add-page detection (for iteration / chat edits) ─────────────────

# Page types we recognise
_PAGE_TYPES = {
    "services": "services",
    "service": "services",
    "about": "about",
    "about us": "about",
    "contact": "contact",
    "contact us": "contact",
    "pricing": "pricing",
    "plans": "pricing",
    "portfolio": "portfolio",
    "work": "portfolio",
    "projects": "portfolio",
    "team": "team",
    "our team": "team",
    "blog": "blog",
    "news": "blog",
    "articles": "blog",
    "faq": "faq",
    "faqs": "faq",
    "gallery": "gallery",
    "photos": "gallery",
    "careers": "careers",
    "jobs": "careers",
    "testimonials": "testimonials",
    "reviews": "testimonials",
}


def detect_add_page_request(prompt: str) -> dict | None:
    """Detect if the user wants to add a new page (not a section).

    Returns {"slug": "services", "title": "Services"} or None.
    Only matches explicit "add/create … page" patterns to avoid
    false positives with section edits.
    """
    p = prompt.lower().strip()

    # Patterns: "add a services page", "create about page", "add new pricing page"
    add_page_patterns = [
        r"\b(?:add|create|make|build|generate|include)\b.*?\b(\w[\w\s]*?)\s+page\b",
    ]

    for pattern in add_page_patterns:
        m = re.search(pattern, p)
        if m:
            raw = m.group(1).strip()
            # Strip filler words
            raw = re.sub(r"^(a|an|the|new|another)\s+", "", raw).strip()
            # Look up in known page types
            if raw in _PAGE_TYPES:
                slug = _PAGE_TYPES[raw]
                title = slug.replace("-", " ").title()
                return {"slug": slug, "title": title}
            # Accept unknown types too — slugify them
            if raw and len(raw) < 30:
                slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
                if slug:
                    title = raw.title()
                    return {"slug": slug, "title": title}
    return None


# ── Prompt for generating a new page from reference ──────────────────

ADD_PAGE_HTML_PROMPT = """You are an expert frontend developer. Generate a NEW page for an existing website.

REFERENCE PAGE (the existing homepage — match its design EXACTLY):
```html
{reference_html}
```

EXISTING CSS (use the same variables and styles):
```css
{reference_css}
```

PAGE TO CREATE: {page_title} ({page_slug})
USER REQUEST: {prompt}

EXISTING IMAGE URLS (reuse these where appropriate — do NOT use random stock images):
{image_urls}

RULES:
- Return ONLY HTML inside a single ```html code block
- Output a <style> block FIRST (only for NEW styles this page needs — do NOT duplicate the reference CSS) then the HTML body content
- NO <html>, <head>, <body>, <link> tags — just <style> block + body content
- Match the EXACT same design language as the reference page:
  * Same CSS class patterns and naming
  * Same CSS variables: var(--primary), var(--bg), var(--accent), etc.
  * Same typography scale, font families, spacing rhythm
  * Same button styles, card styles, border-radius patterns
  * Same color palette — do NOT introduce new colors
- Copy the EXACT navbar and footer HTML from the reference page (including all classes and structure)
  * Update the nav links to include: Home (href="/"), {page_title} (href="/{page_slug}.html")
  * Add class "active" or similar visual indicator to the current page link
- Generate 3-5 content sections appropriate for a {page_title} page
- EVERY section MUST use: <section data-section-type="{{type}}">
- Reuse images from the EXISTING IMAGE URLS list above when they fit contextually
- Only use new Unsplash/Pexels URLs if no existing image is suitable
- All images must have: loading="lazy", alt text, width/height attributes
- Responsive: mobile-first with @media breakpoints
- Do NOT include any explanation — just the html code block"""


# ═══════════════════════════════════════════════════════════════════════
# STAGE 2: HTML Generation — use build_html_prompt() from patterns/
# STAGE 3: CSS — now inline in HTML stage
# (Legacy HTML_GEN_SYSTEM_PROMPT and CSS_GEN_SYSTEM_PROMPT deleted)
# ═══════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════
# STAGE 4: JavaScript Generation (Claude → JS only)
# ═══════════════════════════════════════════════════════════════════════

JS_GEN_SYSTEM_PROMPT = """You are a frontend JavaScript developer. Generate ONLY vanilla JavaScript for a website.

HTML STRUCTURE (for reference):
{html_summary}

SECTIONS IN PAGE: {section_types}

RULES:
- Return ONLY JavaScript inside a single ```js code block
- Vanilla JS only — no frameworks, no libraries (AOS is loaded separately)
- Include these behaviors:
  * Mobile hamburger menu: querySelector('.nav-toggle') toggles class 'active' on querySelector('.nav-links'). Do NOT create the button dynamically — it already exists in the HTML as <button class="nav-toggle">
  * Close mobile menu when any nav link is clicked (remove 'active' from .nav-links)
  * Smooth scroll for anchor links — IMPORTANT: skip links where href is exactly "#" (bare hash). Only scroll to links like href="#about", href="#contact". Guard: if (href && href !== '#' && href.length > 1) before calling querySelector(href).
  * Sticky/transparent navbar on scroll (add class 'nav-scrolled')
  * FAQ accordion toggle (if FAQ section exists) — toggle 'active' class on .faq-item when .faq-question clicked
  * Scroll-triggered counter animation (if stats section exists) — parse the number from .stat-number text, animate from 0 to that number, preserve any suffix (+, %, M, K, M+)
  * Testimonial slider (if testimonial_slider exists) — clicking .slider-dot shows matching .testimonial-slide (toggle 'active' class), auto-advance every 5 seconds
  * Image carousel (if .carousel-container exists) — MUST implement fully:
    - var currentSlide = 0; var totalSlides = document.querySelectorAll('.carousel-slide').length;
    - function goToSlide(index): set currentSlide = index, set .carousel-track transform to 'translateX(-' + (index * 100) + '%)', update all .carousel-dot (remove 'active' from all, add 'active' to dot at index)
    - .carousel-prev onclick: goToSlide((currentSlide - 1 + totalSlides) % totalSlides)
    - .carousel-next onclick: goToSlide((currentSlide + 1) % totalSlides)
    - Each .carousel-dot onclick: goToSlide(parseInt(dot.dataset.slide))
    - Auto-advance: setInterval that calls goToSlide((currentSlide + 1) % totalSlides) every 5000ms
    - Pause auto-advance on .carousel-container mouseenter, resume on mouseleave
    - CRITICAL: This carousel MUST work. Test all selectors match the HTML.
  * Gallery lightbox (if #gallery-lightbox exists):
    - Click .gallery-item img → open lightbox, show clicked image full-size
    - .lightbox-close button closes lightbox (remove 'active' class)
    - .lightbox-prev / .lightbox-next navigate between gallery images
    - Click backdrop (outside image) also closes lightbox
    - Keyboard: Escape closes, ArrowLeft/ArrowRight navigate
  * Service modals (if .modal-trigger exists):
    - Click .modal-trigger → find data-modal attribute → add 'active' class to matching modal ID
    - .modal-close button removes 'active' class from parent .detail-modal
    - Click backdrop (outside modal content) also closes
    - Keyboard: Escape closes any open modal
  * Typed.js hero effect (if .typed-text element exists):
    - Parse data-typed attribute (JSON array of strings)
    - Initialize: new Typed('.typed-text', {{ strings: parsedArray, typeSpeed: 50, backSpeed: 30, loop: true, backDelay: 2000 }})
    - Only init if typeof Typed !== 'undefined'
  * Newsletter form (if .newsletter-form exists):
    - On submit, preventDefault, replace form with a styled success message: "Thanks for subscribing!"
    - Do NOT use alert() — show inline message
  * Logo carousel (if .logo-carousel-track exists):
    - Duplicate all children of .logo-carousel-track and append them (creates seamless infinite loop)
    - CSS animation handles the scrolling — JS just duplicates the content
  * Back-to-top button (if #back-to-top exists):
    - Show button (add class 'visible') when scrollY > 300, hide when < 300
    - On click, smooth scroll to top: window.scrollTo({{ top: 0, behavior: 'smooth' }})
  * Search bar toggle (if .search-toggle exists):
    - Click .search-toggle → toggle 'active' class on .search-dropdown
    - Click outside .search-container → remove 'active' from .search-dropdown
    - Escape key closes search dropdown
  * Vanilla-tilt.js (if elements with data-tilt exist):
    - Only init if typeof VanillaTilt !== 'undefined'
    - VanillaTilt.init(document.querySelectorAll('[data-tilt]'), {{ max: 15, speed: 400, glare: true, 'max-glare': 0.2 }})
  * tsParticles (if #tsparticles element exists):
    - Only init if typeof tsParticles !== 'undefined'
    - tsParticles.load('tsparticles', {{ particles: {{ number: {{ value: 40 }}, color: {{ value: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim() || '#3b82f6' }}, links: {{ enable: true, color: '#ffffff', opacity: 0.15 }}, move: {{ enable: true, speed: 1.5 }}, size: {{ value: {{ min: 1, max: 3 }} }}, opacity: {{ value: {{ min: 0.1, max: 0.4 }} }} }}, background: {{ color: 'transparent' }} }})
  * Splitting.js (if elements with data-splitting exist):
    - Only init if typeof Splitting !== 'undefined'
    - Splitting({{ target: '[data-splitting]', by: 'chars' }})
  * Lenis smooth scroll:
    - Only init if typeof Lenis !== 'undefined'
    - const lenis = new Lenis({{ duration: 1.2, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)) }})
    - function raf(time) {{ lenis.raf(time); requestAnimationFrame(raf); }} requestAnimationFrame(raf);
  * Section scroll reveal: IntersectionObserver on all <section> elements — add class 'visible' when section enters viewport (threshold 0.1). Do NOT target nav. DO include footer sections.
  * Staggered grid item reveals: For every grid of cards/items inside sections, add staggered transition-delay so items appear to "fall in" left to right:
    - querySelectorAll('[data-section-type] .grid > *') — for each child, set style.transitionDelay = (index % 3) * 120 + 'ms'
    - This makes columns stagger: col 0 = 0ms, col 1 = 120ms, col 2 = 240ms
    - Apply this to all grid containers, not just specific ones
  * Hero stagger entrance: If .hero-stagger elements exist, they animate via CSS @keyframes heroIn — JS just needs to add 'visible' class to hero section immediately (no delay)
  * Active nav link highlighting on scroll
  * Set footer year: document.getElementById('year') — set textContent to new Date().getFullYear()
- IMPORTANT: Use these exact selectors: '.nav-links' for nav menu, '.nav-toggle' for hamburger button. Do NOT use '.navbar-nav' or '.mobile-menu-btn'
- Keep code clean and concise
- Use modern JS (const, let, arrow functions, querySelectorAll)
- Do NOT wrap code in DOMContentLoaded — the script runs inline at the bottom of body, DOM is already available
- Use an IIFE wrapper: (function() {{ ... }})();
- CRITICAL: Do NOT use template literals (backticks) anywhere in the JS code. Use string concatenation instead.
  BAD:  track.style.transform = `translateX(-${{index * 100}}%)`;
  GOOD: track.style.transform = 'translateX(-' + (index * 100) + '%)';
  This is mandatory because the JS is injected inside a template literal in the host page.
- Do NOT include any CSS or HTML
- Do NOT include any explanation, just the js code block"""


# ═══════════════════════════════════════════════════════════════════════
# ITERATION PROMPT (single Claude call to modify existing site)
# ═══════════════════════════════════════════════════════════════════════

ITERATION_SYSTEM_PROMPT = """You are an expert web developer modifying an existing website that uses pure CSS classes (NO Tailwind, NO utility frameworks).

CURRENT CODE:
--- HTML (includes <style> block + body content with semantic CSS classes) ---
{html}

--- CSS (extracted <style> block — CSS variables, animations, states) ---
{css}

--- JS ---
{js}

CONVERSATION HISTORY:
{conversation_history}

USER'S CHANGE REQUEST: {prompt}

Apply the requested changes. Return TWO fenced code blocks: ```html and ```js

RULES:
- Return COMPLETE updated code (not partial diffs)
- HTML first, then JS
- HTML = <style> block FIRST (CSS variables, fonts, layout, components) + body content with semantic CSS classes
- Use pure CSS classes for layout, spacing, typography, colors, responsive
- Use CSS variables: var(--primary), var(--bg), var(--accent), etc.
- NO Tailwind utility classes. Write proper CSS in the <style> block.
- Maintain existing design and functionality unless changes are requested
- Do NOT include any explanation, just the two code blocks

SECTION SIZE CONSTRAINTS:
- Hero: max height 80vh. NEVER taller than viewport.
- All sections: keep same size as original. No excessive padding.

IMAGE HANDLING:
- "Add background image" = CSS background-image ONLY (no extra <img> tag)
- NEVER add BOTH a background-image AND a foreground <img> for the same purpose
- Background images: background-size: cover; background-position: center; with overlay

JS-DEPENDENT CLASS NAMES (do NOT rename — JS will break):
.nav-links, .nav-toggle, .faq-item, .faq-question, .faq-answer,
.testimonial-slide, .slider-dot, .carousel-container, .carousel-track,
.carousel-slide, .carousel-prev, .carousel-next, .carousel-dot,
#gallery-lightbox, .gallery-item, .modal-trigger, .detail-modal,
.modal-close, .stat-number, #year, #back-to-top"""


# ═══════════════════════════════════════════════════════════════════════
# COMPONENT-BASED EDITING (targeted section edits)
# ═══════════════════════════════════════════════════════════════════════

COMPONENT_ROUTER_PROMPT = """You are a website section classifier. Given a user's edit request and a list of sections on the page, determine which section(s) need to be modified.

AVAILABLE SECTIONS:
{sections_list}

{conversation_context}

USER REQUEST: {prompt}

RULES:
- Return ONLY a JSON array of section IDs that need editing
- Most requests target 1 section. Multi-section edits are rare.
- If the request is ONLY about colors, fonts, or spacing (e.g., "change color to blue", "use different font"), return ["__style__"]
- If the request mentions "animation", "effects", "more beautiful", "redesign", "make it better", "more modern", "more professional", "improve design" → these require HTML changes, NOT just CSS. Return ["__full__"]
- If the request asks to ADD/INSERT a new section (e.g., "add a footer", "add testimonials section", "add a gallery"), return ["__append__:SECTION_TYPE"] where SECTION_TYPE is one of: hero, features, services, stats, testimonials, pricing, faq, cta, team, gallery, about, contact, footer, timeline, newsletter
  Examples: "add footer" → ["__append__:footer"], "add a testimonials section" → ["__append__:testimonials"], "add gallery section" → ["__append__:gallery"]
- If the request is about the whole page layout, rearranging sections, or a full redesign, return ["__full__"]
- If the request mentions "hero", "header", "banner" → target the hero section
- If the request mentions "cards", "features", "services" → target the features/services section
- If the request mentions "footer", "bottom" → target the footer section
- If the request mentions "nav", "menu", "navigation" → target the navbar section
- If the request mentions "testimonials", "reviews" → target the testimonials section
- If the request mentions "pricing", "plans" → target the pricing section
- If the request mentions "contact", "form" → target the contact section
- If the request mentions "FAQ", "questions" → target the faq section
- If the request mentions "team", "members" → target the team section
- If the request mentions "gallery", "images", "photos" → target the gallery section
- If the request mentions "stats", "numbers", "counters" → target the stats section
- FOLLOW-UP DETECTION: If the user's message is a follow-up about a previous edit (e.g., "it's broken", "I don't see it", "still wrong", "fix that", "looks bad", "change the image there"), target the SAME section from the most recent edit shown in LAST EDITED below
- If ambiguous AND there is a recent edit, prefer the last-edited section
- If ambiguous and no recent context, target the section that best matches the request context

Return ONLY the JSON array, nothing else. Example: ["section-2"]
Or for multiple: ["section-1", "section-4"]
Or for style: ["__style__"]
Or to add a new section: ["__append__:footer"]
Or for full rewrite: ["__full__"]"""


COMPONENT_EDIT_PROMPT = """You are an expert frontend developer editing a single section of a website.

DESIGN SYSTEM (CSS variables — use these for consistency):
{css_vars}

AVAILABLE CSS CLASSES (these are pre-defined in the page's <style> block — USE THEM):
Layout: .container (max-width 1200px), .container-wide (1400px), .container-narrow (800px), .container-xs (600px)
Grid: .grid-2 (2 columns), .grid-3 (3 columns), .grid-4 (4 columns) — all auto-responsive
Buttons: .btn-primary (gradient bg), .btn-secondary (outline), .btn-primary-light (white bg), .btn-secondary-light (white outline)
  .btn-group (flex row of buttons), .btn-group.center (centered)
Cards: .card (styled card), .card-title, .card-text, .card-body, .card-image, .card-link, .icon-box (icon container)
Images: .img-cover (object-fit cover), .img-wrapper (rounded container)
Hero: .hero-section (padded section), .hero-section-flush (edge-to-edge), .hero-heading (huge responsive h1), .hero-subtitle (lead text)
  .hero-split-grid (2-col hero), .hero-ctas (button row), .hero-ctas-center (centered), .trust-line (small muted text)
  .hero-bg-cover (full-bleed bg image), .hero-overlay (dark gradient), .hero-overlay-left, .hero-overlay-center
  .bg-number (giant faded decorative number), .section-label + .label-line (small uppercase label)
  .floating-card (floating accent card), .browser-frame (mockup frame)
Section: .section-header, .section-title, .section-subtitle, .text-center, .text-light (white text)
Nav: .navbar, .navbar-inner, .nav-brand, .nav-links, .nav-toggle, .nav-cta, .mobile-cta, .nav-scrolled
Footer: .footer-grid, .footer-heading, .footer-links, .footer-description, .social-links, .social-link, .footer-bottom
Stats: .stat-item, .stat-icon, .stat-number, .stat-label
FAQ: .faq-item, .faq-question, .faq-answer
Testimonials: .stars, .testimonial-quote, .testimonial-quote-lg, .testimonial-author, .slider-dots, .slider-dot
Pricing: .pricing-card, .pricing-card.featured, .plan-price, .plan-features, .popular-badge
Gallery: .gallery-item, .gallery-image, .gallery-lightbox, .masonry-grid, .masonry-item, .masonry-overlay
Carousel: .carousel-container, .carousel-track, .carousel-slide, .carousel-image, .carousel-prev, .carousel-next, .carousel-dots, .carousel-dot
Forms: .form-input, .form-textarea, .newsletter-form, .form-hint, .contact-form, .contact-info, .contact-item, .contact-icon
Other: .team-photo, .timeline-item, .timeline-date, .timeline-dot, .timeline-card, .logo-cloud, .logo-item, .trust-badges, .trust-badge

SECTION TO EDIT ({section_type} section):
{section_html}

USER REQUEST: {prompt}

RULES:
- Return ONLY the updated section HTML inside a single ```html code block
- Return the COMPLETE section element (opening tag through closing tag)
- Use the CSS classes listed above — they are already defined in the <style> block
- Use CSS variables: var(--accent), var(--bg), var(--radius), etc.
- Keep the same outer element tag and data-section-type attribute
- Keep the same data-section-id attribute
- For images, keep existing src URLs unless user asks to change images
- Do NOT add Font Awesome script tags — icons are already loaded
- Do NOT wrap in extra divs or add <html>/<head>/<body> tags
- Do NOT include any explanation, just the html code block
- You CAN freely change the section's internal layout/structure when the user asks for it (e.g., converting hero_split to hero with background image)
- Do NOT generate large inline SVGs or decorative clip-path shapes — use CSS gradients, borders, and the existing utility classes instead
- Keep decorative elements minimal and CSS-based (gradients, box-shadows, border-radius, pseudo-elements)

SECTION SIZE CONSTRAINTS (CRITICAL):
- Hero sections: max height 80vh. NEVER make a hero taller than viewport.
- All other sections: keep the same visual size as the original.
- Do NOT add excessive padding/margins that make the section abnormally tall.

IMAGE HANDLING FOR EDITS:
- "Add background image" = CSS background-image ONLY. Do NOT also add a foreground <img> tag.
- NEVER add BOTH a background-image AND a foreground <img> for the same visual purpose.
- When converting an <img> to a background image: use the SAME src URL from the existing <img> tag as the background-image URL
- Background image hero: use .hero-bg-cover + .hero-overlay classes, or inline style with background-size: cover; background-position: center;
- When moving image from side to background, REMOVE the old <img> tag completely
- Make sure text is readable over the background (use .text-light class + dark overlay)

CRITICAL — JS-DEPENDENT CLASS NAMES (DO NOT rename or remove these):
JavaScript already exists on the page and depends on these exact class names and IDs.
If you change them, the interactive features will break silently.

NAVBAR:
- .nav-links MUST keep class "nav-links"
- .nav-toggle MUST keep class "nav-toggle"
- .nav-cta stays visible on desktop; .mobile-cta stays hidden on desktop
- Mobile responsive behavior is handled by existing CSS @media rules — do NOT override

FAQ ACCORDION:
- Each item MUST have class "faq-item"
- Question button MUST have class "faq-question"
- Answer div MUST have class "faq-answer"
- JS toggles "active" class on .faq-item when clicked

TESTIMONIAL SLIDER:
- Each slide MUST have class "testimonial-slide"
- Navigation dots MUST have class "slider-dot" with data-slide="0", "1", etc.
- JS toggles "active" class to show/hide slides

IMAGE CAROUSEL:
- Container MUST have class "carousel-container"
- Track MUST have class "carousel-track"
- Each slide MUST have class "carousel-slide" with min-w-full
- Prev/next buttons MUST have classes "carousel-prev" and "carousel-next"
- Dots MUST have class "carousel-dot" with data-slide="0", "1", etc.
- JS translates .carousel-track by -100% per slide

GALLERY LIGHTBOX:
- Each gallery item MUST have class "gallery-item"
- Lightbox container MUST have id "gallery-lightbox"
- Close/prev/next buttons MUST have classes "lightbox-close", "lightbox-prev", "lightbox-next"

SERVICE MODALS:
- Trigger cards MUST have class "modal-trigger" with data-modal="modal-N"
- Modal divs MUST have class "detail-modal" with matching id="modal-N"
- Close button MUST have class "modal-close"

STATS:
- Counter elements MUST have class "stat-number" (JS animates from 0 to value)
- Number + suffix (e.g. "500+") MUST be in the SAME .stat-number element

FOOTER:
- Year span MUST have id="year" (JS sets current year)

OTHER:
- Search dropdown: class "search-toggle" and "search-dropdown" (JS toggles "active")
- Back-to-top: id "back-to-top" (JS adds "visible" class on scroll)
- data-tilt attributes: JS initializes VanillaTilt on these elements
- data-splitting attributes: JS initializes Splitting.js on these elements
- data-aos attributes: AOS library handles scroll animations — keep these"""


STYLE_EDIT_PROMPT = """You are an expert frontend developer editing the CSS variables and style block of a website.

CURRENT STYLE BLOCK:
{css}

ALL SECTION TYPES ON PAGE: {section_types}

USER REQUEST: {prompt}

RULES:
- Return ONLY the updated <style> block inside a single ```css code block
- CRITICAL: You MUST return the COMPLETE CSS — every single rule, unchanged, except for what the user asked to modify
- NEVER remove or shorten existing CSS rules — the output MUST be the same length or longer than the input
- Only modify what the user specifically requested (colors, fonts, spacing, etc.)
- CSS variables are in :root {{ ... }}
- Maintain ALL animation keyframes, media queries, component styles, responsive rules, and utility classes
- If in doubt, keep the rule as-is
- Do NOT include any explanation, just the css code block"""


APPEND_SECTION_PROMPT = """You are an expert frontend developer adding a NEW section to an existing website.

DESIGN SYSTEM (CSS variables — use these for consistency):
{css_vars}

AVAILABLE CSS CLASSES (pre-defined in the page's <style> block — USE THEM):
Layout: .container, .container-wide, .container-narrow, .container-xs
Grid: .grid-2, .grid-3, .grid-4 (auto-responsive)
Buttons: .btn-primary, .btn-secondary, .btn-primary-light, .btn-secondary-light, .btn-group
Cards: .card, .card-title, .card-text, .card-body, .card-image, .icon-box
Images: .img-cover, .img-wrapper
Section: .section-header, .section-title, .section-subtitle, .text-center, .text-light
Hero: .hero-section, .hero-heading, .hero-subtitle, .hero-split-grid, .hero-ctas, .hero-bg-cover, .hero-overlay
Stats: .stat-item, .stat-icon, .stat-number, .stat-label
FAQ: .faq-item, .faq-question, .faq-answer
Testimonials: .stars, .testimonial-quote, .testimonial-author, .slider-dots, .slider-dot
Pricing: .pricing-card, .plan-price, .plan-features, .popular-badge
Gallery: .gallery-item, .gallery-image, .masonry-grid, .masonry-item
Forms: .form-input, .contact-form, .newsletter-form
Footer: .footer-grid, .footer-heading, .footer-links, .social-links, .footer-bottom

EXISTING SECTIONS ON PAGE (for context — match the style):
{existing_sections}

BRAND/BUSINESS CONTEXT:
{brand_context}

SECTION TO ADD: {section_type}
PATTERN TEMPLATE:
{pattern_template}

USER REQUEST: {prompt}

RULES:
- Return ONLY the new section HTML inside a single ```html code block
- The section MUST have data-section-type="{section_type}" attribute
- Use the CSS classes listed above — they are already defined in the <style> block
- Use CSS variables: var(--accent), var(--bg), var(--radius), etc.
- Do NOT generate large inline SVGs or decorative clip-path shapes
- Match the design style of the existing sections (colors, fonts, spacing, border radius)
- Write REAL content that matches the business context — no "Lorem ipsum" or placeholder text
- For images, use placeholder format: src="{{{{IMG:descriptive keywords}}}}"
- Do NOT add Font Awesome script tags — icons are already loaded
- Do NOT wrap in extra divs or add <html>/<head>/<body> tags
- Do NOT include any explanation, just the html code block
- Use standard section padding consistent with the existing page
- Footer sections: use dark background (style="background: #1a1a2e")

SECTION SIZE CONSTRAINTS:
- Keep sections compact and content-dense. No min-h-screen.
- Do NOT add excessive padding/margins.

CRITICAL — JS-DEPENDENT CLASS NAMES:
- Footer: year span MUST have id="year"
- FAQ: items need class "faq-item", questions "faq-question", answers "faq-answer"
- Gallery: items need class "gallery-item", lightbox id "gallery-lightbox"
- Stats: counter elements MUST have class "stat-number"
- Testimonial slider: slides "testimonial-slide", dots "slider-dot"
- Carousel: container "carousel-container", track "carousel-track", slides "carousel-slide"
- Service modals: triggers "modal-trigger" with data-modal, modals "detail-modal" with matching id"""


# ═══════════════════════════════════════════════════════════════════════
# Design variety seeds — niche-aware
# ═══════════════════════════════════════════════════════════════════════

# Category → list of design seeds appropriate for that category
NICHE_DESIGN_SEEDS = {
    "tech": [
        "Dark theme (#0a0a0a bg) with electric blue (#3b82f6) + cyan gradients. Use hero_full_image + icon_grid. Futuristic, bold typography. Glass-morphism cards.",
        "Deep navy (#0f172a bg) with neon green (#22c55e) accents. Use hero_asymmetric + card_grid. Terminal/hacker aesthetic, monospace headings.",
        "Pure black (#000000 bg) with violet (#8b5cf6) + pink (#ec4899) gradient accents. Use hero_center + feature_split. Dramatic, high-contrast.",
        "Clean white (#ffffff bg) with indigo (#4f46e5) + sharp geometric accents. Use hero_product_mockup + icon_grid. Apple-like precision.",
        "Warm gray (#1c1917 bg) with amber (#f59e0b) accents. Use hero_split + card_grid. Premium dev-tool aesthetic.",
        "Light gray (#f8fafc bg) with teal (#0d9488) + dark charcoal text. Use hero_split + feature_cards. Modern SaaS clean.",
    ],
    "corporate": [
        "Deep charcoal (#1a1a2e bg) with gold (#d4a843) accents. Use hero_full_image + feature_split. Executive, powerful.",
        "Navy (#0c1b33 bg) with silver (#94a3b8) + white text. Use hero_center + card_grid. Institutional authority.",
        "Slate (#0f172a bg) with emerald (#059669) accents. Use hero_split + icon_grid. Finance/consulting premium.",
        "Off-white (#fafaf9 bg) with deep navy (#1e293b) + copper (#b45309) accents. Use hero_full_image + feature_split. Heritage luxury.",
        "Warm white (#fffbeb bg) with forest green (#166534) + gold. Use hero_split + card_grid. Trust and tradition.",
        "Light stone (#f5f5f4 bg) with burgundy (#881337) + dark gray. Use hero_asymmetric + feature_cards. Bold corporate.",
    ],
    "luxury": [
        "Black (#050505 bg) with gold (#c8a84e) + cream text. Use hero_full_image + feature_split. Ultra-premium, editorial.",
        "Deep plum (#1a0a2e bg) with rose gold (#e8b4b8) accents. Use hero_center + card_grid. Feminine luxury.",
        "Charcoal (#111111 bg) with champagne (#d4b896) + white. Use hero_asymmetric + feature_cards. Boutique hotel feel.",
        "Ivory (#faf8f5 bg) with black (#111111) + gold (#b8860b). Use hero_split + feature_split. Editorial luxury.",
        "Warm cream (#f5f0e8 bg) with deep green (#1a3a2a) + brass. Use hero_full_image + card_grid. Organic luxury.",
        "Pearl white (#f8f6f3 bg) with matte black (#1c1c1c) + copper (#b87333). Use hero_asymmetric + icon_grid. Architectural luxury.",
    ],
    "creative": [
        "Near-black (#0d0d0d bg) with multi-color gradient accents (pink→orange→yellow). Use hero_asymmetric + feature_cards. Bold, expressive.",
        "Dark purple (#1e1b4b bg) with lime (#a3e635) + cyan (#22d3ee). Use hero_center + card_grid. Electric creative energy.",
        "Deep teal (#042f2e bg) with coral (#fb7185) + white. Use hero_split + feature_split. Creative studio.",
        "Bright white (#ffffff bg) with black (#000000) + one bold accent (red #ef4444). Use hero_asymmetric + icon_grid. Swiss design minimal.",
        "Soft pink (#fdf2f8 bg) with deep violet (#5b21b6) + black text. Use hero_split + feature_cards. Fashion-forward.",
        "Light lavender (#f5f3ff bg) with orange (#ea580c) + charcoal. Use hero_center + card_grid. Playful creative.",
    ],
    "food": [
        "Dark moody (#1a1209 bg) with warm amber (#d97706) + cream text. Use hero_full_image + feature_cards. Fine dining, atmospheric.",
        "Rich espresso (#1c1210 bg) with copper (#c2884c) + ivory. Use hero_center + service_modal. Coffee/bistro luxury.",
        "Charcoal (#1f1f1f bg) with red (#dc2626) + white. Use hero_full_image + feature_cards. Bold steakhouse/grill.",
        "Warm cream (#fef3c7 bg) with terracotta (#c2410c) + dark brown. Use hero_split + card_grid. Mediterranean warmth.",
        "Soft sage (#f0fdf4 bg) with deep green (#166534) + wood brown. Use hero_split + feature_cards. Farm-to-table organic.",
        "Clean white (#ffffff bg) with coral (#f97316) + charcoal. Use hero_full_image + feature_cards. Modern cafe bright.",
    ],
    "health": [
        "Deep teal (#042f2e bg) with aqua (#2dd4bf) + white text. Use hero_split + card_grid. Medical tech futuristic.",
        "Navy (#0c2340 bg) with sky blue (#38bdf8) + clean white. Use hero_center + icon_grid. Clinical precision.",
        "Dark slate (#0f172a bg) with green (#22c55e) + light gray. Use hero_full_image + feature_split. Health tech modern.",
        "Soft mint (#f0fdfa bg) with teal (#0d9488) + dark text. Use hero_split + card_grid. Calming wellness.",
        "Warm white (#fffbeb bg) with sage (#65a30d) + earth brown. Use hero_split + feature_cards. Natural health.",
        "Clean blue-white (#f0f9ff bg) with royal blue (#2563eb) + navy text. Use hero_center + icon_grid. Professional healthcare.",
    ],
    "nature": [
        "Forest dark (#0a1f0a bg) with emerald (#34d399) + gold. Use hero_full_image + feature_split. Deep nature immersive.",
        "Deep ocean (#0c1b33 bg) with turquoise (#14b8a6) + sand. Use hero_center + card_grid. Coastal resort.",
        "Warm sand (#fefce8 bg) with forest (#166534) + earth brown. Use hero_full_image + feature_cards. Eco-resort.",
        "Light sage (#ecfdf5 bg) with deep green (#065f46) + wood tones. Use hero_split + card_grid. Sustainable brand.",
    ],
    "wedding": [
        "Charcoal (#1a1a1a bg) with blush pink (#f9a8d4) + gold. Use hero_full_image + feature_cards. Dramatic elegance.",
        "Deep burgundy (#450a0a bg) with rose gold (#e8b4b8) + cream. Use hero_center + card_grid. Romantic luxury.",
        "Soft blush (#fdf2f8 bg) with sage (#6b8f71) + gold. Use hero_split + feature_split. Garden wedding.",
        "Ivory (#fffff0 bg) with dusty rose (#d4a0a0) + deep green. Use hero_full_image + feature_cards. Classic romance.",
    ],
    "education": [
        "Dark navy (#0f172a bg) with yellow (#eab308) + white. Use hero_split + card_grid. Bold academic.",
        "Deep indigo (#1e1b4b bg) with cyan (#06b6d4) + light text. Use hero_center + icon_grid. EdTech modern.",
        "Light cream (#fefce8 bg) with navy (#1e3a5f) + orange accent. Use hero_split + feature_cards. Warm institutional.",
        "Clean white (#f8fafc bg) with blue (#3b82f6) + dark gray. Use hero_center + card_grid. Clean academic.",
    ],
    "minimal": [
        "Pure black (#000000 bg) with white (#ffffff) text only. Use hero_center + feature_split. Ultra-minimal dark.",
        "Dark gray (#18181b bg) with light gray (#d4d4d8) + single accent. Use hero_asymmetric + icon_grid. Monochrome modern.",
        "Off-white (#fafafa bg) with black (#000000) + no accent. Use hero_split + card_grid. Swiss clean.",
        "Warm cream (#f5f5f0 bg) with charcoal (#292524) + subtle gold. Use hero_center + feature_split. Warm minimal.",
    ],
}

# Map niche keys → design category
_NICHE_CATEGORY_MAP = {
    # Tech
    "ai_startup": "tech",
    "blockchain": "tech",
    "cloud_services": "tech",
    "coding_bootcamp": "tech",
    "cybersecurity": "tech",
    "electronics_store": "tech",
    "saas": "tech",
    "software": "tech",
    "tech_startup": "tech",
    "web_agency": "tech",
    "gaming": "tech",
    "iot": "tech",
    "it_services": "tech",
    # Corporate
    "accounting": "corporate",
    "consulting": "corporate",
    "construction": "corporate",
    "coworking_space": "corporate",
    "insurance": "corporate",
    "law_firm": "corporate",
    "logistics": "corporate",
    "moving_company": "corporate",
    "real_estate": "corporate",
    "recruitment": "corporate",
    "marketing_agency": "corporate",
    "financial_advisor": "corporate",
    # Luxury
    "fashion_boutique": "luxury",
    "jewelry": "luxury",
    "luxury_hotel": "luxury",
    "luxury_real_estate": "luxury",
    "spa": "luxury",
    "beauty_salon": "luxury",
    "car_dealership": "luxury",
    "cruise": "luxury",
    "wine": "luxury",
    # Creative
    "art_gallery": "creative",
    "dance_studio": "creative",
    "film_production": "creative",
    "graphic_design": "creative",
    "interior_design": "creative",
    "music": "creative",
    "photography": "creative",
    "tattoo": "creative",
    "theater": "creative",
    "podcast": "creative",
    "video_production": "creative",
    # Food
    "bakery": "food",
    "brewery": "food",
    "catering": "food",
    "coffee_shop": "food",
    "food_truck": "food",
    "restaurant": "food",
    "meal_prep": "food",
    # Health
    "chiropractor": "health",
    "dentist": "health",
    "fitness": "health",
    "gym": "health",
    "healthcare": "health",
    "mental_health": "health",
    "nutrition": "health",
    "pharmacy": "health",
    "physiotherapy": "health",
    "veterinary": "health",
    "yoga": "health",
    "wellness": "health",
    # Nature
    "environmental": "nature",
    "gardening": "nature",
    "landscaping": "nature",
    "organic_farm": "nature",
    "pet_care": "nature",
    "sustainability": "nature",
    # Wedding
    "wedding_planner": "wedding",
    "florist": "wedding",
    "bridal": "wedding",
    "event_management": "wedding",
    # Education
    "education": "education",
    "language_school": "education",
    "music_school": "education",
    "tutoring": "education",
    "daycare": "education",
    "driving_school": "education",
    "church": "education",
    "community_center": "education",
}

# Fallback pool for unmapped niches
_FALLBACK_SEEDS = [
    "Dark theme (#0a0a0a bg) with electric blue (#3b82f6) + white text. Use hero_full_image + card_grid. Modern, bold, high-contrast.",
    "Deep navy (#0c1b33 bg) with gold (#d4a843) + cream. Use hero_split + feature_split. Premium, authoritative.",
    "Charcoal (#1c1c1c bg) with coral (#f97316) + white. Use hero_center + feature_cards. Warm, energetic.",
    "Clean white (#ffffff bg) with black (#000000) + one bold accent. Use hero_asymmetric + icon_grid. Swiss precision.",
    "Warm cream (#faf8f5 bg) with deep green (#166534) + gold. Use hero_split + card_grid. Organic, premium.",
    "Soft gray (#f8fafc bg) with indigo (#4f46e5) + dark charcoal. Use hero_split + icon_grid. Modern SaaS.",
    "Pure black (#000000 bg) with gradient accents (violet→pink). Use hero_center + feature_split. Bold, dramatic.",
    "Slate (#1e293b bg) with emerald (#10b981) + light gray. Use hero_full_image + card_grid. Professional tech.",
]


_last_used_seeds: dict[str, str] = {}  # category -> last seed used


def get_design_seed(niche_key: str = None) -> str:
    """Pick a design seed that matches the detected niche category.
    Avoids repeating the last-used seed for the same category."""
    category = None
    pool = _FALLBACK_SEEDS

    if niche_key:
        category = _NICHE_CATEGORY_MAP.get(niche_key)
        if category and category in NICHE_DESIGN_SEEDS:
            pool = NICHE_DESIGN_SEEDS[category]

    cat_key = category or "__fallback__"
    last = _last_used_seeds.get(cat_key)

    # Filter out last-used seed to avoid repeats
    candidates = [s for s in pool if s != last] if last and len(pool) > 1 else pool
    chosen = random.choice(candidates)
    _last_used_seeds[cat_key] = chosen
    return chosen


# ═══════════════════════════════════════════════════════════════════════
# Utility functions
# ═══════════════════════════════════════════════════════════════════════


def parse_json_response(text: str) -> dict:
    """Extract JSON from an LLM response."""
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def parse_single_code_block(text: str, expected_lang: str = None) -> str:
    """Extract content from a single fenced code block."""
    pattern = r"`{3,}\s*(\w*)[ \t]*\r?\n(.*?)`{3,}"
    matches = re.findall(pattern, text, re.DOTALL)
    for lang, code in matches:
        lang = lang.lower()
        if lang in ("javascript", "jsx"):
            lang = "js"
        elif lang == "stylesheet":
            lang = "css"
        if expected_lang is None or lang == expected_lang:
            return code.strip()
    # Fallback: strip any leading/trailing code fence markers and return
    cleaned = text.strip()
    # Remove leading ```html or ```css or ```js etc.
    cleaned = re.sub(r"^`{3,}\s*\w*\s*\n?", "", cleaned)
    # Remove trailing ```
    cleaned = re.sub(r"\n?`{3,}\s*$", "", cleaned)
    return cleaned.strip() if not matches else ""


def parse_code_blocks(text: str) -> dict[str, str]:
    """Extract html, css, js from fenced code blocks.

    Uses line-by-line parsing to handle nested backticks inside code blocks.
    """
    result = {"html": "", "css": "", "js": ""}
    lines = text.split("\n")
    current_lang = None
    current_lines: list[str] = []
    fence_pattern = re.compile(r"^`{3,}\s*(\w*)[ \t]*$")

    for line in lines:
        m = fence_pattern.match(line)
        if m:
            if current_lang is not None:
                # Closing fence — save accumulated content
                code = "\n".join(current_lines).strip()
                if code and current_lang in result:
                    result[current_lang] = code
                current_lang = None
                current_lines = []
            else:
                # Opening fence — start accumulating
                lang = m.group(1).lower()
                if lang in ("javascript", "jsx"):
                    lang = "js"
                elif lang == "stylesheet":
                    lang = "css"
                current_lang = lang
                current_lines = []
        elif current_lang is not None:
            current_lines.append(line)

    # Handle unclosed fence (Claude sometimes omits closing ```)
    if current_lang is not None and current_lines:
        code = "\n".join(current_lines).strip()
        if code and current_lang in result:
            result[current_lang] = code

    return result


def summarize_html(html: str, max_lines: int = 200) -> str:
    """Create a summary of HTML structure for the JS stage."""
    lines = html.split("\n")
    if len(lines) <= max_lines:
        return html
    return "\n".join(lines[:120]) + "\n\n<!-- ... more sections ... -->\n\n" + "\n".join(lines[-80:])


def extract_section_types(html: str) -> str:
    """Extract section types from data-section-type attributes."""
    types = re.findall(r'data-section-type="([^"]+)"', html)
    return ", ".join(types) if types else "navbar, hero, features, testimonials, cta, footer"


def extract_sections_summary(plan: dict) -> str:
    """Extract section layout info from plan for CSS stage."""
    sections = plan.get("sections", [])
    summary = []
    for s in sections:
        stype = s.get("type", "unknown")
        pattern = s.get("pattern", "unknown")
        headline = s.get("content", {}).get("headline", "")
        items_count = len(s.get("content", {}).get("items", []))
        line = f"- {stype} (pattern: {pattern})"
        if headline:
            line += f' — "{headline}"'
        if items_count:
            line += f" [{items_count} items]"
        summary.append(line)
    return "\n".join(summary)
