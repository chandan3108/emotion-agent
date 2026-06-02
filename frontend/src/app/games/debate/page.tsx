"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { startDebate, chatDebate, type DebateStartResponse, type DebateChatResponse } from "@/lib/gameApi";

const TOPICS = [
  { id: "pineapple", label: "🍍 Pineapple Pizza", desc: "Is pineapple on pizza a crime against food?" },
  { id: "birds", label: "🐦 Birds Surveillance", desc: "Are birds real animals, or government spy drones?" },
  { id: "hotdog", label: "🌭 Hot Dog Sandwich", desc: "Is a hot dog technically a sandwich?" },
  { id: "water", label: "💧 Dry Water", desc: "Is water wet, or does it only make other things wet?" },
  { id: "cereal", label: "🥣 Cereal Soup", desc: "Is cereal structurally and legally classified as soup?" },
  { id: "socks", label: "🧦 Sleeping Socks", desc: "Is sleeping with socks on a sign of instability?" },
  { id: "soup_drink", label: "🍜 Soup Beverage", desc: "Is soup a beverage rather than food?" },
  { id: "straw", label: "🥤 Straw Holes", desc: "Does a drinking straw have one hole or two?" },
  { id: "shrek", label: "👹 Shrek Cinema", desc: "Is Shrek 2 the greatest film of the century?" },
];

export default function DebatePage() {
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [session, setSession] = useState<DebateStartResponse | null>(null);
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [inputText, setInputText] = useState("");
  const [turnCount, setTurnCount] = useState(0);
  const [sentiment, setSentiment] = useState(0.0); // -1.0 to 1.0
  const [loading, setLoading] = useState(false);
  const [finished, setFinished] = useState(false);
  const [verdict, setVerdict] = useState<any>(null);

  // Turn Timer
  const [timeLeft, setTimeLeft] = useState(60);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (session && !finished && !loading) {
      setTimeLeft(60);
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(timerRef.current!);
            handleSendMessage("..."); // brain freeze auto-send
            return 60;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [session, finished, turnCount, loading]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartDebate = (topicId: string) => {
    setLoading(true);
    setSelectedTopic(topicId);
    startDebate(topicId)
      .then((res) => {
        setSession(res);
        setMessages([{ role: "assistant", content: res.greeting }]);
        setTurnCount(0);
        setSentiment(0.0);
        setFinished(false);
        setVerdict(null);
      })
      .catch(() => {
        alert("Failed to initialize debate. Please check API connection.");
      })
      .finally(() => setLoading(false));
  };

  const handleSendMessage = (textToSend?: string) => {
    const text = textToSend !== undefined ? textToSend : inputText.trim();
    if (!text || loading) return;

    if (textToSend === undefined) {
      setInputText("");
    }

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    if (timerRef.current) clearInterval(timerRef.current);

    chatDebate(text)
      .then((res: DebateChatResponse) => {
        setTurnCount(res.turn_count);
        setSentiment(res.sentiment_score);
        setMessages((prev) => [...prev, { role: "assistant", content: res.rem_response }]);
        if (res.finished) {
          setFinished(true);
          setVerdict(res.verdict);
        }
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

  if (!session) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: 650, margin: "0 auto" }}>
        <div style={{ marginBottom: 32 }}>
          <a href="/games" style={{ color: "var(--text-muted)", fontSize: "0.8125rem", textDecoration: "none" }}>
            ← Back to Games
          </a>
          <h1 className="section-title" style={{ fontSize: "1.625rem", fontWeight: 700, marginTop: 12 }}>
            ⚖️ Debate Battle Arena
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: 4 }}>
            Rem challenges your logic. Choose a silly debate topic. **Stances are randomly assigned** to force hilarious arguments.
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {TOPICS.map((topic) => (
            <button
              key={topic.id}
              onClick={() => handleStartDebate(topic.id)}
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
                display: "block",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
            >
              <div style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                {topic.label}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
                {topic.desc}
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", position: "relative" }}>
      {/* Header Info Panel */}
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
          <span style={{ fontSize: "0.625rem", color: "var(--accent-primary)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Debate Battle
          </span>
          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginTop: 2 }}>
            Topic: {session.topic}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          {/* Turn step indicators */}
          <div style={{ display: "flex", gap: 6 }}>
            {[1, 2, 3, 4, 5].map((step) => (
              <div
                key={step}
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  fontSize: "0.6875rem",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: turnCount >= step ? "var(--accent-primary)" : "rgba(255,255,255,0.05)",
                  color: turnCount >= step ? "#000" : "var(--text-muted)",
                  border: turnCount === step - 1 && !finished ? "1px solid var(--accent-primary)" : "none",
                }}
              >
                {step}
              </div>
            ))}
          </div>

          {/* Turn timer */}
          {!finished && (
            <div
              style={{
                fontSize: "0.8125rem",
                fontWeight: 700,
                color: timeLeft <= 15 ? "#ef4444" : "var(--text-primary)",
                padding: "4px 10px",
                background: timeLeft <= 15 ? "rgba(239, 68, 68, 0.1)" : "rgba(255, 255, 255, 0.05)",
                borderRadius: "var(--radius-md)",
                border: timeLeft <= 15 ? "1px solid #ef4444" : "none",
              }}
            >
              ⏱️ {timeLeft}s
            </div>
          )}
        </div>
      </div>

      {/* Tug of war meter */}
      <div
        style={{
          padding: "10px 24px",
          background: "rgba(8, 8, 15, 0.5)",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.625rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          <span>👈 Rem's Side</span>
          <span>User's Side 👉</span>
        </div>
        <div style={{ height: 6, background: "rgba(255,255,255,0.05)", borderRadius: 3, position: "relative", overflow: "hidden" }}>
          <div
            style={{
              position: "absolute",
              left: "50%",
              width: `${Math.abs(sentiment) * 50}%`,
              transform: sentiment < 0 ? "translateX(-100%)" : "translateX(0)",
              height: "100%",
              background: sentiment < 0 ? "#ec4899" : "#10b981",
              transition: "all 0.5s ease",
            }}
          />
          <div style={{ position: "absolute", left: "50%", top: 0, width: 2, height: "100%", background: "#fff", opacity: 0.3 }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.6875rem" }}>
          <span style={{ color: "#ec4899" }}>{session.rem_side}</span>
          <span style={{ color: "#10b981" }}>{session.user_side}</span>
        </div>
      </div>

      {/* Chat scroll box */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
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
            Rem is typing a rebuttal...
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Interactive Verdict Overlay when finished */}
      {finished && verdict && (
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
              maxWidth: 550,
              width: "100%",
              padding: 36,
              border: verdict.winner === "user" ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(239, 68, 68, 0.3)",
              background: "rgba(10, 10, 20, 0.95)",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "3rem", marginBottom: 12 }}>
              {verdict.winner === "user" ? "🏆" : "💀"}
            </div>
            <h2
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: verdict.winner === "user" ? "#10b981" : "#ef4444",
                marginBottom: 8,
              }}
            >
              {verdict.winner === "user" ? "Debate Victory!" : "Debate Defeat"}
            </h2>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginBottom: 24 }}>
              The neutral LLM Judge has rendered a final decision.
            </p>

            {/* Scoreboard */}
            <div style={{ display: "flex", justifyContent: "center", gap: 32, marginBottom: 24 }}>
              <div>
                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase" }}>User Score</div>
                <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)" }}>{verdict.score_user}</div>
              </div>
              <div style={{ display: "flex", alignItems: "center", fontSize: "1.25rem", color: "var(--text-muted)" }}>vs</div>
              <div>
                <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Rem Score</div>
                <div style={{ fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)" }}>{verdict.score_rem}</div>
              </div>
            </div>

            {/* MVP Quote */}
            <div
              style={{
                padding: "16px 20px",
                background: "rgba(255, 255, 255, 0.02)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
                marginBottom: 20,
                textAlign: "left",
              }}
            >
              <div style={{ fontSize: "0.625rem", color: "var(--accent-primary)", fontWeight: 700, textTransform: "uppercase", marginBottom: 6 }}>
                MVP Quote of the Match:
              </div>
              <div style={{ fontSize: "0.8125rem", fontStyle: "italic", color: "var(--text-secondary)" }}>
                &ldquo;{verdict.mvp_quote}&rdquo;
              </div>
            </div>

            {/* Judge Reasoning */}
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 32 }}>
              {verdict.reasoning}
            </p>

            <div style={{ display: "flex", gap: 12 }}>
              <a
                href="/games/debate"
                onClick={(e) => {
                  e.preventDefault();
                  window.location.href = "/games/debate";
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
                Topics Lobby
              </a>
              <a
                href="/games"
                onClick={(e) => {
                  e.preventDefault();
                  window.location.href = "/games";
                }}
                style={{
                  flex: 1,
                  background: "var(--accent-primary)",
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

      {/* Input panel */}
      {!finished && (
        <div style={{ padding: 20, borderTop: "1px solid var(--border-subtle)", background: "rgba(8, 8, 15, 0.8)", display: "flex", gap: 12 }}>
          <input
            type="text"
            placeholder={loading ? "Waiting for Rem..." : `Type your point... (${session.user_side.split('(')[0].trim()})`}
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
            onClick={() => handleSendMessage()}
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
