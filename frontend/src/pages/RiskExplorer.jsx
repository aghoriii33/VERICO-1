import React, { useState, useEffect } from "react";
import {
  ShieldAlert, AlertTriangle, AlertCircle, FileText,
  Filter, BookOpen, Loader, BadgeAlert
} from "lucide-react";
import { fetchDocuments, fetchRisks } from "../services/api";

const SEVERITY_BADGES = {
  HIGH: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  MEDIUM: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  LOW: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
};

const RISK_NAMES = {
  unlimited_liability: "Unlimited Liability Clause",
  auto_renewal: "Auto-Renewal Provision",
  no_audit_rights: "Audit Restriction Clause",
  termination_clause: "Immediate Termination Clause",
  data_ownership: "Data Ownership Risk",
  indemnification_waiver: "Indemnification Waiver",
  ml_high_risk: "ML Flagged — High Severity",
  ml_medium_risk: "ML Flagged — Medium Severity",
};

export default function RiskExplorer() {
  const [documents, setDocuments] = useState([]);
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [selectedSeverity, setSelectedSeverity] = useState("");
  const [selectedRiskItem, setSelectedRiskItem] = useState(null);

  useEffect(() => {
    const loadDocs = async () => {
      try {
        const docs = await fetchDocuments();
        setDocuments(docs.filter(d => d.status === "processed"));
      } catch (err) {
        console.error(err);
      }
    };
    loadDocs();
  }, []);

  const loadRisks = async () => {
    setLoading(true);
    try {
      const data = await fetchRisks(selectedDoc || null, selectedSeverity || null);
      setRisks(data);
      setSelectedRiskItem(data.length > 0 ? data[0] : null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadRisks(); }, [selectedDoc, selectedSeverity]);

  return (
    <div className="space-y-6 animate-slide-up">
      {/* ─── Filter Bar ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-4" id="risk-filters">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-indigo-400" />
          <span className="font-semibold text-white">Filter Compliance Risks:</span>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <select
            id="filter-document"
            value={selectedDoc}
            onChange={(e) => setSelectedDoc(e.target.value)}
            className="glass-input px-3 py-2 text-sm bg-slate-900 focus:outline-none"
          >
            <option value="">All Documents</option>
            {documents.map(doc => (
              <option key={doc.id} value={doc.id}>{doc.filename}</option>
            ))}
          </select>

          <select
            id="filter-severity"
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="glass-input px-3 py-2 text-sm bg-slate-900 focus:outline-none"
          >
            <option value="">All Severities</option>
            <option value="HIGH">High Severity</option>
            <option value="MEDIUM">Medium Severity</option>
            <option value="LOW">Low Severity</option>
          </select>
        </div>
      </div>

      {/* ─── Main Grid ──────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-[calc(100vh-20rem)]">
        {/* Risks List */}
        <div className="lg:col-span-2 glass-panel p-6 flex flex-col h-full overflow-hidden">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            Flagged Risk Clauses
            <span className="text-xs font-normal text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
              {risks.length} issues
            </span>
          </h2>

          <div className="flex-1 overflow-y-auto space-y-3 pr-2" id="risk-list">
            {loading ? (
              <div className="flex justify-center items-center py-12">
                <Loader className="h-8 w-8 text-indigo-400 animate-spin" />
              </div>
            ) : risks.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <BadgeAlert className="h-10 w-10 text-slate-700 mx-auto mb-2" />
                <p>No risks flagged with the active filters.</p>
              </div>
            ) : (
              risks.map((risk) => (
                <div
                  key={risk.id}
                  onClick={() => setSelectedRiskItem(risk)}
                  className={`border rounded-xl p-4 cursor-pointer transition-all duration-200 text-left ${
                    selectedRiskItem?.id === risk.id
                      ? "bg-slate-900 border-indigo-500/50 shadow-md"
                      : "bg-slate-900/30 border-slate-800 hover:border-slate-700 hover:bg-slate-900/10"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <h3 className="font-semibold text-white text-sm">
                        {RISK_NAMES[risk.risk_type] || risk.risk_type}
                      </h3>
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <FileText className="h-3 w-3 text-slate-500" />
                        <span className="truncate max-w-[150px] sm:max-w-xs">{risk.document_name}</span>
                        <span>•</span>
                        <span>Page {risk.page_num}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider ${SEVERITY_BADGES[risk.severity]}`}>
                        {risk.severity}
                      </span>
                      <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded font-mono">
                        {risk.classification_method}
                      </span>
                    </div>
                  </div>

                  <p className="text-gray-300 text-xs mt-3 line-clamp-2 italic">
                    &ldquo;{risk.text}&rdquo;
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ─── Clause Detail Panel ──────────────────────────────── */}
        <div className="lg:col-span-1 glass-panel p-6 flex flex-col h-full overflow-hidden">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-indigo-400" /> Clause Detail
          </h2>

          {selectedRiskItem ? (
            <div className="flex-1 flex flex-col justify-between overflow-hidden">
              <div className="space-y-5 overflow-y-auto pr-1">
                {/* Severity Banner */}
                <div className={`p-4 rounded-xl border flex items-center gap-3 ${
                  selectedRiskItem.severity === "HIGH"
                    ? "bg-rose-500/5 border-rose-500/20 text-rose-400"
                    : selectedRiskItem.severity === "MEDIUM"
                    ? "bg-amber-500/5 border-amber-500/20 text-amber-400"
                    : "bg-emerald-500/5 border-emerald-500/20 text-emerald-400"
                }`}>
                  {selectedRiskItem.severity === "HIGH" ? (
                    <ShieldAlert className="h-8 w-8 text-rose-500" />
                  ) : selectedRiskItem.severity === "MEDIUM" ? (
                    <AlertTriangle className="h-8 w-8 text-amber-500" />
                  ) : (
                    <AlertCircle className="h-8 w-8 text-emerald-500" />
                  )}
                  <div>
                    <h3 className="font-bold text-sm text-white">
                      {selectedRiskItem.severity === "HIGH"
                        ? "Critical Audit Alert"
                        : selectedRiskItem.severity === "MEDIUM"
                        ? "Compliance Advisory"
                        : "Low Risk Notice"}
                    </h3>
                    <p className="text-xs mt-0.5">
                      This clause exposes the organization to{" "}
                      {selectedRiskItem.severity === "HIGH" ? "severe" : selectedRiskItem.severity === "MEDIUM" ? "moderate" : "minimal"}{" "}
                      liabilities.
                    </p>
                  </div>
                </div>

                {/* Metadata */}
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">Document name</p>
                    <p className="text-sm font-semibold text-white mt-0.5 flex items-center gap-1.5">
                      <FileText className="h-4 w-4 text-indigo-400" />
                      {selectedRiskItem.document_name}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">Location</p>
                      <p className="text-sm text-white mt-0.5">Page {selectedRiskItem.page_num}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">Confidence</p>
                      <p className="text-sm text-white mt-0.5 font-mono">
                        {(selectedRiskItem.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider">Risk Type</p>
                    <p className="text-sm text-white mt-0.5">
                      {RISK_NAMES[selectedRiskItem.risk_type] || selectedRiskItem.risk_type}
                    </p>
                  </div>
                </div>

                {/* Excerpt */}
                <div>
                  <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wider mb-2">
                    Flagged Clause Excerpt
                  </p>
                  <div className={`p-4 rounded-xl border font-serif leading-relaxed text-sm italic relative ${
                    selectedRiskItem.severity === "HIGH"
                      ? "border-rose-500/20 bg-rose-950/10 text-rose-100"
                      : selectedRiskItem.severity === "MEDIUM"
                      ? "border-amber-500/20 bg-amber-950/10 text-amber-100"
                      : "border-emerald-500/20 bg-emerald-950/10 text-emerald-100"
                  }`}>
                    &ldquo;{selectedRiskItem.text}&rdquo;
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 border border-dashed border-slate-800 rounded-lg p-4">
              <AlertCircle className="h-8 w-8 text-slate-700 mb-2" />
              <p className="text-xs">No risk selected.</p>
              <p className="text-[10px] text-gray-600 mt-1">
                Select a risk card from the left panel to inspect detailed severity audits.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
