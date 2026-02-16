# create a management command: manage.py migrate_calculation_bases.py

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migrate CalculationBase data from old system to new'
    
    def handle(self, *args, **options):
        from old_app.models import CalculationBase as OldCalculationBase
        from Exactus.regulations.models import CalculationBase, Regulations, Element
        
        migrated_count = 0
        
        with transaction.atomic():
            for old_base in OldCalculationBase.objects.all():
                try:
                    # Find corresponding regulation
                    regulation = Regulations.objects.filter(
                        country=old_base.country,
                        fiscal_year=old_base.regulations.fiscal_year
                    ).first()
                    
                    if not regulation:
                        self.stdout.write(f"Warning: No regulation found for {old_base}")
                        continue
                    
                    # Find corresponding element
                    element = Element.objects.filter(
                        country=old_base.country,
                        element_code=old_base.element.element_code
                    ).first()
                    
                    if not element:
                        self.stdout.write(f"Warning: No element found for {old_base.element.element_code}")
                        continue
                    
                    # Create new CalculationBase
                    new_base = CalculationBase.objects.create(
                        country=old_base.country,
                        regulations=regulation,
                        element=element,
                        tax_jurisdiction=old_base.tax_jurisdiction,
                        table_type=old_base.table_type,
                        ss_category=old_base.ss_category,
                        base_frequency=old_base.base_frequency,
                        # Copy all bracket fields
                        bracket_00=Decimal(str(old_base.bracket_00)) if old_base.bracket_00 else Decimal('0'),
                        bracket_01=Decimal(str(old_base.bracket_01)) if old_base.bracket_01 else Decimal('0'),
                        # ... copy all bracket fields
                        rate_00=Decimal(str(old_base.rate_00)) if old_base.rate_00 else Decimal('0'),
                        rate_01=Decimal(str(old_base.rate_01)) if old_base.rate_01 else Decimal('0'),
                        # ... copy all rate fields
                    )
                    
                    migrated_count += 1
                    
                except Exception as e:
                    self.stderr.write(f"Error migrating {old_base}: {e}")
                    continue
        
        self.stdout.write(f"Successfully migrated {migrated_count} CalculationBase records")