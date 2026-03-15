"""About / Story section pattern templates."""

PATTERNS = {
    "about_split_scroll": """about_split_scroll pattern:
  <div class="container grid-2" style="align-items: start;">
    <div style="position: sticky; top: 2rem;">
      <span class="section-label"><span class="label-line"></span>OUR STORY</span>
      <h2 class="section-title">About heading</h2>
      <p class="section-subtitle">Brief company intro paragraph.</p>
      <p>Second paragraph with more detail about mission, values, or journey.</p>
      <p>Third paragraph about what makes the company unique.</p>
      <div class="btn-group" style="margin-top: 1.5rem;">
        <a href="#" class="btn-primary">Learn More</a>
      </div>
    </div>
    <div class="img-wrapper">
      <img src="{{IMG:about company office team}}" alt="About us" class="img-cover image-fade-zoom" style="border-radius: var(--radius);">
    </div>
  </div>
  NOTE: Left column is STICKY while scrolling. Right column has a tall image. Creates a premium scroll-lock storytelling effect. Use stagger-reveal on text paragraphs.""",

    "about_timeline_visual": """about_timeline_visual pattern:
  <div class="container-narrow" style="text-align: center;">
    <span class="section-label"><span class="label-line"></span>OUR JOURNEY<span class="label-line"></span></span>
    <h2 class="section-title">Company history heading</h2>
    <p class="section-subtitle">Brief intro about the company journey.</p>
  </div>
  <div class="container" style="margin-top: 3rem;">
    <!-- Timeline items alternate left/right -->
    <div class="timeline-track">
      <div class="timeline-item fade-up">
        <div class="timeline-marker"></div>
        <div class="timeline-content card">
          <span style="font-weight: 700; color: var(--primary);">2018</span>
          <h3>Milestone title</h3>
          <p>Description of what happened at this milestone.</p>
        </div>
      </div>
      <!-- Repeat 4-6 timeline items with years -->
    </div>
  </div>
  NOTE: Uses timeline CSS from the timeline pattern. Each item staggers in with fade-up. Alternate items can offset left/right via CSS. Include 4-6 real milestones.""",

    "about_numbers": """about_numbers pattern:
  <div class="container">
    <div class="grid-2" style="align-items: center; gap: 3rem;">
      <div>
        <span class="section-label"><span class="label-line"></span>WHO WE ARE</span>
        <h2 class="section-title">About heading</h2>
        <p class="section-subtitle">Company narrative paragraph explaining mission and values.</p>
        <p>Second paragraph with more context.</p>
      </div>
      <div class="grid-2" style="gap: 1.5rem;">
        <div class="card stagger-child" style="text-align: center; padding: 2rem;">
          <span class="counter" data-target="500" data-suffix="+" style="font-size: 2.5rem; font-weight: 800; color: var(--primary);">0</span>
          <p style="margin-top: 0.5rem; color: var(--text-muted);">Clients Served</p>
        </div>
        <div class="card stagger-child" style="text-align: center; padding: 2rem;">
          <span class="counter" data-target="15" data-suffix="+" style="font-size: 2.5rem; font-weight: 800; color: var(--primary);">0</span>
          <p style="margin-top: 0.5rem; color: var(--text-muted);">Years Experience</p>
        </div>
        <div class="card stagger-child" style="text-align: center; padding: 2rem;">
          <span class="counter" data-target="50" style="font-size: 2.5rem; font-weight: 800; color: var(--primary);">0</span>
          <p style="margin-top: 0.5rem; color: var(--text-muted);">Team Members</p>
        </div>
        <div class="card stagger-child" style="text-align: center; padding: 2rem;">
          <span class="counter" data-target="98" data-suffix="%" style="font-size: 2.5rem; font-weight: 800; color: var(--primary);">0</span>
          <p style="margin-top: 0.5rem; color: var(--text-muted);">Satisfaction Rate</p>
        </div>
      </div>
    </div>
  </div>
  NOTE: Left side is narrative text. Right side is a 2x2 grid of animated counters. Wrap right grid in stagger-reveal. Counters auto-animate on scroll via built-in JS.""",
}
