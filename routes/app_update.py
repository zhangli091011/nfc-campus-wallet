"""
App OTA Update routes.

提供 APK 上传和版本检查接口，支持 Android 端 OTA 更新。
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging
import json
from datetime import datetime, timezone

from core.database import get_db
from core.security import get_current_user, RoleChecker
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/app-update", tags=["App Update"])

# APK 存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "apk")
VERSION_FILE = os.path.join(UPLOAD_DIR, "version.json")


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_version_info() -> dict:
    """读取当前版本信息"""
    if not os.path.exists(VERSION_FILE):
        return None
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _save_version_info(info: dict):
    """保存版本信息"""
    _ensure_upload_dir()
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


@router.get("/check")
async def check_update(
    current_version: Optional[str] = None,
    version_code: Optional[int] = None,
):
    """
    检查是否有新版本可用。

    Query Parameters:
        - current_version: 当前版本名称（如 "1.0"）
        - version_code: 当前版本号（如 1）

    Returns:
        {
            "has_update": true/false,
            "version_name": "1.1",
            "version_code": 2,
            "download_url": "/app-update/download",
            "release_notes": "修复了xxx",
            "file_size": 12345678,
            "uploaded_at": "2026-05-12T10:00:00Z"
        }
    """
    version_info = _get_version_info()
    if not version_info:
        return {"has_update": False}

    has_update = False
    if version_code is not None:
        has_update = version_info.get("version_code", 0) > version_code
    elif current_version is not None:
        has_update = version_info.get("version_name", "") != current_version
    else:
        has_update = True  # 没提供版本信息，返回最新版本

    if not has_update:
        return {"has_update": False}

    return {
        "has_update": True,
        "version_name": version_info.get("version_name", ""),
        "version_code": version_info.get("version_code", 0),
        "download_url": "/app-update/download",
        "release_notes": version_info.get("release_notes", ""),
        "file_size": version_info.get("file_size", 0),
        "uploaded_at": version_info.get("uploaded_at", ""),
        "force_update": version_info.get("force_update", False),
    }


@router.get("/download")
async def download_apk():
    """下载最新 APK 文件"""
    version_info = _get_version_info()
    if not version_info or not version_info.get("filename"):
        raise HTTPException(status_code=404, detail="没有可用的 APK 文件")

    file_path = os.path.join(UPLOAD_DIR, version_info["filename"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="APK 文件不存在")

    return FileResponse(
        path=file_path,
        filename=version_info["filename"],
        media_type="application/vnd.android.package-archive"
    )


@router.post("/upload")
async def upload_apk(
    file: UploadFile = File(...),
    version_name: str = Form(...),
    version_code: int = Form(...),
    release_notes: str = Form(""),
    force_update: bool = Form(False),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin"])),
):
    """
    上传新版本 APK（仅 super_admin）。

    Form Data:
        - file: APK 文件
        - version_name: 版本名称（如 "1.1"）
        - version_code: 版本号（如 2）
        - release_notes: 更新说明
        - force_update: 是否强制更新
    """
    if not file.filename.endswith('.apk'):
        raise HTTPException(status_code=400, detail="只能上传 .apk 文件")

    _ensure_upload_dir()

    # 保存文件
    filename = f"nfc-wallet-v{version_name}.apk"
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    file_size = len(content)

    with open(file_path, 'wb') as f:
        f.write(content)

    # 保存版本信息
    version_info = {
        "version_name": version_name,
        "version_code": version_code,
        "release_notes": release_notes,
        "force_update": force_update,
        "filename": filename,
        "file_size": file_size,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": current_user.username,
    }
    _save_version_info(version_info)

    logger.info(
        f"APK uploaded: v{version_name} (code={version_code}), "
        f"size={file_size}, by={current_user.username}"
    )

    return {
        "success": True,
        "message": f"APK v{version_name} 上传成功",
        "version_info": version_info,
    }


@router.get("/info")
async def get_current_version_info(
    current_user: User = Depends(get_current_user),
):
    """获取当前发布的版本信息（需登录）"""
    version_info = _get_version_info()
    if not version_info:
        return {"has_version": False}
    return {"has_version": True, **version_info}
