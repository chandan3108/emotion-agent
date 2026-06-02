"use client";

import { useEffect, useState } from "react";
import { getPostcards, getAchievements, type PostcardEntry } from "@/lib/gameApi";

export default function ScrapbookPage() {
  const [postcards, setPostcards] = useState<PostcardEntry[]>([]);
  const [unlocked, setUnlocked] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [flippedCards, setFlippedCards] = useState<Record<string, boolean>>({});

  useEffect(() => {
    Promise.all([getPostcards(), getAchievements()])
      .then(([pcRes, achRes]) => {
        if (pcRes && pcRes.postcards) {
          setPostcards(pcRes.postcards);
        }
        if (achRes && achRes.unlocked) {
          setUnlocked(achRes.unlocked);
        }
      })
      .catch((err) => {
        console.error("Failed to load scrapbook items:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const toggleFlip = (id: string) => {
    setFlippedCards((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  function renderLocationSVG(location: string) {
    const loc = location.toLowerCase();
    if (loc.includes("cafe") || loc.includes("coffee") || loc.includes("starbucks")) {
      return (
        <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", display: "block" }}>
          <defs>
            <linearGradient id="cafeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f39c12" />
              <stop offset="100%" stopColor="#d35400" />
            </linearGradient>
          </defs>
          <rect width="100" height="100" fill="url(#cafeGrad)" />
          <path d="M42,20 Q45,15 42,10 T42,0 M50,20 Q53,15 50,10 T50,0 M58,20 Q61,15 58,10 T58,0" stroke="#fff" strokeWidth="2" fill="none" strokeLinecap="round" opacity="0.6" />
          <path d="M30,30 L70,30 C68,55 60,65 50,65 C40,65 32,55 30,30 Z" fill="#ffffff" />
          <path d="M70,36 C75,36 78,39 78,43 C78,47 75,50 70,50" stroke="#ffffff" strokeWidth="4" fill="none" />
          <ellipse cx="50" cy="30" rx="20" ry="4" fill="#6f4e37" />
          <text x="50" y="85" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle" letterSpacing="1">COZY CAFE</text>
        </svg>
      );
    }
    if (loc.includes("movie") || loc.includes("cinema") || loc.includes("theater") || loc.includes("show")) {
      return (
        <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", display: "block" }}>
          <defs>
            <linearGradient id="movieGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#9b59b6" />
              <stop offset="100%" stopColor="#2c3e50" />
            </linearGradient>
          </defs>
          <rect width="100" height="100" fill="url(#movieGrad)" />
          <rect x="25" y="30" width="30" height="45" rx="2" fill="#e74c3c" transform="rotate(-15 40 52)" />
          <rect x="45" y="25" width="30" height="45" rx="2" fill="#f1c40f" transform="rotate(10 60 47)" />
          <circle cx="40" cy="52" r="3" fill="#fff" />
          <circle cx="60" cy="47" r="3" fill="#2c3e50" />
          <text x="50" y="85" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle" letterSpacing="1">CINEMA NIGHT</text>
        </svg>
      );
    }
    if (loc.includes("park") || loc.includes("garden") || loc.includes("walk") || loc.includes("beach") || loc.includes("lake") || loc.includes("nature") || loc.includes("outdoors")) {
      return (
        <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", display: "block" }}>
          <defs>
            <linearGradient id="parkGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3498db" />
              <stop offset="50%" stopColor="#a8e6cf" />
              <stop offset="100%" stopColor="#1ebd60" />
            </linearGradient>
          </defs>
          <rect width="100" height="100" fill="url(#parkGrad)" />
          <circle cx="80" cy="25" r="8" fill="#f1c40f" opacity="0.9" />
          <polygon points="0,70 30,40 60,70" fill="#2e7d32" opacity="0.8" />
          <polygon points="40,75 70,45 100,75" fill="#1b5e20" opacity="0.9" />
          <path d="M0,75 Q25,70 50,75 T100,75 L100,100 L0,100 Z" fill="#81c784" />
          <text x="50" y="90" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle" letterSpacing="1">OUTDOORS</text>
        </svg>
      );
    }
    if (loc.includes("dinner") || loc.includes("restaurant") || loc.includes("food") || loc.includes("bbq") || loc.includes("barbecue") || loc.includes("eat")) {
      return (
        <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", display: "block" }}>
          <defs>
            <linearGradient id="foodGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#e74c3c" />
              <stop offset="100%" stopColor="#c0392b" />
            </linearGradient>
          </defs>
          <rect width="100" height="100" fill="url(#foodGrad)" />
          <circle cx="50" cy="45" r="22" fill="#fff" opacity="0.9" />
          <circle cx="50" cy="45" r="16" fill="#f3f3f3" />
          <path d="M38,32 L38,48 M35,32 L35,42 M41,32 L41,42" stroke="#7f8c8d" strokeWidth="2" strokeLinecap="round" />
          <path d="M62,30 L62,50" stroke="#7f8c8d" strokeWidth="2.5" strokeLinecap="round" />
          <text x="50" y="85" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle" letterSpacing="1">FINE DINING</text>
        </svg>
      );
    }
    return (
      <svg viewBox="0 0 100 100" style={{ width: "100%", height: "100%", display: "block" }}>
        <defs>
          <linearGradient id="defaultGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#e1306c" />
            <stop offset="50%" stopColor="#c13584" />
            <stop offset="100%" stopColor="#833ab4" />
          </linearGradient>
        </defs>
        <rect width="100" height="100" fill="url(#defaultGrad)" />
        <circle cx="50" cy="40" r="15" fill="#fff" opacity="0.9" />
        <path d="M0,65 Q25,60 50,65 T100,65 L100,100 L0,100 Z" fill="#ffffff" opacity="0.2" />
        <path d="M0,75 Q25,72 50,75 T100,75 L100,100 L0,100 Z" fill="#ffffff" opacity="0.1" />
        <text x="50" y="88" fill="#fff" fontSize="8" fontWeight="bold" textAnchor="middle" letterSpacing="1">MEMORIES</text>
      </svg>
    );
  }

  if (loading) {
    return (
      <div className="empty-state" style={{ height: "100vh" }}>
        <div className="empty-state-orb" />
        <span style={{ fontSize: "0.75rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)" }}>
          Loading Scrapbook...
        </span>
      </div>
    );
  }

  return (
    <div className="scrapbook-page page-container" style={{ padding: "40px 36px" }}>
      <style dangerouslySetInnerHTML={{ __html: `
        .scrapbook-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
          gap: 40px;
          padding: 20px 0;
          justify-items: center;
        }

        .postcard-container {
          perspective: 1000px;
          width: 260px;
          height: 320px;
          cursor: pointer;
        }

        .postcard-inner {
          position: relative;
          width: 100%;
          height: 100%;
          transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.2);
          transform-style: preserve-3d;
        }

        .postcard-container.flipped .postcard-inner {
          transform: rotateY(180deg);
        }

        .postcard-front, .postcard-back {
          position: absolute;
          width: 100%;
          height: 100%;
          backface-visibility: hidden;
          border-radius: 12px;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
          background: #ffffff;
          padding: 14px 14px 20px 14px;
          display: flex;
          flex-direction: column;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .postcard-front {
          color: #1a1a2e;
        }

        .postcard-back {
          transform: rotateY(180deg);
          background: #fdfbf7;
          border: 1px solid #e2d7be;
          color: #2b2b2b;
          background-image: radial-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 0);
          background-size: 16px 16px;
        }

        .polaroid-img-area {
          flex: 1;
          border-radius: 6px;
          overflow: hidden;
          position: relative;
          border: 1px solid #e1e1e1;
        }

        .polaroid-label {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          margin-top: 10px;
          text-align: center;
        }

        .polaroid-title {
          font-weight: 700;
          font-size: 0.9rem;
          color: #1a1a2e;
          text-transform: capitalize;
        }

        .polaroid-location {
          font-size: 0.72rem;
          color: #7b7b93;
          margin-top: 2px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .postcard-stamp {
          position: absolute;
          top: 14px;
          right: 14px;
          width: 44px;
          height: 52px;
          border: 1px dashed #9e8a60;
          border-radius: 2px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.125rem;
          transform: rotate(8deg);
          opacity: 0.7;
          background: rgba(158, 138, 96, 0.03);
          color: #9e8a60;
        }

        .postcard-divider {
          width: 1px;
          background: #e2d7be;
          height: 75%;
          position: absolute;
          left: 50%;
          top: 12%;
        }

        .postcard-message-area {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0 10px;
          text-align: center;
          font-family: var(--font-caveat), 'Caveat', cursive;
          font-size: 1.625rem;
          line-height: 1.35;
          color: #3b3a5f;
          transform: rotate(-1deg);
        }

        .postcard-date {
          font-family: var(--font-caveat), 'Caveat', cursive;
          font-size: 1.25rem;
          color: #8c7e65;
          text-align: right;
          border-top: 1px dashed rgba(226, 215, 190, 0.6);
          padding-top: 6px;
        }

        .postcard-tag {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 0.625rem;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: #9e8a60;
          position: absolute;
          top: 14px;
          left: 14px;
        }
      ` }} />

      {/* Header */}
      <div className="fade-in-up" style={{ marginBottom: 36, textAlign: "center" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <span style={{
            width: 32, height: 32, borderRadius: "50%",
            background: "linear-gradient(135deg, var(--accent-primary), var(--accent-tertiary))",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.875rem", boxShadow: "0 0 16px var(--accent-glow)",
          }}>📸</span>
          <h1 style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: "1.75rem",
            fontWeight: 700,
            color: "var(--text-primary)",
            letterSpacing: "-0.03em",
          }}>
            Date Scrapbook
          </h1>
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", maxWidth: 460, margin: "0 auto", lineHeight: 1.6 }}>
          Keepsake postcards Rem collected from your dates together. Click a postcard to read her handwritten note on the back.
        </p>
      </div>

      {/* Achievements Section */}
      <div className="fade-in-up" style={{
        margin: "0 auto 36px auto",
        maxWidth: 700,
        background: "rgba(255, 255, 255, 0.02)",
        borderRadius: "var(--radius-md)",
        padding: "16px 20px",
        border: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        gap: 10
      }}>
        <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
          🏆 Challenge Medals
        </div>
        <div style={{ display: "flex", gap: 12, justifyContent: "space-between" }}>
          {[
            { id: "debate_champion", title: "Debate Champion", icon: "👑", desc: "Won a Debate Battle" },
            { id: "win_over_promise", title: "Trust Rebuilder", icon: "🤝", desc: "Won 'Broken Promise'" },
            { id: "win_over_ghost", title: "Anger Tamer", icon: "🔥", desc: "Won 'Silent Treatment'" },
            { id: "win_over_stranger", title: "Heart Melter", icon: "❄️", desc: "Won 'Cold Stranger'" }
          ].map(ach => {
            const hasMedal = unlocked.includes(ach.id);
            return (
              <div key={ach.id} style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 12px",
                background: hasMedal ? "rgba(16, 185, 129, 0.05)" : "rgba(255,255,255,0.01)",
                borderRadius: "var(--radius-md)",
                border: hasMedal ? "1px solid rgba(16, 185, 129, 0.2)" : "1px solid var(--border-subtle)",
                opacity: hasMedal ? 1 : 0.35,
                fontSize: "0.75rem",
              }}>
                <span style={{ fontSize: "1.125rem" }}>{hasMedal ? ach.icon : "🔒"}</span>
                <div>
                  <div style={{ fontWeight: 600, color: hasMedal ? "var(--text-primary)" : "var(--text-muted)" }}>{ach.title}</div>
                  <div style={{ fontSize: "0.5625rem", color: "var(--text-muted)", marginTop: 1 }}>{hasMedal ? "Unlocked" : "Locked"}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {postcards.length === 0 ? (
        <div className="fade-in-up" style={{ textAlign: "center", padding: "80px 20px" }}>
          <div style={{ fontSize: "3rem", marginBottom: 16, opacity: 0.3 }}>📸</div>
          <h3 style={{ fontSize: "1.125rem", color: "var(--text-primary)", marginBottom: 8 }}>Scrapbook is Empty</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", maxWidth: 320, margin: "0 auto", lineHeight: 1.5 }}>
            Go on dates with Rem using Date Mode! When a date finishes, she will clip a postcard keepsake here.
          </p>
        </div>
      ) : (
        <div className="scrapbook-grid">
          {postcards.map((pc, idx) => {
            const isFlipped = !!flippedCards[pc.id];
            return (
              <div
                key={pc.id}
                className={`postcard-container fade-in-up stagger-${Math.min(idx + 1, 6)} ${isFlipped ? "flipped" : ""}`}
                onClick={() => toggleFlip(pc.id)}
              >
                <div className="postcard-inner">
                  {/* FRONT */}
                  <div className="postcard-front">
                    <div className="polaroid-img-area">
                      {renderLocationSVG(pc.location)}
                    </div>
                    <div className="polaroid-label">
                      <span className="polaroid-title">{pc.activity}</span>
                      <span className="polaroid-location">{pc.location}</span>
                    </div>
                  </div>

                  {/* BACK */}
                  <div className="postcard-back">
                    <div className="postcard-tag">POST CARD</div>
                    <div className="postcard-stamp">📮</div>
                    <div className="postcard-divider" />
                    <div className="postcard-message-area">
                      <p>&ldquo;{pc.note}&rdquo;</p>
                    </div>
                    <div className="postcard-date">
                      {new Date(pc.timestamp).toLocaleDateString("en-IN", {
                        month: "short",
                        day: "numeric",
                        year: "numeric"
                      })}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
