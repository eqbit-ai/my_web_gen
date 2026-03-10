"""
Component variant definitions for the layout composer.
Each component type has multiple layout variants with design instructions
that guide the LLM to generate specific visual layouts.
"""

COMPONENT_VARIANTS = {
    "navbar": {
        "name": "Navigation Bar",
        "variants": {
            "navbar_standard": {
                "name": "Standard Navbar",
                "description": "Logo left, links center/right, clean horizontal layout",
                "layout_instruction": "Horizontal navbar with logo on the left, navigation links in the center or right, and optional CTA button. Fixed to top, white/transparent background with backdrop blur. Include mobile hamburger toggle.",
                "suitable_for": ["all"],
            },
            "navbar_centered": {
                "name": "Centered Logo Navbar",
                "description": "Logo centered with links split on both sides",
                "layout_instruction": "Logo centered in the navbar with half of navigation links on the left and half on the right. Elegant, balanced layout. Fixed to top with subtle border-bottom.",
                "suitable_for": ["elegant", "luxury", "fashion"],
            },
            "navbar_transparent": {
                "name": "Transparent Overlay Navbar",
                "description": "Transparent navbar overlaying the hero section",
                "layout_instruction": "Transparent navbar positioned absolute over the hero. White text, logo left, links right. On scroll, transitions to solid white background with dark text. Include mobile menu.",
                "suitable_for": ["creative", "photography", "hotel"],
            },
            "navbar_sidebar": {
                "name": "Side Navigation",
                "description": "Vertical sidebar navigation (desktop), hamburger (mobile)",
                "layout_instruction": "Fixed vertical sidebar navigation on the left (240px wide) with logo at top, nav links stacked vertically, social icons at bottom. On mobile, collapses to hamburger menu. Main content offset to the right.",
                "suitable_for": ["portfolio", "creative", "agency"],
            },
            "navbar_mega_menu": {
                "name": "Mega Menu Navbar",
                "description": "Mega dropdown with multi-column categories and featured items",
                "layout_instruction": "Horizontal navbar with logo left and top-level links right. Hovering a link reveals a full-width mega dropdown panel with 3-4 columns of categorized sub-links, optional featured image or promo card in the last column. Dropdown has subtle shadow and smooth fade-in. Include mobile hamburger that expands to an accordion-style menu.",
                "suitable_for": ["ecommerce", "corporate", "enterprise", "saas"],
            },
            "navbar_topbar": {
                "name": "Topbar + Main Nav",
                "description": "Thin top bar with contact/social info plus main navigation below",
                "layout_instruction": "Two-row navigation. Top bar: thin strip (32-36px) with dark background showing phone number, email on the left and social media icon links on the right. Main navbar below: logo left, navigation links center/right, CTA button far right. Main navbar is sticky on scroll while top bar scrolls away. Include mobile hamburger for main nav.",
                "suitable_for": ["corporate", "local", "service", "consulting"],
            },
        },
    },
    "hero": {
        "name": "Hero Section",
        "variants": {
            "hero_centered": {
                "name": "Centered Hero",
                "description": "Large centered heading with subtitle and CTA buttons",
                "layout_instruction": "Full-width hero section with vertically and horizontally centered content. Large bold heading (4-5rem), subtitle below, two CTA buttons side by side (primary filled + secondary outline). Subtle gradient or solid background. Min-height 100vh.",
                "suitable_for": ["saas", "corporate", "startup"],
            },
            "hero_split": {
                "name": "Split Hero",
                "description": "Text on left, image/illustration on right",
                "layout_instruction": "Two-column grid hero (55/45 split). Left column: heading, subtitle, description paragraph, CTA buttons. Right column: large product image or illustration. Vertically centered content. On mobile: stack vertically, text first.",
                "suitable_for": ["saas", "app", "product"],
            },
            "hero_image_bg": {
                "name": "Background Image Hero",
                "description": "Full-screen background image with overlay text",
                "layout_instruction": "Full-viewport hero with background image (use img tag, not CSS background). Dark gradient overlay (rgba(0,0,0,0.5)). White centered text: large heading, subtitle, single CTA button. The image should be in an absolutely positioned container behind the text.",
                "suitable_for": ["restaurant", "hotel", "travel", "real_estate"],
            },
            "hero_minimal": {
                "name": "Minimal Text Hero",
                "description": "Clean text-only hero with large typography",
                "layout_instruction": "Minimal hero with just text. Very large heading (5-6rem), small tagline above in uppercase, short subtitle below. Single CTA link (not button). Lots of whitespace. Left-aligned or centered. Subtle background color.",
                "suitable_for": ["portfolio", "agency", "minimal"],
            },
            "hero_video": {
                "name": "Video Hero",
                "description": "Background video with overlay content",
                "layout_instruction": "Full-viewport hero with a placeholder video element (or animated gradient as fallback). Dark overlay with white centered text. Large heading, subtitle, CTA button. Play/pause button in corner. On mobile: replace video with static image.",
                "suitable_for": ["creative", "agency", "entertainment"],
            },
            "hero_cards": {
                "name": "Hero with Feature Cards",
                "description": "Hero text above, feature preview cards below",
                "layout_instruction": "Two-part hero: top area with centered heading, subtitle, CTA. Bottom area overlapping with the next section, showing 3 feature/stat cards in a horizontal row. Cards have slight elevation (box-shadow) and overlap the hero/next section boundary.",
                "suitable_for": ["saas", "corporate", "consulting"],
            },
            "hero_gradient": {
                "name": "Animated Gradient Hero",
                "description": "Animated gradient background with centered text and smooth color transitions",
                "layout_instruction": "Full-viewport hero with an animated CSS gradient background that slowly shifts between 3-4 brand colors using a @keyframes animation on background-position. Centered white text: large bold heading (4-5rem), short subtitle, and a CTA button with frosted-glass effect (backdrop-filter: blur). Min-height 100vh. Include subtle noise texture overlay for depth.",
                "suitable_for": ["creative", "startup", "saas", "app"],
            },
            "hero_parallax": {
                "name": "Parallax Hero",
                "description": "Parallax scrolling background image with layered depth effect",
                "layout_instruction": "Full-viewport hero with a large background image inside a container using CSS transform for parallax scrolling effect. Dark overlay gradient from bottom. Content positioned in the lower-third: large heading, subtitle, and CTA button, all white text. Include JS IntersectionObserver or scroll listener to translate the background image at a slower rate than the page scroll. On mobile: disable parallax and show static image.",
                "suitable_for": ["travel", "hotel", "photography", "real_estate", "restaurant"],
            },
            "hero_slider": {
                "name": "Image Slider Hero",
                "description": "Image slider/carousel with text overlays and navigation controls",
                "layout_instruction": "Full-viewport hero with 3-4 slides, each containing a background image with dark overlay and unique heading + subtitle text. Navigation arrows on left/right edges and dot indicators at the bottom. Auto-advance every 5 seconds with JS. Smooth crossfade or slide transition between slides. Each slide can have its own CTA button. On mobile: maintain swipe hint with partial arrow visibility.",
                "suitable_for": ["hotel", "real_estate", "travel", "ecommerce", "restaurant"],
            },
        },
    },
    "features": {
        "name": "Features Section",
        "variants": {
            "features_grid": {
                "name": "Icon Grid",
                "description": "3-4 column grid of feature cards with icons",
                "layout_instruction": "Section with centered heading and subtitle. Below: 3 or 4 column grid of feature cards. Each card has an icon (use a colored circle with emoji or SVG), heading, and short description. Cards have subtle border or shadow on hover. Equal height cards.",
                "suitable_for": ["all"],
            },
            "features_alternating": {
                "name": "Alternating Rows",
                "description": "Features alternate between image-left and image-right",
                "layout_instruction": "Section with centered heading. Below: alternating two-column rows. Odd rows: image left, text right. Even rows: text left, image right. Each row has a heading, description paragraph, and optional bullet points. Generous spacing between rows.",
                "suitable_for": ["saas", "product", "app"],
            },
            "features_cards": {
                "name": "Elevated Cards",
                "description": "Feature cards with hover effects and prominent shadows",
                "layout_instruction": "Section with heading. 3-column grid of elevated cards. Each card has a colored accent bar on top (4px), icon, heading, description, and a 'Learn more' link. Cards have shadow-md, on hover lift up with shadow-lg. Background slightly different from page.",
                "suitable_for": ["corporate", "consulting", "saas"],
            },
            "features_list": {
                "name": "Feature List",
                "description": "Vertical list with icons and descriptions",
                "layout_instruction": "Two-column layout: left column has heading, subtitle, and CTA. Right column has a vertical list of 4-5 features, each with a checkmark/icon, feature name, and one-line description. Clean, compact layout.",
                "suitable_for": ["saas", "pricing", "comparison"],
            },
            "features_tabs": {
                "name": "Tabbed Features",
                "description": "Tab navigation revealing different feature details",
                "layout_instruction": "Section with heading. Horizontal tab buttons (3-4 tabs). Below: content area that changes per tab. Each tab shows an image/screenshot on one side and feature description on the other. Include tab switching via JS click handlers.",
                "suitable_for": ["saas", "product", "dashboard"],
            },
            "features_icon_left": {
                "name": "Icon Left Feature Rows",
                "description": "Icon on left, text on right, stacked rows for easy scanning",
                "layout_instruction": "Section with centered heading and subtitle. Below: 4-6 vertically stacked rows, each row is a flex container with a large icon or icon circle on the left (64px), and a text block on the right containing a bold feature name and a 1-2 line description. Rows separated by subtle borders or generous spacing. Max-width 720px, centered on page. On mobile: icon shrinks slightly but layout stays horizontal.",
                "suitable_for": ["saas", "service", "consulting", "corporate"],
            },
            "features_numbered": {
                "name": "Numbered Steps",
                "description": "Numbered steps with a connecting vertical line for process flows",
                "layout_instruction": "Section with centered heading. Below: 4-5 steps arranged vertically with a thin connecting line running down the left side. Each step has a numbered circle (1, 2, 3...) on the line, and to its right a heading and description paragraph. The connecting line uses a primary/accent color. Alternate steps can slightly indent for visual rhythm. On mobile: maintain the vertical timeline layout with smaller circles.",
                "suitable_for": ["saas", "service", "onboarding", "process", "consulting"],
            },
            "features_hover_cards": {
                "name": "Hover Reveal Cards",
                "description": "Cards with hover animations that reveal additional content",
                "layout_instruction": "Section with heading. 3-column grid of cards. Default state shows an icon and feature title on a clean card. On hover: card background transitions to primary/accent color, text turns white, and a hidden description paragraph slides up into view with a smooth CSS transition (transform + opacity). Cards have equal height and rounded corners. Include subtle scale(1.02) on hover for lift effect.",
                "suitable_for": ["creative", "startup", "agency", "saas"],
            },
        },
    },
    "testimonials": {
        "name": "Testimonials",
        "variants": {
            "testimonials_cards": {
                "name": "Testimonial Cards",
                "description": "Grid of testimonial cards with quotes and avatars",
                "layout_instruction": "Section with heading. 3-column grid of testimonial cards. Each card has: opening quote mark (large, decorative), quote text, horizontal divider, avatar image (rounded), name, and job title. Cards have subtle background and rounded corners.",
                "suitable_for": ["all"],
            },
            "testimonials_single": {
                "name": "Single Spotlight",
                "description": "One large featured testimonial with navigation",
                "layout_instruction": "Large centered testimonial display. Big quote marks, large quote text (1.25rem), centered. Below: avatar, name, company. Navigation dots or prev/next arrows below. Can be static (just one) or include JS for cycling through testimonials.",
                "suitable_for": ["corporate", "consulting", "agency"],
            },
            "testimonials_masonry": {
                "name": "Masonry Grid",
                "description": "Pinterest-style varying height testimonial cards",
                "layout_instruction": "Section with heading. CSS columns (3 columns) masonry layout. Various length testimonial cards with different background colors (using design system accent/surface colors). Each has quote, name, role. Some cards longer, some shorter, creating a dynamic visual.",
                "suitable_for": ["saas", "creative", "startup"],
            },
            "testimonials_slider": {
                "name": "Testimonial Slider",
                "description": "Auto-rotating testimonial slider with dot navigation",
                "layout_instruction": "Section with centered heading. A single large testimonial display area showing one testimonial at a time: large decorative quote marks, quote text (1.2rem), avatar, name, role, and company. Below: dot indicators for 4-5 testimonials. Auto-rotates every 4 seconds with a smooth fade transition via JS. Left/right arrow buttons on the sides for manual navigation. Pause auto-rotation on hover.",
                "suitable_for": ["corporate", "saas", "service", "consulting"],
            },
            "testimonials_video": {
                "name": "Video Testimonials",
                "description": "Video testimonial cards with play buttons and thumbnail previews",
                "layout_instruction": "Section with heading and subtitle. 3-column grid of video testimonial cards. Each card has a thumbnail image with a centered play button overlay (circular, semi-transparent with a triangle icon). Below the thumbnail: person's name, role, and a short pull-quote. Clicking the play button can trigger a modal overlay with a placeholder video element. Cards have rounded corners and subtle shadow on hover.",
                "suitable_for": ["agency", "saas", "enterprise", "consulting"],
            },
        },
    },
    "pricing": {
        "name": "Pricing Section",
        "variants": {
            "pricing_three_col": {
                "name": "Three Column Pricing",
                "description": "Three pricing tiers with featured middle option",
                "layout_instruction": "Section with heading and subtitle. Three pricing cards side by side. Middle card is 'featured' (slightly larger, colored border or background, 'Popular' badge). Each card: plan name, price with period, feature list with checkmarks, CTA button. Featured card has primary-colored button, others have outline buttons.",
                "suitable_for": ["saas", "app", "service"],
            },
            "pricing_toggle": {
                "name": "Monthly/Annual Toggle",
                "description": "Pricing cards with monthly/annual price toggle",
                "layout_instruction": "Section with heading. Toggle switch for Monthly/Annual (with 'Save 20%' badge on annual). Three pricing cards below. When toggle is switched (JS), prices update. Include transition animation on price change. Featured middle card with highlight.",
                "suitable_for": ["saas", "subscription", "app"],
            },
            "pricing_comparison": {
                "name": "Feature Comparison Table",
                "description": "Full comparison table with checkmarks per plan",
                "layout_instruction": "Section with heading. Responsive table with plan names as column headers and features as rows. Check/cross icons per feature per plan. Sticky header row. On mobile: horizontal scroll or accordion per plan. Clean grid lines.",
                "suitable_for": ["enterprise", "saas", "comparison"],
            },
            "pricing_single": {
                "name": "Single Plan Spotlight",
                "description": "Single featured plan with detailed feature list and prominent CTA",
                "layout_instruction": "Section with centered heading and subtitle. A single large pricing card centered on the page (max-width 560px). Card contains: plan name, large price with billing period, a horizontal divider, then a detailed checklist of 6-8 included features with checkmark icons. Prominent full-width CTA button at the bottom. Card has elevated shadow and optional accent border on top. Below the card: a short note like 'No credit card required' or 'Cancel anytime'.",
                "suitable_for": ["startup", "saas", "freelance", "minimal"],
            },
            "pricing_cards": {
                "name": "Horizontal Scrollable Pricing",
                "description": "Horizontally scrollable pricing cards for many plan options",
                "layout_instruction": "Section with heading and subtitle. A horizontally scrollable container (overflow-x: auto with scroll-snap) showing 4-5 pricing cards. Each card has: plan name, price, 4-5 key features, and a CTA button. Cards use scroll-snap-align: start for smooth snapping. Show partial next card to hint at scrollability. On desktop: can show 3 fully visible cards. Each card has a subtle border, and the recommended plan has an accent-colored top border and a 'Recommended' badge.",
                "suitable_for": ["saas", "ecommerce", "service", "enterprise"],
            },
        },
    },
    "cta": {
        "name": "Call to Action",
        "variants": {
            "cta_banner": {
                "name": "Full-Width Banner CTA",
                "description": "Bold colored banner with heading and button",
                "layout_instruction": "Full-width section with primary color background (or gradient). Centered white text: bold heading, short subtitle, large CTA button (white bg, primary text). Generous vertical padding. Optional subtle pattern or texture overlay.",
                "suitable_for": ["all"],
            },
            "cta_split": {
                "name": "Split CTA",
                "description": "Text on one side, form or button on the other",
                "layout_instruction": "Two-column layout within a rounded card or distinct section. Left: heading, description. Right: email input + submit button (newsletter style) or a prominent CTA button. Subtle background color difference. Rounded corners on the container.",
                "suitable_for": ["saas", "newsletter", "blog"],
            },
            "cta_card": {
                "name": "Floating Card CTA",
                "description": "Centered card with CTA standing out from background",
                "layout_instruction": "A prominent card centered on the page with shadow-xl. Inside: heading, short text, large CTA button. Card has a different background from the section (e.g., section is gray, card is white or dark). Optional decorative elements (dots, circles) in background.",
                "suitable_for": ["startup", "saas", "creative"],
            },
            "cta_sticky_bar": {
                "name": "Sticky Bottom Bar CTA",
                "description": "Fixed bottom bar with CTA that stays visible while scrolling",
                "layout_instruction": "A thin fixed bar (56-64px tall) anchored to the bottom of the viewport with a high z-index. Contains a short one-line message on the left and a prominent CTA button on the right, all within a centered max-width container. Background is solid (white or dark) with a top shadow for separation. Include a small close/dismiss button (X icon) on the far right. On mobile: stack text above button or use a single full-width button. Use JS to show the bar only after scrolling past the hero section.",
                "suitable_for": ["saas", "ecommerce", "app", "startup"],
            },
            "cta_fullscreen": {
                "name": "Fullscreen CTA",
                "description": "Fullscreen CTA section with background image and strong visual impact",
                "layout_instruction": "Full-viewport section (min-height: 100vh) with a background image and dark gradient overlay. All content centered vertically and horizontally: large bold heading (3-4rem) in white, a short subtitle, and an oversized CTA button with high contrast. The background image sits in an absolute container with object-fit: cover. Add a subtle scroll-down indicator (animated chevron) at the bottom. On mobile: reduce heading size but maintain full-viewport height.",
                "suitable_for": ["creative", "agency", "travel", "hotel", "entertainment"],
            },
        },
    },
    "contact": {
        "name": "Contact Section",
        "variants": {
            "contact_form": {
                "name": "Contact Form",
                "description": "Form with name, email, message fields",
                "layout_instruction": "Two-column layout. Left: heading, description, contact info (phone, email, address) with icons. Right: form with Name, Email, Subject, Message (textarea) fields and Submit button. Clean input styling with focus states. Form validation visual hints.",
                "suitable_for": ["all"],
            },
            "contact_minimal": {
                "name": "Minimal Contact",
                "description": "Clean centered contact info with social links",
                "layout_instruction": "Centered section with heading, short text, email link (large, prominent), phone number, and social media icon links in a row. Minimal, no form. Clean whitespace-heavy design.",
                "suitable_for": ["portfolio", "creative", "minimal"],
            },
            "contact_map": {
                "name": "Contact with Map",
                "description": "Contact info beside an embedded map",
                "layout_instruction": "Two-column layout. Left: contact form (name, email, message, submit). Right: placeholder for a map (gray box with 'Map' text or a static image). Below both: address, phone, email in a horizontal bar. On mobile: stack vertically.",
                "suitable_for": ["local", "restaurant", "office"],
            },
            "contact_split_card": {
                "name": "Split Card Contact",
                "description": "Contact form on left, contact info card on right in a unified container",
                "layout_instruction": "A single large card container with rounded corners and shadow, split into two halves. Left half (white/light background): contact form with Name, Email, Phone, and Message fields stacked vertically, plus a Submit button. Right half (primary/dark accent background): contact info with icon + text rows for address, phone, email, and business hours. The right side uses white/light text. On mobile: stack vertically with form on top and info card below.",
                "suitable_for": ["corporate", "consulting", "service", "local"],
            },
            "contact_chat": {
                "name": "Chat-Style Contact",
                "description": "Chat-style interface for inquiries with message bubbles",
                "layout_instruction": "Section with heading. A centered chat-window-style container (max-width 560px) with a mock chat interface: a top bar with an avatar and 'Online' status indicator, a message area showing 2-3 pre-filled bot message bubbles (e.g., 'Hi! How can we help?'), and a bottom input bar with a text field and send button. Message bubbles alternate left (bot, gray) and right (user, primary color). Purely decorative — the input field can link to a real contact form or mailto. Rounded corners and subtle shadow on the container.",
                "suitable_for": ["startup", "saas", "app", "creative"],
            },
        },
    },
    "footer": {
        "name": "Footer",
        "variants": {
            "footer_simple": {
                "name": "Simple Footer",
                "description": "Single row with copyright and links",
                "layout_instruction": "Dark background footer. Single row with copyright text on the left and 3-4 links (Privacy, Terms, Contact) on the right. Subtle top border. Compact vertical padding.",
                "suitable_for": ["minimal", "blog", "portfolio"],
            },
            "footer_mega": {
                "name": "Mega Footer",
                "description": "Multi-column footer with links, newsletter, social",
                "layout_instruction": "Dark background, multi-column footer (4 columns). Column 1: logo, short description, social icons. Columns 2-3: link lists with headings (Company, Services, Resources). Column 4: newsletter signup (email input + button). Below: horizontal divider, copyright row. On mobile: 2x2 grid then stack.",
                "suitable_for": ["corporate", "saas", "ecommerce"],
            },
            "footer_centered": {
                "name": "Centered Footer",
                "description": "All content centered with stacked elements",
                "layout_instruction": "Dark or light footer with all content centered. Logo on top, navigation links in a horizontal row, social media icons row, then copyright text. Everything stacked vertically with generous spacing. Clean and symmetric.",
                "suitable_for": ["creative", "portfolio", "agency"],
            },
            "footer_minimal": {
                "name": "Minimal Single-Line Footer",
                "description": "Single compact line with logo, links, and copyright",
                "layout_instruction": "A compact single-line footer with minimal vertical padding (py-4). Logo or brand name on the far left, 3-4 inline navigation links in the center, and copyright text on the far right. All on one horizontal row using flexbox with justify-between. Light border-top as separator. On mobile: stack into two rows — logo and links on top, copyright below, all centered.",
                "suitable_for": ["minimal", "portfolio", "blog", "startup"],
            },
            "footer_dark_gradient": {
                "name": "Dark Gradient Footer",
                "description": "Dark gradient background with 4 columns and newsletter signup",
                "layout_instruction": "Footer with a dark gradient background (e.g., from gray-900 to black). Four-column layout: Column 1 has logo, a short company description, and social media icons. Columns 2-3 have categorized link lists with bold headings (Products, Company, Resources). Column 4 has a newsletter section with heading, short text, email input, and subscribe button. Below the columns: a full-width divider line, then a bottom bar with copyright left and legal links (Privacy, Terms) right. On mobile: columns stack into a single column.",
                "suitable_for": ["corporate", "saas", "enterprise", "ecommerce"],
            },
        },
    },
    "faq": {
        "name": "FAQ Section",
        "variants": {
            "faq_accordion": {
                "name": "Accordion FAQ",
                "description": "Click-to-expand question/answer pairs",
                "layout_instruction": "Section with heading. Vertical list of FAQ items. Each item has a question (clickable) with a +/- or chevron icon on the right. Clicking toggles the answer visibility (JS). Clean borders between items. Max-width 800px, centered. Include JS for toggle functionality.",
                "suitable_for": ["all"],
            },
            "faq_two_col": {
                "name": "Two Column FAQ",
                "description": "Questions and answers in a two-column grid",
                "layout_instruction": "Section with heading and subtitle. Two-column grid of FAQ cards. Each card has a question (bold) and answer paragraph below it. Cards have subtle background or border. 4-6 FAQ items total. On mobile: single column.",
                "suitable_for": ["saas", "service", "product"],
            },
            "faq_search": {
                "name": "Searchable FAQ",
                "description": "FAQ section with a search bar to filter questions in real-time",
                "layout_instruction": "Section with centered heading. Below the heading: a search input field (max-width 480px, centered) with a magnifying glass icon and placeholder text 'Search questions...'. Below the search bar: a vertical list of 6-8 FAQ items, each with a bold question and answer paragraph. Include JS that filters the FAQ items in real-time as the user types, hiding non-matching items with a smooth transition. Show a 'No results found' message when nothing matches. Clean card or bordered styling for each item.",
                "suitable_for": ["saas", "service", "enterprise", "product"],
            },
            "faq_categories": {
                "name": "Categorized FAQ with Tabs",
                "description": "FAQ organized into categories with tab navigation",
                "layout_instruction": "Section with centered heading. Below: horizontal tab buttons for 3-4 categories (e.g., General, Billing, Technical, Account). Below the tabs: FAQ items for the active category displayed as accordion-style expandable items. Clicking a tab shows only that category's questions via JS (hide/show). Active tab has primary color underline or filled background. Max-width 800px, centered. On mobile: tabs become horizontally scrollable pills.",
                "suitable_for": ["saas", "enterprise", "service", "ecommerce"],
            },
        },
    },
    "stats": {
        "name": "Statistics / Metrics",
        "variants": {
            "stats_bar": {
                "name": "Stats Bar",
                "description": "Horizontal row of key metrics",
                "layout_instruction": "Full-width section (or band) with 4 stats in a row. Each stat has a large number (bold, 2-3rem), label below. Background color contrasts with adjacent sections. Can have a subtle divider between each stat. On mobile: 2x2 grid.",
                "suitable_for": ["corporate", "consulting", "startup"],
            },
            "stats_cards": {
                "name": "Stats Cards",
                "description": "Individual metric cards with icons",
                "layout_instruction": "4-column grid of stat cards. Each card has an icon (in a colored circle), large number, label text, and optional small description. Cards have subtle shadow. Optional counting animation on scroll via JS IntersectionObserver.",
                "suitable_for": ["saas", "dashboard", "corporate"],
            },
            "stats_animated": {
                "name": "Animated Counter Stats",
                "description": "Numbers that count up on scroll with decorative icons",
                "layout_instruction": "Full-width section with a contrasting background (primary color or dark). 4 stats in a horizontal row, each with a decorative icon above, a large number (2.5-3rem, bold, white) that counts up from 0 to the target value when scrolled into view, and a label below. Include JS using IntersectionObserver to trigger the counting animation once. Numbers should increment smoothly over 2 seconds using requestAnimationFrame. Support suffixes like '+', '%', 'K'. On mobile: 2x2 grid.",
                "suitable_for": ["corporate", "startup", "saas", "agency"],
            },
            "stats_progress": {
                "name": "Progress Bar Stats",
                "description": "Horizontal progress bars with labels and percentage values",
                "layout_instruction": "Section with heading and optional subtitle. Below: 4-6 vertically stacked progress bar items, each with a label on the left, percentage value on the right, and a horizontal progress bar below that fills to the given percentage. The bar track is a light gray, and the filled portion uses the primary/accent color. Include JS with IntersectionObserver to animate the bar width from 0% to the target value when scrolled into view. Max-width 680px, centered. On mobile: maintain full-width bars.",
                "suitable_for": ["portfolio", "agency", "consulting", "skills"],
            },
        },
    },
    "gallery": {
        "name": "Gallery / Portfolio",
        "variants": {
            "gallery_grid": {
                "name": "Image Grid",
                "description": "Responsive grid of images with hover effects",
                "layout_instruction": "Section with heading. Responsive grid (3-4 columns) of images. Each image has a hover overlay showing a title and category. Images are equal height using object-fit: cover. Filter buttons above the grid (All, Category 1, Category 2, etc.) for JS-based filtering.",
                "suitable_for": ["portfolio", "photography", "agency"],
            },
            "gallery_masonry": {
                "name": "Masonry Gallery",
                "description": "Pinterest-style varying height image gallery",
                "layout_instruction": "CSS columns masonry gallery (3 columns). Images of varying aspect ratios. Hover effect: slight scale + shadow increase. Optional lightbox-style click (JS). Heading above. On mobile: 2 columns.",
                "suitable_for": ["photography", "creative", "art"],
            },
            "gallery_lightbox": {
                "name": "Lightbox Gallery",
                "description": "Grid gallery with lightbox popup overlay on click",
                "layout_instruction": "Section with heading. A 3-column grid of image thumbnails with rounded corners and subtle shadow. Clicking any image opens a fullscreen lightbox overlay: dark semi-transparent backdrop, the image displayed large and centered, a close button (X) in the top-right corner, and prev/next arrow buttons on the sides. Include JS for lightbox open/close, keyboard navigation (Escape to close, arrow keys), and prev/next cycling. On mobile: 2-column grid, lightbox goes full-width.",
                "suitable_for": ["photography", "portfolio", "creative", "real_estate"],
            },
            "gallery_carousel": {
                "name": "Horizontal Carousel Gallery",
                "description": "Horizontally scrollable image carousel with snap scrolling",
                "layout_instruction": "Section with heading. A horizontally scrollable container (overflow-x: auto) showing images in a single row. Each image is a card with rounded corners, consistent height (320px), and varying widths based on aspect ratio. Use scroll-snap-type: x mandatory and scroll-snap-align: start for smooth snapping. Show partial next image to hint scrollability. Optional left/right navigation arrow buttons positioned at the vertical center of the carousel. On mobile: full-width cards with horizontal swipe.",
                "suitable_for": ["photography", "travel", "portfolio", "ecommerce", "real_estate"],
            },
        },
    },
    "team": {
        "name": "Team Section",
        "variants": {
            "team_grid": {
                "name": "Team Grid",
                "description": "Grid of team member cards with photos",
                "layout_instruction": "Section with heading. 3-4 column grid of team cards. Each card: circular avatar image, name (bold), role (muted), short bio (1-2 lines), social media icon links. Cards have subtle hover effect. On mobile: 2 columns.",
                "suitable_for": ["all"],
            },
            "team_carousel": {
                "name": "Team Carousel",
                "description": "Horizontally scrolling team member cards",
                "layout_instruction": "Section with heading. Horizontal scroll container showing team cards. Each card: large photo, name, role, short bio. Show 3 cards at a time with partial 4th visible to indicate scrollability. Scroll with CSS overflow-x: auto + snap points. Nav arrows optional.",
                "suitable_for": ["agency", "startup", "corporate"],
            },
            "team_minimal": {
                "name": "Minimal Team Cards",
                "description": "Small compact cards with photo, name, and role only",
                "layout_instruction": "Section with centered heading and short subtitle. A 4-column grid of compact team cards. Each card contains only: a square photo (160x160px, rounded-lg, object-fit: cover), the person's name in bold below, and their role in muted smaller text. No bio, no social links — purely visual and clean. Cards have no border or shadow, just clean spacing. On hover: subtle scale(1.03) and shadow appears. On mobile: 2-column grid.",
                "suitable_for": ["minimal", "startup", "portfolio", "creative"],
            },
            "team_detailed": {
                "name": "Detailed Team Cards",
                "description": "Large cards with photo, bio, social links, and skill tags",
                "layout_instruction": "Section with heading. 2-column grid of large horizontal team cards. Each card is a flex row: left side has a large portrait photo (200x240px, rounded, object-fit: cover), right side has the person's name (large bold), role (accent color), a 2-3 sentence bio paragraph, a row of skill/expertise tags (small pills with background color), and social media icon links (LinkedIn, Twitter, etc.). Cards have a subtle border and rounded corners. On mobile: cards stack with photo on top and info below, single column.",
                "suitable_for": ["agency", "consulting", "corporate", "enterprise"],
            },
        },
    },
}


def get_all_components_summary() -> list[dict]:
    """Return a summary of all component types and their variants for the frontend."""
    result = []
    for comp_key, comp in COMPONENT_VARIANTS.items():
        variants = []
        for var_key, var in comp["variants"].items():
            variants.append({
                "key": var_key,
                "name": var["name"],
                "description": var["description"],
            })
        result.append({
            "key": comp_key,
            "name": comp["name"],
            "variants": variants,
        })
    return result


def get_variant_detail(component_type: str, variant_key: str) -> dict | None:
    """Get full details of a specific variant."""
    comp = COMPONENT_VARIANTS.get(component_type)
    if not comp:
        return None
    variant = comp["variants"].get(variant_key)
    if not variant:
        return None
    return {
        "component_type": component_type,
        "component_name": comp["name"],
        **variant,
    }


def get_variant_prompt(component_type: str, variant_key: str) -> str | None:
    """Get the layout instruction for a variant, formatted for LLM prompts."""
    detail = get_variant_detail(component_type, variant_key)
    if not detail:
        return None
    return (
        f"COMPONENT: {detail['component_name']} — {detail['name']}\n"
        f"DESCRIPTION: {detail['description']}\n"
        f"LAYOUT INSTRUCTION: {detail['layout_instruction']}\n"
    )


def get_component_types() -> list[str]:
    """Return list of component type keys."""
    return list(COMPONENT_VARIANTS.keys())
