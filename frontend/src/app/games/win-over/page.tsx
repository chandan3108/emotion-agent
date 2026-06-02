"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { startWinOver, chatWinOver, type WinOverStartResponse, type WinOverChatResponse } from "@/lib/gameApi";

const SCENARIOS = [
  { id: "promise", label: "🤝 The Broken Promise", desc: "Forgot study plans to hang out with friends. High Hurt, Medium Anger.", diff: "Medium" },
  { id: "ghost", label: "🔥 The Silent Treatment", desc: "Ghosted her for 3 days and sent a lazy 'what's up'. High Anger, Low Trust.", diff: "Hard" },
  { id: "stranger", label: "❄️ The Cold Stranger", desc: "She starts completely detached and bored, thinking you are unoriginal. Apathy.", diff: "Expert" },
];

export default function WinOverPage() {
  const [selectedScen, setSelectedScen] = useState<string | null>(null);
  const [session, setSession] = useState<WinOverStartResponse | null>(null);
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [inputText, setInputText] = useState("");
  const [turnsLeft, setTurnsLeft] = useState(10);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [gameStatus, setGameStatus] = useState<"active" | "won" | "lost" | "blocked">("active");
  const [evalResult, setEvalResult] = useState<any>(null);

  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartGame = (scenId: string) => {
    setLoading(true);
    setSelectedScen(scenId);
    startWinOver(scenId)
      .then((res) => {
        setSession(res);
        setMessages([{ role: "assistant", content: res.greeting }]);
        setTurnsLeft(10);
        setStats(res.stats);
        setGameStatus("active");
        setEvalResult(null);
      })
      .catch(() => {
        alert("Failed to start the challenge. Please verify backend is running.");
      })
      .finally(() => setLoading(false));
  };

  const handleSendMessage = () => {
    const text = inputText.trim();
    if (!text || loading || gameStatus !== "active") return;

    setInputText("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    chatWinOver(text)
      .then((res: WinOverChatResponse) => {
        setTurnsLeft(res.turns_remaining);
        setStats(res.stats);
        setGameStatus(res.game_status);
        setEvalResult(res.evaluation);
        setMessages((prev) => [...prev, { role: "assistant", content: res.rem_response }]);
      })
      .catch(() => {
        alert("Error sending message.");
      })
      .finally(() => setLoading(false));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  // Helper to determine emoji expression status
  const getExpressionTag = (anger = 0, hurt = 0, trust = 0) => {
    if (gameStatus === "blocked") return { icon: "🚫", text: "Blocked", color: "#ef4444" };
    if (gameStatus === "won") return { icon: "💖", text: "Won Over", color: "#ec4899" };
    if (gameStatus === "lost") return { icon: "😞", text: "Cold / Rejected", color: "#6b7280" };

    if (anger > 0.7) return { icon: "😠", text: "Hostile", color: "#ef4444" };
    if (hurt > 0.6) return { icon: "🙄", text: "Stung & Deflective", color: "#3b82f6" };
    if (trust < 0.2) return { icon: "🤨", text: "Suspicious", color: "#eab308" };
    if (trust > 0.5) return { icon: "🙂", text: "Mildly Amused", color: "#10b981" };
    return { icon: "😐", text: "Guarded", color: "#a855f7" };
  };

  const expr = getExpressionTag(stats.anger, stats.hurt, stats.trust);

  if (!session) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: 650, margin: "0 auto" }}>
        <div style={{ marginBottom: 32 }}>
          <a href="/games" style={{ color: "var(--text-muted)", fontSize: "0.8125rem", textDecoration: "none" }}>
            ← Back to Games
          </a>
          <h1 className="section-title" style={{ fontSize: "1.625rem", fontWeight: 700, marginTop: 12 }}>
            💔 Win Her Over Challenge
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: 4 }}>
            Rem starts in a highly defensive mood. Rebuild trust in **10 turns or less**. Sincere empathy wins; lazy defensiveness or gaslighting will get you blocked.
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {SCENARIOS.map((scen) => (
            <button
              key={scen.id}
              onClick={() => handleStartGame(scen.id)}
              disabled={loading}
              className="glass-card"
              style={{
                width: "100%",
                padding: "20px 24px",
                textAlign: "left",
                cursor: "pointer",
                border: "1px solid var(--border-subtle)",
                background: "rgba(255, 255, 255, 0.01)",
                transition: "all 0.2s ease",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
            >
              <div style={{ flex: 1, marginRight: 16 }}>
                <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                  {scen.label}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
                  {scen.desc}
                </div>
              </div>
              <div
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: 700,
                  padding: "4px 10px",
                  background:
                    scen.diff === "Medium"
                      ? "rgba(16, 185, 129, 0.1)"
                      : scen.diff === "Hard"
                      ? "rgba(234, 179, 8, 0.1)"
                      : "rgba(239, 68, 68, 0.1)",
                  color: scen.diff === "Medium" ? "#10b981" : scen.diff === "Hard" ? "#eab308" : "#ef4444",
                  borderRadius: "var(--radius-full)",
                  border: `1px solid ${
                    scen.diff === "Medium" ? "#10b981" : scen.diff === "Hard" ? "#eab308" : "#ef4444"
                  }`,
                }}
              >
                {scen.diff}
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", position: "relative" }}>
      {/* Top Header Panel */}
      <div
        style={{
          padding: "16px 24px",
          borderBottom: "1px solid var(--border-subtle)",
          background: "rgba(8, 8, 15, 0.9)",
          backdropFilter: "blur(10px)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          zIndex: 5,
        }}
      >
        <div>
          <span style={{ fontSize: "0.625rem", color: "#22d3ee", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Win Her Over Challenge
          </span>
          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginTop: 2 }}>
            Scenario: {session.scenario_name}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {/* Reaction status badge */}
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              padding: "5px 12px",
              background: "rgba(255,255,255,0.02)",
              border: `1px solid ${expr.color}`,
              borderRadius: "var(--radius-md)",
              display: "flex",
              alignItems: "center",
              gap: 6,
              color: expr.color,
            }}
          >
            <span>{expr.icon}</span>
            <span>{expr.text}</span>
          </div>

          <div
            style={{
              fontSize: "0.8125rem",
              fontWeight: 700,
              color: turnsLeft <= 3 ? "#ef4444" : "var(--text-primary)",
              padding: "4px 10px",
              background: "rgba(255,255,255,0.05)",
              borderRadius: "var(--radius-md)",
            }}
          >
            🗝️ Turns Left: {turnsLeft}
          </div>
        </div>
      </div>

      {/* Dynamic Cylinders Status bar */}
      <div
        style={{
          padding: "16px 24px",
          background: "rgba(8, 8, 15, 0.6)",
          borderBottom: "1px solid var(--border-subtle)",
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 16,
        }}
      >
        {[
          { label: "Cortisol (Anger)", val: stats.anger, color: "#ef4444", key: "anger" },
          { label: "Dopamine (Humor)", val: stats.dopamine || 0.1, color: "#eab308", key: "dopamine" },
          { label: "Oxytocin (Trust)", val: stats.trust, color: "#10b981", key: "trust", target: ">= 0.65" },
          { label: "Hurt / Stung", val: stats.hurt, color: "#3b82f6", key: "hurt" },
        ].map((bar) => (
          <div key={bar.label} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.625rem", color: "var(--text-muted)" }}>
              <span>{bar.label}</span>
              <span style={{ color: bar.color, fontWeight: 700 }}>
                {Math.round(bar.val * 100)}% {bar.target && `(Target: ${bar.target})`}
              </span>
            </div>
            <div
              style={{
                height: 10,
                background: "rgba(255,255,255,0.03)",
                borderRadius: 5,
                border: "1px solid rgba(255,255,255,0.05)",
                overflow: "hidden",
                position: "relative",
              }}
            >
              <div
                style={{
                  width: `${bar.val * 100}%`,
                  height: "100%",
                  background: bar.color,
                  boxShadow: `0 0 10px ${bar.color}`,
                  transition: "width 0.8s cubic-bezier(0.16, 1, 0.3, 1)",
                  borderRadius: 5,
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Chat scroll box */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: 16 }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "70%",
              padding: "14px 18px",
              background: m.role === "user" ? "var(--bg-glass-heavy)" : "rgba(255, 255, 255, 0.02)",
              border: m.role === "user" ? "1px solid var(--accent-primary)" : "1px solid var(--border-subtle)",
              borderRadius: m.role === "user" ? "16px 16px 2px 16px" : "16px 16px 16px 2px",
              fontSize: "0.875rem",
              lineHeight: 1.5,
              color: m.role === "user" ? "var(--text-primary)" : "var(--text-secondary)",
            }}
          >
            {m.content}
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: "flex-start", padding: "14px 18px", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
            Rem is typing...
          </div>
        )}

        {/* Display live LLM evaluation feedback after response */}
        {!loading && evalResult && gameStatus === "active" && (
          <div
            style={{
              alignSelf: "center",
              fontSize: "0.6875rem",
              color: evalResult.tactic.includes("toxic") || evalResult.tactic.includes("lazy") ? "#ef4444" : "#10b981",
              background: "rgba(0,0,0,0.2)",
              padding: "6px 14px",
              borderRadius: "var(--radius-full)",
              border: "1px solid var(--border-subtle)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              fontWeight: 600,
            }}
          >
            🎭 Tactic: {evalResult.tactic.replace("_", " ")} | Sincerity: {Math.round(evalResult.sincerity_rating * 100)}%
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Game Over Verdict Overlays */}
      {gameStatus !== "active" && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(8, 8, 15, 0.95)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
            zIndex: 10,
          }}
        >
          <div
            className="glass-card"
            style={{
              maxWidth: 480,
              width: "100%",
              padding: 40,
              border:
                gameStatus === "won"
                  ? "1px solid rgba(16, 185, 129, 0.3)"
                  : gameStatus === "blocked"
                  ? "1px solid rgba(239, 68, 68, 0.5)"
                  : "1px solid rgba(107, 114, 128, 0.3)",
              background: "rgba(10, 10, 20, 0.95)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "3.5rem", marginBottom: 12 }}>
              {gameStatus === "won" ? "💖" : gameStatus === "blocked" ? "🚫" : "😞"}
            </div>

            <h2
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: gameStatus === "won" ? "#10b981" : gameStatus === "blocked" ? "#ef4444" : "var(--text-muted)",
                marginBottom: 8,
              }}
            >
              {gameStatus === "won"
                ? "Challenge Succeeded!"
                : gameStatus === "blocked"
                ? "Rem Blocked You!"
                : "Challenge Failed"}
            </h2>

            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 32 }}>
              {gameStatus === "won"
                ? "Congratulations! You successfully de-escalated her anger, validated her feelings, and rebuilt a secure connection. The study plan keepsake has been unlocked in your Scrapbook Achievements!"
                : gameStatus === "blocked"
                ? "You triggered her zero-tolerance threshold. Rem recognized manipulative gaslighting or verbal hostility and permanently ended the connection. Try a softer, more validating approach next time."
                : "You ran out of conversational turns. The friction remained too high and Rem decided to walk away to get some space. Better luck next time."}
            </p>

            <div style={{ display: "flex", gap: 12 }}>
              <a
                href="/games/win-over"
                onClick={(e) => {
                  e.preventDefault();
                  window.location.href = "/games/win-over";
                }}
                style={{
                  flex: 1,
                  background: "var(--bg-glass)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-primary)",
                  padding: "12px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  textDecoration: "none",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "0.875rem",
                }}
              >
                Scenarios
              </a>
              <a
                href="/games"
                onClick={(e) => {
                  e.preventDefault();
                  window.location.href = "/games";
                }}
                style={{
                  flex: 1,
                  background: gameStatus === "won" ? "var(--accent-primary)" : "var(--border-subtle)",
                  color: "#000",
                  padding: "12px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  textDecoration: "none",
                  fontWeight: 600,
                  fontSize: "0.875rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                Games Hub
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Text Message Input bar */}
      {gameStatus === "active" && (
        <div style={{ padding: 20, borderTop: "1px solid var(--border-subtle)", background: "rgba(8, 8, 15, 0.8)", display: "flex", gap: 12 }}>
          <input
            type="text"
            placeholder={loading ? "Waiting..." : "Send a message to Rem..."}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={loading}
            style={{
              flex: 1,
              background: "rgba(0,0,0,0.2)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "12px 18px",
              color: "#fff",
              fontSize: "0.875rem",
            }}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !inputText.trim()}
            style={{
              background: "var(--accent-primary)",
              color: "#000",
              border: "none",
              borderRadius: "var(--radius-md)",
              padding: "0 24px",
              fontWeight: 600,
              fontSize: "0.875rem",
              cursor: "pointer",
              opacity: loading || !inputText.trim() ? 0.5 : 1,
            }}
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
}
