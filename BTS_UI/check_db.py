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
    
    # 检查notifications表是否存在
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    """, (db_config['database'], 'notifications'))
    
    table_exists = cursor.fetchone()[0] > 0
    
    if table_exists:
        print("通知表(notifications)已存在于数据库中。")
    else:
        print("通知表(notifications)不存在，正在创建...")
        
        # 创建通知表
        cursor.execute("""
            CREATE TABLE notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                type ENUM('new_diagnosis', 'follow_up', 'todo') NOT NULL,
                title VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                related_id INT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 检查diagnoses表中是否存在follow_up_date字段
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s AND column_name = %s
        """, (db_config['database'], 'diagnoses', 'follow_up_date'))
        
        column_exists = cursor.fetchone()[0] > 0
        
        if column_exists:
            print("复诊日期字段(follow_up_date)已存在于diagnoses表中。")
        else:
            print("复诊日期字段(follow_up_date)不存在，正在添加...")
            cursor.execute("""
                ALTER TABLE diagnoses
                ADD COLUMN follow_up_date DATE NULL
            """)
            print("复诊日期字段添加成功。")
        
        print("通知表创建成功。")
    
    # 提交事务
    db.commit()
    print("数据库检查和更新完成。")
    
except mysql.connector.Error as err:
    print(f"数据库操作错误: {err}")
    if 'db' in locals():
        db.rollback()
finally:
    # 关闭游标和连接
    if 'cursor' in locals():
        cursor.close()
    if 'db' in locals():
        db.close()