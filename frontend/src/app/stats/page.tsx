"use client";

import { useEffect, useState } from "react";
import {
  getStats,
  getPatterns,
  getInsideJokes,
  type StatsData,
  type PatternsData,
  type InsideJokesData,
} from "@/lib/gameApi";

export default function StatsPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [patterns, setPatterns] = useState<PatternsData | null>(null);
  const [jokes, setJokes] = useState<InsideJokesData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getStats(), getPatterns(), getInsideJokes()])
      .then(([s, p, j]) => { setStats(s); setPatterns(p); setJokes(j); })
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
    <div style={{ padding: "40px 36px", maxWidth: 860, margin: "0 auto" }}>
      <div className="fade-in-up" style={{ marginBottom: 36 }}>
        <div className="section-title">Relationship Stats</div>
      </div>

      {/* Stat Cards */}
      {stats && (
        <div
          className="fade-in-up stagger-1"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 12,
            marginBottom: 24,
          }}
        >
          {[
            { label: "Messages", value: stats.total_messages },
            { label: "Longest Streak", value: stats.longest_streak },
            { label: "Current Streak", value: stats.current_streak },
            { label: "Phase", value: stats.current_phase },
            { label: "Total XP", value: stats.total_xp },
            { label: "Days Active", value: stats.days_active ?? 0 },
          ].map((s) => (
            <div key={s.label} className="glass-card stat-card">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Behavioral Patterns */}
      <div className="glass-card fade-in-up stagger-2" style={{ padding: 28, marginBottom: 20 }}>
        <div className="section-title">Behavioral Patterns</div>

        {(!patterns || patterns.patterns.length === 0) ? (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: "1.5rem", marginBottom: 8, opacity: 0.3 }}>◇</div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
              Patterns emerge over time. Keep talking.
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {patterns.patterns.map((p, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px 16px",
                  background: "var(--bg-glass)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <div>
                  <div style={{ fontSize: "0.875rem", color: "var(--text-primary)", fontWeight: 500 }}>
                    {p.pattern}
                  </div>
                  <div style={{ fontSize: "0.625rem", color: "var(--text-muted)", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    {p.pattern_type}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: "0.625rem",
                    color: "var(--accent-primary)",
                    fontWeight: 600,
                    padding: "3px 10px",
                    background: "var(--accent-soft)",
                    borderRadius: "var(--radius-full)",
                    letterSpacing: "0.05em",
                  }}
                >
                  {p.confidence}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inside Jokes */}
      <div className="glass-card fade-in-up stagger-3" style={{ padding: 28 }}>
        <div className="section-title">Inside Jokes</div>

        {(!jokes || jokes.jokes.length === 0) ? (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: "1.5rem", marginBottom: 8, opacity: 0.3 }}>◇</div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
              No inside jokes yet. They form naturally.
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {jokes.jokes.map((joke, i) => (
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
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginTop: 6,
                  }}
                >
                  <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                    {joke.context}
                  </span>
                  {joke.joke_type && (
                    <span
                      style={{
                        fontSize: "0.5625rem",
                        color: "var(--text-muted)",
                        textTransform: "uppercase",
                        letterSpacing: "0.08em",
                      }}
                    >
                      {joke.joke_type}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
