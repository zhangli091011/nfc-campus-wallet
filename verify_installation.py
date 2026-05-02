"""
Installation Verification Script.

验证所有依赖是否正确安装。
"""

import sys

def verify_installation():
    """验证安装"""
    print("=" * 60)
    print("NFC Campus Event System - Installation Verification")
    print("=" * 60)
    print()
    
    errors = []
    
    # 检查 Python 版本
    print("📋 Checking Python version...")
    python_version = sys.version_info
    if python_version >= (3, 9):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.9+)")
        errors.append("Python version too old")
    print()
    
    # 检查核心依赖
    print("📦 Checking core dependencies...")
    
    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pymysql", "PyMySQL"),
        ("cryptography", "Cryptography"),
        ("pydantic", "Pydantic"),
        ("jwt", "PyJWT"),
        ("bcrypt", "bcrypt"),
        ("openpyxl", "openpyxl"),
        ("pytest", "pytest"),
        ("hypothesis", "Hypothesis"),
    ]
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except ImportError:
            print(f"❌ {display_name} - NOT INSTALLED")
            errors.append(f"{display_name} not installed")
    
    print()
    
    # 检查项目模块
    print("🔍 Checking project modules...")
    
    project_modules = [
        ("core.config", "Core Configuration"),
        ("core.database", "Core Database"),
        ("core.security", "Core Security"),
        ("core.exceptions", "Core Exceptions"),
        ("models.user", "User Model"),
        ("models.event", "Event Model"),
        ("models.booth", "Booth Model"),
        ("models.cash_reconciliation", "Cash Reconciliation Model"),
        ("services.auth_service", "Auth Service"),
        ("services.event_service", "Event Service"),
        ("services.cash_reconciliation_service", "Cash Reconciliation Service"),
        ("services.export_service", "Export Service"),
    ]
    
    for module_name, display_name in project_modules:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except ImportError as e:
            print(f"❌ {display_name} - {str(e)}")
            errors.append(f"{display_name} import failed")
    
    print()
    
    # 总结
    print("=" * 60)
    if errors:
        print("❌ Installation verification FAILED")
        print()
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("Please fix the errors and run this script again.")
        return False
    else:
        print("✅ Installation verification PASSED")
        print()
        print("All dependencies and modules are correctly installed!")
        print()
        print("Next steps:")
        print("  1. Configure .env file")
        print("  2. Run database migration: python scripts/migrate_cash_reconciliation.py")
        print("  3. Create admin user: python scripts/create_admin.py")
        print("  4. Start server: python -m uvicorn app.main:app --reload")
        return True


if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)
