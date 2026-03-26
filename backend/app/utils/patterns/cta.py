"""CTA section pattern templates — PREMIUM quality, Envato-level design."""

PATTERNS = {
    "cta_banner": """cta_banner pattern:
  <div class="container" style="background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: var(--radius); padding: 4rem 3rem; text-align: center; position:relative; overflow:hidden;">
    <!-- Decorative circles for depth -->
    <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,0.05);"></div>
    <div style="position:absolute;bottom:-60px;left:-30px;width:250px;height:250px;border-radius:50%;background:rgba(255,255,255,0.03);"></div>
    <h2 class="section-title" style="color: white; position:relative;">Headline</h2>
    <p class="section-subtitle" style="color: rgba(255,255,255,0.85); position:relative;">Description</p>
    <div class="btn-group center" style="position:relative;">
      <a href="#" class="btn-primary-light">Primary CTA</a>
      <a href="#" class="btn-secondary-light">Secondary CTA</a>
    </div>
  </div>
  NOTE: Decorative background circles add depth and visual interest to the gradient banner.""",
    "cta_split": """cta_split pattern:
  <div class="container grid-2" style="gap:4rem;">
    <div>
      <span class="section-label"><span class="label-line"></span>GET STARTED</span>
      <h2 class="section-title" style="margin-bottom:1rem;">Headline</h2>
      <p class="section-subtitle" style="margin-bottom: 1.5rem;">Description</p>
      <div class="btn-group">
        <a href="#" class="btn-primary">Primary CTA</a>
        <a href="#" class="btn-secondary">Secondary CTA</a>
      </div>
      <p style="font-size:0.8rem;color:var(--text-muted);margin-top:1rem;"><i class="fa-solid fa-shield-halved" style="margin-right:0.5rem;"></i>No commitment required</p>
    </div>
    <div class="img-wrapper" style="border-radius:var(--radius);overflow:hidden;">
      <img src="{{IMG:cta image query from plan}}" alt="Call to action" class="img-cover">
    </div>
  </div>
  NOTE: Added section label, trust signal below CTAs for premium feel.""",
    "cta_gradient": """cta_gradient pattern:
  <div style="background: linear-gradient(135deg, var(--primary), var(--secondary)); text-align: center; padding: 5rem 0; position: relative; overflow:hidden;">
    <!-- Decorative elements -->
    <div style="position:absolute;top:50%;left:10%;width:300px;height:300px;border-radius:50%;background:rgba(255,255,255,0.04);transform:translateY(-50%);"></div>
    <div style="position:absolute;top:20%;right:5%;width:150px;height:150px;border-radius:50%;background:rgba(255,255,255,0.06);"></div>
    <div class="container-narrow" style="position:relative;">
      <h2 class="section-title" style="color: white; font-size:clamp(1.75rem, 3.5vw, 2.5rem);">Headline</h2>
      <p class="section-subtitle" style="color: rgba(255,255,255,0.85); margin-bottom:2rem;">Description</p>
      <a href="#" class="btn-primary-light" style="padding:1rem 2.5rem;font-size:1.05rem;">Primary CTA</a>
    </div>
  </div>
  NOTE: Decorative circles add depth. Larger button for emphasis.""",
    "cta_centered": """cta_centered pattern:
  <div class="container-narrow" style="text-align: center;">
    <span class="section-label" style="justify-content:center;"><span class="label-line"></span>READY TO START<span class="label-line"></span></span>
    <h2 class="section-title">Headline</h2>
    <p class="section-subtitle" style="margin-bottom: 2rem;">Description</p>
    <a href="#" class="btn-primary" style="padding:0.875rem 2.5rem;">Primary CTA</a>
  </div>
  NOTE: Added section label for visual hierarchy. Slightly larger button padding.""",

    "cta_sticky_reveal": """cta_sticky_reveal pattern:
  <div style="position: relative; overflow: hidden;">
    <div class="container" style="display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; align-items: center; min-height: 400px;">
      <div class="fade-up">
        <span class="section-label"><span class="label-line"></span>GET STARTED</span>
        <h2 class="section-title" style="margin-bottom: 1rem;">Compelling headline that drives action</h2>
        <p style="color: var(--text-muted); margin-bottom: 2rem;">Persuasive description explaining exactly what happens when they click. Remove friction, build confidence.</p>
        <div class="btn-group">
          <a href="#" class="btn-primary" style="padding: 1rem 2.5rem; font-size: 1.1rem;">Primary CTA</a>
          <a href="#" class="btn-secondary">Secondary CTA</a>
        </div>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 1rem;"><i class="fa-solid fa-shield-halved" style="margin-right: 0.5rem;"></i>No credit card required &bull; Free 14-day trial</p>
      </div>
      <div class="fade-up" style="position: relative;">
        <div class="card" style="padding: 2.5rem; text-align: center; background: linear-gradient(135deg, color-mix(in srgb, var(--primary) 5%, var(--bg-surface)), var(--bg-surface));">
          <div style="font-size: 3rem; font-weight: 800; color: var(--primary); margin-bottom: 0.5rem;">$99<span style="font-size: 1rem; color: var(--text-muted);">/mo</span></div>
          <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Everything you need to get started</p>
          <ul style="text-align: left; list-style: none; padding: 0; margin-bottom: 2rem;">
            <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.75rem;"><i class="fa-solid fa-check" style="color: var(--primary);"></i> Feature one</li>
            <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.75rem;"><i class="fa-solid fa-check" style="color: var(--primary);"></i> Feature two</li>
            <li style="padding: 0.5rem 0; display: flex; align-items: center; gap: 0.75rem;"><i class="fa-solid fa-check" style="color: var(--primary);"></i> Feature three</li>
          </ul>
          <a href="#" class="btn-primary" style="display: block; width: 100%; text-align: center;">Get Started Now</a>
        </div>
      </div>
    </div>
  </div>
  NOTE: Left side is persuasive copy with trust signals. Right side is a pricing/signup card. On mobile: stack vertically. The trust line (no credit card, etc.) reduces friction.""",

    "cta_parallax": """cta_parallax pattern:
  <div style="position: relative; background-image: url('{{IMG:dramatic background landscape}}'); background-size: cover; background-position: center; background-attachment: fixed; padding: 6rem 0;">
    <div style="position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,0,0,0.75), rgba(0,0,0,0.5));"></div>
    <div class="container-narrow" style="position: relative; z-index: 2; text-align: center;">
      <h2 class="section-title" style="color: white; font-size: 2.5rem;">Headline</h2>
      <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">Description text that compels action.</p>
      <div class="btn-group center">
        <a href="#" class="btn-primary" style="padding: 1rem 2.5rem;">Primary CTA</a>
        <a href="#" class="btn-secondary" style="color: white; border-color: rgba(255,255,255,0.3);">Secondary CTA</a>
      </div>
    </div>
  </div>
  NOTE: background-attachment: fixed creates parallax scroll effect. Image stays while content moves. Gradient overlay ensures text readability. On mobile, background-attachment: fixed may not work — fallback is fine (scroll). Very cinematic, high-end feel.""",
}
