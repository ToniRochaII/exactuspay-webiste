from decimal import Decimal

class CountryPayrollStrategy:
    """
    Base strategy for country-specific payroll logic.
    """
    def __init__(self, universal_calculator):
        self.calc = universal_calculator  # Access to results_dict, employee, period
        self.results = self.calc.results_dict

    def process_nuances(self):
        """
        Override this method to implement country-specific logic.
        This runs AFTER standard aggregation but BEFORE final Net Pay.
        """
        pass