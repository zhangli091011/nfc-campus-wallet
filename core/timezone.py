"""
时区配置 - 统一使用 UTC+8（中国标准时间）

所有后端时间统一使用 Asia/Shanghai (UTC+8)。
"""

from datetime import timezone, timedelta

# UTC+8 时区（中国标准时间）
CST = timezone(timedelta(hours=8))

def now():
    """获取当前 UTC+8 时间"""
    from datetime import datetime
    return datetime.now(CST)
