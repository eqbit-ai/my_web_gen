"""Navigation (navbar + footer) pattern templates."""

# Style additions that are always needed
STYLE_ADDITIONS = ""

PATTERNS = {
    "navbar": """navbar pattern:
  <nav class="fixed top-0 w-full z-50 backdrop-blur-md [bg-white/85 border-b border-black/[0.06] OR bg-black/40 border-b border-white/[0.08] based on theme] transition-all duration-300">
    <div class="max-w-[1200px] mx-auto px-6 flex justify-between items-center py-4">
      <a href="#" class="flex items-center gap-2.5 no-underline text-[var(--text)] font-bold text-lg">
        LOGO_MARK (see logo rules below)
        <span class="font-bold text-lg tracking-tight">Brand Name</span>
      </a>
      <button class="nav-toggle hidden bg-transparent border-none text-2xl cursor-pointer text-[var(--text)] p-2 min-w-[44px] min-h-[44px] flex items-center justify-center" aria-label="Toggle menu"><i class="fa-solid fa-bars"></i></button>
      <ul class="nav-links flex list-none gap-8 items-center m-0 p-0">
        <li><a href="#services" class="no-underline font-medium text-[var(--text)] hover:text-[var(--primary)] transition-colors duration-300">Services</a></li>
        <li class="mobile-cta hidden"><a href="#" class="inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline">Get Started</a></li>
      </ul>
      <a href="#" class="nav-cta inline-block bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] text-white py-3 px-7 rounded-[var(--radius-btn)] font-semibold no-underline transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg">Get Started</a>
    </div>
  </nav>
  NAVBAR RULES: Use bg-white/85 + border-black for light themes, bg-black/40 + border-white for dark themes.""",
    "footer_columns": """footer_columns pattern:
  CRITICAL: Footer MUST have ALL 4 columns. Do NOT skip any column. Do NOT output a minimal footer.
  <div class="max-w-[1200px] mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
    <!-- COLUMN 1: Brand + description + social icons -->
    <div class="mb-6">
      <a href="#" class="flex items-center gap-2.5 no-underline text-white font-bold text-lg mb-4">
        SAME_LOGO_MARK_AS_NAVBAR (use the exact same logo mark from the navbar — keep it consistent)
        <span class="font-bold text-lg tracking-tight">Brand</span>
      </a>
      <p class="text-sm text-white/60 leading-relaxed max-w-[280px]">Short brand description from the plan.</p>
      <div class="flex gap-3 mt-4">
        <a href="#" class="w-10 h-10 rounded-full bg-white/[0.08] flex items-center justify-center text-white border border-white/10 hover:bg-[var(--primary)] hover:border-[var(--primary)] hover:-translate-y-0.5 transition-all duration-300"><i class="fa-brands fa-linkedin"></i></a>
        <a href="#" class="w-10 h-10 rounded-full bg-white/[0.08] flex items-center justify-center text-white border border-white/10 hover:bg-[var(--primary)] hover:border-[var(--primary)] hover:-translate-y-0.5 transition-all duration-300"><i class="fa-brands fa-twitter"></i></a>
        <a href="#" class="w-10 h-10 rounded-full bg-white/[0.08] flex items-center justify-center text-white border border-white/10 hover:bg-[var(--primary)] hover:border-[var(--primary)] hover:-translate-y-0.5 transition-all duration-300"><i class="fa-brands fa-instagram"></i></a>
      </div>
    </div>
    <!-- COLUMN 2: Quick Links — link to page sections using anchor hrefs -->
    <div>
      <h4 class="font-bold text-white mb-4">Quick Links</h4>
      <ul class="list-none p-0 space-y-2">
        <li><a href="#services" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Services</a></li>
        <li><a href="#about" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">About Us</a></li>
        <li><a href="#testimonials" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Testimonials</a></li>
        <li><a href="#faq" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">FAQ</a></li>
      </ul>
    </div>
    <!-- COLUMN 3: Services — list 4-5 actual services from the plan -->
    <div>
      <h4 class="font-bold text-white mb-4">Services</h4>
      <ul class="list-none p-0 space-y-2">
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 1</a></li>
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 2</a></li>
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 3</a></li>
        <li><a href="#" class="text-white/70 no-underline hover:text-white transition-colors duration-300 text-sm">Service Name 4</a></li>
      </ul>
    </div>
    <!-- COLUMN 4: Contact info — address, phone, email, hours -->
    <div>
      <h4 class="font-bold text-white mb-4">Contact</h4>
      <ul class="list-none p-0 space-y-3">
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-location-dot text-[var(--accent)] mt-1 w-4"></i><span>Office address, City, UAE</span></li>
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-phone text-[var(--accent)] mt-1 w-4"></i><span>+971 XX XXX XXXX</span></li>
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-envelope text-[var(--accent)] mt-1 w-4"></i><span>info@brand.ae</span></li>
        <li class="flex items-start gap-2 text-sm text-white/60"><i class="fa-solid fa-clock text-[var(--accent)] mt-1 w-4"></i><span>Sun-Thu: 9AM-6PM</span></li>
      </ul>
    </div>
  </div>
  <div class="max-w-[1200px] mx-auto px-6 border-t border-white/[0.08] mt-10 pt-6 text-center text-sm text-white/50">
    <p>&copy; <span id="year"></span> Brand. All rights reserved.</p>
  </div>
  FOOTER RULES (CRITICAL — follow ALL):
  - Footer MUST have EXACTLY 4 columns: Brand+Social, Quick Links, Services, Contact
  - Quick Links column: use anchor links (#services, #about, etc.) matching actual page sections
  - Services column: list 4-5 real services from the plan — NOT placeholder text
  - Contact column: include address, phone, email, and business hours with icons
  - Footer section element MUST have an inline dark background: style="background: #1a1a2e" — this is MANDATORY regardless of theme. Footer is ALWAYS dark.
  - ALL footer text uses white/white-opacity colors (text-white, text-white/70, text-white/60, text-white/50). NEVER use dark text in footer.
  - NEVER output a minimal footer with just logo + address. ALL 4 columns are mandatory.""",
}
