import React, { useEffect, useState } from "react";
import { Box, Typography, LinearProgress, Button } from "@mui/material";
import client from "../api";

export default function JobStatus({ jobId, onComplete }: { jobId: string | null, onComplete?: (r:any)=>void }) {
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    let t: any = null;
    if (jobId) {
      setStatus("PENDING");
      setResult(null);
      setPolling(true);
      t = setInterval(async () => {
        try {
          const res = await client.get(`/jobs/${jobId}`);
          setStatus(res.data.status);
          setResult(res.data.result);
          if (["SUCCESS", "FAILURE", "REVOKED"].includes(res.data.status) || (res.data.result && (res.data.result.schedule_id || res.data.result.status === "no_solution"))) {
            setPolling(false);
            clearInterval(t);
            if (onComplete) onComplete(res.data.result);
          }
        } catch (e) {
          setStatus("ERROR");
          setPolling(false);
          clearInterval(t);
        }
      }, 2000);
    }
    return () => { if(t) clearInterval(t); };
  }, [jobId]);

  if (!jobId) return <Box>No active job</Box>;

  return (
    <Box>
      <Typography>Job ID: {jobId}</Typography>
      <Typography>Status: {status}</Typography>
      {polling && <LinearProgress sx={{mt:1}} />}
      {result && <pre style={{whiteSpace:"pre-wrap"}}>{JSON.stringify(result, null, 2)}</pre>}
    </Box>
  );
}
