import os
root = r'C:\Users\ss2ar\source\repos\xemail_agent\barebones_starter\.venv\Lib\site-packages'
matches = []
for dirpath, dirnames, filenames in os.walk(root):
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
