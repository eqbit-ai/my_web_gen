"""Testimonial section pattern templates."""

SLIDER_STYLE = "  .slider-dot.active { background: var(--primary); }"

PATTERNS = {
    "testimonial_cards": """testimonial_cards pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card" data-aos="flip-up" data-aos-delay="100">
      <div class="stars"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
      <p class="testimonial-quote">"Quote text"</p>
      <div class="testimonial-author">
        <div><strong>Name</strong><span>Role, Company</span></div>
      </div>
    </div>
  </div>""",
    "testimonial_slider": """testimonial_slider pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container-narrow text-center" data-aos="fade-up">
    <div class="testimonial-slide active">
      <div class="stars"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
      <blockquote class="testimonial-quote-lg">"Large featured quote text goes here."</blockquote>
      <div><strong>Name</strong><span>Role, Company</span></div>
    </div>
    <div class="testimonial-slide"><!-- additional slides hidden by default --></div>
    <div class="slider-dots">
      <button class="slider-dot active" data-slide="0"></button>
      <button class="slider-dot" data-slide="1"></button>
    </div>
  </div>
  NOTE: .testimonial-slide and .slider-dot.active styles are in the <style> block.""",
    "testimonial_split": """testimonial_split pattern:
  <div class="container">
    <div class="grid-2" data-aos="fade-up">
      <div>
        <div class="stars"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <blockquote class="testimonial-quote-lg">"Large impactful quote text here."</blockquote>
        <div><strong>Name</strong><span>Role, Company</span></div>
      </div>
      <div class="img-wrapper">
        <img src="{{IMG:testimonial professional portrait business person}}" alt="Author name" class="img-cover">
      </div>
    </div>
  </div>""",
}
