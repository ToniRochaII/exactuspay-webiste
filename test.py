import sqlite3
import os

def inspect_employee_2():
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        print("❌ Error: db.sqlite3 not found.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"--- 🔍 INSPECTING EMPLOYEE ID 2 ---")

    try:
        # 1. FETCH EMPLOYEE DETAILS
        cursor.execute("""
            SELECT id, employee_name, employee_surname, tax_info_03 
            FROM employee_employee 
            WHERE id = 2
        """)
        emp = cursor.fetchone()
        
        if not emp:
            print("❌ Employee with ID 2 not found.")
            return

        print(f"👤 Employee: {emp['employee_name']} {emp['employee_surname']} (ID: 2)")
        print(f"   Tax Code Setting: {emp['tax_info_03']}") # Should be 1000N

        # 2. GET LATEST PAYROLL RESULT FOR THIS EMPLOYEE
        cursor.execute("""
            SELECT * FROM payroll_payrollresult 
            WHERE employee_id = 2 
            ORDER BY id DESC LIMIT 1
        """)
        result = cursor.fetchone()

        if not result:
            print("❌ No calculated payroll results found for Employee 2.")
            return

        print("\n📊 STORED DATABASE VALUES (What the website shows):")
        print(f"   Result ID:  {result['id']}")
        print("-" * 30)
        print(f"   Gross Pay:  £{result['gross_pay']}")
        print(f"   Total Tax:  £{result['total_tax']}") 
        print(f"   Net Pay:    £{result['net_pay']}")
        print("-" * 30)

        # 3. DIAGNOSIS
        stored_tax = float(result['total_tax'])
        
        # Expected Tax ~2038.03 | Old Wrong Tax ~2371.80
        if abs(stored_tax - 2038) < 50:
            print("   ✅ The database has the CORRECT number (~£2038).")
            print("      (If you see the old number on the site, clear your browser cache).")
        elif abs(stored_tax - 2371) < 50:
            print("   ⚠️  The database has the OLD wrong number (~£2371).")
            print("      (The fix works, but you haven't re-processed this specific payroll yet).")
            print("      -> Restart Server -> Go to Page -> Click 'Process Payroll'.")
        else:
            print(f"   ❓ Stored value is unexpected: £{stored_tax}")

    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_employee_2()