"""
High-quality HTML reference snippets for each section type.
These serve as per-section quality references for Claude during generation.
Each snippet uses Tailwind CSS utility classes and {{IMG:description}} placeholders.
"""

import random
from typing import Optional


SECTION_REFERENCES = {
    # ─── HERO ──────────────────────────────────────────────────────────
    "hero": [
        {
            "name": "split_hero_with_image",
            "style": "modern",
            "description": "Split layout: text left, image right, gradient overlay, CTA buttons",
            "html": '''<section data-section-type="hero" class="relative min-h-[90vh] flex items-center bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8 grid lg:grid-cols-2 gap-12 items-center">
    <div class="space-y-8">
      <span class="inline-block px-4 py-1.5 bg-[var(--primary)]/10 text-[var(--primary)] rounded-full text-sm font-medium tracking-wide">Trusted by 500+ Companies</span>
      <h1 class="text-5xl lg:text-6xl font-bold leading-tight text-[var(--text)]" style="font-family:var(--font-heading)">Build Something People Actually Want</h1>
      <p class="text-lg text-[var(--text-muted)] max-w-lg leading-relaxed">Streamline your workflow, collaborate seamlessly, and ship products faster with our all-in-one platform designed for modern teams.</p>
      <div class="flex flex-wrap gap-4">
        <a href="#contact" class="px-8 py-3.5 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] font-semibold hover:opacity-90 transition-all shadow-lg shadow-[var(--primary)]/25">Start Free Trial</a>
        <a href="#features" class="px-8 py-3.5 border-2 border-[var(--text)]/20 text-[var(--text)] rounded-[var(--radius-btn)] font-semibold hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all">See How It Works</a>
      </div>
      <div class="flex items-center gap-6 pt-2">
        <div class="flex -space-x-3">
          <div class="w-10 h-10 rounded-full bg-[var(--primary)]/20 border-2 border-white"></div>
          <div class="w-10 h-10 rounded-full bg-[var(--accent)]/20 border-2 border-white"></div>
          <div class="w-10 h-10 rounded-full bg-[var(--secondary)]/20 border-2 border-white"></div>
        </div>
        <p class="text-sm text-[var(--text-muted)]"><strong class="text-[var(--text)]">2,000+</strong> teams already on board</p>
      </div>
    </div>
    <div class="relative">
      <div class="absolute -inset-4 bg-[var(--primary)]/5 rounded-3xl blur-2xl"></div>
      <img src="{{IMG:professional team collaborating on modern software dashboard}}" alt="Platform preview" class="relative rounded-2xl shadow-2xl w-full" />
    </div>
  </div>
</section>''',
        },
        {
            "name": "full_background_hero",
            "style": "bold",
            "description": "Full-screen background image with centered text overlay and dark gradient",
            "html": '''<section data-section-type="hero" class="relative min-h-screen flex items-center justify-center overflow-hidden">
  <div class="absolute inset-0">
    <img src="{{IMG:dramatic aerial cityscape at sunset with modern architecture}}" alt="Background" class="w-full h-full object-cover" />
    <div class="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black/80"></div>
  </div>
  <div class="relative z-10 max-w-4xl mx-auto px-6 text-center space-y-8">
    <h1 class="text-5xl md:text-7xl font-bold text-white leading-tight" style="font-family:var(--font-heading)">Elevate Your Business to New Heights</h1>
    <p class="text-xl text-white/80 max-w-2xl mx-auto leading-relaxed">We partner with forward-thinking companies to deliver strategies that drive measurable growth and lasting impact.</p>
    <div class="flex flex-wrap justify-center gap-4 pt-4">
      <a href="#contact" class="px-10 py-4 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] font-semibold text-lg hover:opacity-90 transition-all shadow-xl">Get Started Today</a>
      <a href="#about" class="px-10 py-4 bg-white/10 backdrop-blur-sm text-white border border-white/30 rounded-[var(--radius-btn)] font-semibold text-lg hover:bg-white/20 transition-all">Learn More</a>
    </div>
  </div>
  <div class="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
    <i class="fa-solid fa-chevron-down text-white/60 text-2xl"></i>
  </div>
</section>''',
        },
        {
            "name": "gradient_hero",
            "style": "vibrant",
            "description": "Gradient background with centered content, floating shapes, and stats bar",
            "html": '''<section data-section-type="hero" class="relative min-h-[90vh] flex items-center overflow-hidden" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">
  <div class="absolute inset-0 overflow-hidden">
    <div class="absolute top-20 left-10 w-72 h-72 bg-white/10 rounded-full blur-3xl"></div>
    <div class="absolute bottom-20 right-10 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>
  </div>
  <div class="relative z-10 max-w-5xl mx-auto px-6 text-center space-y-8">
    <span class="inline-block px-5 py-2 bg-white/15 backdrop-blur-sm text-white rounded-full text-sm font-medium">New: AI-Powered Analytics Now Live</span>
    <h1 class="text-5xl md:text-7xl font-bold text-white leading-tight" style="font-family:var(--font-heading)">The Smarter Way to Grow Your Revenue</h1>
    <p class="text-xl text-white/85 max-w-2xl mx-auto">Harness real-time data insights, automate your marketing pipeline, and convert more leads with intelligent workflows.</p>
    <div class="flex flex-wrap justify-center gap-4">
      <a href="#pricing" class="px-10 py-4 bg-white text-[var(--primary)] rounded-[var(--radius-btn)] font-bold text-lg hover:shadow-xl transition-all">Start Free Trial</a>
      <a href="#demo" class="px-10 py-4 border-2 border-white/40 text-white rounded-[var(--radius-btn)] font-semibold text-lg hover:bg-white/10 transition-all flex items-center gap-2"><i class="fa-solid fa-play"></i> Watch Demo</a>
    </div>
  </div>
  <div class="absolute bottom-0 left-0 right-0 bg-black/20 backdrop-blur-sm border-t border-white/10">
    <div class="max-w-6xl mx-auto px-6 py-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
      <div><p class="text-3xl font-bold text-white">50K+</p><p class="text-white/60 text-sm">Active Users</p></div>
      <div><p class="text-3xl font-bold text-white">99.9%</p><p class="text-white/60 text-sm">Uptime SLA</p></div>
      <div><p class="text-3xl font-bold text-white">150+</p><p class="text-white/60 text-sm">Integrations</p></div>
      <div><p class="text-3xl font-bold text-white">4.9/5</p><p class="text-white/60 text-sm">User Rating</p></div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "video_style_hero",
            "style": "cinematic",
            "description": "Video-style hero with play button overlay and minimal text",
            "html": '''<section data-section-type="hero" class="relative min-h-screen flex items-center bg-[#0a0a0a]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8 grid lg:grid-cols-2 gap-16 items-center">
    <div class="space-y-8">
      <div class="flex items-center gap-3">
        <span class="w-12 h-[2px] bg-[var(--primary)]"></span>
        <span class="text-[var(--primary)] text-sm font-semibold tracking-widest uppercase">Award-Winning Agency</span>
      </div>
      <h1 class="text-5xl lg:text-6xl font-bold text-white leading-tight" style="font-family:var(--font-heading)">We Create Digital Experiences That Matter</h1>
      <p class="text-lg text-gray-400 max-w-md leading-relaxed">From strategy to execution, we craft digital products that captivate audiences and deliver real business results.</p>
      <a href="#work" class="inline-flex items-center gap-3 text-white font-semibold group">
        <span>View Our Work</span>
        <i class="fa-solid fa-arrow-right group-hover:translate-x-2 transition-transform"></i>
      </a>
    </div>
    <div class="relative group cursor-pointer">
      <img src="{{IMG:cinematic dark studio with creative team working on digital project}}" alt="Our work" class="rounded-2xl w-full brightness-75 group-hover:brightness-90 transition-all duration-500" />
      <div class="absolute inset-0 flex items-center justify-center">
        <div class="w-20 h-20 bg-[var(--primary)] rounded-full flex items-center justify-center shadow-2xl group-hover:scale-110 transition-transform">
          <i class="fa-solid fa-play text-white text-xl ml-1"></i>
        </div>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "minimal_hero",
            "style": "clean",
            "description": "Ultra-clean minimal hero with large typography and single CTA",
            "html": '''<section data-section-type="hero" class="min-h-[85vh] flex items-center bg-[var(--bg)]">
  <div class="max-w-5xl mx-auto px-6 space-y-10">
    <h1 class="text-6xl md:text-8xl font-bold text-[var(--text)] leading-[1.1] tracking-tight" style="font-family:var(--font-heading)">Design that<br/><span class="text-[var(--primary)]">speaks volumes.</span></h1>
    <p class="text-xl text-[var(--text-muted)] max-w-xl leading-relaxed">We help brands find their voice through thoughtful design, clear strategy, and meticulous execution.</p>
    <div class="flex items-center gap-8">
      <a href="#contact" class="px-8 py-3.5 bg-[var(--text)] text-[var(--bg)] rounded-[var(--radius-btn)] font-semibold hover:opacity-80 transition-all">Get in Touch</a>
      <a href="#work" class="text-[var(--text-muted)] hover:text-[var(--text)] font-medium transition-colors flex items-center gap-2">Our Projects <i class="fa-solid fa-arrow-right"></i></a>
    </div>
  </div>
</section>''',
        },
    ],

    # ─── FEATURES ──────────────────────────────────────────────────────
    "features": [
        {
            "name": "icon_grid_features",
            "style": "clean",
            "description": "3-column icon grid with hover effects and descriptive text",
            "html": '''<section data-section-type="features" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <span class="text-[var(--primary)] font-semibold text-sm tracking-widest uppercase">What We Offer</span>
      <h2 class="text-4xl font-bold text-[var(--text)] mt-4 mb-6" style="font-family:var(--font-heading)">Everything You Need to Scale</h2>
      <p class="text-lg text-[var(--text-muted)]">Our platform provides the essential tools and integrations your team needs to work faster and deliver better results.</p>
    </div>
    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
      <div class="p-8 rounded-[var(--radius)] bg-[var(--bg-surface)] hover:shadow-xl transition-all duration-300 group" data-aos="fade-up" data-aos-delay="100">
        <div class="w-14 h-14 rounded-2xl bg-[var(--primary)]/10 flex items-center justify-center mb-6 group-hover:bg-[var(--primary)] transition-colors">
          <i class="fa-solid fa-bolt text-[var(--primary)] text-xl group-hover:text-white transition-colors"></i>
        </div>
        <h3 class="text-xl font-bold text-[var(--text)] mb-3">Lightning Fast Setup</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Get up and running in under five minutes. No complex configuration, no technical expertise required.</p>
      </div>
      <div class="p-8 rounded-[var(--radius)] bg-[var(--bg-surface)] hover:shadow-xl transition-all duration-300 group" data-aos="fade-up" data-aos-delay="200">
        <div class="w-14 h-14 rounded-2xl bg-[var(--primary)]/10 flex items-center justify-center mb-6 group-hover:bg-[var(--primary)] transition-colors">
          <i class="fa-solid fa-shield-halved text-[var(--primary)] text-xl group-hover:text-white transition-colors"></i>
        </div>
        <h3 class="text-xl font-bold text-[var(--text)] mb-3">Enterprise Security</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Bank-grade encryption, SOC 2 compliance, and role-based access control keep your data safe at all times.</p>
      </div>
      <div class="p-8 rounded-[var(--radius)] bg-[var(--bg-surface)] hover:shadow-xl transition-all duration-300 group" data-aos="fade-up" data-aos-delay="300">
        <div class="w-14 h-14 rounded-2xl bg-[var(--primary)]/10 flex items-center justify-center mb-6 group-hover:bg-[var(--primary)] transition-colors">
          <i class="fa-solid fa-chart-line text-[var(--primary)] text-xl group-hover:text-white transition-colors"></i>
        </div>
        <h3 class="text-xl font-bold text-[var(--text)] mb-3">Advanced Analytics</h3>
        <p class="text-[var(--text-muted)] leading-relaxed">Real-time dashboards and custom reports give you deep visibility into every aspect of your operations.</p>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "card_grid_features",
            "style": "modern",
            "description": "Card-based feature grid with icons, borders, and number badges",
            "html": '''<section data-section-type="features" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-6" style="font-family:var(--font-heading)">Powerful Features, Simple Interface</h2>
      <p class="text-lg text-[var(--text-muted)]">Designed with simplicity in mind, packed with the capabilities your business demands.</p>
    </div>
    <div class="grid md:grid-cols-2 gap-6">
      <div class="flex gap-5 p-6 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5 hover:border-[var(--primary)]/30 transition-all" data-aos="fade-up" data-aos-delay="100">
        <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-[var(--primary)] flex items-center justify-center text-white font-bold text-lg">1</div>
        <div>
          <h3 class="text-lg font-bold text-[var(--text)] mb-2">Smart Automation</h3>
          <p class="text-[var(--text-muted)] text-sm leading-relaxed">Automate repetitive tasks with intelligent workflows that learn from your patterns and adapt over time.</p>
        </div>
      </div>
      <div class="flex gap-5 p-6 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5 hover:border-[var(--primary)]/30 transition-all" data-aos="fade-up" data-aos-delay="200">
        <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-[var(--primary)] flex items-center justify-center text-white font-bold text-lg">2</div>
        <div>
          <h3 class="text-lg font-bold text-[var(--text)] mb-2">Team Collaboration</h3>
          <p class="text-[var(--text-muted)] text-sm leading-relaxed">Real-time editing, comments, and shared workspaces keep everyone aligned and productive.</p>
        </div>
      </div>
      <div class="flex gap-5 p-6 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5 hover:border-[var(--primary)]/30 transition-all" data-aos="fade-up" data-aos-delay="300">
        <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-[var(--primary)] flex items-center justify-center text-white font-bold text-lg">3</div>
        <div>
          <h3 class="text-lg font-bold text-[var(--text)] mb-2">Custom Integrations</h3>
          <p class="text-[var(--text-muted)] text-sm leading-relaxed">Connect with 200+ tools you already use, including Slack, Salesforce, HubSpot, and Google Workspace.</p>
        </div>
      </div>
      <div class="flex gap-5 p-6 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5 hover:border-[var(--primary)]/30 transition-all" data-aos="fade-up" data-aos-delay="400">
        <div class="flex-shrink-0 w-12 h-12 rounded-xl bg-[var(--primary)] flex items-center justify-center text-white font-bold text-lg">4</div>
        <div>
          <h3 class="text-lg font-bold text-[var(--text)] mb-2">Priority Support</h3>
          <p class="text-[var(--text-muted)] text-sm leading-relaxed">Dedicated account managers and 24/7 live chat ensure you always have expert help when you need it.</p>
        </div>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "alternating_rows_features",
            "style": "editorial",
            "description": "Alternating image-text rows with large visuals",
            "html": '''<section data-section-type="features" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8 space-y-24">
    <div class="grid lg:grid-cols-2 gap-16 items-center" data-aos="fade-up">
      <div class="space-y-6">
        <span class="inline-block px-3 py-1 bg-[var(--primary)]/10 text-[var(--primary)] rounded-full text-xs font-semibold tracking-widest uppercase">Workflow</span>
        <h2 class="text-3xl font-bold text-[var(--text)]" style="font-family:var(--font-heading)">Manage Projects with Visual Clarity</h2>
        <p class="text-[var(--text-muted)] leading-relaxed">Drag-and-drop boards, timeline views, and automated status updates give your team a clear picture of every project at every stage.</p>
        <ul class="space-y-3">
          <li class="flex items-center gap-3 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--primary)]"></i> Kanban, list, and calendar views</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--primary)]"></i> Custom fields and filters</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--primary)]"></i> Automated task assignments</li>
        </ul>
      </div>
      <div>
        <img src="{{IMG:clean project management dashboard with kanban board interface}}" alt="Project management" class="rounded-2xl shadow-xl w-full" />
      </div>
    </div>
    <div class="grid lg:grid-cols-2 gap-16 items-center" data-aos="fade-up">
      <div class="order-2 lg:order-1">
        <img src="{{IMG:analytics dashboard showing colorful charts and real-time data}}" alt="Analytics" class="rounded-2xl shadow-xl w-full" />
      </div>
      <div class="order-1 lg:order-2 space-y-6">
        <span class="inline-block px-3 py-1 bg-[var(--accent)]/10 text-[var(--accent)] rounded-full text-xs font-semibold tracking-widest uppercase">Analytics</span>
        <h2 class="text-3xl font-bold text-[var(--text)]" style="font-family:var(--font-heading)">Data-Driven Decisions, Made Easy</h2>
        <p class="text-[var(--text-muted)] leading-relaxed">Transform raw data into actionable insights with interactive dashboards and automated reporting that surface what matters most.</p>
        <ul class="space-y-3">
          <li class="flex items-center gap-3 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--accent)]"></i> Real-time performance metrics</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--accent)]"></i> Exportable PDF and CSV reports</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)]"><i class="fa-solid fa-check text-[var(--accent)]"></i> Custom goal tracking</li>
        </ul>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "bento_grid_features",
            "style": "trendy",
            "description": "Bento-style asymmetric grid with mixed card sizes",
            "html": '''<section data-section-type="features" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-6" style="font-family:var(--font-heading)">Built for Modern Teams</h2>
      <p class="text-lg text-[var(--text-muted)]">A toolkit that adapts to how you work, not the other way around.</p>
    </div>
    <div class="grid md:grid-cols-3 gap-4">
      <div class="md:col-span-2 p-8 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5 relative overflow-hidden group" data-aos="fade-up" data-aos-delay="100">
        <div class="relative z-10">
          <div class="w-10 h-10 rounded-lg bg-[var(--primary)]/10 flex items-center justify-center mb-4"><i class="fa-solid fa-rocket text-[var(--primary)]"></i></div>
          <h3 class="text-xl font-bold text-[var(--text)] mb-2">Rapid Deployment</h3>
          <p class="text-[var(--text-muted)] max-w-md">Ship to production in minutes with one-click deployments, automatic rollbacks, and zero-downtime releases.</p>
        </div>
        <div class="absolute -bottom-8 -right-8 w-40 h-40 bg-[var(--primary)]/5 rounded-full blur-2xl group-hover:bg-[var(--primary)]/10 transition-colors"></div>
      </div>
      <div class="p-8 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="200">
        <div class="w-10 h-10 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center mb-4"><i class="fa-solid fa-lock text-[var(--accent)]"></i></div>
        <h3 class="text-xl font-bold text-[var(--text)] mb-2">Secure by Default</h3>
        <p class="text-[var(--text-muted)] text-sm">End-to-end encryption and compliance built into every layer.</p>
      </div>
      <div class="p-8 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="300">
        <div class="w-10 h-10 rounded-lg bg-[var(--secondary)]/10 flex items-center justify-center mb-4"><i class="fa-solid fa-plug text-[var(--secondary)]"></i></div>
        <h3 class="text-xl font-bold text-[var(--text)] mb-2">200+ Integrations</h3>
        <p class="text-[var(--text-muted)] text-sm">Connect your existing stack in a few clicks.</p>
      </div>
      <div class="md:col-span-2 p-8 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="400">
        <div class="w-10 h-10 rounded-lg bg-[var(--primary)]/10 flex items-center justify-center mb-4"><i class="fa-solid fa-users text-[var(--primary)]"></i></div>
        <h3 class="text-xl font-bold text-[var(--text)] mb-2">Built for Collaboration</h3>
        <p class="text-[var(--text-muted)] max-w-lg">Shared workspaces, real-time cursors, threaded comments, and granular permissions for teams of any size.</p>
      </div>
    </div>
  </div>
</section>''',
        },
    ],

    # ─── TESTIMONIALS ──────────────────────────────────────────────────
    "testimonials": [
        {
            "name": "carousel_single_testimonial",
            "style": "elegant",
            "description": "Single large testimonial with photo, name, and company",
            "html": '''<section data-section-type="testimonials" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-4xl mx-auto px-6 text-center">
    <span class="text-[var(--primary)] font-semibold text-sm tracking-widest uppercase">Testimonials</span>
    <h2 class="text-4xl font-bold text-[var(--text)] mt-4 mb-16" style="font-family:var(--font-heading)">What Our Clients Say</h2>
    <div class="relative">
      <i class="fa-solid fa-quote-left text-[var(--primary)]/20 text-6xl absolute -top-4 left-0"></i>
      <blockquote class="text-2xl text-[var(--text)] leading-relaxed font-medium italic px-8">"Switching to this platform cut our deployment time by 80%. The team collaboration features alone have transformed how we ship products. It is genuinely the best investment we have made this year."</blockquote>
      <div class="mt-10 flex items-center justify-center gap-4">
        <img src="{{IMG:professional headshot of business executive woman}}" alt="Sarah Chen" class="w-14 h-14 rounded-full object-cover" />
        <div class="text-left">
          <p class="font-semibold text-[var(--text)]">Sarah Chen</p>
          <p class="text-sm text-[var(--text-muted)]">VP of Engineering, TechCorp</p>
        </div>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "grid_testimonial_cards",
            "style": "modern",
            "description": "3-column grid of testimonial cards with star ratings",
            "html": '''<section data-section-type="testimonials" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Trusted by Industry Leaders</h2>
      <p class="text-lg text-[var(--text-muted)]">Join thousands of companies that rely on us every day.</p>
    </div>
    <div class="grid md:grid-cols-3 gap-8">
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] shadow-sm" data-aos="fade-up" data-aos-delay="100">
        <div class="flex gap-1 text-yellow-400 mb-4"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <p class="text-[var(--text-muted)] leading-relaxed mb-6">"The onboarding was seamless and our team was productive within the first week. Support has been incredibly responsive to every question."</p>
        <div class="flex items-center gap-3 border-t border-[var(--text)]/10 pt-6">
          <div class="w-10 h-10 rounded-full bg-[var(--primary)]/20 flex items-center justify-center text-[var(--primary)] font-bold">M</div>
          <div><p class="font-semibold text-[var(--text)] text-sm">Marcus Rivera</p><p class="text-xs text-[var(--text-muted)]">CEO, Bloom Digital</p></div>
        </div>
      </div>
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] shadow-sm" data-aos="fade-up" data-aos-delay="200">
        <div class="flex gap-1 text-yellow-400 mb-4"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <p class="text-[var(--text-muted)] leading-relaxed mb-6">"We evaluated five different platforms. This one had the best balance of power and simplicity. Our conversion rates increased 35% in three months."</p>
        <div class="flex items-center gap-3 border-t border-[var(--text)]/10 pt-6">
          <div class="w-10 h-10 rounded-full bg-[var(--accent)]/20 flex items-center justify-center text-[var(--accent)] font-bold">A</div>
          <div><p class="font-semibold text-[var(--text)] text-sm">Aisha Patel</p><p class="text-xs text-[var(--text-muted)]">Head of Growth, Nexus Labs</p></div>
        </div>
      </div>
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] shadow-sm" data-aos="fade-up" data-aos-delay="300">
        <div class="flex gap-1 text-yellow-400 mb-4"><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i></div>
        <p class="text-[var(--text-muted)] leading-relaxed mb-6">"The automation features saved us 20 hours per week. What used to require three people now runs on autopilot with better accuracy."</p>
        <div class="flex items-center gap-3 border-t border-[var(--text)]/10 pt-6">
          <div class="w-10 h-10 rounded-full bg-[var(--secondary)]/20 flex items-center justify-center text-[var(--secondary)] font-bold">J</div>
          <div><p class="font-semibold text-[var(--text)] text-sm">James Okafor</p><p class="text-xs text-[var(--text-muted)]">COO, ScaleUp Ventures</p></div>
        </div>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "large_quote_testimonial",
            "style": "bold",
            "description": "Full-width large quote with background accent color",
            "html": '''<section data-section-type="testimonials" class="py-24 bg-[var(--primary)]">
  <div class="max-w-5xl mx-auto px-6 text-center">
    <i class="fa-solid fa-quote-left text-white/20 text-7xl mb-8"></i>
    <blockquote class="text-3xl md:text-4xl text-white leading-relaxed font-medium">"This platform did not just improve our workflow. It completely redefined how our team thinks about collaboration and delivery."</blockquote>
    <div class="mt-12 flex items-center justify-center gap-4">
      <img src="{{IMG:professional business man portrait in suit}}" alt="David Kim" class="w-16 h-16 rounded-full object-cover border-2 border-white/30" />
      <div class="text-left">
        <p class="font-semibold text-white text-lg">David Kim</p>
        <p class="text-white/70">CTO, Horizon Systems</p>
      </div>
    </div>
  </div>
</section>''',
        },
    ],

    # ─── PRICING ───────────────────────────────────────────────────────
    "pricing": [
        {
            "name": "three_column_pricing",
            "style": "standard",
            "description": "Classic 3-column pricing cards with highlighted popular plan",
            "html": '''<section data-section-type="pricing" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Simple, Transparent Pricing</h2>
      <p class="text-lg text-[var(--text-muted)]">No hidden fees. No surprises. Choose the plan that fits your team.</p>
    </div>
    <div class="grid md:grid-cols-3 gap-8 items-start">
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] border border-[var(--text)]/10" data-aos="fade-up" data-aos-delay="100">
        <h3 class="text-xl font-bold text-[var(--text)] mb-2">Starter</h3>
        <p class="text-[var(--text-muted)] text-sm mb-6">Perfect for small teams getting started.</p>
        <div class="mb-8"><span class="text-5xl font-bold text-[var(--text)]">$29</span><span class="text-[var(--text-muted)]">/month</span></div>
        <ul class="space-y-3 mb-8">
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> Up to 5 team members</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> 10 GB storage</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> Basic analytics</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> Email support</li>
        </ul>
        <a href="#contact" class="block text-center py-3 border-2 border-[var(--text)]/15 text-[var(--text)] rounded-[var(--radius-btn)] font-semibold hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all">Get Started</a>
      </div>
      <div class="p-8 bg-[var(--primary)] rounded-[var(--radius)] text-white relative shadow-xl shadow-[var(--primary)]/20 scale-105" data-aos="fade-up" data-aos-delay="200">
        <span class="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-[var(--accent)] text-white text-xs font-bold rounded-full uppercase tracking-wide">Most Popular</span>
        <h3 class="text-xl font-bold mb-2">Professional</h3>
        <p class="text-white/70 text-sm mb-6">Best for growing companies and teams.</p>
        <div class="mb-8"><span class="text-5xl font-bold">$79</span><span class="text-white/70">/month</span></div>
        <ul class="space-y-3 mb-8">
          <li class="flex items-center gap-3 text-white/80 text-sm"><i class="fa-solid fa-check"></i> Up to 25 team members</li>
          <li class="flex items-center gap-3 text-white/80 text-sm"><i class="fa-solid fa-check"></i> 100 GB storage</li>
          <li class="flex items-center gap-3 text-white/80 text-sm"><i class="fa-solid fa-check"></i> Advanced analytics</li>
          <li class="flex items-center gap-3 text-white/80 text-sm"><i class="fa-solid fa-check"></i> Priority support</li>
          <li class="flex items-center gap-3 text-white/80 text-sm"><i class="fa-solid fa-check"></i> Custom integrations</li>
        </ul>
        <a href="#contact" class="block text-center py-3 bg-white text-[var(--primary)] rounded-[var(--radius-btn)] font-semibold hover:opacity-90 transition-all">Get Started</a>
      </div>
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] border border-[var(--text)]/10" data-aos="fade-up" data-aos-delay="300">
        <h3 class="text-xl font-bold text-[var(--text)] mb-2">Enterprise</h3>
        <p class="text-[var(--text-muted)] text-sm mb-6">Custom solutions for large organizations.</p>
        <div class="mb-8"><span class="text-5xl font-bold text-[var(--text)]">Custom</span></div>
        <ul class="space-y-3 mb-8">
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> Unlimited members</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> Unlimited storage</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> Custom analytics</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> Dedicated account manager</li>
          <li class="flex items-center gap-3 text-[var(--text-muted)] text-sm"><i class="fa-solid fa-check text-[var(--primary)]"></i> SLA guarantee</li>
        </ul>
        <a href="#contact" class="block text-center py-3 border-2 border-[var(--text)]/15 text-[var(--text)] rounded-[var(--radius-btn)] font-semibold hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all">Contact Sales</a>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "toggle_pricing",
            "style": "interactive",
            "description": "Pricing with monthly/annual toggle and savings badge",
            "html": '''<section data-section-type="pricing" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Invest in Your Growth</h2>
      <p class="text-lg text-[var(--text-muted)] mb-8">Start free, upgrade when you are ready. Cancel anytime.</p>
      <div class="inline-flex items-center gap-4 p-1.5 bg-[var(--bg)] rounded-full border border-[var(--text)]/10">
        <button class="px-6 py-2 rounded-full bg-[var(--primary)] text-white text-sm font-semibold" data-pricing-toggle="monthly">Monthly</button>
        <button class="px-6 py-2 rounded-full text-[var(--text-muted)] text-sm font-semibold hover:text-[var(--text)] transition-colors" data-pricing-toggle="annual">Annual <span class="text-[var(--primary)] text-xs font-bold">Save 20%</span></button>
      </div>
    </div>
    <div class="grid md:grid-cols-3 gap-8">
      <div class="p-8 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/10 hover:shadow-lg transition-shadow" data-aos="fade-up" data-aos-delay="100">
        <h3 class="text-lg font-bold text-[var(--text)] mb-1">Basic</h3>
        <p class="text-sm text-[var(--text-muted)] mb-6">For individuals and freelancers</p>
        <div class="mb-6"><span class="text-4xl font-bold text-[var(--text)]" data-price-monthly="19" data-price-annual="15">$19</span><span class="text-[var(--text-muted)]">/mo</span></div>
        <a href="#" class="block text-center py-3 border border-[var(--primary)] text-[var(--primary)] rounded-[var(--radius-btn)] font-semibold hover:bg-[var(--primary)] hover:text-white transition-all mb-6">Choose Basic</a>
        <ul class="space-y-3 text-sm text-[var(--text-muted)]">
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> 3 projects</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> 1 GB storage</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> Community support</li>
        </ul>
      </div>
      <div class="p-8 bg-[var(--bg)] rounded-[var(--radius)] border-2 border-[var(--primary)] hover:shadow-lg transition-shadow relative" data-aos="fade-up" data-aos-delay="200">
        <span class="absolute -top-3 right-6 px-3 py-1 bg-[var(--primary)] text-white text-xs font-bold rounded-full">Best Value</span>
        <h3 class="text-lg font-bold text-[var(--text)] mb-1">Pro</h3>
        <p class="text-sm text-[var(--text-muted)] mb-6">For small teams and startups</p>
        <div class="mb-6"><span class="text-4xl font-bold text-[var(--text)]" data-price-monthly="49" data-price-annual="39">$49</span><span class="text-[var(--text-muted)]">/mo</span></div>
        <a href="#" class="block text-center py-3 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] font-semibold hover:opacity-90 transition-all mb-6">Choose Pro</a>
        <ul class="space-y-3 text-sm text-[var(--text-muted)]">
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> Unlimited projects</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> 50 GB storage</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> Priority support</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> Advanced analytics</li>
        </ul>
      </div>
      <div class="p-8 bg-[var(--bg)] rounded-[var(--radius)] border border-[var(--text)]/10 hover:shadow-lg transition-shadow" data-aos="fade-up" data-aos-delay="300">
        <h3 class="text-lg font-bold text-[var(--text)] mb-1">Team</h3>
        <p class="text-sm text-[var(--text-muted)] mb-6">For growing organizations</p>
        <div class="mb-6"><span class="text-4xl font-bold text-[var(--text)]" data-price-monthly="99" data-price-annual="79">$99</span><span class="text-[var(--text-muted)]">/mo</span></div>
        <a href="#" class="block text-center py-3 border border-[var(--primary)] text-[var(--primary)] rounded-[var(--radius-btn)] font-semibold hover:bg-[var(--primary)] hover:text-white transition-all mb-6">Choose Team</a>
        <ul class="space-y-3 text-sm text-[var(--text-muted)]">
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> Everything in Pro</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> Unlimited storage</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> SSO and SAML</li>
          <li class="flex items-center gap-2"><i class="fa-solid fa-check text-green-500"></i> Dedicated manager</li>
        </ul>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "comparison_table_pricing",
            "style": "detailed",
            "description": "Feature comparison table with checkmarks across plans",
            "html": '''<section data-section-type="pricing" class="py-24 bg-[var(--bg)]">
  <div class="max-w-5xl mx-auto px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Compare Plans</h2>
      <p class="text-lg text-[var(--text-muted)]">Find the perfect fit for your business needs.</p>
    </div>
    <div class="overflow-x-auto rounded-[var(--radius)] border border-[var(--text)]/10">
      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-[var(--text)]/10 bg-[var(--bg-surface)]">
            <th class="p-5 text-[var(--text-muted)] font-medium text-sm">Feature</th>
            <th class="p-5 text-center text-[var(--text)] font-bold">Free</th>
            <th class="p-5 text-center text-[var(--primary)] font-bold">Pro<br/><span class="text-sm font-normal">$49/mo</span></th>
            <th class="p-5 text-center text-[var(--text)] font-bold">Business<br/><span class="text-sm font-normal">$149/mo</span></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[var(--text)]/5">
          <tr><td class="p-4 text-[var(--text)] text-sm">Projects</td><td class="p-4 text-center text-[var(--text-muted)] text-sm">3</td><td class="p-4 text-center text-[var(--text)] text-sm font-medium">Unlimited</td><td class="p-4 text-center text-[var(--text)] text-sm font-medium">Unlimited</td></tr>
          <tr><td class="p-4 text-[var(--text)] text-sm">Storage</td><td class="p-4 text-center text-[var(--text-muted)] text-sm">500 MB</td><td class="p-4 text-center text-[var(--text)] text-sm font-medium">50 GB</td><td class="p-4 text-center text-[var(--text)] text-sm font-medium">500 GB</td></tr>
          <tr><td class="p-4 text-[var(--text)] text-sm">Team Members</td><td class="p-4 text-center text-[var(--text-muted)] text-sm">1</td><td class="p-4 text-center text-[var(--text)] text-sm font-medium">10</td><td class="p-4 text-center text-[var(--text)] text-sm font-medium">Unlimited</td></tr>
          <tr><td class="p-4 text-[var(--text)] text-sm">Analytics</td><td class="p-4 text-center"><i class="fa-solid fa-xmark text-gray-300"></i></td><td class="p-4 text-center"><i class="fa-solid fa-check text-[var(--primary)]"></i></td><td class="p-4 text-center"><i class="fa-solid fa-check text-[var(--primary)]"></i></td></tr>
          <tr><td class="p-4 text-[var(--text)] text-sm">Priority Support</td><td class="p-4 text-center"><i class="fa-solid fa-xmark text-gray-300"></i></td><td class="p-4 text-center"><i class="fa-solid fa-check text-[var(--primary)]"></i></td><td class="p-4 text-center"><i class="fa-solid fa-check text-[var(--primary)]"></i></td></tr>
          <tr><td class="p-4 text-[var(--text)] text-sm">Custom Branding</td><td class="p-4 text-center"><i class="fa-solid fa-xmark text-gray-300"></i></td><td class="p-4 text-center"><i class="fa-solid fa-xmark text-gray-300"></i></td><td class="p-4 text-center"><i class="fa-solid fa-check text-[var(--primary)]"></i></td></tr>
          <tr><td class="p-4 text-[var(--text)] text-sm">SSO / SAML</td><td class="p-4 text-center"><i class="fa-solid fa-xmark text-gray-300"></i></td><td class="p-4 text-center"><i class="fa-solid fa-xmark text-gray-300"></i></td><td class="p-4 text-center"><i class="fa-solid fa-check text-[var(--primary)]"></i></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</section>''',
        },
    ],

    # ─── CTA ───────────────────────────────────────────────────────────
    "cta": [
        {
            "name": "centered_cta",
            "style": "clean",
            "description": "Centered CTA with heading, subtext, and button",
            "html": '''<section data-section-type="cta" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-3xl mx-auto px-6 text-center space-y-8">
    <h2 class="text-4xl font-bold text-[var(--text)]" style="font-family:var(--font-heading)">Ready to Transform Your Workflow?</h2>
    <p class="text-lg text-[var(--text-muted)] max-w-xl mx-auto">Join over 10,000 teams who have already made the switch. Start your free 14-day trial today — no credit card required.</p>
    <div class="flex flex-wrap justify-center gap-4">
      <a href="#contact" class="px-10 py-4 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] font-semibold text-lg hover:opacity-90 transition-all shadow-lg shadow-[var(--primary)]/25">Start Free Trial</a>
      <a href="#contact" class="px-10 py-4 border-2 border-[var(--text)]/15 text-[var(--text)] rounded-[var(--radius-btn)] font-semibold text-lg hover:border-[var(--primary)] transition-all">Talk to Sales</a>
    </div>
    <p class="text-sm text-[var(--text-muted)]">Free for 14 days. No credit card needed. Cancel anytime.</p>
  </div>
</section>''',
        },
        {
            "name": "split_cta_with_image",
            "style": "modern",
            "description": "Split CTA with text on one side and image on the other",
            "html": '''<section data-section-type="cta" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="grid lg:grid-cols-2 gap-12 items-center bg-[var(--bg-surface)] rounded-2xl overflow-hidden">
      <div class="p-12 space-y-6">
        <h2 class="text-3xl font-bold text-[var(--text)]" style="font-family:var(--font-heading)">Start Building Something Great</h2>
        <p class="text-[var(--text-muted)] leading-relaxed">Whether you are a solo founder or leading a team of hundreds, our platform scales with your ambition. Get started in minutes.</p>
        <div class="flex flex-wrap gap-4">
          <a href="#contact" class="px-8 py-3.5 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] font-semibold hover:opacity-90 transition-all">Get Started Free</a>
          <a href="#demo" class="px-8 py-3.5 text-[var(--text-muted)] hover:text-[var(--text)] font-semibold transition-colors flex items-center gap-2"><i class="fa-solid fa-play-circle text-[var(--primary)]"></i> Watch Demo</a>
        </div>
      </div>
      <div class="h-full min-h-[300px]">
        <img src="{{IMG:happy team celebrating project success in modern office}}" alt="Get started" class="w-full h-full object-cover" />
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "gradient_banner_cta",
            "style": "vibrant",
            "description": "Full-width gradient banner with bold CTA",
            "html": '''<section data-section-type="cta" class="py-20" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">
  <div class="max-w-5xl mx-auto px-6 text-center space-y-8">
    <h2 class="text-4xl md:text-5xl font-bold text-white" style="font-family:var(--font-heading)">Let Us Build Your Future Together</h2>
    <p class="text-xl text-white/80 max-w-2xl mx-auto">Schedule a free consultation with our team and discover how we can accelerate your digital transformation.</p>
    <a href="#contact" class="inline-block px-12 py-4 bg-white text-[var(--primary)] rounded-[var(--radius-btn)] font-bold text-lg hover:shadow-2xl transition-all">Book a Free Call</a>
  </div>
</section>''',
        },
    ],

    # ─── FOOTER ────────────────────────────────────────────────────────
    "footer": [
        {
            "name": "four_column_footer",
            "style": "standard",
            "description": "4-column footer with links, newsletter, and social icons",
            "html": '''<footer data-section-type="footer" class="bg-[var(--text)] text-white pt-16 pb-8">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
      <div>
        <h3 class="text-xl font-bold mb-4">BrandName</h3>
        <p class="text-white/60 text-sm leading-relaxed mb-6">Empowering businesses with modern tools and strategies to grow faster and smarter.</p>
        <div class="flex gap-4">
          <a href="#" class="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center hover:bg-[var(--primary)] transition-colors"><i class="fa-brands fa-twitter text-sm"></i></a>
          <a href="#" class="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center hover:bg-[var(--primary)] transition-colors"><i class="fa-brands fa-linkedin-in text-sm"></i></a>
          <a href="#" class="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center hover:bg-[var(--primary)] transition-colors"><i class="fa-brands fa-instagram text-sm"></i></a>
        </div>
      </div>
      <div>
        <h4 class="font-semibold mb-4 text-sm uppercase tracking-wider">Company</h4>
        <ul class="space-y-3 text-sm text-white/60">
          <li><a href="#about" class="hover:text-white transition-colors">About Us</a></li>
          <li><a href="#careers" class="hover:text-white transition-colors">Careers</a></li>
          <li><a href="#blog" class="hover:text-white transition-colors">Blog</a></li>
          <li><a href="#press" class="hover:text-white transition-colors">Press</a></li>
        </ul>
      </div>
      <div>
        <h4 class="font-semibold mb-4 text-sm uppercase tracking-wider">Support</h4>
        <ul class="space-y-3 text-sm text-white/60">
          <li><a href="#help" class="hover:text-white transition-colors">Help Center</a></li>
          <li><a href="#docs" class="hover:text-white transition-colors">Documentation</a></li>
          <li><a href="#status" class="hover:text-white transition-colors">System Status</a></li>
          <li><a href="#contact" class="hover:text-white transition-colors">Contact Us</a></li>
        </ul>
      </div>
      <div>
        <h4 class="font-semibold mb-4 text-sm uppercase tracking-wider">Stay Updated</h4>
        <p class="text-sm text-white/60 mb-4">Subscribe for tips, news, and product updates.</p>
        <form class="flex gap-2">
          <input type="email" placeholder="Your email" class="flex-1 px-4 py-2.5 bg-white/10 rounded-[var(--radius-btn)] text-sm text-white placeholder-white/40 border border-white/10 focus:border-[var(--primary)] outline-none" />
          <button class="px-5 py-2.5 bg-[var(--primary)] rounded-[var(--radius-btn)] text-sm font-semibold hover:opacity-90 transition-all">Join</button>
        </form>
      </div>
    </div>
    <div class="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-white/40">
      <p>2025 BrandName. All rights reserved.</p>
      <div class="flex gap-6">
        <a href="#" class="hover:text-white transition-colors">Privacy Policy</a>
        <a href="#" class="hover:text-white transition-colors">Terms of Service</a>
      </div>
    </div>
  </div>
</footer>''',
        },
        {
            "name": "minimal_footer",
            "style": "clean",
            "description": "Minimal single-row footer with logo, links, and copyright",
            "html": '''<footer data-section-type="footer" class="py-8 bg-[var(--bg)] border-t border-[var(--text)]/10">
  <div class="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">
    <span class="text-lg font-bold text-[var(--text)]">BrandName</span>
    <nav class="flex flex-wrap gap-6 text-sm text-[var(--text-muted)]">
      <a href="#about" class="hover:text-[var(--text)] transition-colors">About</a>
      <a href="#features" class="hover:text-[var(--text)] transition-colors">Features</a>
      <a href="#pricing" class="hover:text-[var(--text)] transition-colors">Pricing</a>
      <a href="#contact" class="hover:text-[var(--text)] transition-colors">Contact</a>
    </nav>
    <p class="text-sm text-[var(--text-muted)]">2025 BrandName</p>
  </div>
</footer>''',
        },
        {
            "name": "mega_footer",
            "style": "comprehensive",
            "description": "Large footer with multiple link columns, contact info, and badges",
            "html": '''<footer data-section-type="footer" class="bg-gray-900 text-white pt-20 pb-8">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="grid md:grid-cols-2 lg:grid-cols-5 gap-10 mb-16">
      <div class="lg:col-span-2">
        <h3 class="text-2xl font-bold mb-4">BrandName</h3>
        <p class="text-gray-400 text-sm leading-relaxed mb-6 max-w-sm">Building the future of business technology. Trusted by over 10,000 companies in 50 countries worldwide.</p>
        <div class="flex items-center gap-6 mb-6">
          <div class="flex gap-3">
            <a href="#" class="text-gray-400 hover:text-white transition-colors"><i class="fa-brands fa-twitter text-lg"></i></a>
            <a href="#" class="text-gray-400 hover:text-white transition-colors"><i class="fa-brands fa-linkedin-in text-lg"></i></a>
            <a href="#" class="text-gray-400 hover:text-white transition-colors"><i class="fa-brands fa-github text-lg"></i></a>
            <a href="#" class="text-gray-400 hover:text-white transition-colors"><i class="fa-brands fa-youtube text-lg"></i></a>
          </div>
        </div>
        <div class="space-y-2 text-sm text-gray-400">
          <p class="flex items-center gap-2"><i class="fa-solid fa-envelope text-xs"></i> hello@brandname.com</p>
          <p class="flex items-center gap-2"><i class="fa-solid fa-phone text-xs"></i> +971 4 123 4567</p>
          <p class="flex items-center gap-2"><i class="fa-solid fa-location-dot text-xs"></i> Dubai, United Arab Emirates</p>
        </div>
      </div>
      <div>
        <h4 class="font-semibold mb-4 text-sm uppercase tracking-wider">Product</h4>
        <ul class="space-y-3 text-sm text-gray-400">
          <li><a href="#" class="hover:text-white transition-colors">Features</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Pricing</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Integrations</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Changelog</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Roadmap</a></li>
        </ul>
      </div>
      <div>
        <h4 class="font-semibold mb-4 text-sm uppercase tracking-wider">Resources</h4>
        <ul class="space-y-3 text-sm text-gray-400">
          <li><a href="#" class="hover:text-white transition-colors">Documentation</a></li>
          <li><a href="#" class="hover:text-white transition-colors">API Reference</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Blog</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Community</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Webinars</a></li>
        </ul>
      </div>
      <div>
        <h4 class="font-semibold mb-4 text-sm uppercase tracking-wider">Legal</h4>
        <ul class="space-y-3 text-sm text-gray-400">
          <li><a href="#" class="hover:text-white transition-colors">Privacy Policy</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Terms of Service</a></li>
          <li><a href="#" class="hover:text-white transition-colors">Cookie Policy</a></li>
          <li><a href="#" class="hover:text-white transition-colors">GDPR</a></li>
        </ul>
      </div>
    </div>
    <div class="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-500">
      <p>2025 BrandName Inc. All rights reserved.</p>
      <p>Made with <i class="fa-solid fa-heart text-red-500 text-xs"></i> in Dubai</p>
    </div>
  </div>
</footer>''',
        },
    ],

    # ─── NAVBAR ────────────────────────────────────────────────────────
    "navbar": [
        {
            "name": "transparent_navbar",
            "style": "overlay",
            "description": "Transparent navbar that overlays the hero section",
            "html": '''<nav data-section-type="navbar" class="fixed top-0 left-0 right-0 z-50 bg-transparent backdrop-blur-sm border-b border-white/10">
  <div class="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between h-20">
    <a href="#" class="text-xl font-bold text-[var(--text)]">BrandName</a>
    <div class="hidden md:flex items-center gap-8">
      <a href="#features" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors font-medium">Features</a>
      <a href="#pricing" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors font-medium">Pricing</a>
      <a href="#about" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors font-medium">About</a>
      <a href="#contact" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors font-medium">Contact</a>
    </div>
    <div class="hidden md:flex items-center gap-4">
      <a href="#login" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] font-medium transition-colors">Log In</a>
      <a href="#signup" class="px-5 py-2.5 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] text-sm font-semibold hover:opacity-90 transition-all">Get Started</a>
    </div>
    <button class="md:hidden text-[var(--text)]" aria-label="Menu"><i class="fa-solid fa-bars text-xl"></i></button>
  </div>
</nav>''',
        },
        {
            "name": "solid_navbar",
            "style": "professional",
            "description": "Solid background navbar with shadow",
            "html": '''<nav data-section-type="navbar" class="fixed top-0 left-0 right-0 z-50 bg-[var(--bg)] shadow-sm border-b border-[var(--text)]/5">
  <div class="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between h-16">
    <a href="#" class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-lg bg-[var(--primary)] flex items-center justify-center text-white font-bold text-sm">B</div>
      <span class="text-lg font-bold text-[var(--text)]">BrandName</span>
    </a>
    <div class="hidden md:flex items-center gap-8">
      <a href="#features" class="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">Features</a>
      <a href="#pricing" class="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">Pricing</a>
      <a href="#testimonials" class="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">Reviews</a>
      <a href="#faq" class="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">FAQ</a>
      <a href="#contact" class="text-sm text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors">Contact</a>
    </div>
    <a href="#contact" class="hidden md:inline-block px-6 py-2.5 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] text-sm font-semibold hover:opacity-90 transition-all">Book a Demo</a>
    <button class="md:hidden text-[var(--text)]" aria-label="Menu"><i class="fa-solid fa-bars text-xl"></i></button>
  </div>
</nav>''',
        },
        {
            "name": "centered_logo_navbar",
            "style": "elegant",
            "description": "Centered logo with links split on both sides",
            "html": '''<nav data-section-type="navbar" class="fixed top-0 left-0 right-0 z-50 bg-[var(--bg)]/95 backdrop-blur-md border-b border-[var(--text)]/5">
  <div class="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between h-20">
    <div class="hidden md:flex items-center gap-8">
      <a href="#about" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors tracking-wide">About</a>
      <a href="#services" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors tracking-wide">Services</a>
      <a href="#work" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors tracking-wide">Portfolio</a>
    </div>
    <a href="#" class="text-2xl font-bold text-[var(--text)] tracking-tight" style="font-family:var(--font-heading)">BRAND</a>
    <div class="hidden md:flex items-center gap-8">
      <a href="#blog" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors tracking-wide">Journal</a>
      <a href="#testimonials" class="text-sm text-[var(--text-muted)] hover:text-[var(--text)] transition-colors tracking-wide">Reviews</a>
      <a href="#contact" class="text-sm text-[var(--text)] font-semibold hover:text-[var(--primary)] transition-colors tracking-wide">Contact</a>
    </div>
    <button class="md:hidden text-[var(--text)]" aria-label="Menu"><i class="fa-solid fa-bars text-xl"></i></button>
  </div>
</nav>''',
        },
    ],

    # ─── STATS ─────────────────────────────────────────────────────────
    "stats": [
        {
            "name": "inline_counters",
            "style": "clean",
            "description": "Horizontal row of stat counters with labels",
            "html": '''<section data-section-type="stats" class="py-16 bg-[var(--bg-surface)] border-y border-[var(--text)]/5">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
      <div data-aos="fade-up" data-aos-delay="100">
        <p class="text-4xl md:text-5xl font-bold text-[var(--primary)]">500+</p>
        <p class="text-[var(--text-muted)] mt-2 text-sm font-medium">Projects Delivered</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="200">
        <p class="text-4xl md:text-5xl font-bold text-[var(--primary)]">98%</p>
        <p class="text-[var(--text-muted)] mt-2 text-sm font-medium">Client Satisfaction</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="300">
        <p class="text-4xl md:text-5xl font-bold text-[var(--primary)]">15+</p>
        <p class="text-[var(--text-muted)] mt-2 text-sm font-medium">Years Experience</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="400">
        <p class="text-4xl md:text-5xl font-bold text-[var(--primary)]">24/7</p>
        <p class="text-[var(--text-muted)] mt-2 text-sm font-medium">Dedicated Support</p>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "card_counters",
            "style": "modern",
            "description": "Stats displayed in individual cards with icons",
            "html": '''<section data-section-type="stats" class="py-20 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] text-center border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="100">
        <div class="w-12 h-12 rounded-xl bg-[var(--primary)]/10 flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-users text-[var(--primary)] text-xl"></i></div>
        <p class="text-3xl font-bold text-[var(--text)]">10K+</p>
        <p class="text-[var(--text-muted)] text-sm mt-1">Active Users</p>
      </div>
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] text-center border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="200">
        <div class="w-12 h-12 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-globe text-[var(--accent)] text-xl"></i></div>
        <p class="text-3xl font-bold text-[var(--text)]">50+</p>
        <p class="text-[var(--text-muted)] text-sm mt-1">Countries Served</p>
      </div>
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] text-center border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="300">
        <div class="w-12 h-12 rounded-xl bg-[var(--secondary)]/10 flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-award text-[var(--secondary)] text-xl"></i></div>
        <p class="text-3xl font-bold text-[var(--text)]">25</p>
        <p class="text-[var(--text-muted)] text-sm mt-1">Industry Awards</p>
      </div>
      <div class="p-8 bg-[var(--bg-surface)] rounded-[var(--radius)] text-center border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="400">
        <div class="w-12 h-12 rounded-xl bg-[var(--primary)]/10 flex items-center justify-center mx-auto mb-4"><i class="fa-solid fa-star text-[var(--primary)] text-xl"></i></div>
        <p class="text-3xl font-bold text-[var(--text)]">4.9</p>
        <p class="text-[var(--text-muted)] text-sm mt-1">Average Rating</p>
      </div>
    </div>
  </div>
</section>''',
        },
    ],

    # ─── TEAM ──────────────────────────────────────────────────────────
    "team": [
        {
            "name": "grid_team_cards",
            "style": "professional",
            "description": "Grid of team member cards with photos and social links",
            "html": '''<section data-section-type="team" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Meet Our Leadership</h2>
      <p class="text-lg text-[var(--text-muted)]">The talented people behind our mission to transform businesses worldwide.</p>
    </div>
    <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
      <div class="text-center group" data-aos="fade-up" data-aos-delay="100">
        <div class="relative mb-6 overflow-hidden rounded-[var(--radius)]">
          <img src="{{IMG:professional headshot of male CEO in business attire}}" alt="Team member" class="w-full aspect-[3/4] object-cover group-hover:scale-105 transition-transform duration-500" />
          <div class="absolute inset-0 bg-[var(--primary)]/0 group-hover:bg-[var(--primary)]/20 transition-colors flex items-end justify-center pb-4 opacity-0 group-hover:opacity-100">
            <div class="flex gap-3">
              <a href="#" class="w-8 h-8 rounded-full bg-white flex items-center justify-center"><i class="fa-brands fa-linkedin-in text-[var(--primary)] text-xs"></i></a>
              <a href="#" class="w-8 h-8 rounded-full bg-white flex items-center justify-center"><i class="fa-brands fa-twitter text-[var(--primary)] text-xs"></i></a>
            </div>
          </div>
        </div>
        <h3 class="text-lg font-bold text-[var(--text)]">Alexander Wright</h3>
        <p class="text-[var(--primary)] text-sm font-medium">Chief Executive Officer</p>
      </div>
      <div class="text-center group" data-aos="fade-up" data-aos-delay="200">
        <div class="relative mb-6 overflow-hidden rounded-[var(--radius)]">
          <img src="{{IMG:professional headshot of female CTO with confident expression}}" alt="Team member" class="w-full aspect-[3/4] object-cover group-hover:scale-105 transition-transform duration-500" />
        </div>
        <h3 class="text-lg font-bold text-[var(--text)]">Priya Sharma</h3>
        <p class="text-[var(--primary)] text-sm font-medium">Chief Technology Officer</p>
      </div>
      <div class="text-center group" data-aos="fade-up" data-aos-delay="300">
        <div class="relative mb-6 overflow-hidden rounded-[var(--radius)]">
          <img src="{{IMG:professional headshot of male creative director}}" alt="Team member" class="w-full aspect-[3/4] object-cover group-hover:scale-105 transition-transform duration-500" />
        </div>
        <h3 class="text-lg font-bold text-[var(--text)]">Omar Hassan</h3>
        <p class="text-[var(--primary)] text-sm font-medium">Creative Director</p>
      </div>
      <div class="text-center group" data-aos="fade-up" data-aos-delay="400">
        <div class="relative mb-6 overflow-hidden rounded-[var(--radius)]">
          <img src="{{IMG:professional headshot of female marketing executive}}" alt="Team member" class="w-full aspect-[3/4] object-cover group-hover:scale-105 transition-transform duration-500" />
        </div>
        <h3 class="text-lg font-bold text-[var(--text)]">Elena Rodriguez</h3>
        <p class="text-[var(--primary)] text-sm font-medium">Head of Marketing</p>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "horizontal_scroll_team",
            "style": "modern",
            "description": "Horizontal scrollable team cards with compact layout",
            "html": '''<section data-section-type="team" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="flex justify-between items-end mb-12">
      <div>
        <h2 class="text-4xl font-bold text-[var(--text)] mb-2" style="font-family:var(--font-heading)">Our Team</h2>
        <p class="text-[var(--text-muted)]">The experts driving your success.</p>
      </div>
      <div class="hidden md:flex gap-2">
        <button class="w-10 h-10 rounded-full border border-[var(--text)]/15 flex items-center justify-center text-[var(--text-muted)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all" aria-label="Previous"><i class="fa-solid fa-arrow-left text-sm"></i></button>
        <button class="w-10 h-10 rounded-full border border-[var(--text)]/15 flex items-center justify-center text-[var(--text-muted)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all" aria-label="Next"><i class="fa-solid fa-arrow-right text-sm"></i></button>
      </div>
    </div>
    <div class="flex gap-6 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide">
      <div class="min-w-[280px] snap-start bg-[var(--bg)] rounded-[var(--radius)] overflow-hidden border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="100">
        <img src="{{IMG:professional team member portrait in casual business setting}}" alt="Team member" class="w-full h-56 object-cover" />
        <div class="p-5">
          <h3 class="font-bold text-[var(--text)]">Sarah Mitchell</h3>
          <p class="text-sm text-[var(--primary)]">Lead Designer</p>
          <p class="text-xs text-[var(--text-muted)] mt-2">10+ years crafting digital experiences for Fortune 500 companies.</p>
        </div>
      </div>
      <div class="min-w-[280px] snap-start bg-[var(--bg)] rounded-[var(--radius)] overflow-hidden border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="200">
        <img src="{{IMG:professional male software engineer portrait}}" alt="Team member" class="w-full h-56 object-cover" />
        <div class="p-5">
          <h3 class="font-bold text-[var(--text)]">James Park</h3>
          <p class="text-sm text-[var(--primary)]">Engineering Lead</p>
          <p class="text-xs text-[var(--text-muted)] mt-2">Former Google engineer, passionate about scalable architecture.</p>
        </div>
      </div>
      <div class="min-w-[280px] snap-start bg-[var(--bg)] rounded-[var(--radius)] overflow-hidden border border-[var(--text)]/5" data-aos="fade-up" data-aos-delay="300">
        <img src="{{IMG:professional female business strategist portrait}}" alt="Team member" class="w-full h-56 object-cover" />
        <div class="p-5">
          <h3 class="font-bold text-[var(--text)]">Amara Johnson</h3>
          <p class="text-sm text-[var(--primary)]">Strategy Director</p>
          <p class="text-xs text-[var(--text-muted)] mt-2">MBA from Wharton, specializing in digital transformation.</p>
        </div>
      </div>
    </div>
  </div>
</section>''',
        },
    ],

    # ─── GALLERY ───────────────────────────────────────────────────────
    "gallery": [
        {
            "name": "masonry_gallery",
            "style": "creative",
            "description": "Masonry-style image gallery with varying heights",
            "html": '''<section data-section-type="gallery" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Our Portfolio</h2>
      <p class="text-lg text-[var(--text-muted)]">A selection of our recent work across industries.</p>
    </div>
    <div class="columns-1 md:columns-2 lg:columns-3 gap-4 space-y-4">
      <div class="break-inside-avoid group relative overflow-hidden rounded-[var(--radius)]" data-aos="fade-up" data-aos-delay="100">
        <img src="{{IMG:modern corporate office interior design}}" alt="Project" class="w-full group-hover:scale-105 transition-transform duration-500" />
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex items-end p-6 opacity-0 group-hover:opacity-100">
          <div><p class="text-white font-bold">Office Redesign</p><p class="text-white/70 text-sm">Interior Architecture</p></div>
        </div>
      </div>
      <div class="break-inside-avoid group relative overflow-hidden rounded-[var(--radius)]" data-aos="fade-up" data-aos-delay="200">
        <img src="{{IMG:sleek mobile app UI design on phone mockup}}" alt="Project" class="w-full group-hover:scale-105 transition-transform duration-500" />
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex items-end p-6 opacity-0 group-hover:opacity-100">
          <div><p class="text-white font-bold">FinTrack App</p><p class="text-white/70 text-sm">Mobile Design</p></div>
        </div>
      </div>
      <div class="break-inside-avoid group relative overflow-hidden rounded-[var(--radius)]" data-aos="fade-up" data-aos-delay="300">
        <img src="{{IMG:luxury brand packaging and identity design}}" alt="Project" class="w-full group-hover:scale-105 transition-transform duration-500" />
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex items-end p-6 opacity-0 group-hover:opacity-100">
          <div><p class="text-white font-bold">Luxe Cosmetics</p><p class="text-white/70 text-sm">Brand Identity</p></div>
        </div>
      </div>
      <div class="break-inside-avoid group relative overflow-hidden rounded-[var(--radius)]" data-aos="fade-up" data-aos-delay="400">
        <img src="{{IMG:e-commerce website on laptop showing product grid}}" alt="Project" class="w-full group-hover:scale-105 transition-transform duration-500" />
        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex items-end p-6 opacity-0 group-hover:opacity-100">
          <div><p class="text-white font-bold">StyleHaven Store</p><p class="text-white/70 text-sm">E-commerce</p></div>
        </div>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "lightbox_grid_gallery",
            "style": "structured",
            "description": "Uniform grid gallery with category filters",
            "html": '''<section data-section-type="gallery" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center mb-12">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Featured Work</h2>
      <div class="flex flex-wrap justify-center gap-3 mt-8">
        <button class="px-5 py-2 bg-[var(--primary)] text-white rounded-full text-sm font-medium">All</button>
        <button class="px-5 py-2 bg-[var(--bg)] text-[var(--text-muted)] rounded-full text-sm font-medium hover:text-[var(--text)] transition-colors border border-[var(--text)]/10">Branding</button>
        <button class="px-5 py-2 bg-[var(--bg)] text-[var(--text-muted)] rounded-full text-sm font-medium hover:text-[var(--text)] transition-colors border border-[var(--text)]/10">Web Design</button>
        <button class="px-5 py-2 bg-[var(--bg)] text-[var(--text-muted)] rounded-full text-sm font-medium hover:text-[var(--text)] transition-colors border border-[var(--text)]/10">Development</button>
      </div>
    </div>
    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div class="group cursor-pointer" data-aos="fade-up" data-aos-delay="100">
        <div class="relative overflow-hidden rounded-[var(--radius)] mb-4">
          <img src="{{IMG:clean corporate website design displayed on desktop monitor}}" alt="Project" class="w-full aspect-[4/3] object-cover group-hover:scale-105 transition-transform duration-500" />
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div class="w-12 h-12 rounded-full bg-white flex items-center justify-center"><i class="fa-solid fa-expand text-[var(--text)]"></i></div>
          </div>
        </div>
        <h3 class="font-bold text-[var(--text)]">Meridian Capital</h3>
        <p class="text-sm text-[var(--text-muted)]">Web Design &amp; Development</p>
      </div>
      <div class="group cursor-pointer" data-aos="fade-up" data-aos-delay="200">
        <div class="relative overflow-hidden rounded-[var(--radius)] mb-4">
          <img src="{{IMG:creative brand identity design with logo and stationery}}" alt="Project" class="w-full aspect-[4/3] object-cover group-hover:scale-105 transition-transform duration-500" />
        </div>
        <h3 class="font-bold text-[var(--text)]">Verde Organics</h3>
        <p class="text-sm text-[var(--text-muted)]">Brand Identity</p>
      </div>
      <div class="group cursor-pointer" data-aos="fade-up" data-aos-delay="300">
        <div class="relative overflow-hidden rounded-[var(--radius)] mb-4">
          <img src="{{IMG:modern SaaS dashboard with analytics and data visualization}}" alt="Project" class="w-full aspect-[4/3] object-cover group-hover:scale-105 transition-transform duration-500" />
        </div>
        <h3 class="font-bold text-[var(--text)]">DataPulse Analytics</h3>
        <p class="text-sm text-[var(--text-muted)]">SaaS Product Design</p>
      </div>
    </div>
  </div>
</section>''',
        },
    ],

    # ─── CONTACT ───────────────────────────────────────────────────────
    "contact": [
        {
            "name": "split_form_map_contact",
            "style": "practical",
            "description": "Split layout with contact form on one side and info/map on the other",
            "html": '''<section data-section-type="contact" class="py-24 bg-[var(--bg)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="grid lg:grid-cols-2 gap-16">
      <div>
        <span class="text-[var(--primary)] font-semibold text-sm tracking-widest uppercase">Get in Touch</span>
        <h2 class="text-4xl font-bold text-[var(--text)] mt-4 mb-6" style="font-family:var(--font-heading)">Let Us Start a Conversation</h2>
        <p class="text-[var(--text-muted)] leading-relaxed mb-10">Have a project in mind? Fill out the form and our team will get back to you within 24 hours.</p>
        <div class="space-y-6">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-[var(--primary)]/10 flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-envelope text-[var(--primary)]"></i></div>
            <div><p class="text-sm text-[var(--text-muted)]">Email</p><p class="font-medium text-[var(--text)]">hello@brandname.com</p></div>
          </div>
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-[var(--primary)]/10 flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-phone text-[var(--primary)]"></i></div>
            <div><p class="text-sm text-[var(--text-muted)]">Phone</p><p class="font-medium text-[var(--text)]">+971 4 123 4567</p></div>
          </div>
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-[var(--primary)]/10 flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-location-dot text-[var(--primary)]"></i></div>
            <div><p class="text-sm text-[var(--text-muted)]">Office</p><p class="font-medium text-[var(--text)]">Meydan Free Zone, Dubai, UAE</p></div>
          </div>
        </div>
      </div>
      <div class="bg-[var(--bg-surface)] rounded-[var(--radius)] p-8 border border-[var(--text)]/5">
        <form class="space-y-5">
          <div class="grid md:grid-cols-2 gap-5">
            <div>
              <label class="block text-sm font-medium text-[var(--text)] mb-2">First Name</label>
              <input type="text" class="w-full px-4 py-3 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors" placeholder="John" />
            </div>
            <div>
              <label class="block text-sm font-medium text-[var(--text)] mb-2">Last Name</label>
              <input type="text" class="w-full px-4 py-3 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors" placeholder="Doe" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text)] mb-2">Email</label>
            <input type="email" class="w-full px-4 py-3 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors" placeholder="john@company.com" />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text)] mb-2">Message</label>
            <textarea rows="4" class="w-full px-4 py-3 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors resize-none" placeholder="Tell us about your project..."></textarea>
          </div>
          <button type="submit" class="w-full py-3.5 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] font-semibold hover:opacity-90 transition-all">Send Message</button>
        </form>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "centered_form_contact",
            "style": "minimal",
            "description": "Centered compact contact form with clean layout",
            "html": '''<section data-section-type="contact" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-2xl mx-auto px-6">
    <div class="text-center mb-12">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Contact Us</h2>
      <p class="text-[var(--text-muted)]">We would love to hear from you. Send us a message and we will respond promptly.</p>
    </div>
    <form class="space-y-5">
      <div class="grid md:grid-cols-2 gap-5">
        <input type="text" class="w-full px-4 py-3.5 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors text-sm" placeholder="Your Name" />
        <input type="email" class="w-full px-4 py-3.5 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors text-sm" placeholder="Your Email" />
      </div>
      <input type="text" class="w-full px-4 py-3.5 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors text-sm" placeholder="Subject" />
      <textarea rows="5" class="w-full px-4 py-3.5 bg-[var(--bg)] rounded-[var(--radius-btn)] border border-[var(--text)]/10 text-[var(--text)] focus:border-[var(--primary)] outline-none transition-colors resize-none text-sm" placeholder="Your message..."></textarea>
      <button type="submit" class="w-full py-3.5 bg-[var(--primary)] text-white rounded-[var(--radius-btn)] font-semibold hover:opacity-90 transition-all">Send Message</button>
    </form>
  </div>
</section>''',
        },
    ],

    # ─── FAQ ───────────────────────────────────────────────────────────
    "faq": [
        {
            "name": "accordion_faq",
            "style": "standard",
            "description": "Expandable accordion-style FAQ section",
            "html": '''<section data-section-type="faq" class="py-24 bg-[var(--bg)]">
  <div class="max-w-3xl mx-auto px-6">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Frequently Asked Questions</h2>
      <p class="text-lg text-[var(--text-muted)]">Everything you need to know about our platform.</p>
    </div>
    <div class="space-y-4">
      <div class="border border-[var(--text)]/10 rounded-[var(--radius)] overflow-hidden" data-aos="fade-up" data-aos-delay="100">
        <button class="w-full flex items-center justify-between p-6 text-left font-semibold text-[var(--text)] hover:text-[var(--primary)] transition-colors" data-faq-toggle>
          <span>How long does it take to get started?</span>
          <i class="fa-solid fa-plus text-sm text-[var(--text-muted)]"></i>
        </button>
        <div class="px-6 pb-6 text-[var(--text-muted)] leading-relaxed hidden" data-faq-content>Most teams are fully onboarded within 48 hours. Our guided setup process walks you through configuration, team invitations, and your first project in under 10 minutes.</div>
      </div>
      <div class="border border-[var(--text)]/10 rounded-[var(--radius)] overflow-hidden" data-aos="fade-up" data-aos-delay="200">
        <button class="w-full flex items-center justify-between p-6 text-left font-semibold text-[var(--text)] hover:text-[var(--primary)] transition-colors" data-faq-toggle>
          <span>Can I cancel my subscription at any time?</span>
          <i class="fa-solid fa-plus text-sm text-[var(--text-muted)]"></i>
        </button>
        <div class="px-6 pb-6 text-[var(--text-muted)] leading-relaxed hidden" data-faq-content>Absolutely. There are no long-term contracts or cancellation fees. You can downgrade or cancel your plan at any time from your account settings.</div>
      </div>
      <div class="border border-[var(--text)]/10 rounded-[var(--radius)] overflow-hidden" data-aos="fade-up" data-aos-delay="300">
        <button class="w-full flex items-center justify-between p-6 text-left font-semibold text-[var(--text)] hover:text-[var(--primary)] transition-colors" data-faq-toggle>
          <span>Do you offer custom enterprise solutions?</span>
          <i class="fa-solid fa-plus text-sm text-[var(--text-muted)]"></i>
        </button>
        <div class="px-6 pb-6 text-[var(--text-muted)] leading-relaxed hidden" data-faq-content>Yes. Our enterprise plan includes custom integrations, dedicated account management, SLA guarantees, and on-premise deployment options. Contact our sales team for a tailored proposal.</div>
      </div>
      <div class="border border-[var(--text)]/10 rounded-[var(--radius)] overflow-hidden" data-aos="fade-up" data-aos-delay="400">
        <button class="w-full flex items-center justify-between p-6 text-left font-semibold text-[var(--text)] hover:text-[var(--primary)] transition-colors" data-faq-toggle>
          <span>What kind of support do you provide?</span>
          <i class="fa-solid fa-plus text-sm text-[var(--text-muted)]"></i>
        </button>
        <div class="px-6 pb-6 text-[var(--text-muted)] leading-relaxed hidden" data-faq-content>All plans include email support with a 24-hour response time. Pro and Enterprise plans get priority support with live chat and a dedicated success manager.</div>
      </div>
    </div>
  </div>
</section>''',
        },
        {
            "name": "two_column_faq",
            "style": "spacious",
            "description": "Two-column FAQ layout for more questions",
            "html": '''<section data-section-type="faq" class="py-24 bg-[var(--bg-surface)]">
  <div class="max-w-7xl mx-auto px-6 lg:px-8">
    <div class="text-center max-w-3xl mx-auto mb-16">
      <h2 class="text-4xl font-bold text-[var(--text)] mb-4" style="font-family:var(--font-heading)">Common Questions</h2>
      <p class="text-lg text-[var(--text-muted)]">Quick answers to the questions we hear most often.</p>
    </div>
    <div class="grid md:grid-cols-2 gap-x-12 gap-y-10">
      <div data-aos="fade-up" data-aos-delay="100">
        <h3 class="text-lg font-bold text-[var(--text)] mb-3 flex items-start gap-3"><i class="fa-solid fa-circle-question text-[var(--primary)] mt-1 text-sm"></i> Is there a free trial?</h3>
        <p class="text-[var(--text-muted)] leading-relaxed pl-7">Yes, every plan comes with a 14-day free trial. No credit card required. You get full access to all features during the trial period.</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="200">
        <h3 class="text-lg font-bold text-[var(--text)] mb-3 flex items-start gap-3"><i class="fa-solid fa-circle-question text-[var(--primary)] mt-1 text-sm"></i> Can I change plans later?</h3>
        <p class="text-[var(--text-muted)] leading-relaxed pl-7">Of course. You can upgrade or downgrade your plan at any time. Changes take effect immediately and billing is prorated.</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="300">
        <h3 class="text-lg font-bold text-[var(--text)] mb-3 flex items-start gap-3"><i class="fa-solid fa-circle-question text-[var(--primary)] mt-1 text-sm"></i> Is my data secure?</h3>
        <p class="text-[var(--text-muted)] leading-relaxed pl-7">We use AES-256 encryption, are SOC 2 Type II certified, and perform regular security audits. Your data is backed up daily across multiple regions.</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="400">
        <h3 class="text-lg font-bold text-[var(--text)] mb-3 flex items-start gap-3"><i class="fa-solid fa-circle-question text-[var(--primary)] mt-1 text-sm"></i> Do you offer refunds?</h3>
        <p class="text-[var(--text-muted)] leading-relaxed pl-7">We offer a 30-day money-back guarantee on all annual plans. If you are not satisfied, contact support for a full refund.</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="500">
        <h3 class="text-lg font-bold text-[var(--text)] mb-3 flex items-start gap-3"><i class="fa-solid fa-circle-question text-[var(--primary)] mt-1 text-sm"></i> What integrations are available?</h3>
        <p class="text-[var(--text-muted)] leading-relaxed pl-7">We integrate with over 200 tools including Slack, Jira, Salesforce, HubSpot, Google Workspace, and Zapier for custom workflows.</p>
      </div>
      <div data-aos="fade-up" data-aos-delay="600">
        <h3 class="text-lg font-bold text-[var(--text)] mb-3 flex items-start gap-3"><i class="fa-solid fa-circle-question text-[var(--primary)] mt-1 text-sm"></i> How do I contact support?</h3>
        <p class="text-[var(--text-muted)] leading-relaxed pl-7">Email us at support@brandname.com, use the in-app chat widget, or visit our help center for documentation and video tutorials.</p>
      </div>
    </div>
  </div>
</section>''',
        },
    ],
}


# ─── Helper Functions ──────────────────────────────────────────────────


def get_section_reference(section_type: str, variant: int = None) -> Optional[dict]:
    """Return a random or specific variant reference for a section type.

    Args:
        section_type: The section type key (e.g., "hero", "features").
        variant: Optional 0-based index to pick a specific variant.
                 If None, a random variant is returned.

    Returns:
        A dict with name, style, description, html keys, or None if not found.
    """
    refs = SECTION_REFERENCES.get(section_type)
    if not refs:
        return None
    if variant is not None and 0 <= variant < len(refs):
        return refs[variant]
    return random.choice(refs)


def format_reference_for_prompt(ref: dict) -> str:
    """Format a single reference dict into a prompt-ready string."""
    return (
        f"--- Reference: {ref['name']} ({ref['style']} style) ---\n"
        f"Description: {ref['description']}\n"
        f"{ref['html']}\n"
        f"--- End Reference ---"
    )


def get_references_for_plan(plan: dict) -> str:
    """Given a plan with sections, return a formatted string with one
    reference per section type for prompt injection.

    The plan is expected to have a ``sections`` list where each section
    has a ``type`` key (e.g., "hero", "features").
    """
    sections = plan.get("sections", [])
    seen_types: set[str] = set()
    parts: list[str] = []

    for section in sections:
        section_type = section.get("type", "")
        if section_type in seen_types:
            continue
        seen_types.add(section_type)

        ref = get_section_reference(section_type)
        if ref:
            parts.append(format_reference_for_prompt(ref))

    if not parts:
        return ""

    header = (
        "SECTION QUALITY REFERENCES (use these as INSPIRATION for layout, "
        "spacing, and structure — do NOT copy verbatim):\n\n"
    )
    return header + "\n\n".join(parts) + "\n"
