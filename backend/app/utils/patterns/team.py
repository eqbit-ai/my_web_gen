"""Team section pattern templates."""

PATTERNS = {
    "team_grid": """team_grid pattern:
  IMPORTANT: Keep team card content SHORT — name (1 line) and role/title (1 line only). Do NOT add credentials, bar admissions, or long descriptions. The card has fixed height and will clip overflow.
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card team-card" data-aos="zoom-in" data-aos-delay="100" style="overflow:visible">
      <img src="{{IMG:team professional man portrait studio}}" alt="Name" class="team-photo">
      <div class="card-body">
        <h3 class="card-title">Name</h3>
        <p class="card-text">Role / Title</p>
      </div>
    </div>
  </div>""",
    "team_cards": """team_cards pattern:
  IMPORTANT: Keep team card content SHORT — name (1 line), role (1 line), and bio (1-2 short sentences MAX). Do NOT list credentials, degrees, or bar admissions. The card has fixed height and will clip overflow.
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container grid-3">
    <div class="card team-card" data-aos="flip-up" data-aos-delay="100" style="overflow:visible">
      <img src="{{IMG:team professional woman portrait studio}}" alt="Name" class="team-photo">
      <div class="card-body">
        <h3 class="card-title">Name</h3>
        <p class="card-text">Role / Title</p>
        <p class="card-text" style="margin-top: 0.5rem;">One short sentence about expertise.</p>
      </div>
    </div>
  </div>""",
    "team_masonry": """team_masonry pattern:
  <div class="section-header"><h2 class="section-title">Headline</h2><p class="section-subtitle">Subheadline</p></div>
  <div class="container masonry-grid">
    <div class="masonry-item" data-aos="fade-up" data-aos-delay="100">
      <img src="{{IMG:team professional man portrait studio}}" alt="Name" class="img-cover">
      <div class="masonry-overlay">
        <h3>Name</h3>
        <p>Role</p>
      </div>
    </div>
  </div>""",
}
