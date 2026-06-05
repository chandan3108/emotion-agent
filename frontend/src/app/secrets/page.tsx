"use client";
import { useEffect, useState } from "react";
import { getSecrets } from "@/lib/gameApi";

export default function SecretsPage() {
  const [secrets, setSecrets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSecrets()
      .then((res) => {
        if (res && res.secrets) {
          setSecrets(res.secrets);
        }
      })
      .catch((err) => {
        console.error("Failed to load secrets:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  function getHearts(intensity: number) {
    const num = Math.round(intensity * 5);
    return "💖".repeat(num) + "🖤".repeat(5 - num);
  }

  if (loading) {
    return (
      <div className="empty-state" style={{ height: "100vh", background: "radial-gradient(circle at center, #1b0a1a 0%, #08020b 100%)" }}>
        <div className="empty-state-orb" style={{ background: "rgba(244, 63, 94, 0.25)", boxShadow: "0 0 40px rgba(244, 63, 94, 0.4)" }} />
        <span style={{ fontSize: "0.75rem", letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)" }}>
          Opening Secrets Vault...
        </span>
      </div>
    );
  }

  return (
    <div className="secrets-page page-container" style={{ 
      padding: "40px 36px", 
      background: "radial-gradient(circle at top, #1c0915 0%, #09030b 100%)",
      minHeight: "100vh"
    }}>
      {/* Header */}
      <div className="fade-in-up" style={{ marginBottom: 44, textAlign: "center" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <span style={{
            width: 40, height: 40, borderRadius: "50%",
            background: "linear-gradient(135deg, #f43f5e, #be123c)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "1.125rem", boxShadow: "0 0 20px rgba(244, 63, 94, 0.5)",
          }}>🫦</span>
          <h1 style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: "2rem",
            fontWeight: 700,
            color: "#fff",
            letterSpacing: "-0.03em",
            textShadow: "0 0 10px rgba(244, 63, 94, 0.3)"
          }}>
            Rem&apos;s Secrets
          </h1>
        </div>
        <p style={{ color: "#f43f5e", opacity: 0.8, fontSize: "0.875rem", maxWidth: 460, margin: "0 auto", lineHeight: 1.6, fontStyle: "italic" }}>
          &ldquo;things spoken in the shadows, kept close to the heart.&rdquo;
        </p>
      </div>

      {secrets.length === 0 ? (
        <div className="fade-in-up" style={{ 
          textAlign: "center", 
          padding: "80px 20px", 
          maxWidth: 420, 
          margin: "0 auto",
          background: "rgba(244, 63, 94, 0.02)",
          borderRadius: 16,
          border: "1px dashed rgba(244, 63, 94, 0.15)",
          boxShadow: "inset 0 0 20px rgba(244, 63, 94, 0.01)"
        }}>
          <div style={{ fontSize: "3.5rem", marginBottom: 20, filter: "grayscale(1) brightness(0.6) sepia(1) hue-rotate(310deg)" }}>🥀</div>
          <h3 style={{ fontSize: "1.125rem", color: "#f43f5e", marginBottom: 10, fontWeight: 600 }}>The Vault is Sealed</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", lineHeight: 1.6 }}>
            Spicy and intimate memories have not been logged yet. Launch a **Spicy Chat** in Mini-Games and end the session to extract her most romantic confessions.
          </p>
        </div>
      ) : (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 28,
          maxWidth: 1000,
          margin: "0 auto"
        }}>
          {secrets.map((sec, idx) => (
            <div 
              key={sec.id || idx} 
              className="fade-in-up" 
              style={{
                background: "linear-gradient(145deg, rgba(30, 10, 20, 0.9) 0%, rgba(12, 4, 10, 0.95) 100%)",
                borderRadius: 14,
                border: "1px solid rgba(244, 63, 94, 0.15)",
                padding: "24px 20px",
                display: "flex",
                flexDirection: "column",
                gap: 16,
                boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(254, 244, 244, 0.05)",
                position: "relative",
                overflow: "hidden"
              }}
            >
              {/* Glowing background hint */}
              <div style={{
                position: "absolute",
                top: "-30px",
                right: "-30px",
                width: 90,
                height: 90,
                borderRadius: "50%",
                background: "radial-gradient(circle, rgba(244, 63, 94, 0.15) 0%, transparent 70%)",
                pointerEvents: "none"
              }} />

              {/* Intensity Hearts */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "#f43f5e", fontWeight: 600 }}>
                  {getHearts(sec.intensity || 0.6)}
                </span>
                <span style={{ fontSize: "0.5625rem", color: "var(--text-muted)" }}>
                  {sec.timestamp ? new Date(sec.timestamp).toLocaleDateString("en-IN", { month: "short", day: "numeric" }) : ""}
                </span>
              </div>

              {/* Confession text */}
              <div style={{
                fontFamily: "var(--font-caveat), 'Caveat', cursive",
                fontSize: "1.75rem",
                lineHeight: 1.3,
                color: "#ffe4e6",
                textAlign: "center",
                padding: "8px 4px",
                textShadow: "0 2px 4px rgba(0,0,0,0.3)"
              }}>
                &ldquo;{sec.quote}&rdquo;
              </div>

              {/* Context label */}
              <div style={{ 
                marginTop: "auto", 
                borderTop: "1px solid rgba(244, 63, 94, 0.1)", 
                paddingTop: 12,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}>
                <span style={{ fontSize: "0.625rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Keepsake Location
                </span>
                <span style={{ 
                  fontSize: "0.75rem", 
                  color: "#f43f5e", 
                  fontWeight: 500,
                  background: "rgba(244, 63, 94, 0.05)",
                  padding: "2px 8px",
                  borderRadius: 4,
                  border: "1px solid rgba(244, 63, 94, 0.1)"
                }}>
                  {sec.context || "Intimate Encounter"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
