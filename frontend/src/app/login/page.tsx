"use client";

import React, { useState, useEffect } from "react";
import { registerUser, loginUser, getOAuthUrl, oauthCallback } from "@/lib/gameApi";

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [oauthStatus, setOauthStatus] = useState<string | null>(null);
  const [oauthLoading, setOauthLoading] = useState<string | null>(null);

  useEffect(() => {
    // Read query parameters
    const searchParams = new URLSearchParams(window.location.search);
    const code = searchParams.get("code");
    const provider = searchParams.get("provider");

    // Only clear token if we are not processing an OAuth callback
    if (!code) {
      localStorage.removeItem("token");
      return;
    }

    if (code && provider) {
      setLoading(true);
      setOauthStatus(`Authenticating with ${provider === "google" ? "Google" : "Discord"}...`);
      
      const redirectUri = window.location.origin + window.location.pathname + "?provider=" + provider;
      
      oauthCallback(provider, code, redirectUri)
        .then((res) => {
          if (res.success && res.token) {
            localStorage.setItem("token", res.token);
            if (res.email) localStorage.setItem("user_email", res.email);
            window.location.href = "/";
          } else {
            setError(res.error || "Authentication failed.");
            setLoading(false);
            setOauthStatus(null);
            // Clean URL query params to let them retry
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        })
        .catch((err: any) => {
          setError(err.message || "An unexpected error occurred during OAuth login.");
          setLoading(false);
          setOauthStatus(null);
          window.history.replaceState({}, document.title, window.location.pathname);
        });
    }
  }, []);

  const handleOAuthLogin = async (provider: string) => {
    setError(null);
    setOauthLoading(provider);
    try {
      const redirectUri = window.location.origin + window.location.pathname + "?provider=" + provider;
      const res = await getOAuthUrl(provider, redirectUri);
      if (res.url) {
        window.location.href = res.url;
      } else {
        setError(`Failed to retrieve OAuth URL for ${provider}.`);
      }
    } catch (err: any) {
      setError(err.message || `An error occurred preparing OAuth login for ${provider}.`);
    } finally {
      setOauthLoading(null);
    }
  };

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

        {/* OAuth Loading Status */}
        {oauthStatus && (
          <div style={{
            background: "rgba(198, 172, 133, 0.1)",
            border: "1px solid rgba(198, 172, 133, 0.3)",
            borderRadius: "8px",
            padding: "12px",
            fontSize: "0.8rem",
            color: "#C6AC85",
            textAlign: "center",
            fontFamily: "var(--font-mono)",
            lineHeight: 1.4,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
          }}>
            <span className="spinner" style={{
              width: "14px",
              height: "14px",
              border: "2px solid rgba(198, 172, 133, 0.2)",
              borderTop: "2px solid #C6AC85",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
            }} />
            {oauthStatus}
          </div>
        )}

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

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ flex: 1, height: "1px", background: "rgba(198, 172, 133, 0.15)" }} />
          <span style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.1em", color: "#C6AC85", opacity: 0.6 }}>or</span>
          <div style={{ flex: 1, height: "1px", background: "rgba(198, 172, 133, 0.15)" }} />
        </div>

        {/* OAuth Buttons */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {/* Google Button */}
          <button
            type="button"
            disabled={loading || !!oauthLoading}
            onClick={() => handleOAuthLogin("google")}
            style={{
              background: "transparent",
              border: "1px solid rgba(198, 172, 133, 0.3)",
              borderRadius: "8px",
              padding: "12px",
              color: "#FFF",
              fontSize: "0.85rem",
              fontWeight: 500,
              cursor: (loading || !!oauthLoading) ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              transition: "all 0.2s ease",
            }}
            onMouseOver={(e) => {
              if (!loading && !oauthLoading) {
                e.currentTarget.style.background = "rgba(198, 172, 133, 0.08)";
                e.currentTarget.style.borderColor = "#C6AC85";
              }
            }}
            onMouseOut={(e) => {
              if (!loading && !oauthLoading) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.borderColor = "rgba(198, 172, 133, 0.3)";
              }
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
            </svg>
            {oauthLoading === "google" ? "Connecting to Google..." : "Continue with Google"}
          </button>

          {/* Discord Button */}
          <button
            type="button"
            disabled={loading || !!oauthLoading}
            onClick={() => handleOAuthLogin("discord")}
            style={{
              background: "#5865F2",
              border: "none",
              borderRadius: "8px",
              padding: "12px",
              color: "#FFF",
              fontSize: "0.85rem",
              fontWeight: 500,
              cursor: (loading || !!oauthLoading) ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              transition: "all 0.2s ease",
            }}
            onMouseOver={(e) => {
              if (!loading && !oauthLoading) {
                e.currentTarget.style.background = "#4752C4";
              }
            }}
            onMouseOut={(e) => {
              if (!loading && !oauthLoading) {
                e.currentTarget.style.background = "#5865F2";
              }
            }}
          >
            <svg width="18" height="18" viewBox="0 0 127.14 96.36" fill="currentColor">
              <path d="M107.7,8.07A105.15,105.15,0,0,0,77.26,0a77.19,77.19,0,0,0-3.3,6.83A96.67,96.67,0,0,0,53.22,6.83,77.19,77.19,0,0,0,49.88,0,105.15,105.15,0,0,0,19.44,8.07C3.66,31.58-1.86,54.65,1,77.53A105.73,105.73,0,0,0,32,96.36a77.7,77.7,0,0,0,6.63-10.85,68.43,68.43,0,0,1-10.4-5c.8-1.57,1.57-3.17,2.3-4.81a74.9,74.9,0,0,0,73.13,0c.73,1.64,1.5,3.24,2.3,4.81a68.43,68.43,0,0,1-10.4,5,77.7,77.7,0,0,0,6.63,10.85,105.73,105.73,0,0,0,31.06-18.83C129,50.7,122.64,27.78,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53S36.18,40.36,42.45,40.36,53.83,46,53.83,53,48.72,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.24,60,73.24,53S78.41,40.36,84.69,40.36,96.07,46,96.07,53,91,65.69,84.69,65.69Z"/>
            </svg>
            {oauthLoading === "discord" ? "Connecting to Discord..." : "Continue with Discord"}
          </button>
        </div>

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
