#!/usr/bin/env python
"""
COMPLETE COUNTRY APP SETUP - Fixes settings and sets up everything
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_health_module():
    """Create the health module"""
    print("🏥 Setting up health module...")
    
    health_dir = 'country/health'
    if not os.path.exists(health_dir):
        os.makedirs(health_dir, exist_ok=True)
    
    # Create __init__.py
    with open(f'{health_dir}/__init__.py', 'w') as f:
        f.write('# Health module\n')
    
    # Create urls.py
    with open(f'{health_dir}/urls.py', 'w') as f:
        f.write('''from django.urls import path
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "country"})

urlpatterns = [
    path('', health_check),
]
''')
    print("✅ Health module created")

def fix_urls():
    """Fix the URLs to handle health check"""
    print("🔗 Fixing URLs...")
    
    urls_path = 'ExactusPay/urls.py'
    if os.path.exists(urls_path):
        with open(urls_path, 'r') as f:
            content = f.read()
        
        # Add health URL if not present
        if "path('healthz/', include('country.health.urls'))," not in content:
            # Find where to insert it (after other includes)
            if "path('api/geo/', include('country.api.routers'))," in content:
                content = content.replace(
                    "path('api/geo/', include('country.api.routers')),",
                    "path('api/geo/', include('country.api.routers')),\n    path('healthz/', include('country.health.urls')),"
                )
                print("✅ Added health URL")
        
        with open(urls_path, 'w') as f:
            f.write(content)

def setup_country_app():
    """Setup the country app with migrations and data"""
    print("🚀 Setting up Country App...")
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExactusPay.settings')
    
    try:
        django.setup()
        print("✅ Django setup successful")
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False
    
    commands = [
        ['manage.py', 'check'],
        ['manage.py', 'makemigrations', 'country'],
        ['manage.py', 'migrate'],
        ['manage.py', 'load_country_seed'],
    ]
    
    for cmd in commands:
        print(f"🔄 Running: {' '.join(cmd)}")
        try:
            execute_from_command_line(cmd)
            print(f"✅ {' '.join(cmd)} completed")
        except Exception as e:
            print(f"❌ {' '.join(cmd)} failed: {e}")
            return False
    
    return True

def test_country_app():
    """Test that the country app is working"""
    print("🧪 Testing Country App...")
    
    try:
        from country.models import Currency, Country
        
        currency_count = Currency.objects.count()
        country_count = Country.objects.count()
        
        print(f"✅ Found {currency_count} currencies and {country_count} countries")
        
        # Test creating a record
        if currency_count == 0:
            currency = Currency.objects.create(
                code='TEST',
                name='Test Currency',
                numeric_code='999'
            )
            country = Country.objects.create(
                name='Test Country',
                alpha2='TC',
                alpha3='TCO',
                numeric='001',
                currency=currency,
                primary_time_zone='UTC'
            )
            print(f"✅ Created test data: {currency.code}, {country.alpha2}")
        
        print("🎉 Country app is working!")
        return True
        
    except Exception as e:
        print(f"❌ Country app test failed: {e}")
        return False

def main():
    print("🎯 COMPLETE COUNTRY APP SETUP")
    print("=" * 50)
    
    # Step 1: Setup health module
    setup_health_module()
    
    # Step 2: Fix URLs
    fix_urls()
    
    # Step 3: Setup country app
    if setup_country_app():
        print("\n✅ Country app setup completed!")
    else:
        print("\n⚠️ Country app setup had issues")
    
    # Step 4: Test the app
    test_country_app()
    
    print("\n🎉 SETUP COMPLETED!")
    print("\nNext steps:")
    print("1. Create superuser: python manage.py createsuperuser")
    print("2. Run tests: python manage.py test country.tests")
    print("3. Check health: python manage.py update_country_metrics --health-check")

if __name__ == '__main__':
    main()