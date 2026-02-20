import requests

# 测试登录功能
def test_login():
    # 应用程序URL
    base_url = 'http://127.0.0.1:5000'
    
    # 登录数据 - 使用已知的管理员账号
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    # 创建会话
    session = requests.Session()
    
    try:
        # 发送登录请求
        response = session.post(f'{base_url}/login', data=login_data, allow_redirects=True)
        
        print(f'登录请求状态码: {response.status_code}')
        
        # 检查是否成功登录并重定向到主界面
        if response.status_code == 200 and 'main_interface' in response.url:
            print('登录成功！已重定向到主界面。')
            print('页面内容包含以下关键文本:')
            
            # 检查页面内容中是否包含仪表盘相关文本
            if '肿瘤病例管理系统' in response.text:
                print('✓ 页面包含系统名称')
            if '主界面' in response.text:
                print('✓ 页面包含"主界面"链接')
            if '病人管理' in response.text:
                print('✓ 页面包含"病人管理"链接')
                
            return True
        else:
            print('登录失败或未正确重定向到主界面。')
            print(f'重定向URL: {response.url}')
            print('页面内容前500字符:')
            print(response.text[:500])
            return False
            
    except Exception as e:
        print(f'测试过程中发生错误: {e}')
        return False

if __name__ == '__main__':
    print('开始测试登录功能...')
    test_login()
