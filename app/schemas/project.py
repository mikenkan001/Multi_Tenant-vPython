from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.project import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(ProjectBase):
    id: int
    organization_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProjectList(BaseModel):
    projects: list[ProjectResponse]
    total: int
    page: int
    limit: int
    total_pages: int