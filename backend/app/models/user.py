"""
User and role models for authentication
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


# Association table for user roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, comment="Username")
    email = Column(String(255), unique=True, nullable=False, comment="Email address")
    hashed_password = Column(String(255), nullable=False, comment="Hashed password")
    full_name = Column(String(200), nullable=True, comment="Full name")
    is_active = Column(Boolean, default=True, comment="Is user active")
    is_superuser = Column(Boolean, default=False, comment="Is superuser")
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class Role(Base, TimestampMixin):
    """Role model"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="Role name")
    description = Column(String(200), nullable=True, comment="Role description")
    permissions = Column(String(500), nullable=True, comment="Comma-separated permissions")
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"
