-- Full export for database `SECD2`
-- Generated at 2026-05-30 20:34:48

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;

CREATE DATABASE IF NOT EXISTS `SECD2` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `SECD2`;

DROP TABLE IF EXISTS `todos`;
DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `images`;
DROP TABLE IF EXISTS `diagnoses`;
DROP TABLE IF EXISTS `patients`;
DROP TABLE IF EXISTS `users`;

-- Structure for `users`
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('admin','doctor') COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `real_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `department` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=133 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Structure for `patients`
CREATE TABLE `patients` (
  `id` int NOT NULL AUTO_INCREMENT,
  `patient_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gender` enum('男','女') COLLATE utf8mb4_unicode_ci NOT NULL,
  `age` int NOT NULL,
  `birthday` date DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `patient_id` (`patient_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Structure for `diagnoses`
CREATE TABLE `diagnoses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int NOT NULL,
  `doctor_id` int NOT NULL,
  `diagnosis_date` timestamp NOT NULL,
  `follow_up_date` date DEFAULT NULL,
  `diagnosis_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tumor_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tumor_stage` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `diagnosis_content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `treatment_plan` text COLLATE utf8mb4_unicode_ci,
  `examination_results` text COLLATE utf8mb4_unicode_ci,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `patient_id` (`patient_id`),
  KEY `doctor_id` (`doctor_id`),
  CONSTRAINT `diagnoses_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE,
  CONSTRAINT `diagnoses_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Structure for `images`
CREATE TABLE `images` (
  `id` int NOT NULL AUTO_INCREMENT,
  `diagnosis_id` int NOT NULL,
  `image_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `uploaded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `diagnosis_id` (`diagnosis_id`),
  CONSTRAINT `images_ibfk_1` FOREIGN KEY (`diagnosis_id`) REFERENCES `diagnoses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Structure for `notifications`
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `type` enum('new_diagnosis','follow_up','todo') COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `related_id` int NOT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `read_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Structure for `todos`
CREATE TABLE `todos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `assigner_id` int NOT NULL,
  `assignee_id` int NOT NULL,
  `due_date` date NOT NULL,
  `is_completed` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `completed_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `assigner_id` (`assigner_id`),
  KEY `assignee_id` (`assignee_id`),
  CONSTRAINT `todos_ibfk_1` FOREIGN KEY (`assigner_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `todos_ibfk_2` FOREIGN KEY (`assignee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data for `users`
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (1, 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', '2026-03-08 14:24:50', NULL, NULL, NULL, NULL);
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (2, 'doctor1', '0000000000000000000000000000000000000000000000000000000000000000', 'doctor', '2026-03-08 14:24:50', '王鹏静', '神经肿瘤科', '住院医师', '13920007919');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (3, 'doctor2', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'doctor', '2026-03-11 23:21:39', '李丽倩', '脑膜瘤专病门诊', '主治医师', '13820015838');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (5, 'doctor3', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-18 11:56:05', '张莉', '胶质瘤诊疗中心', '副主任医师', '13720023757');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (6, 'doctor4', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-19 11:56:05', '刘洁丽', '垂体瘤诊疗组', '主任医师', '13620031676');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (7, 'doctor5', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-20 11:56:05', '陈涛晶', '听神经瘤专科', '住院医师', '13520039595');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (8, 'doctor6', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-21 11:56:05', '杨波', '肿瘤放疗科', '主治医师', '15020047514');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (9, 'doctor7', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-21 11:56:05', '赵娟敏', '肿瘤内科', '副主任医师', '15120055433');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (10, 'doctor8', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-22 11:56:05', '黄倩琳', '神经肿瘤科', '主任医师', '15220063352');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (11, 'doctor9', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-23 11:56:05', '周洋', '脑膜瘤专病门诊', '住院医师', '15720071271');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (12, 'doctor10', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-24 11:56:05', '吴峰艳', '胶质瘤诊疗中心', '主治医师', '15820079190');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (13, 'doctor11', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-25 11:56:05', '徐静颖', '垂体瘤诊疗组', '副主任医师', '15920087109');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (14, 'doctor12', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-25 11:56:05', '孙雪', '听神经瘤专科', '主任医师', '18620095028');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (15, 'doctor13', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-26 11:56:05', '胡颖娟', '肿瘤放疗科', '住院医师', '18720102947');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (16, 'doctor14', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-27 11:56:05', '朱杰洁', '肿瘤内科', '主治医师', '18820110866');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (17, 'doctor15', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-28 11:56:05', '高鑫', '神经肿瘤科', '副主任医师', '13920118785');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (18, 'doctor16', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-29 11:56:05', '林艳萍', '脑膜瘤专病门诊', '主任医师', '13820126704');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (19, 'doctor17', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-29 11:56:05', '王娜伟', '胶质瘤诊疗中心', '住院医师', '13720134623');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (20, 'doctor18', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-30 11:56:05', '李磊', '垂体瘤诊疗组', '主治医师', '13620142542');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (21, 'doctor19', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2025-12-31 11:56:05', '张超婷', '听神经瘤专科', '副主任医师', '13520150461');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (22, 'doctor20', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-01 11:56:05', '刘宁磊', '肿瘤放疗科', '主任医师', '15020158380');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (23, 'doctor21', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-02 11:56:05', '陈婷', '肿瘤内科', '住院医师', '15120166299');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (24, 'doctor22', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-02 11:56:05', '杨琳雪', '神经肿瘤科', '主治医师', '15220174218');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (25, 'doctor23', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-03 11:56:05', '赵军洋', '脑膜瘤专病门诊', '副主任医师', '15720182137');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (26, 'doctor24', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-04 11:56:05', '黄强', '胶质瘤诊疗中心', '主任医师', '15820190056');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (27, 'doctor25', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-05 11:56:05', '周敏莉', '垂体瘤诊疗组', '住院医师', '15920197975');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (28, 'doctor26', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-06 11:56:05', '吴芳勇', '听神经瘤专科', '主治医师', '18620205894');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (29, 'doctor27', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-06 11:56:05', '徐伟', '肿瘤放疗科', '副主任医师', '18720213813');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (30, 'doctor28', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-07 11:56:05', '孙明芳', '肿瘤内科', '主任医师', '18820221732');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (31, 'doctor29', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-08 11:56:05', '胡斌军', '神经肿瘤科', '住院医师', '13920229651');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (32, 'doctor30', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-09 11:56:05', '朱萍', '脑膜瘤专病门诊', '主治医师', '13820237570');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (33, 'doctor31', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-10 11:56:05', '高晶娜', '胶质瘤诊疗中心', '副主任医师', '13720245489');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (34, 'doctor32', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-10 11:56:05', '林勇杰', '垂体瘤诊疗组', '主任医师', '13620253408');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (35, 'doctor33', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-11 11:56:05', '王鹏', '听神经瘤专科', '住院医师', '13520261327');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (36, 'doctor34', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-12 11:56:05', '李丽倩', '肿瘤放疗科', '主治医师', '15020269246');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (37, 'doctor35', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-13 11:56:05', '张莉涛', '肿瘤内科', '副主任医师', '15120277165');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (38, 'doctor36', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-14 11:56:05', '刘洁', '神经肿瘤科', '主任医师', '15220285084');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (39, 'doctor37', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-14 11:56:05', '陈涛晶', '脑膜瘤专病门诊', '住院医师', '15720293003');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (40, 'doctor38', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-15 11:56:05', '杨波明', '胶质瘤诊疗中心', '主治医师', '15820300922');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (41, 'doctor39', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-16 11:56:05', '赵娟', '垂体瘤诊疗组', '副主任医师', '15920308841');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (42, 'doctor40', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-17 11:56:05', '黄倩琳', '听神经瘤专科', '主任医师', '18620316760');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (43, 'doctor41', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-18 11:56:05', '周洋超', '肿瘤放疗科', '住院医师', '18720324679');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (44, 'doctor42', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-18 11:56:05', '吴峰', '肿瘤内科', '主治医师', '18820332598');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (45, 'doctor43', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-19 11:56:05', '徐静颖', '神经肿瘤科', '副主任医师', '13920340517');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (46, 'doctor44', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-20 11:56:05', '孙雪峰', '脑膜瘤专病门诊', '主任医师', '13820348436');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (47, 'doctor45', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-21 11:56:05', '胡颖', '胶质瘤诊疗中心', '住院医师', '13720356355');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (48, 'doctor46', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-22 11:56:05', '朱杰洁', '垂体瘤诊疗组', '主治医师', '13620364274');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (49, 'doctor47', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-22 11:56:05', '高鑫鹏', '听神经瘤专科', '副主任医师', '13520372193');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (50, 'doctor48', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-23 11:56:05', '林艳', '肿瘤放疗科', '主任医师', '15020380112');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (51, 'doctor49', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-24 11:56:05', '王娜伟', '肿瘤内科', '住院医师', '15120388031');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (52, 'doctor50', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-25 11:56:05', '李磊强', '神经肿瘤科', '主治医师', '15220395950');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (53, 'doctor51', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-26 11:56:05', '张超', '脑膜瘤专病门诊', '副主任医师', '15720403869');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (54, 'doctor52', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-26 11:56:05', '刘宁磊', '胶质瘤诊疗中心', '主任医师', '15820411788');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (55, 'doctor53', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-27 11:56:05', '陈婷鑫', '垂体瘤诊疗组', '住院医师', '15920419707');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (56, 'doctor54', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-28 11:56:05', '杨琳', '听神经瘤专科', '主治医师', '18620427626');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (57, 'doctor55', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-29 11:56:05', '赵军洋', '肿瘤放疗科', '副主任医师', '18720435545');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (58, 'doctor56', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-30 11:56:05', '黄强波', '肿瘤内科', '主任医师', '18820443464');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (59, 'doctor57', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-30 11:56:05', '周敏', '神经肿瘤科', '住院医师', '13920451383');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (60, 'doctor58', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-01-31 11:56:05', '吴芳勇', '脑膜瘤专病门诊', '主治医师', '13820459302');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (61, 'doctor59', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-01 11:56:05', '徐伟斌', '胶质瘤诊疗中心', '副主任医师', '13720467221');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (62, 'doctor60', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-02 11:56:05', '孙明', '垂体瘤诊疗组', '主任医师', '13620475140');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (63, 'doctor61', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-03 11:56:05', '胡斌军', '听神经瘤专科', '住院医师', '13520483059');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (64, 'doctor62', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-03 11:56:05', '朱萍宁', '肿瘤放疗科', '主治医师', '15020490978');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (65, 'doctor63', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-04 11:56:05', '高晶', '肿瘤内科', '副主任医师', '15120498897');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (66, 'doctor64', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-05 11:56:05', '林勇杰', '神经肿瘤科', '主任医师', '15220506816');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (67, 'doctor65', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-06 11:56:05', '王鹏静', '脑膜瘤专病门诊', '住院医师', '15720514735');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (68, 'doctor66', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-07 11:56:05', '李丽', '胶质瘤诊疗中心', '主治医师', '15820522654');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (69, 'doctor67', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-07 11:56:05', '张莉涛', '垂体瘤诊疗组', '副主任医师', '15920530573');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (70, 'doctor68', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-08 11:56:05', '刘洁丽', '听神经瘤专科', '主任医师', '18620538492');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (71, 'doctor69', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-09 11:56:05', '陈涛', '肿瘤放疗科', '住院医师', '18720546411');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (72, 'doctor70', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-10 11:56:05', '杨波明', '肿瘤内科', '主治医师', '18820554330');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (73, 'doctor71', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-11 11:56:05', '赵娟敏', '神经肿瘤科', '副主任医师', '13920562249');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (74, 'doctor72', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-11 11:56:05', '黄倩', '脑膜瘤专病门诊', '主任医师', '13820570168');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (75, 'doctor73', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-12 11:56:05', '周洋超', '胶质瘤诊疗中心', '住院医师', '13720578087');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (76, 'doctor74', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-13 11:56:05', '吴峰艳', '垂体瘤诊疗组', '主治医师', '13620586006');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (77, 'doctor75', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-14 11:56:05', '徐静', '听神经瘤专科', '副主任医师', '13520593925');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (78, 'doctor76', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-15 11:56:05', '孙雪峰', '肿瘤放疗科', '主任医师', '15020601844');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (79, 'doctor77', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-15 11:56:05', '胡颖娟', '肿瘤内科', '住院医师', '15120609763');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (80, 'doctor78', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-16 11:56:05', '朱杰', '神经肿瘤科', '主治医师', '15220617682');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (81, 'doctor79', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-17 11:56:05', '高鑫鹏', '脑膜瘤专病门诊', '副主任医师', '15720625601');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (82, 'doctor80', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-18 11:56:05', '林艳萍', '胶质瘤诊疗中心', '主任医师', '15820633520');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (83, 'doctor81', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-19 11:56:05', '王娜', '垂体瘤诊疗组', '住院医师', '15920641439');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (84, 'doctor82', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-19 11:56:05', '李磊强', '听神经瘤专科', '主治医师', '18620649358');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (85, 'doctor83', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-20 11:56:05', '张超婷', '肿瘤放疗科', '副主任医师', '18720657277');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (86, 'doctor84', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-21 11:56:05', '刘宁', '肿瘤内科', '主任医师', '18820665196');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (87, 'doctor85', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-22 11:56:05', '陈婷鑫', '神经肿瘤科', '住院医师', '13920673115');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (88, 'doctor86', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-23 11:56:05', '杨琳雪', '脑膜瘤专病门诊', '主治医师', '13820681034');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (89, 'doctor87', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-23 11:56:05', '赵军', '胶质瘤诊疗中心', '副主任医师', '13720688953');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (90, 'doctor88', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-24 11:56:05', '黄强波', '垂体瘤诊疗组', '主任医师', '13620696872');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (91, 'doctor89', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-25 11:56:05', '周敏莉', '听神经瘤专科', '住院医师', '13520704791');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (92, 'doctor90', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-26 11:56:05', '吴芳', '肿瘤放疗科', '主治医师', '15020712710');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (93, 'doctor91', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-27 11:56:05', '徐伟斌', '肿瘤内科', '副主任医师', '15120720629');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (94, 'doctor92', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-27 11:56:05', '孙明芳', '神经肿瘤科', '主任医师', '15220728548');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (95, 'doctor93', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-02-28 11:56:05', '胡斌', '脑膜瘤专病门诊', '住院医师', '15720736467');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (96, 'doctor94', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-01 11:56:05', '朱萍宁', '胶质瘤诊疗中心', '主治医师', '15820744386');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (97, 'doctor95', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-02 11:56:05', '高晶娜', '垂体瘤诊疗组', '副主任医师', '15920752305');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (98, 'doctor96', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-03 11:56:05', '林勇', '听神经瘤专科', '主任医师', '18620760224');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (99, 'doctor97', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-03 11:56:05', '王鹏静', '肿瘤放疗科', '住院医师', '18720768143');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (100, 'doctor98', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-04 11:56:05', '李丽倩', '肿瘤内科', '主治医师', '18820776062');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (101, 'doctor99', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-05 11:56:05', '张莉', '神经肿瘤科', '副主任医师', '13920783981');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (102, 'doctor100', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-06 11:56:05', '刘洁丽', '脑膜瘤专病门诊', '主任医师', '13820791900');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (103, 'doctor101', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-07 11:56:05', '陈涛晶', '胶质瘤诊疗中心', '住院医师', '13720799819');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (104, 'doctor102', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-07 11:56:05', '杨波', '垂体瘤诊疗组', '主治医师', '13620807738');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (105, 'doctor103', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-08 11:56:05', '赵娟敏', '听神经瘤专科', '副主任医师', '13520815657');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (106, 'doctor104', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-09 11:56:05', '黄倩琳', '肿瘤放疗科', '主任医师', '15020823576');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (107, 'doctor105', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-10 11:56:05', '周洋', '肿瘤内科', '住院医师', '15120831495');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (108, 'doctor106', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-11 11:56:05', '吴峰艳', '神经肿瘤科', '主治医师', '15220839414');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (109, 'doctor107', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-11 11:56:05', '徐静颖', '脑膜瘤专病门诊', '副主任医师', '15720847333');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (110, 'doctor108', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-12 11:56:05', '孙雪', '胶质瘤诊疗中心', '主任医师', '15820855252');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (111, 'doctor109', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-13 11:56:05', '胡颖娟', '垂体瘤诊疗组', '住院医师', '15920863171');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (112, 'doctor110', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-14 11:56:05', '朱杰洁', '听神经瘤专科', '主治医师', '18620871090');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (113, 'doctor111', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-15 11:56:05', '高鑫', '肿瘤放疗科', '副主任医师', '18720879009');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (114, 'doctor112', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-16 11:56:05', '林艳萍', '肿瘤内科', '主任医师', '18820886928');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (116, 'doctor113', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-16 21:36:09', '王娜伟', '神经肿瘤科', '住院医师', '13920894847');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (124, 'doctor114', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-18 11:57:33', '李磊', '脑膜瘤专病门诊', '主治医师', '13820902766');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (126, 'doctor115', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-18 23:02:04', '许文杰', 'buh', '啊、', '123456');
INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`, `real_name`, `department`, `title`, `phone`) VALUES (129, 'doctor116', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', 'doctor', '2026-03-18 23:31:23', '1', '1', '1', '1');

-- Data for `patients`
INSERT INTO `patients` (`id`, `patient_id`, `name`, `gender`, `age`, `birthday`, `phone`, `address`, `created_at`) VALUES (1, 'PT001', '张三', '男', 56, '1967-05-20', '13800138001', '北京市朝阳区', '2026-03-08 14:24:50');

-- Data for `diagnoses`
INSERT INTO `diagnoses` (`id`, `patient_id`, `doctor_id`, `diagnosis_date`, `follow_up_date`, `diagnosis_type`, `tumor_type`, `tumor_stage`, `diagnosis_content`, `treatment_plan`, `examination_results`, `notes`, `created_at`) VALUES (1, 1, 2, '2023-10-15 14:30:00', NULL, 'CT扫描', '疑似肺癌', 'II期', '左侧肺部阴影，大小约3.5cm×4.0cm，边界不清，建议进一步病理检查。', '建议手术切除+化疗', 'CT扫描显示左侧肺部有占位性病变，肿瘤标志物CEA升高。', '避免吸烟，定期复查。', '2026-03-08 14:24:50');

-- Data for `notifications`
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (1, 2, 'todo', '新的待办任务', '您有一个新的待办任务：好', 1, 0, '2026-03-10 21:42:22', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (2, 2, 'todo', '新的待办任务', '您有一个新的待办任务：不好', 2, 0, '2026-03-11 23:18:31', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (3, 2, 'todo', '新的待办任务', '您有一个新的待办任务：获取样本', 3, 0, '2026-03-11 23:20:53', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (4, 3, 'todo', '新的待办任务', '您有一个新的待办任务：啦啦啦', 4, 0, '2026-03-11 23:24:08', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (5, 2, 'todo', '新的待办任务', '您有一个新的待办任务：哈哈哈', 5, 0, '2026-03-11 23:24:30', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (6, 3, 'todo', '新的待办任务', '您有一个新的待办任务：no', 6, 0, '2026-03-11 23:25:03', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (7, 2, 'todo', '新的待办任务', '您有一个新的待办任务：好吧', 7, 0, '2026-03-11 23:25:28', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (8, 2, 'todo', '新的待办任务', '您有一个新的待办任务：治疗患者', 8, 0, '2026-03-11 23:27:28', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (9, 3, 'todo', '新的待办任务', '您有一个新的待办任务：问诊病人', 9, 0, '2026-03-11 23:34:40', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (10, 2, 'todo', '新的待办任务', '您有一个新的待办任务：调试模型', 10, 0, '2026-03-11 23:59:47', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (11, 14, 'todo', '新的待办任务', '您有一个新的待办任务：用药核对', 95, 0, '2026-03-17 11:09:45', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (12, 108, 'todo', '新的待办任务', '您有一个新的待办任务：影像归档', 96, 0, '2026-03-17 11:20:02', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (13, 13, 'todo', '新的待办任务', '您有一个新的待办任务：影像归档', 97, 0, '2026-03-18 23:00:12', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (14, 13, 'todo', '新的待办任务', '您有一个新的待办任务：印象归档', 98, 0, '2026-03-18 23:17:37', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (15, 111, 'todo', '新的待办任务', '您有一个新的待办任务：印象归档', 99, 0, '2026-03-18 23:36:12', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (16, 19, 'todo', '新的待办任务', '您有一个新的待办任务：上传影像', 100, 0, '2026-04-13 20:21:40', NULL);
INSERT INTO `notifications` (`id`, `user_id`, `type`, `title`, `content`, `related_id`, `is_read`, `created_at`, `read_at`) VALUES (17, 109, 'todo', '新的待办任务', '您有一个新的待办任务：上传影像', 101, 0, '2026-04-13 20:39:05', NULL);

-- Data for `todos`
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (2, '不好', '不好', 1, 2, '2026-05-05', 0, '2026-03-11 23:18:31', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (3, '获取样本', '获取更多样本', 1, 2, '2026-05-06', 0, '2026-03-11 23:20:53', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (5, '哈哈哈', '哈哈哈哈哈', 1, 2, '2026-05-08', 0, '2026-03-11 23:24:30', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (6, 'no', '为何要？', 1, 3, '2026-05-09', 0, '2026-03-11 23:25:03', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (7, '好吧', '没招了', 1, 2, '2026-05-09', 0, '2026-03-11 23:25:28', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (9, '问诊病人', '仔细录入病人信息', 1, 3, '2026-05-09', 0, '2026-03-11 23:34:40', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (10, '调试模型', '提供图片去训练模型', 1, 2, '2026-05-10', 0, '2026-03-11 23:59:47', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (53, '病历建档', '补全病历并归档', 1, 98, '2026-06-03', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (54, '病史核查', '核查病史关键项', 1, 43, '2026-06-06', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (55, '诊断录入', '录入诊断并提交', 1, 74, '2026-06-09', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (56, '影像归档', '整理影像并归档', 1, 38, '2026-06-12', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (57, '影像质检', '抽检影像清晰度', 1, 71, '2026-06-15', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (59, '病例随访', '更新随访记录', 1, 39, '2026-06-21', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (60, '复诊提醒', '发送复诊提醒', 1, 13, '2026-06-24', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (61, '手术评估', '完善术前评估', 1, 31, '2026-06-27', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (62, '用药核对', '核对用药与医嘱', 1, 46, '2026-06-30', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (63, '病灶标注', '完成病灶标注', 1, 28, '2026-07-03', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (64, '远程推理', '执行推理并回传', 1, 79, '2026-07-06', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (65, '模型调参', '调整参数并记录', 1, 102, '2026-07-09', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (66, '结果复审', '复审结果并修正', 1, 81, '2026-07-12', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (67, '数据脱敏', '脱敏后再导出', 1, 106, '2026-07-15', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (68, '数据备份', '执行数据备份', 1, 96, '2026-07-18', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (69, '权限巡检', '巡检权限配置', 1, 11, '2026-07-21', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (71, '通知下发', '下发通知并确认', 1, 114, '2026-07-27', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (72, '工单分派', '按负载分派工单', 1, 51, '2026-07-30', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (73, '工单催办', '催办临期任务', 1, 83, '2026-08-02', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (74, '超期清理', '清理超期工单', 1, 23, '2026-08-05', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (75, '复核排班', '安排复核值班', 1, 100, '2026-08-08', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (76, '病理对照', '完成病理对照', 1, 69, '2026-08-11', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (77, '出院回访', '完成出院回访', 1, 26, '2026-08-14', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (78, '复查安排', '安排复查时间', 1, 63, '2026-08-17', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (79, '指标上报', '汇总指标上报', 1, 88, '2026-08-20', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (80, '统计复盘', '复盘月度统计', 1, 41, '2026-08-23', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (81, '风险筛查', '筛查高风险例', 1, 42, '2026-08-26', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (82, '并发监测', '监测并发指标', 1, 49, '2026-08-29', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (83, '医嘱核对', '核对医嘱执行', 1, 22, '2026-09-01', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (84, '会诊安排', '安排会诊时段', 1, 60, '2026-09-04', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (86, '异常上报', '上报异常并跟踪', 1, 21, '2026-09-10', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (87, '样本追踪', '追踪样本流转', 1, 86, '2026-09-13', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (88, '影像重传', '重传失败影像', 1, 58, '2026-09-16', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (89, '文书修订', '修订病历文书', 1, 108, '2026-09-19', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (91, '数据对账', '核对多表数据', 1, 84, '2026-09-25', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (92, '接口巡检', '巡检接口健康', 1, 5, '2026-09-28', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (93, '质控抽检', '执行质控抽检', 1, 29, '2026-10-01', 0, '2026-03-17 10:40:41', NULL);
INSERT INTO `todos` (`id`, `title`, `content`, `assigner_id`, `assignee_id`, `due_date`, `is_completed`, `created_at`, `completed_at`) VALUES (94, '预警复盘', '复盘预警处置', 1, 3, '2026-10-04', 0, '2026-03-17 10:40:41', NULL);

ALTER TABLE `users` AUTO_INCREMENT = 130;
ALTER TABLE `patients` AUTO_INCREMENT = 2;
ALTER TABLE `diagnoses` AUTO_INCREMENT = 2;
ALTER TABLE `images` AUTO_INCREMENT = 1;
ALTER TABLE `notifications` AUTO_INCREMENT = 18;
ALTER TABLE `todos` AUTO_INCREMENT = 95;

SET FOREIGN_KEY_CHECKS=1;
