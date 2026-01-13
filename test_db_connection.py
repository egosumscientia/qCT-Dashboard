import psycopg2
import os

url = "postgresql://qct:qct@localhost:5432/qct"
print(f"Connecting to {url}...")
try:
    conn = psycopg2.connect(url)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
