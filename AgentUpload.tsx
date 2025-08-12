import React, { useState } from "react";
import { Box, Button, Typography } from "@mui/material";
import client from "../api";

export default function AgentUpload({ projectId }: { projectId: number }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const doUpload = async () => {
    if (!file) return alert("Choose a CSV file first");
    const fd = new FormData();
    fd.append("file", file);
    setLoading(true);
    try {
      const res = await client.post(`/projects/${projectId}/agents/bulk_upload`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000
      });
      alert(`Uploaded ${res.data.count} agents`);
    } catch (err:any) {
      alert("Upload failed: " + (err?.response?.data || err.message));
    } finally { setLoading(false) }
  };

  return (
    <Box sx={{display:"flex",flexDirection:"column",gap:1}}>
      <Typography variant="body2">CSV columns: name,email,channel_skill,fixed_off_start,fixed_off_end,fixed_shift_id,fixed_shift_start,fixed_shift_end</Typography>
      <input type="file" accept=".csv" onChange={(e)=> setFile(e.target.files ? e.target.files[0] : null)} />
      <Button variant="contained" onClick={doUpload} disabled={!file || loading}>{loading ? "Uploading..." : "Upload CSV"}</Button>
    </Box>
  );
}
