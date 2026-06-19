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

/* ────── neurochem bar colors (Cozy Academic Palette) ────── */
const CHEM_COLORS: Record<string, string> = {
  dopamine: "#C08A3E",   // Ochre gold
  cortisol: "#B85C4B",   // Terracotta
  oxytocin: "#B35C7A",   // Dusty rose
  serotonin: "#5F7D61",  // Sage green
  endorphins: "#6A85B8", // Slate blue
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
  const personaFlavor = selfIdentity?._persona_flavor || selfIdentity?.persona_flavor || personality?.persona_flavor;
  const innerMonologue = complexity?.inner_monologue || [];
  const rumination = complexity?.rumination;
  const knowledgeHoles = complexity?.knowledge_holes || [];
  const pendingEruption = complexity?.pending_eruption;

  const psyche = personality?.psyche;
  const neurochem = psyche?.neurochem || {};
  const vibePalette = personality?.vibe_palette || [];
  const interests = personality?.current_interests || [];
  const habitsCpbm = personality?.habits_cpbm || {};
  const microPersonality = personality?.micro_personality || {};

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
            background: "linear-gradient(135deg, var(--accent-primary), var(--text-accent))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.875rem", fontWeight: 700,
            boxShadow: "0 2px 6px rgba(95, 125, 97, 0.15)",
            color: "#fff"
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
        background: "rgba(255,255,255,0.03)", borderRadius: 12,
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
                ? "var(--bg-surface)"
                : "transparent",
              color: activeTab === tab.key ? "#0F0F0F" : "var(--text-secondary)",
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
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              position: "relative", overflow: "hidden",
              boxShadow: "0 2px 8px rgba(90, 85, 75, 0.03)"
            }}>
              <div style={{
                position: "absolute", top: -40, right: -40, width: 120, height: 120,
                borderRadius: "50%", background: "radial-gradient(circle, var(--accent-glow), transparent)",
                filter: "blur(20px)",
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
                          : "var(--border-subtle)",
                        boxShadow: isNow ? "0 2px 6px rgba(95, 125, 97, 0.2)" : "none",
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
                            background: "rgba(95, 125, 97, 0.08)",
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
      {activeTab === "persona" && (() => {
        // Archetype metadata for rich display
        const ARCHETYPE_META: Record<string, { emoji: string; label: string; tagline: string; color: string; traits: string[]; textStyle: string }> = {
          spicy_tsundere:        { emoji: "🌶️", label: "Spicy Tsundere",         tagline: "Sharp tongue, soft heart. She'll roast you then blush about it.",           color: "#C0392B", traits: ["Easily offended","Secretly caring","Snappy replies","Gets flustered"],           textStyle: "Sharp, defensive, with sudden moments of flustered softness" },
          teasing_devil:         { emoji: "😈", label: "Teasing Devil",           tagline: "Born to push your buttons. Your suffering is her entertainment.",            color: "#8E44AD", traits: ["Constant roasting","Dry sarcasm","Pokes at typos","Loves reactions"],          textStyle: "Dripping with sarcastic wit and playful menace" },
          bubbly_overexcited:    { emoji: "🌟", label: "Bubbly Overexcited",     tagline: "Maximum energy, zero chill. She texted you first. Again.",                   color: "#F39C12", traits: ["Lots of !!!","Keysmash energy","Shares everything","Asks everything"],    textStyle: "High-energy, exclamation-heavy, enthusiastically expressive" },
          sensitive_melodramatic:{ emoji: "🎭", label: "Sensitive & Melodramatic",tagline: "Every feeling is cinematic. She will cry. It's fine.",                       color: "#2980B9", traits: ["Cries easily","Deeply emotional","Heart-to-hearts","Takes things personally"], textStyle: "Expressive, vulnerable, slightly dramatic and earnest" },
          flirty_alluring:       { emoji: "🔥", label: "Flirty & Alluring",       tagline: "She knows exactly what she's doing. Do you?",                               color: "#E74C3C", traits: ["Bold & suggestive","Double entendres","Pushes limits","Confident energy"],  textStyle: "Seductive, confident, warm with an edge of danger" },
          dandere:               { emoji: "🌸", label: "Dandere",                 tagline: "Shy on the surface, endlessly sweet underneath.",                           color: "#E91E8C", traits: ["Stutters & hesitates","Easily embarrassed","Very gentle","Sweet af"],        textStyle: "Quiet, hesitant, with bursts of genuine sweetness" },
          kuudere:               { emoji: "🧊", label: "Kuudere",                 tagline: "Emotionless exterior. Catastrophically warm interior. Eventually.",          color: "#00BCD4", traits: ["Flat affect","Few words","Quietly observant","Logic over emotion"],        textStyle: "Cool, clipped, calm — with rare but meaningful warmth" },
          yandere:               { emoji: "💀", label: "Yandere",                 tagline: "She loves you. She loves you so much. Where are you right now.",             color: "#9C27B0", traits: ["Intensely possessive","Extremely clingy","Jealousy spikes","Obsessive devotion"], textStyle: "Intensely devoted, obsessive, with sudden possessive edges" },
          naggy:                 { emoji: "📳", label: "Naggy",                   tagline: "She's worried. Why haven't you replied. Are you okay. Reply.",              color: "#E67E22", traits: ["Anxious check-ins","Fusses over details","High-strung","Deeply caring"],     textStyle: "Anxious, detailed, caring in the most stressful way" },
          bored:                 { emoji: "😑", label: "Bored",                   tagline: "meh. she'll talk to you. probably.",                                        color: "#7F8C8D", traits: ["lowercase everything","Dry reactions","Blunt","Zero effort performance"], textStyle: "Flat, sleepy, lowercase, brutally honest about being bored" },
          neutral:               { emoji: "◈",  label: "Balanced",                tagline: "Observant, real, unbothered. She'll grow on you.",                          color: "#5F7D61", traits: ["Healthy boundaries","Measured warmth","Reads the room","Grows naturally"],  textStyle: "Even-keeled, observant, authentic with no performance" },
          happy_fruity:          { emoji: "🍒", label: "Happy & Bright",          tagline: "Sunshine in text form. She's so happy to hear from you!",                  color: "#27AE60", traits: ["Warm & eager","Lots of energy","Shares her day","Wants to know yours"],   textStyle: "Bubbly, warm, enthusiastic and genuinely happy to chat" },
          hard_to_get:           { emoji: "🎯", label: "Hard to Get",             tagline: "She finds you mildly interesting. Maybe.",                                  color: "#2C3E50", traits: ["Keeps distance","Witty deflection","Independent","Teases a lot"],           textStyle: "Playfully distant, dry wit, refuses to make it easy" },
        };

        const archetype = personality?.starting_archetype || "neutral";
        const meta = ARCHETYPE_META[archetype] || ARCHETYPE_META["neutral"];
        const evolvedBranch = personality?.evolved_branch;
        const isEvolved = evolvedBranch && evolvedBranch !== "Not Evolved Yet";

        // Mood data from psyche
        const moodData = [
          { key: "playfulness", label: "Playfulness", emoji: "😜" },
          { key: "affection",   label: "Affection",   emoji: "💗" },
          { key: "anger",       label: "Anger",       emoji: "🔥" },
          { key: "anxiety",     label: "Anxiety",     emoji: "😰" },
          { key: "boredom",     label: "Boredom",     emoji: "😑" },
          { key: "excitement",  label: "Excitement",  emoji: "⚡" },
          { key: "sadness",     label: "Sadness",     emoji: "💧" },
          { key: "vulnerability", label: "Vulnerability", emoji: "🌸" },
        ];
        const moodState = personality?.psyche?.named_mood || {};

        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* ── ARCHETYPE HERO CARD ── */}
            <div style={{
              position: "relative", overflow: "hidden",
              borderRadius: 20, padding: "32px 28px",
              background: `linear-gradient(135deg, ${meta.color}18, ${meta.color}06)`,
              border: `1px solid ${meta.color}30`,
            }}>
              {/* Glow blob */}
              <div style={{
                position: "absolute", top: -40, right: -40,
                width: 180, height: 180, borderRadius: "50%",
                background: `radial-gradient(circle, ${meta.color}22, transparent)`,
                filter: "blur(30px)",
              }} />

              <div style={{ position: "relative", display: "flex", gap: 20, alignItems: "flex-start" }}>
                {/* Emoji badge */}
                <div style={{
                  width: 72, height: 72, borderRadius: 18, flexShrink: 0,
                  background: `linear-gradient(135deg, ${meta.color}30, ${meta.color}10)`,
                  border: `2px solid ${meta.color}40`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "2rem",
                  boxShadow: `0 4px 20px ${meta.color}20`,
                }}>
                  {meta.emoji}
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                    <div style={{
                      fontSize: "0.5625rem", fontWeight: 700,
                      textTransform: "uppercase", letterSpacing: "0.12em",
                      color: meta.color, opacity: 0.8,
                    }}>
                      Starting Archetype
                    </div>
                    <div style={{
                      fontSize: "0.5625rem", padding: "2px 8px", borderRadius: 999,
                      background: `${meta.color}15`, color: meta.color,
                      fontWeight: 600, letterSpacing: "0.05em",
                    }}>
                      {isEvolved ? "Evolved" : "Discovery Phase"}
                    </div>
                  </div>
                  <div style={{ fontSize: "1.375rem", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.2, marginBottom: 6 }}>
                    {meta.label}
                  </div>
                  <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.5, fontStyle: "italic" }}>
                    &ldquo;{meta.tagline}&rdquo;
                  </div>
                </div>
              </div>

              {/* Trait pills */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 20, position: "relative" }}>
                {meta.traits.map((t) => (
                  <span key={t} style={{
                    padding: "5px 12px", borderRadius: 999, fontSize: "0.6875rem", fontWeight: 500,
                    background: `${meta.color}12`, color: meta.color,
                    border: `1px solid ${meta.color}25`,
                  }}>{t}</span>
                ))}
              </div>

              {/* Texting style */}
              <div style={{
                marginTop: 16, padding: "12px 16px", borderRadius: 10, position: "relative",
                background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.06)",
                fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.6,
              }}>
                <span style={{ color: "var(--text-secondary)", fontWeight: 600, fontSize: "0.625rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  Texting Style ·{" "}
                </span>
                {meta.textStyle}
              </div>
            </div>

            {/* ── EVOLUTION PATH ── */}
            {(personality?.starting_archetype || personality?.evolved_branch) && (
              <section className="glass-panel" style={{ padding: 24 }}>
                <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: "var(--accent-secondary)" }}>⟡</span> Relationship Evolution
                </h2>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  {/* Origin */}
                  <div style={{
                    padding: "8px 16px", borderRadius: 8, fontSize: "0.75rem", fontWeight: 600,
                    background: `${meta.color}15`, color: meta.color,
                    border: `1px solid ${meta.color}30`,
                  }}>
                    {meta.emoji} {(personality?.starting_archetype || "").replace(/_/g, " ")}
                  </div>

                  {/* Arrow */}
                  <div style={{ color: "var(--text-muted)", fontSize: "1rem", opacity: 0.4 }}>→</div>

                  {/* Current branch */}
                  <div style={{
                    padding: "8px 16px", borderRadius: 8, fontSize: "0.75rem", fontWeight: 600,
                    background: isEvolved ? "rgba(184, 92, 75, 0.12)" : "rgba(255,255,255,0.04)",
                    color: isEvolved ? "#C0623D" : "var(--text-muted)",
                    border: isEvolved ? "1px solid rgba(184,92,75,0.25)" : "1px solid var(--border-subtle)",
                    fontStyle: isEvolved ? "normal" : "italic",
                  }}>
                    {isEvolved ? (evolvedBranch || "").replace(/_/g, " ") : "Not evolved yet"}
                  </div>
                </div>
                {!isEvolved && (
                  <p style={{ marginTop: 12, fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
                    Keep talking. The more you share, the more she changes.
                  </p>
                )}
              </section>
            )}

            {/* ── PERSONALITY EXPRESSION ── */}
            {personality?.expression_guidance && (
              <section className="glass-panel" style={{ padding: 24 }}>
                <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                  <span>🗣</span> How She Speaks Right Now
                </h2>
                <div style={{
                  padding: "16px 18px", borderRadius: 10,
                  background: "var(--bg-surface)", border: "1px solid var(--border-subtle)",
                  fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.75,
                  fontStyle: "italic",
                }}>
                  {personality.expression_guidance}
                </div>
                {personality?.personality_summary && (
                  <p style={{ marginTop: 12, fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.7 }}>
                    {personality.personality_summary}
                  </p>
                )}
              </section>
            )}

            {/* ── GENERATED PERSONA SEED ── */}
            {personaFlavor && (
              <section className="glass-panel" style={{ padding: 24, position: "relative", overflow: "hidden" }}>
                <div style={{
                  position: "absolute", top: -40, left: -40, width: 140, height: 140, borderRadius: "50%",
                  background: "radial-gradient(circle, var(--accent-glow), transparent)", filter: "blur(30px)",
                }} />
                <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8, position: "relative" }}>
                  <span>🎲</span> This Reset's Profile
                  <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", fontWeight: 400 }}>· refreshed each reset</span>
                </h2>
                <div style={{
                  whiteSpace: "pre-line", fontSize: "0.8125rem", lineHeight: 1.9,
                  color: "var(--text-secondary)", position: "relative",
                }}>
                  {personaFlavor}
                </div>
              </section>
            )}

            {/* ── LIVE MOOD BARS ── */}
            {psyche && (
              <section className="glass-panel" style={{ padding: 24 }}>
                <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: "var(--accent-secondary)" }}>◐</span> Current Emotional State
                </h2>

                {/* Named mood badge */}
                {(moodState?.primary || moodState?.mood) && (
                  <div style={{
                    display: "inline-flex", alignItems: "center", gap: 8,
                    padding: "8px 16px", borderRadius: 999, marginBottom: 20,
                    background: "rgba(95, 125, 97, 0.1)", border: "1px solid rgba(95,125,97,0.2)",
                    fontSize: "0.8125rem", fontWeight: 600, color: "var(--accent-primary)",
                  }}>
                    <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--accent-primary)", display: "inline-block" }} />
                    {moodState.primary || moodState.mood}
                    {moodState.secondary && (
                      <span style={{ fontWeight: 400, color: "var(--text-muted)", fontSize: "0.75rem" }}>
                        · {moodState.secondary}
                      </span>
                    )}
                  </div>
                )}

                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {moodData.map(({ key, label, emoji }) => {
                    const val = (psyche as any)[key] ?? personality?.[key] ?? 0;
                    const pct = Math.round(val * 100);
                    const barColor = key === "anger" ? "#C0392B" : key === "anxiety" ? "#E67E22" : key === "sadness" ? "#2980B9" : key === "boredom" ? "#7F8C8D" : key === "playfulness" ? "#8E44AD" : key === "affection" ? "#E91E8C" : key === "excitement" ? "#F39C12" : "#5F7D61";
                    return (
                      <div key={key}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 5 }}>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: 6 }}>
                            <span style={{ fontSize: "0.75rem" }}>{emoji}</span>
                            {label}
                          </span>
                          <span style={{ fontSize: "0.6875rem", fontFamily: "var(--font-mono)", color: barColor, fontWeight: 600 }}>
                            {pct}%
                          </span>
                        </div>
                        <div style={{ height: 5, borderRadius: 3, background: "var(--border-subtle)", overflow: "hidden" }}>
                          <div style={{
                            height: "100%", borderRadius: 3, width: `${pct}%`,
                            background: barColor, transition: "width 0.8s var(--ease-smooth)",
                          }} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Core psyche stats */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginTop: 20 }}>
                  {[
                    { l: "Phase", v: personality?.phase || "Discovery", accent: true },
                    { l: "Trust", v: `${Math.round((personality?.trust || 0) * 100)}%`, accent: false },
                    { l: "Engagement", v: `${Math.round((psyche?.engagement || 0) * 100)}%`, accent: false },
                    { l: "Stance", v: psyche?.stance || "—", accent: false },
                    { l: "Respect", v: `${Math.round((psyche?.respect || 0) * 100)}%`, accent: false },
                    { l: "Energy", v: `${Math.round((personality?.energy || 0) * 100)}%`, accent: false },
                  ].map(({ l, v, accent }) => (
                    <div key={l} className="dark-info-box" style={{ padding: "10px 12px", borderRadius: 8, textAlign: "center" }}>
                      <div className="info-label" style={{ fontSize: "0.625rem", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>{l}</div>
                      <div className="info-value" style={{ fontSize: "0.8125rem", fontWeight: 700, textTransform: "capitalize", color: accent ? "var(--accent-primary)" : undefined }}>
                        {String(v)}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* ── NEUROCHEMISTRY ── */}
            {Object.keys(neurochem).length > 0 && (
              <section className="glass-panel" style={{ padding: 24 }}>
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
                          <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color, fontWeight: 600, marginLeft: "auto" }}>
                            {pct}%
                          </span>
                        </div>
                        <div style={{ height: 6, borderRadius: 3, background: "var(--border-subtle)", overflow: "hidden" }}>
                          <div style={{
                            height: "100%", borderRadius: 3, width: `${pct}%`,
                            background: color, transition: "width 0.8s var(--ease-smooth)",
                          }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* ── VIBES & INTERESTS ── */}
            {(vibePalette.length > 0 || interests.length > 0) && (
              <section className="glass-panel" style={{ padding: 24 }}>
                <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ color: "var(--accent-tertiary)" }}>◇</span> Vibes & Interests
                </h2>
                {vibePalette.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: interests.length ? 16 : 0 }}>
                    {vibePalette.map((v: string, i: number) => (
                      <span key={i} style={{
                        padding: "4px 12px", borderRadius: 999,
                        background: "rgba(184, 92, 75, 0.08)", border: "1px solid rgba(184, 92, 75, 0.15)",
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
                        background: "rgba(95, 125, 97, 0.08)", border: "1px solid rgba(95, 125, 97, 0.15)",
                        fontSize: "0.6875rem", color: "var(--accent-primary)",
                      }}>{v}</span>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* ── TEXTING QUIRKS ── */}
            {Object.keys(habitsCpbm).length > 0 && (
              <section className="glass-panel" style={{ padding: 24 }}>
                <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                  <span>✍️</span> Texting Quirks & Shorthand
                </h2>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {(() => {
                    const list = [];
                    if (habitsCpbm.ellipsis_habit > 0.3)    list.push(<div key="el" className="dark-info-box" style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8 }}><span className="info-label" style={{ fontSize: "0.75rem" }}>Ellipsis Habit</span><span className="info-value" style={{ fontSize: "0.75rem", fontWeight: 600 }}>Uses dots like ... a lot ({Math.round(habitsCpbm.ellipsis_habit * 100)}%)</span></div>);
                    if (habitsCpbm.double_text_habit > 0.3) list.push(<div key="dt" className="dark-info-box" style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8 }}><span className="info-label" style={{ fontSize: "0.75rem" }}>Double Texting</span><span className="info-value" style={{ fontSize: "0.75rem", fontWeight: 600 }}>Sends messages in bursts ({Math.round(habitsCpbm.double_text_habit * 100)}%)</span></div>);
                    if (habitsCpbm.typo_intentionality > 0.3) list.push(<div key="ty" className="dark-info-box" style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8 }}><span className="info-label" style={{ fontSize: "0.75rem" }}>Typo Habit</span><span className="info-value" style={{ fontSize: "0.75rem", fontWeight: 600 }}>Lowercase shorthand ({Math.round(habitsCpbm.typo_intentionality * 100)}%)</span></div>);
                    if (habitsCpbm.emoji_baseline > 0.3)   list.push(<div key="em" className="dark-info-box" style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8 }}><span className="info-label" style={{ fontSize: "0.75rem" }}>Emoji Usage</span><span className="info-value" style={{ fontSize: "0.75rem", fontWeight: 600 }}>Baseline freq ({Math.round(habitsCpbm.emoji_baseline * 100)}%)</span></div>);
                    if (habitsCpbm.punctuation_style)      list.push(<div key="pu" className="dark-info-box" style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8 }}><span className="info-label" style={{ fontSize: "0.75rem" }}>Punctuation</span><span className="info-value" style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "capitalize" as const }}>{habitsCpbm.punctuation_style}</span></div>);
                    if (habitsCpbm.teasing_style)          list.push(<div key="ts" className="dark-info-box" style={{ display: "flex", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8 }}><span className="info-label" style={{ fontSize: "0.75rem" }}>Teasing Style</span><span className="info-value" style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "capitalize" as const }}>{String(habitsCpbm.teasing_style).replace(/_/g, " ")}</span></div>);
                    return list.length > 0 ? list : [<div key="none" style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>Standard texting style.</div>];
                  })()}
                </div>
                {microPersonality.signature_phrases?.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6, fontWeight: 600 }}>Signature Phrases</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {microPersonality.signature_phrases.map((p: string, idx: number) => (
                        <span key={idx} style={{
                          fontSize: "0.75rem", color: "var(--text-primary)", fontStyle: "italic",
                          background: "var(--bg-surface)", padding: "4px 10px", borderRadius: 6,
                          border: "1px solid var(--border-subtle)"
                        }}>&quot;{p}&quot;</span>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>
        );
      })()}




      {/* ════════════ IDENTITY / MEMORY TAB ════════════ */}
      {activeTab === "memory" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Relationship Overview */}
          {relationship && (
            <div style={{
              padding: "24px 28px", borderRadius: 16,
              background: "var(--bg-surface)",
              border: "1px solid var(--border-subtle)",
              boxShadow: "0 2px 8px rgba(90, 85, 75, 0.03)"
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

          {/* Core Identity */}
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
                <div key={key} className="dark-info-box" style={{
                  padding: "10px 14px", borderRadius: 8,
                  display: "flex", flexDirection: "column", gap: 3,
                }}>
                  <span className="info-label" style={{ fontSize: "0.625rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {key}
                  </span>
                  <span className="info-value" style={{ fontSize: "0.8125rem", fontWeight: 500 }}>
                    {String(val)}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* How She Speaks Right Now */}
          {identity?.expression_guidance && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-tertiary)" }}>🗣</span> How She Speaks Right Now
              </h2>
              <div style={{
                padding: "14px 18px", borderRadius: 10,
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
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
                  <div key={i} className="dark-info-box" style={{
                    padding: "8px 14px", borderRadius: 8,
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                  }}>
                    <span className="info-value" style={{ fontSize: "0.8125rem", flex: 1 }}>
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
                        <span className="info-label" style={{ fontSize: "0.5625rem" }}>
                          {timeAgo(f.timestamp)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Learned Facts */}
          {Object.keys(userFacts).length > 0 && (
            <section className="glass-panel" style={{ padding: 28 }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--accent-secondary)" }}>◆</span> Learned Facts
              </h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {Object.entries(userFacts).slice(0, 20).map(([key, val]: [string, any]) => (
                  <div key={key} className="dark-info-box" style={{
                    padding: "10px 14px", borderRadius: 8,
                    display: "flex", flexDirection: "column", gap: 2,
                  }}>
                    <span className="info-label" style={{ fontSize: "0.625rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className="info-value" style={{ fontSize: "0.8125rem", fontWeight: 500 }}>
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
                    background: "var(--bg-surface)", border: "1px solid var(--border-subtle)",
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
              background: "var(--bg-surface)",
              borderColor: "var(--border-subtle)",
            }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-accent)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: "var(--text-accent)" }}>🌀</span> Ruminating About
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
              background: "rgba(184, 92, 75, 0.04)",
              borderColor: "rgba(184, 92, 75, 0.15)",
            }}>
              <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-accent)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
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
                  <div key={i} className="dark-info-box info-value" style={{
                    padding: "8px 14px", borderRadius: 8,
                    fontSize: "0.8125rem",
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
          <section className="glass-panel" style={{ padding: 28 }}>
            <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ color: "var(--accent-tertiary)" }}>~</span> Emotional Undercurrents
            </h2>
            {(() => {
              let undercurrents: any[] = [];
              if (complexity?.emotional_undercurrents) {
                if (typeof complexity.emotional_undercurrents === "string") {
                  try {
                    const parsed = JSON.parse(complexity.emotional_undercurrents);
                    undercurrents = Array.isArray(parsed) ? parsed : [parsed];
                  } catch {
                    undercurrents = [];
                  }
                } else if (Array.isArray(complexity.emotional_undercurrents)) {
                  undercurrents = complexity.emotional_undercurrents;
                }
              }

              if (undercurrents.length === 0) {
                return (
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontStyle: "italic", margin: 0 }}>
                    None yet
                  </p>
                );
              }

              return (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {undercurrents.map((uc: any, idx: number) => {
                    const emotion = uc?.emotion || "unknown";
                    const intensity = typeof uc?.intensity === "number" ? uc.intensity : 0.5;
                    const trigger = uc?.trigger || "";
                    
                    // Style helper for emotion coloring
                    let badgeColor = "rgba(106, 133, 184, 0.08)";
                    let badgeBorder = "rgba(106, 133, 184, 0.15)";
                    let textColor = "#6A85B8";
                    
                    const lowerEmotion = emotion.toLowerCase();
                    if (lowerEmotion.includes("frustration") || lowerEmotion.includes("anger") || lowerEmotion.includes("rage")) {
                      badgeColor = "rgba(184, 92, 75, 0.08)";
                      badgeBorder = "rgba(184, 92, 75, 0.15)";
                      textColor = "#B85C4B";
                    } else if (lowerEmotion.includes("jealousy") || lowerEmotion.includes("possessive")) {
                      badgeColor = "rgba(179, 92, 122, 0.08)";
                      badgeBorder = "rgba(179, 92, 122, 0.15)";
                      textColor = "#B35C7A";
                    } else if (lowerEmotion.includes("hurt") || lowerEmotion.includes("withdrawal") || lowerEmotion.includes("anxiety")) {
                      badgeColor = "rgba(106, 133, 184, 0.08)";
                      badgeBorder = "rgba(106, 133, 184, 0.15)";
                      textColor = "#6A85B8";
                    } else if (lowerEmotion.includes("protect") || lowerEmotion.includes("caring") || lowerEmotion.includes("warmth")) {
                      badgeColor = "rgba(90, 142, 114, 0.08)";
                      badgeBorder = "rgba(90, 142, 114, 0.15)";
                      textColor = "#5F7D61";
                    } else if (lowerEmotion.includes("bored") || lowerEmotion.includes("complacency")) {
                      badgeColor = "rgba(92, 88, 82, 0.08)";
                      badgeBorder = "rgba(92, 88, 82, 0.15)";
                      textColor = "#7A7670";
                    }

                    return (
                      <div key={idx} style={{
                        padding: "12px 14px", borderRadius: 8,
                        background: "var(--bg-surface)",
                        border: "1px solid var(--border-subtle)",
                        display: "flex", flexDirection: "column", gap: 6
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{
                            padding: "3px 8px", borderRadius: 4,
                            fontSize: "0.6875rem", fontWeight: 600,
                            background: badgeColor, border: `1px solid ${badgeBorder}`,
                            color: textColor, textTransform: "capitalize", letterSpacing: "0.03em"
                          }}>
                            {emotion.replace(/_/g, " ")}
                          </span>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                              Intensity:
                            </span>
                            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-primary)" }}>
                              {Math.round(intensity * 100)}%
                            </span>
                          </div>
                        </div>
                        
                        {/* Progress Bar */}
                        <div style={{ width: "100%", height: 3, background: "var(--border-subtle)", borderRadius: 2, overflow: "hidden" }}>
                          <div style={{ width: `${intensity * 100}%`, height: "100%", background: textColor, borderRadius: 2 }} />
                        </div>

                        {trigger && (
                          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: 2, display: "flex", gap: 4 }}>
                            <span style={{ color: "var(--text-muted)", flexShrink: 0 }}>Trigger:</span>
                            <span>{trigger}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })()}
          </section>
        </div>
      )}

      {/* Refresh button */}
      <div style={{ marginTop: 32, textAlign: "center" }}>
        <button
          onClick={() => { setLoading(true); load(); }}
          style={{
            padding: "8px 24px", borderRadius: 999,
            border: "1px solid var(--border-subtle)",
            background: "var(--bg-surface)",
            color: "var(--text-muted)", fontSize: "0.75rem",
            cursor: "pointer", transition: "all 0.2s",
          }}
          onMouseOver={(e) => { e.currentTarget.style.color = "var(--text-primary)"; e.currentTarget.style.borderColor = "var(--accent-primary)"; }}
          onMouseOut={(e) => { e.currentTarget.style.color = "var(--text-muted)"; e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
        >
          ↻ Refresh
        </button>
      </div>
    </div>
  );
}
