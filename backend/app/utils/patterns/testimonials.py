"""Testimonial section pattern templates."""

SLIDER_STYLE = "  .slider-dot.active { background: var(--primary); }"

PATTERNS = {
    "testimonial_cards": """testimonial_cards pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06]" data-aos="flip-up" data-aos-delay="100">
      <div class="text-amber-400 mb-3"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
      <p class="text-[var(--text-muted)] leading-relaxed italic mb-5">"Quote text"</p>
      <div class="flex items-center gap-3">
        <div><strong class="block text-[var(--text)]">Name</strong><span class="text-sm text-[var(--text-muted)]">Role, Company</span></div>
      </div>
    </div>
  </div>""",
    "testimonial_slider": """testimonial_slider pattern:
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
  NOTE: .testimonial-slide and .slider-dot.active styles are in the <style> block.""",
    "testimonial_split": """testimonial_split pattern:
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
  </div>""",
}
