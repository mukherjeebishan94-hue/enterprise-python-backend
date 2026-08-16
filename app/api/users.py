from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.api.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/users", tags=["Users Profile & Management"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Protected endpoint: Fetch current logged-in user profile.
    """
    return current_user


@router.get(
    "/",
    response_model=List[UserResponse],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.MANAGER]))],
)
async def list_all_users(
    db: AsyncSession = Depends(get_db),
):
    """
    Admin/Manager-only endpoint: List all registered users in system.
    """
    result = await db.execute(select(User))
    return result.scalars().all()