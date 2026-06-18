"use client";

import { useState, useEffect } from "react";
import { getLinkStatus, linkDiscord, resetUser, getIdentity, updateProfile } from "@/lib/gameApi";

export default function SettingsPage() {
  const [linkCode, setLinkCode] = useState("");
  const [linkStatus, setLinkStatus] = useState<{ linked: boolean; discord_id?: string } | null>(null);
  const [linkMessage, setLinkMessage] = useState("");
  const [resetConfirm, setResetConfirm] = useState(false);
  const [resetMessage, setResetMessage] = useState("");
  const [loading, setLoading] = useState(true);

  // User Profile fields
  const [preferredName, setPreferredName] = useState("");
  const [gender, setGender] = useState("");
  const [pronouns, setPronouns] = useState("");
  const [profileMessage, setProfileMessage] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);

  useEffect(() => {
    Promise.all([
      getLinkStatus().catch(() => ({ linked: false })),
      getIdentity().catch(() => null)
    ])
      .then(([linkRes, identityRes]) => {
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
      })
      .finally(() => setLoading(false));
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

  async function handleLink() {
    if (!linkCode.trim() || linkCode.length !== 6) {
      setLinkMessage("Enter a 6-character code from Discord (!link)");
      return;
    }
    try {
      const result = await linkDiscord(linkCode.trim());
      if (result.success) {
        setLinkMessage(`✅ Linked to Discord (${result.discord_id})`);
        setLinkStatus({ linked: true, discord_id: result.discord_id });
        setLinkCode("");
      } else {
        setLinkMessage(`❌ ${result.error || "Invalid code"}`);
      }
    } catch (e) {
      setLinkMessage(`❌ Error: ${e}`);
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
            <p style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", marginBottom: 12, lineHeight: 1.6 }}>
              Type <code style={{ color: "var(--accent-primary)", background: "rgba(var(--accent-primary-rgb), 0.1)", padding: "2px 6px", borderRadius: 4, fontSize: "0.75rem" }}>!link</code> in Discord DMs to get a 6-character code.
            </p>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="text"
                value={linkCode}
                onChange={(e) => setLinkCode(e.target.value.toUpperCase())}
                placeholder="ABC123"
                maxLength={6}
                style={{
                  flex: 1,
                  padding: "10px 14px",
                  borderRadius: 8,
                  border: "1px solid var(--border-subtle)",
                  background: "rgba(255,255,255,0.03)",
                  color: "var(--text-primary)",
                  fontSize: "1rem",
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "0.15em",
                  textAlign: "center",
                  outline: "none",
                }}
              />
              <button
                onClick={handleLink}
                className="btn-primary"
                style={{
                  padding: "10px 20px",
                  borderRadius: 8,
                  border: "none",
                  fontWeight: 600,
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                }}
              >
                Link
              </button>
            </div>
            {linkMessage && (
              <p style={{ marginTop: 8, fontSize: "0.75rem", color: linkMessage.startsWith("✅") ? "var(--accent-primary)" : "var(--accent-warning)" }}>
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
