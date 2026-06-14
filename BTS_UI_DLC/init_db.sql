-- 肿瘤病例管理系统数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS SECD CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE SECD;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'doctor') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建病人表
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender ENUM('男', '女') NOT NULL,
    age INT NOT NULL,
    birthday DATE NULL,
    phone VARCHAR(20) NULL,
    address TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建诊断表
CREATE TABLE IF NOT EXISTS diagnoses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    diagnosis_date TIMESTAMP NOT NULL,
    follow_up_date DATE NULL,
    diagnosis_type VARCHAR(50) NULL,
    tumor_type VARCHAR(100) NULL,
    tumor_stage VARCHAR(20) NULL,
    diagnosis_content TEXT NOT NULL,
    treatment_plan TEXT NULL,
    examination_results TEXT NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建图片表
CREATE TABLE IF NOT EXISTS images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    diagnosis_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    image_name VARCHAR(100) NOT NULL,
    image_type VARCHAR(20) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
);

-- 创建通知表
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('new_diagnosis', 'follow_up') NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    related_id INT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 插入管理员账号（密码：admin123）
INSERT INTO users (username, password, role) VALUES ('admin', '0000000000000000000000000000000000000000000000000000000000000000', 'admin');

-- 插入示例医生账号（密码：doctor123）
INSERT INTO users (username, password, role) VALUES ('doctor1', '0000000000000000000000000000000000000000000000000000000000000000', 'doctor');

-- 插入示例病人数据
INSERT INTO patients (patient_id, name, gender, age, birthday, phone, address) 
VALUES ('PT001', '张三', '男', 56, '1967-05-20', '13800138001', '北京市朝阳区');

-- 插入示例诊断记录
INSERT INTO diagnoses (patient_id, doctor_id, diagnosis_date, diagnosis_type, tumor_type, tumor_stage, diagnosis_content, treatment_plan, examination_results, notes) 
VALUES (1, 2, '2023-10-15 14:30:00', 'CT扫描', '疑似肺癌', 'II期', '左侧肺部阴影，大小约3.5cm×4.0cm，边界不清，建议进一步病理检查。', '建议手术切除+化疗', 'CT扫描显示左侧肺部有占位性病变，肿瘤标志物CEA升高。', '避免吸烟，定期复查。');

SELECT '数据库初始化完成！' AS result;
