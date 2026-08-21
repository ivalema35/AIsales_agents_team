import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { LogOut } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Products from "./pages/Products";
import Leads from "./pages/Leads";
import LeadDetail from "./pages/LeadDetail";
import Settings from "./pages/Settings";
import Analytics from "./pages/Analytics";
import WhatsappTemplates from "./pages/WhatsappTemplates";
import SystemMonitor from "./pages/SystemMonitor";
import Login from "./pages/Login";
import SystemStatusDot from "./components/SystemStatusDot";
import { ConfirmProvider } from "./lib/ConfirmContext";
import { ToastProvider } from "./lib/ToastContext";
import { api } from "./api/client";

function Nav({ onLogout }) {
  const linkClass = ({ isActive }) =>
    `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
      isActive ? "bg-slate-800 text-white" : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
    }`;

  return (
    <nav className="sticky top-0 z-10 border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center gap-2 px-6 py-3">
        <div className="mr-6 flex items-center gap-2">
          <img src="/logo.png" alt="AI-BOS" className="h-7 w-7" />
          <span className="text-sm font-semibold tracking-tight text-slate-900">AI-BOS</span>
        </div>
        <NavLink to="/" end className={linkClass}>
          Dashboard
        </NavLink>
        <NavLink to="/products" className={linkClass}>
          Products
        </NavLink>
        <NavLink to="/whatsapp-templates" className={linkClass}>
          WA Templates
        </NavLink>
        <NavLink to="/leads" className={linkClass}>
          Leads
        </NavLink>
        <NavLink to="/analytics" className={linkClass}>
          Analytics
        </NavLink>
        <NavLink to="/settings" className={linkClass}>
          Settings
        </NavLink>
        <NavLink to="/system" className={linkClass}>
          System
        </NavLink>
        <SystemStatusDot />
        <button
          onClick={onLogout}
          title="Log out"
          className="ml-auto flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-red-600"
        >
          <LogOut size={15} />
          Log out
        </button>
      </div>
    </nav>
  );
}

// Gates the whole app behind a real backend session (api.py's before_request hook
// rejects every non-public route with 401 when unauthenticated) -- this isn't a
// decorative client-side check, the server enforces it independently either way; this
// just decides whether to render the app shell or the login screen.
export default function App() {
  const [authed, setAuthed] = useState(null); // null = still checking

  useEffect(() => {
    api.getMe().then((r) => setAuthed(r.authenticated)).catch(() => setAuthed(false));
  }, []);

  async function handleLogout() {
    await api.logout().catch(() => {});
    setAuthed(false);
  }

  if (authed === null) {
    return <div className="min-h-screen bg-slate-50" />; // avoid a login-page flash while checking
  }

  if (!authed) {
    return <Login onLoggedIn={() => setAuthed(true)} />;
  }

  return (
    <BrowserRouter>
      <ToastProvider>
        <ConfirmProvider>
          <div className="min-h-screen bg-slate-50">
            <Nav onLogout={handleLogout} />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/products" element={<Products />} />
              <Route path="/leads" element={<Leads />} />
              <Route path="/leads/:id" element={<LeadDetail />} />
              <Route path="/whatsapp-templates" element={<WhatsappTemplates />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/system" element={<SystemMonitor />} />
            </Routes>
          </div>
        </ConfirmProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
