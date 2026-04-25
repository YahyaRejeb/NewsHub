import mysql.connector
import os

db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'newshub1')
}

try:
    print("Connecting to MySQL...")
    conn = mysql.connector.connect(**db_config)
    print("Connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interests;")
    rows = cursor.fetchall()
    print("Interests table content:", rows)
    
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
