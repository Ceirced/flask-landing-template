import os

from flask import render_template, request, session

from app.extensions import db
from app.models import Lead
from app.public import bp
from app.tasks import send_lead_confirmation_email


def _store_utm(req):
    """Persist UTM params in session on first visit so they survive funnel steps."""
    for param in ["utm_source", "utm_medium", "utm_campaign", "utm_content"]:
        if req.args.get(param):
            session[param] = req.args.get(param)


def _get_utm():
    """Read UTM params — prefer query string, fall back to session."""
    return {
        "utm_source": request.args.get("utm_source") or session.get("utm_source"),
        "utm_medium": request.args.get("utm_medium") or session.get("utm_medium"),
        "utm_campaign": request.args.get("utm_campaign") or session.get("utm_campaign"),
        "utm_content": request.args.get("utm_content") or session.get("utm_content"),
    }


@bp.route("/")
def index():
    _store_utm(request)
    variant = os.getenv("AB_VARIANT", "a")
    return render_template("public/index.html", variant=variant)


@bp.route("/funnel/step/<int:step>", methods=["GET", "POST"])
def funnel_step(step):
    """HTMX-powered multi-step funnel. Steps 1–3 are questions; after step 3 the contact form is shown."""
    if step < 1 or step > 3:
        return render_template("errors/404.html"), 404

    if request.method == "POST":
        data = session.get("funnel_data", {})
        data[f"step_{step}"] = request.form.to_dict()
        session["funnel_data"] = data
        session["funnel_step_reached"] = max(session.get("funnel_step_reached", 1), step + 1)

        if step < 3:
            return render_template(f"public/funnel/step_{step + 1}.html", step=step + 1)
        # After last question → show contact capture
        return render_template("public/funnel/step_contact.html")

    return render_template(f"public/funnel/step_{step}.html", step=step)


@bp.route("/funnel/submit", methods=["POST"])
def funnel_submit():
    """Save the lead to the DB and queue confirmation email."""
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not email:
        return render_template("public/funnel/step_contact.html", error="Email is required.")

    utm = _get_utm()
    lead = Lead(
        email=email,
        phone=phone or None,
        funnel_data=session.get("funnel_data", {}),
        utm_source=utm["utm_source"],
        utm_medium=utm["utm_medium"],
        utm_campaign=utm["utm_campaign"],
        utm_content=utm["utm_content"],
        ab_variant=os.getenv("AB_VARIANT", "a"),
        ip_address=request.remote_addr,
        funnel_step_reached=session.get("funnel_step_reached", 4),
    )
    db.session.add(lead)
    db.session.commit()

    send_lead_confirmation_email.delay(email, lead.funnel_data)

    session.pop("funnel_data", None)
    session.pop("funnel_step_reached", None)

    return render_template("public/funnel/thank_you.html")
