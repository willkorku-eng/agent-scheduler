import React from "react";
import { Box, Typography, Chip, List, ListItem, ListItemText } from "@mui/material";

type Coverage = {
  date: string;
  shift_id: number;
  shift_name: string;
  required?: { chat?: number; email?: number; total?: number };
  assigned: { chat: number; email: number; both: number; total: number };
};

function statusColor(req: number | undefined, assigned: number) {
  if (req === undefined) return "default";
  if (assigned >= req) return "success";
  const short = req - assigned;
  if (short <= 2) return "warning";
  return "error";
}

export default function CoveragePanel({ coverages }: { coverages: Coverage[] }) {
  return (
    <Box sx={{ p: 1 }}>
      <Typography variant="h6">Coverage Summary</Typography>
      <List dense>
        {coverages.map((c, idx) => (
          <ListItem key={idx} sx={{ borderBottom: "1px solid #eee" }}>
            <ListItemText
              primary={`${c.date} — ${c.shift_name}`}
              secondary={
                <span>
                  <Chip label={`Assigned ${c.assigned.total}`} size="small" sx={{mr:1}} />
                  <Chip label={`Chat ${c.assigned.chat}`} size="small" sx={{mr:1}} />
                  <Chip label={`Email ${c.assigned.email}`} size="small" sx={{mr:1}} />
                  {c.required?.chat !== undefined && (
                    <Chip
                      label={`Req Chat ${c.required.chat}`}
                      size="small"
                      color={statusColor(c.required.chat, c.assigned.chat) as any}
                      sx={{mr:1}}
                    />
                  )}
                  {c.required?.email !== undefined && (
                    <Chip
                      label={`Req Email ${c.required.email}`}
                      size="small"
                      color={statusColor(c.required.email, c.assigned.email) as any}
                    />
                  )}
                </span>
              }
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}
