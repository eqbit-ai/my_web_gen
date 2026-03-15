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
    "pricing_toggle": """pricing_toggle pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <!-- Monthly/Annual toggle -->
  <div style="display: flex; justify-content: center; align-items: center; gap: 1rem; margin-bottom: 2.5rem;">
    <span style="font-weight: 600; font-size: 0.9rem;" class="pricing-label active" data-period="monthly">Monthly</span>
    <label style="position: relative; display: inline-block; width: 52px; height: 28px; cursor: pointer;">
      <input type="checkbox" class="pricing-toggle" style="opacity: 0; width: 0; height: 0;">
      <span style="position: absolute; inset: 0; background: var(--primary); border-radius: 28px; transition: 0.3s;"></span>
      <span class="toggle-knob" style="position: absolute; top: 3px; left: 3px; width: 22px; height: 22px; background: white; border-radius: 50%; transition: 0.3s;"></span>
    </label>
    <span style="font-weight: 600; font-size: 0.9rem;" class="pricing-label" data-period="annual">Annual <span style="background: color-mix(in srgb, var(--primary) 15%, transparent); color: var(--primary); padding: 0.15rem 0.5rem; border-radius: 50px; font-size: 0.7rem; margin-left: 0.25rem;">Save 20%</span></span>
  </div>
  <div class="container grid-3" style="align-items: start;">
    <div class="pricing-card card" data-aos="zoom-in" data-aos-delay="100">
      <h3 class="card-title">Starter</h3>
      <div class="plan-price-wrap">
        <span class="plan-price" data-monthly="29" data-annual="23">$29</span><span class="plan-period">/mo</span>
      </div>
      <ul class="plan-features">
        <li class="plan-feature"><i class="fa-solid fa-check check-icon"></i> Feature</li>
      </ul>
      <a href="#" class="btn-secondary" style="display: block; width: 100%; text-align: center;">Get Started</a>
    </div>
    <div class="pricing-card featured card" style="border: 2px solid var(--primary);">
      <div class="popular-badge">Most Popular</div>
      <h3 class="card-title">Professional</h3>
      <div class="plan-price-wrap">
        <span class="plan-price" data-monthly="79" data-annual="63">$79</span><span class="plan-period">/mo</span>
      </div>
      <ul class="plan-features">
        <li class="plan-feature"><i class="fa-solid fa-check check-icon"></i> Feature</li>
      </ul>
      <a href="#" class="btn-primary" style="display: block; width: 100%; text-align: center;">Get Started</a>
    </div>
    <div class="pricing-card card" data-aos="zoom-in" data-aos-delay="300">
      <h3 class="card-title">Enterprise</h3>
      <div class="plan-price-wrap">
        <span class="plan-price" data-monthly="199" data-annual="159">$199</span><span class="plan-period">/mo</span>
      </div>
      <ul class="plan-features">
        <li class="plan-feature"><i class="fa-solid fa-check check-icon"></i> Feature</li>
      </ul>
      <a href="#" class="btn-secondary" style="display: block; width: 100%; text-align: center;">Contact Sales</a>
    </div>
  </div>
  NOTE: Toggle switches between monthly/annual prices. JS: on toggle change, update .plan-price text from data-monthly/data-annual attributes. Move .toggle-knob left/right. Switch active class on .pricing-label elements. The "Save 20%" badge on Annual is always visible.""",

    "pricing_comparison": """pricing_comparison pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container" style="overflow-x: auto;">
    <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: var(--radius); overflow: hidden;">
      <thead>
        <tr style="background: var(--bg-surface);">
          <th style="padding: 1.25rem; text-align: left; font-weight: 600; width: 30%;">Features</th>
          <th style="padding: 1.25rem; text-align: center; font-weight: 600;">Basic<br><span style="font-size: 1.5rem; color: var(--primary);">$29</span><span style="font-size: 0.8rem; color: var(--text-muted);">/mo</span></th>
          <th style="padding: 1.25rem; text-align: center; font-weight: 600; background: color-mix(in srgb, var(--primary) 8%, var(--bg-surface)); border-top: 3px solid var(--primary);">Pro<br><span style="font-size: 1.5rem; color: var(--primary);">$79</span><span style="font-size: 0.8rem; color: var(--text-muted);">/mo</span></th>
          <th style="padding: 1.25rem; text-align: center; font-weight: 600;">Enterprise<br><span style="font-size: 1.5rem; color: var(--primary);">$199</span><span style="font-size: 0.8rem; color: var(--text-muted);">/mo</span></th>
        </tr>
      </thead>
      <tbody>
        <tr style="border-bottom: 1px solid var(--border);">
          <td style="padding: 1rem 1.25rem;">Feature Name</td>
          <td style="padding: 1rem; text-align: center;"><i class="fa-solid fa-check" style="color: var(--primary);"></i></td>
          <td style="padding: 1rem; text-align: center; background: color-mix(in srgb, var(--primary) 4%, transparent);"><i class="fa-solid fa-check" style="color: var(--primary);"></i></td>
          <td style="padding: 1rem; text-align: center;"><i class="fa-solid fa-check" style="color: var(--primary);"></i></td>
        </tr>
        <!-- Repeat 6-8 feature rows -->
      </tbody>
      <tfoot>
        <tr>
          <td></td>
          <td style="padding: 1.25rem; text-align: center;"><a href="#" class="btn-secondary" style="font-size: 0.875rem;">Choose Basic</a></td>
          <td style="padding: 1.25rem; text-align: center; background: color-mix(in srgb, var(--primary) 4%, transparent);"><a href="#" class="btn-primary" style="font-size: 0.875rem;">Choose Pro</a></td>
          <td style="padding: 1.25rem; text-align: center;"><a href="#" class="btn-secondary" style="font-size: 0.875rem;">Contact Sales</a></td>
        </tr>
      </tfoot>
    </table>
  </div>
  NOTE: Full comparison table with highlighted "Pro" column. Use fa-check for included, fa-xmark for excluded. Some cells can have text values. The Pro column has a subtle tinted background to stand out.""",

    "contact_map_split": """contact_map_split pattern:
  <div class="container">
    <div style="text-align: center; margin-bottom: 3rem;">
      <span class="section-label"><span class="label-line"></span>CONTACT US<span class="label-line"></span></span>
      <h2 class="section-title">Get In Touch</h2>
      <p class="section-subtitle">We'd love to hear from you.</p>
    </div>
    <div class="grid-2" style="gap: 0; border-radius: var(--radius); overflow: hidden;">
      <!-- Map/Image side -->
      <div style="min-height: 450px; position: relative;">
        <img src="{{IMG:office building exterior modern}}" alt="Our office" class="img-cover" style="position: absolute; inset: 0;">
        <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 1.5rem; background: linear-gradient(transparent, rgba(0,0,0,0.8));">
          <p style="color: white; font-weight: 600; margin: 0;"><i class="fa-solid fa-location-dot" style="margin-right: 0.5rem;"></i>123 Business St, Dubai, UAE</p>
        </div>
      </div>
      <!-- Form side -->
      <div style="background: var(--bg-surface); padding: 2.5rem;">
        <h3 style="margin-bottom: 1.5rem;">Send Us a Message</h3>
        <form class="contact-form">
          <div class="grid-2" style="gap: 1rem; margin-bottom: 1rem;">
            <input type="text" placeholder="First Name" required class="form-input">
            <input type="text" placeholder="Last Name" required class="form-input">
          </div>
          <input type="email" placeholder="Email Address" required class="form-input" style="margin-bottom: 1rem;">
          <input type="tel" placeholder="Phone Number" class="form-input" style="margin-bottom: 1rem;">
          <textarea placeholder="Your Message" rows="4" required class="form-input form-textarea" style="margin-bottom: 1.5rem;"></textarea>
          <button type="submit" class="btn-primary" style="width: 100%;">Send Message</button>
        </form>
      </div>
    </div>
  </div>
  NOTE: Left side is a full-bleed image (office/map) with address overlay. Right side is a detailed contact form. No gap between halves — they merge into one card. On mobile: image stacks on top of form.""",

    "contact_minimal": """contact_minimal pattern:
  <div class="container-narrow" style="text-align: center;">
    <span class="section-label"><span class="label-line"></span>CONTACT<span class="label-line"></span></span>
    <h2 class="section-title">Let's Work Together</h2>
    <p class="section-subtitle" style="margin-bottom: 2.5rem;">Drop us a line and we'll get back to you within 24 hours.</p>
    <form class="contact-form" style="max-width: 500px; margin: 0 auto;">
      <input type="text" placeholder="Your Name" required class="form-input" style="margin-bottom: 1rem;">
      <input type="email" placeholder="Email Address" required class="form-input" style="margin-bottom: 1rem;">
      <textarea placeholder="Tell us about your project..." rows="5" required class="form-input form-textarea" style="margin-bottom: 1.5rem;"></textarea>
      <button type="submit" class="btn-primary" style="width: 100%;">Send Message</button>
    </form>
    <div style="display: flex; justify-content: center; gap: 2.5rem; margin-top: 3rem; flex-wrap: wrap;">
      <a href="mailto:hello@company.com" style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-muted);"><i class="fa-solid fa-envelope" style="color: var(--primary);"></i> hello@company.com</a>
      <a href="tel:+971000000000" style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-muted);"><i class="fa-solid fa-phone" style="color: var(--primary);"></i> +971 00 000 0000</a>
      <span style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-muted);"><i class="fa-solid fa-location-dot" style="color: var(--primary);"></i> Dubai, UAE</span>
    </div>
  </div>
  NOTE: Minimal centered contact section. Form is narrow and clean. Contact details appear below as icon links. Perfect for modern/minimal sites.""",

    "marquee_text": """marquee_text pattern:
  <!-- Full-width scrolling text band — no container needed -->
  <div style="overflow: hidden; padding: 1.5rem 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);">
    <div class="marquee-track" style="display: flex; gap: 3rem; align-items: center; animation: marqueeLeft 20s linear infinite; white-space: nowrap;">
      <span style="font-size: 2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">KEYWORD ONE</span>
      <span style="color: var(--primary); font-size: 1.5rem;">&bull;</span>
      <span style="font-size: 2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">KEYWORD TWO</span>
      <span style="color: var(--primary); font-size: 1.5rem;">&bull;</span>
      <span style="font-size: 2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">KEYWORD THREE</span>
      <span style="color: var(--primary); font-size: 1.5rem;">&bull;</span>
      <span style="font-size: 2rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">KEYWORD FOUR</span>
      <span style="color: var(--primary); font-size: 1.5rem;">&bull;</span>
      <!-- DUPLICATE all items above for seamless loop -->
    </div>
  </div>
  NOTE: Infinite scrolling text marquee. Use brand keywords, services, or taglines as the text items. Must duplicate all items for seamless loop. Add @keyframes marqueeLeft in style block. Use between major sections as a visual divider. Very trendy — seen on Framer, Linear, Vercel sites.""",

    "before_after": """before_after pattern:
  <div class="container">
    <div style="text-align: center; margin-bottom: 3rem;">
      <span class="section-label"><span class="label-line"></span>RESULTS<span class="label-line"></span></span>
      <h2 class="section-title">Before & After</h2>
      <p class="section-subtitle">See the transformation.</p>
    </div>
    <div class="grid-2" style="gap: 2rem;">
      <!-- Before -->
      <div class="card fade-up" style="overflow: hidden; padding: 0;">
        <div style="padding: 0.75rem 1.25rem; background: color-mix(in srgb, var(--primary) 8%, var(--bg-surface)); display: flex; align-items: center; gap: 0.5rem;">
          <span style="width: 10px; height: 10px; border-radius: 50%; background: var(--text-muted);"></span>
          <span style="font-weight: 600; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em;">Before</span>
        </div>
        <div class="img-wrapper" style="aspect-ratio: 16/10;">
          <img src="{{IMG:before renovation old worn}}" alt="Before" class="img-cover">
        </div>
      </div>
      <!-- After -->
      <div class="card fade-up" style="overflow: hidden; padding: 0;">
        <div style="padding: 0.75rem 1.25rem; background: color-mix(in srgb, var(--primary) 8%, var(--bg-surface)); display: flex; align-items: center; gap: 0.5rem;">
          <span style="width: 10px; height: 10px; border-radius: 50%; background: var(--primary);"></span>
          <span style="font-weight: 600; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em;">After</span>
        </div>
        <div class="img-wrapper" style="aspect-ratio: 16/10;">
          <img src="{{IMG:after renovation modern beautiful}}" alt="After" class="img-cover">
        </div>
      </div>
    </div>
  </div>
  NOTE: Side-by-side before/after comparison. Each card has a labeled header with a status dot. Can be repeated for multiple before/after pairs. Great for renovation, design, fitness, consulting, etc.""",

    "vertical_tabs": """vertical_tabs pattern:
  <div class="container">
    <div style="text-align: center; margin-bottom: 3rem;">
      <span class="section-label"><span class="label-line"></span>SERVICES<span class="label-line"></span></span>
      <h2 class="section-title">What We Offer</h2>
    </div>
    <div class="grid-2" style="gap: 0; min-height: 450px;">
      <!-- Tab navigation (left) -->
      <div style="border-right: 1px solid var(--border);">
        <button class="vtab-btn active" data-vtab="vtab-1" style="display: flex; align-items: center; gap: 1rem; width: 100%; padding: 1.25rem 1.5rem; border: none; background: none; cursor: pointer; text-align: left; border-left: 3px solid transparent; transition: all 0.3s;">
          <div class="icon-box" style="background: color-mix(in srgb, var(--primary) 12%, transparent); flex-shrink: 0;"><i class="fa-solid fa-xxx"></i></div>
          <div>
            <h4 style="margin: 0; font-size: 1rem;">Tab Title</h4>
            <p style="margin: 0.25rem 0 0; font-size: 0.8rem; color: var(--text-muted);">Brief one-liner</p>
          </div>
        </button>
        <!-- Repeat 3-5 tab buttons -->
      </div>
      <!-- Tab content (right) -->
      <div style="padding: 2rem;">
        <div id="vtab-1" class="vtab-content active">
          <h3 style="margin-bottom: 1rem;">Service Title</h3>
          <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Detailed description of this service, including benefits, process, and outcomes.</p>
          <div class="img-wrapper" style="border-radius: var(--radius); overflow: hidden; aspect-ratio: 16/9;">
            <img src="{{IMG:service specific visual}}" alt="Service" class="img-cover">
          </div>
        </div>
        <!-- Repeat content panels (hidden by default except active) -->
      </div>
    </div>
  </div>
  NOTE: Left side has clickable tabs, right side shows corresponding content. JS: clicking tab sets active class on button (border-left: 3px solid var(--primary)) and shows matching content panel. Only one panel visible at a time. On mobile: tabs stack on top of content.""",

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
