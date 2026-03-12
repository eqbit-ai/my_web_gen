"""Feature section pattern templates."""

PATTERNS = {
    "card_grid": """card_grid pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card" data-aos="fade-up" data-aos-delay="100">
      <div class="icon-box" style="background: color-mix(in srgb, var(--accent) 12%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h3 class="card-title">Title</h3>
      <p class="card-text">Description</p>
    </div>
  </div>
  NOTE: Light themes use subtle borders. Card borders are handled by the .card class in the style block.""",
    "icon_grid": """icon_grid pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-4 text-center">
    <div class="p-6" data-aos="zoom-in" data-aos-delay="100">
      <div class="icon-box" style="background: color-mix(in srgb, var(--accent) 10%, transparent)"><i class="fa-solid fa-xxx"></i></div>
      <h4 class="card-title">Title</h4>
      <p class="card-text">Short description</p>
    </div>
  </div>""",
    "feature_split": """feature_split pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container feature-split-list">
    <div class="grid-2" data-aos="fade-right">
      <div><h3 class="feature-title">Title</h3><p class="feature-text">Description</p></div>
      <div class="img-wrapper"><img src="{{IMG:feature specific query from plan}}" alt="Feature name" class="img-cover"></div>
    </div>
    <div class="grid-2" data-aos="fade-left">
      <div class="md-order-2"><h3 class="feature-title">Title</h3><p class="feature-text">Description</p></div>
      <div class="img-wrapper md-order-1"><img src="{{IMG:feature different query}}" alt="Feature name" class="img-cover"></div>
    </div>
  </div>
  NOTE: Alternate rows. Second row uses md-order to flip text/image.""",
    "feature_cards": """feature_cards pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card" data-aos="fade-up" data-aos-delay="100">
      <div class="img-wrapper"><img src="{{IMG:feature image query from plan}}" alt="Feature name" class="card-image"></div>
      <div class="card-body">
        <h3 class="card-title">Title</h3>
        <p class="card-text">Description</p>
      </div>
    </div>
  </div>
  NOTE: Each card MUST have a unique {{IMG:feature ...}} with the image_query from the plan.""",
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
}
