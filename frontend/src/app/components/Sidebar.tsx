"use client";
 
import { useState, useEffect } from "react";
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
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isHidden, setIsHidden] = useState(false);
  const [mounted, setMounted] = useState(false);
 
  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("sidebar_collapsed");
    if (stored === "true") {
      setIsCollapsed(true);
    }
    const storedHidden = localStorage.getItem("sidebar_hidden");
    if (storedHidden === "true") {
      setIsHidden(true);
    }
  }, []);
 
  useEffect(() => {
    const handleToggle = () => {
      setIsHidden(prev => {
        const next = !prev;
        localStorage.setItem("sidebar_hidden", next ? "true" : "false");
        setTimeout(() => {
          window.dispatchEvent(new Event("sidebar-toggle"));
        }, 100);
        return next;
      });
    };
    window.addEventListener("toggle-modes-sidebar", handleToggle);
    return () => window.removeEventListener("toggle-modes-sidebar", handleToggle);
  }, []);
 
  const toggleCollapse = () => {
    const nextState = !isCollapsed;
    setIsCollapsed(nextState);
    localStorage.setItem("sidebar_collapsed", nextState ? "true" : "false");
    // Dispatch custom event to let pages know sidebar width changed
    window.dispatchEvent(new Event("sidebar-toggle"));
  };
 
  if (pathname === "/login") {
    return null;
  }
 
  return (
    <aside
      className="theme-dark"
      style={{
        width: isHidden ? 0 : (isCollapsed ? 68 : 200),
        borderRight: isHidden ? "none" : "1px solid var(--border-subtle)",
        background: "var(--bg-primary)",
        padding: isHidden ? 0 : (isCollapsed ? "20px 8px" : "28px 12px"),
        display: "flex",
        flexDirection: "column",
        gap: 4,
        position: "sticky",
        top: 0,
        height: "100vh",
        zIndex: 10,
        flexShrink: 0,
        transition: "width 0.25s cubic-bezier(0.4, 0, 0.2, 1), padding 0.25s ease, border-right 0.25s ease",
        overflowX: "hidden",
      }}
    >
      <div style={{ opacity: isHidden ? 0 : 1, transition: "opacity 0.15s ease", display: "flex", flexDirection: "column", height: "100%", width: "100%", overflowX: "hidden" }}>
        {/* Logo & Toggle Header */}
      <div 
        style={{ 
          padding: "4px 8px", 
          marginBottom: 20, 
          display: "flex", 
          alignItems: "center", 
          justifyContent: isCollapsed ? "center" : "space-between",
          gap: 10,
          position: "relative"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="rem-orb" style={{ width: 28, height: 28, flexShrink: 0 }} />
          {!isCollapsed && (
            <h1
              style={{
                fontSize: "1.125rem",
                fontWeight: 700,
                color: "var(--text-primary)",
                letterSpacing: "-0.03em",
                margin: 0,
                opacity: 1,
                transition: "opacity 0.2s ease"
              }}
            >
              Rem
            </h1>
          )}
        </div>
        
        {/* Collapse Button */}
        <button
          onClick={toggleCollapse}
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--text-muted)",
            cursor: "pointer",
            fontSize: "0.8125rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 4,
            borderRadius: 4,
            transition: "all 0.2s ease",
            alignSelf: "center",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.color = "var(--text-primary)";
            e.currentTarget.style.background = "rgba(255,255,255,0.05)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.color = "var(--text-muted)";
            e.currentTarget.style.background = "transparent";
          }}
        >
          {isCollapsed ? "▶" : "◀"}
        </button>
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
              title={isCollapsed ? item.label : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: isCollapsed ? "center" : "flex-start",
                padding: isCollapsed ? "10px 0" : "8px 12px",
                borderRadius: 8,
                fontSize: "0.8125rem",
                fontWeight: isActive ? 600 : 500,
                transition: "all 0.2s ease",
                height: 38,
              }}
            >
              <span
                style={{
                  fontSize: "0.875rem",
                  opacity: isActive ? 1 : 0.6,
                  color: isActive ? "var(--accent-primary)" : "inherit",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: isCollapsed ? "100%" : "auto",
                  marginRight: isCollapsed ? 0 : 10,
                  flexShrink: 0
                }}
              >
                {item.icon}
              </span>
              {!isCollapsed && item.label}
            </a>
          );
        })}
      </nav>
 
      {/* Footer */}
      <div 
        style={{ 
          marginTop: "auto", 
          padding: isCollapsed ? "8px 0" : "8px 8px", 
          display: "flex", 
          flexDirection: "column", 
          gap: 12,
          alignItems: isCollapsed ? "center" : "stretch"
        }}
      >
        {isCollapsed ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, width: "100%", alignItems: "center" }}>
            <button
              onClick={() => {
                if (pathname !== "/") {
                  window.location.href = "/?drawer=plans";
                } else {
                  const event = new CustomEvent("open-plans-drawer", { detail: 'plans' });
                  window.dispatchEvent(event);
                }
              }}
              title="Plans"
              style={{
                background: "rgba(95, 125, 97, 0.08)",
                border: "1px solid rgba(95, 125, 97, 0.15)",
                borderRadius: 6,
                color: "var(--accent-primary)",
                cursor: "pointer",
                padding: "8px",
                width: 32,
                height: 32,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.875rem"
              }}
            >
              📅
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
              title="Vault"
              style={{
                background: "rgba(184, 92, 75, 0.08)",
                border: "1px solid rgba(184, 92, 75, 0.15)",
                borderRadius: 6,
                color: "var(--text-accent)",
                cursor: "pointer",
                padding: "8px",
                width: 32,
                height: 32,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "0.875rem"
              }}
            >
              🧠
            </button>
          </div>
        ) : (
          <>
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
                  background: "rgba(95, 125, 97, 0.08)",
                  border: "1px solid rgba(95, 125, 97, 0.15)",
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
                  background: "rgba(184, 92, 75, 0.08)",
                  border: "1px solid rgba(184, 92, 75, 0.15)",
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
          </>
        )}
      </div>
      </div>
    </aside>
  );
}
