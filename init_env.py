#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTS-Agent 数据库初始化脚本
自动导入数据库和验证配置
"""

import os
import sys
import mysql.connector
from pathlib import Path

# 配置
MYSQL_HOST = os.environ.get('DLC_MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('DLC_MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('DLC_MYSQL_PASSWORD', 'wpw242512')
MYSQL_DB = os.environ.get('DLC_MYSQL_DB', 'SECD2')

# SQL 文件位置
PROJECT_ROOT = Path(__file__).parent
SQL_FILES = [
    PROJECT_ROOT / 'secd2.sql',
    PROJECT_ROOT / 'BTS_UI_DLC' / 'current_data.sql',
    PROJECT_ROOT / 'BTS_UI_DLC' / 'init_db.sql',
    PROJECT_ROOT / 'new.sql',
]

def print_status(message, status='INFO'):
    """打印状态消息"""
    colors = {
        'INFO': '\033[94m',      # 蓝色
        'SUCCESS': '\033[92m',   # 绿色
        'ERROR': '\033[91m',     # 红色
        'WARNING': '\033[93m',   # 黄色
    }
    reset = '\033[0m'
    color = colors.get(status, '')
    print(f"{color}[{status}]{reset} {message}")

def test_connection():
    """测试数据库连接"""
    print_status("测试 MySQL 连接...", 'INFO')
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        conn.close()
        print_status(f"✓ 成功连接到 MySQL ({MYSQL_HOST})", 'SUCCESS')
        return True
    except mysql.connector.Error as e:
        print_status(f"✗ 连接失败: {e}", 'ERROR')
        print_status("请检查:", 'WARNING')
        print(f"  - MySQL 服务是否启动")
        print(f"  - 主机: {MYSQL_HOST}")
        print(f"  - 用户: {MYSQL_USER}")
        print(f"  - 密码是否正确")
        return False

def create_database():
    """创建数据库"""
    print_status(f"创建数据库 '{MYSQL_DB}'...", 'INFO')
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
        conn.commit()
        cursor.close()
        conn.close()
        print_status(f"✓ 数据库 '{MYSQL_DB}' 已创建", 'SUCCESS')
        return True
    except mysql.connector.Error as e:
        print_status(f"✗ 创建数据库失败: {e}", 'ERROR')
        return False

def import_sql_file(filepath):
    """导入 SQL 文件"""
    if not filepath.exists():
        print_status(f"⊘ 跳过不存在的文件: {filepath.name}", 'WARNING')
        return True

    print_status(f"导入 {filepath.name}...", 'INFO')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()

        # 执行 SQL 脚本
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)

        conn.commit()
        cursor.close()
        conn.close()
        print_status(f"✓ {filepath.name} 导入成功", 'SUCCESS')
        return True
    except Exception as e:
        print_status(f"✗ 导入 {filepath.name} 失败: {e}", 'ERROR')
        return False

def verify_configuration():
    """验证配置"""
    print_status("验证环境配置...", 'INFO')

    env_vars = [
        'AGENT_PIPELINE',
        'MULTI_AGENT_API_KEY',
        'DLC_MYSQL_HOST',
        'DLC_MYSQL_USER',
        'DLC_MYSQL_PASSWORD',
    ]

    missing = []
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"  ✓ {var}")
        else:
            print(f"  ✗ {var} (未设置)")
            missing.append(var)

    if missing:
        print_status(f"请先运行 start_both.local.ps1 或设置缺失的环境变量", 'WARNING')
    else:
        print_status("✓ 所有配置已设置", 'SUCCESS')

def main():
    """主函数"""
    print("\n" + "="*50)
    print("BTS-Agent 数据库初始化")
    print("="*50 + "\n")

    # 1. 测试连接
    if not test_connection():
        sys.exit(1)

    # 2. 创建数据库
    if not create_database():
        sys.exit(1)

    # 3. 导入 SQL 文件
    print_status("开始导入 SQL 文件...", 'INFO')
    for sql_file in SQL_FILES:
        import_sql_file(sql_file)

    # 4. 验证配置
    print()
    verify_configuration()

    print("\n" + "="*50)
    print_status("初始化完成！", 'SUCCESS')
    print("="*50)
    print("\n接下来的步骤:")
    print(f"  1. 浏览器访问: http://127.0.0.1:5000/login")
    print(f"  2. 默认账号: admin / admin123")
    print(f"  3. 数据库: {MYSQL_DB}@{MYSQL_HOST}")
    print()

if __name__ == '__main__':
    main()
