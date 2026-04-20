"""
Contact widgets injection: Social FAB (floating) + footer social-links row.

Builds two sets of social/contact icons from a ``contact_config`` dict:

    1. **Social FAB** — a floating ring button at the right edge of the
       viewport that fans out to reveal every configured icon (brand
       socials + WhatsApp + map). Click the FAB to toggle.

    2. **Footer social row** — the LLM generates a placeholder
       ``<div class="social-links">`` in the footer with empty hrefs.
       We find every such div and replace its contents with real
       anchors wired to the user-provided URLs.

Both are idempotent: sentinel comments and a full replacement pass
ensure re-running the inject produces a single up-to-date copy.

Usage::

    from app.utils.contact_widgets import inject_contact_widgets

    html = inject_contact_widgets(html, contact_config={
        "whatsapp": "971501234567",
        "mapLink": "https://maps.google.com/?q=...",
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
FOOTER_SOCIAL_START = "<!-- MEYDAN_FOOTER_SOCIAL -->"
FOOTER_SOCIAL_END = "<!-- /MEYDAN_FOOTER_SOCIAL -->"

# Map of supported social platforms → (font-awesome icon class, brand color).
# Order is the visual reveal order in the FAB fan (left-to-right of the FAB).
SOCIAL_PLATFORMS = [
    ("facebook", "fa-brands fa-facebook-f", "#1877F2"),
    ("instagram", "fa-brands fa-instagram", "#E4405F"),
    ("tiktok", "fa-brands fa-tiktok", "#000000"),
    ("linkedin", "fa-brands fa-linkedin-in", "#0A66C2"),
    ("youtube", "fa-brands fa-youtube", "#FF0000"),
]

# WhatsApp + map are treated as social icons too — they share the same
# container (FAB + footer) as the brand platforms.
WHATSAPP_META = ("whatsapp", "fa-brands fa-whatsapp", "#25D366", "WhatsApp")
MAP_META = ("map", "fa-solid fa-location-dot", "#EA4335", "Location")


def _normalize_whatsapp(num: str) -> str:
    """Strip everything except digits. wa.me URLs accept digits only."""
    if not num:
        return ""
    return re.sub(r"\D+", "", num)


def _collect_icons(config: dict) -> list[tuple[str, str, str, str, str]]:
    """Return the ordered list of (key, icon_class, color, url, label) for
    every non-empty icon in the config. Used by both the FAB and the
    footer row so they stay in sync.
    """
    social = (config or {}).get("social") or {}
    icons: list[tuple[str, str, str, str, str]] = []

    for key, icon_cls, color in SOCIAL_PLATFORMS:
        url = (social.get(key) or "").strip()
        if url:
            icons.append((key, icon_cls, color, url, key.title()))

    wa_num = _normalize_whatsapp(config.get("whatsapp") or "")
    if wa_num:
        key, icon_cls, color, label = WHATSAPP_META
        icons.append((key, icon_cls, color, f"https://wa.me/{wa_num}", label))

    map_link = (config.get("mapLink") or "").strip()
    if map_link:
        key, icon_cls, color, label = MAP_META
        icons.append((key, icon_cls, color, map_link, label))

    return icons


def _strip_existing_widgets(html: str) -> str:
    """Remove any previously-injected MEYDAN_* widget blocks so the inject
    is idempotent. Also strips:
      - LLM-hardcoded ``.whatsapp-float`` anchors (the cheatsheet still
        mentions this class; stripping avoids a duplicate fixed-position
        button alongside the FAB).
      - The legacy MEYDAN_WHATSAPP_FLOAT block: we no longer inject the
        fixed floater, so existing sessions heal on re-injection.
    """
    # Legacy fixed-position WhatsApp float (we removed this widget)
    html = re.sub(
        re.escape(WHATSAPP_FLOAT_START) + r"[\s\S]*?" + re.escape(WHATSAPP_FLOAT_END),
        "",
        html,
    )
    # Social FAB (sentinel-wrapped)
    html = re.sub(
        re.escape(SOCIAL_FAB_START) + r"[\s\S]*?" + re.escape(SOCIAL_FAB_END),
        "",
        html,
    )
    # LLM-hardcoded whatsapp float anchors with class "whatsapp-float" (NOT our
    # "meydan-whatsapp-float" — negative lookahead on "meydan-" so we only
    # strip the LLM copy and never our own injected button).
    html = re.sub(
        r'<a\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*(?<!meydan-)whatsapp-float)[^>]*>'
        r'[\s\S]*?</a>',
        "",
        html,
        flags=re.IGNORECASE,
    )
    # Defensive: any anchor with an href to wa.me AND position:fixed in its
    # inline style is a floating WhatsApp button regardless of class name.
    # Catches LLM variations ("whatsapp-btn", "chat-float", etc.) that slip
    # past the class-based pattern above. Skips our injected widgets because
    # the FAB icons are rendered with data-platform + the "meydan-social-icon"
    # class (no href to wa.me from a fixed-positioned anchor outside the FAB).
    html = re.sub(
        r'<a\b(?=[^>]*\bhref\s*=\s*["\']https?://(?:wa\.me|(?:api\.)?whatsapp\.com)[^"\']*["\'])'
        r'(?=[^>]*\bstyle\s*=\s*["\'][^"\']*position\s*:\s*fixed)'
        r'(?![^>]*\bclass\s*=\s*["\'][^"\']*meydan-)'
        r'[^>]*>[\s\S]*?</a>',
        "",
        html,
        flags=re.IGNORECASE,
    )
    return html


def _build_social_fab_html(icons: list[tuple[str, str, str, str, str]]) -> str:
    """Build the floating FAB widget from the unified icon list. Returns
    empty string if no icons — no point rendering an empty button.
    """
    if not icons:
        return ""

    icons_html = ""
    for i, (key, icon_cls, color, url, label) in enumerate(icons):
        right_offset = 4.5 + i * 3.5  # rem — first icon at right:4.5rem
        delay = 50 + i * 40  # ms — stagger the fan-out animation
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
            f'aria-label="{label}">'
            f'<i class="{icon_cls}"></i></a>'
        )

    return (
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


def _build_footer_social_inner(icons: list[tuple[str, str, str, str, str]]) -> str:
    """Build the anchor list that replaces the inner content of every
    ``<div class="social-links">`` found in the HTML. Kept sentinel-wrapped
    so subsequent injects can recognise and replace it cleanly.
    """
    if not icons:
        return ""
    parts = [FOOTER_SOCIAL_START]
    for key, icon_cls, _color, url, label in icons:
        parts.append(
            f'<a class="social-link" href="{url}" target="_blank" rel="noopener" '
            f'aria-label="{label}" data-platform="{key}">'
            f'<i class="{icon_cls}"></i></a>'
        )
    parts.append(FOOTER_SOCIAL_END)
    return "".join(parts)


def _inject_footer_social_row(html: str, icons: list[tuple[str, str, str, str, str]]) -> str:
    """Find every ``<div class="social-links">...</div>`` in ``html`` and
    replace its inner content with real anchors wired to user URLs.

    If no icons are configured, empty the container instead of removing
    it — the LLM-generated layout may depend on the div existing for
    spacing.

    The regex assumes the ``.social-links`` div contains only inline
    children (anchors, icons) — it does NOT handle nested ``<div>``. Our
    prompt enforces this shape, and the LLM has been consistent about
    honouring it.
    """
    if not html:
        return html

    inner = _build_footer_social_inner(icons)
    # Match the opening tag with "social-links" in its class (may have other
    # classes too), non-greedy body, closing </div>.
    pattern = re.compile(
        r'(<div\b[^>]*\bclass\s*=\s*["\'][^"\']*\bsocial-links\b[^"\']*["\'][^>]*>)'
        r'[\s\S]*?'
        r'(</div>)',
        flags=re.IGNORECASE,
    )
    return pattern.sub(lambda m: f"{m.group(1)}{inner}{m.group(2)}", html)


def inject_contact_widgets(html: str, contact_config: dict | None) -> str:
    """Inject the Social FAB + footer social row into ``html`` based on
    ``contact_config``. Idempotent — old sentinel blocks are stripped
    before insertion.

    ``contact_config`` shape::

        {
            "whatsapp": "971501234567",    # optional
            "mapLink": "https://...",        # optional
            "social": {                      # optional dict
                "facebook": "https://...",
                "instagram": "https://...",
                "tiktok": "https://...",
                "linkedin": "https://...",
                "youtube": "https://...",
            },
        }

    Passing an empty/None config removes any previously-injected widgets
    and clears the footer social row — useful for the "clear all" path
    in settings.
    """
    if not html:
        return html

    # Always strip first so the function is fully idempotent.
    html = _strip_existing_widgets(html)

    icons = _collect_icons(contact_config or {})

    # Replace footer <div class="social-links"> contents with the real
    # anchors (or empty it if no icons are configured).
    html = _inject_footer_social_row(html, icons)

    # Append the FAB before </body> so it floats over everything.
    fab_html = _build_social_fab_html(icons)
    if not fab_html:
        return html
    if "</body>" in html:
        return html.replace("</body>", f"{fab_html}</body>", 1)
    return html + fab_html
