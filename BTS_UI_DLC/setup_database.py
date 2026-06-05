import getpass
import hashlib
import os
import sys

import mysql.connector


APP_DB = "SECD"
APP_USER = "appuser"
APP_PASSWORD = "123456"


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def connect_root():
    root_password = getpass.getpass("MySQL root password (press Enter if empty): ")
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=root_password,
        autocommit=False,
    )


def execute_statements(cursor, statements):
    for statement in statements:
        statement = statement.strip()
        if statement:
            cursor.execute(statement)


def import_current_data(cursor):
    dump_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "current_data.sql")
    if not os.path.exists(dump_path):
        return False

    print("Importing current_data.sql snapshot...")
    with open(dump_path, "r", encoding="utf-8") as dump_file:
        for raw_line in dump_file:
            statement = raw_line.strip()
            if not statement or statement.startswith("--"):
                continue
            if statement.endswith(";"):
                statement = statement[:-1]
            if statement:
                cursor.execute(statement)
    print("Current database snapshot imported.")
    return True


def main():
    try:
        conn = connect_root()
    except mysql.connector.Error as err:
        print(f"Cannot connect to MySQL as root: {err}")
        return 1

    try:
        cursor = conn.cursor()
        execute_statements(
            cursor,
            [
                f"CREATE DATABASE IF NOT EXISTS {APP_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
                f"CREATE USER IF NOT EXISTS '{APP_USER}'@'localhost' IDENTIFIED BY '{APP_PASSWORD}'",
                f"ALTER USER '{APP_USER}'@'localhost' IDENTIFIED BY '{APP_PASSWORD}'",
                f"GRANT ALL PRIVILEGES ON {APP_DB}.* TO '{APP_USER}'@'localhost'",
                "FLUSH PRIVILEGES",
                f"USE {APP_DB}",
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'doctor') NOT NULL,
                    real_name VARCHAR(100) NULL,
                    department VARCHAR(100) NULL,
                    title VARCHAR(100) NULL,
                    phone VARCHAR(30) NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id VARCHAR(20) NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    gender VARCHAR(20) NOT NULL,
                    age INT NOT NULL,
                    birthday DATE NULL,
                    phone VARCHAR(20) NULL,
                    address TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS diagnoses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT NOT NULL,
                    doctor_id INT NOT NULL,
                    diagnosis_date TIMESTAMP NOT NULL,
                    follow_up_date DATE NULL,
                    diagnosis_type VARCHAR(50) NULL,
                    tumor_type VARCHAR(100) NULL,
                    tumor_stage VARCHAR(20) NULL,
                    diagnosis_content TEXT NOT NULL,
                    treatment_plan TEXT NULL,
                    examination_results TEXT NULL,
                    notes TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    diagnosis_id INT NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    image_name VARCHAR(100) NOT NULL,
                    image_type VARCHAR(20) NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    type ENUM('new_diagnosis', 'follow_up', 'todo') NOT NULL,
                    title VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    related_id INT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS todos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    assigner_id INT NOT NULL,
                    assignee_id INT NOT NULL,
                    due_date DATE NOT NULL,
                    is_completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    FOREIGN KEY (assigner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
            ],
        )

        imported_snapshot = import_current_data(cursor)
        if not imported_snapshot:
            admin_password = hash_password("admin123")
            cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE users
                    SET password = %s, role = 'admin', real_name = '系统管理员',
                        department = '系统管理', title = '管理员', phone = '13800000000'
                    WHERE username = 'admin'
                    """,
                    (admin_password,),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO users (username, password, role, real_name, department, title, phone)
                    VALUES (%s, %s, 'admin', '系统管理员', '系统管理', '管理员', '13800000000')
                    """,
                    ("admin", admin_password),
                )

        conn.commit()
        print("Database initialized successfully.")
        print(f"Database: {APP_DB}")
        print(f"Application user: {APP_USER} / {APP_PASSWORD}")
        print("Default login: admin / admin123")
        return 0
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database initialization failed: {err}")
        return 1
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
