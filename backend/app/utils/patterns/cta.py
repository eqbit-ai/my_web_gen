"""CTA section pattern templates."""

PATTERNS = {
    "cta_banner": """cta_banner pattern:
  <div class="max-w-[1200px] mx-auto px-6 text-center" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: var(--radius); padding: 3rem 2rem;">
    <h2 class="text-2xl md:text-3xl font-bold mb-3 text-white">Headline</h2>
    <p class="text-base text-white/80 mb-6 max-w-lg mx-auto">Description</p>
    <div class="flex flex-wrap gap-4 justify-center">
      <a href="#" class="inline-block bg-white text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg">Primary CTA</a>
      <a href="#" class="inline-block border-2 border-white text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:bg-white hover:text-[var(--primary)] bg-transparent">Secondary CTA</a>
    </div>
  </div>""",
    "cta_split": """cta_split pattern:
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
  </div>""",
    "cta_gradient": """cta_gradient pattern:
  <div class="text-center py-16 md:py-20 relative" style="background: linear-gradient(135deg, var(--primary), var(--secondary));">
    <div class="max-w-[800px] mx-auto px-6">
      <h2 class="text-2xl md:text-3xl font-bold mb-3 text-white">Headline</h2>
      <p class="text-base text-white/80 mb-6 max-w-lg mx-auto">Description</p>
      <a href="#" class="inline-block bg-white text-[var(--primary)] py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:shadow-[0_0_30px_rgba(255,255,255,0.5)]">Primary CTA</a>
    </div>
  </div>""",
    "cta_centered": """cta_centered pattern:
  <div class="max-w-[800px] mx-auto px-6 text-center">
    <h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2>
    <p class="text-base md:text-lg text-[var(--text-muted)] max-w-lg mx-auto leading-relaxed mb-6">Description</p>
    <a href="#" class="BTN_PRIMARY_CLASSES">Primary CTA</a>
  </div>
  NOTE: Simple, clean centered CTA. No gradient background.""",
}
