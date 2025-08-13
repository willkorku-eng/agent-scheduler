import React, { useEffect, useState, useRef } from "react";
import FullCalendar, { EventInput } from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid/main.css";
import dayGridPlugin from "@fullcalendar/daygrid/main.css";
import interactionPlugin from "@fullcalendar/interaction";
import client from "../api";
import dayjs from "dayjs";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import { Box, Dialog, DialogTitle, DialogContent, Typography, Alert } from "@mui/material";
import { SKILL_COLOR, eventIdFor } from "./utils";
import ExportButtons from "./ExportButtons";
import CoveragePanel from "./CoveragePanel";

type Assignment = {
  date: string;
  shift_id: number;
  shift_name: string;
  shift_start: string;
  shift_end: string;
  shift_crosses_midnight: boolean;
  agent_id: number;
  agent_name: string;
  agent_skill: string;
  role: string;
};

export default function CalendarViewFull({ scheduleId, projectName }: { scheduleId: number, projectName?: string }) {
  const [events, setEvents] = useState<EventInput[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [conflicts, setConflicts] = useState<string[]>([]);
  const calendarRef = useRef<any>(null);
  const [selected, setSelected] = useState<Assignment | null>(null);
  const [coverages, setCoverages] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      if (!scheduleId) return;
      try {
        const res = await client.get(`/schedules/${scheduleId}`);
        const sch = res.data.schedule;
        const ass: Assignment[] = sch.assignments;
        setAssignments(ass);

        const evs: EventInput[] = ass.map(a => {
          const start = dayjs(`${a.date}T${a.shift_start}`);
          let end = dayjs(`${a.date}T${a.shift_end}`);
          if (a.shift_crosses_midnight || end.isBefore(start) || end.isSame(start)) end = end.add(1, "day");
          const skill = (a.agent_skill || "unknown").toLowerCase();
          const color = SKILL_COLOR[skill] || SKILL_COLOR.unknown;
          return {
            id: eventIdFor(a),
            title: `${a.agent_name} • ${a.role}`,
            start: start.toISOString(),
            end: end.toISOString(),
            backgroundColor: color,
            borderColor: color,
            textColor: "#fff",
            extendedProps: a
          };
        });
        setEvents(evs);

        const warnings = detectConflicts(ass);
        setConflicts(warnings);

        const groups = new Map();
        ass.forEach(a => {
          const key = `${a.date}::${a.shift_id}`;
          const cur = groups.get(key) || { date: a.date, shift_id: a.shift_id, shift_name: a.shift_name, assigned: { chat:0, email:0, both:0, total:0 } };
          const skill = (a.agent_skill || "both").toLowerCase();
          if (skill === "chat") cur.assigned.chat++;
          else if (skill === "email") cur.assigned.email++;
          else cur.assigned.both++;
          cur.assigned.total++;
          groups.set(key, cur);
        });
        setCoverages(Array.from(groups.values()));

      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, [scheduleId]);

  function detectConflicts(asg: Assignment[]): string[] {
    const map = new Map();
    asg.forEach(a => {
      const start = dayjs(`${a.date}T${a.shift_start}`);
      let end = dayjs(`${a.date}T${a.shift_end}`);
      if (a.shift_crosses_midnight || end.isBefore(start) || end.isSame(start)) end = end.add(1, "day");
      const arr = map.get(a.agent_id) || [];
      arr.push({ start, end, shiftName: a.shift_name, date: a.date });
      map.set(a.agent_id, arr);
    });

    const warnings = [];
    for (const [agentId, windows] of map.entries()) {
      for (let i = 0; i < windows.length; i++) {
        for (let j = i + 1; j < windows.length; j++) {
          const a = windows[i];
          const b = windows[j];
          const overlap = !(a.end.isSameOrBefore(b.start) || b.end.isSameOrBefore(a.start));
          if (overlap) {
            warnings.push(`Agent ${agentId} has overlapping shifts: ${a.shiftName} (${a.date}) and ${b.shiftName} (${b.date})`);
          }
        }
      }
    }
    return warnings;
  }

  const handleEventMount = (info: any) => {
    const a: Assignment = info.event.extendedProps;
    const coverage = coverages.find((c:any) => c.date === a.date && c.shift_id === a.shift_id);
    const html = coverage ? `Assigned: ${coverage.assigned.total}\nChat: ${coverage.assigned.chat}\nEmail: ${coverage.assigned.email}\nBoth: ${coverage.assigned.both}` : `Assigned: —`;
    tippy(info.el, { content: html, placement: "top", animation: "shift-away", allowHTML: false });
    const hasConflict = conflicts.some(w => w.includes(`Agent ${a.agent_id} `));
    if (hasConflict) {
      (info.el as HTMLElement).style.border = "3px solid red";
      (info.el as HTMLElement).style.boxShadow = "0 0 8px rgba(255,0,0,0.5)";
    }
  };

  const handleEventClick = (clickInfo: any) => {
    setSelected(clickInfo.event.extendedProps as Assignment);
  };

  return (
    <Box sx={{ display: "flex", gap: 2 }}>
      <Box sx={{ flex: 1 }}>
        {conflicts.length > 0 && (
          <Alert severity="warning" sx={{ mb: 1 }}>
            {conflicts.length} conflict(s) detected. See details to resolve.
          </Alert>
        )}
        <FullCalendar
          ref={calendarRef}
          plugins={[timeGridPlugin, dayGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "timeGridWeek,timeGridDay,dayGridMonth"
          }}
          events={events}
          eventMount={handleEventMount}
          eventClick={handleEventClick}
          height="auto"
          slotMinTime="00:00:00"
          slotMaxTime="24:00:00"
        />
        <Box sx={{ mt: 1 }}>
          <ExportButtons assignments={assignments.map(a => ({
            date: a.date, shift_name: a.shift_name, shift_start: a.shift_start, shift_end: a.shift_end, agent_id: a.agent_id, agent_name: a.agent_name, agent_skill: a.agent_skill, role: a.role
          }))} projectName={projectName} />
        </Box>
      </Box>

      <Box sx={{ width: 360 }}>
        <CoveragePanel coverages={coverages.map((c:any) => ({
          date: c.date, shift_id: c.shift_id, shift_name: c.shift_name, assigned: c.assigned, required: undefined
        }))} />
      </Box>

      <Dialog open={!!selected} onClose={() => setSelected(null)}>
        <DialogTitle>Assignment details</DialogTitle>
        <DialogContent>
          {selected && (
            <>
              <Typography><strong>Agent:</strong> {selected.agent_name} (#{selected.agent_id})</Typography>
              <Typography><strong>Skill:</strong> {selected.agent_skill}</Typography>
              <Typography><strong>Role:</strong> {selected.role}</Typography>
              <Typography><strong>Shift:</strong> {selected.shift_name} — {selected.shift_start} → {selected.shift_end}{selected.shift_crosses_midnight ? " (crosses midnight)" : ""}</Typography>
              <Typography><strong>Date:</strong> {selected.date}</Typography>
            </>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
