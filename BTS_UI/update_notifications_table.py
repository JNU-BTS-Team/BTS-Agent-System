import mysql.connector

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'wpw242512',
    'database': 'SECD'
}

try:
    # 连接到数据库
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    
    # 修改notifications表的type字段，添加todo类型
    cursor.execute("ALTER TABLE notifications MODIFY COLUMN type ENUM('new_diagnosis', 'follow_up', 'todo') NOT NULL")
    
    db.commit()
    print("成功修改notifications表，添加了todo类型")
    
except Exception as e:
    print(f"修改表时出错: {e}")
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'db' in locals():
        db.close()