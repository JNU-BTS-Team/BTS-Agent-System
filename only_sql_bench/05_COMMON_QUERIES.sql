-- ============================================================================
-- BTS-Agent 脑肿瘤诊断系统 - 常用查询语句
-- ============================================================================
-- 说明：日常查询、统计分析、数据审计等常用 SELECT 语句
-- 可在 Workbench 中单独选中一条执行

USE SECD;

-- ============================================================================
-- 【查询1】系统总体统计概览
-- ============================================================================
SELECT
    (SELECT COUNT(*) FROM users WHERE role = 'admin')  AS 管理员数,
    (SELECT COUNT(*) FROM users WHERE role = 'doctor') AS 医生数,
    (SELECT COUNT(*) FROM users WHERE role = 'viewer') AS 只读用户数,
    (SELECT COUNT(*) FROM patients)                    AS 患者总数,
    (SELECT COUNT(*) FROM diagnoses)                   AS 诊断记录数,
    (SELECT COUNT(*) FROM todos)                       AS 待办任务数,
    (SELECT COUNT(*) FROM todos WHERE is_completed=1)  AS 已完成任务数,
    (SELECT COUNT(*) FROM diagnoses WHERE follow_up_date < CURDATE()) AS 超期随访数;

-- ============================================================================
-- 【查询2】所有用户列表
-- ============================================================================
SELECT id, username, real_name, role, department, title, phone, created_at
FROM users
ORDER BY role DESC, id ASC;

-- ============================================================================
-- 【查询3】所有患者列表
-- ============================================================================
SELECT id, patient_id, name, gender, age, birthday, phone, address, created_at
FROM patients
ORDER BY created_at DESC;

-- ============================================================================
-- 【查询4】所有诊断记录（含患者和医生信息）
-- ============================================================================
SELECT
    d.id AS 诊断ID,
    p.name AS 患者姓名,
    p.patient_id AS 患者编号,
    u.real_name AS 主治医生,
    d.diagnosis_date AS 诊断日期,
    d.diagnosis_type AS 诊断类型,
    d.tumor_type AS 肿瘤类型,
    d.tumor_stage AS 分期,
    d.follow_up_date AS 随访日期
FROM diagnoses d
JOIN patients p ON d.patient_id = p.id
JOIN users u ON d.doctor_id = u.id
ORDER BY d.diagnosis_date DESC;

-- ============================================================================
-- 【查询5】医生工作量排名
-- ============================================================================
SELECT
    u.real_name AS 医生姓名,
    u.department AS 科室,
    u.title AS 职称,
    COUNT(d.id) AS 诊断总数,
    MAX(d.diagnosis_date) AS 最后诊断时间
FROM users u
LEFT JOIN diagnoses d ON u.id = d.doctor_id
WHERE u.role = 'doctor'
GROUP BY u.id
ORDER BY COUNT(d.id) DESC;

-- ============================================================================
-- 【查询6】待随访患者列表（按时间排序）
-- ============================================================================
SELECT
    p.name AS 患者姓名,
    p.phone AS 联系电话,
    d.follow_up_date AS 随访日期,
    DATEDIFF(d.follow_up_date, CURDATE()) AS 距今天数,
    CASE
        WHEN d.follow_up_date < CURDATE() THEN '⚠ 已超期'
        WHEN DATEDIFF(d.follow_up_date, CURDATE()) <= 7 THEN '⚡ 即将到期'
        ELSE '✓ 正常'
    END AS 状态,
    u.real_name AS 责任医生
FROM diagnoses d
JOIN patients p ON d.patient_id = p.id
JOIN users u ON d.doctor_id = u.id
WHERE d.follow_up_date IS NOT NULL
ORDER BY d.follow_up_date ASC;

-- ============================================================================
-- 【查询7】各科室医生分布
-- ============================================================================
SELECT
    department AS 科室,
    COUNT(*) AS 医生人数,
    GROUP_CONCAT(real_name ORDER BY id SEPARATOR '、') AS 医生名单
FROM users
WHERE role = 'doctor' AND department IS NOT NULL
GROUP BY department
ORDER BY COUNT(*) DESC;

-- ============================================================================
-- 【查询8】待办任务完成情况
-- ============================================================================
SELECT
    t.title AS 任务标题,
    t.content AS 任务内容,
    a.real_name AS 发布人,
    b.real_name AS 接收人,
    t.due_date AS 截止日期,
    CASE t.is_completed WHEN 1 THEN '已完成' ELSE '未完成' END AS 状态,
    t.completed_at AS 完成时间
FROM todos t
JOIN users a ON t.assigner_id = a.id
JOIN users b ON t.assignee_id = b.id
ORDER BY t.due_date ASC;

-- ============================================================================
-- 【查询9】按肿瘤类型统计患者分布
-- ============================================================================
SELECT
    tumor_type AS 肿瘤类型,
    COUNT(*) AS 病例数,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM diagnoses WHERE tumor_type IS NOT NULL), 1) AS 占比百分比
FROM diagnoses
WHERE tumor_type IS NOT NULL
GROUP BY tumor_type
ORDER BY COUNT(*) DESC;

-- ============================================================================
-- 【查询10】系统通知列表
-- ============================================================================
SELECT
    n.id AS 通知ID,
    u.username AS 接收用户,
    n.type AS 通知类型,
    n.title AS 标题,
    n.content AS 内容,
    CASE n.is_read WHEN 1 THEN '已读' ELSE '未读' END AS 状态,
    n.created_at AS 创建时间
FROM notifications n
JOIN users u ON n.user_id = u.id
ORDER BY n.created_at DESC;
