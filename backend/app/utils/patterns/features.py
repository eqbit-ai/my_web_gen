"""Feature section pattern templates."""

PATTERNS = {
    "card_grid": """card_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06]" data-aos="fade-up" data-aos-delay="100">
      <div class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--accent)] mb-5" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="text-lg font-bold mb-2 text-[var(--text)]">Title</h3>
      <p class="text-[var(--text-muted)] leading-relaxed text-sm">Description</p>
    </div>
  </div>
  NOTE: Light themes use border-gray-100 instead of border-white/[0.06].""",
    "icon_grid": """icon_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 text-center">
    <div class="p-6" data-aos="zoom-in" data-aos-delay="100">
      <div class="w-12 h-12 mx-auto mb-4 rounded-full flex items-center justify-center text-lg text-[var(--accent)]" style="background: color-mix(in srgb, var(--accent) 10%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h4 class="font-bold mb-1 text-[var(--text)]">Title</h4>
      <p class="text-sm text-[var(--text-muted)]">Short description</p>
    </div>
  </div>""",
    "feature_split": """feature_split pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 space-y-12">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center" data-aos="fade-right">
      <div><h3 class="text-xl font-bold mb-3 text-[var(--text)]">Title</h3><p class="text-[var(--text-muted)] leading-relaxed">Description</p></div>
      <div class="overflow-hidden rounded-xl"><img src="{{IMG:feature specific query from plan}}" alt="Feature name" class="w-full h-auto rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]"></div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center" data-aos="fade-left">
      <div class="md:order-2"><h3 class="text-xl font-bold mb-3 text-[var(--text)]">Title</h3><p class="text-[var(--text-muted)] leading-relaxed">Description</p></div>
      <div class="overflow-hidden rounded-xl md:order-1"><img src="{{IMG:feature different query}}" alt="Feature name" class="w-full h-auto rounded-xl object-cover transition-transform duration-300 hover:scale-[1.02]"></div>
    </div>
  </div>
  NOTE: Alternate rows. Second row uses md:order to flip text/image.""",
    "feature_cards": """feature_cards pattern:
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
  NOTE: Each card MUST have a unique {{IMG:feature ...}} with the image_query from the plan.""",
    "feature_stacked": """feature_stacked pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[800px] mx-auto px-6 divide-y divide-white/10">
    <div class="flex flex-col md:flex-row gap-5 items-start py-8" data-aos="fade-right">
      <div class="w-14 h-14 min-w-[3.5rem] rounded-xl flex items-center justify-center text-xl text-[var(--accent)]" style="background: color-mix(in srgb, var(--accent) 10%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <div>
        <h3 class="text-lg font-bold mb-1 text-[var(--text)]">Title</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Long detailed description of this feature or service.</p>
      </div>
    </div>
  </div>
  NOTE: Light themes use divide-gray-100 instead of divide-white/10.""",
    "feature_steps": """feature_steps pattern:
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
  NOTE: The connecting vertical line is handled by .steps-container in the <style> block. Use 3 or 4 steps.""",
}
