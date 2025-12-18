# payroll/calculator/countries/gb/calculator.py

from Exactus.payroll.calculator.base import BasePayrollCalculator
from .income_tax import calculate_income_tax
from .national_insurance import calculate_ni

class GBPayrollCalculator(BasePayrollCalculator):

    def calculate(self):
        employee_results = []
        totals = {
            "gross": 0,
            "tax": 0,
            "employee_ni": 0,
            "net": 0,
        }

        for employee in self.employees:
            gross = employee.get_period_gross(self.period)

            tax = calculate_income_tax(gross, self.tax_year)
            ni = calculate_ni(gross, self.tax_year)

            net = gross - tax - ni

            employee_results.append({
                "employee_id": employee.id,
                "gross": gross,
                "tax": tax,
                "ni": ni,
                "net": net,
            })

            totals["gross"] += gross
            totals["tax"] += tax
            totals["employee_ni"] += ni
            totals["net"] += net

        return {
            "employee_results": employee_results,
            "totals": totals,
        }

    def calculate_tax(self, employee, gross, period):
        """
        Calculate the total tax (income tax + NI) for a given employee and gross amount for the period.
        We assume the period is a month and the gross is the monthly gross.
        """
        # Annualize the gross
        annual_gross = gross * 12
        tax = calculate_income_tax(annual_gross)
        ni = calculate_ni(annual_gross)
        # Return the monthly tax
        return (tax + ni) / 12