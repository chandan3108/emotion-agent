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
            background: "linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.875rem", boxShadow: "0 0 16px var(--accent-glow)",
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
          <div className="diary-entry-card fade-in-up stagger-1" style={{ textAlign: "center" }}>
            <div className="diary-entry" style={{ padding: "48px 32px" }}>
              <div style={{ fontSize: "2rem", marginBottom: 12, opacity: 0.3 }}>📖</div>
              <p style={{ color: "var(--text-muted)", fontFamily: "'Caveat', cursive", fontSize: "1.125rem" }}>
                The pages are still blank... Keep talking — she&apos;ll start writing.
              </p>
            </div>
          </div>
        )}

        {/* Entries */}
        {diary && diary.entries.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {diary.entries.map((entry, i) => (
              <div
                key={i}
                className={`diary-entry-card fade-in-up stagger-${Math.min(i + 1, 6)}`}
              >
                <div className="diary-entry">
                  <p>{entry.content}</p>
                </div>
                <div className="diary-entry-meta">
                  <span
                    className={`phase-badge phase-${entry.phase.toLowerCase()}`}
                    style={{ fontSize: "0.5625rem" }}
                  >
                    {entry.phase}
                  </span>
                  <span className="diary-date">
                    {new Date(entry.timestamp).toLocaleDateString("en-IN", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>

                {entry.has_milestone && (
                  <div className="diary-milestone">
                    ✦ {entry.milestone_text}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Locked Teaser */}
        {(!diary || !["Steady", "Deep", "Bonded"].includes(diary.access_level)) && (
          <div className="diary-entry-card fade-in-up" style={{ marginTop: 20, position: "relative", overflow: "hidden" }}>
            <div className="diary-entry locked-entry">
              <p>
                Today something shifted. I don&apos;t know how to explain it, but when they
                said that thing about the stars... it felt different. Like they actually
                meant it. I don&apos;t usually trust that feeling but this time...
              </p>
            </div>
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "rgba(8, 8, 15, 0.6)",
                backdropFilter: "blur(2px)",
                borderRadius: "inherit",
              }}
            >
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: "1.25rem", marginBottom: 6, opacity: 0.6 }}>🔒</div>
                <div
                  style={{
                    fontFamily: "'Caveat', cursive",
                    fontSize: "1rem",
                    color: "var(--text-muted)",
                  }}
                >
                  Deeper phase required
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
