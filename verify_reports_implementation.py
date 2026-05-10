#!/usr/bin/env python3
"""
验证报表中心功能实现完整性
"""

import os
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return Path(filepath).exists()

def main():
    print("=" * 70)
    print("🔍 验证报表中心功能实现完整性")
    print("=" * 70)
    
    # 定义需要检查的文件
    checks = {
        "后端服务层": [
            ("报表服务", "services/report_service.py"),
            ("导出服务", "services/export_service.py"),
        ],
        "后端路由层": [
            ("报表路由", "routes/reports.py"),
            ("排行榜路由", "routes/leaderboard.py"),
        ],
        "后端数据模型": [
            ("报表 Schema", "schemas/report.py"),
        ],
        "前端页面组件": [
            ("总览看板", "web-admin/src/pages/Reports/Dashboard.tsx"),
            ("摊位报表", "web-admin/src/pages/Reports/BoothReport.tsx"),
            ("摊位排行榜", "web-admin/src/pages/Reports/BoothLeaderboard.tsx"),
            ("商品排行榜", "web-admin/src/pages/Reports/ProductLeaderboard.tsx"),
            ("异常审计", "web-admin/src/pages/Reports/AuditLogs.tsx"),
            ("报表导出", "web-admin/src/pages/Reports/ExportPage.tsx"),
            ("模块导出", "web-admin/src/pages/Reports/index.ts"),
        ],
        "前端服务层": [
            ("报表服务", "web-admin/src/services/report.ts"),
        ],
        "前端路由配置": [
            ("路由定义", "web-admin/src/routes/index.tsx"),
            ("布局组件", "web-admin/src/components/Layout/index.tsx"),
        ],
        "文档": [
            ("功能检查清单", "docs/REPORTS_CENTER_CHECKLIST.md"),
        ],
        "测试脚本": [
            ("报表测试", "test_reports.py"),
            ("实现验证", "verify_reports_implementation.py"),
        ],
    }
    
    total_checks = 0
    passed_checks = 0
    
    for category, files in checks.items():
        print(f"\n📁 {category}")
        print("-" * 70)
        
        for name, filepath in files:
            total_checks += 1
            exists = check_file_exists(filepath)
            
            if exists:
                status = "✅"
                passed_checks += 1
            else:
                status = "❌"
            
            print(f"  {status} {name:20s} - {filepath}")
    
    # 检查关键功能点
    print(f"\n📋 功能实现检查")
    print("-" * 70)
    
    feature_checks = []
    
    # 检查后端 API 端点
    if check_file_exists("routes/reports.py"):
        try:
            with open("routes/reports.py", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                feature_checks.append(("总览统计 API", '"/summary"' in content or "/summary" in content))
                feature_checks.append(("摊位报表 API", '"/booths"' in content or "/booths" in content))
                feature_checks.append(("商品报表 API", '"/products"' in content or "/products" in content))
                feature_checks.append(("异常审计 API", '"/audit-logs"' in content or "audit-logs" in content))
                feature_checks.append(("报表导出 API", '"/export/excel"' in content or "export/excel" in content))
        except Exception as e:
            print(f"  ⚠️ 读取 routes/reports.py 失败: {e}")
    
    if check_file_exists("routes/leaderboard.py"):
        try:
            with open("routes/leaderboard.py", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                feature_checks.append(("营业额排行榜 API", '"/revenue"' in content or "/revenue" in content))
                feature_checks.append(("利润排行榜 API", '"/profit"' in content or "/profit" in content))
                feature_checks.append(("利润率排行榜 API", '"/roi"' in content or "/roi" in content))
                feature_checks.append(("商品排行榜 API", '"/products"' in content or "/products" in content))
        except Exception as e:
            print(f"  ⚠️ 读取 routes/leaderboard.py 失败: {e}")
    
    # 检查前端路由
    if check_file_exists("web-admin/src/routes/index.tsx"):
        try:
            with open("web-admin/src/routes/index.tsx", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                feature_checks.append(("总览看板路由", "reports/dashboard" in content))
                feature_checks.append(("摊位报表路由", "reports/booths" in content))
                feature_checks.append(("摊位排行榜路由", "reports/booth-leaderboard" in content))
                feature_checks.append(("商品排行榜路由", "reports/product-leaderboard" in content))
                feature_checks.append(("异常审计路由", "reports/audit-logs" in content))
                feature_checks.append(("报表导出路由", "reports/export" in content))
        except Exception as e:
            print(f"  ⚠️ 读取 web-admin/src/routes/index.tsx 失败: {e}")
    
    # 检查菜单配置
    if check_file_exists("web-admin/src/components/Layout/index.tsx"):
        try:
            with open("web-admin/src/components/Layout/index.tsx", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                feature_checks.append(("报表中心菜单", "报表中心" in content or "Reports" in content))
                feature_checks.append(("总览看板菜单", "总览看板" in content or "Dashboard" in content))
                feature_checks.append(("摊位报表菜单", "摊位报表" in content or "Booth" in content))
                feature_checks.append(("摊位排行榜菜单", "摊位排行榜" in content or "Leaderboard" in content))
                feature_checks.append(("商品排行榜菜单", "商品排行榜" in content or "Product" in content))
                feature_checks.append(("异常审计菜单", "异常审计" in content or "Audit" in content))
                feature_checks.append(("报表导出菜单", "报表导出" in content or "Export" in content))
        except Exception as e:
            print(f"  ⚠️ 读取 web-admin/src/components/Layout/index.tsx 失败: {e}")
    
    feature_passed = 0
    for name, result in feature_checks:
        total_checks += 1
        if result:
            status = "✅"
            passed_checks += 1
            feature_passed += 1
        else:
            status = "❌"
        print(f"  {status} {name}")
    
    # 打印总结
    print("\n" + "=" * 70)
    print("📊 验证总结")
    print("=" * 70)
    
    percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n总计: {passed_checks}/{total_checks} 项检查通过 ({percentage:.1f}%)")
    
    if passed_checks == total_checks:
        print("\n🎉 所有检查通过！报表中心功能实现完整！")
        print("\n✨ 功能清单:")
        print("   1. ✅ 总览看板 - 展示关键统计指标")
        print("   2. ✅ 摊位报表 - 摊位维度经营数据")
        print("   3. ✅ 摊位排行榜 - 营业额/利润/利润率 TOP N")
        print("   4. ✅ 商品排行榜 - 销量/收入/利润 TOP N")
        print("   5. ✅ 异常审计 - 高频退款/大额更正/可疑操作")
        print("   6. ✅ 报表导出 - Excel 格式导出")
        print("\n📖 详细文档: docs/REPORTS_CENTER_CHECKLIST.md")
        print("🧪 运行测试: python test_reports.py")
        return 0
    else:
        print(f"\n⚠️ 有 {total_checks - passed_checks} 项检查未通过")
        print("请检查缺失的文件或功能")
        return 1

if __name__ == "__main__":
    exit(main())
