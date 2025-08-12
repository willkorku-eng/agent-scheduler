import os
from celery import Celery
from datetime import date, timedelta
from . import db, crud, scheduler_engine, models
from sqlalchemy.orm import Session

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://scheduler:scheduler@localhost:5432/scheduler")

celery_app = Celery("scheduler_tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(bind=True)
def run_schedule_task(self, project_id: int, start_date_str: str, horizon_days: int, per_shift_reqs: dict, solver_time_limit: int = 120):
    start_date = date.fromisoformat(start_date_str)
    session = next(db.get_db())
    try:
        proj = crud.get_project(session, project_id)
        if not proj:
            return {"status": "error", "message": "project_not_found"}

        agents = crud.list_agents(session, project_id)
        shifts = crud.get_shifts(session, project_id)
        exceptions = []
        for ag in agents:
            for ex in ag.exceptions:
                exceptions.append({"agent_id": ag.id, "type": ex.type, "start_date": ex.start_date, "end_date": ex.end_date, "shift_id": ex.shift_id})

        agents_dicts = [{"id": a.id, "name": a.name, "channel_skill": a.channel_skill} for a in agents]
        shifts_dicts = [{"id": s.id, "name": s.name, "start_time": s.start_time, "end_time": s.end_time, "crosses_midnight": s.crosses_midnight} for s in shifts]

        prev_metrics = {}
        last_sch = session.query(models.Schedule).filter(models.Schedule.project_id==project_id).order_by(models.Schedule.generated_at.desc()).first()
        if last_sch:
            from collections import defaultdict
            cnt = defaultdict(int)
            for a in last_sch.assignments:
                s = session.get(models.Shift, a.shift_id)
                if s and s.name.lower().startswith("night"):
                    cnt[a.agent_id] += 1
            prev_metrics = {ag['id']: {"nights": cnt.get(ag['id'], 0)} for ag in agents_dicts}
        else:
            prev_metrics = {ag['id']: {"nights": 0} for ag in agents_dicts}

        sol = scheduler_engine.build_schedule(
            project_id=project_id,
            start_date=start_date,
            horizon_days=horizon_days,
            agents=agents_dicts,
            shifts=shifts_dicts,
            exceptions=exceptions,
            per_shift_requirements=per_shift_reqs,
            previous_metrics=prev_metrics,
            solver_time_limit=solver_time_limit
        )

        assigns = sol.get("assignments", [])
        if assigns:
            end_date = start_date + timedelta(days=horizon_days - 1)
            gen_meta = {"per_shift_requirements": per_shift_reqs, "metrics": sol.get("metrics")}
            sch = crud.persist_schedule(session, project_id, start_date, end_date, gen_meta, assigns)
            return {"status": sol.get("metrics", {}).get("status", "finished"), "schedule_id": sch.id, "metrics": sol.get("metrics")}
        else:
            return {"status": "no_solution", "metrics": sol.get("metrics")}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            session.close()
        except:
            pass
