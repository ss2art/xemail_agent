import os
from pathlib import Path

repo_root = Path(__file__).resolve().parent
site_packages = repo_root / ".venv" / "Lib" / "site-packages"

matches = []
for dirpath, dirnames, filenames in os.walk(site_packages):
    for fn in filenames:
        if fn.endswith('.py'):
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    txt = f.read()
            except Exception:
                continue
            if 'ChatOpenAI' in txt:
                matches.append(fp)
for m in matches:
    print(m)
print('found', len(matches), 'matches')
print('done')
