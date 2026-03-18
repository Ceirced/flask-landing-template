from celery import shared_task
from flask import render_template, current_app
from flask_mailman import EmailMultiAlternatives

from app.extensions import mail


@shared_task
def send_lead_confirmation_email(email: str, funnel_data: dict):
    """Send a confirmation email to a new lead after funnel completion."""
    subject = current_app.config.get("LEAD_EMAIL_SUBJECT", "Thanks for your interest!")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER")
    html = render_template("emails/lead_confirmation.html", funnel_data=funnel_data)

    with mail.get_connection() as connection:
        msg = EmailMultiAlternatives(
            subject=subject,
            body="Thanks for your interest! Please view this email in HTML.",
            from_email=sender,
            to=[email],
            connection=connection,
        )
        msg.attach_alternative(html, "text/html")
        msg.send()
