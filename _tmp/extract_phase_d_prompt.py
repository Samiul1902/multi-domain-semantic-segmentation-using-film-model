import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
hits = []
for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        record = json.loads(line)
    except Exception:
        continue
    if not isinstance(record, dict) or record.get("role") != "user":
        continue
    content = record.get("content")
    chunks = []
    if isinstance(content, str):
        chunks = [content]
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type", "").endswith("_text"):
                chunks.append(part.get("text") or "")
    joined = "\n".join(chunks)
    if "Reliability" in joined and "FiLM" in joined:
        hits.append(joined)

print("hits:", len(hits))
if hits:
    prompt = max(hits, key=len)
    print("len:", len(prompt))
    index = prompt.find("FiLM")
    print("=" * 70)
    print(prompt[max(0, index - 900):index + 2600])
