from django.core.management.base import BaseCommand
from Exactus.accounts.models import PermissionMatrix

BASE = {
    "ADMIN": [("ALL", "ALL")],
    "COMPLIANCE": [("RULE", "CREATE"), ("RULE", "READ"), ("RULE", "UPDATE"), ("RULE", "DELETE")],
    "BILLING": [("COMPANY", "READ"), ("PAYROLL", "READ"), ("PERIOD", "READ"), ("EMPLOYEE", "READ")],
    "IMPLEMENTATION": [
        ("COMPANY", "CREATE"), ("COMPANY", "READ"), ("COMPANY", "UPDATE"), ("COMPANY", "DELETE"),
        ("EMPLOYEE", "CREATE"), ("EMPLOYEE", "READ"), ("EMPLOYEE", "UPDATE"), ("EMPLOYEE", "DELETE"),
        ("PAYROLL", "CREATE"), ("PAYROLL", "READ"), ("PAYROLL", "UPDATE"), ("PAYROLL", "DELETE"),
        ("PERIOD", "CREATE"), ("PERIOD", "READ"), ("PERIOD", "UPDATE"), ("PERIOD", "DELETE")
    ],
    "OPERATION": [
        ("COMPANY", "READ"), ("COMPANY", "UPDATE"),
        ("EMPLOYEE", "READ"), ("EMPLOYEE", "UPDATE"),
        ("PAYROLL", "EXECUTE"), ("PAYROLL", "READ"), ("PAYROLL", "UPDATE"), ("PAYROLL", "TRANSFER"),
        ("PERIOD", "READ"), ("PERIOD", "UPDATE")
    ],
    "DIRECTOR": [
        ("COMPANY", "EXECUTE"), ("COMPANY", "READ"), ("COMPANY", "UPDATE"), ("COMPANY", "TRANSFER"),
        ("COMPANY", "APPROVE"), ("COMPANY", "ASSIGN")
    ],
    "MANAGER": [
        ("COMPANY", "EXECUTE"), ("COMPANY", "READ"), ("COMPANY", "UPDATE"), ("COMPANY", "TRANSFER"),
        ("COMPANY", "APPROVE"), ("COMPANY", "ASSIGN")
    ],
    "SPECIALIST": [
        ("COMPANY", "EXECUTE"), ("COMPANY", "READ"), ("COMPANY", "UPDATE"), ("COMPANY", "TRANSFER")
    ],
    "FINANCE": [("REPORT", "READ")],
    "EMPLOYEE": [("REPORT", "READ")],  # filter by self in views later
}

class Command(BaseCommand):
    help = "Seed PermissionMatrix with default role/domain/action rules."

    def handle(self, *args, **options):
        created = 0
        for role, pairs in BASE.items():
            for domain, action in pairs:
                obj, was_created = PermissionMatrix.objects.get_or_create(
                    role=role, domain=domain, action=action,
                    defaults={"allowed": True}
                )
                if was_created:
                    created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} permissions."))