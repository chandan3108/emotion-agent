"use client";

import { useEffect, useState } from "react";
import { getDiary, type DiaryData } from "@/lib/gameApi";

export default function DiaryPage() {
  const [diary, setDiary] = useState<DiaryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDiary()
      .then(setDiary)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state" style={{ height: "100vh" }}>
        <div className="empty-state-orb" />
        <span style={{ fontSize: "0.75rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)" }}>
          Opening diary...
        </span>
      </div>
    );
  }

  return (
    <div className="diary-page page-container" style={{ padding: "40px 36px" }}>
      {/* Header */}
      <div className="fade-in-up" style={{ marginBottom: 36, textAlign: "center" }}>
        <div style={{
          display: "inline-flex", alignItems: "center", gap: 10,
          marginBottom: 8,
        }}>
          <span style={{
            width: 32, height: 32, borderRadius: "50%",
            background: "linear-gradient(135deg, var(--accent-primary), var(--text-accent))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.875rem", boxShadow: "0 2px 6px rgba(95, 125, 97, 0.15)",
            color: "#fff"
          }}>◉</span>
          <h1 style={{
            fontFamily: "'Caveat', cursive",
            fontSize: "2rem",
            fontWeight: 700,
            color: "var(--text-primary)",
            letterSpacing: "0.02em",
          }}>
            Rem&apos;s Diary
          </h1>
        </div>
        <p style={{
          color: "var(--text-muted)", lineHeight: 1.6,
          fontFamily: "'Caveat', cursive", fontSize: "1rem",
        }}>
          Private thoughts she writes about your conversations
        </p>
      </div>

      <div className="diary-book">
        {/* Empty State */}
        {(!diary || diary.entries.length === 0) && (
          <div className="notebook-container fade-in-up stagger-1">
            <div className="notebook-spirals">
              {[...Array(6)].map((_, idx) => (
                <div key={idx} className="notebook-spiral-ring" />
              ))}
            </div>
            <div className="notebook-page" style={{ padding: "48px 32px", textAlign: "center" }}>
              <div style={{ fontSize: "2.5rem", marginBottom: 16 }}>📖</div>
              <p style={{ color: "#8C7E66", fontFamily: "'Caveat', cursive", fontSize: "1.35rem", textAlign: "center" }}>
                The pages are still blank... Keep talking — she&apos;ll start writing soon.
              </p>
            </div>
          </div>
        )}

        {/* Entries */}
        {diary && diary.entries.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
            {diary.entries.map((entry, i) => (
              <div
                key={i}
                className={`notebook-container fade-in-up stagger-${Math.min(i + 1, 6)}`}
              >
                {/* Spiral Rings */}
                <div className="notebook-spirals">
                  {[...Array(6)].map((_, idx) => (
                    <div key={idx} className="notebook-spiral-ring" />
                  ))}
                </div>

                {/* Notebook Page */}
                <div className="notebook-page">
                  {/* Handwritten Date Header */}
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    borderBottom: "1px solid #E3DBC7",
                    paddingBottom: 6,
                    marginBottom: 16,
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.8125rem",
                    color: "#8C8370",
                    letterSpacing: "0.02em"
                  }}>
                    <span style={{ fontWeight: 600, textTransform: "uppercase", fontSize: "0.75rem" }}>
                      {new Date(entry.timestamp).toLocaleDateString("en-IN", { weekday: "long" })}
                    </span>
                    <span>
                      {new Date(entry.timestamp).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "long",
                        year: "numeric",
                      })}
                    </span>
                  </div>

                  {/* Ruled content */}
                  <div style={{ minHeight: 96 }}>
                    <p>{entry.content}</p>
                  </div>

                  {/* Metadata at bottom right */}
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginTop: 16,
                    borderTop: "1px solid #E3DBC7",
                    paddingTop: 8,
                    fontSize: "0.75rem"
                  }}>
                    <span className={`phase-badge phase-${entry.phase.toLowerCase()}`} style={{ fontSize: "0.5625rem" }}>
                      {entry.phase}
                    </span>
                    {entry.has_milestone && entry.milestone_text && (
                      <span style={{ fontStyle: "italic", color: "#B85C4B", fontWeight: 500 }}>
                        ✦ {entry.milestone_text}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Locked Teaser */}
        {(!diary || !["Steady", "Deep", "Bonded"].includes(diary.access_level)) && (
          <div className="notebook-container fade-in-up" style={{ marginTop: 32 }}>
            <div className="notebook-spirals">
              {[...Array(6)].map((_, idx) => (
                <div key={idx} className="notebook-spiral-ring" />
              ))}
            </div>

            <div className="notebook-page" style={{ position: "relative", overflow: "hidden" }}>
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                borderBottom: "1px solid #E3DBC7",
                paddingBottom: 6,
                marginBottom: 16,
                fontFamily: "var(--font-sans)",
                fontSize: "0.8125rem",
                color: "#8C8370",
                letterSpacing: "0.02em"
              }}>
                <span style={{ fontWeight: 600, textTransform: "uppercase", fontSize: "0.75rem" }}>
                  Locked Entry
                </span>
                <span>
                  ???
                </span>
              </div>
              <p style={{ filter: "blur(2.5px)", opacity: 0.5 }}>
                Today something shifted. I don&apos;t know how to explain it, but when they
                said that thing about the stars... it felt different. Like they actually
                meant it. I don&apos;t usually trust that feeling but this time...
              </p>
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: "rgba(250, 246, 238, 0.4)",
                  borderRadius: "inherit",
                }}
              >
                <div style={{ textAlign: "center", background: "#FAF6EE", padding: "16px 24px", borderRadius: 8, border: "1px solid #D6C8AF", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
                  <div style={{ fontSize: "1.25rem", marginBottom: 6, opacity: 0.8 }}>🔒</div>
                  <div
                    style={{
                      fontFamily: "var(--font-sans)",
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      color: "#5C5243",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em"
                    }}
                  >
                    Deeper Connection Required
                  </div>
                  <div
                    style={{
                      fontFamily: "'Caveat', cursive",
                      fontSize: "1.05rem",
                      color: "#8C7E66",
                      marginTop: 4
                    }}
                  >
                    Unlock Rem&apos;s personal diary entries in the Steady phase
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
