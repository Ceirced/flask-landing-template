import csv
import io

from flask import Response
from flask_admin import Admin
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView

from app.extensions import db
from app.models import Lead


class LeadAdmin(ModelView):
    """Admin view for lead management with CSV export."""

    column_list = [
        "email", "phone", "utm_source", "utm_medium",
        "utm_campaign", "ab_variant", "funnel_step_reached", "created_at",
    ]
    column_searchable_list = ["email", "utm_campaign", "utm_source"]
    column_filters = ["utm_source", "utm_medium", "utm_campaign", "ab_variant", "funnel_step_reached"]
    column_default_sort = ("created_at", True)
    can_create = False
    can_edit = False
    page_size = 50

    @action("export_csv", "Export CSV", "Export selected leads to CSV?")
    def export_csv(self, ids):
        leads = Lead.query.filter(Lead.id.in_(ids)).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "email", "phone", "utm_source", "utm_medium",
            "utm_campaign", "utm_content", "ab_variant",
            "funnel_step_reached", "ip_address", "created_at",
        ])
        for lead in leads:
            writer.writerow([
                lead.email, lead.phone,
                lead.utm_source, lead.utm_medium, lead.utm_campaign, lead.utm_content,
                lead.ab_variant, lead.funnel_step_reached, lead.ip_address, lead.created_at,
            ])
        output.seek(0)
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=leads.csv"},
        )


def init_admin(app):
    admin = Admin(app, name="Lead Dashboard")
    admin.add_view(LeadAdmin(Lead, db.session))
