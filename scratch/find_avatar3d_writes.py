import json

log_file = "/Users/chandu/.gemini/antigravity/brain/8a2129d9-2196-408b-84e7-87ac094b0d2b/.system_generated/logs/transcript.jsonl"
out_file = "/Users/chandu/Downloads/emotion-agent/scratch/avatar3d_writes_history.txt"

with open(log_file, "r") as f, open(out_file, "w") as out:
    for line_idx, line in enumerate(f):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        
        tool_calls = data.get("tool_calls", [])
        for tc in tool_calls:
            name = tc.get("name")
            args = tc.get("args", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass
            target = args.get("TargetFile", "") if isinstance(args, dict) else ""
            if "Avatar3D.tsx" in target or "Avatar3D.tsx" in str(args):
                out.write(f"Step {data.get('step_index')}: {name}\n")
                if name == "write_to_file":
                    out.write(f"Written content: {args.get('CodeContent')[:4000]}...\n\n")
                elif name == "replace_file_content":
                    out.write(f"ReplacementTarget:\n{args.get('TargetContent')}\n")
                    out.write(f"ReplacementContent:\n{args.get('ReplacementContent')}\n\n")
                elif name == "multi_replace_file_content":
                    chunks = args.get("ReplacementChunks", [])
                    if isinstance(chunks, str):
                        try:
                            chunks = json.loads(chunks)
                        except Exception:
                            pass
                    out.write(f"Chunks:\n")
                    for chunk in chunks:
                        if isinstance(chunk, dict):
                            out.write(f"  Target:\n{chunk.get('TargetContent')}\n")
                            out.write(f"  Replacement:\n{chunk.get('ReplacementContent')}\n\n")
                        else:
                            out.write(f"  Chunk string: {chunk}\n\n")
