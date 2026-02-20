import mysql.connector
import hashlib
from datetime import datetime
# 创建表并初始化管理员账号

"""
数据库设计：
四个表：
- users ：存储管理员和医生账号信息
- patients ：存储病人的基本信息
- diagnoses ：存储诊断记录和Agent分析结果
- images ：存储MRI图片信息

"""

# 创建数据库连接
db = mysql.connector.connect(
    host="localhost",  # MySQL服务器地址
    user="root",   # 用户名
    password="wpw242512",  # 密码
    database="SECD"  # 数据库名称
)

# 创建游标对象
cursor = db.cursor()

# 哈希函数，用于加密密码
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

try:
    # 创建用户表（管理员和医生）
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'doctor') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_users_table)
    print("用户表创建成功！")
    
    # 创建病人表
    create_patients_table = """
    CREATE TABLE IF NOT EXISTS patients (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id VARCHAR(20) NOT NULL UNIQUE,
        name VARCHAR(100) NOT NULL,
        gender ENUM('男', '女', '其他') NOT NULL,
        age INT NOT NULL,
        birthday DATE,
        phone VARCHAR(20),
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_patients_table)
    print("病人表创建成功！")
    
    # 创建诊断表
    create_diagnoses_table = """
    CREATE TABLE IF NOT EXISTS diagnoses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT NOT NULL,
        doctor_id INT,
        diagnosis_date DATE NOT NULL,
        follow_up_date DATE NULL,
        tumor_type VARCHAR(100),
        tumor_location VARCHAR(100),
        tumor_size VARCHAR(50),
        agent_analysis TEXT,
        agent_recommendations TEXT,
        doctor_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """
    cursor.execute(create_diagnoses_table)
    print("诊断表创建成功！")
    
    # 创建图片表
    create_images_table = """
    CREATE TABLE IF NOT EXISTS images (
        id INT AUTO_INCREMENT PRIMARY KEY,
        diagnosis_id INT NOT NULL,
        image_path VARCHAR(255) NOT NULL,
        image_name VARCHAR(100) NOT NULL,
        image_type VARCHAR(50),
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        segmentation_result TEXT,
        FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
    );
    """
    cursor.execute(create_images_table)
    print("图片表创建成功！")
    
    # 更新通知表类型，添加todo类型
    update_notifications_type = "ALTER TABLE notifications MODIFY COLUMN type ENUM('new_diagnosis', 'follow_up', 'todo') NOT NULL;"
    try:
        cursor.execute(update_notifications_type)
        print("通知表类型更新成功！")
    except Exception as e:
        print(f"更新通知表类型失败（可能是已经更新过）: {e}")
    
    # 创建待办任务表
    create_todos_table = """
    CREATE TABLE IF NOT EXISTS todos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        content TEXT NOT NULL,
        assigner_id INT NOT NULL,
        assignee_id INT NOT NULL,
        due_date DATE NOT NULL,
        is_completed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        FOREIGN KEY (assigner_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    cursor.execute(create_todos_table)
    print("待办任务表创建成功！")
    
    # 插入默认管理员账号
    admin_username = "admin"
    admin_password = "admin123"
    hashed_password = hash_password(admin_password)
    
    # 检查管理员账号是否已存在
    cursor.execute("SELECT * FROM users WHERE username = %s", (admin_username,))
    if not cursor.fetchone():
        insert_admin = "INSERT INTO users (username, password, role) VALUES (%s, %s, 'admin')"
        cursor.execute(insert_admin, (admin_username, hashed_password))
        print("默认管理员账号创建成功！")
    else:
        print("管理员账号已存在！")
    
    # 提交事务
    db.commit()
    print("数据库初始化完成！")
    
except mysql.connector.Error as err:
    print(f"数据库错误: {err}")
    db.rollback()

finally:
    # 关闭游标和数据库连接
    cursor.close()
    db.close()