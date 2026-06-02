# Rem — Evolving AI Companion (Web & Discord)

Rem is a psychological companion AI designed as a 20-year-old psychology student. She is governed by an advanced 17-stage cognitive pipeline, a dynamic neurochemical balance system, and multi-layered episodic/identity memory storage. Rem remembers inside jokes, analyzes behavioral patterns, and synchronizes state seamlessly between a high-fidelity Next.js web dashboard and a companion Discord bot.

---

## 🚀 Key Architectures

### 1. 17-Stage Cognitive Processing Pipeline
Rem's messaging engine does not just call an LLM; it orchestrates a multi-step cognitive loop for every incoming message:
* **Stage 1: Intent & Complexity Classification**: Identifies core intent (greeting, question, banter, conflict, etc.) and assigns a complexity score to optimize downstream token usage.
* **Stage 2: Short-Term Memory Retrieval**: Loads recent conversational turns.
* **Stage 3: Semantic Memory Recall**: Performs SQLite-backed vector search on episodic memories, user facts, and relationship milestones.
* **Stage 4: Temporal Awareness**: Evaluates time of day, days active, and texting frequency.
* **Stage 5: Quantum Multi-Agent Subconscious (QMAS)**: Simulated inner monologue agents evaluate boundaries, emotional valence, and safety.
* **Stage 6: Intention & Initiative Engine**: Decides if Rem should take the initiative, change the topic, or check in.
* **Stage 7: Context Distillation**: Compresses the system instructions, memory, and personality profile into a tight, optimized context window.
* **Stage 8: LLM Generation & Verification**: Calls the primary model (Llama-3) and verifies the response against hard limitations (e.g. no action narration, strict second-person pronouns).

### 2. Neurochemical Simulation (CPBM)
Rem's mood, text formatting, typing speed, and conversational posture are dynamically regulated by five simulated neurochemicals:
* **Dopamine (Humor / Amusement)**: High dopamine triggers playful banter and trailing punctuation.
* **Oxytocin (Trust / Connection)**: Dictates trust rank and access to deeper features.
* **Serotonin (Stance / Mood)**: Regulates emotional stability.
* **Adrenaline (Energy / Reactivity)**: High adrenaline shortens reply delays and increases energy.
* **Cortisol (Anger / Stress)**: Rises on toxic inputs; triggers defensive posturing, clinical psychological distancing, or blocks.

---

## 🎮 Game Modes & Features

### 1. Main Chat & Date Mode
* **Chat**: Casual messaging with typing delay simulations. Unlocks inner monologue reflection blocks as trust grows.
* **Date Mode**: Plan activities (e.g. eating ramen, movie night) at specific locations. Date completions generate texting journals and postcards, automatically logging milestones on the `/timeline`.

### 2. Mini-Games Hub (State Isolated)
* **Debate Battle**:
  * Passively judged by Llama-3.1 LORDS in a 5-turn clash on silly topics (e.g. *"Cereal is soup"*, *"Socks-sleepers are unstable"*).
  * Verdict includes scores, MVP savageness quotes, and reasoning.
* **Win Her Over Challenge**:
  * De-escalation simulation with 3 difficulty scenarios (*The Broken Promise*, *The Silent Treatment*, *The Cold Stranger*).
  * Features 5 vertical progress cylinders representing neurochemical metrics.
  * Deterministic Python updates classify 10 tactics (e.g. `intellectual_challenge`, `charming_flirtation`, `awkward_reaction`, `empathy_validation`) to prevent LLM stat hallucinations.

### 3. Scrapbook & Timeline
* Displays dates, milestones, and unlocked achievements (e.g., *Debate Champion*, *Heart Melter*) with glowing neon glassmorphic badges.

---

## 🛠️ Technical Stack

* **Backend**: FastAPI, Uvicorn, Python, SQLite (Vector indexing & FTS5 searching).
* **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Vanilla CSS Glassmorphism.
* **Discord Integration**: Discord.py bot executing the exact same cognitive core pipeline, paired with link-code sync schemas.

---

## 💻 Setup & Execution

### 1. Backend Server
1. Navigate to `/backend`.
2. Install virtual environment and dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set your environment variables in `.env` (copy from `.env.example`).
4. Start FastAPI server:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

### 2. Frontend Web App
1. Navigate to `/frontend`.
2. Install Node packages:
   ```bash
   npm install
   ```
3. Run dev server:
   ```bash
   npm run dev
   ```
4. Access dashboard at `http://localhost:3000`.