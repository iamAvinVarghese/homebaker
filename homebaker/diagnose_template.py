import os
path = r"d:\HomeBakerProject\homebaker\templates\baker_orders.html"
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"FILE SIZE: {len(content)}")
        print("--- CONTENT START ---")
        print(content[content.find('{% if order.status =='):content.find('{% endwith %}')+13])
        print("--- CONTENT END ---")
else:
    print("FILE NOT FOUND")
