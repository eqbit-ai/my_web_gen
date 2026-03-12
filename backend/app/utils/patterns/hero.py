"""Hero section pattern templates."""

PATTERNS = {
    "hero_split": """hero_split pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="py-16 md:py-24 relative overflow-hidden">
  <!-- Giant faded decorative number -->
  <span class="absolute right-[5%] top-[10%] text-[clamp(120px,22vw,320px)] font-bold opacity-[0.04] pointer-events-none select-none leading-none" style="font-family: var(--font-heading)">01</span>

  <div class="max-w-[1400px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12 items-center relative z-10">
    <div>
      <!-- Section label -->
      <span class="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[var(--accent)] mb-6"><span class="w-10 h-[2px] bg-[var(--accent)]"></span>LABEL TEXT</span>

      <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-none mb-6 text-[var(--text)]">Headline</h1>
      <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-8 max-w-xl">Subheadline</p>
      <div class="flex flex-wrap gap-4 mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-[var(--text-muted)]">Trust line</p>
    </div>
    <div class="overflow-hidden rounded-xl">
      <img src="{{IMG:hero image query from plan}}" alt="Hero" class="w-full h-auto max-h-[500px] rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]">
    </div>
  </div>
  NOTE: ALL text must stay in the first column. Image in second column. On mobile: single column, image first (use md:order-none order-first on image div). ALWAYS include the giant faded number and section label — these are NOT optional.""",
    "hero_center": """hero_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="relative -mt-[80px]"> (edge-to-edge, no gap)
  If plan has image_query for hero, use background image variant:
  <div class="relative min-h-[85vh] bg-cover bg-center bg-no-repeat flex items-center pt-[80px]" style="background-image: url('{{IMG:hero image query from plan}}');">
    <div class="absolute inset-0 bg-gradient-to-b from-black/50 via-black/40 to-black/60"></div>
    <div class="relative max-w-[1400px] mx-auto px-6 text-center">
      <!-- Section label -->
      <span class="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-white/80 mb-6 mx-auto"><span class="w-10 h-[2px] bg-white/60"></span>LABEL TEXT<span class="w-10 h-[2px] bg-white/60"></span></span>

      <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-none mb-6 text-white">Headline</h1>
      <p class="text-base md:text-lg text-white/85 leading-relaxed mb-8 max-w-xl mx-auto">Subheadline</p>
      <div class="flex flex-wrap gap-4 justify-center mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-white/70">Trust line</p>
    </div>
  </div>
  If plan has NO image_query for hero (rare), use solid background variant:
  <div class="max-w-[1400px] mx-auto px-6 text-center py-20 md:py-28 pt-[100px]">
    <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-none mb-6 text-[var(--text)]">Headline</h1>
    <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-8 max-w-xl mx-auto">Subheadline</p>
    <div class="flex flex-wrap gap-4 justify-center mb-6">
      <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
      <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
    </div>
    <p class="text-sm text-[var(--text-muted)]">Trust line</p>
  </div>
  NOTE: Overlay uses a gradient (NOT flat bg-black/70) — image must be clearly visible. Max 50% opacity.""",
    "hero_full_image": """hero_full_image pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="relative -mt-[80px]"> (negative margin pulls hero behind navbar — NO gap)
  <div class="relative min-h-[85vh] bg-cover bg-center bg-no-repeat flex items-center pt-[80px]" style="background-image: url('{{IMG:background hero scene query from plan}}');">
    <div class="absolute inset-0 bg-gradient-to-r from-black/60 via-black/40 to-transparent"></div>
    <div class="relative max-w-[1200px] mx-auto px-6">
      <!-- Section label -->
      <span class="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-white/80 mb-6"><span class="w-10 h-[2px] bg-white/60"></span>LABEL TEXT</span>

      <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-none mb-6 text-white max-w-3xl">Headline</h1>
      <p class="text-base md:text-lg text-white/85 leading-relaxed mb-8 max-w-xl">Subheadline</p>
      <div class="flex flex-wrap gap-4 mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-white/70">Trust line</p>
    </div>
  </div>
  NOTE: Overlay uses a LEFT-TO-RIGHT gradient — text readable on left, image visible on right. NEVER use flat bg-black/70. The -mt-[80px] on section and pt-[80px] on inner div ensure hero extends behind fixed navbar with no gap. Text is LEFT-ALIGNED (not centered) for editorial impact.""",
    "hero_minimal": """hero_minimal pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="py-16 md:py-24 relative overflow-hidden">
  <!-- Giant faded decorative text -->
  <span class="absolute left-[50%] top-[50%] -translate-x-1/2 -translate-y-1/2 text-[clamp(150px,25vw,400px)] font-bold opacity-[0.03] pointer-events-none select-none leading-none" style="font-family: var(--font-heading)">BRAND</span>

  <div class="max-w-[800px] mx-auto px-6 text-center py-20 md:py-28 relative z-10">
    <h1 class="text-6xl md:text-7xl lg:text-8xl font-bold leading-none mb-6 text-[var(--text)]">Big Bold Headline</h1>
    <p class="text-lg md:text-xl text-[var(--text-muted)] leading-relaxed mb-8 max-w-lg mx-auto">One concise line of supporting text</p>
    <div class="flex justify-center">
      <a href="#" class="BTN_PRIMARY_CLASSES">Single CTA</a>
    </div>
  </div>""",
    "hero_video_bg": """hero_video_bg pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="relative -mt-[80px]"> (edge-to-edge hero, no gap)
  <div class="min-h-[85vh] flex items-center relative pt-[80px]" style="background: linear-gradient(-45deg, var(--primary), var(--secondary), var(--accent, var(--primary)), var(--primary)); background-size: 400% 400%; animation: gradientShift 8s ease infinite;">
    <!-- Giant faded decorative number -->
    <span class="absolute right-[8%] top-[15%] text-[clamp(120px,22vw,320px)] font-bold opacity-[0.08] pointer-events-none select-none leading-none text-white" style="font-family: var(--font-heading)">01</span>

    <div class="max-w-[1200px] mx-auto px-6 text-center relative z-10">
      <!-- Section label -->
      <span class="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-white/80 mb-6 mx-auto"><span class="w-10 h-[2px] bg-white/60"></span>LABEL TEXT<span class="w-10 h-[2px] bg-white/60"></span></span>

      <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-none mb-6 text-white">Headline</h1>
      <p class="text-base md:text-lg text-white/85 leading-relaxed mb-8 max-w-xl mx-auto">Subheadline</p>
      <div class="flex flex-wrap gap-4 justify-center mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-white/70">Trust line</p>
    </div>
  </div>""",
    "hero_product_mockup": """hero_product_mockup pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="pt-8 md:pt-16 pb-16 md:pb-20 relative overflow-hidden">
  <!-- Giant faded decorative number -->
  <span class="absolute right-[5%] top-[10%] text-[clamp(100px,18vw,280px)] font-bold opacity-[0.04] pointer-events-none select-none leading-none" style="font-family: var(--font-heading)">01</span>

  <div class="max-w-[900px] mx-auto px-6 text-center relative z-10">
    <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-4 text-[var(--text)]">Headline (keep SHORT — max 8 words)</h1>
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
  NOTE: Text constrained to max-w-[900px], image wider at max-w-[1000px]. Headline MUST be short (max 8 words).""",
    "hero_mockup_center": """hero_mockup_center pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="pt-8 md:pt-16 pb-16 md:pb-20 relative overflow-hidden">
  <!-- Giant faded decorative number -->
  <span class="absolute right-[5%] top-[10%] text-[clamp(100px,18vw,280px)] font-bold opacity-[0.04] pointer-events-none select-none leading-none" style="font-family: var(--font-heading)">01</span>

  <div class="max-w-[900px] mx-auto px-6 text-center relative z-10">
    <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-4 text-[var(--text)]">Headline (keep SHORT — max 8 words)</h1>
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
  NOTE: Browser frame with colored dots. For dark themes use bg-white/[0.06] on the dots bar and border-white/[0.08] on frame.""",
    "hero_asymmetric": """hero_asymmetric pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="py-16 md:py-24 relative overflow-hidden">
  <!-- Giant faded decorative number -->
  <span class="absolute right-[5%] top-[10%] text-[clamp(120px,22vw,320px)] font-bold opacity-[0.04] pointer-events-none select-none leading-none" style="font-family: var(--font-heading)">01</span>

  <div class="max-w-[1400px] mx-auto px-6 grid grid-cols-1 md:grid-cols-[55%_45%] gap-12 items-center relative z-10">
    <div>
      <!-- Section label -->
      <span class="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[var(--accent)] mb-6"><span class="w-10 h-[2px] bg-[var(--accent)]"></span>LABEL TEXT</span>

      <h1 class="text-5xl md:text-6xl lg:text-7xl font-bold leading-none mb-6 text-[var(--text)]">Headline</h1>
      <p class="text-base md:text-lg text-[var(--text-muted)] leading-relaxed mb-8 max-w-xl">Subheadline</p>
      <div class="flex flex-wrap gap-4 mb-6">
        <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
        <a href="#" class="BTN_SECONDARY_CLASSES">Secondary CTA</a>
      </div>
      <p class="text-sm text-[var(--text-muted)]">Trust line</p>
    </div>
    <div class="relative">
      <img src="{{IMG:hero image query from plan}}" alt="Hero visual" class="w-full rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]">
      <div class="absolute -bottom-5 -left-5 bg-[var(--bg-surface)] rounded-[var(--radius)] py-5 px-6 shadow-xl flex items-center gap-3 backdrop-blur-[10px] border border-white/10 z-10 hidden md:flex">
        <i class="fa-solid fa-chart-line text-2xl text-[var(--accent)]"></i>
        <span class="font-semibold text-sm">Key metric or highlight</span>
      </div>
    </div>
  </div>
  NOTE: Floating card is hidden on mobile (hidden md:flex). Text 55%, image 45%. ALWAYS include the giant faded number and section label.""",
}
