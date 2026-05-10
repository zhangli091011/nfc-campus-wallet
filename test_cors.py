#!/usr/bin/env python3
"""
测试CORS配置
"""

import requests

def test_cors():
    """测试CORS响应头"""
    print("🔍 测试CORS配置...")
    print("=" * 60)
    
    # 测试健康检查端点
    url = "http://localhost:8000/health"
    headers = {
        "Origin": "http://localhost:3000"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"✅ 请求成功: {response.status_code}")
        print(f"\n📋 响应头:")
        
        cors_headers = {
            k: v for k, v in response.headers.items()
            if 'access-control' in k.lower() or 'cors' in k.lower()
        }
        
        if cors_headers:
            for key, value in cors_headers.items():
                print(f"  {key}: {value}")
        else:
            print("  ⚠️ 没有找到CORS相关的响应头")
        
        print(f"\n📄 响应内容: {response.text}")
        
        # 检查必要的CORS头
        required_headers = [
            'access-control-allow-origin',
            'access-control-allow-credentials',
            'access-control-allow-methods',
            'access-control-allow-headers'
        ]
        
        print(f"\n🔍 CORS头检查:")
        for header in required_headers:
            if header in [k.lower() for k in response.headers.keys()]:
                print(f"  ✅ {header}")
            else:
                print(f"  ❌ {header} - 缺失")
        
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False
    
    # 测试报表端点
    print(f"\n" + "=" * 60)
    print("🔍 测试报表端点（需要认证）...")
    
    url = "http://localhost:8000/reports/summary"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ 端点存在（需要认证）")
        elif response.status_code == 200:
            print("✅ 端点正常工作")
        else:
            print(f"⚠️ 意外状态码: {response.status_code}")
        
        # 检查CORS头
        cors_headers = {
            k: v for k, v in response.headers.items()
            if 'access-control' in k.lower()
        }
        
        if cors_headers:
            print("✅ CORS头存在:")
            for key, value in cors_headers.items():
                print(f"  {key}: {value}")
        else:
            print("❌ CORS头缺失")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
    
    # 测试OPTIONS预检请求
    print(f"\n" + "=" * 60)
    print("🔍 测试OPTIONS预检请求...")
    
    url = "http://localhost:8000/reports/summary"
    
    try:
        response = requests.options(
            url,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            }
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OPTIONS请求成功")
        else:
            print(f"⚠️ OPTIONS请求状态码: {response.status_code}")
        
        # 检查预检响应头
        cors_headers = {
            k: v for k, v in response.headers.items()
            if 'access-control' in k.lower()
        }
        
        if cors_headers:
            print("✅ CORS预检响应头:")
            for key, value in cors_headers.items():
                print(f"  {key}: {value}")
        else:
            print("❌ CORS预检响应头缺失")
            
    except Exception as e:
        print(f"❌ OPTIONS请求失败: {str(e)}")
    
    print(f"\n" + "=" * 60)
    print("📋 总结")
    print("=" * 60)
    print("✅ 如果所有测试通过，CORS配置正确")
    print("❌ 如果有测试失败，请重启后端服务后再试")
    print("\n💡 重启命令: python start_server.py")

if __name__ == "__main__":
    test_cors()
