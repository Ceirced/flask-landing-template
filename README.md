# Flask Landing Page Template

A minimal, production-ready Flask template for **lead generation landing pages** with a multi-step HTMX funnel, UTM tracking, A/B variant testing, and an admin dashboard.

Built on top of [flask-app](https://github.com/Ceirced/flask-app) — stripped of auth, focused on conversion.

## Features

- **HTMX multi-step funnel** — 3 configurable question steps → contact capture → thank you, all without page reloads
- **Lead model** — stores email, phone, funnel answers, UTM params, A/B variant, IP address
- **UTM tracking** — auto-captures `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` from URL and persists them through the funnel
- **A/B variant routing** — serve different headlines/CTAs via `AB_VARIANT=a|b` env var; tracked per lead + PostHog
- **Admin lead dashboard** — Flask-Admin at `/admin` with search, filters by source/campaign/variant, and CSV export
- **Async confirmation email** — sends via Celery + Redis using flask-mailman
- **Production-ready** — Docker, nginx, gunicorn, PostgreSQL, TailwindCSS v4 + DaisyUI

## Stack

- Python / Flask
- HTMX + Alpine.js
- TailwindCSS v4 + DaisyUI
- PostgreSQL + SQLAlchemy + Flask-Migrate
- Celery + Redis (email queue)
- Flask-Admin (lead dashboard)
- PostHog (analytics)
- Docker + nginx

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Ceirced/flask-landing-template.git my-campaign
cd my-campaign
uv sync
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
APP_SETTINGS=config.ProductionConfig
SECRET_KEY=your-secret-key
APP_NAME=Your Campaign Name

# Database
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/dbname

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Mail
MAIL_SERVER=smtp.your-provider.com
MAIL_PORT=587
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Campaign
LEAD_EMAIL_SUBJECT=Thanks for your interest!
AB_VARIANT=a          # "a" or "b" — controls landing page headline variant
POSTHOG_API_KEY=      # optional
```

### 3. Run migrations

```bash
flask --app flask_app db upgrade
```

### 4. Start

**Development:**
```bash
flask --app flask_app run --debug
```

**Production (Docker):**
```bash
docker compose up -d
```

### 5. Build CSS

```bash
npm install
npm run build  # or: npm run dev (watch mode)
```

## Customization

### Funnel questions

Edit `app/templates/public/funnel/step_1.html`, `step_2.html`, `step_3.html`.

Each step is a plain HTML partial loaded via HTMX — just change the question text and radio options. The step number, progress bar, and HTMX routing are already wired up.

### Landing page copy

Edit `app/templates/public/index.html`.

Variant A and B headlines are in the `{% if variant == "a" %}` block. Switch variants via `AB_VARIANT` env var.

### Confirmation email

Edit `app/templates/emails/lead_confirmation.html`. The funnel answers are available as `{{ funnel_data }}`.

### Email subject

Set `LEAD_EMAIL_SUBJECT` in your environment or update the default in `config.py`.

## Admin Dashboard

Available at `/admin` — shows all leads with:
- Filter by UTM source, campaign, A/B variant, funnel step reached
- Search by email
- Bulk CSV export (select leads → Actions → Export CSV)

> **Note:** The admin is open by default. Add auth before going to production (Flask-BasicAuth or Flask-Login).

## A/B Testing

Set `AB_VARIANT=a` or `AB_VARIANT=b` on your server. The variant is stored with each lead, so you can compare conversion rates between variants in the admin or your analytics tool.

Use PostHog to track events and measure variant performance — the PostHog snippet is already included in `base_base.html`.

## UTM Tracking

Any UTM params passed in the URL (`?utm_source=instagram&utm_campaign=spring`) are:
1. Stored in the user's session on first visit
2. Persisted through all funnel steps
3. Saved to the `Lead` record on submission

This lets you attribute leads back to specific ads or channels.

## Project Structure

```
app/
├── models.py              # Lead model
├── tasks.py               # Celery task: send confirmation email
├── admin_views.py         # Flask-Admin: LeadAdmin with CSV export
├── public/
│   └── routes.py          # Landing page + funnel routes
├── templates/
│   ├── public/
│   │   ├── index.html     # Landing page (A/B variants)
│   │   └── funnel/
│   │       ├── step_1.html     # Question 1
│   │       ├── step_2.html     # Question 2
│   │       ├── step_3.html     # Question 3
│   │       ├── step_contact.html  # Email + phone capture
│   │       └── thank_you.html     # Success screen
│   └── emails/
│       └── lead_confirmation.html  # Confirmation email
└── extensions/
    └── celery.py          # Celery factory
```
