from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class ProjectCreate(BaseModel):
    name: str
    max_agents: Optional[int] = 80
    off_pattern: Optional[str] = None

class AgentCreate(BaseModel):
    name: str
    email: Optional[str] = None
    channel_skill: str = "both"

class ShiftCreate(BaseModel):
    name: str
    start_time: str
    end_time: str
    crosses_midnight: bool = False
    shift_order: int = 0

class ExceptionCreate(BaseModel):
    agent_id: int
    type: str
    start_date: date
    end_date: date
    shift_id: Optional[int] = None

class PerShiftReq(BaseModel):
    shift_id: int
    chat_min: int = 0
    email_min: int = 0
    total: Optional[int] = None

class GenerateScheduleReq(BaseModel):
    start_date: date
    horizon_days: int = 14
    per_shift_requirements: List[PerShiftReq]
    solver_time_limit: Optional[int] = 60
