-- ============================================================================
-- BTS-Agent 脑肿瘤诊断系统 - UPDATE / DELETE 演示
-- ============================================================================
-- 说明：演示数据修改和删除操作，每条语句可单独在 Workbench 中执行
-- 执行顺序：第6步（按需执行，注意 DELETE 操作不可撤销）

USE SECD;

-- ============================================================================
-- 【UPDATE - 患者信息修改】
-- ============================================================================

-- 更新患者联系方式
UPDATE patients
SET phone = '13900000099', address = '北京市朝阳区新地址'
WHERE patient_id = 'PAT20260001';

-- 更新患者年龄
UPDATE patients
SET age = 46
WHERE patient_id = 'PAT20260001';

-- 查询确认修改结果
SELECT * FROM patients WHERE patient_id = 'PAT20260001';

-- ============================================================================
-- 【UPDATE - 医生信息修改】
-- ============================================================================

-- 医生科室调换
UPDATE users
SET department = '神经肿瘤科'
WHERE username = 'doctor2' AND role = 'doctor';

-- 医生职称晋升
UPDATE users
SET title = '副主任医师'
WHERE username = 'doctor1' AND role = 'doctor';

-- 查询确认修改结果
SELECT id, username, real_name, department, title FROM users WHERE role = 'doctor';

-- ============================================================================
-- 【UPDATE - 待办任务状态修改】
-- ============================================================================

-- 标记任务已完成
UPDATE todos
SET is_completed = 1, completed_at = NOW()
WHERE title = '诊断报告整理';

-- 查询待办任务状态
SELECT title, is_completed, completed_at FROM todos;

-- ============================================================================
-- 【UPDATE - 通知标记已读】
-- ============================================================================

-- 标记所有通知为已读
UPDATE notifications
SET is_read = 1, read_at = NOW()
WHERE user_id = 1;

-- ============================================================================
-- 【DELETE - 删除操作（谨慎执行）】
-- ============================================================================

-- 删除指定患者（会级联删除其诊断记录和图片）
-- DELETE FROM patients WHERE patient_id = 'PAT20260004';

-- 删除指定诊断记录（仅管理员操作）
-- DELETE FROM diagnoses WHERE id = 1;

-- 删除指定医生账户（离职场景，会级联删除其相关记录）
-- DELETE FROM users WHERE username = 'doctor3' AND role = 'doctor';

-- 删除已完成的待办任务
-- DELETE FROM todos WHERE is_completed = 1;

-- 删除已读通知
-- DELETE FROM notifications WHERE is_read = 1;

-- ============================================================================
-- 完成：UPDATE/DELETE 演示语句
-- ============================================================================
