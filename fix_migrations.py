#!/usr/bin/env python
"""
Script to fix migration issues on Render
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExactusPay.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

def fix_company_migrations():
    """Fix company migration issues."""
    print("Fixing company migrations...")
    
    with connection.cursor() as cursor:
        # 1. Add county column if it doesn't exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'company_company' AND column_name = 'county'
        """)
        if not cursor.fetchone():
            print("Adding county column...")
            cursor.execute("ALTER TABLE company_company ADD COLUMN county VARCHAR(100)")
        
        # 2. Check and mark migrations as applied
        cursor.execute("SELECT * FROM django_migrations WHERE app = 'company'")
        existing = cursor.fetchall()
        
        if not any('0001_initial' in str(row) for row in existing):
            print("Marking company.0001_initial as applied...")
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('company', '0001_initial', NOW())
                ON CONFLICT DO NOTHING
            """)
        
        if not any('0002_company_county' in str(row) for row in existing):
            print("Marking company.0002_company_county as applied...")
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('company', '0002_company_county', NOW())
                ON CONFLICT DO NOTHING
            """)
    
    print("Company migrations fixed!")

def fix_payroll_migrations():
    """Fix payroll migration timestamp issues."""
    print("Checking payroll migrations...")
    
    with connection.cursor() as cursor:
        # Check if payroll table exists and has created_at
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'payroll_payroll' AND column_name = 'created_at'
        """)
        
        if not cursor.fetchone():
            print("Payroll table doesn't have created_at column yet.")
    
    print("Payroll check complete.")

if __name__ == '__main__':
    fix_company_migrations()
    fix_payroll_migrations()
    print("Migration fixes applied successfully!")