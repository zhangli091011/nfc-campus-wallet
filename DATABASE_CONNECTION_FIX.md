# 数据库连接问题修复指南

## 问题描述

```
sqlalchemy.exc.UnboundExecutionError: Could not locate a bind configured on mapper Mapper[User(users)]
```

## 问题原因

### 1. **数据库连接池耗尽**
- 长时间运行后，连接没有正确释放
- 连接泄漏导致无法创建新连接

### 2. **数据库连接超时**
- MySQL 默认 `wait_timeout` 为 8 小时
- 空闲连接被数据库服务器关闭
- 应用尝试使用已关闭的连接

### 3. **Session 生命周期管理**
- FastAPI 依赖注入的 Session 没有正确关闭
- 异步操作中 Session 被提前释放

### 4. **并发请求竞态条件**
- 多个请求同时访问导致 Session 状态混乱

---

## 立即解决方案

### 重启后端服务

```bash
# 方法 1：使用重启脚本
cd /home/ubuntu/nfc-campus-wallet
bash restart_backend.sh

# 方法 2：手动重启
pkill -f "uvicorn app.main:app"
sleep 2
source .venv/bin/activate
nohup python start_server.py > backend.log 2>&1 &

# 方法 3：systemd 服务
sudo systemctl restart nfc-wallet
```

### 验证服务状态

```bash
# 检查进程
ps aux | grep uvicorn

# 测试 API
curl http://localhost:8000/docs

# 查看日志
tail -f backend.log
```

---

## 长期解决方案

### 1. 优化数据库连接池配置

编辑 `.env` 文件，添加或修改以下配置：

```bash
# 数据库连接池配置
DATABASE_POOL_SIZE=10              # 连接池大小（默认 5）
DATABASE_MAX_OVERFLOW=20           # 最大溢出连接（默认 10）
DATABASE_POOL_TIMEOUT=30           # 获取连接超时（秒）
DATABASE_POOL_RECYCLE=3600         # 连接回收时间（秒，1小时）

# 推荐配置（根据并发量调整）
# 低并发（<10 用户）：POOL_SIZE=5, MAX_OVERFLOW=10
# 中并发（10-50 用户）：POOL_SIZE=10, MAX_OVERFLOW=20
# 高并发（>50 用户）：POOL_SIZE=20, MAX_OVERFLOW=40
```

### 2. 优化 MySQL 配置

编辑 MySQL 配置文件 `/etc/mysql/mysql.conf.d/mysqld.cnf`：

```ini
[mysqld]
# 连接超时设置
wait_timeout = 28800              # 8小时（默认）
interactive_timeout = 28800       # 8小时（默认）

# 最大连接数
max_connections = 200             # 根据服务器资源调整

# 连接池相关
max_connect_errors = 100
```

重启 MySQL：
```bash
sudo systemctl restart mysql
```

### 3. 添加连接健康检查

修改 `core/database.py`，确保 `pool_pre_ping=True`：

```python
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # ✅ 使用前检查连接是否有效
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=3600,  # ✅ 每小时回收连接
    echo=False
)
```

### 4. 添加数据库连接监控

创建监控脚本 `monitor_db_connections.py`：

```python
from sqlalchemy import text
from core.database import engine

def check_db_connections():
    """检查数据库连接池状态"""
    with engine.connect() as conn:
        # 检查当前连接数
        result = conn.execute(text("SHOW STATUS LIKE 'Threads_connected'"))
        threads = result.fetchone()
        print(f"当前连接数: {threads[1]}")
        
        # 检查最大连接数
        result = conn.execute(text("SHOW VARIABLES LIKE 'max_connections'"))
        max_conn = result.fetchone()
        print(f"最大连接数: {max_conn[1]}")
        
        # 检查连接池状态
        pool = engine.pool
        print(f"连接池大小: {pool.size()}")
        print(f"已签出连接: {pool.checkedout()}")
        print(f"溢出连接: {pool.overflow()}")

if __name__ == "__main__":
    check_db_connections()
```

### 5. 使用进程管理器（推荐）

#### 方案 A：使用 systemd（已配置）

```bash
# 启用自动重启
sudo systemctl enable nfc-wallet

# 查看状态
sudo systemctl status nfc-wallet

# 查看日志
sudo journalctl -u nfc-wallet -f
```

#### 方案 B：使用 Supervisor

安装 Supervisor：
```bash
sudo apt install supervisor
```

创建配置 `/etc/supervisor/conf.d/nfc-wallet.conf`：
```ini
[program:nfc-wallet]
command=/home/ubuntu/nfc-campus-wallet/.venv/bin/python start_server.py
directory=/home/ubuntu/nfc-campus-wallet
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ubuntu/nfc-campus-wallet/logs/supervisor.log
environment=PATH="/home/ubuntu/nfc-campus-wallet/.venv/bin"
```

启动：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nfc-wallet
```

### 6. 添加健康检查端点

在 `app/main.py` 添加：

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """健康检查端点"""
    try:
        # 测试数据库连接
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

### 7. 定期重启服务（临时方案）

添加 cron 任务，每天凌晨重启：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 3 点重启）
0 3 * * * /home/ubuntu/nfc-campus-wallet/restart_backend.sh >> /home/ubuntu/nfc-campus-wallet/logs/restart.log 2>&1
```

---

## 预防措施

### 1. 代码层面

✅ **确保 Session 正确关闭**
```python
# 使用依赖注入（推荐）
def endpoint(db: Session = Depends(get_db)):
    # db 会自动关闭
    pass

# 手动管理（不推荐）
db = SessionLocal()
try:
    # 操作数据库
    pass
finally:
    db.close()  # 必须关闭
```

✅ **避免长时间持有 Session**
```python
# ❌ 错误：长时间持有
db = SessionLocal()
time.sleep(3600)  # 持有 1 小时
db.query(User).all()

# ✅ 正确：用完即关
db = SessionLocal()
users = db.query(User).all()
db.close()
```

✅ **使用连接池而不是创建新连接**
```python
# ✅ 使用 SessionLocal（连接池）
db = SessionLocal()

# ❌ 不要直接创建 engine
engine = create_engine(...)  # 每次都创建新引擎
```

### 2. 监控告警

设置监控告警：
- 数据库连接数超过阈值
- API 响应时间异常
- 500 错误率上升

### 3. 日志记录

启用详细日志：
```python
# 在 core/database.py
engine = create_engine(
    settings.database_url,
    echo=True,  # 记录所有 SQL 查询
    ...
)
```

---

## 故障排查步骤

### 1. 检查数据库连接

```bash
# 登录 MySQL
mysql -u your_user -p

# 查看当前连接
SHOW PROCESSLIST;

# 查看连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW VARIABLES LIKE 'max_connections';
```

### 2. 检查应用日志

```bash
# 查看后端日志
tail -100 backend.log

# 查看系统日志
sudo journalctl -u nfc-wallet -n 100
```

### 3. 检查系统资源

```bash
# 检查内存
free -h

# 检查磁盘
df -h

# 检查进程
ps aux | grep python
```

### 4. 测试数据库连接

```python
# test_db_connection.py
from core.database import init_database, get_db

init_database()
db = next(get_db())
print("✅ 数据库连接成功")
db.close()
```

---

## 常见问题

### Q1: 重启后还是出现同样错误？
**A:** 检查数据库服务是否正常运行，MySQL 连接数是否达到上限。

### Q2: 如何查看当前连接池状态？
**A:** 使用上面的 `monitor_db_connections.py` 脚本。

### Q3: 需要增加连接池大小吗？
**A:** 根据并发用户数调整：
- 10 用户以下：POOL_SIZE=5
- 10-50 用户：POOL_SIZE=10
- 50+ 用户：POOL_SIZE=20

### Q4: 为什么会突然出现这个问题？
**A:** 可能原因：
- 数据库连接超时
- 并发请求突然增加
- 内存不足导致连接池异常
- 代码中有连接泄漏

---

## 总结

**立即操作：**
1. ✅ 重启后端服务
2. ✅ 验证服务正常

**短期优化：**
1. ✅ 优化连接池配置
2. ✅ 添加健康检查
3. ✅ 启用自动重启

**长期方案：**
1. ✅ 使用进程管理器
2. ✅ 添加监控告警
3. ✅ 定期审查代码

---

## 参考资料

- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [FastAPI Database Guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [MySQL Connection Management](https://dev.mysql.com/doc/refman/8.0/en/connection-management.html)
