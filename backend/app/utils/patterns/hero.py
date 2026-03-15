"""Hero section pattern templates."""

PATTERNS = {
    "hero_split": """hero_split pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section">
  <!-- Giant faded decorative number -->
  <span class="bg-number" style="font-family: var(--font-heading)">01</span>

  <div class="container-wide hero-split-grid">
    <div>
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
    <div class="hero-image-wrapper">
      <img src="{{IMG:hero image query from plan}}" alt="Hero" class="img-cover">
    </div>
  </div>
  NOTE: ALL text must stay in the first column. Image in second column. On mobile: single column, image stacks on top. ALWAYS include the giant faded number and section label — these are NOT optional.""",
    "hero_center": """hero_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush"> (edge-to-edge, no gap)
  If plan has image_query for hero, use background image variant:
  <div class="hero-bg-cover" style="background-image: url('{{IMG:hero image query from plan}}');">
    <div class="hero-overlay hero-overlay-center"></div>
    <div class="container-wide hero-center-content">
      <!-- Section label -->
      <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>

      <h1 class="hero-heading text-light">Headline</h1>
      <p class="hero-subtitle text-light">Subheadline</p>
      <div class="hero-ctas hero-ctas-center">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary">Secondary CTA</a>
      </div>
      <p class="trust-line text-light">Trust line</p>
    </div>
  </div>
  If plan has NO image_query for hero (rare), use solid background variant:
  <div class="container-wide hero-center-content hero-center-padded">
    <h1 class="hero-heading">Headline</h1>
    <p class="hero-subtitle">Subheadline</p>
    <div class="hero-ctas hero-ctas-center">
      <a href="#" class="btn-primary">Primary CTA</a>
      <a href="#" class="btn-secondary">Secondary CTA</a>
    </div>
    <p class="trust-line">Trust line</p>
  </div>
  NOTE: Overlay uses a gradient (NOT flat bg-black/70) — image must be clearly visible. Max 50% opacity.""",
    "hero_full_image": """hero_full_image pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush"> (negative margin pulls hero behind navbar — NO gap)
  <div class="hero-bg-cover" style="background-image: url('{{IMG:background hero scene query from plan}}');">
    <div class="hero-overlay hero-overlay-left"></div>
    <div class="container hero-full-overlay">
      <!-- Section label -->
      <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT</span>

      <h1 class="hero-heading text-light">Headline</h1>
      <p class="hero-subtitle text-light">Subheadline</p>
      <div class="hero-ctas">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary">Secondary CTA</a>
      </div>
      <p class="trust-line text-light">Trust line</p>
    </div>
  </div>
  NOTE: Overlay uses a LEFT-TO-RIGHT gradient — text readable on left, image visible on right. NEVER use flat bg-black/70. The hero-section-flush on section and hero-bg-cover ensure hero extends behind fixed navbar with no gap. Text is LEFT-ALIGNED (not centered) for editorial impact.""",
    "hero_minimal": """hero_minimal pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section">
  <!-- Giant faded decorative text -->
  <span class="bg-number bg-number-center" style="font-family: var(--font-heading)">BRAND</span>

  <div class="container-narrow hero-center-content hero-center-padded">
    <h1 class="hero-heading hero-heading-xl">Big Bold Headline</h1>
    <p class="hero-subtitle">One concise line of supporting text</p>
    <div class="hero-ctas hero-ctas-center">
      <a href="#" class="btn-primary">Single CTA</a>
    </div>
  </div>""",
    "hero_video_bg": """hero_video_bg pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-flush"> (edge-to-edge hero, no gap)
  <div class="hero-animated-bg" style="background: linear-gradient(-45deg, var(--primary), var(--secondary), var(--accent, var(--primary)), var(--primary)); background-size: 400% 400%; animation: gradientShift 8s ease infinite;">
    <!-- Giant faded decorative number -->
    <span class="bg-number text-light" style="font-family: var(--font-heading)">01</span>

    <div class="container hero-center-content">
      <!-- Section label -->
      <span class="section-label text-light"><span class="label-line"></span>LABEL TEXT<span class="label-line"></span></span>

      <h1 class="hero-heading text-light">Headline</h1>
      <p class="hero-subtitle text-light">Subheadline</p>
      <div class="hero-ctas hero-ctas-center">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary">Secondary CTA</a>
      </div>
      <p class="trust-line text-light">Trust line</p>
    </div>
  </div>""",
    "hero_product_mockup": """hero_product_mockup pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-compact">
  <!-- Giant faded decorative number -->
  <span class="bg-number" style="font-family: var(--font-heading)">01</span>

  <div class="container-narrow hero-center-content">
    <h1 class="hero-heading">Headline (keep SHORT — max 8 words)</h1>
    <p class="hero-subtitle">Subheadline</p>
    <div class="hero-ctas hero-ctas-center">
      <a href="#" class="btn-primary">Primary CTA</a>
      <a href="#" class="btn-secondary">Secondary CTA</a>
    </div>
    <p class="trust-line">Trust line</p>
  </div>
  <div class="container hero-mockup-wrapper">
    <img src="{{IMG:mockup laptop dashboard product interface}}" alt="Product screenshot" class="img-cover hero-mockup-image">
  </div>
  NOTE: Text constrained to container-narrow, image wider at container. Headline MUST be short (max 8 words).""",
    "hero_mockup_center": """hero_mockup_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="hero-section hero-section-compact">
  <!-- Giant faded decorative number -->
  <span class="bg-number" style="font-family: var(--font-heading)">01</span>

  <div class="container-narrow hero-center-content">
    <h1 class="hero-heading">Headline (keep SHORT — max 8 words)</h1>
    <p class="hero-subtitle">Subheadline</p>
    <div class="hero-ctas hero-ctas-center">
      <a href="#" class="btn-primary">Primary CTA</a>
      <a href="#" class="btn-secondary">Secondary CTA</a>
    </div>
    <p class="trust-line">Trust line</p>
  </div>
  <div class="container-narrow browser-frame">
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
  <!-- Giant faded decorative number -->
  <span class="bg-number" style="font-family: var(--font-heading)">01</span>

  <div class="container-wide hero-split-grid hero-split-asymmetric">
    <div>
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
    <div class="hero-image-wrapper">
      <img src="{{IMG:hero image query from plan}}" alt="Hero visual" class="img-cover">
      <div class="floating-card" style="background: var(--bg-surface); border-radius: var(--radius);">
        <i class="fa-solid fa-chart-line floating-card-icon" style="color: var(--accent);"></i>
        <span class="floating-card-text">Key metric or highlight</span>
      </div>
    </div>
  </div>
  NOTE: Floating card is hidden on mobile. Text 55%, image 45%. ALWAYS include the giant faded number and section label.""",

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
          <a href="#" class="btn-secondary">Secondary CTA</a>
        </div>
      </div>
    </div>
  </div>
  NOTE: JS moves data-parallax layers at different speeds on scroll. The speed value (0.3, 0.5, 0.8) controls how fast each layer scrolls relative to page scroll. Creates a cinematic depth effect.""",

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
  NOTE: The hero content is sticky — as user scrolls, the hero stays fixed while content below scrolls over it. Creates a dramatic reveal/morph effect. The image scales slightly on scroll via JS transform. Very premium, editorial feel.""",
}
