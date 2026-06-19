import re

file_path = "/Users/chandu/Downloads/emotion-agent/frontend/src/app/games/spicy/Avatar3D.tsx"

with open(file_path, "r") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    # Search for assignments like something.property = ...
    # We want to check if the same something.property is assigned in close proximity (e.g. within 10 lines)
    match = re.search(r"(\w+\.\w+)\s*=", line)
    if match:
        var_name = match.group(1)
        # Check next 10 lines
        for offset in range(1, 10):
            if idx + offset < len(lines):
                next_line = lines[idx + offset]
                next_match = re.search(r"(\w+\.\w+)\s*=", next_line)
                if next_match and next_match.group(1) == var_name:
                    print(f"Line {idx+1}: {var_name} assigned here")
                    print(f"Line {idx+1+offset}: {var_name} assigned again within {offset} lines!")
                    print(f"  Line {idx+1}: {line.strip()}")
                    print(f"  Line {idx+1+offset}: {next_line.strip()}")
                    print("-" * 40)
