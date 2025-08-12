from ortools.sat.python import cp_model
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Tuple

def parse_time_obj(tobj):
    if isinstance(tobj, str):
        h,m = map(int, tobj.split(":"))
        return time(h,m)
    return tobj

def shift_window_for_date(d: date, shift: Dict[str,Any]) -> Tuple[datetime, datetime]:
    st = parse_time_obj(shift['start_time'])
    et = parse_time_obj(shift['end_time'])
    start_dt = datetime.combine(d, st)
    end_dt = datetime.combine(d, et)
    if shift.get('crosses_midnight', False) or end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return start_dt, end_dt

def build_schedule(project_id: int,
                   start_date: date,
                   horizon_days: int,
                   agents: List[Dict[str,Any]],
                   shifts: List[Dict[str,Any]],
                   exceptions: List[Dict[str,Any]],
                   per_shift_requirements: Dict[int, Dict[str,Any]],
                   previous_metrics: Dict[int, Dict[str,int]] = None,
                   solver_time_limit: int = 60) -> Dict[str,Any]:
    if previous_metrics is None:
        previous_metrics = {}

    model = cp_model.CpModel()
    agent_ids = [a['id'] for a in agents]
    shift_ids = [s['id'] for s in shifts]
    roles = ['chat','email']

    assign = {}
    for a in agents:
        for day in range(horizon_days):
            for s in shifts:
                for r in roles:
                    skill = a['channel_skill']
                    if skill == 'chat' and r == 'email': continue
                    if skill == 'email' and r == 'chat': continue
                    assign[(a['id'], day, s['id'], r)] = model.NewBoolVar(f"a{a['id']}_d{day}_s{s['id']}_r{r}")

    for a in agent_ids:
        for day in range(horizon_days):
            vars_day = [v for k,v in assign.items() if k[0]==a and k[1]==day]
            if vars_day:
                model.Add(sum(vars_day) <= 1)

    for ex in exceptions:
        if ex['type'] == 'fixed_off':
            a = ex['agent_id']; s_date = ex['start_date']; e_date = ex['end_date']
            for day in range(horizon_days):
                d = start_date + timedelta(days=day)
                if s_date <= d <= e_date:
                    for sid in shift_ids:
                        for r in roles:
                            var = assign.get((a, day, sid, r))
                            if var is not None: model.Add(var == 0)
        elif ex['type'] == 'fixed_shift':
            a = ex['agent_id']; sid_fixed = ex['shift_id']; s_date = ex['start_date']; e_date = ex['end_date']
            for day in range(horizon_days):
                d = start_date + timedelta(days=day)
                if s_date <= d <= e_date:
                    allowed = []
                    for r in roles:
                        v = assign.get((a, day, sid_fixed, r))
                        if v is not None:
                            allowed.append(v)
                    if allowed:
                        model.Add(sum(allowed) == 1)
                    for sid in shift_ids:
                        if sid == sid_fixed: continue
                        for r in roles:
                            v = assign.get((a, day, sid, r))
                            if v is not None: model.Add(v == 0)

    unmet_vars = []
    big_penalty = 10000
    for day in range(horizon_days):
        for s in shifts:
            sid = s['id']
            chat_vars = []
            email_vars = []
            for a in agent_ids:
                vch = assign.get((a, day, sid, 'chat'))
                if vch is not None: chat_vars.append(vch)
                vem = assign.get((a, day, sid, 'email'))
                if vem is not None: email_vars.append(vem)
            req = per_shift_requirements.get(sid, {})
            chat_min = req.get('chat_min', 0)
            email_min = req.get('email_min', 0)
            total_target = req.get('total', None)
            if chat_min > 0:
                u = model.NewIntVar(0, len(agent_ids), f"unmet_chat_{day}_{sid}")
                model.Add(sum(chat_vars) + u >= chat_min)
                unmet_vars.append((u, big_penalty))
            if email_min > 0:
                u = model.NewIntVar(0, len(agent_ids), f"unmet_email_{day}_{sid}")
                model.Add(sum(email_vars) + u >= email_min)
                unmet_vars.append((u, big_penalty))
            if total_target is not None:
                u = model.NewIntVar(0, len(agent_ids), f"unmet_total_{day}_{sid}")
                model.Add(sum(chat_vars + email_vars) + u >= total_target)
                unmet_vars.append((u, big_penalty))

    windows = {}
    for day in range(horizon_days):
        d = start_date + timedelta(days=day)
        for s in shifts:
            windows[(day, s['id'])] = shift_window_for_date(d, s)

    for day1 in range(horizon_days):
        for s1 in shifts:
            sid1 = s1['id']; st1, ed1 = windows[(day1, sid1)]
            for day2 in range(horizon_days):
                for s2 in shifts:
                    sid2 = s2['id']
                    if (day2, sid2) <= (day1, sid1): continue
                    st2, ed2 = windows[(day2, sid2)]
                    overlap = not (ed1 <= st2 or ed2 <= st1)
                    if overlap:
                        for a in agent_ids:
                            vars_pair = []
                            for r in roles:
                                v1 = assign.get((a, day1, sid1, r))
                                if v1 is not None: vars_pair.append(v1)
                                v2 = assign.get((a, day2, sid2, r))
                                if v2 is not None: vars_pair.append(v2)
                            if len(vars_pair) >= 2:
                                model.Add(sum(vars_pair) <= 1)

    night_shift_ids = [s['id'] for s in shifts if s['name'].lower().startswith('night')]
    night_count_vars = {}
    for a in agent_ids:
        nvar = model.NewIntVar(0, horizon_days, f"n_a{a}")
        night_count_vars[a] = nvar
        night_vars = []
        for day in range(horizon_days):
            for sid in night_shift_ids:
                for r in roles:
                    v = assign.get((a, day, sid, r))
                    if v is not None: night_vars.append(v)
        if night_vars:
            model.Add(nvar == sum(night_vars))
        else:
            model.Add(nvar == 0)

    obj_terms = []
    for u,pen in unmet_vars:
        obj_terms.append(u * pen)

    for a in agent_ids:
        prev_n = previous_metrics.get(a, {}).get('nights', 0)
        alpha = 2
        weight = 1 + alpha * prev_n
        obj_terms.append(night_count_vars[a] * weight)

    model.Minimize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = solver_time_limit
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    st_name = solver.StatusName(status)
    assignments = []
    if st_name in ('OPTIMAL','FEASIBLE'):
        for day in range(horizon_days):
            for s in shifts:
                for a in agents:
                    for r in roles:
                        v = assign.get((a['id'], day, s['id'], r))
                        if v is not None and solver.Value(v) == 1:
                            assignments.append({'date': (start_date + timedelta(days=day)).isoformat(), 'shift_id': s['id'], 'agent_id': a['id'], 'role': r})
    metrics = {'status': st_name, 'objective': solver.ObjectiveValue() if st_name in ('OPTIMAL','FEASIBLE') else None}
    return {'assignments': assignments, 'metrics': metrics}
