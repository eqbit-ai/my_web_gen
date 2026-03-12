"""Other section pattern templates (pricing, FAQ, stats, gallery, carousel, etc.)."""

# Conditional CSS additions
STEPS_STYLE = '  .steps-container::before { content: ""; position: absolute; left: 28px; top: 0; bottom: 0; width: 2px; background: linear-gradient(180deg, var(--primary), var(--secondary)); }'
TIMELINE_STYLE = '  .timeline-container::before { content: ""; position: absolute; left: 118px; top: 0; bottom: 0; width: 2px; background: linear-gradient(180deg, var(--primary), var(--secondary)); }'
CAROUSEL_STYLE = "  .carousel-dot.active { background: var(--primary); }"
LIGHTBOX_STYLE = "  #gallery-lightbox.active { display: flex; }"
MODAL_STYLE = "  .detail-modal.active { display: flex; }"
LOGO_CAROUSEL_STYLE = """  @keyframes logoScroll { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
  .logo-carousel-track { animation: logoScroll 20s linear infinite; }
  .logo-carousel-container::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 60px; background: linear-gradient(90deg, var(--bg), transparent); z-index: 2; pointer-events: none; }
  .logo-carousel-container::after { content: ""; position: absolute; right: 0; top: 0; bottom: 0; width: 60px; background: linear-gradient(-90deg, var(--bg), transparent); z-index: 2; pointer-events: none; }"""
COMPARISON_STYLE = ""  # No extra CSS needed

PATTERNS = {
    "pricing_table": """pricing_table pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3" style="align-items: start;">
    <div class="pricing-card card" data-aos="zoom-in" data-aos-delay="100">
      <h3 class="card-title">Plan</h3>
      <div class="plan-price-wrap"><span class="plan-price">$99</span><span class="plan-period">/mo</span></div>
      <ul class="plan-features">
        <li class="plan-feature"><i class="fa-solid fa-check check-icon"></i> Feature</li>
      </ul>
      <a href="#" class="btn-primary" style="display: block; width: 100%; text-align: center;">Get Started</a>
    </div>
  </div>
  NOTE: The middle/recommended plan card MUST have class "pricing-card featured card" AND include a "Most Popular" badge:
  <div class="pricing-card featured card" style="border: 2px solid var(--primary);">
    <div class="popular-badge">Most Popular</div>
  The featured card auto-scales 105% + primary border via CSS. Non-featured cards have NO border-2.""",
    "faq_accordion": """faq_accordion pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container-narrow">
    <div class="faq-item" data-aos="fade-up">
      <button class="faq-question"><span>Question?</span><i class="fa-solid fa-chevron-down"></i></button>
      <div class="faq-answer"><p>Answer text</p></div>
    </div>
  </div>
  NOTE: FAQ toggle handled by JS + <style> block.""",
    "stats_row": """stats_row pattern:
  <div class="container grid-4 text-center">
    <div class="stat-item" data-aos="fade-up" data-aos-delay="100">
      <div class="stat-icon" style="background: color-mix(in srgb, var(--accent) 12%, transparent)">
        <i class="fa-solid fa-building"></i>
      </div>
      <div class="stat-number">500+</div>
      <div class="stat-label">Projects Completed</div>
    </div>
    <div class="stat-item" data-aos="fade-up" data-aos-delay="200">
      <div class="stat-icon" style="background: color-mix(in srgb, var(--accent) 12%, transparent)">
        <i class="fa-solid fa-leaf"></i>
      </div>
      <div class="stat-number">45%</div>
      <div class="stat-label">Energy Reduction</div>
    </div>
  </div>
  STATS RULES:
  - Each stat: icon box -> .stat-number (MASSIVE size) -> label (tiny uppercase)
  - Stat numbers must be large — this size contrast IS the design
  - Number AND suffix (+, %, M, K, M+) MUST be in the SAME .stat-number element
  - CORRECT: <div class="stat-number">120+</div>
  - WRONG: <span>120</span><span>+</span> (NEVER split number and suffix)
  - Labels should be SHORT (2-3 words max) — they wrap badly at small sizes
  - Do NOT use data-target attributes. JS handles counter animation automatically via IntersectionObserver.""",
    "gallery_grid": """gallery_grid pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3" style="gap: 1rem;">
    <div class="gallery-item" data-aos="zoom-in" data-aos-delay="100">
      <img src="{{IMG:gallery specific image query}}" alt="Gallery item title" class="gallery-image">
    </div>
  </div>
  <!-- Lightbox modal (single, reused for all images) -->
  <div id="gallery-lightbox" class="gallery-lightbox">
    <button class="lightbox-close">&times;</button>
    <button class="lightbox-prev"><i class="fa-solid fa-chevron-left"></i></button>
    <button class="lightbox-next"><i class="fa-solid fa-chevron-right"></i></button>
    <img class="lightbox-img" src="" alt="">
  </div>
  NOTE: Each gallery item MUST have a unique {{IMG:gallery ...}} query. JS handles lightbox open/close/navigation.""",
    "image_carousel": """image_carousel pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="carousel-container container" data-aos="fade-up">
    <div class="carousel-track">
      <div class="carousel-slide">
        <img src="{{IMG:carousel specific image query}}" alt="Slide title" class="carousel-image">
        <div class="carousel-caption">
          <h3 class="carousel-caption-title">Slide Title</h3>
          <p class="carousel-caption-text">Slide description text</p>
        </div>
      </div>
      <!-- Repeat for each slide (3-5 slides) -->
    </div>
    <button class="carousel-prev"><i class="fa-solid fa-chevron-left"></i></button>
    <button class="carousel-next"><i class="fa-solid fa-chevron-right"></i></button>
    <div class="carousel-dots">
      <button class="carousel-dot active" data-slide="0"></button>
      <!-- One dot per slide -->
    </div>
  </div>
  CAROUSEL RULES (CRITICAL — carousel MUST work):
  - Each slide MUST have a unique {{IMG:carousel ...}} query
  - Generate 3-5 .carousel-slide elements inside .carousel-track
  - Generate matching .carousel-dot buttons (one per slide) with data-slide="0", data-slide="1", etc.
  - The .carousel-prev and .carousel-next buttons MUST exist with those exact classes
  - First dot MUST have class "active" initially
  - JS will translate .carousel-track by -100% per slide index
  - Do NOT add any inline onclick handlers — JS handles all navigation""",
    "service_modal": """service_modal pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="modal-trigger card" data-modal="modal-1" data-aos="fade-right" data-aos-delay="100">
      <div class="icon-box" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="card-title">Service Title</h3>
      <p class="card-text" style="margin-bottom: 0.75rem;">Short description visible on the card.</p>
      <span class="card-link">Learn More <i class="fa-solid fa-arrow-right"></i></span>
    </div>
  </div>
  <!-- Modals (one per card, hidden by default) -->
  <div id="modal-1" class="detail-modal">
    <div class="modal-content">
      <button class="modal-close">&times;</button>
      <div class="icon-box" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="card-title" style="font-size: 1.25rem; margin-bottom: 0.75rem;">Service Title</h3>
      <p class="card-text">Expanded detailed description of this service. Include specifics, benefits, process details, what the client gets, etc.</p>
    </div>
  </div>
  NOTE: Each card has data-modal="modal-N" pointing to matching modal ID. Use modal-1, modal-2, modal-3, etc. JS handles open/close.""",
    "timeline": """timeline pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="timeline-container container-narrow">
    <div class="timeline-item" data-aos="fade-up" data-aos-delay="100">
      <div class="timeline-date">
        <span>2020</span>
      </div>
      <div class="timeline-dot"></div>
      <div class="timeline-card">
        <h3 class="card-title">Milestone Title</h3>
        <p class="card-text">Description of what happened at this milestone.</p>
      </div>
    </div>
    <!-- Repeat 4-6 milestones -->
  </div>
  NOTE: The connecting vertical line is handled by .timeline-container::before in the <style> block. Dates can be years, months, or descriptive phases.""",
    "newsletter_cta": """newsletter_cta pattern:
  <div class="container-xs" style="text-align: center;">
    <h2 class="section-title">Headline</h2>
    <p class="section-subtitle">Short pitch about why they should subscribe.</p>
    <form class="newsletter-form">
      <input type="email" placeholder="Enter your email" required class="form-input">
      <button type="submit" class="btn-primary">Subscribe</button>
    </form>
    <p class="form-hint">No spam. Unsubscribe anytime.</p>
  </div>
  NOTE: JS handles form submit with inline success message (not alert).""",
    "comparison_table": """comparison_table pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container-narrow" style="overflow-x: auto;" data-aos="fade-up">
    <table class="comparison-table">
      <thead>
        <tr>
          <th>Feature</th>
          <th class="highlight-col">Our Product</th>
          <th>Competitor</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Feature name</td>
          <td class="text-center"><i class="fa-solid fa-check check-icon"></i></td>
          <td class="text-center"><i class="fa-solid fa-xmark miss-icon"></i></td>
        </tr>
        <!-- Repeat 5-8 feature rows -->
      </tbody>
    </table>
  </div>
  NOTE: Use fa-check (green) for included features, fa-xmark (red/dim) for missing. Some cells can have text instead of icons. """,
    "logo_cloud": """logo_cloud pattern:
  <div class="section-header"><h2 class="section-subtitle">Headline</h2></div>
  <div class="container logo-cloud">
    <div class="logo-item" data-aos="fade-up" data-aos-delay="100">
      <span class="logo-text">Company 1</span>
    </div>
    <div class="logo-item" data-aos="fade-up" data-aos-delay="200">
      <span class="logo-text">Company 2</span>
    </div>
  </div>
  NOTE: Text-only logos. Do NOT use <img> tags, dummyimage.com, or any image URLs for logos.""",
    "logo_carousel": """logo_carousel pattern:
  <div class="section-header"><h2 class="section-subtitle">Headline</h2></div>
  <div class="logo-carousel-container container">
    <div class="logo-carousel-track">
      <span class="logo-text">Company 1</span>
      <span class="logo-text">Company 2</span>
      <span class="logo-text">Company 3</span>
      <span class="logo-text">Company 4</span>
      <span class="logo-text">Company 5</span>
      <span class="logo-text">Company 6</span>
      <!-- JS duplicates these for infinite scroll effect -->
    </div>
  </div>
  NOTE: Text-only logos, NO images. JS handles infinite scroll by duplicating track content. The carousel auto-scrolls continuously.""",
    "trust_badges": """trust_badges pattern:
  <div class="container trust-badges">
    <div class="trust-badge" data-aos="fade-right" data-aos-delay="100">
      <i class="fa-solid fa-shield-halved badge-icon"></i>
      <div><span class="badge-title">SSL Secured</span><span class="badge-subtitle">256-bit encryption</span></div>
    </div>
    <div class="trust-badge" data-aos="fade-right" data-aos-delay="200">
      <i class="fa-solid fa-certificate badge-icon"></i>
      <div><span class="badge-title">ISO 27001</span><span class="badge-subtitle">Certified</span></div>
    </div>
  </div>
  NOTE: 3-5 badges. Pick industry-relevant certifications: GDPR, HIPAA, SOC2, ISO, PCI-DSS, DED Licensed, TDRA Approved, etc. Compact section — use minimal vertical padding.""",
    "contact_split": """contact_split pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-2">
    <div class="contact-info">
      <div class="contact-item"><i class="fa-solid fa-location-dot contact-icon"></i><p>Address</p></div>
      <div class="contact-item"><i class="fa-solid fa-phone contact-icon"></i><p>Phone</p></div>
      <div class="contact-item"><i class="fa-solid fa-envelope contact-icon"></i><p>Email</p></div>
    </div>
    <form class="contact-form">
      <input type="text" placeholder="Your Name" required class="form-input">
      <input type="email" placeholder="Your Email" required class="form-input">
      <textarea placeholder="Your Message" rows="5" required class="form-input form-textarea"></textarea>
      <button type="submit" class="btn-primary">Send Message</button>
    </form>
  </div>
  NOTE: Light themes use border-gray-200 instead of border-white/10.""",
}
