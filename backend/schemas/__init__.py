"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class BaseResponseModel(BaseModel):
    """Base response model for all API responses"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ServerCreateSchema(BaseModel):
    """Schema for creating a new server"""
    ip: str = Field(..., description="Server IP address")
    alias: str = Field(..., min_length=1, max_length=100, description="Server alias")
    name: str = Field(..., min_length=1, max_length=200, description="Server name")
    user: str = Field(..., min_length=1, max_length=100, description="SSH username")
    script_path: str = Field(..., min_length=1, max_length=500, description="Deployment script path")
    ssh_port: Optional[int] = Field(22, ge=1, le=65535, description="SSH port")
    description: Optional[str] = Field(None, max_length=1000, description="Server description")
    environment: Optional[str] = Field("production", description="Environment (production, staging, development)")
    
    @validator('ip')
    def validate_ip(cls, v):
        # Basic IPv4 validation
        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        if not ip_pattern.match(v):
            raise ValueError('Invalid IP address format')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_environments = ['production', 'staging', 'development']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {", ".join(valid_environments)}')
        return v


class ServerUpdateSchema(BaseModel):
    """Schema for updating a server"""
    ip: Optional[str] = Field(None, description="Server IP address")
    alias: Optional[str] = Field(None, min_length=1, max_length=100, description="Server alias")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Server name")
    user: Optional[str] = Field(None, min_length=1, max_length=100, description="SSH username")
    script_path: Optional[str] = Field(None, min_length=1, max_length=500, description="Deployment script path")
    ssh_port: Optional[int] = Field(None, ge=1, le=65535, description="SSH port")
    description: Optional[str] = Field(None, max_length=1000, description="Server description")
    environment: Optional[str] = Field(None, description="Environment")
    is_active: Optional[bool] = Field(None, description="Whether server is active")
    
    @validator('ip')
    def validate_ip(cls, v):
        if v is not None:
            ip_pattern = re.compile(
                r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            )
            if not ip_pattern.match(v):
                raise ValueError('Invalid IP address format')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        if v is not None:
            valid_environments = ['production', 'staging', 'development']
            if v not in valid_environments:
                raise ValueError(f'Environment must be one of: {", ".join(valid_environments)}')
        return v


class DeployRequestSchema(BaseModel):
    """Schema for deployment request"""
    server_id: int = Field(..., description="ID of target server")
    command: Optional[str] = Field(None, description="Custom command to execute (optional)")
    environment: Optional[str] = Field(None, description="Deployment environment")
    git_commit: Optional[str] = Field(None, max_length=40, description="Git commit hash")


class HealthCheckRequestSchema(BaseModel):
    """Schema for health check request"""
    detailed: Optional[bool] = Field(True, description="Whether to perform detailed system metrics check")


class LogSearchSchema(BaseModel):
    """Schema for log search request"""
    search_term: str = Field(..., min_length=1, description="Search term")
    server_id: Optional[int] = Field(None, description="Filter by server ID")
    case_sensitive: Optional[bool] = Field(False, description="Case sensitive search")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum results")


class PaginationSchema(BaseModel):
    """Schema for pagination parameters"""
    page: Optional[int] = Field(1, ge=1, description="Page number")
    per_page: Optional[int] = Field(50, ge=1, le=100, description="Items per page")


class DateRangeSchema(BaseModel):
    """Schema for date range filtering"""
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')
        return v


class UserCreateSchema(BaseModel):
    """Schema for creating a new user"""
    username: str = Field(..., min_length=3, max_length=80, description="Username")
    email: Optional[str] = Field(None, max_length=120, description="Email address")
    password: str = Field(..., min_length=6, description="Password")
    role: Optional[str] = Field("user", description="User role")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['admin', 'user', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(v):
                raise ValueError('Invalid email format')
        return v


class UserLoginSchema(BaseModel):
    """Schema for user login"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class ErrorResponseSchema(BaseModel):
    """Schema for error responses"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# Response schemas for documentation
class ServerResponseSchema(BaseModel):
    """Schema for server response"""
    id: int
    ip: str
    alias: str
    name: str
    user: str
    script_path: str
    ssh_port: int
    description: Optional[str]
    environment: str
    status: str
    is_active: bool
    created_at: str
    updated_at: str
    last_deployed: Optional[str]
    last_health_check: Optional[str]
    created_by: Optional[int]


class DeployLogResponseSchema(BaseModel):
    """Schema for deployment log response"""
    id: int
    server_id: int
    executed_by: Optional[int]
    status: str
    command: Optional[str]
    output: Optional[str]
    error_message: Optional[str]
    started_at: str
    completed_at: Optional[str]
    duration: Optional[int]
    duration_formatted: str
    deployment_type: str
    git_commit: Optional[str]
    environment: Optional[str]
    created_at: str
    updated_at: str


class HealthMetricResponseSchema(BaseModel):
    """Schema for health metric response"""
    id: int
    server_id: int
    ping_time: Optional[float]
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    network_rx: Optional[int]
    network_tx: Optional[int]
    uptime: Optional[int]
    uptime_formatted: str
    load_average: Optional[float]
    status: str
    dns_resolved: Optional[str]
    error_message: Optional[str]
    check_type: str
    created_at: str
    updated_at: str
