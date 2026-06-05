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


// ── Personality Test APIs ──
export function startPersonality(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ session_id: string; total_questions: number; questions: any[] }>(`/api/user/${userId}/games/personality/start`, {
    method: "POST"
  });
}

export function answerPersonality(sessionId: string, questionId: number, choice: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ banter: string; finished: boolean; result: any }>(`/api/user/${userId}/games/personality/answer`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, question_id: questionId, choice })
  });
}

// ── Cooking APIs ──
export function searchRecipes(query: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ results: any[] }>(`/api/user/${userId}/games/cook/search?query=${encodeURIComponent(query)}`);
}

export function startCooking(dishName: string = "", userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ session_id: string; dish_name: string; category: string; thumbnail: string; ingredients: string[]; steps: string[]; greeting: string }>(`/api/user/${userId}/games/cook/start`, {
    method: "POST",
    body: JSON.stringify({ dish_name: dishName })
  });
}

export function stepCooking(userMessage: string, action: "next" | "disaster" | "skip", userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ banter: string; current_step: number; chaos_meter: number; finished: boolean }>(`/api/user/${userId}/games/cook/step`, {
    method: "POST",
    body: JSON.stringify({ user_message: userMessage, action })
  });
}

export function getCookbook(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ cookbook: any[] }>(`/api/user/${userId}/games/cookbook`);
}

// ── Spicy Chat APIs ──
export function startSpicy(scenario: string, mood: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ session_id: string; greeting: string }>(`/api/user/${userId}/games/spicy/start`, {
    method: "POST",
    body: JSON.stringify({ scenario, mood })
  });
}

export function chatSpicy(message: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ response: string }>(`/api/user/${userId}/games/spicy/chat`, {
    method: "POST",
    body: JSON.stringify({ message })
  });
}

export function endSpicy(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ secret_unlocked: boolean; secret: any }>(`/api/user/${userId}/games/spicy/end`, {
    method: "POST"
  });
}

export function getSecrets(userId: string = DEFAULT_USER_ID) {
  return apiFetch<{ secrets: any[] }>(`/api/user/${userId}/games/secrets`);
}

// ── Yap Mode APIs ──
export interface YapStartResponse {
  session_id: string;
  greeting: string;
  facts: string[];
}

export interface YapChatResponse {
  response: string;
  turn_count: number;
  finished: boolean;
  achievement_unlocked: boolean;
  facts?: string[];
}

export function startYap(topic: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<YapStartResponse>(`/api/user/${userId}/games/yap/start`, {
    method: "POST",
    body: JSON.stringify({ topic })
  });
}

export function chatYap(message: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<YapChatResponse>(`/api/user/${userId}/games/yap/chat`, {
    method: "POST",
    body: JSON.stringify({ message })
  });
}

// ── RPG Quest & Murder Mystery APIs ──

export interface RpgScenario {
  quest_id: string;
  title: string;
  difficulty?: string;
  description: string;
  starting_location: string;
  max_turns: number;
  locations: Array<{ id: string; name: string; desc: string }>;
  suspects: Array<{ name: string; role: string; bio: string; starting_suspicion: number; alibi?: string }>;
  weapons: Array<{ id: string; name: string; desc: string }>;
  clues: Array<{ id: string; name: string; desc: string; hidden_at: string; belongs_to?: string }>;
  contradictions?: Array<{ id: string; description: string }>;
}

export interface RpgStartResponse {
  session_id: string;
  title: string;
  current_location: string;
  narrator_text: string;
  rem_dialogue: string;
  suggested_choices: string[];
  suspects: Array<{ name: string; role: string; bio: string; starting_suspicion: number; alibi?: string }>;
  weapons: Array<{ id: string; name: string; desc: string }>;
  clues: Array<{ id: string; name: string; desc: string; hidden_at: string; belongs_to?: string }>;
  max_turns: number;
  difficulty: string;
  rem_consultations_left: number;
  health?: number;
}

export interface RpgTurnResponse {
  current_location: string;
  narrator_text: string;
  rem_dialogue: string;
  suggested_choices: string[];
  suspect_states: Record<string, { suspicion: number; interrogated: boolean; defensiveness: number; alibi?: string; last_statement?: string; current_location?: string }>;
  inventory: string[];
  clues_found: string[];
  turn_count: number;
  max_turns: number;
  finished: boolean;
  rem_consultations_left: number;
  discovered_contradictions: string[];
  active_effects: string[];
  health?: number;
}

export interface RpgAccuseResponse {
  success: boolean;
  narrator_text: string;
  rem_dialogue: string;
  secret_culprit: string;
  secret_weapon: string;
}

export function getRpgScenarios(userId: string = DEFAULT_USER_ID) {
  return apiFetch<RpgScenario[]>(`/api/user/${userId}/games/rpg/scenarios`);
}

export function startRpgGame(scenarioId: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<RpgStartResponse>(`/api/user/${userId}/games/rpg/start`, {
    method: "POST",
    body: JSON.stringify({ scenario_id: scenarioId })
  });
}

export function turnRpgGame(userAction: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<RpgTurnResponse>(`/api/user/${userId}/games/rpg/turn`, {
    method: "POST",
    body: JSON.stringify({ user_action: userAction })
  });
}

export function accuseRpgGame(suspect: string, weapon: string, motive: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<RpgAccuseResponse>(`/api/user/${userId}/games/rpg/accuse`, {
    method: "POST",
    body: JSON.stringify({ suspect, weapon, motive })
  });
}


// ── Courtroom Battle ("Law and Rem") Types ──

export interface CourtScenario {
  case_id: string;
  title: string;
  difficulty: string;
  description: string;
  client_name: string;
  client_role: string;
  client_bio: string;
  prosecutor_name: string;
  judge_name: string;
}

export interface CourtStartResponse {
  session_id: string;
  title: string;
  difficulty: string;
  client_name: string;
  client_role: string;
  client_bio: string;
  prosecutor_name: string;
  judge_name: string;
  inventory: Array<{ id: string; name: string; desc: string }>;
  witnesses: Array<{
    id: string;
    name: string;
    role: string;
    bio: string;
    testimony: string[];
  }>;
  recess_locations: Array<{
    id: string;
    name: string;
    desc: string;
    clue: { id: string; name: string; desc: string } | null;
  }>;
  strikes_left: number;
  jury_sentiment: number;
  current_witness_idx: number;
  recess_searched: string[];
  rem_consults_left: number;
  rem_chat_history: Array<{ role: string; content: string }>;
  history: Array<{ role: string; speaker: string; content: string }>;
  phase: "briefing" | "cross_examination" | "recess" | "closing" | "verdict";
  finished: boolean;
}

export interface CourtVerdictResponse {
  success: boolean;
  verdict_text: string;
  votes_not_guilty: number;
  votes_guilty: number;
  judge_decision: string;
  rem_dialogue: string;
}

export function getCourtScenarios(userId: string = DEFAULT_USER_ID) {
  return apiFetch<CourtScenario[]>(`/api/user/${userId}/games/court/scenarios`);
}

export function startCourtGame(caseId: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<CourtStartResponse>(`/api/user/${userId}/games/court/start`, {
    method: "POST",
    body: JSON.stringify({ case_id: caseId })
  });
}

export function submitCourtAction(
  actionType: "call_witness" | "press" | "present_evidence" | "text_question" | "consult_rem",
  params: { statementIdx?: number; evidenceId?: string; question?: string },
  userId: string = DEFAULT_USER_ID
) {
  return apiFetch<CourtStartResponse>(`/api/user/${userId}/games/court/action`, {
    method: "POST",
    body: JSON.stringify({
      action_type: actionType,
      statement_idx: params.statementIdx || 0,
      evidence_id: params.evidenceId || "",
      question: params.question || ""
    })
  });
}

export function searchRecessRoom(roomId: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<CourtStartResponse>(`/api/user/${userId}/games/court/recess`, {
    method: "POST",
    body: JSON.stringify({ room_id: roomId })
  });
}

export function submitClosingArguments(closingArgument: string, userId: string = DEFAULT_USER_ID) {
  return apiFetch<CourtVerdictResponse>(`/api/user/${userId}/games/court/verdict`, {
    method: "POST",
    body: JSON.stringify({ closing_argument: closingArgument })
  });
}




