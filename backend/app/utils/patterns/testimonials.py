"""Testimonial section pattern templates."""

SLIDER_STYLE = "  .slider-dot.active { background: var(--primary); }"

PATTERNS = {
    "testimonial_cards": """testimonial_cards pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card" data-aos="fade-up" data-aos-delay="100" style="padding:2rem;position:relative;">
      <!-- Large decorative quote mark -->
      <div style="font-size:3rem;line-height:1;color:var(--primary);opacity:0.15;font-family:serif;position:absolute;top:1rem;right:1.5rem;">&ldquo;</div>
      <div class="stars"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
      <p class="testimonial-quote">"Quote text"</p>
      <div class="testimonial-author" style="display:flex;align-items:center;gap:0.75rem;">
        <!-- Avatar initial circle -->
        <div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--primary),var(--secondary));display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:0.85rem;flex-shrink:0;">AB</div>
        <div><strong style="display:block;">Name</strong><span style="font-size:0.85rem;color:var(--text-muted);">Role, Company</span></div>
      </div>
    </div>
  </div>
  NOTE: Each card has a decorative quote mark and an avatar initial circle for the author (use their initials). This creates a much more polished look than plain text.""",
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

    "testimonial_video": """testimonial_video pattern:
  <div class="container">
    <div style="text-align: center; margin-bottom: 3rem;">
      <span class="section-label"><span class="label-line"></span>TESTIMONIALS<span class="label-line"></span></span>
      <h2 class="section-title">What Our Clients Say</h2>
    </div>
    <div class="grid-2" style="gap: 2rem; align-items: center;">
      <!-- Video/image side with play button overlay -->
      <div class="fade-up" style="position: relative; border-radius: var(--radius); overflow: hidden; aspect-ratio: 16/9;">
        <img src="{{IMG:professional person speaking interview}}" alt="Client testimonial" class="img-cover">
        <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.2); cursor: pointer;">
          <div style="width: 72px; height: 72px; border-radius: 50%; background: var(--primary); display: flex; align-items: center; justify-content: center; transition: transform 0.3s;">
            <i class="fa-solid fa-play" style="color: white; font-size: 1.5rem; margin-left: 4px;"></i>
          </div>
        </div>
      </div>
      <!-- Quote side -->
      <div class="fade-up">
        <div style="font-size: 3rem; color: var(--primary); line-height: 1; margin-bottom: 1rem;">&ldquo;</div>
        <blockquote style="font-size: 1.25rem; font-style: italic; line-height: 1.7; margin-bottom: 1.5rem;">"Detailed testimonial quote that feels genuine and speaks to specific results achieved."</blockquote>
        <div style="display: flex; align-items: center; gap: 1rem;">
          <div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--secondary)); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">JD</div>
          <div>
            <strong style="display: block;">Client Name</strong>
            <span style="color: var(--text-muted); font-size: 0.875rem;">CEO, Company Name</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  NOTE: Left side is a testimonial image with a decorative play button overlay (does not play actual video — purely visual). Right side is a large quote with author avatar initials. Creates a high-end editorial feel.""",

    "testimonial_marquee": """testimonial_marquee pattern:
  <div style="text-align: center; margin-bottom: 2rem;">
    <span class="section-label"><span class="label-line"></span>REVIEWS<span class="label-line"></span></span>
    <h2 class="section-title">Trusted by Hundreds</h2>
  </div>
  <!-- Scrolling row 1 (left to right) -->
  <div style="overflow: hidden; margin-bottom: 1.5rem;">
    <div class="marquee-track" style="display: flex; gap: 1.5rem; animation: marqueeLeft 30s linear infinite;">
      <div class="card" style="min-width: 350px; max-width: 350px; padding: 1.5rem; flex-shrink: 0;">
        <div class="stars" style="margin-bottom: 0.75rem;"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">"Short punchy testimonial quote."</p>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <div style="width: 36px; height: 36px; border-radius: 50%; background: var(--primary); display: flex; align-items: center; justify-content: center; color: white; font-size: 0.75rem; font-weight: 700;">AB</div>
          <div><strong style="font-size: 0.85rem;">Name</strong><br><span style="font-size: 0.75rem; color: var(--text-muted);">Role</span></div>
        </div>
      </div>
      <!-- Repeat 4-6 cards, then DUPLICATE the entire set for seamless loop -->
    </div>
  </div>
  <!-- Scrolling row 2 (right to left) -->
  <div style="overflow: hidden;">
    <div class="marquee-track" style="display: flex; gap: 1.5rem; animation: marqueeRight 35s linear infinite;">
      <!-- Same structure, different testimonials, duplicated for loop -->
    </div>
  </div>
  NOTE: Two rows scrolling in opposite directions. Each row has 4-6 cards duplicated for seamless infinite loop. Add @keyframes marqueeLeft { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } } and marqueeRight (opposite) in the style block. Cards must be duplicated (content repeated twice) for seamless scrolling.""",
}
