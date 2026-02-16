import paramiko
 
# 实例化SSHClient
client = paramiko.SSHClient()

# 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
 
# 连接SSH服务器，用户名密码认证
client.connect(hostname='117.50.179.58', port=22, username='ubuntu', password='wpw242512')
 
# 打开一个Chanent并执行命令
stdin, stdout, stderr = client.exec_command('df -h') # stdout 为正确输出，stderr为错误输出，同时是有1个变量有值
print(stdout.read().decode('utf8')) # 打印结果 

# 打开一个Chanent并执行命令
stdin, stdout, stderr = client.exec_command('nvidia-smi') # stdout 为正确输出，stderr为错误输出，同时是有1个变量有值
print(stdout.read().decode('utf8')) # 打印结果

# 关闭连接
client.close()
