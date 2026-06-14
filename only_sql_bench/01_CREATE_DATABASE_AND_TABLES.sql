-- ============================================================================
-- BTS-Agent 脑肿瘤诊断系统 - 数据库和表创建
-- ============================================================================
-- 说明：创建数据库、所有表结构和约束
-- 执行顺序：第1步

-- 创建数据库
CREATE DATABASE IF NOT EXISTS SECD CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE SECD;

-- ============================================================================
-- 【users 表】- 系统用户表
-- ============================================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `role` ENUM('admin', 'doctor', 'viewer') NOT NULL,
    `real_name` VARCHAR(100) NULL,
    `department` VARCHAR(100) NULL,
    `title` VARCHAR(100) NULL,
    `phone` VARCHAR(30) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 【patients 表】- 患者基本信息表
-- ============================================================================
DROP TABLE IF EXISTS `patients`;
CREATE TABLE `patients` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `patient_id` VARCHAR(20) NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `gender` VARCHAR(20) NOT NULL,
    `age` INT NOT NULL,
    `birthday` DATE NULL,
    `phone` VARCHAR(20) NULL,
    `address` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 【diagnoses 表】- 诊断记录表（核心业务表）
-- ============================================================================
DROP TABLE IF EXISTS `diagnoses`;
CREATE TABLE `diagnoses` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `patient_id` INT NOT NULL,
    `doctor_id` INT NOT NULL,
    `diagnosis_date` TIMESTAMP NOT NULL,
    `follow_up_date` DATE NULL,
    `diagnosis_type` VARCHAR(50) NULL,
    `tumor_type` VARCHAR(100) NULL,
    `tumor_stage` VARCHAR(20) NULL,
    `diagnosis_content` TEXT NOT NULL,
    `treatment_plan` TEXT NULL,
    `examination_results` TEXT NULL,
    `notes` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 【images 表】- 诊断图像管理表
-- ============================================================================
DROP TABLE IF EXISTS `images`;
CREATE TABLE `images` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `diagnosis_id` INT NOT NULL,
    `file_path` VARCHAR(255) NOT NULL,
    `image_name` VARCHAR(100) NOT NULL,
    `image_type` VARCHAR(20) NOT NULL,
    `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 【notifications 表】- 系统通知表
-- ============================================================================
DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `type` ENUM('new_diagnosis', 'follow_up', 'todo') NOT NULL,
    `title` VARCHAR(100) NOT NULL,
    `content` TEXT NOT NULL,
    `related_id` INT NOT NULL,
    `is_read` BOOLEAN DEFAULT FALSE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `read_at` TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 【todos 表】- 待办任务表
-- ============================================================================
DROP TABLE IF EXISTS `todos`;
CREATE TABLE `todos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(100) NOT NULL,
    `content` TEXT NOT NULL,
    `assigner_id` INT NOT NULL,
    `assignee_id` INT NOT NULL,
    `due_date` DATE NOT NULL,
    `is_completed` BOOLEAN DEFAULT FALSE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `completed_at` TIMESTAMP NULL,
    FOREIGN KEY (assigner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 创建索引以优化查询性能
-- ============================================================================
CREATE INDEX idx_diagnoses_patient ON diagnoses(patient_id);
CREATE INDEX idx_diagnoses_doctor ON diagnoses(doctor_id);
CREATE INDEX idx_diagnoses_date ON diagnoses(diagnosis_date);
CREATE INDEX idx_patients_name ON patients(name);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_todos_assigner ON todos(assigner_id);
CREATE INDEX idx_todos_assignee ON todos(assignee_id);

-- ============================================================================
-- 完成：所有表已创建
-- ============================================================================
