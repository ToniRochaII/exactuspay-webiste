# Exactus/reports/engine.py
from django.template import Template, Context
from .models import ReportConfiguration


class ReportEngine:
    """
    Resolves which report configuration/layout to use
    (Company > Country > System) and renders the selected HTML template.
    """

    @staticmethod
    def get_configuration(report_type_code, company=None, country=None):
        # 1) Company
        if company:
            config = ReportConfiguration.objects.filter(
                report_type__code=report_type_code,
                company=company
            ).first()
            if config:
                return config

        # 2) Country
        target_country = country
        if not target_country and company and hasattr(company, "country_id"):
            target_country = company.country

        if target_country:
            config = ReportConfiguration.objects.filter(
                report_type__code=report_type_code,
                country=target_country,
                company__isnull=True
            ).first()
            if config:
                return config

        # 3) System default
        return ReportConfiguration.objects.filter(
            report_type__code=report_type_code,
            country__isnull=True,
            company__isnull=True
        ).first()

    @staticmethod
    def render_report(config, context_data):
        if not config or not config.selected_layout:
            return "Error: No layout configured for this report type."

        try:
            with config.selected_layout.template_file.open("r") as f:
                template_content = f.read()
                if isinstance(template_content, bytes):
                    template_content = template_content.decode("utf-8")

            django_template = Template(template_content)

            full_context = dict(context_data or {})
            full_context["settings"] = getattr(config, "data_settings", {}) or {}

            return django_template.render(Context(full_context))

        except Exception as e:
            return f"Error rendering report: {str(e)}"
