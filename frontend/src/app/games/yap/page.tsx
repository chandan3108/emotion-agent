"use client";

import { useState, useRef, useEffect } from "react";
import { startYap, chatYap } from "@/lib/gameApi";

export default function YapGamePage() {
  const [topicInput, setTopicInput] = useState("");
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [researching, setResearching] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputText, setInputText] = useState("");
  const [facts, setFacts] = useState<string[]>([]);
  const [showFacts, setShowFacts] = useState(true);
  const [turnCount, setTurnCount] = useState(0);
  const [showAchievementModal, setShowAchievementModal] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartSession = async () => {
    const topic = topicInput.trim();
    if (!topic) return;

    setLoading(true);
    setResearching(true);
    try {
      const res = await startYap(topic);
      setSession(res);
      setFacts(res.facts || []);
      setMessages([{ role: "assistant", content: res.greeting }]);
      setTurnCount(0);
    } catch (e) {
      console.error(e);
      alert("Failed to start research. Please verify network connection.");
    } finally {
      setLoading(false);
      setResearching(false);
    }
  };

  const handleSendMessage = async () => {
    const text = inputText.trim();
    if (!text || !session || loading) return;

    setInputText("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await chatYap(text);
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
      setTurnCount(res.turn_count);
      if (res.facts) {
        setFacts(res.facts);
      }
      if (res.achievement_unlocked) {
        setShowAchievementModal(true);
      }
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "my brain short-circuited trying to reply to that, try sending it again lol" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleResetSession = () => {
    setSession(null);
    setFacts([]);
    setMessages([]);
    setInputText("");
    setTopicInput("");
    setTurnCount(0);
    setShowAchievementModal(false);
  };

  if (researching) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "calc(100vh - 100px)", gap: 20 }}>
        <div className="spinner" style={{ width: 50, height: 50, borderRadius: "50%", border: "4px solid rgba(16, 185, 129, 0.1)", borderTopColor: "#10b981", animation: "spin 1s linear infinite" }} />
        <div style={{ textAlign: "center" }}>
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.25rem", color: "#10b981", fontWeight: 600 }}>
            Rem is researching topic...
          </h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", marginTop: 6 }}>
            fetching verified facts on &ldquo;{topicInput}&rdquo; to anchor the discussion.
          </p>
        </div>
        <style jsx global>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (!session) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: 600, margin: "0 auto" }} className="fade-in-up">
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>🗣️</div>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.75rem", fontWeight: 700, color: "#10b981" }}>
            Academic Yap Sandbox
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", lineHeight: 1.6, marginTop: 8 }}>
            Type in any topic you want to discuss. Rem will load grounded, verified facts from the web to debate and yap with you in-depth.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: 28, background: "rgba(8, 8, 15, 0.8)", border: "1px solid rgba(16, 185, 129, 0.15)" }}>
          <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 10 }}>
            Topic of Discussion
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 16 }}>
            Enter a theory, historical event, animal mystery, technology, or current debate (e.g. &ldquo;Quantum Mechanics&rdquo;, &ldquo;Why do cats purr&rdquo;, or &ldquo;Theory of Relativity&rdquo;).
          </p>
          <input
            type="text"
            placeholder="e.g. Theory of Relativity"
            value={topicInput}
            onChange={(e) => setTopicInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleStartSession(); }}
            style={{
              width: "100%", padding: "12px 18px", borderRadius: 8,
              background: "rgba(255,255,255,0.01)", border: "1px solid rgba(16, 185, 129, 0.2)",
              color: "var(--text-primary)", fontSize: "0.8125rem", marginBottom: 20,
              outline: "none"
            }}
          />

          <button
            onClick={handleStartSession}
            disabled={loading || !topicInput.trim()}
            style={{
              width: "100%", padding: "12px 0", borderRadius: 8, background: "#10b981",
              color: "#fff", border: "none", fontSize: "0.875rem", fontWeight: 600,
              cursor: "pointer", boxShadow: "0 0 20px rgba(16, 185, 129, 0.3)", transition: "all 0.2s"
            }}
          >
            Start Yapping
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", height: "calc(100vh - 60px)", overflow: "hidden" }} className="fade-in-up">
      {/* Chat Area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "20px 24px" }}>
        
        {/* HUD Header */}
        <div className="glass-panel" style={{ padding: "12px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderColor: "rgba(16, 185, 129, 0.15)", background: "rgba(10, 25, 20, 0.2)" }}>
          <div>
            <span style={{ fontSize: "0.5625rem", textTransform: "uppercase", color: "#10b981", fontWeight: 700, letterSpacing: "0.05em" }}>
              Grounded Discussion
            </span>
            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500, marginTop: 1 }}>
              🗣️ Topic: {topicInput} | Turns: {turnCount}/10
            </div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button
              onClick={() => setShowFacts(!showFacts)}
              style={{
                padding: "6px 12px", borderRadius: 6, background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", fontSize: "0.6875rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              {showFacts ? "Hide Verified Grounds" : "Show Grounds"}
            </button>
            <button
              onClick={handleResetSession}
              style={{
                padding: "6px 14px", borderRadius: 6, background: "rgba(16, 185, 129, 0.15)",
                border: "1px solid rgba(16, 185, 129, 0.3)", color: "#ffe4e6", fontSize: "0.6875rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              New Topic
            </button>
          </div>
        </div>

        {/* Scrollable messages container */}
        <div
          className="glass-panel"
          style={{
            flex: 1,
            padding: 24,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            borderColor: "rgba(16, 185, 129, 0.1)",
            background: "rgba(8, 8, 15, 0.7)"
          }}
        >
          {messages.map((m, i) => {
            const isUser = m.role === "user";
            return (
              <div
                key={i}
                style={{
                  alignSelf: isUser ? "flex-end" : "flex-start",
                  maxWidth: "75%",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: isUser ? "flex-end" : "flex-start",
                  gap: 4
                }}
              >
                <div
                  style={{
                    background: isUser ? "rgba(255,255,255,0.03)" : "rgba(16, 185, 129, 0.05)",
                    border: isUser ? "1px solid var(--border-subtle)" : "1px solid rgba(16, 185, 129, 0.15)",
                    padding: "12px 16px",
                    borderRadius: isUser ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                    color: isUser ? "var(--text-primary)" : "#e6fcf5",
                    fontSize: "0.8125rem",
                    lineHeight: 1.5,
                    whiteSpace: "pre-line"
                  }}
                >
                  {m.content}
                </div>
                <span style={{ fontSize: "0.5625rem", color: "var(--text-muted)" }}>
                  {isUser ? "You" : "Rem"}
                </span>
              </div>
            );
          })}
          {loading && (
            <div style={{ alignSelf: "flex-start", display: "flex", gap: 6, alignItems: "center", padding: "10px 16px", background: "rgba(16, 185, 129, 0.02)", border: "1px solid rgba(16, 185, 129, 0.08)", borderRadius: "12px 12px 12px 2px" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontStyle: "italic" }}>Rem is yapping...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
          <input
            type="text"
            placeholder="Yap back at her..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSendMessage(); }}
            style={{
              flex: 1, padding: "12px 18px", borderRadius: 8,
              background: "rgba(255,255,255,0.01)", border: "1px solid rgba(16, 185, 129, 0.2)",
              color: "var(--text-primary)", fontSize: "0.8125rem",
              outline: "none"
            }}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !inputText.trim()}
            style={{
              padding: "0 24px", borderRadius: 8, background: "#10b981",
              color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
              cursor: "pointer", transition: "all 0.2s"
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* Facts Side Drawer */}
      {showFacts && (
        <div
          className="glass-panel"
          style={{
            width: 320,
            borderLeft: "1px solid rgba(16, 185, 129, 0.15)",
            background: "rgba(8, 8, 15, 0.9)",
            padding: 24,
            display: "flex",
            flexDirection: "column",
            gap: 16,
            overflowY: "auto",
            animation: "slideIn 0.3s ease-out"
          }}
        >
          <div style={{ borderBottom: "1px solid rgba(16, 185, 129, 0.15)", paddingBottom: 12 }}>
            <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#10b981" }}>
              Verified Grounds
            </h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.6875rem", marginTop: 4, lineHeight: 1.4 }}>
              Factual snippets fetched from Tavily Search. Rem&apos;s responses are strictly constrained to these to guarantee zero hallucinations.
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {facts.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", fontStyle: "italic" }}>
                No facts loaded.
              </p>
            ) : (
              facts.map((fact, index) => (
                <div
                  key={index}
                  style={{
                    padding: 12,
                    background: "rgba(16, 185, 129, 0.03)",
                    border: "1px solid rgba(16, 185, 129, 0.1)",
                    borderRadius: 8,
                    fontSize: "0.75rem",
                    color: "var(--text-secondary)",
                    lineHeight: 1.4
                  }}
                >
                  {fact}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Achievement modal */}
      {showAchievementModal && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center",
          background: "rgba(0,0,0,0.8)", backdropFilter: "blur(6px)"
        }}>
          <div
            className="glass-panel"
            style={{
              width: "90%", maxWidth: 400, padding: 32, textAlign: "center",
              background: "linear-gradient(135deg, #051410 0%, #020806 100%)",
              border: "1px solid #10b981", boxShadow: "0 0 30px rgba(16, 185, 129, 0.4)",
              borderRadius: 16
            }}
          >
            <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>🎓</div>
            <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.5rem", fontWeight: 700, color: "#fff", marginBottom: 8 }}>
              Achievement Unlocked!
            </h2>
            <h4 style={{ color: "#10b981", fontSize: "0.875rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>
              Yap Scholar
            </h4>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 28, lineHeight: 1.5 }}>
              You survived a 10-turn grounded academic discussion with Rem on &ldquo;{topicInput}&rdquo; without triggered blocks or errors.
            </p>

            <button
              onClick={() => setShowAchievementModal(false)}
              style={{
                padding: "10px 28px", borderRadius: 8, background: "#10b981",
                color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              Continue Yapping
            </button>
          </div>
        </div>
      )}

      <style jsx global>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
