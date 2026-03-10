"""Team section pattern templates."""

PATTERNS = {
    "team_grid": """team_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] overflow-hidden shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06] text-center" data-aos="zoom-in" data-aos-delay="100">
      <img src="{{IMG:team professional man portrait studio}}" alt="Name" class="w-full h-64 object-cover">
      <div class="p-5">
        <h3 class="text-lg font-bold text-[var(--text)]">Name</h3>
        <p class="text-sm text-[var(--text-muted)]">Role</p>
      </div>
    </div>
  </div>""",

    "team_cards": """team_cards pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] overflow-hidden shadow-md hover:-translate-y-1.5 hover:shadow-xl transition-all duration-300 border border-white/[0.06]" data-aos="flip-up" data-aos-delay="100">
      <img src="{{IMG:team professional woman portrait studio}}" alt="Name" class="w-full h-72 object-cover">
      <div class="p-5">
        <h3 class="text-lg font-bold text-[var(--text)]">Name</h3>
        <p class="text-sm text-[var(--text-muted)]">Role</p>
        <p class="text-sm text-[var(--text-muted)] mt-2">Short bio about this team member and their expertise.</p>
      </div>
    </div>
  </div>""",

    "team_masonry": """team_masonry pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 columns-1 md:columns-2 lg:columns-3 gap-6">
    <div class="break-inside-avoid mb-6 relative rounded-[var(--radius)] overflow-hidden group" data-aos="fade-up" data-aos-delay="100">
      <img src="{{IMG:team professional man portrait studio}}" alt="Name" class="w-full block">
      <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent text-white p-6 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
        <h3 class="font-bold">Name</h3>
        <p class="text-sm text-white/80">Role</p>
      </div>
    </div>
  </div>""",
}
