from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.ACTIVE)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    organization = relationship("Organization", back_populates="projects")
    creator = relationship("User", back_populates="projects")
    
    def __repr__(self):
        return f"<Project {self.name}>"