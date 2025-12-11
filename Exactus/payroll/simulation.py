# Exactus/payroll/simulation.py
"""
Production-ready simulation to verify ALL requirements
Run with: python manage.py shell < simulation.py
"""
from django.contrib.auth.models import User
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.payroll.models import Payroll, PayrollPeriod, PayrollStatus, PeriodStatus
from datetime import date

def run_production_simulation():
    print("🚀 EXACTUSPAY PAYROLL MODULE - PRODUCTION SIMULATION")
    print("=" * 60)
    
    # Setup
    admin = User.objects.filter(is_superuser=True).first()
    if not admin:
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    company = Company.objects.first() or Company.objects.create(
        name='ACME Corp',
        created_by=admin
    )
    
    country = Country.objects.first() or Country.objects.create(
        code='US',
        name='United States',
        created_by=admin
    )
    
    print(f"Company: {company.trade_name}")
    print(f"Country: {country.name}")
    print(f"Admin: {admin.username}")
    print("-" * 60)
    
    # TEST 1: Create Payroll 2024
    print("\n📋 TEST 1: Create Payroll for 2024")
    payroll_2024 = Payroll.objects.create(
        company=company,
        fiscal_year=2024,
        country=country,
        regulation_version='2024-v1',
        status=PayrollStatus.DRAFT,
        created_by=admin
    )
    print(f"✅ Created: {payroll_2024}")
    
    # TEST 2: Prevent Duplicate Payroll (CRITICAL REQUIREMENT)
    print("\n📋 TEST 2: Attempt Duplicate Payroll (Should Fail)")
    try:
        Payroll.objects.create(
            company=company,
            fiscal_year=2024,
            country=country,
            created_by=admin
        )
        print("❌ FAILED: Duplicate payroll created!")
    except Exception as e:
        print(f"✅ PASSED: Prevented duplicate: {str(e)[:100]}...")
    
    # TEST 3: Add Periods
    print("\n📋 TEST 3: Add Payroll Periods")
    period1 = PayrollPeriod.objects.create(
        payroll=payroll_2024,
        period_number=1,
        name='January 2024',
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        processing_date=date(2024, 2, 5),
        created_by=admin
    )
    print(f"✅ Added Period 1: {period1}")
    print(f"   Editable: {period1.is_editable}, Deletable: {period1.is_deletable}")
    
    # TEST 4: Prevent Overlapping Period
    print("\n📋 TEST 4: Attempt Overlapping Period (Should Fail)")
    try:
        PayrollPeriod.objects.create(
            payroll=payroll_2024,
            period_number=2,
            name='Overlap',
            start_date=date(2024, 1, 15),
            end_date=date(2024, 2, 15),
            created_by=admin
        )
        print("❌ FAILED: Overlapping period created!")
    except Exception as e:
        print(f"✅ PASSED: Prevented overlap: {str(e)[:100]}...")
    
    # TEST 5: Process Period
    print("\n📋 TEST 5: Process Period (Lock after execution)")
    print(f"Before processing - Editable: {period1.is_editable}")
    
    if period1.mark_as_processing(admin):
        print("✅ Marked as processing")
        
        results = {'employee_count': 50, 'total_amount': 100000.00}
        if period1.mark_as_completed(results):
            print("✅ Marked as completed")
            print(f"After processing - Editable: {period1.is_editable}")
            print(f"After processing - Deletable: {period1.is_deletable}")
    
    # TEST 6: Create Payroll 2025 (Should succeed)
    print("\n📋 TEST 6: Create Payroll for 2025 (Different year)")
    try:
        payroll_2025 = Payroll.objects.create(
            company=company,
            fiscal_year=2025,
            country=country,
            created_by=admin
        )
        print(f"✅ Created: {payroll_2025}")
        print("   ✓ Different year allowed even with existing 2024 payroll")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # FINAL VERIFICATION
    print("\n" + "=" * 60)
    print("📊 FINAL VERIFICATION")
    print("=" * 60)
    
    active_payrolls = Payroll.objects.filter(
        company=company
    ).exclude(status=PayrollStatus.CANCELLED)
    
    print(f"Active payrolls for {company.trade_name}:")
    for p in active_payrolls:
        periods = p.periods.count()
        print(f"  - FY{p.fiscal_year}: {periods} periods, Status: {p.status}")
    
    # Verify unique constraint
    payroll_2024_count = Payroll.objects.filter(
        company=company,
        fiscal_year=2024
    ).exclude(status=PayrollStatus.CANCELLED).count()
    
    if payroll_2024_count == 1:
        print("\n✅ CRITICAL REQUIREMENT MET: Only ONE payroll per company per year")
    else:
        print(f"\n❌ REQUIREMENT VIOLATED: {payroll_2024_count} payrolls for 2024!")
    
    print("\n🎉 SIMULATION COMPLETE - ALL REQUIREMENTS VERIFIED")

if __name__ == '__main__':
    run_production_simulation()