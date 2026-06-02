"use client";

import { useEffect, useState } from "react";
import { getTimeline, type TimelineData } from "@/lib/gameApi";

const EVENT_STYLES: Record<string, { color: string; symbol: string }> = {
  milestone: { color: "var(--accent-primary)", symbol: "◈" },
  wound: { color: "#ff6b6b", symbol: "✕" },
  wound_resolved: { color: "#55efc4", symbol: "✓" },
  phase_transition: { color: "var(--phase-bonded)", symbol: "◆" },
  default: { color: "var(--text-muted)", symbol: "◇" },
};

export default function TimelinePage() {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTimeline()
      .then(setTimeline)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state" style={{ height: "100vh" }}>
        <div className="empty-state-orb" />
        <span style={{ fontSize: "0.75rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)" }}>
          Loading
        </span>
      </div>
    );
  }

  return (
    <div style={{ padding: "40px 36px", maxWidth: 680, margin: "0 auto" }}>
      <div className="fade-in-up" style={{ marginBottom: 36 }}>
        <div className="section-title">Timeline</div>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
          Your story together
          {timeline?.days_since_start != null && (
            <span style={{ marginLeft: 8, color: "var(--text-accent)" }}>
              · {timeline.days_since_start} days
            </span>
          )}
        </p>
      </div>

      {(!timeline || timeline.events.length === 0) && (
        <div className="glass-card fade-in-up stagger-1" style={{ padding: 40, textAlign: "center" }}>
          <div style={{ fontSize: "2rem", marginBottom: 12, opacity: 0.3 }}>◆</div>
          <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
            No events yet. Milestones appear as your relationship deepens.
          </p>
        </div>
      )}

      {timeline && timeline.events.length > 0 && (
        <div style={{ position: "relative" }}>
          {/* Vertical line */}
          <div
            style={{
              position: "absolute",
              left: 4,
              top: 10,
              bottom: 10,
              width: 2,
              background: "linear-gradient(180deg, var(--border-glow), var(--border-subtle), transparent)",
            }}
          />

          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {timeline.events.map((event, i) => {
              const style = EVENT_STYLES[event.event_type] || EVENT_STYLES.default;
              return (
                <div
                  key={i}
                  className={`fade-in-up stagger-${Math.min(i + 1, 6)}`}
                  style={{
                    display: "flex",
                    gap: 24,
                    paddingLeft: 0,
                    position: "relative",
                  }}
                >
                  {/* Dot */}
                  <div
                    className={`timeline-dot ${event.event_type}`}
                    style={{ marginTop: 5 }}
                  />

                  {/* Content */}
                  <div
                    className="glass-card"
                    style={{
                      flex: 1,
                      padding: "16px 20px",
                      borderLeft: `2px solid ${style.color}`,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: 12,
                      }}
                    >
                      <p
                        style={{
                          fontSize: "0.875rem",
                          color: "var(--text-primary)",
                          lineHeight: 1.6,
                          flex: 1,
                        }}
                      >
                        {event.description}
                      </p>
                      <span
                        style={{
                          fontSize: "0.875rem",
                          color: style.color,
                          flexShrink: 0,
                        }}
                      >
                        {style.symbol}
                      </span>
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: 10,
                        marginTop: 10,
                        alignItems: "center",
                      }}
                    >
                      <span
                        className={`phase-badge phase-${event.phase.toLowerCase()}`}
                        style={{ fontSize: "0.5rem" }}
                      >
                        {event.phase}
                      </span>
                      <span
                        style={{
                          fontSize: "0.5625rem",
                          color: "var(--text-muted)",
                          letterSpacing: "0.05em",
                        }}
                      >
                        {new Date(event.timestamp).toLocaleDateString("en-IN", {
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
