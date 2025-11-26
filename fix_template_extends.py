import os
import re

def fix_template_extends(file_path):
    """Fix extends paths in a single template file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix the extends path
        content = re.sub(
            r'\{%\s*extends\s+["\']Exactus/templates/base\.html["\']\s*%\}',
            r'{% extends "../../templates/base.html" %}',
            content
        )
        
        # Also fix any other variations
        content = re.sub(
            r'\{%\s*extends\s+["\']\.\./\.\./templates/base\.html["\']\s*%\}',
            r'{% extends "../../templates/base.html" %}',
            content
        )
        
        # Write back only if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ FIXED: {file_path}")
            
    except Exception as e:
        print(f"❌ ERROR in {file_path}: {e}")

def scan_and_fix_all_templates():
    """Scan all HTML template files and fix extends paths"""
    template_files = []
    
    # Walk through all directories
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and other non-project directories
        if any(skip in root for skip in ['.venv', '__pycache__', '.git', 'node_modules', 'static', 'media']):
            continue
            
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                template_files.append(file_path)
    
    print(f"🔍 Found {len(template_files)} HTML template files to check...")
    
    # Fix each file
    for file_path in template_files:
        fix_template_extends(file_path)
    
    print("🎉 Template extends paths fixed!")

if __name__ == '__main__':
    scan_and_fix_all_templates()