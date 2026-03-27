import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homebaker.settings')
django.setup()

from django.db import connection

print("--- Searching Database for '1.3' ---")
cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for (table_name,) in tables:
    if table_name.startswith('django_') or table_name.startswith('auth_'):
        continue
        
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [c[1] for c in cursor.fetchall()]
    
    for col in columns:
        try:
            query = f"SELECT * FROM {table_name} WHERE CAST({col} AS TEXT) LIKE '%1.3%'"
            cursor.execute(query)
            rows = cursor.fetchall()
            if rows:
                print(f"Table: {table_name}, Column: {col}")
                for row in rows:
                    print(f"  {row}")
        except Exception as e:
            pass
print("--- Search Completed ---")
