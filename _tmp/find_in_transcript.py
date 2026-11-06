import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
needle = sys.argv[2]
for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
    if needle not in line:
        continue
    try:
        record = json.loads(line)
    except Exception:
        continue
    role = record.get("role")
    print(f"--- line {number} role={role} type={record.get('type')} ---")

    def walk(node, out):
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, list):
            for item in node:
                walk(item, out)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key in ("text", "content", "input", "thinking"):
                    walk(value, out)

    chunks = []
    walk(record.get("content"), chunks)
    if not chunks:
        walk(record, chunks)
    text = "\n".join(chunks)
    index = text.find(needle)
    print(text[max(0, index - 1200):index + 1800])
    print("=" * 78)
