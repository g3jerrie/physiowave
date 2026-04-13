"use client";

import { useState, useRef, useEffect } from "react";
import { uploadDocument, getUploads, deleteUpload, retryUpload, UploadStatus } from "@/lib/api";

const CircularProgress = ({ progress }: { progress: number }) => {
  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;
  
  return (
    <div className="relative w-10 h-10 flex items-center justify-center shrink-0">
      <svg className="transform -rotate-90 w-10 h-10">
        <circle cx="20" cy="20" r={radius} stroke="currentColor" strokeWidth="3" fill="transparent" className="text-gray-500/20" />
        <circle 
            cx="20" cy="20" r={radius} stroke="currentColor" strokeWidth="3" fill="transparent" 
            strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} 
            className="text-blue-500 transition-all duration-500 ease-out drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]" 
            strokeLinecap="round"
        />
      </svg>
      <span className="absolute text-[9px] font-bold text-blue-500">{Math.round(progress)}%</span>
    </div>
  );
};

export default function KnowledgeBasePage() {
  const [uploads, setUploads] = useState<UploadStatus[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [extractImages, setExtractImages] = useState(true);
  const [toastError, setToastError] = useState<string | null>(null);
  const [isProcessingAction, setIsProcessingAction] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{isOpen: boolean, step: 1 | 2, actionType: "delete" | "retry" | null, uploadId: number | null}>({
    isOpen: false, step: 1, actionType: null, uploadId: null
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchUploads = async () => {
    try {
      const data = await getUploads();
      setUploads(data);
    } catch (err) {
      console.error("Failed to fetch uploads", err);
    }
  };

  useEffect(() => {
    // Initial fetch as fallback while SSE connects
    fetchUploads();

    // SSE: Server-Sent Events — single persistent connection replaces polling
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    const eventSource = new EventSource(`${API_BASE}/rag/uploads/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as UploadStatus[];
        setUploads(data);
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    eventSource.onerror = () => {
      // Connection lost — fall back to a one-time fetch, EventSource auto-reconnects
      console.warn("SSE connection lost, will auto-reconnect...");
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const handleFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      alert("Only PDF files are supported.");
      return;
    }
    setIsUploading(true);
    try {
      await uploadDocument(file, "clinical_guide", extractImages);
      await fetchUploads();
    } catch (err: any) {
      alert(err.message || "Failed to upload file");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const initiateAction = (action: "delete" | "retry", id: number) => {
    if (action === "retry") {
      executeAction("retry", id, false);
      return;
    }
    setConfirmModal({ isOpen: true, step: 1, actionType: "delete", uploadId: id });
  };

  const executeAction = async (action: "delete" | "retry", id: number, purgeVectors: boolean, overrides?: {extractImages?: boolean, safeMode?: boolean}) => {
    if (isProcessingAction) return;
    setIsProcessingAction(true);
    try {
      if (action === "delete") {
        await deleteUpload(id, purgeVectors);
      } else if (action === "retry") {
        await retryUpload(id, overrides?.extractImages, overrides?.safeMode);
      }
    } catch(err: any) {
      setToastError(`Action failed: ${err.message}`);
      setTimeout(() => setToastError(null), 5000);
    } finally {
      await fetchUploads();
      setConfirmModal({ isOpen: false, step: 1, actionType: null, uploadId: null });
      setIsProcessingAction(false);
    }
  };

  const getSmartAction = (error: string | undefined): { label: string, icon: string, overrides: {extractImages?: boolean, safeMode?: boolean} } | null => {
    if (!error) return null;
    if (error.includes("Extract Images toggle")) {
        return { label: "Retry with AI Vision", icon: "👁️", overrides: { extractImages: true } };
    }
    if (error.includes("500") || error.includes("internal error") || error.includes("stopped")) {
        return { label: "Retry (Safe Mode)", icon: "🛡️", overrides: { safeMode: true } };
    }
    return null;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pending":
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-500 font-medium border border-yellow-500/30">Queued</span>;
      case "parsing":
        return <span className="px-2 py-1 text-xs rounded-full bg-purple-500/20 text-purple-400 font-medium animate-pulse border border-purple-500/30">Analyzing</span>;
      case "processing":
        return <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-500 font-medium animate-pulse border border-blue-500/30">Embedding</span>;
      case "complete":
        return <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-500 font-medium border border-green-500/30">Complete</span>;
      case "cancelled":
        return <span className="px-2 py-1 text-xs rounded-full bg-orange-500/20 text-orange-400 font-medium border border-orange-500/30">Cancelled</span>;
      case "failed":
        return <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-500 font-medium border border-red-500/30">Failed</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-gray-500/20 text-gray-400 font-medium">{status}</span>;
    }
  };

  const parseFriendlyError = (trace: string | undefined) => {
    if (!trace) return "";
    if (trace.includes("Extract Images toggle")) return "0 chunks extracted. This PDF appears to be a scan with no text layer.";
    if (trace.includes("MemoryError")) return "System Memory Exhausted. The PDF processing overflowed RAM limits.";
    if (trace.includes("500") || trace.includes("internal error")) return "GPU Resource Crash. Ollama's model runner stopped unexpectedly.";
    if (trace.includes("Timeout")) return "AI Processing Timeout. The local Ollama model took too long.";
    if (trace.includes("ConnectError") || trace.includes("Connection refused")) return "Ollama Offline. Ensure 'ollama serve' is running.";
    return "Processing failed unexpectedly. Check the backend logs.";
  };

  return (
    <main className="p-8 max-w-5xl mx-auto w-full h-full flex flex-col pt-16">
      {/* Toast Notification */}
      {toastError && (
        <div className="fixed top-6 right-6 z-50 bg-red-500/90 text-white px-6 py-4 rounded-xl shadow-2xl animate-in fade-in slide-in-from-top-4 flex items-center gap-3 border border-red-400">
          <span className="text-xl">⚠️</span>
          <p className="text-sm font-medium">{toastError}</p>
          <button onClick={() => setToastError(null)} className="ml-2 hover:bg-white/20 p-1 rounded-full w-6 h-6 flex items-center justify-center">×</button>
        </div>
      )}

      <div className="mb-8">
        <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)] text-text-primary">
          Knowledge Base
        </h1>
        <p className="text-text-secondary mt-2">
          Upload PDF equipment manuals and clinical protocols to expand PhysioWave's intelligence.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        <div className="lg:col-span-1">
          <div
            className={`glass-card p-8 rounded-2xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center h-64 text-center ${
              isDragOver ? "border-primary bg-primary/5 shadow-xl" : "border-border hover:border-text-tertiary shadow-md"
            }`}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept="application/pdf"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFile(e.target.files[0]);
                }
                e.target.value = "";
              }}
            />
            <div className="w-16 h-16 rounded-full bg-surface-variant flex items-center justify-center mb-4 text-3xl">
              📄
            </div>
            <h3 className="font-semibold text-text-primary">Upload Document</h3>
            <p className="text-sm text-text-tertiary mt-2 mb-2">
               Drag & drop a PDF here, or click to browse.
            </p>
            {isUploading && (
              <div className="mt-2 text-sm text-primary font-medium animate-pulse">Uploading to server...</div>
            )}
          </div>
          
          <div className="mt-4 flex items-center justify-between glass-card p-4 rounded-xl border border-border bg-surface/50 shadow-sm">
             <div className="flex flex-col">
                 <span className="text-sm font-semibold text-text-primary">Extract Images</span>
                 <span className="text-[11px] text-text-tertiary">Uses Moondream Vision (Slower)</span>
             </div>
             <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" checked={extractImages} onChange={(e) => setExtractImages(e.target.checked)} />
                <div className="w-11 h-6 bg-surface-variant peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary drop-shadow-sm box-content border border-border"></div>
             </label>
          </div>

          <div className="mt-4 glass-card p-5 rounded-xl border border-border bg-surface/50 shadow-sm">
              <h3 className="font-semibold text-sm mb-2 text-text-primary flex items-center gap-2">
                  <span className="text-purple-500">⚡</span> Worker Engine
              </h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                  Documents are safely queued and processed one at a time via a background worker to prevent Ollama GPU memory exhaustion. You can safely cancel uploads without crashing the runtime!
              </p>
          </div>
        </div>

        <div className="lg:col-span-2 flex flex-col min-h-0 glass-card rounded-2xl overflow-hidden shadow-lg border border-border">
          <div className="p-4 border-b border-border bg-surface/80 backdrop-blur-md sticky top-0 z-10 flex justify-between items-center">
            <h2 className="font-semibold text-text-primary text-lg">Ingestion Queue</h2>
            <span className="text-xs font-medium px-2 py-1 bg-surface-variant rounded-md text-text-secondary border border-border shadow-sm">
                {uploads.filter(u => u.status === 'pending' || u.status === 'processing').length} Active
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-surface/30">
            {uploads.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-text-tertiary text-sm min-h-[300px]">
                <span className="text-4xl mb-3 opacity-50">📭</span>
                No documents found in the history.
              </div>
            ) : (
              uploads.map((upload) => (
                <div key={upload.id} className="p-4 rounded-xl border border-border bg-surface hover:bg-surface-variant shadow-sm hover:shadow-md transition-all flex flex-col sm:flex-row sm:items-center gap-4 relative overflow-hidden group">
                  
                  {(upload.status === "processing" || upload.status === "parsing") && upload.total_chunks === 0 ? (
                    <div className="w-10 h-10 flex items-center justify-center shrink-0">
                      <div className="w-6 h-6 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></div>
                    </div>
                  ) : upload.status === "processing" ? (
                     <CircularProgress progress={upload.total_chunks > 0 ? (upload.ingested_chunks / upload.total_chunks) * 100 : 0} />
                  ) : (
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 shadow-inner ${
                        upload.status === 'complete' ? 'bg-green-500/10 text-green-500' : 
                        upload.status === 'failed' ? 'bg-red-500/10 text-red-500' :
                        upload.status === 'cancelled' ? 'bg-orange-500/10 text-orange-400' : 'bg-surface border border-border text-text-tertiary'
                    }`}>
                        {upload.status === "complete" ? "✅" : upload.status === "failed" ? "❌" : upload.status === "cancelled" ? "🛑" : "⏳"}
                    </div>
                  )}

                  <div className="flex-1 min-w-0 z-10">
                    <h4 className="text-sm font-semibold text-text-primary truncate" title={upload.filename}>
                      {upload.filename}
                    </h4>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-text-tertiary">
                      <span className="font-mono text-[10px]">{new Date(upload.created_at).toLocaleString([], {hour: '2-digit', minute:'2-digit', day: '2-digit', month: 'short'})}</span>
                      {upload.extract_images === 1 && (
                          <>
                           <span className="opacity-50">•</span>
                           <span className="text-[10px] text-purple-400 font-medium">Vision Enabled</span>
                          </>
                      )}
                      {(upload.status === "processing" || upload.status === "parsing") && upload.total_chunks === 0 && (
                        <>
                          <span className="opacity-50">•</span>
                          <span className="text-purple-400 font-medium flex items-center gap-1">
                               Extracting content...
                          </span>
                        </>
                      )}
                      {(upload.status === "processing" || upload.status === "parsing") && upload.total_chunks > 0 && upload.ingested_chunks <= upload.total_chunks && upload.status !== "processing" && (
                        <>
                          <span className="opacity-50">•</span>
                          <span className="text-purple-400 font-medium flex items-center gap-1">
                               Analyzing... (Page {upload.ingested_chunks}/{upload.total_chunks})
                          </span>
                        </>
                      )}
                      {upload.status === "processing" && upload.total_chunks > 0 && (
                        <>
                          <span className="opacity-50">•</span>
                          <span className="text-blue-400 font-medium">
                               Embedding {upload.ingested_chunks} / {upload.total_chunks} chunks
                          </span>
                        </>
                      )}
                      {(upload.status === "complete" || upload.status === "failed" || upload.status === "cancelled") && upload.total_chunks > 0 && (
                        <>
                          <span className="opacity-50">•</span>
                          <span className="opacity-80">
                               {upload.total_chunks} chunks embedded
                          </span>
                        </>
                      )}
                    </div>
                    {upload.error_message && (
                      <div className="mt-3 text-xs text-red-500/90 bg-red-500/5 p-3 rounded-lg border border-red-500/20 shadow-sm">
                        <span className="font-semibold block mb-1">Worker Error:</span>
                        {parseFriendlyError(upload.error_message)}
                      </div>
                    )}
                  </div>
                  <div className="shrink-0 flex flex-col items-end gap-3 z-10 relative">
                    {getStatusBadge(upload.status)}
                    <div className="flex gap-2">
                       {(upload.status === "failed" || upload.status === "cancelled") && (
                         <>
                            {getSmartAction(upload.error_message) && (
                                <button 
                                    disabled={isProcessingAction} 
                                    onClick={() => executeAction("retry", upload.id, false, getSmartAction(upload.error_message)!.overrides)} 
                                    className="px-3 py-1.5 font-bold text-[11px] rounded-md bg-blue-600 hover:bg-blue-700 text-white transition-all shadow-md flex items-center gap-1.5 active:scale-95"
                                >
                                    <span>{getSmartAction(upload.error_message)!.icon}</span>
                                    {getSmartAction(upload.error_message)!.label}
                                </button>
                            )}
                            <button disabled={isProcessingAction} onClick={() => initiateAction("retry", upload.id)} className={`px-3 py-1.5 font-medium text-[11px] rounded-md border transition-all shadow-sm ${isProcessingAction ? "bg-surface-variant text-text-tertiary cursor-not-allowed border-border" : "bg-surface hover:bg-surface-variant border-border text-text-primary"}`}>Retry</button>
                         </>
                       )}
                       {(upload.status === "pending" || upload.status === "processing" || upload.status === "parsing") && (
                          <button disabled={isProcessingAction} onClick={() => initiateAction("delete", upload.id)} className={`px-3 py-1.5 font-medium text-[11px] rounded-md border transition-all shadow-sm ${isProcessingAction ? "bg-surface-variant text-text-tertiary cursor-not-allowed border-border" : "bg-red-500/10 hover:bg-red-500/20 border-red-500/30 text-red-400"}`}>Cancel</button>
                       )}
                       {(upload.status === "complete" || upload.status === "failed" || upload.status === "cancelled") && (
                          <button disabled={isProcessingAction} onClick={() => initiateAction("delete", upload.id)} className={`px-3 py-1.5 font-medium text-[11px] rounded-md border transition-all shadow-sm ${isProcessingAction ? "bg-surface-variant text-text-tertiary cursor-not-allowed border-border" : "bg-red-500 hover:bg-red-600 border-red-600 text-white"}`}>Delete</button>
                       )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Application Layer Modal */}
      {confirmModal.isOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-surface glass-card rounded-2xl p-6 max-w-md w-full shadow-2xl border border-border animate-in fade-in zoom-in-95">
            {confirmModal.step === 1 ? (
              <>
                <h3 className="text-xl font-bold font-[family-name:var(--font-outfit)] text-text-primary mb-2">Remove Document?</h3>
                <p className="text-text-secondary text-sm mb-6 leading-relaxed">
                  Are you sure you want to remove this document's original file from the server queue?
                </p>
                <div className="flex justify-end gap-3">
                  <button 
                    disabled={isProcessingAction}
                    onClick={() => setConfirmModal(prev => ({...prev, isOpen: false}))}
                    className="px-5 py-2.5 text-sm font-medium rounded-lg bg-surface-variant hover:bg-surface border border-border text-text-primary transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button 
                    disabled={isProcessingAction}
                    onClick={() => setConfirmModal(prev => ({...prev, step: 2}))}
                    className="px-5 py-2.5 text-sm font-medium rounded-lg bg-red-500 hover:bg-red-600 text-white transition-colors disabled:opacity-50 shadow-md"
                  >
                    Proceed
                  </button>
                </div>
              </>
            ) : (
              <>
                <h3 className="text-xl font-bold font-[family-name:var(--font-outfit)] text-text-primary mb-2">Purge Vector Embeddings?</h3>
                <p className="text-text-secondary text-sm mb-6 leading-relaxed">
                  Do you also want to purge any generated vector embeddings from the local vector store? 
                  <br/><br/>
                  <span className="text-xs bg-surface-variant p-2 rounded block border border-border">
                      Choose <b className="text-red-400">Purge Vectors</b> to erase all trace of it from memory, or <b className="text-text-primary">Keep RAG Knowledge</b> to retain the AI embeddings while still deleting the raw PDF file.
                  </span>
                </p>
                <div className="flex justify-end gap-3 flex-wrap">
                  <button 
                    disabled={isProcessingAction}
                    onClick={() => setConfirmModal(prev => ({...prev, isOpen: false}))}
                    className="px-4 py-2 text-sm font-medium rounded-lg border border-border text-text-primary transition-colors disabled:opacity-50"
                  >
                    Cancel Action
                  </button>
                  <button 
                    disabled={isProcessingAction}
                    onClick={() => executeAction("delete", confirmModal.uploadId!, false)}
                    className="px-4 py-2 text-sm font-medium rounded-lg bg-surface-variant hover:bg-surface border border-border text-text-primary transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    {isProcessingAction && confirmModal.actionType === "delete" ? "Processing..." : "Keep RAG Knowledge"}
                  </button>
                  <button 
                    disabled={isProcessingAction}
                    onClick={() => executeAction("delete", confirmModal.uploadId!, true)}
                    className="px-4 py-2 text-sm font-medium rounded-lg bg-red-500 hover:bg-red-600 text-white shadow-md transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    {isProcessingAction && confirmModal.actionType === "delete" ? "Purging..." : "Purge Vectors"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
