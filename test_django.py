import sys
print(f"Python: {sys.version}")

try:
    import django
    print(f"Django version: {django.__version__}")
    
    from django.db.migrations import migration
    print("Migrations module imported successfully")
    
    from django.db.migrations.migration import Migration
    print("Migration class found")
    
except ImportError as e:
    print(f"Import error: {e}")
    
    # Try to find the file
    import os
    import django
    django_path = os.path.dirname(django.__file__)
    migration_file = os.path.join(django_path, 'db', 'migrations', 'migration.py')
    print(f"Looking for: {migration_file}")
    print(f"Exists: {os.path.exists(migration_file)}")
