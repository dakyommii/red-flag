import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import CaseSelect from "./pages/CaseSelect";
import CaseBriefing from "./pages/CaseBriefing";
import InvestigationPage from "./pages/InvestigationPage";
import FinalDecisionPage from "./pages/FinalDecisionPage";
import CaseReportPage from "./pages/CaseReportPage";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CaseSelect />} />
        <Route path="/session/:sessionId/briefing" element={<CaseBriefing />} />
        <Route path="/session/:sessionId/investigate" element={<InvestigationPage />} />
        <Route path="/session/:sessionId/decision" element={<FinalDecisionPage />} />
        <Route path="/session/:sessionId/report" element={<CaseReportPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
