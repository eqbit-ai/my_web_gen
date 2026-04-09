"""
Contact widgets injection: WhatsApp float + Social FAB.

Builds and injects two floating buttons into generated HTML based on a
``contact_config`` dict. The buttons are positioned to avoid collision
with each other AND with any existing back-to-top button:

    Right edge of viewport, vertical stack:
        bottom: 1.5rem  → back-to-top (already exists in animation library)
        bottom: 6rem    → WhatsApp float
        bottom: 10.5rem → Social FAB

The Social FAB, when clicked, reveals a horizontal row of icons fanning
out to the LEFT of the FAB so they don't collide with the WhatsApp button
above. Only platforms with a non-empty URL in ``contact_config["social"]``
are rendered — empty platforms are skipped entirely.

Both widgets are idempotent: if they're already present in the HTML,
the inject helper removes the old copy first and inserts the fresh one.
This lets the settings page update widgets on existing projects without
duplicating them.

Usage::

    from app.utils.contact_widgets import inject_contact_widgets

    html = inject_contact_widgets(html, contact_config={
        "whatsapp": "971501234567",
        "social": {
            "facebook": "https://facebook.com/foo",
            "instagram": "https://instagram.com/foo",
            "tiktok": "",          # empty → not rendered
            "linkedin": "https://linkedin.com/company/foo",
        },
    })
"""

from __future__ import annotations

import re

# Sentinel comments — used to find/remove old widgets on re-injection.
WHATSAPP_FLOAT_START = "<!-- MEYDAN_WHATSAPP_FLOAT -->"
WHATSAPP_FLOAT_END = "<!-- /MEYDAN_WHATSAPP_FLOAT -->"
SOCIAL_FAB_START = "<!-- MEYDAN_SOCIAL_FAB -->"
SOCIAL_FAB_END = "<!-- /MEYDAN_SOCIAL_FAB -->"

# Map of supported social platforms → (font-awesome icon class, brand color).
# Order is the visual reveal order in the FAB fan (left-to-right of the FAB).
SOCIAL_PLATFORMS = [
    ("facebook", "fa-brands fa-facebook-f", "#1877F2"),
    ("instagram", "fa-brands fa-instagram", "#E4405F"),
    ("tiktok", "fa-brands fa-tiktok", "#000000"),
    ("linkedin", "fa-brands fa-linkedin-in", "#0A66C2"),
    ("youtube", "fa-brands fa-youtube", "#FF0000"),
]


def _normalize_whatsapp(num: str) -> str:
    """Strip everything except digits. wa.me URLs accept digits only."""
    if not num:
        return ""
    return re.sub(r"\D+", "", num)


def _strip_existing_widgets(html: str) -> str:
    """Remove any previously-injected MEYDAN_WHATSAPP_FLOAT / MEYDAN_SOCIAL_FAB
    blocks so the inject is idempotent.

    Uses sentinel comments rather than class-name regex so we never accidentally
    strip a user-edited or LLM-generated whatsapp button that doesn't carry our
    sentinel.
    """
    # WhatsApp float
    html = re.sub(
        re.escape(WHATSAPP_FLOAT_START) + r"[\s\S]*?" + re.escape(WHATSAPP_FLOAT_END),
        "",
        html,
    )
    # Social FAB
    html = re.sub(
        re.escape(SOCIAL_FAB_START) + r"[\s\S]*?" + re.escape(SOCIAL_FAB_END),
        "",
        html,
    )
    return html


def _build_whatsapp_html(number: str) -> str:
    """Build the WhatsApp floating button HTML, positioned at bottom: 6rem
    so it stacks above the back-to-top button.
    """
    safe_num = _normalize_whatsapp(number)
    return (
        f"\n{WHATSAPP_FLOAT_START}\n"
        f'<a href="https://wa.me/{safe_num}" target="_blank" rel="noopener" '
        f'class="meydan-whatsapp-float" '
        f'style="position:fixed;bottom:6rem;right:1.5rem;width:3.5rem;height:3.5rem;'
        f'background:#25D366;border-radius:50%;display:flex;align-items:center;'
        f'justify-content:center;color:white;font-size:1.6rem;'
        f'box-shadow:0 4px 12px rgba(0,0,0,0.18);z-index:51;'
        f'transition:transform 0.25s ease,box-shadow 0.25s ease;'
        f'text-decoration:none;" '
        f'aria-label="Chat on WhatsApp" '
        f"onmouseover=\"this.style.transform='scale(1.08)'\" "
        f"onmouseout=\"this.style.transform='scale(1)'\">"
        f'<i class="fa-brands fa-whatsapp"></i></a>\n'
        f"{WHATSAPP_FLOAT_END}\n"
    )


def _build_social_fab_html(social: dict[str, str]) -> str:
    """Build the social-media FAB widget. Renders only platforms whose URL
    is non-empty in ``social``. Returns an empty string if no platforms
    are filled (so we don't inject an empty button).
    """
    # Filter to only filled platforms, preserving SOCIAL_PLATFORMS order.
    items = []
    for key, icon_cls, color in SOCIAL_PLATFORMS:
        url = (social or {}).get(key, "").strip()
        if url:
            items.append((key, icon_cls, color, url))

    if not items:
        return ""

    # Build the icon list. Each icon is an <a> with brand background color.
    # The icons are absolutely-positioned children of the FAB container,
    # initially hidden via opacity:0 + translateX(20px). On .open they
    # animate in with a stagger.
    icons_html = ""
    for i, (key, icon_cls, color, url) in enumerate(items):
        # Each icon shifts further left (60px gap) and uses a stagger delay
        # so they fan out smoothly when the FAB is clicked.
        right_offset = 4.5 + i * 3.5  # rem — first icon at right:4.5rem, then 8, 11.5...
        delay = 50 + i * 40  # ms
        icons_html += (
            f'<a href="{url}" target="_blank" rel="noopener" '
            f'class="meydan-social-icon" '
            f'data-platform="{key}" '
            f'style="position:fixed;bottom:10.5rem;right:{right_offset}rem;'
            f"width:3rem;height:3rem;background:{color};border-radius:50%;"
            f"display:flex;align-items:center;justify-content:center;color:white;"
            f"font-size:1.15rem;text-decoration:none;"
            f"box-shadow:0 4px 12px rgba(0,0,0,0.15);"
            f"opacity:0;transform:translateX(20px) scale(0.7);pointer-events:none;"
            f"transition:opacity 0.3s ease {delay}ms,transform 0.3s ease {delay}ms;"
            f'z-index:51;" '
            f'aria-label="{key.title()}">'
            f'<i class="{icon_cls}"></i></a>'
        )

    # Inline <script> for the toggle. Uses event delegation off document so
    # it survives any DOM rewrite the user does after page load.
    fab_html = (
        f"\n{SOCIAL_FAB_START}\n"
        f"<style>"
        f".meydan-social-fab.open .meydan-social-icon{{"
        f"opacity:1!important;transform:translateX(0) scale(1)!important;"
        f"pointer-events:auto!important;}}"
        f".meydan-social-fab-btn{{position:fixed;bottom:10.5rem;right:1.5rem;"
        f"width:3.5rem;height:3.5rem;background:linear-gradient(135deg,#667eea,#764ba2);"
        f"border-radius:50%;display:flex;align-items:center;justify-content:center;"
        f"color:white;font-size:1.4rem;cursor:pointer;border:none;"
        f"box-shadow:0 4px 12px rgba(0,0,0,0.18);z-index:52;"
        f"transition:transform 0.25s ease,box-shadow 0.25s ease;}}"
        f".meydan-social-fab-btn:hover{{transform:scale(1.08);}}"
        f".meydan-social-fab.open .meydan-social-fab-btn{{transform:rotate(45deg);}}"
        f"</style>"
        f'<div class="meydan-social-fab">'
        f'<button type="button" class="meydan-social-fab-btn" '
        f'aria-label="Show social media links" aria-expanded="false">'
        f'<i class="fa-solid fa-share-nodes"></i></button>'
        f"{icons_html}"
        f"</div>"
        f"<script>(function(){{"
        f"var wrap=document.querySelector('.meydan-social-fab');"
        f"if(!wrap)return;"
        f"var btn=wrap.querySelector('.meydan-social-fab-btn');"
        f"function close(){{wrap.classList.remove('open');btn.setAttribute('aria-expanded','false');}}"
        f"btn.addEventListener('click',function(e){{"
        f"e.stopPropagation();"
        f"var open=wrap.classList.toggle('open');"
        f"btn.setAttribute('aria-expanded',open?'true':'false');"
        f"}});"
        f"document.addEventListener('click',function(e){{"
        f"if(!wrap.contains(e.target))close();"
        f"}});"
        f"document.addEventListener('keydown',function(e){{"
        f"if(e.key==='Escape')close();"
        f"}});"
        f"}})();</script>"
        f"\n{SOCIAL_FAB_END}\n"
    )
    return fab_html


def inject_contact_widgets(html: str, contact_config: dict | None) -> str:
    """Inject WhatsApp + Social FAB widgets into the given HTML based on
    ``contact_config``. Idempotent — old MEYDAN_* sentinel blocks are
    stripped before insertion, so calling this multiple times produces
    a single up-to-date copy of each widget.

    ``contact_config`` shape::

        {
            "whatsapp": "971501234567",   # optional, digits only at inject time
            "social": {                    # optional dict
                "facebook": "https://...",
                "instagram": "https://...",
                "tiktok": "https://...",
                "linkedin": "https://...",
            },
        }

    If ``whatsapp`` is missing or empty, no WhatsApp button is injected.
    If ``social`` is missing or all four platforms are empty, no FAB is
    injected. The function still strips any pre-existing sentinel blocks
    in either case, so passing an empty config effectively REMOVES both
    widgets — useful for the "clear all contact widgets" path in settings.
    """
    if not html:
        return html

    config = contact_config or {}

    # Always strip first so the function is fully idempotent.
    html = _strip_existing_widgets(html)

    pieces: list[str] = []
    whatsapp_num = _normalize_whatsapp(config.get("whatsapp") or "")
    if whatsapp_num:
        pieces.append(_build_whatsapp_html(whatsapp_num))

    social = config.get("social") or {}
    fab_html = _build_social_fab_html(social)
    if fab_html:
        pieces.append(fab_html)

    if not pieces:
        return html

    blob = "".join(pieces)
    # Insert before </body> if possible, otherwise append.
    if "</body>" in html:
        return html.replace("</body>", f"{blob}</body>", 1)
    return html + blob
