"""
Quantum Multi-Agent System (QMAS)
Seven internal agents debate every decision.
This creates genuine internal conflict and nuanced decisions - not deterministic rules.
"""

import os
import random
from typing import Dict, Any, List, Optional
import httpx
import json
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
DEFAULT_MODEL = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"

# Specialized model configuration per agent
# All agents use the same model now (google/gemma-2-2b-it) to avoid Novita routing
# Can be overridden via environment variables: QMAS_MODEL_EMOTIONAL, QMAS_MODEL_RATIONAL, etc.
AGENT_MODELS = {
    "Emotional": os.environ.get("QMAS_MODEL_EMOTIONAL", DEFAULT_MODEL),
    "Rational": os.environ.get("QMAS_MODEL_RATIONAL", DEFAULT_MODEL),
    "Protective": os.environ.get("QMAS_MODEL_PROTECTIVE", DEFAULT_MODEL),
    "Authentic": os.environ.get("QMAS_MODEL_AUTHENTIC", DEFAULT_MODEL),
    "Growth": os.environ.get("QMAS_MODEL_GROWTH", DEFAULT_MODEL),
    "Creative": os.environ.get("QMAS_MODEL_CREATIVE", DEFAULT_MODEL),
    "Memory": os.environ.get("QMAS_MODEL_MEMORY", DEFAULT_MODEL),
}

# Meta-synthesis model (should be more capable for ranking/synthesis)
META_SYNTHESIS_MODEL = os.environ.get("QMAS_META_SYNTHESIS_MODEL", DEFAULT_MODEL)


class QMASAgent:
    """Single agent in the QMAS system."""
    
    def __init__(self, name: str, perspective: str, temperature: float = 0.8, model_id: Optional[str] = None):
        self.name = name
        self.perspective = perspective
        self.temperature = temperature
        # Use agent-specific model if provided, otherwise use default
        self.model_id = model_id or AGENT_MODELS.get(name, DEFAULT_MODEL)
    
    async def generate_path(self, situation: Dict[str, Any], 
                          sample_number: int = 0,
                          creativity_engine: Optional[Any] = None) -> Dict[str, Any]:
        """
        Generate a decision path from this agent's perspective.
        
        Returns:
            {
                "action": str,
                "reasoning": str,
                "predicted_trust_delta": float,
                "predicted_effects": Dict[str, float],
                "confidence": float
            }
        """
        if not HF_TOKEN:
            return self._fallback_path()
        
        # Generate creative content if this is Creative agent
        creative_content = None
        if self.name == "Creative" and creativity_engine:
            creativity_context = {
                "boredom": situation.get("psyche_state", {}).get("mood", {}).get("boredom", 0.0),
                "tom_receptivity": situation.get("tom_receptivity", 0.5),
                "openness": situation.get("personality", {}).get("big_five", {}).get("openness", 0.5),
                "circadian_phase": situation.get("temporal_context", {}).get("circadian_phase", "afternoon"),
                "relationship_phase": situation.get("relationship_phase", "Building"),
                "recent_topics": [m.get("content", "")[:50] for m in situation.get("selected_memories", [])[:3]],
                "personality": situation.get("personality", {})
            }
            creative_content = await creativity_engine.generate_creative_content(creativity_context)
        
        prompt = self._build_agent_prompt(situation, creative_content)
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json=prompt,
                )
                
                if resp.status_code >= 400:
                    return self._fallback_path()
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return self._parse_path(content, situation)
        except Exception:
            pass
        
        return self._fallback_path()
    
    def _build_agent_prompt(self, situation: Dict[str, Any], 
                           creative_content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build prompt for this agent's perspective."""
        
        user_message = situation.get("user_message", "")
        psyche = situation.get("psyche_state", {})
        memories = situation.get("selected_memories", [])
        temporal_context = situation.get("temporal_context", {})
        relationship_phase = situation.get("relationship_phase", "Building")
        
        # For Creative Agent: Use generated creative content
        creative_content_str = ""
        if self.name == "Creative" and creative_content:
            creative_content_str = f"\n\nCREATIVE IDEAS GENERATED:\n"
            creative_content_str += f"Type: {creative_content.get('type', 'unknown')}\n"
            creative_content_str += f"Content: {creative_content.get('content', '')}\n"
            creative_content_str += "Consider incorporating this creative idea into your recommendation. You can use it directly or adapt it."
        
        # For other agents: Can reference creativity when appropriate
        creativity_note = ""
        if self.name in ["Emotional", "Growth", "Authentic"]:
            creativity_note = "\n\nNOTE: You can suggest creative, novel approaches. Don't just suggest standard responses - think outside the box. Consider unexpected ways to solve problems or express yourself."
        
        # Format memories for prompt
        memories_str = ""
        if memories:
            memories_str = "\n\nRELEVANT MEMORIES (from past conversations):\n"
            for i, mem in enumerate(memories[:5], 1):  # Top 5 memories
                if mem.get("type") == "identity":
                    memories_str += f"{i}. Identity: {mem.get('fact', '')} (confidence: {mem.get('confidence', 0):.2f})\n"
                elif mem.get("type") == "episodic":
                    memories_str += f"{i}. Past event: {mem.get('content', '')[:80]}... (salience: {mem.get('salience', 0):.2f})\n"
                elif mem.get("type") == "act":
                    memories_str += f"{i}. Related topic: {mem.get('anchor_texts', '')[:80]}...\n"
                elif mem.get("type") == "stm":
                    memories_str += f"{i}. Recent: {mem.get('content', '')[:80]}...\n"
        
        # Special handling for Memory Agent
        memory_agent_instructions = ""
        if self.name == "Memory":
            memory_agent_instructions = """
YOUR SPECIFIC ROLE: Analyze history and patterns.
- Look at past conflicts: How were they resolved?
- Consider user patterns: What works with this user?
- Find precedents: Similar situations and outcomes
- Predict based on history: What does the past teach us?
"""
        
        # Special handling for Creative Agent
        creative_agent_instructions = ""
        if self.name == "Creative":
            creative_agent_instructions = """
YOUR SPECIFIC ROLE: Generate novel, creative solutions.
- Think outside the box
- Suggest unexpected approaches
- Consider creative ways to solve problems
- Novelty and spontaneity are your strengths
"""
        
        system_prompt = f"""You are the {self.name} agent in a multi-agent decision system.

Your perspective: {self.perspective}
{memory_agent_instructions}
{creative_agent_instructions}
{creative_content_str}
{creativity_note}

Current situation:
- User message: "{user_message}"
- Trust: {psyche.get('trust', 0.7):.2f}
- Hurt: {psyche.get('hurt', 0.0):.2f}
- Mood: {', '.join([f'{k}={v:.2f}' for k, v in list(psyche.get('mood', {}).items())[:3]])}
- Relationship phase: {relationship_phase}
{memories_str}

From your perspective, what should be done? What action do you recommend?
What are the likely effects on trust, relationship, emotional state?

{"If you are the Memory agent, specifically reference past events, patterns, and precedents in your reasoning." if self.name == "Memory" else ""}
{"If you are the Creative agent, use the generated creative ideas above, or suggest your own novel approaches." if self.name == "Creative" else ""}

Output your recommendation as:
ACTION: [what to do]
REASONING: [why - include memory references if relevant]
TRUST_DELTA: [predicted change in trust, -1 to +1]
EFFECTS: [predicted effects on mood, relationship, etc.]
CONFIDENCE: [0-1, how confident you are]"""

        # Note: This is now async, but we need to return the prompt dict
        # The actual async call happens in generate_path
        return {
            "model": self.model_id,  # Use agent-specific model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "What do you recommend?"}
            ],
            "max_tokens": 300,
            "temperature": self.temperature,  # Different agents have different creativity
        }
    
    def _parse_path(self, content: str, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Parse agent's path from response."""
        # Simple extraction (can be enhanced)
        content_lower = content.lower()
        
        # Extract action
        action = "respond_naturally"
        if "comfort" in content_lower or "support" in content_lower:
            action = "comfort"
        elif "challenge" in content_lower or "push" in content_lower:
            action = "challenge"
        elif "withdraw" in content_lower or "distance" in content_lower:
            action = "withdraw"
        elif "apologize" in content_lower or "repair" in content_lower:
            action = "repair"
        elif "celebrate" in content_lower or "enthusiasm" in content_lower:
            action = "celebrate"
        
        # Extract trust delta (try to find number)
        trust_delta = 0.0
        if "trust" in content_lower:
            # Try to extract number near "trust"
            import re
            trust_match = re.search(r'trust[:\s]+([-+]?\d*\.?\d+)', content_lower)
            if trust_match:
                try:
                    trust_delta = float(trust_match.group(1))
                    trust_delta = max(-1.0, min(1.0, trust_delta))
                except:
                    pass
        
        return {
            "agent": self.name,
            "action": action,
            "reasoning": content[:200],  # First 200 chars
            "predicted_trust_delta": trust_delta,
            "predicted_effects": {
                "mood_impact": 0.5,
                "relationship_impact": 0.5
            },
            "confidence": 0.7
        }
    
    def _fallback_path(self) -> Dict[str, Any]:
        """Fallback path when LLM unavailable."""
        return {
            "agent": self.name,
            "action": "respond_naturally",
            "reasoning": f"{self.perspective} perspective",
            "predicted_trust_delta": 0.0,
            "predicted_effects": {},
            "confidence": 0.5
        }


class QuantumMultiAgentSystem:
    """
    Seven-agent debate system that generates 100 Monte Carlo paths.
    This creates genuine multi-perspective decisions, not deterministic formulas.
    """
    
    def __init__(self, agent_models: Optional[Dict[str, str]] = None):
        """
        Initialize QMAS with specialized models per agent.
        
        Args:
            agent_models: Optional dict mapping agent names to model IDs.
                         If not provided, uses AGENT_MODELS config or environment variables.
        """
        # Allow custom model overrides
        models = agent_models or {}
        
        self.agents = [
            QMASAgent(
                "Emotional", 
                "What does my heart want? Prioritizes affection, closeness, impulsive.", 
                0.9,
                model_id=models.get("Emotional")
            ),
            QMASAgent(
                "Rational", 
                "What makes sense? Analyzes patterns, conservative, evidence-based.", 
                0.6,
                model_id=models.get("Rational")
            ),
            QMASAgent(
                "Protective", 
                "What keeps me safe? Defensive, boundary-focused, risk-averse.", 
                0.7,
                model_id=models.get("Protective")
            ),
            QMASAgent(
                "Authentic", 
                "What's true? Honest above all, non-performative, genuine.", 
                0.8,
                model_id=models.get("Authentic")
            ),
            QMASAgent(
                "Growth", 
                "How can we evolve? Uses conflict as opportunity, long-term focus.", 
                0.7,
                model_id=models.get("Growth")
            ),
            QMASAgent(
                "Creative", 
                "What's novel? Spontaneity, playfulness, surprise.", 
                0.9,
                model_id=models.get("Creative")
            ),
            QMASAgent(
                "Memory", 
                "What does history teach? Pattern recognition, precedent analysis.", 
                0.6,
                model_id=models.get("Memory")
            ),
        ]
        self.has_llm = bool(HF_TOKEN)
        self.meta_synthesis_model = META_SYNTHESIS_MODEL
    
    async def execute_debate(self, situation: Dict[str, Any], 
                            num_paths: int = 100,
                            creativity_engine: Optional[Any] = None) -> Dict[str, Any]:
        """
        Execute multi-agent debate with Monte Carlo sampling.
        
        Process:
        1. Each agent generates paths (5 samples per agent)
        2. Sample 100 total paths (Monte Carlo)
        3. Meta-synthesis: LLM ranks paths
        4. Select best path
        
        Args:
            situation: Full situation context
            num_paths: Number of Monte Carlo paths (default 100)
        
        Returns:
            Best path with trust delta, action, reasoning
        """
        if not self.has_llm:
            return self._fallback_synthesis(situation)
        
        # Step 1: Generate paths from each agent
        all_paths = []
        
        # Each agent generates 5 samples (at their temperature)
        samples_per_agent = max(1, num_paths // (len(self.agents) * 2))  # Distribute paths
        
        for agent in self.agents:
            for i in range(samples_per_agent):
                # Pass creativity engine to agents (especially Creative agent)
                path = await agent.generate_path(situation, sample_number=i, 
                                                creativity_engine=creativity_engine)
                all_paths.append(path)
        
        # Step 2: If we need more paths, randomly sample from agents
        while len(all_paths) < num_paths:
            agent = random.choice(self.agents)
            path = await agent.generate_path(situation, sample_number=len(all_paths),
                                            creativity_engine=creativity_engine)
            all_paths.append(path)
        
        # Limit to num_paths
        all_paths = all_paths[:num_paths]
        
        # Step 3: Meta-synthesis - LLM ranks paths
        best_path = await self._meta_synthesis(all_paths, situation)
        
        return best_path
    
    async def _meta_synthesis(self, paths: List[Dict[str, Any]], 
                             situation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Meta-synthesis: LLM ranks paths by:
        - Authenticity
        - Relationship phase alignment
        - Constitutional compliance
        - Theory of Mind match
        """
        if not self.has_llm or not paths:
            return paths[0] if paths else self._fallback_synthesis(situation)
        
        # Build synthesis prompt
        paths_summary = []
        for i, path in enumerate(paths[:20]):  # Limit to top 20 for prompt size
            paths_summary.append(
                f"Path {i+1} ({path.get('agent', 'unknown')}): "
                f"{path.get('action', 'unknown')} - "
                f"Trust delta: {path.get('predicted_trust_delta', 0):.2f} - "
                f"{path.get('reasoning', '')[:100]}"
            )
        
        psyche = situation.get("psyche_state", {})
        trust = psyche.get("trust", 0.7)
        relationship_phase = situation.get("relationship_phase", "Building")
        
        system_prompt = f"""You are synthesizing multiple decision paths from different internal agents.

Current state:
- Trust: {trust:.2f}
- Relationship phase: {relationship_phase}
- User message: "{situation.get('user_message', '')[:100]}"

Available paths:
{chr(10).join(paths_summary)}

Rank these paths by:
1. Authenticity (genuine, not performative)
2. Relationship phase alignment (appropriate for current phase)
3. Constitutional compliance (follows core principles)
4. Theory of Mind match (understands user's state)

Which path is best? Why? What's the recommended action?

Output:
BEST_PATH: [number]
ACTION: [what to do]
REASONING: [why this path]
TRUST_DELTA: [predicted change]"""

        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json={
                        "model": self.meta_synthesis_model,  # Use specialized synthesis model
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": "Synthesize and select best path."}
                        ],
                        "max_tokens": 400,
                        "temperature": 0.7,
                    },
                )
                
                if resp.status_code < 400:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        # Parse and return best path
                        best_idx = self._extract_best_path_index(content, len(paths))
                        if 0 <= best_idx < len(paths):
                            return paths[best_idx]
        except Exception:
            pass
        
        # Fallback: Return path with highest predicted trust delta
        if paths:
            best = max(paths, key=lambda p: p.get("predicted_trust_delta", 0))
            return best
        
        return self._fallback_synthesis(situation)
    
    def _extract_best_path_index(self, content: str, num_paths: int) -> int:
        """Extract best path index from synthesis response."""
        import re
        # Look for "BEST_PATH: 1" or "Path 1" or similar
        match = re.search(r'(?:best_path|path)[:\s]+(\d+)', content.lower())
        if match:
            try:
                idx = int(match.group(1)) - 1  # Convert to 0-based
                return max(0, min(num_paths - 1, idx))
            except:
                pass
        return 0
    
    def _fallback_synthesis(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback when LLM unavailable."""
        return {
            "agent": "Synthesis",
            "action": "respond_naturally",
            "reasoning": "Multi-agent synthesis unavailable",
            "predicted_trust_delta": 0.0,
            "predicted_effects": {},
            "confidence": 0.5,
            "dominant_agent": "Authentic"
        }

