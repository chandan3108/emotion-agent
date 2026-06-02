"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAchievements } from "@/lib/gameApi";

export default function GamesHubPage() {
  const [unlocked, setUnlocked] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAchievements()
      .then((res) => {
        if (res && res.unlocked) {
          setUnlocked(res.unlocked);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const achievementsList = [
    { id: "debate_champion", title: "Debate Champion", icon: "👑", desc: "Won a Debate Battle against Rem" },
    { id: "win_over_promise", title: "Trust Rebuilder", icon: "🤝", desc: "Completed the 'Broken Promise' scenario" },
    { id: "win_over_ghost", title: "Anger Tamer", icon: "🔥", desc: "Completed the 'Silent Treatment' scenario" },
    { id: "win_over_stranger", title: "Heart Melter", icon: "❄️", desc: "Completed the 'Cold Stranger' scenario" },
  ];

  return (
    <div style={{ padding: "40px 36px", maxWidth: 860, margin: "0 auto" }}>
      <div className="fade-in-up" style={{ marginBottom: 36 }}>
        <h1 className="section-title" style={{ fontSize: "1.75rem", fontWeight: 700, letterSpacing: "-0.02em" }}>
          🎮 Mini-Games Hub
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: 6 }}>
          Challenge Rem in isolated mini-experiences. These battles of wits and psychology will not affect your main relationship state.
        </p>
      </div>

      <div
        className="fade-in-up stagger-1"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20,
          marginBottom: 40,
        }}
      >
        {/* Card 1: Debate Battle */}
        <a
          href="/games/debate"
          className="glass-card"
          style={{
            padding: 32,
            border: "1px solid rgba(236, 72, 153, 0.2)",
            position: "relative",
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            minHeight: 240,
            background: "linear-gradient(135deg, rgba(236, 72, 153, 0.05) 0%, rgba(8, 8, 15, 0.8) 100%)",
            textDecoration: "none",
            cursor: "pointer",
          }}
        >
          <div>
            <div style={{ fontSize: "2rem", marginBottom: 12 }}>⚖️</div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#f472b6", marginBottom: 8 }}>
              Debate Battle
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", lineHeight: 1.5 }}>
              Argue with Rem in a 5-turn clash of wits on ridiculous topics. You will be assigned a random stance. Can you convince the neutral LLM Judge to vote for you?
            </p>
          </div>
          <div
            className="action-button"
            style={{
              display: "block",
              marginTop: 20,
              textAlign: "center",
              background: "rgba(236, 72, 153, 0.15)",
              border: "1px solid #f472b6",
              color: "#f472b6",
              textTransform: "uppercase",
              fontSize: "0.75rem",
              fontWeight: 600,
              letterSpacing: "0.08em",
              padding: "10px 16px",
              borderRadius: "var(--radius-md)",
            }}
          >
            Enter Arena
          </div>
        </a>

        {/* Card 2: Win Her Over */}
        <a
          href="/games/win-over"
          className="glass-card"
          style={{
            padding: 32,
            border: "1px solid rgba(6, 182, 212, 0.2)",
            position: "relative",
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            minHeight: 240,
            background: "linear-gradient(135deg, rgba(6, 182, 212, 0.05) 0%, rgba(8, 8, 15, 0.8) 100%)",
            textDecoration: "none",
            cursor: "pointer",
          }}
        >
          <div>
            <div style={{ fontSize: "2rem", marginBottom: 12 }}>💔</div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#22d3ee", marginBottom: 8 }}>
              Win Her Over
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", lineHeight: 1.5 }}>
              Start with Rem in a state of high anger and distress. You have exactly 10 texts to successfully pacify her and rebuild trust. Saying the wrong thing will trigger a block.
            </p>
          </div>
          <div
            className="action-button"
            style={{
              display: "block",
              marginTop: 20,
              textAlign: "center",
              background: "rgba(6, 182, 212, 0.15)",
              border: "1px solid #22d3ee",
              color: "#22d3ee",
              textTransform: "uppercase",
              fontSize: "0.75rem",
              fontWeight: 600,
              letterSpacing: "0.08em",
              padding: "10px 16px",
              borderRadius: "var(--radius-md)",
            }}
          >
            Start Challenge
          </div>
        </a>
      </div>

      {/* Achievements Section */}
      <div className="glass-card fade-in-up stagger-2" style={{ padding: 28 }}>
        <h3 className="section-title" style={{ fontSize: "1rem", fontWeight: 600, marginBottom: 20 }}>
          🏆 Unlocked Scrapbook Medals
        </h3>

        {loading ? (
          <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>Loading achievements...</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {achievementsList.map((ach) => {
              const isUnlocked = unlocked.includes(ach.id);
              return (
                <div
                  key={ach.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                    padding: 16,
                    background: isUnlocked ? "rgba(16, 185, 129, 0.05)" : "rgba(255, 255, 255, 0.02)",
                    borderRadius: "var(--radius-md)",
                    border: isUnlocked
                      ? "1px solid rgba(16, 185, 129, 0.2)"
                      : "1px solid var(--border-subtle)",
                    opacity: isUnlocked ? 1 : 0.4,
                    transition: "all 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "1.75rem",
                      width: 44,
                      height: 44,
                      borderRadius: "50%",
                      background: isUnlocked ? "rgba(16, 185, 129, 0.1)" : "rgba(255, 255, 255, 0.05)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      border: isUnlocked ? "1px solid rgba(16, 185, 129, 0.3)" : "none",
                    }}
                  >
                    {ach.icon}
                  </div>
                  <div>
                    <h4
                      style={{
                        fontSize: "0.875rem",
                        fontWeight: 600,
                        color: isUnlocked ? "var(--text-primary)" : "var(--text-muted)",
                      }}
                    >
                      {ach.title}
                    </h4>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>
                      {isUnlocked ? ach.desc : "Locked Challenge"}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
