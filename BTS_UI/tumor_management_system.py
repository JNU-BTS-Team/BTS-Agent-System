import mysql.connector
import hashlib
import os
import uuid
from datetime import datetime

class TumorManagementSystem:
    def __init__(self):
        self.db = None
        self.cursor = None
        self.current_user = None
        self.connect_db()
    
    def connect_db(self):
        """连接到MySQL数据库"""
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="wpw242512",
                database="SECD"
            )
            self.cursor = self.db.cursor(dictionary=True)  # 返回字典格式的结果
            print("数据库连接成功！")
        except mysql.connector.Error as err:
            print(f"数据库连接失败: {err}")
    
    def hash_password(self, password):
        """密码哈希加密"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username, password):
        """用户登录功能"""
        hashed_password = self.hash_password(password)
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        self.cursor.execute(query, (username, hashed_password))
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = user
            print(f"登录成功！欢迎 {user['role']} {user['username']}")
            return True
        else:
            print("用户名或密码错误！")
            return False
    
    def logout(self):
        """用户登出功能"""
        self.current_user = None
        print("登出成功！")
    
    def change_password(self, old_password, new_password):
        """修改当前用户密码"""
        if not self.current_user:
            print("请先登录！")
            return False
        
        # 验证旧密码
        hashed_old_password = self.hash_password(old_password)
        query = "SELECT * FROM users WHERE id = %s AND password = %s"
        self.cursor.execute(query, (self.current_user['id'], hashed_old_password))
        
        if not self.cursor.fetchone():
            print("旧密码错误！")
            return False
        
        # 更新新密码
        try:
            hashed_new_password = self.hash_password(new_password)
            query = "UPDATE users SET password = %s WHERE id = %s"
            self.cursor.execute(query, (hashed_new_password, self.current_user['id']))
            self.db.commit()
            print("密码修改成功！")
            return True
        except mysql.connector.Error as err:
            print(f"修改密码失败: {err}")
            return False
    
    # ------------------------- 用户管理功能（管理员权限） ------------------------- #
    def add_doctor(self, username, password):
        """添加医生账号（仅管理员可操作）"""
        if not self.current_user or self.current_user['role'] != 'admin':
            print("权限不足，只有管理员可以添加医生账号！")
            return False
        
        try:
            hashed_password = self.hash_password(password)
            query = "INSERT INTO users (username, password, role) VALUES (%s, %s, 'doctor')"
            self.cursor.execute(query, (username, hashed_password))
            self.db.commit()
            print(f"医生账号 {username} 添加成功！")
            return True
        except mysql.connector.Error as err:
            print(f"添加医生失败: {err}")
            return False
    
    def get_all_doctors(self):
        """获取所有医生账号（仅管理员可操作）"""
        if not self.current_user or self.current_user['role'] != 'admin':
            print("权限不足，只有管理员可以查看医生账号！")
            return []
        
        query = "SELECT id, username, role, created_at FROM users WHERE role = 'doctor'"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def search_doctors(self, username):
        """根据用户名搜索医生账号（仅管理员可操作）"""
        if not self.current_user or self.current_user['role'] != 'admin':
            print("权限不足，只有管理员可以搜索医生账号！")
            return []
        
        query = "SELECT id, username, role, created_at FROM users WHERE role = 'doctor' AND username LIKE %s"
        self.cursor.execute(query, (f"%{username}%",))
        return self.cursor.fetchall()
    
    def delete_doctor(self, username):
        """删除医生账号（仅管理员可操作）"""
        if not self.current_user or self.current_user['role'] != 'admin':
            print("权限不足，只有管理员可以删除医生账号！")
            return False
        
        try:
            # 获取医生ID，用于检查是否是当前登录账号
            query = "SELECT id FROM users WHERE username = %s AND role = 'doctor'"
            self.cursor.execute(query, (username,))
            doctor = self.cursor.fetchone()
            
            if not doctor:
                print(f"未找到医生账号 {username}！")
                return False
            
            doctor_id = doctor['id']
            
            # 不能删除自己（如果当前用户是医生的话）
            if self.current_user['id'] == doctor_id:
                print("不能删除当前登录的账号！")
                return False
            
            query = "DELETE FROM users WHERE id = %s AND role = 'doctor'"
            self.cursor.execute(query, (doctor_id,))
            self.db.commit()
            
            if self.cursor.rowcount > 0:
                print(f"医生账号 {username} 删除成功！")
                return True
            else:
                print(f"删除医生 {username} 失败！")
                return False
                
        except mysql.connector.Error as err:
            print(f"删除医生失败: {err}")
            return False
    
    def get_all_patients(self):
        """获取所有病人信息"""
        if not self.current_user:
            print("请先登录！")
            return []
        
        query = "SELECT * FROM patients ORDER BY id DESC"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    # ------------------------- 病人信息管理功能 ------------------------- #
    def add_patient(self, patient_id, name, gender, age, birthday=None, phone=None, address=None):
        """添加病人信息"""
        if not self.current_user:
            print("请先登录！")
            return False
        
        try:
            query = """
            INSERT INTO patients (patient_id, name, gender, age, birthday, phone, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (patient_id, name, gender, age, birthday, phone, address))
            self.db.commit()
            print(f"病人 {name} 添加成功！")
            return True
        except mysql.connector.Error as err:
            print(f"添加病人失败: {err}")
            return False
    
    def delete_patient(self, patient_id):
        """删除病人信息"""
        if not self.current_user:
            print("请先登录！")
            return False
        
        try:
            # 先获取病人ID
            query = "SELECT id FROM patients WHERE patient_id = %s"
            self.cursor.execute(query, (patient_id,))
            patient = self.cursor.fetchone()
            
            if not patient:
                print(f"未找到病人ID为 {patient_id} 的病人！")
                return False
            
            # 删除病人（级联删除相关的诊断和图片记录）
            query = "DELETE FROM patients WHERE patient_id = %s"
            self.cursor.execute(query, (patient_id,))
            self.db.commit()
            print(f"病人 {patient_id} 删除成功！")
            return True
        except mysql.connector.Error as err:
            print(f"删除病人失败: {err}")
            return False
    
    def get_patient(self, patient_id):
        """根据病人ID获取病人信息"""
        if not self.current_user:
            print("请先登录！")
            return None
        
        query = "SELECT * FROM patients WHERE patient_id = %s"
        self.cursor.execute(query, (patient_id,))
        return self.cursor.fetchone()
    
    def search_patients_by_name(self, name):
        """根据姓名搜索病人信息"""
        if not self.current_user:
            print("请先登录！")
            return []
        
        query = "SELECT * FROM patients WHERE name LIKE %s"
        self.cursor.execute(query, (f"%{name}%",))
        return self.cursor.fetchall()
    
    def update_patient(self, patient_id, **kwargs):
        """更新病人信息"""
        if not self.current_user:
            print("请先登录！")
            return False
        
        try:
            # 构建更新语句
            set_clause = ", ".join([f"{key} = %s" for key in kwargs.keys()])
            values = list(kwargs.values()) + [patient_id]
            
            query = f"UPDATE patients SET {set_clause} WHERE patient_id = %s"
            self.cursor.execute(query, values)
            self.db.commit()
            print(f"病人 {patient_id} 信息更新成功！")
            return True
        except mysql.connector.Error as err:
            print(f"更新病人信息失败: {err}")
            return False
    
    # ------------------------- 诊断信息管理功能 ------------------------- #
    def add_diagnosis(self, patient_id, diagnosis_date, tumor_type=None, tumor_location=None, 
                     tumor_size=None, agent_analysis=None, agent_recommendations=None, 
                     doctor_notes=None):
        """添加诊断信息"""
        if not self.current_user:
            print("请先登录！")
            return None
        
        try:
            # 先获取病人ID
            query = "SELECT id FROM patients WHERE patient_id = %s"
            self.cursor.execute(query, (patient_id,))
            patient = self.cursor.fetchone()
            
            if not patient:
                print(f"未找到病人ID为 {patient_id} 的病人！")
                return None
            
            # 添加诊断记录
            query = """
            INSERT INTO diagnoses (patient_id, doctor_id, diagnosis_date, tumor_type, 
                                 tumor_location, tumor_size, agent_analysis, 
                                 agent_recommendations, doctor_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                patient['id'],
                self.current_user['id'] if self.current_user['role'] == 'doctor' else None,
                diagnosis_date,
                tumor_type,
                tumor_location,
                tumor_size,
                agent_analysis,
                agent_recommendations,
                doctor_notes
            )
            
            self.cursor.execute(query, values)
            self.db.commit()
            
            diagnosis_id = self.cursor.lastrowid
            print(f"诊断记录添加成功！诊断ID: {diagnosis_id}")
            return diagnosis_id
            
        except mysql.connector.Error as err:
            print(f"添加诊断记录失败: {err}")
            return None
    
    def get_patient_diagnoses(self, patient_id):
        """获取病人的所有诊断记录"""
        if not self.current_user:
            print("请先登录！")
            return []
        
        try:
            # 先获取病人ID
            query = "SELECT id FROM patients WHERE patient_id = %s"
            self.cursor.execute(query, (patient_id,))
            patient = self.cursor.fetchone()
            
            if not patient:
                print(f"未找到病人ID为 {patient_id} 的病人！")
                return []
            
            # 获取诊断记录
            query = """
            SELECT d.*, u.username as doctor_name
            FROM diagnoses d
            LEFT JOIN users u ON d.doctor_id = u.id
            WHERE d.patient_id = %s
            ORDER BY d.diagnosis_date DESC
            """
            self.cursor.execute(query, (patient['id'],))
            return self.cursor.fetchall()
            
        except mysql.connector.Error as err:
            print(f"获取诊断记录失败: {err}")
            return []
    
    # ------------------------- 图片管理功能 ------------------------- #
    def upload_image(self, diagnosis_id, image_path):
        """上传MRI图片到系统"""
        if not self.current_user:
            print("请先登录！")
            return False
        
        try:
            # 检查图片是否存在
            if not os.path.exists(image_path):
                print(f"图片文件 {image_path} 不存在！")
                return False
            
            # 创建图片存储目录（如果不存在）
            upload_dir = "uploaded_images"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # 生成唯一的文件名
            file_extension = os.path.splitext(image_path)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            new_image_path = os.path.join(upload_dir, unique_filename)
            
            # 复制图片到存储目录
            import shutil
            shutil.copy(image_path, new_image_path)
            
            # 保存图片信息到数据库
            image_name = os.path.basename(image_path)
            image_type = file_extension[1:].lower()  # 去除点号
            
            query = """
            INSERT INTO images (diagnosis_id, image_path, image_name, image_type)
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (diagnosis_id, new_image_path, image_name, image_type))
            self.db.commit()
            
            print(f"图片上传成功！存储路径: {new_image_path}")
            return True
            
        except Exception as err:
            print(f"图片上传失败: {err}")
            return False
    
    def get_diagnosis_images(self, diagnosis_id):
        """获取诊断记录的所有图片"""
        if not self.current_user:
            print("请先登录！")
            return []
        
        query = "SELECT * FROM images WHERE diagnosis_id = %s"
        self.cursor.execute(query, (diagnosis_id,))
        return self.cursor.fetchall()
    
    # ------------------------- 统计数据功能 ------------------------- #
    def get_patient_age_distribution(self):
        """获取病人年龄分布统计"""
        if not self.current_user:
            print("请先登录！")
            return []
        
        query = """
        SELECT 
            CASE 
                WHEN age < 20 THEN '20岁以下'
                WHEN age >= 20 AND age < 40 THEN '20-39岁'
                WHEN age >= 40 AND age < 60 THEN '40-59岁'
                WHEN age >= 60 AND age < 80 THEN '60-79岁'
                ELSE '80岁以上'
            END as age_group,
            COUNT(*) as count
        FROM patients
        GROUP BY age_group
        ORDER BY MIN(age)
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_tumor_type_distribution(self):
        """获取肿瘤类型分布统计"""
        if not self.current_user:
            print("请先登录！")
            return []
        
        query = """
        SELECT tumor_type, COUNT(*) as count
        FROM diagnoses
        WHERE tumor_type IS NOT NULL AND tumor_type != ''
        GROUP BY tumor_type
        ORDER BY count DESC
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_monthly_diagnoses(self):
        """获取各月诊断数量统计"""
        if not self.current_user:
            print("请先登录！")
            return []
        
        query = """
        SELECT 
            DATE_FORMAT(diagnosis_date, '%Y-%m') as month,
            COUNT(*) as count
        FROM diagnoses
        GROUP BY month
        ORDER BY month
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_total_statistics(self):
        """获取总体统计数据"""
        if not self.current_user:
            print("请先登录！")
            return {}
        
        # 总病人数
        self.cursor.execute("SELECT COUNT(*) as total FROM patients")
        total_patients = self.cursor.fetchone()['total']
        
        # 总诊断数
        self.cursor.execute("SELECT COUNT(*) as total FROM diagnoses")
        total_diagnoses = self.cursor.fetchone()['total']
        
        # 总图片数
        self.cursor.execute("SELECT COUNT(*) as total FROM images")
        total_images = self.cursor.fetchone()['total']
        
        # 本月诊断数
        self.cursor.execute("SELECT COUNT(*) as total FROM diagnoses WHERE DATE_FORMAT(diagnosis_date, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')")
        monthly_diagnoses = self.cursor.fetchone()['total']
        
        return {
            'total_patients': total_patients,
            'total_diagnoses': total_diagnoses,
            'total_images': total_images,
            'monthly_diagnoses': monthly_diagnoses
        }
    
    # ------------------------- Agent分析结果管理 ------------------------- #
    def update_agent_analysis(self, diagnosis_id, agent_analysis, agent_recommendations):
        """更新Agent分析结果"""
        if not self.current_user:
            print("请先登录！")
            return False
        
        try:
            query = """
            UPDATE diagnoses 
            SET agent_analysis = %s, agent_recommendations = %s
            WHERE id = %s
            """
            self.cursor.execute(query, (agent_analysis, agent_recommendations, diagnosis_id))
            self.db.commit()
            print("Agent分析结果更新成功！")
            return True
        except mysql.connector.Error as err:
            print(f"更新Agent分析结果失败: {err}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.db:
            self.db.close()
        print("数据库连接已关闭！")


# ------------------------- 系统使用示例 ------------------------- #
if __name__ == "__main__":
    system = TumorManagementSystem()
    
    # 示例：管理员登录
    # system.login("admin", "admin123")
    # 示例：添加医生
    # system.add_doctor("doctor1", "doctor123")
    
    # 示例：医生登录
    # system.login("doctor1", "doctor123")
    # 示例：添加病人
    # system.add_patient(
    #     patient_id="P001",
    #     name="张三",
    #     gender="男",
    #     age=45,
    #     phone="13800138000",
    #     address="北京市朝阳区"
    # )
    
    # 示例：添加诊断记录
    # diagnosis_id = system.add_diagnosis(
    #     patient_id="P001",
    #     diagnosis_date="2024-05-20",
    #     tumor_type="胶质瘤",
    #     tumor_location="左侧额叶",
    #     doctor_notes="病人有头痛症状，建议进一步检查"
    # )
    
    # 示例：上传图片（需要替换为实际图片路径）
    # if diagnosis_id:
    #     system.upload_image(diagnosis_id, "path/to/your/image.jpg")
    
    # 示例：更新Agent分析结果
    # if diagnosis_id:
    #     system.update_agent_analysis(
    #         diagnosis_id,
    #         "根据MRI图像分析，肿瘤位于左侧额叶，大小约3cm×2.5cm，边界较清晰。",
    #         "建议进行手术切除，并结合放疗进行综合治疗。定期复查MRI以监测病情变化。"
    #     )
    
    # 示例：获取病人的诊断记录
    # diagnoses = system.get_patient_diagnoses("P001")
    # for diag in diagnoses:
    #     print(f"诊断日期: {diag['diagnosis_date']}, 肿瘤类型: {diag['tumor_type']}")
    
    system.close()