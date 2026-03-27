#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

filepath = 'templates/baker_orders.html'
if not os.path.exists(filepath):
    print(f"File {filepath} not found")
    exit(1)

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Comprehensive fix for baker_orders.html to prevent auto-formatter issues
# 1. Consolidate the specific confirmed status check
old_if = """{% if order.status == 'confirmed' or order.status == 'baking' or order.status == 'packing'
                            or order.status == 'ready' %}"""
new_if = "{% if order.status == 'confirmed' or order.status == 'baking' or order.status == 'packing' or order.status == 'ready' %}"
content = content.replace(old_if, new_if)

# 2. Fix OTP split
old_otp = """OTP: <strong>{{ order.delivery_otp
                                        }}</strong>"""
new_otp = "OTP: <strong>{{ order.delivery_otp }}</strong>"
content = content.replace(old_otp, new_otp)

# 3. Fix disabled button split
old_btn = """disabled>{{
                                order.get_status_display }}</button>"""
new_btn = "disabled>{{ order.get_status_display }}</button>"
content = content.replace(old_btn, new_btn)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied single-line fixes to baker_orders.html")
