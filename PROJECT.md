# template_flask_app

## What

Flask boilerplate/template app — the base template that Narcos was forked from. Reusable starting point for Flask + HTMX web apps with auth, user profiles, and friends system baked in.

## Stack

- **Backend:** Flask 3.x, SQLAlchemy, Flask-Security, Celery + Redis
- **Frontend:** HTMX, TailwindCSS v4, DaisyUI — server-side rendering
- **DB:** PostgreSQL (via SQLAlchemy + Alembic)
- **Auth:** Flask-Security with WebAuthn/passkeys

## Structure

```text
app/
├── api/            # REST API endpoints
├── public/         # Public routes
├── extensions/     # Flask extensions (security, admin, celery)
├── templates/      # Jinja2 (security views, user profiles, settings, theme toggle)
├── static/         # CSS (Tailwind), favicons
├── models.py       # User, WebAuthn models
config.py           # Dev/Test/Prod configs
migrations/         # Alembic (initial + webauthn)
```

## Purpose

Start new Flask projects from this. Clone it, rename, and build features on top. Narcos is an example of a project built from this template.

## Dev Commands

```bash
npm install && poetry install
cp .env.example .env
flask db upgrade
flask run
npm run dev         # Tailwind watch
```

## Template Structure

Every page template follows a dual-render pattern using Jinja2 macros. This allows the same template to serve both full page loads (direct URL visit) and partial HTMX responses (in-app navigation).

### Page Template Pattern

Each page defines two macros and a conditional block:

```jinja2
{% macro top_bar() %}
    {# Page-specific header: back links, action buttons, etc. #}
{% endmacro %}

{% macro content() %}
    {# Main page content #}
{% endmacro %}

{% if htmx.boosted -%}
    <title>{{ title }}</title>
    <div id="top-bar" hx-swap-oob="innerHTML">
        {{ top_bar() }}
    </div>
    {{ content() }}
{% else %}
    {% extends 'base.html' %}
    {% block top_bar %}
        {{ top_bar() }}
    {% endblock %}
    {% block content %}
        {{ content() }}
    {% endblock %}
{% endif %}
```

- **`htmx.boosted` is true** (HTMX navigation): Returns only the title, the top bar as an out-of-band swap, and the content — no base layout wrapping.
- **`htmx.boosted` is false** (direct page load): Extends `base.html` and fills the `top_bar` and `content` blocks so the full page with nav renders.

### Navigation Links

All internal links must use these three HTMX attributes:

```html
<a
    href="{{ url_for('blueprint.view') }}"
    hx-boost="true"
    hx-swap="show:window:top"
    hx-target="#content">
    Link Text
</a>
```

- `hx-boost="true"` — Turns the link into an AJAX request, preserves browser history.
- `hx-target="#content"` — Swaps the response into the `#content` div defined in `base.html`.
- `hx-swap="show:window:top"` — Scrolls the window to the top after swap.

### Base Templates

- **`base_base.html`** — Root HTML skeleton (head, scripts, HTMX config).
- **`base.html`** — App layout extending `base_base.html`. Defines `#top-bar` and `#content` divs, includes desktop nav (`_top_nav.html`) and mobile nav (`_bottom_nav.html`).

### Reference

See `users/profile.html` for a complete example with both macros, and `first/index.html` for a simpler page.
