from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
import hashlib
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于会话管理的密钥

# MySQL数据库配置
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'wpw242512'
app.config['MYSQL_DB'] = 'SECD'

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 登录页面的路由

class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    if user:
        return User(user['id'], user['username'], user['role'])
    return None

def get_db():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

def hash_password(password):
    """对密码进行哈希处理"""
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed

def send_notification(user_id, notification_type, title, content, related_id):
    """发送通知"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO notifications (user_id, type, title, content, related_id, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (user_id, notification_type, title, content, related_id, 0))
        db.commit()
        cursor.close()
        db.close()
    except Exception as err:
        print(f"发送通知失败: {err}")

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        # 查找用户
        cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user and user['password'] == hash_password(password):
            # 登录成功
            user_obj = User(user['id'], user['username'], user['role'])
            login_user(user_obj)
            flash('登录成功！', 'success')
            return redirect(url_for('main_interface'))
        else:
            # 登录失败
            flash('用户名或密码错误！', 'danger')
    return render_template('login.html')

# 登出路由
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出！', 'success')
    return redirect(url_for('login'))

# 仪表盘路由
@app.route('/main_interface')
@login_required
def main_interface():
    # 获取统计数据
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 总病人数
    cursor.execute("SELECT COUNT(*) as total FROM patients")
    total_patients = cursor.fetchone()['total']
    
    # 总诊断数
    cursor.execute("SELECT COUNT(*) as total FROM diagnoses")
    total_diagnoses = cursor.fetchone()['total']
    
    # 总图片数
    cursor.execute("SELECT COUNT(*) as total FROM images")
    total_images = cursor.fetchone()['total']
    
    # 本月诊断数
    cursor.execute("SELECT COUNT(*) as total FROM diagnoses WHERE DATE_FORMAT(diagnosis_date, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')")
    monthly_diagnoses = cursor.fetchone()['total']
    
    # 获取当前年份
    current_year = datetime.now().year
    
    # 创建全年12个月的月份列表
    all_months = [f"{current_year}-{str(i).zfill(2)}" for i in range(1, 13)]
    
    # 获取当前年份每个月的诊断数量数据
    cursor.execute("""
        SELECT 
            DATE_FORMAT(diagnosis_date, '%Y-%m') as month, 
            COUNT(*) as count 
        FROM diagnoses 
        WHERE YEAR(diagnosis_date) = %s 
        GROUP BY DATE_FORMAT(diagnosis_date, '%Y-%m') 
        ORDER BY month
    """, (current_year,))
    monthly_data = cursor.fetchall()
    
    # 将每月诊断数据转换为字典，方便查找
    monthly_dict = {data['month']: data['count'] for data in monthly_data}
    
    # 为全年所有月份创建数据点，没有数据的月份用0填充
    chart_data = []
    for month in all_months:
        count = monthly_dict.get(month, 0)
        # 将月份格式化为中文显示，例如"2024-01" → "1月"
        month_display = month.split('-')[1] + '月'
        chart_data.append({"month": month_display, "count": count})
    
    cursor.close()
    db.close()
    
    # 提取月份和数量用于图表
    months = [data['month'] for data in chart_data]
    counts = [data['count'] for data in chart_data]
    
    return render_template('main_interface.html', 
                           total_patients=total_patients,
                           total_diagnoses=total_diagnoses,
                           total_images=total_images,
                           monthly_diagnoses=monthly_diagnoses,
                           chart_data=chart_data,
                           months=months,
                           counts=counts)

# 医生管理路由（仅管理员）
@app.route('/doctors')
@login_required
def doctors():
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取搜索参数
    search_keyword = request.args.get('search', '').strip()
    
    if search_keyword:
        # 根据医生ID或用户名搜索医生
        cursor.execute("SELECT id, username, real_name, department, title, phone, role, created_at FROM users WHERE role = 'doctor' AND (id LIKE %s OR username LIKE %s)", (f"%{search_keyword}%", f"%{search_keyword}%"))
    else:
        # 获取所有医生
        cursor.execute("SELECT id, username, real_name, department, title, phone, role, created_at FROM users WHERE role = 'doctor'")
    
    doctors = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('doctors.html', doctors=doctors, search_keyword=search_keyword)

# 添加医生路由（仅管理员）
@app.route('/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        real_name = request.form['real_name']
        department = request.form['department']
        title = request.form['title']
        phone = request.form['phone']
        
        # 哈希密码
        hashed_password = hash_password(password)
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        try:
            # 插入医生数据
            cursor.execute("""
                INSERT INTO users (username, password, real_name, department, title, phone, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (username, hashed_password, real_name, department, title, phone, 'doctor'))
            
            db.commit()
            flash('医生添加成功！', 'success')
            return redirect(url_for('doctors'))
        except mysql.connector.Error as err:
            flash(f'添加医生失败: {err}', 'danger')
        finally:
            cursor.close()
            db.close()
    
    return render_template('add_doctor.html')

# 删除医生路由（仅管理员）
@app.route('/delete_doctor/<int:doctor_id>', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # 检查医生是否存在
        cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'doctor'", (doctor_id,))
        doctor = cursor.fetchone()
        
        if not doctor:
            flash('医生不存在！', 'danger')
            return redirect(url_for('doctors'))
        
        # 删除医生
        cursor.execute("DELETE FROM users WHERE id = %s AND role = 'doctor'", (doctor_id,))
        
        # 更新所有大于被删除ID的记录的ID，实现ID顺延
        cursor.execute("UPDATE users SET id = id - 1 WHERE id > %s AND role = 'doctor'", (doctor_id,))
        
        db.commit()
        flash('医生删除成功！', 'success')
    except mysql.connector.Error as err:
        flash(f'删除医生失败: {err}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('doctors'))

# 病人管理路由
@app.route('/patients')
@login_required
def patients():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取搜索参数
    search_keyword = request.args.get('search', '').strip()
    
    if search_keyword:
        # 根据姓名搜索病人
        cursor.execute("SELECT * FROM patients WHERE name LIKE %s ORDER BY id DESC", (f"%{search_keyword}%",))
    else:
        # 获取所有病人
        cursor.execute("SELECT * FROM patients ORDER BY id DESC")
    
    patients = cursor.fetchall()
    cursor.close()
    db.close()
    
    # 检查是否有重复姓名的病人
    has_duplicate_names = False
    if search_keyword and len(patients) > 1:
        name_count = {}
        for patient in patients:
            if patient['name'] in name_count:
                name_count[patient['name']] += 1
            else:
                name_count[patient['name']] = 1
        
        # 检查是否有重复姓名
        for count in name_count.values():
            if count > 1:
                has_duplicate_names = True
                break
    
    return render_template('patients.html', patients=patients, search_keyword=search_keyword, has_duplicate_names=has_duplicate_names)

# 添加病人路由
@app.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        name = request.form['name']
        gender = request.form['gender']
        age = request.form['age']
        birthday = request.form['birthday'] if request.form['birthday'] else None
        phone = request.form['phone'] if request.form['phone'] else None
        address = request.form['address'] if request.form['address'] else None
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        try:
            # 插入病人数据
            cursor.execute("""
                INSERT INTO patients (patient_id, name, gender, age, birthday, phone, address, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (patient_id, name, gender, age, birthday, phone, address))
            
            db.commit()
            flash('病人添加成功！', 'success')
            return redirect(url_for('patients'))
        except mysql.connector.Error as err:
            flash(f'添加病人失败: {err}', 'danger')
        finally:
            cursor.close()
            db.close()
    
    return render_template('add_patient.html')

# 删除病人路由
@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # 检查病人是否存在
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        
        if not patient:
            flash('病人不存在！', 'danger')
            return redirect(url_for('patients'))
        
        # 删除病人
        cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        
        # 更新所有大于被删除ID的记录的ID，实现ID顺延
        cursor.execute("UPDATE patients SET id = id - 1 WHERE id > %s", (patient_id,))
        
        db.commit()
        flash('病人删除成功！', 'success')
    except mysql.connector.Error as err:
        flash(f'删除病人失败: {err}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('patients'))

# 诊断记录路由
@app.route('/diagnoses/<int:patient_id>')
@login_required
def diagnoses(patient_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取病人信息
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    
    # 获取诊断记录
    cursor.execute("""
        SELECT d.*, u.username as doctor_name
        FROM diagnoses d
        LEFT JOIN users u ON d.doctor_id = u.id
        WHERE d.patient_id = %s
        ORDER BY d.diagnosis_date DESC
    """, (patient_id,))
    diagnoses = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('diagnoses.html', patient=patient, diagnoses=diagnoses)

# 图片上传路由
@app.route('/upload_image/<int:diagnosis_id>', methods=['POST'])
@login_required
def upload_image(diagnosis_id):
    if 'image' not in request.files:
        flash('没有选择图片！', 'danger')
        # 获取该诊断记录的病人ID
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT patient_id FROM diagnoses WHERE id = %s", (diagnosis_id,))
        diagnosis = cursor.fetchone()
        cursor.close()
        db.close()
        if diagnosis:
            return redirect(url_for('diagnoses', patient_id=diagnosis['patient_id']))
        return redirect(url_for('main_interface'))
    
    file = request.files['image']
    if file.filename == '':
        flash('没有选择图片！', 'danger')
        # 获取该诊断记录的病人ID
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT patient_id FROM diagnoses WHERE id = %s", (diagnosis_id,))
        diagnosis = cursor.fetchone()
        cursor.close()
        db.close()
        if diagnosis:
            return redirect(url_for('diagnoses', patient_id=diagnosis['patient_id']))
        return redirect(url_for('main_interface'))
    
    if file:
        try:
            # 创建图片存储目录（如果不存在）
            upload_dir = "static/uploaded_images"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # 生成唯一的文件名
            filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            file_path = os.path.join(upload_dir, filename)
            
            # 保存图片
            file.save(file_path)
            
            # 将图片信息存入数据库
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO images (diagnosis_id, file_path, uploaded_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, (diagnosis_id, filename))
            db.commit()
            
            # 获取该诊断记录的病人ID和病人姓名
            cursor.execute("""
                SELECT p.name as patient_name
                FROM diagnoses d
                JOIN patients p ON d.patient_id = p.id
                WHERE d.id = %s
            """, (diagnosis_id,))
            diagnosis_info = cursor.fetchone()
            
            cursor.close()
            db.close()
            
            if diagnosis_info:
                # 发送通知
                send_notification(
                    user_id=current_user.id,
                    notification_type='image_upload',
                    title='图片上传成功',
                    content=f'您已成功为病人 {diagnosis_info["patient_name"]} 的诊断记录上传了一张图片',
                    related_id=diagnosis_id
                )
            
            flash('图片上传成功！', 'success')
        except Exception as err:
            flash(f'图片上传失败: {err}', 'danger')
    
    # 获取该诊断记录的病人ID用于重定向
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT patient_id FROM diagnoses WHERE id = %s", (diagnosis_id,))
    diagnosis = cursor.fetchone()
    cursor.close()
    db.close()
    
    if diagnosis:
        return redirect(url_for('diagnoses', patient_id=diagnosis['patient_id']))
    return redirect(url_for('main_interface'))

# 删除诊断记录路由
@app.route('/delete_diagnosis/<int:diagnosis_id>', methods=['POST'])
@login_required
def delete_diagnosis(diagnosis_id):
    try:
        # 获取该诊断记录的病人ID和创建者ID
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT patient_id, doctor_id FROM diagnoses WHERE id = %s", (diagnosis_id,))
        diagnosis = cursor.fetchone()
        
        if diagnosis:
            patient_id = diagnosis['patient_id']
            
            # 权限检查：只有管理员或记录创建者才能删除
            if current_user.role == 'admin' or current_user.id == diagnosis['doctor_id']:
                # 删除诊断记录（级联删除相关图片）
                cursor.execute("DELETE FROM diagnoses WHERE id = %s", (diagnosis_id,))
                # 更新所有大于被删除ID的记录的ID，实现ID顺延
                cursor.execute("UPDATE diagnoses SET id = id - 1 WHERE id > %s", (diagnosis_id,))
                db.commit()
                flash('诊断记录删除成功！', 'success')
            else:
                flash('您没有权限删除此诊断记录！', 'danger')
            
            return redirect(url_for('diagnoses', patient_id=patient_id))
        else:
            flash('诊断记录不存在！', 'danger')
            return redirect(url_for('main_interface'))
    except Exception as err:
        flash(f'删除诊断记录失败: {err}', 'danger')
        return redirect(url_for('main_interface'))
    finally:
        cursor.close()
        db.close()

# 添加诊断记录路由
@app.route('/add_diagnosis/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def add_diagnosis(patient_id):
    # 获取当前日期
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        diagnosis_type = request.form['diagnosis_type']
        tumor_type = request.form['tumor_type']
        tumor_stage = request.form['tumor_stage']
        diagnosis_date_str = request.form['diagnosis_date']
        diagnosis_content = request.form['diagnosis_content']
        treatment_plan = request.form['treatment_plan']
        examination_results = request.form['examination_results']
        notes = request.form['notes']
        
        # 转换诊断日期为datetime格式
        diagnosis_date = datetime.strptime(diagnosis_date_str, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # 获取病人信息
        cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        
        try:
            cursor.execute("""
                INSERT INTO diagnoses (patient_id, doctor_id, diagnosis_date, diagnosis_type, tumor_type, 
                                      tumor_stage, diagnosis_content, treatment_plan, examination_results, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (patient_id, current_user.id, diagnosis_date, diagnosis_type, tumor_type, 
                  tumor_stage, diagnosis_content, treatment_plan, examination_results, notes))
            
            diagnosis_id = cursor.lastrowid
            db.commit()
            
            # 发送新诊断记录通知
            # 1. 发送给创建者自己
            send_notification(
                user_id=current_user.id,
                notification_type='new_diagnosis',
                title='诊断记录已创建',
                content=f'您已成功创建病人 {patient["name"]} 的诊断记录',
                related_id=diagnosis_id
            )
            
            # 2. 发送给其他所有医生（如果需要的话）
            # 这里可以扩展，例如发送给相关团队或特定医生
            
            flash('诊断记录添加成功！', 'success')
            return redirect(url_for('diagnoses', patient_id=patient_id))
        except mysql.connector.Error as err:
            flash(f'添加诊断记录失败: {err}', 'danger')
        finally:
            cursor.close()
            db.close()
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    db.close()
    
    return render_template('add_diagnosis.html', patient=patient, today=today)

# 查看诊断图片路由
@app.route('/view_images/<int:diagnosis_id>')
@login_required
def view_images(diagnosis_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # 获取诊断记录信息
        cursor.execute("""
            SELECT d.*, p.name as patient_name 
            FROM diagnoses d 
            JOIN patients p ON d.patient_id = p.id 
            WHERE d.id = %s
        """, (diagnosis_id,))
        diagnosis = cursor.fetchone()
        
        if not diagnosis:
            flash('诊断记录不存在！', 'danger')
            return redirect(url_for('main_interface'))
        
        # 获取该诊断记录的所有图片
        cursor.execute("SELECT * FROM images WHERE diagnosis_id = %s", (diagnosis_id,))
        images = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        return render_template('view_images.html', diagnosis=diagnosis, images=images)
    except Exception as err:
        # 发生异常时，仍然渲染页面并显示错误信息
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.*, p.name as patient_name 
            FROM diagnoses d 
            JOIN patients p ON d.patient_id = p.id 
            WHERE d.id = %s
        """, (diagnosis_id,))
        diagnosis = cursor.fetchone()
        cursor.close()
        db.close()
        
        return render_template('view_images.html', diagnosis=diagnosis, images=[])

# 待办任务路由
@app.route('/todos')
@login_required
def todos():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取未读通知数量
    cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = FALSE", (current_user.id,))
    unread_notifications = cursor.fetchone()['count']
    
    if current_user.role == 'admin':
        # 管理员可以查看所有待办任务
        cursor.execute("""
            SELECT t.*, u.username as assignee_name, u2.username as assigner_name
            FROM todos t
            JOIN users u ON t.assignee_id = u.id
            JOIN users u2 ON t.assigner_id = u2.id
            ORDER BY t.is_completed ASC, t.due_date ASC
        """)
    else:
        # 普通医生只能查看分配给自己的待办任务
        cursor.execute("""
            SELECT t.*, u.username as assignee_name, u2.username as assigner_name
            FROM todos t
            JOIN users u ON t.assignee_id = u.id
            JOIN users u2 ON t.assigner_id = u2.id
            WHERE t.assignee_id = %s
            ORDER BY t.is_completed ASC, t.due_date ASC
        """, (current_user.id,))
    
    todos = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('todos.html', todos=todos, unread_notifications=unread_notifications)

# 添加待办任务路由
@app.route('/add_todo', methods=['GET', 'POST'])
@login_required
def add_todo():
    try:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            due_date_str = request.form['due_date']
            assignee_id = request.form['assignee_id']
            
            # 转换截止日期格式
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            # 插入待办任务
            cursor.execute("""
                INSERT INTO todos (title, content, assigner_id, assignee_id, due_date, is_completed, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (title, content, current_user.id, assignee_id, due_date, 0))
            
            todo_id = cursor.lastrowid
            db.commit()
            
            # 发送通知给任务负责人
            send_notification(
                user_id=assignee_id,
                notification_type='todo',
                title='新的待办任务',
                content=f'您有一个新的待办任务：{title}',
                related_id=todo_id
            )
            
            cursor.close()
            db.close()
            
            flash('待办任务发布成功！', 'success')
            return redirect(url_for('todos'))
        else:
            # GET请求，显示添加待办任务表单
            db = get_db()
            cursor = db.cursor(dictionary=True)
            
            # 获取所有医生（包含真实姓名）
            cursor.execute("SELECT id, username, real_name FROM users WHERE role = 'doctor' ORDER BY username")
            doctors = cursor.fetchall()
            
            cursor.close()
            db.close()
            
            return render_template('add_todo.html', doctors=doctors)
    except Exception as err:
        flash(f'发布待办任务失败: {err}', 'danger')
        return redirect(url_for('todos'))

# 标记待办任务完成路由
@app.route('/complete_todo/<int:todo_id>', methods=['POST'])
@login_required
def complete_todo(todo_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # 检查任务是否存在且属于当前用户
        cursor.execute("""
            SELECT * FROM todos WHERE id = %s AND assignee_id = %s
        """, (todo_id, current_user.id))
        todo = cursor.fetchone()
        
        if not todo:
            flash('待办任务不存在或您没有权限操作！', 'danger')
            return redirect(url_for('todos'))
        
        # 标记任务完成
        cursor.execute("""
            UPDATE todos SET is_completed = TRUE, completed_at = CURRENT_TIMESTAMP WHERE id = %s
        """, (todo_id,))
        db.commit()
        
        cursor.close()
        db.close()
        
        flash('待办任务已标记完成！', 'success')
        return redirect(url_for('todos'))
    except Exception as err:
        flash(f'标记任务完成失败: {err}', 'danger')
        return redirect(url_for('todos'))

# 修改病人路由（仅管理员）
@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取病人信息
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    
    if not patient:
        flash('病人不存在！', 'danger')
        return redirect(url_for('patients'))
    
    if request.method == 'POST':
        patient_id_new = request.form['patient_id']
        name = request.form['name']
        gender = request.form['gender']
        age = request.form['age']
        birthday = request.form['birthday'] if request.form['birthday'] else None
        phone = request.form['phone'] if request.form['phone'] else None
        address = request.form['address'] if request.form['address'] else None
        
        try:
            cursor.execute("""
                UPDATE patients 
                SET patient_id = %s, name = %s, gender = %s, age = %s, birthday = %s, phone = %s, address = %s
                WHERE id = %s
            """, (patient_id_new, name, gender, age, birthday, phone, address, patient_id))
            
            db.commit()
            flash('病人信息修改成功！', 'success')
            return redirect(url_for('patients'))
        except mysql.connector.Error as err:
            flash(f'修改病人失败: {err}', 'danger')
        finally:
            cursor.close()
            db.close()
    
    cursor.close()
    db.close()
    
    return render_template('edit_patient.html', patient=patient)

# 修改医生路由（仅管理员）
@app.route('/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取医生信息
    cursor.execute("SELECT id, username, real_name, department, title, phone FROM users WHERE id = %s AND role = 'doctor'", (doctor_id,))
    doctor = cursor.fetchone()
    
    if not doctor:
        flash('医生不存在！', 'danger')
        return redirect(url_for('doctors'))
    
    if request.method == 'POST':
        username = request.form['username']
        real_name = request.form['real_name']
        department = request.form['department']
        title = request.form['title']
        phone = request.form['phone']
        password = request.form['password']
        
        try:
            if password:
                # 修改密码
                hashed_password = hash_password(password)
                cursor.execute("""
                    UPDATE users 
                    SET username = %s, real_name = %s, department = %s, title = %s, phone = %s, password = %s
                    WHERE id = %s AND role = 'doctor'
                """, (username, real_name, department, title, phone, hashed_password, doctor_id))
            else:
                # 不修改密码
                cursor.execute("""
                    UPDATE users 
                    SET username = %s, real_name = %s, department = %s, title = %s, phone = %s
                    WHERE id = %s AND role = 'doctor'
                """, (username, real_name, department, title, phone, doctor_id))
            
            db.commit()
            flash('医生信息修改成功！', 'success')
            return redirect(url_for('doctors'))
        except mysql.connector.Error as err:
            flash(f'修改医生失败: {err}', 'danger')
        finally:
            cursor.close()
            db.close()
    
    cursor.close()
    db.close()
    
    return render_template('edit_doctor.html', doctor=doctor)

if __name__ == '__main__':
    # 确保上传目录存在
    if not os.path.exists('static'):
        os.makedirs('static')
    if not os.path.exists('static/uploaded_images'):
        os.makedirs('static/uploaded_images')
    
    app.run(debug=True)