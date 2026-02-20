import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from PIL import Image, ImageTk
from tumor_management_system import TumorManagementSystem
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class TumorGUISystem:
    def __init__(self):
        self.system = TumorManagementSystem()
        self.root = tk.Tk()
        self.root.title("智能脑肿瘤诊疗病例管理系统")
        self.root.geometry("1200x800")
        
        # 添加背景图片
        self.background_image = Image.open("images.jpg")
        self.background_image = self.background_image.resize((1200, 800), Image.Resampling.LANCZOS)
        self.background_photo = ImageTk.PhotoImage(self.background_image)
        self.background_label = tk.Label(self.root, image=self.background_photo)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # 设置全局样式
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 12), background="#ffffff")
        self.style.configure("TButton", font=("Arial", 12, "bold"), padding=10, background="#a8d8ea", foreground="#000000")
        self.style.map("TButton", background=[("active", "#87ceeb")], relief=[("pressed", "sunken")])
        self.style.configure("TEntry", font=("Arial", 12), padding=5, relief=tk.GROOVE)
        self.style.configure("TCombobox", font=("Arial", 12))
        self.style.configure("Treeview", font=("Arial", 10), rowheight=25)
        self.style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#a8d8ea")
        
        # 创建登录界面
        self.create_login_frame()
    
    def create_login_frame(self):
        """创建登录界面"""
        # 移除所有现有框架
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 登录框架
        self.login_frame = tk.Frame(self.root, bg="#f0f0f0", bd=5, relief=tk.RAISED)
        self.login_frame.pack(expand=True, padx=50, pady=50)
        
        # 标题
        title_label = tk.Label(self.login_frame, text="智能脑肿瘤诊疗病例管理系统", font=("Arial", 24, "bold"), bg="#f0f0f0")
        title_label.grid(row=0, column=0, columnspan=2, pady=40)
        
        # 用户名标签和输入框
        username_label = ttk.Label(self.login_frame, text="用户名：")
        username_label.grid(row=1, column=0, padx=20, pady=15, sticky=tk.E)
        
        self.username_entry = ttk.Entry(self.login_frame, width=30)
        self.username_entry.grid(row=1, column=1, padx=20, pady=15)
        
        # 密码标签和输入框
        password_label = ttk.Label(self.login_frame, text="密码：")
        password_label.grid(row=2, column=0, padx=20, pady=15, sticky=tk.E)
        
        self.password_entry = ttk.Entry(self.login_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, padx=20, pady=15)
        
        # 登录按钮
        login_button = ttk.Button(self.login_frame, text="登录", width=15, command=self.login)
        login_button.grid(row=3, column=0, columnspan=2, pady=30)
        
        # 回车键登录
        self.root.bind('<Return>', lambda event: self.login())
    
    def login(self):
        """登录功能"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("警告", "请输入用户名和密码！")
            return
        
        if self.system.login(username, password):
            messagebox.showinfo("成功", f"登录成功！欢迎 {self.system.current_user['role']} {username}")
            self.create_main_frame()
        else:
            messagebox.showerror("错误", "用户名或密码错误！")
    
    def create_main_frame(self):
        """创建主界面"""
        # 移除登录框架
        self.login_frame.destroy()
        
        # 创建主框架
        self.main_frame = tk.Frame(self.root, bg="#ffffff", bd=5, relief=tk.FLAT)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 顶部菜单栏
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # 文件菜单
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="文件", menu=self.file_menu)
        self.file_menu.add_command(label="退出系统", command=self.exit_system)
        
        # 用户菜单
        self.user_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="用户", menu=self.user_menu)
        self.user_menu.add_command(label="切换账号", command=self.create_login_frame)
        self.user_menu.add_command(label="修改密码", command=self.change_password)
        
        # 根据用户角色显示不同的功能菜单
        if self.system.current_user['role'] == 'admin':
            self.create_admin_frame()
        else:
            self.create_doctor_frame()
    
    def create_admin_frame(self):
        """创建管理员界面"""
        # 功能选择框架
        self.function_frame = tk.Frame(self.main_frame, bg="#f0f0f0ff", bd=2, relief=tk.GROOVE)
        self.function_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # 标题
        title_label = tk.Label(self.function_frame, text="管理员功能", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # 功能按钮
        doctor_manage_button = ttk.Button(self.function_frame, text="医生管理", width=20, command=self.show_doctor_management)
        doctor_manage_button.pack(pady=10, padx=20)
        
        # 内容显示框架
        self.content_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始显示医生管理界面
        self.show_doctor_management()
    
    def create_doctor_frame(self):
        """创建医生界面"""
        # 功能选择框架
        self.function_frame = tk.Frame(self.main_frame, bg="#f0f0f0", bd=2, relief=tk.RAISED)
        self.function_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # 标题
        title_label = tk.Label(self.function_frame, text="医生功能", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # 功能按钮
        patient_manage_button = ttk.Button(self.function_frame, text="病人管理", width=20, command=self.show_patient_management)
        patient_manage_button.pack(pady=10, padx=20)
        
        diagnosis_button = ttk.Button(self.function_frame, text="诊断记录", width=20, command=self.show_diagnosis_management)
        diagnosis_button.pack(pady=10, padx=20)
        
        # 数据统计按钮
        statistics_button = ttk.Button(self.function_frame, text="数据统计分析", width=20, command=self.show_statistics)
        statistics_button.pack(pady=10, padx=20)
        
        # 内容显示框架
        self.content_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始显示病人管理界面
        self.show_patient_management()
    
    # ------------------------- 管理员功能：医生管理 ------------------------- #
    def show_doctor_management(self):
        """显示医生管理界面"""
        # 清除内容框架
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = tk.Label(self.content_frame, text="医生管理", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # 添加医生框架
        add_frame = tk.LabelFrame(self.content_frame, text="添加医生", font=("Arial", 14), bg="#f0f0f0", padx=20, pady=15)
        add_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 用户名
        tk.Label(add_frame, text="用户名：", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.new_doc_username = ttk.Entry(add_frame, width=30)
        self.new_doc_username.grid(row=0, column=1, padx=10, pady=10)
        
        # 密码
        tk.Label(add_frame, text="密码：", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=2, padx=10, pady=10, sticky=tk.E)
        self.new_doc_password = ttk.Entry(add_frame, width=30, show="*")
        self.new_doc_password.grid(row=0, column=3, padx=10, pady=10)
        
        # 添加按钮
        add_button = ttk.Button(add_frame, text="添加医生", command=self.add_doctor)
        add_button.grid(row=0, column=4, padx=20, pady=10)
        
        # 搜索框架
        search_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(search_frame, text="用户名：", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT, padx=10)
        self.search_doc_username = ttk.Entry(search_frame, width=20)
        self.search_doc_username.pack(side=tk.LEFT, padx=10)
        
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_doctor)
        search_button.pack(side=tk.LEFT, padx=10)
        
        clear_button = ttk.Button(search_frame, text="清空", command=self.clear_search_doctor)
        clear_button.pack(side=tk.LEFT, padx=10)
        
        # 医生列表
        list_frame = tk.LabelFrame(self.content_frame, text="医生列表", font=("Arial", 14), bg="#f0f0f0", padx=20, pady=15)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建树视图
        columns = ("id", "username", "role", "created_at")
        self.doctor_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列宽和标题
        self.doctor_tree.column("id", width=50, anchor=tk.CENTER)
        self.doctor_tree.column("username", width=150, anchor=tk.CENTER)
        self.doctor_tree.column("role", width=100, anchor=tk.CENTER)
        self.doctor_tree.column("created_at", width=200, anchor=tk.CENTER)
        
        self.doctor_tree.heading("id", text="ID")
        self.doctor_tree.heading("username", text="用户名")
        self.doctor_tree.heading("role", text="角色")
        self.doctor_tree.heading("created_at", text="创建时间")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.doctor_tree.yview)
        self.doctor_tree.configure(yscroll=scrollbar.set)
        
        self.doctor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 操作按钮
        button_frame = tk.Frame(list_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=10)
        
        refresh_button = ttk.Button(button_frame, text="刷新列表", command=self.refresh_doctor_list)
        refresh_button.pack(side=tk.LEFT, padx=10)
        
        delete_button = ttk.Button(button_frame, text="删除医生", command=self.delete_doctor)
        delete_button.pack(side=tk.LEFT, padx=10)
        
        # 初始加载医生列表
        self.refresh_doctor_list()
    
    def add_doctor(self):
        """添加医生功能"""
        username = self.new_doc_username.get()
        password = self.new_doc_password.get()
        
        if not username or not password:
            messagebox.showwarning("警告", "请输入用户名和密码！")
            return
        
        if self.system.add_doctor(username, password):
            messagebox.showinfo("成功", f"医生账号 {username} 添加成功！")
            self.new_doc_username.delete(0, tk.END)
            self.new_doc_password.delete(0, tk.END)
            self.refresh_doctor_list()
        else:
            messagebox.showerror("错误", "添加医生失败！")
    
    def search_doctor(self):
        """搜索医生功能"""
        username = self.search_doc_username.get()
        if not username:
            messagebox.showwarning("警告", "请输入用户名！")
            return
        
        # 清空现有数据
        for item in self.doctor_tree.get_children():
            self.doctor_tree.delete(item)
        
        # 搜索医生
        doctors = self.system.search_doctors(username)
        
        # 显示搜索结果
        if doctors:
            for i, doctor in enumerate(doctors, 1):
                self.doctor_tree.insert("", tk.END, values=(i, doctor["username"], doctor["role"], doctor["created_at"]))
        else:
            messagebox.showinfo("提示", f"未找到用户名包含 '{username}' 的医生！")
    
    def clear_search_doctor(self):
        """清空搜索条件"""
        self.search_doc_username.delete(0, tk.END)
        self.refresh_doctor_list()
    
    def refresh_doctor_list(self):
        """刷新医生列表"""
        # 清空现有数据
        for item in self.doctor_tree.get_children():
            self.doctor_tree.delete(item)
        
        # 获取医生列表
        doctors = self.system.get_all_doctors()
        
        # 显示医生列表，使用虚拟ID（从1开始）
        for i, doctor in enumerate(doctors, 1):
            self.doctor_tree.insert("", tk.END, values=(i, doctor["username"], doctor["role"], doctor["created_at"]))
        return
        

    
    # ------------------------- 医生功能：病人管理 ------------------------- #
    def show_patient_management(self):
        """显示病人管理界面"""
        # 清除内容框架
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = tk.Label(self.content_frame, text="病人管理", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # 添加病人框架
        add_frame = tk.LabelFrame(self.content_frame, text="添加病人", font=("Arial", 14), bg="#f0f0f0", padx=20, pady=15)
        add_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 病人ID
        tk.Label(add_frame, text="病人ID：", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, padx=10, pady=10, sticky=tk.E)
        self.patient_id = ttk.Entry(add_frame, width=20)
        self.patient_id.grid(row=0, column=1, padx=10, pady=10)
        
        # 姓名
        tk.Label(add_frame, text="姓名：", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=2, padx=10, pady=10, sticky=tk.E)
        self.patient_name = ttk.Entry(add_frame, width=20)
        self.patient_name.grid(row=0, column=3, padx=10, pady=10)
        
        # 性别
        tk.Label(add_frame, text="性别：", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=0, padx=10, pady=10, sticky=tk.E)
        self.patient_gender = ttk.Combobox(add_frame, values=["男", "女", "其他"], width=18, state="readonly")
        self.patient_gender.grid(row=1, column=1, padx=10, pady=10)
        self.patient_gender.current(0)
        
        # 年龄
        tk.Label(add_frame, text="年龄：", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=2, padx=10, pady=10, sticky=tk.E)
        self.patient_age = ttk.Entry(add_frame, width=20)
        self.patient_age.grid(row=1, column=3, padx=10, pady=10)
        
        # 电话
        tk.Label(add_frame, text="电话：", font=("Arial", 12), bg="#f0f0f0").grid(row=2, column=0, padx=10, pady=10, sticky=tk.E)
        self.patient_phone = ttk.Entry(add_frame, width=20)
        self.patient_phone.grid(row=2, column=1, padx=10, pady=10)
        
        # 地址
        tk.Label(add_frame, text="地址：", font=("Arial", 12), bg="#f0f0f0").grid(row=2, column=2, padx=10, pady=10, sticky=tk.E)
        self.patient_address = ttk.Entry(add_frame, width=20)
        self.patient_address.grid(row=2, column=3, padx=10, pady=10)
        
        # 添加按钮
        add_button = ttk.Button(add_frame, text="添加病人", command=self.add_patient)
        add_button.grid(row=3, column=0, columnspan=4, pady=20)
        
        # 病人列表
        list_frame = tk.LabelFrame(self.content_frame, text="病人列表", font=("Arial", 14), bg="#f0f0f0", padx=20, pady=15)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建树视图
        columns = ("id", "patient_id", "name", "gender", "age", "phone", "address")
        self.patient_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列宽和标题
        self.patient_tree.column("id", width=50, anchor=tk.CENTER)
        self.patient_tree.column("patient_id", width=100, anchor=tk.CENTER)
        self.patient_tree.column("name", width=100, anchor=tk.CENTER)
        self.patient_tree.column("gender", width=80, anchor=tk.CENTER)
        self.patient_tree.column("age", width=80, anchor=tk.CENTER)
        self.patient_tree.column("phone", width=150, anchor=tk.CENTER)
        self.patient_tree.column("address", width=200, anchor=tk.CENTER)
        
        self.patient_tree.heading("id", text="ID")
        self.patient_tree.heading("patient_id", text="病人ID")
        self.patient_tree.heading("name", text="姓名")
        self.patient_tree.heading("gender", text="性别")
        self.patient_tree.heading("age", text="年龄")
        self.patient_tree.heading("phone", text="电话")
        self.patient_tree.heading("address", text="地址")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.patient_tree.yview)
        self.patient_tree.configure(yscroll=scrollbar.set)
        
        self.patient_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 操作按钮
        button_frame = tk.Frame(list_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=10)
        
        refresh_button = ttk.Button(button_frame, text="刷新列表", command=self.refresh_patient_list)
        refresh_button.pack(side=tk.LEFT, padx=10)
        
        delete_button = ttk.Button(button_frame, text="删除病人", command=self.delete_patient)
        delete_button.pack(side=tk.LEFT, padx=10)
        
        # 初始加载病人列表
        self.refresh_patient_list()
    
    def add_patient(self):
        """添加病人功能"""
        patient_id = self.patient_id.get()
        name = self.patient_name.get()
        gender = self.patient_gender.get()
        age = self.patient_age.get()
        phone = self.patient_phone.get()
        address = self.patient_address.get()
        
        if not all([patient_id, name, gender, age]):
            messagebox.showwarning("警告", "请填写病人ID、姓名、性别和年龄！")
            return
        
        # 验证年龄
        try:
            age = int(age)
            if age < 0 or age > 120:
                messagebox.showwarning("警告", "年龄必须在0-120之间！")
                return
        except ValueError:
            messagebox.showwarning("警告", "年龄必须是数字！")
            return
        
        # 验证手机号格式
        if phone and not phone.isdigit():
            messagebox.showwarning("警告", "手机号必须是数字！")
            return
        
        if self.system.add_patient(patient_id, name, gender, age, None, phone, address):
            messagebox.showinfo("成功", f"病人 {name} 添加成功！")
            # 清空输入框
            self.patient_id.delete(0, tk.END)
            self.patient_name.delete(0, tk.END)
            self.patient_gender.current(0)
            self.patient_age.delete(0, tk.END)
            self.patient_phone.delete(0, tk.END)
            self.patient_address.delete(0, tk.END)
            self.refresh_patient_list()
        else:
            messagebox.showerror("错误", "添加病人失败！")
    
    def refresh_patient_list(self):
        """刷新病人列表"""
        # 清空现有数据
        for item in self.patient_tree.get_children():
            self.patient_tree.delete(item)
        
        # 获取病人列表
        patients = self.system.get_all_patients()
        
        # 显示病人列表，使用虚拟ID（从1开始）
        for i, patient in enumerate(patients, 1):
            self.patient_tree.insert("", tk.END, values=(i, patient["patient_id"], patient["name"], 
                                                          patient["gender"], patient["age"], patient["phone"], 
                                                          patient["address"]))
    
    def delete_patient(self):
        """删除病人功能"""
        selected_item = self.patient_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择要删除的病人！")
            return
        
        item = self.patient_tree.item(selected_item)
        patient_id = item["values"][1]  # 获取病人ID
        
        if messagebox.askyesno("确认删除", f"确定要删除病人ID为 {patient_id} 的记录吗？"):
            if self.system.delete_patient(patient_id):
                messagebox.showinfo("成功", "病人删除成功！")
                self.refresh_patient_list()
            else:
                messagebox.showerror("错误", "病人删除失败！")
    
    def show_diagnosis_management(self):
        """显示诊断管理界面"""
        # 清除内容框架
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = tk.Label(self.content_frame, text="诊断记录管理", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # 搜索框架
        search_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(search_frame, text="病人姓名：", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT, padx=10)
        self.search_patient_name = ttk.Entry(search_frame, width=20)
        self.search_patient_name.pack(side=tk.LEFT, padx=10)
        
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_patient)
        search_button.pack(side=tk.LEFT, padx=10)
        
        # 搜索结果显示区域
        self.result_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 诊断记录列表将在这里显示
        tk.Label(self.result_frame, text="搜索病人后显示诊断记录", font=("Arial", 16), bg="#f0f0f0").pack(pady=50)
    
    def search_patient(self):
        """搜索病人功能"""
        patient_name = self.search_patient_name.get()
        if not patient_name:
            messagebox.showwarning("警告", "请输入病人姓名！")
            return
        
        # 清除结果框架
        for widget in self.result_frame.winfo_children():
            widget.destroy()
        
        # 根据姓名搜索病人
        patients = self.system.search_patients_by_name(patient_name)
        if not patients:
            messagebox.showwarning("警告", f"未找到姓名包含 '{patient_name}' 的病人！")
            tk.Label(self.result_frame, text="搜索病人后显示诊断记录", font=("Arial", 16), bg="#f0f0f0").pack(pady=50)
            return
        
        # 如果找到多个病人，让用户选择
        if len(patients) > 1:
            from tkinter import simpledialog
            
            # 创建选择对话框
            patient_options = [f"ID: {p['patient_id']}, 姓名: {p['name']}, 年龄: {p['age']}" for p in patients]
            patient_choice = simpledialog.askstring("选择病人", "找到多个病人，请输入要查看的病人ID:\n" + "\n".join(patient_options))
            
            if not patient_choice:
                tk.Label(self.result_frame, text="搜索病人后显示诊断记录", font=("Arial", 16), bg="#f0f0f0").pack(pady=50)
                return
            
            # 查找选择的病人
            selected_patient = None
            for p in patients:
                if p['patient_id'] == patient_choice:
                    selected_patient = p
                    break
            
            if not selected_patient:
                messagebox.showwarning("警告", f"未找到病人ID为 {patient_choice} 的病人！")
                tk.Label(self.result_frame, text="搜索病人后显示诊断记录", font=("Arial", 16), bg="#f0f0f0").pack(pady=50)
                return
        else:
            selected_patient = patients[0]
        
        patient = selected_patient
        
        # 显示病人信息
        patient_frame = tk.LabelFrame(self.result_frame, text="病人信息", font=("Arial", 14), bg="#f0f0f0", padx=20, pady=15)
        patient_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(patient_frame, text=f"病人ID：{patient['patient_id']}", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT, padx=20)
        tk.Label(patient_frame, text=f"姓名：{patient['name']}", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT, padx=20)
        tk.Label(patient_frame, text=f"性别：{patient['gender']}", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT, padx=20)
        tk.Label(patient_frame, text=f"年龄：{patient['age']}", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT, padx=20)
        
        # 添加诊断记录框架
        add_diagnosis_frame = tk.LabelFrame(self.result_frame, text="添加诊断记录", font=("Arial", 14), bg="#f0f0f0", padx=10, pady=5)
        add_diagnosis_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 肿瘤类型
        tk.Label(add_diagnosis_frame, text="肿瘤类型：", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.tumor_type = ttk.Entry(add_diagnosis_frame, width=25)
        self.tumor_type.grid(row=0, column=1, padx=5, pady=5)
        
        # 肿瘤位置
        tk.Label(add_diagnosis_frame, text="肿瘤位置：", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        self.tumor_location = ttk.Entry(add_diagnosis_frame, width=25)
        self.tumor_location.grid(row=0, column=3, padx=5, pady=5)
        
        # 肿瘤大小
        tk.Label(add_diagnosis_frame, text="肿瘤大小：", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.tumor_size = ttk.Entry(add_diagnosis_frame, width=25)
        self.tumor_size.grid(row=1, column=1, padx=5, pady=5)
        
        # 诊断日期
        tk.Label(add_diagnosis_frame, text="诊断日期：", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=2, padx=5, pady=5, sticky=tk.E)
        self.diagnosis_date = ttk.Entry(add_diagnosis_frame, width=25)
        self.diagnosis_date.grid(row=1, column=3, padx=5, pady=5)
        self.diagnosis_date.insert(0, datetime.now().strftime("%Y-%m-%d"))  # 默认今天
        
        # 医生备注
        tk.Label(add_diagnosis_frame, text="医生备注：", font=("Arial", 12), bg="#f0f0f0").grid(row=2, column=0, padx=5, pady=5, sticky=tk.NE)
        self.doctor_notes = tk.Text(add_diagnosis_frame, width=70, height=2, font=("Arial", 12))
        self.doctor_notes.grid(row=2, column=1, columnspan=3, padx=5, pady=5)
        
        # 添加诊断按钮
        add_diagnosis_button = ttk.Button(add_diagnosis_frame, text="添加诊断记录", command=lambda: self.add_diagnosis(patient['patient_id']))
        add_diagnosis_button.grid(row=3, column=0, columnspan=4, pady=10)
        
        # 上传MRI图片框架
        upload_frame = tk.LabelFrame(self.result_frame, text="上传MRI图片", font=("Arial", 14), bg="#f0f0f0", padx=10, pady=5)
        upload_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.image_path = tk.StringVar()
        tk.Label(upload_frame, text="图片路径：", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        tk.Entry(upload_frame, textvariable=self.image_path, width=50, font=("Arial", 12)).grid(row=0, column=1, padx=5, pady=5)
        
        browse_button = ttk.Button(upload_frame, text="浏览", command=self.browse_image)
        browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.selected_diagnosis_id = tk.StringVar()
        tk.Label(upload_frame, text="诊断ID：", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(upload_frame, textvariable=self.selected_diagnosis_id, width=50, font=("Arial", 12)).grid(row=1, column=1, padx=5, pady=5)
        
        upload_button = ttk.Button(upload_frame, text="上传图片", command=self.upload_image)
        upload_button.grid(row=2, column=0, columnspan=3, pady=10)
        
        # 诊断记录列表
        diagnosis_list_frame = tk.LabelFrame(self.result_frame, text="诊断记录列表", font=("Arial", 14), bg="#f0f0f0", padx=10, pady=5)
        diagnosis_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建树视图
        columns = ("id", "date", "type", "location", "size", "doctor")
        self.diagnosis_tree = ttk.Treeview(diagnosis_list_frame, columns=columns, show="headings", height=25)
        
        # 设置列宽和标题
        self.diagnosis_tree.column("id", width=80, anchor=tk.CENTER)
        self.diagnosis_tree.column("date", width=120, anchor=tk.CENTER)
        self.diagnosis_tree.column("type", width=150, anchor=tk.CENTER)
        self.diagnosis_tree.column("location", width=150, anchor=tk.CENTER)
        self.diagnosis_tree.column("size", width=100, anchor=tk.CENTER)
        self.diagnosis_tree.column("doctor", width=100, anchor=tk.CENTER)
        
        self.diagnosis_tree.heading("id", text="诊断ID")
        self.diagnosis_tree.heading("date", text="诊断日期")
        self.diagnosis_tree.heading("type", text="肿瘤类型")
        self.diagnosis_tree.heading("location", text="肿瘤位置")
        self.diagnosis_tree.heading("size", text="肿瘤大小")
        self.diagnosis_tree.heading("doctor", text="医生")
        
        # 添加滚动条
        diagnosis_scrollbar = ttk.Scrollbar(diagnosis_list_frame, orient='vertical', command=self.diagnosis_tree.yview)
        self.diagnosis_tree.configure(yscrollcommand=diagnosis_scrollbar.set)
        
        self.diagnosis_tree.pack(side='left', fill=tk.BOTH, expand=True)
        diagnosis_scrollbar.pack(side='right', fill='y')
        
        # 加载诊断记录
        self.load_diagnoses(patient['patient_id'])
    
    def add_diagnosis(self, patient_id):
        """添加诊断记录"""
        tumor_type = self.tumor_type.get()
        tumor_location = self.tumor_location.get()
        tumor_size = self.tumor_size.get()
        diagnosis_date = self.diagnosis_date.get()
        doctor_notes = self.doctor_notes.get(1.0, tk.END).strip()
        
        if not all([tumor_type, tumor_location, diagnosis_date]):
            messagebox.showwarning("警告", "请填写肿瘤类型、位置和诊断日期！")
            return
        
        # 验证日期格式 (YYYY-MM-DD)
        import re
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, diagnosis_date):
            messagebox.showwarning("警告", "日期格式不正确！请使用YYYY-MM-DD格式。")
            return
        
        # 验证肿瘤大小格式 (可选)
        if tumor_size:
            # 支持格式: "3.5x4.2", "5.0", "3-4"
            size_pattern = r'^\d+(\.\d+)?(x|-|,|\s)?\d*(\.\d+)?$'
            if not re.match(size_pattern, tumor_size):
                messagebox.showwarning("警告", "肿瘤大小格式不正确！例如: 3.5x4.2, 5.0, 3-4")
                return
        
        # 添加诊断记录
        diagnosis_id = self.system.add_diagnosis(
            patient_id=patient_id,
            diagnosis_date=diagnosis_date,
            tumor_type=tumor_type,
            tumor_location=tumor_location,
            tumor_size=tumor_size,
            doctor_notes=doctor_notes
        )
        
        if diagnosis_id:
            messagebox.showinfo("成功", f"诊断记录添加成功！诊断ID：{diagnosis_id}")
            # 清空输入框
            self.tumor_type.delete(0, tk.END)
            self.tumor_location.delete(0, tk.END)
            self.tumor_size.delete(0, tk.END)
            self.diagnosis_date.delete(0, tk.END)
            self.diagnosis_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.doctor_notes.delete(1.0, tk.END)
            # 更新诊断记录列表
            self.load_diagnoses(patient_id)
        else:
            messagebox.showerror("错误", "添加诊断记录失败！")
    
    def browse_image(self):
        """浏览选择图片"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tiff")]
        )
        if file_path:
            self.image_path.set(file_path)
    
    def upload_image(self):
        """上传图片功能"""
        image_path = self.image_path.get()
        diagnosis_id = self.selected_diagnosis_id.get()
        
        if not image_path:
            messagebox.showwarning("警告", "请选择要上传的图片！")
            return
        
        if not diagnosis_id:
            messagebox.showwarning("警告", "请输入诊断ID！")
            return
        
        try:
            diagnosis_id = int(diagnosis_id)
        except ValueError:
            messagebox.showwarning("警告", "诊断ID必须是数字！")
            return
        
        if self.system.upload_image(diagnosis_id, image_path):
            messagebox.showinfo("成功", "图片上传成功！")
            self.image_path.set("")
            self.selected_diagnosis_id.set("")
        else:
            messagebox.showerror("错误", "图片上传失败！")
    
    def load_diagnoses(self, patient_id):
        """加载病人的诊断记录"""
        # 清空现有数据
        for item in self.diagnosis_tree.get_children():
            self.diagnosis_tree.delete(item)
        
        # 获取诊断记录
        diagnoses = self.system.get_patient_diagnoses(patient_id)
        
        # 添加到树视图
        for diagnosis in diagnoses:
            self.diagnosis_tree.insert("", tk.END, values=(diagnosis["id"], diagnosis["diagnosis_date"], diagnosis["tumor_type"], 
                                                          diagnosis["tumor_location"], diagnosis["tumor_size"], 
                                                          diagnosis["doctor_name"] if "doctor_name" else "未知"))
    
    def show_statistics(self):
        """显示数据统计分析界面"""
        # 清除内容框架
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 标题
        title_label = tk.Label(self.content_frame, text="数据统计分析", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # 获取统计数据
        total_stats = self.system.get_total_statistics()
        
        # 统计卡片框架
        stats_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 总病人数
        patient_card = tk.LabelFrame(stats_frame, text="总病人数", font=("Arial", 12, "bold"), bg="#ffffff", padx=20, pady=15, relief="solid", bd=2)
        patient_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        tk.Label(patient_card, text=total_stats.get('total_patients', 0), font=("Arial", 32, "bold"), bg="#ffffff", fg="#2196F3").pack()
        
        # 总诊断数
        diagnosis_card = tk.LabelFrame(stats_frame, text="总诊断记录", font=("Arial", 12, "bold"), bg="#ffffff", padx=20, pady=15, relief="solid", bd=2)
        diagnosis_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        tk.Label(diagnosis_card, text=total_stats.get('total_diagnoses', 0), font=("Arial", 32, "bold"), bg="#ffffff", fg="#4CAF50").pack()
        
        # 总图片数
        image_card = tk.LabelFrame(stats_frame, text="总图片数", font=("Arial", 12, "bold"), bg="#ffffff", padx=20, pady=15, relief="solid", bd=2)
        image_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        tk.Label(image_card, text=total_stats.get('total_images', 0), font=("Arial", 32, "bold"), bg="#ffffff", fg="#FF9800").pack()
        
        # 本月诊断数
        monthly_card = tk.LabelFrame(stats_frame, text="本月诊断", font=("Arial", 12, "bold"), bg="#ffffff", padx=20, pady=15, relief="solid", bd=2)
        monthly_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        tk.Label(monthly_card, text=total_stats.get('monthly_diagnoses', 0), font=("Arial", 32, "bold"), bg="#ffffff", fg="#9C27B0").pack()
        
        # 图表框架
        charts_frame = tk.Frame(self.content_frame, bg="#f0f0f0")
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 年龄分布饼图
        age_frame = tk.LabelFrame(charts_frame, text="病人年龄分布", font=("Arial", 14, "bold"), bg="#f0f0f0", padx=20, pady=15)
        age_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        age_stats = self.system.get_patient_age_distribution()
        if age_stats:
            labels = [stat['age_group'] for stat in age_stats]
            sizes = [stat['count'] for stat in age_stats]
            
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
            ax.axis('equal')  # 保证饼图是圆形
            
            canvas = FigureCanvasTkAgg(fig, master=age_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(age_frame, text="暂无年龄分布数据", font=("Arial", 14), bg="#f0f0f0").pack(pady=50)
        
        # 肿瘤类型柱状图
        tumor_frame = tk.LabelFrame(charts_frame, text="肿瘤类型分布", font=("Arial", 14, "bold"), bg="#f0f0f0", padx=20, pady=15)
        tumor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tumor_stats = self.system.get_tumor_type_distribution()
        if tumor_stats:
            labels = [stat['tumor_type'] for stat in tumor_stats]
            values = [stat['count'] for stat in tumor_stats]
            
            fig = Figure(figsize=(5, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.bar(labels, values, color='skyblue')
            ax.set_ylabel('数量')
            ax.tick_params(axis='x', rotation=45)
            
            canvas = FigureCanvasTkAgg(fig, master=tumor_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(tumor_frame, text="暂无肿瘤类型数据", font=("Arial", 14), bg="#f0f0f0").pack(pady=50)
        
        # 月度诊断趋势图
        monthly_frame = tk.LabelFrame(self.content_frame, text="月度诊断趋势", font=("Arial", 14, "bold"), bg="#f0f0f0", padx=20, pady=15)
        monthly_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        monthly_stats = self.system.get_monthly_diagnoses()
        if monthly_stats:
            months = [stat['month'] for stat in monthly_stats]
            counts = [stat['count'] for stat in monthly_stats]
            
            fig = Figure(figsize=(10, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.plot(months, counts, marker='o', color='orange', linewidth=2)
            ax.set_ylabel('诊断数量')
            ax.grid(True, alpha=0.3)
            
            canvas = FigureCanvasTkAgg(fig, master=monthly_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(monthly_frame, text="暂无月度诊断数据", font=("Arial", 14), bg="#f0f0f0").pack(pady=50)
    
    def delete_doctor(self):
        """删除选中的医生账号"""
        selected_item = self.doctor_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择要删除的医生账号！")
            return
        
        # 获取选中医生的信息
        item = self.doctor_tree.item(selected_item[0])
        username = item['values'][1]
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除医生 '{username}' 吗？"):
            success = self.system.delete_doctor(username)
            if success:
                messagebox.showinfo("成功", f"医生 '{username}' 删除成功！")
                self.refresh_doctor_list()
            else:
                messagebox.showerror("错误", "删除医生失败！")
    
    def change_password(self):
        """修改密码功能"""
        from tkinter import Toplevel
        
        # 创建修改密码对话框
        password_window = Toplevel(self.root)
        password_window.title("修改密码")
        password_window.geometry("350x250")
        password_window.resizable(False, False)
        
        # 居中显示
        window_width = password_window.winfo_reqwidth()
        window_height = password_window.winfo_reqheight()
        position_right = int(password_window.winfo_screenwidth() / 2 - window_width / 2)
        position_down = int(password_window.winfo_screenheight() / 2 - window_height / 2)
        password_window.geometry(f"+{position_right}+{position_down}")
        
        # 创建标签和输入框
        ttk.Label(password_window, text="旧密码：").pack(pady=(20, 5))
        old_password_entry = ttk.Entry(password_window, show="*")
        old_password_entry.pack(fill="x", padx=20, pady=(0, 15))
        old_password_entry.focus()
        
        ttk.Label(password_window, text="新密码：").pack(pady=5)
        new_password_entry = ttk.Entry(password_window, show="*")
        new_password_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        ttk.Label(password_window, text="确认新密码：").pack(pady=5)
        confirm_password_entry = ttk.Entry(password_window, show="*")
        confirm_password_entry.pack(fill="x", padx=20, pady=(0, 20))
        
        def save_password():
            old_password = old_password_entry.get().strip()
            new_password = new_password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            
            # 输入验证
            if not old_password:
                messagebox.showwarning("警告", "请输入旧密码！")
                return
            
            if not new_password:
                messagebox.showwarning("警告", "请输入新密码！")
                return
            
            if len(new_password) < 6:
                messagebox.showwarning("警告", "新密码长度不能少于6位！")
                return
            
            if new_password != confirm_password:
                messagebox.showwarning("警告", "两次输入的新密码不一致！")
                return
            
            # 修改密码
            success = self.system.change_password(old_password, new_password)
            if success:
                messagebox.showinfo("成功", "密码修改成功！")
                password_window.destroy()
            else:
                messagebox.showerror("错误", "旧密码错误或修改失败！")
        
        # 创建按钮
        btn_frame = ttk.Frame(password_window)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        save_btn = ttk.Button(btn_frame, text="保存", command=save_password)
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=password_window.destroy)
        cancel_btn.pack(side="left", fill="x", expand=True)
    
    def exit_system(self):
        """退出系统"""
        if messagebox.askyesno("退出", "确定要退出系统吗？"):
            self.system.close()
            self.root.destroy()
    
    def run(self):
        """运行GUI系统"""
        self.root.mainloop()


# 运行GUI系统
if __name__ == "__main__":
    gui = TumorGUISystem()
    gui.run()