"""CTA section pattern templates."""

PATTERNS = {
    "cta_banner": """cta_banner pattern:
  <div class="container" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: var(--radius); padding: 3rem 2rem; text-align: center;">
    <h2 class="section-title" style="color: white;">Headline</h2>
    <p class="section-subtitle" style="color: rgba(255,255,255,0.8);">Description</p>
    <div class="btn-group center">
      <a href="#" class="btn-primary-light">Primary CTA</a>
      <a href="#" class="btn-secondary-light">Secondary CTA</a>
    </div>
  </div>""",
    "cta_split": """cta_split pattern:
  <div class="container grid-2">
    <div>
      <h2 class="section-title">Headline</h2>
      <p class="section-subtitle" style="margin-bottom: 1.5rem;">Description</p>
      <div class="btn-group">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary">Secondary CTA</a>
      </div>
    </div>
    <div class="img-wrapper">
      <img src="{{IMG:cta image query from plan}}" alt="Call to action" class="img-cover">
    </div>
  </div>""",
    "cta_gradient": """cta_gradient pattern:
  <div style="background: linear-gradient(135deg, var(--primary), var(--secondary)); text-align: center; padding: 4rem 0; position: relative;">
    <div class="container-narrow">
      <h2 class="section-title" style="color: white;">Headline</h2>
      <p class="section-subtitle" style="color: rgba(255,255,255,0.8);">Description</p>
      <a href="#" class="btn-primary-light">Primary CTA</a>
    </div>
  </div>""",
    "cta_centered": """cta_centered pattern:
  <div class="container-narrow" style="text-align: center;">
    <h2 class="section-title">Headline</h2>
    <p class="section-subtitle" style="margin-bottom: 1.5rem;">Description</p>
    <a href="#" class="btn-primary">Primary CTA</a>
  </div>
  NOTE: Simple, clean centered CTA. No gradient background.""",
}
