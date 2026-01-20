import psycopg2

# 데이터베이스 연결 설정
connection = psycopg2.connect(
    host="localhost",
    database="Working_report_table",
    user="postgres",
    password="8176",
    port=5432
)

cursor = connection.cursor()

# SELECT 쿼리 실행
cursor.execute("SELECT * FROM users")

# 결과 가져오기
rows = cursor.fetchall()
for row in rows:
    print(row)

# 연결 종료
cursor.close()
connection.close()