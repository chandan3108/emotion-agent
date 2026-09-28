#!/usr/bin/env python3
"""
Chat Export Ingestion & Burst Turn Parser (Persona Cloner)

Parses WhatsApp (.txt) or Discord (.json) chat export logs into multi-turn
ChatML JSONL training datasets for fine-tuning conversational companion models.

Key Features:
- Rapid burst aggregation: Combines rapid consecutive texts within 90s into '|||' delimited turns.
- Session segmentation: Splits conversation trees on inactivity gaps (>3h).
- System noise & media filter: Purges encryption notices, deleted messages, media stubs.
- ChatML formatting: Outputs OpenAI / Unsloth compliant JSONL datasets.
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


# Regex patterns for WhatsApp dates
WHATSAPP_PATTERNS = [
    # [12/31/23, 23:59:59] Name: Message
    re.compile(r"^\[(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s*(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\]\s*(?P<sender>[^:]+):\s*(?P<message>.*)$"),
    # 12/31/23, 11:59 PM - Name: Message
    re.compile(r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s*(?P<time>\d{1,2}:\d{2}(?:\s*[APap][Mm])?)\s*-\s*(?P<sender>[^:]+):\s*(?P<message>.*)$"),
    # 31.12.23, 23:59 - Name: Message
    re.compile(r"^(?P<date>\d{1,2}\.\d{1,2}\.\d{2,4}),\s*(?P<time>\d{1,2}:\d{2})\s*-\s*(?P<sender>[^:]+):\s*(?P<message>.*)$"),
]

# System messages to discard
WHATSAPP_IGNORE = [
    "messages and calls are end-to-end encrypted",
    "<media omitted>",
    "image omitted",
    "audio omitted",
    "video omitted",
    "sticker omitted",
    "document omitted",
    "this message was deleted",
    "you deleted this message",
    "joined using this group",
    "changed the subject to",
    "security code changed",
    "pinned a message",
]


def parse_timestamp(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse various WhatsApp date/time formats into datetime object."""
    date_str = date_str.replace(".", "/").strip()
    time_str = time_str.strip()
    
    formats = [
        "%d/%m/%y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%y %I:%M %p",
        "%d/%m/%Y %I:%M %p",
        "%m/%d/%y %I:%M %p",
        "%m/%d/%Y %I:%M %p",
        "%d/%m/%y %H:%M",
        "%d/%m/%Y %H:%M",
        "%m/%d/%y %H:%M",
        "%m/%d/%Y %H:%M",
    ]
    
    clean_dt = f"{date_str} {time_str}"
    for fmt in formats:
        try:
            return datetime.strptime(clean_dt, fmt)
        except ValueError:
            continue
    return None


def parse_whatsapp(file_path: str) -> List[Dict[str, Any]]:
    """Parse raw WhatsApp .txt chat export into raw chronological message records."""
    messages = []
    
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        current_msg = None
        
        for line in f:
            line_str = line.strip("\u200e\u202a\u202c\n")  # Strip hidden unicode direction markers
            matched = False
            
            for pat in WHATSAPP_PATTERNS:
                m = pat.match(line_str)
                if m:
                    sender = m.group("sender").strip()
                    msg_body = m.group("message").strip()
                    dt = parse_timestamp(m.group("date"), m.group("time"))
                    
                    # Check if line is a system notice
                    if any(ign in msg_body.lower() for ign in WHATSAPP_IGNORE):
                        current_msg = None
                        matched = True
                        break
                        
                    current_msg = {
                        "sender": sender,
                        "content": msg_body,
                        "timestamp": dt or datetime.now()
                    }
                    messages.append(current_msg)
                    matched = True
                    break
                    
            if not matched and current_msg is not None:
                # Multi-line message continuation
                if not any(ign in line_str.lower() for ign in WHATSAPP_IGNORE):
                    current_msg["content"] += "\n" + line_str
                    
    return messages


def parse_discord(file_path: str) -> List[Dict[str, Any]]:
    """Parse Discord JSON export (e.g. DiscordChatExporter)."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    raw_list = data.get("messages", data) if isinstance(data, dict) else data
    messages = []
    
    for item in raw_list:
        author = item.get("author", {})
        sender = author.get("name") or author.get("username") or "Unknown"
        content = item.get("content", "").strip()
        ts_str = item.get("timestamp") or ""
        
        if not content:
            continue
            
        dt = None
        if ts_str:
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                pass
                
        messages.append({
            "sender": sender,
            "content": content,
            "timestamp": dt or datetime.now()
        })
        
    # Ensure chronological sorting
    messages.sort(key=lambda m: m["timestamp"])
    return messages


def aggregate_burst_turns(
    messages: List[Dict[str, Any]],
    burst_gap_seconds: int = 90
) -> List[Dict[str, Any]]:
    """
    Groups rapid consecutive messages from the same sender within `burst_gap_seconds`
    into single turns delimited by ' ||| '.
    """
    if not messages:
        return []
        
    grouped = []
    current_turn = None
    
    for msg in messages:
        if not msg["content"].strip():
            continue
            
        if current_turn is None:
            current_turn = {
                "sender": msg["sender"],
                "content": msg["content"].strip(),
                "timestamp": msg["timestamp"],
                "last_timestamp": msg["timestamp"]
            }
            continue
            
        time_diff = (msg["timestamp"] - current_turn["last_timestamp"]).total_seconds()
        
        # Same sender within burst window -> join with ||| delimiter
        if msg["sender"] == current_turn["sender"] and abs(time_diff) <= burst_gap_seconds:
            current_turn["content"] += f" ||| {msg['content'].strip()}"
            current_turn["last_timestamp"] = msg["timestamp"]
        else:
            grouped.append(current_turn)
            current_turn = {
                "sender": msg["sender"],
                "content": msg["content"].strip(),
                "timestamp": msg["timestamp"],
                "last_timestamp": msg["timestamp"]
            }
            
    if current_turn:
        grouped.append(current_turn)
        
    return grouped


def segment_into_conversations(
    turns: List[Dict[str, Any]],
    target_speaker: str,
    session_gap_hours: float = 3.0,
    system_prompt: str = "You are Rem, an authentic, emotionally intelligent college student. You text casually in lowercase with rapid multi-bubble bursts separated by |||."
) -> List[Dict[str, Any]]:
    """
    Splits aggregated turns into distinct multi-turn conversations based on inactivity gaps.
    Formats turns into ChatML: {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
    """
    conversations = []
    current_conv = []
    last_ts = None
    
    for turn in turns:
        # Check for session boundary
        if last_ts and (turn["timestamp"] - last_ts).total_seconds() > (session_gap_hours * 3600):
            if len(current_conv) >= 2:
                # Validate that conversation has at least one assistant turn
                if any(m["role"] == "assistant" for m in current_conv):
                    conversations.append({
                        "messages": [{"role": "system", "content": system_prompt}] + current_conv
                    })
            current_conv = []
            
        role = "assistant" if turn["sender"].lower() == target_speaker.lower() else "user"
        
        # Avoid consecutive same-role turns in final ChatML
        if current_conv and current_conv[-1]["role"] == role:
            current_conv[-1]["content"] += f" ||| {turn['content']}"
        else:
            current_conv.append({
                "role": role,
                "content": turn["content"]
            })
            
        last_ts = turn["last_timestamp"]
        
    if len(current_conv) >= 2 and any(m["role"] == "assistant" for m in current_conv):
        conversations.append({
            "messages": [{"role": "system", "content": system_prompt}] + current_conv
        })
        
    return conversations


def main():
    parser = argparse.ArgumentParser(description="Parse chat archives into ChatML JSONL datasets.")
    parser.add_argument("--input", "-i", required=True, help="Path to input chat file (.txt or .json)")
    parser.add_argument("--target", "-t", required=True, help="Name of target sender to clone as 'assistant'")
    parser.add_argument("--output", "-o", default="data/finetune_chatml.jsonl", help="Output .jsonl path")
    parser.add_argument("--format", "-f", choices=["whatsapp", "discord", "auto"], default="auto", help="Input format")
    parser.add_argument("--burst-gap", type=int, default=90, help="Seconds threshold to group bursts (default: 90)")
    parser.add_argument("--session-gap", type=float, default=3.0, help="Hours of inactivity to split conversations (default: 3.0)")
    parser.add_argument("--system-prompt", default=None, help="Custom system prompt to inject into ChatML headers")
    
    args = parser.parse_args()
    
    fmt = args.format
    if fmt == "auto":
        fmt = "discord" if args.input.endswith(".json") else "whatsapp"
        
    print(f"[*] Ingesting {args.input} using format: {fmt.upper()}")
    if fmt == "whatsapp":
        raw_msgs = parse_whatsapp(args.input)
    else:
        raw_msgs = parse_discord(args.input)
        
    print(f"[*] Parsed {len(raw_msgs)} raw message entries.")
    if not raw_msgs:
        print("[!] No messages found or parsed. Check input format.")
        sys.exit(1)
        
    # Group bursts
    turns = aggregate_burst_turns(raw_msgs, burst_gap_seconds=args.burst_gap)
    print(f"[*] Aggregated into {len(turns)} conversational burst turns (using {args.burst_gap}s window).")
    
    # Segment into ChatML sessions
    sys_prompt = args.system_prompt or "You are Rem, an authentic, emotionally intelligent college student. You text casually in lowercase with rapid multi-bubble bursts separated by |||."
    conversations = segment_into_conversations(turns, target_speaker=args.target, session_gap_hours=args.session_gap, system_prompt=sys_prompt)
    print(f"[*] Created {len(conversations)} multi-turn ChatML conversation sessions.")
    
    if not conversations:
        print(f"[!] Warning: 0 conversations generated. Check if target sender '{args.target}' matches senders in chat:")
        senders = set(m["sender"] for m in raw_msgs)
        print(f"    Available senders: {list(senders)[:10]}")
        sys.exit(1)
        
    # Write to JSONL
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for c in conversations:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
            
    print(f"[+] Successfully exported {len(conversations)} training sessions to {args.output}")
    print("\nSample Generated Conversation Turn:")
    sample = conversations[0]["messages"][:3]
    for s in sample:
        print(f"  [{s['role'].upper()}]: {s['content'][:120]}...")


if __name__ == "__main__":
    main()
