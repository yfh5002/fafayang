# -*- coding: utf-8 -*-
"""
HJSYSTEM Database Models
SQLAlchemy ORM models for Component, Log, and User
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Component(Base):
    """元器件数据模型"""
    __tablename__ = "components"
    
    id = Column(Integer, primary_key=True, index=True)
    sequence = Column(Integer, default=0, index=True, comment="序号")
    name = Column(String(200), nullable=False, index=True, comment="名称")
    model = Column(String(500), nullable=True, index=True, comment="型号及规格")
    quantity = Column(Integer, default=1, comment="数量")
    unit_price = Column(Float, default=0.0, comment="单价")
    subtotal = Column(Float, default=0.0, comment="小计")
    remarks = Column(String(500), nullable=True, index=True, comment="备注")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "sequence": self.sequence,
            "name": self.name,
            "model": self.model or "",
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
            "remarks": self.remarks or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def calculate_subtotal(self):
        """Calculate subtotal based on quantity and unit price"""
        self.subtotal = self.quantity * self.unit_price
        return self.subtotal


class LogEntry(Base):
    """操作日志模型"""
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(50), nullable=False, index=True, comment="操作类型")
    details = Column(Text, nullable=True, comment="操作详情")
    component_name = Column(String(200), nullable=True, comment="相关元器件名称")
    component_model = Column(String(500), nullable=True, comment="相关元器件型号")
    user_ip = Column(String(50), nullable=True, comment="用户IP")
    user_agent = Column(String(500), nullable=True, comment="用户代理")
    computer_name = Column(String(100), nullable=True, comment="电脑名称")
    username = Column(String(100), nullable=True, comment="用户名")
    created_at = Column(DateTime, default=datetime.now, index=True, comment="操作时间")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "action": self.action,
            "details": self.details,
            "component_name": self.component_name or "",
            "component_model": self.component_model or "",
            "user_ip": self.user_ip or "",
            "computer_name": self.computer_name or "",
            "username": self.username or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(200), nullable=False, comment="密码哈希")
    display_name = Column(String(50), nullable=True, comment="显示名称")
    is_admin = Column(Boolean, default=False, comment="是否管理员")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    last_login = Column(DateTime, nullable=True, index=True, comment="最后登录时间")
