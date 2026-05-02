#!/usr/bin/env python3
"""
测试余额查询 API

测试事件模式的余额查询是否正常工作
"""

import requests
import sys

# API 配置
API_BASE_URL = "http://localhost:8000"

def test_balance_query():
    """测试余额查询"""
    print("=" * 60)
    print("测试余额查询 API")
    print("=" * 60)
    
    # 测试参数
    event_id = 2
    card_uid = "2BC8694C"
    
    # 构建请求 URL
    url = f"{API_BASE_URL}/balance"
    params = {
        "event_id": event_id,
        "card_uid": card_uid
    }
    
    print(f"\n📡 发送请求:")
    print(f"URL: {url}")
    print(f"参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"\n📥 响应:")
        print(f"状态码: {response.status_code}")
        print(f"响应体: {response.json()}")
        
        if response.status_code == 200:
            print("\n✅ 测试成功！")
            return True
        else:
            print(f"\n❌ 测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return False


if __name__ == "__main__":
    success = test_balance_query()
    sys.exit(0 if success else 1)
