# elements/views.py
import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Element
from country.models import Country
from .forms import ElementForm, ElementUploadForm
from .utils.csv_importer import import_elements_from_csv

@login_required
def element(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    elements = Element.objects.filter(country=country)
    return render(request, 'elements/index.html', {
        'elements': elements,
        'country': country
    })

@login_required
def element_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    if request.method == 'POST':
        form = ElementForm(request.POST)
        if form.is_valid():
            element = form.save(commit=False)
            element.country = country
            element.save()
            messages.success(request, 'Element created successfully!')
            return redirect('elements:elements', country_slug=country_slug)
    else:
        form = ElementForm()
    return render(request, 'elements/create.html', {
        'form': form,
        'country': country
    })

@login_required
def element_edit(request, country_slug, element_code):
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, country=country, element_code=element_code)
    if request.method == 'POST':
        form = ElementForm(request.POST, instance=element)
        if form.is_valid():
            form.save()
            messages.success(request, 'Element updated successfully!')
            return redirect('elements:elements', country_slug=country_slug)
    else:
        form = ElementForm(instance=element)
    return render(request, 'elements/edit.html', {
        'form': form,
        'element': element,
        'country': country
    })

@login_required
def element_delete(request, country_slug, element_code):
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, country=country, element_code=element_code)
    if request.method == 'POST':
        element.delete()
        messages.success(request, 'Element deleted successfully!')
        return redirect('elements:elements', country_slug=country_slug)
    return render(request, 'elements/delete.html', {
        'element': element,
        'country': country
    })

@login_required
def element_upload_view(request, country_slug=None):
    """Handle element CSV uploads with country context"""
    
    # Determine if this is a country-specific or global upload
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    if request.method == 'POST':
        form = ElementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Read the CSV file
            try:
                # Try to decode the file as UTF-8
                data_set = csv_file.read().decode('UTF-8')
            except UnicodeDecodeError:
                # If UTF-8 fails, try ISO-8859-1
                csv_file.seek(0)  # Reset file pointer
                data_set = csv_file.read().decode('ISO-8859-1')
            
            io_string = io.StringIO(data_set)
            
            # Import elements from CSV
            success_count, error_count, errors = import_elements_from_csv(io_string, country)
            
            # Store results in session for the result page
            request.session['upload_results'] = {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors,
                'country_slug': country_slug
            }
            
            # Redirect to results page with proper country_slug
            if country_slug:
                return redirect(reverse('elements:elements_upload_result', kwargs={'country_slug': country_slug}))
            else:
                return redirect(reverse('elements:elements_upload_result_global'))
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        form = ElementUploadForm()
    
    return render(request, 'elements/upload_form.html', {
        'form': form,
        'country': country
    })

@login_required
def element_upload_result_view(request, country_slug=None):
    """Display results of CSV upload"""
    
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    # Get results from session
    upload_results = request.session.pop('upload_results', None)
    
    if not upload_results:
        messages.warning(request, 'No upload results found. Please upload a file first.')
        if country_slug:
            return redirect(reverse('elements:elements_upload', kwargs={'country_slug': country_slug}))
        else:
            return redirect(reverse('elements:elements_upload_global'))
    
    return render(request, 'elements/upload_result.html', {
        'success_count': upload_results.get('success_count', 0),
        'error_count': upload_results.get('error_count', 0),
        'errors': upload_results.get('errors', []),
        'country': country,
        'country_slug': upload_results.get('country_slug')
    })

@login_required
def download_elements_template(request, country_slug=None):
    """Download CSV template for elements"""
    
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    
    if country:
        filename = f'elements_template_{country.iso2_code}.csv'
    else:
        filename = 'elements_template.csv'
        
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'country_code', 'element_code', 'element_name', 'element_description',
        'element_status', 'element_account', 'element_map_code', 'element_gl_account',
        'element_frequency', 'element_type', 'element_class', 'element_category',
        'element_taxable', 'element_tax_flat', 'element_tax_irregular',
        'element_social_securitable', 'element_pensionable', 'element_payable',
        'element_calculate', 'element_categorytype', 'archive'
    ])
    
    # Add example rows based on country if provided
    if country:
        writer.writerow([
            country.iso2_code, '6000', 'Income Tax', 'Income Tax Description',
            'Visible', '6000', '6000', '6000', 'Recurring', 'Regular',
            'statutory', 'Deduction', 'FALSE', 'FALSE', 'FALSE', 'FALSE',
            'FALSE', 'TRUE', 'TRUE', 'Bracketable', 'N'
        ])
    
    return response