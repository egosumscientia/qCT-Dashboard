import pg8000.native

print("Connecting with pg8000...")
try:
    conn = pg8000.native.Connection(user="qct", password="qct", host="localhost", port=5432, database="qct")
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
