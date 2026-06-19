import React, { useState, useEffect } from "react";
import {
  FileText, ShieldAlert, AlertTriangle, AlertCircle,
  Trash2, Loader, RefreshCw, FileUp, Sparkles, TrendingUp
} from "lucide-react";
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
  Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid
} from "recharts";
import { fetchDocuments, uploadDocuments, deleteDocument } from "../services/api";

const COLORS = {
  HIGH: "#f43f5e",
  MEDIUM: "#f59e0b",
  LOW: "#10b981",
};

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleFileDrop = async (e) => {
    e.preventDefault();
    setDragOver(false);
    setUploadError(null);
    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;
    await uploadFiles(files);
  };

  const handleFileSelect = async (e) => {
    setUploadError(null);
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    await uploadFiles(files);
  };

  const uploadFiles = async (files) => {
    const pdfs = files.filter(f => f.name.toLowerCase().endsWith(".pdf"));
    if (pdfs.length === 0) {
      setUploadError("Only PDF files are supported.");
      return;
    }
    setUploading(true);
    try {
      await uploadDocuments(pdfs);
      await loadData();
    } catch (err) {
      setUploadError("Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = (doc) => {
    setDeleteTarget(doc);
  };

  // ─── Aggregation ────────────────────────────────────────────────
  const totalDocs = documents.length;
  const processedDocs = documents.filter(d => d.status === "processed");
  const totalRisks = processedDocs.reduce((a, d) => a + (d.total_risks || 0), 0);
  const highRisks = processedDocs.reduce((a, d) => a + (d.high_risks || 0), 0);
  const mediumRisks = processedDocs.reduce((a, d) => a + (d.medium_risks || 0), 0);
  const lowRisks = processedDocs.reduce((a, d) => a + (d.low_risks || 0), 0);

  const riskData = [
    { name: "High Severity", value: highRisks, color: COLORS.HIGH },
    { name: "Medium Severity", value: mediumRisks, color: COLORS.MEDIUM },
    { name: "Low Severity", value: lowRisks, color: COLORS.LOW },
  ].filter(item => item.value > 0);

  const documentRiskData = processedDocs.map(d => ({
    name: d.filename.length > 20 ? d.filename.substring(0, 17) + "..." : d.filename,
    High: d.high_risks || 0,
    Medium: d.medium_risks || 0,
    Low: d.low_risks || 0,
  }));

  const statCards = [
    { label: "Total Documents", value: totalDocs, icon: FileText, color: "indigo" },
    { label: "High Risks", value: highRisks, icon: ShieldAlert, color: "rose" },
    { label: "Medium Risks", value: mediumRisks, icon: AlertTriangle, color: "amber" },
    { label: "Total Flagged", value: totalRisks, icon: TrendingUp, color: "emerald" },
  ];

  return (
    <div className="space-y-8 animate-slide-up">
      {/* ─── Header ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            Compliance Dashboard <Sparkles className="h-6 w-6 text-indigo-400 fill-indigo-400/20" />
          </h1>
          <p className="text-gray-400 mt-1">Real-time analysis of legal and corporate policy documents.</p>
        </div>
        <button
          id="refresh-dashboard"
          onClick={loadData}
          disabled={loading}
          className="self-start sm:self-center flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-all disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* ─── Stats Cards ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="glass-panel glass-panel-hover p-6 flex items-center gap-4">
            <div className={`p-4 rounded-xl bg-${color}-500/10 text-${color}-400`}>
              <Icon className="h-8 w-8" />
            </div>
            <div>
              <p className="text-sm text-gray-400 font-medium">{label}</p>
              <h3 className="text-3xl font-bold text-white mt-1">{value}</h3>
            </div>
          </div>
        ))}
      </div>

      {/* ─── Upload + Charts ────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload */}
        <div className="lg:col-span-1 glass-panel p-6 flex flex-col h-full">
          <h2 className="text-xl font-semibold text-white mb-4">Upload Documents</h2>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            className={`flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-8 text-center cursor-pointer transition-all duration-300 ${
              dragOver
                ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400 scale-[0.98]'
                : 'border-slate-700 hover:border-indigo-400 text-gray-400'
            }`}
            onClick={() => document.getElementById("fileInput").click()}
          >
            <input
              id="fileInput"
              type="file"
              multiple
              accept=".pdf"
              className="hidden"
              onChange={handleFileSelect}
            />
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader className="h-10 w-10 text-indigo-400 animate-spin" />
                <p className="text-indigo-300 font-medium">Analyzing PDFs...</p>
                <p className="text-xs text-gray-500">Chunking & classifying risks</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="p-3 rounded-full bg-slate-800 text-gray-300">
                  <FileUp className="h-8 w-8" />
                </div>
                <p className="font-medium text-white">Drag & drop PDFs here</p>
                <p className="text-xs">or click to browse from files</p>
                <span className="text-[10px] px-2 py-1 rounded bg-slate-800 text-gray-500 mt-2 font-mono">PDF only</span>
              </div>
            )}
          </div>
          {uploadError && (
            <p className="text-sm text-rose-400 text-center mt-3 font-medium bg-rose-500/10 p-2 rounded-lg">
              {uploadError}
            </p>
          )}
        </div>

        {/* Charts */}
        <div className="lg:col-span-2 glass-panel p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Risk Profile Analysis</h2>
          {processedDocs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[280px] text-gray-500 border border-slate-800 rounded-xl bg-slate-900/30">
              <ShieldAlert className="h-12 w-12 text-slate-700 mb-2" />
              <p>No processed document data to analyze.</p>
              <p className="text-sm text-gray-600 mt-1">Upload a PDF to view risk charts.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-[280px]">
              {/* Pie Chart */}
              <div className="h-full flex flex-col justify-center items-center">
                {riskData.length === 0 ? (
                  <p className="text-sm text-emerald-400 bg-emerald-500/10 px-3 py-2 rounded-lg">🎉 No risks detected!</p>
                ) : (
                  <ResponsiveContainer width="100%" height={230}>
                    <PieChart>
                      <Pie
                        data={riskData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {riskData.map((entry, i) => (
                          <Cell key={`cell-${i}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: "#1e293b",
                          border: "1px solid rgba(255,255,255,0.1)",
                          color: "#fff",
                          borderRadius: "8px",
                        }}
                      />
                      <Legend verticalAlign="bottom" height={36} iconType="circle" />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Stacked Bar Chart */}
              <div className="h-full">
                <ResponsiveContainer width="100%" height={230}>
                  <BarChart data={documentRiskData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{
                        background: "#1e293b",
                        border: "1px solid rgba(255,255,255,0.1)",
                        color: "#fff",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend verticalAlign="bottom" height={36} />
                    <Bar dataKey="High" stackId="a" fill={COLORS.HIGH} />
                    <Bar dataKey="Medium" stackId="a" fill={COLORS.MEDIUM} />
                    <Bar dataKey="Low" stackId="a" fill={COLORS.LOW} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ─── Document List ──────────────────────────────────────── */}
      <div className="glass-panel p-6">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          Indexed Documents
          <span className="text-xs font-normal text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
            {documents.length} files
          </span>
        </h2>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Loader className="h-8 w-8 text-indigo-400 animate-spin" />
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 border border-slate-800 rounded-xl bg-slate-900/10">
            <FileText className="h-12 w-12 text-slate-700 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-white">No documents uploaded</h3>
            <p className="text-sm text-gray-500 mt-1 max-w-sm mx-auto">
              Upload compliance contracts or guidelines to parse text and detect risks.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse" id="documents-table">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-sm font-medium">
                  <th className="pb-3 pl-4">Filename</th>
                  <th className="pb-3">Upload Time</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-center">Risks Found</th>
                  <th className="pb-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {documents.map((doc) => (
                  <tr key={doc.id} className="text-gray-300 hover:bg-slate-800/10 transition">
                    <td className="py-4 pl-4 font-medium text-white flex items-center gap-2">
                      <FileText className="h-4 w-4 text-indigo-400" />
                      {doc.filename}
                    </td>
                    <td className="py-4 text-sm text-gray-400">
                      {new Date(doc.upload_time).toLocaleString()}
                    </td>
                    <td className="py-4">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        doc.status === "processed"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : doc.status.startsWith("failed")
                          ? "bg-rose-500/10 text-rose-400"
                          : "bg-amber-500/10 text-amber-400 animate-pulse"
                      }`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-4 text-center">
                      {doc.status === "processed" ? (
                        <div className="flex justify-center gap-2">
                          {(doc.high_risks || 0) > 0 && (
                            <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 text-xs font-semibold">
                              {doc.high_risks} High
                            </span>
                          )}
                          {(doc.medium_risks || 0) > 0 && (
                            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 text-xs font-semibold">
                              {doc.medium_risks} Med
                            </span>
                          )}
                          {(doc.total_risks || 0) === 0 && (
                            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-xs font-semibold">
                              Clean
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-600">-</span>
                      )}
                    </td>
                    <td className="py-4 text-center">
                      <button
                        onClick={() => handleDelete(doc)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition"
                        title="Delete document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Sleek Custom Deletion Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-panel max-w-md w-full p-6 mx-4 animate-fade-in border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-2">Delete Document</h3>
            <p className="text-gray-400 text-sm mb-6">
              Are you sure you want to delete <span className="text-indigo-300 font-semibold">{deleteTarget.filename}</span>? 
              This will remove all text chunks, vector embeddings, and detected risks permanently.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-gray-300 font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  const docId = deleteTarget.id;
                  setDeleteTarget(null);
                  try {
                    await deleteDocument(docId);
                    await loadData();
                  } catch (err) {
                    alert("Failed to delete document.");
                  }
                }}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-medium transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
