import re
import sqlite3
import json

def clean_and_format_memory_content(content: str, event_type: str) -> str:
    if not content:
        return ""
    
    # 1. Clean explicit_bookmark
    if event_type == "explicit_bookmark" or content.startswith(("[User]", "[Rem]")):
        if content.startswith("[User]"):
            val = content[len("[User]"):].strip()
            return f"You: \"{val}\""
        elif content.startswith("[Rem]"):
            val = content[len("[Rem]"):].strip()
            return f"I: \"{val}\""
    
    # 2. Clean own_reaction
    if event_type == "own_reaction" or content.startswith("Shifted from"):
        # Match Shifted from 'x' to 'y'. [details] I said: "..."
        match = re.match(r"Shifted from\s+'[^']+'\s+to\s+'([^']+)'\.\s*(.*?)\s*I said:\s*(.*)", content, re.DOTALL)
        if match:
            to_state = match.group(1)
            details = match.group(2).strip()
            said = match.group(3).strip()
            if details:
                if not details.endswith('.'):
                    details += '.'
                return f"I felt {to_state} ({details.lower().rstrip('.')}) and said: {said}"
            else:
                return f"I felt {to_state} and said: {said}"
        
        # Match Shifted from 'x' to 'y'. [details]
        match2 = re.match(r"Shifted from\s+'[^']+'\s+to\s+'([^']+)'\.\s*(.*)", content, re.DOTALL)
        if match2:
            to_state = match2.group(1)
            details = match2.group(2).strip()
            if details:
                return f"I felt {to_state} - {details}"
            return f"I felt {to_state}"
            
    # 3. Handle third-person to first-person translation
    s = content
    
    s = re.sub(r"\bRem's\b", "my", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem'\b", "my", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem\b", "I", s, flags=re.IGNORECASE)
    
    s = re.sub(r"\bthe user's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthe user\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser\b", "you", s, flags=re.IGNORECASE)
    
    s = re.sub(r"\btheir\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthem\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\bhimself/herself/themselves\b", "yourself", s, flags=re.IGNORECASE)
    
    # Verb correction for 'you'
    s = re.sub(r"\byou was\b", "you were", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou is\b", "you are", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou has\b", "you have", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou seems\b", "you seem", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou feels\b", "you feel", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou wants\b", "you want", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou looks\b", "you look", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou thinks\b", "you think", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou makes\b", "you make", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou agrees\b", "you agreed", s, flags=re.IGNORECASE)
    
    # Verb correction for 'I'
    s = re.sub(r"\bI feels\b", "I feel", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI wants\b", "I want", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI thinks\b", "I think", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI is\b", "I am", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI has\b", "I have", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI plays\b", "I play", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI says\b", "I say", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI teases\b", "I teased", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI playfully teases\b", "I playfully teased", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI playfully teased\b", "I playfully teased", s, flags=re.IGNORECASE)
    
    # Prefix verbs if it starts with a verb
    verbs = [
        "Discussed", "Talked", "Shared", "Exchanged", "Argued", "Agreed", "Went", 
        "Had", "Made", "Planned", "Told", "Asked", "Showed", "Felt", "Wished", 
        "Wanted", "Joked", "Laughed", "Smiled", "Wondered", "Opened", "Expressed"
    ]
    words = s.split()
    if words:
        first_word = words[0].rstrip(',.:;!?')
        if first_word in verbs:
            s = "We " + s[0].lower() + s[1:]
        elif first_word.lower() in [v.lower() for v in verbs]:
            s = "We " + s
            
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        s = s[0].upper() + s[1:]
        
    return s

def clean_and_format_fact(fact: str) -> str:
    if not fact:
        return ""
    
    s = fact.strip()
    words = s.split()
    if words:
        first = words[0].lower()
        if first == "not" and len(words) > 1 and words[1].lower() == "into":
            s = "You are " + s
        elif first.endswith("s") or first.endswith("ing") or first in ["read", "like", "love", "hate", "want", "need", "have", "has", "is", "into", "studying", "reading", "working"]:
            if first == "into":
                s = "You are " + s
            elif first == "studying":
                s = "You are " + s
            elif first == "reading":
                s = "You are " + s
            elif first == "working":
                s = "You are " + s
            elif first.endswith("s"):
                if first == "is":
                    words[0] = "are"
                elif first == "has":
                    words[0] = "have"
                elif first == "thinks":
                    words[0] = "think"
                elif first == "likes":
                    words[0] = "like"
                elif first == "loves":
                    words[0] = "love"
                elif first == "wants":
                    words[0] = "want"
                elif first == "needs":
                    words[0] = "need"
                elif first == "feels":
                    words[0] = "feel"
                elif first == "hates":
                    words[0] = "hate"
                elif first == "knows":
                    words[0] = "know"
                elif first == "believes":
                    words[0] = "believe"
                elif first == "prefers":
                    words[0] = "prefer"
                else:
                    if len(first) > 3:
                        words[0] = first[:-1]
                s = "You " + " ".join(words)
            else:
                s = "You " + s

    s = re.sub(r"\bthe user's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthe user\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem's\b", "my", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem\b", "me", s, flags=re.IGNORECASE)
    
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        s = s[0].upper() + s[1:]
        
    return s

conn = sqlite3.connect("state.db")
cursor = conn.cursor()
cursor.execute("SELECT state_json FROM user_state WHERE user_id = \"web_web_user_001\"")
row = cursor.fetchone()
if row:
    state = json.loads(row[0])
    mem = state.get("memory_hierarchy", {})
    
    print("--- FORMATTED EPISODIC MEMORIES ---")
    for e in mem.get("episodic", []):
        raw = e.get("content", "")
        fmt = clean_and_format_memory_content(raw, e.get("event_type", ""))
        print(f"[{e.get('event_type')}]:")
        print(f"  Raw: {raw}")
        print(f"  Fmt: {fmt}")
        print()
        
    print("--- FORMATTED IDENTITY FACTS ---")
    for i in mem.get("identity", []):
        raw = i.get("fact", "")
        fmt = clean_and_format_fact(raw)
        print(f"  Raw: {raw}")
        print(f"  Fmt: {fmt}")
        print()
