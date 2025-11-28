# Exactus/context_processors.py
def sidebar_context(request):
    context = {}
    
    # Extract country_slug from URL
    if hasattr(request, 'resolver_match') and request.resolver_match:
        kwargs = request.resolver_match.kwargs
        context['country_slug'] = kwargs.get('country_slug')
        context['company_id'] = kwargs.get('company_id')
        context['regulations_id'] = kwargs.get('regulations_id')
        context['element_code'] = kwargs.get('element_code')
        
        # You can fetch objects here if needed
        # from Exactus.country.models import Country
        # if context['country_slug']:
        #     context['country'] = Country.objects.filter(slug=context['country_slug']).first()
    
    return context