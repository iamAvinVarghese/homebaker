#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix the split template tag in baker_orders.html"""

with open('templates/baker_orders.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the split if condition
old_text = """{% if order.status == 'confirmed' or order.status == 'baking' or order.status == 'packing'
                            or order.status == 'ready' %}"""

new_text = """{% if order.status == 'confirmed' or order.status == 'baking' or order.status == 'packing' or order.status == 'ready' %}"""

content = content.replace(old_text, new_text)

with open('templates/baker_orders.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed split template tag!")
