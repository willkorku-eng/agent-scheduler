import React from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline } from "@mui/material";
import App from "./App";

import "@fullcalendar/common/index.css";
import "@fullcalendar/daygrid/index.css";
import "@fullcalendar/timegrid/index.css";
import "tippy.js/dist/tippy.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <CssBaseline />
    <App />
  </React.StrictMode>
);
