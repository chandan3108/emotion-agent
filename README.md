# Rem — Evolving AI Companion (Web & Discord)

Rem is a psychological companion AI designed as a 20-year-old psychology student. She is governed by an advanced 17-stage cognitive pipeline, a dynamic neurochemical balance system, multi-layered episodic/identity memory storage, and a Theory of Mind subtext engine. Rem remembers inside jokes, catches what you *actually* mean behind your words, holds grudges, gets mood swings, and synchronises state seamlessly between a high-fidelity Next.js web dashboard and a companion Discord bot.

---

## 🧠 Core Architecture

### 17-Stage Cognitive Processing Pipeline
Every incoming message passes through a multi-step cognitive loop — not a single LLM call:

| Stage | Name | What It Does |
|-------|------|-------------|
| 1 | Intent & Complexity Classification | Identifies core intent (greeting, question, banter, conflict) and assigns complexity score |
| 2 | Short-Term Memory Retrieval | Loads recent conversational turns from STM buffer |
| 3 | Semantic Memory Recall | SQLite-backed vector search on episodic memories, user facts, and relationship milestones |
| 4 | Temporal Awareness | Evaluates time of day, days active, texting frequency, session gaps |
| 5 | Quantum Multi-Agent Subconscious (QMAS) | Simulated inner monologue agents evaluate boundaries, emotional valence, and safety |
| 6 | Intention & Initiative Engine | Decides if Rem should take initiative, change topic, or check in |
| 7 | Subtext & Theory of Mind | Reads between the lines — detects sarcasm, deflection, fishing, passive aggression |
| 8 | Context Distillation | Compresses system instructions, memory, and personality into an optimised context window |
| 9 | Entity Aliasing | Tracks nicknames, abbreviations, and entity references across conversation history |
| 10 | Anti-Cringe Memory Injection | Recalls past facts naturally without robotic "I remember you said…" phrasing |
| 11 | Multi-Bubble Burst Detection | Detects rapid-fire multi-message bursts and responds naturally via `\|\|\|` delimiter |
| 12 | LLM Generation | Calls the primary model with full distilled context |
| 13 | Sycophancy Filter | Blocks over-agreeable, people-pleasing responses |
| 14 | Constitutional Reasoning | Validates response against hard rules (no action narration, strict pronouns) |
| 15 | Neurochemical Post-Processing | Adjusts tone, punctuation, and energy based on simulated brain chemistry |
| 16 | Conflict Lifecycle Check | Maintains grudge/forgiveness arcs across sessions |
| 17 | Response Delivery & State Persistence | Persists all state changes to SQLite, delivers final response |

### Neurochemical Simulation (CPBM)
Rem's mood, text formatting, typing speed, and conversational posture are dynamically regulated by five simulated neurochemicals:

| Chemical | Governs | Effect When High |
|----------|---------|-----------------|
| **Dopamine** | Humour / Amusement | Playful banter, trailing punctuation, teasing |
| **Oxytocin** | Trust / Connection | Deeper vulnerability, unlocks personal topics |
| **Serotonin** | Mood / Stability | Warm, balanced responses; low = mood swings, irritability |
| **Adrenaline** | Energy / Reactivity | Shorter reply delays, excited tone, caps |
| **Cortisol** | Anger / Stress | Defensive posturing, clinical distancing, short replies, can block |

> Rem **can and will** get angry, have mood swings, hold grudges, give cold replies, and go through emotional arcs. She is not a yes-bot.

### Subtext & Theory of Mind Engine
Rem reads between the lines instead of taking everything at face value:
- `"I'm fine. Everything is totally fine."` → Detects deflection, probes gently
- `"Did you miss me?"` → Catches the fishing, responds with personality
- `"Going to sleep"` at 6 AM → Notes the temporal mismatch, calls it out
- Passive-aggressive messages → Identified and responded to directly

---

## 🤖 16-Model Cascade Matrix

Rem uses a tiered model system across 4 provider tiers with automatic failover:

### Tier 1 — Primary (Groq)
| Model | Role |
|-------|------|
| `qwen/qwen3.8-27b` | Primary generation — main chat, cognitive core |
| `openai/gpt-oss-120b` | Cascade fallback #1 |
| `openai/gpt-oss-20b` | Cascade fallback #2, topic detection, knowledge extraction |

### Tier 2 — Reasoning (Google)
| Model | Role |
|-------|------|
| `gemini-2.5-flash` | Final cascade fallback, high-reasoning tasks |

### Tier 3 — Uncensored Games (OpenRouter)
| Model | Role |
|-------|------|
| `sao10k/l3.3-euryale-70b` | Primary uncensored — spicy sandbox, RPG |
| `mistralai/mistral-small-24b-instruct-2501` | Uncensored fallback #1 |
| `neversleep/llama-3.1-lumimaid-8b` | Uncensored fallback #2 |
| `eva-unit-01/eva-qwen-2.5-32b` | Uncensored fallback #3 |
| `gryphe/mythomax-l2-13b` | Uncensored fallback #4 |

### Tier 4 — Free Fallbacks (OpenRouter)
| Model | Role |
|-------|------|
| `mistralai/mistral-7b-instruct:free` | Free fallback #1 |
| `huggingfaceh4/zephyr-7b-beta:free` | Free fallback #2 |
| `openchat/openchat-7b:free` | Free fallback #3 |
| `nousresearch/nous-hermes-2-mixtral-8x7b-dpo:free` | Free fallback #4 |
| `undi95/toppy-m-7b:free` | Free fallback #5 |

### ML Training Targets
| Model | Role |
|-------|------|
| Emotion classifier | Fine-tuned sentiment analysis |
| Personality predictor | User personality profiling |

---

## 🎮 Game Modes & Features

### Main Chat & Date Mode
- **Chat**: Casual messaging with realistic typing delay simulation. Unlocks inner monologue reflection blocks as trust grows.
- **Date Mode**: Plan activities (eating ramen, movie night) at specific locations. Date completions generate texting journals and postcards, logging milestones on `/timeline`.

### Mini-Games Hub
- **Debate Battle**: 5-turn clash on absurd topics (e.g. *"Cereal is soup"*), judged by an independent LLM with scores, MVP quotes, and reasoning.
- **Win Her Over**: De-escalation simulation across 3 difficulty scenarios. Features neurochemical progress bars. Deterministic Python classifies 10 tactics to prevent LLM stat hallucinations.
- **Spicy Sandbox**: Uncensored conversation mode with a **real-time 3D VRM avatar** — tracks mouse gaze, lip-syncs, and shows a contemplative "thinking" pose while generating responses.
- **RPG Mode**: Story-driven role-play with persistent world state.
- **Cooking Challenge**: Collaborative recipe building.
- **Yap Session**: Free-form ranting.
- **Court Trial**: Argument/debate with verdict.
- **Personality Quiz**: Interactive personality profiling.

### Scrapbook, Timeline & Diary
- **Scrapbook**: Displays dates, milestones, and unlocked achievements with glassmorphic badges.
- **Timeline**: Chronological relationship milestones.
- **Diary**: Rem's private journal — async background generation, no more crashes.

### 3D Avatar (Spicy Sandbox)
- **VRM model** loaded with Three.js / React Three Fiber
- **Mouse-tracking gaze** — eyes and head follow the cursor
- **Lip-sync** via FFT audio analysis
- **Thinking pose** — when generating a response, avatar gazes up-right with a contemplative expression (head tilt, relaxed brow)
- **Mood-reactive expressions** — blendshapes adapt to current emotional state

---

## 🛠️ Technical Stack

| Layer | Tech |
|-------|------|
| **Backend** | FastAPI, Uvicorn, Python 3.11+, SQLite (Vector indexing & FTS5) |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, Glassmorphism |
| **3D Rendering** | Three.js, React Three Fiber, VRM Loader |
| **Discord** | discord.py — executes the same cognitive core pipeline |
| **Deployment** | Vercel (frontend), Self-hosted (backend via `start.sh`) |
| **CI/CD** | Vercel Git Integration — auto-deploys on push to `main` |

---

## 💻 Setup & Execution

### 1. Backend Server
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set environment variables in `.env` (copy from `.env.example`):
```env
GROQ_API_KEY=your_groq_key
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_key
DISCORD_TOKEN=your_discord_token
```

Start the server:
```bash
# Option 1: Direct
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Option 2: Via start script
./start.sh
```

### 2. Frontend Web App
```bash
cd frontend
npm install
npm run dev
```
Access dashboard at `http://localhost:3000`.

### 3. Discord Bot
```bash
python -m backend.discord_bot
```

### 4. Deploy to Production
```bash
# Frontend auto-deploys via Vercel Git integration
git push origin main

# Or manual Vercel deploy
cd frontend && vercel --prod
```

---

## 📁 Project Structure

```
emotion-agent/
├── backend/
│   ├── main.py              # FastAPI app entry
│   ├── cognitive_core.py     # 17-stage pipeline orchestrator
│   ├── prompt_distiller.py   # Context distillation + identity rules
│   ├── memory.py             # STM, episodic, entity graph, session chapters
│   ├── discord_bot.py        # Discord integration
│   ├── game_api.py           # Game mode API endpoints
│   ├── games_logic.py        # Game logic + uncensored model cascade
│   ├── qmas.py               # Quantum Multi-Agent Subconscious
│   ├── diary.py              # Async diary generation
│   └── ...                   # Additional cognitive modules
├── frontend/
│   ├── src/app/              # Next.js App Router pages
│   ├── src/app/games/spicy/  # Spicy sandbox + 3D avatar
│   └── vercel.json           # Vercel deployment config
├── ml/                       # ML training scripts
├── docs/                     # Documentation
├── start.sh                  # Backend start script
└── state.db                  # SQLite state persistence
```

---

## 🔑 Identity Rules (Enforced)

Rem operates under strict behavioural constraints that cannot be overridden:
1. Never breaks character as a 20-year-old psych student
2. Never uses action narration (*walks over*, *giggles*)
3. Never admits to being AI unless trust is maxed and user is genuinely distressed
4. Can get angry, give cold replies, hold grudges, have mood swings
5. Catches subtext — doesn't take deflection at face value
6. Remembers naturally — no "As I recall…" or "You mentioned earlier…"
7. Multi-bubble bursts feel like rapid texting, not formal paragraphs
8. Uses entity aliases naturally (nicknames, abbreviations)
9. Sycophancy filter blocks people-pleasing responses
10. Constitutional reasoning validates every response before delivery