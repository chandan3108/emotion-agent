"use client";

import { useState } from "react";
import { startPersonality, answerPersonality } from "@/lib/gameApi";

export default function PersonalityGamePage() {
  const [session, setSession] = useState<any>(null);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [banter, setBanter] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const startTest = async () => {
    setLoading(true);
    try {
      const res = await startPersonality();
      setSession(res);
      setCurrentQIndex(0);
      setResult(null);
      setBanter(null);
      setSelectedChoice(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectChoice = async (choice: string) => {
    if (selectedChoice || !session) return;
    setSelectedChoice(choice);
    setLoading(true);
    
    try {
      const question = session.questions[currentQIndex];
      const res = await answerPersonality(session.session_id, question.id, choice);
      setBanter(res.banter);
      if (res.finished && res.result) {
        setResult(res.result);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const nextQuestion = () => {
    setSelectedChoice(null);
    setBanter(null);
    setCurrentQIndex((prev) => prev + 1);
  };

  // Helper to draw the custom SVG Radar Chart
  function renderRadarChart(metrics: Record<string, number>) {
    const keys = ["Logic", "Charm", "Empathy", "Defense", "Chaos"];
    const values = keys.map(k => metrics[k] || 50);
    const center = 100;
    const r = 60;
    
    // Calculate vertices for value polygon and grid layers
    const getCoordinates = (valList: number[]) => {
      return valList.map((val, i) => {
        const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
        const dist = r * (val / 100);
        const x = center + dist * Math.cos(angle);
        const y = center + dist * Math.sin(angle);
        return { x, y, labelX: center + (r + 14) * Math.cos(angle), labelY: center + (r + 8) * Math.sin(angle) };
      });
    };

    const points = getCoordinates(values);
    const polyPath = points.map(p => `${p.x},${p.y}`).join(" ");
    
    const grids = [25, 50, 75, 100];

    return (
      <svg viewBox="0 0 200 200" style={{ width: "100%", maxHeight: 220, display: "block", margin: "0 auto" }}>
        {/* Grid lines */}
        {grids.map((g, idx) => {
          const gridPoints = getCoordinates(Array(5).fill(g));
          const gridPath = gridPoints.map(p => `${p.x},${p.y}`).join(" ");
          return (
            <polygon 
              key={idx} 
              points={gridPath} 
              fill="none" 
              stroke="rgba(255,255,255,0.06)" 
              strokeWidth="0.75" 
            />
          );
        })}
        
        {/* Axis rays */}
        {getCoordinates(Array(5).fill(100)).map((p, i) => (
          <line 
            key={i} 
            x1={center} 
            y1={center} 
            x2={p.x} 
            y2={p.y} 
            stroke="rgba(255,255,255,0.06)" 
            strokeWidth="0.75" 
          />
        ))}

        {/* Data polygon */}
        <polygon 
          points={polyPath} 
          fill="rgba(167, 139, 250, 0.2)" 
          stroke="var(--accent-primary)" 
          strokeWidth="1.5" 
          style={{ transition: "all 0.5s" }}
        />

        {/* Vertex points */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3" fill="#fff" stroke="var(--accent-primary)" strokeWidth="1" />
        ))}

        {/* Axis labels */}
        {getCoordinates(Array(5).fill(100)).map((p, i) => (
          <text 
            key={i} 
            x={p.labelX} 
            y={p.labelY} 
            fill="var(--text-muted)" 
            fontSize="6" 
            fontFamily="Space Grotesk"
            fontWeight="bold"
            textAnchor="middle"
            alignmentBaseline="middle"
          >
            {keys[i]} ({values[i]}%)
          </text>
        ))}
      </svg>
    );
  }

  if (!session) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: 600, margin: "0 auto", textAlign: "center" }}>
        <div style={{ fontSize: "3.5rem", marginBottom: 16 }}>🧠</div>
        <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "1.75rem", fontWeight: 700, color: "var(--text-primary)" }}>
          Psyche Profiler
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", lineHeight: 1.6, margin: "12px 0 28px 0" }}>
          Rem has designed a 30-question psychological evaluation. As you select choices, she will comment on your traits in real-time, mapping you to an ultimate dynamic archetype at the end.
        </p>
        <button
          onClick={startTest}
          disabled={loading}
          style={{
            padding: "12px 32px", borderRadius: 999, background: "var(--accent-primary)",
            color: "#fff", border: "none", fontSize: "0.875rem", fontWeight: 600,
            cursor: "pointer", boxShadow: "0 0 20px var(--accent-glow)", transition: "all 0.2s"
          }}
        >
          {loading ? "Initializing..." : "Begin Evaluation"}
        </button>
      </div>
    );
  }

  if (result) {
    return (
      <div style={{ padding: "40px 36px", maxWidth: 720, margin: "0 auto" }} className="fade-in-up">
        {/* Certificate Card */}
        <div className="glass-panel" style={{ padding: 32, textAlign: "center", border: "1px solid rgba(167, 139, 250, 0.25)" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--accent-primary)", fontWeight: 700, letterSpacing: "0.15em", textTransform: "uppercase" }}>
            evaluation complete
          </span>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "2.25rem", fontWeight: 700, color: "var(--text-primary)", marginTop: 6 }}>
            {result.archetype}
          </h1>

          <div style={{ margin: "24px 0" }}>
            {renderRadarChart(result.metrics)}
          </div>

          <div style={{ textAlign: "left", display: "flex", flexDirection: "column", gap: 16, marginTop: 32 }}>
            <div style={{ padding: "16px 20px", borderRadius: 10, background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-subtle)" }}>
              <h3 style={{ fontSize: "0.8125rem", color: "var(--accent-primary)", fontWeight: 700, marginBottom: 4 }}>Archetype Description</h3>
              <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>{result.description}</p>
            </div>
            
            <div style={{ padding: "16px 20px", borderRadius: 10, background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-subtle)" }}>
              <h3 style={{ fontSize: "0.8125rem", color: "var(--accent-secondary)", fontWeight: 700, marginBottom: 4 }}>How It Shapes Your Life</h3>
              <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>{result.how_it_affects_you}</p>
            </div>

            <div style={{ padding: "16px 20px", borderRadius: 10, background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-subtle)" }}>
              <h3 style={{ fontSize: "0.8125rem", color: "var(--accent-tertiary)", fontWeight: 700, marginBottom: 4 }}>Rem Compatibility Verdict</h3>
              <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>{result.rem_compatibility}</p>
            </div>

            <div style={{ padding: "16px 20px", borderRadius: 10, background: "rgba(167, 139, 250, 0.05)", border: "1px dashed rgba(167, 139, 250, 0.2)" }}>
              <h3 style={{ fontSize: "0.8125rem", color: "var(--accent-primary)", fontWeight: 700, marginBottom: 4 }}>Rem&apos;s Advice</h3>
              <p style={{ color: "var(--text-primary)", fontStyle: "italic", fontFamily: "var(--font-caveat), 'Caveat', cursive", fontSize: "1.25rem" }}>
                &ldquo;{result.advice}&rdquo;
              </p>
            </div>
          </div>

          <div style={{ marginTop: 36, display: "flex", gap: 12, justifyContent: "center" }}>
            <button
              onClick={() => { window.location.href = "/scrapbook"; }}
              style={{
                padding: "10px 24px", borderRadius: 8, background: "rgba(255,255,255,0.02)",
                color: "var(--text-secondary)", border: "1px solid var(--border-subtle)", fontSize: "0.8125rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              View Medals
            </button>
            <button
              onClick={startTest}
              style={{
                padding: "10px 24px", borderRadius: 8, background: "var(--accent-primary)",
                color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
                cursor: "pointer", boxShadow: "0 0 12px var(--accent-glow)", transition: "all 0.2s"
              }}
            >
              Retake Test
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = session.questions[currentQIndex];

  return (
    <div style={{ padding: "40px 36px", maxWidth: 640, margin: "0 auto" }}>
      {/* Quiz Progression Card */}
      <div className="glass-panel" style={{ padding: "28px 32px", position: "relative" }}>
        
        {/* Progress header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            psyche evaluation
          </span>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-primary)" }}>
            Question {currentQIndex + 1} of {session.total_questions}
          </span>
        </div>

        {/* Progress indicator bar */}
        <div style={{ width: "100%", height: 3, background: "rgba(255,255,255,0.03)", borderRadius: 2, marginBottom: 28, overflow: "hidden" }}>
          <div 
            style={{ 
              width: `${((currentQIndex + 1) / session.total_questions) * 100}%`, 
              height: "100%", background: "var(--accent-primary)", transition: "all 0.3s" 
            }} 
          />
        </div>

        {/* The Question */}
        <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 24, lineHeight: 1.5 }}>
          {currentQuestion.question}
        </h2>

        {/* Answer Choices */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {Object.entries(currentQuestion.options).map(([key, optText]: [string, any]) => {
            const isSelected = selectedChoice === key;
            const isDisabled = selectedChoice !== null;
            
            let cardBg = "rgba(255,255,255,0.01)";
            let cardBorder = "var(--border-subtle)";
            if (isSelected) {
              cardBg = "rgba(167, 139, 250, 0.08)";
              cardBorder = "rgba(167, 139, 250, 0.4)";
            }

            return (
              <button
                key={key}
                disabled={isDisabled}
                onClick={() => handleSelectChoice(key)}
                style={{
                  textAlign: "left", padding: "14px 18px", borderRadius: 8,
                  background: cardBg, border: `1px solid ${cardBorder}`,
                  cursor: isDisabled ? "default" : "pointer", display: "flex", gap: 12, alignItems: "flex-start",
                  transition: "all 0.2s"
                }}
                onMouseOver={(e) => { if (!isDisabled) e.currentTarget.style.borderColor = "var(--accent-primary)"; }}
                onMouseOut={(e) => { if (!isDisabled && !isSelected) e.currentTarget.style.borderColor = "var(--border-subtle)"; }}
              >
                <span style={{
                  width: 20, height: 20, borderRadius: "50%",
                  background: isSelected ? "var(--accent-primary)" : "rgba(255,255,255,0.03)",
                  border: "1px solid " + (isSelected ? "var(--accent-primary)" : "var(--border-subtle)"),
                  color: isSelected ? "#fff" : "var(--text-muted)", fontSize: "0.6875rem", fontWeight: 700,
                  display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0
                }}>
                  {key}
                </span>
                <span style={{ fontSize: "0.8125rem", color: isSelected ? "var(--text-primary)" : "var(--text-secondary)", lineHeight: 1.4 }}>
                  {optText}
                </span>
              </button>
            );
          })}
        </div>

        {/* Live Banter bubble from Rem */}
        {banter && (
          <div 
            className="fade-in-up" 
            style={{ 
              marginTop: 28, padding: "14px 18px", borderRadius: 10,
              background: "rgba(232,121,249,0.04)", border: "1px solid rgba(232,121,249,0.08)",
              fontSize: "0.8125rem", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: 1.5,
              position: "relative"
            }}
          >
            <div style={{ position: "absolute", top: -6, left: 24, width: 0, height: 0, borderLeft: "6px solid transparent", borderRight: "6px solid transparent", borderBottom: "6px solid rgba(232,121,249,0.04)" }} />
            &ldquo;{banter}&rdquo;
            <span style={{ display: "block", fontSize: "0.5625rem", color: "var(--accent-tertiary)", fontWeight: 700, textTransform: "uppercase", marginTop: 6, letterSpacing: "0.05em" }}>
              Rem&apos;s diagnosis
            </span>
          </div>
        )}

        {/* Next Button */}
        {banter && (
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 24 }} className="fade-in-up">
            <button
              onClick={nextQuestion}
              style={{
                padding: "8px 24px", borderRadius: 6, background: "var(--accent-primary)",
                color: "#fff", border: "none", fontSize: "0.8125rem", fontWeight: 600,
                cursor: "pointer", transition: "all 0.2s"
              }}
            >
              {currentQIndex + 1 >= session.total_questions ? "Finish & Analyze" : "Next Question →"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
