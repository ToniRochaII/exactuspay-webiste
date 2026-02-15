from django.template import Template, Context
from django.apps import apps
from .models import ReportConfiguration, ReportLayout

class ReportEngine:
    """
    Handles the logic of resolving which report layout to use
    based on the hierarchy: Company > Country > System.
    """

    @staticmethod
    def get_configuration(report_type_code, company=None, country=None):
        """
        Walks up the chain to find the most specific configuration.
        """
        # 1. Try Company Level
        if company:
            config = ReportConfiguration.objects.filter(
                report_type__code=report_type_code,
                company=company
            ).first()
            if config:
                return config

        # 2. Try Country Level (If company didn't match or wasn't provided)
        # If we have a company, we infer the country from it if not explicitly passed
        target_country = country
        if not target_country and company:
            # Assuming Company model has a 'country' FK
            target_country = company.country 
        
        if target_country:
            config = ReportConfiguration.objects.filter(
                report_type__code=report_type_code,
                country=target_country,
                company__isnull=True
            ).first()
            if config:
                return config

        # 3. Fallback to System Default
        config = ReportConfiguration.objects.filter(
            report_type__code=report_type_code,
            country__isnull=True,
            company__isnull=True
        ).first()
        
        return config

    @staticmethod
    def render_report(config, context_data):
        """
        Loads the uploaded HTML file and renders it with Django context.
        """
        if not config or not config.selected_layout:
             return "Error: No layout configured for this report type."

        # Read the file content from storage
        try:
            # Open the uploaded file
            with config.selected_layout.template_file.open('r') as f:
                template_content = f.read()
                # If bytes, decode to string
                if isinstance(template_content, bytes):
                    template_content = template_content.decode('utf-8')
            
            # Create a Django Template object
            django_template = Template(template_content)
            
            # Merge context with Settings Toggles
            # This allows the HTML to use {% if settings.show_logo %}
            full_context = context_data.copy()
            full_context['settings'] = config.data_settings
            
            # Render
            return django_template.render(Context(full_context))

        except Exception as e:
            return f"Error rendering report: {str(e)}"