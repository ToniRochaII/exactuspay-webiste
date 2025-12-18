# Exactus/payroll/calculator/countries/br/calculator.py
from decimal import Decimal
from typing import Dict, List

from Exactus.payroll.calculator.base import BasePayrollCalculator
from .income_tax import calculate_irrf
from .social_security import calculate_inss


class BRPayrollCalculator(BasePayrollCalculator):
    """
    Brazil Payroll Calculator
    """
    
    def calculate_tax(self, employee, gross, period):
        """
        Calculate Brazil taxes for a single employee
        Returns: {'inss': Decimal, 'irrf': Decimal, 'total_tax': Decimal}
        """
        # Calculate INSS (social security)
        inss = calculate_inss(gross)
        
        # Calculate IRRF (income tax - taxable base = gross - INSS)
        taxable_base = gross - inss
        irrf = calculate_irrf(taxable_base)
        
        return {
            'inss': inss,
            'irrf': irrf,
            'total_tax': inss + irrf
        }
    
    def calculate_social_security(self, employee, gross, period):
        """Calculate INSS for an employee"""
        return calculate_inss(gross)
    
    def calculate_income_tax(self, employee, gross, period):
        """Calculate IRRF for an employee"""
        inss = calculate_inss(gross)
        taxable_base = gross - inss
        return calculate_irrf(taxable_base)
    
    def calculate(self, employees_data):
        """
        Calculate payroll for multiple employees at once
        employees_data: List of dicts with {'employee': obj, 'gross': Decimal}
        """
        employee_results = []
        totals = {
            "gross": Decimal("0.00"),
            "inss": Decimal("0.00"),
            "irrf": Decimal("0.00"),
            "total_tax": Decimal("0.00"),
            "net": Decimal("0.00"),
        }
        
        for emp_data in employees_data:
            employee = emp_data['employee']
            gross = emp_data['gross']
            
            # Calculate taxes
            tax_result = self.calculate_tax(employee, gross, self.period)
            
            # Calculate net
            net = gross - tax_result['total_tax']
            
            employee_results.append({
                "employee_id": employee.id,
                "employee_code": employee.employee_code,
                "employee_name": f"{employee.employee_name} {employee.employee_surname}",
                "gross": gross,
                "inss": tax_result['inss'],
                "irrf": tax_result['irrf'],
                "total_tax": tax_result['total_tax'],
                "net": net,
                "additional_deductions": emp_data.get('deductions', Decimal('0')),
            })
            
            # Update totals
            totals["gross"] += gross
            totals["inss"] += tax_result['inss']
            totals["irrf"] += tax_result['irrf']
            totals["total_tax"] += tax_result['total_tax']
            totals["net"] += net
        
        return {
            "employee_results": employee_results,
            "totals": totals,
        }

