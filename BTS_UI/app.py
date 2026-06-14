from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
import json
import hashlib
import base64
import hmac
import os
import uuid
import string
from datetime import datetime, timedelta
import paramiko  # 用于SSH远程执行
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(hours=8)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_NAME'] = 'bts_ui_session'

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

def ensure_patient_clinical_info_table():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_clinical_info (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL UNIQUE,
                chief_complaint TEXT,
                present_illness TEXT,
                past_medical_history TEXT,
                family_history TEXT,
                allergy_history TEXT,
                headache BOOLEAN,
                vomiting BOOLEAN,
                seizure BOOLEAN,
                vision_problem BOOLEAN,
                speech_problem BOOLEAN,
                limb_weakness BOOLEAN,
                specific_remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
            )
        """)
        db.commit()
        cursor.close()
        db.close()
    except Exception:
        pass

def ensure_diagnosis_agent_results_table():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnosis_agent_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                diagnosis_id INT NOT NULL,
                tumor_location VARCHAR(100),
                tumor_analysis TEXT,
                severity_assessment VARCHAR(20),
                possible_diagnosis VARCHAR(200),
                recommendation TEXT,
                need_doctor_review BOOLEAN,
                confidence FLOAT,
                confidence_reason TEXT,
                remarks TEXT,
                raw_output JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
            )
        """)
        db.commit()
        cursor.close()
        db.close()
    except Exception:
        pass

ensure_patient_clinical_info_table()
ensure_diagnosis_agent_results_table()

def _get_remote_hosts():
    raw = str(os.environ.get("REMOTE_HOSTS") or "").strip()
    if raw:
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        hosts = [p for p in parts if p]
        if hosts:
            return hosts
    host = str(os.environ.get("REMOTE_HOST") or "").strip()
    if host:
        return [host]
    return ["10.125.125.1", "10.125.125.2", "10.125.125.3", "117.50.179.58"]

def _connect_remote_ssh():
    hosts = _get_remote_hosts()
    port = int(os.environ.get("REMOTE_PORT", "22"))
    username = os.environ.get("REMOTE_USERNAME", "ubuntu")
    password = os.environ.get("REMOTE_PASSWORD", "wpw242512")
    timeout = int(os.environ.get("REMOTE_SSH_TIMEOUT", "30"))
    banner_timeout = int(os.environ.get("REMOTE_SSH_BANNER_TIMEOUT", "120"))
    auth_timeout = int(os.environ.get("REMOTE_SSH_AUTH_TIMEOUT", "100"))

    last_err = None
    for hostname in hosts:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=timeout,
                banner_timeout=banner_timeout,
                auth_timeout=auth_timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            try:
                transport = client.get_transport()
                if transport:
                    transport.set_keepalive(30)
            except Exception:
                pass
            return client, hostname, port
        except Exception as e:
            last_err = e
            try:
                client.close()
            except Exception:
                pass
            continue
    raise last_err if last_err else RuntimeError("remote_ssh_connect_failed")

def load_remote_json_file(remote_path):
    client, _hostname, _port = _connect_remote_ssh()
    sftp = client.open_sftp()
    try:
        with sftp.open(remote_path, "rb") as f:
            content = f.read()
        return json.loads(content.decode("utf-8"))
    finally:
        try:
            sftp.close()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass

def normalize_case_id(value):
    allowed = set(string.ascii_letters + string.digits + "_-")
    return "".join((c if c in allowed else "_") for c in str(value or ""))

def ensure_remote_dir(sftp, remote_dir):
    remote_dir = remote_dir.strip("/")
    if not remote_dir:
        return
    current = ""
    for part in remote_dir.split("/"):
        current = current + "/" + part
        try:
            sftp.stat(current)
        except Exception:
            try:
                sftp.mkdir(current)
            except Exception:
                pass

def build_agent_input(diagnosis_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM diagnoses WHERE id = %s", (diagnosis_id,))
    diagnosis = cursor.fetchone()
    if not diagnosis:
        cursor.close()
        db.close()
        return None, None
    cursor.execute("SELECT * FROM patients WHERE id = %s", (diagnosis["patient_id"],))
    patient = cursor.fetchone()
    cursor.execute("SELECT * FROM patient_clinical_info WHERE patient_id = %s", (diagnosis["patient_id"],))
    clinical_info = cursor.fetchone()
    cursor.close()
    db.close()
    patient_info = {
        "name": patient["name"] if patient else "None",
        "age": patient["age"] if patient and patient.get("age") is not None else 0,
        "gender": patient["gender"] if patient and patient.get("gender") else "unknown"
    }
    medical_history = {
        "chief_complaint": (clinical_info.get("chief_complaint") or "") if clinical_info else "",
        "present_illness": (clinical_info.get("present_illness") or "") if clinical_info else "",
        "past_medical_history": (clinical_info.get("past_medical_history") or "") if clinical_info else "",
        "family_history": (clinical_info.get("family_history") or "") if clinical_info else "",
        "allergy_history": (clinical_info.get("allergy_history") or "") if clinical_info else ""
    }
    symptoms = {
        "headache": bool(clinical_info.get("headache")) if clinical_info else False,
        "vomiting": bool(clinical_info.get("vomiting")) if clinical_info else False,
        "seizure": bool(clinical_info.get("seizure")) if clinical_info else False,
        "vision_problem": bool(clinical_info.get("vision_problem")) if clinical_info else False,
        "speech_problem": bool(clinical_info.get("speech_problem")) if clinical_info else False,
        "limb_weakness": bool(clinical_info.get("limb_weakness")) if clinical_info else False,
        "specific_remarks": (clinical_info.get("specific_remarks") or "") if clinical_info else ""
    }
    tumor_segmentation = {
        "file_type": "numpy_array",
        "labels": {
            "0": "normal",
            "1": "NCR/NET",
            "2": "ED",
            "4": "ET"
        },
        "shape": [0, 0, 0],
        "ncr_net_voxel_percentage": 0,
        "ed_voxel_percentage": 0,
        "et_voxel_percentage": 0
    }
    seg_case_id_used = ""
    try:
        seg_case_ids = []
        configured_case_id = os.environ.get("SEG_CASE_ID")
        patient_case_id = patient.get("patient_id") if patient else None
        diagnosis_case_id = diagnosis.get("seg_case_id") if isinstance(diagnosis, dict) else None

        if diagnosis_case_id:
            seg_case_ids.append(str(diagnosis_case_id))
        if patient_case_id:
            seg_case_ids.append(f"{patient_case_id}_{diagnosis_id}")
        if configured_case_id:
            seg_case_ids.append(str(configured_case_id))

        seen = set()
        seg_case_ids = [cid for cid in seg_case_ids if not (cid in seen or seen.add(cid))]

        seg_root = os.environ.get("REMOTE_SEG_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/MMCFormer-main/SegResults")

        for case_id in seg_case_ids:
            remote_summary_path = f"{seg_root}/{case_id}/summary.json"
            summary_data = load_remote_json_file(remote_summary_path)
            seg = summary_data.get("tumor_segmentation") if isinstance(summary_data, dict) else None
            if isinstance(seg, dict):
                required = ["labels", "shape", "ncr_net_voxel_percentage", "ed_voxel_percentage", "et_voxel_percentage"]
                if all(k in seg for k in required):
                    tumor_segmentation = seg
                    seg_case_id_used = str(case_id)
                    break
    except Exception:
        pass
    payload = {
        "patient_info": patient_info,
        "medical_history": medical_history,
        "symptoms": symptoms,
        "tumor_segmentation": tumor_segmentation,
        "diagnosis_record": {
            "diagnosis_id": int(diagnosis_id),
            "diagnosis_date": diagnosis.get("diagnosis_date").isoformat() if hasattr(diagnosis.get("diagnosis_date"), "isoformat") else str(diagnosis.get("diagnosis_date") or ""),
            "diagnosis_type": str(diagnosis.get("diagnosis_type") or ""),
            "tumor_type": str(diagnosis.get("tumor_type") or ""),
            "tumor_stage": str(diagnosis.get("tumor_stage") or ""),
            "diagnosis_content": str(diagnosis.get("diagnosis_content") or ""),
            "treatment_plan": str(diagnosis.get("treatment_plan") or ""),
            "examination_results": str(diagnosis.get("examination_results") or ""),
            "notes": str(diagnosis.get("notes") or ""),
            "seg_case_id_used": seg_case_id_used
        }
    }
    return payload, diagnosis["patient_id"]

def call_agent(payload):
    try:
        from utils import get_required_api_key_env
    except Exception as e:
        raise RuntimeError(f"智能体依赖未就绪: {e}")

    try:
        from single_agent_pipeline import validate_unified_input
    except Exception as e:
        raise RuntimeError(f"智能体输入校验不可用: {e}")

    pipeline = (os.environ.get("AGENT_PIPELINE") or "").strip().lower()
    if not pipeline:
        try:
            candidate_dir = os.path.join(os.path.dirname(__file__), "Multi-Agent")
            pipeline = "multi" if os.path.isdir(candidate_dir) else "single"
        except Exception:
            pipeline = "single"

    if pipeline in {"multi", "multi-agent", "multi_agent", "ma"}:
        try:
            from multi_agent_pipeline import run_decision
        except Exception as e:
            raise RuntimeError(f"多智能体依赖未就绪: {e}")
        model_info = (os.environ.get("MULTI_AGENT_MODEL") or os.environ.get("SINGLE_AGENT_MODEL") or "deepseek-chat").strip() or "deepseek-chat"
        api_key = os.environ.get("MULTI_AGENT_API_KEY") or os.environ.get("SINGLE_AGENT_API_KEY")
        strategy = (request.args.get("strategy") or request.headers.get("X-Multi-Agent-Strategy") or os.environ.get("MULTI_AGENT_STRATEGY") or "debate").strip().lower()
        trace = str(request.args.get("trace") or request.headers.get("X-Multi-Agent-Trace") or "").strip() in {"1", "true", "yes"}
    else:
        try:
            from single_agent_pipeline import run_decision
        except Exception as e:
            raise RuntimeError(f"单智能体依赖未就绪: {e}")
        model_info = (os.environ.get("SINGLE_AGENT_MODEL") or "deepseek-chat").strip() or "deepseek-chat"
        api_key = os.environ.get("SINGLE_AGENT_API_KEY")
        strategy = None
        trace = False

    api_key_env = get_required_api_key_env(model_info)
    if api_key:
        os.environ[api_key_env] = api_key
        os.environ[api_key_env.upper()] = api_key
    if not (os.environ.get(api_key_env) or os.environ.get(api_key_env.upper())):
        raise EnvironmentError(f"缺少 {api_key_env}。请设置环境变量或设置 SINGLE_AGENT_API_KEY/MULTI_AGENT_API_KEY。")

    validate_unified_input(payload)
    result = run_decision(payload, model_info, strategy, trace=trace) if strategy else run_decision(payload, model_info)
    if isinstance(result, dict):
        result.setdefault("agent_pipeline", pipeline)
        if strategy:
            result.setdefault("agent_strategy", strategy)
    return result

ensure_patient_clinical_info_table()

def hash_password(password):
    """对密码进行哈希处理"""
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed

def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('utf-8')

def _build_sso_token(username: str, role: str) -> str:
    secret = (os.environ.get('BTS_SSO_SECRET') or 'bts_sso_demo').encode('utf-8')
    payload = {"u": username, "r": role, "ts": int(time.time())}
    data = _b64url_encode(json.dumps(payload, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8'))
    sig = _b64url_encode(hmac.new(secret, data.encode('utf-8'), hashlib.sha256).digest())
    return f"{data}.{sig}"

def _derive_dlc_base_url() -> str:
    override = (os.environ.get('BTS_DLC_BASE_URL') or '').strip()
    if override:
        return override.rstrip('/')
    try:
        host = (request.host or '127.0.0.1').split(':')[0]
        scheme = request.scheme or 'http'
        return f"{scheme}://{host}:5001"
    except Exception:
        return "http://127.0.0.1:5001"

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
    login_user(User(user['id'], user['username'], user['role']), remember=True)
    return redirect(url_for('patient_portal'))

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
            # 登录成功 - 先在5000建立session，再SSO跳转5001
            user_obj = User(user['id'], user['username'], user['role'])
            login_user(user_obj, remember=True)
            flash('登录成功！', 'success')
            token = _build_sso_token(user_obj.username, user_obj.role)
            dlc_base = _derive_dlc_base_url()
            return redirect(f"{dlc_base}/sso?token={token}")
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

@app.route('/patient_portal')
@login_required
def patient_portal():
    ui_path = os.path.join(os.path.dirname(__file__), "UI", "patient.txt")
    try:
        with open(ui_path, "r", encoding="utf-8") as f:
            inner_html = f.read()
    except Exception:
        return redirect(url_for('main_interface'))
    patient_ids = []
    patient_names = []
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM patients ORDER BY created_at ASC, id ASC")
        rows = cursor.fetchall()
        for r in rows:
            name = str(r.get("name") or "").strip()
            pid = r.get("id")
            if name and pid is not None:
                patient_ids.append(int(pid))
                patient_names.append(name)
    except Exception:
        pass
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if db:
                db.close()
        except Exception:
            pass
    original_main_url = url_for('main_interface')
    dlc_base = _derive_dlc_base_url()
    sso_token = _build_sso_token(current_user.username, current_user.role)
    entry_url = f"{dlc_base}/sso?token={sso_token}"
    patient_portal_url = url_for('patient_portal')
    patients_url = url_for('patients')
    doctors_url = f"{dlc_base}/sso?token={sso_token}&next=/team_management"
    test1_url = f"{dlc_base}/sso?token={sso_token}"
    logout_url = url_for('logout')
    report_api_base = url_for('api_patient_report', patient_id=0)[:-1]
    chat_api_base = url_for('api_patient_chat', patient_id=0)[:-1]
    uploads_api_base = url_for('api_patient_uploads', patient_id=0)[:-1]
    nii_previews_api_base = url_for('api_patient_nii_previews', patient_id=0)[:-1]
    nii_seg_api_base = url_for('api_patient_nii_segmentation', patient_id=0)[:-1]
    nii_spin_api_base = url_for('api_patient_nii_spin', patient_id=0)[:-1]
    nii_spin_vtk_api_base = url_for('api_patient_nii_spin_vtk', patient_id=0)[:-1]
    agent_run_api_base = url_for('run_agent_analysis_api', diagnosis_id=0)[:-1]
    patient_names_json = json.dumps(patient_names, ensure_ascii=False)
    patient_ids_json = json.dumps(patient_ids, ensure_ascii=False)
    diagnoses_base = url_for('diagnoses', patient_id=0)[:-1]
    current_username_json = json.dumps(str(getattr(current_user, "username", "") or ""), ensure_ascii=False)
    entry_url_json = json.dumps(entry_url, ensure_ascii=False)
    original_main_url_json = json.dumps(original_main_url, ensure_ascii=False)
    full_html = (
        "<!DOCTYPE html><html lang='zh-CN'><head>"
        "<meta charset='UTF-8'>"
        "<title>患者态势总览</title>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<style>"
        "html,body{width:100%;height:100%;margin:0;overflow:hidden;background:#030C31;}"
        "svg,img{display:block;}"
        "#portalStage *{box-sizing:border-box;}"
        "#portalViewport{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;}"
        "#portalStage{width:1920px;height:1080px;transform-origin:50% 50%;}"
        "</style>"
        "</head><body>"
        "<div id='portalViewport'><div id='portalStage'>"
        f"{inner_html}"
        "</div></div>"
        "<script>"
        "(function(){"
        "const stage=document.getElementById('portalStage');"
        "function fit(){"
        "const vw=window.innerWidth||1920;"
        "const vh=window.innerHeight||1080;"
        "const scale=Math.min(vw/1920,vh/1080);"
        "stage.style.transform='scale('+scale+')';"
        "}"
        "window.addEventListener('resize',fit);"
        "fit();"
        f"const patientNames={patient_names_json};"
        f"const patientIds={patient_ids_json};"
        f"const diagnosesBase={json.dumps(diagnoses_base, ensure_ascii=False)};"
        f"const patientPortalUrl={json.dumps(patient_portal_url, ensure_ascii=False)};"
        f"const patientsUrl={json.dumps(patients_url, ensure_ascii=False)};"
        f"const doctorsUrl={json.dumps(doctors_url, ensure_ascii=False)};"
        f"const test1Url={json.dumps(test1_url, ensure_ascii=False)};"
        f"const entryUrl={entry_url_json};"
        f"const originalMainUrl={original_main_url_json};"
        f"const logoutUrl={json.dumps(logout_url, ensure_ascii=False)};"
        f"const reportApiBase={json.dumps(report_api_base, ensure_ascii=False)};"
        f"const chatApiBase={json.dumps(chat_api_base, ensure_ascii=False)};"
        f"const uploadsApiBase={json.dumps(uploads_api_base, ensure_ascii=False)};"
        f"const niiPreviewsApiBase={json.dumps(nii_previews_api_base, ensure_ascii=False)};"
        f"const niiSegApiBase={json.dumps(nii_seg_api_base, ensure_ascii=False)};"
        f"const niiSpinApiBase={json.dumps(nii_spin_api_base, ensure_ascii=False)};"
        f"const niiSpinVtkApiBase={json.dumps(nii_spin_vtk_api_base, ensure_ascii=False)};"
        f"const agentRunApiBase={json.dumps(agent_run_api_base, ensure_ascii=False)};"
        f"const currentUsername={current_username_json};"
        "try{"
        "const stageRoot=document.getElementById('portalStage');"
        "const reportBox=document.createElement('div');"
        "reportBox.id='portalReportBox';"
        "reportBox.style.cssText='position:absolute;left:430px;top:200px;width:396px;height:760px;"
        "padding:16px 14px;overflow:auto;z-index:50;color:#EAF7FF;font-size:16px;"
        "background:rgba(5,13,75,0.45);border:1px solid rgba(20,128,240,0.7);border-radius:10px;"
        "box-shadow:0 0 18px rgba(20,128,240,0.25) inset;font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;';"
        "stageRoot.appendChild(reportBox);"
        "const centerBox=document.createElement('div');"
        "centerBox.id='portalCenterBox';"
        "centerBox.style.cssText='position:absolute;left:902px;top:200px;width:496px;height:760px;"
        "padding:0;overflow:hidden;z-index:40;color:#EAF7FF;font-size:16px;"
        "background:rgba(5,13,75,0.25);border:1px solid rgba(20,128,240,0.55);border-radius:10px;"
        "box-shadow:0 0 18px rgba(20,128,240,0.18) inset;font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;';"
        "stageRoot.appendChild(centerBox);"
        "const uploadsView=document.createElement('div');"
        "uploadsView.id='portalUploadsView';"
        "uploadsView.style.cssText='height:420px;padding:0;overflow:hidden;border-bottom:1px solid rgba(20,128,240,0.28);display:flex;flex-direction:column;';"
        "centerBox.appendChild(uploadsView);"
        "const centerBottom=document.createElement('div');"
        "centerBottom.id='portalCenterBottom';"
        "centerBottom.style.cssText='height:340px;padding:0;overflow:hidden;display:flex;flex-direction:column;';"
        "centerBox.appendChild(centerBottom);"
        "const spinHeader=document.createElement('div');"
        "spinHeader.style.cssText='flex:0 0 auto;padding:10px 12px;font-size:18px;font-weight:600;color:#67FFFF;"
        "border-bottom:1px solid rgba(20,128,240,0.18);display:flex;align-items:center;justify-content:space-between;gap:10px;"
        "position:relative;z-index:2;pointer-events:auto;';"
        "const spinTitle=document.createElement('div');"
        "spinTitle.textContent='3D视图';"
        "spinHeader.appendChild(spinTitle);"
        "const spinTabs=document.createElement('div');"
        "spinTabs.style.cssText='display:flex;gap:8px;';"
        "const btnB=document.createElement('button');"
        "btnB.textContent='全屏显示';"
        "btnB.type='button';"
        "btnB.style.cssText='width:84px;height:28px;border-radius:8px;border:1px solid rgba(103,255,255,0.65);"
        "background:rgba(103,255,255,0.22);color:#67FFFF;font-size:14px;cursor:pointer;pointer-events:auto;';"
        "spinTabs.appendChild(btnB);"
        "spinHeader.appendChild(spinTabs);"
        "centerBottom.appendChild(spinHeader);"
        "const spinBody=document.createElement('div');"
        "spinBody.style.cssText='flex:1 1 auto;overflow:hidden;display:flex;align-items:center;justify-content:center;padding:10px 10px;"
        "position:relative;z-index:1;pointer-events:auto;';"
        "centerBottom.appendChild(spinBody);"
        "const spinImg=document.createElement('img');"
        "spinImg.style.cssText='display:block;width:100%;height:100%;object-fit:contain;background:rgba(0,0,0,0.35);border-radius:8px;"
        "pointer-events:none;user-select:none;';"
        "const flatCanvas=document.createElement('canvas');"
        "flatCanvas.style.cssText='display:none;width:100%;height:100%;background:rgba(0,0,0,0.35);border-radius:8px;"
        "pointer-events:none;user-select:none;';"
        "spinBody.appendChild(spinImg);"
        "spinBody.appendChild(flatCanvas);"
        "let spinTimer=null;"
        "let spinFrames=[];"
        "let spinFramesVtk=[];"
        "let currentSpinPid=null;"
        "function setTab(active){"
        "if(spinTimer){clearInterval(spinTimer);spinTimer=null;}"
        "btnB.style.background='rgba(103,255,255,0.22)';"
        "btnB.style.borderColor='rgba(103,255,255,0.65)';"
        "btnB.style.color='#67FFFF';"
        "spinImg.style.display='block';"
        "flatCanvas.style.display='none';"
        "if(spinFramesVtk&&spinFramesVtk.length>0){"
        "spinBody.innerHTML='';"
        "spinBody.appendChild(spinImg);"
        "spinBody.appendChild(flatCanvas);"
        "spinImg.onerror=function(){spinBody.textContent='3D视图帧加载失败';};"
        "let idx=0;"
        "spinImg.src=spinFramesVtk[0];"
        "spinTimer=setInterval(function(){idx=(idx+1)%spinFramesVtk.length;spinImg.src=spinFramesVtk[idx];},140);"
        "}else if(currentSpinPid!==null&&currentSpinPid!==undefined){"
        "spinBody.textContent='正在生成3D视图...';"
        "loadSpinVtk(currentSpinPid);"
        "}else{"
        "spinBody.textContent='请先选择病人';"
        "}"
        "}"
        "let fsOverlay=null;"
        "let fsImg=null;"
        "let fsTimer=null;"
        "let fsEscBound=false;"
        "function closeFullscreen(){"
        "if(fsTimer){clearInterval(fsTimer);fsTimer=null;}"
        "if(fsOverlay){fsOverlay.style.display='none';}"
        "try{setTab('B');}catch(_e){}"
        "}"
        "function ensureFullscreen(){"
        "if(fsOverlay){return;}"
        "fsOverlay=document.createElement('div');"
        "fsOverlay.id='portalSpinFullscreen';"
        "fsOverlay.style.cssText='position:fixed;inset:0;display:none;align-items:center;justify-content:center;"
        "z-index:2147483646;background:rgba(0,0,0,0.72);backdrop-filter:blur(8px);';"
        "const panel=document.createElement('div');"
        "panel.style.cssText='width:96vw;height:96vh;max-width:1600px;max-height:960px;box-sizing:border-box;"
        "border-radius:14px;border:1px solid rgba(103,255,255,0.45);"
        "background:rgba(3,12,49,0.78);box-shadow:0 0 30px rgba(20,128,240,0.25) inset;"
        "display:flex;flex-direction:column;overflow:hidden;';"
        "const head=document.createElement('div');"
        "head.style.cssText='flex:0 0 auto;display:flex;align-items:center;justify-content:space-between;"
        "padding:10px 12px;border-bottom:1px solid rgba(20,128,240,0.25);color:#67FFFF;font-size:16px;font-weight:600;';"
        "const title=document.createElement('div');"
        "title.textContent='3D视图（全屏）';"
        "const closeBtn=document.createElement('button');"
        "closeBtn.type='button';"
        "closeBtn.textContent='关闭';"
        "closeBtn.style.cssText='border-radius:10px;border:1px solid rgba(103,255,255,0.55);"
        "background:rgba(103,255,255,0.12);color:#EAF7FF;padding:6px 10px;font-size:14px;cursor:pointer;';"
        "closeBtn.addEventListener('click',function(ev){try{ev.preventDefault();ev.stopPropagation();}catch(_e){}closeFullscreen();});"
        "head.appendChild(title);"
        "head.appendChild(closeBtn);"
        "const body=document.createElement('div');"
        "body.style.cssText='flex:1 1 auto;min-height:0;display:flex;align-items:center;justify-content:center;padding:12px;overflow:hidden;';"
        "fsImg=document.createElement('img');"
        "fsImg.style.cssText='max-width:100%;max-height:100%;width:100%;height:100%;object-fit:contain;background:rgba(0,0,0,0.35);border-radius:10px;';"
        "body.appendChild(fsImg);"
        "panel.appendChild(head);"
        "panel.appendChild(body);"
        "fsOverlay.appendChild(panel);"
        "fsOverlay.addEventListener('click',function(){closeFullscreen();});"
        "panel.addEventListener('click',function(ev){try{ev.stopPropagation();}catch(_e){}});"
        "document.body.appendChild(fsOverlay);"
        "if(!fsEscBound){"
        "fsEscBound=true;"
        "document.addEventListener('keydown',function(ev){if(ev&&ev.key==='Escape'){closeFullscreen();}});"
        "}"
        "}"
        "async function openFullscreen(){"
        "ensureFullscreen();"
        "if(!currentSpinPid&&currentSpinPid!==0){fsOverlay.style.display='flex';if(fsImg){fsImg.removeAttribute('src');}return;}"
        "if(spinTimer){clearInterval(spinTimer);spinTimer=null;}"
        "if((!spinFramesVtk)||spinFramesVtk.length===0){"
        "await loadSpinVtk(currentSpinPid);"
        "}"
        "fsOverlay.style.display='flex';"
        "if(!spinFramesVtk||spinFramesVtk.length===0){return;}"
        "let idx=0;"
        "fsImg.onerror=function(){try{closeFullscreen();}catch(_e){}};"
        "fsImg.src=spinFramesVtk[0];"
        "if(fsTimer){clearInterval(fsTimer);}"
        "fsTimer=setInterval(function(){idx=(idx+1)%spinFramesVtk.length;fsImg.src=spinFramesVtk[idx];},140);"
        "}"
        "function renderFlatBrain(){"
        "const w=Math.max(10,flatCanvas.clientWidth||0);"
        "const h=Math.max(10,flatCanvas.clientHeight||0);"
        "const dpr=window.devicePixelRatio||1;"
        "flatCanvas.width=Math.floor(w*dpr);"
        "flatCanvas.height=Math.floor(h*dpr);"
        "const ctx=flatCanvas.getContext('2d');"
        "ctx.setTransform(dpr,0,0,dpr,0,0);"
        "ctx.clearRect(0,0,w,h);"
        "const bg=ctx.createRadialGradient(w*0.55,h*0.55,10,w*0.55,h*0.55,Math.max(w,h));"
        "bg.addColorStop(0,'rgba(6,18,72,0.38)');"
        "bg.addColorStop(1,'rgba(0,0,0,0.88)');"
        "ctx.fillStyle=bg;"
        "ctx.fillRect(0,0,w,h);"
        "const cx=w*0.52, cy=h*0.56;"
        "const rx=w*0.36, ry=h*0.24;"
        "const brain=new Path2D();"
        "brain.moveTo(cx-rx*1.18, cy-ry*0.08);"
        "brain.bezierCurveTo(cx-rx*1.28, cy-ry*0.78, cx-rx*0.85, cy-ry*1.14, cx-rx*0.20, cy-ry*1.00);"
        "brain.bezierCurveTo(cx+rx*0.25, cy-ry*1.16, cx+rx*1.05, cy-ry*0.78, cx+rx*1.08, cy-ry*0.08);"
        "brain.bezierCurveTo(cx+rx*1.22, cy+ry*0.52, cx+rx*0.82, cy+ry*1.06, cx+rx*0.18, cy+ry*0.94);"
        "brain.bezierCurveTo(cx-rx*0.15, cy+ry*1.10, cx-rx*0.98, cy+ry*0.76, cx-rx*1.14, cy+ry*0.18);"
        "brain.bezierCurveTo(cx-rx*1.26, cy+ry*0.08, cx-rx*1.26, cy-ry*0.02, cx-rx*1.18, cy-ry*0.08);"
        "brain.closePath();"
        "const cereb=new Path2D();"
        "cereb.ellipse(cx+rx*0.78, cy+ry*0.58, rx*0.38, ry*0.30, 0, 0, Math.PI*2);"
        "const stem=new Path2D();"
        "stem.moveTo(cx+rx*0.78, cy+ry*0.82);"
        "stem.bezierCurveTo(cx+rx*0.86, cy+ry*1.10, cx+rx*0.80, cy+ry*1.28, cx+rx*0.70, cy+ry*1.45);"
        "stem.bezierCurveTo(cx+rx*0.62, cy+ry*1.55, cx+rx*0.58, cy+ry*1.58, cx+rx*0.54, cy+ry*1.60);"
        "ctx.save();"
        "const fill=ctx.createLinearGradient(cx-rx*1.2,cy-ry*1.1,cx+rx*1.2,cy+ry*1.2);"
        "fill.addColorStop(0,'rgba(20,128,240,0.20)');"
        "fill.addColorStop(0.45,'rgba(3,12,49,0.18)');"
        "fill.addColorStop(1,'rgba(0,0,0,0.15)');"
        "ctx.fillStyle=fill;"
        "ctx.fill(brain);"
        "ctx.fill(cereb);"
        "ctx.fill(stem);"
        "ctx.restore();"
        "ctx.save();"
        "ctx.shadowColor='rgba(103,255,255,0.92)';"
        "ctx.shadowBlur=30;"
        "ctx.strokeStyle='rgba(103,255,255,0.92)';"
        "ctx.lineWidth=3.2;"
        "ctx.stroke(brain);"
        "ctx.stroke(cereb);"
        "ctx.stroke(stem);"
        "ctx.shadowBlur=0;"
        "ctx.strokeStyle='rgba(20,128,240,0.40)';"
        "ctx.lineWidth=1.2;"
        "ctx.stroke(brain);"
        "ctx.stroke(cereb);"
        "ctx.stroke(stem);"
        "ctx.restore();"
        "ctx.save();"
        "ctx.clip(brain);"
        "ctx.globalAlpha=0.16;"
        "for(let i=0;i<10;i++){"
        "const y=cy-ry*0.88+i*(ry*1.7/9);"
        "ctx.strokeStyle='rgba(103,255,255,0.22)';"
        "ctx.lineWidth=1;"
        "ctx.beginPath();"
        "ctx.moveTo(cx-rx*1.05,y);"
        "ctx.bezierCurveTo(cx-rx*0.45,y-ry*0.22,cx+rx*0.20,y+ry*0.22,cx+rx*0.95,y);"
        "ctx.stroke();"
        "}"
        "ctx.globalAlpha=1;"
        "ctx.restore();"
        "ctx.save();"
        "const mid=new Path2D();"
        "mid.moveTo(cx-rx*0.15,cy-ry*0.92);"
        "mid.bezierCurveTo(cx-rx*0.10,cy-ry*0.55,cx+rx*0.05,cy-ry*0.25,cx+rx*0.10,cy+ry*0.18);"
        "ctx.strokeStyle='rgba(230,255,255,0.20)';"
        "ctx.lineWidth=2;"
        "ctx.stroke(mid);"
        "ctx.restore();"
        "function seeded(seed){let t=seed+0x6D2B79F5;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;}"
        "let seed=(currentSpinPid||1)*13331;"
        "function rand(){seed=(seed*1664525+1013904223)>>>0;return seeded(seed);}"
        "ctx.save();"
        "ctx.clip(brain);"
        "ctx.globalCompositeOperation='lighter';"
        "const pts=[];"
        "let guard=0;"
        "while(pts.length<78&&guard<12000){"
        "guard++;"
        "const x=cx+(rand()-0.5)*rx*2.15;"
        "const y=cy+(rand()-0.5)*ry*1.95;"
        "if(ctx.isPointInPath(brain,x,y)){pts.push({x:x,y:y});}"
        "}"
        "const maxD=rx*0.55;"
        "for(let i=0;i<pts.length;i++){"
        "let best=[-1,-1,-1];"
        "let bestD=[1e18,1e18,1e18];"
        "for(let j=0;j<pts.length;j++){"
        "if(i===j){continue;}"
        "const dx=pts[i].x-pts[j].x;"
        "const dy=pts[i].y-pts[j].y;"
        "const d=dx*dx+dy*dy;"
        "for(let k=0;k<3;k++){"
        "if(d<bestD[k]){for(let s=2;s>k;s--){bestD[s]=bestD[s-1];best[s]=best[s-1];}bestD[k]=d;best[k]=j;break;}"
        "}"
        "}"
        "for(let k=0;k<2;k++){"
        "const j=best[k];"
        "if(j<0){continue;}"
        "const d=Math.sqrt(bestD[k]);"
        "if(d>maxD){continue;}"
        "const a=0.26*(1.0-d/maxD);"
        "ctx.strokeStyle='rgba(103,255,255,'+a.toFixed(3)+')';"
        "ctx.lineWidth=1;"
        "ctx.beginPath();"
        "ctx.moveTo(pts[i].x,pts[i].y);"
        "ctx.lineTo(pts[j].x,pts[j].y);"
        "ctx.stroke();"
        "}"
        "}"
        "for(let i=0;i<pts.length;i++){"
        "const p=pts[i];"
        "const big=(i%13===0);"
        "const hot=(i%17===0);"
        "ctx.shadowColor=hot?'rgba(255,120,210,0.90)':'rgba(103,255,255,0.95)';"
        "ctx.shadowBlur=big?20:12;"
        "ctx.fillStyle=hot?'rgba(255,120,210,0.85)':(big?'rgba(230,255,255,0.95)':'rgba(103,255,255,0.92)');"
        "ctx.beginPath();"
        "ctx.arc(p.x,p.y,big?3.2:2.1,0,Math.PI*2);"
        "ctx.fill();"
        "}"
        "ctx.shadowBlur=0;"
        "ctx.globalCompositeOperation='source-over';"
        "ctx.restore();"
        "}"
        "btnB.addEventListener('click',function(ev){try{ev.preventDefault();ev.stopPropagation();}catch(_e){}openFullscreen();});"
        "async function loadSpinVtk(pid){"
        "if(spinTimer){clearInterval(spinTimer);spinTimer=null;}"
        "currentSpinPid=pid;"
        "spinFramesVtk=[];"
        "spinImg.removeAttribute('src');"
        "spinBody.textContent='正在生成VTK 3D视图...';"
        "try{"
        "const resp=await fetch(niiSpinVtkApiBase+String(pid));"
        "const js=await resp.json();"
        "if(!resp.ok||!js||!js.success||!js.frames||js.frames.length===0){"
        "spinBody.textContent=(js&&js.message)?js.message:'暂无VTK 3D预览';"
        "return;"
        "}"
        "spinBody.innerHTML='';"
        "spinBody.appendChild(spinImg);"
        "spinBody.appendChild(flatCanvas);"
        "const bust=Date.now();"
        "spinFramesVtk=js.frames.map(function(u,i){return u+(u.indexOf('?')>-1?'&':'?')+'v='+bust+'-'+i;});"
        "spinFramesVtk.forEach(function(u){const im=new Image();im.src=u;});"
        "setTab('B');"
        "}catch(e){spinBody.textContent='加载VTK 3D预览失败';}"
        "}"
        "async function loadSpin(pid){"
        "return loadSpinVtk(pid);"
        "}"
        "const analysisBox=document.createElement('div');"
        "analysisBox.id='portalAnalysisBox';"
        "analysisBox.style.cssText='position:absolute;left:1464px;top:200px;width:396px;height:760px;"
        "padding:0;overflow:hidden;z-index:50;color:#EAF7FF;font-size:16px;"
        "background:rgba(5,13,75,0.45);border:1px solid rgba(20,128,240,0.7);border-radius:10px;"
        "box-shadow:0 0 18px rgba(20,128,240,0.25) inset;font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;';"
        "stageRoot.appendChild(analysisBox);"
        "const analysisHeader=document.createElement('div');"
        "analysisHeader.style.cssText='height:52px;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;gap:10px;"
        "border-bottom:1px solid rgba(20,128,240,0.35);';"
        "analysisBox.appendChild(analysisHeader);"
        "const analysisHeaderTitle=document.createElement('div');"
        "analysisHeaderTitle.style.cssText='font-size:18px;font-weight:600;color:#67FFFF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;';"
        "analysisHeaderTitle.textContent='智能分析';"
        "analysisHeader.appendChild(analysisHeaderTitle);"
        "const analysisTabs=document.createElement('div');"
        "analysisTabs.style.cssText='display:flex;gap:8px;flex:0 0 auto;';"
        "analysisHeader.appendChild(analysisTabs);"
        "const analysisBtnA=document.createElement('button');"
        "analysisBtnA.type='button';"
        "analysisBtnA.textContent='A';"
        "analysisBtnA.style.cssText='width:34px;height:28px;border-radius:8px;border:1px solid rgba(103,255,255,0.65);"
        "background:rgba(103,255,255,0.22);color:#67FFFF;font-size:14px;cursor:pointer;pointer-events:auto;';"
        "const analysisBtnB=document.createElement('button');"
        "analysisBtnB.type='button';"
        "analysisBtnB.textContent='B';"
        "analysisBtnB.style.cssText='width:34px;height:28px;border-radius:8px;border:1px solid rgba(20,128,240,0.55);"
        "background:rgba(3,12,49,0.35);color:#EAF7FF;font-size:14px;cursor:pointer;pointer-events:auto;';"
        "analysisTabs.appendChild(analysisBtnA);"
        "analysisTabs.appendChild(analysisBtnB);"
        "const analysisView=document.createElement('div');"
        "analysisView.id='portalAnalysisView';"
        "analysisView.style.cssText='height:368px;padding:16px 14px;overflow:auto;border-bottom:1px solid rgba(20,128,240,0.35);';"
        "analysisBox.appendChild(analysisView);"
        "const chatWrap=document.createElement('div');"
        "chatWrap.id='portalChatWrap';"
        "chatWrap.style.cssText='height:340px;display:flex;flex-direction:column;';"
        "analysisBox.appendChild(chatWrap);"
        "const chatMessages=document.createElement('div');"
        "chatMessages.id='portalChatMessages';"
        "chatMessages.style.cssText='flex:1 1 auto;padding:12px 12px;overflow:auto;';"
        "chatWrap.appendChild(chatMessages);"
        "const chatInputRow=document.createElement('div');"
        "chatInputRow.style.cssText='flex:0 0 auto;display:flex;gap:8px;padding:10px 12px;border-top:1px solid rgba(20,128,240,0.35);';"
        "chatWrap.appendChild(chatInputRow);"
        "const chatInput=document.createElement('textarea');"
        "chatInput.id='portalChatInput';"
        "chatInput.rows=2;"
        "chatInput.placeholder='针对智能分析提问，例如：ET/ED 是什么？体积百分比怎么理解？';"
        "chatInput.style.cssText='flex:1 1 auto;resize:none;border-radius:8px;border:1px solid rgba(20,128,240,0.6);"
        "background:rgba(3,12,49,0.55);color:#EAF7FF;padding:10px 10px;font-size:14px;outline:none;';"
        "chatInputRow.appendChild(chatInput);"
        "const chatBtn=document.createElement('button');"
        "chatBtn.textContent='发送';"
        "chatBtn.style.cssText='flex:0 0 auto;border-radius:8px;border:1px solid rgba(103,255,255,0.65);"
        "background:rgba(103,255,255,0.15);color:#67FFFF;padding:0 14px;font-size:14px;cursor:pointer;';"
        "chatInputRow.appendChild(chatBtn);"
        "let chatPatientId=null;"
        "let chatPatientName='';"
        "let chatHistory=[];"
        "let analysisMode='A';"
        "function paintAnalysisTab(){"
        "if(analysisMode==='A'){"
        "analysisBtnA.style.background='rgba(103,255,255,0.22)';"
        "analysisBtnA.style.borderColor='rgba(103,255,255,0.65)';"
        "analysisBtnA.style.color='#67FFFF';"
        "analysisBtnB.style.background='rgba(3,12,49,0.35)';"
        "analysisBtnB.style.borderColor='rgba(20,128,240,0.55)';"
        "analysisBtnB.style.color='#EAF7FF';"
        "}else{"
        "analysisBtnB.style.background='rgba(103,255,255,0.18)';"
        "analysisBtnB.style.borderColor='rgba(103,255,255,0.55)';"
        "analysisBtnB.style.color='#67FFFF';"
        "analysisBtnA.style.background='rgba(3,12,49,0.35)';"
        "analysisBtnA.style.borderColor='rgba(20,128,240,0.55)';"
        "analysisBtnA.style.color='#EAF7FF';"
        "}"
        "}"
        "function addChatMsg(role,text){"
        "const wrap=document.createElement('div');"
        "wrap.style.cssText='margin:8px 0;display:flex;';"
        "wrap.style.justifyContent=(role==='user')?'flex-end':'flex-start';"
        "const bubble=document.createElement('div');"
        "bubble.style.cssText='max-width:92%;white-space:pre-wrap;line-height:1.45;"
        "padding:9px 10px;border-radius:10px;font-size:14px;border:1px solid rgba(20,128,240,0.35);';"
        "bubble.style.background=(role==='user')?'rgba(103,255,255,0.12)':'rgba(3,12,49,0.45)';"
        "bubble.style.color='#EAF7FF';"
        "bubble.textContent=text;"
        "wrap.appendChild(bubble);"
        "chatMessages.appendChild(wrap);"
        "chatMessages.scrollTop=chatMessages.scrollHeight;"
        "chatHistory.push({role:role,content:text});"
        "if(chatHistory.length>20){chatHistory=chatHistory.slice(-20);}"
        "}"
        "function resetChat(pid,name){"
        "chatPatientId=pid;"
        "chatPatientName=name||'';"
        "chatHistory=[];"
        "chatMessages.innerHTML='';"
        "addChatMsg('assistant','你可以问我智能分析里看不懂的内容，我会结合当前病人的分析结果解释。');"
        "}"
        "async function sendChat(){"
        "const q=(chatInput.value||'').trim();"
        "if(!q||!chatPatientId){return;}"
        "chatInput.value='';"
        "addChatMsg('user',q);"
        "try{"
        "chatBtn.disabled=true;"
        "const resp=await fetch(chatApiBase+String(chatPatientId),{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({question:q,history:chatHistory})});"
        "let js=null;"
        "try{js=await resp.json();}catch(_e){js=null;}"
        "if(!resp.ok){"
        "const msg=(js&&js.message)?js.message:'请求失败，请稍后重试。';"
        "addChatMsg('assistant',msg);"
        "return;"
        "}"
        "if(!js||!js.success){addChatMsg('assistant',(js&&js.message)?js.message:'请求失败，请稍后重试。');return;}"
        "addChatMsg('assistant',js.answer||'');"
        "}catch(e){addChatMsg('assistant','请求失败，请稍后重试。');}"
        "finally{chatBtn.disabled=false;}"
        "}"
        "chatBtn.addEventListener('click',sendChat);"
        "chatInput.addEventListener('keydown',function(e){"
        "if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendChat();}"
        "});"
        "function renderReportLoading(name){"
        "reportBox.textContent='正在加载 '+(name||'')+' 的诊断报告...';"
        "analysisHeaderTitle.textContent=(name||'病人')+' 智能分析';"
        "analysisView.textContent='正在加载 '+(name||'')+' 的智能分析...';"
        "uploadsView.textContent='正在加载 '+(name||'')+' 的NII预览...';"
        "}"
        "function renderReportEmpty(name){"
        "reportBox.textContent=(name||'该病人')+' 暂无诊断记录';"
        "analysisHeaderTitle.textContent=(name||'病人')+' 智能分析';"
        "analysisView.textContent=(name||'该病人')+' 暂无智能分析结果';"
        "uploadsView.textContent=(name||'该病人')+' 暂无上传文件';"
        "}"
        "function renderReportError(name){"
        "reportBox.textContent='加载 '+(name||'')+' 的诊断报告失败';"
        "analysisHeaderTitle.textContent=(name||'病人')+' 智能分析';"
        "analysisView.textContent='加载 '+(name||'')+' 的智能分析失败';"
        "uploadsView.textContent='加载 '+(name||'')+' 的上传文件失败';"
        "}"
        "let niiMode='A';"
        "let niiSegCache={};"
        "let niiSegBusy=false;"
        "let niiSegCaseByPid={};"
        "let currentReport=null;"
        "function normalizeCaseId(v){return String(v||'').replace(/[^A-Za-z0-9_-]/g,'_');}"
        "function setSegCaseId(pid, caseId){try{const k=String(pid);const v=normalizeCaseId(caseId);if(k&&v){niiSegCaseByPid[k]=v;}}catch(_e){}}"
        "function getSegCaseIdForPid(pid){"
        "try{const k=String(pid); if(k&&niiSegCaseByPid[k]){return String(niiSegCaseByPid[k]);}}catch(_e){}"
        "return getCurrentSegCaseId();"
        "}"
        "function getCurrentSegCaseId(){"
        "try{"
        "if(!currentReport||!currentReport.patient||!currentReport.diagnosis){return '';}"
        "const cid=String((currentReport.patient&&currentReport.patient.patient_id)||'')+'_'+String((currentReport.diagnosis&&currentReport.diagnosis.id)||'');"
        "return normalizeCaseId(cid);"
        "}catch(_e){return '';}"
        "}"
        "function getLocalSegCandidates(pid){"
        "try{"
        "const safe=getSegCaseIdForPid(pid);"
        "if(!safe){return [];}"
        "return ['/static/nii_seg/'+safe+'/seg_pred.png'];"
        "}catch(_e){return [];}"
        "}"
        "async function tryLoadLocalSeg(pid){"
        "const list=getLocalSegCandidates(pid);"
        "if(!list||!list.length){return null;}"
        "for(const base of list){"
        "const u=base+(base.indexOf('?')>-1?'&':'?')+'v='+(Date.now());"
        "try{"
        "const resp=await fetch(u,{method:'GET',cache:'no-store'});"
        "const ct=String(resp.headers.get('content-type')||'');"
        "if(resp.ok&&ct.indexOf('image/')===0){return u;}"
        "}catch(_e){}"
        "}"
        "return null;"
        "}"
        "async function loadSegPreview(pid, force){"
        "const key=String(pid);"
        "if(!force&&niiSegCache[key]){return niiSegCache[key];}"
        "const url=niiSegApiBase+key+(force?'?force=1':'');"
        "const resp=await fetch(url,{headers:{'Accept':'application/json'}});"
        "let js=null;"
        "try{js=await resp.json();}catch(_e){js=null;}"
        "if(!resp.ok||!js||!js.success){throw new Error((js&&js.message)?js.message:'分割失败');}"
        "niiSegCache[key]=js.url;"
        "return js.url;"
        "}"
        "function renderUploads(pid, name, data, previewsData){"
        "uploadsView.innerHTML='';"
        "const header=document.createElement('div');"
        "header.style.cssText='flex:0 0 auto;padding:12px 14px;font-size:20px;font-weight:600;color:#67FFFF;"
        "border-bottom:1px solid rgba(20,128,240,0.18);display:flex;align-items:center;justify-content:space-between;gap:10px;';"
        "const title=document.createElement('div');"
        "title.textContent='病理可视化';"
        "header.appendChild(title);"
        "const tabs=document.createElement('div');"
        "tabs.style.cssText='display:flex;gap:8px;';"
        "const btnA=document.createElement('button');"
        "btnA.type='button';"
        "btnA.textContent='A';"
        "btnA.style.cssText='width:34px;height:28px;border-radius:8px;border:1px solid rgba(103,255,255,0.65);"
        "background:rgba(103,255,255,0.22);color:#67FFFF;font-size:14px;cursor:pointer;pointer-events:auto;';"
        "const btnB=document.createElement('button');"
        "btnB.type='button';"
        "btnB.textContent='B';"
        "btnB.style.cssText='width:34px;height:28px;border-radius:8px;border:1px solid rgba(20,128,240,0.55);"
        "background:rgba(3,12,49,0.35);color:#EAF7FF;font-size:14px;cursor:pointer;pointer-events:auto;';"
        "tabs.appendChild(btnA);"
        "tabs.appendChild(btnB);"
        "header.appendChild(tabs);"
        "uploadsView.appendChild(header);"
        "const body=document.createElement('div');"
        "body.style.cssText='flex:1 1 auto;overflow:hidden;display:flex;align-items:center;justify-content:center;"
        "padding:10px 10px;';"
        "uploadsView.appendChild(body);"
        "const previews=(previewsData&&previewsData.previews)?previewsData.previews:[];"
        "if(previewsData&&previewsData.case_id){setSegCaseId(pid, previewsData.case_id);}"
        "let rawUrl=null;"
        "if(previews&&previews.length>0){"
        "const p=previews[0];"
        "if(p&&p.url){rawUrl=p.url;}"
        "}"
        "const img=document.createElement('img');"
        "img.style.cssText='display:block;width:100%;height:100%;object-fit:contain;background:rgba(0,0,0,0.65);border-radius:8px;';"
        "body.appendChild(img);"
        "let segRetry=0;"
        "function paintTab(){"
        "if(niiMode==='A'){"
        "btnA.style.background='rgba(103,255,255,0.22)';"
        "btnA.style.borderColor='rgba(103,255,255,0.65)';"
        "btnA.style.color='#67FFFF';"
        "btnB.style.background='rgba(3,12,49,0.35)';"
        "btnB.style.borderColor='rgba(20,128,240,0.55)';"
        "btnB.style.color='#EAF7FF';"
        "}else{"
        "btnB.style.background='rgba(103,255,255,0.18)';"
        "btnB.style.borderColor='rgba(103,255,255,0.55)';"
        "btnB.style.color='#67FFFF';"
        "btnA.style.background='rgba(3,12,49,0.35)';"
        "btnA.style.borderColor='rgba(20,128,240,0.55)';"
        "btnA.style.color='#EAF7FF';"
        "}"
        "}"
        "async function showMode(mode){"
        "niiMode=mode;"
        "paintTab();"
        "if(mode==='A'){"
        "if(!rawUrl){img.removeAttribute('src');return;}"
        "img.src=rawUrl+(rawUrl.indexOf('?')>-1?'&':'?')+'v='+(Date.now());"
        "return;"
        "}"
        "if(niiSegBusy){return;}"
        "niiSegBusy=true;"
        "img.onerror=null;"
        "img.removeAttribute('src');"
        "body.style.opacity='0.92';"
        "try{"
        "const localU=await tryLoadLocalSeg(pid);"
        "if(localU){"
        "img.onerror=null;"
        "img.src=localU;"
        "return;"
        "}"
        "const u=await loadSegPreview(pid,true);"
        "img.onerror=function(){"
        "if(segRetry>=1){"
        "img.onerror=null;"
        "img.removeAttribute('src');"
        "const tip=document.createElement('div');"
        "tip.style.cssText='padding:14px 10px;font-size:13px;opacity:0.9;';"
        "const scid=getCurrentSegCaseId();"
        "tip.textContent='分割加载失败：分割图不存在或无法加载'+(scid?('（case='+scid+'）'):'');"
        "body.innerHTML='';"
        "body.appendChild(tip);"
        "return;"
        "}"
        "segRetry=1;"
        "try{delete niiSegCache[String(pid)];}catch(_e){}"
        "niiSegBusy=true;"
        "loadSegPreview(pid,true).then(function(u2){"
        "img.src=u2+(u2.indexOf('?')>-1?'&':'?')+'v='+(Date.now());"
        "}).catch(function(err2){"
        "img.onerror=null;"
        "img.removeAttribute('src');"
        "const tip=document.createElement('div');"
        "tip.style.cssText='padding:14px 10px;font-size:13px;opacity:0.9;';"
        "tip.textContent='分割加载失败：'+(err2&&err2.message?err2.message:'');"
        "body.innerHTML='';"
        "body.appendChild(tip);"
        "}).finally(function(){niiSegBusy=false;});"
        "};"
        "img.src=u+(u.indexOf('?')>-1?'&':'?')+'v='+(Date.now());"
        "}catch(err){"
        "try{"
        "const msg=String(err&&err.message?err.message:'');"
        "if(msg.indexOf('seg_vis_unavailable')>-1){"
        "const u2=await loadSegPreview(pid,true);"
        "img.onerror=null;"
        "img.src=u2+(u2.indexOf('?')>-1?'&':'?')+'v='+(Date.now());"
        "return;"
        "}"
        "}catch(_e2){}"
        "img.removeAttribute('src');"
        "const tip=document.createElement('div');"
        "tip.style.cssText='padding:14px 10px;font-size:13px;opacity:0.9;';"
        "tip.textContent='分割加载失败：'+(err&&err.message?err.message:'');"
        "body.innerHTML='';"
        "body.appendChild(tip);"
        "}finally{niiSegBusy=false;body.style.opacity='1';}"
        "}"
        "btnA.addEventListener('click',function(ev){try{ev.preventDefault();ev.stopPropagation();}catch(_e){}showMode('A');});"
        "btnB.addEventListener('click',function(ev){try{ev.preventDefault();ev.stopPropagation();}catch(_e){}segRetry=0;showMode('B');});"
        "if(!rawUrl){"
        "const tip=document.createElement('div');"
        "tip.style.cssText='padding:14px 10px;font-size:13px;opacity:0.9;';"
        "tip.textContent=(previews&&previews.length&&previews[0]&&previews[0].error)?('预览生成失败：'+previews[0].error):'暂无预览';"
        "body.innerHTML='';"
        "body.appendChild(tip);"
        "niiMode='A';"
        "paintTab();"
        "return;"
        "}"
        "paintTab();"
        "showMode(niiMode==='B'?'B':'A');"
        "}"
        "async function loadUploads(pid,name){"
        "try{"
        "const pr=await fetch(niiPreviewsApiBase+String(pid));"
        "let previews=null;"
        "try{previews=await pr.json();}catch(_e){previews=null;}"
        "if(!pr.ok||!previews||!previews.success){"
        "const msg=(previews&&previews.message)?previews.message:('加载 '+(name||'')+' 的NII预览失败');"
        "uploadsView.textContent=msg;"
        "return;"
        "}"
        "renderUploads(pid, name, previews, previews);"
        "}catch(e){uploadsView.textContent='加载 '+(name||'')+' 的NII预览失败';}"
        "}"
        "function addField(container,label,value){"
        "if(value===undefined||value===null||String(value).trim()===''){return;}"
        "const row=document.createElement('div');"
        "row.style.cssText='margin:8px 0;line-height:1.5;';"
        "const k=document.createElement('div');"
        "k.style.cssText='font-size:16px;font-weight:700;color:rgba(103,255,255,0.9);margin-bottom:4px;';"
        "k.textContent=label;"
        "const v=document.createElement('div');"
        "v.style.cssText='white-space:pre-wrap;font-size:14px;';"
        "v.textContent=String(value);"
        "row.appendChild(k);"
        "row.appendChild(v);"
        "container.appendChild(row);"
        "}"
        "function renderDiagnosis(data){"
        "reportBox.innerHTML='';"
        "const title=document.createElement('div');"
        "title.style.cssText='font-size:20px;font-weight:600;margin-bottom:10px;color:#67FFFF;';"
        "title.textContent=(data.patient&&data.patient.name?data.patient.name:'病人')+' 诊断报告';"
        "reportBox.appendChild(title);"
        "const d=data.diagnosis||null;"
        "if(!d){return;}"
        "addField(reportBox,'诊断日期', d.diagnosis_date);"
        "addField(reportBox,'诊断类型', d.diagnosis_type);"
        "addField(reportBox,'肿瘤类型', d.tumor_type);"
        "addField(reportBox,'肿瘤分期', d.tumor_stage);"
        "addField(reportBox,'诊断医生', d.doctor_name);"
        "addField(reportBox,'诊断内容', d.diagnosis_content);"
        "addField(reportBox,'治疗方案', d.treatment_plan);"
        "addField(reportBox,'检查结果', d.examination_results);"
        "addField(reportBox,'备注', d.notes);"
        "}"
        "function renderAgent(data){"
        "analysisView.innerHTML='';"
        "analysisHeaderTitle.textContent=(data.patient&&data.patient.name?data.patient.name:'病人')+' 智能分析';"
        "const a=data.agent||null;"
        "if(!a){analysisView.textContent=(data.patient&&data.patient.name?data.patient.name:'该病人')+' 暂无智能分析结果';return;}"
        "addField(analysisView,'严重程度', a.severity_assessment);"
        "addField(analysisView,'可能诊断', a.possible_diagnosis);"
        "addField(analysisView,'肿瘤位置', a.tumor_location);"
        "addField(analysisView,'分析', a.tumor_analysis);"
        "addField(analysisView,'建议', a.recommendation);"
        "addField(analysisView,'置信度', a.confidence);"
        "addField(analysisView,'置信原因', a.confidence_reason);"
        "addField(analysisView,'备注', a.remarks);"
        "}"
        "function renderDebate(data){"
        "analysisView.innerHTML='';"
        "analysisHeaderTitle.textContent=(data.patient&&data.patient.name?data.patient.name:'病人')+' 多专家辩论过程';"
        "const a=data.agent||null;"
        "if(!a){analysisView.textContent=(data.patient&&data.patient.name?data.patient.name:'该病人')+' 暂无智能分析结果';return;}"
        "let raw=a.raw_output;"
        "try{if(typeof raw==='string'){raw=JSON.parse(raw);}}catch(_e){raw=null;}"
        "let trace=null;"
        "try{"
        "if(a.debate_trace){trace=a.debate_trace;}"
        "else if(raw&&raw.debate_trace){trace=raw.debate_trace;}"
        "else if(raw&&raw.initial_results&&raw.critiques){trace=raw;}"
        "}catch(_e2){trace=null;}"
        "if(!trace){"
        "const tip=document.createElement('div');"
        "tip.style.cssText='padding:6px 0 12px 0;font-size:14px;line-height:1.6;';"
        "tip.textContent='暂无多专家辩论过程（需要重新生成并启用 trace）。';"
        "analysisView.appendChild(tip);"
        "const did=data&&data.diagnosis&&data.diagnosis.id?String(data.diagnosis.id):'';"
        "if(!did){return;}"
        "const btn=document.createElement('button');"
        "btn.type='button';"
        "btn.textContent='生成辩论过程';"
        "btn.style.cssText='border-radius:8px;border:1px solid rgba(103,255,255,0.65);"
        "background:rgba(103,255,255,0.15);color:#67FFFF;padding:8px 12px;font-size:14px;cursor:pointer;';"
        "btn.addEventListener('click',async function(){"
        "try{"
        "btn.disabled=true;"
        "btn.textContent='生成中...';"
        "const u=agentRunApiBase+did+'?trace=1&strategy=debate';"
        "const resp=await fetch(u,{method:'POST',headers:{'Accept':'application/json'}});"
        "let js=null;"
        "try{js=await resp.json();}catch(_e3){js=null;}"
        "if(!resp.ok||!js||!js.success){"
        "btn.disabled=false;"
        "btn.textContent='生成失败，重试';"
        "const m=(js&&js.message)?js.message:'生成失败';"
        "const err=document.createElement('div');"
        "err.style.cssText='margin-top:10px;font-size:13px;opacity:0.9;';"
        "err.textContent=m;"
        "analysisView.appendChild(err);"
        "return;"
        "}"
        "if(currentReport){currentReport.agent=js.data||currentReport.agent;}"
        "renderDebate(currentReport||data);"
        "}catch(e){"
        "btn.disabled=false;"
        "btn.textContent='生成失败，重试';"
        "}"
        "});"
        "analysisView.appendChild(btn);"
        "return;"
        "}"
        "function addSection(t){"
        "const h=document.createElement('div');"
        "h.style.cssText='font-size:16px;font-weight:700;margin:10px 0 6px 0;color:#67FFFF;';"
        "h.textContent=t;"
        "analysisView.appendChild(h);"
        "}"
        "function addPre(obj){"
        "const pre=document.createElement('pre');"
        "pre.style.cssText='white-space:pre-wrap;word-break:break-word;font-size:13px;line-height:1.45;"
        "background:rgba(3,12,49,0.35);border:1px solid rgba(20,128,240,0.28);border-radius:10px;padding:10px 10px;margin:0 0 10px 0;';"
        "try{pre.textContent=JSON.stringify(obj,null,2);}catch(_e){pre.textContent=String(obj||'');}"
        "analysisView.appendChild(pre);"
        "}"
        "addSection('最终融合结论');"
        "addPre(trace.final_result||{});"
        "addSection('初始观点');"
        "addPre(trace.initial_results||[]);"
        "addSection('互评意见');"
        "addPre(trace.critiques||[]);"
        "addSection('修正观点');"
        "addPre(trace.revised_results||[]);"
        "}"
        "function setAnalysisMode(mode){"
        "analysisMode=mode;"
        "paintAnalysisTab();"
        "if(mode==='A'){"
        "chatWrap.style.display='flex';"
        "analysisView.style.height='368px';"
        "analysisView.style.borderBottom='1px solid rgba(20,128,240,0.35)';"
        "if(currentReport){renderAgent(currentReport);}else{analysisView.textContent='暂无智能分析结果';}"
        "return;"
        "}"
        "chatWrap.style.display='none';"
        "analysisView.style.height='708px';"
        "analysisView.style.borderBottom='none';"
        "if(currentReport){renderDebate(currentReport);}else{analysisView.textContent='暂无多专家辩论过程';}"
        "}"
        "analysisBtnA.addEventListener('click',function(ev){try{ev.preventDefault();ev.stopPropagation();}catch(_e){}setAnalysisMode('A');});"
        "analysisBtnB.addEventListener('click',function(ev){try{ev.preventDefault();ev.stopPropagation();}catch(_e){}setAnalysisMode('B');});"
        "async function loadPatientReport(pid,name){"
        "renderReportLoading(name);"
        "resetChat(pid,name);"
        "loadUploads(pid,name);"
        "loadSpin(pid);"
        "try{"
        "const resp=await fetch(reportApiBase+String(pid));"
        "const js=await resp.json();"
        "if(!js||!js.success){renderReportError(name);return;}"
        "currentReport=js;"
        "renderDiagnosis(js);"
        "setAnalysisMode('A');"
        "}catch(e){renderReportError(name);}"
        "}"
        "const leftNav=stageRoot.querySelector(\"[data-layer='左侧导航']\");"
        "if(leftNav){"
        "const titleNode=leftNav.querySelector(\"[data-layer='标题场景']\");"
        "if(titleNode){"
        "titleNode.style.cursor='pointer';"
        "titleNode.addEventListener('click',function(){window.location.href=patientsUrl;});"
        "}"
        "}"
        "const homeNode=stageRoot.querySelector(\"[data-layer='首页']\");"
        "if(homeNode){"
        "const btn=homeNode.closest('.Btn')||homeNode;"
        "btn.style.display='none';"
        "}"
        "const test1Node=stageRoot.querySelector(\"[data-layer='测试1']\");"
        "if(test1Node){"
        "const btn=test1Node.closest('.Btn')||test1Node;"
        "btn.style.cursor='pointer';"
        "btn.addEventListener('click',function(){window.location.href=test1Url;});"
        "}"
        "const patientCenterNode=stageRoot.querySelector(\"[data-layer='病人中心']\");"
        "if(patientCenterNode){"
        "const btn=patientCenterNode.closest('.Btn')||patientCenterNode;"
        "btn.style.cursor='pointer';"
        "btn.addEventListener('click',function(){window.location.href=patientPortalUrl;});"
        "}"
        "const doctorCenterNode=stageRoot.querySelector(\"[data-layer='医生中心']\");"
        "if(doctorCenterNode){"
        "const btn=doctorCenterNode.closest('.Btn')||doctorCenterNode;"
        "btn.style.cursor='pointer';"
        "btn.addEventListener('click',function(){window.location.href=doctorsUrl;});"
        "}"
        "const userNode=stageRoot.querySelector(\"[data-layer='张小花']\");"
        "if(userNode&&currentUsername){userNode.textContent=currentUsername;}"
        "const accountNode=stageRoot.querySelector(\"[data-layer='账号']\");"
        "if(accountNode){"
        "const triangleNode=accountNode.querySelector(\"[data-layer='三角形']\");"
        "const dropdown=document.createElement('div');"
        "dropdown.id='portalUserDropdown';"
        "dropdown.style.cssText="
        "'position:fixed;left:0;top:0;min-width:134px;display:none;z-index:2147483647;"
        "background:rgba(3,12,49,0.92);border:1px solid rgba(102,255,255,0.45);"
        "border-radius:8px;overflow:hidden;backdrop-filter:blur(6px);';"
        "const logoutItem=document.createElement('a');"
        "logoutItem.href=logoutUrl;"
        "logoutItem.textContent='退出登录';"
        "logoutItem.style.cssText="
        "'display:block;padding:12px 14px;color:#FFFFFF;text-decoration:none;font-size:14px;"
        "font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;"
        "background:transparent;white-space:nowrap;text-align:center;';"
        "logoutItem.addEventListener('mouseover',function(){logoutItem.style.background='rgba(103,255,255,0.15)';});"
        "logoutItem.addEventListener('mouseout',function(){logoutItem.style.background='transparent';});"
        "dropdown.appendChild(logoutItem);"
        "const originalItem=document.createElement('a');"
        "originalItem.href=originalMainUrl;"
        "originalItem.textContent='原版';"
        "originalItem.style.cssText="
        "'display:block;padding:12px 14px;color:#FFFFFF;text-decoration:none;font-size:14px;"
        "font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;"
        "background:transparent;white-space:nowrap;text-align:center;';"
        "originalItem.addEventListener('mouseover',function(){originalItem.style.background='rgba(103,255,255,0.15)';});"
        "originalItem.addEventListener('mouseout',function(){originalItem.style.background='transparent';});"
        "dropdown.appendChild(originalItem);"
        "document.body.appendChild(dropdown);"
        "function setTriangle(open){"
        "if(!triangleNode){return;}"
        "triangleNode.style.transition='transform 120ms ease';"
        "triangleNode.style.transform=open?'rotate(180deg)':'';"
        "triangleNode.style.transformOrigin='50% 50%';"
        "}"
        "function positionDropdown(){"
        "const rect=accountNode.getBoundingClientRect();"
        "dropdown.style.left=Math.round(rect.left)+'px';"
        "dropdown.style.top=Math.round(rect.bottom+6)+'px';"
        "dropdown.style.minWidth=Math.round(rect.width)+'px';"
        "}"
        "function openDropdown(ev){"
        "if(ev){ev.preventDefault();ev.stopPropagation();}"
        "positionDropdown();"
        "dropdown.style.display='block';"
        "setTriangle(true);"
        "}"
        "function closeDropdown(){"
        "dropdown.style.display='none';"
        "setTriangle(false);"
        "}"
        "function toggleDropdown(ev){"
        "if(dropdown.style.display==='block'){closeDropdown();return;}"
        "openDropdown(ev);"
        "}"
        "if(triangleNode){triangleNode.style.cursor='pointer';triangleNode.addEventListener('click',toggleDropdown);}"
        "window.addEventListener('resize',function(){if(dropdown.style.display==='block'){positionDropdown();}});"
        "document.addEventListener('click',function(){closeDropdown();});"
        "dropdown.addEventListener('click',function(ev){ev.stopPropagation();});"
        "}"
        "let patientListScope=leftNav||stageRoot;"
        "if(leftNav){"
        "let listScroll=document.getElementById('portalPatientListScroll');"
        "if(!listScroll){"
        "listScroll=document.createElement('div');"
        "listScroll.id='portalPatientListScroll';"
        "listScroll.style.cssText="
        "'position:absolute;left:0;top:145px;width:100%;height:calc(100% - 145px);"
        "overflow-y:scroll;overflow-x:hidden;pointer-events:auto;box-sizing:border-box;padding-right:18px;"
        "scrollbar-gutter:stable;scrollbar-width:thin;"
        "scrollbar-color:rgba(103,255,255,0.75) rgba(3,12,49,0.25);';"
        "leftNav.appendChild(listScroll);"
        "}"
        "let listScrollBar=document.getElementById('portalPatientListScrollBar');"
        "if(!listScrollBar){"
        "listScrollBar=document.createElement('div');"
        "listScrollBar.id='portalPatientListScrollBar';"
        "listScrollBar.style.cssText="
        "'position:absolute;right:18px;top:185px;height:calc(100% - 205px);width:8px;"
        "background:rgba(3,12,49,0.20);border:1px solid rgba(103,255,255,0.18);"
        "border-radius:999px;pointer-events:none;z-index:9999;';"
        "const thumb=document.createElement('div');"
        "thumb.id='portalPatientListScrollThumb';"
        "thumb.style.cssText='position:absolute;left:0;top:0;width:100%;height:40px;"
        "background:rgba(103,255,255,0.55);border-radius:999px;';"
        "listScrollBar.appendChild(thumb);"
        "leftNav.appendChild(listScrollBar);"
        "}"
        "const styleId='portalPatientListScrollStyle';"
        "if(!document.getElementById(styleId)){"
        "const st=document.createElement('style');"
        "st.id=styleId;"
        "st.textContent="
        "'#portalPatientListScroll::-webkit-scrollbar{width:10px;}"
        "#portalPatientListScroll::-webkit-scrollbar-track{background:rgba(3,12,49,0.22);border-radius:10px;}"
        "#portalPatientListScroll::-webkit-scrollbar-thumb{background:rgba(103,255,255,0.55);border:1px solid rgba(103,255,255,0.35);border-radius:10px;}"
        "#portalPatientListScroll::-webkit-scrollbar-thumb:hover{background:rgba(103,255,255,0.7);}';"
        "document.head.appendChild(st);"
        "}"
        "const toMove=Array.from(leftNav.querySelectorAll('.List'));"
        "for(let i=0;i<toMove.length;i++){"
        "const el=toMove[i];"
        "let t=parseFloat(el.style.top||'0');"
        "if(isFinite(t)){el.style.top=(t-145)+'px';}"
        "listScroll.appendChild(el);"
        "}"
        "function updatePatientScrollThumb(){"
        "try{"
        "const bar=listScrollBar;"
        "const thumb=document.getElementById('portalPatientListScrollThumb');"
        "if(!bar||!thumb){return;}"
        "const ch=listScroll.clientHeight||0;"
        "const sh=listScroll.scrollHeight||0;"
        "bar.style.display='block';"
        "const bh=bar.clientHeight||0;"
        "if(sh<=ch+1){"
        "thumb.style.height=Math.max(26,bh)+'px';"
        "thumb.style.top='0px';"
        "thumb.style.opacity='0.25';"
        "return;"
        "}"
        "thumb.style.opacity='1';"
        "const ratio=Math.min(1, Math.max(0, ch/sh));"
        "const th=Math.max(26, Math.round(bh*ratio));"
        "const maxTop=Math.max(0, bh-th);"
        "const maxScroll=Math.max(1, sh-ch);"
        "const tt=Math.round((listScroll.scrollTop/maxScroll)*maxTop);"
        "thumb.style.height=th+'px';"
        "thumb.style.top=tt+'px';"
        "}catch(_e){}"
        "}"
        "listScroll.addEventListener('scroll',updatePatientScrollThumb);"
        "window.addEventListener('resize',updatePatientScrollThumb);"
        "setTimeout(updatePatientScrollThumb,0);"
        "patientListScope=listScroll;"
        "}"
        "const scope=patientListScope||leftNav||stageRoot;"
        "const hoverNodes=scope.querySelectorAll(\"[data-layer='hover效果']\");"
        "for(let j=0;j<hoverNodes.length;j++){"
        "const list=hoverNodes[j].closest('.List');"
        "if(list){list.style.display='none';}"
        "}"
        "let lists=Array.from(scope.querySelectorAll('.List'));"
        "lists.sort(function(a,b){"
        "const at=parseFloat(a.style.top||'0');"
        "const bt=parseFloat(b.style.top||'0');"
        "return at-bt;"
        "});"
        "if(patientListScope&&patientListScope.id==='portalPatientListScroll'){"
        "for(let i=0;i<lists.length;i++){scope.appendChild(lists[i]);}"
        "}"
        "if(patientListScope&&patientListScope.id==='portalPatientListScroll'){"
        "patientListScope.style.display='flex';"
        "patientListScope.style.flexDirection='column';"
        "patientListScope.style.gap='11px';"
        "patientListScope.style.paddingLeft='31px';"
        "patientListScope.style.paddingTop='10px';"
        "patientListScope.style.paddingBottom='10px';"
        "}"
        "const labelSelector=\"[data-layer='壹级栏目'],[data-layer='数字可视化']\";"
        "const labelTops=[];"
        "for(let i=0;i<lists.length;i++){"
        "const l=lists[i];"
        "const lab=l.querySelector(labelSelector);"
        "if(!lab){continue;}"
        "const t=parseFloat(l.style.top||'0');"
        "if(isFinite(t)){labelTops.push(t);}"
        "}"
        "labelTops.sort(function(a,b){return a-b;});"
        "let baseTop=labelTops.length?labelTops[0]:0;"
        "let step=57;"
        "for(let i=1;i<labelTops.length;i++){"
        "const d=labelTops[i]-labelTops[i-1];"
        "if(d>30&&d<120){step=Math.min(step,d);}"
        "}"
        "const patientItems=[];"
        "let activeIndex=-1;"
        "const inactiveBg='linear-gradient(90deg, rgba(103, 255, 255, 0.20) 0%, rgba(137.11, 251.02, 255, 0.09) 41%, rgba(163, 248, 255, 0) 100%)';"
        "const activeBg='linear-gradient(90deg, rgba(103, 255, 255, 0.60) 0%, rgba(137.11, 251.02, 255, 0.26) 41%, rgba(163, 248, 255, 0) 100%)';"
        "function getListBg(list){"
        "const rects=list.querySelectorAll(\"div[data-layer='矩形']\");"
        "return rects&&rects.length?rects[0]:null;"
        "}"
        "function createCaret(list){"
        "const old=list.querySelector(\"[data-svg-wrapper][data-layer='形状']\");"
        "if(old){old.style.display='none';}"
        "const caret=document.createElement('div');"
        "caret.style.cssText="
        "'position:absolute;right:22px;top:18px;width:0;height:0;"
        "border-left:7px solid transparent;border-right:7px solid transparent;"
        "border-top:8px solid rgba(103,255,255,0.95);"
        "filter:drop-shadow(0 0 4px rgba(103,255,255,0.55));"
        "transform:rotate(0deg);transform-origin:50% 40%;transition:transform 120ms ease;"
        "z-index:1000;pointer-events:none;';"
        "list.appendChild(caret);"
        "return caret;"
        "}"
        "function setActiveIndex(nextIndex){"
        "if(nextIndex===activeIndex){return;}"
        "for(let i=0;i<patientItems.length;i++){"
        "const item=patientItems[i];"
        "if(item.bg){item.bg.style.background=inactiveBg;}"
        "if(item.caret){item.caret.style.transform='rotate(0deg)';}"
        "}"
        "if(nextIndex>=0&&nextIndex<patientItems.length){"
        "const item=patientItems[nextIndex];"
        "if(item.bg){item.bg.style.background=activeBg;}"
        "if(item.caret){item.caret.style.transform='rotate(180deg)';}"
        "}"
        "activeIndex=nextIndex;"
        "}"
        "for(let k=0;k<lists.length;k++){"
        "const list=lists[k];"
        "list.style.position='relative';"
        "list.style.left='0px';"
        "list.style.top='0px';"
        "}"
        "const templateList=(function(){"
        "for(let i=0;i<lists.length;i++){"
        "if(lists[i].querySelector(labelSelector)){return lists[i];}"
        "}"
        "return lists.length?lists[0]:null;"
        "})();"
        "if(templateList&&patientNames.length>lists.length){"
        "for(let i=lists.length;i<patientNames.length;i++){"
        "const clone=templateList.cloneNode(true);"
        "clone.style.position='relative';"
        "clone.style.left='0px';"
        "clone.style.top='0px';"
        "clone.style.display='block';"
        "scope.appendChild(clone);"
        "lists.push(clone);"
        "}"
        "}"
        "let idx=0;"
        "for(let k=0;k<lists.length;k++){"
        "const list=lists[k];"
        "const label=list.querySelector(labelSelector);"
        "if(!label){list.style.display='none';continue;}"
        "if(idx<patientNames.length){"
        "const thisIdx=idx;"
        "patientItems.push({list:list,bg:getListBg(list),caret:createCaret(list)});"
        "label.textContent=patientNames[thisIdx];"
        "list.style.cursor='pointer';"
        "list.addEventListener('click',function(){"
        "const pid=patientIds[thisIdx];"
        "setActiveIndex(thisIdx);"
        "if(pid){loadPatientReport(pid, patientNames[thisIdx]);}"
        "});"
        "idx++;"
        "}else{"
        "list.style.display='none';"
        "}"
        "}"
        "if(patientIds.length>0){setActiveIndex(0);loadPatientReport(patientIds[0], patientNames[0]);}"
        "}catch(e){}"
        "})();"
        "</script>"
        "</body></html>"
    )
    resp = make_response(full_html)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

@app.route('/doctor_portal')
@login_required
def doctor_portal():
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))

    ui_path = os.path.join(os.path.dirname(__file__), "UI", "test5.txt")
    try:
        with open(ui_path, "r", encoding="utf-8") as f:
            inner_html = f.read()
    except Exception:
        return redirect(url_for('doctors'))

    entry_url = url_for('main_interface')
    patient_portal_url = url_for('patient_portal')
    doctor_portal_url = url_for('doctor_portal')
    doctors_page_url = url_for('doctors')
    test1_url = url_for('test1_interface')
    logout_url = url_for('logout')
    doctors_api = url_for('api_doctors')
    current_username_json = json.dumps(str(getattr(current_user, "username", "") or ""), ensure_ascii=False)

    full_html = (
        "<!DOCTYPE html><html lang='zh-CN'><head>"
        "<meta charset='UTF-8'>"
        "<title>医生中心</title>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<style>"
        "html,body{width:100%;height:100%;margin:0;overflow:hidden;background:#030C31;}"
        "svg,img{display:block;}"
        "#doctorStage *{box-sizing:border-box;}"
        "#doctorViewport{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;}"
        "#doctorStage{width:1920px;height:1080px;transform-origin:50% 50%;}"
        "</style>"
        "</head><body>"
        "<div id='doctorViewport'><div id='doctorStage'>"
        f"{inner_html}"
        "</div></div>"
        "<script>"
        "(function(){"
        "const stage=document.getElementById('doctorStage');"
        "function fit(){"
        "const vw=window.innerWidth||1920;"
        "const vh=window.innerHeight||1080;"
        "const scale=Math.min(vw/1920,vh/1080);"
        "stage.style.transform='scale('+scale+')';"
        "}"
        "window.addEventListener('resize',fit);"
        "fit();"
        f"const entryUrl={json.dumps(entry_url, ensure_ascii=False)};"
        f"const patientPortalUrl={json.dumps(patient_portal_url, ensure_ascii=False)};"
        f"const doctorPortalUrl={json.dumps(doctor_portal_url, ensure_ascii=False)};"
        f"const doctorsPageUrl={json.dumps(doctors_page_url, ensure_ascii=False)};"
        f"const test1Url={json.dumps(test1_url, ensure_ascii=False)};"
        f"const logoutUrl={json.dumps(logout_url, ensure_ascii=False)};"
        f"const doctorsApi={json.dumps(doctors_api, ensure_ascii=False)};"
        f"const currentUsername={current_username_json};"
        "try{"
        "const stageRoot=document.getElementById('doctorStage');"
        "const top=stageRoot.querySelector(\"[data-layer='top']\");"
        "if(top){"
        "let tplBtn=null;"
        "try{"
        "const homeNode=top.querySelector(\"[data-layer='首页']\");"
        "const homeBtn=homeNode?(homeNode.closest('.Btn')||homeNode):null;"
        "if(homeBtn){tplBtn=homeBtn;}"
        "const digitalNode=top.querySelector(\"[data-layer='数字中心']\");"
        "const digitalBtn=digitalNode?(digitalNode.closest('.Btn')||digitalNode):null;"
        "if(!tplBtn&&digitalBtn){tplBtn=digitalBtn;}"
        "if(homeBtn){homeBtn.remove();}"
        "if(digitalBtn){digitalBtn.remove();}"
        "}catch(_e){}"
        "function makeTopBtn(text,leftPx,onClick){"
        "if(!tplBtn){return null;}"
        "const b=tplBtn.cloneNode(true);"
        "b.style.left=leftPx+'px';"
        "b.style.top='32px';"
        "b.style.cursor='pointer';"
        "const label=b.querySelector(\"[data-layer='首页'],[data-layer='数字中心'],[data-layer='测试1'],[data-layer='病人中心'],[data-layer='医生中心']\");"
        "if(label){label.textContent=text;}"
        "b.addEventListener('click',function(ev){try{ev.stopPropagation();}catch(_e){} onClick();});"
        "top.appendChild(b);"
        "return b;"
        "}"
        "makeTopBtn('原版',1212,function(){window.location.href=entryUrl;});"
        "makeTopBtn('首页',1350,function(){window.location.href=test1Url;});"
        "makeTopBtn('病人中心',1488,function(){window.location.href=patientPortalUrl;});"
        "makeTopBtn('医生中心',1626,function(){window.location.href=doctorPortalUrl;});"
        "const userNode=top.querySelector(\"[data-layer='张小花']\");"
        "if(userNode&&currentUsername){userNode.textContent=currentUsername;}"
        "const accountNode=top.querySelector(\"[data-layer='账号']\");"
        "if(accountNode){"
        "const dropdown=document.createElement('div');"
        "dropdown.style.cssText='position:fixed;left:0;top:0;min-width:134px;display:none;z-index:2147483647;"
        "background:rgba(3,12,49,0.92);border:1px solid rgba(102,255,255,0.45);"
        "border-radius:8px;overflow:hidden;backdrop-filter:blur(6px);';"
        "const patientBtn=document.createElement('button');"
        "patientBtn.type='button';"
        "patientBtn.textContent='病人中心';"
        "patientBtn.style.cssText='display:block;width:100%;padding:10px 12px;background:transparent;border:0;color:#EAF7FF;"
        "text-align:left;cursor:pointer;font-size:14px;';"
        "patientBtn.addEventListener('click',function(){window.location.href=patientPortalUrl;});"
        "const logoutBtn=document.createElement('button');"
        "logoutBtn.type='button';"
        "logoutBtn.textContent='退出登录';"
        "logoutBtn.style.cssText='display:block;width:100%;padding:10px 12px;background:transparent;border:0;color:#EAF7FF;"
        "text-align:left;cursor:pointer;font-size:14px;';"
        "logoutBtn.addEventListener('click',function(){window.location.href=logoutUrl;});"
        "dropdown.appendChild(patientBtn);"
        "dropdown.appendChild(logoutBtn);"
        "document.body.appendChild(dropdown);"
        "function hide(){dropdown.style.display='none';}"
        "function show(){"
        "const r=accountNode.getBoundingClientRect();"
        "dropdown.style.left=Math.max(8,Math.min(window.innerWidth-160,r.right-134))+'px';"
        "dropdown.style.top=(r.bottom+6)+'px';"
        "dropdown.style.display='block';"
        "}"
        "accountNode.style.cursor='pointer';"
        "accountNode.addEventListener('click',function(ev){try{ev.stopPropagation();}catch(_e){}"
        "if(dropdown.style.display==='block'){hide();}else{show();}});"
        "window.addEventListener('click',hide);"
        "}"
        "}"

        "function replaceUiText(){"
        "try{"
        "const root=stageRoot;"
        "const exactMap={"
        "'今日受理工单':'今日受理病例',"
        "'今日工单':'今日病例',"
        "'月度工单类型概况':'月度病例类型概况',"
        "'本月受理工单':'本月受理病例',"
        "'月度受理工单概况':'月度受理病例情况',"
        "'受理工单总数':'受理病例总数',"
        "'平均处理时长':'平均诊断时长',"
        "'月度服务评分':'月度病例评分',"
        "'已处理':'已受理',"
        "'未完成':'待复核',"
        "'已完成':'已归档'"
        "};"
        "for(const k in exactMap){"
        "const v=exactMap[k];"
        "const nodes=root.querySelectorAll(\"[data-layer='\"+k+\"']\");"
        "for(let i=0;i<nodes.length;i++){"
        "const n=nodes[i];"
        "if(n&&n.childElementCount===0){n.textContent=v;}"
        "}"
        "}"
        "const subs=["
        "['今日工单','今日病例'],"
        "['本月受理工单','本月受理病例'],"
        "['受理工单总数','受理病例总数'],"
        "['待受理','待处理'],"
        "['共计工单','共计病例'],"
        "['物业报修总数','脑膜瘤病例数'],"
        "['设备保修总数','胶质瘤病例数'],"
        "['物业报修','脑膜瘤'],"
        "['设备故障','胶质瘤'],"
        "['类型三','垂体瘤'],"
        "['类型四','听神经瘤']"
        "];"
        "const all=root.querySelectorAll('div');"
        "for(let i=0;i<all.length;i++){"
        "const el=all[i];"
        "if(!el){continue;}"
        "if(el.childElementCount===0){"
        "let t=el.textContent||'';"
        "let changed=false;"
        "for(let j=0;j<subs.length;j++){"
        "const a=subs[j][0];"
        "const b=subs[j][1];"
        "if(t&&t.indexOf(a)>=0){t=t.split(a).join(b);changed=true;}"
        "}"
        "if(changed){el.textContent=t;}"
        "continue;"
        "}"
        "let brOnly=true;"
        "for(let c=0;c<el.children.length;c++){"
        "if(el.children[c].tagName!=='BR'){brOnly=false;break;}"
        "}"
        "if(brOnly){"
        "let html=el.innerHTML;"
        "let changed=false;"
        "for(let j=0;j<subs.length;j++){"
        "const a=subs[j][0];"
        "const b=subs[j][1];"
        "if(html&&html.indexOf(a)>=0){html=html.split(a).join(b);changed=true;}"
        "}"
        "if(changed){el.innerHTML=html;}"
        "}"
        "}"
        "}catch(_e){}"
        "}"
        "replaceUiText();"

        "function el(tag, css){const n=document.createElement(tag); if(css){n.style.cssText=css;} return n;}"
        "function hudCard(css){return el('div','background:rgba(3,12,49,0.38);border:1px solid rgba(102,255,255,0.25);border-radius:14px;box-shadow:0 0 22px rgba(20,128,240,0.12) inset;'+(css||''));}"
        ""
        "const leftNav=stageRoot.querySelector(\"[data-layer='左侧导航']\");"
        "const labelSelector=\"[data-layer='壹级栏目'],[data-layer='数字可视化']\";"
        "let navLists=[];"
        "if(leftNav){"
        "const circles=leftNav.querySelectorAll(\"[data-layer='选择器']\");"
        "for(let i=0;i<circles.length;i++){circles[i].style.display='none';}"
        "const ringShapes=leftNav.querySelectorAll(\"[data-svg-wrapper][data-layer='形状']\");"
        "for(let i=0;i<ringShapes.length;i++){"
        "const n=ringShapes[i];"
        "const t=parseFloat(n.style.top||'9999');"
        "const l=parseFloat(n.style.left||'9999');"
        "const svg=n.querySelector('svg');"
        "const w=svg?parseFloat(svg.getAttribute('width')||'0'):0;"
        "const h=svg?parseFloat(svg.getAttribute('height')||'0'):0;"
        "if(t<30&&l<80&&w>=80&&h<=80){"
        "n.style.display='none';"
        "}"
        "}"
        "const hoverText=leftNav.querySelector(\"[data-layer='hover效果']\");"
        "if(hoverText){const host=hoverText.closest('.List')||hoverText.parentElement; if(host){host.style.display='none';}}"
        "const titleScene=leftNav.querySelector(\"[data-layer='标题场景']\");"
        "if(titleScene){"
        "titleScene.style.display='block';"
        "titleScene.textContent='医生管理';"
        "titleScene.style.cursor='pointer';"
        "titleScene.style.userSelect='none';"
        "titleScene.addEventListener('click',function(ev){try{ev.stopPropagation();}catch(_e){} window.location.href=doctorsPageUrl;});"
        "}"
        "navLists=Array.from(leftNav.querySelectorAll('.List'));"
        "navLists=navLists.filter(function(n){return !n.querySelector(\"[data-layer='hover效果']\");});"
        "navLists.sort(function(a,b){return (parseFloat(a.style.top||'0')||0)-(parseFloat(b.style.top||'0')||0);});"
        "}"
        "function listLabel(list){return list?list.querySelector(labelSelector):null;}"
        "const inactiveBg='linear-gradient(90deg, rgba(103, 255, 255, 0.20) 0%, rgba(137.11, 251.02, 255, 0.09) 41%, rgba(163, 248, 255, 0) 100%)';"
        "const activeBg='linear-gradient(90deg, rgba(103, 255, 255, 0.60) 0%, rgba(137.11, 251.02, 255, 0.26) 41%, rgba(163, 248, 255, 0) 100%)';"
        "function getListBg(list){"
        "const rects=list.querySelectorAll(\"div[data-layer='矩形']\");"
        "return rects&&rects.length?rects[0]:null;"
        "}"
        "function createCaret(list){"
        "const olds=list.querySelectorAll(\"[data-svg-wrapper][data-layer='形状']\");"
        "for(let i=0;i<olds.length;i++){olds[i].style.display='none';}"
        "const exist=list.querySelector('.portal-caret');"
        "if(exist){exist.remove();}"
        "const caret=document.createElement('div');"
        "caret.className='portal-caret';"
        "caret.style.cssText="
        "'position:absolute;right:22px;top:18px;width:0;height:0;"
        "border-left:7px solid transparent;border-right:7px solid transparent;"
        "border-top:8px solid rgba(103,255,255,0.95);"
        "filter:drop-shadow(0 0 4px rgba(103,255,255,0.55));"
        "transform:rotate(0deg);transform-origin:50% 40%;transition:transform 120ms ease;"
        "z-index:1000;pointer-events:none;';"
        "list.appendChild(caret);"
        "return caret;"
        "}"
        "const doctorItems=[];"
        "let activeDoctorIndex=-1;"
        "function setActiveList(nextIndex){"
        "if(nextIndex===activeDoctorIndex){return;}"
        "for(let i=0;i<doctorItems.length;i++){"
        "const it=doctorItems[i];"
        "if(it.bg){it.bg.style.background=inactiveBg;}"
        "if(it.caret){it.caret.style.transform='rotate(0deg)';}"
        "}"
        "if(nextIndex>=0&&nextIndex<doctorItems.length){"
        "const it=doctorItems[nextIndex];"
        "if(it.bg){it.bg.style.background=activeBg;}"
        "if(it.caret){it.caret.style.transform='rotate(180deg)';}"
        "}"
        "activeDoctorIndex=nextIndex;"
        "}"
        ""
        "const overlay=el('div');"
        "overlay.id='doctorCenterOverlay';"
        "overlay.style.cssText='position:absolute;left:404px;top:130px;width:860px;height:640px;z-index:20;pointer-events:auto;"
        "padding:0;display:block;font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;color:#EAF7FF;';"
        "(stageRoot||document.body).appendChild(overlay);"
        "function parsePx(v){"
        "const n=parseFloat(String(v||'').replace('px',''));"
        "return isFinite(n)?n:null;"
        "}"
        "function fitOverlay(){"
        "try{"
        "const overlayLeft=404;"
        "const overlayTop=130;"
        "let rightStart=null;"
        "const rightAnchors=['今日受理工单','今日受理病例','任务代办','核心指标'];"
        "for(let i=0;i<rightAnchors.length;i++){"
        "const n=stageRoot.querySelector(\"[data-layer='\"+rightAnchors[i]+\"']\");"
        "if(n){const x=parsePx(n.style.left); if(x!==null){rightStart=x; break;}}"
        "}"
        "let bottomTop=null;"
        "const bottomAnchors=['月度受理工单概况','月度受理病例情况','月度工单类型概况'];"
        "for(let i=0;i<bottomAnchors.length;i++){"
        "const n=stageRoot.querySelector(\"[data-layer='\"+bottomAnchors[i]+\"']\");"
        "if(n){const y=parsePx(n.style.top); if(y!==null){bottomTop=y; break;}}"
        "}"
        "const stageWidth=1920;"
        "const gap=18;"
        "const w=Math.max(560, ((rightStart!==null?rightStart:stageWidth)-overlayLeft-gap));"
        "const h=Math.max(360, ((bottomTop!==null?bottomTop:(overlayTop+640)) - overlayTop - gap));"
        "overlay.style.left=overlayLeft+'px';"
        "overlay.style.top=overlayTop+'px';"
        "overlay.style.width=w+'px';"
        "overlay.style.height=h+'px';"
        "}catch(_e){}"
        "}"
        "setTimeout(fitOverlay,0);"
        "window.addEventListener('resize',fitOverlay);"
        ""
        "const center=hudCard('width:100%;height:100%;display:flex;flex-direction:column;overflow:hidden;');"
        "overlay.appendChild(center);"
        "const centerHead=el('div','padding:24px 22px 18px 22px;border-bottom:1px solid rgba(20,128,240,0.22);display:flex;align-items:center;justify-content:space-between;gap:14px;');"
        "center.appendChild(centerHead);"
        "const leftHeadGroup=el('div','display:flex;align-items:center;gap:14px;');"
        "centerHead.appendChild(leftHeadGroup);"
        "const avatar=el('div','width:104px;height:104px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid rgba(103,255,255,0.55);background:rgba(3,12,49,0.25);color:#67FFFF;font-size:54px;font-weight:900;');"
        "leftHeadGroup.appendChild(avatar);"
        "const headText=el('div','display:flex;flex-direction:column;gap:6px;');"
        "leftHeadGroup.appendChild(headText);"
        "headText.appendChild(el('div','font-size:26px;font-weight:900;color:#67FFFF;letter-spacing:1px;')).textContent='医生信息';"
        "headText.appendChild(el('div','font-size:13px;opacity:0.85;letter-spacing:1.2px;')).textContent='DOCTOR PROFILE';"
        "const headActions=el('div','display:flex;gap:10px;align-items:center;');"
        "centerHead.appendChild(headActions);"
        "const btnAdd=el('button','height:38px;padding:0 14px;border-radius:10px;border:1px solid rgba(103,255,255,0.55);background:rgba(103,255,255,0.14);color:#67FFFF;cursor:pointer;font-weight:800;font-size:14px;');"
        "btnAdd.type='button'; btnAdd.textContent='新增';"
        "const btnEdit=el('button','height:38px;padding:0 14px;border-radius:10px;border:1px solid rgba(255,160,108,0.65);background:rgba(255,160,108,0.14);color:#FFA06C;cursor:pointer;font-weight:800;font-size:14px;');"
        "btnEdit.type='button'; btnEdit.textContent='修改';"
        "const btnDel=el('button','height:38px;padding:0 14px;border-radius:10px;border:1px solid rgba(255,72,72,0.65);background:rgba(255,72,72,0.14);color:#FFB4B4;cursor:pointer;font-weight:800;font-size:14px;');"
        "btnDel.type='button'; btnDel.textContent='删除';"
        "headActions.appendChild(btnAdd);"
        "headActions.appendChild(btnEdit);"
        "headActions.appendChild(btnDel);"
        ""
        "const profileBody=el('div','padding:22px 22px;display:grid;grid-template-columns:190px 1fr;row-gap:18px;column-gap:16px;');"
        "center.appendChild(profileBody);"
        "function kv(k){"
        "const kk=el('div','font-size:16px;color:rgba(103,255,255,0.92);font-weight:900;');"
        "kk.textContent=k;"
        "const vv=el('div','font-size:18px;color:#EAF7FF;font-weight:800;');"
        "vv.textContent='-';"
        "profileBody.appendChild(kk);"
        "profileBody.appendChild(vv);"
        "return vv;"
        "}"
        "const vUsername=kv('用户名');"
        "const vReal=kv('真实姓名');"
        "const vDept=kv('科室');"
        "const vTitle=kv('职称');"
        "const vPhone=kv('联系电话');"
        "const vId=kv('医生编号');"
        "const vCreated=kv('创建时间');"
        ""
        "let doctorCountEl=null;"
        "let doctors=[];"
        "let selected=null;"
        "function setSelected(d){"
        "selected=d||null;"
        "const name=(selected&&(selected.real_name||selected.username))?String(selected.real_name||selected.username):'';"
        "avatar.textContent=name?name.trim().slice(0,1):'医';"
        "vUsername.textContent=selected?(selected.username||'-'):'-';"
        "vReal.textContent=selected?(selected.real_name||'-'):'-';"
        "vDept.textContent=selected?(selected.department||'-'):'-';"
        "vTitle.textContent=selected?(selected.title||'-'):'-';"
        "vPhone.textContent=selected?(selected.phone||'-'):'-';"
        "vId.textContent=selected?(String(selected.id||'-')):'-';"
        "vCreated.textContent=selected?(selected.created_at||'-'):'-';"
        "}"
        ""
        "function bindDoctorToList(list, idx){"
        "const lab=listLabel(list);"
        "if(lab){lab.textContent=(doctors[idx].real_name||doctors[idx].username||'');}"
        "list.style.cursor='pointer';"
        "const bg=getListBg(list);"
        "const caret=createCaret(list);"
        "doctorItems[idx]={list:list,bg:bg,caret:caret};"
        "list.onclick=function(){"
        "setSelected(doctors[idx]);"
        "setActiveList(idx);"
        "};"
        "}"
        ""
        "function loadDoctors(){"
        "fetch(doctorsApi,{headers:{'Accept':'application/json'}})"
        ".then(resp=>resp.json().catch(()=>null).then(js=>({resp,js})))"
        ".then(({resp,js})=>{"
        "if(!resp.ok||!js||!js.success){return;}"
        "doctors=(js.doctors||[]).slice().sort(function(a,b){return (a.id||0)-(b.id||0);});"
        "if(doctorCountEl){doctorCountEl.textContent=String(doctors.length);}"
        "if(leftNav){"
        "doctorItems.length=0;"
        "activeDoctorIndex=-1;"
        "let lists=Array.from(leftNav.querySelectorAll('.List'));"
        "lists=lists.filter(function(n){return !n.querySelector(\"[data-layer='hover效果']\");});"
        "lists.sort(function(a,b){return (parseFloat(a.style.top||'0')||0)-(parseFloat(b.style.top||'0')||0);});"
        "let usable=[];"
        "for(let i=0;i<lists.length;i++){"
        "const l=lists[i];"
        "const lab=listLabel(l);"
        "if(!lab){l.style.display='none';continue;}"
        "const t=(lab.textContent||'').trim();"
        "if(t==='hover效果'||t==='标题场景'){l.style.display='none';continue;}"
        "usable.push(l);"
        "}"
        "let baseTop=153;"
        "let step=57;"
        "if(usable.length){"
        "const tops=[];"
        "for(let i=0;i<usable.length;i++){"
        "const tt=parseFloat(usable[i].style.top||'0');"
        "if(isFinite(tt)){tops.push(tt);}"
        "}"
        "tops.sort(function(a,b){return a-b;});"
        "if(tops.length){baseTop=tops[0];}"
        "for(let i=1;i<tops.length;i++){"
        "const d=tops[i]-tops[i-1];"
        "if(d>30&&d<120){step=Math.min(step,d);}"
        "}"
        "}"
        "const template=usable.length?usable[0]:null;"
        "while(template&&usable.length<doctors.length){"
        "const c=template.cloneNode(true);"
        "c.style.display='block';"
        "c.style.top=(baseTop+(usable.length*step))+'px';"
        "leftNav.appendChild(c);"
        "usable.push(c);"
        "}"
        "navLists=usable.slice();"
        "for(let i=0;i<usable.length;i++){"
        "const l=usable[i];"
        "if(i<doctors.length){"
        "l.style.display='block';"
        "l.style.top=(baseTop+(i*step))+'px';"
        "bindDoctorToList(l,i);"
        "}else{"
        "l.style.display='none';"
        "}"
        "}"
        "}"
        "if(doctors.length){"
        "setSelected(doctors[0]);"
        "setActiveList(0);"
        "}"
        "})"
        ".catch(()=>{});"
        "}"

        "const modal=el('div','position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,0.55);z-index:2147483647;');"
        "const card=el('div','width:520px;max-width:92vw;background:rgba(3,12,49,0.95);border:1px solid rgba(102,255,255,0.45);border-radius:12px;overflow:hidden;');"
        "const mh=el('div','padding:14px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(20,128,240,0.28);');"
        "const mhTitle=el('div','font-size:18px;font-weight:700;color:#67FFFF;');"
        "mh.appendChild(mhTitle);"
        "const close=el('button','background:transparent;border:0;color:#EAF7FF;font-size:18px;cursor:pointer;'); close.type='button'; close.textContent='×';"
        "mh.appendChild(close);"
        "card.appendChild(mh);"
        "const mb=el('div','padding:14px 16px;display:flex;flex-direction:column;gap:10px;');"
        "function field(label,type,placeholder){const row=el('div','display:flex;gap:10px;align-items:center;');"
        "const l=el('div','width:90px;color:#EAF7FF;opacity:0.92;'); l.textContent=label;"
        "const inp=el('input','flex:1;height:32px;padding:0 10px;border-radius:8px;border:1px solid rgba(102,255,255,0.35);background:rgba(0,0,0,0.25);color:#EAF7FF;outline:none;');"
        "inp.type=type; inp.placeholder=placeholder||''; row.appendChild(l); row.appendChild(inp); mb.appendChild(row); return inp;}"
        "const fUsername=field('用户名','text','如：doctor01');"
        "const fPassword=field('密码','password','');"
        "const fReal=field('姓名','text','');"
        "const fDept=field('科室','text','');"
        "const fTitle=field('职称','text','');"
        "const fPhone=field('电话','text','');"
        "card.appendChild(mb);"
        "const mf=el('div','padding:12px 16px;display:flex;justify-content:flex-end;gap:10px;border-top:1px solid rgba(20,128,240,0.28);');"
        "const cancel=el('button','height:32px;padding:0 14px;border-radius:8px;border:1px solid rgba(255,255,255,0.25);background:transparent;color:#EAF7FF;cursor:pointer;'); cancel.type='button'; cancel.textContent='取消';"
        "const submit=el('button','height:32px;padding:0 14px;border-radius:8px;border:1px solid rgba(103,255,255,0.65);background:rgba(103,255,255,0.22);color:#67FFFF;cursor:pointer;'); submit.type='button'; submit.textContent='提交';"
        "mf.appendChild(cancel); mf.appendChild(submit); card.appendChild(mf);"
        "modal.appendChild(card); document.body.appendChild(modal);"
        "function closeModal(){modal.style.display='none';}"
        "close.addEventListener('click',closeModal); cancel.addEventListener('click',closeModal);"
        "modal.addEventListener('click',function(ev){if(ev.target===modal){closeModal();}});"
        "let mode='add';"
        "let editId=null;"
        "function openAdd(){"
        "mode='add'; editId=null;"
        "mhTitle.textContent='新增医生';"
        "fUsername.disabled=false;"
        "fUsername.value='';fPassword.value='';fReal.value='';fDept.value='';fTitle.value='';fPhone.value='';"
        "modal.style.display='flex';"
        "}"
        "function openEdit(){"
        "if(!selected){alert('请先选择医生');return;}"
        "mode='edit'; editId=selected.id;"
        "mhTitle.textContent='修改医生';"
        "fUsername.disabled=true;"
        "fUsername.value=selected.username||'';"
        "fPassword.value='';"
        "fReal.value=selected.real_name||'';"
        "fDept.value=selected.department||'';"
        "fTitle.value=selected.title||'';"
        "fPhone.value=selected.phone||'';"
        "modal.style.display='flex';"
        "}"
        "btnAdd.addEventListener('click',openAdd);"
        "btnEdit.addEventListener('click',openEdit);"
        "btnDel.addEventListener('click',function(){"
        "if(!selected){alert('请先选择医生');return;}"
        "if(!confirm('确定删除该医生？')){return;}"
        "fetch(doctorsApi+'/'+String(selected.id),{method:'DELETE',headers:{'Accept':'application/json'}})"
        ".then(resp=>resp.json().catch(()=>null).then(js=>({resp,js})))"
        ".then(({resp,js})=>{if(!resp.ok||!js||!js.success){alert((js&&js.message)||'删除失败');return;} selected=null; loadDoctors();})"
        ".catch(()=>alert('删除失败'));"
        "});"
        "submit.addEventListener('click',function(){"
        "if(mode==='add'){"
        "const payload={username:(fUsername.value||'').trim(),password:(fPassword.value||''),real_name:(fReal.value||'').trim(),department:(fDept.value||'').trim(),title:(fTitle.value||'').trim(),phone:(fPhone.value||'').trim()};"
        "if(!payload.username||!payload.password){alert('请填写用户名和密码');return;}"
        "submit.disabled=true;"
        "fetch(doctorsApi,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(payload)})"
        ".then(resp=>resp.json().catch(()=>null).then(js=>({resp,js})))"
        ".then(({resp,js})=>{submit.disabled=false; if(!resp.ok||!js||!js.success){alert((js&&js.message)||'新增失败');return;} closeModal(); loadDoctors();})"
        ".catch(()=>{submit.disabled=false; alert('新增失败');});"
        "return;"
        "}"
        "if(!editId){return;}"
        "const payload={password:(fPassword.value||''),real_name:(fReal.value||'').trim(),department:(fDept.value||'').trim(),title:(fTitle.value||'').trim(),phone:(fPhone.value||'').trim()};"
        "submit.disabled=true;"
        "fetch(doctorsApi+'/'+String(editId),{method:'PUT',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(payload)})"
        ".then(resp=>resp.json().catch(()=>null).then(js=>({resp,js})))"
        ".then(({resp,js})=>{submit.disabled=false; if(!resp.ok||!js||!js.success){alert((js&&js.message)||'修改失败');return;} closeModal(); loadDoctors();})"
        ".catch(()=>{submit.disabled=false; alert('修改失败');});"
        "});"

        "loadDoctors();"
        "}catch(e){}"
        "})();"
        "</script>"
        "</body></html>"
    )
    resp = make_response(full_html)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

@app.route('/api/doctors', methods=['GET', 'POST'])
@login_required
def api_doctors():
    if request.method == 'POST':
        if current_user.role != 'admin':
            return jsonify(success=False, message="forbidden"), 403

    if request.method == 'GET':
        db = get_db()
        cursor = db.cursor(dictionary=True)
        search_keyword = request.args.get('search', '').strip()
        try:
            if search_keyword:
                if search_keyword.isdigit():
                    cursor.execute(
                        """
                        SELECT id, username, real_name, department, title, phone, created_at
                        FROM users
                        WHERE role = 'doctor' AND id = %s
                        """,
                        (int(search_keyword),),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, username, real_name, department, title, phone, created_at
                        FROM users
                        WHERE role = 'doctor' AND username LIKE %s
                        """,
                        (f"%{search_keyword}%",),
                    )
            else:
                cursor.execute(
                    """
                    SELECT id, username, real_name, department, title, phone, created_at
                    FROM users
                    WHERE role = 'doctor'
                    """
                )
            rows = cursor.fetchall() or []
            doctors = []
            for r in rows:
                created = r.get("created_at")
                if hasattr(created, "isoformat"):
                    created_text = created.isoformat(sep=" ", timespec="seconds")
                else:
                    created_text = str(created or "")
                doctors.append(
                    {
                        "id": r.get("id"),
                        "username": r.get("username"),
                        "real_name": r.get("real_name"),
                        "department": r.get("department"),
                        "title": r.get("title"),
                        "phone": r.get("phone"),
                        "created_at": created_text,
                    }
                )
            return jsonify(success=True, doctors=doctors)
        finally:
            cursor.close()
            db.close()

    data = request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "").strip()
    if not password:
        password = '123456'
    real_name = str(data.get("real_name") or "").strip()
    department = str(data.get("department") or "").strip()
    title = str(data.get("title") or "").strip()
    phone = str(data.get("phone") or "").strip()
    if not username:
        return jsonify(success=False, message="missing_username"), 400

    hashed_password = hash_password(password)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE username=%s LIMIT 1", (username,))
        if cursor.fetchone():
            return jsonify(success=False, message="username_exists"), 400
        cursor.execute(
            """
            INSERT INTO users (username, password, real_name, department, title, phone, role, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (username, hashed_password, real_name, department, title, phone, 'doctor'),
        )
        db.commit()
        return jsonify(success=True)
    except mysql.connector.Error as err:
        return jsonify(success=False, message=str(err)), 500
    finally:
        cursor.close()
        db.close()

@app.route('/api/doctors/<int:doctor_id>', methods=['DELETE'])
@login_required
def api_delete_doctor(doctor_id):
    if current_user.role != 'admin':
        return jsonify(success=False, message="forbidden"), 403
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE id=%s AND role='doctor'", (doctor_id,))
        if not cursor.fetchone():
            return jsonify(success=False, message="doctor_not_found"), 404
        cursor.execute("DELETE FROM users WHERE id=%s AND role='doctor'", (doctor_id,))
        cursor.execute("UPDATE users SET id = id - 1 WHERE id > %s AND role = 'doctor'", (doctor_id,))
        db.commit()
        return jsonify(success=True)
    except mysql.connector.Error as err:
        return jsonify(success=False, message=str(err)), 500
    finally:
        cursor.close()
        db.close()


@app.route('/api/doctors/<int:doctor_id>', methods=['PUT'])
@login_required
def api_update_doctor(doctor_id):
    if current_user.role != 'admin':
        return jsonify(success=False, message="forbidden"), 403

    data = request.get_json(silent=True) or {}
    real_name = str(data.get("real_name") or "").strip()
    department = str(data.get("department") or "").strip()
    title = str(data.get("title") or "").strip()
    phone = str(data.get("phone") or "").strip()
    password = str(data.get("password") or "")

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE id=%s AND role='doctor'", (doctor_id,))
        if not cursor.fetchone():
            return jsonify(success=False, message="doctor_not_found"), 404

        if password:
            hashed_password = hash_password(password)
            cursor.execute(
                """
                UPDATE users
                SET password=%s, real_name=%s, department=%s, title=%s, phone=%s
                WHERE id=%s AND role='doctor'
                """,
                (hashed_password, real_name, department, title, phone, doctor_id),
            )
        else:
            cursor.execute(
                """
                UPDATE users
                SET real_name=%s, department=%s, title=%s, phone=%s
                WHERE id=%s AND role='doctor'
                """,
                (real_name, department, title, phone, doctor_id),
            )
        db.commit()
        return jsonify(success=True)
    except mysql.connector.Error as err:
        return jsonify(success=False, message=str(err)), 500
    finally:
        cursor.close()
        db.close()

# 仪表盘路由
@app.route('/main_interface')
@login_required
def main_interface():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        def _safe_total(sql, params=()):
            try:
                cursor.execute(sql, params)
                row = cursor.fetchone() or {}
                val = row.get("total")
                return int(val) if val is not None else 0
            except Exception:
                return 0

        total_patients = _safe_total("SELECT COUNT(*) as total FROM patients")
        total_diagnoses = _safe_total("SELECT COUNT(*) as total FROM diagnoses")
        total_images = _safe_total("SELECT COUNT(*) as total FROM images")
        monthly_diagnoses = _safe_total(
            "SELECT COUNT(*) as total FROM diagnoses WHERE DATE_FORMAT(diagnosis_date, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')"
        )

        current_year = datetime.now().year
        all_months = [f"{current_year}-{str(i).zfill(2)}" for i in range(1, 13)]

        monthly_data = []
        try:
            cursor.execute(
                """
                SELECT 
                    DATE_FORMAT(diagnosis_date, '%Y-%m') as month, 
                    COUNT(*) as count 
                FROM diagnoses 
                WHERE YEAR(diagnosis_date) = %s 
                GROUP BY DATE_FORMAT(diagnosis_date, '%Y-%m') 
                ORDER BY month
                """,
                (current_year,),
            )
            monthly_data = cursor.fetchall() or []
        except Exception:
            monthly_data = []

        monthly_dict = {data.get("month"): data.get("count", 0) for data in monthly_data if data.get("month")}
        chart_data = []
        for month in all_months:
            count = int(monthly_dict.get(month, 0) or 0)
            month_display = month.split("-")[1] + "月"
            chart_data.append({"month": month_display, "count": count})

        months = [data["month"] for data in chart_data]
        counts = [data["count"] for data in chart_data]

        try:
            return render_template(
                "main.html",
                total_patients=total_patients,
                total_diagnoses=total_diagnoses,
                total_images=total_images,
                monthly_diagnoses=monthly_diagnoses,
                months=months,
                counts=counts,
            )
        except Exception as e:
            return render_template(
                "main_interface_simple.html",
                error=f"{type(e).__name__}:{str(e)}",
                total_patients=total_patients,
                total_diagnoses=total_diagnoses,
                total_images=total_images,
                monthly_diagnoses=monthly_diagnoses,
                chart_data=chart_data,
            ), 200
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass

@app.route('/test1')
@login_required
def test1_interface():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        def _safe_total(sql, params=()):
            try:
                cursor.execute(sql, params)
                row = cursor.fetchone() or {}
                val = row.get("total")
                return int(val) if val is not None else 0
            except Exception:
                return 0

        figma_html = ""
        figma_candidates = []
        env_figma = (os.environ.get("BTS_TEST1_FIGMA_PATH") or "").strip()
        if env_figma:
            figma_candidates.append(env_figma)
        base_dir = os.path.dirname(__file__)
        figma_candidates.extend(
            [
                os.path.join(base_dir, "UI", "test3.txt"),
                os.path.join(base_dir, "ui", "test3.txt"),
                os.path.join(base_dir, "UI", "test1.txt"),
                os.path.join(base_dir, "ui", "test1.txt"),
            ]
        )
        for figma_path in figma_candidates:
            try:
                with open(figma_path, "r", encoding="utf-8") as f:
                    figma_html = f.read()
                if figma_html:
                    break
            except Exception:
                continue
        if figma_html:
            try:
                figma_html = figma_html.replace(">肿瘤</div>", ">端侧脑瘤病历系统</div>", 1)
                figma_html = figma_html.replace(
                    "left: 920px; top: 24px; position: absolute; text-align: center; color: white; font-size: 38px; font-family: Abhaya Libre SemiBold; font-weight: 600; letter-spacing: 7.60px; word-wrap: break-word",
                    "left: 50%; top: 24px; position: absolute; transform: translateX(-50%); text-align: center; white-space: nowrap; color: white; font-size: 38px; font-family: Abhaya Libre SemiBold; font-weight: 600; letter-spacing: 2px; word-wrap: break-word",
                    1,
                )
                figma_html = figma_html.replace('data-layer="data-layer="todo-panel-mask""', 'data-layer="todo-panel-mask"')
                figma_html = figma_html.replace('data-layer="data-layer="todo-panel-scroll""', 'data-layer="todo-panel-scroll"')
                figma_html = figma_html.replace('data-layer="data-layer="todo-card-item""', 'data-layer="todo-card-item"')
            except Exception:
                pass

        total_patients = _safe_total("SELECT COUNT(*) as total FROM patients")
        total_diagnoses = _safe_total("SELECT COUNT(*) as total FROM diagnoses")
        total_images = _safe_total("SELECT COUNT(*) as total FROM images")
        monthly_diagnoses = _safe_total(
            "SELECT COUNT(*) as total FROM diagnoses WHERE DATE_FORMAT(diagnosis_date, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')"
        )

        today = datetime.now().date()
        start_day = today - timedelta(days=23)
        recent_24_counts = []
        try:
            cursor.execute(
                """
                SELECT DATE(diagnosis_date) as day, COUNT(*) as count
                FROM diagnoses
                WHERE diagnosis_date >= %s
                GROUP BY DATE(diagnosis_date)
                ORDER BY day
                """,
                (start_day,),
            )
            recent_rows = cursor.fetchall() or []
            recent_dict = {}
            for row in recent_rows:
                day_value = row.get("day")
                if isinstance(day_value, datetime):
                    day_key = day_value.date().isoformat()
                else:
                    day_key = str(day_value)
                recent_dict[day_key] = int(row.get("count") or 0)
            for offset in range(24):
                target_day = start_day + timedelta(days=offset)
                recent_24_counts.append(recent_dict.get(target_day.isoformat(), 0))
        except Exception:
            recent_24_counts = [12, 18, 15, 21, 17, 24, 19, 22, 26, 20, 23, 28, 25, 31, 27, 29, 33, 30, 35, 32, 34, 37, 36, 39]

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
        image_coverage = safe_percent(total_images, total_diagnoses if total_diagnoses > 0 else 1)
        active_day_rate = safe_percent(sum(1 for value in recent_24_counts if value > 0), 24)
        system_health = int(round(0.35 * max(diagnosis_coverage, 86) + 0.35 * max(image_coverage, 86) + 0.30 * max(active_day_rate, 86)))
        system_health = max(86, min(99, system_health))

        dashboard_overview = {
            "date_label": datetime.now().strftime("%Y年%m月%d日"),
            "left_title": "病例全周期管理",
            "left_description": "覆盖建档、诊断、影像归档与协同，形成可追溯临床数据闭环。",
            "right_title": "远程推理评估",
            "right_description": "支持 .nii 上传与 SSH 调度推理，结果回传后用于可视化分析。",
            "center_percent": system_health,
            "center_status": "核心系统在线" if system_health >= 90 else "系统监测中",
            "bar_title": "近24日推理任务量",
        }

        module_cards = [
            {"title": "病例管理", "percent": max(86, diagnosis_coverage), "value": compact_metric(max(total_patients, 128))},
            {"title": "诊断记录", "percent": max(86, safe_percent(monthly_diagnoses, total_diagnoses if total_diagnoses > 0 else 1)), "value": compact_metric(max(total_diagnoses, 286))},
            {"title": "影像归档", "percent": max(86, image_coverage), "value": compact_metric(max(total_images, 244))},
            {"title": "远程推理", "percent": max(84, active_day_rate), "value": compact_metric(48)},
            {"title": "医患协同", "percent": 96, "value": compact_metric(12)},
            {"title": "智能评估", "percent": system_health, "value": compact_metric(max(monthly_diagnoses, 36))},
        ]

        task_publish_data = {
            "title": "系统任务概览",
            "cards": [
                {"container": "已预订", "value": "128", "label": "任务总量"},
                {"container": "会议使用率", "value": "96%", "label": "完成率"},
                {"container": "已开会议", "value": "122", "label": "已完成"},
                {"container": "待开会议", "value": "6", "label": "待处理"},
            ],
            "categories": [
                {"label": "病例建档", "value": max(total_patients, 128)},
                {"label": "诊断录入", "value": max(total_diagnoses, 286)},
                {"label": "影像归档", "value": max(total_images, 244)},
                {"label": "远程推理", "value": 48},
                {"label": "智能评估", "value": 96},
                {"label": "协同随访", "value": 212},
            ],
        }

        warning_overview = {
            "title": "系统预警",
            "rings": [
                {"container": "待处理", "label": "待处理任务", "value": "6"},
                {"container": "处理率", "label": "逾期任务", "value": "0"},
                {"container": "历史总数", "label": "任务完成率", "value": "96%"},
            ],
            "items": [
                {"message": "待办：影像归档核对（未分配）", "time": datetime.now().strftime("%m.%d %H:%M")},
                {"message": "今日新增诊断：0 例", "time": datetime.now().strftime("%m.%d %H:%M")},
                {"message": "系统状态：正常运行", "time": datetime.now().strftime("%m.%d %H:%M")},
            ],
            "summary": {"today_diagnoses": 0, "total_notifications": 0, "unread_notifications": 0},
        }

        return render_template(
            "main_interface_test1.html",
            total_patients=total_patients,
            total_diagnoses=total_diagnoses,
            total_images=total_images,
            monthly_diagnoses=monthly_diagnoses,
            months=[],
            counts=[],
            chart_data=[],
            figma_html=figma_html,
            dashboard_overview=dashboard_overview,
            module_cards=module_cards,
            task_publish_data=task_publish_data,
            warning_overview=warning_overview,
            bar_values=recent_24_counts,
        )
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass

# 医生管理路由（管理员可全部操作，医生仅可查看）
@app.route('/doctors')
@login_required
def doctors():
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # 获取搜索参数
    search_keyword = request.args.get('search', '').strip()
    
    if search_keyword:
        # 数字按医生ID精确搜索，其他按用户名模糊搜索
        if search_keyword.isdigit():
            cursor.execute(
                """
                SELECT id, username, real_name, department, title, phone, role, created_at
                FROM users
                WHERE role = 'doctor' AND id = %s
                """,
                (int(search_keyword),),
            )
        else:
            cursor.execute(
                """
                SELECT id, username, real_name, department, title, phone, role, created_at
                FROM users
                WHERE role = 'doctor' AND username LIKE %s
                """,
                (f"%{search_keyword}%",),
            )
    else:
        # 获取所有医生
        cursor.execute(
            """
            SELECT id, username, real_name, department, title, phone, role, created_at
            FROM users
            WHERE role = 'doctor'
            """
        )
    
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
        password = request.form.get('password', '').strip()
        if not password:
            password = '123456'
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
        cursor.execute("SELECT * FROM patients WHERE name LIKE %s ORDER BY CAST(patient_id AS UNSIGNED) ASC, patient_id ASC", (f"%{search_keyword}%",))
    else:
        # 获取所有病人
        cursor.execute("SELECT * FROM patients ORDER BY CAST(patient_id AS UNSIGNED) ASC, patient_id ASC")
    
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
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('patients'))
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        name = request.form['name']
        gender = request.form['gender']
        age = request.form['age']
        birthday = request.form['birthday'] if request.form['birthday'] else None
        phone = request.form['phone'] if request.form['phone'] else None
        address = request.form['address'] if request.form['address'] else None

        if gender not in ['男', '女']:
            flash('请选择性别！', 'danger')
            return redirect(url_for('add_patient'))
        
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
    cursor.execute("SELECT * FROM patient_clinical_info WHERE patient_id = %s", (patient_id,))
    clinical_info = cursor.fetchone()
    
    cursor.execute("""
        SELECT d.*, u.username as doctor_name
        FROM diagnoses d
        LEFT JOIN users u ON d.doctor_id = u.id
        WHERE d.patient_id = %s
        ORDER BY d.diagnosis_date DESC
    """, (patient_id,))
    diagnoses = cursor.fetchall()

    diagnosis_ids = [d["id"] for d in diagnoses]
    agent_results = {}
    if diagnosis_ids:
        placeholders = ",".join(["%s"] * len(diagnosis_ids))
        query = f"""
            SELECT r.*
            FROM diagnosis_agent_results r
            JOIN (
                SELECT diagnosis_id, MAX(created_at) AS max_created
                FROM diagnosis_agent_results
                WHERE diagnosis_id IN ({placeholders})
                GROUP BY diagnosis_id
            ) t ON r.diagnosis_id = t.diagnosis_id AND r.created_at = t.max_created
        """
        cursor.execute(query, diagnosis_ids)
        for row in cursor.fetchall():
            agent_results[row["diagnosis_id"]] = row
    
    cursor.close()
    db.close()
    
    return render_template('diagnoses.html', patient=patient, diagnoses=diagnoses, clinical_info=clinical_info, agent_results=agent_results)

@app.route('/api/patient_report/<int:patient_id>')
@login_required
def api_patient_report(patient_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        return jsonify(success=False, message="patient_not_found"), 404
    cursor.execute("""
        SELECT d.*, u.username AS doctor_name
        FROM diagnoses d
        LEFT JOIN users u ON d.doctor_id = u.id
        WHERE d.patient_id = %s
        ORDER BY d.diagnosis_date DESC, d.id DESC
        LIMIT 1
    """, (patient_id,))
    diagnosis = cursor.fetchone()
    agent = None
    if diagnosis and diagnosis.get("id"):
        cursor.execute("""
            SELECT *
            FROM diagnosis_agent_results
            WHERE diagnosis_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """, (diagnosis["id"],))
        agent = cursor.fetchone()
    cursor.close()
    db.close()
    return jsonify(success=True, patient=patient, diagnosis=diagnosis, agent=agent)

@app.route('/api/patient_uploads/<int:patient_id>')
@login_required
def api_patient_uploads(patient_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        return jsonify(success=False, message="patient_not_found"), 404
    cursor.execute("""
        SELECT id
        FROM diagnoses
        WHERE patient_id = %s
        ORDER BY diagnosis_date DESC, id DESC
        LIMIT 1
    """, (patient_id,))
    diagnosis = cursor.fetchone()
    cursor.close()
    db.close()
    if not diagnosis:
        return jsonify(success=True, case_id=None, files=[])
    case_id = f"{patient.get('patient_id')}_{diagnosis.get('id')}"
    base_upload_root = os.environ.get("REMOTE_UPLOAD_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/Uploads")
    remote_dir = f"{base_upload_root}/{case_id}/"
    hostname = ""
    port = ""
    client = None
    try:
        client, hostname, port = _connect_remote_ssh()
        sftp = client.open_sftp()
        try:
            try:
                names = sftp.listdir(remote_dir)
            except Exception:
                return jsonify(success=True, case_id=case_id, files=[])
            files = []
            for name in names:
                if not (name.endswith(".nii") or name.endswith(".nii.gz")):
                    continue
                p = remote_dir.rstrip("/") + "/" + name
                size = None
                try:
                    size = int(sftp.stat(p).st_size)
                except Exception:
                    size = None
                files.append({"name": name, "size_bytes": size})
            files.sort(key=lambda x: x.get("name") or "")
            return jsonify(success=True, case_id=case_id, files=files)
        finally:
            try:
                sftp.close()
            except Exception:
                pass
    except Exception as e:
        return jsonify(success=False, message=f"remote_uploads_error:{hostname}:{port}:{str(e)}"), 500
    finally:
        try:
            if client:
                client.close()
        except Exception:
            pass

@app.route('/api/patient_nii_previews/<int:patient_id>')
@login_required
def api_patient_nii_previews(patient_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        return jsonify(success=False, message="patient_not_found"), 404
    cursor.execute("""
        SELECT id
        FROM diagnoses
        WHERE patient_id = %s
        ORDER BY diagnosis_date DESC, id DESC
        LIMIT 1
    """, (patient_id,))
    diagnosis = cursor.fetchone()
    cursor.close()
    db.close()
    if not diagnosis:
        return jsonify(success=True, case_id=None, previews=[])
    case_id = f"{patient.get('patient_id')}_{diagnosis.get('id')}"
    safe_case_id = normalize_case_id(case_id)
    base_upload_root = os.environ.get("REMOTE_UPLOAD_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/Uploads")
    remote_dir = f"{base_upload_root}/{case_id}/"

    conda_env = os.environ.get("REMOTE_CONDA_ENV", "BTS_env")
    conda_sh = os.environ.get("REMOTE_CONDA_SH", "/home/wpw/miniconda3/etc/profile.d/conda.sh")

    static_root = os.path.join(app.root_path, "static")
    local_dir = os.path.join(static_root, "nii_previews", safe_case_id)
    os.makedirs(local_dir, exist_ok=True)
    try:
        cached = [f for f in os.listdir(local_dir) if str(f).lower().endswith(".png")]
    except Exception:
        cached = []
    if cached:
        cached.sort()
        previews = []
        for f in cached:
            rel_path = f"nii_previews/{safe_case_id}/{f}"
            previews.append({"name": str(f), "url": url_for("static", filename=rel_path)})
        return jsonify(success=True, case_id=case_id, files=[], previews=previews)

    hostname = ""
    port = ""
    client = None
    sftp = None
    last_err = None
    for _ in range(3):
        try:
            client, hostname, port = _connect_remote_ssh()
            sftp = client.open_sftp()
            break
        except Exception as e:
            last_err = e
            try:
                if client:
                    client.close()
            except Exception:
                pass
            client = None
            sftp = None
            time.sleep(0.4)
    if not sftp:
        return jsonify(success=False, message=f"remote_nii_preview_error:{hostname}:{port}:{str(last_err)}"), 500
    try:
            try:
                names = sftp.listdir(remote_dir)
            except Exception:
                return jsonify(success=True, case_id=case_id, files=[], previews=[])

            nii_files = [n for n in names if (n.endswith(".nii") or n.endswith(".nii.gz"))]
            nii_files.sort()
            files = []
            for name in nii_files:
                p = remote_dir.rstrip("/") + "/" + name
                size = None
                try:
                    size = int(sftp.stat(p).st_size)
                except Exception:
                    size = None
                files.append({"name": name, "size_bytes": size})
            previews = []
            for name in nii_files:
                base_name = name
                if base_name.endswith(".nii.gz"):
                    base_name = base_name[:-7]
                elif base_name.endswith(".nii"):
                    base_name = base_name[:-4]
                preview_file = f"{normalize_case_id(base_name)}_preview.png"
                remote_png = remote_dir.rstrip("/") + "/.preview_" + preview_file
                local_path = os.path.join(local_dir, preview_file)
                rel_path = f"nii_previews/{safe_case_id}/{preview_file}"

                remote_nii = remote_dir.rstrip("/") + "/" + name
                remote_cmd = (
                    "bash -lc "
                    + json.dumps(
                        f"source {conda_sh}; "
                        f"conda activate {conda_env}; "
                        "python -c "
                        + json.dumps(
                            (
                                "import os; os.environ['MPLBACKEND']='Agg'; "
                                "import numpy as np; import nibabel as nib; "
                                "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; "
                                f"nii_path={remote_nii!r}; out_path={remote_png!r}; "
                                "img=nib.load(nii_path); data=img.get_fdata(); "
                                "data=data[...,0] if getattr(data,'ndim',0)==4 else data; "
                                "idx=int(data.shape[2]//2); sl=data[:,:,idx]; sl=np.nan_to_num(sl); "
                                "lo,hi=np.percentile(sl,[1,99]); "
                                "lo=float(lo) if np.isfinite(lo) else float(np.min(sl)); "
                                "hi=float(hi) if np.isfinite(hi) else float(np.max(sl)); "
                                "hi=hi if hi>lo else (lo+1.0); "
                                "sl=(np.clip(sl,lo,hi)-lo)/(hi-lo); "
                                "arr=(sl*255.0).astype(np.uint8); "
                                "plt.imsave(out_path, arr, cmap='gray'); "
                                "print(out_path)"
                            ),
                            ensure_ascii=False,
                        ),
                        ensure_ascii=False,
                    )
                )
                try:
                    _stdin, _stdout, _stderr = client.exec_command(remote_cmd, get_pty=False)
                    exit_status = None
                    try:
                        exit_status = _stdout.channel.recv_exit_status()
                    except Exception:
                        exit_status = None
                    stdout_text = ""
                    stderr_text = ""
                    try:
                        stdout_text = (_stdout.read() or b"").decode("utf-8", "ignore")
                    except Exception:
                        stdout_text = ""
                    try:
                        stderr_text = (_stderr.read() or b"").decode("utf-8", "ignore")
                    except Exception:
                        stderr_text = ""
                    if exit_status not in (0, None):
                        previews.append({"name": name, "url": None, "error": (stderr_text or stdout_text or "remote_command_failed")[:400]})
                        continue
                    sftp.get(remote_png, local_path)
                    previews.append({"name": name, "url": url_for("static", filename=rel_path)})
                except Exception as e:
                    previews.append({"name": name, "url": None, "error": str(e)[:400]})

            return jsonify(success=True, case_id=case_id, files=files, previews=previews)
    finally:
        try:
            if sftp:
                sftp.close()
        except Exception:
            pass
        try:
            if client:
                client.close()
        except Exception:
            pass

@app.route('/api/patient_nii_segmentation/<int:patient_id>')
@login_required
def api_patient_nii_segmentation(patient_id):
    force = (request.args.get("force") or "").strip() == "1"
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        return jsonify(success=False, message="patient_not_found"), 404
    cursor.execute(
        """
        SELECT id
        FROM diagnoses
        WHERE patient_id = %s
        ORDER BY diagnosis_date DESC, id DESC
        LIMIT 1
        """,
        (patient_id,),
    )
    diagnosis = cursor.fetchone()
    cursor.close()
    db.close()
    if not diagnosis:
        return jsonify(success=False, message="diagnosis_not_found"), 404

    case_id = f"{patient.get('patient_id')}_{diagnosis.get('id')}"
    safe_case_id = normalize_case_id(case_id)

    static_root = os.path.join(app.root_path, "static")
    local_dir = os.path.join(static_root, "nii_seg", safe_case_id)
    os.makedirs(local_dir, exist_ok=True)
    local_gt_name = "seg_gt.png"
    local_gt_path = os.path.join(local_dir, local_gt_name)
    local_pred_name = "seg_pred.png"
    local_pred_path = os.path.join(local_dir, local_pred_name)
    local_mask_name = "seg_mask.nii.gz"
    local_mask_path = os.path.join(local_dir, local_mask_name)
    local_vis_name = "seg_vis.png"
    local_vis_path = os.path.join(local_dir, local_vis_name)
    rel_vis_path = f"nii_seg/{safe_case_id}/{local_vis_name}"
    rel_gt_path = f"nii_seg/{safe_case_id}/{local_gt_name}"
    rel_pred_path = f"nii_seg/{safe_case_id}/{local_pred_name}"

    def _save_color_mask(mask2d):
        try:
            import numpy as _np
        except Exception:
            return False
        arr = _np.asarray(mask2d).astype(_np.int32)
        h, w = arr.shape[:2]
        rgb = _np.zeros((h, w, 3), dtype=_np.uint8)
        rgb[arr == 2] = (0, 0, 255)
        rgb[arr == 1] = (0, 255, 0)
        rgb[(arr == 4) | (arr == 3)] = (255, 0, 0)
        try:
            from PIL import Image as _Image

            _Image.fromarray(rgb, mode="RGB").save(local_vis_path, format="PNG")
            return True
        except Exception:
            try:
                os.environ.setdefault("MPLBACKEND", "Agg")
                import matplotlib

                try:
                    matplotlib.use("Agg")
                except Exception:
                    pass
                import matplotlib.pyplot as _plt

                _plt.imsave(local_vis_path, rgb)
                return True
            except Exception:
                return False

    def _try_build_vis_from_mask() -> bool:
        if not os.path.exists(local_mask_path):
            return False
        try:
            import numpy as _np
            import nibabel as _nib

            img = _nib.load(local_mask_path)
            data = img.get_fdata()
            data = data[..., 0] if getattr(data, "ndim", 0) == 4 else data
            data = _np.nan_to_num(data)
            data = _np.rint(data).astype(_np.int32)
            if data.ndim != 3:
                return False
            areas = [(data[..., z] > 0).sum() for z in range(data.shape[-1])]
            z = int(_np.argmax(areas)) if max(areas) > 0 else int(data.shape[-1] // 2)
            return _save_color_mask(data[..., z])
        except Exception:
            return False

    def _try_build_vis_from_raw_png(src_path: str) -> bool:
        if not os.path.exists(src_path):
            return False
        try:
            import numpy as _np
            from PIL import Image as _Image

            img = _Image.open(src_path)
            img.load()
            if img.mode in ("RGB", "RGBA"):
                return False
            img_l = img.convert("L")
            arr = _np.array(img_l, dtype=_np.int32)
            uniq = _np.unique(arr)
            if uniq.size > 64:
                return False
            nonzero = [int(v) for v in uniq.tolist() if int(v) != 0]
            mapping = {}
            if set(nonzero).issubset({1, 2, 3, 4}):
                mapping = {int(v): int(v) for v in nonzero}
            elif len(nonzero) <= 4:
                nonzero_sorted = sorted(nonzero)
                if len(nonzero_sorted) == 1:
                    mapping[nonzero_sorted[0]] = 4
                elif len(nonzero_sorted) == 2:
                    mapping[nonzero_sorted[0]] = 2
                    mapping[nonzero_sorted[1]] = 4
                elif len(nonzero_sorted) == 3:
                    mapping[nonzero_sorted[0]] = 1
                    mapping[nonzero_sorted[1]] = 2
                    mapping[nonzero_sorted[2]] = 4
                else:
                    mapping[nonzero_sorted[0]] = 1
                    mapping[nonzero_sorted[1]] = 2
                    mapping[nonzero_sorted[2]] = 3
                    mapping[nonzero_sorted[3]] = 4
            if not mapping:
                return False
            out = _np.zeros_like(arr, dtype=_np.int32)
            for src, dst in mapping.items():
                out[arr == int(src)] = int(dst)
            return _save_color_mask(out)
        except Exception:
            return False

    if not force:
        if os.path.exists(local_pred_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_pred_path))
        if os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))
        if _try_build_vis_from_mask() and os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))
        if _try_build_vis_from_raw_png(local_pred_path) and os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))
        if _try_build_vis_from_raw_png(local_gt_path) and os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))
        if os.path.exists(local_mask_path):
            return jsonify(success=False, message="seg_vis_unavailable_from_mask"), 500
        if os.path.exists(local_gt_path):
            return jsonify(success=False, message="seg_vis_unavailable_from_png"), 500

    base_upload_root = os.environ.get("REMOTE_UPLOAD_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/Uploads")
    remote_upload_dir = f"{base_upload_root}/{safe_case_id}/"
    remote_upload_dir_alt = f"{base_upload_root}/{case_id}/"

    hostname = ""
    port = ""
    client = None
    try:
        client, hostname, port = _connect_remote_ssh()
        sftp_check = client.open_sftp()
        try:
            try:
                names = sftp_check.listdir(remote_upload_dir_alt)
                remote_upload_dir = remote_upload_dir_alt
            except Exception:
                names = sftp_check.listdir(remote_upload_dir)
            nii_files = [n for n in (names or []) if (n.endswith(".nii") or n.endswith(".nii.gz"))]
            if not nii_files:
                return jsonify(success=False, message=f"remote_uploads_empty:{safe_case_id}"), 400
        finally:
            try:
                sftp_check.close()
            except Exception:
                pass

        conda_env = os.environ.get("REMOTE_CONDA_ENV", "BTS_env")
        conda_sh = os.environ.get("REMOTE_CONDA_SH", "/home/wpw/miniconda3/etc/profile.d/conda.sh")
        mmc_root = os.environ.get("REMOTE_MMC_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/MMCFormer-main")

        command = (
            "bash -lc "
            + json.dumps(
                "export MPLBACKEND='Agg'; "
                "export DISPLAY=''; "
                "export QT_QPA_PLATFORM='offscreen'; "
                "export SDL_VIDEODRIVER='dummy'; "
                f"export CASE_ID='{safe_case_id}'; "
                f"export UPLOAD_DIR='{remote_upload_dir}'; "
                f"source {conda_sh}; "
                f"conda activate {conda_env}; "
                f"cd {mmc_root}; "
                "python Valide.py",
                ensure_ascii=False,
            )
        )
        _stdin, stdout, stderr = client.exec_command(command, get_pty=False)
        exit_status = None
        try:
            exit_status = stdout.channel.recv_exit_status()
        except Exception:
            exit_status = None
        out = ""
        err = ""
        try:
            out = (stdout.read() or b"").decode("utf-8", "ignore")
        except Exception:
            out = ""
        try:
            err = (stderr.read() or b"").decode("utf-8", "ignore")
        except Exception:
            err = ""

        remote_path_default = "/home/wpw/data/BTS-Agent-Sys/BTS/MMCFormer-main/Downloads_SegGraph/seg_pred.png"
        remote_path_env = (os.environ.get("REMOTE_SEG_IMAGE") or "").strip()
        remote_seg_dir = (os.environ.get("REMOTE_SEG_DIR") or "").strip() or os.path.dirname(remote_path_env or remote_path_default)
        remote_case_pred = remote_seg_dir.rstrip("/") + f"/.seg_pred_{safe_case_id}.png"
        remote_case_gt = remote_seg_dir.rstrip("/") + f"/.seg_gt_{safe_case_id}.png"
        remote_case_dir = remote_seg_dir.rstrip("/") + f"/cases/{safe_case_id}"
        remote_case_pred2 = remote_case_dir + "/seg_pred.png"
        remote_case_gt2 = remote_case_dir + "/seg_gt.png"
        remote_case_meta = remote_case_dir + "/meta.json"
        try:
            _cp_cmd = (
                "bash -lc "
                + json.dumps(
                    f"cd {remote_seg_dir}; "
                    f"if [ -f seg_pred.png ]; then cp -f seg_pred.png {remote_case_pred}; fi; "
                    f"if [ -f seg_gt.png ]; then cp -f seg_gt.png {remote_case_gt}; fi; ",
                    ensure_ascii=False,
                )
            )
            _i_cp, _o_cp, _e_cp = client.exec_command(_cp_cmd, get_pty=False)
            try:
                _o_cp.channel.recv_exit_status()
            except Exception:
                pass
        except Exception:
            pass
        try:
            _case_dir_cmd = (
                "bash -lc "
                + json.dumps(
                    f"mkdir -p {remote_case_dir}; "
                    f"cd {remote_seg_dir}; "
                    f"if [ -f seg_pred.png ]; then cp -f seg_pred.png {remote_case_pred2}; fi; "
                    f"if [ -f seg_gt.png ]; then cp -f seg_gt.png {remote_case_gt2}; fi; "
                    "python -c "
                    + json.dumps(
                        (
                            "import json, os, time; "
                            f"out={remote_case_meta!r}; "
                            "meta={"
                            f"'case_id':{safe_case_id!r},"
                            f"'remote_seg_dir':{remote_seg_dir!r},"
                            f"'upload_dir':{remote_upload_dir!r},"
                            "'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),"
                            f"'files':{{'seg_pred':{remote_case_pred2!r},'seg_gt':{remote_case_gt2!r}}}"
                            "}; "
                            "os.makedirs(os.path.dirname(out), exist_ok=True); "
                            "open(out,'w',encoding='utf-8').write(json.dumps(meta,ensure_ascii=False,indent=2))"
                        ),
                        ensure_ascii=False,
                    ),
                    ensure_ascii=False,
                )
            )
            _i_cd, _o_cd, _e_cd = client.exec_command(_case_dir_cmd, get_pty=False)
            try:
                _o_cd.channel.recv_exit_status()
            except Exception:
                pass
        except Exception:
            pass
        downloaded = False
        download_err = None
        sftp = client.open_sftp()
        try:
            chosen_mask_remote = None
            chosen_png_remote = None
            try:
                sftp.stat(remote_case_pred2)
                chosen_png_remote = remote_case_pred2
            except Exception:
                chosen_png_remote = None

            if not chosen_png_remote:
                try:
                    sftp.stat(remote_case_pred)
                    chosen_png_remote = remote_case_pred
                except Exception:
                    chosen_png_remote = None

            if (not chosen_png_remote) and remote_path_env:
                try:
                    sftp.stat(remote_path_env)
                    base_env = os.path.basename(remote_path_env).lower()
                    if remote_path_env.lower().endswith((".nii", ".nii.gz")):
                        chosen_mask_remote = remote_path_env
                    elif ("pred" in base_env) or (safe_case_id.lower() in base_env):
                        chosen_png_remote = remote_path_env
                    else:
                        pass
                except Exception:
                    pass

            names = []
            if not (chosen_mask_remote or chosen_png_remote):
                try:
                    names = sftp.listdir(remote_seg_dir)
                except Exception:
                    names = []

                def _score(name: str) -> int:
                    s = name.lower()
                    score = 0
                    if safe_case_id.lower() in s:
                        score += 200
                    if "seg_pred" in s:
                        score += 100
                    if "pred" in s:
                        score += 50
                    if "seg" in s or "mask" in s or "label" in s:
                        score += 10
                    if "color" in s or "overlay" in s or "vis" in s:
                        score += 40
                    if "gt" in s:
                        score -= 10
                    return score

                nii_candidates = [n for n in (names or []) if str(n).lower().endswith((".nii", ".nii.gz"))]
                nii_candidates.sort(key=lambda n: _score(str(n)), reverse=True)
                if nii_candidates:
                    chosen_mask_remote = remote_seg_dir.rstrip("/") + "/" + str(nii_candidates[0])

                png_candidates = [n for n in (names or []) if str(n).lower().endswith(".png")]
                png_candidates.sort(key=lambda n: _score(str(n)), reverse=True)
                if png_candidates:
                    chosen_png_remote = remote_seg_dir.rstrip("/") + "/" + str(png_candidates[0])
            if chosen_png_remote:
                chosen_mask_remote = None

            if chosen_mask_remote:
                sftp.get(chosen_mask_remote, local_mask_path)
                remote_vis_path = remote_seg_dir.rstrip("/") + f"/.seg_vis_{safe_case_id}.png"
                remote_vis_cmd = (
                    "bash -lc "
                    + json.dumps(
                        "export MPLBACKEND='Agg'; "
                        "export DISPLAY=''; "
                        "export QT_QPA_PLATFORM='offscreen'; "
                        "export SDL_VIDEODRIVER='dummy'; "
                        f"source {conda_sh}; "
                        f"conda activate {conda_env}; "
                        "python -c "
                        + json.dumps(
                            (
                                "import os; os.environ['MPLBACKEND']='Agg'; "
                                "import numpy as np; import nibabel as nib; "
                                "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; "
                                f"mask_path={chosen_mask_remote!r}; out_path={remote_vis_path!r}; "
                                "os.makedirs(os.path.dirname(out_path), exist_ok=True); "
                                "img=nib.load(mask_path); data=img.get_fdata(); "
                                "data=np.nan_to_num(data); "
                                "mask=None; "
                                "thr_wt=float(os.environ.get('SEG_THR_WT','0.5')); "
                                "thr_tc=float(os.environ.get('SEG_THR_TC','0.5')); "
                                "thr_et=float(os.environ.get('SEG_THR_ET','0.5')); "
                                "nd=getattr(data,'ndim',0); "
                                "if nd==4: "
                                "  if data.shape[0] in (3,4): "
                                "    wt=data[0]; tc=data[1] if data.shape[0]>1 else np.zeros_like(wt); et=data[2] if data.shape[0]>2 else np.zeros_like(wt); "
                                "  elif data.shape[-1] in (3,4): "
                                "    wt=data[...,0]; tc=data[...,1]; et=data[...,2]; "
                                "  else: "
                                "    wt=data[...,0]; tc=np.zeros_like(wt); et=np.zeros_like(wt); "
                                "  mask=np.zeros_like(wt,dtype=np.int32); "
                                "  mask[wt>thr_wt]=2; mask[tc>thr_tc]=1; mask[et>thr_et]=4; "
                                "else: "
                                "  mask=np.rint(data).astype(np.int32) if nd==3 else np.rint(np.asarray(data)).astype(np.int32); "
                                "areas=[int((mask[...,z]>0).sum()) for z in range(mask.shape[-1])] if getattr(mask,'ndim',0)==3 else [0]; "
                                "z=int(np.argmax(areas)) if areas and max(areas)>0 else int((mask.shape[-1]//2) if getattr(mask,'ndim',0)==3 else 0); "
                                "sl=(mask[...,z] if getattr(mask,'ndim',0)==3 else mask).astype(np.int32); "
                                "rgb=np.zeros(sl.shape+(3,),dtype=np.uint8); "
                                "rgb[sl==2]=(0,0,255); "
                                "rgb[sl==1]=(0,255,0); "
                                "rgb[(sl==4)|(sl==3)]=(255,0,0); "
                                "plt.imsave(out_path, rgb); "
                                "print(out_path)"
                            ),
                            ensure_ascii=False,
                        ),
                        ensure_ascii=False,
                    )
                )
                try:
                    _i2, _o2, _e2 = client.exec_command(remote_vis_cmd, get_pty=False)
                    try:
                        _o2.channel.recv_exit_status()
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    sftp.get(remote_vis_path, local_vis_path)
                except Exception:
                    pass
                downloaded = True
            else:
                if not chosen_png_remote:
                    chosen_png_remote = remote_path_default
                remote_base = os.path.basename(str(chosen_png_remote)).lower()
                if "pred" in remote_base:
                    sftp.get(chosen_png_remote, local_pred_path)
                elif remote_base.endswith("seg_gt.png") or "gt" in remote_base:
                    sftp.get(chosen_png_remote, local_gt_path)
                else:
                    sftp.get(chosen_png_remote, local_pred_path)
                downloaded = True
        except Exception as img_err:
            download_err = img_err
        finally:
            try:
                sftp.close()
            except Exception:
                pass

        if not downloaded:
            msg = (err or out or str(download_err) or "remote_seg_failed")[:800]
            if exit_status not in (0, None):
                msg = f"remote_seg_failed(exit={exit_status}): " + msg
            return jsonify(success=False, message=msg), 500

        if os.path.exists(local_pred_path):
            try:
                from PIL import Image

                _img = Image.open(local_pred_path)
                _img.load()
                if _img.mode in ("RGB", "RGBA"):
                    return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_pred_path))
            except Exception:
                pass

        if _try_build_vis_from_mask() and os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))
        if _try_build_vis_from_raw_png(local_pred_path) and os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))
        if _try_build_vis_from_raw_png(local_gt_path) and os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))

        if os.path.exists(local_vis_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_vis_path))
        if os.path.exists(local_pred_path):
            return jsonify(success=True, case_id=case_id, url=url_for("static", filename=rel_pred_path))
        return jsonify(success=False, message="seg_vis_generate_failed"), 500
    except Exception as e:
        return jsonify(success=False, message=str(e)[:800]), 500
    finally:
        try:
            client.close()
        except Exception:
            pass

@app.route('/api/patient_nii_spin/<int:patient_id>')
@login_required
def api_patient_nii_spin(patient_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        return jsonify(success=False, message="patient_not_found"), 404
    cursor.execute("""
        SELECT id
        FROM diagnoses
        WHERE patient_id = %s
        ORDER BY diagnosis_date DESC, id DESC
        LIMIT 1
    """, (patient_id,))
    diagnosis = cursor.fetchone()
    cursor.close()
    db.close()
    if not diagnosis:
        return jsonify(success=True, case_id=None, frames=[])

    case_id = f"{patient.get('patient_id')}_{diagnosis.get('id')}"
    safe_case_id = normalize_case_id(case_id)
    frame_count = int(os.environ.get("NII_SPIN_FRAMES", "24"))
    frame_count = max(8, min(frame_count, 72))

    static_root = os.path.join(app.root_path, "static")
    local_dir = os.path.join(static_root, "nii_spin", safe_case_id)
    os.makedirs(local_dir, exist_ok=True)
    existing = []
    try:
        for i in range(frame_count):
            p = os.path.join(local_dir, f"frame_{i:02d}.png")
            if os.path.exists(p):
                existing.append(i)
    except Exception:
        existing = []
    if len(existing) == frame_count:
        urls = [url_for("static", filename=f"nii_spin/{safe_case_id}/frame_{i:02d}.png") for i in range(frame_count)]
        return jsonify(success=True, case_id=case_id, frames=urls)

    base_upload_root = os.environ.get("REMOTE_UPLOAD_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/Uploads")
    remote_dir = f"{base_upload_root}/{case_id}/"

    conda_env = os.environ.get("REMOTE_CONDA_ENV", "BTS_env")
    conda_sh = os.environ.get("REMOTE_CONDA_SH", "/home/wpw/miniconda3/etc/profile.d/conda.sh")

    hostname = ""
    port = ""
    client = None
    sftp = None
    last_err = None
    for _ in range(3):
        try:
            client, hostname, port = _connect_remote_ssh()
            sftp = client.open_sftp()
            break
        except Exception as e:
            last_err = e
            try:
                if client:
                    client.close()
            except Exception:
                pass
            client = None
            sftp = None
            time.sleep(0.4)
    if not sftp:
        return jsonify(success=False, message=f"remote_nii_spin_error:{hostname}:{port}:{str(last_err)}"), 500
    try:
            try:
                names = sftp.listdir(remote_dir)
            except Exception:
                return jsonify(success=True, case_id=case_id, frames=[])
            nii_files = [n for n in names if (n.endswith(".nii") or n.endswith(".nii.gz"))]
            nii_files.sort()
            if not nii_files:
                return jsonify(success=True, case_id=case_id, frames=[])
            src_name = None
            for n in nii_files:
                if "flair" in n.lower():
                    src_name = n
                    break
            if not src_name:
                src_name = nii_files[0]

            remote_nii = remote_dir.rstrip("/") + "/" + src_name
            remote_prefix = remote_dir.rstrip("/") + "/.spin_frame_"
            remote_script = f"/tmp/nii_spin_{safe_case_id}.py"
            script_body = f"""
import os
os.environ.pop('DISPLAY', None)
os.environ['MPLBACKEND'] = 'Agg'
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

nii_path = {remote_nii!r}
out_prefix = {remote_prefix!r}
n_frames = {frame_count}

img = nib.load(nii_path)
data = img.get_fdata()
if getattr(data, 'ndim', 0) == 4:
    data = data[..., 0]
data = np.nan_to_num(data)
lo, hi = np.percentile(data, [1, 99])
if (not np.isfinite(lo)) or (not np.isfinite(hi)) or hi <= lo:
    lo = float(np.min(data))
    hi = float(np.max(data))
if hi <= lo:
    hi = lo + 1.0
data = (np.clip(data, lo, hi) - lo) / (hi - lo)

sx = max(1, int(data.shape[0] // 64))
sy = max(1, int(data.shape[1] // 64))
sz = max(1, int(data.shape[2] // 64))
vol = data[::sx, ::sy, ::sz]
thr = float(np.percentile(vol, 60))
vox = vol > thr
if int(vox.sum()) > 45000:
    vox = vol > float(np.percentile(vol, 75))

fc = np.zeros(vox.shape + (4,), dtype=float)
fc[..., 0] = 0.78
fc[..., 1] = 0.78
fc[..., 2] = 0.78
fc[..., 3] = 0.88

for i in range(n_frames):
    fig = plt.figure(figsize=(4, 4), dpi=160)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_axis_off()
    ax.view_init(elev=18, azim=(i * (360.0 / n_frames)))
    ax.voxels(vox, facecolors=fc, edgecolor='none')
    plt.tight_layout(pad=0)
    fig.savefig(f"{{out_prefix}}{{i:02d}}.png", transparent=False)
    plt.close(fig)
print("ok")
""".lstrip()
            try:
                with sftp.open(remote_script, "w") as f:
                    f.write(script_body)
            except Exception as e:
                return jsonify(success=False, message=("3d_write_script_failed:" + str(e))[:500]), 500

            remote_cmd = (
                "bash -lc "
                + json.dumps(
                    f"source {conda_sh}; "
                    f"conda activate {conda_env}; "
                    f"MPLBACKEND=Agg python {remote_script}",
                    ensure_ascii=False,
                )
            )
            _stdin, _stdout, _stderr = client.exec_command(remote_cmd, get_pty=False)
            exit_status = None
            try:
                exit_status = _stdout.channel.recv_exit_status()
            except Exception:
                exit_status = None
            stdout_text = ""
            stderr_text = ""
            try:
                stdout_text = (_stdout.read() or b"").decode("utf-8", "ignore")
            except Exception:
                stdout_text = ""
            try:
                stderr_text = (_stderr.read() or b"").decode("utf-8", "ignore")
            except Exception:
                stderr_text = ""
            if exit_status not in (0, None):
                return jsonify(
                    success=False,
                    message=("3d_generate_failed:" + (stderr_text or stdout_text or "unknown_error"))[:500],
                ), 500

            try:
                sftp.remove(remote_script)
            except Exception:
                pass

            urls = []
            for i in range(frame_count):
                remote_png = f"{remote_prefix}{i:02d}.png"
                local_path = os.path.join(local_dir, f"frame_{i:02d}.png")
                try:
                    sftp.get(remote_png, local_path)
                    urls.append(url_for("static", filename=f"nii_spin/{safe_case_id}/frame_{i:02d}.png"))
                except Exception:
                    break
            if not urls:
                return jsonify(
                    success=False,
                    message=("3d_no_frames:" + (stderr_text or stdout_text or "no_output_frames"))[:500],
                ), 500
            return jsonify(success=True, case_id=case_id, frames=urls)
    finally:
        try:
            if sftp:
                sftp.close()
        except Exception:
            pass
        try:
            if client:
                client.close()
        except Exception:
            pass

@app.route('/api/patient_nii_spin_vtk/<int:patient_id>')
@login_required
def api_patient_nii_spin_vtk(patient_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        return jsonify(success=False, message="patient_not_found"), 404
    cursor.execute("""
        SELECT id
        FROM diagnoses
        WHERE patient_id = %s
        ORDER BY diagnosis_date DESC, id DESC
        LIMIT 1
    """, (patient_id,))
    diagnosis = cursor.fetchone()
    cursor.close()
    db.close()
    if not diagnosis:
        return jsonify(success=True, case_id=None, frames=[])

    case_id = f"{patient.get('patient_id')}_{diagnosis.get('id')}"
    safe_case_id = normalize_case_id(case_id)
    frame_count = int(os.environ.get("NII_VTK_FRAMES", "36"))
    frame_count = max(8, min(frame_count, 72))

    static_root = os.path.join(app.root_path, "static")
    local_dir = os.path.join(static_root, "nii_spin_vtk7", safe_case_id)
    os.makedirs(local_dir, exist_ok=True)
    existing = []
    try:
        for i in range(frame_count):
            p = os.path.join(local_dir, f"frame_{i:02d}.png")
            if os.path.exists(p):
                existing.append(i)
    except Exception:
        existing = []
    if len(existing) == frame_count:
        urls = [url_for("static", filename=f"nii_spin_vtk7/{safe_case_id}/frame_{i:02d}.png") for i in range(frame_count)]
        return jsonify(success=True, case_id=case_id, frames=urls)

    base_upload_root = os.environ.get("REMOTE_UPLOAD_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/Uploads")
    remote_dir = f"{base_upload_root}/{case_id}/"
    conda_env = os.environ.get("REMOTE_CONDA_ENV", "BTS_env")
    conda_sh = os.environ.get("REMOTE_CONDA_SH", "/home/wpw/miniconda3/etc/profile.d/conda.sh")

    hostname = ""
    port = ""
    client = None
    sftp = None
    last_err = None
    for _ in range(3):
        try:
            client, hostname, port = _connect_remote_ssh()
            sftp = client.open_sftp()
            break
        except Exception as e:
            last_err = e
            try:
                if client:
                    client.close()
            except Exception:
                pass
            client = None
            sftp = None
            time.sleep(0.4)
    if not sftp:
        return jsonify(success=False, message=f"remote_nii_vtk_spin_error:{hostname}:{port}:{str(last_err)}"), 500

    try:
        try:
            names = sftp.listdir(remote_dir)
        except Exception:
            return jsonify(success=True, case_id=case_id, frames=[])
        nii_files = [n for n in names if (n.endswith(".nii") or n.endswith(".nii.gz"))]
        nii_files.sort()
        if not nii_files:
            return jsonify(success=True, case_id=case_id, frames=[])
        src_name = None
        for n in nii_files:
            if "flair" in n.lower():
                src_name = n
                break
        if not src_name:
            src_name = nii_files[0]

        remote_nii = remote_dir.rstrip("/") + "/" + src_name
        remote_prefix = remote_dir.rstrip("/") + "/.spin_vtk7_frame_"
        remote_script = f"/tmp/nii_spin_vtk7_{safe_case_id}.py"
        script_body = f"""
import os
os.environ.pop('DISPLAY', None)
os.environ['VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN'] = '1'

import numpy as np
import nibabel as nib
import vtk
from vtk.util.numpy_support import numpy_to_vtk
import math

nii_path = {remote_nii!r}
out_prefix = {remote_prefix!r}
n_frames = {frame_count}

img = nib.load(nii_path)
try:
    img = nib.as_closest_canonical(img)
except Exception:
    pass
zooms = None
try:
    zooms = img.header.get_zooms()[:3]
except Exception:
    zooms = None
data = img.get_fdata()
if getattr(data, 'ndim', 0) == 4:
    data = data[..., 0]
data = np.nan_to_num(data).astype(np.float32)

lo, hi = np.percentile(data, [1, 99])
if (not np.isfinite(lo)) or (not np.isfinite(hi)) or hi <= lo:
    lo = float(np.min(data))
    hi = float(np.max(data))
if hi <= lo:
    hi = lo + 1.0
data = (np.clip(data, lo, hi) - lo) / (hi - lo)

sx = max(1, int(data.shape[0] // 160))
sy = max(1, int(data.shape[1] // 160))
sz = max(1, int(data.shape[2] // 160))
data = data[::sx, ::sy, ::sz]

x, y, z = int(data.shape[0]), int(data.shape[1]), int(data.shape[2])
vtk_data = numpy_to_vtk(data.ravel(order='F'), deep=True, array_type=vtk.VTK_FLOAT)
image = vtk.vtkImageData()
image.SetDimensions(x, y, z)
if zooms and len(zooms) == 3:
    try:
        image.SetSpacing(float(zooms[0]) * sx, float(zooms[1]) * sy, float(zooms[2]) * sz)
    except Exception:
        pass
image.GetPointData().SetScalars(vtk_data)

smooth = vtk.vtkImageGaussianSmooth()
smooth.SetInputData(image)
smooth.SetStandardDeviations(1.0, 1.0, 1.0)
smooth.SetRadiusFactors(1.5, 1.5, 1.5)

try:
    mc = vtk.vtkFlyingEdges3D()
except Exception:
    mc = vtk.vtkMarchingCubes()
mc.SetInputConnection(smooth.GetOutputPort())

isos = [float(np.percentile(data, p)) for p in (60, 50, 40, 30, 20, 10, 5, 2)]
picked = None
for iso in isos:
    iso = max(0.005, min(iso, 0.25))
    mc.SetValue(0, iso)
    mc.Update()
    try:
        cells = int(mc.GetOutput().GetNumberOfCells())
    except Exception:
        cells = 0
    if cells > 800:
        picked = iso
        break
if picked is None:
    mc.SetValue(0, 0.02)

normals = vtk.vtkPolyDataNormals()
normals.SetInputConnection(mc.GetOutputPort())
normals.SetFeatureAngle(60.0)
normals.ConsistencyOn()
normals.SplittingOff()

sm = vtk.vtkSmoothPolyDataFilter()
sm.SetInputConnection(normals.GetOutputPort())
sm.SetNumberOfIterations(20)
sm.SetRelaxationFactor(0.10)
sm.FeatureEdgeSmoothingOff()
sm.BoundarySmoothingOn()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(sm.GetOutputPort())
mapper.ScalarVisibilityOff()

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetColor(0.20, 0.78, 1.00)
actor.GetProperty().SetOpacity(0.55)
actor.GetProperty().SetAmbient(0.35)
actor.GetProperty().SetDiffuse(0.75)
actor.GetProperty().SetSpecular(0.35)
actor.GetProperty().SetSpecularPower(20.0)

wire = vtk.vtkActor()
wire.SetMapper(mapper)
wire.GetProperty().SetRepresentationToWireframe()
wire.GetProperty().SetColor(0.65, 0.98, 1.00)
wire.GetProperty().SetLineWidth(1.2)
wire.GetProperty().SetOpacity(0.14)

ren = vtk.vtkRenderer()
ren.SetBackground(0.02, 0.02, 0.04)
ren.AddActor(actor)
ren.AddActor(wire)

try:
    kit = vtk.vtkLightKit()
    kit.SetKeyLightIntensity(1.25)
    kit.SetFillLightIntensity(0.85)
    kit.SetBackLightIntensity(0.55)
    kit.SetHeadLightIntensity(0.25)
    kit.AddLightsToRenderer(ren)
except Exception:
    light = vtk.vtkLight()
    light.SetLightTypeToSceneLight()
    light.SetPosition(1.0, 1.0, 1.0)
    light.SetFocalPoint(0.0, 0.0, 0.0)
    light.SetIntensity(1.2)
    ren.AddLight(light)

renWin = vtk.vtkRenderWindow()
renWin.SetOffScreenRendering(1)
renWin.AddRenderer(ren)
renWin.SetSize(640, 640)
try:
    renWin.SetAlphaBitPlanes(1)
    renWin.SetMultiSamples(0)
    ren.SetUseDepthPeeling(1)
    ren.SetMaximumNumberOfPeels(60)
    ren.SetOcclusionRatio(0.08)
except Exception:
    pass

cam = ren.GetActiveCamera()
cx0, cy0, cz0 = (x / 2.0), (y / 2.0), (z / 2.0)
cam.SetFocalPoint(cx0, cy0, cz0)
dist = max(x, y, z) * 1.8
cam.SetViewUp(0.0, 0.0, 1.0)
cam.OrthogonalizeViewUp()
try:
    cam.SetViewAngle(28.0)
except Exception:
    pass
ren.ResetCameraClippingRange()
w2i = vtk.vtkWindowToImageFilter()
w2i.SetInput(renWin)
w2i.SetInputBufferTypeToRGBA()
w2i.ReadFrontBufferOff()
w2i.Update()

writer = vtk.vtkPNGWriter()
writer.SetInputConnection(w2i.GetOutputPort())

for i in range(n_frames):
    theta = (2.0 * math.pi * i) / float(n_frames)
    cam.SetPosition(cx0 + dist * math.cos(theta), cy0 + dist * math.sin(theta), cz0 + dist * 0.18)
    cam.SetViewUp(0.0, 0.0, 1.0)
    cam.OrthogonalizeViewUp()
    renWin.Render()
    w2i.Modified()
    out_path = f"{{out_prefix}}{{i:02d}}.png"
    writer.SetFileName(out_path)
    writer.Write()

print("ok")
""".lstrip()
        try:
            with sftp.open(remote_script, "w") as f:
                f.write(script_body)
        except Exception as e:
            return jsonify(success=False, message=("vtk_write_script_failed:" + str(e))[:500]), 500

        remote_cmd = (
            "bash -lc "
            + json.dumps(
                f"source {conda_sh}; "
                f"conda activate {conda_env}; "
                f"VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN=1 MPLBACKEND=Agg python {remote_script}",
                ensure_ascii=False,
            )
        )
        _stdin, _stdout, _stderr = client.exec_command(remote_cmd, get_pty=False)
        exit_status = None
        try:
            exit_status = _stdout.channel.recv_exit_status()
        except Exception:
            exit_status = None
        stdout_text = ""
        stderr_text = ""
        try:
            stdout_text = (_stdout.read() or b"").decode("utf-8", "ignore")
        except Exception:
            stdout_text = ""
        try:
            stderr_text = (_stderr.read() or b"").decode("utf-8", "ignore")
        except Exception:
            stderr_text = ""
        if exit_status not in (0, None):
            return jsonify(success=False, message=("vtk_generate_failed:" + (stderr_text or stdout_text or "unknown_error"))[:500]), 500
        try:
            sftp.remove(remote_script)
        except Exception:
            pass

        urls = []
        for i in range(frame_count):
            remote_png = f"{remote_prefix}{i:02d}.png"
            local_path = os.path.join(local_dir, f"frame_{i:02d}.png")
            try:
                sftp.get(remote_png, local_path)
                urls.append(url_for("static", filename=f"nii_spin_vtk7/{safe_case_id}/frame_{i:02d}.png"))
            except Exception:
                break
        if not urls:
            return jsonify(success=False, message=("vtk_no_frames:" + (stderr_text or stdout_text or "no_output_frames"))[:500]), 500
        return jsonify(success=True, case_id=case_id, frames=urls)
    finally:
        try:
            if sftp:
                sftp.close()
        except Exception:
            pass
        try:
            if client:
                client.close()
        except Exception:
            pass

@app.route('/api/patient_chat/<int:patient_id>', methods=['POST'])
@login_required
def api_patient_chat(patient_id):
    from utils import Agent, get_required_api_key_env
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    history = payload.get("history") or []
    if not question:
        return jsonify(success=False, message="empty_question"), 400
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        return jsonify(success=False, message="patient_not_found"), 404
    cursor.execute("""
        SELECT d.*, u.username AS doctor_name
        FROM diagnoses d
        LEFT JOIN users u ON d.doctor_id = u.id
        WHERE d.patient_id = %s
        ORDER BY d.diagnosis_date DESC, d.id DESC
        LIMIT 1
    """, (patient_id,))
    diagnosis = cursor.fetchone()
    agent = None
    if diagnosis and diagnosis.get("id"):
        cursor.execute("""
            SELECT *
            FROM diagnosis_agent_results
            WHERE diagnosis_id = %s
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """, (diagnosis["id"],))
        agent = cursor.fetchone()
    cursor.close()
    db.close()

    model_info = (os.environ.get('SINGLE_AGENT_MODEL') or 'deepseek-chat').strip() or 'deepseek-chat'
    api_key_env = get_required_api_key_env(model_info)
    api_key = os.environ.get('SINGLE_AGENT_API_KEY')
    if api_key:
        os.environ[api_key_env] = api_key
        os.environ[api_key_env.upper()] = api_key
    if not (os.environ.get(api_key_env) or os.environ.get(api_key_env.upper())):
        return jsonify(success=False, message=f"missing_api_key:{api_key_env}"), 400

    instruction = "你是医疗AI助手，帮助用户理解智能分析结果与医学术语，用中文回答，简洁、准确、避免编造。"
    doctor_agent = Agent(instruction, role='AI Assistant', model_info=model_info)

    safe_history = []
    try:
        for item in history[-10:]:
            r = (item.get("role") or "").strip()
            c = (item.get("content") or "").strip()
            if r in ("user", "assistant") and c:
                safe_history.append({"role": r, "content": c})
    except Exception:
        safe_history = []

    context_obj = {
        "patient": {
            "id": patient.get("id"),
            "patient_id": patient.get("patient_id"),
            "name": patient.get("name"),
            "gender": patient.get("gender"),
            "age": patient.get("age"),
        },
        "diagnosis": diagnosis,
        "agent_result": agent,
    }
    context_text = json.dumps(context_obj, ensure_ascii=False, default=str)
    history_text = ""
    if safe_history:
        history_text = json.dumps(safe_history, ensure_ascii=False)
    prompt = (
        "下面是当前病人的诊断与智能分析结果（JSON）：\n"
        + context_text
        + "\n\n"
        + ("对话历史（JSON）：\n" + history_text + "\n\n" if history_text else "")
        + "用户问题：\n"
        + question
        + "\n\n"
        + "请解释用户不理解的点，必要时用通俗类比；如果信息不足，明确说明需要补充什么。"
    )
    try:
        answer = doctor_agent.chat(prompt)
        return jsonify(success=True, answer=answer)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/patient/<int:patient_id>/clinical_info', methods=['GET', 'POST'])
@login_required
def edit_patient_clinical_info(patient_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
    patient = cursor.fetchone()
    if not patient:
        cursor.close()
        db.close()
        flash('病人不存在！', 'danger')
        return redirect(url_for('patients'))
    cursor.execute("SELECT * FROM patient_clinical_info WHERE patient_id = %s", (patient_id,))
    clinical_info = cursor.fetchone()
    if request.method == 'POST':
        chief_complaint = request.form.get('chief_complaint') or None
        present_illness = request.form.get('present_illness') or None
        past_medical_history = request.form.get('past_medical_history') or None
        family_history = request.form.get('family_history') or None
        allergy_history = request.form.get('allergy_history') or None
        headache = request.form.get('symptom_headache') == 'on'
        vomiting = request.form.get('symptom_vomiting') == 'on'
        seizure = request.form.get('symptom_seizure') == 'on'
        vision_problem = request.form.get('symptom_vision_problem') == 'on'
        speech_problem = request.form.get('symptom_speech_problem') == 'on'
        limb_weakness = request.form.get('symptom_limb_weakness') == 'on'
        specific_remarks = request.form.get('specific_remarks') or None
        if clinical_info:
            cursor.execute("""
                UPDATE patient_clinical_info
                SET chief_complaint = %s,
                    present_illness = %s,
                    past_medical_history = %s,
                    family_history = %s,
                    allergy_history = %s,
                    headache = %s,
                    vomiting = %s,
                    seizure = %s,
                    vision_problem = %s,
                    speech_problem = %s,
                    limb_weakness = %s,
                    specific_remarks = %s
                WHERE patient_id = %s
            """, (
                chief_complaint,
                present_illness,
                past_medical_history,
                family_history,
                allergy_history,
                headache,
                vomiting,
                seizure,
                vision_problem,
                speech_problem,
                limb_weakness,
                specific_remarks,
                patient_id
            ))
        else:
            cursor.execute("""
                INSERT INTO patient_clinical_info (
                    patient_id,
                    chief_complaint,
                    present_illness,
                    past_medical_history,
                    family_history,
                    allergy_history,
                    headache,
                    vomiting,
                    seizure,
                    vision_problem,
                    speech_problem,
                    limb_weakness,
                    specific_remarks
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                patient_id,
                chief_complaint,
                present_illness,
                past_medical_history,
                family_history,
                allergy_history,
                headache,
                vomiting,
                seizure,
                vision_problem,
                speech_problem,
                limb_weakness,
                specific_remarks
            ))
        db.commit()
        cursor.close()
        db.close()
        flash('临床信息已保存！', 'success')
        return redirect(url_for('diagnoses', patient_id=patient_id))
    cursor.close()
    db.close()
    return render_template('patient_clinical_info.html', patient=patient, clinical_info=clinical_info)

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
            upload_dir = os.path.join(app.root_path, "static", "uploaded_images")
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
                INSERT INTO images (diagnosis_id, image_path, image_name, image_type)
                VALUES (%s, %s, %s, %s)
            """, (diagnosis_id, filename, file.filename, file.mimetype))
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
                    notification_type='todo',
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

@app.route('/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT diagnosis_id, image_path FROM images WHERE id = %s", (image_id,))
    image = cursor.fetchone()
    if not image:
        cursor.close()
        db.close()
        flash('图片不存在', 'danger')
        return redirect(url_for('main_interface'))
    diagnosis_id = image['diagnosis_id']
    image_path = image['image_path']
    cursor.execute("DELETE FROM images WHERE id = %s", (image_id,))
    db.commit()
    cursor.close()
    db.close()
    file_path = os.path.join(app.root_path, "static", "uploaded_images", image_path)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass
    flash('图片已删除', 'success')
    return redirect(url_for('view_images', diagnosis_id=diagnosis_id))

# 删除诊断记录路由
@app.route('/delete_diagnosis/<int:diagnosis_id>', methods=['POST'])
@login_required
def delete_diagnosis(diagnosis_id):
    if current_user.role != 'admin':
        flash('权限不足！', 'danger')
        return redirect(url_for('main_interface'))
    
    try:
        # 获取该诊断记录的病人ID
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT patient_id FROM diagnoses WHERE id = %s", (diagnosis_id,))
        diagnosis = cursor.fetchone()
        
        if diagnosis:
            patient_id = diagnosis['patient_id']
            
            # 删除诊断记录（级联删除相关图片）
            cursor.execute("DELETE FROM diagnoses WHERE id = %s", (diagnosis_id,))
            # 更新所有大于被删除ID的记录的ID，实现ID顺延
            cursor.execute("UPDATE diagnoses SET id = id - 1 WHERE id > %s", (diagnosis_id,))
            db.commit()
            flash('诊断记录删除成功！', 'success')
            
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

@app.route('/run_agent_analysis/<int:diagnosis_id>', methods=['POST'])
@login_required
def run_agent_analysis(diagnosis_id):
    payload, patient_id = build_agent_input(diagnosis_id)
    if not payload:
        flash('诊断记录不存在，无法进行智能分析', 'danger')
        return redirect(url_for('main_interface'))
    try:
        agent_output = call_agent(payload)
    except Exception as e:
        flash(f'智能分析失败: {e}', 'danger')
        return redirect(url_for('diagnoses', patient_id=patient_id))
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO diagnosis_agent_results (
                diagnosis_id,
                tumor_location,
                tumor_analysis,
                severity_assessment,
                possible_diagnosis,
                recommendation,
                need_doctor_review,
                confidence,
                confidence_reason,
                remarks,
                raw_output
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            diagnosis_id,
            agent_output.get("tumor_location"),
            agent_output.get("tumor_analysis"),
            agent_output.get("severity_assessment"),
            agent_output.get("possible_diagnosis"),
            agent_output.get("recommendation"),
            agent_output.get("need_doctor_review"),
            agent_output.get("confidence"),
            agent_output.get("confidence_reason"),
            agent_output.get("remarks"),
            json.dumps(agent_output, ensure_ascii=False)
        ))
        db.commit()
        cursor.close()
        db.close()
        flash('智能体分析完成！', 'success')
    except Exception as e:
        flash(f'保存智能分析结果失败: {e}', 'danger')
    return redirect(url_for('diagnoses', patient_id=patient_id))

@app.route('/run_agent_analysis_api/<int:diagnosis_id>', methods=['POST'])
@login_required
def run_agent_analysis_api(diagnosis_id):
    payload, patient_id = build_agent_input(diagnosis_id)
    if not payload:
        return jsonify(success=False, message='诊断记录不存在')
    try:
        agent_output = call_agent(payload)
    except Exception as e:
        return jsonify(success=False, message=f'智能分析失败: {e}')
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO diagnosis_agent_results (
                diagnosis_id,
                tumor_location,
                tumor_analysis,
                severity_assessment,
                possible_diagnosis,
                recommendation,
                need_doctor_review,
                confidence,
                confidence_reason,
                remarks,
                raw_output
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            diagnosis_id,
            agent_output.get("tumor_location"),
            agent_output.get("tumor_analysis"),
            agent_output.get("severity_assessment"),
            agent_output.get("possible_diagnosis"),
            agent_output.get("recommendation"),
            agent_output.get("need_doctor_review"),
            agent_output.get("confidence"),
            agent_output.get("confidence_reason"),
            agent_output.get("remarks"),
            json.dumps(agent_output, ensure_ascii=False)
        ))
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        return jsonify(success=False, message=f'保存智能分析结果失败: {e}')
    return jsonify(success=True, data=agent_output)

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

@app.route('/edit_diagnosis/<int:diagnosis_id>', methods=['GET', 'POST'])
@login_required
def edit_diagnosis(diagnosis_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.*, p.name as patient_name, p.gender, p.age, p.patient_id as case_patient_id
        FROM diagnoses d
        JOIN patients p ON d.patient_id = p.id
        WHERE d.id = %s
    """, (diagnosis_id,))
    diagnosis = cursor.fetchone()
    if not diagnosis:
        cursor.close()
        db.close()
        flash('诊断记录不存在！', 'danger')
        return redirect(url_for('main_interface'))

    if request.method == 'POST':
        diagnosis_type = request.form['diagnosis_type']
        tumor_type = request.form['tumor_type']
        tumor_stage = request.form['tumor_stage']
        diagnosis_date_str = request.form['diagnosis_date']
        diagnosis_content = request.form['diagnosis_content']
        treatment_plan = request.form['treatment_plan']
        examination_results = request.form['examination_results']
        notes = request.form['notes']
        try:
            diagnosis_date = datetime.strptime(diagnosis_date_str, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            diagnosis_date = diagnosis['diagnosis_date']
        try:
            cursor.execute("""
                UPDATE diagnoses
                SET diagnosis_date = %s,
                    diagnosis_type = %s,
                    tumor_type = %s,
                    tumor_stage = %s,
                    diagnosis_content = %s,
                    treatment_plan = %s,
                    examination_results = %s,
                    notes = %s
                WHERE id = %s
            """, (
                diagnosis_date,
                diagnosis_type,
                tumor_type,
                tumor_stage,
                diagnosis_content,
                treatment_plan,
                examination_results,
                notes,
                diagnosis_id
            ))
            db.commit()
            flash('诊断记录已更新！', 'success')
            patient_id = diagnosis['patient_id']
            cursor.close()
            db.close()
            return redirect(url_for('diagnoses', patient_id=patient_id))
        except mysql.connector.Error as err:
            db.rollback()
            flash(f'更新诊断记录失败: {err}', 'danger')
    cursor.close()
    db.close()
    patient = {
        "id": diagnosis['patient_id'],
        "name": diagnosis['patient_name'],
        "gender": diagnosis.get('gender'),
        "age": diagnosis.get('age'),
        "patient_id": diagnosis.get('case_patient_id')
    }
    return render_template(
        'add_diagnosis.html',
        patient=patient,
        today=diagnosis['diagnosis_date'],
        diagnosis=diagnosis,
        is_edit=True
    )

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
    diagnosis_id_raw = request.form.get('diagnosis_id')
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
    # 传到远程目录
    try:
        case_id = os.environ.get("SEG_CASE_ID", "Brats18_TCIA01_1_1")
        if diagnosis_id_raw:
            try:
                diagnosis_id = int(diagnosis_id_raw)
                db = get_db()
                cursor = db.cursor(dictionary=True)
                cursor.execute("""
                    SELECT p.patient_id
                    FROM diagnoses d
                    JOIN patients p ON d.patient_id = p.id
                    WHERE d.id = %s
                """, (diagnosis_id,))
                row = cursor.fetchone()
                cursor.close()
                db.close()
                if row and row.get("patient_id"):
                    case_id = f"{row['patient_id']}_{diagnosis_id}"
            except Exception:
                pass
        case_id = normalize_case_id(case_id)

        client, _hostname, _port = _connect_remote_ssh()
        sftp = client.open_sftp()
        base_upload_root = os.environ.get("REMOTE_UPLOAD_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/Uploads")
        remote_dir = f"{base_upload_root}/{case_id}/"
        ensure_remote_dir(sftp, remote_dir)
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
        return jsonify(success=True, message=f"上传成功（{case_id}）", case_id=case_id)
    except Exception as e:
        return jsonify(success=False, message=f"上传失败: {str(e)}")

# 远程测试路由
@app.route('/remote_test', methods=['GET', 'POST'])
@login_required
def remote_test():
    status = "未运行"
    output = ""
    image_url = None
    diagnosis_id = request.args.get('diagnosis_id', default=None, type=int)
    if request.method == 'POST':
        diagnosis_id_form = request.form.get('diagnosis_id')
        if diagnosis_id_form:
            try:
                diagnosis_id = int(diagnosis_id_form)
            except Exception:
                diagnosis_id = None
    if request.method == 'POST':
        # 点击按钮后，由前端JS立即设置为运行中，后台开始执行
        status = "运行中"
        try:
            # 参考 test.py 中的逻辑
            case_id = os.environ.get("SEG_CASE_ID", "Brats18_TCIA01_1_1")
            if diagnosis_id:
                try:
                    db = get_db()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT p.patient_id
                        FROM diagnoses d
                        JOIN patients p ON d.patient_id = p.id
                        WHERE d.id = %s
                    """, (diagnosis_id,))
                    row = cursor.fetchone()
                    cursor.close()
                    db.close()
                    if row and row.get("patient_id"):
                        case_id = f"{row['patient_id']}_{diagnosis_id}"
                except Exception:
                    pass
            case_id = normalize_case_id(case_id)
            base_upload_root = os.environ.get("REMOTE_UPLOAD_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/Uploads")
            remote_upload_dir = f"{base_upload_root}/{case_id}/"

            client, _hostname, _port = _connect_remote_ssh()

            # 在运行之前检查远程Uploads目录是否有文件
            try:
                sftp_check = client.open_sftp()
                files_list = sftp_check.listdir(remote_upload_dir)
                if not files_list:
                    status = "未运行"
                    output = f"远程Uploads目录没有nii文件，请先上传（{case_id}）"
                    sftp_check.close()
                    client.close()
                    return render_template('remote_test.html', status=status, output=output, image_url=image_url, diagnosis_id=diagnosis_id, case_id=case_id)
                sftp_check.close()
            except Exception:
                # 如果目录不存在或其他问题，也继续执行命令，留给后续步骤处理
                pass

            conda_env = os.environ.get("REMOTE_CONDA_ENV", "BTS_env")
            mmc_root = os.environ.get("REMOTE_MMC_ROOT", "/home/wpw/data/BTS-Agent-Sys/BTS/MMCFormer-main")
            command = (
                "bash -lc "
                + json.dumps(
                    f"export CASE_ID='{case_id}'; "
                    f"export UPLOAD_DIR='{remote_upload_dir}'; "
                    "source /home/wpw/miniconda3/etc/profile.d/conda.sh; "
                    f"conda activate {conda_env}; "
                    f"cd {mmc_root}; "
                    "python Valide.py",
                    ensure_ascii=False,
                )
            )

            stdin, stdout, stderr = client.exec_command(command)
            out = stdout.read().decode('utf8')
            err = stderr.read().decode('utf8')

            # 尝试获取远程生成的图片
            try:
                sftp = client.open_sftp()
                remote_path = os.environ.get("REMOTE_SEG_IMAGE", '/home/wpw/data/BTS-Agent-Sys/BTS/MMCFormer-main/Downloads_SegGraph/seg_gt.png')
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
    case_id_for_page = ""
    if diagnosis_id:
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.patient_id
                FROM diagnoses d
                JOIN patients p ON d.patient_id = p.id
                WHERE d.id = %s
            """, (diagnosis_id,))
            row = cursor.fetchone()
            cursor.close()
            db.close()
            if row and row.get("patient_id"):
                case_id_for_page = normalize_case_id(f"{row['patient_id']}_{diagnosis_id}")
        except Exception:
            pass
    return render_template('remote_test.html', status=status, output=output, image_url=image_url, diagnosis_id=diagnosis_id, case_id=case_id_for_page)

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

@app.route('/api/main-todos', methods=['GET'])
@login_required
def api_main_todos():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        if current_user.role == 'admin':
            cursor.execute(
                """
                SELECT t.id, t.title, t.content, t.due_date, t.is_completed,
                       t.assignee_id, u.username as assignee_name
                FROM todos t
                JOIN users u ON t.assignee_id = u.id
                ORDER BY t.is_completed ASC, t.due_date ASC, t.created_at DESC
                LIMIT 12
                """
            )
        else:
            cursor.execute(
                """
                SELECT t.id, t.title, t.content, t.due_date, t.is_completed,
                       t.assignee_id, u.username as assignee_name
                FROM todos t
                JOIN users u ON t.assignee_id = u.id
                WHERE t.assignee_id = %s
                ORDER BY t.is_completed ASC, t.due_date ASC, t.created_at DESC
                LIMIT 12
                """,
                (current_user.id,),
            )
        todo_rows = cursor.fetchall() or []

        cursor.execute("SELECT id, username, real_name FROM users WHERE role = 'doctor' ORDER BY username")
        doctor_rows = cursor.fetchall() or []

        todos_out = []
        for row in todo_rows:
            due_date = row.get("due_date")
            if hasattr(due_date, "strftime"):
                due_date_str = due_date.strftime("%Y-%m-%d")
            else:
                due_date_str = str(due_date or "")
            todos_out.append(
                {
                    "id": int(row.get("id") or 0),
                    "task_name": str(row.get("title") or ""),
                    "content": str(row.get("content") or ""),
                    "deadline": due_date_str,
                    "assignee_id": int(row.get("assignee_id") or 0),
                    "assignee_name": str(row.get("assignee_name") or ""),
                    "is_completed": bool(row.get("is_completed")),
                }
            )

        doctors_out = []
        for row in doctor_rows:
            doctors_out.append(
                {
                    "id": int(row.get("id") or 0),
                    "username": str(row.get("username") or ""),
                    "real_name": str(row.get("real_name") or ""),
                }
            )

        return jsonify({"ok": True, "todos": todos_out, "doctors": doctors_out})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass

@app.route('/api/main-todos', methods=['POST'])
@login_required
def api_create_main_todo():
    if current_user.role != 'admin':
        return jsonify({"ok": False, "message": "权限不足"}), 403
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("task_name") or "").strip()
    content = str(payload.get("content") or "").strip()
    deadline = str(payload.get("deadline") or "").strip()
    assignee_id = payload.get("assignee_id")
    if not title or not content or not deadline or not assignee_id:
        return jsonify({"ok": False, "message": "参数不完整"}), 400
    try:
        due_date = datetime.strptime(deadline, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return jsonify({"ok": False, "message": "日期格式应为 YYYY-MM-DD"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            INSERT INTO todos (title, content, assigner_id, assignee_id, due_date, is_completed, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (title, content, current_user.id, int(assignee_id), due_date, 0),
        )
        todo_id = cursor.lastrowid
        db.commit()
        return jsonify(
            {
                "ok": True,
                "todo": {
                    "id": int(todo_id),
                    "task_name": title,
                    "content": content,
                    "deadline": due_date,
                    "assignee_id": int(assignee_id),
                },
            }
        )
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "message": str(e)}), 500
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass

@app.route('/api/main-todos/<int:todo_id>', methods=['DELETE'])
@login_required
def api_delete_main_todo(todo_id):
    if current_user.role != 'admin':
        return jsonify({"ok": False, "message": "权限不足"}), 403
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM todos WHERE id = %s", (todo_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"ok": False, "message": "待办不存在"}), 404
        cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
        db.commit()
        return jsonify({"ok": True})
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "message": str(e)}), 500
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass

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

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    if current_user.role != 'admin':
        flash('只有管理员可以删除待办任务！', 'danger')
        return redirect(url_for('todos'))
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM todos WHERE id = %s", (todo_id,))
        todo = cursor.fetchone()
        if not todo:
            flash('待办任务不存在！', 'danger')
            cursor.close()
            db.close()
            return redirect(url_for('todos'))
        cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
        db.commit()
        cursor.close()
        db.close()
        flash('待办任务已删除！', 'success')
        return redirect(url_for('todos'))
    except Exception as err:
        flash(f'删除待办任务失败: {err}', 'danger')
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
