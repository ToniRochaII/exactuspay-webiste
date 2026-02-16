# registry.py - FIXED VERSION
import importlib
import logging

logger = logging.getLogger(__name__)

def get_calculator_class(country_slug):
    """
    Returns the main calculator engine.
    Now defaults strictly to the Universal Engine for all countries.
    """
    # IMPORT MOVED HERE to prevent circular dependency
    from Exactus.payroll.calculator.universal import UniversalPayrollCalculator
    logger.debug(f"Registry: Routing '{country_slug}' to UniversalPayrollCalculator")
    return UniversalPayrollCalculator

def get_country_extension(country_slug):
    """
    Uses dynamic imports to find country-specific hooks.
    """
    SLUG_TO_MODULE = {
        'united-kingdom': 'gb',
        'great-britain': 'gb',
        'brazil': 'br',
        'usa': 'us',
    }
    
    folder_code = SLUG_TO_MODULE.get(country_slug, country_slug.replace('-', '_'))
    
    try:
        module_path = f"Exactus.payroll.extensions.{folder_code}.extension"
        module = importlib.import_module(module_path)
        class_name = f"{folder_code.upper()}Extension"
        
        if hasattr(module, class_name):
            logger.debug(f"Registry: Found extension '{class_name}' for {country_slug}")
            return getattr(module, class_name)()
            
        if hasattr(module, 'CountryExtension'):
            return getattr(module, 'CountryExtension')()
    except ImportError:
        pass
    
    return BaseExtension()

class BaseExtension:
    def preprocess(self, calculator):
        pass
        
    def postprocess(self, calculator):
        pass