from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import db, models, schemas, crud
from .tasks import run_schedule_task, celery_app
from datetime import date
import csv, io

app = FastAPI(title="Scheduler API")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=db.engine)

def get_db_session():
    yield from db.get_db()

@app.post("/projects")
def create_project(p: schemas.ProjectCreate, db_s: Session = Depends(get_db_session)):
    proj = crud.create_project(db_s, p)
    return {"id": proj.id, "name": proj.name}

@app.get("/projects")
def list_projects(db_s: Session = Depends(get_db_session)):
    projs = crud.list_projects(db_s)
    return [{"id": p.id, "name": p.name} for p in projs]

@app.post("/projects/{project_id}/shifts")
def add_shift(project_id: int, s: schemas.ShiftCreate, db_s: Session = Depends(get_db_session)):
    proj = crud.get_project(db_s, project_id)
    if not proj: raise HTTPException(404, "project not found")
    sh = crud.create_shift(db_s, project_id, s)
    return {"id": sh.id, "name": sh.name}

@app.get("/projects/{project_id}/shifts")
def get_shifts(project_id: int, db_s: Session = Depends(get_db_session)):
    proj = crud.get_project(db_s, project_id)
    if not proj: raise HTTPException(404, "project not found")
    shifts = crud.get_shifts(db_s, project_id)
    return [{"id": s.id, "name": s.name, "start_time": s.start_time.strftime("%H:%M"), "end_time": s.end_time.strftime("%H:%M"), "crosses_midnight": s.crosses_midnight} for s in shifts]

@app.post("/projects/{project_id}/agents")
def add_agent(project_id: int, a: schemas.AgentCreate, db_s: Session = Depends(get_db_session)):
    proj = crud.get_project(db_s, project_id)
    if not proj: raise HTTPException(404, "project not found")
    ag = crud.create_agent(db_s, project_id, a)
    return {"id": ag.id, "name": ag.name}

@app.get("/projects/{project_id}/agents")
def list_agents(project_id: int, db_s: Session = Depends(get_db_session)):
    return [ { "id": ag.id, "name": ag.name, "channel_skill": ag.channel_skill } for ag in crud.list_agents(db_s, project_id) ]

@app.post("/projects/{project_id}/agents/bulk_upload")
async def bulk_upload_agents(project_id: int, file: UploadFile = File(...), db_s: Session = Depends(get_db_session)):
    proj = crud.get_project(db_s, project_id)
    if not proj:
        raise HTTPException(404, "project not found")
    contents = await file.read()
    s = contents.decode('utf-8')
    reader = csv.DictReader(io.StringIO(s))
    created = []
    for row in reader:
        name = row.get('name') or row.get('Name')
        email = row.get('email') or row.get('Email') or None
        skill = (row.get('channel_skill') or row.get('channel') or 'both').strip().lower()
        if skill not in ('chat','email','both'):
            skill = 'both'
        ag = crud.create_agent(db_s, project_id, type("A", (), {"name": name, "email": email, "channel_skill": skill}))
        created.append({"id": ag.id, "name": ag.name})
        fos = row.get('fixed_off_start') or row.get('fixed_off')
        foe = row.get('fixed_off_end')
        if fos and foe:
            try:
                start = date.fromisoformat(fos.strip()); end = date.fromisoformat(foe.strip())
                ex = type("E", (), {"agent_id": ag.id, "type": "fixed_off", "start_date": start, "end_date": end, "shift_id": None})
                crud.add_exception(db_s, ex)
            except:
                pass
        fsid = row.get('fixed_shift_id')
        fs_start = row.get('fixed_shift_start')
        fs_end = row.get('fixed_shift_end')
        if fsid and fs_start and fs_end:
            try:
                start = date.fromisoformat(fs_start.strip()); end = date.fromisoformat(fs_end.strip())
                ex = type("E", (), {"agent_id": ag.id, "type": "fixed_shift", "start_date": start, "end_date": end, "shift_id": int(fsid)})
                crud.add_exception(db_s, ex)
            except:
                pass
    return {"created": created, "count": len(created)}

@app.post("/exceptions")
def add_exception(ex: schemas.ExceptionCreate, db_s: Session = Depends(get_db_session)):
    e = crud.add_exception(db_s, ex)
    return {"id": e.id}

@app.post("/projects/{project_id}/generate_schedule_async")
def generate_schedule_async(project_id: int, g: schemas.GenerateScheduleReq, db_s: Session = Depends(get_db_session)):
    proj = crud.get_project(db_s, project_id)
    if not proj:
        raise HTTPException(404, "project not found")
    reqs = {}
    for p in g.per_shift_requirements:
        reqs[p.shift_id] = {"chat_min": p.chat_min, "email_min": p.email_min, "total": p.total}
    job = run_schedule_task.apply_async(args=[project_id, g.start_date.isoformat(), g.horizon_days, reqs, g.solver_time_limit or 120])
    return {"job_id": job.id}

from celery.result import AsyncResult
from .tasks import celery_app

@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    res = AsyncResult(job_id, app=celery_app)
    status = res.status
    info = None
    try:
        info = res.result
    except Exception:
        info = None
    return {"job_id": job_id, "status": status, "result": info}

@app.get("/schedules/{schedule_id}")
def get_schedule_full(schedule_id: int, db_s: Session = Depends(get_db_session)):
    sch = crud.get_schedule(db_s, schedule_id)
    if not sch:
        raise HTTPException(404, "schedule not found")
    shift_map = {s.id: s for s in db_s.query(models.Shift).filter(models.Shift.project_id == sch.project_id).all()}
    agent_map = {a.id: a for a in db_s.query(models.Agent).filter(models.Agent.project_id == sch.project_id).all()}

    enriched = []
    for a in sch.assignments:
        s = shift_map.get(a.shift_id)
        ag = agent_map.get(a.agent_id)
        enriched.append({
            "date": a.date.isoformat(),
            "shift_id": a.shift_id,
            "shift_name": s.name if s else None,
            "shift_start": s.start_time.strftime("%H:%M") if s else None,
            "shift_end": s.end_time.strftime("%H:%M") if s else None,
            "shift_crosses_midnight": s.crosses_midnight if s else False,
            "agent_id": a.agent_id,
            "agent_name": ag.name if ag else None,
            "agent_skill": ag.channel_skill if ag else None,
            "role": a.role
        })
    return {
        "schedule": {
            "id": sch.id,
            "project_id": sch.project_id,
            "start_date": sch.start_date.isoformat(),
            "end_date": sch.end_date.isoformat(),
            "generation_metadata": sch.generation_metadata,
            "assignments": enriched
        }
    }
