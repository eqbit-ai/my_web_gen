"""Navigation (navbar + footer) pattern templates."""

# Style additions that are always needed
STYLE_ADDITIONS = ""

PATTERNS = {
    "navbar": """navbar pattern:
  <nav class="navbar">
    <div class="container navbar-inner">
      <a href="#" class="nav-brand">
        LOGO_MARK (see logo rules below)
        <span>Brand Name</span>
      </a>
      <button class="nav-toggle" aria-label="Toggle menu"><i class="fa-solid fa-bars"></i></button>
      <ul class="nav-links">
        <li><a href="#services">Services</a></li>
        <li class="mobile-cta"><a href="#" class="btn-primary">Get Started</a></li>
      </ul>
      <a href="#" class="nav-cta btn-primary">Get Started</a>
    </div>
  </nav>
  NAVBAR RULES (CRITICAL — MUST FOLLOW ALL):
  - Use navbar-light class for light themes, navbar-dark class for dark themes.
  - SINGLE PAGE ANCHOR LINKS (MANDATORY): Every navbar link MUST be an anchor link (href="#section-id") that scrolls to the corresponding section on the page. Use the section's data-section-type as the ID. Example: <a href="#services">Services</a> scrolls to <section data-section-type="services" id="services">. NEVER use href="/" or href="#" for navbar content links — they MUST point to actual sections.
  - EVERY <section data-section-type="X"> MUST also have id="X" so navbar anchor links work. Example: <section data-section-type="about" id="about">.
  - The first nav link should be href="#hero" pointing to the hero section.
  - CTA button in navbar should link to the contact or booking section: href="#contact".
  - MAX 5-6 nav links. Pick the most important sections.""",
    "footer_columns": """footer_columns pattern:
  CRITICAL: Footer MUST have ALL 4 columns. Do NOT skip any column. Do NOT output a minimal footer.
  <!-- Newsletter strip above footer columns -->
  <div class="container" style="border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:2.5rem;margin-bottom:2.5rem;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1.5rem;">
      <div>
        <h3 style="color:white;font-size:1.25rem;margin-bottom:0.25rem;">Stay Updated</h3>
        <p style="color:rgba(255,255,255,0.5);font-size:0.9rem;margin:0;">Subscribe to our newsletter for the latest updates.</p>
      </div>
      <form class="newsletter-form" style="display:flex;gap:0.75rem;flex-wrap:wrap;">
        <input type="email" placeholder="Enter your email" class="form-input" style="min-width:250px;background:rgba(255,255,255,0.06);border-color:rgba(255,255,255,0.1);color:white;">
        <button type="submit" class="btn-primary">Subscribe</button>
      </form>
    </div>
  </div>
  <div class="container footer-grid">
    <!-- COLUMN 1: Brand + description + social icons -->
    <div>
      <a href="#" class="nav-brand" style="color:white;margin-bottom:1rem;display:inline-flex;">
        SAME_LOGO_MARK_AS_NAVBAR (use the exact same logo mark from the navbar — keep it consistent)
        <span>Brand</span>
      </a>
      <p class="footer-description">Short brand description from the plan.</p>
      <div class="social-links">
        <a href="#" class="social-link"><i class="fa-brands fa-linkedin"></i></a>
        <a href="#" class="social-link"><i class="fa-brands fa-twitter"></i></a>
        <a href="#" class="social-link"><i class="fa-brands fa-instagram"></i></a>
      </div>
    </div>
    <!-- COLUMN 2: Quick Links — link to page sections using anchor hrefs -->
    <div>
      <h4 class="footer-heading">Quick Links</h4>
      <ul class="footer-links">
        <li><a href="#services">Services</a></li>
        <li><a href="#about">About Us</a></li>
        <li><a href="#testimonials">Testimonials</a></li>
        <li><a href="#faq">FAQ</a></li>
      </ul>
    </div>
    <!-- COLUMN 3: Services — list 4-5 actual services from the plan -->
    <div>
      <h4 class="footer-heading">Services</h4>
      <ul class="footer-links">
        <li><a href="#">Service Name 1</a></li>
        <li><a href="#">Service Name 2</a></li>
        <li><a href="#">Service Name 3</a></li>
        <li><a href="#">Service Name 4</a></li>
      </ul>
    </div>
    <!-- COLUMN 4: Contact info — address, phone, email, hours -->
    <div>
      <h4 class="footer-heading">Contact</h4>
      <ul class="footer-links">
        <li class="contact-item"><i class="fa-solid fa-location-dot contact-icon"></i><span>Office address, City, UAE</span></li>
        <li class="contact-item"><i class="fa-solid fa-phone contact-icon"></i><span>+971 XX XXX XXXX</span></li>
        <li class="contact-item"><i class="fa-solid fa-envelope contact-icon"></i><span>info@brand.ae</span></li>
        <li class="contact-item"><i class="fa-solid fa-clock contact-icon"></i><span>Sun-Thu: 9AM-6PM</span></li>
      </ul>
    </div>
  </div>
  <div class="container footer-bottom">
    <p>&copy; <span id="year"></span> Brand. All rights reserved.</p>
  </div>
  FOOTER RULES (CRITICAL — follow ALL):
  - Footer MUST include the newsletter strip above the 4 columns — this is standard for premium templates
  - Footer MUST have EXACTLY 4 columns: Brand+Social, Quick Links, Services, Contact
  - Quick Links column: use anchor links (#services, #about, etc.) matching actual page sections
  - Services column: list 4-5 real services from the plan — NOT placeholder text
  - Contact column: include address, phone, email, and business hours with icons. CRITICAL: If the user provided specific contact details (phone, email, address) in their prompt, use those EXACT values — do NOT make up different ones.
  - Footer section element MUST have an inline dark background: style="background: #1a1a2e" — this is MANDATORY regardless of theme. Footer is ALWAYS dark.
  - ALL footer text uses white/white-opacity colors. NEVER use dark text in footer.
  - NEVER output a minimal footer with just logo + address. ALL 4 columns + newsletter strip are mandatory.""",
}
