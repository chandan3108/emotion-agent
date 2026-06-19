import json
import re

log_file = "/Users/chandu/.gemini/antigravity/brain/8a2129d9-2196-408b-84e7-87ac094b0d2b/.system_generated/logs/transcript.jsonl"

with open(log_file, "r") as f:
    for line in f:
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
            
            content = ""
            if name == "write_to_file" and "Avatar3D.tsx" in args.get("TargetFile", ""):
                content = args.get("CodeContent", "")
            elif name in ["replace_file_content", "multi_replace_file_content"] and "Avatar3D.tsx" in args.get("TargetFile", ""):
                content = str(args)
            
            if content:
                # Search for duplicate assignments in content
                # For example, look for targetPose.rightUpperArm = ... targetPose.rightUpperArm = ...
                # or pose.leftUpperArm = ... pose.leftUpperArm = ...
                for bone in ["leftUpperArm", "rightUpperArm", "leftLowerArm", "rightLowerArm"]:
                    # Find if the bone is assigned twice in the same block/near each other
                    # We can look for occurrences of targetPose.bone or pose.bone
                    patterns = [
                        rf"targetPose\.{bone}\s*=",
                        rf"pose\.{bone}\s*="
                    ]
                    for pattern in patterns:
                        matches = list(re.finditer(pattern, content))
                        if len(matches) > 1:
                            print(f"Step {data.get('step_index')}: Found {len(matches)} assignments of {bone} using pattern '{pattern}'")
                            # print the context around matches
                            for m in matches:
                                start = max(0, m.start() - 50)
                                end = min(len(content), m.end() + 100)
                                print("  Context:", content[start:end].replace('\n', ' '))
