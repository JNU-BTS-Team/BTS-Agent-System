-- ============================================================================
-- BTS-Agent 脑肿瘤诊断系统 - 视图创建
-- ============================================================================
-- 说明：创建常用查询视图，方便在 Workbench 中直接查看
-- 执行顺序：第4步

USE SECD;

-- ============================================================================
-- 【视图1】医生工作量统计视图
-- ============================================================================
DROP VIEW IF EXISTS view_doctor_workload;
CREATE VIEW view_doctor_workload AS
SELECT
    u.id AS 医生ID,
    u.username AS 账号,
    u.real_name AS 姓名,
    u.department AS 科室,
    u.title AS 职称,
    u.phone AS 电话,
    COUNT(d.id) AS 诊断记录数,
    MAX(d.diagnosis_date) AS 最后诊断时间
FROM users u
LEFT JOIN diagnoses d ON u.id = d.doctor_id
WHERE u.role = 'doctor'
GROUP BY u.id, u.username, u.real_name, u.department, u.title, u.phone;

-- 使用：SELECT * FROM view_doctor_workload;

-- ============================================================================
-- 【视图2】患者诊断详情视图
-- ============================================================================
DROP VIEW IF EXISTS view_patient_diagnosis;
CREATE VIEW view_patient_diagnosis AS
SELECT
    p.patient_id AS 患者编号,
    p.name AS 患者姓名,
    p.gender AS 性别,
    p.age AS 年龄,
    p.phone AS 患者电话,
    d.diagnosis_date AS 诊断日期,
    d.follow_up_date AS 随访日期,
    d.diagnosis_type AS 诊断类型,
    d.tumor_type AS 肿瘤类型,
    d.tumor_stage AS 肿瘤分期,
    d.diagnosis_content AS 诊断内容,
    d.treatment_plan AS 治疗方案,
    u.real_name AS 主治医生,
    u.department AS 医生科室
FROM patients p
LEFT JOIN diagnoses d ON p.id = d.patient_id
LEFT JOIN users u ON d.doctor_id = u.id;

-- 使用：SELECT * FROM view_patient_diagnosis;

-- ============================================================================
-- 【视图3】待随访患者视图
-- ============================================================================
DROP VIEW IF EXISTS view_followup_patients;
CREATE VIEW view_followup_patients AS
SELECT
    p.name AS 患者姓名,
    p.phone AS 患者电话,
    d.diagnosis_date AS 诊断日期,
    d.follow_up_date AS 随访日期,
    DATEDIFF(d.follow_up_date, CURDATE()) AS 距今天数,
    CASE
        WHEN d.follow_up_date < CURDATE() THEN '已超期'
        WHEN DATEDIFF(d.follow_up_date, CURDATE()) <= 7 THEN '即将到期'
        ELSE '正常'
    END AS 状态,
    u.real_name AS 责任医生,
    u.phone AS 医生电话
FROM diagnoses d
JOIN patients p ON d.patient_id = p.id
JOIN users u ON d.doctor_id = u.id
WHERE d.follow_up_date IS NOT NULL
ORDER BY d.follow_up_date ASC;

-- 使用：SELECT * FROM view_followup_patients;

-- ============================================================================
-- 【视图4】系统用户权限视图
-- ============================================================================
DROP VIEW IF EXISTS view_user_permissions;
CREATE VIEW view_user_permissions AS
SELECT
    id AS 用户ID,
    username AS 账号,
    real_name AS 姓名,
    role AS 角色,
    CASE role
        WHEN 'admin'  THEN '增删改查全部权限'
        WHEN 'doctor' THEN '查看患者/诊断，无删除权限'
        WHEN 'viewer' THEN '只读，无任何修改权限'
    END AS 权限说明,
    department AS 部门,
    title AS 职称,
    created_at AS 注册时间
FROM users;

-- 使用：SELECT * FROM view_user_permissions;

-- ============================================================================
-- 【视图5】科室医生分布视图
-- ============================================================================
DROP VIEW IF EXISTS view_department_summary;
CREATE VIEW view_department_summary AS
SELECT
    department AS 科室,
    COUNT(*) AS 医生人数,
    GROUP_CONCAT(real_name ORDER BY id SEPARATOR '、') AS 医生名单,
    SUM(CASE WHEN title = '主任医师' THEN 1 ELSE 0 END) AS 主任医师数,
    SUM(CASE WHEN title = '副主任医师' THEN 1 ELSE 0 END) AS 副主任医师数,
    SUM(CASE WHEN title = '主治医师' THEN 1 ELSE 0 END) AS 主治医师数,
    SUM(CASE WHEN title = '住院医师' THEN 1 ELSE 0 END) AS 住院医师数
FROM users
WHERE role = 'doctor' AND department IS NOT NULL
GROUP BY department
ORDER BY COUNT(*) DESC;

-- 使用：SELECT * FROM view_department_summary;

-- ============================================================================
-- 完成：所有视图已创建，可直接 SELECT * FROM 视图名 查看
-- ============================================================================
SELECT '已创建视图列表：' AS 提示;
SELECT TABLE_NAME AS 视图名
FROM information_schema.VIEWS
WHERE TABLE_SCHEMA = 'SECD';
