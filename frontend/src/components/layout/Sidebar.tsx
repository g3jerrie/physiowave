"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/advisor", label: "Treatment Advisor", icon: "🧠" },
  { href: "/protocols", label: "Protocols", icon: "📋" },
  { href: "/knowledge", label: "Knowledge Base", icon: "📚" },
  { href: "/safety", label: "Safety Check", icon: "🛡️" },
  { href: "/patients", label: "Patients", icon: "👥" },
  { href: "/sessions", label: "Sessions", icon: "📝" },
  { href: "/analytics", label: "Analytics", icon: "📈" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-surface border-r border-border flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-border">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center text-white shadow-lg group-hover:shadow-xl transition-shadow">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold font-[family-name:var(--font-outfit)] text-text-primary">
              PhysioWave
            </h1>
            <p className="text-[10px] uppercase tracking-widest text-text-tertiary">
              Clinical AI
            </p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? "bg-primary/10 text-primary shadow-sm"
                  : "text-text-secondary hover:bg-surface-variant hover:text-text-primary"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary animate-pulse-glow" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Status Badge */}
      <div className="px-4 py-4 border-t border-border">
        <StatusBadge />
      </div>
    </aside>
  );
}

function StatusBadge() {
  return (
    <div className="glass-card rounded-xl px-4 py-3">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
        <span className="text-xs font-semibold text-text-secondary">System Status</span>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-[11px]">
          <span className="text-text-tertiary">AI Engine</span>
          <span className="text-success font-medium">Gemma 3 4B</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-text-tertiary">Mode</span>
          <span className="text-primary font-medium">100% Offline</span>
        </div>
      </div>
    </div>
  );
}
