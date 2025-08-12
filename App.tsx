import React, { useEffect, useState } from "react";
import { Box, Container, Typography, AppBar, Toolbar, Button } from "@mui/material";
import ProjectsList from "./components/ProjectsList";
import ProjectView from "./components/ProjectView";
import client from "./api";

type Project = { id: number; name: string; max_agents?: number };

export default function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await client.get("/projects");
        if (Array.isArray(res.data)) setProjects(res.data);
      } catch (e) {
        setProjects([]);
      }
    }
    load();
  }, []);

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flex: 1 }}>Scheduling Admin</Typography>
          <Button color="inherit" href="/docs" target="_blank">API Docs</Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 3 }}>
        {!selected ? (
          <>
            <Typography variant="h5" gutterBottom>Projects</Typography>
            <ProjectsList projects={projects} onSelect={(p) => setSelected(p)} />
          </>
        ) : (
          <ProjectView project={selected} onBack={() => setSelected(null)} />
        )}
      </Container>
    </Box>
  );
}
