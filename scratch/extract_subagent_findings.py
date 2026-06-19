import json

log_path = "/Users/chandu/.gemini/antigravity/brain/8a2129d9-2196-408b-84e7-87ac094b0d2b/.system_generated/logs/transcript.jsonl"
with open(log_path, "r") as f:
    for line in f:
        try:
            step = json.loads(line)
            if step.get("step_index") == 10865:
                print("Step 10865 details:")
                for tc in step.get("tool_calls", []):
                    args = tc.get("args", {})
                    content = args.get("ReplacementContent", "") or args.get("CodeContent", "")
                    if not content and "ReplacementChunks" in args:
                        content = str(args["ReplacementChunks"])
                    # Print parts of content that mention folded-arms
                    idx = 0
                    while True:
                        idx = content.find("folded-arms", idx)
                        if idx == -1:
                            break
                        print(content[max(0, idx - 200): min(len(content), idx + 800)])
                        print("=" * 40)
                        idx += 1
                break
        except Exception as e:
            pass
