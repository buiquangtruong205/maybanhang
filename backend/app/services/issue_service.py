from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.issue import Issue, IssueStatus
from typing import Optional

class IssueService:
    @staticmethod
    async def create_issue(db: AsyncSession, user_id: int, machine_id: Optional[int], content: str):
        try:
            new_issue = Issue(
                user_id=user_id,
                machine_id=machine_id,
                content=content,
                status=IssueStatus.OPEN
            )
            db.add(new_issue)
            await db.commit()
            await db.refresh(new_issue)
            return new_issue
        except Exception as e:
            await db.rollback()
            print(f"❌ Lỗi khi tạo Issue: {e}")
            raise e

    @staticmethod
    async def list_issues(db: AsyncSession, status: Optional[IssueStatus] = None, skip: int = 0, limit: int = 50):
        query = select(Issue).order_by(Issue.created_at.desc())
        if status:
            query = query.where(Issue.status == status)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_issue_status(db: AsyncSession, issue_id: int, status: IssueStatus):
        result = await db.execute(select(Issue).where(Issue.id == issue_id))
        issue = result.scalar_one_or_none()
        if issue:
            issue.status = status
            await db.commit()
            await db.refresh(issue)
            return issue
        return None
