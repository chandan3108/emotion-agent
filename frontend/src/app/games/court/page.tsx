"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  getCourtScenarios,
  startCourtGame,
  submitCourtAction,
  searchRecessRoom,
  submitClosingArguments,
  CourtScenario,
  CourtStartResponse,
  CourtVerdictResponse
} from "@/lib/gameApi";

export default function LawAndRemPage() {
  const router = useRouter();

  // Scenarios state
  const [scenarios, setScenarios] = useState<CourtScenario[]>([]);
  const [selectedCase, setSelectedCase] = useState<CourtScenario | null>(null);
  const [loadingScenarios, setLoadingScenarios] = useState(true);
  const [initializingGame, setInitializingGame] = useState(false);

  // Active game state
  const [session, setSession] = useState<CourtStartResponse | null>(null);
  const [selectedStatementIdx, setSelectedStatementIdx] = useState<number | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string>("");
  const [questionText, setQuestionText] = useState("");
  const [closingText, setClosingText] = useState("");
  
  const [loadingAction, setLoadingAction] = useState(false);
  const [shaking, setShaking] = useState(false);
  
  // Objection / Hold It visual overlays
  const [objectionType, setObjectionType] = useState<"objection" | "hold_it" | null>(null);
  const [showObjectionText, setShowObjectionText] = useState(false);
  
  // Final Verdict state
  const [verdictData, setVerdictData] = useState<CourtVerdictResponse | null>(null);

  // Rem Co-Counsel Chat state
  const [showRemChat, setShowRemChat] = useState(false);
  const [remQuestion, setRemQuestion] = useState("");

  const isNoir = selectedCase?.difficulty === "hard" || selectedCase?.difficulty === "extreme";

  const logsEndRef = useRef<HTMLDivElement>(null);

  // Fetch cases on mount
  useEffect(() => {
    getCourtScenarios()
      .then((data) => setScenarios(data))
      .catch((err) => console.error("Failed to load scenarios:", err))
      .finally(() => setLoadingScenarios(false));
  }, []);

  // Scroll to bottom when history updates
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.history]);

  const handleStartCase = async (caseScenario: CourtScenario) => {
    setSelectedCase(caseScenario);
    setInitializingGame(true);
    setVerdictData(null);
    setSelectedStatementIdx(null);
    setSelectedEvidenceId("");
    setQuestionText("");
    setClosingText("");
    
    try {
      const res = await startCourtGame(caseScenario.case_id);
      setSession(res);
    } catch (e) {
      console.error(e);
      alert("Failed to start the courtroom battle.");
    } finally {
      setInitializingGame(false);
    }
  };

  const triggerVisualShout = (type: "objection" | "hold_it") => {
    setObjectionType(type);
    setShowObjectionText(true);
    setShaking(true);
    
    setTimeout(() => {
      setShowObjectionText(false);
      setObjectionType(null);
    }, 1200);

    setTimeout(() => {
      setShaking(false);
    }, 500);
  };

  const handlePressStatement = async (statementIdx: number) => {
    if (!session || loadingAction) return;
    setLoadingAction(true);
    triggerVisualShout("hold_it");

    try {
      const updated = await submitCourtAction("press", { statementIdx });
      setSession(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handlePresentEvidence = async (statementIdx: number, evidenceId: string) => {
    if (!session || !evidenceId || loadingAction) return;
    setLoadingAction(true);
    triggerVisualShout("objection");

    try {
      const updated = await submitCourtAction("present_evidence", { statementIdx, evidenceId });
      setSession(updated);
      setSelectedEvidenceId("");
      setSelectedStatementIdx(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleAskQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session || !questionText.trim() || loadingAction) return;
    setLoadingAction(true);

    const question = questionText;
    setQuestionText("");

    try {
      const updated = await submitCourtAction("text_question", { question });
      setSession(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleSearchRecessRoom = async (roomId: string) => {
    if (!session || loadingAction) return;
    setLoadingAction(true);

    try {
      const updated = await searchRecessRoom(roomId);
      setSession(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleConsultRem = async (question?: string) => {
    if (!session || loadingAction) return;
    setLoadingAction(true);

    try {
      const updated = await submitCourtAction("consult_rem", { question });
      setSession(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleCallWitness = async () => {
    if (!session || loadingAction) return;
    setLoadingAction(true);

    try {
      const updated = await submitCourtAction("call_witness", {});
      setSession(updated);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleSubmitClosing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session || !closingText.trim() || loadingAction) return;
    setLoadingAction(true);

    try {
      const verdict = await submitClosingArguments(closingText);
      setVerdictData(verdict);
      // Retrieve final session log updates
      const updated = await submitCourtAction("consult_rem", {}); // dummy action to refresh finished session view
      setSession(prev => prev ? { ...prev, finished: true, phase: "verdict", history: updated.history } : null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleExitGame = () => {
    router.push("/games");
  };

  // Curated premium design system styles
  const themePrimary = "#d4af37"; // Rich Antique Gold
  const themePrimaryHover = "#b8972f";
  const bgMain = "linear-gradient(135deg, #0e0d0c 0%, #1c1815 100%)"; // Mahogany / Gold Hue Dark theme
  const borderGold = "rgba(212, 175, 55, 0.15)";
  const glassBack = "rgba(10, 8, 7, 0.85)";

  if (loadingScenarios) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: bgMain, color: "#fff" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ width: 40, height: 40, border: "3px solid rgba(255,255,255,0.05)", borderTopColor: themePrimary, borderRadius: "50%", animation: "spin 1s linear infinite", margin: "0 auto 16px" }} />
          <p style={{ fontSize: "0.875rem", fontStyle: "italic", color: "var(--text-muted)" }}>Loading cases files...</p>
        </div>
      </div>
    );
  }

  // CASE SELECTION SCREEN
  if (!session) {
    return (
      <div style={{ minHeight: "100vh", background: bgMain, padding: "40px 24px", color: "#fff", fontFamily: "'Inter', sans-serif" }}>
        <div style={{ maxWidth: 1000, margin: "0 auto" }}>
          <header style={{ marginBottom: 40, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "2.25rem", fontWeight: 800, letterSpacing: "-0.03em", color: "#fff" }}>
                🏛️ Law and Rem
              </h1>
              <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: 4 }}>
                Ace Attorney Courtroom Battles. Interrogate witnesses, find alibi contradictions, and present decisive evidence.
              </p>
            </div>
            <button
              onClick={handleExitGame}
              style={{
                padding: "8px 16px", borderRadius: 8, background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.08)", color: "var(--text-secondary)", fontSize: "0.8125rem",
                fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6
              }}
            >
              ✕ Exit Game
            </button>
          </header>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(310px, 1fr))", gap: 24 }}>
            {scenarios.map((sc) => (
              <div
                key={sc.case_id}
                className="glass-panel"
                style={{
                  padding: 28, display: "flex", flexDirection: "column", justifyContent: "space-between",
                  background: "rgba(18, 14, 11, 0.7)", border: `1px solid ${borderGold}`, borderRadius: 12,
                  boxShadow: "0 8px 32px rgba(0,0,0,0.4)"
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                    <span style={{
                      fontSize: "0.625rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em",
                      padding: "4px 8px", borderRadius: 4,
                      background: sc.difficulty === "normal" ? "rgba(56,189,248,0.06)" : "rgba(244,63,94,0.06)",
                      border: sc.difficulty === "normal" ? "1px solid rgba(56,189,248,0.15)" : "1px solid rgba(244,63,94,0.15)",
                      color: sc.difficulty === "normal" ? "#38bdf8" : "#f43f5e"
                    }}>
                      Case: {sc.difficulty}
                    </span>
                    <span style={{ fontSize: "1.25rem" }}>⚖️</span>
                  </div>

                  <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "#fff", marginBottom: 8, fontFamily: "'Space Grotesk', sans-serif" }}>
                    {sc.title}
                  </h3>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.5, marginBottom: 20 }}>
                    {sc.description}
                  </p>

                  <div style={{ display: "flex", flexDirection: "column", gap: 6, padding: "12px 14px", background: "rgba(255,255,255,0.01)", border: "1px solid rgba(255,255,255,0.02)", borderRadius: 8, fontSize: "0.6875rem", color: "var(--text-secondary)", marginBottom: 24 }}>
                    <div>Client: <strong style={{ color: "#fff" }}>{sc.client_name} ({sc.client_role})</strong></div>
                    <div>Prosecutor: <strong style={{ color: "#fff" }}>{sc.prosecutor_name}</strong></div>
                    <div>Presiding Judge: <strong style={{ color: "#fff" }}>{sc.judge_name}</strong></div>
                  </div>
                </div>

                <button
                  disabled={initializingGame}
                  onClick={() => handleStartCase(sc)}
                  style={{
                    width: "100%", padding: "12px", borderRadius: 8, background: themePrimary,
                    color: "#0c0a09", border: "none", fontSize: "0.8125rem", fontWeight: 800,
                    cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 6
                  }}
                >
                  {initializingGame ? "Loading Trial..." : "Take Defense Stand"}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // CURRENT ACTIVE WITNESS DETAILS
  const currentWitness = session.witnesses[session.current_witness_idx];

  // SCALE OF JUSTICE BAR CALCULATIONS
  const scalePercent = ((session.jury_sentiment + 100) / 200) * 100;

  return (
    <div
      style={{
        minHeight: "100vh", background: bgMain, color: "#fff", fontFamily: "'Inter', sans-serif",
        display: "flex", flexDirection: "column", transition: "transform 0.05s ease",
        transform: shaking ? "translate(3px, 2px) rotate(0.5deg)" : "none"
      }}
    >
      {/* HEADER BAR */}
      <header
        style={{
          background: glassBack, borderBottom: `1px solid ${borderGold}`,
          padding: "16px 24px", display: "flex", flexDirection: "column", gap: 12
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "1rem", fontWeight: 800, color: themePrimary, letterSpacing: "-0.01em", display: "flex", alignItems: "center", gap: 6 }}>
              🏛️ {session.title}
            </h1>
            <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: 2, display: "block" }}>
              Defense Bench: You & Rem | Defending {session.client_name}
            </span>
          </div>

          {/* Gavel Strikes warnings */}
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Credibility:</span>
              <div style={{ display: "flex", gap: 4 }}>
                {Array.from({ length: 5 }).map((_, i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: "1rem", filter: i >= session.strikes_left ? "grayscale(100%) opacity(0.2)" : "none",
                      transition: "all 0.3s ease"
                    }}
                  >
                    🔨
                  </span>
                ))}
              </div>
            </div>

            <button
              onClick={() => setSession(null)}
              style={{
                padding: "6px 12px", borderRadius: 6, background: "rgba(244,63,94,0.08)",
                border: "1px solid rgba(244,63,94,0.2)", color: "#f43f5e", fontSize: "0.6875rem",
                fontWeight: 700, cursor: "pointer"
              }}
            >
              Withdraw Case
            </button>
          </div>
        </div>

        {/* Dynamic Scales of Justice Index bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "4px 0" }}>
          <span style={{ fontSize: "0.6875rem", color: "#f43f5e", fontWeight: 700, width: 90 }}>⚖️ Prosecution</span>
          <div style={{ flex: 1, height: 8, background: "rgba(255,255,255,0.03)", borderRadius: 4, overflow: "hidden", border: "1px solid rgba(255,255,255,0.05)" }}>
            <div
              style={{
                height: "100%", width: `${scalePercent}%`,
                background: "linear-gradient(90deg, #f43f5e 0%, #10b981 100%)",
                transition: "width 0.6s cubic-bezier(0.16, 1, 0.3, 1)"
              }}
            />
          </div>
          <span style={{ fontSize: "0.6875rem", color: "#10b981", fontWeight: 700, width: 80, textAlign: "right" }}>Defense ⚖️</span>
        </div>
      </header>

      {/* CORE SPLIT SCREEN VIEW */}
      <main style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        
        {/* LEFT PANEL: Courtroom Stage visual board */}
        <section
          style={{
            flex: 1.1, padding: 24, borderRight: `1px solid ${borderGold}`,
            display: "flex", flexDirection: "column", gap: 20, overflowY: "auto"
          }}
        >
          {/* Court Participants Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {/* Judge Bench */}
            <div style={{ padding: 16, background: "rgba(10,8,7,0.4)", border: "1px solid rgba(255,255,255,0.02)", borderRadius: 8, textAlign: "center" }}>
              <div style={{ fontSize: "2rem", marginBottom: 6 }}>👨‍⚖️</div>
              <strong style={{ fontSize: "0.75rem", color: "#fff", display: "block" }}>{session.judge_name}</strong>
              <span style={{ fontSize: "0.5625rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Presiding Judge</span>
            </div>

            {/* Prosecution Desk */}
            <div style={{ padding: 16, background: "rgba(10,8,7,0.4)", border: "1px solid rgba(255,255,255,0.02)", borderRadius: 8, textAlign: "center" }}>
              <div style={{ fontSize: "2rem", marginBottom: 6 }}>👔</div>
              <strong style={{ fontSize: "0.75rem", color: "#fff", display: "block" }}>{session.prosecutor_name}</strong>
              <span style={{ fontSize: "0.5625rem", color: "#f43f5e", textTransform: "uppercase", fontWeight: 700 }}>Prosecutor</span>
            </div>

            {/* Witness Stand */}
            <div style={{ padding: 16, background: "rgba(212,175,55,0.02)", border: `1px solid ${borderGold}`, borderRadius: 8, textAlign: "center", gridColumn: "span 2" }}>
              <div style={{ fontSize: "2.5rem", marginBottom: 6 }}>🎤</div>
              <strong style={{ fontSize: "0.8125rem", color: themePrimary, display: "block" }}>
                {session.phase === "recess" ? "Witness Stand Empty (Recess)" : currentWitness.name}
              </strong>
              <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                {session.phase === "recess" ? "Recess Investigation" : currentWitness.role}
              </span>
              {!session.finished && session.phase !== "recess" && (
                <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: 6, fontStyle: "italic" }}>
                  "{currentWitness.bio}"
                </p>
              )}
            </div>
          </div>

          {/* CHRONOLOGICAL COURT LOGS */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Courtroom Log
            </div>

            <div
              style={{
                flex: 1, background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.02)",
                borderRadius: 8, padding: 16, overflowY: "auto", display: "flex", flexDirection: "column", gap: 16,
                maxHeight: "300px"
              }}
            >
              {session.history.map((h, i) => {
                if (h.role === "testimony") return null; // Render testimony list separately in right panel
                
                const isUser = h.role === "user";
                const isRem = h.role === "rem";
                
                return (
                  <div
                    key={i}
                    style={{
                      display: "flex", flexDirection: "column",
                      alignItems: isUser ? "flex-end" : "flex-start",
                      alignSelf: isUser ? "flex-end" : "flex-start",
                      maxWidth: "80%"
                    }}
                  >
                    <div style={{
                      background: isUser ? "rgba(255,255,255,0.03)" : isRem ? "rgba(212,175,55,0.03)" : "rgba(255,255,255,0.01)",
                      border: isUser ? "1px solid rgba(255,255,255,0.05)" : isRem ? `1px solid ${borderGold}` : "1px solid rgba(255,255,255,0.02)",
                      padding: "8px 12px", borderRadius: isUser ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
                      color: isUser ? "#fff" : isRem ? "#e6c387" : "#e5e7eb", fontSize: "0.75rem",
                      lineHeight: 1.4
                    }}>
                      {h.content}
                    </div>
                    <span style={{ fontSize: "0.5625rem", color: isRem ? themePrimary : "var(--text-muted)", marginTop: 2, paddingLeft: 4 }}>
                      {h.speaker || h.role}
                    </span>
                  </div>
                );
              })}
              <div ref={logsEndRef} />
            </div>
          </div>

          {/* DYNAMIC TEXT QUESTION BAR */}
          {session.phase === "cross_examination" && !session.finished && (
            <form onSubmit={handleAskQuestion} style={{ display: "flex", gap: 8 }}>
              <input
                type="text"
                placeholder={`Ask ${currentWitness.name} a custom question... (e.g. 'Did you enter Johnny's room?')`}
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                disabled={loadingAction}
                style={{
                  flex: 1, padding: "10px 14px", borderRadius: 8, background: "rgba(0,0,0,0.2)",
                  border: `1px solid ${borderGold}`, color: "#fff", fontSize: "0.75rem",
                  outline: "none"
                }}
              />
              <button
                type="submit"
                disabled={loadingAction || !questionText.trim()}
                style={{
                  padding: "0 18px", borderRadius: 8, background: themePrimary,
                  color: "#0a0f1d", border: "none", fontSize: "0.75rem", fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                Question
              </button>
            </form>
          )}
        </section>

        {/* RIGHT PANEL: Interactive testimony list / Case File / Verdict */}
        <section
          style={{
            flex: 0.9, padding: 24, display: "flex", flexDirection: "column",
            gap: 20, overflowY: "auto"
          }}
        >
          {/* PHASE 1: BRIEFING SETUP */}
          {session.phase === "briefing" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ padding: 18, background: "rgba(212,175,55,0.03)", border: `1px solid ${borderGold}`, borderRadius: 10 }}>
                <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: themePrimary, marginBottom: 8 }}>Case Briefing</h3>
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  Review Toby's file and the initial evidence in your locker. Click 'Start Trial' to call the first witness to the stand and begin cross-examination.
                </p>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <h4 style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Initial Evidence</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {session.inventory.map(ev => (
                    <div key={ev.id} style={{ padding: 12, background: "rgba(255,255,255,0.01)", border: "1px solid rgba(255,255,255,0.03)", borderRadius: 8 }}>
                      <strong style={{ fontSize: "0.75rem", color: "#fff", display: "block" }}>📁 {ev.name}</strong>
                      <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: 4 }}>{ev.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={handleCallWitness}
                disabled={loadingAction}
                style={{
                  width: "100%", padding: "12px", borderRadius: 8, background: themePrimary,
                  color: "#0a0f1d", border: "none", fontSize: "0.8125rem", fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                Start Trial & Call Witness
              </button>
            </div>
          )}

          {/* PHASE 2: CROSS EXAMINATION WITNESS TESTIMONY */}
          {session.phase === "cross_examination" && !session.finished && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Witness Testimony
                </span>
                <button
                  onClick={() => setShowRemChat(true)}
                  disabled={loadingAction}
                  style={{
                    padding: "4px 8px", borderRadius: 4, background: "rgba(212,175,55,0.06)",
                    border: `1px solid ${borderGold}`, color: themePrimary, fontSize: "0.625rem",
                    fontWeight: 700, cursor: "pointer"
                  }}
                >
                  💡 Consult Rem
                </button>
              </div>

              {/* Testimony List */}
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {currentWitness.testimony.map((line, idx) => {
                  const isSelected = selectedStatementIdx === idx;
                  
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedStatementIdx(isSelected ? null : idx)}
                      style={{
                        padding: 14, background: isSelected ? "rgba(212,175,55,0.03)" : "rgba(255,255,255,0.01)",
                        border: isSelected ? `1px solid ${themePrimary}` : "1px solid rgba(255,255,255,0.02)",
                        borderRadius: 8, cursor: "pointer", transition: "all 0.2s ease"
                      }}
                    >
                      <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                        <span style={{ fontSize: "0.6875rem", color: themePrimary, fontWeight: 700 }}>#{idx + 1}</span>
                        <p style={{ fontSize: "0.75rem", color: isSelected ? "#fff" : "var(--text-secondary)", lineHeight: 1.4, margin: 0 }}>
                          "{line}"
                        </p>
                      </div>

                      {/* Expanding panel controls */}
                      {isSelected && (
                        <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid rgba(255,255,255,0.05)", display: "flex", gap: 8 }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePressStatement(idx);
                            }}
                            disabled={loadingAction}
                            style={{
                              flex: 1, padding: "6px", borderRadius: 6, background: "rgba(255,255,255,0.03)",
                              border: "1px solid rgba(255,255,255,0.08)", color: "#fff", fontSize: "0.6875rem",
                              fontWeight: 700, cursor: "pointer"
                            }}
                          >
                            👈 Press Statement
                          </button>
                          
                          <button
                            disabled={!selectedEvidenceId || loadingAction}
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePresentEvidence(idx, selectedEvidenceId);
                            }}
                            style={{
                              flex: 1.2, padding: "6px", borderRadius: 6, background: themePrimary,
                              color: "#0a0f1d", border: "none", fontSize: "0.6875rem",
                              fontWeight: 800, cursor: "pointer", opacity: selectedEvidenceId ? 1 : 0.4
                            }}
                          >
                            💥 Present Evidence!
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Evidence selection locker */}
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Present Evidence Locker (Select One)
                </span>
                
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {session.inventory.map(ev => {
                    const isPicked = selectedEvidenceId === ev.id;
                    
                    return (
                      <div
                        key={ev.id}
                        onClick={() => setSelectedEvidenceId(isPicked ? "" : ev.id)}
                        style={{
                          padding: 10, background: isPicked ? "rgba(212,175,55,0.05)" : "rgba(255,255,255,0.01)",
                          border: isPicked ? `1px solid ${themePrimary}` : "1px solid rgba(255,255,255,0.03)",
                          borderRadius: 8, cursor: "pointer", transition: "all 0.2s ease", textAlign: "left"
                        }}
                      >
                        <strong style={{ fontSize: "0.75rem", color: isPicked ? themePrimary : "#fff", display: "block" }}>
                          📁 {ev.name}
                        </strong>
                        <p style={{ fontSize: "0.5625rem", color: "var(--text-muted)", marginTop: 4 }}>
                          {ev.desc}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* PHASE 3: TRIAL RECESS INVESTIGATION MAP */}
          {session.phase === "recess" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ padding: 16, background: "rgba(239, 68, 68, 0.02)", border: "1px solid rgba(239, 68, 68, 0.15)", borderRadius: 8 }}>
                <h3 style={{ fontSize: "0.8125rem", fontWeight: 700, color: "#f87171", marginBottom: 6 }}>⚖️ 10-Minute Recess Declared</h3>
                <p style={{ fontSize: "0.6875rem", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                  The judge has declared a brief recess. You and Rem must investigate the gallery rooms to search for clue contradictions before the trial resumes.
                </p>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <h4 style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Select Room to Search</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {session.recess_locations.map(room => {
                    const isSearched = session.recess_searched.includes(room.id);
                    
                    return (
                      <div
                        key={room.id}
                        style={{
                          padding: 14, background: "rgba(255,255,255,0.01)", border: "1px solid rgba(255,255,255,0.03)",
                          borderRadius: 8, display: "flex", justifyContent: "space-between", alignItems: "center"
                        }}
                      >
                        <div style={{ textAlign: "left" }}>
                          <strong style={{ fontSize: "0.75rem", color: "#fff", display: "block" }}>📍 {room.name}</strong>
                          <span style={{ fontSize: "0.5625rem", color: "var(--text-muted)", marginTop: 2, display: "block" }}>
                            {isSearched ? "Searched" : "Unexplored"}
                          </span>
                        </div>

                        <button
                          onClick={() => handleSearchRecessRoom(room.id)}
                          disabled={isSearched || loadingAction}
                          style={{
                            padding: "6px 12px", borderRadius: 6, background: isSearched ? "rgba(255,255,255,0.02)" : themePrimary,
                            color: isSearched ? "var(--text-muted)" : "#0c0a09", border: "none", fontSize: "0.6875rem",
                            fontWeight: 700, cursor: isSearched ? "default" : "pointer"
                          }}
                        >
                          {isSearched ? "Done" : "Search"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* PHASE 4: CLOSING ARGUMENTS INPUT */}
          {session.phase === "closing" && (
            <form onSubmit={handleSubmitClosing} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ padding: 16, background: "rgba(212,175,55,0.03)", border: `1px solid ${borderGold}`, borderRadius: 10 }}>
                <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: themePrimary, marginBottom: 8 }}>Present Closing Arguments</h3>
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  The cross-examinations are complete. Enter a strong, convincing closing plea summarizing the timeline and contradictions to sway the Jury and Judge.
                </p>
              </div>

              <textarea
                placeholder="Type your final plea here... (e.g. 'Mickey pawned the watch at 8:30 PM, so there was no theft at 10:05 PM...')"
                value={closingText}
                onChange={(e) => setClosingText(e.target.value)}
                disabled={loadingAction}
                style={{
                  height: 120, padding: 14, borderRadius: 8, background: "rgba(0,0,0,0.2)",
                  border: `1px solid ${borderGold}`, color: "#fff", fontSize: "0.75rem",
                  outline: "none", resize: "none", lineHeight: 1.5
                }}
              />

              <button
                type="submit"
                disabled={loadingAction || !closingText.trim()}
                style={{
                  width: "100%", padding: "12px", borderRadius: 8, background: themePrimary,
                  color: "#0a0f1d", border: "none", fontSize: "0.8125rem", fontWeight: 800,
                  cursor: "pointer"
                }}
              >
                {loadingAction ? "Jury Deliberating..." : "Submit to Jury & Judge"}
              </button>
            </form>
          )}

          {/* PHASE 5: VERDICT OUTCOME RESOLUTION DISPLAY */}
          {session.phase === "verdict" && verdictData && (
            <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
              
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                <div style={{ fontSize: "4.5rem", lineHeight: 1 }}>
                  {verdictData.success ? "🎉" : "💀"}
                </div>
                
                <h2 style={{
                  fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.75rem", fontWeight: 800,
                  color: verdictData.success ? "#10b981" : "#ef4444", textShadow: verdictData.success ? "0 0 10px rgba(16,185,129,0.2)" : "none",
                  margin: 0
                }}>
                  {verdictData.verdict_text}
                </h2>
                
                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  Trial Verdict Decided
                </span>
              </div>

              {/* Jurors Visualizer spots */}
              <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "12px 16px", background: "rgba(255,255,255,0.01)", border: "1px solid rgba(255,255,255,0.03)", borderRadius: 8 }}>
                <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", textAlign: "center" }}>
                  Jury Panel Votes (6 Jurors)
                </span>
                
                <div style={{ display: "flex", justifyContent: "space-around", padding: "8px 0" }}>
                  {Array.from({ length: 6 }).map((_, i) => {
                    const isNotGuilty = i < verdictData.votes_not_guilty;
                    return (
                      <div
                        key={i}
                        style={{
                          width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                          background: isNotGuilty ? "rgba(16, 185, 129, 0.05)" : "rgba(239, 68, 68, 0.05)",
                          border: isNotGuilty ? "1px solid rgba(16, 185, 129, 0.2)" : "1px solid rgba(239, 68, 68, 0.2)"
                        }}
                      >
                        <span style={{ fontSize: "0.75rem" }}>{isNotGuilty ? "⚖️" : "💀"}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Judge Decision text block */}
              <div style={{ display: "flex", flexDirection: "column", gap: 6, textAlign: "left" }}>
                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Judge Decision Report</span>
                <div style={{
                  maxHeight: "180px", overflowY: "auto", padding: "12px 14px", background: "rgba(0,0,0,0.2)",
                  border: "1px solid rgba(255,255,255,0.02)", borderLeft: `3px solid ${verdictData.success ? "#10b981" : "#ef4444"}`, borderRadius: 6
                }}>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.5, margin: 0, whiteSpace: "pre-line" }}>
                    {verdictData.judge_decision}
                  </p>
                </div>
              </div>

              {/* Rem verdict reaction */}
              {verdictData.rem_dialogue && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
                  <div style={{
                    background: isNoir ? "rgba(6, 182, 212, 0.04)" : "rgba(56, 189, 248, 0.04)",
                    border: isNoir ? "1px solid rgba(6, 182, 212, 0.15)" : "1px solid rgba(56, 189, 248, 0.15)",
                    padding: "10px 14px", borderRadius: "12px 12px 12px 2px", color: isNoir ? "#e0f7fa" : "#e0f2fe",
                    fontSize: "0.75rem", width: "100%", textAlign: "left"
                  }}>
                    {verdictData.rem_dialogue}
                  </div>
                  <span style={{ fontSize: "0.5625rem", color: themePrimary, paddingLeft: 4 }}>rem's verdict</span>
                </div>
              )}

              {/* Action buttons */}
              <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
                <button
                  onClick={() => handleStartCase(selectedCase!)}
                  style={{
                    flex: 1, padding: "12px", borderRadius: 8, background: themePrimary,
                    color: "#0a0f1d", border: "none", fontSize: "0.8125rem", fontWeight: 700,
                    cursor: "pointer"
                  }}
                >
                  Restart Case
                </button>
                <button
                  onClick={() => setSession(null)}
                  style={{
                    flex: 1, padding: "12px", borderRadius: 8, background: "rgba(255, 255, 255, 0.02)",
                    border: "1px solid var(--border-subtle)", color: "var(--text-secondary)", fontSize: "0.8125rem", fontWeight: 600,
                    cursor: "pointer"
                  }}
                >
                  Exit to Cases List
                </button>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* FULLSCREEN OBJECTION / HOLD IT TEXT SHOUT OVERLAYS */}
      {showObjectionText && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 120, display: "flex", alignItems: "center", justifyContent: "center",
          background: "rgba(0, 0, 0, 0.4)", backdropFilter: "blur(2px)",
          pointerEvents: "none", animation: "fade-out 1s forwards"
        }}>
          <div style={{
            fontFamily: "'Impact', 'Arial Black', sans-serif", fontSize: "4.5rem", fontWeight: 900,
            color: objectionType === "objection" ? "#ef4444" : "#10b981",
            textShadow: "0 0 30px rgba(0,0,0,0.8), 2px 2px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000",
            letterSpacing: "0.05em",
            animation: "scale-in 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards"
          }}>
            {objectionType === "objection" ? "OBJECTION!" : "HOLD IT!"}
          </div>
        </div>
      )}

      {/* CO-COUNSEL REM CHAT WINDOW */}
      {showRemChat && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            width: 330,
            height: 420,
            background: "rgba(15, 12, 10, 0.96)",
            border: `2px solid ${borderGold}`,
            borderRadius: 12,
            display: "flex",
            flexDirection: "column",
            boxShadow: "0 12px 48px rgba(0,0,0,0.7)",
            backdropFilter: "blur(12px)",
            zIndex: 150,
            overflow: "hidden"
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "14px 16px",
              background: "rgba(212, 175, 55, 0.08)",
              borderBottom: `1px solid ${borderGold}`,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center"
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: "1.2rem" }}>👩‍💼</span>
              <div>
                <strong style={{ fontSize: "0.8125rem", color: themePrimary }}>Rem (Co-Counsel)</strong>
                <span style={{ display: "block", fontSize: "0.5625rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700, marginTop: 1 }}>
                  {session.rem_consults_left} tries left
                </span>
              </div>
            </div>
            <button
              onClick={() => setShowRemChat(false)}
              style={{
                background: "none", border: "none", color: "var(--text-muted)", fontSize: "1rem", cursor: "pointer", padding: 4, display: "flex", alignItems: "center", justifyContent: "center"
              }}
            >
              ✕
            </button>
          </div>

          {/* Messages Box */}
          <div
            style={{
              flex: 1,
              padding: 16,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 12
            }}
          >
            {session.rem_chat_history.length === 0 ? (
              <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", padding: 16 }}>
                <span style={{ fontSize: "1.8rem", marginBottom: 10 }}>🧠</span>
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600, margin: "0 0 4px 0" }}>Talk to Rem</p>
                <p style={{ fontSize: "0.6875rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.4 }}>
                  Ask Rem about witness alibis, statements, or evidence. We only have {session.rem_consults_left} consults left for this trial!
                </p>
              </div>
            ) : (
              session.rem_chat_history.map((msg, i) => {
                const isUser = msg.role === "user";
                return (
                  <div
                    key={i}
                    style={{
                      alignSelf: isUser ? "flex-end" : "flex-start",
                      maxWidth: "85%",
                      background: isUser ? "rgba(212,175,55,0.06)" : "rgba(255,255,255,0.02)",
                      border: isUser ? `1px solid ${themePrimary}` : "1px solid rgba(255,255,255,0.05)",
                      borderRadius: 8,
                      padding: "8px 12px",
                      fontSize: "0.75rem",
                      lineHeight: 1.4
                    }}
                  >
                    <div style={{ fontSize: "0.5625rem", color: isUser ? themePrimary : "var(--text-muted)", marginBottom: 4, fontWeight: 800 }}>
                      {isUser ? "Defense (You)" : "Rem (Co-Counsel)"}
                    </div>
                    <div style={{ color: "#fff", whiteSpace: "pre-wrap" }}>{msg.content}</div>
                  </div>
                );
              })
            )}
          </div>

          {/* Input Form */}
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const text = remQuestion.trim();
              if (!text || loadingAction || session.rem_consults_left <= 0) return;
              setRemQuestion("");
              await handleConsultRem(text);
            }}
            style={{
              padding: 12,
              borderTop: "1px solid rgba(255,255,255,0.05)",
              display: "flex",
              gap: 8,
              background: "rgba(0,0,0,0.15)"
            }}
          >
            <input
              type="text"
              placeholder={session.rem_consults_left <= 0 ? "Out of consults" : "Ask Rem..."}
              value={remQuestion}
              onChange={(e) => setRemQuestion(e.target.value)}
              disabled={loadingAction || session.rem_consults_left <= 0}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: 6,
                background: "rgba(0,0,0,0.25)",
                border: "1px solid rgba(255,255,255,0.06)",
                color: "#fff",
                fontSize: "0.75rem",
                outline: "none"
              }}
            />
            <button
              type="submit"
              disabled={loadingAction || !remQuestion.trim() || session.rem_consults_left <= 0}
              style={{
                padding: "0 14px",
                borderRadius: 6,
                background: themePrimary,
                color: "#0a0f1d",
                border: "none",
                fontSize: "0.75rem",
                fontWeight: 700,
                cursor: "pointer"
              }}
            >
              Send
            </button>
          </form>
        </div>
      )}

      {/* Gavel / Scale Styles */}
      <style jsx global>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes scale-in {
          0% { transform: scale(0.3) rotate(-10deg); opacity: 0; }
          100% { transform: scale(1.1) rotate(0deg); opacity: 1; }
        }
        @keyframes fade-out {
          0% { opacity: 1; }
          80% { opacity: 1; }
          100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
