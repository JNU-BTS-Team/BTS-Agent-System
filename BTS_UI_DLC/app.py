from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
import json
import hashlib
import base64
import hmac
import os
import uuid
from datetime import datetime, timedelta
try:
    import paramiko  # 用于SSH远程执行
except Exception:
    paramiko = None

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于会话管理的密钥

# MySQL数据库配置
app.config['MYSQL_HOST'] = (os.environ.get('DLC_MYSQL_HOST') or os.environ.get('MYSQL_HOST') or 'localhost').strip()
app.config['MYSQL_USER'] = (os.environ.get('DLC_MYSQL_USER') or os.environ.get('MYSQL_USER') or 'appuser').strip()
app.config['MYSQL_PASSWORD'] = (os.environ.get('DLC_MYSQL_PASSWORD') or os.environ.get('MYSQL_PASSWORD') or '123456')
app.config['MYSQL_DB'] = (os.environ.get('DLC_MYSQL_DB') or os.environ.get('MYSQL_DB') or 'SECD2').strip()

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
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
    except mysql.connector.Error:
        return None
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

def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('utf-8')

def _b64url_decode(text: str) -> bytes:
    raw = (text or '').encode('utf-8')
    pad = b'=' * ((4 - (len(raw) % 4)) % 4)
    return base64.urlsafe_b64decode(raw + pad)

def _verify_sso_token(token: str) -> dict:
    secret = (os.environ.get('BTS_SSO_SECRET') or 'bts_sso_demo').encode('utf-8')
    parts = (token or '').split('.', 1)
    if len(parts) != 2:
        return {}
    data, sig = parts
    expected = _b64url_encode(hmac.new(secret, data.encode('utf-8'), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig):
        return {}
    try:
        payload = json.loads(_b64url_decode(data).decode('utf-8'))
    except Exception:
        return {}
    ts = int(payload.get('ts') or 0)
    if ts <= 0:
        return {}
    if abs(int(datetime.now().timestamp()) - ts) > 300:
        return {}
    return payload if isinstance(payload, dict) else {}

def _derive_ui_base_url() -> str:
    override = (os.environ.get('BTS_UI_BASE_URL') or '').strip()
    if override:
        return override.rstrip('/')
    try:
        host = (request.host or '127.0.0.1').split(':')[0]
        scheme = request.scheme or 'http'
        return f"{scheme}://{host}:5000"
    except Exception:
        return "http://127.0.0.1:5000"

def _ui_patient_url() -> str:
    return f"{_derive_ui_base_url()}/patient_portal"

@app.route('/sso')
def sso_login():
    token = (request.args.get('token') or '').strip()
    payload = _verify_sso_token(token)
    username = (payload.get('u') or '').strip()
    if not username:
        return redirect(url_for('login'))
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, username, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
    except mysql.connector.Error:
        return redirect(url_for('login'))
    if not user:
        return redirect(url_for('login'))
    login_user(User(user['id'], user['username'], user['role']))
    return redirect(url_for('main_interface'))

def load_first_text_file(candidate_paths):
    for candidate in candidate_paths:
        path_value = (candidate or '').strip()
        if not path_value:
            continue
        try:
            with open(path_value, 'r', encoding='utf-8') as f:
                return f.read(), path_value
        except (OSError, UnicodeDecodeError):
            continue
    return '', ''

def build_figma_candidates(env_keys, fallback_names):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    for key in env_keys:
        value = os.environ.get(key)
        if value and value.strip():
            candidates.append(value.strip())
    for name in fallback_names:
        candidates.extend([
            os.path.join(base_dir, 'UI', name),
            os.path.join(base_dir, 'ui', name),
            os.path.join(base_dir, 'figma', name),
            os.path.join(base_dir, name),
        ])
    return candidates

def ensure_users_columns():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users'
        """, (app.config['MYSQL_DB'],))
        existing_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        required_columns = {
            "real_name": "VARCHAR(100) NULL",
            "department": "VARCHAR(100) NULL",
            "title": "VARCHAR(100) NULL",
            "phone": "VARCHAR(30) NULL"
        }
        for column_name, column_def in required_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
        db.commit()
        cursor.close()
        db.close()
    except Exception as err:
        print(f"补齐users字段失败: {err}")

ensure_users_columns()

def ensure_todos_schema():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'todos'
        """, (app.config['MYSQL_DB'],))
        todos_exists = cursor.fetchone()['count'] > 0
        if not todos_exists:
            cursor.execute("""
                CREATE TABLE todos (
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
                )
            """)
        else:
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'todos'
            """, (app.config['MYSQL_DB'],))
            existing_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
            column_defs = {
                "title": "VARCHAR(100) NOT NULL",
                "content": "TEXT NOT NULL",
                "assigner_id": "INT NOT NULL",
                "assignee_id": "INT NOT NULL",
                "due_date": "DATE NOT NULL",
                "is_completed": "BOOLEAN DEFAULT FALSE",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "completed_at": "TIMESTAMP NULL"
            }
            for column_name, column_def in column_defs.items():
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE todos ADD COLUMN {column_name} {column_def}")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'notifications'
        """, (app.config['MYSQL_DB'],))
        notifications_exists = cursor.fetchone()['count'] > 0
        if not notifications_exists:
            cursor.execute("""
                CREATE TABLE notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    type ENUM('new_diagnosis', 'follow_up', 'todo') NOT NULL,
                    title VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    related_id INT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        else:
            cursor.execute("""
                SELECT COLUMN_TYPE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'notifications' AND COLUMN_NAME = 'type'
            """, (app.config['MYSQL_DB'],))
            row = cursor.fetchone()
            if row and 'todo' not in row['COLUMN_TYPE']:
                cursor.execute("""
                    ALTER TABLE notifications
                    MODIFY COLUMN type ENUM('new_diagnosis', 'follow_up', 'todo') NOT NULL
                """)
        db.commit()
        cursor.close()
        db.close()
    except Exception as err:
        print(f"补齐待办表失败: {err}")

ensure_todos_schema()

def ensure_demo_doctors():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            UPDATE users u
            LEFT JOIN users x
                ON x.username = CONCAT('doctor', SUBSTRING(u.username, 7))
            SET u.username = CONCAT('doctor', SUBSTRING(u.username, 7))
            WHERE u.role = 'doctor'
              AND u.username LIKE 'docter%'
              AND x.id IS NULL
        """)
        cursor.execute("""
            DELETE u
            FROM users u
            INNER JOIN users d
                ON d.username = CONCAT('doctor', SUBSTRING(u.username, 7))
               AND d.role = 'doctor'
            WHERE u.role = 'doctor'
              AND u.username LIKE 'docter%'
        """)
        cursor.execute("""
            SELECT id, username
            FROM users
            WHERE role = 'doctor' AND (username LIKE 'doctor%' OR username LIKE 'docter%')
        """)
        existing_rows = cursor.fetchall()
        existing_map = {row['username']: row['id'] for row in existing_rows}
        surnames = ['王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高', '林']
        given_names = [
            '伟', '磊', '洋', '勇', '军', '杰', '涛', '明', '超', '峰', '鹏', '强', '鑫', '波', '斌', '宁',
            '静', '丽', '敏', '艳', '娟', '萍', '婷', '雪', '莉', '芳', '娜', '倩', '晶', '琳', '颖', '洁'
        ]
        departments = [
            '神经肿瘤科',
            '脑膜瘤专病门诊',
            '胶质瘤诊疗中心',
            '垂体瘤诊疗组',
            '听神经瘤专科',
            '肿瘤放疗科',
            '肿瘤内科'
        ]
        titles = ['住院医师', '主治医师', '副主任医师', '主任医师']
        base_date = datetime.now() - timedelta(days=89)
        hashed_password = hash_password('123456')
        phone_prefixes = ['139', '138', '137', '136', '135', '150', '151', '152', '157', '158', '159', '186', '187', '188']
        for idx in range(1, 115):
            username = f"doctor{idx}"
            legacy_username = f"docter{idx}"
            surname = surnames[(idx - 1) % len(surnames)]
            given_1 = given_names[(idx * 7 + 3) % len(given_names)]
            given_2 = given_names[(idx * 11 + 5) % len(given_names)]
            if idx % 3 == 0:
                real_name = f"{surname}{given_1}"
            else:
                real_name = f"{surname}{given_1}{given_2}"
            department = departments[(idx - 1) % len(departments)]
            title = titles[(idx - 1) % len(titles)]
            prefix = phone_prefixes[(idx - 1) % len(phone_prefixes)]
            phone_tail = ((10000000 + idx * 7919) % 90000000) + 10000000
            phone = f"{prefix}{phone_tail:08d}"
            day_offset = int(((idx - 1) / 111) * 89)
            created_at = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d %H:%M:%S')
            if username in existing_map:
                cursor.execute("""
                    UPDATE users
                    SET real_name = %s, department = %s, title = %s, phone = %s, role = 'doctor'
                    WHERE id = %s
                """, (real_name, department, title, phone, existing_map[username]))
            elif legacy_username in existing_map:
                cursor.execute("""
                    UPDATE users
                    SET username = %s, real_name = %s, department = %s, title = %s, phone = %s, role = 'doctor'
                    WHERE id = %s
                """, (username, real_name, department, title, phone, existing_map[legacy_username]))
            else:
                cursor.execute("""
                    INSERT INTO users (username, password, real_name, department, title, phone, role, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'doctor', %s)
                """, (username, hashed_password, real_name, department, title, phone, created_at))
        db.commit()
        cursor.close()
        db.close()
    except Exception as err:
        print(f"初始化演示医生失败: {err}")

ensure_demo_doctors()

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
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            db.close()
        except mysql.connector.Error:
            flash('数据库连接失败，请先启动 MySQL 服务后再登录。', 'danger')
            return render_template('login.html')
        
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
    figma_html = ''
    candidates = build_figma_candidates(
        env_keys=[
            'BTS_DLC_MAIN_FIGMA_PATH',
            'DLC_MAIN_FIGMA_PATH',
            'DLC_FIGMA_MAIN_PATH',
        ],
        fallback_names=['test3.txt', 'main_interface.txt'],
    )
    figma_html, figma_path_used = load_first_text_file(candidates)
    if not figma_html:
        print(f"[DLC] 未找到主界面 Figma 导出文件，候选路径: {candidates}")
    else:
        figma_html = figma_html.replace('>肿瘤</div>', '>端侧脑瘤病历系统</div>', 1)
        figma_html = figma_html.replace(
            'left: 920px; top: 24px; position: absolute; text-align: center; color: white; font-size: 38px; font-family: Abhaya Libre SemiBold; font-weight: 600; letter-spacing: 7.60px; word-wrap: break-word',
            'left: 50%; top: 24px; position: absolute; transform: translateX(-50%); text-align: center; white-space: nowrap; color: white; font-size: 38px; font-family: Abhaya Libre SemiBold; font-weight: 600; letter-spacing: 2px; word-wrap: break-word',
            1
        )
        figma_html = figma_html.replace('data-layer="data-layer="todo-panel-mask""', 'data-layer="todo-panel-mask"')
        figma_html = figma_html.replace('data-layer="data-layer="todo-panel-scroll""', 'data-layer="todo-panel-scroll"')
        figma_html = figma_html.replace('data-layer="data-layer="todo-panel-scroll"', 'data-layer="todo-panel-scroll"')
        figma_html = figma_html.replace('data-layer="data-layer="todo-card-item""', 'data-layer="todo-card-item"')
        figma_html = figma_html.replace('data-layer="data-layer="todo-card-item"', 'data-layer="todo-card-item"')

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

    # 医生人数
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'doctor'")
    total_doctors = cursor.fetchone()['total']

    # 待办任务统计
    cursor.execute("SELECT COUNT(*) as total FROM todos")
    total_todos = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM todos WHERE is_completed = TRUE")
    completed_todos = cursor.fetchone()['total']
    pending_todos = max(0, total_todos - completed_todos)
    
    # 本月诊断数
    cursor.execute("SELECT COUNT(*) as total FROM diagnoses WHERE DATE_FORMAT(diagnosis_date, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')")
    monthly_diagnoses = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM diagnoses WHERE DATE(diagnosis_date) = CURDATE()")
    today_diagnoses = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM todos WHERE is_completed = FALSE AND due_date < CURDATE()")
    overdue_todos = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM notifications")
    total_notifications = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as total FROM notifications WHERE user_id = %s AND is_read = FALSE", (current_user.id,))
    unread_notifications = cursor.fetchone()['total']
    cursor.execute("""
        SELECT t.title, t.due_date, u.username as assignee_name
        FROM todos t
        JOIN users u ON t.assignee_id = u.id
        WHERE t.is_completed = FALSE
        ORDER BY t.due_date ASC, t.created_at DESC
        LIMIT 3
    """)
    todo_alert_rows = cursor.fetchall()

    # 近24日诊断趋势（用于主界面柱状图）
    today = datetime.now().date()
    start_day = today - timedelta(days=23)
    cursor.execute("""
        SELECT DATE(diagnosis_date) as day, COUNT(*) as count
        FROM diagnoses
        WHERE diagnosis_date >= %s
        GROUP BY DATE(diagnosis_date)
        ORDER BY day
    """, (start_day,))
    recent_rows = cursor.fetchall()
    recent_dict = {}
    for row in recent_rows:
        day_value = row.get('day')
        if isinstance(day_value, datetime):
            day_key = day_value.date().isoformat()
        else:
            day_key = str(day_value)
        recent_dict[day_key] = int(row.get('count') or 0)

    recent_24_counts = []
    for offset in range(24):
        target_day = start_day + timedelta(days=offset)
        recent_24_counts.append(recent_dict.get(target_day.isoformat(), 0))
    
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

    # 远程推理结果图片数量（近似代表远程推理执行次数）
    remote_result_count = 0
    try:
        static_folder = app.static_folder or ''
        remote_result_count = len([
            name for name in os.listdir(static_folder)
            if name.startswith('remote_result_') and name.endswith('.png')
        ])
    except OSError:
        remote_result_count = 0

    def safe_percent(numerator, denominator):
        if denominator <= 0:
            return 0
        ratio = int(round((numerator / denominator) * 100))
        return max(0, min(99, ratio))

    def compact_metric(value):
        number = int(value or 0)
        if number >= 1000:
            return f"{round(number / 1000, 1)}k"
        return str(number)

    diagnosis_coverage = safe_percent(total_diagnoses, total_patients if total_patients > 0 else 1)
    monthly_contribution = safe_percent(monthly_diagnoses, total_diagnoses if total_diagnoses > 0 else 1)
    image_coverage = safe_percent(total_images, total_diagnoses if total_diagnoses > 0 else 1)
    todo_completion = safe_percent(completed_todos, total_todos if total_todos > 0 else 1)
    active_day_rate = safe_percent(sum(1 for value in recent_24_counts if value > 0), 24)

    sparse_data_mode = (total_patients + total_diagnoses + total_images + total_todos + remote_result_count) <= 8
    
    # 强制使任务概览数据为指定值（无论是否是 sparse_data_mode）
    effective_total_todos = 128
    effective_completed_todos = int(128 * 0.96) # 122
    effective_pending_todos = 128 - effective_completed_todos # 6
    todo_completion_display = 96

    if sparse_data_mode:
        bar_values = [12, 18, 15, 21, 17, 24, 19, 22, 26, 20, 23, 28, 25, 31, 27, 29, 33, 30, 35, 32, 34, 37, 36, 39]
    else:
        bar_values = recent_24_counts

    effective_patients = max(total_patients, 128 if sparse_data_mode else total_patients)
    effective_diagnoses = max(total_diagnoses, 286 if sparse_data_mode else total_diagnoses)
    effective_images = max(total_images, 244 if sparse_data_mode else total_images)
    effective_remote_results = max(remote_result_count, 48 if sparse_data_mode else remote_result_count)
    effective_doctors = max(total_doctors, 12 if sparse_data_mode else total_doctors)
    effective_monthly = max(monthly_diagnoses, 36 if sparse_data_mode else monthly_diagnoses)

    diagnosis_coverage_display = max(diagnosis_coverage, 92 if sparse_data_mode else diagnosis_coverage)
    monthly_contribution_display = max(monthly_contribution, 88 if sparse_data_mode else monthly_contribution)
    image_coverage_display = max(image_coverage, 91 if sparse_data_mode else image_coverage)

    active_day_rate_display = max(active_day_rate, 84 if sparse_data_mode else active_day_rate)

    if any([diagnosis_coverage, image_coverage, todo_completion, active_day_rate]):
        system_health = int(round(0.25 * diagnosis_coverage_display + 0.3 * image_coverage_display + 0.25 * todo_completion_display + 0.2 * active_day_rate_display))
        system_health = max(86, min(99, system_health))
    else:
        system_health = 92

    dashboard_overview = {
        "date_label": datetime.now().strftime('%Y年%m月%d日'),
        "left_title": "病例全周期管理",
        "left_description": "覆盖建档、诊断、影像归档与协同，形成可追溯临床数据闭环。",
        "right_title": "远程推理评估",
        "right_description": "支持 .nii 上传与 SSH 调度推理，结果回传后用于可视化分析。",
        "center_percent": system_health,
        "center_status": "核心系统在线" if system_health >= 90 else "系统监测中",
        "bar_title": "近24日推理任务量"
    }

    module_cards = [
        {"title": "病例管理", "percent": diagnosis_coverage_display, "value": compact_metric(effective_patients)},
        {"title": "诊断记录", "percent": monthly_contribution_display, "value": compact_metric(effective_diagnoses)},
        {"title": "影像归档", "percent": image_coverage_display, "value": compact_metric(effective_images)},
        {"title": "远程推理", "percent": active_day_rate_display, "value": compact_metric(effective_remote_results)},
        {"title": "医患协同", "percent": todo_completion_display, "value": compact_metric(effective_doctors)},
        {"title": "智能评估", "percent": system_health, "value": compact_metric(effective_monthly)}
    ]

    task_publish_data = {
        "title": "系统任务概览",
        "cards": [
            {"container": "已预订", "value": compact_metric(effective_total_todos), "label": "任务总量"},
            {"container": "会议使用率", "value": f"{todo_completion_display}%", "label": "完成率"},
            {"container": "已开会议", "value": compact_metric(effective_completed_todos), "label": "已完成"},
            {"container": "待开会议", "value": compact_metric(effective_pending_todos), "label": "待处理"}
        ],
        "categories": [
            {"label": "病例建档", "value": effective_patients},
            {"label": "诊断录入", "value": effective_diagnoses},
            {"label": "影像归档", "value": effective_images},
            {"label": "远程推理", "value": effective_remote_results},
            {"label": "智能评估", "value": 96},
            {"label": "协同随访", "value": 212}
        ]
    }

    warning_items = []
    for row in todo_alert_rows:
        due_date = row.get('due_date')
        if isinstance(due_date, datetime):
            due_text = due_date.strftime('%m.%d 23:59')
        else:
            due_text = str(due_date)[5:].replace('-', '.') + " 23:59" if due_date else datetime.now().strftime('%m.%d %H:%M')
        warning_items.append({
            "message": f"待办：{(row.get('title') or '未命名任务')[:16]}（{row.get('assignee_name') or '未分配'}）",
            "time": due_text
        })
    if len(warning_items) < 3:
        warning_items.append({"message": f"逾期待办：{overdue_todos} 条", "time": datetime.now().strftime('%m.%d %H:%M')})
    if len(warning_items) < 3:
        warning_items.append({"message": f"今日新增诊断：{today_diagnoses} 例", "time": datetime.now().strftime('%m.%d %H:%M')})
    if len(warning_items) < 3:
        warning_items.append({"message": f"未读通知：{unread_notifications} 条", "time": datetime.now().strftime('%m.%d %H:%M')})

    warning_overview = {
        "title": "系统预警",
        "rings": [
            {"container": "待处理", "label": "待处理任务", "value": compact_metric(effective_pending_todos)},
            {"container": "处理率", "label": "逾期任务", "value": compact_metric(overdue_todos)},
            {"container": "历史总数", "label": "任务完成率", "value": f"{todo_completion_display}%"}
        ],
        "items": warning_items[:3],
        "summary": {
            "today_diagnoses": today_diagnoses,
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications
        }
    }
    
    # 提取月份和数量用于图表
    months = [data['month'] for data in chart_data]
    counts = [data['count'] for data in chart_data]
    
    return render_template('main_interface.html', 
                           total_patients=total_patients,
                           total_diagnoses=total_diagnoses,
                           total_images=total_images,
                           total_doctors=total_doctors,
                           total_todos=effective_total_todos,
                           completed_todos=effective_completed_todos,
                           pending_todos=effective_pending_todos,
                           monthly_diagnoses=monthly_diagnoses,
                           dashboard_overview=dashboard_overview,
                           module_cards=module_cards,
                           task_publish_data=task_publish_data,
                           warning_overview=warning_overview,
                           bar_values=bar_values,
                           chart_data=chart_data,
                           months=months,
                           counts=counts,
                           ui_patient_url=_ui_patient_url(),
                           figma_html=figma_html)

@app.route('/team_management')
@login_required
def team_management():
    figma_html = ''
    doctors = []
    ensure_demo_doctors()
    candidates = build_figma_candidates(
        env_keys=[
            'BTS_DLC_TEAM_FIGMA_PATH',
            'DLC_TEAM_FIGMA_PATH',
            'DLC_FIGMA_TEAM_PATH',
        ],
        fallback_names=['page_test3.txt', 'team_management.txt'],
    )
    figma_html, figma_path_used = load_first_text_file(candidates)
    if not figma_html:
        print(f"[DLC] 未找到医生中心 Figma 导出文件，候选路径: {candidates}")
    else:
        replacements = [
            ('月度受理工单概况', '月度受理病例情况'),
            ('受理工单总数', '月度受理总量'),
            ('待处理 10%', '待处理'),
            ('待受理 10%', '待处理'),
            ('物业报修总数', '脑膜瘤受理'),
            ('设备保修总数', '胶质瘤受理'),
            ('平均每天', '日均受理'),
            ('物业报修', '脑膜瘤'),
            ('设备故障', '胶质瘤'),
            ('类型三', '垂体瘤'),
            ('类型四', '听神经瘤'),
            ('共计工单', '当日受理'),
            ('今日受理工单', '今日受理病例'),
            ('月度工单类型概况', '月度病例类型概况')
        ]
        for source_text, target_text in replacements:
            figma_html = figma_html.replace(source_text, target_text)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            u.id,
            u.username,
            u.real_name,
            u.department,
            u.title,
            u.phone,
            COALESCE(d.diagnosis_count, 0) AS diagnosis_count
        FROM users u
        LEFT JOIN (
            SELECT doctor_id, COUNT(*) AS diagnosis_count
            FROM diagnoses
            WHERE doctor_id IS NOT NULL
            GROUP BY doctor_id
        ) d ON d.doctor_id = u.id
        WHERE u.role = 'doctor'
          AND u.username NOT LIKE 'docter%'
        ORDER BY u.id ASC
    """)
    doctors = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('team_management.html', figma_html=figma_html, doctors=doctors, ui_patient_url=_ui_patient_url())

@app.route('/team_management/create_doctor', methods=['POST'])
@login_required
def create_team_doctor():
    if current_user.role != 'admin':
        return jsonify({'ok': False, 'message': '权限不足'}), 403
    payload = request.get_json(silent=True) or {}
    real_name = (payload.get('real_name') or '').strip()
    department = (payload.get('department') or '').strip()
    title = (payload.get('title') or '').strip()
    phone = (payload.get('phone') or '').strip()
    if not real_name or not department or not title or not phone:
        return jsonify({'ok': False, 'message': '请完整填写医生信息'}), 400
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTRING(username, 7) AS UNSIGNED)), 0) AS max_seq
            FROM users
            WHERE role = 'doctor' AND username REGEXP '^doctor[0-9]+$'
        """)
        row = cursor.fetchone() or {}
        next_seq = int(row.get('max_seq') or 0) + 1
        username = f"doctor{next_seq}"
        cursor.execute("""
            INSERT INTO users (username, password, real_name, department, title, phone, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'doctor', CURRENT_TIMESTAMP)
        """, (username, hash_password('123456'), real_name, department, title, phone))
        db.commit()
        doctor_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, username, real_name, department, title, phone, 0 AS diagnosis_count
            FROM users
            WHERE id = %s
        """, (doctor_id,))
        doctor = cursor.fetchone()
        return jsonify({'ok': True, 'doctor': doctor})
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({'ok': False, 'message': f'保存失败: {err}'}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/team_management/update_doctor/<int:doctor_id>', methods=['POST'])
@login_required
def update_team_doctor(doctor_id):
    if current_user.role != 'admin':
        return jsonify({'ok': False, 'message': '权限不足'}), 403
    payload = request.get_json(silent=True) or {}
    real_name = (payload.get('real_name') or '').strip()
    department = (payload.get('department') or '').strip()
    title = (payload.get('title') or '').strip()
    phone = (payload.get('phone') or '').strip()
    if not real_name or not department or not title or not phone:
        return jsonify({'ok': False, 'message': '请完整填写医生信息'}), 400
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'doctor' LIMIT 1", (doctor_id,))
        if not cursor.fetchone():
            return jsonify({'ok': False, 'message': '医生不存在'}), 404
        cursor.execute("""
            UPDATE users
            SET real_name = %s, department = %s, title = %s, phone = %s
            WHERE id = %s AND role = 'doctor'
        """, (real_name, department, title, phone, doctor_id))
        db.commit()
        cursor.execute("""
            SELECT
                u.id,
                u.username,
                u.real_name,
                u.department,
                u.title,
                u.phone,
                COALESCE(d.diagnosis_count, 0) AS diagnosis_count
            FROM users u
            LEFT JOIN (
                SELECT doctor_id, COUNT(*) AS diagnosis_count
                FROM diagnoses
                WHERE doctor_id IS NOT NULL
                GROUP BY doctor_id
            ) d ON d.doctor_id = u.id
            WHERE u.id = %s AND u.role = 'doctor'
            LIMIT 1
        """, (doctor_id,))
        doctor = cursor.fetchone()
        return jsonify({'ok': True, 'doctor': doctor})
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({'ok': False, 'message': f'保存失败: {err}'}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/team_management/delete_doctor/<int:doctor_id>', methods=['POST'])
@login_required
def delete_team_doctor(doctor_id):
    if current_user.role != 'admin':
        return jsonify({'ok': False, 'message': '权限不足'}), 403
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE id = %s AND role = 'doctor' LIMIT 1", (doctor_id,))
        if not cursor.fetchone():
            return jsonify({'ok': False, 'message': '医生不存在'}), 404
        cursor.execute("DELETE FROM users WHERE id = %s AND role = 'doctor'", (doctor_id,))
        db.commit()
        return jsonify({'ok': True, 'deleted_id': doctor_id})
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({'ok': False, 'message': f'删除失败: {err}'}), 500
    finally:
        cursor.close()
        db.close()

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

# 上传nii文件路由
@app.route('/upload_nii', methods=['POST'])
@login_required
def upload_nii():
    # 接受前端传来的类型选择和文件
    selected = request.form.getlist('types')
    files = request.files.getlist('nii_files')
    sel_count = len(selected)
    file_count = len(files)
    # 至少要选择一种类型
    if sel_count == 0:
        return jsonify(success=False, message="请至少选择一种类型")
    # 文件数必须与选择的类型数一致
    if file_count != sel_count:
        if file_count < sel_count:
            return jsonify(success=False, message="请继续输入文件")
        else:
            return jsonify(success=False, message="当前上传文件数目过多")
    if paramiko is None:
        return jsonify(success=False, message="缺少paramiko依赖，无法执行远程上传")
    # 传到远程目录
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname='117.50.179.58',
            port=22,
            username='ubuntu',
            password='wpw242512'
        )
        sftp = client.open_sftp()
        remote_dir = '/data/WPW/BTS-Agent-Sys/BTS/Uploads/Brats18_TCIA01_1_1/'
        # 确保远程目录存在，如果需要可以创建，但是这里假设已经存在
        for f in files:
            # f 是一个 FileStorage 对象，直接从流中上传
            remote_path = remote_dir + f.filename
            try:
                f.stream.seek(0)
            except Exception:
                pass
            sftp.putfo(f.stream, remote_path)
        sftp.close()
        client.close()
        return jsonify(success=True, message="上传成功")
    except Exception as e:
        return jsonify(success=False, message=f"上传失败: {str(e)}")

# 远程测试路由
@app.route('/remote_test', methods=['GET', 'POST'])
@login_required
def remote_test():
    status = "未运行"
    output = ""
    image_url = None
    if request.method == 'POST':
        # 点击按钮后，由前端JS立即设置为运行中，后台开始执行
        status = "运行中"
        try:
            if paramiko is None:
                status = "未知错误"
                output = "缺少paramiko依赖，无法执行远程测试"
                return render_template('remote_test.html', status=status, output=output, image_url=image_url)
            # 参考 test.py 中的逻辑
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname='117.50.179.58',
                port=22,
                username='ubuntu',
                password='wpw242512'
            )

            # 在运行之前检查远程Uploads目录是否有文件
            try:
                sftp_check = client.open_sftp()
                remote_upload_dir = '/data/WPW/BTS-Agent-Sys/BTS/Uploads/Brats18_TCIA01_1_1/'
                files_list = sftp_check.listdir(remote_upload_dir)
                if not files_list:
                    status = "未运行"
                    output = "远程Uploads目录没有nii文件，请先上传"
                    sftp_check.close()
                    client.close()
                    return render_template('remote_test.html', status=status, output=output, image_url=image_url)
                sftp_check.close()
            except Exception:
                # 如果目录不存在或其他问题，也继续执行命令，留给后续步骤处理
                pass

            command = """
                source /home/ubuntu/miniconda3/etc/profile.d/conda.sh &&
                conda activate PeiweiWu_env &&
                cd /data/WPW/BTS-Agent-Sys/BTS/MMCFormer-main/ &&
                python Valide.py
            """

            stdin, stdout, stderr = client.exec_command(command)
            out = stdout.read().decode('utf8')
            err = stderr.read().decode('utf8')

            # 尝试获取远程生成的图片
            try:
                sftp = client.open_sftp()
                remote_path = '/data/WPW/BTS-Agent-Sys/BTS/MMCFormer-main/Downloads_SegGraph/seg_gt.png'
                local_name = f'remote_result_{uuid.uuid4().hex}.png'
                # 保存到 flask 静态文件夹
                local_path = os.path.join(app.static_folder, local_name)
                sftp.get(remote_path, local_path)
                sftp.close()
                # 将本地路径转换为 url（静态文件夹）
                image_url = url_for('static', filename=local_name)
            except Exception as img_err:
                # 如果获取失败则忽略，仅保留文本输出
                print(f"获取远程图片失败: {img_err}")

            client.close()

            if err:
                status = "未知错误"
                output = f"STDOUT:\n{out}\nSTDERR:\n{err}"
            else:
                status = "运行完毕"
                output = f"STDOUT:\n{out}"
        except Exception as e:
            status = "未知错误"
            output = str(e)
    return render_template('remote_test.html', status=status, output=output, image_url=image_url)

@app.route('/api/main-todos', methods=['GET'])
@login_required
def api_main_todos():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, username, real_name FROM users WHERE role = 'doctor' ORDER BY username")
        doctors = cursor.fetchall()
        if current_user.role == 'admin':
            cursor.execute("""
                SELECT t.id, t.title, t.content, t.due_date, t.assignee_id, t.created_at, u.username as assignee_name
                FROM todos t
                JOIN users u ON t.assignee_id = u.id
                ORDER BY t.created_at DESC
                LIMIT 120
            """)
        else:
            cursor.execute("""
                SELECT t.id, t.title, t.content, t.due_date, t.assignee_id, t.created_at, u.username as assignee_name
                FROM todos t
                JOIN users u ON t.assignee_id = u.id
                WHERE t.assignee_id = %s
                ORDER BY t.created_at DESC
                LIMIT 120
            """, (current_user.id,))
        todo_rows = cursor.fetchall()
        todos = []
        for row in todo_rows:
            due_date = row.get('due_date')
            due_date_text = due_date.strftime('%y-%m-%d') if due_date else ''
            todos.append({
                'id': row['id'],
                'task_name': row['title'],
                'content': row['content'],
                'deadline': due_date_text,
                'assignee_id': row['assignee_id'],
                'assignee_name': row['assignee_name']
            })
        doctor_items = []
        for doctor in doctors:
            label = doctor['real_name'] if doctor.get('real_name') else doctor['username']
            doctor_items.append({
                'id': doctor['id'],
                'username': doctor['username'],
                'label': label
            })
        return jsonify({'ok': True, 'todos': todos, 'doctors': doctor_items})
    except Exception as err:
        return jsonify({'ok': False, 'message': str(err)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/api/main-todos', methods=['POST'])
@login_required
def api_create_main_todo():
    payload = request.get_json(silent=True) or {}
    task_name = (payload.get('task_name') or '').strip()
    content = (payload.get('content') or '').strip()
    deadline = (payload.get('deadline') or '').strip()
    assignee_id_raw = payload.get('assignee_id')
    if not task_name or not content or not deadline or not assignee_id_raw:
        return jsonify({'ok': False, 'message': '字段不完整'}), 400
    try:
        assignee_id = int(assignee_id_raw)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'message': '医生信息无效'}), 400
    try:
        due_date = datetime.strptime(deadline, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return jsonify({'ok': False, 'message': '日期格式错误'}), 400
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, username FROM users WHERE id = %s AND role = 'doctor'", (assignee_id,))
        doctor = cursor.fetchone()
        if not doctor:
            return jsonify({'ok': False, 'message': '医生不存在'}), 404
        cursor.execute("""
            INSERT INTO todos (title, content, assigner_id, assignee_id, due_date, is_completed, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (task_name, content, current_user.id, assignee_id, due_date, 0))
        todo_id = cursor.lastrowid
        db.commit()
        send_notification(
            user_id=assignee_id,
            notification_type='todo',
            title='新的待办任务',
            content=f'您有一个新的待办任务：{task_name}',
            related_id=todo_id
        )
        return jsonify({
            'ok': True,
            'todo': {
                'id': todo_id,
                'task_name': task_name,
                'content': content,
                'deadline': datetime.strptime(due_date, '%Y-%m-%d').strftime('%y-%m-%d'),
                'assignee_id': assignee_id,
                'assignee_name': doctor['username']
            }
        })
    except Exception as err:
        db.rollback()
        return jsonify({'ok': False, 'message': str(err)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/api/main-todos/<int:todo_id>', methods=['DELETE'])
@login_required
def api_delete_main_todo(todo_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, assigner_id FROM todos WHERE id = %s", (todo_id,))
        todo = cursor.fetchone()
        if not todo:
            return jsonify({'ok': False, 'message': '待办不存在'}), 404
        if current_user.role != 'admin' and todo['assigner_id'] != current_user.id:
            return jsonify({'ok': False, 'message': '没有删除权限'}), 403
        cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
        db.commit()
        return jsonify({'ok': True})
    except Exception as err:
        db.rollback()
        return jsonify({'ok': False, 'message': str(err)}), 500
    finally:
        cursor.close()
        db.close()

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
    
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    try:
        port = int(os.environ.get('FLASK_PORT', '5000'))
    except Exception:
        port = 5000
    debug = os.environ.get('FLASK_DEBUG', '').strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

    app.run(host=host, port=port, debug=debug)
