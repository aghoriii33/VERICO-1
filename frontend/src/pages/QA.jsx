import React, { useState, useEffect } from "react";
import {
  Send, HelpCircle, FileText, CheckCircle2,
  MapPin, BookOpen, AlertCircle, Quote, Loader
} from "lucide-react";
import { fetchDocuments, askQuestion } from "../services/api";

export default function QA() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [selectedCitation, setSelectedCitation] = useState(null);

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

  const handleDocSelect = (docId) => {
    setSelectedDocs(prev =>
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setLoading(true);
    setQuery("");

    const userMessage = { role: "user", text: cleanQuery };
    setChatHistory(prev => [...prev, userMessage]);

    try {
      const response = await askQuestion(
        cleanQuery,
        selectedDocs.length > 0 ? selectedDocs : null
      );

      const assistantMessage = {
        role: "assistant",
        text: response.answer,
        confidence: response.confidence,
        citations: response.citations || [],
        method: response.method,
      };

      setChatHistory(prev => [...prev, assistantMessage]);

      if (response.citations?.length > 0) {
        setSelectedCitation(response.citations[0]);
      } else {
        setSelectedCitation(null);
      }
    } catch (err) {
      setChatHistory(prev => [
        ...prev,
        {
          role: "assistant",
          text: "Sorry, I encountered an error. Make sure the backend server is running.",
          error: true,
        },
      ]);
      setSelectedCitation(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 h-[calc(100vh-12rem)] animate-slide-up">
      {/* ─── Sidebar: Document Scope Filter ─────────────────────── */}
      <div className="lg:col-span-1 glass-panel p-6 flex flex-col h-full overflow-hidden">
        <h2 className="text-lg font-semibold text-white mb-3">Scope Filter</h2>
        <p className="text-xs text-gray-400 mb-4">
          Select documents to search across. If none are checked, all documents are searched.
        </p>

        <div className="flex-1 overflow-y-auto space-y-2 pr-2">
          {documents.length === 0 ? (
            <div className="text-center py-6 text-gray-500 text-sm">
              No processed documents available.
            </div>
          ) : (
            documents.map(doc => {
              const isChecked = selectedDocs.includes(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => handleDocSelect(doc.id)}
                  className={`flex items-center gap-3 p-3 rounded-lg border text-sm cursor-pointer transition-all ${
                    isChecked
                      ? "bg-indigo-500/10 border-indigo-500/50 text-white"
                      : "bg-slate-900/40 border-slate-800 text-gray-400 hover:border-slate-700"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}}
                    className="accent-indigo-500 pointer-events-none rounded"
                  />
                  <span className="truncate flex-1 font-medium">{doc.filename}</span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* ─── Center: Chat Interface ─────────────────────────────── */}
      <div className="lg:col-span-2 flex flex-col h-full overflow-hidden">
        {/* Chat Log */}
        <div className="flex-1 glass-panel p-6 mb-4 overflow-y-auto space-y-4 pr-3" id="chat-log">
          {chatHistory.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 space-y-3">
              <div className="p-4 rounded-full bg-slate-900 text-gray-300">
                <HelpCircle className="h-8 w-8 text-indigo-400" />
              </div>
              <h3 className="font-semibold text-white">Ask anything about your documents</h3>
              <p className="text-sm max-w-xs">
                Enter a compliance, policy, or contractual question to extract precise answers with page citations.
              </p>
            </div>
          ) : (
            chatHistory.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} animate-fade-in`}
              >
                <div
                  className={`max-w-[85%] rounded-xl p-4 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-lg'
                      : msg.error
                      ? 'bg-rose-500/10 border border-rose-500/20 text-rose-300 rounded-bl-none'
                      : 'bg-slate-900/80 border border-slate-800 text-gray-100 rounded-bl-none'
                  }`}
                >
                  <p>{msg.text}</p>

                  {/* Confidence metadata */}
                  {msg.role === 'assistant' && !msg.error && (
                    <div className="flex items-center gap-3 mt-3 pt-3 border-t border-slate-800/80 text-[10px] text-gray-400">
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                        Confidence: {(msg.confidence * 100).toFixed(1)}%
                      </span>
                      <span>•</span>
                      <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-gray-300">
                        {msg.method}
                      </span>
                    </div>
                  )}
                </div>

                {/* Citations */}
                {msg.role === 'assistant' && msg.citations?.length > 0 && (
                  <div className="mt-2 pl-2 flex flex-wrap gap-2">
                    {msg.citations.map((cite, cIdx) => (
                      <button
                        key={cIdx}
                        onClick={() => setSelectedCitation(cite)}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border font-medium transition ${
                          selectedCitation?.excerpt === cite.excerpt
                            ? "bg-indigo-500/20 border-indigo-400 text-indigo-300 shadow-sm"
                            : "bg-slate-900/60 border-slate-800 text-gray-400 hover:text-gray-200 hover:border-slate-700"
                        }`}
                      >
                        <FileText className="h-3 w-3" />
                        {cite.document} (pg. {cite.page})
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Input Bar */}
        <form onSubmit={handleAsk} className="flex gap-3" id="qa-form">
          <input
            type="text"
            id="qa-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            placeholder="Ask a question (e.g. What is the limit on vendor liability?)"
            className="flex-1 glass-input px-4 py-3 text-sm focus:outline-none"
          />
          <button
            type="submit"
            id="qa-submit"
            disabled={loading || !query.trim()}
            className="px-5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition flex items-center justify-center disabled:opacity-50"
          >
            {loading ? (
              <Loader className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
      </div>

      {/* ─── Right: Citation Panel ──────────────────────────────── */}
      <div className="lg:col-span-1 glass-panel p-6 flex flex-col h-full overflow-hidden">
        <h2 className="text-lg font-semibold text-white mb-2 flex items-center gap-1.5">
          <BookOpen className="h-4 w-4 text-indigo-400" /> Source Citation
        </h2>

        {selectedCitation ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-lg p-3 mb-4 space-y-1.5">
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <MapPin className="h-3.5 w-3.5 text-indigo-400" />
                <span className="font-semibold text-gray-300 truncate">{selectedCitation.document}</span>
              </div>
              <div className="flex justify-between items-center text-[11px] text-gray-400 pt-1 border-t border-slate-800/60">
                <span>Page number: {selectedCitation.page}</span>
                <span className="text-[10px] bg-slate-800 text-gray-400 px-1.5 py-0.5 rounded">PDF Reference</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto text-sm text-gray-300 leading-relaxed border border-slate-800 rounded-lg p-4 bg-slate-950/20 pr-2 relative font-serif">
              <Quote className="absolute -top-1 -left-1 h-8 w-8 text-indigo-500/10 rotate-180" />
              {selectedCitation.excerpt}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 border border-dashed border-slate-800 rounded-lg p-4">
            <AlertCircle className="h-8 w-8 text-slate-700 mb-2" />
            <p className="text-xs">No citation selected.</p>
            <p className="text-[10px] text-gray-600 mt-1">
              Submit a question and click on references below answers to view source excerpts.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
