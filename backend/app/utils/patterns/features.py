"""Feature section pattern templates — PREMIUM quality, Envato-level design."""

PATTERNS = {
    "card_grid": """card_grid pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card" data-aos="fade-up" data-aos-delay="100" style="padding:2rem;position:relative;overflow:hidden;">
      <!-- Accent top border -->
      <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--primary),var(--accent));opacity:0;transition:opacity 0.3s;"></div>
      <div class="icon-box" style="background:linear-gradient(135deg, color-mix(in srgb, var(--primary) 15%, transparent), color-mix(in srgb, var(--accent) 10%, transparent));"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="card-title">Title</h3>
      <p class="card-text">Description</p>
    </div>
  </div>
  NOTE: Each card has a gradient top border that appears on hover (add CSS: .card:hover > div:first-child { opacity: 1; }). Icon boxes use gradient backgrounds instead of flat color. Light themes use subtle borders.""",
    "icon_grid": """icon_grid pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-4 text-center">
    <div style="padding:2rem;" data-aos="zoom-in" data-aos-delay="100">
      <div class="icon-box" style="background:linear-gradient(135deg, var(--primary), var(--secondary));color:white;width:3.5rem;height:3.5rem;margin:0 auto 1.25rem;"><i class="fa-solid fa-xxx"></i></div>
      <h4 class="card-title">Title</h4>
      <p class="card-text">Short description</p>
    </div>
  </div>
  NOTE: Icon boxes use gradient backgrounds with white icons for a premium, polished look.""",
    "feature_split": """feature_split pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container feature-split-list">
    <div class="grid-2" data-aos="fade-right" style="gap:4rem;">
      <div>
        <span class="section-label"><span class="label-line"></span>FEATURE</span>
        <h3 class="feature-title" style="font-size:1.5rem;margin-bottom:1rem;">Title</h3>
        <p class="feature-text" style="margin-bottom:1.5rem;">Description</p>
        <!-- Feature bullet points -->
        <ul style="list-style:none;padding:0;margin:0;">
          <li style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;"><i class="fa-solid fa-check" style="color:var(--accent);font-size:0.8rem;"></i><span style="color:var(--text-muted);font-size:0.9rem;">Key benefit point</span></li>
          <li style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;"><i class="fa-solid fa-check" style="color:var(--accent);font-size:0.8rem;"></i><span style="color:var(--text-muted);font-size:0.9rem;">Key benefit point</span></li>
        </ul>
      </div>
      <div class="img-wrapper" style="border-radius:var(--radius);overflow:hidden;"><img src="{{IMG:feature specific query from plan}}" alt="Feature name" class="img-cover"></div>
    </div>
    <div class="grid-2" data-aos="fade-left" style="gap:4rem;">
      <div class="md-order-2">
        <span class="section-label"><span class="label-line"></span>FEATURE</span>
        <h3 class="feature-title" style="font-size:1.5rem;margin-bottom:1rem;">Title</h3>
        <p class="feature-text" style="margin-bottom:1.5rem;">Description</p>
        <ul style="list-style:none;padding:0;margin:0;">
          <li style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;"><i class="fa-solid fa-check" style="color:var(--accent);font-size:0.8rem;"></i><span style="color:var(--text-muted);font-size:0.9rem;">Key benefit point</span></li>
          <li style="display:flex;align-items:center;gap:0.75rem;padding:0.5rem 0;"><i class="fa-solid fa-check" style="color:var(--accent);font-size:0.8rem;"></i><span style="color:var(--text-muted);font-size:0.9rem;">Key benefit point</span></li>
        </ul>
      </div>
      <div class="img-wrapper md-order-1" style="border-radius:var(--radius);overflow:hidden;"><img src="{{IMG:feature different query}}" alt="Feature name" class="img-cover"></div>
    </div>
  </div>
  NOTE: Each feature row has a section label, larger title, description, AND bullet-point benefits. This creates much richer content blocks. Alternate rows — second row uses md-order to flip text/image. Customize the label text, bullet points to match the business.""",
    "feature_cards": """feature_cards pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card" data-aos="fade-up" data-aos-delay="100" style="padding:0;overflow:hidden;">
      <div class="img-wrapper" style="position:relative;">
        <img src="{{IMG:feature image query from plan}}" alt="Feature name" class="card-image">
        <!-- Category badge on image -->
        <span style="position:absolute;top:1rem;left:1rem;background:var(--primary);color:white;font-size:0.7rem;font-weight:600;padding:0.25rem 0.75rem;border-radius:50px;text-transform:uppercase;letter-spacing:0.05em;">Category</span>
      </div>
      <div class="card-body" style="padding:1.5rem;">
        <h3 class="card-title">Title</h3>
        <p class="card-text">Description</p>
      </div>
    </div>
  </div>
  NOTE: Each card has a category badge overlaying the image for a polished editorial look. Each card MUST have a unique {{IMG:feature ...}} with the image_query from the plan. Customize the category badge text per card.""",
    "feature_stacked": """feature_stacked pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container-narrow stacked-list">
    <div class="stacked-item" data-aos="fade-right">
      <div class="icon-box" style="background: color-mix(in srgb, var(--accent) 10%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <div>
        <h3 class="card-title">Title</h3>
        <p class="feature-text">Long detailed description of this feature or service.</p>
      </div>
    </div>
  </div>
  NOTE: Light themes use divide-gray-100 instead of divide-white/10.""",
    "feature_steps": """feature_steps pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="steps-container container-narrow">
    <div class="step-item" data-aos="fade-up" data-aos-delay="100">
      <div class="step-number" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">1</div>
      <div>
        <h3 class="card-title">Step Title</h3>
        <p class="feature-text">Description of this step.</p>
      </div>
    </div>
    <div class="step-item" data-aos="fade-up" data-aos-delay="200">
      <div class="step-number" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">2</div>
      <div>
        <h3 class="card-title">Step Title</h3>
        <p class="feature-text">Description of this step.</p>
      </div>
    </div>
    <div class="step-item" data-aos="fade-up" data-aos-delay="300">
      <div class="step-number" style="background: linear-gradient(135deg, var(--primary), var(--secondary))">3</div>
      <div>
        <h3 class="card-title">Step Title</h3>
        <p class="feature-text">Description of this step.</p>
      </div>
    </div>
  </div>
  NOTE: The connecting vertical line is handled by .steps-container in the <style> block. Use 3 or 4 steps.""",

    "feature_bento_grid": """feature_bento_grid pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container" style="display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: auto auto; gap: 1.5rem;">
    <!-- Large featured card spanning 2 columns -->
    <div class="card fade-up" style="grid-column: span 2; padding: 2.5rem; display: flex; flex-direction: column; justify-content: space-between; min-height: 320px; background: linear-gradient(135deg, color-mix(in srgb, var(--primary) 8%, var(--bg-surface)), var(--bg-surface));">
      <div>
        <div class="icon-box" style="background: color-mix(in srgb, var(--primary) 15%, transparent); width: 56px; height: 56px;"><i class="fa-solid fa-xxx" style="font-size: 1.25rem;"></i></div>
        <h3 style="margin: 1rem 0 0.5rem; font-size: 1.5rem;">Main Feature Title</h3>
        <p style="color: var(--text-muted); max-width: 400px;">Detailed description of the primary feature.</p>
      </div>
      <a href="#" class="btn-primary" style="align-self: flex-start; margin-top: 1.5rem;">Learn More</a>
    </div>
    <!-- Tall card spanning 2 rows -->
    <div class="card fade-up" style="grid-row: span 2; padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem;">
      <div class="img-wrapper" style="flex: 1; min-height: 200px;"><img src="{{IMG:feature product detail}}" alt="Feature" class="img-cover"></div>
      <div>
        <h3 style="margin-bottom: 0.5rem;">Feature Title</h3>
        <p style="color: var(--text-muted);">Description text.</p>
      </div>
    </div>
    <!-- Two small cards in bottom-left -->
    <div class="card fade-up" style="padding: 2rem;">
      <div class="icon-box" style="background: color-mix(in srgb, var(--accent) 12%, transparent);"><i class="fa-solid fa-xxx"></i></div>
      <h3 style="margin: 0.75rem 0 0.25rem;">Feature</h3>
      <p style="color: var(--text-muted); font-size: 0.875rem;">Short description.</p>
    </div>
    <div class="card fade-up" style="padding: 2rem;">
      <div class="icon-box" style="background: color-mix(in srgb, var(--accent) 12%, transparent);"><i class="fa-solid fa-xxx"></i></div>
      <h3 style="margin: 0.75rem 0 0.25rem;">Feature</h3>
      <p style="color: var(--text-muted); font-size: 0.875rem;">Short description.</p>
    </div>
  </div>
  NOTE: Bento grid layout inspired by Apple/Linear. Large card spans 2 cols, tall card spans 2 rows, 2 small cards fill remaining space. On mobile: single column stack. Use subtle gradient on the large card for emphasis.""",

    "feature_hover_cards": """feature_hover_cards pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3 stagger-reveal">
    <div class="card card-lift stagger-child" style="padding: 2.5rem; text-align: center; position: relative; overflow: hidden;">
      <!-- Decorative gradient circle behind icon -->
      <div style="position: absolute; top: -30px; right: -30px; width: 120px; height: 120px; border-radius: 50%; background: linear-gradient(135deg, color-mix(in srgb, var(--primary) 15%, transparent), transparent); pointer-events: none;"></div>
      <div class="icon-box" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; width: 64px; height: 64px; margin: 0 auto 1.25rem;"><i class="fa-solid fa-xxx" style="font-size: 1.5rem;"></i></div>
      <h3 class="card-title" style="margin-bottom: 0.75rem;">Feature Title</h3>
      <p class="card-text">Feature description with enough detail to show value.</p>
      <a href="#" style="display: inline-block; margin-top: 1rem; color: var(--primary); font-weight: 600; font-size: 0.875rem;">Learn More <i class="fa-solid fa-arrow-right" style="font-size: 0.75rem;"></i></a>
    </div>
    <!-- Repeat 3-6 cards -->
  </div>
  NOTE: card-lift class provides Y-translate on hover. Decorative gradient circle adds depth. Icon uses gradient background instead of flat color. Each card has a "Learn More" link for premium feel.""",

    "feature_accordion_visual": """feature_accordion_visual pattern:
  <div class="container grid-2" style="gap: 3rem; align-items: start;">
    <div>
      <span class="section-label"><span class="label-line"></span>FEATURES</span>
      <h2 class="section-title">Headline</h2>
      <p class="section-subtitle" style="margin-bottom: 2rem;">Brief intro text.</p>
      <!-- Accordion items -->
      <div class="feature-accordion">
        <div class="feature-acc-item active" data-target="feat-img-1">
          <button class="feature-acc-trigger">
            <div style="display: flex; align-items: center; gap: 1rem;">
              <div class="icon-box" style="background: color-mix(in srgb, var(--primary) 12%, transparent); flex-shrink: 0;"><i class="fa-solid fa-xxx"></i></div>
              <h3 style="margin: 0; font-size: 1.1rem;">Feature Title</h3>
            </div>
            <i class="fa-solid fa-chevron-down" style="transition: transform 0.3s;"></i>
          </button>
          <div class="feature-acc-content">
            <p style="color: var(--text-muted); padding: 0 0 0 calc(40px + 1rem);">Detailed description of this feature and its benefits.</p>
          </div>
        </div>
        <!-- Repeat 3-4 items -->
      </div>
    </div>
    <div style="position: sticky; top: 2rem;">
      <!-- Image changes based on active accordion item -->
      <div class="img-wrapper" style="border-radius: var(--radius); overflow: hidden;">
        <img id="feat-img-1" src="{{IMG:feature visual}}" alt="Feature" class="img-cover feature-acc-img active" style="aspect-ratio: 4/3;">
      </div>
    </div>
  </div>
  NOTE: Left accordion, right sticky image that swaps based on active item. JS: clicking accordion item shows its content and swaps the image. Premium Apple-style interactive feature showcase. On mobile: image stacks above accordion.""",
}
