import React, { useState } from "react";
import { LayoutDashboard, HelpCircle, ShieldAlert, Sparkles } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import QA from "./pages/QA";
import RiskExplorer from "./pages/RiskExplorer";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "qa", label: "Query Panel", icon: HelpCircle },
    { id: "risks", label: "Risk Audit", icon: ShieldAlert },
  ];

  return (
    <div className="min-h-screen bg-transparent text-slate-100 flex flex-col">
      {/* ─── Top Navbar ──────────────────────────────────────────── */}
      <header className="glass-panel rounded-none border-t-0 border-x-0 border-b border-slate-800/80 sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 text-white shadow-lg shadow-indigo-500/20">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-tight text-gradient flex items-center gap-1.5">
              VERICO
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 tracking-wider">
                v1.0
              </span>
            </span>
            <p className="text-[10px] text-slate-500 font-medium tracking-wide">
              AI-Powered QA & Risk Detection
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center gap-2">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              id={`nav-${id}`}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 ${
                activeTab === id
                  ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 shadow-sm"
                  : "text-gray-400 hover:text-slate-200 border border-transparent hover:bg-slate-800/50"
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </header>

      {/* ─── Main Content ────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        <div className="animate-fade-in">
          {activeTab === "dashboard" && <Dashboard />}
          {activeTab === "qa" && <QA />}
          {activeTab === "risks" && <RiskExplorer />}
        </div>
      </main>

      {/* ─── Footer ──────────────────────────────────────────────── */}
      <footer className="text-center py-4 text-[10px] text-slate-600 border-t border-slate-900">
        Powered by FAISS · SentenceTransformers · DistilBERT · FastAPI
      </footer>
    </div>
  );
}
