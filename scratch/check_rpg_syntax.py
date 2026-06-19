import ast
import os

class FStringChecker(ast.NodeVisitor):
    def __init__(self, filename, source):
        self.filename = filename
        self.source = source

    def visit_JoinedStr(self, node):
        for val in node.values:
            if isinstance(val, ast.FormattedValue):
                val_source = ast.get_source_segment(self.source, val)
                if val_source and "\\" in val_source:
                    print(f"[{self.filename}] Line {val.lineno}: Backslash in f-string expression: {val_source}")
        self.generic_visit(node)

backend_dir = "backend"
for root, dirs, files in os.walk(backend_dir):
    # skip venv and __pycache__
    if "venv" in root.split(os.sep) or "__pycache__" in root.split(os.sep):
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source, filename=filepath)
                FStringChecker(filepath, source).visit(tree)
            except Exception as e:
                print(f"Failed to process {filepath}: {e}")
