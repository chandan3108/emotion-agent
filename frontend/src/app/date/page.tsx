"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { sendChat, getXP, getSchedule, getIdentity, getPlans, getMemory, bookmarkMemory, resetUser, endActiveDate, type ChatResponse, type XPData } from "@/lib/gameApi";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface DateSession {
  id: string;
  activity: string;
  location: string;
  startTime: string;
  endTime?: string;
  messages: Message[];
  active: boolean;
}

const SESSIONS_STORAGE_KEY = "rem_date_sessions";

function loadSessions(): DateSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(SESSIONS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveSessions(sessions: DateSession[]) {
  try {
    localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions));
  } catch {}
}

export default function DatePage() {
  const [sessions, setSessions] = useState<DateSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [xp, setXp] = useState<XPData | null>(null);
  const [currentActivity, setCurrentActivity] = useState<string | null>(null);
  const [roleplay, setRoleplay] = useState<{ active: boolean; activity: string; location: string } | null>(null);
  const [futurePlans, setFuturePlans] = useState<any[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /* Hydrate sessions from localStorage AFTER mount */
  useEffect(() => {
    setSessions(loadSessions());
    setMounted(true);
  }, []);

  /* Save to localStorage whenever sessions change */
  useEffect(() => {
    if (mounted) {
      saveSessions(sessions);
    }
  }, [sessions, mounted]);

  const getPresetClass = useCallback(() => {
    if (!roleplay || !roleplay.active) return "";
    const act = (roleplay.activity || "").toLowerCase();
    const loc = (roleplay.location || "").toLowerCase();
    
    if (act.includes("bbq") || loc.includes("bbq") || act.includes("barbecue") || loc.includes("barbecue")) {
      return "preset-crimson";
    } else if (act.includes("cafe") || loc.includes("cafe") || act.includes("coffee") || loc.includes("coffee")) {
      return "preset-amber";
    } else if (act.includes("movie") || loc.includes("movie") || act.includes("theater") || loc.includes("theater")) {
      return "preset-indigo";
    } else if (act.includes("study") || loc.includes("study") || act.includes("library") || loc.includes("library") || act.includes("class")) {
      return "preset-emerald";
    } else {
      return "preset-violet";
    }
  }, [roleplay]);

  useEffect(() => {
    const themeClass = getPresetClass();
    document.body.classList.remove(
      "preset-amber",
      "preset-crimson",
      "preset-indigo",
      "preset-emerald",
      "preset-violet"
    );
    if (themeClass && themeClass.startsWith("preset-")) {
      document.body.classList.add(themeClass);
    }
    return () => {
      document.body.classList.remove(
        "preset-amber",
        "preset-crimson",
        "preset-indigo",
        "preset-emerald",
        "preset-violet"
      );
    };
  }, [getPresetClass]);

  const fetchPlansAndSchedule = useCallback(() => {
    getSchedule()
      .then((res: any) => {
        if (res) {
          setCurrentActivity(prev => {
            const nextAct = res.current_activity || null;
            return prev === nextAct ? prev : nextAct;
          });
          if (res.future_plans) {
            setFuturePlans(res.future_plans);
          }
          if (res.is_roleplay_mode !== undefined) {
            setRoleplay(prev => {
              const active = res.is_roleplay_mode;
              const activity = res.current_activity || "";
              const location = res.location || "hanging out";
              if (prev && prev.active === active && prev.activity === activity && prev.location === location) {
                return prev;
              }
              return { active, activity, location };
            });
          }
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    getXP().then(setXp).catch(() => {});
    fetchPlansAndSchedule();
    
    // Poll schedule state every 20 seconds
    const interval = setInterval(() => {
      fetchPlansAndSchedule();
    }, 20000);
    return () => clearInterval(interval);
  }, [fetchPlansAndSchedule]);

  /* Handle active session creation or auto-expiration based on roleplay state */
  useEffect(() => {
    if (!mounted || roleplay === null) return;
    
    if (roleplay.active) {
      setSessions(prev => {
        const activeIdx = prev.findIndex(s => s.active);
        if (activeIdx !== -1) {
          const currentActive = prev[activeIdx];
          // If the activity or location changed, deactivate old one and start new one
          if (currentActive.activity !== roleplay.activity || currentActive.location !== roleplay.location) {
            const updated = prev.map(s => s.active ? { ...s, active: false, endTime: new Date().toISOString() } : s);
            const newSession: DateSession = {
              id: `date_${Date.now()}`,
              activity: roleplay.activity,
              location: roleplay.location,
              startTime: new Date().toISOString(),
              messages: [],
              active: true
            };
            return [newSession, ...updated];
          }
          return prev;
        } else {
          // No active session, create a new one
          const newSession: DateSession = {
            id: `date_${Date.now()}`,
            activity: roleplay.activity,
            location: roleplay.location,
            startTime: new Date().toISOString(),
            messages: [],
            active: true
          };
          return [newSession, ...prev];
        }
      });
    } else {
      // Auto-expire any active session if roleplay ended
      setSessions(prev => {
        const hasActive = prev.some(s => s.active);
        if (hasActive) {
          return prev.map(s => s.active ? { ...s, active: false, endTime: new Date().toISOString() } : s);
        }
        return prev;
      });
    }
  }, [roleplay, mounted]);

  const activeSession = sessions.find(s => s.active);
  const selectedSession = roleplay?.active 
    ? activeSession 
    : (sessions.find(s => s.id === selectedSessionId) || sessions[0] || null);

  const displayedMessages = selectedSession ? selectedSession.messages : [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayedMessages]);

  const sendMessageToServer = async (textToSend: string) => {
    if (loading || !textToSend.trim() || !roleplay?.active) return;

    const userMsg: Message = {
      role: "user",
      content: textToSend,
      timestamp: new Date().toISOString(),
    };

    // Append to active session messages
    setSessions(prev => 
      prev.map(s => s.active ? { ...s, messages: [...s.messages, userMsg] } : s)
    );
    setInput("");
    setLoading(true);

    try {
      const response = await sendChat({ 
        message: textToSend,
        session_id: selectedSession?.id || undefined
      });
      if (response && response.reply) {
        const assistantMsg: Message = {
          role: "assistant",
          content: response.reply,
          timestamp: new Date().toISOString(),
        };
        
        // Append reply to active session messages
        setSessions(prev => 
          prev.map(s => s.active ? { ...s, messages: [...s.messages, assistantMsg] } : s)
        );
        
        // Update local metrics
        if (response.current_xp !== undefined && xp) {
          setXp((prevXP) => prevXP ? { ...prevXP, total_xp: response.current_xp } : null);
        }
        if (response.roleplay) {
          setRoleplay(response.roleplay);
        }
      }
    } catch (err: any) {
      setToast(`Error: ${err.message || err}`);
      setTimeout(() => setToast(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessageToServer(input);
  };

  const handleBookmarkMessage = async (content: string, role: string) => {
    try {
      setToast("Sending to Memory Vault...");
      const res = await bookmarkMemory(content, role);
      if (res.success) {
        setToast("Rem will remember this!");
      } else {
        setToast("Failed to save memory.");
      }
    } catch (err: any) {
      setToast(`Error: ${err.message || err}`);
    } finally {
      setTimeout(() => setToast(null), 3000);
    }
  };

  const handleEndDate = async () => {
    try {
      setToast("Ending date early...");
      const res = await endActiveDate();
      if (res.success) {
        setToast("Date ended. Relational impact applied.");
        // Mark active session as inactive
        setSessions(prev => 
          prev.map(s => s.active ? { ...s, active: false, endTime: new Date().toISOString() } : s)
        );
        fetchPlansAndSchedule();
      } else {
        setToast("Failed to end date.");
      }
    } catch (err: any) {
      setToast(`Error: ${err.message || err}`);
    } finally {
      setTimeout(() => setToast(null), 3000);
    }
  };

  const getActionChips = () => {
    const act = (roleplay?.activity || "").toLowerCase();
    const loc = (roleplay?.location || "").toLowerCase();
    if (act.includes("bbq") || loc.includes("bbq") || act.includes("barbecue") || loc.includes("barbecue")) {
      return ["*grills brisket*", "*passes tongs*", "*takes a bite*", "*cheers drinks*", "*pours water*"];
    } else if (act.includes("cafe") || loc.includes("cafe") || act.includes("coffee") || loc.includes("coffee")) {
      return ["*sips coffee*", "*eats pastry*", "*looks out window*", "*adds sugar*", "*laughs softly*"];
    } else if (act.includes("movie") || loc.includes("movie") || act.includes("theater") || loc.includes("theater")) {
      return ["*shares popcorn*", "*whispers comment*", "*gasps at scene*", "*laughs out loud*", "*checks phone*"];
    } else if (act.includes("study") || loc.includes("study") || act.includes("library") || loc.includes("library") || act.includes("class")) {
      return ["*turns page*", "*whispers question*", "*shares notes*", "*points to diagram*", "*stretches*"];
    }
    return ["*smiles*", "*nods*", "*looks around*", "*laughs*", "*waves*"];
  };

  const getPresetGradients = (actStr: string, locStr: string) => {
    const act = actStr.toLowerCase();
    const loc = locStr.toLowerCase();
    
    if (act.includes("bbq") || loc.includes("bbq") || act.includes("barbecue") || loc.includes("barbecue")) {
      return "radial-gradient(circle at center, rgba(239, 68, 68, 0.18) 0%, rgba(5,5,8,1) 85%)";
    } else if (act.includes("cafe") || loc.includes("cafe") || act.includes("coffee") || loc.includes("coffee")) {
      return "radial-gradient(circle at center, rgba(245, 158, 11, 0.15) 0%, rgba(5,5,8,1) 85%)";
    } else if (act.includes("movie") || loc.includes("movie") || act.includes("theater") || loc.includes("theater")) {
      return "radial-gradient(circle at center, rgba(99, 102, 241, 0.15) 0%, rgba(5,5,8,1) 85%)";
    } else if (act.includes("study") || loc.includes("study") || act.includes("library") || loc.includes("library") || act.includes("class")) {
      return "radial-gradient(circle at center, rgba(16, 185, 129, 0.15) 0%, rgba(5,5,8,1) 85%)";
    }
    return "radial-gradient(circle at center, rgba(167, 139, 250, 0.15) 0%, rgba(5,5,8,1) 85%)";
  };

  const parseDialogue = (text: string) => {
    const parts = [];
    const regex = /\*([^*]+)\*/g;
    let lastIndex = 0;
    let match;
    
    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ text: text.substring(lastIndex, match.index), isAction: false });
      }
      parts.push({ text: match[1], isAction: true });
      lastIndex = regex.lastIndex;
    }
    
    if (lastIndex < text.length) {
      parts.push({ text: text.substring(lastIndex), isAction: false });
    }
    
    return parts.map((p, idx) => (
      <span key={idx} style={{ 
        fontStyle: p.isAction ? "italic" : "normal", 
        color: p.isAction ? "var(--text-accent)" : "#ffffff",
        textShadow: p.isAction ? "0 0 8px rgba(201, 176, 255, 0.4)" : "none",
        fontWeight: p.isAction ? 500 : 400
      }}>
        {p.isAction ? `*${p.text}*` : p.text}
      </span>
    ));
  };

  const assistantMessages = displayedMessages.filter(m => m.role === "assistant");
  const lastReply = assistantMessages.length > 0 
    ? assistantMessages[assistantMessages.length - 1].content 
    : "Hey, let's spend some time together...";

  // Get upcoming plans
  const upcomingPlans = futurePlans.filter(p => {
    try {
      const todayStr = new Date().toISOString().split("T")[0];
      return p.date >= todayStr;
    } catch { return false; }
  });
  upcomingPlans.sort((a, b) => {
    if (a.date !== b.date) return a.date.localeCompare(b.date);
    return a.start.localeCompare(b.start);
  });
  const nextPlan = upcomingPlans[0] || null;

  // Format Date Helper
  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch { return isoStr; }
  };

  if (!mounted) return null;

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        background: "var(--bg-void)",
        color: "var(--text-primary)",
        overflow: "hidden"
      }}
    >
      {/* LEFT PANEL: Glassmorphic History Log OR Past Dates Records */}
      <div
        style={{
          width: "35%",
          minWidth: 320,
          borderRight: "1px solid var(--border-subtle)",
          background: "rgba(8, 8, 15, 0.6)",
          backdropFilter: "blur(20px)",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          zIndex: 5
        }}
      >
        {roleplay?.active ? (
          /* ACTIVE MODE HEADER & CHAT LOG */
          <>
            <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-subtle)" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                📖 Current Date Dialogue
              </h3>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
                Review dialogue history for this active session
              </p>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                gap: 14
              }}
            >
              {displayedMessages.length === 0 ? (
                <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: "0.875rem", fontStyle: "italic" }}>
                  Start texting to build history...
                </div>
              ) : (
                displayedMessages.map((msg, i) => (
                  <div
                    key={i}
                    className="group"
                    style={{
                      alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                      maxWidth: "85%",
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      justifyContent: msg.role === "user" ? "flex-end" : "flex-start"
                    }}
                  >
                    {msg.role === "user" && (
                      <button
                        onClick={() => handleBookmarkMessage(msg.content, msg.role)}
                        style={{
                          background: "transparent",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "0.8125rem",
                          opacity: 0.15,
                          transition: "all 0.2s ease",
                          padding: 4
                        }}
                        className="bookmark-btn"
                        title="Remember this message"
                      >
                        🔖
                      </button>
                    )}
                    <div
                      style={{
                        background: msg.role === "user" ? "linear-gradient(135deg, rgba(124, 92, 231, 0.15), rgba(151, 117, 250, 0.08))" : "rgba(255, 255, 255, 0.02)",
                        border: msg.role === "user" ? "1px solid rgba(151, 117, 250, 0.12)" : "1px solid var(--border-subtle)",
                        borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
                        padding: "10px 14px",
                        fontSize: "0.8125rem",
                        lineHeight: 1.5,
                        color: "#fff"
                      }}
                    >
                      {parseDialogue(msg.content)}
                    </div>
                    {msg.role === "assistant" && (
                      <button
                        onClick={() => handleBookmarkMessage(msg.content, msg.role)}
                        style={{
                          background: "transparent",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "0.8125rem",
                          opacity: 0.15,
                          transition: "all 0.2s ease",
                          padding: 4
                        }}
                        className="bookmark-btn"
                        title="Remember this message"
                      >
                        🔖
                      </button>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </>
        ) : (
          /* INACTIVE MODE: PAST DATES LISTING OR ARCHIVED DIALOGUE */
          selectedSessionId ? (
            <>
              <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-subtle)" }}>
                <button
                  onClick={() => setSelectedSessionId(null)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--accent-primary)",
                    fontSize: "0.75rem",
                    cursor: "pointer",
                    padding: 0,
                    marginBottom: 8,
                    display: "block",
                    fontWeight: 600
                  }}
                >
                  ← Back to Records List
                </button>
                <h3 style={{ fontSize: "1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                  📖 Archived Date Dialogue
                </h3>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
                  Location: {selectedSession?.location} ({selectedSession?.activity})
                </p>
              </div>

              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: "24px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 14
                }}
              >
                {displayedMessages.length === 0 ? (
                  <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: "0.875rem", fontStyle: "italic" }}>
                    No messages recorded for this date.
                  </div>
                ) : (
                  displayedMessages.map((msg, i) => (
                    <div
                      key={i}
                      style={{
                        alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                        maxWidth: "85%",
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        justifyContent: msg.role === "user" ? "flex-end" : "flex-start"
                      }}
                    >
                      <div
                        style={{
                          background: msg.role === "user" ? "linear-gradient(135deg, rgba(124, 92, 231, 0.15), rgba(151, 117, 250, 0.08))" : "rgba(255, 255, 255, 0.02)",
                          border: msg.role === "user" ? "1px solid rgba(151, 117, 250, 0.12)" : "1px solid var(--border-subtle)",
                          borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
                          padding: "10px 14px",
                          fontSize: "0.8125rem",
                          lineHeight: 1.5,
                          color: "#fff"
                        }}
                      >
                        {parseDialogue(msg.content)}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <>
              <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-subtle)" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                  📚 Past Date Records
                </h3>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
                  Browse diaries of your past sessions with Rem
                </p>
              </div>

              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 10
                }}
              >
                {sessions.length === 0 ? (
                  <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center", color: "var(--text-muted)", fontSize: "0.875rem", fontStyle: "italic", textAlign: "center", padding: 20 }}>
                    No past dates recorded yet.<br />Go schedule a date to begin!
                  </div>
                ) : (
                  sessions.map((sess) => {
                    const isSelected = selectedSession?.id === sess.id;
                    return (
                      <div
                        key={sess.id}
                        onClick={() => setSelectedSessionId(sess.id)}
                        style={{
                          padding: "12px 16px",
                          borderRadius: 12,
                          background: isSelected ? "rgba(151, 117, 250, 0.08)" : "rgba(255, 255, 255, 0.02)",
                          border: isSelected ? "1px solid rgba(151, 117, 250, 0.3)" : "1px solid var(--border-subtle)",
                          cursor: "pointer",
                          transition: "all 0.2s ease"
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                          <span style={{ fontSize: "0.8125rem", fontWeight: 600, color: "#fff" }}>
                            📍 {sess.location}
                          </span>
                          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                            {formatDate(sess.startTime)}
                          </span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                            {sess.activity}
                          </span>
                          <span style={{ fontSize: "0.6875rem", background: "rgba(255,255,255,0.05)", padding: "2px 6px", borderRadius: 4, color: "var(--text-muted)" }}>
                            {sess.messages.length} lines
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </>
          )
        )}
      </div>

      {/* RIGHT PANEL: Immersive VN overlay OR Past Date Reader */}
      <div
        style={{
          flex: 1,
          position: "relative",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: "center",
          background: selectedSession 
            ? getPresetGradients(selectedSession.activity, selectedSession.location) 
            : "radial-gradient(circle at center, rgba(167, 139, 250, 0.08) 0%, rgba(5,5,8,1) 85%)",
          padding: "30px 40px",
          overflow: "hidden"
        }}
      >
        {roleplay?.active ? (
          /* ACTIVE ROLEPLAY VN OVERLAY */
          <>
            {/* Top location & end date banner */}
            <div 
              style={{ 
                width: "100%",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                zIndex: 10
              }}
            >
              <div 
                style={{ 
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--border-subtle)",
                  backdropFilter: "blur(10px)",
                  padding: "8px 16px",
                  borderRadius: 12,
                  fontSize: "0.8125rem",
                  color: "var(--text-secondary)",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  boxShadow: "0 4px 20px rgba(0,0,0,0.5)"
                }}
              >
                <span>📍</span>
                <span>{roleplay.location} — {roleplay.activity}</span>
              </div>

              <button
                onClick={handleEndDate}
                style={{
                  background: "rgba(239, 68, 68, 0.12)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  color: "#ff6b6b",
                  padding: "8px 16px",
                  borderRadius: 12,
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  cursor: "pointer",
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                  transition: "all 0.2s ease",
                  boxShadow: "0 4px 15px rgba(239, 68, 68, 0.1)"
                }}
                className="end-date-btn"
                title="End this date session early (penalizes relationship)"
              >
                🔴 End Date Early
              </button>
            </div>

            {/* Central Emoting/Breathing Orb */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
              <div 
                className="date-breathing-orb"
                style={{ 
                  width: 140, 
                  height: 140, 
                  borderRadius: "50%",
                  background: "radial-gradient(circle, var(--accent-primary) 0%, var(--accent-secondary) 100%)",
                  boxShadow: "0 0 60px var(--accent-glow)",
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}
              >
                <div 
                  style={{
                    position: "absolute",
                    inset: 6,
                    borderRadius: "50%",
                    background: "var(--bg-primary)",
                    opacity: 0.95,
                  }}
                />
                {/* Core breathing center */}
                <div 
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: "50%",
                    background: "var(--accent-primary)",
                    boxShadow: "0 0 20px var(--accent-primary)",
                  }}
                />
              </div>
              <span style={{ fontSize: "0.6875rem", letterSpacing: "0.15em", textTransform: "uppercase", color: "var(--text-muted)" }}>
                Rem's Presence
              </span>
            </div>

            {/* Choice chips & Bottom Dialog Box */}
            <div style={{ width: "100%", maxWidth: 650, zIndex: 10 }}>
              {/* Centered Choice Chips */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 10,
                  justifyContent: "center",
                  marginBottom: 16
                }}
              >
                {getActionChips().map((chip, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => sendMessageToServer(chip)}
                    disabled={loading}
                    style={{
                      background: "rgba(10, 10, 18, 0.8)",
                      border: "1px solid var(--border-glow)",
                      color: "var(--text-primary)",
                      padding: "8px 18px",
                      borderRadius: "20px",
                      cursor: "pointer",
                      fontSize: "0.8125rem",
                      transition: "all 0.2s var(--ease-spring)",
                      boxShadow: "0 4px 15px rgba(0,0,0,0.3)"
                    }}
                    className="action-chip-date"
                  >
                    {chip}
                  </button>
                ))}
              </div>

              {/* Dialogue Box */}
              <div
                style={{
                  background: "rgba(10, 10, 18, 0.9)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "16px",
                  padding: "24px 28px",
                  boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
                  backdropFilter: "blur(20px)",
                  position: "relative",
                  minHeight: 110,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center"
                }}
              >
                {/* Name Tag */}
                <div
                  style={{
                    position: "absolute",
                    top: -15,
                    left: 20,
                    background: "var(--accent-primary)",
                    color: "#fff",
                    fontWeight: 700,
                    fontSize: "0.8125rem",
                    padding: "4px 18px",
                    borderRadius: 8,
                    boxShadow: "0 4px 10px rgba(151,117,250,0.3)",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase"
                  }}
                >
                  Rem
                </div>
                
                {/* Dialogue Text */}
                <div style={{ fontSize: "0.9375rem", lineHeight: 1.7, color: "#fff" }}>
                  {loading ? (
                    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                      <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Rem is thinking...</span>
                    </div>
                  ) : (
                    parseDialogue(lastReply)
                  )}
                </div>
              </div>

              {/* Text Input Bar */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                style={{ 
                  display: "flex", 
                  gap: 10, 
                  marginTop: 14,
                  width: "100%"
                }}
              >
                <input
                  ref={inputRef}
                  type="text"
                  className="input-field"
                  placeholder="Type your reaction..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                  autoComplete="off"
                  style={{
                    flex: 1,
                    background: "rgba(10, 10, 18, 0.8)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 12,
                    padding: "12px 20px",
                    color: "#fff"
                  }}
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  style={{
                    background: "var(--accent-primary)",
                    color: "#fff",
                    border: "none",
                    borderRadius: 12,
                    padding: "0 24px",
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "opacity 0.2s ease"
                  }}
                >
                  Send
                </button>
              </form>
            </div>
          </>
        ) : selectedSession ? (
          /* INACTIVE MODE: PAST DATE VIEWER */
          <>
            <div style={{ alignSelf: "flex-start" }}>
              <div 
                style={{ 
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--border-subtle)",
                  backdropFilter: "blur(10px)",
                  padding: "8px 16px",
                  borderRadius: 12,
                  fontSize: "0.8125rem",
                  color: "var(--text-secondary)",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <span>📅 Date Completed</span>
              </div>
            </div>

            {/* Central summary information */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", gap: 12 }}>
              <div 
                style={{ 
                  width: 90, 
                  height: 90, 
                  borderRadius: "50%",
                  background: "radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.02) 100%)",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "2rem",
                  marginBottom: 12
                }}
              >
                💾
              </div>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#fff" }}>
                Date Archive: {selectedSession.location}
              </h2>
              <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", maxWidth: 380, lineHeight: 1.6 }}>
                You went out with Rem to <strong>{selectedSession.activity}</strong> at <strong>{selectedSession.location}</strong> on {formatDate(selectedSession.startTime)}.
              </p>
              {selectedSession.endTime && (
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  Duration: {Math.max(1, Math.round((new Date(selectedSession.endTime).getTime() - new Date(selectedSession.startTime).getTime()) / 60000))} min
                </span>
              )}
            </div>

            {/* Bottom Actions */}
            <div style={{ width: "100%", maxWidth: 650, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                Browse their full dialog history on the left panel.
              </p>
              
              <button
                onClick={() => window.location.href = "/?drawer=plans"}
                style={{
                  background: "var(--accent-primary)",
                  color: "#050508",
                  border: "none",
                  borderRadius: 12,
                  padding: "12px 24px",
                  fontWeight: 700,
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                  boxShadow: "0 4px 15px var(--accent-glow)",
                  transition: "all 0.2s ease"
                }}
              >
                📅 Schedule a New Date
              </button>
            </div>
          </>
        ) : (
          /* INACTIVE MODE: EMPTY STATE */
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              flex: 1,
              maxWidth: 450,
              textAlign: "center"
            }}
          >
            {nextPlan ? (
              <>
                <div 
                  className="date-breathing-orb"
                  style={{ 
                    width: 80, 
                    height: 80, 
                    borderRadius: "50%",
                    background: "radial-gradient(circle, var(--accent-primary) 0%, var(--accent-secondary) 100%)",
                    boxShadow: "0 0 40px var(--accent-glow)",
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: 24,
                    opacity: 0.6
                  }}
                >
                  <div style={{ position: "absolute", inset: 4, borderRadius: "50%", background: "var(--bg-primary)" }} />
                  <span style={{ fontSize: "1.25rem", zIndex: 2 }}>⏳</span>
                </div>
                <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#fff", marginBottom: 12 }}>
                  ⏳ Upcoming Date Scheduled
                </h3>
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 16 }}>
                  You have a date scheduled with Rem:
                </p>
                <div style={{
                  background: "rgba(151, 117, 250, 0.05)",
                  border: "1px solid rgba(151, 117, 250, 0.15)",
                  borderRadius: 12,
                  padding: "16px 20px",
                  textAlign: "left",
                  width: "100%",
                  marginBottom: 24,
                  display: "flex",
                  flexDirection: "column",
                  gap: 8
                }}>
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                    <strong>Activity:</strong> {nextPlan.activity}
                  </div>
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                    <strong>Location:</strong> {nextPlan.location}
                  </div>
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                    <strong>Time:</strong> {nextPlan.date} ({nextPlan.start} - {nextPlan.end})
                  </div>
                </div>
                <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", lineHeight: 1.5, marginBottom: 24 }}>
                  Date Mode will automatically activate when this scheduled time is reached. In the meantime, you can text Rem in standard mode.
                </p>
              </>
            ) : (
              <>
                <div className="rem-orb" style={{ width: 80, height: 80, marginBottom: 24 }} />
                <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#fff", marginBottom: 12 }}>
                  🎭 No Active Date Mode
                </h3>
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 24 }}>
                  There is currently no active scheduled date. Go to the <strong>Chat page</strong>, open the <strong>plans drawer 📅</strong>, and schedule a date with Rem to trigger the immersive visual novel mode.
                </p>
              </>
            )}
            <button
              onClick={() => window.location.href = "/?drawer=plans"}
              style={{
                background: "var(--accent-primary)",
                color: "#050508",
                border: "none",
                borderRadius: 8,
                padding: "12px 24px",
                fontWeight: 700,
                fontSize: "0.8125rem",
                cursor: "pointer",
                boxShadow: "0 4px 15px var(--accent-glow)"
              }}
            >
              Go to Plans Drawer
            </button>
          </div>
        )}
      </div>

      {/* Toast popup */}
      {toast && <div className="xp-toast">{toast}</div>}
    </div>
  );
}
