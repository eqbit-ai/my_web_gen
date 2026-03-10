"""Hero section pattern templates."""

PATTERNS = {
    "hero_split": """hero_split pattern:
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
  NOTE: ALL text must stay in the first column. Image in second column. On mobile: single column, image first (use md:order-none order-first on image div).""",
    "hero_center": """hero_center pattern:
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
  </div>""",
    "hero_full_image": """hero_full_image pattern:
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
  NOTE: Overlay MUST be bg-black/70 minimum — text must be readable over any image. The -mt-[80px] on the section and pt-[80px] on the inner div ensure hero extends behind the fixed navbar with no gap.""",
    "hero_minimal": """hero_minimal pattern:
  SECTION WRAPPER: <section data-section-type="hero" class="py-16 md:py-24">
  <div class="max-w-[800px] mx-auto px-6 text-center py-20 md:py-28">
    <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-4 text-[var(--text)]">Big Bold Headline</h1>
    <p class="text-lg md:text-xl text-[var(--text-muted)] leading-relaxed mb-8 max-w-lg mx-auto">One concise line of supporting text</p>
    <div class="flex justify-center">
      <a href="#" class="BTN_PRIMARY_CLASSES">Single CTA</a>
    </div>
  </div>""",
    "hero_video_bg": """hero_video_bg pattern:
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
  </div>""",
    "hero_product_mockup": """hero_product_mockup pattern:
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
  NOTE: Text constrained to max-w-[900px], image wider at max-w-[1000px]. Headline MUST be short (max 8 words).""",
    "hero_mockup_center": """hero_mockup_center pattern:
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
  NOTE: Browser frame with colored dots. For dark themes use bg-white/[0.06] on the dots bar and border-white/[0.08] on frame.""",
    "hero_asymmetric": """hero_asymmetric pattern:
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
        <i class="fa-solid fa-chart-line text-2xl text-[var(--accent)]"></i>
        <span class="font-semibold text-sm">Key metric or highlight</span>
      </div>
    </div>
  </div>
  NOTE: Floating card is hidden on mobile (hidden md:flex). Text 55%, image 45%.""",
}
