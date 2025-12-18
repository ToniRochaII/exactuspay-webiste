# Exactus/payroll/calculator/base.py
from abc import ABC, abstractmethod
from decimal import Decimal


class BasePayrollCalculator(ABC):
    """Base class for country-specific payroll calculators"""
    
    def __init__(self, *, country, tax_year, period, employees):
        self.country = country
        self.tax_year = tax_year
        self.period = period
        self.employees = employees
    
    @abstractmethod
    def calculate_tax(self, employee, gross, period):
        """Calculate tax for a single employee"""
        pass
    
    @abstractmethod
    def calculate(self, employees_data):
        """Calculate payroll for multiple employees"""
        pass
    
    def get_period_factor(self):
        """Get factor to convert period amount to monthly"""
        days_in_period = (self.period.end_date - self.period.start_date).days + 1
        return Decimal(days_in_period) / Decimal(30.44)  # Average month days