import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.apps import apps
from django.utils import timezone
from django.db import transaction
from faker import Faker

class Command(BaseCommand):
    help = 'Populates the database with smart dummy data for the Dashboard'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting Data Population...'))
        fake = Faker()
        
        # --- 1. LOAD MODELS DYNAMICALLY (Safe & Robust) ---
        try:
            Company = apps.get_model('company', 'Company')
            Employee = apps.get_model('employee', 'Employee')
            Country = apps.get_model('country', 'Country')
            # Assuming typical structure based on your shell output
            Payroll = apps.get_model('payroll', 'Payroll') 
            PayrollPeriod = apps.get_model('payroll', 'PayrollPeriod')
            PayrollResult = apps.get_model('payroll', 'PayrollResult')
        except LookupError as e:
            self.stdout.write(self.style.ERROR(f'Model lookup failed: {e}'))
            return

        with transaction.atomic():
            # --- 2. CREATE COUNTRIES (For the Map) ---
            countries = ['United Kingdom', 'United States', 'France', 'Germany', 'Spain', 'Ireland']
            country_objs = []
            for name in countries:
                c, created = Country.objects.get_or_create(name=name, defaults={'code': name[:2].upper()})
                country_objs.append(c)
            self.stdout.write(self.style.SUCCESS(f'Verified {len(country_objs)} Countries.'))

            # --- 3. CREATE COMPANIES ---
            companies = []
            for i in range(5):
                comp, created = Company.objects.get_or_create(
                    trade_name=fake.company(),
                    defaults={
                        'country': random.choice(country_objs),
                        'account_status': 'ACTIVE'
                    }
                )
                companies.append(comp)
            self.stdout.write(self.style.SUCCESS(f'Verified {len(companies)} Companies.'))

            # --- 4. CREATE EMPLOYEES (For Demographics Chart) ---
            employees = []
            genders = ['Male', 'Female']
            for comp in companies:
                # Create 10-20 employees per company
                for _ in range(random.randint(10, 20)):
                    emp = Employee.objects.create(
                        company=comp,
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        email=fake.email(),
                        gender=random.choice(genders), # Critical for Pie Chart
                        employment_start_date=timezone.now() - timedelta(days=random.randint(100, 1000))
                    )
                    employees.append(emp)
            self.stdout.write(self.style.SUCCESS(f'Created {len(employees)} Employees with Gender data.'))

            # --- 5. CREATE PAYROLL HISTORY (For Trend Chart) ---
            # We need 6 months of history + 1 future open period
            
            for comp in companies:
                # Create a Payroll Definition if needed
                payroll_def, _ = Payroll.objects.get_or_create(
                    company=comp, 
                    defaults={'name': 'Monthly Salaried', 'frequency': 'MONTHLY'}
                )

                # Generate last 6 months
                today = timezone.now()
                for i in range(6):
                    month_date = today - timedelta(days=30 * (5-i)) # Go back 5 months to now
                    
                    period = PayrollPeriod.objects.create(
                        payroll=payroll_def,
                        name=f"{month_date.strftime('%B %Y')}",
                        payment_date=month_date,
                        status='CLOSED',
                        total_gross=0,
                        total_net=0
                    )

                    # Create Payslips (Results) for this period
                    period_gross = 0
                    period_net = 0
                    
                    # Process payroll for all employees in this company
                    company_employees = Employee.objects.filter(company=comp)
                    for emp in company_employees:
                        gross = random.randint(3000, 8000)
                        net = gross * 0.75 # Approx tax calculation
                        
                        PayrollResult.objects.create(
                            period=period,
                            employee=emp,
                            gross_pay=gross,
                            net_pay=net
                        )
                        period_gross += gross
                        period_net += net
                    
                    # Update Period Totals (Critical for Bar Chart)
                    period.total_gross = period_gross
                    period.total_net = period_net
                    period.save()

                # --- 6. CREATE PENDING ACTION (For "Pending Approvals" List) ---
                # Create next month's open payroll
                next_month = today + timedelta(days=30)
                PayrollPeriod.objects.create(
                    payroll=payroll_def,
                    name=f"{next_month.strftime('%B %Y')}",
                    payment_date=next_month,
                    status='OPEN', # This will show up in the "Pending" list
                    total_gross=0,
                    total_net=0
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with smart dashboard data!'))