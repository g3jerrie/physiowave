"use client";

import { useState, useEffect } from "react";
import { getConfig, updateConfig, SystemConfig } from "@/lib/api";

export default function SettingsPage() {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form State
  const [llmModel, setLlmModel] = useState("");
  const [visionModel, setVisionModel] = useState("");

  useEffect(() => {
    getConfig().then(data => {
      setConfig(data);
      setLlmModel(data.llm_model);
      setVisionModel(data.vision_model);
    }).catch(err => {
      console.error("Failed to load setup config", err);
    });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await updateConfig({ llm_model: llmModel, vision_model: visionModel });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!config) return <div className="p-8 pt-16 flex justify-center text-text-tertiary animate-pulse">Loading settings...</div>;

  return (
    <main className="p-8 max-w-5xl mx-auto w-full pt-16 h-full overflow-y-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)] text-text-primary">
          System Settings
        </h1>
        <p className="text-text-secondary mt-2">
          Configure the offline Ollama AI model profiles governing PhysioWave.
        </p>
      </div>

      <div className="glass-card rounded-2xl p-8 max-w-2xl border border-border mt-8">
        <h2 className="text-xl font-semibold text-text-primary mb-6">AI Model Architecture</h2>
        
        <form onSubmit={handleSave} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Core Reasoning LLM</label>
            <input 
              type="text" 
              value={llmModel} 
              onChange={e => setLlmModel(e.target.value)} 
              className="w-full bg-surface-variant text-text-primary px-4 py-3 rounded-lg border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
              placeholder="e.g. gemma3:4b"
            />
            <p className="text-xs text-text-tertiary">The main foundational language model powering the clinical advisor and chat interactions.</p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-text-secondary">Vision RAG Model (Multimodal)</label>
            <input 
              type="text" 
              value={visionModel} 
              onChange={e => setVisionModel(e.target.value)} 
              className="w-full bg-surface-variant text-text-primary px-4 py-3 rounded-lg border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
              placeholder="e.g. moondream"
            />
            <p className="text-xs text-text-tertiary">The multimodal model used to read and describe embedded diagrams during PDF ingestion.</p>
          </div>

          <div className="space-y-2 pt-2 border-t border-border">
             <label className="text-sm font-medium text-text-secondary">Document Embedding Model</label>
             <input 
               type="text"
               value={config.embedding_model}
               disabled
               className="w-full bg-[rgba(20,20,20,0.5)] text-text-tertiary px-4 py-3 rounded-lg border border-border cursor-not-allowed"
             />
             <p className="text-xs text-text-tertiary">Vector storage model. You cannot change this without purging the entire ChromaDB index.</p>
          </div>

          <div className="pt-6 flex items-center justify-end gap-4">
             {saveSuccess && <span className="text-green-500 text-sm font-medium">Saved Successfully!</span>}
             <button 
               type="submit" 
               disabled={isSaving}
               className={`px-6 py-3 rounded-xl font-medium text-white transition-all ${
                 isSaving ? "bg-primary/50 cursor-wait" : "bg-primary hover:bg-primary-hover shadow-lg shadow-primary/25"
               }`}
             >
               {isSaving ? "Saving..." : "Save Settings"}
             </button>
          </div>
        </form>
      </div>

    </main>
  );
}
