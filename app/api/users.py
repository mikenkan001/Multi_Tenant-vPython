from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    users = await db.scalars(
        select(User).where(
            User.organization_id == current_user.organization_id
        ).order_by(User.created_at.desc())
    )
    return users.all()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    return current_user