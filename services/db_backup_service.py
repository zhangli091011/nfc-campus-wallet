"""
Database Backup Service - 数据库全量备份服务

每5分钟执行一次 mysqldump 全量备份，保留最近的备份文件。
备份文件存储在项目根目录的 backups/ 文件夹中。
"""

import os
import subprocess
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# 备份配置
BACKUP_INTERVAL_SECONDS = 5 * 60  # 5分钟
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
MAX_BACKUP_FILES = 50  # 最多保留50个备份文件（约4小时）


class DatabaseBackupService:
    """数据库定时全量备份服务"""

    def __init__(self):
        self._timer: threading.Timer | None = None
        self._running = False
        self._lock = threading.Lock()

        # 从环境变量读取数据库配置
        self.db_host = os.getenv("DATABASE_HOST", "localhost")
        self.db_port = os.getenv("DATABASE_PORT", "3306")
        self.db_name = os.getenv("DATABASE_NAME", "nfc")
        self.db_user = os.getenv("DATABASE_USER", "")
        self.db_password = os.getenv("DATABASE_PASSWORD", "")

        # 确保备份目录存在
        os.makedirs(BACKUP_DIR, exist_ok=True)

    def start(self):
        """启动定时备份"""
        with self._lock:
            if self._running:
                logger.warning("Database backup service is already running")
                return
            self._running = True

        logger.info(
            f"Database backup service started: interval={BACKUP_INTERVAL_SECONDS}s, "
            f"backup_dir={BACKUP_DIR}, max_files={MAX_BACKUP_FILES}"
        )
        self._schedule_next()

    def stop(self):
        """停止定时备份"""
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
        logger.info("Database backup service stopped")

    def _schedule_next(self):
        """调度下一次备份"""
        if not self._running:
            return
        self._timer = threading.Timer(BACKUP_INTERVAL_SECONDS, self._run_backup)
        self._timer.daemon = True
        self._timer.start()

    def _run_backup(self):
        """执行一次全量备份"""
        try:
            self._do_backup()
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
        finally:
            self._schedule_next()

    def _do_backup(self):
        """执行 mysqldump 全量备份"""
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"nfc_backup_{timestamp}.sql"
        filepath = os.path.join(BACKUP_DIR, filename)

        cmd = [
            "mysqldump",
            f"--host={self.db_host}",
            f"--port={self.db_port}",
            f"--user={self.db_user}",
            f"--password={self.db_password}",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--quick",
            self.db_name,
        ]

        logger.info(f"Starting database backup: {filename}")

        with open(filepath, "w", encoding="utf-8") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                timeout=120,  # 2分钟超时
            )

        if result.returncode != 0:
            # 备份失败，删除不完整的文件
            stderr_msg = result.stderr.decode("utf-8", errors="replace").strip()
            if os.path.exists(filepath):
                os.remove(filepath)
            raise RuntimeError(f"mysqldump failed (code {result.returncode}): {stderr_msg}")

        file_size = os.path.getsize(filepath)
        logger.info(f"Database backup completed: {filename} ({file_size / 1024:.1f} KB)")

        # 清理旧备份
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        """删除超出保留数量的旧备份文件"""
        try:
            backup_files = sorted(
                Path(BACKUP_DIR).glob("nfc_backup_*.sql"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

            if len(backup_files) > MAX_BACKUP_FILES:
                for old_file in backup_files[MAX_BACKUP_FILES:]:
                    old_file.unlink()
                    logger.info(f"Deleted old backup: {old_file.name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

    def backup_now(self) -> str:
        """手动触发一次备份，返回备份文件路径"""
        self._do_backup()
        # 返回最新的备份文件
        backup_files = sorted(
            Path(BACKUP_DIR).glob("nfc_backup_*.sql"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        return str(backup_files[0]) if backup_files else ""


# 全局单例
_backup_service: DatabaseBackupService | None = None


def get_backup_service() -> DatabaseBackupService:
    """获取备份服务单例"""
    global _backup_service
    if _backup_service is None:
        _backup_service = DatabaseBackupService()
    return _backup_service


def start_backup_service():
    """启动备份服务"""
    service = get_backup_service()
    service.start()


def stop_backup_service():
    """停止备份服务"""
    global _backup_service
    if _backup_service:
        _backup_service.stop()
        _backup_service = None
