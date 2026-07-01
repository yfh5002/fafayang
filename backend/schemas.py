# -*- coding: utf-8 -*-
"""
HJSYSTEM Pydantic Schemas
Data validation and serialization schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ComponentBase(BaseModel):
    """Base component schema"""
    sequence: int = Field(default=0, description="序号")
    name: str = Field(..., min_length=1, max_length=200, description="名称")
    model: Optional[str] = Field(default="", max_length=500, description="型号及规格")
    quantity: int = Field(default=1, ge=1, description="数量")
    unit_price: float = Field(default=0.0, ge=0, description="单价")
    remarks: Optional[str] = Field(default="", max_length=500, description="备注")


class ComponentCreate(ComponentBase):
    """Schema for creating component"""
    pass


class ComponentUpdate(BaseModel):
    """Schema for updating component"""
    sequence: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    model: Optional[str] = Field(default=None, max_length=500)
    quantity: Optional[int] = Field(default=None, ge=1)
    unit_price: Optional[float] = Field(default=None, ge=0)
    remarks: Optional[str] = Field(default=None, max_length=500)


class ComponentResponse(ComponentBase):
    """Schema for component response"""
    id: int
    subtotal: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ComponentListResponse(BaseModel):
    """Schema for component list response"""
    total: int
    items: List[ComponentResponse]


class SearchRequest(BaseModel):
    """Schema for search request"""
    keyword: str = Field(default="", description="搜索关键词")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=50, ge=1, le=1000, description="每页数量")


class LogEntryResponse(BaseModel):
    """Schema for log entry response"""
    id: int
    action: str
    details: Optional[str] = None
    component_name: Optional[str] = None
    component_model: Optional[str] = None
    user_ip: Optional[str] = None
    computer_name: Optional[str] = None
    username: Optional[str] = None
    created_at: str

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Handle datetime conversion from ORM
        data = {}
        for key in cls.model_fields:
            val = getattr(obj, key, None)
            if key == "created_at" and val is not None:
                if hasattr(val, "strftime"):
                    val = val.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    val = str(val)
            data[key] = val
        return cls(**data)


class LogCreateRequest(BaseModel):
    """Schema for creating log entry"""
    action: str = Field(..., min_length=1, max_length=50)
    details: Optional[str] = None
    component_name: Optional[str] = None
    component_model: Optional[str] = None


class ExcelImportResponse(BaseModel):
    """Schema for Excel import response"""
    success: bool
    imported: int
    skipped: int
    message: str


class ExcelExportRequest(BaseModel):
    """Schema for Excel export request"""
    title: str = Field(default="元器件报价清单", max_length=100)
    filename: Optional[str] = Field(default=None, description="导出文件名（不含扩展名）")
    selected_only: bool = Field(default=False, description="仅导出选中项")
    selected_ids: Optional[List[int]] = Field(default=None, description="选中的ID列表")


class PriceCalculationRequest(BaseModel):
    """Schema for price calculation"""
    items: List[dict] = Field(..., description="计算项目列表")


class PriceCalculationResponse(BaseModel):
    """Schema for price calculation response"""
    items: List[dict]
    total: float


class SystemStatus(BaseModel):
    """Schema for system status"""
    total_components: int
    online_users: int
    version: str = "2.0.0"


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    display_name: Optional[str] = Field(default=None, max_length=50, description="显示名称")


class UserCreate(UserBase):
    """Schema for creating user"""
    password: str = Field(..., min_length=1, max_length=100, description="密码")
    is_admin: bool = Field(default=False, description="是否管理员")


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_admin: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class UserLoginResponse(BaseModel):
    """Schema for login response"""
    success: bool
    token: str
    username: str
    display_name: Optional[str] = None
    is_admin: bool
    message: str
