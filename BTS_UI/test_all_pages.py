import requests

# 测试所有主要页面的访问情况
base_url = 'http://localhost:5000'

# 登录凭证
login_data = {
    'username': 'admin',
    'password': 'admin123'
}

def test_login():
    print('测试登录功能...')
    response = requests.post(f'{base_url}/login', data=login_data, allow_redirects=True)
    if response.status_code == 200:
        print('✓ 登录成功')
        return response.cookies
    else:
        print(f'✗ 登录失败，状态码: {response.status_code}')
        return None

def test_page_access(cookies, page_name, page_url):
    print(f'测试{page_name}页面...')
    response = requests.get(f'{base_url}{page_url}', cookies=cookies)
    if response.status_code == 200:
        print(f'✓ {page_name}页面访问成功')
        return True
    else:
        print(f'✗ {page_name}页面访问失败，状态码: {response.status_code}')
        return False

def main():
    print('开始测试所有主要页面...')
    print('=' * 50)
    
    # 先登录获取会话
    cookies = test_login()
    if not cookies:
        print('无法获取登录会话，测试终止')
        return
    
    print('=' * 50)
    
    # 测试所有主要页面
    pages = [
        ('主界面', '/main_interface'),
        ('病人管理', '/patients'),
        ('医生管理', '/doctors'),
        ('远程测试', '/remote_test')
    ]
    
    success_count = 0
    total_count = len(pages)
    
    for page_name, page_url in pages:
        if test_page_access(cookies, page_name, page_url):
            success_count += 1

    # 简单测试 upload_nii 接口：不带文件或类型应该返回错误
    print('测试上传接口返回错误信息...')
    response = requests.post(f'{base_url}/upload_nii', cookies=cookies)
    if response.status_code == 200 and '请至少选择一种类型' in response.text:
        print('✓ upload_nii基础验证通过')
    else:
        print(f'✗ upload_nii基础验证失败，状态码: {response.status_code}, 响应: {response.text}')
    
    print('=' * 50)
    print(f'测试完成: {success_count}/{total_count} 页面访问成功')
    
    if success_count == total_count:
        print('所有页面测试通过！')
    else:
        print('部分页面测试失败，请检查系统配置')

if __name__ == '__main__':
    main()