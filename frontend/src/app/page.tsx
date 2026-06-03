"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { sendChat, getXP, getSchedule, getIdentity, getPlans, addPlan, deletePlan, getMemory, bookmarkMemory, resetUser, getMessages, type ChatResponse, type XPData } from "@/lib/gameApi";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const STORAGE_KEY = "rem_chat_messages";

function loadMessages(): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveMessages(msgs: Message[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(msgs)); } catch {}
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [xp, setXp] = useState<XPData | null>(null);
  const [currentActivity, setCurrentActivity] = useState<string | null>(null);
  const [hurt, setHurt] = useState(0.0);
  const [anger, setAnger] = useState(0.0);
  const [toast, setToast] = useState<string | null>(null);
  const [activeRankUp, setActiveRankUp] = useState<{
    from_rank: number;
    to_rank: number;
    from_phase: string;
    to_phase: string;
    unlocks: string[];
  } | null>(null);
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Plans & roleplay states
  const [roleplay, setRoleplay] = useState<{ active: boolean; activity: string; location: string } | null>(null);
  const [scheduleList, setScheduleList] = useState<any[]>([]);
  const [futurePlans, setFuturePlans] = useState<any[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [newPlanDate, setNewPlanDate] = useState(() => {
    return new Date(Date.now() + 86400000).toISOString().split('T')[0];
  });
  const [newPlanStart, setNewPlanStart] = useState("15:00");
  const [newPlanEnd, setNewPlanEnd] = useState("17:00");
  const [newPlanActivity, setNewPlanActivity] = useState("");
  const [newPlanLocation, setNewPlanLocation] = useState("");
  const [planMessage, setPlanMessage] = useState("");

  // Drawer and memory states
  const [drawerTab, setDrawerTab] = useState<'plans' | 'vault'>('plans');
  const [memoryData, setMemoryData] = useState<any>(null);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [memoryQuery, setMemoryQuery] = useState("");
  const [showDateOverlay, setShowDateOverlay] = useState(true);

  const fetchMemoryData = useCallback(() => {
    setMemoryLoading(true);
    getMemory()
      .then((res: any) => {
        setMemoryData(res);
      })
      .catch((err: any) => {
        console.error("Failed to load memories:", err);
      })
      .finally(() => {
        setMemoryLoading(false);
      });
  }, []);

  const getFilteredFacts = () => {
    if (!memoryData?.identity?.facts) return [];
    const q = memoryQuery.toLowerCase().trim();
    if (!q) return memoryData.identity.facts;
    return memoryData.identity.facts.filter((f: any) => f.fact.toLowerCase().includes(q));
  };

  const getFilteredEpisodic = () => {
    if (!memoryData?.episodic?.entries) return [];
    const entries = memoryData.episodic.entries.filter((e: any) => e.event_type !== "explicit_bookmark");
    const q = memoryQuery.toLowerCase().trim();
    if (!q) return entries;
    return entries.filter((e: any) => e.content.toLowerCase().includes(q) || e.event_type.toLowerCase().includes(q));
  };

  const getFilteredBookmarks = () => {
    if (!memoryData?.episodic?.entries) return [];
    const entries = memoryData.episodic.entries.filter((e: any) => e.event_type === "explicit_bookmark");
    const q = memoryQuery.toLowerCase().trim();
    if (!q) return entries;
    return entries.filter((e: any) => e.content.toLowerCase().includes(q));
  };

  const getFilteredStm = () => {
    if (!memoryData?.stm?.entries) return [];
    const q = memoryQuery.toLowerCase().trim();
    if (!q) return memoryData.stm.entries;
    return memoryData.stm.entries.filter((s: any) => s.content.toLowerCase().includes(q) || s.topic.toLowerCase().includes(q));
  };

  const openDrawer = (tab: 'plans' | 'vault') => {
    setDrawerTab(tab);
    setDrawerOpen(true);
    if (tab === 'vault') {
      fetchMemoryData();
    }
  };

  const handleBookmarkMessage = async (content: string, role: string) => {
    try {
      setToast("Sending to Memory Vault...");
      const res = await bookmarkMemory(content, role);
      if (res.success) {
        setToast("Rem will remember this!");
        if (drawerOpen && drawerTab === 'vault') {
          fetchMemoryData();
        }
      } else {
        setToast("Failed to save memory.");
      }
    } catch (err: any) {
      setToast(`Error: ${err.message || err}`);
    } finally {
      setTimeout(() => setToast(null), 3000);
    }
  };

  const fetchPlansAndSchedule = useCallback(() => {
    getSchedule()
      .then((res: any) => {
        if (res) {
          setCurrentActivity(prev => {
            const nextAct = res.current_activity || null;
            return prev === nextAct ? prev : nextAct;
          });
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
          if (res.schedule) {
            setScheduleList(prev => {
              if (JSON.stringify(prev) === JSON.stringify(res.schedule)) return prev;
              return res.schedule;
            });
          }
          if (res.future_plans) {
            setFuturePlans(prev => {
              if (JSON.stringify(prev) === JSON.stringify(res.future_plans)) return prev;
              return res.future_plans;
            });
          }
        }
      })
      .catch(() => {});
  }, []);

  const fetchEmotions = useCallback(() => {
    getIdentity()
      .then((res: any) => {
        if (res && res.relationship) {
          if (res.relationship.hurt !== undefined) {
            setHurt(prev => prev === res.relationship.hurt ? prev : res.relationship.hurt);
          }
          if (res.relationship.anger !== undefined) {
            setAnger(prev => prev === res.relationship.anger ? prev : res.relationship.anger);
          }
        }
      })
      .catch(() => {});
  }, []);

  /* Hydrate messages from localStorage AFTER mount (prevents SSR mismatch) */
  useEffect(() => {
    const saved = loadMessages();
    setMessages(saved);
    setMounted(true);

    getMessages()
      .then((res) => {
        if (res && res.messages && res.messages.length > 0) {
          setMessages(res.messages);
          saveMessages(res.messages);
        }
      })
      .catch((err) => {
        console.error("Failed to sync chat messages on mount:", err);
      });
    
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const initialDrawer = params.get("drawer");
      if (initialDrawer === "plans" || initialDrawer === "vault") {
        openDrawer(initialDrawer as "plans" | "vault");
        // Clear query parameters from URL without reloading
        const newUrl = window.location.pathname;
        window.history.replaceState({}, "", newUrl);
      }
    }
  }, []);

  /* Save to localStorage whenever messages change (skip initial mount) */
  const saveRef = useRef(false);
  useEffect(() => {
    if (saveRef.current) {
      saveMessages(messages);
    } else {
      saveRef.current = true;
    }
  }, [messages]);

  useEffect(() => {
    const handleOpenDrawer = (e: any) => {
      if (e.detail) {
        openDrawer(e.detail);
      }
    };
    window.addEventListener("open-plans-drawer", handleOpenDrawer);
    return () => window.removeEventListener("open-plans-drawer", handleOpenDrawer);
  }, []);

  useEffect(() => {
    getXP().then(setXp).catch(() => {});
    fetchPlansAndSchedule();
    fetchEmotions();
    
    // Poll schedule and emotions every 30 seconds
    const interval = setInterval(() => {
      fetchPlansAndSchedule();
      fetchEmotions();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchPlansAndSchedule, fetchEmotions]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [loading]);

  const clearHistory = useCallback(async () => {
    if (window.confirm("Are you sure you want to completely reset Rem's memory and chat history? This cannot be undone.")) {
      try {
        setMessages([]);
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem("rem_date_sessions");
        setToast("Resetting persona...");
        await resetUser();
        setXp(null);
        setRoleplay(null);
        setScheduleList([]);
        setFuturePlans([]);
        setHurt(0.0);
        setAnger(0.0);
        setToast("Rem has been reset to a fresh start!");
      } catch (err: any) {
        setToast(`Error resetting: ${err.message || err}`);
      } finally {
        setTimeout(() => setToast(null), 3000);
      }
    }
  }, []);

  const isGlitched = hurt > 0.4 || anger > 0.4;

  const getPresetClass = useCallback(() => {
    if (isGlitched) return "crimson-glitch";
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
  }, [roleplay, isGlitched]);

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

  const sendMessageToServer = async (text: string) => {
    if (!text || loading) return;

    const userMsg: Message = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res: ChatResponse = await sendChat({ message: text });

      // Simulate Rem's typing delay client-side (server sends the delay value)
      // This prevents Vercel function timeouts from server-side sleeping.
      const typingDelay = res.typing_delay_ms ?? 1200;
      await new Promise((resolve) => setTimeout(resolve, typingDelay));

      if (res.reply_parts && res.reply_parts.length > 1) {
        for (let i = 0; i < res.reply_parts.length; i++) {
          const partMsg: Message = {
            role: "assistant",
            content: res.reply_parts[i],
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, partMsg]);
          if (i < res.reply_parts.length - 1) {
            setLoading(true);
            await new Promise((resolve) => setTimeout(resolve, 800 + Math.random() * 600));
          }
        }
      } else {
        const remMsg: Message = {
          role: "assistant",
          content: res.reply,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, remMsg]);
      }

      if (res.xp_delta && res.xp_delta > 0) {
        setToast(`+${res.xp_delta} XP`);
        setTimeout(() => setToast(null), 4000);
      }

      if (res.phase_transition) {
        const unlockText = res.new_unlocks
          ? `\n${Object.keys(res.new_unlocks).join(" · ")}`
          : "";
        setToast(
          `◈ ${res.phase_transition.from} → ${res.phase_transition.to}${unlockText}`
        );
        setTimeout(() => setToast(null), 5000);
      }

      if (res.rank_transition) {
        setActiveRankUp(res.rank_transition);
      }

      if (res.hurt !== undefined) setHurt(res.hurt);
      if (res.anger !== undefined) setAnger(res.anger);
      if (res.hurt === undefined || res.anger === undefined) {
        fetchEmotions();
      }

      if (res.roleplay) {
        setRoleplay(res.roleplay);
      }
      if (res.schedule) {
        setScheduleList(res.schedule);
      }
      if (res.future_plans) {
        setFuturePlans(res.future_plans);
      }

      getXP().then(setXp).catch(() => {});
      fetchPlansAndSchedule();
    } catch {
      // Restore input text so they don't lose their typed message on error
      setInput(text);
      const errMsg: Message = {
        role: "assistant",
        content: "⚠️ Message failed to send. Please check your connection or try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    await sendMessageToServer(text);
  };

  const handleSchedulePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlanActivity.trim() || !newPlanLocation.trim()) {
      setPlanMessage("Activity and Location are required.");
      return;
    }
    setPlanMessage("Scheduling...");
    try {
      const res = await addPlan({
        date: newPlanDate,
        start: newPlanStart,
        end: newPlanEnd,
        activity: newPlanActivity,
        location: newPlanLocation
      });
      if (res.success) {
        setPlanMessage("Plan scheduled successfully!");
        setNewPlanActivity("");
        setNewPlanLocation("");
        // Reload schedule and future plans
        fetchPlansAndSchedule();
      } else {
        setPlanMessage("Failed to schedule plan.");
      }
    } catch (err: any) {
      setPlanMessage(`Error: ${err.message || err}`);
    }
  };

  const handleDeletePlan = async (date: string, start: string, end: string) => {
    if (!confirm("Are you sure you want to cancel this plan?")) return;
    try {
      const res = await deletePlan(date, start, end);
      if (res.success) {
        fetchPlansAndSchedule();
      }
    } catch (err: any) {
      alert(`Failed to delete plan: ${err.message || err}`);
    }
  };

  const getActionChips = () => {
    if (!roleplay || !roleplay.active) return [];
    const act = (roleplay.activity || "").toLowerCase();
    const loc = (roleplay.location || "").toLowerCase();
    
    if (act.includes("bbq") || loc.includes("bbq") || act.includes("barbecue") || loc.includes("barbecue")) {
      return [
        "*passes the tongs*",
        "*grills some brisket*",
        "*tastes the food*",
        "*offers you a piece of meat*",
        "*pours a drink*"
      ];
    } else if (act.includes("cafe") || loc.includes("cafe") || act.includes("coffee") || loc.includes("coffee")) {
      return [
        "*takes a sip of coffee*",
        "*slides a pastry over*",
        "*looks out the window*",
        "*wipes a crumb off your cheek*",
        "*smiles over the cup*"
      ];
    } else if (act.includes("movie") || loc.includes("movie") || act.includes("theater") || loc.includes("theater")) {
      return [
        "*offers the popcorn bucket*",
        "*whispers in your ear*",
        "*leans closer to you*",
        "*points at the screen*",
        "*holds your hand in the dark*"
      ];
    } else if (act.includes("study") || loc.includes("study") || act.includes("library") || loc.includes("library") || act.includes("class")) {
      return [
        "*taps the notebook*",
        "*points at a hard question*",
        "*whispers quietly*",
        "*passes a sticky note*",
        "*yawns and stretches*"
      ];
    } else {
      return [
        "*smiles at you*",
        "*looks at you*",
        "*hands you a drink*",
        "*takes a walk together*",
        "*laughs at your joke*"
      ];
    }
  };

  const DateOverlayView = () => {
    // Get the last assistant message
    const assistantMessages = messages.filter(m => m.role === "assistant");
    const lastReply = assistantMessages.length > 0 ? assistantMessages[assistantMessages.length - 1].content : "Hey, let's spend some time together...";
    
    // Parse actions inside asterisks
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

    // Preset mapping for background/glows
    const getPresetGradients = () => {
      if (isGlitched) return "radial-gradient(circle at center, rgba(239, 68, 68, 0.25) 0%, rgba(5,5,8,1) 80%)";
      const act = (roleplay?.activity || "").toLowerCase();
      const loc = (roleplay?.location || "").toLowerCase();
      
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

    return (
      <div
        style={{
          flex: 1,
          position: "relative",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: "center",
          background: getPresetGradients(),
          padding: "30px 40px",
          overflow: "hidden",
          animation: "fadeIn 0.5s ease"
        }}
      >
        {/* Floating location card */}
        <div 
          style={{ 
            alignSelf: "flex-start",
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
          <span>{roleplay?.location} — {roleplay?.activity}</span>
        </div>

        {/* Central Emoting/Breathing Orb */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
          <div 
            className="date-breathing-orb"
            style={{ 
              width: 130, 
              height: 130, 
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
                opacity: 0.9,
              }}
            />
            {/* Little core dot */}
            <div 
              style={{
                width: 14,
                height: 14,
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
        <div style={{ width: "100%", maxWidth: 700, zIndex: 10 }}>
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
                  padding: "10px 20px",
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
              minHeight: 120,
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
            <div style={{ fontSize: "1rem", lineHeight: 1.7, color: "#fff" }}>
              {loading ? (
                <div style={{ display: "flex", gap: 6, alignItems: "center", height: 28 }}>
                  <span style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>Rem is thinking...</span>
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
      </div>
    );
  };

  return (
    <div 
      className={isGlitched ? "crimson-glitch" : ""}
      style={{ 
        display: "flex", 
        flexDirection: "column", 
        height: "100vh",
        background: "var(--bg-void)",
        color: "var(--text-primary)",
        transition: "all 0.5s ease"
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "14px 28px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "rgba(8, 8, 15, 0.8)",
          backdropFilter: "blur(20px)",
          zIndex: 5,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div 
            className={`rem-orb ${loading ? "typing" : ""}`} 
            style={{ 
              width: 36, 
              height: 36,
              "--orb-gradient": anger > 0.4 
                ? "conic-gradient(from 0deg, #ff4d4d, #ff0055, #ff4444, #ff4d4d)" 
                : hurt > 0.4 
                ? "conic-gradient(from 0deg, #4b6584, #778ca3, #a5b1c2, #4b6584)" 
                : xp && ["Steady", "Deep", "Bonded"].includes(xp.phase)
                ? "conic-gradient(from 0deg, #ff9f43, #ff6b6b, #feca57, #ff9f43)"
                : "conic-gradient(from 0deg, #7c5ce7, #e879f9, #74b9ff, #7c5ce7)",
              "--orb-speed": anger > 0.4 ? "1.5s" : hurt > 0.4 ? "7.0s" : xp && ["Steady", "Deep", "Bonded"].includes(xp.phase) ? "3.0s" : "4.5s"
            } as React.CSSProperties} 
          />
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <h2
                style={{
                  fontSize: "0.9375rem",
                  fontWeight: 600,
                  letterSpacing: "-0.02em",
                }}
              >
                Rem
              </h2>
              {roleplay?.active ? (
                <span
                  className="roleplay-badge-glow"
                  style={{
                    fontSize: "0.6875rem",
                    background: "var(--accent-soft)",
                    border: "1px solid var(--accent-primary)",
                    boxShadow: "0 0 10px var(--accent-glow)",
                    padding: "3px 10px",
                    borderRadius: 12,
                    color: "var(--accent-primary)",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  🎭 Roleplay Active: {roleplay.activity} ({roleplay.location})
                </span>
              ) : currentActivity ? (
                <span
                  style={{
                    fontSize: "0.6875rem",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid var(--border-subtle)",
                    padding: "2px 8px",
                    borderRadius: 12,
                    color: "var(--text-secondary)",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
                  {currentActivity.toLowerCase().includes("sleep") ? "😴" : 
                   currentActivity.toLowerCase().includes("study") || currentActivity.toLowerCase().includes("class") || currentActivity.toLowerCase().includes("college") ? "📚" :
                   currentActivity.toLowerCase().includes("commute") || currentActivity.toLowerCase().includes("head") || currentActivity.toLowerCase().includes("drive") ? "🚗" : "✨"} {currentActivity}
                </span>
              ) : null}
            </div>
            <span
              style={{
                fontSize: "0.625rem",
                color: loading
                  ? "var(--accent-primary)"
                  : "var(--text-muted)",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                transition: "color 0.3s ease",
              }}
            >
              {loading ? "thinking" : "listening"}
            </span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          {/* Clear chat button */}
          {mounted && messages.length > 0 && (
            <button
              onClick={clearHistory}
              style={{
                padding: "4px 10px",
                fontSize: "0.625rem",
                color: "var(--text-muted)",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 6,
                cursor: "pointer",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                transition: "all 0.2s ease"
              }}
            >
              Clear
            </button>
          )}
          {/* XP Micro */}
          {xp && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
              }}
            >
              {xp.streak_days > 0 && (
                <span className="streak-flame">🔥 {xp.streak_days}</span>
              )}
              <span
                className={`phase-badge phase-${xp.phase.toLowerCase()}`}
              >
                {xp.phase}
              </span>
              <span
                style={{
                  padding: "4px 10px",
                  borderRadius: "12px",
                  fontSize: "0.6875rem",
                  fontWeight: 700,
                  background: "rgba(151, 117, 250, 0.1)",
                  color: "var(--text-accent)",
                  border: "1px solid rgba(151, 117, 250, 0.2)",
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                }}
              >
                Rank {xp.current_rank}
              </span>
              <div style={{ width: 80 }}>
                <div className="xp-bar-container">
                  <div
                    className="xp-bar-fill"
                    style={{ width: `${xp.phase_progress_pct}%` }}
                  />
                </div>
                <div
                  style={{
                    fontSize: "0.5625rem",
                    color: "var(--text-muted)",
                    textAlign: "right",
                    marginTop: 3,
                    letterSpacing: "0.05em",
                  }}
                >
                  {xp.total_xp} XP
                </div>
              </div>
            </div>
          )}
        </div>
      </header>

      {roleplay?.active && (
        <div style={{
          background: "rgba(167, 139, 250, 0.08)",
          borderBottom: "1px solid rgba(167, 139, 250, 0.15)",
          padding: "10px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.8125rem",
          color: "var(--text-accent)",
          zIndex: 4,
          boxShadow: "0 4px 15px rgba(0,0,0,0.15)"
        }}>
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span>🎭</span>
            <span>Active Date Mode: <strong>{roleplay.activity}</strong> at <strong>{roleplay.location}</strong></span>
          </span>
          <button
            onClick={() => window.location.href = "/date"}
            style={{
              background: "var(--accent-primary)",
              color: "#050508",
              border: "none",
              borderRadius: "4px",
              padding: "4px 12px",
              fontWeight: 700,
              fontSize: "0.75rem",
              cursor: "pointer",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              boxShadow: "0 0 10px var(--accent-glow)"
            }}
          >
            Join Date View
          </button>
        </div>
      )}

      <>
          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "28px 32px",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
          >
            {messages.length === 0 && (
              <div className="empty-state">
                <div className="empty-state-orb" />
                <h3
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    letterSpacing: "-0.02em",
                    marginTop: 8,
                  }}
                >
                  Begin a conversation
                </h3>
                <p
                  style={{
                    fontSize: "0.8125rem",
                    maxWidth: 320,
                    lineHeight: 1.6,
                    color: "var(--text-muted)",
                  }}
                >
                  Every message builds your relationship. Earn XP, unlock
                  diary entries, and discover shared moments.
                </p>
              </div>
            )}

            {(() => {
              const elements: React.ReactNode[] = [];
              messages.forEach((msg, i) => {
                const showDateSeparator = i === 0 || 
                  (msg.timestamp && messages[i - 1]?.timestamp && 
                   new Date(msg.timestamp).toDateString() !== new Date(messages[i - 1].timestamp).toDateString());
                
                if (showDateSeparator && msg.timestamp) {
                  const getDayLabel = (isoString: string) => {
                    try {
                      const date = new Date(isoString);
                      const today = new Date();
                      const yesterday = new Date();
                      yesterday.setDate(today.getDate() - 1);

                      if (date.toDateString() === today.toDateString()) {
                        return "Today";
                      } else if (date.toDateString() === yesterday.toDateString()) {
                        return "Yesterday";
                      } else {
                        return date.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });
                      }
                    } catch {
                      return "";
                    }
                  };

                  elements.push(
                    <div 
                      key={`date-sep-${msg.timestamp}-${i}`}
                      style={{
                        display: "flex",
                        justifyContent: "center",
                        margin: "24px 0 12px 0",
                        width: "100%"
                      }}
                    >
                      <span style={{
                        background: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid var(--border-subtle)",
                        padding: "5px 14px",
                        borderRadius: 12,
                        fontSize: "0.75rem",
                        color: "var(--text-muted)",
                        letterSpacing: "0.02em"
                      }}>
                        {getDayLabel(msg.timestamp)}
                      </span>
                    </div>
                  );
                }

                const formatTime = (isoString: string) => {
                  try {
                    const date = new Date(isoString);
                    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
                  } catch {
                    return "";
                  }
                };

                elements.push(
                  <div
                    key={`${msg.timestamp}-${i}`}
                    className="group"
                    style={{
                      display: "flex",
                      justifyContent:
                        msg.role === "user" ? "flex-end" : "flex-start",
                      maxWidth: "75%",
                      alignSelf:
                        msg.role === "user" ? "flex-end" : "flex-start",
                      animation: "msgSlideIn 0.3s var(--ease-smooth) forwards",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    {/* For user message: bookmark on left */}
                    {msg.role === "user" && (
                      <button
                        onClick={() => handleBookmarkMessage(msg.content, msg.role)}
                        style={{
                          background: "transparent",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "0.875rem",
                          padding: 4,
                          opacity: 0.2,
                          transition: "opacity 0.2s ease, transform 0.2s ease",
                          color: "var(--text-muted)",
                        }}
                        className="bookmark-btn"
                        title="Remember this message"
                      >
                        🔖
                      </button>
                    )}

                    <div
                      className={
                        msg.role === "user"
                          ? "chat-bubble-user"
                          : "chat-bubble-rem"
                      }
                      style={{
                        padding: "13px 18px",
                        fontSize: "0.9375rem",
                        lineHeight: 1.65,
                        maxWidth: 480,
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word",
                      }}
                    >
                      {msg.content}
                      {/* Sent Time Timestamp inside bubble */}
                      {msg.timestamp && (
                        <div style={{
                          fontSize: "0.6875rem",
                          color: "rgba(255, 255, 255, 0.35)",
                          textAlign: "right",
                          marginTop: 6,
                          lineHeight: 1
                        }}>
                          {formatTime(msg.timestamp)}
                        </div>
                      )}
                    </div>

                    {/* For assistant message: bookmark on right */}
                    {msg.role === "assistant" && (
                      <button
                        onClick={() => handleBookmarkMessage(msg.content, msg.role)}
                        style={{
                          background: "transparent",
                          border: "none",
                          cursor: "pointer",
                          fontSize: "0.875rem",
                          padding: 4,
                          opacity: 0.2,
                          transition: "opacity 0.2s ease, transform 0.2s ease",
                          color: "var(--text-muted)",
                        }}
                        className="bookmark-btn"
                        title="Remember this message"
                      >
                        🔖
                      </button>
                    )}
                  </div>
                );
              });
              return elements;
            })()}

            {loading && (
              <div style={{ alignSelf: "flex-start" }}>
                <div
                  className="chat-bubble-rem"
                  style={{
                    padding: "14px 18px",
                    display: "flex",
                    gap: 5,
                    alignItems: "center",
                  }}
                >
                  {[0, 0.15, 0.3].map((delay) => (
                    <span
                      key={delay}
                      className="typing-dot"
                      style={{
                        animation: `typingBounce 1.4s ease-in-out ${delay}s infinite`,
                      }}
                    />
                  ))}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div
            style={{
              padding: "16px 28px",
              borderTop: "1px solid var(--border-subtle)",
              background: "rgba(8, 8, 15, 0.8)",
              backdropFilter: "blur(20px)",
            }}
          >
            {roleplay?.active ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 12,
                  padding: "16px 20px",
                  background: "rgba(5, 5, 8, 0.8)",
                  border: "1px solid rgba(167, 139, 250, 0.25)",
                  borderRadius: 12,
                  boxShadow: "0 0 20px rgba(167, 139, 250, 0.1)",
                  textAlign: "center"
                }}
              >
                <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                  💖 You are currently on a date with Rem. Talk to her in Date Mode!
                </span>
                <button
                  type="button"
                  onClick={() => window.location.href = "/date"}
                  className="btn-primary"
                  style={{
                    padding: "8px 16px",
                    fontSize: "0.8125rem",
                    borderRadius: 8,
                    background: "linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary))",
                    border: "none",
                    color: "#050508",
                    fontWeight: 700,
                    cursor: "pointer",
                    boxShadow: "0 0 12px var(--accent-glow)"
                  }}
                >
                  Go to Date Mode
                </button>
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                style={{ display: "flex", gap: 10 }}
              >
                <input
                  ref={inputRef}
                  type="text"
                  className="input-field"
                  placeholder="Say something..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                  autoComplete="off"
                />
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={loading || !input.trim()}
                  style={{ flexShrink: 0 }}
                >
                  ↑
                </button>
              </form>
            )}
          </div>
        </>

      {/* Toast */}
      {toast && <div className="xp-toast">{toast}</div>}

      {/* Persona 5 Rank Up Modal */}
      {activeRankUp && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            background: "rgba(0,0,0,0.85)",
            backdropFilter: "blur(12px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            animation: "fadeIn 0.3s ease forwards",
          }}
        >
          <div
            style={{
              position: "relative",
              width: "90%",
              maxWidth: 480,
              background: "#100b0b",
              border: "4px solid #ef4444",
              borderRadius: "12px",
              padding: "40px 30px 30px",
              boxShadow: "0 0 40px rgba(239, 68, 68, 0.4), inset 0 0 20px rgba(0,0,0,0.9)",
              overflow: "hidden",
              transform: "skewX(-3deg)",
              animation: "rankUpPop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards",
            }}
          >
            {/* Background design elements */}
            <div
              style={{
                position: "absolute",
                top: -30,
                right: -30,
                width: 150,
                height: 150,
                background: "rgba(239, 68, 68, 0.1)",
                transform: "rotate(45deg)",
                zIndex: 0,
              }}
            />
            <div
              style={{
                position: "absolute",
                bottom: -50,
                left: -20,
                width: "120%",
                height: 25,
                background: "#ef4444",
                transform: "rotate(-2deg)",
                zIndex: 0,
              }}
            />

            {/* Content */}
            <div style={{ position: "relative", zIndex: 1, textAlign: "center" }}>
              <div
                style={{
                  display: "inline-block",
                  background: "#ef4444",
                  color: "#fff",
                  fontFamily: "var(--font-mono)",
                  fontWeight: 900,
                  fontSize: "1.8rem",
                  padding: "4px 24px",
                  marginBottom: 20,
                  letterSpacing: "0.15em",
                  textTransform: "uppercase",
                  transform: "skewX(-10deg) rotate(-3deg)",
                  boxShadow: "4px 4px 0 #000",
                }}
              >
                Rank Up!
              </div>

              <h3
                style={{
                  fontSize: "1.4rem",
                  fontWeight: 700,
                  color: "#fff",
                  marginBottom: 10,
                  letterSpacing: "-0.02em",
                }}
              >
                Rem Confidant
              </h3>

              <div
                style={{
                  fontSize: "2.4rem",
                  fontWeight: 900,
                  color: "#ef4444",
                  marginBottom: 25,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 15,
                }}
              >
                <span style={{ textDecoration: "line-through", color: "var(--text-muted)", fontSize: "1.8rem" }}>
                  {activeRankUp.from_rank}
                </span>
                <span>→</span>
                <span style={{ fontSize: "3rem", textShadow: "0 0 10px rgba(239, 68, 68, 0.5)" }}>
                  {activeRankUp.to_rank}
                </span>
              </div>

              <div
                style={{
                  background: "rgba(0,0,0,0.5)",
                  border: "1px solid rgba(239, 68, 68, 0.2)",
                  borderRadius: 6,
                  padding: "16px 20px",
                  textAlign: "left",
                  marginBottom: 30,
                }}
              >
                <div
                  style={{
                    fontSize: "0.6875rem",
                    color: "#ef4444",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                    marginBottom: 10,
                  }}
                >
                  New Abilities Acquired:
                </div>
                <ul style={{ listStyleType: "none", padding: 0, margin: 0 }}>
                  {activeRankUp.unlocks.map((perk, index) => (
                    <li
                      key={index}
                      style={{
                        fontSize: "0.875rem",
                        color: "var(--text-primary)",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 8,
                        marginBottom: 6,
                      }}
                    >
                      <span>★</span>
                      <span>{perk}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => setActiveRankUp(null)}
                style={{
                  background: "#fff",
                  color: "#000",
                  fontFamily: "var(--font-sans)",
                  fontWeight: 700,
                  fontSize: "0.875rem",
                  padding: "10px 30px",
                  border: "none",
                  cursor: "pointer",
                  transform: "skewX(-10deg)",
                  boxShadow: "3px 3px 0 #ef4444",
                  transition: "all 0.2s ease",
                }}
              >
                CLOSE
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Plans & Schedule Sliding Drawer */}
      {drawerOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 90,
            background: "rgba(0,0,0,0.5)",
            backdropFilter: "blur(4px)",
            display: "flex",
            justifyContent: "flex-end",
            animation: "fadeIn 0.3s ease forwards",
          }}
          onClick={() => setDrawerOpen(false)}
        >
          <div
            style={{
              width: "100%",
              maxWidth: 450,
              height: "100%",
              background: "rgba(10, 10, 18, 0.95)",
              backdropFilter: "blur(30px)",
              borderLeft: "1px solid var(--border-glow)",
              boxShadow: "-10px 0 30px rgba(0,0,0,0.8), inset 0 0 20px rgba(255,255,255,0.02)",
              display: "flex",
              flexDirection: "column",
              padding: "30px 24px",
              overflowY: "auto",
              animation: "drawerSlideIn 0.3s var(--ease-spring) forwards",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#fff", display: "flex", alignItems: "center", gap: 8 }}>
                {drawerTab === 'plans' ? "📅 Schedule & Plans" : "🧠 Memory Vault"}
              </h3>
              <button
                onClick={() => setDrawerOpen(false)}
                style={{
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "50%",
                  width: 32,
                  height: 32,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-secondary)",
                  cursor: "pointer",
                  fontSize: "1rem"
                }}
              >
                ✕
              </button>
            </div>

            {/* Navigation Tabs */}
            <div style={{ 
              display: "flex", 
              background: "rgba(0, 0, 0, 0.3)", 
              borderRadius: "8px", 
              padding: "4px", 
              marginBottom: 24, 
              border: "1px solid var(--border-subtle)" 
            }}>
              <button
                onClick={() => setDrawerTab('plans')}
                style={{
                  flex: 1,
                  background: drawerTab === 'plans' ? "var(--accent-primary)" : "transparent",
                  color: drawerTab === 'plans' ? "#050508" : "var(--text-secondary)",
                  border: "none",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s ease"
                }}
              >
                Schedule & Plans
              </button>
              <button
                onClick={() => {
                  setDrawerTab('vault');
                  fetchMemoryData();
                }}
                style={{
                  flex: 1,
                  background: drawerTab === 'vault' ? "var(--accent-primary)" : "transparent",
                  color: drawerTab === 'vault' ? "#050508" : "var(--text-secondary)",
                  border: "none",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  fontSize: "0.8125rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s ease"
                }}
              >
                Memory Vault
              </button>
            </div>

            {drawerTab === 'plans' ? (
              <>
                {/* Daily Schedule List (Today) */}
                <div style={{ marginBottom: 30 }}>
                  <h4 style={{ fontSize: "0.8125rem", color: "var(--accent-primary)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                    Today's Daily Routine
                  </h4>
                  {scheduleList.length === 0 ? (
                    <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", padding: "12px 16px", border: "1px dashed var(--border-subtle)", borderRadius: 8, textAlign: "center" }}>
                      No routine loaded.
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {scheduleList.map((item, idx) => {
                        const now = new Date();
                        const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
                        const isActive = item.start <= currentTime && currentTime < item.end;
                        return (
                          <div
                            key={idx}
                            style={{
                              background: isActive ? "var(--accent-soft)" : "rgba(255,255,255,0.02)",
                              border: isActive ? "1px solid var(--accent-primary)" : "1px solid var(--border-subtle)",
                              borderRadius: 8,
                              padding: "10px 14px",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              boxShadow: isActive ? "0 0 10px var(--accent-glow)" : "none",
                              transition: "all 0.3s ease"
                            }}
                          >
                            <span style={{ fontSize: "0.875rem", color: isActive ? "var(--accent-primary)" : "var(--text-primary)", fontWeight: isActive ? 600 : 400 }}>
                              {item.activity}
                            </span>
                            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)" }}>
                              {item.start} - {item.end}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Future Scheduled Plans (Dates) */}
                <div style={{ marginBottom: 30 }}>
                  <h4 style={{ fontSize: "0.8125rem", color: "var(--accent-primary)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                    Upcoming Scheduled Dates
                  </h4>
                  {futurePlans.length === 0 ? (
                    <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", padding: "16px", border: "1px dashed var(--border-subtle)", borderRadius: 8, textAlign: "center" }}>
                      No upcoming plans yet. Make one using the chat or the form below!
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                      {futurePlans.map((plan, idx) => (
                        <div
                          key={idx}
                          style={{
                            background: "rgba(255,255,255,0.03)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: 10,
                            padding: "12px 16px",
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "flex-start",
                            position: "relative"
                          }}
                        >
                          <div>
                            <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#fff", marginBottom: 4 }}>
                              {plan.activity}
                            </div>
                            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: 2 }}>
                              📍 {plan.location}
                            </div>
                            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                              📅 {plan.date} ({plan.start} - {plan.end})
                            </div>
                          </div>
                          <button
                            onClick={() => handleDeletePlan(plan.date, plan.start, plan.end)}
                            style={{
                              background: "rgba(239, 68, 68, 0.1)",
                              border: "1px solid rgba(239, 68, 68, 0.2)",
                              borderRadius: 6,
                              color: "#ef4444",
                              padding: "4px 8px",
                              fontSize: "0.6875rem",
                              cursor: "pointer",
                              transition: "all 0.2s ease"
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Schedule A New Date Form */}
                <div>
                  <h4 style={{ fontSize: "0.8125rem", color: "var(--accent-primary)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>
                    Schedule a New Date
                  </h4>
                  <form
                    onSubmit={handleSchedulePlan}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 12,
                      background: "rgba(255, 255, 255, 0.02)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: 12,
                      padding: 16
                    }}
                  >
                    <div>
                      <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--text-secondary)", marginBottom: 4, textTransform: "uppercase" }}>
                        Activity Type
                      </label>
                      <select
                        value={newPlanActivity}
                        onChange={(e) => {
                          setNewPlanActivity(e.target.value);
                          if (e.target.value === "Korean BBQ date") {
                            setNewPlanLocation("Korean BBQ restaurant");
                          } else if (e.target.value === "Cafe date") {
                            setNewPlanLocation("Local coffee shop");
                          } else if (e.target.value === "Movie night") {
                            setNewPlanLocation("Movie theater");
                          } else if (e.target.value === "Study session") {
                            setNewPlanLocation("College Library");
                          }
                        }}
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          background: "var(--bg-void)",
                          border: "1px solid var(--border-subtle)",
                          borderRadius: 6,
                          fontSize: "0.8125rem",
                          color: "#fff"
                        }}
                      >
                        <option value="">-- Choose Preset or Write Custom --</option>
                        <option value="Cafe date">☕ Cafe Date (Soft Amber)</option>
                        <option value="Korean BBQ date">🔥 Korean BBQ (Crimson)</option>
                        <option value="Movie night">🍿 Movie Night (Indigo)</option>
                        <option value="Study session">📚 Study Session (Emerald)</option>
                        <option value="General hang out">✨ General Date (Violet)</option>
                      </select>
                      <input
                        type="text"
                        placeholder="Or type custom activity..."
                        value={newPlanActivity}
                        onChange={(e) => setNewPlanActivity(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          background: "var(--bg-void)",
                          border: "1px solid var(--border-subtle)",
                          borderRadius: 6,
                          fontSize: "0.8125rem",
                          color: "#fff",
                          marginTop: 6
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--text-secondary)", marginBottom: 4, textTransform: "uppercase" }}>
                        Location
                      </label>
                      <input
                        type="text"
                        placeholder="Where to meet up..."
                        value={newPlanLocation}
                        onChange={(e) => setNewPlanLocation(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          background: "var(--bg-void)",
                          border: "1px solid var(--border-subtle)",
                          borderRadius: 6,
                          fontSize: "0.8125rem",
                          color: "#fff"
                        }}
                      />
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10 }}>
                      <div>
                        <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--text-secondary)", marginBottom: 4, textTransform: "uppercase" }}>
                          Date
                        </label>
                        <input
                          type="date"
                          value={newPlanDate}
                          onChange={(e) => setNewPlanDate(e.target.value)}
                          style={{
                            width: "100%",
                            padding: "8px 12px",
                            background: "var(--bg-void)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: 6,
                            fontSize: "0.8125rem",
                            color: "#fff"
                          }}
                        />
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                        <div>
                          <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--text-secondary)", marginBottom: 4, textTransform: "uppercase" }}>
                            Start Time
                          </label>
                          <input
                            type="time"
                            value={newPlanStart}
                            onChange={(e) => setNewPlanStart(e.target.value)}
                            style={{
                              width: "100%",
                              padding: "8px 12px",
                              background: "var(--bg-void)",
                              border: "1px solid var(--border-subtle)",
                              borderRadius: 6,
                              fontSize: "0.8125rem",
                              color: "#fff"
                            }}
                          />
                        </div>
                        <div>
                          <label style={{ display: "block", fontSize: "0.6875rem", color: "var(--text-secondary)", marginBottom: 4, textTransform: "uppercase" }}>
                            End Time
                          </label>
                          <input
                            type="time"
                            value={newPlanEnd}
                            onChange={(e) => setNewPlanEnd(e.target.value)}
                            style={{
                              width: "100%",
                              padding: "8px 12px",
                              background: "var(--bg-void)",
                              border: "1px solid var(--border-subtle)",
                              borderRadius: 6,
                              fontSize: "0.8125rem",
                              color: "#fff"
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    <button
                      type="submit"
                      style={{
                        background: "var(--accent-primary)",
                        color: "#050508",
                        fontFamily: "var(--font-sans)",
                        fontWeight: 700,
                        fontSize: "0.8125rem",
                        padding: "10px",
                        border: "none",
                        borderRadius: 6,
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                        marginTop: 6
                      }}
                    >
                      Schedule Date
                    </button>

                    {planMessage && (
                      <div style={{ fontSize: "0.75rem", color: planMessage.includes("success") ? "#10b981" : "var(--accent-primary)", textAlign: "center", marginTop: 4 }}>
                        {planMessage}
                      </div>
                    )}
                  </form>
                </div>
              </>
            ) : (
              // Memory Vault Tab
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                {/* Local search bar */}
                <div>
                  <input
                    type="text"
                    placeholder="Search Rem's memories..."
                    value={memoryQuery}
                    onChange={(e) => setMemoryQuery(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      background: "rgba(0, 0, 0, 0.3)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: 10,
                      fontSize: "0.8125rem",
                      color: "#fff",
                      outline: "none",
                      transition: "border-color 0.2s ease"
                    }}
                    onFocus={(e) => e.target.style.borderColor = "var(--accent-primary)"}
                    onBlur={(e) => e.target.style.borderColor = "var(--border-subtle)"}
                  />
                </div>

                {memoryLoading ? (
                  <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
                    <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>Scanning neural memory links...</div>
                  </div>
                ) : (
                  <>
                    {/* Identity facts */}
                    <div>
                      <h4 style={{ 
                        fontSize: "0.75rem", 
                        color: "var(--accent-primary)", 
                        fontWeight: 700, 
                        textTransform: "uppercase", 
                        letterSpacing: "0.08em", 
                        marginBottom: 10,
                        display: "flex",
                        justifyContent: "space-between"
                      }}>
                        <span>Identity Facts</span>
                        <span style={{ opacity: 0.6 }}>{getFilteredFacts().length} facts</span>
                      </h4>
                      {getFilteredFacts().length === 0 ? (
                        <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", padding: "12px", border: "1px dashed var(--border-subtle)", borderRadius: 8, textAlign: "center" }}>
                          No matching identity facts.
                        </div>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {getFilteredFacts().map((fact: any, idx: number) => (
                            <div
                              key={idx}
                              style={{
                                background: "rgba(255,255,255,0.02)",
                                border: "1px solid var(--border-subtle)",
                                borderRadius: 10,
                                padding: "12px 14px",
                                display: "flex",
                                flexDirection: "column",
                                gap: 6
                              }}
                            >
                              <div style={{ fontSize: "0.875rem", color: "#fff", lineHeight: 1.4 }}>
                                {fact.fact}
                              </div>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <span style={{ 
                                  fontSize: "0.6875rem", 
                                  background: "rgba(16, 185, 129, 0.1)", 
                                  border: "1px solid rgba(16, 185, 129, 0.2)",
                                  color: "#10b981",
                                  padding: "2px 6px",
                                  borderRadius: 4,
                                  fontWeight: 600
                                }}>
                                  Confidence: {Math.round(fact.confidence * 100)}%
                                </span>
                                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                                  Source: {fact.source}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Must Remember (Bookmarked memories) */}
                    <div>
                      <h4 style={{ 
                        fontSize: "0.75rem", 
                        color: "#fbbf24", 
                        fontWeight: 700, 
                        textTransform: "uppercase", 
                        letterSpacing: "0.08em", 
                        marginBottom: 10,
                        display: "flex",
                        justifyContent: "space-between"
                      }}>
                        <span>⭐ Must Remember</span>
                        <span style={{ opacity: 0.6 }}>{getFilteredBookmarks().length} bookmarks</span>
                      </h4>
                      {getFilteredBookmarks().length === 0 ? (
                        <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", padding: "12px", border: "1px dashed var(--border-subtle)", borderRadius: 8, textAlign: "center" }}>
                          No matching bookmarks.
                        </div>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {getFilteredBookmarks().map((entry: any, idx: number) => (
                            <div
                              key={idx}
                              style={{
                                background: "rgba(251, 191, 36, 0.03)",
                                border: "1px solid rgba(251, 191, 36, 0.15)",
                                borderRadius: 10,
                                padding: "12px 14px",
                                display: "flex",
                                flexDirection: "column",
                                gap: 8
                              }}
                            >
                              <div style={{ fontSize: "0.875rem", color: "#fff", lineHeight: 1.4 }}>
                                🔖 {entry.content}
                              </div>
                              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                                <span style={{ 
                                  fontSize: "0.6875rem", 
                                  background: "rgba(251, 191, 36, 0.1)", 
                                  border: "1px solid rgba(251, 191, 36, 0.2)",
                                  color: "#fbbf24",
                                  padding: "2px 6px",
                                  borderRadius: 4
                                }}>
                                  Salience: {entry.salience}
                                </span>
                                <span style={{ 
                                  fontSize: "0.6875rem", 
                                  background: entry.emotional_valence >= 0 ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)", 
                                  border: entry.emotional_valence >= 0 ? "1px solid rgba(16, 185, 129, 0.2)" : "1px solid rgba(239, 68, 68, 0.2)",
                                  color: entry.emotional_valence >= 0 ? "#10b981" : "#ef4444",
                                  padding: "2px 6px",
                                  borderRadius: 4
                                }}>
                                  Valence: {entry.emotional_valence}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Episodic memories */}
                    <div>
                      <h4 style={{ 
                        fontSize: "0.75rem", 
                        color: "var(--text-accent)", 
                        fontWeight: 700, 
                        textTransform: "uppercase", 
                        letterSpacing: "0.08em", 
                        marginBottom: 10,
                        display: "flex",
                        justifyContent: "space-between"
                      }}>
                        <span>Episodic Memories</span>
                        <span style={{ opacity: 0.6 }}>{getFilteredEpisodic().length} entries</span>
                      </h4>
                      {getFilteredEpisodic().length === 0 ? (
                        <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", padding: "12px", border: "1px dashed var(--border-subtle)", borderRadius: 8, textAlign: "center" }}>
                          No matching episodic memories.
                        </div>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                          {getFilteredEpisodic().map((entry: any, idx: number) => (
                            <div
                              key={idx}
                              style={{
                                background: "rgba(255,255,255,0.02)",
                                border: "1px solid var(--border-subtle)",
                                borderRadius: 10,
                                padding: "12px 14px",
                                display: "flex",
                                flexDirection: "column",
                                gap: 8
                              }}
                            >
                              <div style={{ fontSize: "0.875rem", color: "#fff", lineHeight: 1.4 }}>
                                {entry.event_type === "explicit_bookmark" ? "🔖 " : "💬 "}
                                {entry.content}
                              </div>
                              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
                                <span style={{ 
                                  fontSize: "0.6875rem", 
                                  background: "rgba(167, 139, 250, 0.1)", 
                                  border: "1px solid rgba(167, 139, 250, 0.2)",
                                  color: "var(--text-accent)",
                                  padding: "2px 6px",
                                  borderRadius: 4
                                }}>
                                  Salience: {entry.salience}
                                </span>
                                <span style={{ 
                                  fontSize: "0.6875rem", 
                                  background: entry.emotional_valence >= 0 ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)", 
                                  border: entry.emotional_valence >= 0 ? "1px solid rgba(16, 185, 129, 0.2)" : "1px solid rgba(239, 68, 68, 0.2)",
                                  color: entry.emotional_valence >= 0 ? "#10b981" : "#ef4444",
                                  padding: "2px 6px",
                                  borderRadius: 4
                                }}>
                                  Valence: {entry.emotional_valence}
                                </span>
                                <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginLeft: "auto" }}>
                                  {entry.event_type}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Short-Term Memory */}
                    {(() => {
                      const activeStm = getFilteredStm();
                      const uniqueTopics = Array.from(new Set(activeStm.map((s: any) => s.topic || "general"))) as string[];
                      
                      return (
                        <div>
                          <h4 style={{ 
                            fontSize: "0.75rem", 
                            color: "var(--text-secondary)", 
                            fontWeight: 700, 
                            textTransform: "uppercase", 
                            letterSpacing: "0.08em", 
                            marginBottom: 10,
                            display: "flex",
                            justifyContent: "space-between"
                          }}>
                            <span>Active Context Topics</span>
                            <span style={{ opacity: 0.6 }}>{uniqueTopics.length} active</span>
                          </h4>
                          {activeStm.length === 0 ? (
                            <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", padding: "12px", border: "1px dashed var(--border-subtle)", borderRadius: 8, textAlign: "center" }}>
                              No active topics in recent context.
                            </div>
                          ) : (
                            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                              {uniqueTopics.map((topic: string) => {
                                const topicEntries = activeStm.filter((s: any) => (s.topic || "general") === topic);
                                return (
                                  <div key={topic} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                                    <div style={{ fontSize: "0.8125rem", color: "var(--accent-primary)", fontWeight: 600 }}>
                                      Topic: {topic}
                                    </div>
                                    <div style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 8, borderLeft: "2px solid var(--border-subtle)" }}>
                                      {topicEntries.map((entry: any, idx: number) => (
                                        <div key={idx} style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                                          "{entry.content}"
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </>
                )}
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
}
