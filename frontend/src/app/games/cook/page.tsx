"use client";

import { useState, useEffect } from "react";
import { startCooking, stepCooking, searchRecipes } from "@/lib/gameApi";

export default function CookingGamePage() {
  const [dishQuery, setDishQuery] = useState("");
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [chaosMeter, setChaosMeter] = useState(0);
  const [banter, setBanter] = useState("");
  const [finished, setFinished] = useState(false);
  const [messageInput, setMessageInput] = useState("");
  const [checkedIngredients, setCheckedIngredients] = useState<Record<number, boolean>>({});

  // Search states
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searched, setSearched] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);

  // Active Timer state
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null);
  const [timerActive, setTimerActive] = useState(false);

  useEffect(() => {
    let interval: any = null;
    if (timerActive && timeRemaining !== null && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prev) => (prev !== null ? prev - 1 : null));
      }, 1000);
    } else if (timeRemaining === 0) {
      setTimerActive(false);
      setTimeRemaining(null);
      // Play a subtle notification sound (browser-native beep)
      try {
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        osc.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
      } catch (err) {}
      alert("⏱️ Cooking step timer finished!");
    }
    return () => clearInterval(interval);
  }, [timerActive, timeRemaining]);

  const startTimer = (seconds: number) => {
    setTimeRemaining(seconds);
    setTimerActive(true);
  };

  const handleSearchRecipes = async () => {
    const queryStr = dishQuery.trim();
    if (!queryStr) {
      // Surprise random recipe directly
      handleStartCooking("");
      return;
    }
    setSearchLoading(true);
    setSearched(true);
    try {
      const res = await searchRecipes(queryStr);
      setSearchResults(res.results || []);
    } catch (e) {
      console.error(e);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleStartCooking = async (dishNameOrId: string) => {
    setLoading(true);
    try {
      const res = await startCooking(dishNameOrId);
      setSession(res);
      setCurrentStep(0);
      setChaosMeter(0);
      setBanter(res.greeting);
      setFinished(false);
      setMessageInput("");
      setCheckedIngredients({});
      setTimerActive(false);
      setTimeRemaining(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleStepAction = async (action: "next" | "disaster" | "skip") => {
    if (!session || loading) return;
    setLoading(true);
    
    // Default messages if user didn't write anything
    let userMsg = messageInput.trim();
    if (!userMsg) {
      if (action === "disaster") {
        userMsg = "oops, i just burnt something... help!";
      } else if (action === "next") {
        userMsg = "finished the step. what's next?";
      } else {
        userMsg = "skipping this step for now.";
      }
    }

    try {
      const res = await stepCooking(userMsg, action);
      setBanter(res.banter);
      setChaosMeter(res.chaos_meter);
      setCurrentStep(res.current_step);
      if (res.finished) {
        setFinished(true);
      }
      setMessageInput("");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleIngredient = (idx: number) => {
    setCheckedIngredients((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const formatTime = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  if (!session) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: searched ? 900 : 600, margin: "0 auto", textAlign: "center" }}>
        <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>🍳</div>
        <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)" }}>
          Cooking with Rem
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", lineHeight: 1.6, margin: "12px 0 28px 0" }}>
          Type a recipe name to search matching recipes on TheMealDB. Rem will act as your opinionated, sarcastic sous-chef, guiding you step-by-step. Keep the Chaos Meter down to successfully log a clean dish in your Cookbook!
        </p>

        <div style={{ display: "flex", gap: 10, maxWidth: 440, margin: "0 auto 20px auto" }}>
          <input
            type="text"
            placeholder="Search dish (e.g. Chicken Curry, Pasta, Cake...)"
            value={dishQuery}
            onChange={(e) => setDishQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSearchRecipes(); }}
            style={{
              flex: 1, padding: "10px 16px", borderRadius: 8,
              background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-subtle)",
              color: "var(--text-primary)", fontSize: "0.8125rem",
            }}
          />
          <button
            onClick={handleSearchRecipes}
            disabled={searchLoading}
            style={{
              padding: "10px 24px", borderRadius: 8, background: "var(--accent-primary)",
              color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
              cursor: "pointer", transition: "all 0.2s", whiteSpace: "nowrap"
            }}
          >
            {searchLoading ? "Searching..." : "Search Recipe"}
          </button>
        </div>
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 10 }}>
          Leave empty for a surprise random recipe!
        </div>

        {/* Search Results Grid */}
        {searchLoading && (
          <div style={{ marginTop: 40, color: "var(--text-muted)", fontSize: "0.875rem" }}>
            Searching recipes on TheMealDB...
          </div>
        )}

        {!searchLoading && searched && searchResults !== null && (
          <div style={{ marginTop: 40 }}>
            {searchResults.length === 0 ? (
              <div style={{ padding: "30px 20px", background: "rgba(255,255,255,0.01)", borderRadius: 12, border: "1px dashed var(--border-subtle)" }}>
                <span style={{ fontSize: "2rem" }}>🔍❌</span>
                <h3 style={{ fontSize: "1rem", color: "var(--text-primary)", marginTop: 12 }}>No Matching Recipes Found</h3>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 6, marginBottom: 16 }}>
                  We couldn&apos;t find any recipes for &ldquo;{dishQuery}&rdquo;. Try another term, or let Rem surprise you.
                </p>
                <button
                  onClick={() => handleStartCooking("")}
                  style={{
                    padding: "8px 20px", borderRadius: 8, background: "var(--accent-primary)",
                    color: "#fff", border: "none", fontSize: "0.75rem", fontWeight: 600, cursor: "pointer"
                  }}
                >
                  Surprise Me!
                </button>
              </div>
            ) : (
              <div>
                <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", textAlign: "left", marginBottom: 16 }}>
                  Matching Recipes ({searchResults.length})
                </h3>
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
                  gap: 20,
                  justifyItems: "stretch"
                }}>
                  {searchResults.map((recipe) => (
                    <div
                      key={recipe.id}
                      className="glass-panel fade-in-up"
                      style={{
                        padding: 0,
                        overflow: "hidden",
                        display: "flex",
                        flexDirection: "column",
                        border: "1px solid var(--border-subtle)",
                        background: "rgba(255,255,255,0.01)",
                        borderRadius: 12,
                        textAlign: "left"
                      }}
                    >
                      <div style={{
                        height: 120,
                        background: recipe.thumbnail ? `url(${recipe.thumbnail}) center/cover no-repeat` : "linear-gradient(135deg, rgba(151,117,250,0.1), rgba(232,121,249,0.05))",
                        position: "relative"
                      }} />
                      <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12, flex: 1 }}>
                        <div>
                          <span style={{ fontSize: "0.5625rem", color: "var(--accent-secondary)", textTransform: "uppercase", fontWeight: 700 }}>
                            {recipe.category}
                          </span>
                          <h4 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)", marginTop: 2, lineClamp: 1, WebkitLineClamp: 1, display: "-webkit-box", WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                            {recipe.name}
                          </h4>
                        </div>
                        <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                          📖 {recipe.ingredients.length} ingredients | ⏱️ {recipe.steps.length} steps
                        </div>
                        <button
                          onClick={() => handleStartCooking(recipe.id)}
                          disabled={loading}
                          style={{
                            width: "100%", padding: "8px 16px", borderRadius: 8, background: "var(--accent-primary)",
                            color: "#fff", border: "none", fontSize: "0.75rem", fontWeight: 600,
                            cursor: "pointer", transition: "all 0.2s", textAlign: "center", marginTop: "auto"
                          }}
                        >
                          Cook with Rem
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  if (finished) {
    const isDisaster = chaosMeter > 0.5;
    return (
      <div style={{ padding: "40px 36px", maxWidth: 640, margin: "0 auto" }} className="fade-in-up">
        <div className="glass-panel" style={{ padding: 32, textAlign: "center", border: isDisaster ? "1px solid rgba(239, 68, 68, 0.25)" : "1px solid rgba(16, 185, 129, 0.25)" }}>
          <div style={{ fontSize: "4rem", marginBottom: 16 }}>{isDisaster ? "💨🔥🍲" : "✨🍛🍽️"}</div>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {isDisaster ? "Culinary Disaster!" : "Cooking Successful!"}
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: 8 }}>
            You finished cooking **{session.dish_name}** with Rem.
          </p>

          <div style={{ margin: "28px auto", maxWidth: 440, padding: "18px 22px", borderRadius: 10, background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-subtle)" }}>
            <span style={{ fontSize: "0.625rem", textTransform: "uppercase", color: "var(--accent-secondary)", fontWeight: 700, letterSpacing: "0.05em" }}>
              Sous Chef Review
            </span>
            <p style={{ 
              fontSize: "1.25rem", color: "var(--text-secondary)", fontStyle: "italic", marginTop: 6,
              fontFamily: "var(--font-caveat), 'Caveat', cursive", lineHeight: 1.4
            }}>
              &ldquo;{banter}&rdquo;
            </p>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10, width: "100%", maxWidth: 300, margin: "0 auto" }}>
            <div style={{ display: "flex", justifyContent: "center", gap: 8, fontSize: "0.75rem", color: "var(--text-muted)" }}>
              <span>Final Chaos Level:</span>
              <span style={{ color: isDisaster ? "#f87171" : "#34d399", fontWeight: 700 }}>
                {Math.round(chaosMeter * 100)}%
              </span>
            </div>
            <div style={{ width: "100%", height: 4, background: "rgba(255,255,255,0.03)", borderRadius: 2, overflow: "hidden" }}>
              <div style={{ 
                width: `${chaosMeter * 100}%`, height: "100%", 
                background: isDisaster ? "#ef4444" : "#10b981", borderRadius: 2 
              }} />
            </div>
          </div>

          <div style={{ marginTop: 36, display: "flex", gap: 12, justifyContent: "center" }}>
            <button
              onClick={() => { window.location.href = "/scrapbook?tab=cookbook"; }}
              style={{
                padding: "10px 24px", borderRadius: 8, background: "rgba(255,255,255,0.02)",
                color: "var(--text-secondary)", border: "1px solid var(--border-subtle)", fontSize: "0.8125rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              Check Cookbook
            </button>
            <button
              onClick={() => { setSession(null); setSearched(false); setSearchResults(null); }}
              style={{
                padding: "10px 24px", borderRadius: 8, background: "var(--accent-primary)",
                color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
                cursor: "pointer", boxShadow: "0 0 12px var(--accent-glow)", transition: "all 0.2s"
              }}
            >
              Cook Another Dish
            </button>
          </div>
        </div>
      </div>
    );
  }

  const steps = session.steps || [];
  const stepText = steps[currentStep] || "";

  return (
    <div style={{ padding: "40px 36px", maxWidth: 960, margin: "0 auto" }} className="fade-in-up">
      {/* 2-Column Split: Ingredients Panel (Left) & Active Step Panel (Right) */}
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 24, alignItems: "start" }}>
        
        {/* LEFT PANEL: Ingredients list */}
        <div className="glass-panel" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
          {session.thumbnail && (
            <div style={{ 
              width: "100%", height: 140, borderRadius: 8, overflow: "hidden", 
              background: `url(${session.thumbnail}) center/cover no-repeat` 
            }} />
          )}
          
          <div>
            <span style={{ fontSize: "0.5625rem", textTransform: "uppercase", color: "var(--accent-secondary)", letterSpacing: "0.05em", fontWeight: 700 }}>
              {session.category}
            </span>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)" }}>
              {session.dish_name}
            </h2>
          </div>

          <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: 14 }}>
            <h3 style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 10 }}>
              Ingredients Checklist
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {session.ingredients.map((ing: string, i: number) => {
                const isChecked = !!checkedIngredients[i];
                return (
                  <label 
                    key={i} 
                    style={{ 
                      display: "flex", gap: 8, alignItems: "flex-start", cursor: "pointer",
                      fontSize: "0.75rem", color: isChecked ? "var(--text-muted)" : "var(--text-secondary)",
                      textDecoration: isChecked ? "line-through" : "none"
                    }}
                  >
                    <input 
                      type="checkbox" 
                      checked={isChecked} 
                      onChange={() => toggleIngredient(i)}
                      style={{ marginTop: 2, cursor: "pointer" }} 
                    />
                    <span>{ing}</span>
                  </label>
                );
              })}
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: Current cooking step & timer */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          
          <div className="glass-panel" style={{ padding: 28, position: "relative" }}>
            
            {/* Header info */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Active Step
              </span>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-primary)" }}>
                Step {currentStep + 1} of {steps.length}
              </span>
            </div>

            {/* Progress bar */}
            <div style={{ width: "100%", height: 3, background: "rgba(255,255,255,0.03)", borderRadius: 2, marginBottom: 24, overflow: "hidden" }}>
              <div 
                style={{ 
                  width: `${((currentStep + 1) / steps.length) * 100}%`, 
                  height: "100%", background: "var(--accent-primary)", transition: "all 0.3s" 
                }} 
              />
            </div>

            {/* Instruction description */}
            <p style={{ fontSize: "0.9375rem", color: "var(--text-primary)", fontWeight: 500, lineHeight: 1.6, marginBottom: 28 }}>
              {stepText}
            </p>

            {/* Built-in Step Timer */}
            <div style={{ 
              display: "flex", alignItems: "center", gap: 14, padding: "12px 18px", borderRadius: 8, 
              background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-subtle)", marginBottom: 28 
            }}>
              <span style={{ fontSize: "1.25rem" }}>⏱️</span>
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <span style={{ fontSize: "0.625rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>
                  Kitchen Timer
                </span>
                <span style={{ fontSize: "1rem", fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--text-primary)" }}>
                  {timeRemaining !== null ? formatTime(timeRemaining) : "0:00"}
                </span>
              </div>
              <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
                {!timerActive && timeRemaining === null ? (
                  <>
                    <button onClick={() => startTimer(60)} style={{ padding: "4px 8px", borderRadius: 4, background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-subtle)", fontSize: "0.6875rem", color: "var(--text-secondary)", cursor: "pointer" }}>1m</button>
                    <button onClick={() => startTimer(180)} style={{ padding: "4px 8px", borderRadius: 4, background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-subtle)", fontSize: "0.6875rem", color: "var(--text-secondary)", cursor: "pointer" }}>3m</button>
                    <button onClick={() => startTimer(300)} style={{ padding: "4px 8px", borderRadius: 4, background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-subtle)", fontSize: "0.6875rem", color: "var(--text-secondary)", cursor: "pointer" }}>5m</button>
                  </>
                ) : (
                  <button 
                    onClick={() => { setTimerActive(!timerActive); }}
                    style={{ 
                      padding: "4px 12px", borderRadius: 4, 
                      background: timerActive ? "rgba(239, 68, 68, 0.1)" : "rgba(16, 185, 129, 0.1)", 
                      border: "1px solid " + (timerActive ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)"), 
                      fontSize: "0.6875rem", color: timerActive ? "#f87171" : "#34d399", cursor: "pointer" 
                    }}
                  >
                    {timerActive ? "Pause" : "Resume"}
                  </button>
                )}
                {(timeRemaining !== null) && (
                  <button 
                    onClick={() => { setTimerActive(false); setTimeRemaining(null); }}
                    style={{ padding: "4px 10px", borderRadius: 4, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-subtle)", fontSize: "0.6875rem", color: "var(--text-muted)", cursor: "pointer" }}
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>

            {/* Rem's dialogue feedback bubble */}
            <div 
              style={{ 
                padding: "16px 20px", borderRadius: 10,
                background: "rgba(232,121,249,0.04)", border: "1px solid rgba(232,121,249,0.08)",
                fontSize: "0.8125rem", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: 1.5,
                position: "relative"
              }}
            >
              <div style={{ position: "absolute", bottom: -6, right: 36, width: 0, height: 0, borderLeft: "6px solid transparent", borderRight: "6px solid transparent", borderTop: "6px solid rgba(232,121,249,0.04)" }} />
              &ldquo;{banter}&rdquo;
              <span style={{ display: "block", fontSize: "0.5625rem", color: "var(--accent-tertiary)", fontWeight: 700, textTransform: "uppercase", marginTop: 6, letterSpacing: "0.05em" }}>
                Sous Chef Rem
              </span>
            </div>
            
            {/* Sarcastic chatter comment input */}
            <div style={{ marginTop: 24, display: "flex", gap: 10 }}>
              <input
                type="text"
                placeholder="Talk back or write how step is going (optional)..."
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                style={{
                  flex: 1, padding: "8px 14px", borderRadius: 6,
                  background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-subtle)",
                  color: "var(--text-primary)", fontSize: "0.75rem",
                }}
              />
            </div>

            {/* Stepper action controls */}
            <div style={{ display: "flex", gap: 12, marginTop: 16, justifyContent: "flex-end" }}>
              <button
                disabled={loading}
                onClick={() => handleStepAction("disaster")}
                style={{
                  padding: "8px 16px", borderRadius: 6, background: "rgba(239, 68, 68, 0.08)",
                  color: "#f87171", border: "1px solid rgba(239, 68, 68, 0.2)", fontSize: "0.75rem", fontWeight: 600,
                  cursor: "pointer", transition: "all 0.2s"
                }}
              >
                💥 Disaster! / Burnt it
              </button>
              <button
                disabled={loading}
                onClick={() => handleStepAction("skip")}
                style={{
                  padding: "8px 16px", borderRadius: 6, background: "rgba(255,255,255,0.02)",
                  color: "var(--text-muted)", border: "1px solid var(--border-subtle)", fontSize: "0.75rem", fontWeight: 600,
                  cursor: "pointer", transition: "all 0.2s"
                }}
              >
                Skip Step
              </button>
              <button
                disabled={loading}
                onClick={() => handleStepAction("next")}
                style={{
                  padding: "8px 24px", borderRadius: 6, background: "var(--accent-primary)",
                  color: "#fff", border: "none", fontSize: "0.75rem", fontWeight: 600,
                  cursor: "pointer", boxShadow: "0 0 10px var(--accent-glow)", transition: "all 0.2s"
                }}
              >
                {currentStep + 1 >= steps.length ? "Finish Dish" : "Step Complete →"}
              </button>
            </div>

          </div>

          {/* HUD: Chaos Meter Bar */}
          <div className="glass-panel" style={{ padding: "18px 24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 8 }}>
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                🔥 Kitchen Chaos Meter
              </span>
              <span style={{ fontWeight: 700, color: chaosMeter > 0.5 ? "var(--text-error)" : "var(--text-primary)" }}>
                {Math.round(chaosMeter * 100)}%
              </span>
            </div>
            <div style={{ width: "100%", height: 6, background: "rgba(255,255,255,0.03)", borderRadius: 3, overflow: "hidden" }}>
              <div 
                style={{ 
                  width: `${chaosMeter * 100}%`, height: "100%", 
                  background: chaosMeter > 0.5 ? "linear-gradient(to right, #ff8787, #ef4444)" : "linear-gradient(to right, #69db7c, #10b981)", 
                  borderRadius: 3, transition: "all 0.3s" 
                }} 
              />
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
