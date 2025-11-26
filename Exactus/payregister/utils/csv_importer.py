import csv
from datetime import datetime
from Exactus.payregister.models import PayRegister
from Exactus.employee.models import Employee
from Exactus.pdcodes.models import PDcode


def import_payregister_csv(file, company, created_by, dry_run=False):
    """
    Imports pay register earnings in bulk.
    Columns required:

    employee_number
    pd_code
    category
    amount
    start_date
    end_date
    entry_date
    """

    decoded = file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)

    results = {
        "created": 0,
        "errors": [],
        "rows": 0,
    }

    for i, row in enumerate(reader, start=2):  # Start at row 2 (after header)
        results["rows"] += 1

        emp_no = row.get("employee_number")
        pd_code_code = row.get("pd_code")
        category = row.get("category")
        amount = row.get("amount")

        # Validate required fields
        if not emp_no or not pd_code_code or not amount:
            results["errors"].append(f"Row {i}: Missing required fields.")
            continue

        # Validate employee
        try:
            employee = Employee.objects.get(company=company, employee_number=emp_no)
        except Employee.DoesNotExist:
            results["errors"].append(f"Row {i}: Employee {emp_no} not found in company.")
            continue

        # Validate PD code
        try:
            pd = PDcode.objects.get(company=company, pdcode_code=pd_code_code)
        except PDcode.DoesNotExist:
            results["errors"].append(f"Row {i}: PD code {pd_code_code} not found.")
            continue

        # Parse dates
        def parse_date(val):
            if not val:
                return None
            return datetime.strptime(val, "%Y-%m-%d").date()

        start = parse_date(row.get("start_date"))
        end = parse_date(row.get("end_date"))
        entry_date = parse_date(row.get("entry_date"))

        # Category rules validation
        if category == "PERMANENT" and not start:
            results["errors"].append(f"Row {i}: Permanent requires start_date.")
            continue

        if category == "TEMPORARY" and (not start or not end):
            results["errors"].append(f"Row {i}: Temporary requires start_date and end_date.")
            continue

        if category == "VARIABLE" and not entry_date:
            results["errors"].append(f"Row {i}: Variable requires entry_date.")
            continue

        # If dry-run, don't save
        if dry_run:
            continue

        # Create the PayRegister entry
        PayRegister.objects.create(
            employee=employee,
            pd_code=pd,
            category=category,
            amount=amount,
            start_date=start,
            end_date=end,
            entry_date=entry_date,
            created_by=created_by
        )

        results["created"] += 1

    return results
