from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Text, JSON, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    max_agents = Column(Integer, default=80)
    schedule_cycle_days = Column(Integer, default=14)
    off_pattern = Column(String, nullable=True)

    agents = relationship("Agent", back_populates="project", cascade="all, delete")
    shifts = relationship("Shift", back_populates="project", cascade="all, delete")
    schedules = relationship("Schedule", back_populates="project", cascade="all, delete")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    channel_skill = Column(String, default="both")
    is_active = Column(Boolean, default=True)

    project = relationship("Project", back_populates="agents")
    exceptions = relationship("ExceptionRow", back_populates="agent", cascade="all,delete")

class Shift(Base):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    crosses_midnight = Column(Boolean, default=False)
    shift_order = Column(Integer, default=0)

    project = relationship("Project", back_populates="shifts")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    generation_metadata = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="schedules")
    assignments = relationship("ScheduleAssignment", back_populates="schedule", cascade="all,delete")

class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"))
    date = Column(Date, nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="CASCADE"))
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"))
    role = Column(String, nullable=False)
    is_fixed = Column(Boolean, default=False)
    note = Column(Text, nullable=True)

    schedule = relationship("Schedule", back_populates="assignments")

class ExceptionRow(Base):
    __tablename__ = "exceptions"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"))
    type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    shift_id = Column(Integer, nullable=True)

    agent = relationship("Agent", back_populates="exceptions")
