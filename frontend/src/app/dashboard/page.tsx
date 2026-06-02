"use client";

import { useEffect, useState } from "react";
import {
  getXP,
  getStats,
  getInsideJokes,
  type XPData,
  type StatsData,
  type InsideJokesData,
} from "@/lib/gameApi";

const PHASE_ORDER = ["Discovery", "Building", "Steady", "Deep", "Bonded"];

const PHASE_DESCRIPTIONS: Record<string, string> = {
  Discovery: "Getting to know each other",
  Building: "Mutual interest forming",
  Steady: "Comfortable rapport",
  Deep: "Real emotional investment",
  Bonded: "Unshakeable connection",
};

const PHASE_UNLOCKS: Record<string, string[]> = {
  Discovery: ["Basic conversation"],
  Building: ["Inside jokes", "Diary access"],
  Steady: ["Pattern recognition", "Proactive callbacks"],
  Deep: ["Full diary", "Vulnerability"],
  Bonded: ["Complete access", "Unfiltered mode"],
};

export default function DashboardPage() {
  const [xp, setXp] = useState<XPData | null>(null);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [jokes, setJokes] = useState<InsideJokesData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getXP(), getStats(), getInsideJokes()])
      .then(([x, s, j]) => { setXp(x); setStats(s); setJokes(j); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state" style={{ height: "100vh" }}>
        <div className="empty-state-orb" />
        <span style={{ fontSize: "0.75rem", letterSpacing: "0.1em", textTransform: "uppercase" }}>
          Loading
        </span>
      </div>
    );
  }

  const currentIdx = xp ? PHASE_ORDER.indexOf(xp.phase) : 0;

  return (
    <div style={{ padding: "40px 36px", maxWidth: 860, margin: "0 auto" }}>
      {/* Title */}
      <div className="fade-in-up" style={{ marginBottom: 36 }}>
        <div className="section-title">Overview</div>
      </div>

      {/* XP Hero Card */}
      {xp && (
        <div className="glass-card fade-in-up stagger-1" style={{ padding: 32, marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span className={`phase-badge phase-${xp.phase.toLowerCase()}`}>{xp.phase}</span>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginTop: 10, lineHeight: 1.5 }}>
                {PHASE_DESCRIPTIONS[xp.phase]}
              </p>
            </div>
            <div style={{ textAlign: "right" }}>
              <div
                style={{
                  fontSize: "2.5rem",
                  fontWeight: 700,
                  letterSpacing: "-0.03em",
                  background: "linear-gradient(135deg, var(--text-primary), var(--accent-primary))",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                {xp.total_xp}
              </div>
              <div style={{ fontSize: "0.5625rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginTop: 2 }}>
                Total XP
              </div>
            </div>
          </div>

          {/* Progress */}
          <div style={{ marginTop: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.625rem", color: "var(--text-muted)", marginBottom: 8, letterSpacing: "0.05em", textTransform: "uppercase" }}>
              <span>{xp.phase}</span>
              <span>{xp.next_phase || "Max"}</span>
            </div>
            <div className="xp-bar-container" style={{ height: 6 }}>
              <div className="xp-bar-fill" style={{ width: `${xp.phase_progress_pct}%` }} />
            </div>
            <div style={{ textAlign: "right", fontSize: "0.5625rem", color: "var(--text-muted)", marginTop: 6, letterSpacing: "0.05em" }}>
              {xp.xp_to_next > 0 ? `${xp.xp_to_next} XP to next` : "Max reached"}
            </div>
          </div>

          {/* Streak */}
          {xp.streak_days > 0 && (
            <div
              style={{
                marginTop: 16,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "6px 14px",
                background: "rgba(253, 203, 110, 0.06)",
                borderRadius: "var(--radius-full)",
                border: "1px solid rgba(253, 203, 110, 0.1)",
              }}
            >
              <span style={{ fontSize: "0.875rem" }}>🔥</span>
              <span style={{ fontWeight: 600, color: "#fdcb6e", fontSize: "0.8125rem" }}>
                {xp.streak_days} day streak
              </span>
            </div>
          )}
        </div>
      )}

      {/* Phase Ladder */}
      <div className="glass-card fade-in-up stagger-2" style={{ padding: 28, marginBottom: 20 }}>
        <div className="section-title">Progression</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {PHASE_ORDER.map((phase, idx) => {
            const reached = idx <= currentIdx;
            const current = idx === currentIdx;
            return (
              <div
                key={phase}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "10px 14px",
                  borderRadius: "var(--radius-md)",
                  background: current ? "rgba(151, 117, 250, 0.04)" : "transparent",
                  border: current ? "1px solid rgba(151, 117, 250, 0.08)" : "1px solid transparent",
                  opacity: reached ? 1 : 0.3,
                  transition: "all 0.3s ease",
                }}
              >
                <div
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.625rem",
                    fontWeight: 600,
                    background: reached ? "var(--accent-primary)" : "var(--bg-input)",
                    color: reached ? "white" : "var(--text-muted)",
                    flexShrink: 0,
                    transition: "all 0.3s ease",
                  }}
                >
                  {reached ? "✓" : idx + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <span
                    style={{
                      fontSize: "0.8125rem",
                      fontWeight: current ? 600 : 400,
                      color: current ? "var(--text-accent)" : "var(--text-secondary)",
                    }}
                  >
                    {phase}
                  </span>
                  <div style={{ fontSize: "0.625rem", color: "var(--text-muted)", marginTop: 2 }}>
                    {(PHASE_UNLOCKS[phase] || []).join(" · ")}
                  </div>
                </div>
                {current && (
                  <span
                    style={{
                      fontSize: "0.5rem",
                      color: "var(--accent-primary)",
                      fontWeight: 600,
                      letterSpacing: "0.12em",
                      textTransform: "uppercase",
                    }}
                  >
                    Now
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div
          className="fade-in-up stagger-3"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 12,
            marginBottom: 20,
          }}
        >
          {[
            { label: "Messages", value: stats.total_messages },
            { label: "Streak", value: stats.current_streak },
            { label: "Inside Jokes", value: stats.inside_joke_count },
            { label: "Diary", value: stats.diary_entry_count },
            { label: "Milestones", value: stats.milestone_count },
            { label: "Days", value: stats.days_active ?? 0 },
          ].map((s) => (
            <div key={s.label} className="glass-card stat-card">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Inside Jokes */}
      {jokes && jokes.jokes.length > 0 && (
        <div className="glass-card fade-in-up stagger-4" style={{ padding: 28 }}>
          <div className="section-title">Inside Jokes</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {jokes.jokes.slice(0, 4).map((joke, i) => (
              <div
                key={i}
                style={{
                  padding: "12px 16px",
                  background: "var(--bg-glass)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-primary)" }}>
                  &ldquo;{joke.reference}&rdquo;
                </div>
                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: 4 }}>
                  {joke.context}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
