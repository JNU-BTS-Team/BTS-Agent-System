-- ============================================================================
-- 4.2 视图保护（7分）- 脱敏视图保护方案
-- ============================================================================
-- 针对含敏感字段的表创建视图，隐藏和脱敏敏感信息
-- ============================================================================

USE SECD;

-- ============================================================================
-- 【视图1】用户信息脱敏视图 - view_user_masked
-- ============================================================================
-- 原始表：users 表（系统登录用户）
-- 敏感字段：password（密码哈希值）、real_name（真实姓名）、phone（联系电话）
-- 脱敏方式：
--   - password: 完全隐藏（不在视图中显示）
--   - real_name: 显示首字符+** (如：王**)
--   - phone: 显示前3位+****+后4位 (如：139****7919)

DROP VIEW IF EXISTS view_user_masked;
CREATE VIEW view_user_masked AS
SELECT
    id AS 用户ID,
    username AS 账号,
    -- 真实姓名脱敏：显示首字 + **
    CONCAT(
        SUBSTR(real_name, 1, 1),
        REPEAT('*', CHAR_LENGTH(real_name) - 1)
    ) AS 真实姓名,
    role AS 角色,
    CASE role
        WHEN 'admin'  THEN '系统管理员'
        WHEN 'doctor' THEN '医生'
        WHEN 'viewer' THEN '审计员'
    END AS 角色说明,
    department AS 所属科室,
    title AS 职位,
    -- 电话号码脱敏：显示前3位+****+后4位 (如：139****7919)
    CONCAT(
        SUBSTR(phone, 1, 3),
        '****',
        SUBSTR(phone, -4)
    ) AS 联系电话,
    created_at AS 注册时间
FROM users
WHERE real_name IS NOT NULL;

-- ============================================================================
-- 【视图2】患者信息脱敏视图 - view_patient_masked
-- ============================================================================
-- 原始表：patients 表（患者基本信息）
-- 敏感字段：birthday（出生日期）、phone（联系电话）、address（住址）
-- 脱敏方式：
--   - birthday: 只显示年份，隐藏月日 (如：1990-** 或仅显示年龄)
--   - phone: 显示前3位+****+后4位 (如：139****7919)
--   - address: 只显示前5个字符，后续用**表示 (如：北京市朝阳**)
-- 说明：web 界面实际不展示这些字段，但通过视图进一步限制 doctor 和 viewer 的权限

DROP VIEW IF EXISTS view_patient_masked;
CREATE VIEW view_patient_masked AS
SELECT
    id AS 患者ID,
    patient_id AS 患者编号,
    name AS 患者姓名,
    gender AS 性别,
    age AS 年龄,
    -- 出生日期脱敏：只显示年份，隐藏月日
    CONCAT(YEAR(birthday), '-**') AS 出生日期,
    -- 电话号码脱敏：显示前3位+****+后4位 (如：139****7919)
    CONCAT(
        SUBSTR(phone, 1, 3),
        '****',
        SUBSTR(phone, -4)
    ) AS 联系电话,
    -- 住址脱敏：只保留前5个字符，后续用**表示
    CONCAT(
        SUBSTR(address, 1, 5),
        '**'
    ) AS 住址,
    created_at AS 注册时间
FROM patients
WHERE phone IS NOT NULL;

-- ============================================================================
-- 【权限管理】授予不同角色的访问权限
-- ============================================================================

-- 授予 doctor 角色对脱敏用户视图的访问权限
GRANT SELECT ON SECD.view_user_masked TO 'doctor'@'localhost';

-- 授予 viewer 角色对脱敏用户视图的访问权限
GRANT SELECT ON SECD.view_user_masked TO 'viewer'@'localhost';

-- 授予 doctor 角色对脱敏患者视图的访问权限
GRANT SELECT ON SECD.view_patient_masked TO 'doctor'@'localhost';

-- 授予 viewer 角色对脱敏患者视图的访问权限
GRANT SELECT ON SECD.view_patient_masked TO 'viewer'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- ============================================================================
-- 【验证脱敏效果】
-- ============================================================================

-- 查看用户脱敏视图
SELECT '=== 用户信息脱敏视图（view_user_masked）===' AS 提示;
SELECT * FROM view_user_masked LIMIT 5;

-- 查看患者脱敏视图
SELECT '=== 患者信息脱敏视图（view_patient_masked）===' AS 提示;
SELECT * FROM view_patient_masked LIMIT 5;

-- ============================================================================
-- 【对比演示】原始表 vs 脱敏视图
-- ============================================================================

SELECT '=== 【原始 users 表】包含完整敏感信息 ===' AS 提示;
SELECT id, username, real_name, phone, password, role FROM users LIMIT 2;

SELECT '=== 【脱敏视图】隐藏密码，脱敏姓名和电话 ===' AS 提示;
SELECT 用户ID, 账号, 真实姓名, 联系电话, 角色 FROM view_user_masked LIMIT 2;

SELECT '';
SELECT '=== 【原始 patients 表】包含完整敏感信息 ===' AS 提示;
SELECT id, patient_id, name, birthday, phone, address FROM patients LIMIT 2;

SELECT '=== 【脱敏视图】脱敏出生日期、电话、住址 ===' AS 提示;
SELECT 患者ID, 患者编号, 患者姓名, 出生日期, 联系电话, 住址 FROM view_patient_masked LIMIT 2;

-- ============================================================================
-- 完成：视图保护方案已实施
-- ============================================================================
