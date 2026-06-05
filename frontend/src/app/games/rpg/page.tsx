"use client";

import { useState, useEffect, useRef } from "react";
import {
  getRpgScenarios,
  startRpgGame,
  turnRpgGame,
  accuseRpgGame,
  RpgScenario,
  RpgStartResponse,
  RpgTurnResponse,
  RpgAccuseResponse
} from "@/lib/gameApi";

export default function RpgGamePage() {
  const [scenarios, setScenarios] = useState<RpgScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<RpgScenario | null>(null);
  const [session, setSession] = useState<RpgStartResponse | null>(null);
  const [loadingScenarios, setLoadingScenarios] = useState(true);
  const [loadingTurn, setLoadingTurn] = useState(false);
  const [initializingGame, setInitializingGame] = useState(false);
  
  // Game session logs
  const [messages, setMessages] = useState<Array<{ role: "narrator" | "rem" | "user"; content: string }>>([]);
  const [inputText, setInputText] = useState("");
  
  // Dynamic board states
  const [currentLocation, setCurrentLocation] = useState("");
  const [turnCount, setTurnCount] = useState(0);
  const [maxTurns, setMaxTurns] = useState(16);
  const [finished, setFinished] = useState(false);
  const [suggestedChoices, setSuggestedChoices] = useState<string[]>([]);
  const [suspectStates, setSuspectStates] = useState<Record<string, { suspicion: number; interrogated: boolean; defensiveness: number; alibi?: string; last_statement?: string; current_location?: string }>>({});
  const [inventory, setInventory] = useState<string[]>([]);
  const [cluesFound, setCluesFound] = useState<string[]>([]);
  const [health, setHealth] = useState<number | null>(null);
  const [damageFlashed, setDamageFlashed] = useState(false);

  // Hard Mode features states
  const [difficulty, setDifficulty] = useState("normal");
  const [remConsultationsLeft, setRemConsultationsLeft] = useState(2);
  const [discoveredContradictions, setDiscoveredContradictions] = useState<string[]>([]);
  const [activeEffects, setActiveEffects] = useState<string[]>([]);
  const [activeRightTab, setActiveRightTab] = useState<"suspects" | "dossier">("suspects");
  const [showCorkboard, setShowCorkboard] = useState(false);

  // Accusation flow states
  const [showAccuseModal, setShowAccuseModal] = useState(false);
  const [accusedSuspect, setAccusedSuspect] = useState("");
  const [accusedWeapon, setAccusedWeapon] = useState("");
  const [accusedMotive, setAccusedMotive] = useState("");
  const [submittingAccusation, setSubmittingAccusation] = useState(false);
  const [accusationResult, setAccusationResult] = useState<RpgAccuseResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch scenarios on mount
  useEffect(() => {
    getRpgScenarios()
      .then((data) => {
        setScenarios(data);
      })
      .catch((err) => {
        console.error("Failed to load scenarios:", err);
      })
      .finally(() => {
        setLoadingScenarios(false);
      });
  }, []);

  // Smooth scroll messages to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleStartGame = async (scenario: RpgScenario) => {
    setSelectedScenario(scenario);
    setInitializingGame(true);
    setMessages([]);
    setAccusationResult(null);
    setFinished(false);
    setActiveRightTab("suspects");
    setDiscoveredContradictions([]);
    setActiveEffects([]);
    
    try {
      const res = await startRpgGame(scenario.quest_id);
      setSession(res);
      setCurrentLocation(res.current_location);
      setTurnCount(0);
      setMaxTurns(res.max_turns);
      setSuggestedChoices(res.suggested_choices);
      setInventory([]);
      setCluesFound([]);
      setDifficulty(res.difficulty || "normal");
      setRemConsultationsLeft(res.rem_consultations_left !== undefined ? res.rem_consultations_left : 2);
      setHealth(res.health !== undefined ? res.health : null);
      setDamageFlashed(false);
      
      // Initialize suspects states
      const initialSuspects: typeof suspectStates = {};
      scenario.suspects.forEach((s) => {
        initialSuspects[s.name] = {
          suspicion: s.starting_suspicion,
          interrogated: false,
          defensiveness: 0.20,
          alibi: s.alibi || "",
          last_statement: "",
          current_location: scenario.quest_id === "hotel_eutopia" ? "Unknown" : ""
        };
      });
      setSuspectStates(initialSuspects);

      setMessages([
        { role: "narrator", content: res.narrator_text },
        { role: "rem", content: res.rem_dialogue }
      ]);
    } catch (e) {
      console.error(e);
      alert("Failed to initialize case. Please check connection.");
      setSelectedScenario(null);
    } finally {
      setInitializingGame(false);
    }
  };

  const handleAction = async (actionText: string) => {
    if (!session || finished || loadingTurn || !actionText.trim()) return;

    setInputText("");
    setLoadingTurn(true);
    
    // Add user action to messages log if not a consult
    const isConsult = actionText.toLowerCase().includes("consult") || actionText.toLowerCase().includes("ask rem");
    if (!isConsult) {
      setMessages((prev) => [...prev, { role: "user", content: actionText }]);
    }

    try {
      const res = await turnRpgGame(actionText);
      
      setCurrentLocation(res.current_location);
      setTurnCount(res.turn_count);
      setFinished(res.finished);
      setSuggestedChoices(res.suggested_choices);
      setInventory(res.inventory || []);
      setCluesFound(res.clues_found || []);
      setSuspectStates(res.suspect_states || {});
      setRemConsultationsLeft(res.rem_consultations_left !== undefined ? res.rem_consultations_left : 2);
      setDiscoveredContradictions(res.discovered_contradictions || []);
      setActiveEffects(res.active_effects || []);
      
      // Track damage taken
      if (res.health !== undefined && health !== null && res.health < health) {
        setDamageFlashed(true);
        setTimeout(() => setDamageFlashed(false), 800);
      }
      setHealth(res.health !== undefined ? res.health : null);

      setMessages((prev) => [
        ...prev,
        { role: "narrator", content: res.narrator_text },
        { role: "rem", content: res.rem_dialogue }
      ]);
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { role: "rem", content: "sorry, my brain lagged for a second. try doing that action again." }
      ]);
    } finally {
      setLoadingTurn(false);
    }
  };

  const handleConsultRem = () => {
    if (remConsultationsLeft <= 0 || loadingTurn) return;
    handleAction("Ask Rem for help");
  };

  const handleSubmitAccusation = async () => {
    if (!accusedSuspect || !accusedWeapon || !accusedMotive.trim()) {
      alert("Fill in all accusation details before closing the case.");
      return;
    }

    setSubmittingAccusation(true);
    try {
      const res = await accuseRpgGame(accusedSuspect, accusedWeapon, accusedMotive);
      setAccusationResult(res);
      setFinished(true);
      setShowAccuseModal(false);
      
      setMessages((prev) => [
        ...prev,
        { role: "narrator", content: res.narrator_text },
        { role: "rem", content: res.rem_dialogue }
      ]);
    } catch (e) {
      console.error(e);
      alert("Accusation submission failed. Try again.");
    } finally {
      setSubmittingAccusation(false);
    }
  };

  const handleExitGame = () => {
    setSelectedScenario(null);
    setSession(null);
    setMessages([]);
    setAccusationResult(null);
    setFinished(false);
    setAccusedSuspect("");
    setAccusedWeapon("");
    setAccusedMotive("");
    setDiscoveredContradictions([]);
    setActiveEffects([]);
    setHealth(null);
    setDamageFlashed(false);
  };

  const isNoir = selectedScenario?.quest_id === "jazz_club_betrayal" || difficulty === "hard" || selectedScenario?.quest_id === "hotel_eutopia" || difficulty === "extreme";
  const isExtreme = selectedScenario?.quest_id === "hotel_eutopia" || difficulty === "extreme";

  // Render scenario selection if no active session
  if (!selectedScenario || !session) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: 1000, margin: "0 auto" }} className="fade-in-up">
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>🕵️‍♂️</div>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "2rem", fontWeight: 700, color: "#38bdf8" }}>
            Sherlock Rem: Procedural Cases
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", lineHeight: 1.6, marginTop: 8, maxWidth: 650, margin: "8px auto 0" }}>
            Partner up with Rem to solve atmospheric mystery quests. Suspects, alibis, murder weapons, and clues are randomly generated on start, offering infinite replayability.
          </p>
        </div>

        {loadingScenarios || initializingGame ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 250, gap: 20 }}>
            <div className="spinner" style={{ width: 50, height: 50, borderRadius: "50%", border: "4px solid rgba(56, 189, 248, 0.1)", borderTopColor: "#38bdf8", animation: "spin 1s linear infinite" }} />
            <div style={{ color: "#38bdf8", fontWeight: 600, fontSize: "0.9rem" }}>
              {initializingGame ? "Randomizing culprit & hiding clues..." : "Preparing case files..."}
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 24 }}>
            {scenarios.map((sc) => {
              const isHard = sc.difficulty === "hard" || sc.difficulty === "extreme";
              const isExtremeCard = sc.difficulty === "extreme";
              return (
                <div
                  key={sc.quest_id}
                  className="glass-panel"
                  style={{
                    background: isExtremeCard ? "rgba(20, 8, 28, 0.85)" : isHard ? "rgba(18, 10, 10, 0.8)" : "rgba(10, 15, 30, 0.8)",
                    border: isExtremeCard ? "1px solid rgba(168, 85, 247, 0.3)" : isHard ? "1px solid rgba(239, 68, 68, 0.25)" : "1px solid rgba(56, 189, 248, 0.15)",
                    borderRadius: 12,
                    padding: 28,
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    boxShadow: isExtremeCard ? "0 10px 30px rgba(168, 85, 247, 0.1)" : isHard ? "0 10px 30px rgba(239, 68, 68, 0.05)" : "0 10px 30px rgba(0, 0, 0, 0.3)",
                    transition: "transform 0.2s, border-color 0.2s",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                      <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.3rem", fontWeight: 600, color: isExtremeCard ? "#a855f7" : isHard ? "#ef4444" : "#38bdf8" }}>
                        {sc.title}
                      </h3>
                      <span style={{
                        fontSize: "0.625rem",
                        padding: "3px 8px",
                        borderRadius: 4,
                        fontWeight: 700,
                        textTransform: "uppercase",
                        background: isExtremeCard ? "rgba(168, 85, 247, 0.15)" : isHard ? "rgba(239, 68, 68, 0.15)" : "rgba(56, 189, 248, 0.15)",
                        color: isExtremeCard ? "#c084fc" : isHard ? "#f87171" : "#38bdf8",
                        border: isExtremeCard ? "1px solid rgba(168, 85, 247, 0.3)" : isHard ? "1px solid rgba(239, 68, 68, 0.3)" : "1px solid rgba(56, 189, 248, 0.3)"
                      }}>
                        {isExtremeCard ? "☠ Extreme" : isHard ? "Chamber Noir (Hard)" : "Casual"}
                      </span>
                    </div>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.825rem", lineHeight: 1.6, marginBottom: 20 }}>
                      {sc.description}
                    </p>
                    
                    <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
                      <div style={{ fontSize: "0.75rem" }}>
                        <strong style={{ color: isExtremeCard ? "#c084fc" : isHard ? "#f87171" : "#38bdf8" }}>Suspects: </strong>
                        <span style={{ color: "var(--text-secondary)" }}>
                          {sc.suspects.map(s => s.name).join(", ")}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.75rem" }}>
                        <strong style={{ color: isExtremeCard ? "#c084fc" : isHard ? "#f87171" : "#38bdf8" }}>Rooms to Explore: </strong>
                        <span style={{ color: "var(--text-secondary)" }}>
                          {sc.locations.map(l => l.name).join(", ")}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.75rem" }}>
                        <strong style={{ color: isExtremeCard ? "#c084fc" : isHard ? "#f87171" : "#38bdf8" }}>Turn Limit: </strong>
                        <span style={{ color: "var(--text-secondary)" }}>{sc.max_turns} actions</span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleStartGame(sc)}
                    style={{
                      width: "100%",
                      padding: "12px 0",
                      borderRadius: 8,
                      background: isExtremeCard ? "#a855f7" : isHard ? "#ef4444" : "#38bdf8",
                      color: isExtremeCard ? "#fff" : isHard ? "#fff" : "#0a0f1d",
                      border: "none",
                      fontSize: "0.875rem",
                      fontWeight: 700,
                      cursor: "pointer",
                      boxShadow: isExtremeCard ? "0 0 20px rgba(168, 85, 247, 0.3)" : isHard ? "0 0 20px rgba(239, 68, 68, 0.3)" : "0 0 20px rgba(56, 189, 248, 0.3)",
                      transition: "all 0.2s"
                    }}
                  >
                    Start Investigation
                  </button>
                </div>
              );
            })}
          </div>
        )}
        <style jsx global>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Active Quest Splitscreen Layout
  // Check active environmental effect styles
  const isBlackout = activeEffects.includes("blackout");
  const isLockdown = activeEffects.includes("lockdown");
  const isStorm = activeEffects.includes("storm");

  // Dynamic board styles for visual noir effects
  const terminalOverlayStyle: React.CSSProperties = isBlackout
    ? { boxShadow: "inset 0 0 120px rgba(0,0,0,0.95)", filter: "brightness(0.7) contrast(1.2)" }
    : isLockdown
      ? { boxShadow: "inset 0 0 80px rgba(239, 68, 68, 0.15)", filter: "contrast(1.05)" }
      : isStorm
        ? { boxShadow: "inset 0 0 80px rgba(56, 189, 248, 0.1)", filter: "contrast(1.02)" }
        : {};

  const themePrimary = isNoir ? "#06b6d4" : "#38bdf8";
  const themeBorder = isNoir ? "rgba(6, 182, 212, 0.2)" : "rgba(56, 189, 248, 0.2)";
  const themeBg = isNoir ? "rgba(8, 16, 24, 0.4)" : "rgba(14, 22, 45, 0.4)";

  return (
    <div style={{ display: "flex", height: "calc(100vh - 60px)", overflow: "hidden", background: isNoir ? "#030712" : "#060913", position: "relative" }} className="fade-in-up">
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes damage-flash {
          0% { opacity: 0.8; }
          100% { opacity: 0; }
        }
        @keyframes shake {
          0% { transform: translate(1px, 1px) rotate(0deg); }
          10% { transform: translate(-1px, -2px) rotate(-1deg); }
          20% { transform: translate(-3px, 0px) rotate(1deg); }
          30% { transform: translate(0px, 2px) rotate(0deg); }
          40% { transform: translate(1px, -1px) rotate(1deg); }
          50% { transform: translate(-1px, 2px) rotate(-1deg); }
          60% { transform: translate(-3px, 1px) rotate(0deg); }
          70% { transform: translate(2px, 1px) rotate(-1deg); }
          80% { transform: translate(-1px, -1px) rotate(1deg); }
          90% { transform: translate(2px, 2px) rotate(0deg); }
          100% { transform: translate(1px, -2px) rotate(-1deg); }
        }
        .corkboard {
          background-color: #5c4033;
          background-image: 
            radial-gradient(rgba(255,255,255,.15) 15%, transparent 20%),
            radial-gradient(rgba(0,0,0,.3) 15%, transparent 20%),
            linear-gradient(45deg, transparent 45%, rgba(0,0,0,.1) 48%, rgba(0,0,0,.1) 52%, transparent 55%),
            linear-gradient(-45deg, transparent 45%, rgba(0,0,0,.1) 48%, rgba(0,0,0,.1) 52%, transparent 55%);
          background-size: 60px 60px;
          box-shadow: inset 0 0 40px rgba(0,0,0,0.8);
          border: 12px solid #3e2723;
          border-radius: 8px;
          padding: 20px;
          min-height: 500px;
        }
        .evidence-card {
          background: #efebe9;
          border-left: 5px solid #d84315;
          padding: 10px;
          margin-bottom: 8px;
          border-radius: 4px;
          box-shadow: 2px 2px 5px rgba(0,0,0,0.15);
          position: relative;
          transform: rotate(-0.5deg);
          transition: all 0.2s;
        }
        .evidence-card:hover {
          transform: scale(1.02) rotate(0.5deg);
          box-shadow: 3px 3px 8px rgba(0,0,0,0.25);
        }
      `}} />

      {health !== null && health <= 0 && (
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0,0,0,0.85)",
          backdropFilter: "blur(6px)",
          zIndex: 99999,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 20
        }}>
          <span style={{ fontSize: "3rem" }}>💀</span>
          <h2 style={{ color: "#ef4444", fontSize: "1.75rem", fontWeight: 700, fontFamily: "'Space Grotesk', sans-serif" }}>
            CRITICAL INJURY
          </h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", maxWidth: 450, textAlign: "center", lineHeight: 1.5 }}>
            The physical hazards of Hotel Eutopia were too severe. You collapsed into the snow, and Rem couldn&apos;t pull you out in time.
          </p>
          <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
            <button
              onClick={() => handleStartGame(selectedScenario)}
              style={{
                padding: "10px 24px", borderRadius: 8, background: "#ef4444",
                color: "#fff", border: "none", fontSize: "0.875rem", fontWeight: 700,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              Restart Case
            </button>
            <button
              onClick={handleExitGame}
              style={{
                padding: "10px 24px", borderRadius: 8, background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", fontSize: "0.875rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              Return to Hub
            </button>
          </div>
        </div>
      )}

      {damageFlashed && (
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(239, 68, 68, 0.25)",
          boxShadow: "inset 0 0 100px rgba(220, 38, 38, 0.7)",
          pointerEvents: "none",
          zIndex: 9999,
          animation: "shake 0.3s ease-in-out infinite",
          transition: "opacity 0.2s"
        }} />
      )}
      
      {/* LEFT PANEL: Narrative Terminal Log & Input (60%) */}
      <div style={{ flex: 6, display: "flex", flexDirection: "column", borderRight: `1px solid ${themeBorder}`, padding: "20px 24px" }}>
        
        {/* HUD Header */}
        <div className="glass-panel" style={{ padding: "10px 18px", marginBottom: 16, borderColor: themeBorder, background: themeBg }}>
          {/* Row 1: Title + Turn Counter + Abandon */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
                🕵️‍♂️ {selectedScenario.title}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
                Turn <strong style={{ color: themePrimary }}>{turnCount}</strong>/{maxTurns}
              </span>
              <button
                onClick={handleExitGame}
                style={{
                  padding: "4px 10px", borderRadius: 5, background: "rgba(239, 68, 68, 0.08)",
                  border: "1px solid rgba(239, 68, 68, 0.25)", color: "#f87171", fontSize: "0.625rem", fontWeight: 600,
                  cursor: "pointer", transition: "all 0.2s"
                }}
              >
                ✕ Quit
              </button>
            </div>
          </div>

          {/* Row 2: Location + Events + Health (compact) */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 8, flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.65rem", background: isNoir ? "rgba(6, 182, 212, 0.12)" : "rgba(56, 189, 248, 0.12)", color: themePrimary, padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
              📍 {currentLocation}
            </span>

            {isBlackout && (
              <span className="pulse-alert" style={{ fontSize: "0.6rem", background: "rgba(234, 179, 8, 0.12)", border: "1px solid rgba(234,179,8,0.3)", color: "#facc15", padding: "2px 6px", borderRadius: 4, fontWeight: 700 }}>
                ⚡ OUTAGE
              </span>
            )}
            {isLockdown && (
              <span className="pulse-alert" style={{ fontSize: "0.6rem", background: "rgba(239, 68, 68, 0.12)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", padding: "2px 6px", borderRadius: 4, fontWeight: 700 }}>
                🚨 LOCKDOWN
              </span>
            )}
            {isStorm && (
              <span className="pulse-alert" style={{ fontSize: "0.6rem", background: "rgba(56, 189, 248, 0.12)", border: "1px solid rgba(56,189,248,0.3)", color: "#7dd3fc", padding: "2px 6px", borderRadius: 4, fontWeight: 700 }}>
                🌧️ STORM
              </span>
            )}

            {health !== null && (
              <>
                <div style={{ width: 1, height: 14, background: "rgba(255,255,255,0.08)" }} />
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: "0.65rem", color: health < 40 ? "#ef4444" : "#10b981" }}>❤️ {health}%</span>
                  <div style={{ width: 60, height: 4, background: "rgba(255,255,255,0.05)", borderRadius: 2, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${health}%`, background: health < 40 ? "#ef4444" : "#10b981", borderRadius: 2, transition: "width 0.4s ease" }} />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Narrator/Rem Chat Logs */}
        <div
          className="glass-panel"
          style={{
            flex: 1,
            padding: 24,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: 20,
            borderColor: isNoir ? "rgba(6, 182, 212, 0.08)" : "rgba(56, 189, 248, 0.08)",
            background: isNoir ? "rgba(3, 7, 18, 0.9)" : "rgba(6, 9, 19, 0.9)",
            borderRadius: 8,
            transition: "all 0.4s ease",
            ...terminalOverlayStyle
          }}
        >
          {messages.map((m, i) => {
            if (m.role === "narrator") {
              return (
                <div key={i} style={{ padding: "8px 12px", background: "rgba(255, 255, 255, 0.01)", borderLeft: `2px solid ${isNoir ? "#4b5563" : "#64748b"}`, borderRadius: "0 8px 8px 0" }}>
                  <p style={{ fontFamily: "Georgia, serif", fontSize: "0.85rem", fontStyle: "italic", color: isNoir ? "#9ca3af" : "#94a3b8", lineHeight: 1.6, whiteSpace: "pre-line" }}>
                    {m.content}
                  </p>
                </div>
              );
            }
            if (m.role === "user") {
              return (
                <div key={i} style={{ alignSelf: "flex-end", maxWidth: "75%", display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
                  <div style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid var(--border-subtle)", padding: "10px 14px", borderRadius: "12px 12px 2px 12px", color: "#f1f5f9", fontSize: "0.8125rem" }}>
                    {m.content}
                  </div>
                  <span style={{ fontSize: "0.5625rem", color: "var(--text-muted)", marginTop: 2 }}>You</span>
                </div>
              );
            }
            // Rem dialogue
            return (
              <div key={i} style={{ alignSelf: "flex-start", maxWidth: "75%", display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                <div style={{
                  background: isNoir ? "rgba(6, 182, 212, 0.04)" : "rgba(56, 189, 248, 0.04)",
                  border: isNoir ? "1px solid rgba(6, 182, 212, 0.15)" : "1px solid rgba(56, 189, 248, 0.15)",
                  padding: "10px 14px", borderRadius: "12px 12px 12px 2px", color: isNoir ? "#e0f7fa" : "#e0f2fe",
                  fontSize: "0.8125rem", lineHeight: 1.5
                }}>
                  {m.content}
                </div>
                <span style={{ fontSize: "0.5625rem", color: themePrimary, marginTop: 2 }}>rem</span>
              </div>
            );
          })}
          
          {loadingTurn && (
            <div style={{ alignSelf: "flex-start", display: "flex", gap: 6, alignItems: "center", padding: "10px 16px", background: `${themePrimary}02`, border: `1px solid ${themePrimary}08`, borderRadius: "12px 12px 12px 2px" }}>
              <div className="spinner" style={{ width: 12, height: 12, borderRadius: "50%", border: `2px solid ${themePrimary}10`, borderTopColor: themePrimary, animation: "spin 1s linear infinite" }} />
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontStyle: "italic" }}>Rem is examining...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Action Panel: Room Navigation shortcuts & Decision buttons */}
        <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
          
          {/* Quick Location Travel Shortcuts */}
          {!finished && (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {selectedScenario.quest_id === "hotel_eutopia" ? (
                <>
                  <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 600, marginBottom: 2 }}>Grouped Hotel Navigation:</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {[
                      { name: "🏰 Level 1 & 2", ids: ["lobby", "ballroom", "kitchen", "library"] },
                      { name: "🚪 Upper Suites", ids: ["suite404", "observatory"] },
                      { name: "⚙️ Basement", ids: ["cellar", "boiler", "laundry", "quarters", "elevator"] },
                      { name: "❄️ Outside", ids: ["garden"] }
                    ].map((group) => {
                      const groupLocations = selectedScenario.locations.filter(l => group.ids.includes(l.id));
                      return (
                        <div key={group.name} style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", background: "rgba(255,255,255,0.01)", padding: "4px 8px", borderRadius: 6, border: "1px solid rgba(255,255,255,0.03)" }}>
                          <span style={{ fontSize: "0.625rem", color: themePrimary, fontWeight: 700, minWidth: 90 }}>{group.name}</span>
                          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                            {groupLocations.map((loc) => {
                              const isActive = loc.name === currentLocation;
                              return (
                                <button
                                  key={loc.id}
                                  disabled={isActive || loadingTurn}
                                  onClick={() => handleAction(`Go to ${loc.name}`)}
                                  style={{
                                    padding: "3px 8px",
                                    borderRadius: 4,
                                    background: isActive ? `${themePrimary}25` : "rgba(255, 255, 255, 0.02)",
                                    border: isActive ? `1px solid ${themePrimary}` : "1px solid var(--border-subtle)",
                                    color: isActive ? themePrimary : "var(--text-secondary)",
                                    fontSize: "0.625rem",
                                    cursor: isActive ? "default" : "pointer",
                                    opacity: isActive ? 1 : 0.7,
                                    transition: "all 0.15s"
                                  }}
                                >
                                  {loc.name}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              ) : (
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Explore Room:</span>
                  {selectedScenario.locations.map((loc) => {
                    const isActive = loc.name === currentLocation;
                    return (
                      <button
                        key={loc.id}
                        disabled={isActive || loadingTurn}
                        onClick={() => handleAction(`Go to ${loc.name}`)}
                        style={{
                          padding: "4px 10px",
                          borderRadius: 4,
                          background: isActive ? `${themePrimary}25` : "rgba(255, 255, 255, 0.02)",
                          border: isActive ? `1px solid ${themePrimary}` : "1px solid var(--border-subtle)",
                          color: isActive ? themePrimary : "var(--text-secondary)",
                          fontSize: "0.6875rem",
                          cursor: isActive ? "default" : "pointer",
                          opacity: isActive ? 1 : 0.7,
                          transition: "all 0.2s"
                        }}
                      >
                        🚶‍♂️ {loc.name}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Dynamic Choices Buttons */}
          {!finished && suggestedChoices.length > 0 && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {suggestedChoices.map((choice, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAction(choice)}
                  disabled={loadingTurn}
                  style={{
                    flex: "1 1 calc(33% - 8px)",
                    minWidth: 150,
                    padding: "10px 14px",
                    borderRadius: 8,
                    background: `${themePrimary}06`,
                    border: `1px solid ${themePrimary}20`,
                    color: isNoir ? "#e0f7fa" : "#e0f2fe",
                    fontSize: "0.75rem",
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    display: "flex",
                    alignItems: "center",
                    gap: 8
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = `${themePrimary}12`; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = `${themePrimary}06`; }}
                >
                  <span>🕵️</span>
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{choice}</span>
                </button>
              ))}
            </div>
          )}

          {/* Sandbox command line & Accuse CTA */}
          <div style={{ display: "flex", gap: 10 }}>
            {finished ? (
              <div style={{ width: "100%", display: "flex", gap: 12 }}>
                <button
                  onClick={() => handleStartGame(selectedScenario)}
                  style={{
                    flex: 1, padding: "12px", borderRadius: 8, background: themePrimary,
                    color: "#0a0f1d", border: "none", fontSize: "0.8125rem", fontWeight: 700,
                    cursor: "pointer"
                  }}
                >
                  Play Case Again
                </button>
                <button
                  onClick={handleExitGame}
                  style={{
                    flex: 1, padding: "12px", borderRadius: 8, background: "rgba(255, 255, 255, 0.02)",
                    border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", fontSize: "0.8125rem", fontWeight: 600,
                    cursor: "pointer"
                  }}
                >
                  Return to Games Hub
                </button>
              </div>
            ) : (
              <>
                <input
                  type="text"
                  placeholder="Conduct custom searches, interrogations, or moves..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleAction(inputText); }}
                  disabled={loadingTurn}
                  style={{
                    flex: 1, padding: "12px 18px", borderRadius: 8,
                    background: "rgba(255,255,255,0.01)", border: `1px solid ${themePrimary}20`,
                    color: "var(--text-primary)", fontSize: "0.8125rem",
                    outline: "none"
                  }}
                />
                <button
                  onClick={() => handleAction(inputText)}
                  disabled={loadingTurn || !inputText.trim()}
                  style={{
                    padding: "0 24px", borderRadius: 8, background: themePrimary,
                    color: "#0a0f1d", border: "none", fontSize: "0.8125rem", fontWeight: 700,
                    cursor: "pointer", transition: "all 0.2s"
                  }}
                >
                  Send
                </button>
                
                <button
                  onClick={() => setShowAccuseModal(true)}
                  disabled={loadingTurn}
                  style={{
                    padding: "0 18px", borderRadius: 8, background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
                    color: "#fff", border: "none", fontSize: "0.75rem", fontWeight: 700,
                    cursor: "pointer", boxShadow: "0 0 15px rgba(239, 68, 68, 0.3)", textTransform: "uppercase",
                    letterSpacing: "0.05em"
                  }}
                >
                  Accuse
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* RIGHT PANEL: Suspects Board / Dossier Tabs Layout (40%) */}
      <div style={{ flex: 4, display: "flex", flexDirection: "column", padding: "20px 24px", gap: 16, background: isNoir ? "rgba(8, 12, 24, 0.4)" : "rgba(8, 12, 24, 0.2)", overflowY: "hidden" }}>
        
        {/* Tab Headers */}
        <div style={{ display: "flex", borderBottom: `1px solid ${themeBorder}` }}>
          <button
            onClick={() => setActiveRightTab("suspects")}
            style={{
              flex: 1,
              padding: "10px 0",
              background: "none",
              border: "none",
              borderBottom: activeRightTab === "suspects" ? `2px solid ${themePrimary}` : "none",
              color: activeRightTab === "suspects" ? themePrimary : "var(--text-muted)",
              fontSize: "0.75rem",
              fontWeight: 700,
              cursor: "pointer",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              transition: "all 0.2s"
            }}
          >
            📋 Suspects & Alibis
          </button>
          <button
            onClick={() => setActiveRightTab("dossier")}
            style={{
              flex: 1,
              padding: "10px 0",
              background: "none",
              border: "none",
              borderBottom: activeRightTab === "dossier" ? `2px solid ${themePrimary}` : "none",
              color: activeRightTab === "dossier" ? themePrimary : "var(--text-muted)",
              fontSize: "0.75rem",
              fontWeight: 700,
              cursor: "pointer",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              transition: "all 0.2s"
            }}
          >
            📁 Clues & Secrets
          </button>
          {isExtreme && (
            <button
              onClick={() => setShowCorkboard(true)}
              style={{
                flex: 1,
                padding: "10px 0",
                background: "none",
                border: "none",
                borderBottom: "none",
                color: showCorkboard ? themePrimary : "var(--text-muted)",
                fontSize: "0.75rem",
                fontWeight: 700,
                cursor: "pointer",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                transition: "all 0.2s"
              }}
            >
              📌 Clue Board
            </button>
          )}
        </div>

        {/* Tab Content 1: Suspects & Alibis */}
        {activeRightTab === "suspects" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14, overflowY: "auto", flex: 1, paddingRight: 4 }}>
            {selectedScenario.suspects.map((susp) => {
              const state = suspectStates[susp.name] || { suspicion: susp.starting_suspicion, interrogated: false, alibi: "", last_statement: "" };
              const suspPct = Math.round(state.suspicion * 100);
              
              // Dynamic meter color
              const progressColor = state.suspicion > 0.7
                ? "linear-gradient(90deg, #dc2626 0%, #ef4444 100%)"
                : state.suspicion > 0.4
                  ? "linear-gradient(90deg, #d97706 0%, #f59e0b 100%)"
                  : `linear-gradient(90deg, ${isNoir ? "#0891b2" : "#0284c7"} 0%, ${themePrimary} 100%)`;

              return (
                <div
                  key={susp.name}
                  style={{
                    padding: 14,
                    background: isNoir ? "rgba(255, 255, 255, 0.01)" : "rgba(255, 255, 255, 0.01)",
                    border: `1px solid ${isNoir ? "rgba(6, 182, 212, 0.12)" : "var(--border-subtle)"}`,
                    borderRadius: 8,
                    display: "flex",
                    flexDirection: "column",
                    gap: 6
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                    <div>
                      <strong style={{ fontSize: "0.8125rem", color: "#f8fafc" }}>{susp.name}</strong>
                      <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginLeft: 6 }}>({susp.role})</span>
                      {state.current_location && (
                        <div style={{ fontSize: "0.625rem", color: themePrimary, marginTop: 2, display: "flex", alignItems: "center", gap: 4 }}>
                          <span>📍 Location:</span>
                          <strong>{state.current_location}</strong>
                        </div>
                      )}
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                      {state.interrogated && (
                        <span style={{ fontSize: "0.5625rem", background: "rgba(16, 185, 129, 0.15)", color: "#10b981", padding: "1px 6px", borderRadius: 4, textTransform: "uppercase", fontWeight: 700 }}>
                          Interrogated
                        </span>
                      )}
                      {state.current_location === currentLocation && (
                        <span style={{ fontSize: "0.5625rem", background: "rgba(6, 182, 212, 0.15)", border: "1px solid rgba(6, 182, 212, 0.3)", color: "#06b6d4", padding: "1px 6px", borderRadius: 4, textTransform: "uppercase", fontWeight: 700, display: "flex", alignItems: "center", gap: 3 }} className="pulse-alert">
                          <span style={{ width: 4, height: 4, borderRadius: "50%", background: "#06b6d4" }} />
                          In Room
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                    {susp.bio}
                  </p>

                  {/* Render Alibi details for Hard/Noir mode */}
                  {state.alibi && (
                    <div style={{
                      marginTop: 4, padding: "8px 10px", background: "rgba(255,255,255,0.02)",
                      border: `1px solid ${isNoir ? "rgba(255,255,255,0.03)" : "rgba(255,255,255,0.05)"}`,
                      borderRadius: 6, fontSize: "0.6875rem", color: "var(--text-secondary)"
                    }}>
                      <strong style={{ color: themePrimary }}>Alibi Claim:</strong> &ldquo;{state.alibi}&rdquo;
                    </div>
                  )}

                  {/* Render Testimony / Last Statement if interrogated */}
                  {state.last_statement && (
                    <div style={{
                      marginTop: 4, padding: "8px 10px", background: "rgba(16, 185, 129, 0.03)",
                      border: "1px solid rgba(16, 185, 129, 0.15)",
                      borderRadius: 6, fontSize: "0.6875rem", color: "var(--text-secondary)"
                    }}>
                      <strong style={{ color: "#10b981" }}>📢 Testimony:</strong> &ldquo;{state.last_statement}&rdquo;
                    </div>
                  )}

                  <div style={{ marginTop: 4 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.625rem", color: "var(--text-secondary)", marginBottom: 4 }}>
                      <span>Suspicion Index</span>
                      <strong style={{ color: state.suspicion > 0.7 ? "#ef4444" : themePrimary }}>{suspPct}%</strong>
                    </div>
                    <div style={{ width: "100%", height: 6, background: "rgba(255,255,255,0.05)", borderRadius: 3, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${suspPct}%`, background: progressColor, borderRadius: 3, transition: "width 0.4s cubic-bezier(0.16, 1, 0.3, 1)" }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Tab Content 2: Case Clues & Secrets */}
        {activeRightTab === "dossier" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, overflowY: "auto", flex: 1, paddingRight: 4 }}>
            
            {/* Rem's Deduction Consulting Widget */}
            <div style={{
              padding: 14, background: "rgba(6, 182, 212, 0.02)", border: `1px solid ${themeBorder}`,
              borderRadius: 8, display: "flex", flexDirection: "column", gap: 8
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: "0.75rem", color: "#f8fafc", display: "flex", alignItems: "center", gap: 6 }}>
                  🧠 Rem&apos;s Deduction Notebook
                </strong>
                <span style={{ fontSize: "0.6875rem", color: remConsultationsLeft > 0 ? themePrimary : "#ef4444", fontWeight: 700 }}>
                  {remConsultationsLeft} / 2 Charges Left
                </span>
              </div>
              <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", lineHeight: 1.3 }}>
                Need psychological analysis or alibi reviews? Consulting Rem gives you a sarcasm-heavy case summary (doesn&apos;t consume turns).
              </p>
              {!finished && (
                <button
                  disabled={remConsultationsLeft <= 0 || loadingTurn}
                  onClick={handleConsultRem}
                  style={{
                    width: "100%", padding: "8px 0", borderRadius: 6, background: remConsultationsLeft > 0 ? themePrimary : "rgba(255,255,255,0.03)",
                    border: "none", color: remConsultationsLeft > 0 ? "#0a0f1d" : "var(--text-muted)", fontSize: "0.6875rem",
                    fontWeight: 700, cursor: remConsultationsLeft > 0 ? "pointer" : "not-allowed", transition: "all 0.2s"
                  }}
                >
                  Consult Rem
                </button>
              )}
            </div>

            {/* Case Contradictions (Discovered vs Predefined) */}
            {selectedScenario.contradictions && selectedScenario.contradictions.length > 0 && (
              <div style={{ padding: 14, background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-subtle)", borderRadius: 8 }}>
                <strong style={{ fontSize: "0.75rem", color: "#f8fafc", display: "block", marginBottom: 10 }}>
                  ⚠️ Statement Contradictions
                </strong>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {selectedScenario.contradictions.map((contra) => {
                    const isUnlocked = discoveredContradictions.includes(contra.id);
                    return (
                      <div
                        key={contra.id}
                        style={{
                          padding: 10,
                          borderRadius: 6,
                          background: isUnlocked ? "rgba(245, 158, 11, 0.04)" : "rgba(255, 255, 255, 0.01)",
                          border: isUnlocked ? "1px solid rgba(245, 158, 11, 0.3)" : "1px dashed rgba(255,255,255,0.05)",
                          color: isUnlocked ? "#fbd58e" : "var(--text-muted)",
                          fontSize: "0.6875rem",
                          lineHeight: 1.4
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                          <strong>{isUnlocked ? "⚠️ Discrepancy Found!" : "🔒 Locked Discrepancy"}</strong>
                        </div>
                        {isUnlocked ? contra.description : "Cross-examine alibis and statements to lock onto this contradiction."}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Evidence & Clues locker */}
            <div>
              <strong style={{ fontSize: "0.75rem", color: "#f8fafc", display: "block", marginBottom: 10 }}>
                🎒 Collected Clues ({cluesFound.length}/{selectedScenario.clues.length})
              </strong>
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10 }}>
                {selectedScenario.clues.map((clue) => {
                  const isDiscovered = cluesFound.includes(clue.name) || inventory.includes(clue.name);
                  
                  if (isDiscovered) {
                    return (
                      <div
                        key={clue.id}
                        style={{
                          padding: 12,
                          background: `${themePrimary}03`,
                          border: `1px solid ${themePrimary}20`,
                          borderRadius: 8,
                          display: "flex",
                          gap: 10,
                          alignItems: "flex-start",
                          transition: "all 0.3s ease"
                        }}
                      >
                        <span style={{ fontSize: "1.25rem" }}>🔍</span>
                        <div>
                          <strong style={{ fontSize: "0.75rem", color: themePrimary }}>{clue.name}</strong>
                          <p style={{ fontSize: "0.6875rem", color: "var(--text-secondary)", marginTop: 2, lineHeight: 1.3 }}>
                            {clue.desc}
                          </p>
                          <span style={{ fontSize: "0.5625rem", background: "rgba(255,255,255,0.05)", padding: "1px 5px", borderRadius: 3, color: "var(--text-muted)", marginTop: 4, display: "inline-block" }}>
                            Found in: {clue.hidden_at}
                          </span>
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div
                      key={clue.id}
                      style={{
                        padding: 12,
                        background: "rgba(255,255,255,0.02)",
                        border: "1px dashed rgba(255, 255, 255, 0.05)",
                        borderRadius: 8,
                        display: "flex",
                        gap: 10,
                        alignItems: "center",
                        opacity: 0.5
                      }}
                    >
                      <span style={{ fontSize: "1rem" }}>🔒</span>
                      <div>
                        <strong style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Undiscovered Evidence</strong>
                        <p style={{ fontSize: "0.625rem", color: "var(--text-muted)", marginTop: 2 }}>
                          Inspect rooms and search alibis to lock onto this clue.
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}

      </div>

      {/* FULL-SCREEN CLUE CORKBOARD OVERLAY */}
      {showCorkboard && isExtreme && (
        <div style={{
          position: "fixed",
          inset: 0,
          zIndex: 90,
          display: "flex",
          flexDirection: "column",
          background: "rgba(3, 5, 10, 0.92)",
          backdropFilter: "blur(12px)",
          animation: "fadeInBoard 0.25s ease"
        }}>
          <style dangerouslySetInnerHTML={{ __html: `
            @keyframes fadeInBoard { from { opacity: 0; } to { opacity: 1; } }
          `}} />
          {/* Header */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "18px 32px",
            borderBottom: "1px solid rgba(141, 110, 99, 0.25)"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: "1.25rem" }}>📌</span>
              <div>
                <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.1rem", fontWeight: 700, color: "#d7ccc8", margin: 0, letterSpacing: "0.04em" }}>
                  Clue Corkboard
                </h2>
                <p style={{ fontSize: "0.7rem", color: "#8d6e63", margin: 0, marginTop: 2 }}>
                  Discovered evidence pinned to suspects. Connect the dots.
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowCorkboard(false)}
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#bcaaa4",
                padding: "8px 20px",
                borderRadius: 8,
                cursor: "pointer",
                fontSize: "0.8rem",
                fontWeight: 600,
                transition: "all 0.2s"
              }}
            >
              ✕ Close Board
            </button>
          </div>

          {/* Corkboard Grid */}
          <div style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px 32px",
          }}>
            <div className="corkboard" style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: 16
            }}>
              {selectedScenario.suspects.map((susp) => {
                const state = suspectStates[susp.name] || { suspicion: susp.starting_suspicion, interrogated: false, alibi: "", last_statement: "" };
                const linkedClues = selectedScenario.clues.filter((clue) => 
                  clue.belongs_to === susp.name && (cluesFound.includes(clue.name) || inventory.includes(clue.name))
                );
                const suspPct = Math.round(state.suspicion * 100);

                return (
                  <div key={susp.name} style={{
                    padding: 16,
                    background: "rgba(0, 0, 0, 0.35)",
                    border: linkedClues.length > 0 ? "1px solid rgba(216, 67, 21, 0.4)" : "1px solid rgba(141, 110, 99, 0.25)",
                    borderRadius: 8,
                    display: "flex",
                    flexDirection: "column",
                    gap: 10
                  }}>
                    {/* Suspect header */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: "1.1rem" }}>👤</span>
                        <div>
                          <strong style={{ fontSize: "0.825rem", color: "#efebe9" }}>
                            {susp.name}
                          </strong>
                          <div style={{ fontSize: "0.625rem", color: "#bcaaa4", fontStyle: "italic" }}>
                            {susp.role}
                          </div>
                        </div>
                      </div>
                      <span style={{
                        fontSize: "0.6rem",
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontWeight: 700,
                        background: suspPct > 70 ? "rgba(239,68,68,0.15)" : suspPct > 40 ? "rgba(217,119,6,0.15)" : "rgba(6,182,212,0.1)",
                        color: suspPct > 70 ? "#f87171" : suspPct > 40 ? "#f59e0b" : "#06b6d4"
                      }}>
                        {suspPct}% SUS
                      </span>
                    </div>

                    {/* Last statement if any */}
                    {state.last_statement && (
                      <div style={{
                        fontSize: "0.675rem",
                        color: "#a1887f",
                        fontStyle: "italic",
                        padding: "6px 10px",
                        background: "rgba(255,255,255,0.02)",
                        borderLeft: "2px solid rgba(141,110,99,0.5)",
                        borderRadius: "0 4px 4px 0"
                      }}>
                        &ldquo;{state.last_statement}&rdquo;
                      </div>
                    )}

                    {/* Evidence cards */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {linkedClues.length > 0 ? (
                        linkedClues.map((clue) => (
                          <div key={clue.id} className="evidence-card" style={{ transform: `rotate(${Math.random() > 0.5 ? 0.5 : -0.5}deg)` }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.7rem" }}>
                              <span style={{ fontWeight: 700, color: "#8c1d1d" }}>
                                📌 {clue.name}
                              </span>
                              <span style={{ fontSize: "0.5625rem", background: "rgba(216, 67, 21, 0.15)", color: "#d84315", padding: "1px 6px", borderRadius: 3, fontWeight: 700 }}>
                                EVIDENCE
                              </span>
                            </div>
                            <p style={{ fontSize: "0.65rem", color: "#4e342e", marginTop: 4, lineHeight: 1.4 }}>
                              {clue.desc}
                            </p>
                          </div>
                        ))
                      ) : (
                        <span style={{ fontSize: "0.65rem", color: "#6d4c41", fontStyle: "italic" }}>
                          No linked evidence discovered yet.
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* FINAL RESOLUTION ACCUSATION MODAL */}
      {showAccuseModal && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center",
          background: "rgba(0,0,0,0.85)", backdropFilter: "blur(6px)"
        }}>
          <div
            className="glass-panel"
            style={{
              width: "90%", maxWidth: 450, padding: 32,
              background: "linear-gradient(135deg, #090e1d 0%, #050811 100%)",
              border: "1px solid #ef4444", boxShadow: "0 0 40px rgba(239, 68, 68, 0.25)",
              borderRadius: 16
            }}
          >
            <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.3rem", fontWeight: 700, color: "#fff", marginBottom: 6, display: "flex", alignItems: "center", gap: 10 }}>
              🚨 Present Final Case Dossier
            </h2>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 20 }}>
              Specify the culprit, matching weapon, and complete motive. Submitting the wrong accusation allows the killer to slip away.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 28 }}>
              {/* Suspect Selector */}
              <div>
                <label style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--text-secondary)", fontWeight: 700, display: "block", marginBottom: 6 }}>
                  Accused Suspect
                </label>
                <select
                  value={accusedSuspect}
                  onChange={(e) => setAccusedSuspect(e.target.value)}
                  style={{
                    width: "100%", padding: "10px", borderRadius: 8, background: "#060913",
                    border: "1px solid rgba(255, 255, 255, 0.1)", color: "#fff", fontSize: "0.8125rem", outline: "none"
                  }}
                >
                  <option value="">-- Choose suspect --</option>
                  {selectedScenario.suspects.map(s => (
                    <option key={s.name} value={s.name}>{s.name} ({s.role})</option>
                  ))}
                </select>
              </div>

              {/* Weapon Selector */}
              <div>
                <label style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--text-secondary)", fontWeight: 700, display: "block", marginBottom: 6 }}>
                  Weapon Used
                </label>
                <select
                  value={accusedWeapon}
                  onChange={(e) => setAccusedWeapon(e.target.value)}
                  style={{
                    width: "100%", padding: "10px", borderRadius: 8, background: "#060913",
                    border: "1px solid rgba(255, 255, 255, 0.1)", color: "#fff", fontSize: "0.8125rem", outline: "none"
                  }}
                >
                  <option value="">-- Choose weapon --</option>
                  {selectedScenario.weapons.map(w => (
                    <option key={w.id} value={w.name}>{w.name}</option>
                  ))}
                </select>
              </div>

              {/* Motive input */}
              <div>
                <label style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--text-secondary)", fontWeight: 700, display: "block", marginBottom: 6 }}>
                  Accusation motive
                </label>
                <textarea
                  placeholder="Explain why they committed this crime..."
                  rows={3}
                  value={accusedMotive}
                  onChange={(e) => setAccusedMotive(e.target.value)}
                  style={{
                    width: "100%", padding: "10px", borderRadius: 8, background: "#060913",
                    border: "1px solid rgba(255, 255, 255, 0.1)", color: "#fff", fontSize: "0.8125rem",
                    outline: "none", resize: "none"
                  }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: 12 }}>
              <button
                disabled={submittingAccusation}
                onClick={handleSubmitAccusation}
                style={{
                  flex: 2, padding: "10px 0", borderRadius: 8, background: "#ef4444",
                  color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 700,
                  cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center"
                }}
              >
                {submittingAccusation ? "Filing Charges..." : "Submit Case"}
              </button>
              <button
                disabled={submittingAccusation}
                onClick={() => setShowAccuseModal(false)}
                style={{
                  flex: 1, padding: "10px 0", borderRadius: 8, background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", fontSize: "0.8125rem",
                  fontWeight: 600, cursor: "pointer"
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ACCUSATION OUTCOME OVERLAY SCREEN (solved or failed) */}
      {finished && accusationResult && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 110, display: "flex", alignItems: "center", justifyContent: "center",
          background: "rgba(0,0,0,0.92)", backdropFilter: "blur(8px)"
        }}>
          <div
            className="glass-panel"
            style={{
              width: "95%", maxWidth: 720, padding: 32, textAlign: "center",
              background: "linear-gradient(135deg, #090e1d 0%, #050811 100%)",
              border: accusationResult.success ? "2px solid #10b981" : "2px solid #ef4444",
              boxShadow: accusationResult.success ? "0 0 40px rgba(16, 185, 129, 0.25)" : "0 0 40px rgba(239, 68, 68, 0.25)",
              borderRadius: 16,
              display: "flex", flexDirection: "column", gap: 20
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <div style={{ fontSize: "3.5rem", marginBottom: 8, lineHeight: 1 }}>
                {accusationResult.success ? "🎉" : "💀"}
              </div>
              
              <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.5rem", fontWeight: 700, color: "#fff", margin: 0 }}>
                {accusationResult.success ? "MYSTERY SOLVED!" : "CASE FILE COLD"}
              </h2>
              
              <h4 style={{ color: accusationResult.success ? "#10b981" : "#ef4444", fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", margin: 0 }}>
                {accusationResult.success ? "Master Detective Unlocked" : "The Killer Escapes"}
              </h4>
            </div>

            {accusationResult.success ? (
              <div style={{ padding: "12px 16px", background: "rgba(16, 185, 129, 0.05)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: 10, display: "flex", gap: 12, alignItems: "center", textAlign: "left" }}>
                <span style={{ fontSize: "1.5rem" }}>🕵️‍♂️</span>
                <div>
                  <strong style={{ color: "#fff", fontSize: "0.75rem" }}>Medal Unlocked: Master Detective</strong>
                  <p style={{ fontSize: "0.625rem", color: "var(--text-muted)", marginTop: 2 }}>
                    Solved a procedural Murder Mystery. Scrapbook achievement loaded successfully.
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ padding: "12px 16px", background: "rgba(239, 68, 68, 0.04)", border: "1px solid rgba(239, 68, 68, 0.15)", borderRadius: 10, fontSize: "0.75rem", color: "#f87171", display: "flex", justifyContent: "space-around", gap: 12 }}>
                <div>Actual Culprit: <strong style={{ color: "#fff" }}>{accusationResult.secret_culprit}</strong></div>
                <div style={{ width: 1, background: "rgba(239, 68, 68, 0.15)" }} />
                <div>Actual Murder Weapon: <strong style={{ color: "#fff" }}>{accusationResult.secret_weapon}</strong></div>
              </div>
            )}

            {/* SCROLLABLE DETAILED CRIME HISTORY STORY BLOCK */}
            <div style={{ display: "flex", flexDirection: "column", gap: 8, textAlign: "left" }}>
              <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Case Resolution & Crime Timeline
              </div>
              
              <div style={{
                maxHeight: "240px", overflowY: "auto", padding: "16px 20px",
                background: "rgba(255, 255, 255, 0.01)", border: `1px solid var(--border-subtle)`,
                borderLeft: `3px solid ${accusationResult.success ? "#10b981" : "#ef4444"}`, borderRadius: 8
              }}>
                <p style={{
                  fontFamily: "Georgia, serif", fontSize: "0.8125rem", fontStyle: "italic",
                  color: "#9ca3af", lineHeight: 1.6, whiteSpace: "pre-line", margin: 0
                }}>
                  {accusationResult.narrator_text}
                </p>
              </div>
            </div>

            {/* REM'S REACTION BUBBLE */}
            {accusationResult.rem_dialogue && (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 4, textAlign: "left" }}>
                <div style={{
                  background: isNoir ? "rgba(6, 182, 212, 0.04)" : "rgba(56, 189, 248, 0.04)",
                  border: isNoir ? "1px solid rgba(6, 182, 212, 0.15)" : "1px solid rgba(56, 189, 248, 0.15)",
                  padding: "12px 16px", borderRadius: "12px 12px 12px 2px", color: isNoir ? "#e0f7fa" : "#e0f2fe",
                  fontSize: "0.8125rem", lineHeight: 1.5, width: "100%"
                }}>
                  {accusationResult.rem_dialogue}
                </div>
                <span style={{ fontSize: "0.5625rem", color: themePrimary, paddingLeft: 4 }}>rem's verdict</span>
              </div>
            )}

            <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
              <button
                onClick={() => handleStartGame(selectedScenario)}
                style={{
                  flex: 1, padding: "12px", borderRadius: 8, background: themePrimary,
                  color: "#0a0f1d", border: "none", fontSize: "0.8125rem", fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                Start New Case
              </button>
              <button
                onClick={handleExitGame}
                style={{
                  flex: 1, padding: "12px", borderRadius: 8, background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", fontSize: "0.8125rem", fontWeight: 600,
                  cursor: "pointer"
                }}
              >
                Exit to Games Hub
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx global>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .pulse-alert {
          animation: pulse-glow 2s infinite ease-in-out;
        }
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.85; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.03); }
        }
      `}</style>

    </div>
  );
}
