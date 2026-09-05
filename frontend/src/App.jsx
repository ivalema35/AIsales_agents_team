import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { LogOut } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import CampaignDetail from "./pages/CampaignDetail";
import Products from "./pages/Products";
import Leads from "./pages/Leads";
import LeadDetail from "./pages/LeadDetail";
import Settings from "./pages/Settings";
import Analytics from "./pages/Analytics";
import WhatsappTemplates from "./pages/WhatsappTemplates";
import SocialQueue from "./pages/SocialQueue";
import ProspectFinder from "./pages/ProspectFinder";
import SystemMonitor from "./pages/SystemMonitor";
import Login from "./pages/Login";
import SystemStatusDot from "./components/SystemStatusDot";
import { ConfirmProvider } from "./lib/ConfirmContext";
import { ToastProvider } from "./lib/ToastContext";
import { api } from "./api/client";

function Nav({ onLogout }) {
  // shrink-0 + whitespace-nowrap on every item -- without them a crowded bar squeezes
  // "AI-BOS" / "WA Templates" / "Log out" into ugly mid-word wraps (seen live).
  const linkClass = ({ isActive }) =>
    `shrink-0 whitespace-nowrap rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-colors ${
      isActive ? "bg-ink-900 text-parchment-raised" : "text-ink-500 hover:bg-parchment-raised-2 hover:text-ink-900"
    }`;

  return (
    <nav className="sticky top-0 z-10 border-b border-line bg-parchment-raised/95 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4 sm:px-6">
        {/* Brand lockup: logo PNG has a white square bake-in -- mix-blend-multiply
           drops that white against parchment so the "A" mark sits clean, not in a
           white tile. Wordmark stays one line; never let the lockup shrink. */}
        <NavLink to="/" end className="flex shrink-0 items-center gap-2.5 whitespace-nowrap">
          <img
            src="/logo.png"
            alt=""
            className="h-8 w-8 object-contain mix-blend-multiply"
          />
          <span className="font-display text-[15px] font-semibold tracking-tight text-ink-900">
            AI-BOS
          </span>
        </NavLink>

        {/* Links can scroll horizontally on a tight viewport rather than wrapping the bar. */}
        <div className="flex min-w-0 flex-1 items-center gap-0.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <NavLink to="/" end className={linkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/products" className={linkClass}>
            Products
          </NavLink>
          <NavLink to="/whatsapp-templates" className={linkClass}>
            Templates
          </NavLink>
          <NavLink to="/social-queue" className={linkClass}>
            Social
          </NavLink>
          <NavLink to="/leads" className={linkClass}>
            Leads
          </NavLink>
          <NavLink to="/prospects" className={linkClass}>
            Prospects
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
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <SystemStatusDot />
          <button
            onClick={onLogout}
            title="Log out"
            className="flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-md px-2.5 py-1.5 text-[13px] font-medium text-ink-500 transition-colors hover:bg-parchment-raised-2 hover:text-alert-600"
          >
            <LogOut size={15} className="shrink-0" />
            <span className="hidden sm:inline">Log out</span>
          </button>
        </div>
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
    return <div className="min-h-screen bg-parchment" />; // avoid a login-page flash while checking
  }

  if (!authed) {
    return <Login onLoggedIn={() => setAuthed(true)} />;
  }

  return (
    <BrowserRouter>
      <ToastProvider>
        <ConfirmProvider>
          <div className="min-h-screen bg-parchment">
            <Nav onLogout={handleLogout} />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/campaigns/:id" element={<CampaignDetail />} />
              <Route path="/products" element={<Products />} />
              <Route path="/leads" element={<Leads />} />
              <Route path="/leads/:id" element={<LeadDetail />} />
              <Route path="/prospects" element={<ProspectFinder />} />
              <Route path="/whatsapp-templates" element={<WhatsappTemplates />} />
              <Route path="/social-queue" element={<SocialQueue />} />
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
