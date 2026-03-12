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
  NAVBAR RULES: Use navbar-light class for light themes, navbar-dark class for dark themes.""",
    "footer_columns": """footer_columns pattern:
  CRITICAL: Footer MUST have ALL 4 columns. Do NOT skip any column. Do NOT output a minimal footer.
  <div class="container footer-grid">
    <!-- COLUMN 1: Brand + description + social icons -->
    <div>
      <a href="#" class="nav-brand">
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
  - Footer MUST have EXACTLY 4 columns: Brand+Social, Quick Links, Services, Contact
  - Quick Links column: use anchor links (#services, #about, etc.) matching actual page sections
  - Services column: list 4-5 real services from the plan — NOT placeholder text
  - Contact column: include address, phone, email, and business hours with icons
  - Footer section element MUST have an inline dark background: style="background: #1a1a2e" — this is MANDATORY regardless of theme. Footer is ALWAYS dark.
  - ALL footer text uses white/white-opacity colors. NEVER use dark text in footer.
  - NEVER output a minimal footer with just logo + address. ALL 4 columns are mandatory.""",
}
