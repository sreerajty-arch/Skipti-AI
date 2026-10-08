import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Setup from "@/pages/Setup";
import Context from "@/pages/Context";
import Projects from "@/pages/Projects";
import ProjectDetail from "@/pages/ProjectDetail";
import ProjectHistory from "@/pages/ProjectHistory";
import Playground from "@/pages/Playground";
import Share from "@/pages/Share";
import Connect from "@/pages/Connect";
import Settings from "@/pages/Settings";
import NotFound from "@/pages/NotFound";

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/setup" element={<Setup />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/context" element={<Context />} />
      <Route path="/projects" element={<Projects />} />
      <Route path="/projects/:id" element={<ProjectDetail />} />
      <Route path="/projects/:id/history" element={<ProjectHistory />} />
      <Route path="/playground" element={<Playground />} />
      <Route path="/share" element={<Share />} />
      <Route path="/connect/:token" element={<Connect />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
