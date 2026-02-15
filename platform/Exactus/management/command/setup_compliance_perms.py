from django.core.management.base import BaseCommand
from Exactus.accounts.models import PermissionMatrix

class Command(BaseCommand):
    help = 'Seeds permissions for the Compliance role'

    def handle(self, *args, **kwargs):
        # Define the permissions Compliance needs to see the menu
        permissions = [
            # Domain, Action
            ("COMPANY", "READ"),
            ("COMPANY", "CREATE"), # Needed for "Add Company" button
            ("PAYROLL", "READ"),
            ("EMPLOYEE", "READ"),
            ("REPORT", "READ"),
            ("RULE", "READ"),      # Needed for "Regulations" menu
            ("USER", "READ"),      # Needed for "User Management"
        ]

        role = "COMPLIANCE"
        count = 0

        for domain, action in permissions:
            # Check if exists, if not create
            obj, created = PermissionMatrix.objects.get_or_create(
                role=role,
                domain=domain,
                action=action,
                defaults={'allowed': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Added: {role} -> {domain}:{action}'))
                count += 1
            else:
                self.stdout.write(f'Skipped (Exists): {role} -> {domain}:{action}')

        self.stdout.write(self.style.SUCCESS(f'Done. Added {count} permissions.'))
        
        # Clear cache to ensure changes appear immediately
        from django.core.cache import cache
        cache.clear()
        self.stdout.write(self.style.WARNING('Cache cleared.'))