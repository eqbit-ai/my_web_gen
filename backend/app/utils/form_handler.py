"""
Form handler injection for generated contact forms.

Detects <form> elements in generated HTML and injects a universal
form handler script that captures submissions via fetch API.
"""

import re

# ---------------------------------------------------------------------------
# Universal form handler JS
# ---------------------------------------------------------------------------

FORM_HANDLER_JS = """
// ── Universal Form Handler ──────────────────────────────────────────
(function() {
    document.querySelectorAll('form[data-form-handler]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var btn = form.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
            if (!btn) return;

            var originalText = btn.textContent || btn.value;
            if (btn.tagName === 'INPUT') {
                btn.value = 'Sending...';
            } else {
                btn.textContent = 'Sending...';
            }
            btn.disabled = true;

            var formData = new FormData(form);
            var data = {};
            formData.forEach(function(value, key) { data[key] = value; });

            var endpoint = form.getAttribute('data-form-handler') || form.action;
            if (!endpoint || endpoint === window.location.href) {
                // No endpoint configured — show success anyway (demo mode)
                form.reset();
                if (btn.tagName === 'INPUT') {
                    btn.value = 'Sent!';
                } else {
                    btn.textContent = 'Sent!';
                }
                setTimeout(function() {
                    if (btn.tagName === 'INPUT') {
                        btn.value = originalText;
                    } else {
                        btn.textContent = originalText;
                    }
                    btn.disabled = false;
                }, 3000);
                return;
            }

            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(function(res) {
                if (res.ok) {
                    form.reset();
                    if (btn.tagName === 'INPUT') {
                        btn.value = 'Sent!';
                    } else {
                        btn.textContent = 'Sent!';
                    }
                    setTimeout(function() {
                        if (btn.tagName === 'INPUT') {
                            btn.value = originalText;
                        } else {
                            btn.textContent = originalText;
                        }
                        btn.disabled = false;
                    }, 3000);
                } else {
                    throw new Error('Failed to send');
                }
            })
            .catch(function() {
                if (btn.tagName === 'INPUT') {
                    btn.value = 'Error - Try Again';
                } else {
                    btn.textContent = 'Error - Try Again';
                }
                btn.disabled = false;
                setTimeout(function() {
                    if (btn.tagName === 'INPUT') {
                        btn.value = originalText;
                    } else {
                        btn.textContent = originalText;
                    }
                }, 3000);
            });
        });
    });
})();
"""


# ---------------------------------------------------------------------------
# 1. has_contact_form
# ---------------------------------------------------------------------------


def has_contact_form(html: str) -> bool:
    """Check if the HTML contains a form element (contact, newsletter, etc.)."""
    return bool(re.search(r"<form\b", html, re.I))


# ---------------------------------------------------------------------------
# 2. inject_form_handler
# ---------------------------------------------------------------------------


def inject_form_handler(html: str, js: str) -> tuple[str, str]:
    """
    Add form handling to contact forms in generated HTML.

    - Detects <form> elements
    - Adds data-form-handler attribute if missing
    - Adds name attributes to inputs if missing
    - Appends FORM_HANDLER_JS to the JS output

    Returns (updated_html, updated_js).
    """
    if not has_contact_form(html):
        return html, js

    fixed_html = html

    # ── Add data-form-handler to forms without it ────────────────────
    def _add_form_handler_attr(m):
        tag = m.group(0)
        if "data-form-handler" in tag.lower():
            return tag

        # Use existing action as the handler endpoint, or empty string
        action_match = re.search(r'action\s*=\s*["\']([^"\']*)["\']', tag, re.I)
        if action_match:
            endpoint = action_match.group(1)
        else:
            endpoint = ""

        # Insert data-form-handler before the closing >
        return tag[:-1] + f' data-form-handler="{endpoint}">'

    fixed_html = re.sub(r"<form\b[^>]*>", _add_form_handler_attr, fixed_html, flags=re.I | re.S)

    # ── Add name attributes to inputs missing them ───────────────────
    def _add_input_names(m):
        tag = m.group(0)
        if re.search(r"\bname\s*=", tag, re.I):
            return tag

        # Derive name from type, placeholder, or id
        name = None

        type_match = re.search(r'type\s*=\s*["\'](\w+)["\']', tag, re.I)
        input_type = type_match.group(1).lower() if type_match else "text"

        # Skip submit/button/hidden — they don't need names for form data
        if input_type in ("submit", "button", "hidden"):
            return tag

        # Common placeholder → canonical name mapping
        _placeholder_to_name = {
            "your name": "name", "full name": "name", "name": "name",
            "first name": "first_name", "last name": "last_name",
            "your email": "email", "email address": "email", "email": "email",
            "your phone": "phone", "phone number": "phone", "phone": "phone",
            "your message": "message", "message": "message", "write your message": "message",
            "subject": "subject", "company": "company", "company name": "company",
        }

        # Try placeholder
        ph_match = re.search(r'placeholder\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if ph_match:
            ph_text = ph_match.group(1).lower().strip().rstrip(".*")
            name = _placeholder_to_name.get(ph_text)
            if not name:
                name = re.sub(r"[^a-zA-Z0-9]", "_", ph_text)
                name = re.sub(r"_+", "_", name).strip("_")[:30]

        # Try id
        if not name:
            id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', tag, re.I)
            if id_match:
                name = id_match.group(1)

        # Fallback to type
        if not name:
            type_to_name = {
                "email": "email",
                "tel": "phone",
                "text": "text_field",
                "number": "number_field",
                "url": "website",
            }
            name = type_to_name.get(input_type, input_type)

        return tag[:-1] + f' name="{name}">'

    fixed_html = re.sub(r"<input\b[^>]*>", _add_input_names, fixed_html, flags=re.I | re.S)

    # ── Add name to textarea if missing ──────────────────────────────
    def _add_textarea_name(m):
        tag = m.group(0)
        if re.search(r"\bname\s*=", tag, re.I):
            return tag

        # Try placeholder or id — normalize to "message" for common variants
        ph_match = re.search(r'placeholder\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if ph_match:
            ph_text = ph_match.group(1).lower().strip().rstrip(".*")
            if any(kw in ph_text for kw in ("message", "inquiry", "comment", "write", "tell us")):
                name = "message"
            else:
                name = re.sub(r"[^a-zA-Z0-9]", "_", ph_text)
                name = re.sub(r"_+", "_", name).strip("_")[:30] or "message"
        else:
            name = "message"

        return tag[:-1] + f' name="{name}">'

    # Match opening <textarea> tag only
    fixed_html = re.sub(
        r"<textarea\b[^>]*>",
        _add_textarea_name,
        fixed_html,
        flags=re.I | re.S,
    )

    # ── Append form handler JS ───────────────────────────────────────
    fixed_js = js
    if "data-form-handler" not in js:
        fixed_js = js + "\n\n" + FORM_HANDLER_JS

    return fixed_html, fixed_js
