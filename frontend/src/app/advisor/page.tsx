"use client";

import { useState, useRef } from "react";
import { streamSuggestion, type IntakeForm, type StreamMetadata } from "@/lib/api";

const RISK_FACTORS = [
  "metal_implants",
  "pacemaker",
  "cardiac_monitor",
  "pregnancy",
  "epilepsy",
  "malignancy",
  "open_wounds",
  "active_infection",
  "dvt_history",
  "osteoporosis",
  "sensory_deficit",
  "skin_disease_active",
];

const BODY_AREAS = [
  "Cervical spine", "Thoracic spine", "Lumbar spine",
  "Shoulder", "Elbow", "Wrist/Hand",
  "Hip", "Knee", "Ankle/Foot",
  "Neck", "Upper back", "Lower back",
];

export default function AdvisorPage() {
  const [step, setStep] = useState<"intake" | "generating" | "result">("intake");
  const [suggestion, setSuggestion] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [metadata, setMetadata] = useState<StreamMetadata | null>(null);
  const [citationsOpen, setCitationsOpen] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  // Form state
  const [form, setForm] = useState<IntakeForm>({
    diagnosis: "",
    risk_factors: [],
    symptoms: "",
    age: undefined,
    gender: undefined,
    pain_scale: undefined,
    condition_phase: undefined,
    body_area: undefined,
    additional_notes: undefined,
  });

  const toggleRiskFactor = (factor: string) => {
    setForm((prev) => ({
      ...prev,
      risk_factors: prev.risk_factors.includes(factor)
        ? prev.risk_factors.filter((f) => f !== factor)
        : [...prev.risk_factors, factor],
    }));
  };

  const handleSubmit = () => {
    if (!form.diagnosis.trim()) return;

    setStep("generating");
    setSuggestion("");
    setMetadata(null);
    setCitationsOpen(false);
    setIsStreaming(true);

    controllerRef.current = streamSuggestion(
      form,
      (token) => setSuggestion((prev) => prev + token),
      () => {
        setIsStreaming(false);
        setStep("result");
      },
      (error) => {
        setIsStreaming(false);
        setSuggestion(`Error: ${error}`);
        setStep("result");
      },
      (meta) => setMetadata(meta)
    );
  };

  const handleReset = () => {
    controllerRef.current?.abort();
    setStep("intake");
    setSuggestion("");
    setMetadata(null);
    setCitationsOpen(false);
    setIsStreaming(false);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)]">
          🧠 Smart Treatment Advisor
        </h1>
        <p className="mt-1 text-text-secondary">
          AI-powered therapy protocol recommendations based on clinical evidence
        </p>
      </div>

      {step === "intake" && (
        <div className="glass-card rounded-2xl p-6 space-y-6">
          {/* Patient Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Age
              </label>
              <input
                type="number"
                min={0}
                max={120}
                value={form.age ?? ""}
                onChange={(e) =>
                  setForm({ ...form, age: e.target.value ? +e.target.value : undefined })
                }
                className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
                placeholder="e.g. 55"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Gender
              </label>
              <select
                value={form.gender ?? ""}
                onChange={(e) =>
                  setForm({ ...form, gender: e.target.value || undefined })
                }
                className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Pain Scale (VAS 0–10)
              </label>
              <input
                type="number"
                min={0}
                max={10}
                value={form.pain_scale ?? ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    pain_scale: e.target.value ? +e.target.value : undefined,
                  })
                }
                className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
                placeholder="0–10"
              />
            </div>
          </div>

          {/* Diagnosis */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5">
              Condition / Diagnosis <span className="text-danger">*</span>
            </label>
            <input
              type="text"
              value={form.diagnosis}
              onChange={(e) => setForm({ ...form, diagnosis: e.target.value })}
              className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
              placeholder="e.g. Knee Osteoarthritis, Cervical Spondylosis, Frozen Shoulder..."
            />
          </div>

          {/* Condition Phase & Body Area */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Condition Phase
              </label>
              <select
                value={form.condition_phase ?? ""}
                onChange={(e) =>
                  setForm({ ...form, condition_phase: e.target.value || undefined })
                }
                className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
              >
                <option value="">Select...</option>
                <option value="acute">Acute</option>
                <option value="subacute">Subacute</option>
                <option value="chronic">Chronic</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                Body Area Affected
              </label>
              <select
                value={form.body_area ?? ""}
                onChange={(e) =>
                  setForm({ ...form, body_area: e.target.value || undefined })
                }
                className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition"
              >
                <option value="">Select...</option>
                {BODY_AREAS.map((area) => (
                  <option key={area} value={area}>
                    {area}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Symptoms */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5">
              Associated Symptoms
            </label>
            <textarea
              rows={2}
              value={form.symptoms ?? ""}
              onChange={(e) => setForm({ ...form, symptoms: e.target.value })}
              className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition resize-none"
              placeholder="e.g. Stiffness, swelling, radiating pain, restricted ROM..."
            />
          </div>

          {/* Risk Factors */}
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-3">
              ⚠️ Contraindications / Risk Factors
            </label>
            <div className="flex flex-wrap gap-2">
              {RISK_FACTORS.map((factor) => {
                const active = form.risk_factors.includes(factor);
                return (
                  <button
                    key={factor}
                    onClick={() => toggleRiskFactor(factor)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      active
                        ? "bg-danger text-white shadow-md"
                        : "bg-surface-variant text-text-secondary hover:bg-danger/10 hover:text-danger"
                    }`}
                  >
                    {factor.replace(/_/g, " ")}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={!form.diagnosis.trim()}
            className="w-full py-3 rounded-xl gradient-primary text-white font-semibold text-sm shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
          >
            🧠 Generate AI Suggestion
          </button>
        </div>
      )}

      {/* Generating / Result */}
      {(step === "generating" || step === "result") && (
        <div className="space-y-4">

          {/* ── Redline Warning (Safety Gate triggered) ─────────────────── */}
          {metadata && !metadata.is_safe && (
            <div className="safety-warning relative rounded-2xl p-6 animate-slide-in">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">🚨</span>
                <div>
                  <h3 className="font-bold text-danger text-lg">
                    ⛔ REDLINE — Safety Gate Triggered
                  </h3>
                  <p className="text-sm text-text-secondary mt-1">
                    The AI suggestion contained protocols contraindicated for this patient.
                    The following therapies have been blocked:
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                {metadata.blocked_protocols.map((protocol) => (
                  <span
                    key={protocol}
                    className="px-3 py-1.5 rounded-lg bg-danger/20 text-danger text-xs font-bold tracking-wide"
                  >
                    🚫 {protocol.replace(/_/g, " ").toUpperCase()}
                  </span>
                ))}
              </div>
              {metadata.warning_message && (
                <pre className="text-xs text-text-secondary whitespace-pre-wrap font-mono bg-surface/50 rounded-xl p-4 border border-danger/20">
                  {metadata.warning_message}
                </pre>
              )}
            </div>
          )}

          {/* ── AI Suggestion (streaming output) ─────────────────────────── */}
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              {isStreaming && (
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              )}
              <h2 className="text-sm font-semibold text-text-secondary">
                {isStreaming ? "Generating suggestion..." : "AI Suggestion"}
              </h2>
              {metadata?.is_safe && (
                <span className="ml-auto px-2 py-0.5 rounded-full bg-success/15 text-success text-xs font-semibold">
                  ✅ Safety Gate: PASSED
                </span>
              )}
            </div>

            <div className="prose prose-sm max-w-none text-text-primary whitespace-pre-wrap leading-relaxed">
              {suggestion || (
                <div className="space-y-3">
                  <div className="h-4 bg-surface-variant rounded animate-shimmer w-3/4" />
                  <div className="h-4 bg-surface-variant rounded animate-shimmer w-full" />
                  <div className="h-4 bg-surface-variant rounded animate-shimmer w-2/3" />
                </div>
              )}
              {isStreaming && (
                <span className="inline-block w-0.5 h-5 bg-primary animate-pulse ml-0.5" />
              )}
            </div>
          </div>

          {/* ── Citations Accordion ───────────────────────────────────────── */}
          {metadata && metadata.source_chunks.length > 0 && (
            <div className="glass-card rounded-2xl overflow-hidden">
              <button
                onClick={() => setCitationsOpen((o) => !o)}
                className="w-full flex items-center justify-between px-6 py-4 text-sm font-semibold text-text-secondary hover:bg-surface-variant/50 transition-colors"
              >
                <span>
                  📚 Clinical Sources ({metadata.source_chunks.length} chunks retrieved)
                </span>
                <span
                  className={`transition-transform duration-200 ${citationsOpen ? "rotate-180" : ""}`}
                >
                  ▾
                </span>
              </button>

              {citationsOpen && (
                <div className="border-t border-border divide-y divide-border">
                  {metadata.source_chunks.map((chunk, idx) => {
                    const c = chunk as Record<string, unknown>;
                    return (
                      <div key={idx} className="px-6 py-4 space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                            Source {idx + 1}
                          </span>
                          {Boolean(c.source_file) && (
                            <span className="text-xs text-text-secondary font-mono">
                              📄 {String(c.source_file)}
                            </span>
                          )}
                          {c.page_number != null && (
                            <span className="text-xs text-text-secondary">
                              — Page {String(c.page_number)}
                            </span>
                          )}
                          {c.score != null && (
                            <span className="ml-auto text-xs text-text-secondary">
                              Score: {(Number(c.score) * 100).toFixed(1)}%
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-text-secondary leading-relaxed line-clamp-4">
                          {String(c.content ?? "")}
                        </p>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleReset}
              className="px-6 py-2.5 rounded-xl bg-surface-variant text-text-secondary text-sm font-medium hover:bg-border transition"
            >
              ← New Consultation
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
