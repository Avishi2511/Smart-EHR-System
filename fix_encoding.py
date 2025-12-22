# Quick fix for encoding issues in ADNI pipeline
# This script removes problematic Unicode characters

import re

files_to_fix = [
    r"c:\Users\hp\Documents\GitHub\Smart-EHR-System\adni-python\api\run_pipeline.py",
]

for filepath in files_to_fix:
    try:
        # Read with UTF-8
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Only fix if not already corrupted
        if '[FAIL][[FAIL]' not in content:
            # Replace Unicode checkmarks with ASCII
            content = content.replace('✓', '[OK]')
            content = content.replace('✗', '[FAIL]')
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Fixed: {filepath}")
        else:
            print(f"Skipped (already corrupted): {filepath}")
            
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")

print("\nDone!")
