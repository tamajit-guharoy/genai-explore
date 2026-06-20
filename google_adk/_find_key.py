import json

with open(r'c:\Users\guhar\ws\calude_tutorial\google_adk\01_installation_setup.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    src = cell['source']
    if isinstance(src, list):
        src = ''.join(src)
    if 'AQ.Ab8RN6I4IffBekdaKbfU' in src or 'Ab8RN6I4IffBekdaKbfU' in src:
        print(f'=== Cell {i} (type={cell["cell_type"]}) ===')
        print(src)
        print()
