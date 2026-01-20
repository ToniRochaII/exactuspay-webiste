from decimal import Decimal
from Exactus.payroll.calculator.base import BasePayrollCalculator
from Exactus.payroll.constants import (
    BASE_TAXABLE, BASE_NIABLE, EL_GROSS_PAYABLE,
    EL_TAX_FREE_ALLOWANCE, EL_INCOME_TAX, EL_NI_EE, EL_NI_ER,
    EL_PENSION_EE, EL_NET_PAY
)

class GBPayrollCalculator(BasePayrollCalculator):
    """
    Implements the 'Statutory Elements (law)' layer for Great Britain.
    """

    def calculate(self):
        # 1. Run Universal Segregation
        super().calculate()
        
        # 2. Run Statutory Calculations
        self.calculate_paye()      
        self.calculate_ni()
        
        # 3. Run Net Calculation
        self.calculate_net_pay()
        
        return {
            'elements': self.register,
            'breakdown': self.pd_breakdown
        }

    def calculate_paye(self):
        taxable_base = self.register[BASE_TAXABLE]
        
        # A. Tax-Free Allowance
        annual_allowance = Decimal('12570.00')
        period_allowance = round(annual_allowance / Decimal('12'), 2)
        
        self.register[EL_TAX_FREE_ALLOWANCE] = period_allowance
        
        # B. Taxable Income
        taxable_income = max(taxable_base - period_allowance, Decimal('0.00'))
        
        # C. Apply Tax Bands
        tax_due = Decimal('0.00')
        basic_band_limit = Decimal('3141.67') 
        
        if taxable_income <= basic_band_limit:
            tax_due += taxable_income * Decimal('0.20')
        else:
            tax_due += basic_band_limit * Decimal('0.20')
            remainder = taxable_income - basic_band_limit
            tax_due += remainder * Decimal('0.40')
            
        self.register[EL_INCOME_TAX] = round(tax_due, 2)

    def calculate_ni(self):
        ni_base = self.register[BASE_NIABLE]
        
        pt = Decimal('1048.00')
        st = Decimal('758.00')
        uel = Decimal('4189.00')
        
        # EE NI
        ni_ee = Decimal('0.00')
        if ni_base > pt:
            earnings_band_1 = min(ni_base, uel) - pt
            ni_ee += earnings_band_1 * Decimal('0.08')
            
            if ni_base > uel:
                ni_ee += (ni_base - uel) * Decimal('0.02')
                
        self.register[EL_NI_EE] = round(ni_ee, 2)

        # ER NI
        ni_er = Decimal('0.00')
        if ni_base > st:
            ni_er += (ni_base - st) * Decimal('0.138')
            
        self.register[EL_NI_ER] = round(ni_er, 2)

    def calculate_net_pay(self):
        gross_payable = self.register[EL_GROSS_PAYABLE]
        
        total_deductions = (
            self.register.get(EL_INCOME_TAX, Decimal('0')) + 
            self.register.get(EL_NI_EE, Decimal('0')) +
            self.register.get(EL_PENSION_EE, Decimal('0'))
        )
        
        net_pay = gross_payable - total_deductions
        self.register[EL_NET_PAY] = net_pay