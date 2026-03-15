"""Portfolio / Case Study section pattern templates."""

PATTERNS = {
    "portfolio_case_study": """portfolio_case_study pattern:
  <div class="container">
    <div style="text-align: center; margin-bottom: 3rem;">
      <span class="section-label"><span class="label-line"></span>OUR WORK<span class="label-line"></span></span>
      <h2 class="section-title">Portfolio heading</h2>
      <p class="section-subtitle">Brief intro about completed projects.</p>
    </div>
    <div style="display: flex; flex-direction: column; gap: 3rem;">
      <!-- Case study card — full width, image + text side by side -->
      <div class="card fade-up" style="display: grid; grid-template-columns: 1fr 1fr; overflow: hidden; padding: 0;">
        <div class="img-wrapper" style="min-height: 320px;">
          <img src="{{IMG:project case study}}" alt="Project" class="img-cover">
        </div>
        <div style="padding: 2.5rem; display: flex; flex-direction: column; justify-content: center;">
          <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--primary); font-weight: 600;">Category</span>
          <h3 style="margin: 0.5rem 0;">Project Title</h3>
          <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Description of the project, the challenge, and the solution delivered.</p>
          <a href="#" class="btn-primary" style="align-self: flex-start;">View Project</a>
        </div>
      </div>
      <!-- Repeat 2-3 case study cards, alternating image left/right -->
    </div>
  </div>
  NOTE: Each case study is a full-width card with image on one side and text on the other. Alternate the image position (left/right) for visual rhythm. On mobile: stack vertically.""",

    "portfolio_hover_reveal": """portfolio_hover_reveal pattern:
  <div class="container">
    <div style="text-align: center; margin-bottom: 3rem;">
      <span class="section-label"><span class="label-line"></span>PORTFOLIO<span class="label-line"></span></span>
      <h2 class="section-title">Our Work</h2>
    </div>
    <div class="grid-3 stagger-reveal">
      <!-- Portfolio item with hover overlay -->
      <div class="stagger-child image-reveal" style="position: relative; border-radius: var(--radius); overflow: hidden; aspect-ratio: 4/3;">
        <img src="{{IMG:portfolio project}}" alt="Project" class="img-cover">
        <div style="position: absolute; inset: 0; background: linear-gradient(transparent 40%, rgba(0,0,0,0.8)); display: flex; flex-direction: column; justify-content: flex-end; padding: 1.5rem; opacity: 0; transition: opacity 0.3s ease;">
          <span style="color: var(--primary); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;">Category</span>
          <h3 style="color: white; margin: 0.25rem 0;">Project Title</h3>
        </div>
      </div>
      <!-- Repeat 6 items -->
    </div>
  </div>
  NOTE: Grid of images with hover overlay that fades in from bottom showing project title and category. Use image-reveal class for scroll animation. The overlay uses opacity transition — add :hover style in CSS to show it.""",

    "portfolio_filterable": """portfolio_filterable pattern:
  <div class="container">
    <div style="text-align: center; margin-bottom: 2rem;">
      <span class="section-label"><span class="label-line"></span>PROJECTS<span class="label-line"></span></span>
      <h2 class="section-title">Our Portfolio</h2>
    </div>
    <!-- Filter buttons -->
    <div style="display: flex; justify-content: center; gap: 0.75rem; margin-bottom: 2.5rem; flex-wrap: wrap;">
      <button class="filter-btn active" data-filter="all" style="padding: 0.5rem 1.25rem; border-radius: 50px; border: 1px solid var(--border); background: var(--primary); color: white; cursor: pointer; font-size: 0.875rem; transition: all 0.3s;">All</button>
      <button class="filter-btn" data-filter="category1" style="padding: 0.5rem 1.25rem; border-radius: 50px; border: 1px solid var(--border); background: transparent; cursor: pointer; font-size: 0.875rem; transition: all 0.3s;">Category 1</button>
      <button class="filter-btn" data-filter="category2" style="padding: 0.5rem 1.25rem; border-radius: 50px; border: 1px solid var(--border); background: transparent; cursor: pointer; font-size: 0.875rem; transition: all 0.3s;">Category 2</button>
    </div>
    <!-- Filterable grid -->
    <div class="grid-3 stagger-reveal" id="portfolio-grid">
      <div class="card card-lift stagger-child" data-category="category1">
        <div class="img-wrapper" style="aspect-ratio: 16/10;"><img src="{{IMG:project}}" alt="Project" class="img-cover"></div>
        <div style="padding: 1.25rem;">
          <span style="font-size: 0.75rem; color: var(--primary); text-transform: uppercase;">Category 1</span>
          <h3 style="margin: 0.25rem 0;">Project Title</h3>
          <p style="color: var(--text-muted); font-size: 0.875rem;">Brief project description.</p>
        </div>
      </div>
      <!-- Repeat 6 items with different data-category values -->
    </div>
  </div>
  NOTE: Filter buttons toggle visibility of items by data-category attribute. JS: clicking a filter-btn sets active class and shows/hides items. Use transition for smooth show/hide.""",
}

FILTERABLE_STYLE = """
/* Portfolio filter */
.filter-btn { transition: all 0.3s ease; }
.filter-btn:hover { border-color: var(--primary); color: var(--primary); }
.filter-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
[data-category] { transition: opacity 0.4s ease, transform 0.4s ease; }
[data-category].hidden { opacity: 0; transform: scale(0.9); position: absolute; pointer-events: none; }
"""
