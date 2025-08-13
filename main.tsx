import React from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline } from "@mui/material";
import App from "./App";

import "@fullcalendar/common";
import "@fullcalendar/daygrid";
import "@fullcalendar/timegrid";
import "tippy.js/dist/tippy.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <CssBaseline />
    <App />
  </React.StrictMode>
);
