#!/usr/bin/env python3
"""
测试报表中心所有功能
"""

import requests
import json
from typing import Optional

# API 基础 URL
BASE_URL = "http://localhost:8000"

# 测试用户凭证
TEST_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"
}

def login() -> Optional[str]:
    """登录并获取 token"""
    print("🔐 正在登录...")
    response = requests.post(
        f"{BASE_URL}/login",
        json=TEST_CREDENTIALS
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✅ 登录成功！Token: {token[:20]}...")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None

def test_summary_report(token: str):
    """测试总览统计报表"""
    print("\n📊 测试总览统计报表...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/reports/summary",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 总览统计报表获取成功！")
        print(f"   - 总发放额度: ¥{data['total_issued']:.2f}")
        print(f"   - 总充值额: ¥{data['total_recharged']:.2f}")
        print(f"   - 总消费额: ¥{data['total_consumed']:.2f}")
        print(f"   - 总退款额: ¥{data['total_refunded']:.2f}")
        print(f"   - 净消费额: ¥{data['net_consumed']:.2f}")
        print(f"   - 总交易笔数: {data['total_transactions']}")
        print(f"   - 参与者数量: {data['participant_count']}")
        print(f"   - 摊位数量: {data['booth_count']}")
        return True
    else:
        print(f"❌ 获取失败: {response.status_code} - {response.text}")
        return False

def test_booth_report(token: str):
    """测试摊位报表"""
    print("\n🏪 测试摊位报表...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/reports/booths",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 摊位报表获取成功！共 {data['total_count']} 个摊位")
        if data['booths']:
            booth = data['booths'][0]
            print(f"   示例摊位: {booth['booth_name']}")
            print(f"   - 营业额: ¥{booth['revenue']:.2f}")
            print(f"   - 净收入: ¥{booth['net_revenue']:.2f}")
            print(f"   - 利润: ¥{booth['profit']:.2f}")
            print(f"   - 利润率: {booth['profit_margin']}%")
        return True
    else:
        print(f"❌ 获取失败: {response.status_code} - {response.text}")
        return False

def test_product_report(token: str):
    """测试商品报表"""
    print("\n🛍️ 测试商品报表...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/reports/products",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 商品报表获取成功！共 {data['total_count']} 个商品")
        if data['products']:
            product = data['products'][0]
            print(f"   示例商品: {product['product_name']}")
            print(f"   - 销量: {product['sales_quantity']} 件")
            print(f"   - 收入: ¥{product['revenue']:.2f}")
            print(f"   - 利润: ¥{product['profit']:.2f}")
        return True
    else:
        print(f"❌ 获取失败: {response.status_code} - {response.text}")
        return False

def test_booth_leaderboard(token: str):
    """测试摊位排行榜"""
    print("\n🏆 测试摊位排行榜...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试营业额排行榜
    print("   📈 营业额排行榜...")
    response = requests.get(
        f"{BASE_URL}/leaderboard/revenue?limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 营业额排行榜获取成功！TOP {len(data['leaderboard'])}")
        for item in data['leaderboard'][:3]:
            print(f"      {item['rank']}. {item['booth_name']} - ¥{item['value']:.2f}")
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        return False
    
    # 测试利润排行榜
    print("   💰 利润排行榜...")
    response = requests.get(
        f"{BASE_URL}/leaderboard/profit?limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 利润排行榜获取成功！TOP {len(data['leaderboard'])}")
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        return False
    
    # 测试利润率排行榜
    print("   📊 利润率排行榜...")
    response = requests.get(
        f"{BASE_URL}/leaderboard/roi?limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 利润率排行榜获取成功！TOP {len(data['leaderboard'])}")
        return True
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        return False

def test_product_leaderboard(token: str):
    """测试商品排行榜"""
    print("\n🥇 测试商品排行榜...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试销量排行榜
    print("   📦 销量排行榜...")
    response = requests.get(
        f"{BASE_URL}/leaderboard/products?metric=sales&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 销量排行榜获取成功！TOP {len(data['leaderboard'])}")
        for item in data['leaderboard'][:3]:
            print(f"      {item['rank']}. {item['product_name']} - {item['value']} 件")
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        return False
    
    # 测试收入排行榜
    print("   💵 收入排行榜...")
    response = requests.get(
        f"{BASE_URL}/leaderboard/products?metric=revenue&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 收入排行榜获取成功！TOP {len(data['leaderboard'])}")
        return True
    else:
        print(f"   ❌ 获取失败: {response.status_code}")
        return False

def test_audit_logs(token: str):
    """测试异常审计日志"""
    print("\n🔍 测试异常审计日志...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/reports/audit-logs?flag_type=all&limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 异常审计日志获取成功！共 {data['total_count']} 条记录")
        if data['logs']:
            log = data['logs'][0]
            print(f"   示例记录:")
            print(f"   - 交易ID: {log['transaction_id']}")
            print(f"   - 交易类型: {log['transaction_type']}")
            print(f"   - 金额: ¥{log['amount']:.2f}")
            print(f"   - 异常标记: {log['flag_reason']}")
        return True
    else:
        print(f"❌ 获取失败: {response.status_code} - {response.text}")
        return False

def test_export(token: str):
    """测试报表导出"""
    print("\n📥 测试报表导出...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试导出总览报表
    print("   📊 导出总览报表...")
    response = requests.get(
        f"{BASE_URL}/reports/export/excel?report_type=summary",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"   ✅ 总览报表导出成功！文件大小: {len(response.content)} 字节")
    else:
        print(f"   ❌ 导出失败: {response.status_code}")
        return False
    
    # 测试导出摊位报表
    print("   🏪 导出摊位报表...")
    response = requests.get(
        f"{BASE_URL}/reports/export/excel?report_type=booths",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"   ✅ 摊位报表导出成功！文件大小: {len(response.content)} 字节")
        return True
    else:
        print(f"   ❌ 导出失败: {response.status_code}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 开始测试报表中心所有功能")
    print("=" * 60)
    
    # 登录
    token = login()
    if not token:
        print("\n❌ 登录失败，无法继续测试")
        return
    
    # 运行所有测试
    tests = [
        ("总览统计报表", lambda: test_summary_report(token)),
        ("摊位报表", lambda: test_booth_report(token)),
        ("商品报表", lambda: test_product_report(token)),
        ("摊位排行榜", lambda: test_booth_leaderboard(token)),
        ("商品排行榜", lambda: test_product_leaderboard(token)),
        ("异常审计日志", lambda: test_audit_logs(token)),
        ("报表导出", lambda: test_export(token)),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 {name} 时发生异常: {str(e)}")
            results.append((name, False))
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！报表中心功能完整！")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，请检查")

if __name__ == "__main__":
    main()
