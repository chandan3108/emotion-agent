const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEFAULT_USER_ID = "web_user_001";

// ── Generic fetch wrapper ──

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Types ──

export interface XPData {
  total_xp: number;
  phase: string;
  phase_progress_pct: number;
  xp_to_next: number;
  next_phase: string | null;
  streak_days: number;
  daily_awards_today: string[];
  phase_unlocks: Record<string, unknown>;
  current_rank: number;
  next_rank: number | null;
}

export interface DiaryEntry {
  content: string;
  phase: string;
  timestamp: string;
  has_milestone: boolean;
  milestone_text: string | null;
}

export interface DiaryData {
  entries: DiaryEntry[];
  total_entries: number;
  access_level: string;
}

export interface TimelineEvent {
  event_type: string;
  description: string;
  timestamp: string;
  phase: string;
  significance: string | null;
}

export interface TimelineData {
  events: TimelineEvent[];
  current_phase: string;
  days_since_start: number | null;
}

export interface StatsData {
  total_messages: number;
  longest_streak: number;
  current_streak: number;
  current_phase: string;
  total_xp: number;
  inside_joke_count: number;
  temporal_pattern_count: number;
  diary_entry_count: number;
  milestone_count: number;
  days_active: number | null;
}

export interface InsideJoke {
  reference: string;
  context: string;
  joke_type: string | null;
}

export interface InsideJokesData {
  jokes: InsideJoke[];
  phase_required: string;
}

export interface PatternItem {
  pattern: string;
  confidence: string;
  pattern_type: string;
}

export interface PatternsData {
  patterns: PatternItem[];
  phase_required: string;
}

export interface ChatRequest {
  message: string;
  user_name?: string;
}

export interface ChatResponse {
  reply: string;
  reply_parts?: string[];
  xp_delta: number | null;
  phase_transition: { from: string; to: string } | null;
  new_unlocks: Record<string, unknown> | null;
  current_xp: number;
  current_phase: string;
  hurt?: number;
  anger?: number;
  rank_transition?: {
    from_rank: number;
    to_rank: number;
    from_phase: string;
    to_phase: string;
    unlocks: string[];
  } | null;
  roleplay?: { active: boolean; activity: string; location: string } | null;
  schedule?: any[];
  future_plans?: any[];
  typing_delay_ms?: number;
}


export interface PostcardEntry {
  id: string;
  activity: string;
  location: string;
  date: string;
  note: string;
  timestamp: string;
}

export interface PostcardsData {
  postcards: PostcardEntry[];
  total_postcards: number;
}

// ── Memory types ──

export interface MemoryData {
  stm: { count: number; entries: { content: string; timestamp: string; topic: string }[] };
  episodic: { count: number; entries: { content: string; event_type: string; salience: number; emotional_valence: number; timestamp: string }[] };
  identity: { count: number; facts: { fact: string; confidence: number; source: string; timestamp: string }[] };
}

// ── Personality types ──

export interface PersonalityData {
  personality_text: string;
  personality_summary: string;
  expression_guidance: string;
  vibe_palette: string[];
  current_interests: string[];
  psyche: {
    stance: string;
    respect: number;
    engagement: number;
    posture: string;
    named_mood: Record<string, unknown>;
    neurochem: Record<string, number>;
  };
  phase: string;
  trust: number;
  energy: number;
}

// ── Identity types ──

export interface IdentityData {
  about_user: { fact: string; confidence: number; timestamp: string }[];
  user_facts: Record<string, unknown>;
  user_evaluation: string | null;
  conversation_context: string | null;
  relationship: {
    phase: string;
    phase_description: string;
    trust: number;
    hurt: number;
    reciprocity_balance: number;
  };
}

// ── Link types ──

export interface LinkStatus {
  linked: boolean;
  discord_id?: string;
  linked_at?: string;
}

export interface LinkResult {
  success: boolean;
  discord_id?: string;
  error?: string;
}

// ═══════════════════════════════════════════
//  API Functions
// ═══════════════════════════════════════════

// Existing endpoints
export function getXP(userId: string = DEFAULT_USER_ID) {
  return apiFetch<XPData>(`/api/user/${userId}/xp`);
}

export function getDiary(userId: string = DEFAULT_USER_ID) {
  return apiFetch<DiaryData>(`/api/user/${userId}/diary`);
}

export function getTimeline(userId: string = DEFAULT_USER_ID) {
  return apiFetch<TimelineData>(`/api/user/${userId}/timeline`);
}

export function getStats(userId: string = DEFAULT_USER_ID) {
  return apiFetch<StatsData>(`/api/user/${userId}/stats`);
}

export function getInsideJokes(userId: string = DEFAULT_USER_ID) {
  return apiFetch<InsideJokesData>(`/api/user/${userId}/inside-jokes`);
}

export function getPatterns(userId: string = DEFAULT_USER_ID) {
  return apiFetch<PatternsData>(`/api/user/${userId}/patterns`);
}

export function sendChat(payload: ChatRequest, userId: string = DEFAULT_USER_ID) {
  return apiFetch<ChatResponse>(`/api/user/${userId}/chat`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── New endpoints (previously Discord-only) ──

export function getMemory(userId: string = DEFAULT_USER_ID) {
  return apiFetch<MemoryData>(`/api/user/${userId}/memory`);
}

export function bookmarkMemory(content: string, role: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ success: boolean; message: string }>(`/api/user/${userId}/memories`, {
    method: "POST",
    body: JSON.stringify({ content, role }),
  });
}

export function getPersonality(userId: string = DEFAULT_USER_ID) {
  return apiFetch<PersonalityData>(`/api/user/${userId}/personality`);
}

export function getIdentity(userId: string = DEFAULT_USER_ID) {
  return apiFetch<IdentityData>(`/api/user/${userId}/identity`);
}

export function getState(userId: string = DEFAULT_USER_ID) {
  return apiFetch<Record<string, unknown>>(`/api/user/${userId}/state`);
}

export function getSchedule(userId: string = DEFAULT_USER_ID) {
  return apiFetch<Record<string, unknown>>(`/api/user/${userId}/schedule`);
}

export function getComplexity(userId: string = DEFAULT_USER_ID) {
  return apiFetch<Record<string, unknown>>(`/api/user/${userId}/complexity`);
}

export function getDebug(userId: string = DEFAULT_USER_ID) {
  return apiFetch<Record<string, unknown>>(`/api/user/${userId}/debug`);
}

export function resetUser(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ success: boolean; message: string }>(`/api/user/${userId}/reset`, {
    method: "POST",
  });
}

export function endActiveDate(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ success: boolean; message: string }>(`/api/user/${userId}/end-date`, {
    method: "POST",
  });
}

// ── Discord link ──

export function getLinkStatus(userId: string = DEFAULT_USER_ID) {
  return apiFetch<LinkStatus>(`/api/user/${userId}/link`);
}

export function linkDiscord(code: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<LinkResult>(`/api/user/${userId}/link`, {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function getPlans(userId: string = DEFAULT_USER_ID) {
  return apiFetch<any[]>(`/api/user/${userId}/plans`);
}

export function addPlan(plan: { date: string; start: string; end: string; activity: string; location: string }, userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ success: boolean; plans: any[] }>(`/api/user/${userId}/plans`, {
    method: "POST",
    body: JSON.stringify(plan),
  });
}

export function deletePlan(date: string, start: string, end: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ success: boolean; plans: any[] }>(
    `/api/user/${userId}/plans?date=${encodeURIComponent(date)}&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`,
    {
      method: "DELETE",
    }
  );
}

export function getPostcards(userId: string = DEFAULT_USER_ID) {
  return apiFetch<PostcardsData>(`/api/user/${userId}/postcards`);
}

export function getMessages(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ messages: { role: "user" | "assistant"; content: string; timestamp: string }[] }>(`/api/user/${userId}/messages`);
}

// ── Mini-Games APIs ──

export interface DebateStartResponse {
  session_id: string;
  topic: string;
  user_side: string;
  rem_side: string;
  greeting: string;
  turn_limit: number;
}

export interface DebateChatResponse {
  rem_response: string;
  turn_count: number;
  turn_limit: number;
  sentiment_score: number;
  finished: boolean;
  verdict?: {
    winner: "user" | "rem";
    score_user: number;
    score_rem: number;
    mvp_quote: string;
    reasoning: string;
  };
}

export interface WinOverStartResponse {
  session_id: string;
  scenario_name: string;
  description: string;
  greeting: string;
  turns_remaining: number;
  stats: Record<string, number>;
}

export interface WinOverChatResponse {
  rem_response: string;
  turns_remaining: number;
  stats: Record<string, number>;
  game_status: "active" | "won" | "lost" | "blocked";
  evaluation: {
    tactic: string;
    sincerity_rating: number;
    disrespect_detected: boolean;
  };
}

export function startDebate(topicId: string, userStance: string = "for", userId: string = DEFAULT_USER_ID) {
  return apiFetch<DebateStartResponse>(`/api/user/${userId}/games/debate/start`, {
    method: "POST",
    body: JSON.stringify({ topic_id: topicId, user_stance: userStance }),
  });
}

export function chatDebate(message: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<DebateChatResponse>(`/api/user/${userId}/games/debate/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function startWinOver(scenarioId: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<WinOverStartResponse>(`/api/user/${userId}/games/win-over/start`, {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
}

export function chatWinOver(message: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<WinOverChatResponse>(`/api/user/${userId}/games/win-over/chat`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function getAchievements(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ unlocked: string[] }>(`/api/user/${userId}/games/achievements`);
}

