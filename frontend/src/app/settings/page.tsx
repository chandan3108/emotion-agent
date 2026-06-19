"use client";

import { useState, useEffect } from "react";
import { getLinkStatus, getOAuthUrl, linkDiscordOAuth, resetUser, getIdentity, updateProfile } from "@/lib/gameApi";

export default function SettingsPage() {
  const [linkStatus, setLinkStatus] = useState<{ linked: boolean; discord_id?: string } | null>(null);
  const [linkMessage, setLinkMessage] = useState("");
  const [resetConfirm, setResetConfirm] = useState(false);
  const [resetMessage, setResetMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [linkingLoading, setLinkingLoading] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  // User Profile fields
  const [preferredName, setPreferredName] = useState("");
  const [gender, setGender] = useState("");
  const [pronouns, setPronouns] = useState("");
  const [profileMessage, setProfileMessage] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const code = searchParams.get("code");

    if (typeof window !== "undefined") {
      setUserEmail(localStorage.getItem("user_email") || "");
    }

    async function loadData() {
      try {
        const [linkRes, identityRes] = await Promise.all([
          getLinkStatus().catch(() => ({ linked: false })),
          getIdentity().catch(() => null)
        ]);
        
        setLinkStatus(linkRes);
        if (identityRes && identityRes.user_facts) {
          const getFactVal = (key: string) => {
            const entry = identityRes.user_facts[key];
            if (!entry) return "";
            if (typeof entry === "object" && entry !== null && "v" in entry) {
              return (entry as any).v || "";
            }
            return String(entry);
          };
          setPreferredName(getFactVal("preferred_name"));
          setGender(getFactVal("gender"));
          setPronouns(getFactVal("pronouns"));
        }
      } catch (err) {
        console.error("Failed to load settings data", err);
      } finally {
        setLoading(false);
      }
    }

    async function checkOAuthLink() {
      if (code) {
        setLinkMessage("Linking Discord account...");
        try {
          const redirectUri = window.location.origin + window.location.pathname;
          const result = await linkDiscordOAuth(code, redirectUri);
          if (result.success) {
            setLinkMessage(`✅ Linked to Discord successfully!`);
          } else {
            setLinkMessage(`❌ Failed to link Discord: Unknown error`);
          }
        } catch (e: any) {
          setLinkMessage(`❌ Failed to link: ${e.message || e}`);
        }
        window.history.replaceState({}, document.title, window.location.pathname);
      }
      loadData();
    }

    checkOAuthLink();
  }, []);

  async function handleSaveProfile() {
    setProfileSaving(true);
    setProfileMessage("");
    try {
      const result = await updateProfile({
        preferred_name: preferredName,
        gender: gender,
        pronouns: pronouns,
      });
      if (result.success) {
        setProfileMessage("✅ Profile updated successfully!");
      } else {
        setProfileMessage("❌ Failed to update profile.");
      }
    } catch (e) {
      setProfileMessage(`❌ Error: ${e}`);
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleDiscordOAuthLink() {
    setLinkingLoading(true);
    setLinkMessage("");
    try {
      const redirectUri = window.location.origin + window.location.pathname;
      const res = await getOAuthUrl("discord", redirectUri);
      if (res.url) {
        window.location.href = res.url;
      } else {
        setLinkMessage("❌ Failed to initiate Discord OAuth link: No URL returned.");
      }
    } catch (e: any) {
      setLinkMessage(`❌ Error: ${e.message || e}`);
    } finally {
      setLinkingLoading(false);
    }
  }

  async function handleReset() {
    if (!resetConfirm) {
      setResetConfirm(true);
      return;
    }
    try {
      const result = await resetUser();
      if (typeof window !== "undefined") {
        localStorage.removeItem("rem_chat_messages");
        localStorage.removeItem("rem_date_sessions");
      }
      setResetMessage(result.message || "Reset complete");
      setResetConfirm(false);
    } catch (e) {
      setResetMessage(`Error: ${e}`);
      setResetConfirm(false);
    }
  }

  function handleLogout() {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user_email");
      window.location.href = "/login";
    }
  }

  if (loading) {
    return (
      <div className="page-container" style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="rem-orb" style={{ width: 40, height: 40, animation: "pulse-glow 2s ease-in-out infinite" }} />
      </div>
    );
  }

  return (
    <div className="page-container" style={{ padding: "40px 48px", maxWidth: 720 }}>
      <h1 className="page-title" style={{ marginBottom: 8 }}>Settings</h1>
      <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem", marginBottom: 40 }}>
        Account linking and system controls.
      </p>

      {/* ── Active Account Details & Log Out ── */}
      <section className="glass-panel" style={{ padding: "20px 28px", marginBottom: 28, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 4, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ color: "var(--accent-secondary)" }}>⟡</span> Active Profile
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", margin: 0 }}>
            Logged in as: <strong style={{ color: "var(--accent-primary)", fontFamily: "var(--font-mono)" }}>{userEmail || "Guest User"}</strong>
          </p>
        </div>
        <button
          onClick={handleLogout}
          style={{
            padding: "10px 20px",
            borderRadius: 8,
            border: "1px solid var(--border-subtle)",
            background: "rgba(255,255,255,0.03)",
            color: "var(--text-primary)",
            fontWeight: 600,
            fontSize: "0.8125rem",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = "rgba(255, 60, 60, 0.08)";
            e.currentTarget.style.borderColor = "rgba(255, 60, 60, 0.3)";
            e.currentTarget.style.color = "#ff4444";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = "rgba(255,255,255,0.03)";
            e.currentTarget.style.borderColor = "var(--border-subtle)";
            e.currentTarget.style.color = "var(--text-primary)";
          }}
        >
          Sign Out
        </button>
      </section>

      {/* ── User Profile Settings ── */}
      <section className="glass-panel" style={{ padding: 28, marginBottom: 28 }}>
        <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "var(--accent-secondary)" }}>⟡</span> User Profile
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", marginBottom: 20, lineHeight: 1.6 }}>
          Set your preferred name, gender, and pronouns. Rem uses this information to personalize your conversations and refer to you correctly.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 20 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Preferred Name</label>
            <input
              type="text"
              value={preferredName}
              onChange={(e) => setPreferredName(e.target.value)}
              placeholder="e.g. Alex"
              style={{
                padding: "10px 14px",
                borderRadius: 8,
                border: "1px solid var(--border-subtle)",
                background: "rgba(255,255,255,0.03)",
                color: "var(--text-primary)",
                fontSize: "0.875rem",
                outline: "none",
              }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Gender Identity</label>
            <input
              type="text"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              placeholder="e.g. Male, Female, Non-binary"
              style={{
                padding: "10px 14px",
                borderRadius: 8,
                border: "1px solid var(--border-subtle)",
                background: "rgba(255,255,255,0.03)",
                color: "var(--text-primary)",
                fontSize: "0.875rem",
                outline: "none",
              }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Pronouns</label>
            <input
              type="text"
              value={pronouns}
              onChange={(e) => setPronouns(e.target.value)}
              placeholder="e.g. he/him, she/her, they/them"
              style={{
                padding: "10px 14px",
                borderRadius: 8,
                border: "1px solid var(--border-subtle)",
                background: "rgba(255,255,255,0.03)",
                color: "var(--text-primary)",
                fontSize: "0.875rem",
                outline: "none",
              }}
            />
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={handleSaveProfile}
            disabled={profileSaving}
            className="btn-primary"
            style={{
              padding: "10px 20px",
              borderRadius: 8,
              border: "none",
              fontWeight: 600,
              fontSize: "0.8125rem",
              cursor: "pointer",
              opacity: profileSaving ? 0.6 : 1,
            }}
          >
            {profileSaving ? "Saving..." : "Save Profile"}
          </button>
          {profileMessage && (
            <span style={{ fontSize: "0.8125rem", color: profileMessage.startsWith("✅") ? "var(--accent-primary)" : "var(--accent-warning)" }}>
              {profileMessage}
            </span>
          )}
        </div>
      </section>

      {/* ── Discord Link ── */}
      <section className="glass-panel" style={{ padding: 28, marginBottom: 28 }}>
        <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "var(--accent-secondary)" }}>⟡</span> Discord Link
        </h2>

        {linkStatus?.linked ? (
          <div style={{ padding: "12px 16px", borderRadius: 8, background: "rgba(var(--accent-primary-rgb), 0.08)", border: "1px solid rgba(var(--accent-primary-rgb), 0.2)" }}>
            <span style={{ color: "var(--accent-primary)", fontSize: "0.8125rem" }}>
              ✓ Linked to Discord user {linkStatus.discord_id}
            </span>
            <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginTop: 4 }}>
              Web and Discord share the same Rem. All memories, XP, and phase progression are synced.
            </p>
          </div>
        ) : (
          <div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", marginBottom: 20, lineHeight: 1.6 }}>
              Sync your web progress with Discord. Both interfaces will share the same memories, XP, relationship status, and dialogue history.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <button
                onClick={handleDiscordOAuthLink}
                disabled={linkingLoading}
                className="btn-primary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "10px",
                  background: "#5865F2",
                  color: "#FFF",
                  border: "none",
                  borderRadius: 8,
                  padding: "12px 24px",
                  fontWeight: 600,
                  fontSize: "0.875rem",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  width: "100%",
                }}
              >
                <svg width="18" height="18" viewBox="0 0 127.14 96.36" fill="currentColor">
                  <path d="M107.7,8.07A105.15,105.15,0,0,0,77.26,0a77.19,77.19,0,0,0-3.3,6.83A96.67,96.67,0,0,0,53.22,6.83,77.19,77.19,0,0,0,49.88,0,105.15,105.15,0,0,0,19.44,8.07C3.66,31.58-1.86,54.65,1,77.53A105.73,105.73,0,0,0,32,96.36a77.7,77.7,0,0,0,6.63-10.85,68.43,68.43,0,0,1-10.4-5c.8-1.57,1.57-3.17,2.3-4.81a74.9,74.9,0,0,0,73.13,0c.73,1.64,1.5,3.24,2.3,4.81a68.43,68.43,0,0,1-10.4,5,77.7,77.7,0,0,0,6.63,10.85,105.73,105.73,0,0,0,31.06-18.83C129,50.7,122.64,27.78,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53S36.18,40.36,42.45,40.36,53.83,46,53.83,53,48.72,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.24,60,73.24,53S78.41,40.36,84.69,40.36,96.07,46,96.07,53,91,65.69,84.69,65.69Z"/>
                </svg>
                {linkingLoading ? "Connecting..." : "Link Discord Account"}
              </button>
            </div>
            {linkMessage && (
              <p style={{ marginTop: 12, fontSize: "0.8125rem", color: linkMessage.startsWith("✅") ? "var(--accent-primary)" : "var(--accent-warning)" }}>
                {linkMessage}
              </p>
            )}
          </div>
        )}
      </section>

      {/* ── Danger Zone ── */}
      <section className="glass-panel" style={{ padding: 28, borderColor: "rgba(255, 60, 60, 0.15)" }}>
        <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#ff4444", marginBottom: 12 }}>
          Danger Zone
        </h2>
        <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginBottom: 16, lineHeight: 1.6 }}>
          Reset erases all memories, XP, phase progress, and personality evolution. This cannot be undone.
        </p>
        <button
          onClick={handleReset}
          style={{
            padding: "10px 20px",
            borderRadius: 8,
            border: resetConfirm ? "1px solid #ff4444" : "1px solid rgba(255, 60, 60, 0.3)",
            background: resetConfirm ? "rgba(255, 60, 60, 0.15)" : "transparent",
            color: resetConfirm ? "#ff4444" : "var(--text-muted)",
            fontWeight: 600,
            fontSize: "0.8125rem",
            cursor: "pointer",
          }}
        >
          {resetConfirm ? "Click again to confirm reset" : "Reset Rem"}
        </button>
        {resetMessage && (
          <p style={{ marginTop: 8, fontSize: "0.75rem", color: "var(--text-muted)" }}>{resetMessage}</p>
        )}
      </section>
    </div>
  );
}
