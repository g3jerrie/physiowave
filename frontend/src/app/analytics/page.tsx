"use client";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)]">
          📈 Progress Analytics
        </h1>
        <p className="mt-1 text-text-secondary">
          Visual analytics for patient recovery tracking
        </p>
      </div>

      {/* Placeholder — will be populated from session data */}
      <div className="glass-card rounded-2xl p-12 text-center">
        <span className="text-5xl">📊</span>
        <h3 className="mt-4 font-semibold text-text-primary">
          Analytics Coming Soon
        </h3>
        <p className="text-sm text-text-secondary mt-2 max-w-md mx-auto">
          Patient progress analytics will be available once treatment sessions
          are logged. Track pain score improvements, range of motion, swelling,
          and functional recovery over time.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 max-w-2xl mx-auto">
          {[
            { label: "Pain Score Trends", icon: "📉" },
            { label: "ROM Progress", icon: "🦵" },
            { label: "Swelling Tracking", icon: "📏" },
            { label: "Functional Gains", icon: "🎯" },
          ].map((item) => (
            <div
              key={item.label}
              className="bg-surface-variant rounded-xl p-4 text-center"
            >
              <span className="text-2xl">{item.icon}</span>
              <p className="text-xs font-medium text-text-secondary mt-2">
                {item.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
