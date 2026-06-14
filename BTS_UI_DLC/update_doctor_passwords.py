import mysql.connector
import hashlib

def hash_password(password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed

# 连接数据库（SECD2）
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="wpw242512",
    database="SECD2"
)

cursor = db.cursor(dictionary=True)

try:
    # 获取所有doctor用户
    cursor.execute("SELECT id, username, real_name, role FROM users WHERE role = 'doctor'")
    doctors = cursor.fetchall()
    
    print(f"找到 {len(doctors)} 个医生账号")
    print()
    
    # 计算123456的哈希
    default_password = "123456"
    hashed_password = hash_password(default_password)
    print(f"默认密码: {default_password}")
    print(f"密码哈希: {hashed_password}")
    print()
    
    # 更新所有doctor的密码
    for doctor in doctors:
        print(f"正在更新医生: {doctor['username']} ({doctor.get('real_name', doctor['username'])})")
        
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hashed_password, doctor['id'])
        )
        
    db.commit()
    print()
    print("成功！所有医生账号的密码已更新为 123456")
    
except mysql.connector.Error as err:
    print(f"数据库错误: {err}")
    db.rollback()
    
finally:
    cursor.close()
    db.close()
