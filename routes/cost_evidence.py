"""
Cost Evidence routes for Merchant System.

商户成本凭据上传管理 API 端点。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import logging
import uuid
import os
import shutil

from core.database import get_db
from core.security import get_current_user, RoleChecker
from core.timezone import CST
from models.user import User
from models.booth import Booth
from models.cost_evidence import CostEvidence
from core.exceptions import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merchant/cost-evidence", tags=["merchant-cost-evidence"])

# 允许的文件类型
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'image/bmp', 'image/tiff',
}

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.bmp', '.tiff', '.tif'
}

# 最大文件大小 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# 上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "cost_evidence")

# 凭据类别
VALID_CATEGORIES = {'material', 'logistics', 'labor', 'rent', 'other'}


def ensure_upload_dir():
    """确保上传目录存在"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    _, ext = os.path.splitext(filename)
    return ext.lower()


@router.post("", status_code=201)
async def upload_cost_evidence(
    file: UploadFile = File(..., description="凭据文件（图片或PDF）"),
    category: str = Form(default="other", description="凭据类别: material/logistics/labor/rent/other"),
    amount: Optional[float] = Form(default=None, description="凭据金额（元）"),
    description: Optional[str] = Form(default=None, description="凭据描述/备注"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    上传成本凭据。

    商户可以上传成本凭据（收据、发票照片等），支持图片和PDF格式。

    需要商户角色认证。

    Form Data:
        - file: 凭据文件（必填，支持 jpg/png/gif/webp/pdf，最大10MB）
        - category: 凭据类别（可选，默认 other）
            - material: 原材料
            - logistics: 物流运输
            - labor: 人工费用
            - rent: 租金
            - other: 其他
        - amount: 凭据金额（可选，单位：元）
        - description: 凭据描述/备注（可选，最多500字符）

    Returns:
        上传成功的凭据信息

    Error Responses:
        400: 文件类型不支持 / 文件过大 / 参数错误
        401: 未认证
        403: 权限不足
        404: 商铺不存在
        500: 上传失败
    """
    try:
        # 验证商铺
        booth = db.query(Booth).filter(Booth.id == current_user.booth_id).first()
        if booth is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "MERCHANT_NOT_FOUND", "message": "商铺不存在"}
            )

        # 验证类别
        if category not in VALID_CATEGORIES:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_CATEGORY",
                    "message": f"无效的凭据类别，可选值: {', '.join(VALID_CATEGORIES)}"
                }
            )

        # 验证金额
        if amount is not None and amount < 0:
            return JSONResponse(
                status_code=400,
                content={"error_code": "INVALID_AMOUNT", "message": "金额不能为负数"}
            )

        # 验证描述长度
        if description and len(description) > 500:
            return JSONResponse(
                status_code=400,
                content={"error_code": "DESCRIPTION_TOO_LONG", "message": "描述不能超过500个字符"}
            )

        # 验证文件名
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={"error_code": "INVALID_FILE", "message": "文件名不能为空"}
            )

        # 验证文件扩展名
        ext = get_file_extension(file.filename)
        if ext not in ALLOWED_EXTENSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": f"不支持的文件类型，允许: {', '.join(ALLOWED_EXTENSIONS)}"
                }
            )

        # 验证 MIME 类型
        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_MIME_TYPE",
                    "message": f"不支持的文件格式: {file.content_type}"
                }
            )

        # 读取文件内容并验证大小
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "FILE_TOO_LARGE",
                    "message": f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）"
                }
            )

        if file_size == 0:
            return JSONResponse(
                status_code=400,
                content={"error_code": "EMPTY_FILE", "message": "文件内容为空"}
            )

        # 生成存储文件名
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        
        # 按商铺ID分目录存储
        booth_dir = os.path.join(UPLOAD_DIR, str(booth.id))
        os.makedirs(booth_dir, exist_ok=True)
        
        file_path = os.path.join(booth_dir, stored_filename)

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        # 创建数据库记录
        evidence = CostEvidence(
            booth_id=booth.id,
            uploader_id=current_user.id,
            filename=file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or 'application/octet-stream',
            category=category,
            amount=amount,
            description=description,
            status='pending'
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        logger.info(
            f"Cost evidence uploaded: id={evidence.id}, booth_id={booth.id}, "
            f"filename='{file.filename}', category='{category}', "
            f"size={file_size}, user={current_user.username}"
        )

        return {
            "id": evidence.id,
            "booth_id": evidence.booth_id,
            "filename": evidence.filename,
            "file_size": evidence.file_size,
            "mime_type": evidence.mime_type,
            "category": evidence.category,
            "amount": float(evidence.amount) if evidence.amount else None,
            "description": evidence.description,
            "status": evidence.status,
            "created_at": evidence.created_at.isoformat() if evidence.created_at else None
        }

    except Exception as e:
        logger.error(f"Upload cost evidence error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "UPLOAD_FAILED", "message": "上传凭据失败，请稍后重试"}
        )


@router.get("")
async def list_cost_evidences(
    category: Optional[str] = Query(None, description="按类别筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    获取当前商户的成本凭据列表。

    支持按类别和状态筛选，分页查询。

    需要商户角色认证。

    Query Parameters:
        - category: 按类别筛选（可选）
        - status: 按审核状态筛选（可选）
        - limit: 返回记录数限制（默认50，最大200）
        - offset: 偏移量（默认0）

    Returns:
        凭据列表和总数
    """
    try:
        booth = db.query(Booth).filter(Booth.id == current_user.booth_id).first()
        if booth is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "MERCHANT_NOT_FOUND", "message": "商铺不存在"}
            )

        # 构建查询
        query = db.query(CostEvidence).filter(CostEvidence.booth_id == booth.id)

        if category and category in VALID_CATEGORIES:
            query = query.filter(CostEvidence.category == category)

        if status_filter and status_filter in ('pending', 'approved', 'rejected'):
            query = query.filter(CostEvidence.status == status_filter)

        # 总数
        total_count = query.count()

        # 分页
        evidences = query.order_by(
            CostEvidence.created_at.desc()
        ).limit(limit).offset(offset).all()

        # 构建响应
        evidence_list = []
        for ev in evidences:
            evidence_list.append({
                "id": ev.id,
                "booth_id": ev.booth_id,
                "filename": ev.filename,
                "file_size": ev.file_size,
                "mime_type": ev.mime_type,
                "category": ev.category,
                "amount": float(ev.amount) if ev.amount else None,
                "description": ev.description,
                "status": ev.status,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            })

        return {
            "evidences": evidence_list,
            "total_count": total_count
        }

    except Exception as e:
        logger.error(f"List cost evidences error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取凭据列表失败"}
        )


@router.get("/{evidence_id}")
async def get_cost_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    获取单个成本凭据详情。

    需要商户角色认证，只能查看自己商铺的凭据。
    """
    try:
        evidence = db.query(CostEvidence).filter(
            CostEvidence.id == evidence_id,
            CostEvidence.booth_id == current_user.booth_id
        ).first()

        if evidence is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "EVIDENCE_NOT_FOUND", "message": "凭据不存在"}
            )

        return {
            "id": evidence.id,
            "booth_id": evidence.booth_id,
            "filename": evidence.filename,
            "file_size": evidence.file_size,
            "mime_type": evidence.mime_type,
            "category": evidence.category,
            "amount": float(evidence.amount) if evidence.amount else None,
            "description": evidence.description,
            "status": evidence.status,
            "reviewed_by": evidence.reviewed_by,
            "reviewed_at": evidence.reviewed_at.isoformat() if evidence.reviewed_at else None,
            "created_at": evidence.created_at.isoformat() if evidence.created_at else None
        }

    except Exception as e:
        logger.error(f"Get cost evidence error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取凭据详情失败"}
        )


@router.get("/{evidence_id}/file")
async def download_cost_evidence_file(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant", "super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    下载/查看成本凭据文件。

    商户只能下载自己商铺的凭据，管理员可以下载所有凭据。
    """
    try:
        query = db.query(CostEvidence).filter(CostEvidence.id == evidence_id)

        # 商户只能访问自己的凭据
        if current_user.role == 'merchant':
            query = query.filter(CostEvidence.booth_id == current_user.booth_id)

        evidence = query.first()

        if evidence is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "EVIDENCE_NOT_FOUND", "message": "凭据不存在"}
            )

        if not os.path.exists(evidence.file_path):
            return JSONResponse(
                status_code=404,
                content={"error_code": "FILE_NOT_FOUND", "message": "凭据文件不存在"}
            )

        return FileResponse(
            path=evidence.file_path,
            filename=evidence.filename,
            media_type=evidence.mime_type
        )

    except Exception as e:
        logger.error(f"Download cost evidence error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "下载凭据失败"}
        )


@router.delete("/{evidence_id}", status_code=204)
async def delete_cost_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    删除成本凭据。

    商户只能删除自己商铺的凭据，且只能删除待审核状态的凭据。

    需要商户角色认证。
    """
    try:
        evidence = db.query(CostEvidence).filter(
            CostEvidence.id == evidence_id,
            CostEvidence.booth_id == current_user.booth_id
        ).first()

        if evidence is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "EVIDENCE_NOT_FOUND", "message": "凭据不存在"}
            )

        if evidence.status != 'pending':
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "CANNOT_DELETE",
                    "message": "只能删除待审核状态的凭据"
                }
            )

        # 删除文件
        if os.path.exists(evidence.file_path):
            os.remove(evidence.file_path)

        # 删除数据库记录
        db.delete(evidence)
        db.commit()

        logger.info(
            f"Cost evidence deleted: id={evidence_id}, "
            f"booth_id={current_user.booth_id}, user={current_user.username}"
        )

        return None

    except Exception as e:
        logger.error(f"Delete cost evidence error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "删除凭据失败"}
        )


@router.get("/stats/summary")
async def get_cost_evidence_stats(
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["merchant"])),
    db: Session = Depends(get_db)
):
    """
    获取成本凭据统计摘要。

    返回各类别的凭据数量和总金额。

    需要商户角色认证。
    """
    try:
        from sqlalchemy import func

        booth = db.query(Booth).filter(Booth.id == current_user.booth_id).first()
        if booth is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "MERCHANT_NOT_FOUND", "message": "商铺不存在"}
            )

        # 按类别统计
        category_stats = db.query(
            CostEvidence.category,
            func.count(CostEvidence.id).label('count'),
            func.coalesce(func.sum(CostEvidence.amount), 0).label('total_amount')
        ).filter(
            CostEvidence.booth_id == booth.id
        ).group_by(CostEvidence.category).all()

        # 按状态统计
        status_stats = db.query(
            CostEvidence.status,
            func.count(CostEvidence.id).label('count')
        ).filter(
            CostEvidence.booth_id == booth.id
        ).group_by(CostEvidence.status).all()

        # 总计
        total = db.query(
            func.count(CostEvidence.id).label('total_count'),
            func.coalesce(func.sum(CostEvidence.amount), 0).label('total_amount')
        ).filter(
            CostEvidence.booth_id == booth.id
        ).first()

        return {
            "booth_id": booth.id,
            "total_count": total.total_count if total else 0,
            "total_amount": float(total.total_amount) if total and total.total_amount else 0,
            "by_category": [
                {
                    "category": stat.category,
                    "count": stat.count,
                    "total_amount": float(stat.total_amount) if stat.total_amount else 0
                }
                for stat in category_stats
            ],
            "by_status": [
                {
                    "status": stat.status,
                    "count": stat.count
                }
                for stat in status_stats
            ]
        }

    except Exception as e:
        logger.error(f"Get cost evidence stats error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取统计信息失败"}
        )


# ============================================================================
# 管理员审核端点
# ============================================================================

admin_router = APIRouter(prefix="/admin/cost-evidence", tags=["admin-cost-evidence"])


class ReviewRequest(BaseModel):
    """审核请求模型"""
    action: str = Field(..., description="审核动作: approve/reject")
    remark: Optional[str] = Field(None, max_length=500, description="审核备注")


@admin_router.get("")
async def admin_list_cost_evidences(
    booth_id: Optional[int] = Query(None, description="按商铺ID筛选"),
    category: Optional[str] = Query(None, description="按类别筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="按状态筛选"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员获取所有商户的成本凭据列表。

    支持按商铺、类别、状态筛选。

    需要 super_admin 或 event_admin 角色。
    """
    try:
        from sqlalchemy import func

        query = db.query(CostEvidence)

        if booth_id is not None:
            query = query.filter(CostEvidence.booth_id == booth_id)

        if category and category in VALID_CATEGORIES:
            query = query.filter(CostEvidence.category == category)

        if status_filter and status_filter in ('pending', 'approved', 'rejected'):
            query = query.filter(CostEvidence.status == status_filter)

        total_count = query.count()

        evidences = query.order_by(
            CostEvidence.created_at.desc()
        ).limit(limit).offset(offset).all()

        evidence_list = []
        for ev in evidences:
            # 获取商铺信息
            booth = db.query(Booth).filter(Booth.id == ev.booth_id).first()
            booth_name = booth.name if booth else "未知"
            class_name = booth.class_name if booth else "未知"

            evidence_list.append({
                "id": ev.id,
                "booth_id": ev.booth_id,
                "booth_name": booth_name,
                "class_name": class_name,
                "uploader_id": ev.uploader_id,
                "filename": ev.filename,
                "file_size": ev.file_size,
                "mime_type": ev.mime_type,
                "category": ev.category,
                "amount": float(ev.amount) if ev.amount else None,
                "description": ev.description,
                "status": ev.status,
                "reviewed_by": ev.reviewed_by,
                "reviewed_at": ev.reviewed_at.isoformat() if ev.reviewed_at else None,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            })

        return {
            "evidences": evidence_list,
            "total_count": total_count
        }

    except Exception as e:
        logger.error(f"Admin list cost evidences error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取凭据列表失败"}
        )


@admin_router.get("/stats")
async def admin_cost_evidence_stats(
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员获取全局成本凭据统计。

    返回待审核数量、各状态统计、各类别统计。
    """
    try:
        from sqlalchemy import func

        # 按状态统计
        status_stats = db.query(
            CostEvidence.status,
            func.count(CostEvidence.id).label('count'),
            func.coalesce(func.sum(CostEvidence.amount), 0).label('total_amount')
        ).group_by(CostEvidence.status).all()

        # 按类别统计
        category_stats = db.query(
            CostEvidence.category,
            func.count(CostEvidence.id).label('count'),
            func.coalesce(func.sum(CostEvidence.amount), 0).label('total_amount')
        ).group_by(CostEvidence.category).all()

        # 总计
        total = db.query(
            func.count(CostEvidence.id).label('total_count'),
            func.coalesce(func.sum(CostEvidence.amount), 0).label('total_amount')
        ).first()

        pending_count = next(
            (s.count for s in status_stats if s.status == 'pending'), 0
        )

        return {
            "total_count": total.total_count if total else 0,
            "total_amount": float(total.total_amount) if total and total.total_amount else 0,
            "pending_count": pending_count,
            "by_status": [
                {
                    "status": stat.status,
                    "count": stat.count,
                    "total_amount": float(stat.total_amount) if stat.total_amount else 0
                }
                for stat in status_stats
            ],
            "by_category": [
                {
                    "category": stat.category,
                    "count": stat.count,
                    "total_amount": float(stat.total_amount) if stat.total_amount else 0
                }
                for stat in category_stats
            ]
        }

    except Exception as e:
        logger.error(f"Admin cost evidence stats error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取统计信息失败"}
        )


@admin_router.get("/{evidence_id}")
async def admin_get_cost_evidence(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员获取单个凭据详情。
    """
    try:
        evidence = db.query(CostEvidence).filter(CostEvidence.id == evidence_id).first()

        if evidence is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "EVIDENCE_NOT_FOUND", "message": "凭据不存在"}
            )

        booth = db.query(Booth).filter(Booth.id == evidence.booth_id).first()

        return {
            "id": evidence.id,
            "booth_id": evidence.booth_id,
            "booth_name": booth.name if booth else "未知",
            "class_name": booth.class_name if booth else "未知",
            "uploader_id": evidence.uploader_id,
            "filename": evidence.filename,
            "stored_filename": evidence.stored_filename,
            "file_size": evidence.file_size,
            "mime_type": evidence.mime_type,
            "category": evidence.category,
            "amount": float(evidence.amount) if evidence.amount else None,
            "description": evidence.description,
            "status": evidence.status,
            "reviewed_by": evidence.reviewed_by,
            "reviewed_at": evidence.reviewed_at.isoformat() if evidence.reviewed_at else None,
            "created_at": evidence.created_at.isoformat() if evidence.created_at else None
        }

    except Exception as e:
        logger.error(f"Admin get cost evidence error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "获取凭据详情失败"}
        )


@admin_router.get("/{evidence_id}/file")
async def admin_download_cost_evidence_file(
    evidence_id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员下载/查看凭据文件。
    """
    try:
        evidence = db.query(CostEvidence).filter(CostEvidence.id == evidence_id).first()

        if evidence is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "EVIDENCE_NOT_FOUND", "message": "凭据不存在"}
            )

        if not os.path.exists(evidence.file_path):
            return JSONResponse(
                status_code=404,
                content={"error_code": "FILE_NOT_FOUND", "message": "凭据文件不存在"}
            )

        return FileResponse(
            path=evidence.file_path,
            filename=evidence.filename,
            media_type=evidence.mime_type
        )

    except Exception as e:
        logger.error(f"Admin download cost evidence error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "下载凭据失败"}
        )


@admin_router.post("/{evidence_id}/review")
async def admin_review_cost_evidence(
    evidence_id: int,
    request: ReviewRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员审核成本凭据（通过/驳回）。

    Request Body:
        - action: 审核动作 (approve/reject)
        - remark: 审核备注（可选）

    需要 super_admin 或 event_admin 角色。
    """
    try:
        if request.action not in ('approve', 'reject'):
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_ACTION",
                    "message": "无效的审核动作，可选值: approve, reject"
                }
            )

        evidence = db.query(CostEvidence).filter(CostEvidence.id == evidence_id).first()

        if evidence is None:
            return JSONResponse(
                status_code=404,
                content={"error_code": "EVIDENCE_NOT_FOUND", "message": "凭据不存在"}
            )

        if evidence.status != 'pending':
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "ALREADY_REVIEWED",
                    "message": f"该凭据已被审核（当前状态: {evidence.status}）"
                }
            )

        # 更新状态
        new_status = 'approved' if request.action == 'approve' else 'rejected'
        evidence.status = new_status
        evidence.reviewed_by = current_user.id
        evidence.reviewed_at = datetime.now(CST)

        db.commit()
        db.refresh(evidence)

        logger.info(
            f"Cost evidence reviewed: id={evidence_id}, action={request.action}, "
            f"reviewer={current_user.username}"
        )

        booth = db.query(Booth).filter(Booth.id == evidence.booth_id).first()

        return {
            "id": evidence.id,
            "booth_id": evidence.booth_id,
            "booth_name": booth.name if booth else "未知",
            "filename": evidence.filename,
            "category": evidence.category,
            "amount": float(evidence.amount) if evidence.amount else None,
            "status": evidence.status,
            "reviewed_by": evidence.reviewed_by,
            "reviewed_at": evidence.reviewed_at.isoformat() if evidence.reviewed_at else None,
            "message": f"凭据已{'通过' if request.action == 'approve' else '驳回'}"
        }

    except Exception as e:
        logger.error(f"Admin review cost evidence error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "审核操作失败"}
        )


@admin_router.post("/batch-review")
async def admin_batch_review_cost_evidences(
    request: dict,
    current_user: User = Depends(get_current_user),
    _: None = Depends(RoleChecker(["super_admin", "event_admin"])),
    db: Session = Depends(get_db)
):
    """
    管理员批量审核成本凭据。

    Request Body:
        - ids: 凭据ID列表
        - action: 审核动作 (approve/reject)

    需要 super_admin 或 event_admin 角色。
    """
    try:
        ids = request.get("ids", [])
        action = request.get("action", "")

        if not ids or not isinstance(ids, list):
            return JSONResponse(
                status_code=400,
                content={"error_code": "INVALID_IDS", "message": "请提供凭据ID列表"}
            )

        if action not in ('approve', 'reject'):
            return JSONResponse(
                status_code=400,
                content={
                    "error_code": "INVALID_ACTION",
                    "message": "无效的审核动作，可选值: approve, reject"
                }
            )

        new_status = 'approved' if action == 'approve' else 'rejected'
        now = datetime.now(CST)

        updated_count = db.query(CostEvidence).filter(
            CostEvidence.id.in_(ids),
            CostEvidence.status == 'pending'
        ).update(
            {
                CostEvidence.status: new_status,
                CostEvidence.reviewed_by: current_user.id,
                CostEvidence.reviewed_at: now
            },
            synchronize_session='fetch'
        )

        db.commit()

        logger.info(
            f"Batch review cost evidences: action={action}, "
            f"requested={len(ids)}, updated={updated_count}, "
            f"reviewer={current_user.username}"
        )

        return {
            "action": action,
            "requested_count": len(ids),
            "updated_count": updated_count,
            "message": f"已{'通过' if action == 'approve' else '驳回'} {updated_count} 条凭据"
        }

    except Exception as e:
        logger.error(f"Admin batch review error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "批量审核失败"}
        )
