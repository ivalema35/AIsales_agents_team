import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Products from "./pages/Products";
import Leads from "./pages/Leads";
import LeadDetail from "./pages/LeadDetail";
import Settings from "./pages/Settings";
import Analytics from "./pages/Analytics";
import { ConfirmProvider } from "./lib/ConfirmContext";

function Nav() {
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
        <NavLink to="/leads" className={linkClass}>
          Leads
        </NavLink>
        <NavLink to="/analytics" className={linkClass}>
          Analytics
        </NavLink>
        <NavLink to="/settings" className={linkClass}>
          Settings
        </NavLink>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ConfirmProvider>
        <div className="min-h-screen bg-slate-50">
          <Nav />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/leads" element={<Leads />} />
            <Route path="/leads/:id" element={<LeadDetail />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </div>
      </ConfirmProvider>
    </BrowserRouter>
  );
}
