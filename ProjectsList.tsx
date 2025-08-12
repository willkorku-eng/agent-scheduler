import React, { useState } from "react";
import { List, ListItemButton, ListItemText, Box, TextField, Button } from "@mui/material";

type Props = {
  projects: { id: number; name: string }[];
  onSelect: (p: { id: number; name: string }) => void;
};

export default function ProjectsList({ projects, onSelect }: Props) {
  const [manualId, setManualId] = useState("");
  return (
    <Box>
      <List>
        {projects.length === 0 && <Box sx={{p:2}}>No projects returned by backend.</Box>}
        {projects.map((p) => (
          <ListItemButton key={p.id} onClick={() => onSelect(p)}>
            <ListItemText primary={p.name} secondary={`ID: ${p.id}`} />
          </ListItemButton>
        ))}
      </List>

      <Box sx={{ mt: 2, display: "flex", gap: 1 }}>
        <TextField label="Open project by ID" value={manualId} onChange={(e)=>setManualId(e.target.value)} />
        <Button variant="contained" onClick={() => onSelect({ id: Number(manualId), name: `Project ${manualId}` })}>Open</Button>
      </Box>
    </Box>
);
}
