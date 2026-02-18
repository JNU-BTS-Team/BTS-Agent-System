# 使用密钥SSH连接远程服务器: https://www.cnblogs.com/zhujingzhi/p/9686208.html

import paramiko

client = paramiko.SSHClient() # 实例化SSHClient
client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接

client.connect(
    hostname='117.50.179.58',
    port=22,
    username='ubuntu',
    password='wpw242512'
)

# 激活conda环境并且运行远程脚本
command = """
source /home/ubuntu/miniconda3/etc/profile.d/conda.sh &&
conda activate PeiweiWu_env &&
cd /data/WPW/BTS-Agent-Sys/BTS &&
python main.py
"""
# command = 'nvidia-smi'

stdin, stdout, stderr = client.exec_command(command)

# 打印标准输出
print("STDOUT:")
print(stdout.read().decode('utf8'))

# 打印错误输出
print("STDERR:")
print(stderr.read().decode('utf8'))

client.close() # 关闭连接
