import pymysql

try:
    conn = pymysql.connect(host='localhost', user='root', password='')
    cursor = conn.cursor()
    cursor.execute("SHOW VARIABLES LIKE 'datadir'")
    result = cursor.fetchone()
    print("DATADIR:", result[1] if result else "Not found")
    conn.close()
except Exception as e:
    print("Error:", e)
