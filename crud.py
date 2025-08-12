from sqlalchemy.orm import Session
from . import models
from datetime import date, timedelta
from typing import List

def create_project(db: Session, project):
    p = models.Project(name=project.name, max_agents=project.max_agents, off_pattern=project.off_pattern)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def list_projects(db: Session):
    return db.query(models.Project).all()

def get_project(db: Session, project_id: int):
    return db.get(models.Project, project_id)

def create_shift(db: Session, project_id: int, s):
    from datetime import datetime
    h,m = map(int, s.start_time.split(":"))
    st = (datetime(2000,1,1,h,m)).time()
    h2,m2 = map(int, s.end_time.split(":"))
    et = (datetime(2000,1,1,h2,m2)).time()
    shift = models.Shift(project_id=project_id, name=s.name, start_time=st, end_time=et, crosses_midnight=s.crosses_midnight, shift_order=s.shift_order)
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift

def create_agent(db: Session, project_id: int, a):
    ag = models.Agent(project_id=project_id, name=a.name, email=a.email, channel_skill=a.channel_skill)
    db.add(ag)
    db.commit()
    db.refresh(ag)
    return ag

def list_agents(db: Session, project_id: int):
    return db.query(models.Agent).filter(models.Agent.project_id==project_id).all()

def get_shifts(db: Session, project_id: int):
    return db.query(models.Shift).filter(models.Shift.project_id==project_id).order_by(models.Shift.shift_order).all()

def add_exception(db: Session, ex):
    e = models.ExceptionRow(agent_id=ex.agent_id, type=ex.type, start_date=ex.start_date, end_date=ex.end_date, shift_id=ex.shift_id)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e

def persist_schedule(db: Session, project_id: int, start_date: date, end_date: date, generation_metadata: dict, assignments: List[dict]):
    sch = models.Schedule(project_id=project_id, start_date=start_date, end_date=end_date, generation_metadata=generation_metadata)
    db.add(sch)
    db.commit()
    db.refresh(sch)
    for a in assignments:
        ass = models.ScheduleAssignment(schedule_id=sch.id, date=a['date'], shift_id=a['shift_id'], agent_id=a['agent_id'], role=a['role'])
        db.add(ass)
    db.commit()
    return sch

def get_schedule(db: Session, schedule_id: int):
    return db.query(models.Schedule).filter(models.Schedule.id==schedule_id).first()
