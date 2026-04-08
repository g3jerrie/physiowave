"use client";

import { useState } from "react";
import { checkSafety, type SafetyCheckResponse } from "@/lib/api";

const ALL_RISK_FACTORS = [
  { id: "metal_implants", label: "Metal Implants", icon: "🦴" },
  { id: "pacemaker", label: "Pacemaker", icon: "❤️" },
  { id: "cardiac_monitor", label: "Cardiac Monitor", icon: "📟" },
  { id: "pregnancy", label: "Pregnancy", icon: "🤰" },
  { id: "epilepsy", label: "Epilepsy", icon: "⚡" },
  { id: "malignancy", label: "Malignancy", icon: "🔬" },
  { id: "open_wounds", label: "Open Wounds", icon: "🩹" },
  { id: "active_infection", label: "Active Infection", icon: "🦠" },
  { id: "dvt_history", label: "DVT History", icon: "🩸" },
  { id: "osteoporosis", label: "Osteoporosis", icon: "💀" },
  { id: "sensory_deficit", label: "Sensory Deficit", icon: "🖐️" },
  { id: "skin_disease_active", label: "Skin Disease", icon: "🧴" },
  { id: "acute_fracture", label: "Acute Fracture", icon: "🦴" },
  { id: "thrombophlebitis", label: "Thrombophlebitis", icon: "🩸" },
  { id: "cochlear_implant", label: "Cochlear Implant", icon: "👂" },
  { id: "active_hemorrhage", label: "Active Hemorrhage", icon: "🩸" },
];

export default function SafetyPage() {
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<SafetyCheckResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
    setResult(null);
  };

  const handleCheck = async () => {
    if (!selected.length) return;
    setLoading(true);
    try {
      const res = await checkSafety(selected);
      setResult(res);
    } catch {
      setResult(null);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)]">
          🛡️ Safety & Contraindication Checker
        </h1>
        <p className="mt-1 text-text-secondary">
          Screen patients before treatment — real-time contraindication detection
        </p>
      </div>

      {/* Risk Factor Selection */}
      <div className="glass-card rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-text-secondary mb-4">
          Select Patient Risk Factors
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {ALL_RISK_FACTORS.map((factor) => {
            const active = selected.includes(factor.id);
            return (
              <button
                key={factor.id}
                onClick={() => toggle(factor.id)}
                className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all border ${
                  active
                    ? "bg-danger/10 border-danger text-danger shadow-sm"
                    : "bg-surface border-border text-text-secondary hover:border-primary/30 hover:bg-primary/5"
                }`}
              >
                <span>{factor.icon}</span>
                <span>{factor.label}</span>
              </button>
            );
          })}
        </div>

        <button
          onClick={handleCheck}
          disabled={!selected.length || loading}
          className="mt-6 w-full py-3 rounded-xl gradient-primary text-white font-semibold text-sm shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
        >
          {loading ? "Checking..." : "🔍 Check Contraindications"}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="animate-slide-in">
          {result.is_safe ? (
            <div className="glass-card rounded-2xl p-6 border-l-4 border-success">
              <div className="flex items-center gap-3">
                <span className="text-3xl">✅</span>
                <div>
                  <h3 className="font-bold text-success">No Contraindications Detected</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    Based on the selected risk factors, no automatic therapy blocks are triggered.
                    Always verify clinically before proceeding.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="safety-warning relative rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">⚠️</span>
                  <div>
                    <h3 className="font-bold text-danger text-lg">
                      Contraindications Detected
                    </h3>
                    <p className="text-sm text-text-secondary mt-1">
                      The following therapy protocols are blocked:
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {result.blocked_protocols.map((protocol) => (
                    <span
                      key={protocol}
                      className="px-3 py-1.5 rounded-lg bg-danger/20 text-danger text-xs font-semibold"
                    >
                      🚫 {protocol.replace(/_/g, " ").toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>

              {result.warning_message && (
                <div className="glass-card rounded-2xl p-5">
                  <pre className="text-sm text-text-secondary whitespace-pre-wrap font-mono">
                    {result.warning_message}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
