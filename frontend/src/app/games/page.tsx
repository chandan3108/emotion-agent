"use client";

import { useEffect, useState } from "react";
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
    { id: "personality_certified", title: "Psyche Certified", icon: "🧠", desc: "Completed the 30-Question Personality Test" },
    { id: "master_chef", title: "Star Sous Chef", icon: "🍳", desc: "Cooked a successful meal step-by-step with Rem" },
    { id: "secret_unlocked", title: "Vibe Alchemist", icon: "🫦", desc: "Unlocked a romantic secret during Spicy Chat" },
    { id: "yap_scholar", title: "Yap Scholar", icon: "🎓", desc: "Survived a 10-turn grounded debate in Yap Mode" },
    { id: "detective_rem", title: "Master Detective", icon: "🕵️‍♂️", desc: "Solved a procedural Murder Mystery with Rem" },
    { id: "court_master", title: "Courtroom Master", icon: "⚖️", desc: "Won a Trial Verdict in Law and Rem" }
  ];

  const games = [
    {
      href: "/games/rpg",
      icon: "🕵️‍♂️",
      title: "Sherlock Rem",
      desc: "Investigate procedural murder mysteries and corporate hacks with Rem as your sarcasm-heavy partner. Search rooms for hidden clues, interrogate suspects, build alibis, and present your final accusation.",
      btnText: "Start Case"
    },
    {
      href: "/games/court",
      icon: "⚖️",
      title: "Law and Rem",
      desc: "Defend clients in Ace Attorney courtroom battles. Question witnesses dynamically, raise objections with evidence, explore rooms during recesses, and win over the Judge and Jury LLMs.",
      btnText: "Take Stand"
    },
    {
      href: "/games/spicy",
      icon: "🌶️",
      title: "Spicy Chat",
      desc: "An isolated, uncensored fantasy chat sandbox with Rem powered by OpenRouter models. Customize locations and moods, and extract romantic Secrets keepsakes.",
      btnText: "Enter Vault"
    },
    {
      href: "/games/debate",
      icon: "⚖️",
      title: "Debate Battle",
      desc: "Argue with Rem in a 5-turn clash of wits on ridiculous topics. You will be assigned a random stance. Can you convince the neutral LLM Judge to vote for you?",
      btnText: "Enter Arena"
    },
    {
      href: "/games/win-over",
      icon: "💔",
      title: "Win Her Over",
      desc: "Start with Rem in a state of high anger and distress. You have exactly 10 texts to successfully pacify her and rebuild trust. Saying the wrong thing will trigger a block.",
      btnText: "Start Challenge"
    },
    {
      href: "/games/personality",
      icon: "🧠",
      title: "Psyche Profiler",
      desc: "Answer 30 personality/relationship questions. Rem will offer dynamic, sarcastic feedback after your answers and run a detailed LLM evaluation of your character.",
      btnText: "Get Evaluated"
    },
    {
      href: "/games/cook",
      icon: "🍳",
      title: "Cooking with Rem",
      desc: "Choose a dish to cook together step-by-step. Keep the Chaos Meter low to avoid culinary disasters, and read Rem's sarcastic review in your Scrapbook Cookbook.",
      btnText: "Start Cooking"
    },
    {
      href: "/games/yap",
      icon: "🗣️",
      title: "Yap Mode",
      desc: "Give Rem a topic and watch her load grounded, verified facts from the web to yap about it in-depth. Discuss facts and her sarcastic views with zero hallucinations.",
      btnText: "Start Yapping"
    }
  ];

  return (
    <div style={{ padding: "40px 36px", maxWidth: 960, margin: "0 auto" }}>
      <div className="fade-in-up" style={{ marginBottom: 36 }}>
        <h1 className="section-title" style={{ fontSize: "1.75rem", fontWeight: 700, letterSpacing: "-0.02em" }}>
          🎮 Mini-Games Hub
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: 6 }}>
          Challenge Rem in isolated mini-experiences. These battles of wits, psychology, and romance will not affect your main relationship state.
        </p>
      </div>

      <div
        className="fade-in-up stagger-1"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 20,
          marginBottom: 40,
        }}
      >
        {games.map((g, i) => (
          <a
            key={i}
            href={g.href}
            className="glass-card"
            style={{
              padding: 28,
              border: "1px solid var(--border-subtle)",
              position: "relative",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              minHeight: 250,
              background: "var(--bg-surface)",
              textDecoration: "none",
              cursor: "pointer",
            }}
          >
            <div>
              <div style={{ fontSize: "2rem", marginBottom: 12 }}>{g.icon}</div>
              <h2 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
                {g.title}
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", lineHeight: 1.5 }}>
                {g.desc}
              </p>
            </div>
            <div
              className="action-button"
              style={{
                display: "block",
                marginTop: 20,
                textAlign: "center",
                background: "#000000",
                color: "#FAF6EE",
                textTransform: "uppercase",
                fontSize: "0.75rem",
                fontWeight: 600,
                letterSpacing: "0.08em",
                padding: "8px 14px",
                borderRadius: "var(--radius-md)",
                border: "none",
              }}
            >
              {g.btnText}
            </div>
          </a>
        ))}
      </div>

      {/* Achievements Section */}
      <div className="glass-card fade-in-up stagger-2" style={{ padding: 28 }}>
        <h3 className="section-title" style={{ fontSize: "1rem", fontWeight: 600, marginBottom: 20 }}>
          🏆 Unlocked Scrapbook Medals
        </h3>

        {loading ? (
          <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>Loading achievements...</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12 }}>
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
                      fontSize: "1.5rem",
                      width: 40,
                      height: 40,
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
                        fontSize: "0.8125rem",
                        fontWeight: 600,
                        color: isUnlocked ? "var(--text-primary)" : "var(--text-muted)",
                      }}
                    >
                      {ach.title}
                    </h4>
                    <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: 2 }}>
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
