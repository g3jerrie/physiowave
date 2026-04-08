"use client";

import { useState, useEffect } from "react";
import { getSessions, type Session } from "@/lib/api";

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data);
    } catch {
      // Backend not running
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-[family-name:var(--font-outfit)]">
            📝 Treatment Sessions
          </h1>
          <p className="mt-1 text-text-secondary">
            Record and manage therapy sessions
          </p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card rounded-2xl p-5">
              <div className="h-4 bg-surface-variant rounded animate-shimmer w-1/3 mb-2" />
              <div className="h-3 bg-surface-variant rounded animate-shimmer w-2/3" />
            </div>
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <span className="text-5xl">📝</span>
          <h3 className="mt-4 font-semibold text-text-primary">No Sessions Yet</h3>
          <p className="text-sm text-text-secondary mt-1">
            Treatment session records will appear here. Use the Treatment Advisor
            to create AI-powered therapy sessions.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="glass-card rounded-2xl p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      session.status === "completed"
                        ? "bg-success"
                        : session.status === "cancelled"
                          ? "bg-text-tertiary"
                          : "bg-accent animate-pulse"
                    }`}
                  />
                  <div>
                    <h3 className="font-semibold text-sm text-text-primary">
                      {session.diagnosis || "Session"} — {session.therapy_used || "Unspecified"}
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">
                      Patient #{session.patient_id.slice(0, 8)} ·{" "}
                      {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {session.pain_score_before != null && session.pain_score_after != null && (
                    <div className="text-right">
                      <p className="text-xs text-text-tertiary">Pain Score</p>
                      <p className="text-sm font-semibold">
                        <span className="text-danger">{session.pain_score_before}</span>
                        <span className="text-text-tertiary mx-1">→</span>
                        <span className="text-success">{session.pain_score_after}</span>
                      </p>
                    </div>
                  )}

                  {session.duration_minutes && (
                    <span className="px-3 py-1 rounded-lg bg-surface-variant text-xs font-medium text-text-secondary">
                      {session.duration_minutes} min
                    </span>
                  )}

                  <span
                    className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                      session.status === "completed"
                        ? "bg-success/10 text-success"
                        : session.status === "cancelled"
                          ? "bg-surface-variant text-text-tertiary"
                          : "bg-accent/10 text-accent"
                    }`}
                  >
                    {session.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
