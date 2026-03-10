"""
Website template blueprints for the Meydan Free Zone website generator.

Each template is a design blueprint passed to the LLM to produce a specific
visual style.  Templates are NOT raw HTML/CSS -- they are structured
instructions that guide generation.
"""

TEMPLATES: dict[str, dict] = {
    # =========================================================================
    # MINIMAL (10)
    # =========================================================================
    "minimal_dark": {
        "name": "Minimal Dark",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%)",
        "description": "Clean dark theme with generous whitespace and subtle animations",
        "design_instructions": (
            "Color palette: background #0a0a0a, surface #111118, text #e4e4e7, accent #6366f1, muted #71717a.\n"
            "Typography: Inter or system sans-serif, light weight headings (300), regular body (400). Large display text at 3.5-4rem.\n"
            "Layout: single-column centered, max-width 1080px, generous vertical padding (120px per section).\n"
            "Effects: subtle fade-in-up on scroll, 1px border lines as dividers with #222 color, no heavy shadows.\n"
            "Sections: use full-width backgrounds alternating #0a0a0a and #0f0f15. Hero text left-aligned.\n"
            "Buttons: pill-shaped with #6366f1 fill, 12px 32px padding, subtle hover glow (box-shadow 0 0 20px rgba(99,102,241,0.3)).\n"
            "Mood: sophisticated, developer-friendly, calm. Think Linear or Vercel landing pages."
        ),
        "suitable_for": ["tech_startup", "portfolio", "saas", "developer_tools"],
    },
    "minimal_light": {
        "name": "Minimal Light",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%)",
        "description": "Airy white theme with fine typography and delicate accents",
        "design_instructions": (
            "Color palette: background #ffffff, surface #fafafa, text #18181b, accent #2563eb, muted #a1a1aa.\n"
            "Typography: DM Sans or system sans-serif, medium weight headings (500), normal body. Heading sizes 2.5-3rem.\n"
            "Layout: centered single column, max-width 960px, 100px section padding, 24px paragraph spacing.\n"
            "Effects: very subtle box-shadows (0 1px 3px rgba(0,0,0,0.04)), smooth opacity transitions on scroll.\n"
            "Sections: all white backgrounds, separated by thin 1px #e4e4e7 horizontal lines. Clean card components with 1px borders.\n"
            "Buttons: rounded-md, border 1px solid #2563eb on secondary, filled #2563eb on primary, font-weight 500.\n"
            "Mood: clean, breathable, trustworthy. Inspired by Apple or Stripe product pages."
        ),
        "suitable_for": ["saas", "consultancy", "portfolio", "agency"],
    },
    "minimal_mono": {
        "name": "Minimal Monochrome",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #1a1a1a 0%, #333333 100%)",
        "description": "Strictly black-and-white with bold typographic hierarchy",
        "design_instructions": (
            "Color palette: only #000000, #ffffff, and grays #222, #555, #888, #ccc. Zero chromatic color.\n"
            "Typography: Space Grotesk or bold grotesque font, headings uppercase 700 weight at 4rem, body 16px 400 weight.\n"
            "Layout: asymmetric two-column grid on desktop, full-width stacked on mobile. Max-width 1200px.\n"
            "Effects: sharp hover transitions (transform scale 1.02), underline animations on links, no rounded corners.\n"
            "Sections: alternate black-bg-white-text and white-bg-black-text for dramatic contrast.\n"
            "Buttons: rectangular with thick 2px borders, uppercase text, letter-spacing 2px, no fill on hover invert.\n"
            "Mood: editorial, high-fashion, stark. Think Comme des Garcons or Ssense."
        ),
        "suitable_for": ["portfolio", "fashion", "photography", "architecture"],
    },
    "minimal_warm": {
        "name": "Minimal Warm",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #faf7f2 0%, #f0e6d6 100%)",
        "description": "Warm off-white tones with earthy accents and soft type",
        "design_instructions": (
            "Color palette: background #faf7f2, surface #f5efe6, text #3d3229, accent #c2703e, muted #9c8b7a.\n"
            "Typography: Libre Baskerville for headings (serif, 500), Source Sans 3 for body. Headings 2.5rem, body 17px with 1.7 line-height.\n"
            "Layout: centered content, max-width 840px for text blocks, images edge-to-edge. 100px vertical rhythm.\n"
            "Effects: gentle parallax on hero image, smooth color transitions on hover (0.3s ease), warm drop shadows (0 4px 12px rgba(61,50,41,0.08)).\n"
            "Sections: cream/beige backgrounds, occasional full-bleed image sections. Card components with 8px radius and warm shadow.\n"
            "Buttons: rounded-full with #c2703e fill, cream text, 14px 28px padding. Ghost variant with #c2703e border.\n"
            "Mood: artisanal, approachable, handcrafted. Like a boutique bakery or lifestyle brand."
        ),
        "suitable_for": ["bakery", "lifestyle", "wellness", "boutique"],
    },
    "minimal_cool": {
        "name": "Minimal Cool",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%)",
        "description": "Cool blue-gray palette with crisp geometric precision",
        "design_instructions": (
            "Color palette: background #f0f4f8, surface #ffffff, text #243b53, accent #2680c2, muted #829ab1.\n"
            "Typography: IBM Plex Sans, headings 600 weight, body 400. Clean 2rem headings, 15px body, tight letter-spacing (-0.01em).\n"
            "Layout: 12-column CSS grid, content in center 8 columns, max-width 1100px. 80px section gaps.\n"
            "Effects: crisp 1px borders (#d9e2ec), hover lift on cards (translateY -4px + shadow increase), smooth 0.2s transitions.\n"
            "Sections: alternating #f0f4f8 and #ffffff backgrounds. Stats sections use large #2680c2 numbers.\n"
            "Buttons: 6px radius, #2680c2 fill, white text, medium font. Hover darkens to #1a6dab. 12px 24px padding.\n"
            "Mood: precise, analytical, trustworthy. Think Notion or Linear documentation."
        ),
        "suitable_for": ["saas", "fintech", "analytics", "b2b"],
    },
    "minimal_nature": {
        "name": "Minimal Nature",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%)",
        "description": "Organic greens and soft neutrals inspired by natural forms",
        "design_instructions": (
            "Color palette: background #f8faf5, surface #ffffff, text #2e3d2a, accent #4caf50, secondary #81c784, muted #8a9a86.\n"
            "Typography: Nunito for headings (700), Open Sans for body (400). Headings 2.2rem, body 16px, line-height 1.75.\n"
            "Layout: flowing single-column, max-width 960px, organic spacing with varying section padding (80-120px).\n"
            "Effects: leaf-like border-radius (30% 70% 70% 30% / 30% 30% 70% 70%) on decorative elements, soft green shadows (0 8px 24px rgba(76,175,80,0.1)).\n"
            "Sections: soft sage green tinted backgrounds, occasional full-width nature imagery. Rounded cards with 16px radius.\n"
            "Buttons: rounded-full, #4caf50 fill with white text, 14px 32px padding. Hover brightens to #66bb6a.\n"
            "Mood: fresh, sustainable, eco-conscious. Like an organic food brand or eco-startup."
        ),
        "suitable_for": ["eco_brand", "organic", "wellness", "sustainability"],
    },
    "minimal_neon": {
        "name": "Minimal Neon",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #0d0d0d 0%, #1a0d2e 100%)",
        "description": "Dark canvas with a single vivid neon accent color",
        "design_instructions": (
            "Color palette: background #0d0d0d, surface #151519, text #e0e0e0, accent #00ff88, muted #666666.\n"
            "Typography: JetBrains Mono for headings (monospace, 600), Inter for body. Headings 2.5rem, body 15px.\n"
            "Layout: centered narrow column (max-width 900px), generous 100px section padding, code-block aesthetic.\n"
            "Effects: neon glow on accent elements (text-shadow 0 0 10px #00ff88, 0 0 40px rgba(0,255,136,0.3)), scanline texture overlay at 5% opacity.\n"
            "Sections: dark backgrounds with subtle 1px #222 borders between sections. Terminal-style code snippets.\n"
            "Buttons: border 1px solid #00ff88, transparent fill, #00ff88 text, hover fills with #00ff88 and text turns #0d0d0d.\n"
            "Mood: hacker-chic, futuristic, cyberpunk-lite. Think terminal meets landing page."
        ),
        "suitable_for": ["developer_tools", "crypto", "tech_startup", "gaming"],
    },
    "minimal_pastel": {
        "name": "Minimal Pastel",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #fce4ec 0%, #e8eaf6 100%)",
        "description": "Soft pastel colors with rounded shapes and gentle gradients",
        "design_instructions": (
            "Color palette: background #fefefe, surface #fff5f7, text #4a3f55, accent #b388ff, secondary #80deea, tertiary #ffab91.\n"
            "Typography: Quicksand for headings (600), Poppins for body (400). Headings 2.2rem, body 15px, line-height 1.7.\n"
            "Layout: centered content, max-width 1000px, 90px section padding, 3-column feature grids.\n"
            "Effects: pastel gradient backgrounds on cards, large border-radius (20px), soft shadows (0 6px 20px rgba(179,136,255,0.12)), hover scale 1.03.\n"
            "Sections: white base with alternating pastel tint overlays (#fff5f7, #f3e5f5, #e8eaf6). Floating blob decorations.\n"
            "Buttons: rounded-full, pastel gradient (135deg, #b388ff to #80deea), white text, 14px 30px padding, shadow on hover.\n"
            "Mood: friendly, youthful, approachable. Like a modern wellness app or Gen-Z brand."
        ),
        "suitable_for": ["wellness_app", "education", "kids_brand", "lifestyle"],
    },
    "minimal_earth": {
        "name": "Minimal Earth",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #3e2723 0%, #5d4037 100%)",
        "description": "Rich earth tones with textured warmth and artisan feel",
        "design_instructions": (
            "Color palette: background #2c1e17, surface #3e2723, text #efebe9, accent #d4a76a, muted #8d6e63.\n"
            "Typography: Playfair Display for headings (700, serif), Lato for body (300). Headings 3rem, body 16px, line-height 1.8.\n"
            "Layout: wide max-width 1200px, asymmetric hero with large left text and right image, 2-column grids for content.\n"
            "Effects: subtle paper-grain texture overlay at 3% opacity, warm shadows (0 10px 30px rgba(44,30,23,0.5)), gold underlines on headings.\n"
            "Sections: deep brown backgrounds with occasional cream (#efebe9) sections for contrast. Bordered cards with #d4a76a 1px accent lines.\n"
            "Buttons: #d4a76a fill with #2c1e17 text, 8px radius, uppercase, letter-spacing 1.5px, hover darkens to #c49555.\n"
            "Mood: grounded, premium craft, heritage. Like a specialty coffee brand or leather goods shop."
        ),
        "suitable_for": ["coffee_shop", "craft_brand", "restaurant", "artisan"],
    },
    "minimal_ocean": {
        "name": "Minimal Ocean",
        "category": "Minimal",
        "preview_gradient": "linear-gradient(135deg, #0d2137 0%, #1a3a5c 100%)",
        "description": "Deep ocean blues with fluid shapes and tranquil vibes",
        "design_instructions": (
            "Color palette: background #0d2137, surface #132d4a, text #cce5ff, accent #4fc3f7, secondary #0097a7, muted #5d8aa8.\n"
            "Typography: Montserrat for headings (500), Roboto for body (300). Headings 2.8rem, body 16px, line-height 1.7.\n"
            "Layout: centered max-width 1080px, full-width wave SVG dividers between sections, 100px padding.\n"
            "Effects: wavy section dividers using SVG, subtle background gradient animation (slow hue shift), glow on accent text (text-shadow 0 0 15px rgba(79,195,247,0.4)).\n"
            "Sections: dark navy base alternating with slightly lighter #132d4a. Cards have glass-like backgrounds (rgba(255,255,255,0.05) + backdrop-blur).\n"
            "Buttons: rounded-md, #4fc3f7 fill, dark text #0d2137, 12px 28px. Hover brightens. Ghost variant with #4fc3f7 border.\n"
            "Mood: serene, deep, exploratory. Like an ocean conservation nonprofit or travel platform."
        ),
        "suitable_for": ["travel", "marine", "nonprofit", "wellness"],
    },

    # =========================================================================
    # BOLD & MODERN (10)
    # =========================================================================
    "bold_gradient": {
        "name": "Bold Gradient",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #667eea 0%, #f093fb 100%)",
        "description": "Vibrant multi-color gradients with strong visual impact",
        "design_instructions": (
            "Color palette: primary gradient 135deg #667eea to #764ba2, secondary gradient #f093fb to #f5576c, text #ffffff, dark #1a1a2e.\n"
            "Typography: Sora for headings (800), Inter for body (400). Headings 3.5rem, body 16px. White text on gradient backgrounds.\n"
            "Layout: full-width gradient hero (100vh), content sections max-width 1100px, 3-column feature grid, staggered layout.\n"
            "Effects: gradient backgrounds that shift on hover, gradient text (background-clip text) for key headings, floating gradient orbs as decoration.\n"
            "Sections: alternate between gradient-bg-white-text and white-bg-dark-text. Feature cards on white with gradient left border (4px).\n"
            "Buttons: gradient fill (135deg #667eea to #764ba2), white text, rounded-lg (10px), 14px 36px, box-shadow 0 4px 15px rgba(102,126,234,0.4).\n"
            "Mood: energetic, dynamic, modern. Think Stripe or Figma-level polish."
        ),
        "suitable_for": ["saas", "tech_startup", "creative_agency", "app"],
    },
    "bold_geometric": {
        "name": "Bold Geometric",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #ff6b6b 0%, #feca57 100%)",
        "description": "Angular shapes, diagonal lines, and geometric patterns",
        "design_instructions": (
            "Color palette: background #ffffff, primary #ff6b6b, secondary #feca57, dark #2d3436, text #2d3436, accent #6c5ce7.\n"
            "Typography: Archivo Black for headings (900), Work Sans for body (400). Headings 3rem uppercase, letter-spacing 2px, body 15px.\n"
            "Layout: diagonal section dividers (clip-path polygon), overlapping content blocks, 12-column grid with offset elements.\n"
            "Effects: diagonal clip-paths on section backgrounds, geometric shape decorations (triangles, hexagons) as CSS pseudo-elements, bold drop shadows (8px 8px 0 #2d3436).\n"
            "Sections: white sections with single bold color accent backgrounds. Feature cards tilted 2deg on hover. Geometric pattern overlays at 5% opacity.\n"
            "Buttons: chunky rectangular, #ff6b6b fill, white text, bold 4px black shadow offset, uppercase, hover translates -2px -2px.\n"
            "Mood: playful-bold, Memphis-inspired, graphically striking."
        ),
        "suitable_for": ["creative_agency", "event", "brand", "startup"],
    },
    "bold_split": {
        "name": "Bold Split",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(90deg, #1a1a2e 50%, #e94560 50%)",
        "description": "Dramatic two-tone split layouts with high contrast",
        "design_instructions": (
            "Color palette: dark half #1a1a2e, bright half #e94560, text-on-dark #ffffff, text-on-bright #ffffff, accent #eee.\n"
            "Typography: Bebas Neue for headings (display, 400), Roboto for body (400). Headings 4.5rem, body 16px.\n"
            "Layout: 50/50 split hero (left dark, right red), alternating split sections. On mobile stacks vertically.\n"
            "Effects: sharp color splits using CSS grid or flexbox, content slides in from respective sides, hover reveals on split elements.\n"
            "Sections: each section is a split - one side color, one side content or image. Testimonials on dark side, features on bright.\n"
            "Buttons: on dark bg use white outline, on bright bg use white fill with #e94560 text. Rectangular, 14px 36px.\n"
            "Mood: dramatic, editorial, high-impact. Like a fashion magazine or bold portfolio."
        ),
        "suitable_for": ["portfolio", "fashion", "agency", "brand"],
    },
    "bold_neon": {
        "name": "Bold Neon",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #0f0f0f 0%, #1a0033 100%)",
        "description": "Electric neon colors on dark backgrounds with glow effects",
        "design_instructions": (
            "Color palette: background #0f0f0f, surface #1a1a1a, neon-pink #ff006e, neon-blue #00b4d8, neon-green #06d6a0, text #ffffff.\n"
            "Typography: Orbitron for headings (700), Exo 2 for body (400). Headings 3rem, body 15px. Headings use neon glow.\n"
            "Layout: full-width hero with neon text overlay, centered content max-width 1100px, 3-column neon-bordered feature cards.\n"
            "Effects: neon text-shadow (0 0 10px, 0 0 20px, 0 0 40px in neon color), neon border glow on cards, animated gradient border using background-clip.\n"
            "Sections: all dark backgrounds, sections separated by thin neon gradient lines. Hero has animated neon flicker effect (subtle opacity keyframes).\n"
            "Buttons: transparent with 2px neon border, neon text, hover fills with neon color. Glow box-shadow on hover.\n"
            "Mood: electric, nightclub, high-energy. Think gaming or music event sites."
        ),
        "suitable_for": ["gaming", "music", "nightlife", "event"],
    },
    "bold_retro": {
        "name": "Bold Retro",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #f4a261 0%, #e76f51 100%)",
        "description": "70s-80s inspired retro palette with rounded shapes",
        "design_instructions": (
            "Color palette: background #fdf6e3, primary #e76f51, secondary #f4a261, tertiary #2a9d8f, dark #264653, cream #fdf6e3.\n"
            "Typography: Righteous for headings (retro display, 400), Outfit for body (400). Headings 3rem, body 16px.\n"
            "Layout: centered max-width 1000px, rounded section containers (24px radius), stacked card layout.\n"
            "Effects: retro halftone dot pattern overlay at 3% opacity, chunky rounded shadows (6px 6px 0 #264653), hover wobble (rotate 1deg).\n"
            "Sections: cream base with colored section backgrounds (#2a9d8f, #e76f51). Cards are white with thick 3px colored borders.\n"
            "Buttons: pill-shaped (50px radius), bold colored fill, dark text, thick 3px shadow, uppercase, letter-spacing 1px.\n"
            "Mood: nostalgic, groovy, fun. Like a retro diner or vintage brand revival."
        ),
        "suitable_for": ["restaurant", "vintage_brand", "food_truck", "entertainment"],
    },
    "bold_brutalist": {
        "name": "Bold Brutalist",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)",
        "description": "Raw brutalist design with exposed structure and harsh type",
        "design_instructions": (
            "Color palette: background #f5f5f5, text #111111, accent #ff0000, borders #111111. Strictly minimal color.\n"
            "Typography: Space Mono for everything (monospace, 700 headings, 400 body). Headings 3.5rem uppercase, body 14px.\n"
            "Layout: visible grid structure, thick 3px black borders on all containers, no border-radius anywhere, raw exposed layout.\n"
            "Effects: zero animations, zero transitions, zero shadows, zero gradients. Raw CSS. Thick black borders. Text selection highlight in #ff0000.\n"
            "Sections: all sections have thick black top borders. Content blocks are clearly boxed. Intentionally raw and unpolished.\n"
            "Buttons: thick 3px black border, no fill, uppercase monospace text, hover inverts to black fill white text. No transitions.\n"
            "Mood: anti-design, raw, intentionally rough. Think Bloomberg terminal meets punk zine."
        ),
        "suitable_for": ["art_gallery", "experimental", "developer_tools", "portfolio"],
    },
    "bold_duotone": {
        "name": "Bold Duotone",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #5b21b6 0%, #06b6d4 100%)",
        "description": "Two-color duotone palette applied across the entire design",
        "design_instructions": (
            "Color palette: color A #5b21b6 (deep violet), color B #06b6d4 (cyan), white #ffffff, dark blend #1e1545.\n"
            "Typography: General Sans or DM Sans for all text, headings 700 at 3rem, body 400 at 16px. Gradient text on hero heading.\n"
            "Layout: full-width hero with gradient (A to B at 135deg), centered 1080px content, 2-column feature sections.\n"
            "Effects: duotone filter on all images (mix-blend-mode or CSS filter), gradient text headings, gradient border on cards (2px).\n"
            "Sections: alternate between gradient-bg-white-text and white-bg with gradient accents. Cards have subtle gradient borders.\n"
            "Buttons: gradient fill (A to B), white text, 10px radius, 14px 32px. Hover shifts gradient angle. Ghost variant with gradient border.\n"
            "Mood: cohesive, contemporary, visually unified. Like Spotify Wrapped or event branding."
        ),
        "suitable_for": ["music", "event", "brand", "saas"],
    },
    "bold_contrast": {
        "name": "Bold Contrast",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #000000 0%, #facc15 100%)",
        "description": "Maximum contrast black and yellow with sharp edges",
        "design_instructions": (
            "Color palette: black #000000, yellow #facc15, white #ffffff, gray #333333.\n"
            "Typography: Anton for headings (display, 400, uppercase), Barlow for body (400). Headings 4rem, body 16px.\n"
            "Layout: full-width sections, max-width 1200px content, bold asymmetric grids, oversized hero text.\n"
            "Effects: yellow highlight bars behind headings, sharp geometric dividers, elements break the grid intentionally, strong shadows (8px 8px 0 #facc15).\n"
            "Sections: black backgrounds with yellow accents, occasional full-yellow sections with black text. Warning-stripe patterns as decorative elements.\n"
            "Buttons: yellow fill, black text, rectangular sharp corners, bold uppercase, 16px 40px, hover inverts to black fill yellow text.\n"
            "Mood: loud, urgent, attention-grabbing. Like a construction brand or bold startup announcement."
        ),
        "suitable_for": ["construction", "startup_launch", "event", "fitness"],
    },
    "bold_glassmorphism": {
        "name": "Bold Glassmorphism",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #4a00e0 0%, #8e2de2 50%, #00c6ff 100%)",
        "description": "Frosted glass cards floating over vibrant gradient backgrounds",
        "design_instructions": (
            "Color palette: gradient bg #4a00e0 to #8e2de2 to #00c6ff, glass rgba(255,255,255,0.1), border rgba(255,255,255,0.2), text #ffffff.\n"
            "Typography: Poppins for headings (600), Inter for body (400). Headings 2.8rem, body 15px, white text throughout.\n"
            "Layout: gradient full-page background, content in glass cards (max-width 1100px), 3-column glass feature grid.\n"
            "Effects: backdrop-filter blur(16px) on all cards, 1px rgba(255,255,255,0.18) borders, subtle inner glow, floating glass layers at different blur levels.\n"
            "Sections: the entire page has one continuous gradient background. All content sits in glass containers. Decorative blurred circle blobs behind sections.\n"
            "Buttons: glass button (rgba(255,255,255,0.15), backdrop-blur(10px)), 1px white/20% border, 12px 28px, hover brightens glass.\n"
            "Mood: futuristic, premium, iOS-inspired. Think Apple Vision Pro aesthetics."
        ),
        "suitable_for": ["tech_startup", "app", "saas", "fintech"],
    },
    "bold_aurora": {
        "name": "Bold Aurora",
        "category": "Bold & Modern",
        "preview_gradient": "linear-gradient(135deg, #0f172a 0%, #1e3a5f 33%, #22d3ee 66%, #a855f7 100%)",
        "description": "Northern lights inspired with flowing color gradients on dark sky",
        "design_instructions": (
            "Color palette: background #0f172a, aurora-cyan #22d3ee, aurora-purple #a855f7, aurora-green #34d399, text #e2e8f0, muted #64748b.\n"
            "Typography: Plus Jakarta Sans for headings (700), Inter for body (400). Headings 3rem, body 16px, generous line-height 1.8.\n"
            "Layout: full-width sections with max-width 1080px content, centered hero, 3-column features, testimonial slider.\n"
            "Effects: animated gradient mesh background (slow-moving aurora blobs using radial-gradient animation), gradient text for headings, soft glow on accent elements.\n"
            "Sections: dark navy base, aurora gradient blobs positioned as background decorations (large radial gradients at 30% opacity). Glass cards for content.\n"
            "Buttons: gradient fill (cyan to purple), white text, 10px radius, 14px 32px, glow shadow (0 4px 20px rgba(34,211,238,0.3)).\n"
            "Mood: celestial, awe-inspiring, premium dark. Like a space startup or premium SaaS."
        ),
        "suitable_for": ["saas", "tech_startup", "ai_product", "premium_brand"],
    },

    # =========================================================================
    # ELEGANT & LUXURY (10)
    # =========================================================================
    "elegant_gold": {
        "name": "Elegant Gold",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #1a1a1a 0%, #2d2316 100%)",
        "description": "Luxurious dark theme with gold accents and refined typography",
        "design_instructions": (
            "Color palette: background #1a1a1a, surface #222222, gold #c9a96e, light-gold #dfc08a, text #e8e0d5, muted #7a7368.\n"
            "Typography: Cormorant Garamond for headings (serif, 600), Lato for body (300). Headings 3rem, body 16px, letter-spacing 0.02em.\n"
            "Layout: centered narrow content (max-width 900px), generous 120px section padding, symmetrical layouts.\n"
            "Effects: gold gradient text on key headings (linear-gradient #c9a96e to #dfc08a), thin gold 1px lines as decorative dividers, subtle gold shimmer keyframe animation.\n"
            "Sections: dark base with occasional dark-gold (#2d2316) section backgrounds. Gold bordered cards with 1px #c9a96e border.\n"
            "Buttons: gold border 1px, transparent bg, gold text, uppercase, letter-spacing 3px, hover fills gold with dark text.\n"
            "Mood: luxury, premium, exclusive. Think Rolex or premium hotel branding."
        ),
        "suitable_for": ["luxury_brand", "hotel", "jewelry", "real_estate"],
    },
    "elegant_marble": {
        "name": "Elegant Marble",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #f5f2ef 0%, #e8e3dc 100%)",
        "description": "Marble-inspired whites and grays with rose gold accents",
        "design_instructions": (
            "Color palette: background #f5f2ef, surface #ffffff, text #2c2c2c, accent #b76e79 (rose gold), muted #9e9e9e, marble-vein #d5cfc7.\n"
            "Typography: Italiana for display headings (400), Cormorant for sub-headings (500, serif), Lato body (300). Display 4rem, body 16px.\n"
            "Layout: wide max-width 1200px, generous whitespace, centered text blocks, large full-width image sections.\n"
            "Effects: marble texture background (subtle gray veining pattern via CSS gradient overlays), rose gold line accents, delicate hover transitions (0.4s ease).\n"
            "Sections: white and off-white alternating, thin rose gold horizontal rules between sections, large serif pull-quotes.\n"
            "Buttons: rose gold fill #b76e79, white text, slight border-radius (4px), 14px 36px, elegant hover darken.\n"
            "Mood: spa-like, polished, serene luxury. Think high-end spa or wedding planner."
        ),
        "suitable_for": ["spa", "wedding", "beauty", "interior_design"],
    },
    "elegant_serif": {
        "name": "Elegant Serif",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #1b1b1b 0%, #2a2a2a 100%)",
        "description": "Typography-driven design with beautiful serif type hierarchy",
        "design_instructions": (
            "Color palette: background #1b1b1b, surface #232323, text #e5e1dc, accent #c5a47e, muted #7d756b.\n"
            "Typography: EB Garamond for headings (400 italic + 700), Spectral for body (300 serif). Headings 3.5rem, body 17px, line-height 1.85.\n"
            "Layout: narrow centered column (max-width 760px), long-form text friendly, generous paragraph margins, drop caps on first paragraphs.\n"
            "Effects: thin decorative serif ornaments between sections (CSS), italic accent text, smooth scroll behavior, very subtle fade-in on scroll.\n"
            "Sections: minimal section differentiation, content flows like a book page. Occasional full-width image breaks. Pull quotes in large italic.\n"
            "Buttons: minimal style, text-link with underline, accent color #c5a47e, hover underline thickens. Primary: thin border, serif text.\n"
            "Mood: literary, editorial, thoughtful. Think Kinfolk magazine or New Yorker online."
        ),
        "suitable_for": ["publishing", "blog", "literary", "consultancy"],
    },
    "elegant_rose": {
        "name": "Elegant Rose",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #2b1521 0%, #4a2037 100%)",
        "description": "Deep rose and blush tones with feminine luxury feel",
        "design_instructions": (
            "Color palette: background #2b1521, surface #3a1e30, blush #e8a0bf, deep-rose #c2185b, cream #fce4ec, text #f5e6ed.\n"
            "Typography: Playfair Display for headings (700), Raleway for body (300). Headings 2.8rem, body 15px, wide letter-spacing on subheads.\n"
            "Layout: centered max-width 1000px, elegant hero with centered text overlay, 2-column grid for features, full-width testimonials.\n"
            "Effects: blush glow on accent elements (box-shadow 0 0 30px rgba(232,160,191,0.2)), delicate gradient overlays, soft image overlays.\n"
            "Sections: deep rose backgrounds, occasional cream (#fce4ec) sections for contrast. Cards with soft blush borders and gentle shadows.\n"
            "Buttons: blush fill #e8a0bf, dark text #2b1521, rounded-full, 14px 32px, hover deepens to #c2185b with white text.\n"
            "Mood: romantic, feminine luxury, elegant. Think luxury cosmetics or bridal brand."
        ),
        "suitable_for": ["beauty", "fashion", "bridal", "cosmetics"],
    },
    "elegant_midnight": {
        "name": "Elegant Midnight",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #0a0e27 0%, #1a1f4e 100%)",
        "description": "Deep midnight blue with silver and starlight accents",
        "design_instructions": (
            "Color palette: background #0a0e27, surface #12173d, silver #c0c5d0, starlight #e8ecf4, accent #7c83ff, text #d0d5e0.\n"
            "Typography: Cinzel for headings (serif, decorative, 700), Montserrat for body (300). Headings 2.8rem uppercase, letter-spacing 4px, body 15px.\n"
            "Layout: centered 1000px content, symmetric section layouts, hero with centered text, evenly spaced feature columns.\n"
            "Effects: star-like dot pattern background (radial-gradient dots), silver line decorations, subtle shimmer on headings, elegant slow fade transitions.\n"
            "Sections: deep midnight backgrounds, section borders in silver (#c0c5d0) at 20% opacity. Diamond-shaped decorative elements at section joins.\n"
            "Buttons: silver outline 1px, silver text, uppercase, letter-spacing 3px, hover fills silver with #0a0e27 text. 12px 32px.\n"
            "Mood: celestial, exclusive, mysterious. Think luxury watch brand or five-star hotel."
        ),
        "suitable_for": ["luxury_hotel", "fine_dining", "jewelry", "premium_event"],
    },
    "elegant_champagne": {
        "name": "Elegant Champagne",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #f7f0e6 0%, #e8dcc8 100%)",
        "description": "Warm champagne and soft gold on cream backgrounds",
        "design_instructions": (
            "Color palette: background #f7f0e6, surface #ffffff, champagne #d4b896, soft-gold #c9a96e, text #3d3428, muted #8a7e6e.\n"
            "Typography: Bodoni Moda for headings (serif, 400), Jost for body (300). Headings 3rem, body 16px, line-height 1.75.\n"
            "Layout: elegant centered layout, max-width 960px, large hero image with text overlay, 3-column feature cards.\n"
            "Effects: champagne gradient accents, soft warm shadows (0 6px 20px rgba(61,52,40,0.08)), gold horizontal rules, image frames with thin gold border.\n"
            "Sections: cream and white alternating, champagne-tinted feature backgrounds. Decorative gold corner accents on hero section.\n"
            "Buttons: champagne fill #d4b896, dark text #3d3428, 6px radius, 14px 32px, subtle shadow, hover deepens to #c9a96e.\n"
            "Mood: refined celebration, warm luxury, inviting elegance. Think champagne house or luxury event venue."
        ),
        "suitable_for": ["event_venue", "wedding", "luxury_brand", "wine"],
    },
    "elegant_velvet": {
        "name": "Elegant Velvet",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #2d0a31 0%, #4a1650 100%)",
        "description": "Rich velvet purples with plush, tactile visual depth",
        "design_instructions": (
            "Color palette: background #2d0a31, surface #3d1545, velvet #7b2d8e, soft-lilac #d4a5e0, gold #dab06c, text #ede0f0.\n"
            "Typography: Spectral for headings (serif, 600), Karla for body (400). Headings 2.8rem, body 16px, line-height 1.75.\n"
            "Layout: centered max-width 1000px, hero with large centered heading, 2-column content sections, full-width testimonial band.\n"
            "Effects: velvet-like depth via layered shadows (0 2px 4px rgba(0,0,0,0.3), 0 8px 24px rgba(45,10,49,0.5)), gold accent lines, soft lilac glow on hover elements.\n"
            "Sections: deep purple backgrounds with slight gradient variation. Cards have rich dark surfaces with gold top-border accent.\n"
            "Buttons: gold fill #dab06c, dark purple text #2d0a31, 8px radius, 14px 30px, hover glow (box-shadow 0 0 20px rgba(218,176,108,0.3)).\n"
            "Mood: opulent, theatrical, deeply luxurious. Think opera house or exclusive club."
        ),
        "suitable_for": ["theater", "luxury_event", "fashion", "exclusive_club"],
    },
    "elegant_ivory": {
        "name": "Elegant Ivory",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #fffef7 0%, #f5ecd7 100%)",
        "description": "Soft ivory and muted tones with timeless classic styling",
        "design_instructions": (
            "Color palette: background #fffef7, surface #f9f5eb, text #3c3630, accent #8b7355, secondary #c4a77d, muted #a39888.\n"
            "Typography: Libre Caslon Display for headings (serif, 400), Source Serif 4 for body (300). Headings 2.8rem, body 17px, line-height 1.85.\n"
            "Layout: narrow column max-width 800px for text, wider 1100px for cards. Generous 120px section padding, classic proportions.\n"
            "Effects: minimal effects, thin 1px #c4a77d decorative lines, small serif ornamental dividers, gentle image zoom on hover (scale 1.05).\n"
            "Sections: ivory and white alternating, bordered card groups with subtle #e6dfd4 borders. Pull quotes with large serif italic.\n"
            "Buttons: #8b7355 fill, ivory text, 4px radius, 12px 28px, uppercase 12px font, letter-spacing 2px. Understated hover darken.\n"
            "Mood: timeless, quiet luxury, heritage. Think old-money estate or premium stationery."
        ),
        "suitable_for": ["stationery", "consultancy", "law_firm", "heritage_brand"],
    },
    "elegant_onyx": {
        "name": "Elegant Onyx",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #0c0c0c 0%, #1e1e1e 100%)",
        "description": "Pure black with platinum-white accents and sharp refinement",
        "design_instructions": (
            "Color palette: background #0c0c0c, surface #171717, platinum #e8e8e8, white #ffffff, accent #999999, muted #555555.\n"
            "Typography: Didot or Bodoni Moda for headings (thin serif, 400), Montserrat for body (300). Headings 3.5rem, body 15px.\n"
            "Layout: max-width 1100px, full-width hero with oversized thin heading, 2-column layouts, asymmetric image placements.\n"
            "Effects: platinum-white thin line decorations, subtle background grain texture (noise at 2%), image grayscale filter, hover reveals color.\n"
            "Sections: all black/near-black backgrounds, content differentiated by spacing not color. Platinum divider lines at 40% opacity.\n"
            "Buttons: thin 1px white border, white text, uppercase, letter-spacing 4px, 12px 36px. Hover fills white with black text. Minimal and sharp.\n"
            "Mood: ultra-premium, gallery-like, high fashion. Think Chanel or YSL web presence."
        ),
        "suitable_for": ["high_fashion", "luxury_brand", "art_gallery", "architecture"],
    },
    "elegant_pearl": {
        "name": "Elegant Pearl",
        "category": "Elegant & Luxury",
        "preview_gradient": "linear-gradient(135deg, #f5f0f0 0%, #e8e0e4 50%, #f0ebe8 100%)",
        "description": "Pearlescent whites and pinks with iridescent shimmer touches",
        "design_instructions": (
            "Color palette: background #f5f0f0, surface #ffffff, pearl-pink #e8d5dc, pearl-blue #d5dee8, accent #b8a9c9, text #3a3540.\n"
            "Typography: Cormorant for headings (serif, 500), Nunito Sans for body (300). Headings 2.8rem, body 16px, line-height 1.8.\n"
            "Layout: centered 1000px content, gentle curving section dividers (subtle wave SVG), rounded card containers (16px radius).\n"
            "Effects: pearlescent gradient backgrounds (pink to blue at low opacity), soft multi-color shadows (pink and blue at 10%), gentle shimmer via background-position animation.\n"
            "Sections: white base, alternating with pearl-pink and pearl-blue tinted sections at 30% opacity. Cards float with soft shadows.\n"
            "Buttons: soft gradient (pearl-pink to pearl-blue), dark text, rounded-full, 14px 30px, subtle iridescent hover shift.\n"
            "Mood: delicate, ethereal, sophisticated softness. Think luxury skincare or pearl jewelry brand."
        ),
        "suitable_for": ["skincare", "jewelry", "bridal", "beauty"],
    },

    # =========================================================================
    # CORPORATE & PROFESSIONAL (10)
    # =========================================================================
    "corp_blue": {
        "name": "Corporate Blue",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)",
        "description": "Classic corporate blue with structured, trustworthy layouts",
        "design_instructions": (
            "Color palette: primary #1e3a5f, accent #2563eb, background #ffffff, surface #f8fafc, text #1e293b, muted #64748b.\n"
            "Typography: Inter for everything, headings 700 at 2.5rem, body 400 at 16px. Clean and professional throughout.\n"
            "Layout: structured 12-column grid, max-width 1200px, blue hero banner with white text, 3-column feature cards, stats bar.\n"
            "Effects: subtle blue shadows on cards (0 4px 12px rgba(30,58,95,0.1)), clean hover state transitions, professional icon usage.\n"
            "Sections: white and light-blue (#f8fafc) alternating. Blue accent bar at top of page. Professional card grid for services.\n"
            "Buttons: #2563eb fill, white text, 6px radius, 12px 24px. Secondary: white fill with blue text and 1px blue border.\n"
            "Mood: reliable, established, professional. Standard corporate landing page like IBM or Deloitte."
        ),
        "suitable_for": ["corporate", "b2b", "consulting", "finance"],
    },
    "corp_green": {
        "name": "Corporate Green",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #064e3b 0%, #059669 100%)",
        "description": "Green-themed corporate design conveying growth and stability",
        "design_instructions": (
            "Color palette: primary #064e3b, accent #059669, light #d1fae5, background #ffffff, surface #f0fdf4, text #1a2e24, muted #6b7c74.\n"
            "Typography: Plus Jakarta Sans for headings (700), Inter for body (400). Headings 2.5rem, body 16px.\n"
            "Layout: max-width 1200px, green gradient hero (dark to light), 4-column stat counters, 3-column service grid, CTA band.\n"
            "Effects: green-tinted shadows on elevated elements, subtle up-arrow growth indicators, clean chart/data visualization styling.\n"
            "Sections: white base, green (#f0fdf4) tinted alternate sections. Dark green (#064e3b) footer. Professional grid cards.\n"
            "Buttons: #059669 fill, white text, 6px radius, 12px 24px. Hover darkens to #047857. Ghost variant green border.\n"
            "Mood: growth-oriented, sustainable, trustworthy. Like a green finance or ESG consultancy."
        ),
        "suitable_for": ["finance", "sustainability", "consulting", "agriculture"],
    },
    "corp_slate": {
        "name": "Corporate Slate",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #334155 0%, #475569 100%)",
        "description": "Neutral slate grays with refined professional restraint",
        "design_instructions": (
            "Color palette: primary #334155, accent #6366f1, background #ffffff, surface #f8fafc, text #1e293b, muted #94a3b8, border #e2e8f0.\n"
            "Typography: DM Sans for headings (600), Inter for body (400). Headings 2.2rem, body 15px, tight spacing.\n"
            "Layout: max-width 1140px, understated hero with slate gradient, organized 3-column layouts, sidebar-style feature sections.\n"
            "Effects: very subtle box-shadows (0 1px 2px rgba(0,0,0,0.05)), 1px #e2e8f0 borders on all cards, clean hover state (border color darkens).\n"
            "Sections: white and #f8fafc alternating, slate (#334155) used sparingly for hero and footer. Minimal visual noise.\n"
            "Buttons: indigo accent #6366f1 fill, white text, 6px radius, 12px 24px. Professional and restrained.\n"
            "Mood: understated, competent, no-nonsense. Think enterprise software or law firm."
        ),
        "suitable_for": ["law_firm", "enterprise", "b2b_saas", "consulting"],
    },
    "corp_trust": {
        "name": "Corporate Trust",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #1e3a5f 100%)",
        "description": "Deep trust blue with authority indicators and credibility elements",
        "design_instructions": (
            "Color palette: navy #1e3a5f, royal #1e40af, sky #3b82f6, background #ffffff, surface #eff6ff, text #1e293b, gold-accent #d97706.\n"
            "Typography: Merriweather for headings (serif, 700), Source Sans 3 for body (400). Headings 2.5rem, body 16px.\n"
            "Layout: max-width 1100px, navy hero with shield/badge motif, trust badges row, testimonials with photos, certification logos.\n"
            "Effects: subtle navy shadows, gold accent on trust badges, professional headshot circular frames, checkmark icons in #059669.\n"
            "Sections: white base, navy hero, light blue (#eff6ff) testimonial section. Trust-badge strip with logos in grayscale. Dark navy footer.\n"
            "Buttons: navy #1e3a5f fill, white text, 6px radius, 14px 28px. Gold accent button #d97706 for primary CTA.\n"
            "Mood: authoritative, credible, established. Think insurance company or financial institution."
        ),
        "suitable_for": ["insurance", "banking", "government", "healthcare"],
    },
    "corp_modern": {
        "name": "Corporate Modern",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #111827 0%, #374151 100%)",
        "description": "Modern corporate with dark header and clean white content",
        "design_instructions": (
            "Color palette: dark #111827, gray #374151, background #ffffff, surface #f9fafb, accent #8b5cf6, text #111827, muted #6b7280.\n"
            "Typography: Outfit for headings (600), Inter for body (400). Headings 2.5rem, body 16px. Modern and clean.\n"
            "Layout: dark hero section (100vh), white content sections max-width 1200px, alternating left-right feature rows, bottom CTA.\n"
            "Effects: smooth scroll, subtle parallax on hero, clean card hover (lift + shadow increase), purple accent lines on active states.\n"
            "Sections: dark hero transitions to white content. Alternating white/#f9fafb sections. Purple accent touches throughout.\n"
            "Buttons: #8b5cf6 fill, white text, 8px radius, 14px 28px. Dark variant: #111827 fill. Both hover darken slightly.\n"
            "Mood: contemporary, forward-thinking, tech-corporate. Like a modern enterprise SaaS."
        ),
        "suitable_for": ["saas", "enterprise", "tech_company", "startup"],
    },
    "corp_executive": {
        "name": "Corporate Executive",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        "description": "Premium corporate dark theme for C-suite facing brands",
        "design_instructions": (
            "Color palette: background #1a1a2e, surface #16213e, text #d5dbe5, accent #3498db, gold #d4a76a, muted #5a6a7e.\n"
            "Typography: Cormorant for display headings (serif, 500), Inter for body (400). Display 3.5rem, subheadings 1.5rem, body 16px.\n"
            "Layout: max-width 1100px, sophisticated hero with subtle gradient, executive team grid, key metrics dashboard-style section.\n"
            "Effects: gold line accents sparingly, refined shadows (0 8px 30px rgba(0,0,0,0.3)), data visualization styling, subtle background patterns.\n"
            "Sections: dark navy backgrounds throughout, slightly lighter cards (#1e2a4a) for content. Gold horizontal rules between major sections.\n"
            "Buttons: gold outline 1px #d4a76a, gold text, uppercase, letter-spacing 2px, 12px 28px. Primary: #3498db fill, white text.\n"
            "Mood: boardroom-level, prestigious, high-end professional. Think McKinsey or Goldman Sachs."
        ),
        "suitable_for": ["private_equity", "investment", "executive_consulting", "wealth_management"],
    },
    "corp_clean": {
        "name": "Corporate Clean",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #ffffff 0%, #e5e7eb 100%)",
        "description": "Ultra-clean white design with systematic spacing and clarity",
        "design_instructions": (
            "Color palette: background #ffffff, surface #f9fafb, border #e5e7eb, text #111827, accent #2563eb, success #059669, muted #9ca3af.\n"
            "Typography: Inter for everything, headings 600 at 2.2rem, body 400 at 15px. 4px baseline grid. Precise and systematic.\n"
            "Layout: strict 8px grid system, max-width 1080px, 16px gutters, organized card grids, clear information hierarchy.\n"
            "Effects: minimal -- only 1px borders and subtle shadows (0 1px 2px rgba(0,0,0,0.04)). Hover transitions 0.15s. Focus rings for accessibility.\n"
            "Sections: all white or near-white, differentiated by spacing and borders. Clean horizontal rules. Icon + text feature pairs.\n"
            "Buttons: #2563eb fill, white text, 6px radius, 10px 20px. Small, precise, functional. Hover darkens 10%.\n"
            "Mood: systematic, accessible, functional. Think Google Cloud or Atlassian product pages."
        ),
        "suitable_for": ["saas", "b2b", "healthcare", "education"],
    },
    "corp_gradient": {
        "name": "Corporate Gradient",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #0f172a 0%, #1e40af 50%, #7c3aed 100%)",
        "description": "Professional with modern gradient hero and clean white body",
        "design_instructions": (
            "Color palette: gradient #0f172a to #1e40af to #7c3aed, background #ffffff, surface #f8fafc, text #1e293b, accent #7c3aed, muted #64748b.\n"
            "Typography: Sora for headings (600), Inter for body (400). Hero heading 3rem white on gradient, section headings 2rem dark, body 16px.\n"
            "Layout: full-width gradient hero (60vh), white content body max-width 1200px, 3-column features, stats strip, testimonials.\n"
            "Effects: gradient hero with subtle mesh pattern overlay, white cards with purple accent left-borders, smooth scroll reveals.\n"
            "Sections: dramatic gradient hero, then clean white sections. One mid-page gradient CTA band. Light gray alternate sections.\n"
            "Buttons: gradient fill (blue to purple) for primary, 8px radius, 14px 28px. White outline on gradient backgrounds.\n"
            "Mood: progressive corporate, modern-professional. Think Microsoft or Twilio marketing pages."
        ),
        "suitable_for": ["tech_company", "saas", "enterprise", "cloud_service"],
    },
    "corp_minimal": {
        "name": "Corporate Minimal",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #fafafa 0%, #e4e4e7 100%)",
        "description": "Stripped-down corporate with maximum content clarity",
        "design_instructions": (
            "Color palette: background #fafafa, surface #ffffff, text #18181b, accent #18181b, link #2563eb, muted #71717a, border #e4e4e7.\n"
            "Typography: Inter for everything, headings 500 at 2rem (not bold, medium weight), body 400 at 15px. Restraint in sizing.\n"
            "Layout: max-width 920px, narrow content column, text-heavy with clear hierarchy, minimal imagery, structured lists.\n"
            "Effects: almost none. Simple underline links in #2563eb, 1px borders, clean focus states. No shadows, no gradients.\n"
            "Sections: white cards on #fafafa background, separated by 48px gaps. Simple header, clear sections, concise footer.\n"
            "Buttons: #18181b fill, white text, 4px radius, 10px 20px, small and functional. Secondary: 1px border, #18181b text.\n"
            "Mood: content-first, no-frills professional. Think Basecamp or gov.uk simplicity."
        ),
        "suitable_for": ["consultancy", "legal", "accounting", "government"],
    },
    "corp_sharp": {
        "name": "Corporate Sharp",
        "category": "Corporate & Professional",
        "preview_gradient": "linear-gradient(135deg, #18181b 0%, #27272a 50%, #dc2626 100%)",
        "description": "Dark corporate with red accent for bold authority",
        "design_instructions": (
            "Color palette: dark #18181b, surface #27272a, red #dc2626, white #ffffff, text-light #e4e4e7, muted #71717a.\n"
            "Typography: Archivo for headings (800 uppercase), Inter for body (400). Headings 2.8rem, letter-spacing 1px, body 15px.\n"
            "Layout: max-width 1200px, dark full-width hero with red accent stripe, sharp geometric layouts, 4-column stats grid.\n"
            "Effects: red accent underlines on headings, sharp 0px radius everywhere, red left-border accents (4px) on cards, high contrast.\n"
            "Sections: primarily dark backgrounds, white text. Occasional white sections with dark text for variety. Red accent strips between sections.\n"
            "Buttons: red #dc2626 fill, white text, 0px radius (sharp), uppercase, 14px 32px. Dark variant: white border on dark bg.\n"
            "Mood: powerful, decisive, authoritative. Think defense contractor or elite consulting."
        ),
        "suitable_for": ["security", "defense", "executive", "automotive"],
    },

    # =========================================================================
    # CREATIVE & PLAYFUL (10)
    # =========================================================================
    "creative_colorful": {
        "name": "Creative Colorful",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #ff6b6b 0%, #feca57 25%, #48dbfb 50%, #ff9ff3 75%, #54a0ff 100%)",
        "description": "Multi-color rainbow palette with joyful energy",
        "design_instructions": (
            "Color palette: red #ff6b6b, yellow #feca57, blue #48dbfb, pink #ff9ff3, green #1dd1a1, background #ffffff, text #2d3436.\n"
            "Typography: Fredoka One for headings (display, 400), Nunito for body (600). Headings 3rem, body 16px, playful sizing.\n"
            "Layout: max-width 1100px, colorful hero with multiple gradient blobs, offset card grid, zigzag feature layout.\n"
            "Effects: colored blob backgrounds (large radial-gradient circles), card hover color-shift, playful rotation on hover (3deg), bouncy transitions.\n"
            "Sections: white base with colored blob decorations positioned with absolute positioning. Each section has a different accent color.\n"
            "Buttons: colorful fills (each CTA different color), white text, rounded-full, 16px 36px, hover scales up 1.05 with shadow increase.\n"
            "Mood: joyful, energetic, celebration. Like a children's education platform or creative studio."
        ),
        "suitable_for": ["education", "kids_brand", "creative_studio", "toy_brand"],
    },
    "creative_handdrawn": {
        "name": "Creative Hand-Drawn",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
        "description": "Sketch-like aesthetic with hand-drawn borders and doodles",
        "design_instructions": (
            "Color palette: background #fefce8, surface #ffffff, text #1c1917, accent #ea580c, secondary #0d9488, muted #78716c.\n"
            "Typography: Patrick Hand for headings (handwriting, 400), Nunito for body (400). Headings 2.5rem, body 16px.\n"
            "Layout: centered max-width 900px, intentionally imperfect alignment, offset elements, casual asymmetric grids.\n"
            "Effects: wavy/sketchy border-radius (custom SVG borders or rough border simulation), doodle-style underlines, slight rotation on cards (1-2deg random), notebook-line backgrounds.\n"
            "Sections: paper-like backgrounds, sections separated by hand-drawn horizontal lines. Notebook or corkboard feel for testimonials.\n"
            "Buttons: hand-drawn border look (uneven border-radius like 255px 15px 225px 15px/15px 225px 15px 255px), #ea580c fill, white text.\n"
            "Mood: authentic, personal, crafty. Think independent bakery or personal blog."
        ),
        "suitable_for": ["bakery", "personal_blog", "craft_shop", "children_brand"],
    },
    "creative_retro": {
        "name": "Creative Retro 90s",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #7c3aed 0%, #ec4899 50%, #f59e0b 100%)",
        "description": "90s web nostalgia with bold colors and chunky elements",
        "design_instructions": (
            "Color palette: purple #7c3aed, pink #ec4899, yellow #f59e0b, teal #14b8a6, background #faf5ff, text #1e1b4b.\n"
            "Typography: Bungee for headings (display, 400), Space Grotesk for body (400). Headings 3rem, body 16px, bold color usage in text.\n"
            "Layout: max-width 1000px, chunky bordered sections, sticker-like floating elements, grid with visible gaps and colored backgrounds.\n"
            "Effects: thick colored borders (4px), drop-shadows (6px 6px 0 in contrasting color), star/sparkle decorations, marquee-style scrolling text for fun.\n"
            "Sections: different bright colored backgrounds per section. Cards look like stickers with thick borders and shadows. Retro pattern backgrounds.\n"
            "Buttons: chunky, thick 4px border, colored fill, contrasting shadow offset, rounded-lg, 16px 32px, uppercase, bold hover effects.\n"
            "Mood: nostalgic, fun, y2k-inspired. Think 90s Nickelodeon or Geocities modernized."
        ),
        "suitable_for": ["creative_studio", "entertainment", "music", "youth_brand"],
    },
    "creative_gradient_mesh": {
        "name": "Creative Gradient Mesh",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #fbbf24 0%, #ec4899 33%, #8b5cf6 66%, #06b6d4 100%)",
        "description": "Fluid gradient mesh backgrounds with dreamy color blending",
        "design_instructions": (
            "Color palette: mesh colors #fbbf24, #ec4899, #8b5cf6, #06b6d4, background #ffffff, text #1e293b on light, #ffffff on dark.\n"
            "Typography: General Sans or DM Sans for all text, headings 700 at 3rem, body 400 at 16px, clean and modern.\n"
            "Layout: max-width 1100px, full-screen gradient mesh hero, white content sections, gradient mesh CTA section.\n"
            "Effects: gradient mesh backgrounds (multiple overlapping radial-gradients with animation), smooth blob shapes, gradient text on headings, fluid transitions.\n"
            "Sections: hero and CTA sections use animated gradient mesh. Content sections are clean white. Occasional gradient accents on cards.\n"
            "Buttons: gradient fill (pink to purple), white text, 12px radius, 14px 32px, glow shadow on hover. Ghost variant with gradient border.\n"
            "Mood: artistic, dreamy, Instagram-aesthetic. Like a design tool or creative platform."
        ),
        "suitable_for": ["design_tool", "creative_platform", "photography", "social_media"],
    },
    "creative_abstract": {
        "name": "Creative Abstract",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #1e1b4b 0%, #4338ca 50%, #e879f9 100%)",
        "description": "Abstract art inspired with bold shapes and unexpected compositions",
        "design_instructions": (
            "Color palette: deep-indigo #1e1b4b, indigo #4338ca, fuchsia #e879f9, lime #a3e635, white #ffffff, text #e2e8f0.\n"
            "Typography: Clash Display or Space Grotesk for headings (700), Inter for body (400). Headings 3.5rem, body 15px.\n"
            "Layout: max-width 1200px, broken grid layout (elements intentionally overlap and offset), asymmetric 60/40 splits, rotated elements.\n"
            "Effects: abstract geometric shapes (CSS triangles, circles) as background decorations, elements with clip-path for unusual shapes, mix-blend-mode overlays.\n"
            "Sections: dark indigo base with bright accent shapes floating. Content breaks traditional grid with overlapping sections. Bold color blocks.\n"
            "Buttons: fuchsia #e879f9 fill, dark text, 0px radius, 16px 36px, uppercase. Hover rotates slightly (1deg) and scales.\n"
            "Mood: avant-garde, artistically bold, gallery-like. Think art studio or experimental design agency."
        ),
        "suitable_for": ["art_studio", "design_agency", "gallery", "experimental"],
    },
    "creative_pop": {
        "name": "Creative Pop Art",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #fef08a 0%, #f472b6 50%, #38bdf8 100%)",
        "description": "Pop art inspired with bold dots, speech bubbles, and vivid colors",
        "design_instructions": (
            "Color palette: yellow #fef08a, pink #f472b6, sky #38bdf8, red #ef4444, white #ffffff, black #000000.\n"
            "Typography: Bangers for headings (display, 400), Comic Neue for body (700). Headings 3.5rem, body 16px, uppercase headings.\n"
            "Layout: max-width 1100px, comic panel grid layout, speech bubble testimonials, bold section separators.\n"
            "Effects: Ben-Day dot pattern backgrounds (radial-gradient dots), thick 3px black outlines on everything, speech bubble shapes (CSS), POW/ZAP decorative elements.\n"
            "Sections: alternating bright colored backgrounds (yellow, pink, sky), each section like a comic panel with thick black borders.\n"
            "Buttons: bright fill with thick 3px black border, black text, bold shadow (4px 4px 0 #000), 16px 32px, hover shifts shadow.\n"
            "Mood: loud, fun, pop-culture. Think Roy Lichtenstein meets web design."
        ),
        "suitable_for": ["entertainment", "food_brand", "youth_brand", "media"],
    },
    "creative_watercolor": {
        "name": "Creative Watercolor",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #dbeafe 0%, #fce7f3 50%, #dcfce7 100%)",
        "description": "Soft watercolor washes with organic, flowing aesthetics",
        "design_instructions": (
            "Color palette: wash-blue #dbeafe, wash-pink #fce7f3, wash-green #dcfce7, wash-peach #ffedd5, text #374151, accent #6366f1.\n"
            "Typography: Caveat for display headings (handwriting, 700), Nunito Sans for body (400). Display 3rem, body 16px, flowing feel.\n"
            "Layout: centered max-width 960px, organic flowing sections (no sharp lines), rounded containers, overlapping watercolor blobs.\n"
            "Effects: watercolor blob backgrounds (large feathered radial-gradients with blur filters), organic border-radius shapes, text on watercolor splash backgrounds.\n"
            "Sections: white base with watercolor wash overlays in different colors per section. Cards appear to float on watercolor backgrounds.\n"
            "Buttons: soft watercolor fill (gradient with blur), dark text, rounded-full, 14px 30px, hover intensifies color.\n"
            "Mood: artistic, organic, gentle creativity. Think watercolor artist portfolio or wellness retreat."
        ),
        "suitable_for": ["art_portfolio", "wellness", "yoga_studio", "florist"],
    },
    "creative_neon_glow": {
        "name": "Creative Neon Glow",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #0a0a0a 0%, #170a2e 50%, #0a1628 100%)",
        "description": "Vibrant multi-color neon with intense glow and party energy",
        "design_instructions": (
            "Color palette: background #0a0a0a, neon-magenta #ff00ff, neon-cyan #00ffff, neon-yellow #ffff00, neon-orange #ff8800, text #ffffff.\n"
            "Typography: Orbitron for headings (700), Exo 2 for body (400). Headings 3rem with neon text-glow, body 15px white.\n"
            "Layout: full-width dark canvas, max-width 1100px content, neon-bordered feature grid, glowing testimonial cards.\n"
            "Effects: intense multi-color neon glow (text-shadow + box-shadow with 0 0 10px, 20px, 40px), animated color cycling on decorative elements, neon line art decorations.\n"
            "Sections: pitch-black backgrounds throughout, each section accented with a different neon color. Glowing neon divider lines.\n"
            "Buttons: transparent with 2px neon border (alternating colors), neon text, neon glow shadow, hover fills neon with dark text.\n"
            "Mood: party, nightlife, high-energy spectacle. Think music festival or nightclub website."
        ),
        "suitable_for": ["nightclub", "festival", "music", "entertainment"],
    },
    "creative_collage": {
        "name": "Creative Collage",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #fef2f2 0%, #ecfdf5 50%, #eff6ff 100%)",
        "description": "Scrapbook collage style with layered elements and tape effects",
        "design_instructions": (
            "Color palette: background #f5f0eb (paper), tape-yellow #fef08a, pin-red #ef4444, shadow #d4cfc7, text #292524, accent #7c3aed.\n"
            "Typography: Caveat for handwritten labels (700), Inter for body (400). Labels 1.2rem, headings 2.5rem, body 15px.\n"
            "Layout: max-width 1100px, scattered/overlapping card layout, elements at slight random rotations, Masonry-like grid.\n"
            "Effects: cards appear pinned (red dot + subtle shadow), tape strips on images (yellow rectangles at angles), paper texture backgrounds, slight rotation transforms (-2deg to 3deg).\n"
            "Sections: paper-like backgrounds, content in layered card stacks. Polaroid-style image frames. Handwritten annotation labels.\n"
            "Buttons: tape-style (yellow background, slight rotation), dark text, or standard rounded-md #7c3aed fill, 14px 28px.\n"
            "Mood: crafty, personal, scrapbook-authentic. Think indie brand or personal creative portfolio."
        ),
        "suitable_for": ["portfolio", "indie_brand", "photography", "crafts"],
    },
    "creative_comic": {
        "name": "Creative Comic Book",
        "category": "Creative & Playful",
        "preview_gradient": "linear-gradient(135deg, #fbbf24 0%, #ef4444 50%, #3b82f6 100%)",
        "description": "Full comic book aesthetic with panels, halftones, and action text",
        "design_instructions": (
            "Color palette: yellow #fbbf24, red #ef4444, blue #3b82f6, black #000000, white #ffffff, cream #fef3c7.\n"
            "Typography: Bangers for all headings (display, 400), Comic Neue for body (400). Headings 4rem, body 16px. Action words extra-large.\n"
            "Layout: comic panel grid (CSS grid with thick black borders), max-width 1200px, alternating panel sizes, full-width splash panels.\n"
            "Effects: halftone dot pattern overlays (radial-gradient), thick 4px black borders on everything, action word starbursts (clip-path), speed lines as CSS background.\n"
            "Sections: each section is a comic panel row with thick black borders. Hero is a full-width splash panel. Testimonials in speech bubbles.\n"
            "Buttons: starburst shape or thick-bordered rectangle, bright fill, black 4px border, bold text, 4px 4px 0 black shadow, uppercase.\n"
            "Mood: action-packed, entertaining, visually explosive. Think Marvel web meets product page."
        ),
        "suitable_for": ["gaming", "entertainment", "kids_brand", "comic_shop"],
    },

    # =========================================================================
    # LANDING PAGE (10)
    # =========================================================================
    "landing_saas": {
        "name": "SaaS Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #0f172a 0%, #6366f1 100%)",
        "description": "High-converting SaaS landing page with social proof and CTAs",
        "design_instructions": (
            "Color palette: dark #0f172a, primary #6366f1, background #ffffff, surface #f8fafc, text #1e293b, success #22c55e, muted #94a3b8.\n"
            "Typography: Inter for everything, hero heading 600 at 3.5rem, sub-heading 400 at 1.25rem muted, body 400 at 16px.\n"
            "Layout: centered hero with headline+subline+CTA+product screenshot, logo strip, 3-column feature grid, pricing cards, testimonials, FAQ accordion, final CTA.\n"
            "Effects: product screenshot with perspective transform and shadow, floating UI mockups, animated stat counters, smooth scroll to sections.\n"
            "Sections: white base, hero has subtle gradient or illustration bg, logo strip in #f8fafc, features on white, pricing on #f8fafc, dark CTA section at bottom.\n"
            "Buttons: primary #6366f1 fill white text 12px radius 16px 32px large, secondary outline. Hero CTA is extra-large with arrow icon.\n"
            "Mood: conversion-focused, polished, trustworthy-modern. Think Notion, Linear, or Loom landing pages."
        ),
        "suitable_for": ["saas", "b2b_software", "productivity_tool", "platform"],
    },
    "landing_app": {
        "name": "App Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #7c3aed 0%, #ec4899 100%)",
        "description": "Mobile app showcase with phone mockups and app store badges",
        "design_instructions": (
            "Color palette: gradient #7c3aed to #ec4899, background #ffffff, surface #faf5ff, text #1e1b4b, muted #7c7c8a.\n"
            "Typography: Poppins for headings (700), Inter for body (400). Hero heading 3rem, body 16px, app feature labels 600.\n"
            "Layout: hero with phone mockup (centered or right-aligned), app store badges below CTA, feature showcase with phone screenshots, testimonials, download CTA.\n"
            "Effects: phone mockup with gradient background, floating UI elements around phone, feature screenshots in phone frames, parallax phone scroll.\n"
            "Sections: gradient hero, white features with phone mockups alternating left/right, light purple (#faf5ff) testimonials, gradient bottom CTA.\n"
            "Buttons: gradient fill (purple to pink), white text, rounded-full, 16px 36px. App store badges styled as buttons. Hero CTA prominent.\n"
            "Mood: mobile-first, modern, app-store-ready. Think Headspace or Calm app landing pages."
        ),
        "suitable_for": ["mobile_app", "fitness_app", "social_app", "utility_app"],
    },
    "landing_product": {
        "name": "Product Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #f97316 0%, #ef4444 100%)",
        "description": "Physical product showcase with hero product shot and benefits",
        "design_instructions": (
            "Color palette: primary #f97316, secondary #ef4444, background #ffffff, surface #fff7ed, text #1c1917, muted #78716c.\n"
            "Typography: Sora for headings (700), Inter for body (400). Product name 3.5rem, benefits 1.2rem, body 16px.\n"
            "Layout: hero with large product image (centered) + headline + CTA, benefit icons row, before/after comparison, social proof strip, specs grid, FAQ, buy CTA.\n"
            "Effects: product image with clean shadow, zoom on hover, benefit icons with colored circular backgrounds, comparison slider, animated scroll reveals.\n"
            "Sections: white hero with product focus, light orange (#fff7ed) benefits, white specs, orange gradient CTA section. Clean product photography focus.\n"
            "Buttons: #f97316 fill, white text, rounded-lg, 16px 36px, large hero CTA with price badge. Buy now button prominent.\n"
            "Mood: product-focused, persuasive, clean commerce. Think Apple product page or Dyson."
        ),
        "suitable_for": ["physical_product", "electronics", "beauty_product", "food_product"],
    },
    "landing_waitlist": {
        "name": "Waitlist Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #7c3aed 100%)",
        "description": "Pre-launch waitlist page with email capture and teaser content",
        "design_instructions": (
            "Color palette: dark #0f172a, surface #1e293b, accent #7c3aed, text #e2e8f0, muted #94a3b8, input-bg #334155.\n"
            "Typography: Plus Jakarta Sans for headings (800), Inter for body (400). Hero headline 4rem, subline 1.3rem muted, body 16px.\n"
            "Layout: single-page, centered hero (100vh) with headline + subline + email input + submit button, below-fold: 3 teaser feature cards, social proof count, footer.\n"
            "Effects: animated gradient background (slow color shift), floating particle dots, email input with glow focus state, counter animation for waitlist number.\n"
            "Sections: dark full-screen hero with email capture as the focus, subtle teaser content below. Minimal -- the email form is the star.\n"
            "Buttons: #7c3aed fill, white text, connected to email input (inline form), 14px 28px. Hover brightens. Pulse animation on CTA.\n"
            "Mood: exclusive, anticipation-building, minimal-dark. Think Product Hunt upcoming or beta signup pages."
        ),
        "suitable_for": ["pre_launch", "beta", "startup", "new_product"],
    },
    "landing_event": {
        "name": "Event Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #7c2d12 0%, #dc2626 50%, #f59e0b 100%)",
        "description": "Event promotion with countdown, speakers, and ticket CTAs",
        "design_instructions": (
            "Color palette: dark #1c1917, red #dc2626, amber #f59e0b, background #ffffff, surface #fef2f2, text #1c1917, light-text #fef2f2.\n"
            "Typography: Poppins for headings (800), Inter for body (400). Event name 4rem, date/location 1.5rem, body 16px.\n"
            "Layout: hero with event name + date + location + countdown timer + register CTA, speaker grid (photo cards), schedule timeline, sponsors logo strip, register CTA.\n"
            "Effects: countdown timer with flip-card animation, speaker cards with hover bio reveal, timeline with vertical line and dots, gradient text for event name.\n"
            "Sections: dark/gradient hero with countdown, white speaker section, light-red (#fef2f2) schedule, sponsors on white, dark final CTA.\n"
            "Buttons: red #dc2626 fill, white text, rounded-lg, 16px 36px, large register buttons. Amber variant for secondary. Urgency styling.\n"
            "Mood: exciting, urgent, event-energy. Think tech conference or summit landing page."
        ),
        "suitable_for": ["conference", "summit", "workshop", "festival"],
    },
    "landing_course": {
        "name": "Course Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)",
        "description": "Online course sales page with curriculum, instructor, and enrollment",
        "design_instructions": (
            "Color palette: primary #1e40af, accent #3b82f6, background #ffffff, surface #eff6ff, text #1e293b, success #16a34a, muted #64748b.\n"
            "Typography: Inter for headings (700), Inter for body (400). Course title 3rem, module titles 1.3rem, body 16px.\n"
            "Layout: hero with course title + description + enroll CTA + video preview, what-you-learn checklist, curriculum accordion, instructor bio with photo, testimonials, pricing, FAQ, enroll CTA.\n"
            "Effects: video thumbnail with play button overlay, checkmark animations on benefits, accordion expand animation, progress bar visual, trust badges.\n"
            "Sections: white hero with blue accents, light blue (#eff6ff) curriculum section, white testimonials, blue gradient pricing section, white FAQ.\n"
            "Buttons: #1e40af fill, white text, rounded-lg, 16px 32px. Enroll CTA is extra-large with price. Green guarantee badge.\n"
            "Mood: educational, credible, value-communicating. Think Udemy course page or cohort-based course."
        ),
        "suitable_for": ["online_course", "bootcamp", "workshop", "coaching"],
    },
    "landing_agency": {
        "name": "Agency Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #18181b 0%, #27272a 100%)",
        "description": "Creative agency portfolio with case studies and contact form",
        "design_instructions": (
            "Color palette: dark #18181b, surface #27272a, white #ffffff, accent #f59e0b, text-dark #18181b, text-light #fafafa.\n"
            "Typography: Clash Display or Space Grotesk for headings (700), Inter for body (400). Agency name 5rem, section heads 2.5rem, body 16px.\n"
            "Layout: dark hero with massive agency name + tagline, horizontal scrolling case study showcase, services grid, team photos, client logos, contact form.\n"
            "Effects: large text hero with subtle motion, case study cards with image hover reveal, smooth horizontal scroll, cursor follower effect description.\n"
            "Sections: dark hero, white case studies section, dark services section, white team section, dark contact. Alternating dark/light for rhythm.\n"
            "Buttons: amber #f59e0b fill, dark text, 0px radius, uppercase, 14px 32px. Contact CTA is prominent. Arrow icons on links.\n"
            "Mood: cool, confident, portfolio-driven. Think award-winning agency like Instrument or Basic."
        ),
        "suitable_for": ["creative_agency", "design_studio", "marketing_agency", "branding"],
    },
    "landing_nonprofit": {
        "name": "Nonprofit Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #065f46 0%, #10b981 100%)",
        "description": "Nonprofit with impact story, donate CTA, and mission focus",
        "design_instructions": (
            "Color palette: primary #065f46, accent #10b981, warm #f59e0b, background #ffffff, surface #ecfdf5, text #1e293b, muted #6b7280.\n"
            "Typography: Merriweather for headings (serif, 700), Source Sans 3 for body (400). Headline 3rem, impact stats 4rem, body 16px.\n"
            "Layout: emotional hero image with overlay text + donate CTA, impact stats row (big numbers), mission statement, program cards, stories/testimonials, partners, donate CTA.\n"
            "Effects: hero image with dark overlay for text readability, animated counting stats, emotional imagery, progress bars for goals, heart/hand icons.\n"
            "Sections: full-width hero image, white mission section, green (#ecfdf5) programs, white stories, green footer. Warm amber for donate buttons.\n"
            "Buttons: donate button #f59e0b fill dark text rounded-full 16px 36px (warm, inviting). Secondary: green #10b981 fill. Large, accessible.\n"
            "Mood: compassionate, impactful, story-driven. Think charity:water or Khan Academy."
        ),
        "suitable_for": ["nonprofit", "charity", "ngo", "social_enterprise"],
    },
    "landing_launch": {
        "name": "Product Launch Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #000000 0%, #1a1a2e 50%, #e94560 100%)",
        "description": "Dramatic product launch with reveal moment and pre-order CTA",
        "design_instructions": (
            "Color palette: black #000000, dark #1a1a2e, red #e94560, white #ffffff, text #e4e4e7, muted #888888.\n"
            "Typography: Sora for headings (800), Inter for body (400). Product name 5rem, tagline 1.5rem, body 16px. Dramatic sizing.\n"
            "Layout: full-screen hero with product name reveal animation + launch date + pre-order CTA, product features with large images, specs comparison, pre-order section.\n"
            "Effects: cinematic hero with fade-in text sequence, large product images with parallax, feature reveals on scroll, dramatic lighting effects via gradients.\n"
            "Sections: all dark backgrounds, hero is pure black with red accent, feature sections have subtle gradient backgrounds, specs on dark surface.\n"
            "Buttons: red #e94560 fill, white text, 8px radius, 16px 40px. Pre-order CTA is extra-large. Hover glow effect.\n"
            "Mood: cinematic, anticipation, premium launch. Think Tesla Cybertruck or Apple keynote reveal."
        ),
        "suitable_for": ["product_launch", "tech_hardware", "automotive", "premium_product"],
    },
    "landing_membership": {
        "name": "Membership Landing Page",
        "category": "Landing Page",
        "preview_gradient": "linear-gradient(135deg, #4338ca 0%, #7c3aed 50%, #a855f7 100%)",
        "description": "Membership/subscription page with tiers, benefits, and community",
        "design_instructions": (
            "Color palette: primary #4338ca, secondary #7c3aed, light-purple #a855f7, background #ffffff, surface #f5f3ff, text #1e1b4b, muted #6b7280.\n"
            "Typography: Plus Jakarta Sans for headings (700), Inter for body (400). Plan names 2rem, prices 3.5rem, body 16px.\n"
            "Layout: hero with value proposition + CTA, benefits checklist (3 columns), pricing tier cards (3 side-by-side, middle highlighted), member testimonials, community preview, FAQ, join CTA.\n"
            "Effects: pricing card hover lift, popular tier with gradient border and 'Most Popular' badge, checkmark animations, member count ticker.\n"
            "Sections: white hero, light purple (#f5f3ff) benefits, white pricing, purple gradient testimonials (dark), white FAQ, purple gradient final CTA.\n"
            "Buttons: gradient (indigo to purple) fill, white text, rounded-lg, 16px 32px. Popular tier button is larger. Free trial variant outlined.\n"
            "Mood: community-focused, value-clear, conversion-optimized. Think Patreon or membership community landing."
        ),
        "suitable_for": ["membership", "subscription", "community", "premium_content"],
    },
}


# =============================================================================
# Helper functions
# =============================================================================


def get_template(key: str) -> dict | None:
    """Return a single template dict by its key, or None if not found."""
    return TEMPLATES.get(key)


def get_template_design_prompt(key: str) -> str:
    """Return formatted design instructions ready to inject into an LLM prompt.

    Returns an empty string when the key is not found.
    """
    template = TEMPLATES.get(key)
    if not template:
        return ""

    return (
        f"TEMPLATE: {template['name']}\n"
        f"CATEGORY: {template['category']}\n"
        f"DESCRIPTION: {template['description']}\n"
        f"DESIGN INSTRUCTIONS:\n{template['design_instructions']}\n"
        f"SUITABLE FOR: {', '.join(template['suitable_for'])}"
    )


def get_all_templates_summary() -> list[dict]:
    """Return a lightweight list suitable for frontend template-picker display."""
    return [
        {
            "key": key,
            "name": t["name"],
            "category": t["category"],
            "preview_gradient": t["preview_gradient"],
            "description": t["description"],
            "suitable_for": t["suitable_for"],
        }
        for key, t in TEMPLATES.items()
    ]


def get_templates_by_category() -> dict[str, list]:
    """Return templates grouped by category.

    Structure::

        {
            "Minimal": [{"key": "minimal_dark", ...}, ...],
            "Bold & Modern": [...],
            ...
        }
    """
    grouped: dict[str, list] = {}
    for key, t in TEMPLATES.items():
        category = t["category"]
        entry = {
            "key": key,
            "name": t["name"],
            "preview_gradient": t["preview_gradient"],
            "description": t["description"],
            "suitable_for": t["suitable_for"],
        }
        grouped.setdefault(category, []).append(entry)
    return grouped
