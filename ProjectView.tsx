import React, { useEffect, useState } from "react";
import {
  Box, Typography, Button, Paper, Grid, TextField, CircularProgress, Divider
} from "@mui/material";
import client from "../api";
import AgentUpload from "./AgentUpload";
import JobStatus from "./JobStatus";
import CalendarViewFull from "./CalendarViewFull";

type Props = { project: { id: number; name: string }, onBack: () => void };

type ShiftReq = { shift_id: number; chat_min: number; email_min: number; total?: number };

export default function ProjectView({ project, onBack }: Props) {
  const [shifts, setShifts] = useState<{id:number, name:string}[]>([]);
  const [perShiftReqs, setPerShiftReqs] = useState<ShiftReq[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<any>(null);
  const [scheduleId, setScheduleId] = useState<number | null>(null);
  const [loadingShifts, setLoadingShifts] = useState(false);

  useEffect(() => {
    async function loadShifts(){
      setLoadingShifts(true);
      try{
        const res = await client.get(`/projects/${project.id}/shifts`);
        setShifts(res.data || []);
        if(!perShiftReqs.length && Array.isArray(res.data)){
          setPerShiftReqs(res.data.map((s:any) => ({shift_id: s.id, chat_min: 0, email_min:0, total: 0})));
        }
      }catch(e){
        console.error(e);
      }finally{ setLoadingShifts(false) }
    }
    loadShifts();
  }, [project]);

  const submitJob = async (startDateStr: string, horizonDays = 14, solverTimeLimit=120) => {
    const body = {
      start_date: startDateStr,
      horizon_days: horizonDays,
      per_shift_requirements: perShiftReqs,
      solver_time_limit: solverTimeLimit
    };
    try {
      const res = await client.post(`/projects/${project.id}/generate_schedule_async`, body);
      setJobId(res.data.job_id);
      setJobResult(null);
      setScheduleId(null);
    } catch (err:any) {
      alert("Failed to start job: "+(err?.response?.data?.detail || err.message));
    }
  };

  return (
    <Box>
      <Button onClick={onBack}>← Back to projects</Button>
      <Typography variant="h5" gutterBottom>{project.name} (ID: {project.id})</Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} md={5}>
          <Paper sx={{p:2}}>
            <Typography variant="h6">Agent CSV Upload</Typography>
            <AgentUpload projectId={project.id} />
            <Divider sx={{my:2}} />
            <Typography variant="h6">Generate schedule (async)</Typography>
            {loadingShifts ? <CircularProgress /> : (
              <>
                <Typography variant="subtitle2">Per-shift targets</Typography>
                {perShiftReqs.map((r, idx)=> {
                  const s = shifts.find(x => x.id === r.shift_id);
                  return (
                    <Box key={r.shift_id} sx={{display:'flex',gap:1,alignItems:'center',mt:1}}>
                      <TextField label="Shift" value={s? s.name : r.shift_id} disabled sx={{minWidth:140}} />
                      <TextField type="number" label="Chat min" value={r.chat_min} onChange={(e)=> {
                        const v = Math.max(0, Number(e.target.value||0));
                        setPerShiftReqs(ps => ps.map((p,i)=> i===idx? {...p, chat_min:v}:p));
                      }} />
                      <TextField type="number" label="Email min" value={r.email_min} onChange={(e)=> {
                        const v = Math.max(0, Number(e.target.value||0));
                        setPerShiftReqs(ps => ps.map((p,i)=> i===idx? {...p, email_min:v}:p));
                      }} />
                      <TextField type="number" label="Total (optional)" value={r.total} onChange={(e)=> {
                        const v = e.target.value===""? undefined: Math.max(0, Number(e.target.value||0));
                        setPerShiftReqs(ps => ps.map((p,i)=> i===idx? {...p, total:v}:p));
                      }} />
                    </Box>
                  );
                })}
                <Box sx={{mt:2}}>
                  <TextField id="startDate" label="Start date (YYYY-MM-DD)" fullWidth />
                  <Button sx={{mt:1}} variant="contained" onClick={()=>{
                    const el:any = document.getElementById("startDate");
                    const v = el?.value;
                    if(!v) return alert("Enter start date in YYYY-MM-DD");
                    submitJob(v, 14, 120);
                  }}>Start generation</Button>
                </Box>
              </>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={7}>
          <Paper sx={{p:2}}>
            <Typography variant="h6">Job status & schedule</Typography>
            <JobStatus jobId={jobId} onComplete={(result:any)=>{
              setJobResult(result);
              if(result?.schedule_id) setScheduleId(result.schedule_id);
            }} />
            <Divider sx={{my:2}} />
            <Typography variant="h6">Schedule calendar</Typography>
            {scheduleId ? <CalendarViewFull scheduleId={scheduleId} projectName={project.name} /> : <Box sx={{p:2}}>No schedule selected — start generation to create one.</Box>}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
