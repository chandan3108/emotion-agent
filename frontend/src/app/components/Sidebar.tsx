"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Chat", icon: "◈" },
  { href: "/date", label: "Date Mode", icon: "🎭" },
  { href: "/games", label: "Mini-Games", icon: "🎮" },
  { href: "/dashboard", label: "Overview", icon: "◐" },
  { href: "/diary", label: "Diary", icon: "◉" },
  { href: "/scrapbook", label: "Scrapbook", icon: "📸" },
  { href: "/secrets", label: "Rem's Secrets", icon: "🫦" },
  { href: "/timeline", label: "Timeline", icon: "◆" },
  { href: "/stats", label: "Stats", icon: "◇" },
  { href: "/mind", label: "Mind", icon: "✦" },
  { href: "/settings", label: "Settings", icon: "⚙" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      style={{
        width: 200,
        borderRight: "1px solid var(--border-subtle)",
        background: "rgba(8, 8, 15, 0.95)",
        backdropFilter: "blur(20px)",
        padding: "28px 12px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
        position: "sticky",
        top: 0,
        height: "100vh",
        zIndex: 10,
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ padding: "4px 14px", marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="rem-orb" style={{ width: 28, height: 28 }}>
            <div
              style={{
                position: "absolute",
                inset: 2,
                borderRadius: "50%",
                background: "var(--bg-primary)",
              }}
            />
          </div>
          <h1
            style={{
              fontSize: "1.125rem",
              fontWeight: 700,
              color: "var(--text-primary)",
              letterSpacing: "-0.03em",
            }}
          >
            Rem
          </h1>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <a
              key={item.href}
              href={item.href}
              className={`nav-link ${isActive ? "active" : ""}`}
            >
              <span
                style={{
                  fontSize: "0.75rem",
                  opacity: isActive ? 1 : 0.5,
                  color: isActive ? "var(--accent-primary)" : "inherit",
                }}
              >
                {item.icon}
              </span>
              {item.label}
            </a>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ marginTop: "auto", padding: "8px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => {
              if (pathname !== "/") {
                window.location.href = "/?drawer=plans";
              } else {
                const event = new CustomEvent("open-plans-drawer", { detail: 'plans' });
                window.dispatchEvent(event);
              }
            }}
            style={{
              flex: 1,
              padding: "6px 8px",
              fontSize: "0.6875rem",
              fontWeight: 600,
              background: "rgba(151, 117, 250, 0.08)",
              border: "1px solid rgba(151, 117, 250, 0.15)",
              borderRadius: 6,
              color: "var(--accent-primary)",
              cursor: "pointer",
              transition: "all 0.2s ease"
            }}
          >
            📅 Plans
          </button>
          <button
            onClick={() => {
              if (pathname !== "/") {
                window.location.href = "/?drawer=vault";
              } else {
                const event = new CustomEvent("open-plans-drawer", { detail: 'vault' });
                window.dispatchEvent(event);
              }
            }}
            style={{
              flex: 1,
              padding: "6px 8px",
              fontSize: "0.6875rem",
              fontWeight: 600,
              background: "rgba(201, 176, 255, 0.08)",
              border: "1px solid rgba(201, 176, 255, 0.15)",
              borderRadius: 6,
              color: "var(--text-accent)",
              cursor: "pointer",
              transition: "all 0.2s ease"
            }}
          >
            🧠 Vault
          </button>
        </div>

        <div
          style={{
            fontSize: "0.5625rem",
            color: "var(--text-muted)",
            lineHeight: 1.5,
            letterSpacing: "0.05em",
            textTransform: "uppercase",
          }}
        >
          cognitive architecture
          <br />
          v2.0
        </div>
      </div>
    </aside>
  );
}
