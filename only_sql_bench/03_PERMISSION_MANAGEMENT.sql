-- ============================================================================
-- BTS-Agent 脑肿瘤诊断系统 - 权限管理操作
-- ============================================================================
-- 说明：用户角色转换、密码重置、权限相关操作示例
-- 执行顺序：第3步（可选，按需执行）

USE SECD;

-- ============================================================================
-- 【医生管理 - 修改医生信息】
-- ============================================================================

-- 修改医生职称和科室（晋升场景）
UPDATE users
SET department = '胶质瘤诊疗中心', title = '副主任医师', phone = '13800138001'
WHERE username = 'doctor1' AND role = 'doctor';

-- 修改医生联系方式
UPDATE users
SET phone = '13900000001'
WHERE username = 'doctor2';

-- ============================================================================
-- 【权限转换 - 升级/降级用户角色】
-- ============================================================================

-- 升级医生为管理员（医疗主任升职场景）
UPDATE users
SET role = 'admin', title = '系统管理员'
WHERE username = 'doctor1' AND role = 'doctor';

-- 降级管理员回医生（如需撤销）
-- UPDATE users SET role = 'doctor', title = '主治医师' WHERE username = 'doctor1';

-- ============================================================================
-- 【密码管理 - 重置用户密码】
-- ============================================================================
-- 密码说明：
-- admin123 的 SHA256: 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
-- 123456 的 SHA256:   8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266
-- viewer123 的 SHA256: 65375049b9e4d7cad6c9ba286fdeb9394b28135a3e84136404cfccfdcc438894

-- 重置医生密码（医生忘记密码场景）
UPDATE users
SET password = '8d969eef6ecad3c29a3a873fba0f4a36037ffe3d33c9fc07d957aae63f32266'
WHERE username = 'doctor3';

-- 重置管理员密码
UPDATE users
SET password = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
WHERE username = 'admin';

-- 重置只读用户密码
UPDATE users
SET password = '65375049b9e4d7cad6c9ba286fdeb9394b28135a3e84136404cfccfdcc438894'
WHERE username = 'viewer';

-- ============================================================================
-- 【查询操作 - 权限相关查询】
-- ============================================================================

-- 查看所有用户及其角色
SELECT id, username, real_name, role, department, title, phone, created_at
FROM users
ORDER BY role DESC, id ASC;

-- 查看不同角色的用户分布
SELECT role, COUNT(*) as 用户数
FROM users
GROUP BY role;

-- 查看医生的工作信息
SELECT u.id, u.username, u.real_name, u.department, u.title,
       COUNT(d.id) as 诊断记录数,
       MAX(d.diagnosis_date) as 最后诊断时间
FROM users u
LEFT JOIN diagnoses d ON u.id = d.doctor_id
WHERE u.role = 'doctor'
GROUP BY u.id
ORDER BY COUNT(d.id) DESC;

-- ============================================================================
-- 完成：权限管理操作演示
-- ============================================================================
