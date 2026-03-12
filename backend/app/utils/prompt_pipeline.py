"""
Multi-stage AI website generation pipeline.

Stage 1: Plan      → GPT-4.1 analyzes prompt → JSON structure + layout patterns
Stage 2: HTML      → Claude generates HTML with Tailwind CSS + <style> block
Stage 3: JS        → Claude generates interactions/animations

CSS is embedded as Tailwind utility classes in the HTML output.
A small <style> block handles CSS variables, animations, and states.
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

    # Style preset: inject rarely (10% chance) to avoid conflicting with design seed
    if random.random() < 0.10:
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

TEMPLATE_CUSTOMIZE_PROMPT = """You are an expert frontend developer. Study the REFERENCE TEMPLATE below, then generate a NEW website using Tailwind CSS utility classes that matches the template's visual quality.

REFERENCE TEMPLATE (study this for design quality, layout patterns, hover effects, visual texture):
{template_html}

BUSINESS PLAN (use this content):
{plan_json}

YOUR TASK:
Create a website that looks AS GOOD as the reference template, but using Tailwind CSS utility classes + CSS variables. Study the template's:
- Hero layout and visual impact
- Card hover effects and animations
- Section spacing and visual rhythm
- Typography scale and weight usage
- Color usage and gradients
- Background textures and decorative elements
Then recreate that level of quality using Tailwind classes.

OUTPUT FORMAT:
- Return ONLY HTML inside a single ```html code block
- Output a <style> block FIRST (CSS variables, fonts, custom effects) then HTML body content
- NO <html>, <head>, <body>, <link>, <meta> tags
- Do NOT add Font Awesome <script> or <link> tags — FA is pre-loaded
- Do NOT include any JavaScript

MANDATORY STRUCTURE:
1. <style> block with:
   - @import for Google Fonts (from plan's heading_font + body_font)
   - :root {{ --primary, --secondary, --accent, --bg, --bg-surface, --text, --text-muted, --font-heading, --font-body, --radius, --radius-btn }}
   - body, heading, section animation styles
   - .nav-links, .nav-toggle, .nav-scrolled, .faq-item/.faq-answer, .testimonial-slide, .pricing-card.featured styles
   - Mobile responsive @media for nav
   - CUSTOM EFFECTS from the reference template (clip-paths, hover pseudo-elements, noise textures, faded background numbers — put these in <style> block)

2. HTML body with Tailwind utility classes:
   - EVERY <section> MUST have data-section-type="TYPE" (hero, features, services, testimonials, team, gallery, contact, cta, faq, stats, pricing, footer)
   - Use <nav> for navbar, <footer> for footer, <section> for content
   - Use Tailwind classes: bg-[var(--bg)], text-[var(--text)], rounded-[var(--radius)], etc.
   - ⚠️ Use {{{{IMG:role query}}}} placeholders for ALL images — NEVER write real pexels.com/unsplash.com URLs (they will 404)
   - Use Font Awesome icons: <i class="fa-solid fa-icon-name"></i>
   - Include ALL sections from the plan

TAILWIND CLASSES TO USE:
- Container: max-w-[1200px] mx-auto px-6
- Card: bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-lg hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 border border-white/[0.06]
- Btn primary: inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold
- Grid: grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6
- Section: py-20 md:py-28 relative
- Hero headline: text-5xl md:text-6xl lg:text-7xl font-bold (NEVER text-3xl or text-4xl)

PRESERVE FROM REFERENCE (recreate in <style> block):
- Card hover choreography: border-left reveal, ::before gradient sweep, title color change
- Hero depth: faded background elements, gradient overlays, staggered entrance animations
- Section texture: alternating backgrounds, decorative elements
- Transition timing: cubic-bezier easing, staggered delays

ADD THESE ELEMENTS:
- <!-- SEO_META --> after </style> with meta description, og:title, og:description <!-- END_SEO_META -->
- <!-- FAVICON --> with SVG favicon <!-- END_FAVICON -->
- WhatsApp float: <a href="https://wa.me/971XXXXXXXXX" class="whatsapp-float fixed bottom-6 right-6 w-14 h-14 bg-[#25D366] rounded-full flex items-center justify-center text-white text-2xl shadow-lg hover:scale-110 transition-all z-50"><i class="fa-brands fa-whatsapp"></i></a>
- Back-to-top: <button id="back-to-top" class="fixed bottom-6 right-24 w-11 h-11 bg-[var(--primary)] text-white rounded-full flex items-center justify-center shadow-lg opacity-0 pointer-events-none transition-all z-50"><i class="fa-solid fa-chevron-up text-sm"></i></button>

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

CUSTOM CSS EFFECTS — add these in the <style> block (Tailwind can't express them):
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
  * Same Tailwind utility patterns and class naming
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
- Responsive: mobile-first with Tailwind breakpoints (sm:, md:, lg:, xl:)
- Do NOT include any explanation — just the html code block"""


# ═══════════════════════════════════════════════════════════════════════
# STAGE 2: HTML Generation (LEGACY — kept for reference, use build_html_prompt() instead)
# ═══════════════════════════════════════════════════════════════════════

HTML_GEN_SYSTEM_PROMPT = """You are an expert frontend developer. Generate HTML with Tailwind CSS utility classes.

WEBSITE PLAN:
{plan_json}

RULES:
- Return ONLY HTML inside a single ```html code block
- Output a <style> block FIRST (for CSS variables, fonts, animations) then the HTML body content
- NO <html>, <head>, <body>, <link> tags — just <style> block + body content
- Use Tailwind CSS utility classes for ALL layout, spacing, typography, colors, responsive design, hover effects
- Use CSS variables via Tailwind arbitrary values: text-[var(--primary)], bg-[var(--bg)], rounded-[var(--radius)], etc.
- Use semantic HTML5: <nav>, <header>, <main>, <section>, <footer>
- EVERY content section MUST use: <section data-section-type="{{type}}"> — never <div>
- Use the EXACT content from the plan — headlines, descriptions, button text, etc.
- Use Font Awesome icons exactly as specified: <i class="fa-solid fa-icon-name"></i>
- Add data-aos="fade-up" on grid items (cards, faq items, etc.) — NOT on section wrappers
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
- Card icon box: class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--primary)] mb-5" style="background: color-mix(in srgb, var(--primary) 12%, transparent)"
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

navbar pattern:
  <nav class="fixed top-0 w-full z-50 backdrop-blur-md [bg-white/85 border-b border-black/[0.06] OR bg-black/40 border-b border-white/[0.08] based on theme] transition-all duration-300">
    <div class="max-w-[1200px] mx-auto px-6 flex justify-between items-center py-4">
      <a href="#" class="flex items-center gap-2.5 no-underline text-[var(--text)] font-bold text-lg">
        LOGO_MARK (see logo rules below)
        <span class="font-bold text-lg tracking-tight">Brand Name</span>
      </a>
      <button class="nav-toggle hidden bg-transparent border-none text-2xl cursor-pointer text-[var(--text)] p-2" aria-label="Toggle menu"><i class="fa-solid fa-bars"></i></button>
      <ul class="nav-links flex list-none gap-8 items-center m-0 p-0">
        <li><a href="#services" class="no-underline font-medium text-[var(--text)] hover:text-[var(--primary)] transition-colors duration-300">Services</a></li>
        <li class="mobile-cta hidden"><a href="#" class="inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline">Get Started</a></li>
      </ul>
      <a href="#" class="nav-cta inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg">Get Started</a>
    </div>
  </nav>
  NAVBAR RULES: Use bg-white/85 + border-black for light themes, bg-black/40 + border-white for dark themes.

LOGO MARK RULES — generate a unique logo for each brand (NOT a plain colored square):
  Choose ONE of these logo styles based on the brand and industry:

  STYLE A — Brand initial in gradient circle (best for single-word brands):
    <span class="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-sm shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">H</span>
    (Use the first letter of the brand name)

  STYLE B — Industry icon in gradient square (best for service businesses):
    <span class="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center text-white text-sm shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))"><i class="fa-solid fa-scale-balanced"></i></span>
    (Pick a Font Awesome icon that matches the industry: fa-scale-balanced for law, fa-code for tech, fa-utensils for restaurant, fa-dumbbell for fitness, fa-building for real estate, fa-stethoscope for healthcare, fa-graduation-cap for education, fa-plane for travel, fa-palette for creative, fa-chart-line for finance, fa-leaf for eco/nature, fa-spa for beauty/wellness)

  STYLE C — Two initials monogram (best for multi-word brands like "Harrison & Cole"):
    <span class="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center text-white font-bold text-xs tracking-wider shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">HC</span>

  STYLE D — Inline SVG logo mark (best for tech/modern brands):
    <svg class="w-9 h-9 flex-shrink-0" viewBox="0 0 36 36" fill="none">
      <rect width="36" height="36" rx="8" fill="url(#logo-grad)"/>
      <path d="M10 18L16 12L22 18L16 24Z" fill="white" opacity="0.9"/>
      <path d="M14 18L20 12L26 18L20 24Z" fill="white" opacity="0.6"/>
      <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="36" y2="36"><stop stop-color="var(--primary)"/><stop offset="1" stop-color="var(--secondary)"/></linearGradient></defs>
    </svg>
    (Create a UNIQUE simple geometric SVG for each brand — use abstract shapes: overlapping diamonds, stacked lines, circular arcs, interlocking shapes. Make it relate to the industry. NEVER reuse the same SVG path.)

  Pick the style that best matches the brand personality. Vary across generations — do NOT always use the same style.

TYPED.JS HERO EFFECT (optional — use on ~50% of generations for variety):
  For any hero pattern, you can add a typewriter effect on the headline. Replace the static headline text with:
    <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-[var(--text)]">
      <span class="typed-text" data-typed='["First Phrase Here", "Second Phrase Here", "Third Phrase Here"]'></span>
    </h1>
  The JS stage will auto-detect .typed-text elements and initialize Typed.js on them.
  Use 2-3 short phrases that highlight different value props. Example for a law firm:
    data-typed='["Trusted Legal Advocacy", "Decades of Courtroom Experience", "Results That Matter"]'
  Do NOT use on every generation — only when it fits the brand (tech, SaaS, agencies). Skip for minimal/elegant designs.

hero_split pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="py-16 md:py-20 relative"> (hero_split keeps normal padding since it has no bg image)
  <div class="max-w-[1400px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
    <div>
      <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-[var(--text)]">Headline</h1>
      <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-6 max-w-xl">Subheadline</p>
      <div class="flex flex-wrap gap-4 mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-[var(--text-muted)]">Trust line</p>
    </div>
    <div class="overflow-hidden rounded-xl">
      <img src="{{IMG:hero image query from plan}}" alt="Hero" class="w-full h-auto max-h-[420px] rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]">
    </div>
  </div>
  NOTE: ALL text must stay in the first column. Image in second column. On mobile: single column, image first (use md:order-none order-first on image div).

hero_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="relative -mt-[80px]"> (edge-to-edge, no gap)
  If plan has image_query for hero, use background image variant:
  <div class="relative min-h-[80vh] bg-cover bg-center bg-no-repeat flex items-center pt-[80px]" style="background-image: url('{{IMG:hero image query from plan}}');">
    <div class="absolute inset-0 bg-black/60"></div>
    <div class="relative max-w-[1400px] mx-auto px-6 text-center">
      <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-white">Headline</h1>
      <p class="text-base md:text-lg text-white/85 leading-relaxed mb-6 max-w-xl mx-auto">Subheadline</p>
      <div class="flex flex-wrap gap-4 justify-center mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-white/70">Trust line</p>
    </div>
  </div>
  If plan has NO image_query for hero (rare), use solid background variant:
  <div class="max-w-[1400px] mx-auto px-6 text-center py-20 md:py-28 pt-[100px]">
    <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-[var(--text)]">Headline</h1>
    <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-6 max-w-xl mx-auto">Subheadline</p>
    <div class="flex flex-wrap gap-4 justify-center mb-6">
      <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
      <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
    </div>
    <p class="text-sm text-[var(--text-muted)]">Trust line</p>
  </div>

hero_full_image pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="relative -mt-[80px]"> (negative margin pulls hero behind navbar — NO gap)
  <div class="relative min-h-[80vh] bg-cover bg-center bg-no-repeat flex items-center pt-[80px]" style="background-image: url('{{IMG:background hero scene query from plan}}');">
    <div class="absolute inset-0 bg-black/70 flex items-center">
      <div class="max-w-[1200px] mx-auto px-6 text-center">
        <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-white">Headline</h1>
        <p class="text-base md:text-lg text-white/85 leading-relaxed mb-6 max-w-xl mx-auto">Subheadline</p>
        <div class="flex flex-wrap gap-4 justify-center mb-6">
          <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
          <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
        </div>
        <p class="text-sm text-white/70">Trust line</p>
      </div>
    </div>
  </div>
  NOTE: Overlay MUST be bg-black/70 minimum — text must be readable over any image. The -mt-[80px] on the section and pt-[80px] on the inner div ensure hero extends behind the fixed navbar with no gap.

hero_minimal pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="py-16 md:py-24">
  <div class="max-w-[800px] mx-auto px-6 text-center py-20 md:py-28">
    <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-4 text-[var(--text)]">Big Bold Headline</h1>
    <p class="text-lg md:text-xl text-[var(--text-muted)] leading-relaxed mb-8 max-w-lg mx-auto">One concise line of supporting text</p>
    <div class="flex justify-center">
      <a href="#" class="BTN_PRIMARY_CLASSES">Single CTA</a>
    </div>
  </div>

hero_video_bg pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="relative -mt-[80px]"> (edge-to-edge hero, no gap)
  <div class="min-h-[80vh] flex items-center relative pt-[80px]" style="background: linear-gradient(-45deg, var(--primary), var(--secondary), var(--accent, var(--primary)), var(--primary)); background-size: 400% 400%; animation: gradientShift 8s ease infinite;">
    <div class="max-w-[1200px] mx-auto px-6 text-center">
      <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-white">Headline</h1>
      <p class="text-base md:text-lg text-white/85 leading-relaxed mb-6 max-w-xl mx-auto">Subheadline</p>
      <div class="flex flex-wrap gap-4 justify-center mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-white/70">Trust line</p>
    </div>
  </div>

hero_product_mockup pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="pt-8 md:pt-16 pb-16 md:pb-20 relative">
  <div class="max-w-[900px] mx-auto px-6 text-center">
    <h1 class="text-2xl md:text-3xl lg:text-4xl font-bold leading-tight mb-4 text-[var(--text)]">Headline (keep SHORT — max 8 words)</h1>
    <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-6 max-w-xl mx-auto">Subheadline</p>
    <div class="flex flex-wrap gap-4 justify-center mb-6">
      <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
      <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
    </div>
    <p class="text-sm text-[var(--text-muted)] mb-8">Trust line</p>
  </div>
  <div class="max-w-[1000px] mx-auto px-6 mt-4">
    <img src="{{IMG:mockup laptop dashboard product interface}}" alt="Product screenshot" class="mx-auto w-full h-auto rounded-xl object-cover shadow-2xl transition-transform duration-300 hover:scale-[1.02]">
  </div>
  NOTE: Text constrained to max-w-[900px], image wider at max-w-[1000px]. Headline MUST be short (max 8 words).

hero_mockup_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="pt-8 md:pt-16 pb-16 md:pb-20 relative">
  <div class="max-w-[900px] mx-auto px-6 text-center">
    <h1 class="text-2xl md:text-3xl lg:text-4xl font-bold leading-tight mb-4 text-[var(--text)]">Headline (keep SHORT — max 8 words)</h1>
    <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-6 max-w-xl mx-auto">Subheadline</p>
    <div class="flex flex-wrap gap-4 justify-center mb-6">
      <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
      <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
    </div>
    <p class="text-sm text-[var(--text-muted)] mb-8">Trust line</p>
  </div>
  <div class="max-w-[800px] mx-auto px-6 rounded-xl overflow-hidden shadow-2xl border border-black/10">
    <div class="flex gap-1.5 px-4 py-3 bg-black/[0.04]">
      <span class="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"></span>
      <span class="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></span>
      <span class="w-2.5 h-2.5 rounded-full bg-[#28c940]"></span>
    </div>
    <img src="{{IMG:mockup laptop dashboard product interface}}" alt="Product interface" class="w-full block h-auto">
  </div>
  NOTE: Browser frame with colored dots. For dark themes use bg-white/[0.06] on the dots bar and border-white/[0.08] on frame.

hero_asymmetric pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="py-16 md:py-24">
  <div class="max-w-[1400px] mx-auto px-6 grid grid-cols-1 md:grid-cols-[55%_45%] gap-12 items-center">
    <div>
      <h1 class="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4 text-[var(--text)]">Headline</h1>
      <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-6 max-w-xl">Subheadline</p>
      <div class="flex flex-wrap gap-4 mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-[var(--text-muted)]">Trust line</p>
    </div>
    <div class="relative">
      <img src="{{IMG:hero image query from plan}}" alt="Hero visual" class="w-full rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]">
      <div class="absolute -bottom-5 -left-5 bg-[var(--bg-surface)] rounded-[var(--radius)] py-5 px-6 shadow-xl flex items-center gap-3 backdrop-blur-[10px] border border-white/10 z-10 hidden md:flex">
        <i class="fa-solid fa-chart-line text-2xl text-[var(--primary)]"></i>
        <span class="font-semibold text-sm">Key metric or highlight</span>
      </div>
    </div>
  </div>
  NOTE: Floating card is hidden on mobile (hidden md:flex). Text 55%, image 45%.

card_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06]" data-aos="fade-up" data-aos-delay="100">
      <div class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--primary)] mb-5" style="background: color-mix(in srgb, var(--primary) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="text-lg font-bold mb-2 text-[var(--text)]">Title</h3>
      <p class="text-[var(--text-muted)] leading-relaxed text-sm">Description</p>
    </div>
  </div>
  NOTE: Light themes use border-gray-100 instead of border-white/[0.06].

icon_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 text-center">
    <div class="p-6" data-aos="fade-up" data-aos-delay="100">
      <div class="w-12 h-12 mx-auto mb-4 rounded-full flex items-center justify-center text-lg text-[var(--primary)]" style="background: color-mix(in srgb, var(--primary) 10%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h4 class="font-bold mb-1 text-[var(--text)]">Title</h4>
      <p class="text-sm text-[var(--text-muted)]">Short description</p>
    </div>
  </div>

feature_split pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 space-y-12">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center" data-aos="fade-up">
      <div><h3 class="text-xl font-bold mb-3 text-[var(--text)]">Title</h3><p class="text-[var(--text-muted)] leading-relaxed">Description</p></div>
      <div class="overflow-hidden rounded-xl"><img src="{{IMG:feature specific query from plan}}" alt="Feature name" class="w-full h-auto rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]"></div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center" data-aos="fade-up">
      <div class="md:order-2"><h3 class="text-xl font-bold mb-3 text-[var(--text)]">Title</h3><p class="text-[var(--text-muted)] leading-relaxed">Description</p></div>
      <div class="overflow-hidden rounded-xl md:order-1"><img src="{{IMG:feature different query}}" alt="Feature name" class="w-full h-auto rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]"></div>
    </div>
  </div>
  NOTE: Alternate rows. Second row uses md:order to flip text/image.

feature_cards pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] overflow-hidden shadow-md hover:-translate-y-1.5 hover:shadow-xl transition-all duration-300 border border-white/[0.06]" data-aos="fade-up" data-aos-delay="100">
      <div class="overflow-hidden"><img src="{{IMG:feature image query from plan}}" alt="Feature name" class="w-full h-48 object-cover"></div>
      <div class="p-5">
        <h3 class="text-lg font-bold mb-2 text-[var(--text)]">Title</h3>
        <p class="text-sm text-[var(--text-muted)] leading-relaxed">Description</p>
      </div>
    </div>
  </div>
  NOTE: Each card MUST have a unique {{IMG:feature ...}} with the image_query from the plan.

feature_stacked pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[800px] mx-auto px-6 divide-y divide-white/10">
    <div class="flex flex-col md:flex-row gap-5 items-start py-8" data-aos="fade-up">
      <div class="w-14 h-14 min-w-[3.5rem] rounded-xl flex items-center justify-center text-xl text-[var(--primary)]" style="background: color-mix(in srgb, var(--primary) 10%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <div>
        <h3 class="text-lg font-bold mb-1 text-[var(--text)]">Title</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Long detailed description of this feature or service.</p>
      </div>
    </div>
  </div>
  NOTE: Light themes use divide-gray-100 instead of divide-white/10.

feature_steps pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="steps-container max-w-[700px] mx-auto px-6 relative">
    <div class="flex gap-6 items-start py-8 relative" data-aos="fade-up" data-aos-delay="100">
      <div class="w-14 h-14 min-w-[3.5rem] rounded-full flex items-center justify-center font-bold text-lg text-white z-10 shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">1</div>
      <div>
        <h3 class="text-lg font-bold mb-1 text-[var(--text)]">Step Title</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Description of this step.</p>
      </div>
    </div>
    <div class="flex gap-6 items-start py-8 relative" data-aos="fade-up" data-aos-delay="200">
      <div class="w-14 h-14 min-w-[3.5rem] rounded-full flex items-center justify-center font-bold text-lg text-white z-10 shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">2</div>
      <div>
        <h3 class="text-lg font-bold mb-1 text-[var(--text)]">Step Title</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Description of this step.</p>
      </div>
    </div>
    <div class="flex gap-6 items-start py-8 relative" data-aos="fade-up" data-aos-delay="300">
      <div class="w-14 h-14 min-w-[3.5rem] rounded-full flex items-center justify-center font-bold text-lg text-white z-10 shadow-lg" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">3</div>
      <div>
        <h3 class="text-lg font-bold mb-1 text-[var(--text)]">Step Title</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Description of this step.</p>
      </div>
    </div>
  </div>
  NOTE: The connecting vertical line is handled by .steps-container in the <style> block. Use 3 or 4 steps.

pricing_table pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
    <div class="pricing-card bg-[var(--bg-surface)] rounded-[var(--radius)] p-8 text-center shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06] relative" data-aos="fade-up" data-aos-delay="100">
      <h3 class="text-xl font-bold mb-2 text-[var(--text)]">Plan</h3>
      <div class="my-4"><span class="text-4xl font-bold text-[var(--primary)]">$99</span><span class="text-sm font-normal text-[var(--text-muted)]">/mo</span></div>
      <ul class="text-left space-y-3 my-6 text-sm list-none p-0">
        <li class="flex items-center gap-2 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--primary)]"></i> Feature</li>
      </ul>
      <a href="#" class="block w-full BTN_PRIMARY_CLASSES text-center">Get Started</a>
    </div>
  </div>
  NOTE: The middle/recommended plan card should have class "pricing-card featured" to visually emphasize it (auto-scaled 105% + primary border via CSS).

testimonial_cards pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06]" data-aos="fade-up" data-aos-delay="100">
      <div class="text-amber-400 mb-3"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
      <p class="text-[var(--text-muted)] leading-relaxed italic mb-5">"Quote text"</p>
      <div class="flex items-center gap-3">
        <div><strong class="block text-[var(--text)]">Name</strong><span class="text-sm text-[var(--text-muted)]">Role, Company</span></div>
      </div>
    </div>
  </div>

testimonial_slider pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[700px] mx-auto px-6 text-center" data-aos="fade-up">
    <div class="testimonial-slide active">
      <div class="text-amber-400 mb-3"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
      <blockquote class="text-lg md:text-xl italic leading-relaxed text-[var(--text)] my-6">"Large featured quote text goes here."</blockquote>
      <div><strong class="block text-[var(--text)]">Name</strong><span class="text-sm text-[var(--text-muted)]">Role, Company</span></div>
    </div>
    <div class="testimonial-slide"><!-- additional slides hidden by default --></div>
    <div class="slider-dots flex justify-center gap-2 mt-8">
      <button class="slider-dot w-3 h-3 rounded-full border-2 border-[var(--primary)] bg-transparent cursor-pointer p-0 active" data-slide="0"></button>
      <button class="slider-dot w-3 h-3 rounded-full border-2 border-[var(--primary)] bg-transparent cursor-pointer p-0" data-slide="1"></button>
    </div>
  </div>
  NOTE: .testimonial-slide and .slider-dot.active styles are in the <style> block.

testimonial_split pattern:
  <div class="max-w-[1200px] mx-auto px-6">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-12 items-center" data-aos="fade-up">
      <div>
        <div class="text-amber-400 mb-3"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <blockquote class="text-lg md:text-xl italic leading-relaxed text-[var(--text)] my-6">"Large impactful quote text here."</blockquote>
        <div><strong class="block text-[var(--text)]">Name</strong><span class="text-sm text-[var(--text-muted)]">Role, Company</span></div>
      </div>
      <div class="overflow-hidden rounded-xl">
        <img src="{{IMG:testimonial professional portrait business person}}" alt="Author name" class="w-full max-h-[400px] rounded-xl object-cover">
      </div>
    </div>
  </div>

faq_accordion pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[800px] mx-auto px-6">
    <div class="faq-item border-b border-white/10" data-aos="fade-up">
      <button class="faq-question w-full bg-transparent border-none py-5 flex justify-between items-center text-base md:text-lg font-semibold cursor-pointer text-left text-[var(--text)]"><span>Question?</span><i class="fa-solid fa-chevron-down text-sm text-[var(--text-muted)] transition-transform duration-300"></i></button>
      <div class="faq-answer"><p class="text-[var(--text-muted)] leading-relaxed pb-4">Answer text</p></div>
    </div>
  </div>
  NOTE: Light themes use border-gray-200 instead of border-white/10. FAQ toggle handled by JS + <style> block.

stats_row pattern:
  <div class="max-w-[900px] mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
    <div class="flex flex-col items-center gap-2" data-aos="fade-up" data-aos-delay="100">
      <i class="fa-solid fa-building text-2xl text-[var(--primary)] opacity-80"></i>
      <div class="stat-number text-3xl md:text-4xl font-bold text-[var(--primary)] leading-none whitespace-nowrap">500+</div>
      <div class="text-xs uppercase tracking-widest text-[var(--text-muted)] max-w-[200px]">Projects Completed</div>
    </div>
    <div class="flex flex-col items-center gap-2" data-aos="fade-up" data-aos-delay="200">
      <i class="fa-solid fa-leaf text-2xl text-[var(--primary)] opacity-80"></i>
      <div class="stat-number text-3xl md:text-4xl font-bold text-[var(--primary)] leading-none whitespace-nowrap">45%</div>
      <div class="text-xs uppercase tracking-widest text-[var(--text-muted)] max-w-[200px]">Average Energy Reduction</div>
    </div>
  </div>
  STATS RULES:
  - Each stat: optional icon → .stat-number → label
  - Number AND suffix (+, %, M, K, M+) MUST be in the SAME .stat-number element
  - CORRECT: <div class="stat-number ...">120+</div>
  - WRONG: <span>120</span><span>+</span> (NEVER split number and suffix)
  - Do NOT use data-target attributes. JS handles counter animation automatically via IntersectionObserver.

cta_banner pattern:
  <div class="max-w-[1200px] mx-auto px-6 text-center" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: var(--radius); padding: 3rem 2rem;">
    <h2 class="text-2xl md:text-3xl font-bold mb-3 text-white">Headline</h2>
    <p class="text-base text-white/80 mb-6 max-w-lg mx-auto">Description</p>
    <div class="flex flex-wrap gap-4 justify-center">
      <a href="#" class="inline-block bg-white text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg">Primary CTA</a>
      <a href="#" class="inline-block border-2 border-white text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:bg-white hover:text-[var(--primary)] bg-transparent">Secondary CTA</a>
    </div>
  </div>

cta_split pattern:
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
    <div>
      <h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2>
      <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-6">Description</p>
      <div class="flex flex-wrap gap-4">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
    </div>
    <div class="overflow-hidden rounded-xl">
      <img src="{{IMG:cta image query from plan}}" alt="Call to action" class="w-full h-auto rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]">
    </div>
  </div>

cta_gradient pattern:
  <div class="text-center py-16 md:py-20 relative" style="background: linear-gradient(135deg, var(--primary), var(--secondary));">
    <div class="max-w-[800px] mx-auto px-6">
      <h2 class="text-2xl md:text-3xl font-bold mb-3 text-white">Headline</h2>
      <p class="text-base text-white/80 mb-6 max-w-lg mx-auto">Description</p>
      <a href="#" class="inline-block bg-white text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)]">Primary CTA</a>
    </div>
  </div>

cta_centered pattern:
  <div class="max-w-[800px] mx-auto px-6 text-center">
    <h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2>
    <p class="text-base md:text-lg text-[var(--text-muted)] max-w-lg mx-auto leading-relaxed mb-6">Description</p>
    <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
  </div>
  NOTE: Simple, clean centered CTA. No gradient background.

team_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] overflow-hidden shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06] text-center" data-aos="fade-up" data-aos-delay="100">
      <img src="{{IMG:team professional man portrait studio}}" alt="Name" class="w-full h-64 object-cover">
      <div class="p-5">
        <h3 class="text-lg font-bold text-[var(--text)]">Name</h3>
        <p class="text-sm text-[var(--text-muted)]">Role</p>
      </div>
    </div>
  </div>

team_cards pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] overflow-hidden shadow-md hover:-translate-y-1.5 hover:shadow-xl transition-all duration-300 border border-white/[0.06]" data-aos="fade-up" data-aos-delay="100">
      <img src="{{IMG:team professional woman portrait studio}}" alt="Name" class="w-full h-72 object-cover">
      <div class="p-5">
        <h3 class="text-lg font-bold text-[var(--text)]">Name</h3>
        <p class="text-sm text-[var(--text-muted)]">Role</p>
        <p class="text-sm text-[var(--text-muted)] mt-2">Short bio about this team member and their expertise.</p>
      </div>
    </div>
  </div>

team_masonry pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 columns-1 md:columns-2 lg:columns-3 gap-6">
    <div class="break-inside-avoid mb-6 relative rounded-[var(--radius)] overflow-hidden group" data-aos="fade-up" data-aos-delay="100">
      <img src="{{IMG:team professional man portrait studio}}" alt="Name" class="w-full block">
      <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent text-white p-6 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
        <h3 class="font-bold">Name</h3>
        <p class="text-sm text-white/80">Role</p>
      </div>
    </div>
  </div>

contact_split pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12">
    <div class="space-y-6">
      <div class="flex gap-4 items-start"><i class="fa-solid fa-location-dot text-lg text-[var(--primary)] w-5 mt-1"></i><p class="text-[var(--text-muted)]">Address</p></div>
      <div class="flex gap-4 items-start"><i class="fa-solid fa-phone text-lg text-[var(--primary)] w-5 mt-1"></i><p class="text-[var(--text-muted)]">Phone</p></div>
      <div class="flex gap-4 items-start"><i class="fa-solid fa-envelope text-lg text-[var(--primary)] w-5 mt-1"></i><p class="text-[var(--text-muted)]">Email</p></div>
    </div>
    <form class="space-y-4">
      <input type="text" placeholder="Your Name" required class="w-full p-4 rounded-lg border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10">
      <input type="email" placeholder="Your Email" required class="w-full p-4 rounded-lg border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10">
      <textarea placeholder="Your Message" rows="5" required class="w-full p-4 rounded-lg border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10 resize-y"></textarea>
      <button type="submit" class="BTN_PRIMARY_CLASSES">Send Message</button>
    </form>
  </div>
  NOTE: Light themes use border-gray-200 instead of border-white/10.

footer_columns pattern:
  CRITICAL: Footer MUST have ALL 4 columns. Do NOT skip any column. Do NOT output a minimal footer.
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
    <!-- COLUMN 1: Brand + description + social icons -->
    <div class="mb-6">
      <a href="#" class="flex items-center gap-2.5 no-underline text-white font-bold text-lg mb-4">
        SAME_LOGO_MARK_AS_NAVBAR (use the exact same logo mark from the navbar — keep it consistent)
        <span class="font-bold text-lg tracking-tight">Brand</span>
      </a>
      <p class="text-sm text-white/60 leading-relaxed max-w-[280px]">Short brand description from the plan.</p>
      <div class="flex gap-3 mt-4">
        <a href="#" class="w-10 h-10 rounded-full bg-white/[0.08] flex items-center justify-center text-white border border-white/10 hover:bg-[var(--primary)] hover:border-[var(--primary)] hover:-translate-y-0.5 transition-all duration-300"><i class="fa-brands fa-linkedin"></i></a>
        <a href="#" class="w-10 h-10 rounded-full bg-white/[0.08] flex items-center justify-center text-white border border-white/10 hover:bg-[var(--primary)] hover:border-[var(--primary)] hover:-translate-y-0.5 transition-all duration-300"><i class="fa-brands fa-twitter"></i></a>
        <a href="#" class="w-10 h-10 rounded-full bg-white/[0.08] flex items-center justify-center text-white border border-white/10 hover:bg-[var(--primary)] hover:border-[var(--primary)] hover:-translate-y-0.5 transition-all duration-300"><i class="fa-brands fa-instagram"></i></a>
      </div>
    </div>
    <!-- COLUMN 2: Quick Links — anchor links to page sections -->
    <div>
      <h4 class="font-bold text-white mb-4">Quick Links</h4>
      <ul class="list-none p-0 space-y-2">
        <li><a href="#services" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Services</a></li>
        <li><a href="#about" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">About Us</a></li>
        <li><a href="#testimonials" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Testimonials</a></li>
        <li><a href="#faq" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">FAQ</a></li>
      </ul>
    </div>
    <!-- COLUMN 3: Services — list 4-5 actual services from the plan -->
    <div>
      <h4 class="font-bold text-white mb-4">Services</h4>
      <ul class="list-none p-0 space-y-2">
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 1</a></li>
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 2</a></li>
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 3</a></li>
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 4</a></li>
      </ul>
    </div>
    <!-- COLUMN 4: Contact info with icons -->
    <div>
      <h4 class="font-bold text-white mb-4">Contact</h4>
      <ul class="list-none p-0 space-y-3">
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-location-dot text-[var(--accent)] mt-1 w-4"></i><span>Office address, City, UAE</span></li>
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-phone text-[var(--accent)] mt-1 w-4"></i><span>+971 XX XXX XXXX</span></li>
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-envelope text-[var(--accent)] mt-1 w-4"></i><span>info@brand.ae</span></li>
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-clock text-[var(--accent)] mt-1 w-4"></i><span>Sun-Thu: 9AM-6PM</span></li>
      </ul>
    </div>
  </div>
  <div class="max-w-[1200px] mx-auto px-6 border-t border-white/[0.08] mt-10 pt-6 text-center text-sm text-white/50">
    <p>&copy; <span id="year"></span> Brand. All rights reserved.</p>
  </div>
  FOOTER RULES (CRITICAL): Footer MUST have EXACTLY 4 columns. Quick Links use anchor hrefs matching page sections. Services column lists real services from the plan. Contact has address+phone+email+hours with icons. NEVER output a minimal footer. Footer always uses dark background (style="background: #1a1a2e").

logo_cloud pattern:
  <div class="text-center mb-6"><h2 class="text-lg md:text-xl font-semibold text-[var(--text-muted)]">Headline</h2></div>
  <div class="max-w-[1200px] mx-auto px-6 flex flex-wrap justify-center items-center gap-6">
    <div class="px-4 py-3" data-aos="fade-up" data-aos-delay="100">
      <span class="text-base font-bold tracking-wide opacity-40 hover:opacity-80 transition-all duration-300 whitespace-nowrap text-[var(--text)]">Company 1</span>
    </div>
    <div class="px-4 py-3" data-aos="fade-up" data-aos-delay="200">
      <span class="text-base font-bold tracking-wide opacity-40 hover:opacity-80 transition-all duration-300 whitespace-nowrap text-[var(--text)]">Company 2</span>
    </div>
  </div>
  NOTE: Text-only logos. Do NOT use <img> tags, dummyimage.com, or any image URLs for logos.

gallery_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div class="gallery-item overflow-hidden rounded-[var(--radius)] cursor-pointer group" data-aos="fade-up" data-aos-delay="100">
      <img src="{{IMG:gallery specific image query}}" alt="Gallery item title" class="w-full h-64 object-cover transition-transform duration-500 group-hover:scale-110">
    </div>
  </div>
  <!-- Lightbox modal (single, reused for all images) -->
  <div id="gallery-lightbox" class="fixed inset-0 z-[9999] bg-black/90 hidden items-center justify-center p-4">
    <button class="lightbox-close absolute top-6 right-6 text-white text-3xl bg-transparent border-none cursor-pointer hover:text-[var(--primary)] transition-colors z-10">&times;</button>
    <button class="lightbox-prev absolute left-4 top-1/2 -translate-y-1/2 text-white text-4xl bg-black/30 hover:bg-black/60 border-none cursor-pointer rounded-full w-12 h-12 flex items-center justify-center transition-all"><i class="fa-solid fa-chevron-left"></i></button>
    <button class="lightbox-next absolute right-4 top-1/2 -translate-y-1/2 text-white text-4xl bg-black/30 hover:bg-black/60 border-none cursor-pointer rounded-full w-12 h-12 flex items-center justify-center transition-all"><i class="fa-solid fa-chevron-right"></i></button>
    <img class="lightbox-img max-w-[90vw] max-h-[85vh] object-contain rounded-lg" src="" alt="">
  </div>
  NOTE: Each gallery item MUST have a unique {{IMG:gallery ...}} query. JS handles lightbox open/close/navigation.

image_carousel pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="carousel-container max-w-[1200px] mx-auto px-6 relative overflow-hidden rounded-[var(--radius)]" data-aos="fade-up">
    <div class="carousel-track flex transition-transform duration-500 ease-in-out">
      <div class="carousel-slide min-w-full relative">
        <img src="{{IMG:carousel specific image query}}" alt="Slide title" class="w-full h-[400px] md:h-[500px] object-cover">
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-8">
          <h3 class="text-xl md:text-2xl font-bold text-white mb-2">Slide Title</h3>
          <p class="text-white/80 text-sm md:text-base max-w-lg">Slide description text</p>
        </div>
      </div>
      <!-- Repeat for each slide (3-5 slides) -->
    </div>
    <button class="carousel-prev absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm border-none text-white cursor-pointer flex items-center justify-center hover:bg-white/40 transition-all z-10"><i class="fa-solid fa-chevron-left"></i></button>
    <button class="carousel-next absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm border-none text-white cursor-pointer flex items-center justify-center hover:bg-white/40 transition-all z-10"><i class="fa-solid fa-chevron-right"></i></button>
    <div class="carousel-dots flex justify-center gap-2 mt-6">
      <button class="carousel-dot w-3 h-3 rounded-full border-2 border-[var(--primary)] bg-transparent cursor-pointer p-0 transition-all active" data-slide="0"></button>
      <!-- One dot per slide -->
    </div>
  </div>
  CAROUSEL RULES (CRITICAL — carousel MUST work):
  - Each slide MUST have a unique {{IMG:carousel ...}} query
  - Generate 3-5 .carousel-slide elements inside .carousel-track
  - Generate matching .carousel-dot buttons (one per slide) with data-slide="0", data-slide="1", etc.
  - The .carousel-prev and .carousel-next buttons MUST exist with those exact classes
  - First dot MUST have class "active" initially
  - JS will translate .carousel-track by -100% per slide index
  - Do NOT add any inline onclick handlers — JS handles all navigation

service_modal pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="modal-trigger bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06] cursor-pointer group" data-modal="modal-1" data-aos="fade-up" data-aos-delay="100">
      <div class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--primary)] mb-5 group-hover:scale-110 transition-transform" style="background: color-mix(in srgb, var(--primary) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="text-lg font-bold mb-2 text-[var(--text)]">Service Title</h3>
      <p class="text-[var(--text-muted)] leading-relaxed text-sm mb-3">Short description visible on the card.</p>
      <span class="text-[var(--primary)] text-sm font-semibold inline-flex items-center gap-1">Learn More <i class="fa-solid fa-arrow-right text-xs"></i></span>
    </div>
  </div>
  <!-- Modals (one per card, hidden by default) -->
  <div id="modal-1" class="detail-modal fixed inset-0 z-[9999] bg-black/60 hidden items-center justify-center p-4">
    <div class="bg-[var(--bg)] rounded-[var(--radius)] max-w-lg w-full p-8 relative shadow-2xl max-h-[90vh] overflow-y-auto">
      <button class="modal-close absolute top-4 right-4 text-[var(--text-muted)] hover:text-[var(--text)] text-xl bg-transparent border-none cursor-pointer">&times;</button>
      <div class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--primary)] mb-5" style="background: color-mix(in srgb, var(--primary) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="text-xl font-bold mb-3 text-[var(--text)]">Service Title</h3>
      <p class="text-[var(--text-muted)] leading-relaxed">Expanded detailed description of this service. Include specifics, benefits, process details, what the client gets, etc. This is the full content revealed when user clicks the card.</p>
    </div>
  </div>
  NOTE: Each card has data-modal="modal-N" pointing to matching modal ID. Use modal-1, modal-2, modal-3, etc. Light themes use border-gray-100. JS handles open/close.

timeline pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="timeline-container max-w-[800px] mx-auto px-6 relative">
    <div class="flex gap-6 items-start py-8 relative" data-aos="fade-up" data-aos-delay="100">
      <div class="min-w-[80px] text-right">
        <span class="text-sm font-bold text-[var(--primary)]">2020</span>
      </div>
      <div class="w-4 h-4 min-w-[1rem] rounded-full bg-[var(--primary)] mt-1 z-10 shadow-lg ring-4 ring-[var(--bg)]"></div>
      <div class="flex-1 bg-[var(--bg-surface)] rounded-[var(--radius)] p-5 shadow-md border border-white/[0.06]">
        <h3 class="text-lg font-bold mb-1 text-[var(--text)]">Milestone Title</h3>
        <p class="text-sm text-[var(--text-muted)] leading-relaxed">Description of what happened at this milestone.</p>
      </div>
    </div>
    <!-- Repeat 4-6 milestones -->
  </div>
  NOTE: The connecting vertical line is handled by .timeline-container::before in the <style> block. Light themes use border-gray-100. Dates can be years, months, or descriptive phases.

newsletter_cta pattern:
  <div class="max-w-[600px] mx-auto px-6 text-center">
    <h2 class="text-2xl md:text-3xl font-bold mb-3 text-[var(--text)]">Headline</h2>
    <p class="text-base text-[var(--text-muted)] mb-6 max-w-md mx-auto leading-relaxed">Short pitch about why they should subscribe.</p>
    <form class="newsletter-form flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
      <input type="email" placeholder="Enter your email" required class="flex-1 p-3.5 rounded-[var(--radius-btn)] border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10">
      <button type="submit" class="inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3.5 px-7 rounded-[var(--radius-btn)] font-semibold border-none cursor-pointer transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg whitespace-nowrap">Subscribe</button>
    </form>
    <p class="text-xs text-[var(--text-muted)] mt-3 opacity-70">No spam. Unsubscribe anytime.</p>
  </div>
  NOTE: Light themes use border-gray-200 on input. JS handles form submit with inline success message (not alert).

comparison_table pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[800px] mx-auto px-6 overflow-x-auto" data-aos="fade-up">
    <table class="w-full border-collapse text-left">
      <thead>
        <tr>
          <th class="py-4 px-4 text-sm font-semibold text-[var(--text-muted)] border-b border-white/10">Feature</th>
          <th class="py-4 px-4 text-sm font-bold text-[var(--primary)] border-b border-white/10 text-center">Our Product</th>
          <th class="py-4 px-4 text-sm font-semibold text-[var(--text-muted)] border-b border-white/10 text-center">Competitor</th>
        </tr>
      </thead>
      <tbody>
        <tr class="border-b border-white/[0.06] hover:bg-white/[0.02] transition-colors">
          <td class="py-3.5 px-4 text-sm text-[var(--text)]">Feature name</td>
          <td class="py-3.5 px-4 text-center"><i class="fa-solid fa-check text-emerald-500"></i></td>
          <td class="py-3.5 px-4 text-center"><i class="fa-solid fa-xmark text-red-400 opacity-50"></i></td>
        </tr>
        <!-- Repeat 5-8 feature rows -->
      </tbody>
    </table>
  </div>
  NOTE: Use fa-check (green) for included features, fa-xmark (red/dim) for missing. Some cells can have text instead of icons (e.g., "Unlimited" vs "100/mo"). Light themes use border-gray-200.

logo_carousel pattern:
  <div class="text-center mb-6"><h2 class="text-lg md:text-xl font-semibold text-[var(--text-muted)]">Headline</h2></div>
  <div class="logo-carousel-container overflow-hidden relative max-w-[1200px] mx-auto">
    <div class="logo-carousel-track flex gap-12 items-center whitespace-nowrap">
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 1</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 2</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 3</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 4</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 5</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 6</span>
      <!-- JS duplicates these for infinite scroll effect -->
    </div>
  </div>
  NOTE: Text-only logos, NO images. JS handles infinite scroll animation by duplicating the track content and using CSS animation. The carousel auto-scrolls continuously.

trust_badges pattern:
  <div class="max-w-[1000px] mx-auto px-6 flex flex-wrap justify-center items-center gap-8 md:gap-12">
    <div class="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity" data-aos="fade-up" data-aos-delay="100">
      <i class="fa-solid fa-shield-halved text-2xl text-[var(--primary)]"></i>
      <div><span class="text-sm font-bold text-[var(--text)] block">SSL Secured</span><span class="text-xs text-[var(--text-muted)]">256-bit encryption</span></div>
    </div>
    <div class="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity" data-aos="fade-up" data-aos-delay="200">
      <i class="fa-solid fa-certificate text-2xl text-[var(--primary)]"></i>
      <div><span class="text-sm font-bold text-[var(--text)] block">ISO 27001</span><span class="text-xs text-[var(--text-muted)]">Certified</span></div>
    </div>
  </div>
  NOTE: 3-5 badges. Pick industry-relevant certifications: GDPR, HIPAA, SOC2, ISO, PCI-DSS, DED Licensed, TDRA Approved, etc. Compact section — use py-10 md:py-12.

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
  For hero_full_image / hero_video_bg: add class "-mt-[80px]" on the section to pull it UP behind the fixed navbar (edge-to-edge hero with no gap).
  Logo cloud sections: use py-10 md:py-12 (compact).
  Footer: use py-14 md:py-16 and a dark background.

STYLE BLOCK ADDITIONS — add these to the <style> block:
  .steps-container::before {{ content: ""; position: absolute; left: 28px; top: 0; bottom: 0; width: 2px; background: linear-gradient(180deg, var(--primary), var(--secondary)); }}
  .timeline-container::before {{ content: ""; position: absolute; left: 118px; top: 0; bottom: 0; width: 2px; background: linear-gradient(180deg, var(--primary), var(--secondary)); }}
  .slider-dot.active {{ background: var(--primary); }}
  .carousel-dot.active {{ background: var(--primary); }}
  #gallery-lightbox.active {{ display: flex; }}
  .detail-modal.active {{ display: flex; }}
  .typed-cursor {{ color: var(--primary); font-weight: 100; }}
  @keyframes logoScroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
  .logo-carousel-track {{ animation: logoScroll 20s linear infinite; }}
  .logo-carousel-container::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 60px; background: linear-gradient(90deg, var(--bg), transparent); z-index: 2; pointer-events: none; }}
  .logo-carousel-container::after {{ content: ""; position: absolute; right: 0; top: 0; bottom: 0; width: 60px; background: linear-gradient(-90deg, var(--bg), transparent); z-index: 2; pointer-events: none; }}
  .search-dropdown.active {{ display: block; }}
  #back-to-top.visible {{ opacity: 1; pointer-events: auto; }}
  .whatsapp-float {{ animation: floatOrb 3s ease-in-out infinite; animation-duration: 3s; }}
  [data-splitting] .char {{ display: inline-block; opacity: 0; transform: translateY(20px); transition: opacity 0.4s ease, transform 0.4s ease; }}
  [data-splitting].visible .char {{ opacity: 1; transform: translateY(0); }}
  @media (max-width: 768px) {{ .steps-container::before {{ left: 24px; }} .timeline-container::before {{ left: 98px; }} }}

ADDITIONAL HTML RULES:
- Each {{IMG:...}} placeholder MUST have a DIFFERENT query. Never reuse.
- Footer copyright: use &copy; <span id="year"></span> Brand Name — JS sets current year.
- Do NOT hardcode a year like &copy; 2024.
- REMINDER: ALL images must use {{IMG:role query}} placeholders. Real URLs (pexels.com, unsplash.com) will 404.
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

VANILLA-TILT.JS — add data-tilt attribute on interactive cards for 3D hover effect:
  On card_grid cards, pricing_table cards, and team_cards: add data-tilt data-tilt-max="8" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.15"
  Example: <div class="card-classes..." data-tilt data-tilt-max="8" data-tilt-speed="400" data-tilt-glare data-tilt-max-glare="0.15">
  Do NOT add data-tilt to every element — only 3-column grid cards. Skip on mobile (JS handles this).

TSPARTICLES — for hero_video_bg or hero_center on dark themes, add a particles container:
  <div id="tsparticles" class="absolute inset-0 z-0"></div>
  Place INSIDE the hero section, before the text content. The text content must have class="relative z-10" to stay above particles.
  JS initializes tsParticles with a subtle network/dots config. Only use on ~30% of generations (dark tech/SaaS themes).

SPLITTING.JS — for key headlines, add data-splitting attribute:
  <h2 data-splitting class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2>
  Only on 1-2 section headlines per page. JS calls Splitting() on elements with [data-splitting]. Creates letter-by-letter reveal with CSS.
  Do NOT use on every headline — pick the most impactful one (usually the first feature section headline).

LENIS SMOOTH SCROLL — JS initializes Lenis for buttery smooth page scrolling. No HTML changes needed — JS handles everything.

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
  Replace PRIMARY_COLOR with the actual hex color (e.g., %23F97316 — URL-encoded #). Replace FIRST_LETTER with the brand's first letter.

BREADCRUMBS — Do NOT add visible breadcrumbs to single-page websites. They add clutter with no navigation value on one-page sites."""


# ═══════════════════════════════════════════════════════════════════════
# STAGE 3: REMOVED — CSS is now inline Tailwind in HTML
# ═══════════════════════════════════════════════════════════════════════

CSS_GEN_SYSTEM_PROMPT = """REMOVED: CSS is now generated inline as Tailwind utility classes in the HTML stage.

DESIGN SPEC:
{design_json}

SECTION LAYOUT PLAN (use this to understand intended layouts):
{sections_json}

FULL HTML TO STYLE:
{html_content}

DESIGN DIRECTION:
{design_seed}

RULES:
- Return ONLY CSS inside a single ```css code block
- Start with @import for Google Fonts from the design spec
- You MUST style EVERY section and EVERY element in the HTML — do NOT skip any
- Mobile-first responsive design with breakpoints (@media min-width: 768px, 1024px)
- Polished hover states on buttons, cards, and links
- Smooth transitions: transition: all 0.3s ease
- Use CSS Grid or Flexbox for all layouts
- Sticky navbar with backdrop-filter
- Do NOT include any AOS animation styles — AOS CSS is loaded separately via CDN
- Do NOT write any [data-aos] selectors
- NO JavaScript, NO HTML — only CSS
- Do NOT include any explanation, just the css code block

MANDATORY: Start CSS with this :root block (fill in values from the DESIGN SPEC above):

:root {{
  /* Colors */
  --primary: [primary_color from spec];
  --secondary: [secondary_color];
  --accent: [accent_color];
  --bg: [background_color];
  --bg-surface: [surface_color or slightly tinted bg];
  --bg-alt: [alternate section bg — slightly different from --bg];
  --text: [text_color];
  --text-muted: [text_muted or lighter text];
  --white: #ffffff;

  /* Typography */
  --font-heading: '[heading_font]', sans-serif;
  --font-body: '[body_font]', sans-serif;

  /* Spacing scale */
  --space-xs: 8px;
  --space-sm: 16px;
  --space-md: 32px;
  --space-lg: 48px;
  --space-xl: 80px;

  /* Section spacing (based on spacing value: compact/normal/spacious) */
  --section-padding: [48px for compact, 64px normal, 80px spacious];
  --card-padding: [1.5rem compact, 2rem normal, 2.5rem spacious];
  --gap: [1.5rem compact, 2rem normal, 2.5rem spacious];

  /* Shapes */
  --radius: [card_radius from spec];
  --radius-btn: [button_radius from spec];
  --shadow: 0 4px 24px rgba(0,0,0,0.08);
  --shadow-hover: 0 20px 60px rgba(0,0,0,0.18);
  --transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}}

Then use ONLY these CSS variables throughout. Never hardcode colors or spacing.

PREMIUM DESIGN PRINCIPLES (apply to EVERY generated site):
- Use background layered gradients for depth on dark themes:
  body {{ background: radial-gradient(circle at 20% 20%, rgba(var(--primary-rgb), 0.08), transparent 40%), radial-gradient(circle at 80% 70%, rgba(var(--secondary-rgb), 0.06), transparent 40%), var(--bg); }}
  (use actual hex → rgb values from the design spec, NOT the variable names with -rgb)
- Subtle section dividers: section::after {{ content: ""; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 80%; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent); }}
  (only for dark themes — skip for light themes)
- Images: border-radius 14px, transition transform 0.4s ease, img:hover transform scale(1.02)
- All interactive elements must have smooth transitions using var(--transition)
- Large typography hierarchy: h1 should feel dominant, h2 significantly smaller, h3 even smaller
- Generous whitespace between sections and elements

MANDATORY COMPONENT STYLES — implement ALL of these:

1. GLOBAL:
   .container {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
   .container-wide {{ max-width: 1400px; margin: 0 auto; padding: 0 1.5rem; }}
   .container-narrow {{ max-width: 800px; margin: 0 auto; padding: 0 1.5rem; }}
   .section-header {{ text-align: center; margin-bottom: var(--space-md); }}
   .section-header h2 {{ font-size: clamp(1.8rem, 3vw, 2.5rem); font-weight: 700; margin-bottom: 1rem; }}
   .section-header p {{ font-size: 1.1rem; color: var(--text-muted); max-width: 600px; margin: 0 auto; }}
   .btn-primary {{ background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 0.875rem 2rem; border-radius: var(--radius-btn); font-weight: 600; text-decoration: none; display: inline-block; transition: var(--transition); border: none; cursor: pointer; }}
   .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.25); }}
   .btn-secondary {{ border: 2px solid var(--primary); color: var(--primary); padding: 0.875rem 2rem; border-radius: var(--radius-btn); font-weight: 600; text-decoration: none; display: inline-block; transition: var(--transition); background: transparent; }}
   .btn-secondary:hover {{ background: var(--primary); color: white; transform: translateY(-2px); }}

2. CARD GRID: .card-grid
   - display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem;
   - @media max-width 1024px: grid-template-columns: repeat(2, 1fr)
   - @media max-width 640px: grid-template-columns: 1fr
   - .card: background var(--bg-surface), border-radius var(--radius), padding var(--card-padding), box-shadow var(--shadow), transition var(--transition), border 1px solid rgba(255,255,255,0.06)
   - .card:hover: transform translateY(-8px), box-shadow var(--shadow-hover)
   - .card-icon: width 60px, height 60px, border-radius 12px, background linear-gradient(135deg, var(--primary), var(--secondary)) at 12% opacity, display flex, center icon, font-size 1.4rem, color var(--primary), margin-bottom 1.5rem

3. ICON GRID: .icon-grid
   - display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem;
   - @media max-width 1024px: grid-template-columns: repeat(2, 1fr)
   - @media max-width 640px: grid-template-columns: 1fr
   - .icon-item: text-align center, padding 1.5rem
   - .icon-box: width 50px, height 50px, margin 0 auto 1rem, border-radius 50%, background primary 10%, icon centered

4. FAQ ACCORDION: .faq-list, .faq-item, .faq-question, .faq-answer
   - .faq-list: max-width: 800px; margin: 0 auto;
   - .faq-item: border-bottom 1px solid #eee, overflow hidden
   - .faq-question: width 100%, background none, border none, padding 1.25rem 0, display flex, justify-content space-between, align-items center, font-size 1.1rem, font-weight 600, cursor pointer, text-align left
   - .faq-answer: max-height 0, overflow hidden, transition max-height 0.3s ease, padding 0
   - .faq-item.active .faq-answer: max-height 500px, padding-bottom 1.25rem
   - .faq-item.active .faq-question i: transform rotate(180deg)

5. PRICING: .pricing-grid
   - display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; align-items start
   - @media max-width 1024px: grid-template-columns: repeat(2, 1fr)
   - @media max-width 640px: grid-template-columns: 1fr
   - .pricing-card: background var(--bg-surface), border-radius var(--radius), padding 2.5rem, text-align center, box-shadow var(--shadow), position relative, transition var(--transition), border 1px solid rgba(255,255,255,0.06)
   - .pricing-card:hover: transform translateY(-8px), box-shadow var(--shadow-hover)
   - .pricing-card.featured: transform scale(1.05), border 2px solid primary, z-index 1
   - .plan-price: font-size 3rem, font-weight 700, color primary, margin 1rem 0
   - .plan-price .period: font-size 1rem, font-weight 400, color gray
   - .plan-features: list-style none, text-align left, padding 0, margin 1.5rem 0
   - .plan-features li: padding 0.5rem 0, border-bottom 1px solid #f0f0f0, display flex, align-items center, gap 0.5rem
   - .plan-cta: display block, margin-top 2rem

6. TESTIMONIALS: .testimonials-grid
   - display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem;
   - @media max-width 1024px: grid-template-columns: repeat(2, 1fr)
   - @media max-width 640px: grid-template-columns: 1fr
   - .testimonial-card: background var(--bg-surface), border-radius var(--radius), padding var(--card-padding), box-shadow var(--shadow), transition var(--transition), border 1px solid rgba(255,255,255,0.06)
   - .stars: color #f59e0b (gold), margin-bottom 1rem
   - .quote: font-size 1.05rem, line-height 1.7, font-style italic, margin-bottom 1.5rem
   - .author: display flex, align-items center, gap 0.75rem
   - .author strong: display block, .author span: font-size 0.9rem, color #666

7. STATS: .stats-grid
   - display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.5rem; text-align: center; max-width: 900px; margin: 0 auto;
   - @media max-width 768px: grid-template-columns: repeat(2, 1fr)
   - .stat: display flex, flex-direction column, align-items center, justify-content center, gap 0.6rem
   - .stat-icon: font-size 1.6rem, color var(--primary), opacity 0.8
   - .stat-number: font-size clamp(2.5rem, 4vw, 3rem), font-weight 700, line-height 1, white-space nowrap, color var(--primary)
   - .stat-label: font-size 0.9rem, text-transform uppercase, letter-spacing 1px, color var(--text-muted), max-width 200px

8. CTA SECTION: [data-section-type="cta"]
   - background: var(--primary) or dark gradient, color white, text-align center, padding 80px+
   - .cta-buttons: display flex, gap 1rem, justify-content center, margin-top 2rem
   - Override btn colors for dark background

9. CONTACT: .contact-wrapper
   - display grid, grid-template-columns 1fr 1fr on desktop, 1fr on mobile, gap 3rem
   - .contact-item: display flex, gap 1rem, margin-bottom 1.5rem, align-items start
   - .contact-item i: font-size 1.2rem, color primary, width 20px
   - .contact-form input/textarea: width 100%, padding 1rem, border-radius 8px, border 1px solid #ddd, font-family inherit, margin-bottom 1rem
   - .contact-form input:focus, textarea:focus: border-color primary, outline none, box-shadow 0 0 0 3px primary at 10%

10. FOOTER: footer
    - background: dark (--text-color or #1a1a2e), color white/light, padding 60px 0 30px
    - .footer-grid: display grid, grid-template-columns repeat(4, 1fr) desktop, repeat(2, 1fr) tablet, 1fr mobile, gap 2rem
    - .footer-brand-block: margin-bottom 1.5rem
    - .footer-brand-block .nav-brand: display flex, align-items center, gap 10px, text-decoration none, color white, font-weight 700, font-size 1.15rem, margin-bottom 1rem
    - .footer-brand-block .logo-mark: width 32px, height 32px, border-radius 8px, background linear-gradient(135deg, var(--primary), var(--secondary))
    - .footer-description: font-size 0.95rem, color rgba(255,255,255,0.6), line-height 1.6, max-width 280px
    - .footer-col h4: margin-bottom 1.5rem, font-size 1.1rem
    - .footer-col ul: list-style none, padding 0
    - .footer-col a: color rgba(255,255,255,0.7), text-decoration none, transition var(--transition)
    - .footer-col a:hover: color white
    - .social-links: display flex, gap 1rem
    - .social-links a: width 40px, height 40px, border-radius 50%, background rgba(255,255,255,0.08), display flex, align center justify center, color white, transition var(--transition), border 1px solid rgba(255,255,255,0.1)
    - .social-links a:hover: background var(--primary), border-color var(--primary), transform translateY(-2px)
    - .footer-bottom: border-top 1px solid rgba(255,255,255,0.08), margin-top 3rem, padding-top 2rem, text-align center, color rgba(255,255,255,0.5)

11. HERO (CRITICAL — must look good):
    - section[data-section-type="hero"]: padding var(--section-padding) 0; display: flex; align-items: center;
    - Do NOT use min-height: 90vh — let content determine height naturally with padding
    - section .container-wide for hero_split: display grid, grid-template-columns 1fr 1fr, gap 3rem, align-items center
    - ALL text (h1, .hero-subtitle, .hero-ctas, .trust-line) must be inside .hero-content — CSS should NOT rearrange them
    - h1: font-size clamp(2.5rem, 5vw, 3.5rem), font-weight 700, line-height 1.15, margin-bottom 1rem
    - .hero-subtitle: font-size 1.15rem, line-height 1.7, color var(--text-muted), margin-bottom 1.5rem, max-width 540px
    - .hero-ctas: display flex, gap 1rem, flex-wrap wrap
    - .trust-line: margin-top 1.5rem, font-size 0.9rem, color var(--text-muted)
    - .hero-content.centered: margin-bottom 0 (NOT var(--space-lg) — keep hero content tight, mockup is close below)
    - .hero-image img: width 100%, height auto, max-height 420px, border-radius 14px, object-fit cover, transition transform 0.4s ease
    - .hero-image img:hover: transform scale(1.02)
    - @media max-width 768px: section .container-wide grid-template-columns 1fr, .hero-image order -1

12. NAVBAR (CRITICAL — must not break):
    - position fixed, top 0, width 100%, z-index 1000, backdrop-filter blur(12px), transition var(--transition)
    - For light themes: background rgba(255,255,255,0.85), border-bottom 1px solid rgba(0,0,0,0.06)
    - For dark themes: background rgba(0,0,0,0.4), border-bottom 1px solid rgba(255,255,255,0.08)
    - .nav-scrolled: stronger background opacity, box-shadow 0 2px 20px rgba(0,0,0,0.08)
    - Container: display flex, justify-content space-between, align-items center, padding 1rem 1.5rem
    - .nav-brand: display flex, align-items center, gap 10px, text-decoration none, color var(--text), font-weight 700, font-size 1.2rem
    - .logo-mark: width 32px, height 32px, border-radius 8px, background linear-gradient(135deg, var(--primary), var(--accent, var(--primary))), background-size 200% 200%, animation logoGradient 6s ease infinite, flex-shrink 0, box-shadow 0 4px 20px rgba(0,0,0,0.15)
    - IMPORTANT: logo-mark gradient should use --primary to --accent (NOT --secondary). On dark themes where --secondary is similar to --bg, using --secondary makes the logo invisible. Use --accent as the second gradient stop.
    - @keyframes logoGradient: 0% background-position 0% 50%, 50% background-position 100% 50%, 100% background-position 0% 50%
    - .logo-text: font-weight 700, font-size 1.15rem, letter-spacing -0.01em
    - .nav-links: display flex, list-style none, gap 2rem, align-items center, margin: 0, padding: 0
    - .nav-links a: text-decoration none, font-weight 500, color var(--text), transition var(--transition), white-space: nowrap, position relative
    - .nav-links a::after: content "", position absolute, bottom -4px, left 0, width 0, height 2px, background var(--primary), transition width 0.3s ease
    - .nav-links a:hover::after: width 100%
    - .nav-toggle: display none (HIDDEN on desktop by default), background none, border none, font-size 1.5rem, cursor pointer, color var(--text), padding 0.5rem
    - .mobile-cta: display none (HIDDEN on desktop)
    - .nav-cta: display inline-block (VISIBLE on desktop)
    - @media max-width 768px:
      - .nav-toggle: display block
      - .nav-cta: display none (HIDDEN on mobile — CTA moves inside menu)
      - .mobile-cta: display block (VISIBLE inside mobile menu)
      - .nav-links: display none, position fixed, top 70px, left 0, right 0, background var(--bg), backdrop-filter blur(12px), flex-direction column, padding 1.5rem 2rem, gap 1.25rem, box-shadow 0 10px 30px rgba(0,0,0,0.15), z-index 999, border-bottom 1px solid rgba(255,255,255,0.08)
      - .nav-links a: font-size 1.05rem, padding 0.5rem 0
      - .nav-links a::after: display none
      - .nav-links.active: display flex
    - body: padding-top 80px (to offset fixed navbar)

13. LOGO CLOUD: .logo-grid
    - display flex, flex-wrap wrap, justify-content center, align-items center, gap 1.5rem
    - .logo-item: padding 0.75rem 1.5rem
    - .logo-text-item: font-size 1.1rem, font-weight 700, letter-spacing 0.02em, opacity 0.4, transition all 0.3s, white-space nowrap, color var(--text)
    - .logo-text-item:hover: opacity 0.8
    - section[data-section-type="logo_cloud"]: padding var(--space-lg) 0 (SMALLER than other sections — logo clouds should be compact)
    - NOTE: Do NOT style .logo-item img — logo cloud uses text-only spans, no images

14. HERO FULL IMAGE: .hero-bg-image
    - background-size cover, background-position center, background-repeat no-repeat, min-height 70vh, position relative
    - .hero-overlay: position absolute, inset 0, background rgba(0,0,0,0.7), display flex, align-items center
    - IMPORTANT: overlay MUST be 0.7 opacity minimum — text must be clearly readable over any image
    - All text inside: color white
    - .hero-subtitle: color rgba(255,255,255,0.85)
    - .trust-line: color rgba(255,255,255,0.7)

15. HERO MINIMAL: .hero-minimal-content
    - padding 120px 0, max-width 700px, margin 0 auto
    - h1: font-size clamp(3rem, 6vw, 4.5rem), margin-bottom 1rem
    - .hero-subtitle: font-size 1.25rem, margin-bottom 2.5rem

16. HERO PRODUCT MOCKUP: .hero-mockup
    - margin-top var(--space-md), text-align center, position relative
    - .hero-mockup img: max-width 85%, max-height 420px, height auto, border-radius 14px, box-shadow 0 25px 80px rgba(0,0,0,0.2), transition var(--transition), object-fit cover
    - .hero-mockup img:hover: transform scale(1.02)
    - @media max-width 768px: .hero-mockup img max-width 100%, max-height 300px

17. HERO MOCKUP CENTER (browser frame): .hero-browser-frame
    - margin-top var(--space-md), max-width 800px, margin-left auto, margin-right auto, border-radius 14px, overflow hidden, box-shadow 0 25px 80px rgba(0,0,0,0.2), border 1px solid rgba(0,0,0,0.1)
    - .browser-dots: display flex, gap 6px, padding 12px 16px, background rgba(0,0,0,0.04)
    - .browser-dots span: width 10px, height 10px, border-radius 50%, background rgba(0,0,0,0.12)
    - .browser-dots span:first-child: background #ff5f57
    - .browser-dots span:nth-child(2): background #ffbd2e
    - .browser-dots span:last-child: background #28c940
    - For dark themes: .browser-dots background rgba(255,255,255,0.06), border-color rgba(255,255,255,0.08)
    - .hero-browser-frame img: width 100%, display block, height auto
    - @media max-width 768px: .hero-browser-frame max-width 100%, margin-top var(--space-md)

18. HERO ASYMMETRIC: .hero-asymmetric-layout
    - display grid, grid-template-columns 55% 45%, gap 3rem, align-items center
    - .hero-asymmetric-visual: position relative
    - .hero-asymmetric-img: width 100%, border-radius 14px, object-fit cover, transition var(--transition)
    - .hero-asymmetric-img:hover: transform scale(1.02)
    - .hero-floating-card: position absolute, bottom -20px, left -20px, background var(--bg-surface), border-radius var(--radius), padding 1.25rem 1.5rem, box-shadow var(--shadow-hover), display flex, align-items center, gap 0.75rem, backdrop-filter blur(10px), border 1px solid rgba(255,255,255,0.1), z-index 2
    - .hero-floating-card i: font-size 1.5rem, color var(--primary)
    - .hero-floating-card span: font-weight 600, font-size 0.95rem
    - @media max-width 768px: .hero-asymmetric-layout grid-template-columns 1fr, .hero-floating-card position static, margin-top 1rem

19. HERO VIDEO BG: .hero-animated-bg
    - background: animated gradient using CSS (linear-gradient with background-size 400% and animation), min-height 80vh, display flex, align-items center
    - @keyframes gradientShift: 0% background-position 0% 50%, 50% background-position 100% 50%, 100% background-position 0% 50%
    - animation: gradientShift 8s ease infinite
    - All text: color white

17. FEATURE CARDS: .feature-cards-grid
    - display grid, grid-template-columns repeat(3, 1fr), gap 2rem
    - @media max-width 1024px: grid-template-columns repeat(2, 1fr)
    - @media max-width 640px: grid-template-columns 1fr
    - .feature-card: border-radius var(--radius), overflow hidden, background white, box-shadow var(--shadow), transition var(--transition)
    - .feature-card:hover: transform translateY(-5px), box-shadow var(--shadow-hover)
    - .feature-card-image img: width 100%, height 200px, object-fit cover
    - .feature-card-body: padding 1.5rem

18. FEATURE STACKED: .feature-stack
    - max-width 800px, margin 0 auto
    - .feature-stack-item: display flex, gap 2rem, align-items flex-start, padding 2rem 0, border-bottom 1px solid rgba(0,0,0,0.08)
    - .feature-stack-item:last-child: border-bottom none
    - .feature-stack-icon: width 60px, height 60px, min-width 60px, border-radius 12px, background var(--primary) at 10% opacity, display flex, align-items center, justify-content center, font-size 1.4rem, color var(--primary)
    - .feature-stack-content h3: margin-bottom 0.5rem
    - @media max-width 768px: .feature-stack-item flex-direction column, gap 1rem

18b. FEATURE STEPS: .steps-container
    - max-width 700px, margin 0 auto, position relative
    - .steps-container::before: content "", position absolute, left 28px, top 0, bottom 0, width 2px, background linear-gradient(180deg, var(--primary), var(--secondary))
    - .step: display flex, gap 1.5rem, align-items flex-start, padding 2rem 0, position relative
    - .step-number: width 56px, height 56px, min-width 56px, border-radius 50%, background linear-gradient(135deg, var(--primary), var(--secondary)), color white, display flex, align-items center, justify-content center, font-weight 700, font-size 1.2rem, z-index 1, box-shadow 0 4px 20px rgba(0,0,0,0.15)
    - .step-content h3: margin-bottom 0.5rem, font-size 1.2rem
    - .step-content p: color var(--text-muted), line-height 1.7
    - @media max-width 768px: .steps-container::before left 24px, .step-number width 48px, height 48px, min-width 48px, font-size 1rem

19. TESTIMONIAL SLIDER: .testimonial-slider
    - max-width 700px, margin 0 auto, text-align center, position relative
    - .testimonial-slide: display none
    - .testimonial-slide.active: display block
    - .quote: font-size 1.3rem, font-style italic, line-height 1.8, margin 1.5rem 0
    - .slider-dots: display flex, justify-content center, gap 0.5rem, margin-top 2rem
    - .slider-dot: width 12px, height 12px, border-radius 50%, border 2px solid var(--primary), background transparent, cursor pointer, padding 0
    - .slider-dot.active: background var(--primary)

20. TESTIMONIAL SPLIT: .testimonial-split-wrapper
    - display grid, grid-template-columns 1fr 1fr, gap 3rem, align-items center
    - .testimonial-split-quote .quote: font-size 1.3rem, font-style italic, line-height 1.8, margin 1.5rem 0
    - .testimonial-split-image img: width 100%, border-radius var(--radius), object-fit cover, max-height 400px
    - @media max-width 768px: grid-template-columns 1fr

21. TEAM CARDS LARGE: .team-cards-grid
    - display grid, grid-template-columns repeat(3, 1fr), gap 2rem
    - @media max-width 1024px: grid-template-columns repeat(2, 1fr)
    - @media max-width 640px: grid-template-columns 1fr
    - .team-card-lg: background white, border-radius var(--radius), overflow hidden, box-shadow var(--shadow), transition var(--transition)
    - .team-card-lg:hover: transform translateY(-5px), box-shadow var(--shadow-hover)
    - .team-card-lg .team-photo: width 100%, height 280px, object-fit cover
    - .team-card-body: padding 1.5rem
    - .team-bio: font-size 0.9rem, color var(--text-muted), margin-top 0.5rem

22. TEAM MASONRY: .team-masonry-grid
    - column-count 3, column-gap 1.5rem
    - @media max-width 1024px: column-count 2
    - @media max-width 768px: column-count 1
    - .team-masonry-item: break-inside avoid, margin-bottom 1.5rem, position relative, border-radius var(--radius), overflow hidden
    - .team-masonry-item img: width 100%, display block
    - .team-masonry-overlay: position absolute, bottom 0, left 0, right 0, background linear-gradient(transparent, rgba(0,0,0,0.8)), color white, padding 1.5rem, transform translateY(100%), transition transform 0.3s
    - .team-masonry-item:hover .team-masonry-overlay: transform translateY(0)

23. CTA SPLIT: .cta-split-wrapper
    - display grid, grid-template-columns 1fr 1fr, gap 3rem, align-items center
    - .cta-split-image img: width 100%, border-radius var(--radius), object-fit cover
    - @media max-width 768px: grid-template-columns 1fr

24. CTA GRADIENT: .cta-gradient-bg
    - background: linear-gradient(135deg, var(--primary), var(--secondary)), padding var(--section-padding) 0, color white, text-align center
    - .btn-glow: box-shadow 0 0 20px rgba(255,255,255,0.3), border 2px solid rgba(255,255,255,0.3)
    - .btn-glow:hover: box-shadow 0 0 30px rgba(255,255,255,0.5), transform translateY(-2px)

24b. CTA CENTERED: [data-section-type="cta"] with cta_centered pattern
    - text-align center, padding var(--space-xl) 0, background var(--bg-alt)
    - .cta-content.centered h2: font-size clamp(1.8rem, 3vw, 2.5rem), margin-bottom 1rem
    - .cta-content.centered p: color var(--text-muted), max-width 500px, margin 0 auto 2rem, font-size 1.1rem
    - Uses .container-narrow for focused layout, no gradient — clean and minimal

25. BACKGROUND ORBS: .background-orb
    - position fixed, border-radius 50%, filter blur(120px), opacity 0.15, z-index -1, pointer-events none
    - .orb-1: width 400px, height 400px, background var(--primary), top -100px, left -100px, animation floatOrb 20s ease-in-out infinite
    - .orb-2: width 500px, height 500px, background var(--secondary), bottom -150px, right -150px, animation floatOrb 25s ease-in-out infinite reverse
    - @keyframes floatOrb: 0% transform translateY(0), 50% transform translateY(-40px), 100% transform translateY(0)
    - On light themes: reduce opacity to 0.08

SECTION SPACING AND RHYTHM:
- Every <section>: padding var(--section-padding) 0, position relative
- Hero sections: padding var(--section-padding) 0 with extra top padding (account for navbar)
- logo_cloud sections: padding var(--space-lg) 0 (compact — logos don't need much space)
- Alternate section backgrounds for rhythm: section:nth-of-type(even) background var(--bg-alt)
- CTA sections override: background linear-gradient(135deg, var(--primary), var(--secondary)), color white
- body: padding-top 80px (navbar offset)
- Use the spacing scale consistently: var(--space-sm) between elements, var(--space-md) between groups, var(--section-padding) between sections
- IMPORTANT: Sections should NOT be taller than the viewport. Keep sections compact and content-dense. Avoid excessive whitespace.

SECTION SCROLL REVEAL (MANDATORY — include these exact rules):
- section[data-section-type] {{ opacity: 0; transform: translateY(40px); transition: opacity 0.7s ease, transform 0.7s ease; }}
- section[data-section-type].visible {{ opacity: 1; transform: translateY(0); }}
- nav and footer must NOT have opacity 0 — they are always visible
- JS adds class 'visible' via IntersectionObserver — CSS just defines the states

PREMIUM IMAGE TREATMENT:
- All content images (not logos): border-radius 14px, object-fit cover, transition transform 0.4s ease
- Image hover: transform scale(1.02) — subtle zoom effect
- .feature-image img, .hero-image img, .team-photo: all get this treatment
- overflow hidden on parent containers to clip scaled images

PREMIUM VISUAL POLISH (CRITICAL — makes the difference between generic and premium):
- Proper WCAG AA contrast between text and backgrounds
- Heading font for h1-h6, body font for everything else
- Use var(--shadow) and var(--shadow-hover) consistently — never hardcode different shadows
- btn-primary uses linear-gradient(135deg, var(--primary), var(--secondary)) background
- btn-primary border-radius: var(--radius-btn)
- All transitions use var(--transition) — the cubic-bezier curve is important for premium feel
- Cards: border 1px solid rgba(255,255,255,0.06) for glass-edge effect on dark themes
- Link hover underline animation using ::after pseudo-element where appropriate
- Social icons should have hover lift effect (translateY(-2px))
- Generous padding — when in doubt, add MORE whitespace, not less
- Typography scale: h1 clamp(2.5rem, 5vw, 3.5rem), h2 clamp(1.8rem, 3vw, 2.5rem), h3 1.25rem
- Section headers: h2 margin-bottom 1rem, p max-width 600px margin 0 auto

DESIGN REFERENCE — aim for this caliber:
The generated CSS should produce a website that looks like a premium SaaS landing page (Stripe, Linear, Framer, Vercel, Apple quality). Key characteristics:
- Strong typography hierarchy with large, bold headings and generous line-height
- Ample whitespace between all elements — spacious, not cramped
- Glassmorphism on navbar and elevated cards (backdrop-filter, semi-transparent backgrounds, subtle borders)
- Gradient accents on primary buttons, logo marks, and CTA sections
- Soft, deep shadows that increase on hover for a floating effect
- Smooth transitions everywhere — cubic-bezier(0.4, 0, 0.2, 1), never harsh or instant
- Rounded corners (12-16px on cards, 8px on images, pill buttons)
- Floating background orbs for ambient visual depth
- Section scroll-reveal animations for progressive disclosure
- Interactive micro-animations: card lift, image zoom, link underline slide, button glow"""


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

ITERATION_SYSTEM_PROMPT = """You are an expert web developer modifying an existing website that uses Tailwind CSS utility classes.

CURRENT CODE:
--- HTML (includes <style> block + body content with Tailwind classes) ---
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
- HTML = <style> block FIRST (CSS variables, fonts, animations) + body content with Tailwind utility classes
- Use Tailwind CSS utility classes for layout, spacing, typography, colors, responsive
- Use CSS variables via arbitrary values: text-[var(--primary)], bg-[var(--bg)], etc.
- Maintain existing design and functionality unless changes are requested
- Do NOT include any explanation, just the two code blocks

SECTION SIZE CONSTRAINTS:
- Hero: max min-h-[80vh]. NEVER taller than viewport.
- All sections: keep same size as original. No excessive padding.

IMAGE HANDLING:
- "Add background image" = CSS background-image ONLY (no extra <img> tag)
- NEVER add BOTH a background-image AND a foreground <img> for the same purpose
- Background images: bg-cover bg-center with overlay (bg-black/40 max)

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

SECTION TO EDIT ({section_type} section):
{section_html}

USER REQUEST: {prompt}

RULES:
- Return ONLY the updated section HTML inside a single ```html code block
- Return the COMPLETE section element (opening tag through closing tag)
- Use Tailwind CSS utility classes for ALL styling
- Use CSS variables via arbitrary values: text-[var(--accent)], bg-[var(--bg)], rounded-[var(--radius)], etc.
- Keep the same outer element tag and data-section-type attribute
- Keep the same data-section-id attribute
- For icon colors, use text-[var(--accent)] NOT text-[var(--primary)]
- For images, keep existing src URLs unless user asks to change images
- Do NOT add Font Awesome script tags — icons are already loaded
- Do NOT wrap in extra divs or add <html>/<head>/<body> tags
- Do NOT include any explanation, just the html code block
- You CAN freely change the section's internal layout/structure when the user asks for it (e.g., converting hero_split to hero with background image)

SECTION SIZE CONSTRAINTS (CRITICAL):
- Hero sections: max min-h-[80vh]. NEVER make a hero taller than viewport.
- All other sections: keep the same visual size as the original. No min-h-screen unless it was already there.
- Do NOT add excessive padding/margins that make the section abnormally tall.

IMAGE HANDLING FOR EDITS:
- "Add background image" = CSS background-image ONLY. Do NOT also add a foreground <img> tag.
- NEVER add BOTH a background-image AND a foreground <img> for the same visual purpose.
- When converting an <img> to a background image: use the SAME src URL from the existing <img> tag as the background-image URL
- Background image hero: <section style="background-image: url('EXISTING_IMAGE_URL'); background-size: cover; background-position: center;" class="relative min-h-[80vh] flex items-center">
  Then add a dark overlay: <div class="absolute inset-0 bg-black/40"></div> (40% max opacity — image must be visible)
  Then wrap text in: <div class="relative z-10 max-w-[1400px] mx-auto px-6">
- When moving image from side to background, REMOVE the old <img> tag completely
- Make sure text is readable over the background (use text-white + dark overlay)

CRITICAL — JS-DEPENDENT CLASS NAMES (DO NOT rename or remove these):
JavaScript already exists on the page and depends on these exact class names and IDs.
If you change them, the interactive features will break silently.

NAVBAR:
- .nav-links MUST keep class "nav-links" and have "flex list-none gap-8 items-center m-0 p-0"
- .nav-toggle MUST keep class "nav-toggle hidden" (CSS shows it on mobile via @media)
- .nav-cta stays visible on desktop; .mobile-cta stays hidden on desktop
- Do NOT add flex-direction: column, display: none, position: fixed, or class "active" to .nav-links
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
- Use Tailwind CSS utility classes for ALL styling
- Use CSS variables via arbitrary values: text-[var(--accent)], bg-[var(--bg)], rounded-[var(--radius)], etc.
- Match the design style of the existing sections (colors, fonts, spacing, border radius)
- Write REAL content that matches the business context — no "Lorem ipsum" or placeholder text
- For images, use placeholder format: src="{{{{IMG:descriptive keywords}}}}"
- Do NOT add Font Awesome script tags — icons are already loaded
- Do NOT wrap in extra divs or add <html>/<head>/<body> tags
- Do NOT include any explanation, just the html code block
- Section should have class="py-16 md:py-20 relative" (standard section padding)
- Footer sections: use py-14 md:py-16 and dark background (bg-[#1a1a2e] or similar)

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
