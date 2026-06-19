import sys
import os

# Add parent directory to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.discord_bot import clean_think_tags
from backend.prompt_distiller import evolve_archetype

def test_clean_think_tags():
    print("=== Testing clean_think_tags() ===")
    
    # 1. Standard think tags
    t1 = "<think>I should be annoyed</think>Hey there, what's up?"
    assert clean_think_tags(t1) == "Hey there, what's up?", f"Failed t1: {clean_think_tags(t1)}"
    
    # 2. Case insensitive vthink tags
    t2 = "<VTHINK>He seems nice</VTHINK>Oh, hey!"
    assert clean_think_tags(t2) == "Oh, hey!", f"Failed t2: {clean_think_tags(t2)}"
    
    # 3. Unclosed think tags (due to token limits)
    t3 = "Sure, I can help.<think>I'm tired and want to sleep"
    assert clean_think_tags(t3) == "Sure, I can help.", f"Failed t3: {clean_think_tags(t3)}"
    
    # 4. Stray closing tags
    t4 = "Hey there!</think>"
    assert clean_think_tags(t4) == "Hey there!", f"Failed t4: {clean_think_tags(t4)}"
    
    # 5. Plain text prefix
    t5 = "thinking - I should reply nicely\nI would love to help out!"
    assert clean_think_tags(t5) == "I would love to help out!", f"Failed t5: {clean_think_tags(t5)}"
    
    print("✅ All clean_think_tags tests passed!")


def test_archetype_discovery_gating():
    print("\n=== Testing Archetype Discovery Phase Gating ===")
    
    # For a naggy starting archetype in Discovery phase:
    res = evolve_archetype(
        archetype="naggy",
        phase="Discovery",
        trust=0.3,
        hurt=0.0
    )
    
    assert res["branch"] == "naggy (starting)", f"Expected starting branch, got: {res['branch']}"
    assert "Naggy Style" in res["guideline"], f"Expected starting guideline, got: {res['guideline']}"
    
    # For a hard_to_get starting archetype in Discovery phase:
    res_htg = evolve_archetype(
        archetype="hard_to_get",
        phase="Discovery",
        trust=0.3,
        hurt=0.0
    )
    assert res_htg["branch"] == "hard_to_get (starting)", f"Expected starting branch, got: {res_htg['branch']}"
    
    # In Building phase, it should evolve:
    res_evolved = evolve_archetype(
        archetype="naggy",
        phase="Building",
        trust=0.6,
        hurt=0.0
    )
    assert res_evolved["branch"] == "naggy_clingy", f"Expected evolved branch, got: {res_evolved['branch']}"
    
    print("✅ Discovery phase archetype evolution gating works perfectly!")


if __name__ == "__main__":
    test_clean_think_tags()
    test_archetype_discovery_gating()
