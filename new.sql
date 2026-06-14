-- ============================================================================
-- BTS-Agent 脑肿瘤诊断系统 - 现场演示备选 SQL 脚本
-- ============================================================================
-- 说明：这个文件包含多种现场演示场景的 SQL 操作，可根据老师的要求现场选择执行
-- 使用时请勿一次性执行全部，根据演示需求逐个执行
-- 注意：所有 doctor 的默认密码都是 123456（SHA256 哈希值）
-- 备注：viewer 用户已在 current_data.sql 中初始化，账号密码为 viewer / viewer123

-- ============================================================================
-- 【场景1：医生管理 - 批量添加医生】
-- ============================================================================
-- 应用场景：医院新增了一个肿瘤科团队
-- 演示价值：展示系统如何管理多个科室的医生

INSERT INTO users (username, password, real_name, department, title, phone, role, created_at)
VALUES
    ('doctor201', '8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266', '李医生', '脑肿瘤科', '主任医师', '13912345678', 'doctor', NOW()),
    ('doctor202', '8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266', '王医生', '脑肿瘤科', '副主任医师', '13912345679', 'doctor', NOW()),
    ('doctor203', '8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266', '张医生', '神经外科', '主治医师', '13912345680', 'doctor', NOW());

-- ============================================================================
-- 【场景2：医生管理 - 修改医生信息（职称晋升）】
-- ============================================================================
-- 应用场景：医生晋升职称或调换科室
-- 演示价值：展示权限管理员如何更新医生资料

UPDATE users
SET department = '胶质瘤诊疗中心', title = '副主任医师', phone = '13800138001'
WHERE username = 'doctor1' AND role = 'doctor';

-- ============================================================================
-- 【场景3：医生管理 - 升级医生为管理员】
-- ============================================================================
-- 应用场景：医疗主任升职为系统管理员
-- 演示价值：展示权限系统的灵活性和角色转换

UPDATE users
SET role = 'admin', title = '系统管理员'
WHERE username = 'doctor2' AND role = 'doctor';

-- 恢复：降级管理员回医生（如需演示撤销操作）
-- UPDATE users SET role = 'doctor', title = '主治医师' WHERE username = 'doctor2';

-- ============================================================================
-- 【场景4：医生管理 - 重置密码】
-- ============================================================================
-- 应用场景：医生忘记密码，管理员重置
-- 演示价值：展示系统管理员的密码重置权限
-- 密码 123456 的 SHA256 哈希值是 8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266

UPDATE users
SET password = '8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266'
WHERE username = 'doctor3';

-- ============================================================================
-- 【场景5：患者管理 - 批量添加患者】
-- ============================================================================
-- 应用场景：医院导入病历库的患者基础信息
-- 演示价值：展示患者数据的批量导入能力

INSERT INTO patients (patient_id, name, gender, age, birthday, phone, address, created_at)
VALUES
    ('PAT20250101', '张三', '男', 45, '1979-03-15', '13800000001', '北京市朝阳区', NOW()),
    ('PAT20250102', '李四', '女', 52, '1972-07-22', '13800000002', '北京市海淀区', NOW()),
    ('PAT20250103', '王五', '男', 38, '1986-11-08', '13800000003', '北京市东城区', NOW()),
    ('PAT20250104', '赵六', '女', 61, '1963-05-30', '13800000004', '北京市西城区', NOW());

-- ============================================================================
-- 【场景6：患者管理 - 修改患者信息】
-- ============================================================================
-- 应用场景：患者更新了联系方式或地址
-- 演示价值：展示系统如何维护患者信息的完整性

UPDATE patients
SET phone = '13900000001', address = '北京市朝阳区新地址'
WHERE patient_id = 'PAT20250101';

-- ============================================================================
-- 【场景7：数据统计 - 医生工作量统计】
-- ============================================================================
-- 应用场景：评估各医生的诊疗工作量
-- 演示价值：展示系统数据分析和业绩考核功能

SELECT
    u.username as 医生账号,
    u.real_name as 医生姓名,
    u.department as 科室,
    COUNT(d.id) as 诊断记录数,
    MAX(d.diagnosis_date) as 最后诊断时间
FROM users u
LEFT JOIN diagnoses d ON u.id = d.doctor_id
WHERE u.role = 'doctor'
GROUP BY u.id, u.username, u.real_name, u.department
ORDER BY COUNT(d.id) DESC;

-- ============================================================================
-- 【场景8：数据统计 - 患者就诊统计】
-- ============================================================================
-- 应用场景：了解患者群体的诊疗分布
-- 演示价值：展示患者管理的数据可视化基础

SELECT
    p.name as 患者姓名,
    p.gender as 性别,
    p.age as 年龄,
    COUNT(d.id) as 诊断次数,
    MAX(d.diagnosis_date) as 最后就诊时间
FROM patients p
LEFT JOIN diagnoses d ON p.id = d.patient_id
GROUP BY p.id
ORDER BY p.age DESC;

-- ============================================================================
-- 【场景9：数据统计 - 科室医生分布】
-- ============================================================================
-- 应用场景：了解各科室的医生配置
-- 演示价值：展示系统的组织管理和资源配置功能

SELECT
    department as 科室,
    COUNT(*) as 医生数,
    GROUP_CONCAT(real_name SEPARATOR ', ') as 医生列表
FROM users
WHERE role = 'doctor' AND department IS NOT NULL
GROUP BY department
ORDER BY COUNT(*) DESC;

-- ============================================================================
-- 【场景10：查询待随访患者】
-- ============================================================================
-- 应用场景：医生需要了解哪些患者需要复诊
-- 演示价值：展示临床管理的重要功能

SELECT
    d.id as 诊断ID,
    p.name as 患者姓名,
    p.phone as 患者电话,
    d.diagnosis_date as 诊断日期,
    d.follow_up_date as 随访日期,
    DATEDIFF(d.follow_up_date, CURDATE()) as 距今天数
FROM diagnoses d
JOIN patients p ON d.patient_id = p.id
WHERE d.follow_up_date IS NOT NULL
  AND d.follow_up_date >= CURDATE()
ORDER BY d.follow_up_date ASC
LIMIT 10;

-- ============================================================================
-- 【场景11：查询复诊超期患者（预警）】
-- ============================================================================
-- 应用场景：提醒医生已超期的患者需要复诊
-- 演示价值：展示预警系统的重要性

SELECT
    d.id as 诊断ID,
    p.name as 患者姓名,
    d.follow_up_date as 应随访日期,
    DATEDIFF(CURDATE(), d.follow_up_date) as 超期天数,
    u.real_name as 责任医生
FROM diagnoses d
JOIN patients p ON d.patient_id = p.id
JOIN users u ON d.doctor_id = u.id
WHERE d.follow_up_date IS NOT NULL
  AND d.follow_up_date < CURDATE()
ORDER BY d.follow_up_date ASC;

-- ============================================================================
-- 【场景12：创建临时测试医生（权限演示用）】
-- ============================================================================
-- 应用场景：演示权限控制时的临时操作
-- 演示价值：演示医生的查看权限 vs 管理员的修改权限对比

INSERT INTO users (username, password, real_name, department, title, phone, role, created_at)
VALUES ('doctor_temp', '8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266',
        '临时医生', '演示科室', '演示职称', '13800000099', 'doctor', NOW());

-- 查看新创建的医生
SELECT * FROM users WHERE username = 'doctor_temp';

-- 清理临时医生（完成演示后执行此条删除）
-- DELETE FROM users WHERE username = 'doctor_temp';

-- ============================================================================
-- 【审计查询 - 系统用户列表】
-- ============================================================================
-- 应用场景：系统审计，检查所有账户
-- 演示价值：展示系统的管理员审计功能

SELECT
    id as 用户ID,
    username as 用户名,
    real_name as 真实姓名,
    role as 角色,
    department as 部门,
    title as 职称,
    phone as 电话,
    created_at as 创建时间
FROM users
ORDER BY role DESC, id ASC;

-- ============================================================================
-- 【系统状态概览】
-- ============================================================================
-- 查看系统的总体统计

SELECT
    (SELECT COUNT(*) FROM users WHERE role = 'admin') as 管理员数,
    (SELECT COUNT(*) FROM users WHERE role = 'doctor') as 医生数,
    (SELECT COUNT(*) FROM users WHERE role = 'viewer') as 只读用户数,
    (SELECT COUNT(*) FROM patients) as 患者总数,
    (SELECT COUNT(*) FROM diagnoses) as 诊断记录数,
    (SELECT COUNT(*) FROM diagnoses WHERE follow_up_date IS NOT NULL AND follow_up_date > CURDATE()) as 待随访患者数,
    (SELECT COUNT(*) FROM diagnoses WHERE follow_up_date IS NOT NULL AND follow_up_date < CURDATE()) as 超期随访患者数;
