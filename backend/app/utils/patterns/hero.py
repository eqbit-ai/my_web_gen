"""Hero section pattern templates — PREMIUM quality, Envato-level design."""

PATTERNS = {
    "hero_split": """hero_split pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section">

  <!-- Decorative background elements for depth -->
  <div class="hero-bg-accent" style="position:absolute;top:0;right:0;width:50%;height:100%;background:linear-gradient(135deg, color-mix(in srgb, var(--primary) 6%, transparent), color-mix(in srgb, var(--accent) 4%, transparent));z-index:0;"></div>

  <div class="container-wide hero-split-grid" style="position:relative;z-index:1;">
    <div class="hero-text-col">
      <!-- Section label -->
      <span class="section-label"><span class="label-line"></span>LABEL TEXT</span>

      <h1 class="hero-heading">Headline</h1>
      <p class="hero-subtitle">Subheadline</p>
      <div class="hero-ctas">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary">Secondary CTA</a>
      </div>
      <!-- Trust indicators row -->
      <div class="hero-trust-row" style="display:flex;align-items:center;gap:1.5rem;margin-top:2rem;flex-wrap:wrap;">
        <div class="hero-trust-item" style="display:flex;align-items:center;gap:0.5rem;">
          <i class="fa-solid fa-circle-check" style="color:var(--accent);"></i>
          <span style="font-size:0.85rem;color:var(--text-muted);">Trust point 1</span>
        </div>
        <div class="hero-trust-item" style="display:flex;align-items:center;gap:0.5rem;">
          <i class="fa-solid fa-circle-check" style="color:var(--accent);"></i>
          <span style="font-size:0.85rem;color:var(--text-muted);">Trust point 2</span>
        </div>
        <div class="hero-trust-item" style="display:flex;align-items:center;gap:0.5rem;">
          <i class="fa-solid fa-circle-check" style="color:var(--accent);"></i>
          <span style="font-size:0.85rem;color:var(--text-muted);">Trust point 3</span>
        </div>
      </div>
    </div>
    <div class="hero-image-wrapper" style="position:relative;">
      <!-- Decorative accent behind image -->
      <div style="position:absolute;top:-1rem;right:-1rem;width:100%;height:100%;border-radius:var(--radius);border:2px solid color-mix(in srgb, var(--primary) 20%, transparent);z-index:0;"></div>
      <img src="{{IMG:hero image query from plan}}" alt="Hero" class="img-cover" style="position:relative;z-index:1;">
      <!-- Floating stat card overlapping the image -->
      <div class="floating-card" style="position:absolute;bottom:-1.5rem;left:-1.5rem;background:var(--bg-surface);border-radius:var(--radius);padding:1rem 1.25rem;box-shadow:var(--shadow-hover);display:flex;align-items:center;gap:0.75rem;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);z-index:10;">
        <i class="fa-solid fa-chart-line" style="color:var(--accent);font-size:1.25rem;"></i>
        <div>
          <span style="font-weight:700;font-size:1.1rem;display:block;">500+</span>
          <span style="font-size:0.75rem;color:var(--text-muted);">Key metric</span>
        </div>
      </div>
    </div>
  </div>
  NOTE: The hero-trust-row replaces the old plain trust-line — it shows 3 checkmark trust points inline. The decorative accent border behind the image and floating stat card create depth. Customize the trust points, floating card metric, and icon to match the business. On mobile: single column, image stacks below text. Floating card is hidden on mobile via CSS.""",

    "hero_center": """hero_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush"> (edge-to-edge, no gap)
  If plan has image_query for hero, use background image variant:
  <div class="hero-bg-cover" style="background-image: url('{{IMG:hero image query from plan}}');">
    <div class="hero-overlay hero-overlay-center"></div>
    <div class="container-wide hero-center-content" style="position:relative;z-index:2;">
      <!-- Section label -->
      <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>

      <h1 class="hero-heading text-light">Headline</h1>
      <p class="hero-subtitle text-light">Subheadline</p>
      <div class="hero-ctas hero-ctas-center">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary-light">Secondary CTA</a>
      </div>
      <!-- Mini stat counters in hero -->
      <div style="display:flex;justify-content:center;gap:3rem;margin-top:3rem;flex-wrap:wrap;">
        <div style="text-align:center;">
          <span style="font-size:1.75rem;font-weight:700;color:white;display:block;">500+</span>
          <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.7);">Clients</span>
        </div>
        <div style="text-align:center;">
          <span style="font-size:1.75rem;font-weight:700;color:white;display:block;">98%</span>
          <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.7);">Satisfaction</span>
        </div>
        <div style="text-align:center;">
          <span style="font-size:1.75rem;font-weight:700;color:white;display:block;">15+</span>
          <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.7);">Years</span>
        </div>
      </div>
    </div>
  </div>
  NOTE: ALWAYS use the background image variant — hero_center MUST have an image_query and background image. NEVER output a hero without a background image. The mini stat counters add social proof and visual weight. Customize the numbers and labels to match the business. Overlay uses a gradient (NOT flat bg-black/70) — image must be clearly visible. Max 50% opacity.""",

    "hero_full_image": """hero_full_image pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush"> (negative margin pulls hero behind navbar — NO gap)
  <div class="hero-bg-cover" style="background-image: url('{{IMG:background hero scene query from plan}}');">
    <div class="hero-overlay hero-overlay-left"></div>
    <div class="container hero-full-overlay" style="position:relative;z-index:2;">
      <!-- Section label -->
      <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT</span>

      <h1 class="hero-heading text-light">Headline</h1>
      <p class="hero-subtitle text-light" style="max-width:32rem;">Subheadline</p>
      <div class="hero-ctas">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary-light">Secondary CTA</a>
      </div>
      <!-- Vertical stat strip -->
      <div style="display:flex;gap:2.5rem;margin-top:2.5rem;padding-top:1.5rem;border-top:1px solid rgba(255,255,255,0.15);flex-wrap:wrap;">
        <div>
          <span style="font-size:1.5rem;font-weight:700;color:white;">12+</span>
          <span style="font-size:0.75rem;color:rgba(255,255,255,0.6);display:block;text-transform:uppercase;letter-spacing:0.1em;">Years</span>
        </div>
        <div>
          <span style="font-size:1.5rem;font-weight:700;color:white;">500+</span>
          <span style="font-size:0.75rem;color:rgba(255,255,255,0.6);display:block;text-transform:uppercase;letter-spacing:0.1em;">Projects</span>
        </div>
        <div>
          <span style="font-size:1.5rem;font-weight:700;color:white;">98%</span>
          <span style="font-size:0.75rem;color:rgba(255,255,255,0.6);display:block;text-transform:uppercase;letter-spacing:0.1em;">Satisfaction</span>
        </div>
      </div>
    </div>
  </div>
  NOTE: Overlay uses a LEFT-TO-RIGHT gradient — text readable on left, image visible on right. NEVER use flat bg-black/70. The stat strip at the bottom of the hero adds credibility and visual weight. Text is LEFT-ALIGNED (not centered) for editorial impact. Customize stat numbers/labels to match the business.""",

    "hero_minimal": """hero_minimal pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section">

  <div class="container-narrow hero-center-content hero-center-padded">
    <span class="section-label"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>
    <h1 class="hero-heading hero-heading-xl">Big Bold Headline</h1>
    <p class="hero-subtitle">One concise line of supporting text</p>
    <div class="hero-ctas hero-ctas-center">
      <a href="#" class="btn-primary">Single CTA</a>
    </div>
    <!-- Partner logo row for social proof -->
    <div style="margin-top:3rem;padding-top:2rem;border-top:1px solid color-mix(in srgb, var(--text) 8%, transparent);">
      <p style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.15em;color:var(--text-muted);margin-bottom:1rem;">Trusted by leading companies</p>
      <div class="logo-cloud" style="opacity:0.4;">
        <span class="logo-text">Company 1</span>
        <span class="logo-text">Company 2</span>
        <span class="logo-text">Company 3</span>
        <span class="logo-text">Company 4</span>
      </div>
    </div>
  </div>""",

    "hero_video_bg": """hero_video_bg pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush"> (edge-to-edge hero, no gap)
  <div class="hero-animated-bg" style="background: linear-gradient(-45deg, var(--primary), var(--secondary), var(--accent, var(--primary)), var(--primary)); background-size: 400% 400%; animation: gradientShift 8s ease infinite;">

    <div class="container hero-center-content" style="position:relative;z-index:1;">
      <!-- Section label -->
      <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>

      <h1 class="hero-heading text-light">Headline</h1>
      <p class="hero-subtitle text-light">Subheadline</p>
      <div class="hero-ctas hero-ctas-center">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary-light">Secondary CTA</a>
      </div>
      <p class="trust-line text-light">Trust line</p>
    </div>
  </div>""",

    "hero_product_mockup": """hero_product_mockup pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-compact">

  <div class="container-narrow hero-center-content">
    <span class="section-label"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>
    <h1 class="hero-heading">Headline (keep SHORT — max 8 words)</h1>
    <p class="hero-subtitle">Subheadline</p>
    <div class="hero-ctas hero-ctas-center">
      <a href="#" class="btn-primary">Primary CTA</a>
      <a href="#" class="btn-secondary">Secondary CTA</a>
    </div>
    <p class="trust-line">Trust line</p>
  </div>
  <div class="container hero-mockup-wrapper" style="margin-top:3rem;position:relative;">
    <!-- Glow effect behind mockup -->
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:80%;height:60%;background:radial-gradient(ellipse, color-mix(in srgb, var(--primary) 15%, transparent), transparent 70%);z-index:0;filter:blur(40px);"></div>
    <img src="{{IMG:mockup laptop dashboard product interface}}" alt="Product screenshot" class="img-cover hero-mockup-image" style="position:relative;z-index:1;">
  </div>
  NOTE: Text constrained to container-narrow, image wider at container. The glow effect behind the mockup adds premium depth. Headline MUST be short (max 8 words).""",

    "hero_mockup_center": """hero_mockup_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-compact">

  <div class="container-narrow hero-center-content">
    <span class="section-label"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>
    <h1 class="hero-heading">Headline (keep SHORT — max 8 words)</h1>
    <p class="hero-subtitle">Subheadline</p>
    <div class="hero-ctas hero-ctas-center">
      <a href="#" class="btn-primary">Primary CTA</a>
      <a href="#" class="btn-secondary">Secondary CTA</a>
    </div>
    <p class="trust-line">Trust line</p>
  </div>
  <div class="container-narrow browser-frame" style="margin-top:2.5rem;">
    <div class="browser-dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <img src="{{IMG:mockup laptop dashboard product interface}}" alt="Product interface" class="hero-mockup-image">
  </div>
  NOTE: Browser frame with colored dots. Use subtle rgba backgrounds for dark themes.""",

    "hero_asymmetric": """hero_asymmetric pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section">

  <div class="container-wide hero-split-grid hero-split-asymmetric" style="position:relative;z-index:1;">
    <div class="hero-text-col">
      <!-- Section label -->
      <span class="section-label"><span class="label-line"></span>LABEL TEXT</span>

      <h1 class="hero-heading">Headline</h1>
      <p class="hero-subtitle">Subheadline</p>
      <div class="hero-ctas">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary">Secondary CTA</a>
      </div>
      <p class="trust-line">Trust line</p>
    </div>
    <div class="hero-image-wrapper" style="position:relative;">
      <!-- Main hero image with rounded corners -->
      <img src="{{IMG:hero image query from plan}}" alt="Hero visual" class="img-cover" style="border-radius:var(--radius);">
      <!-- Floating metric card 1 — top right -->
      <div class="floating-card" style="position:absolute;top:-1rem;right:-1rem;background:var(--bg-surface);border-radius:var(--radius);padding:1rem 1.25rem;box-shadow:var(--shadow-hover);display:flex;align-items:center;gap:0.75rem;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);z-index:10;">
        <i class="fa-solid fa-chart-line" style="color:var(--accent);font-size:1.1rem;"></i>
        <div>
          <span style="font-weight:700;font-size:1rem;display:block;">200%</span>
          <span style="font-size:0.7rem;color:var(--text-muted);">Growth Rate</span>
        </div>
      </div>
      <!-- Floating metric card 2 — bottom left -->
      <div class="floating-card" style="position:absolute;bottom:-1rem;left:-1rem;background:var(--bg-surface);border-radius:var(--radius);padding:1rem 1.25rem;box-shadow:var(--shadow-hover);display:flex;align-items:center;gap:0.75rem;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);z-index:10;">
        <i class="fa-solid fa-star" style="color:var(--accent);font-size:1.1rem;"></i>
        <div>
          <span style="font-weight:700;font-size:1rem;display:block;">4.9/5</span>
          <span style="font-size:0.7rem;color:var(--text-muted);">Client Rating</span>
        </div>
      </div>
    </div>
  </div>
  NOTE: TWO floating cards — one top-right, one bottom-left — create a dynamic, editorial asymmetric feel. Both hidden on mobile via CSS. Text 55%, image 45%. Customize the floating card metrics and icons to match the business.""",

    "hero_parallax_layers": """hero_parallax_layers pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush">
  <div style="position: relative; min-height: 100vh; overflow: hidden;">
    <!-- Background layer (moves slowest) -->
    <div data-parallax="0.3" style="position: absolute; inset: 0; background-image: url('{{IMG:hero dramatic landscape cityscape}}'); background-size: cover; background-position: center; transform: translateZ(0);"></div>
    <!-- Mid layer: gradient overlay -->
    <div data-parallax="0.5" style="position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 50%, transparent 100%);"></div>
    <!-- Foreground: text content (moves fastest) -->
    <div data-parallax="0.8" style="position: relative; z-index: 2; display: flex; align-items: center; min-height: 100vh;">
      <div class="container">
        <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT</span>
        <h1 class="hero-heading text-light" style="max-width: 700px;">Headline</h1>
        <p class="hero-subtitle text-light" style="max-width: 500px;">Subheadline</p>
        <div class="hero-ctas">
          <a href="#" class="btn-primary">Primary CTA</a>
          <a href="#" class="btn-secondary-light">Secondary CTA</a>
        </div>
      </div>
    </div>
  </div>
  NOTE: JS moves data-parallax layers at different speeds on scroll. Creates a cinematic depth effect.""",

    "hero_text_reveal": """hero_text_reveal pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section">
  <div class="container" style="min-height: 80vh; display: flex; flex-direction: column; justify-content: center;">
    <span class="section-label"><span class="label-line"></span>LABEL TEXT</span>
    <!-- Each word wrapped in span for staggered reveal animation -->
    <h1 class="hero-heading hero-heading-xl split-text" data-splitting style="max-width: 900px; overflow: hidden;">
      Each Word Reveals Dramatically
    </h1>
    <p class="hero-subtitle" style="max-width: 550px; opacity: 0; animation: fadeInUp 0.8s ease forwards 1.2s;">Subheadline text that fades in after heading completes.</p>
    <div class="hero-ctas" style="opacity: 0; animation: fadeInUp 0.8s ease forwards 1.5s;">
      <a href="#" class="btn-primary">Primary CTA</a>
    </div>
  </div>
  NOTE: Uses Splitting.js via data-splitting attribute. Each character/word animates in with staggered delay. The subtitle and CTA fade in after the heading reveal completes. Add @keyframes fadeInUp in the style block.""",

    "hero_scroll_morph": """hero_scroll_morph pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush">
  <div style="position: relative; min-height: 100vh;">
    <div class="hero-bg-cover" style="background-image: url('{{IMG:hero dramatic wide scene}}'); position: sticky; top: 0; height: 100vh;">
      <div class="hero-overlay hero-overlay-center"></div>
      <div class="container hero-center-content" style="position: relative; z-index: 2;">
        <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>
        <h1 class="hero-heading text-light hero-heading-xl">Headline</h1>
        <p class="hero-subtitle text-light">Subheadline</p>
        <div class="hero-ctas hero-ctas-center">
          <a href="#" class="btn-primary">Primary CTA</a>
        </div>
      </div>
    </div>
  </div>
  NOTE: The hero content is sticky — as user scrolls, the hero stays fixed while content below scrolls over it. Creates a dramatic reveal/morph effect.""",
}
