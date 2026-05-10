#!/usr/bin/env python3
"""验证 /users 和 /reports/summary 等端点可通过 JWT 正常访问"""

import requests

BASE_URL = "http://localhost:8000"


def main():
    # 1. 登录 admin
    r = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ 登录成功, token={token[:30]}...")

    # 2. 测试关键端点
    endpoints = [
        ("GET", "/users?limit=10"),
        ("GET", "/reports/summary"),
        ("GET", "/reports/booths"),
        ("GET", "/leaderboard/revenue?limit=5"),
        ("GET", "/booths?status=active"),
        ("GET", "/events"),
        ("GET", "/participants?limit=5"),
        ("GET", "/products?booth_id=18"),
    ]

    for method, path in endpoints:
        try:
            r = requests.request(method, f"{BASE_URL}{path}", headers=headers, timeout=5)
            status_icon = "✅" if r.status_code < 400 else "❌"
            print(f"{status_icon} {method} {path:40s} → {r.status_code}")
            if r.status_code >= 400:
                print(f"    Body: {r.text[:150]}")
        except Exception as e:
            print(f"❌ {method} {path:40s} → Exception: {e}")


if __name__ == "__main__":
    main()
