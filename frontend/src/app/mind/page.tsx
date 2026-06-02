"use client";

import { useState, useEffect, useCallback } from "react";
import { getSchedule, getPersonality, getIdentity, getComplexity } from "@/lib/gameApi";

/* ────── helper: time-ago label ────── */
function timeAgo(ts: string) {
  if (!ts) return "";
  const d = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(d / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

/* ────── neurochem bar colors ────── */
const CHEM_COLORS: Record<string, string> = {
  dopamine: "#f9c846",
  cortisol: "#ff6b6b",
  oxytocin: "#ff85c0",
  serotonin: "#69db7c",
  endorphins: "#74c0fc",
};

const CHEM_ICONS: Record<string, string> = {
  dopamine: "⚡",
  cortisol: "🔥",
  oxytocin: "💗",
  serotonin: "✦",
  endorphins: "◈",
};

export default function MindPage() {
  const [schedule, setSchedule] = useState<any>(null);
  const [personality, setPersonality] = useState<any>(null);
  const [identity, setIdentity] = useState<any>(null);
  const [complexity, setComplexity] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"schedule" | "persona" | "memory" | "inner">("schedule");

  const load = useCallback(async () => {
    try {
      const [sched, pers, ident, comp] = await Promise.all([
        getSchedule().catch(() => null),
        getPersonality().catch(() => null),
        getIdentity().catch(() => null),
        getComplexity().catch(() => null),
      ]);
      setSchedule(sched);
      setPersonality(pers);
      setIdentity(ident);
      setComplexity(comp);
    } catch (e) {
      console.error("Mind page load error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <div className="page-container" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="rem-orb" style={{ width: 48, height: 48, animation: "pulse-glow 2s ease-in-out infinite" }} />
      </div>
    );
  }

  const scheduleItems = schedule?.schedule || [];
  const currentActivity = schedule?.current_activity;
  const dayOfWeek = schedule?.day_of_week;

  const selfIdentity = complexity?.self_identity || {};
  const personaFlavor = selfIdentity?._persona_flavor || selfIdentity?.persona_flavor;
  const innerMonologue = complexity?.inner_monologue || [];
  const rumination = complexity?.rumination;
  const knowledgeHoles = complexity?.knowledge_holes || [];
  const pendingEruption = complexity?.pending_eruption;

  const psyche = personality?.psyche;
  const neurochem = psyche?.neurochem || {};
  const vibePalette = personality?.vibe_palette || [];
  const interests = personality?.current_interests || [];

  const aboutUser = identity?.about_user || [];
  const userFacts = identity?.user_facts || {};
  const userEval = identity?.user_evaluation;
  const relationship = identity?.relationship;

  const TABS = [
    { key: "schedule" as const, label: "Schedule", icon: "◷" },
    { key: "persona" as const, label: "Persona", icon: "✧" },
    { key: "memory" as const, label: "Identity", icon: "◈" },
    { key: "inner" as const, label: "Inner World", icon: "◉" },
  ];

  return (
    <div className="page-container" style={{ padding: "36px 48px", maxWidth: 860 }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 className="page-title" style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{
            width: 36, height: 36, borderRadius: "50%",
            background: "linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.875rem", fontWeight: 700,
            boxShadow: "0 0 20px var(--accent-glow)",
          }}>✦</span>
          Rem&apos;s Mind
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
          Live view of Rem&apos;s cognitive state — what she knows, thinks, and feels right now.
        </p>
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: "flex", gap: 4, marginBottom: 28,
        background: "rgba(255,255,255,0.02)", borderRadius: 12,
        padding: 4, border: "1px solid var(--border-subtle)",
      }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              flex: 1, padding: "10px 0", borderRadius: 8,
              border: "none", cursor: "pointer",
              background: activeTab === tab.key
                ? "linear-gradient(135deg, rgba(151,117,250,0.15), rgba(232,121,249,0.08))"
                : "transparent",
              color: activeTab === tab.key ? "var(--text-primary)" : "var(--text-muted)",
              fontSize: "0.8125rem", fontWeight: activeTab === tab.key ? 600 : 400,
              transition: "all 0.2s var(--ease-smooth)",
              display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
            }}
          >
            <span style={{ fontSize: "0.75rem", opacity: activeTab === tab.key ? 1 : 0.5 }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ════════════ SCHEDULE TAB ════════════ */}
      {activeTab === "schedule" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Current Activity Spotlight */}
          {currentActivity && (
            <div style={{
              padding: "24px 28px", borderRadius: 16,
              background: "linear-gradient(135deg, rgba(151,117,250,0.08), rgba(232,121,249,0.04))",
              border: "1px solid rgba(151,117,250,0.15)",
              position: "relative", overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", top: -40, right: -40, width: 120, height: 120,
                borderRadius: "50%", background: "radial-gradient(circle, var(--accent-glow), transparent)",
                filter: "blur(30px)",
              }} />
              <div style={{ fontSize: "0.6875rem", color: "var(--accent-primary)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8, fontWeight: 600 }}>
                Right Now
              </div>
              <div style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.5 }}>
                {currentActivity}
              </div>
              {dayOfWeek && (
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 8 }}>
                  {dayOfWeek}
                </div>
              )}
            </div>
          )}

          {/* Schedule Timeline */}
          <section className="glass-panel" style={{ padding: 28 }}>
            <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ color: "var(--accent-secondary)" }}>◷</span> Daily Schedule
            </h2>

            {scheduleItems.length === 0 ? (
              <div style={{ padding: "32px 0", textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", marginBottom: 8 }}>🌙</div>
                <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                  No schedule generated yet. Send a message to Rem first — her schedule is generated on the first interaction.
                </p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                {scheduleItems.map((item: any, i: number) => {
                  const time = item.time || item.hour || "";
                  const activity = item.activity || item.description || item.event || JSON.stringify(item);
                  const isNow = currentActivity && activity.toLowerCase().includes(currentActivity.toLowerCase().substring(0, 15));
                  return (
                    <div key={i} style={{
                      display: "flex", gap: 16, padding: "12px 0",
                      borderBottom: i < scheduleItems.length - 1 ? "1px solid var(--border-subtle)" : "none",
                      alignItems: "flex-start",
                    }}>
                      {/* Time column */}
                      <div style={{
                        minWidth: 60, fontSize: "0.75rem", fontFamily: "var(--font-mono)",
                        color: isNow ? "var(--accent-primary)" : "var(--text-muted)",
                        fontWeight: isNow ? 600 : 400, paddingTop: 2,
                      }}>
                        {time}
                      </div>

                      {/* Timeline dot */}
                      <div style={{
                        width: 8, height: 8, borderRadius: "50%", marginTop: 6, flexShrink: 0,
                        background: isNow
                          ? "var(--accent-primary)"
                          : "rgba(255,255,255,0.1)",
                        boxShadow: isNow ? "0 0 8px var(--accent-glow)" : "none",
                      }} />

                      {/* Activity */}
                      <div style={{
                        fontSize: "0.8125rem", lineHeight: 1.5,
                        color: isNow ? "var(--text-primary)" : "var(--text-secondary)",
                        fontWeight: isNow ? 500 : 400,
                      }}>
                        {activity}
                        {isNow && (
                          <span style={{
                            marginLeft: 8,
                            fontSize: "0.5625rem",
                            color: "var(--accent-primary)",
                            background: "rgba(151,117,250,0.1)",
                            padding: "2px 8px",
                            borderRadius: 999,
                            fontWeight: 600,
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                          }}>now</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      )}

      {/* ════════════ PERSONA TAB ════════════ */}
      {activeTab === "persona" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Persona Flavor (randomly generated on reset) */}
          {personaFlavor && (
            <section className="glass-panel" style={{
              padding: 28, position: "relative", overflow: "hidden",
              background: "linear-gradient(135deg, rgba(151,117,250,0.06), rgba(232,121,249,0.03))",
              borderColor: "rgba(151,117,250,0.12)",
            }}>
              <div style={{
                position: "absolute", top: -60, left: -60, width: 160, height: 160,
                borderRadius: "50%", background: "radial-gradient(circle, rgba(232,121,249,0.08), transparent)",
                filter: "blur(40px)",
              }} />
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8, position: "relative" }}>
                <span style={{ color: "var(--accent-tertiary)" }}>🎲</span> Generated Persona
                <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", fontWeight: 400 }}>· refreshed on reset</span>
              </h2>
              <div style={{
                whiteSpace: "pre-line", fontSize: "0.8125rem", lineHeight: 1.8,
                color: "var(--text-secondary)", position: "relative",
              }}>
                {personaFlavor}
              </div>
            </section>
          )}

          {/* Personality Text & Summary */}
          <section className="glass-panel" style={{ padding: 28 }}>
            <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ color: "var(--accent-secondary)" }}>✧</span> Active Personality
            </h2>
            {personality?.personality_summary && (
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: 16 }}>
                {personality.personality_summary}
              </p>
            )}
            {personality?.expression_guidance && (
              <div style={{
                padding: "12px 16px", borderRadius: 8,
                background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-subtle)",
                fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.6,
                fontStyle: "italic",
              }}>
                <span style={{ color: "var(--text-secondary)", fontWeight: 500, fontStyle: "normal" }}>Expression:</span>{" "}
                {personality.expression_guidance}
              </div>
            )}
          </section>

          {/* Neurochemistry */}
          {Object.keys(neurochem).length > 0 && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-secondary)" }}>⟡</span> Neurochemistry
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {Object.entries(neurochem).map(([key, val]: [string, any]) => {
                  const color = CHEM_COLORS[key] || "var(--accent-primary)";
                  const icon = CHEM_ICONS[key] || "•";
                  const pct = Math.round(val * 100);
                  return (
                    <div key={key}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: 6 }}>
                          <span style={{ fontSize: "0.625rem" }}>{icon}</span>
                          {key.charAt(0).toUpperCase() + key.slice(1)}
                        </span>
                        <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color, fontWeight: 600 }}>
                          {pct}%
                        </span>
                      </div>
                      <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.04)", overflow: "hidden" }}>
                        <div style={{
                          height: "100%", borderRadius: 3,
                          width: `${pct}%`,
                          background: `linear-gradient(90deg, ${color}88, ${color})`,
                          transition: "width 0.8s var(--ease-smooth)",
                          boxShadow: `0 0 8px ${color}33`,
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* Psyche Snapshot */}
          {psyche && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-secondary)" }}>◐</span> Psyche State
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
                {[
                  { l: "Stance", v: psyche.stance || "—" },
                  { l: "Posture", v: psyche.posture || "—" },
                  { l: "Engagement", v: `${Math.round((psyche.engagement || 0) * 100)}%` },
                  { l: "Respect", v: `${Math.round((psyche.respect || 0) * 100)}%` },
                  { l: "Trust", v: `${Math.round((personality?.trust || 0) * 100)}%` },
                  { l: "Energy", v: `${Math.round((personality?.energy || 0) * 100)}%` },
                  { l: "Phase", v: personality?.phase || "—" },
                  { l: "Named Mood", v: psyche.named_mood?.primary || psyche.named_mood?.mood || "—" },
                ].map(({ l, v }) => (
                  <div key={l} style={{
                    padding: "10px 14px", borderRadius: 8,
                    background: "rgba(255,255,255,0.02)",
                    display: "flex", justifyContent: "space-between",
                  }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{l}</span>
                    <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-primary)", textTransform: "capitalize" }}>
                      {String(typeof v === "object" ? JSON.stringify(v) : v)}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Vibes & Interests */}
          {(vibePalette.length > 0 || interests.length > 0) && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-tertiary)" }}>◇</span> Vibes & Interests
              </h2>
              {vibePalette.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: interests.length ? 16 : 0 }}>
                  {vibePalette.map((v: string, i: number) => (
                    <span key={i} style={{
                      padding: "4px 12px", borderRadius: 999,
                      background: "rgba(232,121,249,0.08)", border: "1px solid rgba(232,121,249,0.15)",
                      fontSize: "0.6875rem", color: "var(--accent-tertiary)",
                    }}>{v}</span>
                  ))}
                </div>
              )}
              {interests.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {interests.map((v: string, i: number) => (
                    <span key={i} style={{
                      padding: "4px 12px", borderRadius: 999,
                      background: "rgba(151,117,250,0.08)", border: "1px solid rgba(151,117,250,0.15)",
                      fontSize: "0.6875rem", color: "var(--accent-primary)",
                    }}>{v}</span>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      )}

      {/* ════════════ IDENTITY / MEMORY TAB ════════════ */}
      {activeTab === "memory" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Relationship Overview */}
          {relationship && (
            <div style={{
              padding: "24px 28px", borderRadius: 16,
              background: "linear-gradient(135deg, rgba(151,117,250,0.08), rgba(116,185,255,0.04))",
              border: "1px solid rgba(151,117,250,0.12)",
            }}>
              <div style={{ fontSize: "0.6875rem", color: "var(--accent-primary)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8, fontWeight: 600 }}>
                Relationship
              </div>
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", textTransform: "capitalize" }}>
                    {relationship.phase}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 2 }}>
                    {relationship.phase_description}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 16, marginLeft: "auto" }}>
                  {[
                    { l: "Trust", v: Math.round((relationship.trust || 0) * 100) },
                    { l: "Hurt", v: Math.round((relationship.hurt || 0) * 100) },
                    { l: "Reciprocity", v: Math.round((relationship.reciprocity_balance || 0) * 100) },
                  ].map(({ l, v }) => (
                    <div key={l} style={{ textAlign: "center" }}>
                      <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>{v}%</div>
                      <div style={{ fontSize: "0.625rem", color: "var(--text-muted)", textTransform: "uppercase" }}>{l}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Core Identity (fixed) — matches Discord !about */}
          <section className="glass-panel" style={{ padding: 28 }}>
            <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ color: "var(--accent-primary)" }}>📌</span> Core Identity
              <span style={{ marginLeft: "auto", fontSize: "0.5625rem", color: "var(--text-muted)", fontWeight: 400, textTransform: "uppercase", letterSpacing: "0.05em" }}>fixed</span>
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {Object.entries(identity?.core_identity || {
                "Occupation": "College student",
                "Major": "Psychology",
                "Living": "Lives at home",
                "Commute": "~30 min to college",
              }).map(([key, val]: [string, any]) => (
                <div key={key} style={{
                  padding: "10px 14px", borderRadius: 8,
                  background: "rgba(151,117,250,0.04)",
                  border: "1px solid rgba(151,117,250,0.06)",
                  display: "flex", flexDirection: "column", gap: 3,
                }}>
                  <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {key}
                  </span>
                  <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)", fontWeight: 500 }}>
                    {String(val)}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* How She Speaks Right Now — Expression Guidance */}
          {identity?.expression_guidance && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-tertiary)" }}>🗣</span> How She Speaks Right Now
              </h2>
              <div style={{
                padding: "14px 18px", borderRadius: 10,
                background: "rgba(232,121,249,0.04)",
                border: "1px solid rgba(232,121,249,0.08)",
                fontSize: "0.8125rem", color: "var(--text-secondary)",
                lineHeight: 1.8, whiteSpace: "pre-line", fontStyle: "italic",
              }}>
                {identity.expression_guidance}
              </div>
            </section>
          )}

          {/* What Rem knows about you */}
          <section className="glass-panel" style={{ padding: 28 }}>
            <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ color: "var(--accent-secondary)" }}>◈</span> What Rem Knows About You
              <span style={{ marginLeft: "auto", fontSize: "0.625rem", color: "var(--text-muted)", fontWeight: 400 }}>
                {aboutUser.length} facts
              </span>
            </h2>

            {aboutUser.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", textAlign: "center", padding: "20px 0" }}>
                No facts learned yet. Chat with Rem to build her understanding of you.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {aboutUser.slice(0, 30).map((f: any, i: number) => (
                  <div key={i} style={{
                    padding: "8px 14px", borderRadius: 8,
                    background: "rgba(255,255,255,0.02)",
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                  }}>
                    <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", flex: 1 }}>
                      {f.fact}
                    </span>
                    <div style={{ display: "flex", gap: 12, alignItems: "center", flexShrink: 0, marginLeft: 12 }}>
                      <span style={{
                        fontSize: "0.625rem", fontFamily: "var(--font-mono)",
                        color: f.confidence > 0.7 ? "var(--accent-primary)" : "var(--text-muted)",
                      }}>
                        {Math.round(f.confidence * 100)}%
                      </span>
                      {f.timestamp && (
                        <span style={{ fontSize: "0.5625rem", color: "var(--text-muted)" }}>
                          {timeAgo(f.timestamp)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* User facts (key-value) */}
          {Object.keys(userFacts).length > 0 && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-secondary)" }}>◆</span> Learned Facts
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {Object.entries(userFacts).slice(0, 20).map(([key, val]: [string, any]) => (
                  <div key={key} style={{
                    padding: "10px 14px", borderRadius: 8,
                    background: "rgba(255,255,255,0.02)",
                    display: "flex", flexDirection: "column", gap: 2,
                  }}>
                    <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      {key.replace(/_/g, " ")}
                    </span>
                    <span style={{ fontSize: "0.8125rem", color: "var(--text-primary)", fontWeight: 500 }}>
                      {String(typeof val === "object" ? JSON.stringify(val) : val).substring(0, 80)}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* User evaluation */}
          {userEval && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-secondary)" }}>⟡</span> Rem&apos;s Evaluation of You
              </h2>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.7, whiteSpace: "pre-line" }}>
                {userEval}
              </p>
            </section>
          )}
        </div>
      )}

      {/* ════════════ INNER WORLD TAB ════════════ */}
      {activeTab === "inner" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Inner Monologue */}
          <section className="glass-panel" style={{ padding: 28 }}>
            <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ color: "var(--accent-tertiary)" }}>◉</span> Inner Monologue
            </h2>
            {innerMonologue.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", textAlign: "center", padding: "20px 0" }}>
                Rem hasn&apos;t formed any inner thoughts yet. Keep chatting to see what she thinks behind the scenes.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {innerMonologue.slice(-10).reverse().map((thought: any, i: number) => (
                  <div key={i} style={{
                    padding: "12px 16px", borderRadius: 10,
                    background: "rgba(232,121,249,0.04)", border: "1px solid rgba(232,121,249,0.08)",
                    fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.6,
                    fontStyle: "italic",
                  }}>
                    &ldquo;{typeof thought === "string" ? thought : thought.thought || JSON.stringify(thought)}&rdquo;
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Rumination */}
          {rumination && (
            <section className="glass-panel" style={{
              padding: 28,
              background: "linear-gradient(135deg, rgba(255,107,107,0.04), rgba(255,133,192,0.03))",
              borderColor: "rgba(255,107,107,0.1)",
            }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "#ff6b6b" }}>🌀</span> Ruminating About
              </h2>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.7, whiteSpace: "pre-line" }}>
                {typeof rumination === "string" ? rumination : JSON.stringify(rumination)}
              </p>
            </section>
          )}

          {/* Pending Eruption */}
          {pendingEruption && (
            <section className="glass-panel" style={{
              padding: 28,
              background: "linear-gradient(135deg, rgba(255,68,68,0.06), rgba(255,107,107,0.03))",
              borderColor: "rgba(255,68,68,0.15)",
            }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#ff4444", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span>⚡</span> Eruption Pending
              </h2>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.7 }}>
                {typeof pendingEruption === "string" ? pendingEruption : JSON.stringify(pendingEruption)}
              </p>
            </section>
          )}

          {/* Knowledge Holes */}
          {knowledgeHoles.length > 0 && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-secondary)" }}>?</span> Knowledge Gaps
                <span style={{ marginLeft: "auto", fontSize: "0.625rem", color: "var(--text-muted)", fontWeight: 400 }}>
                  {knowledgeHoles.length} holes
                </span>
              </h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {knowledgeHoles.map((hole: any, i: number) => (
                  <div key={i} style={{
                    padding: "8px 14px", borderRadius: 8,
                    background: "rgba(255,255,255,0.02)",
                    fontSize: "0.8125rem", color: "var(--text-secondary)",
                  }}>
                    {typeof hole === "string" ? hole : JSON.stringify(hole)}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Conversation Summary */}
          {complexity?.conversation_summary && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-secondary)" }}>◐</span> Conversation Summary
              </h2>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.7, whiteSpace: "pre-line" }}>
                {complexity.conversation_summary}
              </p>
            </section>
          )}

          {/* Emotional Undercurrents */}
          {complexity?.emotional_undercurrents && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-tertiary)" }}>~</span> Emotional Undercurrents
              </h2>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.7 }}>
                {typeof complexity.emotional_undercurrents === "string"
                  ? complexity.emotional_undercurrents
                  : JSON.stringify(complexity.emotional_undercurrents)}
              </p>
            </section>
          )}
        </div>
      )}

      {/* Refresh button */}
      <div style={{ marginTop: 32, textAlign: "center" }}>
        <button
          onClick={() => { setLoading(true); load(); }}
          style={{
            padding: "8px 24px", borderRadius: 999,
            border: "1px solid var(--border-subtle)",
            background: "rgba(255,255,255,0.02)",
            color: "var(--text-muted)", fontSize: "0.75rem",
            cursor: "pointer", transition: "all 0.2s",
          }}
          onMouseOver={(e) => { e.currentTarget.style.color = "var(--text-primary)"; e.currentTarget.style.borderColor = "rgba(151,117,250,0.3)"; }}
          onMouseOut={(e) => { e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
        >
          ↻ Refresh
        </button>
      </div>
    </div>
  );
}
