from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.database import get_db
from app.services.issue_service import IssueService
from app.api.v1.endpoints.auth import get_current_user
from app.schemas.issue import IssueCreate, IssueUpdate, IssueSchema
from app.models.user import User, UserRole

router = APIRouter()

@router.post("/", response_model=IssueSchema)
async def create_issue(
    issue: IssueCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Nhân viên hoặc Admin gửi báo cáo sự cố."""
    return await IssueService.create_issue(
        db, 
        user_id=current_user.id, 
        machine_id=issue.machine_id, 
        content=issue.content
    )

@router.get("/", response_model=List[IssueSchema])
async def list_issues(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liệt kê danh sách báo cáo (Admin xem tất cả, Staff có thể giới hạn sau này)."""
    # Tạm thời cho phép tất cả mọi người đã đăng nhập xem để tiện theo dõi
    return await IssueService.list_issues(db, status=status, skip=skip, limit=limit)

@router.put("/{issue_id}", response_model=IssueSchema)
async def update_issue(
    issue_id: int, 
    issue_update: IssueUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin cập nhật trạng thái sự cố (Ví dụ: Chuyển sang RESOLVED)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Chỉ Quản trị viên mới có quyền cập nhật trạng thái sự cố")
    
    updated = await IssueService.update_issue_status(db, issue_id, issue_update.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự cố này")
    return updated
