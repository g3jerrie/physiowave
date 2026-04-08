"use client";

const PROTOCOLS = [
  {
    condition: "Knee Osteoarthritis",
    therapy: "IFT",
    frequency: "80–120 Hz",
    intensity: "Comfortable sensory level",
    duration: "15 minutes",
    placement: "Quadripolar around the knee joint",
    sessions: "3–4 per week",
    phase: "Chronic",
  },
  {
    condition: "Cervical Spondylosis",
    therapy: "TENS",
    frequency: "80–100 Hz",
    intensity: "Mild tingling",
    duration: "20 minutes",
    placement: "Paravertebral C3-C7",
    sessions: "Daily for 2 weeks",
    phase: "Subacute",
  },
  {
    condition: "Lumbar Spondylosis",
    therapy: "IFT + Deep Heat",
    frequency: "IFT: 100 Hz / DH: continuous",
    intensity: "Comfortable",
    duration: "15 min each",
    placement: "IFT: Quadripolar lumbar / DH: over paravertebral muscles",
    sessions: "3–4 per week",
    phase: "Chronic",
  },
  {
    condition: "Frozen Shoulder",
    therapy: "Ultrasound + TENS",
    frequency: "US: 1 MHz / TENS: 80 Hz",
    intensity: "US: 1.5 W/cm² / TENS: sensory",
    duration: "US: 5 min / TENS: 20 min",
    placement: "Anterior and posterior glenohumeral joint",
    sessions: "5 per week",
    phase: "Subacute",
  },
  {
    condition: "Sciatica",
    therapy: "IFT",
    frequency: "80–120 Hz (sweep)",
    intensity: "Strong but comfortable",
    duration: "15–20 minutes",
    placement: "Quadripolar over lumbar spine and gluteal region",
    sessions: "4–5 per week",
    phase: "Acute",
  },
  {
    condition: "Tennis Elbow",
    therapy: "Ultrasound",
    frequency: "3 MHz",
    intensity: "0.5–1.0 W/cm²",
    duration: "5 minutes",
    placement: "Lateral epicondyle and common extensor origin",
    sessions: "3 per week",
    phase: "Subacute",
  },
  {
    condition: "Muscle Spasm",
    therapy: "MS (Muscle Stimulation)",
    frequency: "35–50 Hz",
    intensity: "Visible contraction",
    duration: "10–15 minutes",
    placement: "Over the spasmodic muscle belly",
    sessions: "As needed",
    phase: "Acute",
  },
  {
    condition: "Chronic Back Pain",
    therapy: "TENS + Deep Heat",
    frequency: "TENS: 80–100 Hz / DH: continuous",
    intensity: "Comfortable tingling",
    duration: "20–30 min combined",
    placement: "TENS: paravertebral L1-S1 / DH: over erector spinae",
    sessions: "Daily",
    phase: "Chronic",
  },
  {
    condition: "Ligament Sprain (Ankle)",
    therapy: "Ultrasound",
    frequency: "3 MHz pulsed",
    intensity: "0.5 W/cm²",
    duration: "5 minutes",
    placement: "Over the affected ligament",
    sessions: "3–5 per week",
    phase: "Acute",
  },
  {
    condition: "Tendinitis",
    therapy: "Ultrasound + IFT",
    frequency: "US: 3 MHz / IFT: 100 Hz",
    intensity: "US: 1.0 W/cm² / IFT: sensory",
    duration: "US: 5 min / IFT: 15 min",
    placement: "Over the tendon and surrounding tissue",
    sessions: "3–4 per week",
    phase: "Subacute",
  },
];

const PHASE_COLORS: Record<string, string> = {
  Acute: "bg-danger/10 text-danger",
  Subacute: "bg-accent/10 text-accent",
  Chronic: "bg-primary/10 text-primary",
};

export default function ProtocolsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)]">
          📋 Condition Protocol Library
        </h1>
        <p className="mt-1 text-text-secondary">
          Evidence-based treatment protocols aligned with the Combi 5-in-1 machine manual
        </p>
      </div>

      <div className="space-y-4">
        {PROTOCOLS.map((protocol) => (
          <div
            key={protocol.condition}
            className="glass-card rounded-2xl p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold font-[family-name:var(--font-outfit)] text-text-primary">
                  {protocol.condition}
                </h3>
                <span className="inline-block mt-1 px-3 py-1 rounded-lg bg-secondary/10 text-secondary text-xs font-semibold">
                  {protocol.therapy}
                </span>
              </div>
              <span
                className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                  PHASE_COLORS[protocol.phase] || "bg-surface-variant text-text-secondary"
                }`}
              >
                {protocol.phase}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-text-tertiary text-xs">Frequency</p>
                <p className="font-medium text-text-primary mt-0.5">{protocol.frequency}</p>
              </div>
              <div>
                <p className="text-text-tertiary text-xs">Intensity</p>
                <p className="font-medium text-text-primary mt-0.5">{protocol.intensity}</p>
              </div>
              <div>
                <p className="text-text-tertiary text-xs">Duration</p>
                <p className="font-medium text-text-primary mt-0.5">{protocol.duration}</p>
              </div>
              <div className="col-span-2">
                <p className="text-text-tertiary text-xs">Electrode/Probe Placement</p>
                <p className="font-medium text-text-primary mt-0.5">{protocol.placement}</p>
              </div>
              <div>
                <p className="text-text-tertiary text-xs">Sessions</p>
                <p className="font-medium text-text-primary mt-0.5">{protocol.sessions}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
