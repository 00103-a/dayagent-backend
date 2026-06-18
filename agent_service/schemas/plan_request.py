import os
from typing import Any

from pydantic import BaseModel, Field

_DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "南昌")


class ParcelInfo(BaseModel):
    """Java 传入的快递单号信息"""
    tracking_no: str = Field(..., description="快递单号")
    carrier: str = Field(..., description="快递公司，如顺丰、京东")
    remark: str = Field(default="", description="备注，如'耳机'")


class PlanRequest(BaseModel):
    """Java 端调用 /generate-plan 时传入的数据"""
    user_id: str = Field(..., description="用户 ID")
    yesterday_summary: str = Field(default="", description="昨日总结")
    goals: list[str] = Field(default_factory=list, description="当前活跃目标列表")
    location: str = Field(default=_DEFAULT_LOCATION, description="城市，用于查天气")
    force_refresh: bool = Field(default=False, description="跳过缓存，强制重新抓取")
    parcels: list[ParcelInfo] = Field(default_factory=list, description="用户未签收的快递列表")
    user_settings: dict = Field(default_factory=dict, description="用户配置的 API Key 等")


class ParcelStatus(BaseModel):
    """快递状态查询结果，返回给 Java 端用于更新数据库"""
    tracking_no: str
    carrier: str
    remark: str = ""
    state: str
    is_delivered: bool = False
    pickup_code: str = ""              # ← 加这行
    is_waiting_pickup: bool = False
    latest_context: str = ""
    latest_time: str = ""
    details: list[dict[str, str]] = Field(default_factory=list, description="完整物流轨迹")


class PlanResponse(BaseModel):
    """返回给 Java 端的规划结果"""
    plan: str = Field(..., description="今日规划正文")
    priorities: list[str] = Field(default_factory=list, description="优先级列表")
    warnings: list[str] = Field(default_factory=list, description="预警提醒，如作业截止")
    parcels: list[ParcelStatus] = Field(default_factory=list, description="最新的快递状态")
