"""Pre-built interactive templates for common UI patterns.
LLM fills in data, templates handle the structure."""

DETAIL_MODAL_CSS = """
/* Detail Modal Styles */
.detail-modal-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    backdrop-filter: blur(4px);
    z-index: 9999;
    padding: 2rem;
    overflow-y: auto;
}
.detail-modal-overlay.active {
    display: flex;
    align-items: center;
    justify-content: center;
}
.detail-modal {
    background: white;
    border-radius: 16px;
    max-width: 720px;
    width: 100%;
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: 0 25px 60px rgba(0,0,0,0.3);
    animation: modalSlideUp 0.3s ease;
    position: relative;
}
@keyframes modalSlideUp {
    from { transform: translateY(30px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}
.detail-modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    background: rgba(0,0,0,0.08);
    color: #333;
    font-size: 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
    transition: background 0.2s;
}
.detail-modal-close:hover { background: rgba(0,0,0,0.15); }
.detail-modal-image {
    width: 100%;
    height: 280px;
    object-fit: cover;
    border-radius: 16px 16px 0 0;
}
.detail-modal-body {
    padding: 2rem;
}
.detail-modal-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 0.75rem;
}
.detail-modal-desc {
    color: #555;
    line-height: 1.7;
    margin-bottom: 1.5rem;
    font-size: 1.05rem;
}
.detail-modal-features {
    list-style: none;
    padding: 0;
    margin: 0 0 1.5rem 0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
}
.detail-modal-features li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #444;
    font-size: 0.95rem;
    padding: 0.4rem 0;
}
.detail-modal-features li::before {
    content: '\\2713';
    color: var(--primary, #4f46e5);
    font-weight: bold;
    flex-shrink: 0;
}
.detail-modal-cta {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.75rem;
    background: var(--primary, #4f46e5);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    text-decoration: none;
}
.detail-modal-cta:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79,70,229,0.4);
    color: white;
}
@media (max-width: 640px) {
    .detail-modal-overlay { padding: 1rem; }
    .detail-modal-image { height: 200px; }
    .detail-modal-body { padding: 1.25rem; }
    .detail-modal-features { grid-template-columns: 1fr; }
}
"""

# This HTML snippet gets injected at the end of the page body
# It includes both the modal container and the JS — all self-contained
DETAIL_MODAL_HTML_SNIPPET = """
<!-- Detail Modal System -->
<div id="detail-modal-overlay" class="detail-modal-overlay">
  <div class="detail-modal" id="detail-modal-content"></div>
</div>
<script>
(function(){
  var overlay = document.getElementById('detail-modal-overlay');
  var modal = document.getElementById('detail-modal-content');

  // Close handlers
  overlay.addEventListener('click', function(e){ if(e.target===overlay){closeModal();} });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape'){closeModal();} });

  function openModal(card){
    var title = card.getAttribute('data-detail-title') || '';
    var desc = card.getAttribute('data-detail-desc') || '';
    var feats = (card.getAttribute('data-detail-features') || '').split('|').filter(Boolean);
    var img = card.getAttribute('data-detail-image') || '';
    var cta = card.getAttribute('data-detail-cta') || 'Book Appointment';
    var ctaLink = card.getAttribute('data-detail-cta-link') || '#contact';

    var html = '<button class="detail-modal-close" id="detail-modal-close-btn">&times;</button>';
    if(img){ html += '<img class="detail-modal-image" src="'+img+'" alt="'+title+'" loading="lazy">'; }
    html += '<div class="detail-modal-body">';
    html += '<h3 class="detail-modal-title">'+title+'</h3>';
    html += '<p class="detail-modal-desc">'+desc+'</p>';
    if(feats.length){
      html += '<ul class="detail-modal-features">';
      feats.forEach(function(f){ html += '<li>'+f.trim()+'</li>'; });
      html += '</ul>';
    }
    html += '<a href="'+ctaLink+'" class="detail-modal-cta">'+cta+' &rarr;</a>';
    html += '</div>';
    modal.innerHTML = html;

    document.getElementById('detail-modal-close-btn').addEventListener('click', closeModal);

    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeModal(){
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  // Event delegation — catches ALL clicks, no need to bind to specific elements
  document.addEventListener('click', function(e){
    // Find the closest card with data-detail-title
    var card = e.target.closest('[data-detail-title]');
    if(!card) return;

    // Check if clicked on "Learn More" text or the card itself
    var el = e.target;
    var text = el.textContent.trim().toLowerCase();
    var isLearnMore = text.indexOf('learn more') !== -1 || text.indexOf('read more') !== -1 || text.indexOf('view detail') !== -1 || text.indexOf('more info') !== -1;
    var parentText = el.parentElement ? el.parentElement.textContent.trim().toLowerCase() : '';
    var isParentLearnMore = parentText.indexOf('learn more') !== -1 || parentText.indexOf('read more') !== -1;

    if(isLearnMore || isParentLearnMore){
      e.preventDefault();
      e.stopPropagation();
      openModal(card);
    }
  });

  // Also make Learn More elements look clickable
  document.querySelectorAll('[data-detail-title]').forEach(function(card){
    var els = card.querySelectorAll('a, div, span, button, p');
    for(var i=0; i<els.length; i++){
      var t = els[i].textContent.trim().toLowerCase();
      if(t.indexOf('learn more')!==-1 || t.indexOf('read more')!==-1){
        els[i].style.cursor = 'pointer';
        break;
      }
    }
  });
})();
</script>
"""

# The prompt sent to the LLM - it only needs to add data attributes to existing cards
DETAIL_MODAL_PROMPT = """You need to add detail modal data to the service/feature cards in this section.

TASK: Add data attributes to each card element so the pre-built modal system can show detailed information.

For EACH card/service item in the section, add these data attributes to the card's container element:
- data-detail-title="[Service/Feature Name]"
- data-detail-desc="[2-3 sentences with detailed description about this service, specific to the business]"
- data-detail-features="Feature 1|Feature 2|Feature 3|Feature 4|Feature 5|Feature 6" (pipe-separated list of 4-6 key features/benefits)
- data-detail-image="[keep existing image src if the card has one — look for <img> tags inside the card and copy their src]"
- data-detail-cta="Book Appointment" (or appropriate CTA for the business type)
- data-detail-cta-link="#contact"

RULES:
- ONLY add data-detail-* attributes to each card container. Do NOT change any other HTML.
- Keep ALL existing classes, content, structure, images exactly as-is.
- The "Learn More" links should keep their existing markup (the JS will auto-bind them).
- Write descriptions that are professional, specific to the business, and informative.
- Output the modified section in a ```html code block.
"""


def get_detail_modal_template():
    """Return the CSS + HTML snippet for the detail modal system."""
    return {
        "css": DETAIL_MODAL_CSS,
        "html_snippet": DETAIL_MODAL_HTML_SNIPPET,
    }


def get_detail_modal_prompt():
    """Return the prompt to send to the LLM for adding data attributes."""
    return DETAIL_MODAL_PROMPT
