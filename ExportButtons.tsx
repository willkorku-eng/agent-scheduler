import React from "react";
import { Button } from "@mui/material";
import Papa from "papaparse";
import fileDownload from "js-file-download";
import jsPDF from "jspdf";
import "jspdf-autotable";
import html2canvas from "html2canvas";

type Assignment = {
  date: string;
  shift_name: string;
  shift_start: string;
  shift_end: string;
  agent_id: number;
  agent_name: string;
  agent_skill: string;
  role: string;
};

export default function ExportButtons({ assignments, projectName }: { assignments: Assignment[], projectName?: string }) {

  const exportCSV = () => {
    const rows = assignments.map(a => ({
      project: projectName || "",
      date: a.date,
      shift: a.shift_name,
      start: a.shift_start,
      end: a.shift_end,
      agent_id: a.agent_id,
      agent_name: a.agent_name,
      skill: a.agent_skill,
      role: a.role
    }));
    const csv = Papa.unparse(rows);
    fileDownload(csv, `schedule_${projectName || "project"}_${new Date().toISOString().slice(0,10)}.csv`);
  };

  const exportPDF = async () => {
    const doc = new jsPDF({ orientation: "landscape" });
    const head = [["Date","Shift","Start","End","Agent","Skill","Role"]];
    const body = assignments.map(a => [a.date, a.shift_name, a.shift_start, a.shift_end, a.agent_name, a.agent_skill, a.role]);
    (doc as any).autoTable({
      head,
      body,
      startY: 20,
      styles: { fontSize: 9 }
    });
    doc.text(`Schedule export — ${projectName || ""}`, 14, 12);
    doc.save(`schedule_${projectName || "project"}_${new Date().toISOString().slice(0,10)}.pdf`);
  };

  return (
    <>
      <Button variant="outlined" onClick={exportCSV}>Export CSV</Button>
      <Button variant="contained" onClick={exportPDF}>Export PDF</Button>
    </>
  );
}
