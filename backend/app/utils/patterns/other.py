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
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
    <div class="pricing-card bg-[var(--bg-surface)] rounded-[var(--radius)] p-8 text-center shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06] relative" data-aos="zoom-in" data-aos-delay="100">
      <h3 class="text-xl font-bold mb-2 text-[var(--text)]">Plan</h3>
      <div class="my-4"><span class="text-4xl font-bold text-[var(--accent)]">$99</span><span class="text-sm font-normal text-[var(--text-muted)]">/mo</span></div>
      <ul class="text-left space-y-3 my-6 text-sm list-none p-0">
        <li class="flex items-center gap-2 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--accent)]"></i> Feature</li>
      </ul>
      <a href="#" class="block w-full BTN_PRIMARY_CLASSES text-center">Get Started</a>
    </div>
  </div>
  NOTE: The middle/recommended plan card should have class "pricing-card featured" to visually emphasize it (auto-scaled 105% + primary border via CSS).""",
    "faq_accordion": """faq_accordion pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[800px] mx-auto px-6">
    <div class="faq-item border-b border-white/10" data-aos="fade-up">
      <button class="faq-question w-full bg-transparent border-none py-5 flex justify-between items-center text-base md:text-lg font-semibold cursor-pointer text-left text-[var(--text)]"><span>Question?</span><i class="fa-solid fa-chevron-down text-sm text-[var(--text-muted)] transition-transform duration-300"></i></button>
      <div class="faq-answer"><p class="text-[var(--text-muted)] leading-relaxed pb-4">Answer text</p></div>
    </div>
  </div>
  NOTE: Light themes use border-gray-200 instead of border-white/10. FAQ toggle handled by JS + <style> block.""",
    "stats_row": """stats_row pattern:
  <div class="max-w-[900px] mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
    <div class="flex flex-col items-center gap-2" data-aos="fade-up" data-aos-delay="100">
      <i class="fa-solid fa-building text-2xl text-[var(--accent)] opacity-80"></i>
      <div class="stat-number text-3xl md:text-4xl font-bold text-[var(--accent)] leading-none whitespace-nowrap">500+</div>
      <div class="text-xs uppercase tracking-widest text-[var(--text-muted)] max-w-[200px]">Projects Completed</div>
    </div>
    <div class="flex flex-col items-center gap-2" data-aos="fade-up" data-aos-delay="200">
      <i class="fa-solid fa-leaf text-2xl text-[var(--accent)] opacity-80"></i>
      <div class="stat-number text-3xl md:text-4xl font-bold text-[var(--accent)] leading-none whitespace-nowrap">45%</div>
      <div class="text-xs uppercase tracking-widest text-[var(--text-muted)] max-w-[200px]">Average Energy Reduction</div>
    </div>
  </div>
  STATS RULES:
  - Each stat: optional icon -> .stat-number -> label
  - Number AND suffix (+, %, M, K, M+) MUST be in the SAME .stat-number element
  - CORRECT: <div class="stat-number ...">120+</div>
  - WRONG: <span>120</span><span>+</span> (NEVER split number and suffix)
  - Do NOT use data-target attributes. JS handles counter animation automatically via IntersectionObserver.""",
    "gallery_grid": """gallery_grid pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div class="gallery-item overflow-hidden rounded-[var(--radius)] cursor-pointer group" data-aos="zoom-in" data-aos-delay="100">
      <img src="{{IMG:gallery specific image query}}" alt="Gallery item title" class="w-full h-64 object-cover transition-transform duration-500 group-hover:scale-110">
    </div>
  </div>
  <!-- Lightbox modal (single, reused for all images) -->
  <div id="gallery-lightbox" class="fixed inset-0 z-[9999] bg-black/90 hidden items-center justify-center p-4">
    <button class="lightbox-close absolute top-6 right-6 text-white text-3xl bg-transparent border-none cursor-pointer hover:text-[var(--primary)] transition-colors z-10">&times;</button>
    <button class="lightbox-prev absolute left-4 top-1/2 -translate-y-1/2 text-white text-4xl bg-black/30 hover:bg-black/60 border-none cursor-pointer rounded-full w-12 h-12 flex items-center justify-center transition-all"><i class="fa-solid fa-chevron-left"></i></button>
    <button class="lightbox-next absolute right-4 top-1/2 -translate-y-1/2 text-white text-4xl bg-black/30 hover:bg-black/60 border-none cursor-pointer rounded-full w-12 h-12 flex items-center justify-center transition-all"><i class="fa-solid fa-chevron-right"></i></button>
    <img class="lightbox-img max-w-[90vw] max-h-[85vh] object-contain rounded-lg" src="" alt="">
  </div>
  NOTE: Each gallery item MUST have a unique {{IMG:gallery ...}} query. JS handles lightbox open/close/navigation.""",
    "image_carousel": """image_carousel pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="carousel-container max-w-[1200px] mx-auto px-6 relative overflow-hidden rounded-[var(--radius)]" data-aos="fade-up">
    <div class="carousel-track flex transition-transform duration-500 ease-in-out">
      <div class="carousel-slide min-w-full relative">
        <img src="{{IMG:carousel specific image query}}" alt="Slide title" class="w-full h-[400px] md:h-[500px] object-cover">
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-8">
          <h3 class="text-xl md:text-2xl font-bold text-white mb-2">Slide Title</h3>
          <p class="text-white/80 text-sm md:text-base max-w-lg">Slide description text</p>
        </div>
      </div>
      <!-- Repeat for each slide (3-5 slides) -->
    </div>
    <button class="carousel-prev absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm border-none text-white cursor-pointer flex items-center justify-center hover:bg-white/40 transition-all z-10"><i class="fa-solid fa-chevron-left"></i></button>
    <button class="carousel-next absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm border-none text-white cursor-pointer flex items-center justify-center hover:bg-white/40 transition-all z-10"><i class="fa-solid fa-chevron-right"></i></button>
    <div class="carousel-dots flex justify-center gap-2 mt-6">
      <button class="carousel-dot w-3 h-3 rounded-full border-2 border-[var(--primary)] bg-transparent cursor-pointer p-0 transition-all active" data-slide="0"></button>
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
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div class="modal-trigger bg-[var(--bg-surface)] rounded-[var(--radius)] p-6 md:p-8 shadow-md hover:-translate-y-2 hover:shadow-xl transition-all duration-300 border border-white/[0.06] cursor-pointer group" data-modal="modal-1" data-aos="fade-right" data-aos-delay="100">
      <div class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--accent)] mb-5 group-hover:scale-110 transition-transform" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="text-lg font-bold mb-2 text-[var(--text)]">Service Title</h3>
      <p class="text-[var(--text-muted)] leading-relaxed text-sm mb-3">Short description visible on the card.</p>
      <span class="text-[var(--accent)] text-sm font-semibold inline-flex items-center gap-1">Learn More <i class="fa-solid fa-arrow-right text-xs"></i></span>
    </div>
  </div>
  <!-- Modals (one per card, hidden by default) -->
  <div id="modal-1" class="detail-modal fixed inset-0 z-[9999] bg-black/60 hidden items-center justify-center p-4">
    <div class="bg-[var(--bg)] rounded-[var(--radius)] max-w-lg w-full p-8 relative shadow-2xl max-h-[90vh] overflow-y-auto">
      <button class="modal-close absolute top-4 right-4 text-[var(--text-muted)] hover:text-[var(--text)] text-xl bg-transparent border-none cursor-pointer">&times;</button>
      <div class="w-14 h-14 rounded-xl flex items-center justify-center text-xl text-[var(--accent)] mb-5" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="text-xl font-bold mb-3 text-[var(--text)]">Service Title</h3>
      <p class="text-[var(--text-muted)] leading-relaxed">Expanded detailed description of this service. Include specifics, benefits, process details, what the client gets, etc.</p>
    </div>
  </div>
  NOTE: Each card has data-modal="modal-N" pointing to matching modal ID. Use modal-1, modal-2, modal-3, etc. Light themes use border-gray-100. JS handles open/close.""",
    "timeline": """timeline pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="timeline-container max-w-[800px] mx-auto px-6 relative">
    <div class="flex gap-6 items-start py-8 relative" data-aos="fade-up" data-aos-delay="100">
      <div class="min-w-[80px] text-right">
        <span class="text-sm font-bold text-[var(--accent)]">2020</span>
      </div>
      <div class="w-4 h-4 min-w-[1rem] rounded-full bg-[var(--primary)] mt-1 z-10 shadow-lg ring-4 ring-[var(--bg)]"></div>
      <div class="flex-1 bg-[var(--bg-surface)] rounded-[var(--radius)] p-5 shadow-md border border-white/[0.06]">
        <h3 class="text-lg font-bold mb-1 text-[var(--text)]">Milestone Title</h3>
        <p class="text-sm text-[var(--text-muted)] leading-relaxed">Description of what happened at this milestone.</p>
      </div>
    </div>
    <!-- Repeat 4-6 milestones -->
  </div>
  NOTE: The connecting vertical line is handled by .timeline-container::before in the <style> block. Light themes use border-gray-100. Dates can be years, months, or descriptive phases.""",
    "newsletter_cta": """newsletter_cta pattern:
  <div class="max-w-[600px] mx-auto px-6 text-center">
    <h2 class="text-2xl md:text-3xl font-bold mb-3 text-[var(--text)]">Headline</h2>
    <p class="text-base text-[var(--text-muted)] mb-6 max-w-md mx-auto leading-relaxed">Short pitch about why they should subscribe.</p>
    <form class="newsletter-form flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
      <input type="email" placeholder="Enter your email" required class="flex-1 p-3.5 rounded-[var(--radius-btn)] border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10">
      <button type="submit" class="inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3.5 px-7 rounded-[var(--radius-btn)] font-semibold border-none cursor-pointer transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg whitespace-nowrap">Subscribe</button>
    </form>
    <p class="text-xs text-[var(--text-muted)] mt-3 opacity-70">No spam. Unsubscribe anytime.</p>
  </div>
  NOTE: Light themes use border-gray-200 on input. JS handles form submit with inline success message (not alert).""",
    "comparison_table": """comparison_table pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[800px] mx-auto px-6 overflow-x-auto" data-aos="fade-up">
    <table class="w-full border-collapse text-left">
      <thead>
        <tr>
          <th class="py-4 px-4 text-sm font-semibold text-[var(--text-muted)] border-b border-white/10">Feature</th>
          <th class="py-4 px-4 text-sm font-bold text-[var(--accent)] border-b border-white/10 text-center">Our Product</th>
          <th class="py-4 px-4 text-sm font-semibold text-[var(--text-muted)] border-b border-white/10 text-center">Competitor</th>
        </tr>
      </thead>
      <tbody>
        <tr class="border-b border-white/[0.06] hover:bg-white/[0.02] transition-colors">
          <td class="py-3.5 px-4 text-sm text-[var(--text)]">Feature name</td>
          <td class="py-3.5 px-4 text-center"><i class="fa-solid fa-check text-emerald-500"></i></td>
          <td class="py-3.5 px-4 text-center"><i class="fa-solid fa-xmark text-red-400 opacity-50"></i></td>
        </tr>
        <!-- Repeat 5-8 feature rows -->
      </tbody>
    </table>
  </div>
  NOTE: Use fa-check (green) for included features, fa-xmark (red/dim) for missing. Some cells can have text instead of icons. Light themes use border-gray-200.""",
    "logo_cloud": """logo_cloud pattern:
  <div class="text-center mb-6"><h2 class="text-lg md:text-xl font-semibold text-[var(--text-muted)]">Headline</h2></div>
  <div class="max-w-[1200px] mx-auto px-6 flex flex-wrap justify-center items-center gap-6">
    <div class="px-4 py-3" data-aos="fade-up" data-aos-delay="100">
      <span class="text-base font-bold tracking-wide opacity-40 hover:opacity-80 transition-all duration-300 whitespace-nowrap text-[var(--text)]">Company 1</span>
    </div>
    <div class="px-4 py-3" data-aos="fade-up" data-aos-delay="200">
      <span class="text-base font-bold tracking-wide opacity-40 hover:opacity-80 transition-all duration-300 whitespace-nowrap text-[var(--text)]">Company 2</span>
    </div>
  </div>
  NOTE: Text-only logos. Do NOT use <img> tags, dummyimage.com, or any image URLs for logos.""",
    "logo_carousel": """logo_carousel pattern:
  <div class="text-center mb-6"><h2 class="text-lg md:text-xl font-semibold text-[var(--text-muted)]">Headline</h2></div>
  <div class="logo-carousel-container overflow-hidden relative max-w-[1200px] mx-auto">
    <div class="logo-carousel-track flex gap-12 items-center whitespace-nowrap">
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 1</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 2</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 3</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 4</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 5</span>
      <span class="text-base font-bold tracking-wide opacity-40 text-[var(--text)] inline-block px-4">Company 6</span>
      <!-- JS duplicates these for infinite scroll effect -->
    </div>
  </div>
  NOTE: Text-only logos, NO images. JS handles infinite scroll by duplicating track content. The carousel auto-scrolls continuously.""",
    "trust_badges": """trust_badges pattern:
  <div class="max-w-[1000px] mx-auto px-6 flex flex-wrap justify-center items-center gap-8 md:gap-12">
    <div class="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity" data-aos="fade-right" data-aos-delay="100">
      <i class="fa-solid fa-shield-halved text-2xl text-[var(--accent)]"></i>
      <div><span class="text-sm font-bold text-[var(--text)] block">SSL Secured</span><span class="text-xs text-[var(--text-muted)]">256-bit encryption</span></div>
    </div>
    <div class="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity" data-aos="fade-right" data-aos-delay="200">
      <i class="fa-solid fa-certificate text-2xl text-[var(--accent)]"></i>
      <div><span class="text-sm font-bold text-[var(--text)] block">ISO 27001</span><span class="text-xs text-[var(--text-muted)]">Certified</span></div>
    </div>
  </div>
  NOTE: 3-5 badges. Pick industry-relevant certifications: GDPR, HIPAA, SOC2, ISO, PCI-DSS, DED Licensed, TDRA Approved, etc. Compact section — use py-10 md:py-12.""",
    "contact_split": """contact_split pattern:
  <div class="text-center mb-8 md:mb-10"><h2 class="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 text-[var(--text)]">Headline</h2><p class="text-base md:text-lg text-[var(--text-muted)] max-w-xl mx-auto leading-relaxed">Subheadline</p></div>
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12">
    <div class="space-y-6">
      <div class="flex gap-4 items-start"><i class="fa-solid fa-location-dot text-lg text-[var(--accent)] w-5 mt-1"></i><p class="text-[var(--text-muted)]">Address</p></div>
      <div class="flex gap-4 items-start"><i class="fa-solid fa-phone text-lg text-[var(--accent)] w-5 mt-1"></i><p class="text-[var(--text-muted)]">Phone</p></div>
      <div class="flex gap-4 items-start"><i class="fa-solid fa-envelope text-lg text-[var(--accent)] w-5 mt-1"></i><p class="text-[var(--text-muted)]">Email</p></div>
    </div>
    <form class="space-y-4">
      <input type="text" placeholder="Your Name" required class="w-full p-4 rounded-lg border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10">
      <input type="email" placeholder="Your Email" required class="w-full p-4 rounded-lg border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10">
      <textarea placeholder="Your Message" rows="5" required class="w-full p-4 rounded-lg border border-white/10 bg-[var(--bg-surface)] text-[var(--text)] font-[inherit] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10 resize-y"></textarea>
      <button type="submit" class="BTN_PRIMARY_CLASSES">Send Message</button>
    </form>
  </div>
  NOTE: Light themes use border-gray-200 instead of border-white/10.""",
}
