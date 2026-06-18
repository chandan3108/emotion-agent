"use client";

import React, { useState, useEffect } from "react";
import { registerUser, loginUser } from "@/lib/gameApi";

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Clear token on mount if visiting login page explicitly
  useEffect(() => {
    localStorage.removeItem("token");
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        const res = await registerUser({ email, password });
        if (res.success && res.token) {
          localStorage.setItem("token", res.token);
          if (res.email) localStorage.setItem("user_email", res.email);
          window.location.href = "/";
        } else {
          setError(res.error || "Failed to create account.");
        }
      } else {
        const res = await loginUser({ email, password });
        if (res.success && res.token) {
          localStorage.setItem("token", res.token);
          if (res.email) localStorage.setItem("user_email", res.email);
          window.location.href = "/";
        } else {
          setError(res.error || "Invalid email or password.");
        }
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "radial-gradient(circle at center, #0F0F0F 0%, #000000 100%)",
      color: "#F5F5DC",
      fontFamily: "var(--font-space), sans-serif",
      padding: "24px",
    }}>
      <div style={{
        width: "100%",
        maxWidth: "420px",
        background: "rgba(10, 10, 10, 0.85)",
        border: "1px solid rgba(198, 172, 133, 0.2)",
        borderRadius: "16px",
        padding: "40px 32px",
        boxShadow: "0 20px 50px rgba(0, 0, 0, 0.8), 0 0 40px rgba(198, 172, 133, 0.05)",
        backdropFilter: "blur(20px)",
        display: "flex",
        flexDirection: "column",
        gap: "28px",
        position: "relative",
        overflow: "hidden",
      }}>
        {/* Glow Element */}
        <div style={{
          position: "absolute",
          top: "-50px",
          right: "-50px",
          width: "150px",
          height: "150px",
          borderRadius: "50%",
          background: "rgba(198, 172, 133, 0.08)",
          filter: "blur(50px)",
          pointerEvents: "none",
        }} />

        {/* Header */}
        <div style={{ textAlign: "center" }}>
          <div className="rem-orb" style={{ width: "48px", height: "48px", margin: "0 auto 16px auto" }}>
            <div style={{
              position: "absolute",
              inset: 3,
              borderRadius: "50%",
              background: "#000000",
            }} />
          </div>
          <h1 style={{
            fontSize: "2rem",
            fontWeight: 300,
            letterSpacing: "-0.04em",
            color: "#FFF",
            marginBottom: "8px",
          }}>
            Rem
          </h1>
          <p style={{
            fontSize: "0.85rem",
            color: "#C6AC85",
            opacity: 0.8,
            fontWeight: 400,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}>
            {isRegister ? "Begin the journey" : "Reconnect with Rem"}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{
            background: "rgba(184, 92, 75, 0.1)",
            border: "1px solid rgba(184, 92, 75, 0.3)",
            borderRadius: "8px",
            padding: "12px",
            fontSize: "0.8rem",
            color: "#FF8A8A",
            textAlign: "center",
            fontFamily: "var(--font-mono)",
            lineHeight: 1.4,
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{
              fontSize: "0.75rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              color: "#C6AC85",
              opacity: 0.8,
              fontWeight: 500,
            }}>Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@domain.com"
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(198, 172, 133, 0.15)",
                borderRadius: "8px",
                padding: "12px 14px",
                color: "#FFF",
                fontSize: "0.95rem",
                outline: "none",
                transition: "all 0.2s ease",
                fontFamily: "var(--font-mono)",
              }}
              onFocus={(e) => {
                e.target.style.border = "1px solid #C6AC85";
                e.target.style.boxShadow = "0 0 10px rgba(198, 172, 133, 0.1)";
              }}
              onBlur={(e) => {
                e.target.style.border = "1px solid rgba(198, 172, 133, 0.15)";
                e.target.style.boxShadow = "none";
              }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{
              fontSize: "0.75rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              color: "#C6AC85",
              opacity: 0.8,
              fontWeight: 500,
            }}>Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(198, 172, 133, 0.15)",
                borderRadius: "8px",
                padding: "12px 14px",
                color: "#FFF",
                fontSize: "0.95rem",
                outline: "none",
                transition: "all 0.2s ease",
                fontFamily: "var(--font-mono)",
              }}
              onFocus={(e) => {
                e.target.style.border = "1px solid #C6AC85";
                e.target.style.boxShadow = "0 0 10px rgba(198, 172, 133, 0.1)";
              }}
              onBlur={(e) => {
                e.target.style.border = "1px solid rgba(198, 172, 133, 0.15)";
                e.target.style.boxShadow = "none";
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: "12px",
              background: "#C6AC85",
              color: "#000",
              border: "none",
              borderRadius: "8px",
              padding: "14px",
              fontSize: "0.9rem",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.2s ease",
              boxShadow: "0 4px 15px rgba(198, 172, 133, 0.25)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
            }}
            onMouseOver={(e) => {
              if (!loading) {
                e.currentTarget.style.background = "#E0C9A6";
                e.currentTarget.style.transform = "translateY(-1px)";
              }
            }}
            onMouseOut={(e) => {
              if (!loading) {
                e.currentTarget.style.background = "#C6AC85";
                e.currentTarget.style.transform = "translateY(0)";
              }
            }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
                <span className="spinner" style={{
                  width: "16px",
                  height: "16px",
                  border: "2px solid rgba(0, 0, 0, 0.1)",
                  borderTop: "2px solid #000",
                  borderRadius: "50%",
                  animation: "spin 1s linear infinite",
                }} />
                Processing...
              </span>
            ) : isRegister ? "Create Account" : "Access Rem"}
          </button>
        </form>

        {/* Switch mode */}
        <div style={{
          textAlign: "center",
          fontSize: "0.85rem",
          color: "rgba(245, 245, 220, 0.6)",
        }}>
          {isRegister ? "Already registered?" : "New to Rem?"}{" "}
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            style={{
              background: "none",
              border: "none",
              color: "#C6AC85",
              cursor: "pointer",
              textDecoration: "underline",
              fontWeight: 500,
              padding: 0,
              marginLeft: "4px",
            }}
          >
            {isRegister ? "Sign in" : "Create one"}
          </button>
        </div>
      </div>

      <style jsx global>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
