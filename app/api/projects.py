from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.core.database import get_db
from app.api.deps import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.schemas.project import (
    ProjectCreate, 
    ProjectUpdate, 
    ProjectResponse, 
    ProjectList
)
from app.core.redis_client import redis_client
import math

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    project = Project(
        **project_data.model_dump(),
        organization_id=current_user.organization_id,
        created_by=current_user.id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    # Clear cache for this org's projects
    await redis_client.delete(f"projects:org:{current_user.organization_id}")
    
    return project

@router.get("/", response_model=ProjectList)
async def list_projects(
    status: Optional[ProjectStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Try cache first
    cache_key = f"projects:org:{current_user.organization_id}:page:{page}:limit:{limit}:status:{status}"
    cached = await redis_client.get(cache_key)
    if cached:
        return ProjectList(**cached)
    
    # Build query
    query = select(Project).where(
        Project.organization_id == current_user.organization_id
    )
    
    if status:
        query = query.where(Project.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(Project.created_at.desc())
    
    # Execute
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # Prepare response
    response = ProjectList(
        projects=projects,
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if limit > 0 else 0
    )
    
    # Cache for 60 seconds
    await redis_client.set(cache_key, response.model_dump(), expire=60)
    
    return response

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    project = await db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == current_user.organization_id
        )
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    project = await db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == current_user.organization_id
        )
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    # Clear cache
    await redis_client.delete(f"projects:org:{current_user.organization_id}")
    
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    project = await db.scalar(
        select(Project).where(
            Project.id == project_id,
            Project.organization_id == current_user.organization_id
        )
    )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await db.delete(project)
    await db.commit()
    
    # Clear cache
    await redis_client.delete(f"projects:org:{current_user.organization_id}")