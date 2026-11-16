"""Check local Markdown destinations and heading anchors without network calls."""
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
files = [p for p in ROOT.rglob("*.md") if not any(x in p.parts for x in ("node_modules", ".next", ".next-e2e", ".git"))]
errors = []
count = 0
for path in files:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for match in re.finditer(r"\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
        dest = unquote(match[1].strip("<>"))
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", dest):
            continue
        name, _, anchor = dest.partition("#")
        target = (path.parent / name).resolve() if name else path
        count += 1
        if not target.exists():
            errors.append(f"{path.relative_to(ROOT)}: missing {dest}")
        elif anchor and target.suffix == ".md":
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", target.read_text(encoding="utf-8"), re.M)
            slugs = [re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings]
            if anchor not in slugs:
                errors.append(f"{path.relative_to(ROOT)}: missing heading {dest}")
print(f"Checked {len(files)} Markdown files and {count} local destinations")
for error in errors:
    print(error)
sys.exit(bool(errors))
