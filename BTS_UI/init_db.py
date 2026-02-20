import mysql.connector

# 连接数据库
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
    port=3306
)

cursor = conn.cursor()

# 读取SQL文件
with open('init_db.sql', 'r', encoding='utf8') as f:
    sql_content = f.read()

# 执行SQL语句（按分号分割）
sql_statements = sql_content.split(';')
for statement in sql_statements:
    statement = statement.strip()
    if statement:
        try:
            cursor.execute(statement)
        except Exception as e:
            print(f"执行SQL语句时出错: {statement[:50]}...")
            print(f"错误信息: {e}")
            conn.rollback()
            break
else:
    conn.commit()
    print("数据库初始化完成！")
    
cursor.close()
conn.close()