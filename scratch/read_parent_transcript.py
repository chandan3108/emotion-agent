import json

log_path = "/Users/chandu/.gemini/antigravity/brain/8a2129d9-2196-408b-84e7-87ac094b0d2b/.system_generated/logs/transcript.jsonl"
with open(log_path, "r") as f:
    for line in f:
        try:
            step = json.loads(line)
            if "tool_calls" in step:
                for tc in step["tool_calls"]:
                    if tc.get("name") in ["replace_file_content", "write_to_file", "multi_replace_file_content"]:
                        args = tc.get("args", {})
                        if "Avatar3D.tsx" in str(args.get("TargetFile", "")):
                            print(f"Step {step.get('step_index')}: {tc.get('name')}")
                            print(args.get("Description", ""))
                            print("-----------------------------------")
        except Exception as e:
            pass
