import re
import os

def fix_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for pattern, substitute in replacements:
        content = re.sub(pattern, substitute, content)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. views_customer.py
replacements_customer = [
    (r"delivery_charge = Decimal\('20\.00'\)", "delivery_charge = Decimal('50.00')"),
    (r"delivery_charge = Decimal\('20\.00'\)", "delivery_charge = Decimal('50.00')") # Multiple occurrences
]
fix_file(r"d:\HomeBakerProject\homebaker\main\views_customer.py", replacements_customer)

print("Revert completed via script.")
