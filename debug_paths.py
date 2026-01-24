import os
import sys
import importlib

# Add current path
sys.path.append(os.getcwd())

def check_uk_setup():
    print("--- DIAGNOSTIC START ---")
    
    # 1. Check Directory Structure
    base_path = os.path.join("Exactus", "payroll", "calculator", "countries")
    if not os.path.exists(base_path):
        print(f"[FAIL] Base folder not found: {base_path}")
        return

    print(f"Scanning: {base_path}")
    subfolders = [f.name for f in os.scandir(base_path) if f.is_dir() and f.name != "__pycache__"]
    
    if not subfolders:
        print("[FAIL] No country folders found!")
        return
        
    print(f"Found country folders: {subfolders}")
    
    # 2. Check Importability
    for folder in subfolders:
        module_path = f"Exactus.payroll.calculator.countries.{folder}.calculator"
        print(f"\nChecking Folder: '{folder}'")
        
        # Check for __init__.py
        init_path = os.path.join(base_path, folder, "__init__.py")
        if os.path.exists(init_path):
            print(f"  [OK] __init__.py exists")
        else:
            print(f"  [FAIL] MISSING __init__.py (Python cannot import this folder)")
            continue

        # Try Import
        try:
            mod = importlib.import_module(module_path)
            print(f"  [OK] Module imported successfully")
            
            # Look for Strategy Class
            found_class = False
            for attr in dir(mod):
                if attr.lower().endswith("payrollstrategy"):
                    print(f"  [OK] Found Strategy Class: {attr}")
                    found_class = True
            
            if not found_class:
                print("  [FAIL] No class ending in 'PayrollStrategy' found in calculator.py")
                
        except ImportError as e:
            print(f"  [FAIL] Import Error: {e}")
        except Exception as e:
            print(f"  [FAIL] Other Error: {e}")

    print("\n--- DIAGNOSTIC END ---")

if __name__ == "__main__":
    check_uk_setup()