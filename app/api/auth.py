from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token
)
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.models.user import User
from app.models.organization import Organization
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if organization subdomain exists
    org = await db.scalar(
        select(Organization).where(Organization.subdomain == user_data.subdomain)
    )
    if org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already taken"
        )
    
    # Check if user email exists
    existing_user = await db.scalar(
        select(User).where(User.email == user_data.email)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create organization
    org = Organization(
        name=user_data.organization_name,
        subdomain=user_data.subdomain
    )
    db.add(org)
    await db.flush()  # Get org ID without committing
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        organization_id=org.id,
        role="admin"
    )
    db.add(user)
    
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(
        select(User).where(User.email == user_data.email)
    )
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    from sqlalchemy import update
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login="now()")
    )
    await db.commit()
    
    # Create token
    access_token = create_access_token(
        data={"sub": str(user.id), "org": user.organization_id},
        expires_delta=timedelta(minutes=30)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }