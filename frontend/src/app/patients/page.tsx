"use client";

import { useState, useEffect } from "react";
import { getPatients, createPatient, type Patient, type PatientCreate } from "@/lib/api";

const RISK_OPTIONS = [
  "metal_implants", "pacemaker", "cardiac_monitor", "pregnancy",
  "epilepsy", "malignancy", "open_wounds", "active_infection",
  "dvt_history", "osteoporosis", "sensory_deficit",
];

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<PatientCreate>({
    name: "",
    age: undefined,
    gender: undefined,
    risk_factors: [],
    notes: "",
  });

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      const data = await getPatients();
      setPatients(data);
    } catch {
      // Backend not running — show empty state
    }
    setLoading(false);
  };

  const handleCreate = async () => {
    try {
      await createPatient(form);
      setShowForm(false);
      setForm({ name: "", risk_factors: [], notes: "" });
      loadPatients();
    } catch (err) {
      alert("Failed to create patient");
    }
  };

  const toggleRisk = (r: string) => {
    setForm((prev) => ({
      ...prev,
      risk_factors: prev.risk_factors.includes(r)
        ? prev.risk_factors.filter((f) => f !== r)
        : [...prev.risk_factors, r],
    }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)]">
            👥 Patient Records
          </h1>
          <p className="mt-1 text-text-secondary">
            Manage patient profiles and medical histories
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-5 py-2.5 rounded-xl gradient-primary text-white text-sm font-semibold shadow-lg hover:shadow-xl transition-all"
        >
          + Add Patient
        </button>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="glass-card rounded-2xl p-6 space-y-4 animate-slide-in">
          <h2 className="font-semibold text-text-primary">New Patient</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Patient Name"
              value={form.name ?? ""}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
            <input
              type="number"
              placeholder="Age"
              value={form.age ?? ""}
              onChange={(e) =>
                setForm({ ...form, age: e.target.value ? +e.target.value : undefined })
              }
              className="rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
            <select
              value={form.gender ?? ""}
              onChange={(e) =>
                setForm({ ...form, gender: e.target.value || undefined })
              }
              className="rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Gender...</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-2">
              Risk Factors
            </label>
            <div className="flex flex-wrap gap-2">
              {RISK_OPTIONS.map((r) => (
                <button
                  key={r}
                  onClick={() => toggleRisk(r)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                    form.risk_factors.includes(r)
                      ? "bg-danger text-white"
                      : "bg-surface-variant text-text-secondary hover:bg-danger/10"
                  }`}
                >
                  {r.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>

          <textarea
            placeholder="Notes..."
            rows={2}
            value={form.notes ?? ""}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="w-full rounded-xl bg-surface-variant border border-border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
          />

          <div className="flex gap-3">
            <button
              onClick={handleCreate}
              className="px-6 py-2.5 rounded-xl gradient-primary text-white text-sm font-semibold"
            >
              Save Patient
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-6 py-2.5 rounded-xl bg-surface-variant text-text-secondary text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Patient List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card rounded-2xl p-5">
              <div className="h-4 bg-surface-variant rounded animate-shimmer w-1/3 mb-2" />
              <div className="h-3 bg-surface-variant rounded animate-shimmer w-1/2" />
            </div>
          ))}
        </div>
      ) : patients.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <span className="text-5xl">👥</span>
          <h3 className="mt-4 font-semibold text-text-primary">No Patients Yet</h3>
          <p className="text-sm text-text-secondary mt-1">
            Add your first patient to get started with treatment tracking.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {patients.map((patient) => (
            <div
              key={patient.id}
              className="glass-card rounded-2xl p-5 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-text-primary">
                    Patient #{patient.id.slice(0, 8)}
                  </h3>
                  <p className="text-sm text-text-secondary mt-0.5">
                    {patient.age ? `${patient.age}y` : "—"}{" "}
                    {patient.gender ? `· ${patient.gender}` : ""}
                  </p>
                </div>
                <span className="px-2 py-1 rounded-lg bg-primary/10 text-primary text-xs font-semibold">
                  {patient.session_count} sessions
                </span>
              </div>

              {patient.risk_factors.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {patient.risk_factors.map((f) => (
                    <span
                      key={f}
                      className="px-2 py-0.5 rounded bg-danger/10 text-danger text-[10px] font-medium"
                    >
                      {f.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              )}

              {patient.notes && (
                <p className="mt-2 text-xs text-text-tertiary line-clamp-2">
                  {patient.notes}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
