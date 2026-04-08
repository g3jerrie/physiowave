"use client";

import Link from "next/link";

const STAT_CARDS = [
  {
    label: "Active Patients",
    value: "—",
    icon: "👥",
    color: "from-primary to-primary-dark",
    href: "/patients",
  },
  {
    label: "Sessions Today",
    value: "—",
    icon: "📝",
    color: "from-secondary to-secondary-dark",
    href: "/sessions",
  },
  {
    label: "AI Suggestions",
    value: "—",
    icon: "🧠",
    color: "from-accent to-orange-500",
    href: "/advisor",
  },
  {
    label: "Knowledge Chunks",
    value: "—",
    icon: "📚",
    color: "from-success to-emerald-600",
    href: "#",
  },
];

const QUICK_ACTIONS = [
  {
    label: "New Treatment Suggestion",
    description: "AI-powered therapy recommendation",
    icon: "🧠",
    href: "/advisor",
    gradient: "gradient-primary",
  },
  {
    label: "Add Patient",
    description: "Register a new patient record",
    icon: "👤",
    href: "/patients",
    gradient: "gradient-hero",
  },
  {
    label: "Safety Check",
    description: "Check contraindications",
    icon: "🛡️",
    href: "/safety",
    gradient: "gradient-warm",
  },
  {
    label: "Log Session",
    description: "Record a treatment session",
    icon: "📝",
    href: "/sessions",
    gradient: "bg-gradient-to-br from-violet-500 to-purple-700",
  },
];

const THERAPY_MODES = [
  { name: "IFT", full: "Interferential Therapy", icon: "⚡", desc: "Pain management" },
  { name: "TENS", full: "Transcutaneous Electrical Nerve Stimulation", icon: "🔌", desc: "Nerve stimulation" },
  { name: "MS", full: "Muscle Stimulation", icon: "💪", desc: "Muscle recovery" },
  { name: "US", full: "Ultrasound Therapy", icon: "🔊", desc: "Deep tissue healing" },
  { name: "DH", full: "Deep Heat Therapy", icon: "🔥", desc: "Thermal treatment" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)] text-text-primary">
          Dashboard
        </h1>
        <p className="mt-1 text-text-secondary">
          Welcome to PhysioWave — Intelligent Care at Your Fingertips
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map((card) => (
          <Link
            key={card.label}
            href={card.href}
            className="glass-card rounded-2xl p-5 hover:shadow-lg transition-all duration-300 group"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-text-secondary">{card.label}</p>
                <p className="text-3xl font-bold font-[family-name:var(--font-outfit)] mt-1 text-text-primary">
                  {card.value}
                </p>
              </div>
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center text-xl shadow-md group-hover:scale-110 transition-transform`}
              >
                {card.icon}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold font-[family-name:var(--font-outfit)] mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.label}
              href={action.href}
              className={`${action.gradient} rounded-2xl p-5 text-white hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300`}
            >
              <span className="text-2xl">{action.icon}</span>
              <h3 className="text-sm font-semibold mt-3">{action.label}</h3>
              <p className="text-xs text-white/70 mt-1">{action.description}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Combi 5-in-1 Therapy Modes */}
      <div>
        <h2 className="text-xl font-semibold font-[family-name:var(--font-outfit)] mb-4">
          Combi 5-in-1 Therapy Modes
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {THERAPY_MODES.map((mode) => (
            <div
              key={mode.name}
              className="glass-card rounded-2xl p-4 text-center hover:shadow-md transition-shadow"
            >
              <span className="text-3xl">{mode.icon}</span>
              <h3 className="text-lg font-bold font-[family-name:var(--font-outfit)] mt-2 text-primary">
                {mode.name}
              </h3>
              <p className="text-[11px] text-text-secondary mt-0.5 leading-tight">
                {mode.full}
              </p>
              <p className="text-[10px] text-text-tertiary mt-1">{mode.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* HIPAA Notice */}
      <div className="glass-card rounded-2xl p-5 border-l-4 border-primary">
        <div className="flex items-start gap-3">
          <span className="text-xl">🔒</span>
          <div>
            <h3 className="font-semibold text-sm text-text-primary">
              HIPAA-Compliant · 100% Offline
            </h3>
            <p className="text-xs text-text-secondary mt-1">
              All patient data is stored locally and encrypted at rest.
              AI inference runs entirely on-device via Ollama.
              No data ever leaves this machine.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
