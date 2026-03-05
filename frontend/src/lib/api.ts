export async function sendRealtimeEvent(frame: any) {
  const res = await fetch("http://localhost:8000/realtime", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(frame),
  });
  if (!res.ok) {
    throw new Error("Realtime request failed");
  }
  return res.json();
}

export async function sendRealtimeFeedback(payload: {
  features: any;
  true_emotion: string;
  true_valence?: number;
  true_arousal?: number;
}) {
  const res = await fetch("http://localhost:8000/realtime/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error("Feedback request failed");
  }
  return res.json();
}

export async function requestAgentReply(payload: {
  emotion?: string | null;
  valence?: number | null;
  arousal?: number | null;
  stress?: number | null;
  engagement?: number | null;
  messages: { role: "user" | "assistant"; content: string }[];
}) {
  const res = await fetch("http://localhost:8000/agent/respond/v2", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error("Agent request failed");
  }
  return res.json() as Promise<{ reply: string }>;
}
