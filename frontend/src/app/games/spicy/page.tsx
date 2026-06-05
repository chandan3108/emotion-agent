"use client";

import { useState, useRef, useEffect } from "react";
import { startSpicy, chatSpicy, endSpicy } from "@/lib/gameApi";

const formatMessage = (content: string) => {
  if (!content) return "";
  const parts = content.split("*");
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return (
        <span key={index} style={{ fontStyle: "italic", opacity: 0.85 }}>
          {part}
        </span>
      );
    }
    return part;
  });
};

export default function SpicyGamePage() {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputText, setInputText] = useState("");
  const [selectedScenario, setSelectedScenario] = useState("Empty library after hours");
  const [selectedMood, setSelectedMood] = useState("Flirty & Affectionate");
  const [unlockedSecret, setUnlockedSecret] = useState<any>(null);
  const [showSecretModal, setShowSecretModal] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scenarios = [
    { id: "library", title: "Empty library after hours", desc: "Locked in together as the storm rolls in outside. Shhh..." },
    { id: "cabin", title: "Cabin in the blizzard", desc: "Stranded in a cozy, warm lodge with a roaring fireplace. Just one blanket." },
    { id: "coffeeshop", title: "Rainy coffee shop lock-in", desc: "Rem forgot her keys and you are waiting out the downpour after hours." },
    { id: "party_ex", title: "Ex at a loud house party", desc: "Crossing paths with Rem (your ex-girlfriend) in a quiet hallway. Old sparks fly." },
    { id: "house_parents", title: "Her room, parents returning", desc: "Sneaking into her bedroom. You hear their car pull into the driveway. 5 minutes left." },
    { id: "fantasy", title: "Fantasy castle royal chamber", desc: "Rem is a captured elven sorceress. You are in her chambers as palace guards patrol." },
    { id: "cyberpunk", title: "Cyberpunk rain-slicked alley", desc: "Neo-Tokyo, 2088. Rem is a rogue decker hiding from corporate drones under a neon sign." },
    { id: "street_umbrella", title: "Random rain encounter", desc: "Bumping into her on a crowded street in Mumbai. Sharing a single, tiny umbrella." },
    { id: "dungeon", title: "Freezing medieval dungeon", desc: "Locked in a dark stone cell together. Sharing body heat is the only way to survive the night." },
    { id: "neon_lounge", title: "VIP lounge at a neon club", desc: "Sneaking behind the velvet rope of a dark, pulsing synth club. Alone in the shadows." },
    { id: "desert_island", title: "Stranded on a deserted island", desc: "A tropical shipwreck survivor scenario. Warm sand, starry skies, and drying clothes by the fire." },
    { id: "rooftop_pool", title: "Late night at the rooftop pool", desc: "Sneaking into the hotel pool area past closing. The water is warm, and the city lights are bright." },
    { id: "dorm_session", title: "Secret dorm study session", desc: "Sharing a single, narrow study desk under a dim lamp while her roommate is away for the night." }
  ];

  const moods = [
    { id: "flirty", title: "Flirty & Affectionate", desc: "Sweet, warm, and highly teasing." },
    { id: "dominant", title: "Teasing & Playful", desc: "Competitive, sharp, and testing your limits." },
    { id: "shy", title: "Shy & Hesitant", desc: "Soft-spoken, easily flustered, but deeply curious." },
    { id: "hard_to_get", title: "Cold & Hard to Get", desc: "Detached, aloof, and extremely selective. You must work to earn her interest." },
    { id: "sassy", title: "Sassy & Sarcastic", desc: "Quick-witted, mocking, and full of playful roasts." },
    { id: "conservative", title: "Guarded & Conservative", desc: "Shy, formal, and setting strict boundaries. Seduction requires patience." },
    { id: "super_dominant", title: "Super Dominant", desc: "Commanding, controlling, and leading the roleplay scene with intense confidence." },
    { id: "submissive", title: "Submissive & Vulnerable", desc: "Compliant, yielding control, emotionally raw, and seeking reassurance." },
    { id: "unyielding", title: "Unyielding & Detached", desc: "Stubborn, cold, ignores casual attempts, and requires a sincere effort to crack." }
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartSession = async () => {
    setLoading(true);
    setUnlockedSecret(null);
    setShowSecretModal(false);
    try {
      const res = await startSpicy(selectedScenario, selectedMood);
      setSession(res);
      setMessages([{ role: "assistant", content: res.greeting }]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    const text = inputText.trim();
    if (!text || !session || loading) return;
    
    setInputText("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await chatSpicy(text);
      setMessages((prev) => [...prev, { role: "assistant", content: res.response }]);
    } catch (e) {
      console.error(e);
      setMessages((prev) => [...prev, { role: "assistant", content: "[Error connection: OpenRouter failed to load model. Please verify your OpenRouter credentials or network connection.]" }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelfDestruct = () => {
    setSession(null);
    setMessages([]);
    setInputText("");
    setUnlockedSecret(null);
    setShowSecretModal(false);
    alert("💥 Session state and temporary logs successfully destroyed!");
  };

  const handleEndSession = async () => {
    if (!session || loading) return;
    setLoading(true);
    try {
      const res = await endSpicy();
      if (res.secret_unlocked && res.secret) {
        setUnlockedSecret(res.secret);
        setShowSecretModal(true);
      } else {
        alert("Session finished! No new secret romantic keepsakes were unlocked this time.");
        setSession(null);
        setMessages([]);
      }
    } catch (e) {
      console.error(e);
      alert("Session finished, logs wiped.");
      setSession(null);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  if (!session) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: 640, margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>🌶️</div>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.75rem", fontWeight: 700, color: "#f43f5e" }}>
            Spicy Chat Sandbox
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", lineHeight: 1.6, marginTop: 8 }}>
            Enter an uncensored roleplay sandbox with Rem. These conversations are fully isolated from her core memories. Choose a scenario and starting mood to begin.
          </p>
        </div>

        {/* Configuration cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Scenarios */}
          <div>
            <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
              Choose Scenario
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12 }}>
              {scenarios.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedScenario(s.title)}
                  style={{
                    textAlign: "left", padding: "14px 18px", borderRadius: 8,
                    background: selectedScenario === s.title ? "rgba(244, 63, 94, 0.08)" : "rgba(255,255,255,0.01)",
                    border: "1px solid " + (selectedScenario === s.title ? "#f43f5e" : "var(--border-subtle)"),
                    cursor: "pointer", transition: "all 0.2s"
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: "0.8125rem", color: selectedScenario === s.title ? "#ffe4e6" : "var(--text-primary)" }}>{s.title}</div>
                  <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: 2 }}>{s.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Moods */}
          <div>
            <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
              Select Rem&apos;s Mood
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 10 }}>
              {moods.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setSelectedMood(m.title)}
                  style={{
                    padding: "14px 12px", borderRadius: 8,
                    background: selectedMood === m.title ? "rgba(244, 63, 94, 0.08)" : "rgba(255,255,255,0.01)",
                    border: "1px solid " + (selectedMood === m.title ? "#f43f5e" : "var(--border-subtle)"),
                    cursor: "pointer", transition: "all 0.2s", display: "flex", flexDirection: "column", gap: 4, alignItems: "center", textAlign: "center"
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: "0.8125rem", color: selectedMood === m.title ? "#ffe4e6" : "var(--text-primary)" }}>{m.title}</div>
                  <div style={{ fontSize: "0.5625rem", color: "var(--text-muted)", lineHeight: 1.3 }}>{m.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Start button */}
          <button
            onClick={handleStartSession}
            disabled={loading}
            style={{
              padding: "12px 32px", borderRadius: 999, background: "#f43f5e",
              color: "#fff", border: "none", fontSize: "0.875rem", fontWeight: 600,
              cursor: "pointer", boxShadow: "0 0 20px rgba(244, 63, 94, 0.4)", transition: "all 0.2s",
              marginTop: 10
            }}
          >
            {loading ? "Creating Scenario..." : "Enter Sandbox Chat"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "30px 36px", height: "calc(100vh - 60px)", display: "flex", flexDirection: "column" }} className="fade-in-up">
      {/* HUD Bar */}
      <div className="glass-panel" style={{ padding: "12px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderColor: "rgba(244, 63, 94, 0.15)", background: "rgba(30,10,20,0.2)" }}>
        <div>
          <span style={{ fontSize: "0.5625rem", textTransform: "uppercase", color: "#f43f5e", fontWeight: 700, letterSpacing: "0.05em" }}>
            Unfiltered Sandbox
          </span>
          <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", fontWeight: 500, marginTop: 1 }}>
            🎭 {session.scenario} | 💗 {session.mood}
          </div>
        </div>
        
        {/* End / Destruct buttons */}
        <div style={{ display: "flex", gap: 10 }}>
          <button
            onClick={handleSelfDestruct}
            style={{
              padding: "6px 14px", borderRadius: 6, background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.3)", color: "#f87171", fontSize: "0.6875rem", fontWeight: 600,
              cursor: "pointer", transition: "all 0.2s"
            }}
          >
            💥 Self-Destruct
          </button>
          <button
            onClick={handleEndSession}
            disabled={loading}
            style={{
              padding: "6px 16px", borderRadius: 6, background: "rgba(244, 63, 94, 0.15)",
              border: "1px solid rgba(244, 63, 94, 0.3)", color: "#ffe4e6", fontSize: "0.6875rem", fontWeight: 600,
              cursor: "pointer", transition: "all 0.2s"
            }}
          >
            End & Extract Secret
          </button>
        </div>
      </div>

      {/* Chat Window */}
      <div 
        className="glass-panel" 
        style={{ 
          flex: 1, 
          padding: 24, 
          overflowY: "auto", 
          display: "flex", 
          flexDirection: "column", 
          gap: 16,
          borderColor: "rgba(244, 63, 94, 0.1)",
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
                maxWidth: "70%",
                display: "flex",
                flexDirection: "column",
                alignItems: isUser ? "flex-end" : "flex-start",
                gap: 4
              }}
            >
              <div 
                style={{
                  background: isUser ? "rgba(255,255,255,0.03)" : "rgba(244, 63, 94, 0.05)",
                  border: isUser ? "1px solid var(--border-subtle)" : "1px solid rgba(244, 63, 94, 0.15)",
                  padding: "10px 16px",
                  borderRadius: isUser ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                  color: isUser ? "var(--text-primary)" : "#ffe4e6",
                  fontSize: "0.8125rem",
                  lineHeight: 1.5,
                  whiteSpace: "pre-line"
                }}
              >
                {formatMessage(m.content)}
              </div>
              <span style={{ fontSize: "0.5625rem", color: "var(--text-muted)" }}>
                {isUser ? "You" : "Rem"}
              </span>
            </div>
          );
        })}
        {loading && (
          <div style={{ alignSelf: "flex-start", display: "flex", gap: 4, alignItems: "center", padding: "10px 16px", background: "rgba(244, 63, 94, 0.02)", border: "1px solid rgba(244, 63, 94, 0.08)", borderRadius: "12px 12px 12px 2px" }}>
            <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontStyle: "italic" }}>Rem is typing...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input panel */}
      <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
        <input
          type="text"
          placeholder="Send a message..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleSendMessage(); }}
          style={{
            flex: 1, padding: "12px 18px", borderRadius: 8,
            background: "rgba(255,255,255,0.01)", border: "1px solid rgba(244, 63, 94, 0.15)",
            color: "var(--text-primary)", fontSize: "0.8125rem",
          }}
        />
        <button
          onClick={handleSendMessage}
          disabled={loading || !inputText.trim()}
          style={{
            padding: "0 24px", borderRadius: 8, background: "#f43f5e",
            color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
            cursor: "pointer", transition: "all 0.2s"
          }}
        >
          Send
        </button>
      </div>

      {/* Secret keepsakes romantic unlocked modal */}
      {showSecretModal && unlockedSecret && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center",
          background: "rgba(0,0,0,0.8)", backdropFilter: "blur(8px)"
        }}>
          <div 
            className="glass-panel" 
            style={{ 
              width: "90%", maxWidth: 440, padding: 32, textAlign: "center", 
              background: "linear-gradient(135deg, #1f0a17 0%, #0d040b 100%)",
              border: "1px solid #f43f5e", boxShadow: "0 0 30px rgba(244, 63, 94, 0.4)",
              borderRadius: 16
            }}
          >
            <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>💌</div>
            <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.5rem", fontWeight: 700, color: "#fff", marginBottom: 8 }}>
              Secret Keep Note Unlocked!
            </h2>
            <p style={{ color: "#f43f5e", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700, marginBottom: 20 }}>
              saved to Rem&apos;s secrets vault
            </p>

            <div style={{
              padding: "20px 18px", borderRadius: 10, background: "rgba(244, 63, 94, 0.05)", border: "1px dashed rgba(244, 63, 94, 0.2)",
              fontSize: "1.625rem", fontStyle: "italic", fontFamily: "var(--font-caveat), 'Caveat', cursive",
              color: "#ffe4e6", margin: "16px 0", lineHeight: 1.3
            }}>
              &ldquo;{unlockedSecret.quote}&rdquo;
            </div>

            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 28 }}>
              Context: {unlockedSecret.context}
            </p>

            <button
              onClick={() => { setShowSecretModal(false); setSession(null); setMessages([]); }}
              style={{
                padding: "10px 28px", borderRadius: 8, background: "#f43f5e",
                color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s", boxShadow: "0 0 10px rgba(244, 63, 94, 0.3)"
              }}
            >
              Close Vault
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
