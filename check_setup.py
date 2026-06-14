#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BTS-Agent 配置验证脚本
检查所有依赖和配置是否正确
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """检查 Python 版本"""
    print("✓ Python 版本:", sys.version.split()[0])
    return True

def check_mysql():
    """检查 MySQL 连接"""
    try:
        import mysql.connector
        print("✓ mysql-connector-python 已安装")

        # 测试连接
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Hjk608866'
        )
        conn.close()
        print("✓ MySQL 连接成功 (localhost:3306)")
        return True
    except ImportError:
        print("✗ mysql-connector-python 未安装")
        print("  安装命令: pip install mysql-connector-python")
        return False
    except Exception as e:
        print(f"✗ MySQL 连接失败: {e}")
        print("  确保 MySQL 服务已启动，密码正确")
        return False

def check_flask():
    """检查 Flask"""
    try:
        import flask
        print(f"✓ Flask 已安装 (版本: {flask.__version__})")
        return True
    except ImportError:
        print("✗ Flask 未安装")
        print("  安装命令: pip install flask flask-login")
        return False

def check_deepseek():
    """检查 DeepSeek API 配置"""
    try:
        from openai import OpenAI
        api_key = "sk-7d027c8543f246be85e73317e585bdf9"
        if api_key:
            print(f"✓ API 密钥已配置")
            print(f"  键值: {api_key[:10]}...")
            return True
        return False
    except ImportError:
        print("✗ openai 库未安装")
        print("  安装命令: pip install openai")
        return False

def check_env_vars():
    """检查环境变量"""
    vars_to_check = {
        'AGENT_PIPELINE': 'multi',
        'MULTI_AGENT_MODEL': 'deepseek-chat',
        'DLC_MYSQL_HOST': 'localhost',
        'DLC_MYSQL_USER': 'root',
        'DLC_MYSQL_DB': 'SECD2',
    }

    missing = []
    for var, expected in vars_to_check.items():
        value = os.environ.get(var)
        if value:
            status = "✓" if value == expected else "⚠"
            print(f"{status} {var} = {value}")
        else:
            print(f"✗ {var} 未设置")
            missing.append(var)

    return len(missing) == 0

def check_dependencies():
    """检查所有 Python 依赖"""
    required = [
        'flask',
        'mysql',
        'openai',
        'paramiko',
    ]

    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package}")
            missing.append(package)

    return missing

def main():
    print("\n" + "="*60)
    print("BTS-Agent 配置检查")
    print("="*60 + "\n")

    print("[ 1 ] Python 环境")
    check_python()
    print()

    print("[ 2 ] 数据库连接")
    mysql_ok = check_mysql()
    print()

    print("[ 3 ] Web 框架")
    flask_ok = check_flask()
    print()

    print("[ 4 ] AI API 配置")
    api_ok = check_deepseek()
    print()

    print("[ 5 ] 环境变量")
    env_ok = check_env_vars()
    print()

    print("[ 6 ] Python 依赖")
    missing = check_dependencies()
    print()

    # 总结
    print("="*60)
    if mysql_ok and flask_ok and api_ok and not missing:
        print("✓ 所有检查通过！系统已准备就绪")
        print("\n接下来运行:")
        print("  powershell -ExecutionPolicy Bypass -File .\\start_both.ps1")
        return 0
    else:
        print("⚠ 发现问题，请按上述提示修复")
        if missing:
            print(f"\n缺失的包: {', '.join(missing)}")
            print(f"安装命令: pip install {' '.join(missing)}")
        if not env_ok:
            print("\n⚠ 环境变量未设置")
            print("  运行: .\\start_both.local.ps1")
        return 1

if __name__ == '__main__':
    sys.exit(main())
